/**
 * AEGIS Help Documentation System
 * ==========================================
 * Comprehensive documentation for all features.
 * Version: 6.1.7
 *
 * Complete overhaul with:
 * - Beautiful visual design with icons and illustrations
 * - Detailed explanations of "how" and "why" for every feature
 * - Technical deep-dive section for advanced users
 * - Smooth navigation and professional typography
 *
 * v6.1.7 - HeadlessSP diagnostic logging + URL guard all folder endpoints + scan_history.py deploy (fixes 500 errors)
 * v6.1.6 - HeadlessSP SSO fix: launchPersistentContext + msedge channel + EnableAmbientAuthenticationInIncognito
 * v6.1.5 - Playwright Chromium browser binary install fix + auth allowlist deduplication
 * v6.1.4 - Headless SP: Federated SSO fix (3-phase auth, ADFS allowlist, sharepoint.log diagnostics)
 * v6.1.3 - Headless Browser SharePoint Connector (Playwright + Windows SSO bypass for GCC High AADSTS65002)
 * v6.1.2 - SharePoint Device Code Flow UI + URL Misroute Fix (visible OAuth prompt, folder_scan_start URL guard)
 * v6.1.1 - Fix: CRITICAL — MSAL instance_discovery=False + verify=False for GCC High (authority validation & corporate SSL)
 * v6.1.0 - Fix: CRITICAL — SharePoint OAuth tenant identifier format fixed (bare 'ngc' → 'ngc.onmicrosoft.us' or GUID via OIDC discovery)
 * v6.0.9 - Fix: OAuth packages (msal/PyJWT/pywin32) now install via online pip when local wheels missing
 * v6.0.8 - SharePoint zero-config OAuth auto-detection (well-known client ID, tenant from URL, IWA fallback, UI freeze fix)
 * v6.0.7 - SharePoint Auth Fix (pywin32 install for preemptive SSPI, embedded Python detection, offline-only installs)
 * v6.0.6 - SharePoint folder validation auth bypass fix (validate_folder_path now uses _api_get)
 * v6.0.5 - SharePoint Online Modern Auth (preemptive SSPI Negotiate + MSAL OAuth 2.0 for GCC High legacy auth deprecation)
 * v6.0.4 - PDF Zoom/Pan Fix + Proposal Duplicate Detection (viewport-center zoom, click-drag pan, auto-fit width, upload duplicate prompt)
 * v6.0.3 - SharePoint Batch Auth Fix (per-download fresh session for thread-safe NTLM, OData ampersand encoding)
 * v6.0.2 - Fix Assistant Reviewer/Owner Mode + US English Dictionary + Duplicate Proposal Fix
 * v6.0.0 - 5-Module Learning System, Proposal Compare v2, Enhanced Security, 545+ audio clips
 * v5.9.21 - Animated HTML/CSS diagrams replace 5 static PNGs (Architecture, Checkers, Extraction, Docling, NLP Pipeline)
 * v5.9.20 - Data Explorer z-index fix, particle visibility through backdrops, Email Diagnostics .eml with attachments
 * v5.9.19 - Light mode metric card drill-down visibility, settings tab scroll indicators, global particle canvas
 * v5.9.18 - Help beacon hides during demo playback (no longer overlays X stop button), Compare sub-demo QA verified
 * v5.9.17 - Narration Speed Fix + Full Demo QA (BUG #9 race condition fixed, all 12 sections / 93 sub-demos verified)
 * v5.9.16 - SOW Template Upload + Graph Export + Live Demo Overhaul (DOCX template population, PNG/SVG/HTML graph export, demo scene fixes)
 * v5.9.0 - Deep Validation & Scoring Improvements (SemanticAnalyzer fix, response.ok guards, dedup expansion, scoring concentration discount)
 * v5.8.2 - Production Hardening Pass (ReportLab sanitization, CSRF fix, prefers-reduced-motion on 19 CSS files, spaCy SVO extraction)
 * v5.6.0 - Guide System v2.0.0 + Animated Demo Player (real content for all 11 sections, live walkthrough demos, SVG spotlight tours, settings toggle)
 * v5.5.0 - Server-Side Folder Scanning (recursive discovery, chunked processing, batch limits increase to 50/500MB)
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
    version: '6.1.0',
    lastUpdated: '2026-02-25',
    
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
        { id: 'guided-tours', title: 'Guided Tours & Demos', icon: 'play-circle', subsections: [
            { id: 'tour-overview', title: 'Overview', icon: 'info' },
            { id: 'tour-demos', title: 'Watching Demos', icon: 'monitor-play' },
            { id: 'tour-voice', title: 'Voice Narration', icon: 'volume-2' },
            { id: 'tour-sub-demos', title: 'Deep-Dive Sub-Demos', icon: 'layers' }
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
        { id: 'sow-generator', title: 'SOW Generator', icon: 'file-output', subsections: [
            { id: 'sow-overview', title: 'Overview', icon: 'info' },
            { id: 'sow-template', title: 'Template Upload', icon: 'upload' },
            { id: 'sow-placeholders', title: 'Placeholders', icon: 'code' }
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
        { id: 'proposal-compare', title: 'Proposal Compare', icon: 'git-compare-arrows', subsections: [
            { id: 'pc-overview', title: 'Overview', icon: 'info' },
            { id: 'pc-uploading', title: 'Uploading Proposals', icon: 'upload' },
            { id: 'pc-review', title: 'Review & Edit', icon: 'pencil' },
            { id: 'pc-comparison', title: 'Comparison View', icon: 'columns' },
            { id: 'pc-analytics', title: 'Analytics Tabs', icon: 'bar-chart-3' },
            { id: 'pc-history', title: 'History', icon: 'history' },
            { id: 'pc-dashboard', title: 'Project Dashboard', icon: 'layout-dashboard' },
            { id: 'pc-export', title: 'Exporting Results', icon: 'download' },
            { id: 'pc-structure', title: 'Structure Analyzer', icon: 'file-search' }
        ]},
        { id: 'exporting', title: 'Exporting Results', icon: 'download', subsections: [
            { id: 'export-overview', title: 'Export Options', icon: 'info' },
            { id: 'export-word', title: 'Word Document', icon: 'file-text' },
            { id: 'export-pdf', title: 'PDF Report', icon: 'file-badge' },
            { id: 'export-data', title: 'CSV & Excel', icon: 'table' },
            { id: 'export-json', title: 'JSON Data', icon: 'code' },
            { id: 'export-filters', title: 'Filter & Preview', icon: 'sliders-horizontal' }
        ]},
        { id: 'settings', title: 'Settings', icon: 'settings', subsections: [
            { id: 'settings-general', title: 'General', icon: 'sliders' },
            { id: 'settings-review', title: 'Review', icon: 'file-check' },
            { id: 'settings-network', title: 'Network & Auth', icon: 'shield' },
            { id: 'settings-profiles', title: 'Document Profiles', icon: 'layers' },
            { id: 'settings-display', title: 'Display', icon: 'palette' },
            { id: 'settings-updates', title: 'Updates', icon: 'refresh-cw' },
            { id: 'settings-diagnostics', title: 'Diagnostics', icon: 'activity' },
            { id: 'settings-data', title: 'Data Management', icon: 'database' },
            { id: 'settings-sharing', title: 'Sharing', icon: 'share-2' }
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
        // v6.0.0: Cinema showcase disabled — will be re-enabled when AI video is ready
        // { id: 'cinema-showcase', title: 'Behind the Scenes', icon: 'clapperboard' },
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
        <p>AEGIS is a comprehensive document analysis platform that combines <strong>105+ quality checks</strong>, <strong>AI-powered role extraction</strong>, <strong>statement extraction for process modeling</strong>, and <strong>intelligent fix assistance</strong>—all running locally without internet access.</p>
    </div>
</div>

<div class="help-callout help-callout-success">
    <i data-lucide="award"></i>
    <div>
        <strong>Enterprise-Grade Capabilities</strong>
        <p>Validated on government SOWs, defense SEPs, systems engineering management plans, and industry standards. Role extraction achieves <span class="help-stat">94.7% precision</span> and <span class="help-stat">92.3% F1 score</span>.</p>
    </div>
</div>

<h2><i data-lucide="layers"></i> Core Capabilities</h2>

<div class="help-feature-grid">
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="shield-check"></i></div>
        <h3>105+ Quality Checks</h3>
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
            <p>Understand what each of 105+ checks does</p>
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
// GUIDED TOURS & DEMOS
// ============================================================================
HelpDocs.content['tour-overview'] = {
    title: 'Guided Tours & Demos',
    subtitle: 'Interactive walkthroughs of every AEGIS feature',
    html: `
<div class="help-callout help-callout-info">
    <i data-lucide="play-circle"></i>
    <div>
        <strong>New to AEGIS?</strong>
        <p>The Guided Tour system provides animated walkthroughs of every feature. No video files needed — demos run on the live UI with spotlight highlighting, narration, and step-by-step guidance.</p>
    </div>
</div>

<h2><i data-lucide="sparkles"></i> What's Included</h2>
<ul>
    <li><strong>79 overview scenes</strong> covering all 11 AEGIS modules (Document Review, Batch, Roles, Statement Forge, SOW Generator, Hyperlink Validator, Document Compare, Metrics, History, Settings, Portfolio)</li>
    <li><strong>93 deep-dive sub-demos</strong> with approximately 471 scenes covering every sub-function, workflow, export, and import</li>
    <li><strong>Voice narration</strong> with typewriter text display and playback speed control</li>
    <li><strong>Full demo mode</strong> that walks through all modules sequentially (~10 minutes at 1x speed)</li>
</ul>

<h2><i data-lucide="mouse-pointer-click"></i> How to Start</h2>
<ol>
    <li>Click the <strong>?</strong> help beacon in the bottom-right corner of any screen</li>
    <li>In the help panel, click <strong>"Watch Demo"</strong> for the current section</li>
    <li>Or click <strong>"Full Demo"</strong> to watch all sections in sequence</li>
    <li>The demo bar appears at the bottom with play/pause, skip, and speed controls</li>
</ol>

<h2><i data-lucide="settings"></i> Settings</h2>
<p>Enable or disable the guide system in <strong>Settings > General > Guided Tour</strong>. When disabled, the help beacon and demo features are hidden.</p>
`
};

HelpDocs.content['tour-demos'] = {
    title: 'Watching Demos',
    subtitle: 'Overview demos for each AEGIS module',
    html: `
<h2><i data-lucide="monitor-play"></i> Demo Player Controls</h2>
<p>When a demo starts, a glassmorphism control bar appears at the bottom of the screen:</p>
<ul>
    <li><strong>Play/Pause</strong> — Toggle demo playback</li>
    <li><strong>Previous/Next</strong> — Skip between scenes</li>
    <li><strong>Stop (X)</strong> — End the demo and return to normal mode</li>
    <li><strong>Speed selector</strong> — Choose from 0.5x, 1x, 1.5x, or 2x playback speed</li>
    <li><strong>Progress bar</strong> — Visual indicator of current position</li>
</ul>

<h2><i data-lucide="target"></i> Spotlight System</h2>
<p>During demos, an SVG mask spotlight highlights the UI element being discussed. The rest of the screen is dimmed with a semi-transparent overlay. The spotlight automatically follows the element as the demo progresses through scenes.</p>

<h2><i data-lucide="type"></i> Narration Display</h2>
<p>Each scene displays narration text with a typewriter effect in the demo bar. The text describes what the highlighted element does and provides tips for effective use. Narration speed adjusts with the playback speed setting.</p>

<h2><i data-lucide="compass"></i> Section Navigation</h2>
<p>The demo player automatically navigates between modules — opening modals, switching tabs, and scrolling to elements as needed. When a demo ends or is stopped, the UI returns to its previous state.</p>
`
};

HelpDocs.content['tour-voice'] = {
    title: 'Voice Narration',
    subtitle: 'Audio narration for demo walkthroughs',
    html: `
<h2><i data-lucide="volume-2"></i> Audio Provider Chain</h2>
<p>AEGIS uses a three-tier audio system for demo narration:</p>
<ol>
    <li><strong>Pre-generated MP3 clips</strong> — High-quality neural voice audio (requires internet for initial generation)</li>
    <li><strong>Web Speech API</strong> — Browser-native text-to-speech as fallback (works offline)</li>
    <li><strong>Silent timer</strong> — If neither audio source is available, scenes advance on a timed basis</li>
</ol>

<h2><i data-lucide="sliders"></i> Controls</h2>
<ul>
    <li><strong>Narration toggle</strong> — Click the speaker icon in the demo bar to enable/disable voice</li>
    <li><strong>Volume slider</strong> — Adjust narration volume (persisted across sessions)</li>
    <li><strong>Voice selection</strong> — Automatically picks the best available voice</li>
    <li><strong>Speed sync</strong> — Audio playback rate syncs with the demo speed selector</li>
</ul>

<div class="help-callout help-callout-warning">
    <i data-lucide="info"></i>
    <div>
        <strong>Chrome 15-Second Bug</strong>
        <p>Chrome's Web Speech API has a known bug where utterances longer than ~15 seconds are cut off. AEGIS works around this by splitting narration into sentences and chaining them together.</p>
    </div>
</div>
`
};

HelpDocs.content['tour-sub-demos'] = {
    title: 'Deep-Dive Sub-Demos',
    subtitle: 'Detailed walkthroughs for every sub-feature',
    html: `
<h2><i data-lucide="layers"></i> What Are Sub-Demos?</h2>
<p>Sub-demos are focused walkthroughs that cover individual features within a module. While overview demos give a broad tour, sub-demos drill down into specific workflows like exporting data, configuring settings, or using advanced search.</p>

<h2><i data-lucide="mouse-pointer-click"></i> Accessing Sub-Demos</h2>
<ol>
    <li>Click the <strong>?</strong> help beacon to open the help panel</li>
    <li>Click <strong>"Watch Demo"</strong> — the panel transitions to show the demo picker</li>
    <li>The <strong>overview card</strong> plays the module's general walkthrough</li>
    <li>Below it, a <strong>2-column grid of sub-demo cards</strong> shows all available deep-dives</li>
    <li>Each card shows the sub-demo name, description, and estimated duration</li>
</ol>

<h2><i data-lucide="list"></i> Available Sub-Demos</h2>
<p>All 11 AEGIS modules have sub-demos. Examples include:</p>
<ul>
    <li><strong>Document Review</strong> — Loading files, preset configuration, issue triage, export results, fix assistant</li>
    <li><strong>Roles Studio</strong> — Adjudication workflow, dictionary management, export/import, relationship graph, function tags, RACI matrix</li>
    <li><strong>Statement Forge</strong> — Extraction pipeline, history overview, compare viewer, search, bulk editing</li>
    <li><strong>Hyperlink Validator</strong> — Validation flow, deep validate (headless), domain filtering, history, export</li>
    <li><strong>Metrics & Analytics</strong> — Overview dashboard, quality trends, role analysis, document tracking</li>
    <li><strong>Settings</strong> — Review profiles, display customization, network configuration, data management, diagnostics</li>
</ul>

<h2><i data-lucide="navigation"></i> During Sub-Demo Playback</h2>
<p>The demo bar shows a breadcrumb like <strong>"Roles Studio > Adjudication Workflow"</strong> so you always know where you are. Sub-demos automatically open the correct modal and switch to the right tab before playing their scenes.</p>
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
    subtitle: 'Understanding the 105+ checks available',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="shield-check" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>AEGIS includes <strong>105+ quality checks</strong> across 15 checker modules, covering grammar, spelling, acronyms, requirements language, document structure, hyperlinks, and more. All processing happens locally—no cloud dependencies.</p>
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
    subtitle: 'All 105+ quality checks in one place',
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

<h3>Graph Export (v5.9.16)</h3>
<p>Click the <strong>Export</strong> button in the graph toolbar to download the graph in three formats:</p>
<ul>
    <li><strong>PNG (High-Res)</strong> — 3x resolution raster image, ideal for presentations and reports</li>
    <li><strong>SVG (Vector)</strong> — Scalable vector format with inlined styles, ideal for editing in Illustrator or Inkscape</li>
    <li><strong>Interactive HTML</strong> — Standalone D3.js page with pan/zoom, node tooltips, search, and filter by function tag, role type, or org group</li>
</ul>

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
// SOW GENERATOR (v5.9.16)
// ============================================================================
HelpDocs.content['sow-overview'] = {
    title: 'SOW Generator',
    subtitle: 'Generate Statement of Work documents from extracted requirements',
    html: `
<h2><i data-lucide="file-output"></i> What is the SOW Generator?</h2>
<p>The SOW Generator creates professional Statement of Work documents by aggregating data from your scanned documents, extracted statements, adjudicated roles, and function categories. It produces either a standalone HTML document or populates a DOCX template with your data.</p>

<h2><i data-lucide="layout"></i> Two-Panel Interface</h2>
<table class="help-table">
    <thead><tr><th>Panel</th><th>Purpose</th></tr></thead>
    <tbody>
        <tr><td><strong>Configuration (Left)</strong></td><td>Set document metadata (title, version, date, author), custom introduction/scope text, section toggles, and optional DOCX template upload</td></tr>
        <tr><td><strong>Data Summary (Right)</strong></td><td>Live stats (documents, statements, roles, categories), document selection with checkboxes, directive breakdown chart</td></tr>
    </tbody>
</table>

<h2><i data-lucide="list-checks"></i> Generated Sections</h2>
<p>Toggle any section on/off before generating:</p>
<ul>
    <li><strong>Introduction</strong> — Project overview (custom or auto-generated)</li>
    <li><strong>Scope</strong> — Coverage areas with directive distribution</li>
    <li><strong>Applicable Documents</strong> — Table of all selected source documents</li>
    <li><strong>Requirements & Deliverables</strong> — Statements grouped by directive priority (SHALL > MUST > WILL > SHOULD > MAY)</li>
    <li><strong>Work Breakdown Structure</strong> — Hierarchical tree from function categories</li>
    <li><strong>Roles & Responsibilities</strong> — Role cards with function tags and assigned statements</li>
    <li><strong>Acceptance Criteria</strong> — Testable SHALL statements</li>
    <li><strong>Standards & Compliance</strong> — Auto-detected standard references (MIL-STD, DO-, SAE, ISO, etc.)</li>
    <li><strong>Assumptions & Constraints</strong> — Custom or default assumptions</li>
</ul>

<h2><i data-lucide="filter"></i> Document Selection</h2>
<p>Select which documents to include using checkboxes. Use <strong>All</strong> or <strong>None</strong> buttons for quick selection. Stats and directive chart update dynamically based on your selection.</p>
`
};

HelpDocs.content['sow-template'] = {
    title: 'Template Upload',
    subtitle: 'Populate your own DOCX template with extracted data',
    html: `
<h2><i data-lucide="upload"></i> Template Upload (v5.9.16)</h2>
<p>Upload a company DOCX template with placeholder markers. AEGIS will find and replace each placeholder with the corresponding extracted data, returning a populated DOCX document.</p>

<h2><i data-lucide="workflow"></i> How It Works</h2>
<ol>
    <li>Create a DOCX template with <code>{{PLACEHOLDER}}</code> markers where you want data inserted</li>
    <li>Open the SOW Generator and configure your settings</li>
    <li>Drag and drop your template into the upload area (or click Browse)</li>
    <li>Click <strong>Generate from Template</strong></li>
    <li>AEGIS populates all placeholders and downloads the completed DOCX</li>
</ol>

<div class="help-callout help-callout-info">
    <i data-lucide="info"></i>
    <div>
        <strong>Template Mode vs HTML Mode</strong>
        <p>Without a template, AEGIS generates a standalone HTML document with embedded styling. With a template, it returns a DOCX file preserving your template's formatting, fonts, and layout.</p>
    </div>
</div>
`
};

HelpDocs.content['sow-placeholders'] = {
    title: 'Supported Placeholders',
    subtitle: 'Reference guide for DOCX template markers',
    html: `
<h2><i data-lucide="code"></i> Available Placeholders</h2>
<table class="help-table">
    <thead><tr><th>Placeholder</th><th>Replaced With</th></tr></thead>
    <tbody>
        <tr><td><code>{{TITLE}}</code></td><td>SOW title from configuration</td></tr>
        <tr><td><code>{{DOC_NUMBER}}</code></td><td>Document number</td></tr>
        <tr><td><code>{{VERSION}}</code></td><td>Version string</td></tr>
        <tr><td><code>{{DATE}}</code></td><td>Effective date</td></tr>
        <tr><td><code>{{PREPARED_BY}}</code></td><td>Author name</td></tr>
        <tr><td><code>{{ORGANIZATION}}</code></td><td>Organization name</td></tr>
        <tr><td><code>{{INTRO}}</code></td><td>Introduction text</td></tr>
        <tr><td><code>{{SCOPE}}</code></td><td>Scope description</td></tr>
        <tr><td><code>{{REQUIREMENTS}}</code></td><td>All requirements grouped by directive</td></tr>
        <tr><td><code>{{ROLES}}</code></td><td>Role names, types, tags, and assigned statements</td></tr>
        <tr><td><code>{{DOCUMENTS}}</code></td><td>List of source documents with word counts and scores</td></tr>
        <tr><td><code>{{ACCEPTANCE}}</code></td><td>SHALL statements as acceptance criteria</td></tr>
        <tr><td><code>{{STANDARDS}}</code></td><td>Auto-detected standard references</td></tr>
        <tr><td><code>{{ASSUMPTIONS}}</code></td><td>Assumptions text</td></tr>
        <tr><td><code>{{TOTAL_DOCS}}</code></td><td>Number of selected documents</td></tr>
        <tr><td><code>{{TOTAL_STMTS}}</code></td><td>Number of statements</td></tr>
        <tr><td><code>{{TOTAL_ROLES}}</code></td><td>Number of active roles</td></tr>
        <tr><td><code>{{AEGIS_VERSION}}</code></td><td>AEGIS version string</td></tr>
        <tr><td><code>{{EXPORT_DATE}}</code></td><td>Export timestamp</td></tr>
    </tbody>
</table>

<div class="help-callout help-callout-warning">
    <i data-lucide="alert-triangle"></i>
    <div>
        <strong>Placeholder Formatting</strong>
        <p>Placeholders must use double curly braces: <code>{{NAME}}</code>. They work in paragraphs, table cells, headers, and footers. Make sure the entire placeholder is typed as one continuous string in Word (not split across formatting runs).</p>
    </div>
</div>
`
};

// ============================================================================
// EXPORT OVERVIEW
// ============================================================================
HelpDocs.content['export-overview'] = {
    title: 'Export Suite (v5.9.4)',
    subtitle: '5 export formats with pre-export filtering',
    html: `
<div class="help-export-grid">
    <div class="help-export-card" onclick="HelpContent.navigateTo('export-word')">
        <div class="help-export-card-icon"><i data-lucide="file-text"></i></div>
        <h3>Word Document</h3>
        <p>Original document with tracked changes and comments.</p>
        <span class="help-badge">Recommended</span>
    </div>
    <div class="help-export-card" onclick="HelpContent.navigateTo('export-pdf')">
        <div class="help-export-card-icon"><i data-lucide="file-badge"></i></div>
        <h3>PDF Report</h3>
        <p>Branded report with cover page, charts, and issue details.</p>
        <span class="help-badge" style="background: #ef4444;">New</span>
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

<h2><i data-lucide="sliders-horizontal"></i> Pre-Export Filtering</h2>
<p>Click <strong>Filter Issues</strong> in the export modal to narrow your export by severity or category. Chip-based selectors show issue counts, and a live preview displays how many issues will be included.</p>

<h2><i data-lucide="filter"></i> Export Modes</h2>
<ul>
    <li><strong>All Issues</strong> — Every issue from the scan</li>
    <li><strong>Filtered</strong> — Only issues matching the current results filter</li>
    <li><strong>Selected</strong> — Only hand-picked issues from the results table</li>
</ul>
<p>Filters from the export panel are applied <em>on top of</em> the selected mode.</p>

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
// PDF REPORT EXPORT (v5.9.4)
// ============================================================================
HelpDocs.content['export-pdf'] = {
    title: 'PDF Report Export',
    subtitle: 'Professional branded review report',
    html: `
<h2><i data-lucide="file-badge"></i> What You Get</h2>
<p>A multi-page PDF report generated server-side using AEGIS branding:</p>
<ul>
    <li><strong>Cover Page</strong> — Document name, quality score, grade, issue count, word count, reviewer name, AEGIS branding</li>
    <li><strong>Executive Summary</strong> — Score interpretation and key findings narrative</li>
    <li><strong>Severity Distribution</strong> — Table with counts, percentages, and visual bars for each severity level</li>
    <li><strong>Category Distribution</strong> — Top 15 categories ranked by issue count with top severity indicator</li>
    <li><strong>Issue Details</strong> — Full issue listing grouped by category with severity badges, messages, flagged text, and suggestions</li>
</ul>

<h2><i data-lucide="palette"></i> Branding</h2>
<p>The report uses AEGIS gold/bronze branding colors, color-coded severity labels (red for Critical, orange for High, etc.), and alternating row backgrounds for readability.</p>

<h2><i data-lucide="filter"></i> Filtered Reports</h2>
<p>When export filters are active, a yellow notice banner appears on the report indicating which severities or categories were included. This makes it clear the report is a subset of the full scan.</p>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Pro Tip</strong>
        <p>Use pre-export filters to create focused reports. For example, export only Critical and High severity issues for a management summary.</p>
    </div>
</div>
`
};

// ============================================================================
// EXPORT FILTERS (v5.9.4)
// ============================================================================
HelpDocs.content['export-filters'] = {
    title: 'Export Filters & Preview',
    subtitle: 'Control exactly what gets exported',
    html: `
<h2><i data-lucide="sliders-horizontal"></i> Filter Panel</h2>
<p>Click the <strong>Filter Issues</strong> header in the export modal to expand the filter panel. Two filter types are available:</p>

<h3>Severity Filters</h3>
<p>Click severity chips (Critical, High, Medium, Low, Info) to include only those severities. Active chips are highlighted with the severity color. Multiple selections are combined with OR logic.</p>

<h3>Category Filters</h3>
<p>Click category chips to include only specific checker categories. Each chip shows the issue count. Categories are sorted by count (most issues first).</p>

<h2><i data-lucide="eye"></i> Live Preview</h2>
<p>When any filter is active, a gold-bordered preview bar appears showing the exact number of issues that will be exported. This updates in real-time as you toggle filters.</p>

<h2><i data-lucide="x-circle"></i> Clear Filters</h2>
<p>Click <strong>Clear Filters</strong> in the preview bar to deselect all filters and return to exporting all issues (based on the selected export mode).</p>

<h2><i data-lucide="layers"></i> Filter Stacking</h2>
<p>Export filters stack on top of the export mode:</p>
<ol>
    <li>Export mode selects the base set (All, Filtered, or Selected)</li>
    <li>Severity filters narrow to matching severities</li>
    <li>Category filters further narrow to matching categories</li>
</ol>
<p>For example: Mode = "Filtered" + Severity = "Critical" exports only Critical issues from the currently filtered results.</p>
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
    <div class="help-feature-card">
        <div class="help-feature-icon"><i data-lucide="users"></i></div>
        <h3>Reviewer/Owner Mode</h3>
        <p>Toggle between Doc Owner (applies Track Changes) and Reviewer (adds recommendation comments only). Your role persists across sessions.</p>
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
    <li><strong>Choose Your Role</strong> — Use the <strong>Role:</strong> dropdown to select <strong>Doc Owner</strong> (you will apply changes) or <strong>Reviewer</strong> (you will add comments only)</li>
    <li><strong>Review Fixes</strong> — Each fix shows the issue, suggested change, and confidence level</li>
    <li><strong>Make Decisions</strong> — Accept, Reject, or Skip each fix</li>
    <li><strong>Add Notes</strong> — Optionally add reviewer notes to rejected fixes</li>
    <li><strong>Export</strong> — Download with tracked changes (Owner) or recommendation comments (Reviewer)</li>
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

<h3>Review Role Mode</h3>
<p>Before exporting, choose your review role using the <strong>Role:</strong> dropdown in the Fix Assistant header:</p>
<table class="help-table">
    <thead><tr><th>Action</th><th>Doc Owner</th><th>Reviewer</th></tr></thead>
    <tbody>
        <tr><td><strong>Accept</strong></td><td>Physical text change (Track Changes)</td><td>Recommendation comment (no text change)</td></tr>
        <tr><td><strong>Reject</strong></td><td>Comment noting rejection</td><td>No action (skipped)</td></tr>
        <tr><td><strong>Pending</strong></td><td>Left unchanged</td><td>Left unchanged</td></tr>
    </tbody>
</table>
<p>Your role selection is remembered across sessions.</p>

<h3>Word Document with Tracked Changes (Doc Owner)</h3>
<p>Exports a .docx file where:</p>
<ul>
    <li><strong>Accepted fixes</strong> → Applied as tracked changes (insertions/deletions)</li>
    <li><strong>Rejected fixes</strong> → Inserted as comments with your reviewer notes</li>
    <li>Original formatting preserved</li>
</ul>

<h3>Word Document with Comments (Reviewer)</h3>
<p>When in Reviewer mode, exports a .docx file where:</p>
<ul>
    <li><strong>Accepted fixes</strong> → Added as recommendation comments (no text changes)</li>
    <li><strong>Rejected fixes</strong> → Skipped entirely (no comments or changes)</li>
    <li>The document author retains full control over text modifications</li>
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
<p>Export validated hyperlinks with color-coded status highlighting:</p>
<ul>
    <li><strong>Export Highlighted Excel (v5.9.33)</strong> — Multi-color row highlighting by validation status:
        <ul>
            <li><span style="color:#006100;background:#C6EFCE;padding:0 4px;border-radius:3px">Green</span> — Link verified working (HTTP 200)</li>
            <li><span style="color:#7D6608;background:#FFF2CC;padding:0 4px;border-radius:3px">Yellow</span> — SSL warning or redirect issue</li>
            <li><span style="color:#974706;background:#FCE4D6;padding:0 4px;border-radius:3px">Orange</span> — Auth required or blocked by firewall</li>
            <li><span style="color:#C00000;background:#FFC7CE;padding:0 4px;border-radius:3px">Red</span> — Broken, timeout, DNS failed, or SSL error</li>
            <li><span style="color:#808080;background:#F2F2F2;padding:0 4px;border-radius:3px">Grey</span> — No URL in row (not tested)</li>
        </ul>
        Adds "Link Status" and "Link Details" columns plus a Summary sheet with counts and color legend.
    </li>
    <li><strong>Export Highlighted DOCX</strong> — Broken links marked in red/yellow with strikethrough</li>
    <li><strong>CSV Export</strong> — Full results table for spreadsheet analysis</li>
</ul>
<p>The "Export Highlighted" button appears after validation completes. Every row with a URL gets color-coded by its validation status.</p>

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
// PROPOSAL COMPARE - OVERVIEW
// ============================================================================
HelpDocs.content['pc-overview'] = {
    title: 'Proposal Compare',
    subtitle: 'Compare vendor proposals side-by-side',
    html: `
<div class="help-hero help-hero-compact">
    <div class="help-hero-icon"><i data-lucide="git-compare-arrows" class="hero-icon-main"></i></div>
    <div class="help-hero-content">
        <p>Proposal Compare extracts financial data from vendor proposals and displays them in a side-by-side comparison matrix. Upload 2 to 10 proposals in any mix of DOCX, PDF, or Excel formats and instantly see cost breakdowns, line-item variances, and category totals.</p>
    </div>
</div>

<h2><i data-lucide="shield-check"></i> Pure Extraction — No AI</h2>
<p>Proposal Compare uses <strong>deterministic extraction only</strong>. Every number, line item, and total displayed comes directly from your documents. There is no AI summarization, no LLM interpretation, and no generated content. What you see is exactly what was found in the files.</p>

<h2><i data-lucide="file-type"></i> Supported Formats</h2>
<div class="help-formats" style="margin-bottom: 16px;">
    <span class="format-badge format-primary">.xlsx / .xls (Excel)</span>
    <span class="format-badge format-primary">.docx (Word)</span>
    <span class="format-badge format-primary">.pdf</span>
</div>
<p>Excel files provide the richest extraction since financial data is already in structured tables. Word and PDF files are parsed for embedded tables and dollar amounts.</p>

<h2><i data-lucide="list-checks"></i> What Gets Extracted</h2>
<ul>
    <li><strong>Company name</strong> — Detected from headers, cover pages, and metadata</li>
    <li><strong>Dollar amounts</strong> — All currency values found in the document</li>
    <li><strong>Line items</strong> — Description, amount, quantity, unit price from financial tables</li>
    <li><strong>Tables</strong> — All tables with financial data are detected and preserved</li>
    <li><strong>Grand total</strong> — Identified from total/sum rows or computed from line items</li>
    <li><strong>Categories</strong> — Line items classified into 11 categories: Labor, Material, Software, License, Travel, Training, ODC, Subcontract, Overhead, Fee, or Other</li>
    <li><strong>Contract term</strong> — Period extracted (e.g., "3 Year", "Base + 4 Options") from text and sheet tabs</li>
    <li><strong>Indirect rates</strong> — Fringe, overhead, G&amp;A, and fee/profit detected and flagged if outside typical ranges</li>
</ul>

<h2><i data-lucide="target"></i> Quick Start</h2>
<ol>
    <li>Click <strong>Proposal Compare</strong> on the dashboard or sidebar</li>
    <li>Drag and drop 2+ proposal files (or click Browse)</li>
    <li>Click <strong>Extract Data</strong> to parse all files</li>
    <li>In the <strong>Review phase</strong>, verify company names, dates, totals, and line items — edit anything that was misdetected</li>
    <li>Click <strong>Compare Proposals</strong> to generate the comparison</li>
    <li>Use 8 tabs to explore results: Executive Summary, Comparison, Categories, Red Flags, Heatmap, Vendor Scores, Details, and Raw Tables</li>
    <li>Click <strong>Back to Review</strong> to adjust metadata, or export as <strong>XLSX</strong> (8-sheet workbook) or <strong>Interactive HTML</strong> (standalone browser report)</li>
    <li>All comparisons are auto-saved — click <strong>History</strong> on the upload screen to reload past analyses</li>
</ol>

<h2><i data-lucide="brain"></i> Universal Learning System (v5.9.50)</h2>
<p>AEGIS <strong>learns from your behavior across all modules</strong> and gets smarter every time you use it. Every correction, adjudication decision, and exclusion is saved locally so future sessions benefit from your expertise.</p>

<div class="help-callout help-callout-info">
    <i data-lucide="shield-check"></i>
    <div>
        <strong>100% Local — Never Uploaded</strong>
        <p>All learned patterns stay on your machine in local JSON files. Nothing is sent to any server, cloud service, or third party. Your data is your data.</p>
    </div>
</div>

<h3>What Each Module Learns</h3>

<h4>Proposal Compare (<code>parser_patterns.json</code>)</h4>
<ul>
    <li><strong>Category corrections</strong> — When you change a line item category, the keywords are saved. After 2 corrections, future files auto-categorize matching items.</li>
    <li><strong>Company name patterns</strong> — Filename-to-company mappings from your corrections.</li>
    <li><strong>Financial table headers</strong> — Header signatures from verified tables are auto-detected in future parses.</li>
</ul>

<h4>Document Review (<code>review_patterns.json</code>)</h4>
<ul>
    <li><strong>Dismissed categories</strong> — Issue categories you consistently ignore get auto-downgraded to Info severity.</li>
    <li><strong>Fix patterns</strong> — Recurring Fix Assistant corrections are remembered for future suggestions.</li>
    <li><strong>Severity overrides</strong> — When you treat a Warning as Info for certain doc types, that preference is learned.</li>
</ul>

<h4>Statement Forge (<code>statement_patterns.json</code>)</h4>
<ul>
    <li><strong>Directive corrections</strong> — When you change "should" to "shall" for similar statements, future extractions apply the correction automatically.</li>
    <li><strong>Role assignments</strong> — Consistent role assignments to similar statement types are remembered.</li>
    <li><strong>Deletion patterns</strong> — Extraction artifacts you consistently delete are auto-skipped (requires 3+ deletions for safety).</li>
</ul>

<h4>Roles Adjudication (<code>roles_patterns.json</code>)</h4>
<ul>
    <li><strong>Category patterns</strong> — Role name keywords that predict categories (e.g., "engineer" → Engineering).</li>
    <li><strong>Deliverable patterns</strong> — Keywords that predict deliverable vs non-deliverable roles.</li>
    <li><strong>Disposition patterns</strong> — Role name patterns that predict confirmed/rejected status.</li>
    <li><strong>Role type patterns</strong> — Keywords that predict person/tool/process/document role types.</li>
</ul>

<h4>Hyperlink Validator (<code>hv_patterns.json</code>)</h4>
<ul>
    <li><strong>Status overrides</strong> — Domains where you override AUTH_REQUIRED to WORKING are trusted in future scans.</li>
    <li><strong>Trusted domains</strong> — Domains you mark as working despite validation failures.</li>
    <li><strong>Headless-required domains</strong> — Domains recovered by Deep Validate are auto-prioritized for headless validation.</li>
    <li><strong>Exclusion domains</strong> — Frequently excluded domains are suggested for auto-exclusion.</li>
</ul>

<h3>How It Works</h3>
<ol>
    <li>Use AEGIS as normal — review documents, adjudicate roles, validate links, compare proposals</li>
    <li>Make corrections when AEGIS gets something wrong (edit statements, change categories, override statuses)</li>
    <li>Patterns are saved automatically — no extra steps needed</li>
    <li>Next time you use the same module, learned patterns are applied before hardcoded defaults</li>
    <li>Check learning stats via <strong>GET /api/learning/stats</strong> to see pattern counts across all modules</li>
</ol>
<p><strong>Safety threshold</strong>: Learned patterns only activate after being confirmed <strong>at least twice</strong> (3 times for deletion patterns). A single correction won't change future behavior — this prevents accidental learning from one-off mistakes.</p>

<h3>Managing Learning Data (v5.9.52)</h3>
<p>Open <strong>Settings → Learning</strong> tab to manage the Pattern Learning system:</p>
<ul>
    <li><strong>Enable/Disable toggle</strong> — Turn pattern learning on or off globally. When disabled, no new patterns are recorded but existing patterns still apply.</li>
    <li><strong>Module cards</strong> — Each of the 5 modules shows pattern count, last learned date, and action buttons.</li>
    <li><strong>View Patterns</strong> — Opens a read-only JSON viewer showing exactly what AEGIS has learned for that module.</li>
    <li><strong>Export</strong> — Downloads the pattern file as JSON for backup or sharing.</li>
    <li><strong>Clear</strong> — Removes all learned patterns for a specific module (with confirmation).</li>
    <li><strong>Export All</strong> — Downloads a combined JSON of all 5 modules' patterns.</li>
    <li><strong>Clear All</strong> — Removes ALL learned patterns across every module (double confirmation required).</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="play-circle"></i>
    <div>
        <strong>Watch the Demo</strong>
        <p>Click the <strong>?</strong> beacon → Settings → Watch Demo → <strong>Learning System</strong> for a narrated walkthrough of all five learning modules with pre-generated voice narration.</p>
    </div>
</div>
`
};

// ============================================================================
// PROPOSAL COMPARE - UPLOADING
// ============================================================================
HelpDocs.content['pc-uploading'] = {
    title: 'Uploading Proposals',
    subtitle: 'Preparing files for comparison',
    html: `
<h2><i data-lucide="upload"></i> Upload Methods</h2>
<ul>
    <li><strong>Drag & Drop</strong> — Drop files directly onto the upload zone</li>
    <li><strong>Browse Files</strong> — Click the browse button to select files</li>
</ul>

<h2><i data-lucide="info"></i> Upload Limits</h2>
<table class="help-table">
    <thead><tr><th>Limit</th><th>Value</th></tr></thead>
    <tbody>
        <tr><td>Minimum files</td><td>2 (need at least 2 to compare)</td></tr>
        <tr><td>Maximum files</td><td>10 per upload</td></tr>
        <tr><td>Supported types</td><td>.docx, .pdf, .xlsx, .xls</td></tr>
    </tbody>
</table>

<h2><i data-lucide="cpu"></i> Extraction Process</h2>
<p>After uploading, click <strong>Extract Data</strong>. Each file is processed:</p>
<ol>
    <li><strong>Excel files</strong> — All sheets scanned for tables with financial data (dollar amounts, quantity columns)</li>
    <li><strong>Word files</strong> — Tables extracted via python-docx, text scanned for dollar amounts and company names</li>
    <li><strong>PDF files</strong> — Multi-strategy table extraction via EnhancedTableExtractor (camelot, pdfplumber, tabula) with data-pattern column inference for headerless tables</li>
</ol>
<p>Per-file status indicators show success or failure. Files that fail extraction can be removed and re-uploaded.</p>

<h2><i data-lucide="edit-3"></i> Review & Edit</h2>
<p>After extraction, each proposal is shown as a card with:</p>
<ul>
    <li><strong>Company name</strong> — Editable if auto-detection was incorrect</li>
    <li><strong>File type and table count</strong></li>
    <li><strong>Line items found</strong></li>
    <li><strong>Detected grand total</strong></li>
    <li><strong>Extraction notes</strong> — Any warnings or observations</li>
</ul>
<p>Edit company names before comparing to ensure clear labeling in the comparison matrix.</p>

<h2><i data-lucide="copy-check"></i> Duplicate Detection (v6.0.4)</h2>
<p>AEGIS detects duplicate proposals at two stages to prevent double-counting:</p>
<ol>
    <li><strong>File-Level (on upload)</strong> — When adding files, AEGIS checks filenames against already-extracted proposals. Duplicates trigger a prompt: <em>replace existing</em> or <em>keep existing</em></li>
    <li><strong>Post-Extraction (project check)</strong> — After extraction, new proposals are checked against proposals already in the selected project by company name and filename. Duplicates show total amounts for comparison before you choose to replace or keep</li>
</ol>
<p>Both checks use case-insensitive matching. This prevents inflated totals when re-uploading corrected proposals or adding files to an existing project.</p>
`
};

// ============================================================================
// PROPOSAL COMPARE - REVIEW & EDIT
// ============================================================================
HelpDocs.content['pc-review'] = {
    title: 'Review & Edit',
    subtitle: 'Split-pane document viewer with editable metadata',
    html: `
<h2><i data-lucide="pencil"></i> The Review Phase</h2>
<p>After extraction, AEGIS enters the <strong>Review phase</strong> — a split-pane view where you verify and correct all metadata before running the comparison. One proposal is shown at a time with previous/next navigation.</p>

<h2><i data-lucide="file-text"></i> Document Viewer (Left Panel)</h2>
<p>The left panel renders the source document:</p>
<ul>
    <li><strong>PDF files</strong> — Rendered inline via PDF.js at high DPI with zoom controls and optional magnifier loupe</li>
    <li><strong>DOCX files</strong> — Shows extracted text content in a scrollable panel</li>
    <li><strong>Excel files</strong> — Displays parsed tables as formatted HTML tables</li>
</ul>
<p>Use the document viewer to cross-reference extracted data with the original source.</p>

<h3><i data-lucide="zoom-in"></i> PDF Zoom Controls (v6.0.4)</h3>
<p>PDF documents display a zoom toolbar above the page view:</p>
<ul>
    <li><strong>Zoom In / Out</strong> — Increase or decrease scale in 25% increments (range: 50%–300%). Zoom preserves the viewport center so your focus point stays in view</li>
    <li><strong>Fit Width</strong> — Auto-scales to fill the viewer panel width. PDFs now auto-fit on initial render</li>
    <li><strong>Click-and-Drag Panning</strong> — When zoomed in, click and drag the PDF to scroll in any direction. A grab cursor indicates when panning is available</li>
    <li><strong>Magnifier</strong> — Toggle a 3× zoom loupe that follows your cursor over the PDF. Ideal for reading small or scanned text</li>
</ul>
<p>All rendering uses HiDPI/Retina-aware canvas sizing for crisp text on high-resolution displays.</p>

<h2><i data-lucide="edit-3"></i> Metadata Editor (Right Panel)</h2>
<p>Editable fields for each proposal:</p>
<table class="help-table">
    <thead><tr><th>Field</th><th>Description</th></tr></thead>
    <tbody>
        <tr><td>Company Name</td><td>Vendor/supplier name — pre-filled from extraction, editable</td></tr>
        <tr><td>Date</td><td>Proposal date — pre-filled if detected, editable</td></tr>
        <tr><td>Total Amount</td><td>Grand total — pre-filled from extraction, editable (accepts $1,234.56 format)</td></tr>
    </tbody>
</table>

<h2><i data-lucide="list"></i> Line Item Editor</h2>
<p>Click <strong>Edit Line Items</strong> to expand the accordion editor:</p>
<ul>
    <li>Each row shows description, category dropdown, amount, quantity, and unit price</li>
    <li>Change the <strong>category</strong> (Labor, Material, Software, License, Travel, Training, ODC, Subcontract, Overhead, Fee, Other)</li>
    <li>Click the <strong>× button</strong> to delete a line item</li>
    <li>Click <strong>+ Add Line Item</strong> to add a new empty row</li>
</ul>
<p>Edits are saved automatically when you navigate between proposals or click Compare.</p>

<h2><i data-lucide="check-circle"></i> Quality Indicators (v5.9.42)</h2>
<p>Each proposal in the review phase shows status badges below the header:</p>
<ul>
    <li><span style="color:#4caf50">✓</span> <strong>Green badges</strong> — Company detected, line items found, total identified, contract term extracted</li>
    <li><span style="color:#ff9800">⚠</span> <strong>Amber badges</strong> — Missing company name, no line items, no total, or no term detected</li>
</ul>
<p>Use these badges to quickly spot extraction gaps and fix them before comparing.</p>

<h2><i data-lucide="folder"></i> Project Selector (v5.9.42)</h2>
<p>A compact project dropdown appears at the top of the review phase. Select or change the project that proposals belong to — this associates the upcoming comparison with that project. You can also create new projects from the upload phase.</p>

<h2><i data-lucide="eye"></i> Comparison Preview (v5.9.42)</h2>
<p>Before clicking Compare, a preview card below the editor shows:</p>
<ul>
    <li><strong>Proposals ready</strong> — Count and vendor names</li>
    <li><strong>Total line items</strong> across all proposals</li>
    <li><strong>Warnings</strong> — If any proposal has zero line items</li>
    <li><strong>Ready indicator</strong> — Green check when all data looks good to compare</li>
</ul>

<h2><i data-lucide="arrow-right"></i> Navigation</h2>
<p>Use <strong>← Previous</strong> and <strong>Next →</strong> buttons to navigate between proposals. The counter shows "1 of 3" etc. Edits to the current proposal are captured before navigating.</p>
<p>Click <strong>Compare Proposals</strong> when all proposals look correct.</p>

<h2><i data-lucide="alert-triangle"></i> Pre-Comparison Validation (v5.9.45)</h2>
<p>Before the comparison runs, AEGIS checks for potential data issues and displays a warning dialog if any are found:</p>
<ul>
    <li><strong>Fewer than 2 proposals</strong> — At least 2 are required for a meaningful comparison</li>
    <li><strong>Empty line items</strong> — Proposals with zero extracted line items may need re-extraction or manual entry</li>
    <li><strong>Missing company names</strong> — Vendor identification is critical for clear comparison results</li>
    <li><strong>Duplicate vendor names</strong> — Two proposals with the same company name (case-insensitive) may cause confusion unless they represent different contract terms</li>
    <li><strong>Very low item counts</strong> — Proposals with fewer than 3 line items may have incomplete extraction</li>
</ul>
<p>You can proceed despite warnings — click <strong>OK</strong> to continue or <strong>Cancel</strong> to return and fix the issues first.</p>
`
};

// ============================================================================
// PROPOSAL COMPARE - COMPARISON VIEW
// ============================================================================
HelpDocs.content['pc-comparison'] = {
    title: 'Comparison View',
    subtitle: 'Reading the side-by-side matrix',
    html: `
<h2><i data-lucide="columns"></i> Comparison Matrix</h2>
<p>The main comparison view shows a table with:</p>
<ul>
    <li><strong>Rows</strong> — One per aligned line item across proposals</li>
    <li><strong>Columns</strong> — One per vendor/proposal, plus Description and Variance</li>
    <li><strong>Green cells</strong> — Lowest cost for that line item</li>
    <li><strong>Red cells</strong> — Highest cost for that line item</li>
    <li><strong>Dash (—)</strong> — Item not found in that proposal</li>
</ul>

<h2><i data-lucide="git-merge"></i> Line Item Alignment</h2>
<p>The comparison engine uses text similarity matching to align line items across different proposals. Items with similar descriptions are placed on the same row, even if wording differs slightly between vendors. The matching considers:</p>
<ul>
    <li>Description text similarity (fuzzy matching)</li>
    <li>Word overlap between descriptions</li>
    <li>Category matching (Labor, Material, etc.)</li>
</ul>
<p>Unmatched items appear as separate rows with dashes for proposals that don't have them.</p>

<h2><i data-lucide="percent"></i> Variance Column</h2>
<p>The rightmost column shows variance percentage — the spread between the lowest and highest amounts for each line item. Higher variance indicates greater disagreement between vendors on that cost.</p>

<h2><i data-lucide="arrow-up-down"></i> Sort & Filter</h2>
<p>The comparison table is fully interactive:</p>
<ul>
    <li><strong>Sort by any column</strong> — Click any column header to sort ascending/descending. Sort by description, any vendor's amounts, or variance percentage</li>
    <li><strong>Filter by category</strong> — Use the category dropdown to show only Labor, Material, Travel, etc.</li>
    <li><strong>Filter by variance</strong> — Show only items with variance above a threshold (10%, 20%, or 50%) to focus on biggest price differences</li>
    <li><strong>Item count</strong> — The filter bar shows how many items match the current filters</li>
</ul>

<h2><i data-lucide="calendar-range"></i> Multi-Term Comparison (v5.9.46)</h2>
<p>When proposals have different contract terms (e.g., "3 Year", "5 Year"), AEGIS automatically detects the groups and runs <strong>separate comparisons per term</strong>. This ensures vendors are only compared against others bidding for the same contract period.</p>
<ul>
    <li><strong>Automatic detection</strong> — If 2+ distinct contract terms are found, each with 2+ proposals, multi-term mode activates automatically</li>
    <li><strong>Term selector bar</strong> — Gold pill-based selector above the 8 result tabs lets you switch between terms</li>
    <li><strong>All Terms Summary</strong> — Cross-term overview table showing every vendor's total per term, with green badges highlighting the lowest-cost term per vendor and a vendor presence matrix</li>
    <li><strong>Single-vendor exclusions</strong> — Term groups with only one vendor are excluded (need 2+ to compare) with a visible notice</li>
    <li><strong>Set terms in Review</strong> — The "Contract Term" field in the review phase is auto-extracted from documents and can be edited manually. Use values like "3 Year", "5 Year", "Base + 4 Options", etc.</li>
</ul>

<h2><i data-lucide="layout-grid"></i> Result Tabs</h2>
<table class="help-table">
    <thead><tr><th>Tab</th><th>Shows</th></tr></thead>
    <tbody>
        <tr><td><strong>Executive Summary</strong></td><td>Hero stats, price rankings, score rankings, key findings, negotiation opportunities</td></tr>
        <tr><td><strong>Comparison</strong></td><td>Side-by-side line item matrix with color coding</td></tr>
        <tr><td><strong>Categories</strong></td><td>Cost summaries grouped by category with grouped bar chart (one bar per vendor, not stacked) showing lowest in green and highest in red</td></tr>
        <tr><td><strong>Red Flags</strong></td><td>Automated risk checks per vendor — critical, warning, and info severity</td></tr>
        <tr><td><strong>Heatmap</strong></td><td>Color-coded deviation from average for each line item per vendor</td></tr>
        <tr><td><strong>Vendor Scores</strong></td><td>Overall scores, letter grades, and component breakdowns (Price, Completeness, Risk, Data Quality)</td></tr>
        <tr><td><strong>Details</strong></td><td>Per-proposal metadata — company, date, file type, totals</td></tr>
        <tr><td><strong>Raw Tables</strong></td><td>Original extracted tables from each document</td></tr>
    </tbody>
</table>
`
};

// ============================================================================
// PROPOSAL COMPARE - ANALYTICS TABS
// ============================================================================
HelpDocs.content['pc-analytics'] = {
    title: 'Analytics Tabs',
    subtitle: 'Executive summary, red flags, heatmap, and vendor scores',
    html: `
<h2><i data-lucide="trophy"></i> Executive Summary</h2>
<p>The first tab shown after comparison. Displays hero stat cards (line items compared, vendor count, red flags, potential savings), price ranking with gold/silver/bronze medals, overall score ranking, key findings with severity badges, and a negotiation opportunities table.</p>
<p>A <strong>tornado chart</strong> visualizes the biggest price spreads across vendors — horizontal bars sorted by spread, colored by variance intensity (red &gt;50%, orange &gt;25%, gold default). This highlights where negotiation effort will have the greatest financial impact.</p>

<h2><i data-lucide="shield-alert"></i> Red Flags</h2>
<p>Automated risk checks run on each vendor's data. Flags are categorized by severity:</p>
<table class="help-table">
    <thead><tr><th>Severity</th><th>Meaning</th></tr></thead>
    <tbody>
        <tr><td><span style="color:#f44336;font-weight:700">CRITICAL</span></td><td>Serious pricing anomalies, missing major line items, or unusually high costs</td></tr>
        <tr><td><span style="color:#ff9800;font-weight:700">WARNING</span></td><td>Notable deviations, incomplete data, or unusual patterns worth investigating</td></tr>
        <tr><td><span style="color:#2196f3;font-weight:700">INFO</span></td><td>Observations and data quality notes for awareness</td></tr>
    </tbody>
</table>
<p>Red flag checks include: rate anomalies, missing data, cost outliers, <strong>identical pricing</strong> between vendors (possible collusion indicator), <strong>missing categories</strong> (scope gaps where a vendor omits entire cost categories others include), and <strong>FAR 15.404 price reasonableness</strong> (statistical z-score outliers more than 2 standard deviations from the group mean).</p>

<h2><i data-lucide="grid-3x3"></i> Heatmap</h2>
<p>A color-coded table showing how each vendor's line item amounts deviate from the group average. Colors range from dark green (significantly below average) through neutral (within 5%) to red (significantly above average). Grey cells indicate missing data. Items with only one vendor show "only vendor" with a distinctive neutral color (v5.9.45).</p>
<p>The legend dynamically adapts to dark mode using runtime color functions. Seven deviation levels are shown: very low (&lt; -15%), low (-15% to -5%), neutral (-5% to +5%), high (+5% to +15%), very high (&gt; +15%), Only Vendor (single quote), and Missing (no data).</p>

<h2><i data-lucide="bar-chart-3"></i> Vendor Scores</h2>
<p>Each vendor receives an overall score (0-100) and letter grade (A-F) based on four weighted components:</p>
<table class="help-table">
    <thead><tr><th>Component</th><th>Weight</th><th>Measures</th></tr></thead>
    <tbody>
        <tr><td><strong>Price</strong></td><td>40%</td><td>Cost competitiveness relative to other vendors</td></tr>
        <tr><td><strong>Completeness</strong></td><td>25%</td><td>How many line items the vendor quoted vs total across all vendors</td></tr>
        <tr><td><strong>Risk</strong></td><td>25%</td><td>Inverse of red flag count and severity</td></tr>
        <tr><td><strong>Data Quality</strong></td><td>10%</td><td>Extraction confidence and data consistency</td></tr>
    </tbody>
</table>
<p>If Chart.js is loaded, a radar/spider chart overlays all vendors on one plot and a grouped bar chart shows component scores side by side. The radar chart uses suggestedMax scaling with clean point labels (v5.9.45). Score bars show "N/A" with muted fill for zero-value scores. Vendor names in charts are truncated at 25 characters with full names shown on hover.</p>

<h2><i data-lucide="sliders-horizontal"></i> Evaluation Weight Sliders</h2>
<p>Below the vendor score cards, four sliders let you adjust the evaluation weights in real-time:</p>
<ul>
    <li>Drag any slider to change its weight (0-100% in 5% increments)</li>
    <li>The total display turns green at 100% and red otherwise</li>
    <li>Vendor scores, letter grades, and rankings recalculate instantly as you adjust</li>
    <li>Click <strong>Reset</strong> to restore the default weights (Price 40%, Completeness 25%, Risk 25%, Data Quality 10%)</li>
</ul>

<h2><i data-lucide="folder-open"></i> Project Management</h2>
<p>On the upload screen, use the project selector to group proposals into named projects. Create a new project with the folder-plus button. When a project is selected, its existing proposals are shown below the selector and count toward the comparison minimum (2 proposals). This lets you add new proposals to a previous comparison session.</p>

<h2><i data-lucide="bar-chart-3"></i> Metrics & Analytics Integration</h2>
<p>The <strong>Proposals</strong> tab in the Metrics & Analytics dashboard (v5.9.40) shows aggregated data across all your proposal comparison projects:</p>
<ul>
    <li><strong>Hero Stats</strong> — Total projects, proposals, line items, and total value analyzed</li>
    <li><strong>Value Distribution</strong> — Bar chart of average proposal values per vendor</li>
    <li><strong>File Types</strong> — Doughnut chart showing DOCX/PDF/XLSX breakdown</li>
    <li><strong>Top Vendors</strong> — Horizontal bar chart of vendors by proposal frequency</li>
    <li><strong>Line Item Categories</strong> — Doughnut chart of category distribution across all proposals</li>
    <li><strong>Recent Activity</strong> — Sortable table of latest proposals with drill-down to vendor details</li>
</ul>
<p>Data is loaded lazily when you switch to the Proposals tab and cached for 5 minutes. Click <strong>Refresh</strong> to force a data reload.</p>
`
};

// ============================================================================
// PROPOSAL COMPARE - HISTORY
// ============================================================================
HelpDocs.content['pc-history'] = {
    title: 'Comparison History',
    subtitle: 'Browse, reload, and manage past comparisons',
    html: `
<h2><i data-lucide="history"></i> Auto-Save</h2>
<p>Every comparison you run is <strong>automatically saved</strong> to history. No manual save step is required — results are persisted the moment the comparison completes.</p>

<h2><i data-lucide="list"></i> Browsing History</h2>
<p>Click the <strong>History</strong> button on the upload screen (top right) to see all past comparisons. Each card shows:</p>
<ul>
    <li><strong>Project name</strong> (or "Ad-hoc Comparison" for unlinked comparisons)</li>
    <li><strong>Vendor names</strong> as gold badges</li>
    <li><strong>Proposal count, cost spread, and date/time</strong></li>
</ul>

<h2><i data-lucide="eye"></i> Reloading Results</h2>
<p>Click <strong>View</strong> on any history card to reload the full comparison with all 8 analysis tabs restored exactly as they were.</p>

<h2><i data-lucide="pencil"></i> Back to Review</h2>
<p>From results (whether freshly compared or loaded from history), click <strong>Back to Review</strong> to return to the split-pane editor. Your original proposals are preserved — adjust metadata or line items, then re-run the comparison.</p>
<p><strong>Note:</strong> Back to Review is only available when proposal data was preserved (fresh comparisons or comparisons saved with proposal input data).</p>

<h2><i data-lucide="trash-2"></i> Deleting Comparisons</h2>
<p>Click the <strong>trash icon</strong> on a history card to delete it permanently. A confirmation dialog prevents accidental deletion.</p>
`
};

// ============================================================================
// PROPOSAL COMPARE - PROJECT DASHBOARD
// ============================================================================
HelpDocs.content['pc-dashboard'] = {
    title: 'Project Dashboard',
    subtitle: 'Organize proposals into projects, browse past work, and edit from a central hub',
    html: `
<h2><i data-lucide="layout-dashboard"></i> Opening the Dashboard</h2>
<p>Click the <strong>Projects</strong> button in the upload phase header to open the Project Dashboard. The dashboard provides a centralized view of all your saved projects and their proposals.</p>

<h2><i data-lucide="grid-2x2"></i> Project Grid View</h2>
<p>Projects are displayed in a <strong>2-column card grid</strong>. Each card shows:</p>
<ul>
    <li><strong>Project name</strong> and description</li>
    <li><strong>Proposal count</strong> — number of proposals attached to the project</li>
    <li><strong>Line items count</strong> — total extracted items across all proposals</li>
    <li><strong>Last updated</strong> — timestamp of most recent activity</li>
</ul>
<p>Click any card to drill into the <strong>Project Detail View</strong>.</p>

<h2><i data-lucide="folder-open"></i> Project Detail View</h2>
<p>The detail view shows everything inside a single project:</p>
<ul>
    <li><strong>Proposals list</strong> — each proposal with vendor name, file type, line item count, and grand total</li>
    <li><strong>Comparisons list</strong> — past comparison runs linked to this project, with date and vendor badges</li>
</ul>
<p>From here you can view comparison results, edit proposals, or move proposals between projects.</p>

<h2><i data-lucide="pencil"></i> Edit from Dashboard</h2>
<p>Click <strong>Edit</strong> on any proposal card to re-enter the split-pane <strong>Review phase</strong> with that proposal loaded. The full document viewer and metadata editor are available. When you finish editing and click <strong>Save &amp; Back</strong>, your changes are automatically persisted to the database.</p>

<h2><i data-lucide="tag"></i> Tag to Project</h2>
<p>Any proposal — whether freshly uploaded or loaded from history — can be assigned to a project via the <strong>Tag to Project</strong> dropdown. Select an existing project from the list, or create a new project on the fly. Proposals that are already in a project can be reassigned to a different one.</p>

<h2><i data-lucide="move"></i> Move Proposals</h2>
<p>To reorganize proposals across projects, use the <strong>Move</strong> action on a proposal card in the detail view. Select the destination project from the dropdown and the proposal is transferred immediately.</p>

<h2><i data-lucide="save"></i> Edit Persistence</h2>
<p>All edits made in the Review phase are <strong>auto-saved</strong> to the database via fire-and-forget writes. You do not need to manually save — changes persist automatically. The in-memory state drives the current session while the database ensures your edits survive across sessions.</p>

<h2><i data-lucide="bar-chart-3"></i> Project Financial Dashboard</h2>
<p>When you open a project (from the dashboard or the <strong>landing page dropdown</strong>), AEGIS displays a <strong>financial summary dashboard</strong> drawn from the latest comparison. The dashboard includes:</p>
<ul>
    <li><strong>Hero stats</strong> — vendor count, total line items, average total, price spread, and risk flag count</li>
    <li><strong>Vendor Overview cards</strong> — each vendor's total amount, line item count, letter grade, overall score, and contract term. The lowest bidder is highlighted with a trophy badge</li>
    <li><strong>Price Range bar</strong> — gradient visualization from min to max with an average marker</li>
    <li><strong>Category Breakdown table</strong> — per-vendor amounts across all cost categories (Labor, Material, Software, etc.)</li>
    <li><strong>Risk Summary pills</strong> — critical, warning, and info flag counts from the last comparison</li>
    <li><strong>Contract Terms</strong> — badge pills showing detected contract periods when multi-term proposals exist</li>
</ul>
<p>Click <strong>View Full Analysis</strong> to load the complete 8-tab comparison results, or <strong>Export Report</strong> to download an interactive HTML report directly from the project view.</p>

<h2><i data-lucide="home"></i> Landing Page Quick Access</h2>
<p>The Proposal Compare tile on the AEGIS landing page includes a <strong>project dropdown</strong>. Select a project and click the gold arrow button to jump directly to the project's financial dashboard — no need to open the full module first.</p>

<div class="help-tip">
    <i data-lucide="lightbulb"></i>
    <span>Use projects to group related proposals (e.g., by contract vehicle, fiscal year, or program). The dashboard makes it easy to revisit and refine past analyses without re-uploading files.</span>
</div>
`
};

// ============================================================================
// PROPOSAL COMPARE - EXPORT
// ============================================================================
HelpDocs.content['pc-export'] = {
    title: 'Exporting Results',
    subtitle: 'Download as Excel workbook or interactive HTML report',
    html: `
<h2><i data-lucide="download"></i> Export Options</h2>
<p>Two export formats are available from the results toolbar:</p>
<ul>
    <li><strong>Export XLSX</strong> — Formatted 8-sheet Excel workbook with conditional formatting and currency styling</li>
    <li><strong>Export Interactive HTML</strong> — Standalone self-contained HTML report with interactive charts, sort/filter, and dark/light mode toggle</li>
</ul>

<h2><i data-lucide="file-spreadsheet"></i> Excel Export (8 Sheets)</h2>
<p>The XLSX workbook contains 8 sheets with full AEGIS gold/navy branding:</p>

<table class="help-table">
    <thead><tr><th>Sheet</th><th>Contents</th></tr></thead>
    <tbody>
        <tr><td><strong>1. Executive Summary</strong></td><td>Vendor rankings, scores with letter-grade coloring (A=green, F=red), key findings, metadata</td></tr>
        <tr><td><strong>2. Comparison Matrix</strong></td><td>Side-by-side line items with green (lowest) and red (highest) conditional fills, variance column, frozen panes, auto-filter</td></tr>
        <tr><td><strong>3. Category Breakdown</strong></td><td>Costs grouped by category (Labor, Material, Software, License, etc.) with item counts and per-vendor totals</td></tr>
        <tr><td><strong>4. Red Flags</strong></td><td>Risk findings per vendor with severity icons and descriptions</td></tr>
        <tr><td><strong>5. Vendor Scores</strong></td><td>Letter grades with component scores (Price, Completeness, Risk, Data Quality)</td></tr>
        <tr><td><strong>6. Heatmap</strong></td><td>Category × Vendor grid with conditional fills — green (below avg), white (neutral), red (above avg)</td></tr>
        <tr><td><strong>7. Rate Analysis</strong></td><td>Indirect rates (OH, G&amp;A, Fringe, Fee) per vendor with typical ranges and flagged outliers</td></tr>
        <tr><td><strong>8. Raw Line Items</strong></td><td>All extracted line items per vendor — description, category, amount, quantity, unit price, source sheet — with auto-filter</td></tr>
    </tbody>
</table>
<p>All dollar amounts use <code>$#,##0.00</code> formatting throughout.</p>

<h2><i data-lucide="globe"></i> Interactive HTML Export (v5.9.42)</h2>
<p>Click <strong>Export Interactive HTML</strong> to download a <em>completely self-contained</em> HTML file — no external dependencies, no internet required. Open it in any browser for a full interactive report.</p>
<p>Features include:</p>
<ul>
    <li><strong>Tab navigation</strong> — Executive Dashboard, Comparison Matrix, Category Analysis, Vendor Scorecard, Risk Analysis</li>
    <li><strong>SVG charts</strong> — Tornado chart, stacked bars, donut/pie, radar — all inline SVG (no Chart.js dependency)</li>
    <li><strong>Sort &amp; filter</strong> — Click column headers to sort the comparison table, filter by category or variance</li>
    <li><strong>Dark / Light toggle</strong> — Switch between themes, persisted via localStorage</li>
    <li><strong>Animated count-up</strong> — Hero stat numbers animate on page load</li>
    <li><strong>Print-optimized</strong> — <code>@media print</code> rules hide navigation, show all sections linearly</li>
    <li><strong>AEGIS branding</strong> — Gold (#D6A84A) and dark navy (#1B2838) palette throughout</li>
</ul>
<p>The HTML file is typically 150-400 KB depending on line item count — small enough to email as an attachment.</p>

<div class="help-tip">
    <i data-lucide="lightbulb"></i>
    <span>Both exports include all comparison data. Use XLSX for stakeholders who prefer Excel; use HTML for browser-based presentations or email distribution.</span>
</div>
`
};

// ============================================================================
// PROPOSAL COMPARE - STRUCTURE ANALYZER
// ============================================================================
HelpDocs.content['pc-structure'] = {
    title: 'Structure Analyzer',
    subtitle: 'Privacy-safe parsing diagnostics for accuracy refinement',
    html: `
<h2><i data-lucide="file-search"></i> What Is Structure Analysis? (v5.9.48)</h2>
<p>The <strong>Analyze Structure</strong> button in the upload phase parses your selected proposals and produces a <em>privacy-safe structural report</em> that reveals how the parser interpreted each document &mdash; without exposing any proprietary data.</p>
<p><strong>Batch mode (v5.9.48):</strong> Select multiple files (up to 20) and click once &mdash; a single combined JSON downloads with per-file analysis plus a cross-file summary showing aggregate patterns, common parser issues, and extraction quality comparison.</p>

<h2><i data-lucide="shield-check"></i> What&rsquo;s Redacted</h2>
<table class="help-table">
    <thead><tr><th>Data Type</th><th>Treatment</th></tr></thead>
    <tbody>
        <tr><td><strong>Dollar amounts</strong></td><td>Replaced with bucket labels ($1K-$9.9K, $100K-$999K, etc.)</td></tr>
        <tr><td><strong>Company names</strong></td><td>Completely removed &mdash; only &ldquo;detected: yes/no&rdquo; shown</td></tr>
        <tr><td><strong>Line item descriptions</strong></td><td>Replaced with pattern analysis (length, word count, structural type)</td></tr>
        <tr><td><strong>File paths</strong></td><td>Stripped from error messages</td></tr>
        <tr><td><strong>Dates</strong></td><td>Only &ldquo;detected: yes/no&rdquo; shown</td></tr>
    </tbody>
</table>

<h2><i data-lucide="bar-chart-3"></i> What&rsquo;s Included</h2>
<ul>
    <li><strong>Table shapes</strong> &mdash; Rows x columns, header names (standard financial terms only), whether headers are generic</li>
    <li><strong>Column data patterns</strong> &mdash; Per-column analysis: dominant type (dollar/numeric/text), fill rate, avg text length</li>
    <li><strong>Column role inference</strong> &mdash; Which columns the parser identified as description, amount, quantity, unit price</li>
    <li><strong>Category distribution</strong> &mdash; How many items classified as Labor, Material, Travel, ODC, etc.</li>
    <li><strong>Confidence histogram</strong> &mdash; Distribution of high/medium/low extraction confidence</li>
    <li><strong>Amount bucket distribution</strong> &mdash; How many items fall into each dollar range (without revealing exact values)</li>
    <li><strong>Field coverage</strong> &mdash; Percentage of items with populated description, amount, quantity, unit price, category</li>
    <li><strong>Extraction diagnostics</strong> &mdash; Parser notes, strategy used (EnhancedTableExtractor/pymupdf4llm/pdfplumber), warnings</li>
    <li><strong>Parser suggestions</strong> &mdash; Automated recommendations for improving extraction accuracy</li>
</ul>

<h2><i data-lucide="download"></i> How to Use</h2>
<ol>
    <li>Open Proposal Compare and select (or drag) one or more proposal files</li>
    <li>The button shows the file count: <strong>Analyze Structure (3 files)</strong></li>
    <li>Click the button &mdash; a JSON file downloads automatically</li>
    <li>The JSON is safe to share &mdash; it contains no financial data, company names, or proprietary text</li>
    <li>Share the JSON with the developer to diagnose parsing accuracy issues</li>
</ol>

<h2><i data-lucide="layers"></i> Cross-File Summary (Batch Mode)</h2>
<p>When analyzing multiple files, the report includes a <code>cross_file_summary</code> section with:</p>
<ul>
    <li><strong>Files by type</strong> &mdash; Count of XLSX, DOCX, PDF files analyzed</li>
    <li><strong>Merged category distribution</strong> &mdash; Aggregated Labor, Material, Travel, etc. across all files</li>
    <li><strong>Common parser suggestions</strong> &mdash; Issues appearing in 2+ files (indicates systemic patterns)</li>
    <li><strong>Extraction quality comparison</strong> &mdash; Best/worst file by completeness score</li>
    <li><strong>Column pattern consistency</strong> &mdash; How consistently the parser finds description, amount, quantity columns</li>
</ul>

<div class="help-tip">
    <i data-lucide="lightbulb"></i>
    <span>You can analyze any proposal format (XLSX, DOCX, PDF). The report helps identify why the parser might miss line items, miscategorize costs, or fail to detect totals &mdash; all without revealing the actual proposal content.</span>
</div>
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
// SETTINGS - DIAGNOSTICS (v5.9.20)
// ============================================================================
HelpDocs.content['settings-diagnostics'] = {
    title: 'Diagnostics',
    subtitle: 'System health checks and support tools',
    html: `
<h2><i data-lucide="activity"></i> Health Check</h2>
<p>The Diagnostics tab provides a real-time health overview of AEGIS components: Python version, Flask status, database connectivity, NLP model availability, and disk space usage.</p>

<h2><i data-lucide="mail"></i> Email Diagnostics</h2>
<p>Click <strong>"Email to Support"</strong> to generate a diagnostic report package:</p>
<ul>
    <li>Generates an <strong>.eml file</strong> (RFC 2822 format) that opens in your default email client (Outlook, Apple Mail, Thunderbird)</li>
    <li>The diagnostic JSON report is <strong>pre-attached</strong> — no manual file drag-drop required</li>
    <li>Active log files (<code>aegis.log</code> and other module logs) are also attached automatically</li>
    <li>Double-click the downloaded .eml file to open it as a ready-to-send draft</li>
</ul>

<h2><i data-lucide="file-text"></i> Log Viewer</h2>
<p>View recent log entries directly in the Diagnostics panel. Filter by log level (DEBUG, INFO, WARNING, ERROR) and search for specific messages.</p>

<h2><i data-lucide="download"></i> Export Diagnostic Report</h2>
<p>Download a JSON file containing system information, configuration, database statistics, and recent error logs for offline analysis or archival.</p>
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
// SETTINGS - REVIEW (v5.9.28)
// ============================================================================
HelpDocs.content['settings-review'] = {
    title: 'Review Settings',
    subtitle: 'Configure style guide presets, thresholds, and extraction options',
    html: `
<h2><i data-lucide="book-open"></i> Style Guide Presets</h2>
<p>Choose a writing style guide to auto-configure which checkers run:</p>
<ul>
    <li><strong>Microsoft</strong> — Microsoft Writing Style Guide rules</li>
    <li><strong>Google</strong> — Google Developer Documentation style</li>
    <li><strong>Plain Language</strong> — US Plain Language Guidelines</li>
    <li><strong>ASD-STE100</strong> — Simplified Technical English for aerospace</li>
    <li><strong>Government</strong> — US Government/Federal style</li>
    <li><strong>Aerospace</strong> — Aerospace and defense documentation standards</li>
    <li><strong>All Checks</strong> — Enable every available checker</li>
    <li><strong>Minimal</strong> — Basic grammar and spelling only</li>
</ul>

<h2><i data-lucide="sliders-horizontal"></i> Writing Thresholds</h2>
<ul>
    <li><strong>Max Sentence Length</strong> — Sentences exceeding this word count are flagged (default: 40)</li>
    <li><strong>Passive Voice Threshold</strong> — Strict (flag all), Moderate (allow some), or Lenient (only excessive)</li>
</ul>

<h2><i data-lucide="scan-text"></i> Extraction</h2>
<ul>
    <li><strong>Extract roles and responsibilities</strong> — Automatically identify roles, RACI statements, and organizational references during scans</li>
</ul>
`
};

// ============================================================================
// SETTINGS - NETWORK & AUTH (v5.9.28)
// ============================================================================
HelpDocs.content['settings-network'] = {
    title: 'Network & Authentication',
    subtitle: 'Configure hyperlink validation, certificates, and proxy settings',
    html: `
<h2><i data-lucide="link"></i> Hyperlink Validation Mode</h2>
<ul>
    <li><strong>Offline</strong> — Format validation only, no network access. Checks URL syntax without connecting.</li>
    <li><strong>Validator</strong> — Full HTTP reachability check with authentication support. Supports Windows SSO, CAC/PIV certificates, and proxy servers.</li>
</ul>

<h2><i data-lucide="key"></i> Client Certificates</h2>
<p>For CAC/PIV authentication to .mil and .gov sites:</p>
<ul>
    <li><strong>Certificate File (.pem)</strong> — Path to your client certificate</li>
    <li><strong>Private Key File (.pem)</strong> — Path to the corresponding private key</li>
</ul>
<p>Leave both blank to use Windows SSO (NTLM/Kerberos) only.</p>

<h2><i data-lucide="shield-check"></i> SSL & Proxy</h2>
<ul>
    <li><strong>CA Certificate Bundle</strong> — DoD/Federal PKI root CA bundle for government site validation</li>
    <li><strong>Proxy Server</strong> — Enterprise proxy URL for network-restricted environments (e.g., <code>http://proxy.corp.mil:8080</code>)</li>
    <li><strong>Verify SSL certificates</strong> — Disable only for testing with self-signed certificates</li>
</ul>

<div class="help-callout help-callout-info">
    <i data-lucide="shield"></i>
    <div>
        <strong>Privacy</strong>
        <p>All network traffic stays local to your machine. No data is sent to external servers. Hyperlink validation only checks URL reachability.</p>
    </div>
</div>
`
};

// ============================================================================
// SETTINGS - DOCUMENT PROFILES (v5.9.28)
// ============================================================================
HelpDocs.content['settings-profiles'] = {
    title: 'Document Profiles',
    subtitle: 'Create per-document-type checker configurations that persist across sessions',
    html: `
<h2><i data-lucide="file-check"></i> Document Type Profiles</h2>
<p>Profiles let you save different checker configurations for different document types. Select a profile to see and modify which checkers are active for that document type.</p>
<ul>
    <li><strong>PrOP</strong> — Procedure Operational: focus on process clarity and step-by-step instructions</li>
    <li><strong>PAL</strong> — Process Asset Library: comprehensive document quality checks</li>
    <li><strong>FGOST</strong> — Flight Ground Operations Support Tool: safety-critical documentation checks</li>
    <li><strong>SOW</strong> — Statement of Work: requirements language and compliance focus</li>
</ul>

<h2><i data-lucide="list-checks"></i> Checker Selection</h2>
<p>Each profile has its own set of enabled/disabled checkers organized by category:</p>
<ul>
    <li><strong>Writing Quality</strong> — Passive voice, weak language, wordy phrases, sentence length</li>
    <li><strong>Grammar & Spelling</strong> — Spelling, grammar, punctuation, capitalization</li>
    <li><strong>Technical Writing</strong> — Acronyms, requirements language, TBD items, testability</li>
    <li><strong>Clarity</strong> — Ambiguity, readability, hedging, cliches</li>
    <li><strong>Compliance</strong> — MIL-STD, DO-178, accessibility, cross-references</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Quick Actions</strong>
        <p>Use <strong>Select All</strong>, <strong>Clear All</strong>, or <strong>Reset Default</strong> buttons to quickly configure a profile. Changes are saved when you click Save Settings.</p>
    </div>
</div>
`
};

// ============================================================================
// SETTINGS - DISPLAY (v5.9.28)
// ============================================================================
HelpDocs.content['settings-display'] = {
    title: 'Display Settings',
    subtitle: 'Configure interface layout, modes, and pagination',
    html: `
<h2><i data-lucide="layout-grid"></i> Interface Modes</h2>
<ul>
    <li><strong>Essentials mode</strong> — Hides advanced features (Statement Forge, Roles Studio, Triage, Families, Analytics) for a simpler, cleaner interface</li>
    <li><strong>Compact mode</strong> — Reduces spacing and row heights in the issues table for denser information display</li>
    <li><strong>Expand analytics by default</strong> — Automatically shows the charts and statistics panel after each scan</li>
</ul>

<h2><i data-lucide="list"></i> Pagination</h2>
<ul>
    <li><strong>Issues Per Page</strong> — Choose 25, 50, 100, or All (no pagination) for the review results table</li>
</ul>

<div class="help-callout help-callout-tip">
    <i data-lucide="lightbulb"></i>
    <div>
        <strong>Performance Tip</strong>
        <p>For documents with many issues (500+), use pagination instead of "All" to keep the interface responsive.</p>
    </div>
</div>
`
};

// ============================================================================
// SETTINGS - DATA MANAGEMENT (v5.9.28)
// ============================================================================
HelpDocs.content['settings-data'] = {
    title: 'Data Management',
    subtitle: 'View stored data counts and clear individual data categories',
    html: `
<h2><i data-lucide="database"></i> Stored Data</h2>
<p>View and manage the data AEGIS has accumulated across your scanning sessions:</p>
<ul>
    <li><strong>Scan History</strong> — Past document scan results, scores, and issue details</li>
    <li><strong>Statement Data</strong> — Extracted requirements, shall/should/must statements</li>
    <li><strong>Role Dictionary</strong> — Discovered and adjudicated roles, RACI entries, function tags</li>
    <li><strong>Learning Data</strong> — Your Keep/Suppress/Fix decisions that improve future scan accuracy</li>
</ul>
<p>Click <strong>Clear</strong> next to any category to delete just that data type.</p>

<h2><i data-lucide="alert-triangle"></i> Factory Reset</h2>
<p>Permanently deletes <strong>ALL</strong> user data including scan history, role dictionaries, learning data, and preferences. This action cannot be undone.</p>

<div class="help-callout help-callout-warning">
    <i data-lucide="alert-triangle"></i>
    <div>
        <strong>Export First</strong>
        <p>Before clearing data, consider exporting your role dictionary (Roles Studio > Export) and scan history to preserve your work.</p>
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

<div style="width:100%;overflow-x:auto;padding:20px 0;">
<div class="aao-root">
<style>
.aao-root{max-width:720px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e6edf3;position:relative}
.aao-title{text-align:center;font-size:15px;font-weight:700;letter-spacing:2.5px;color:#D6A84A;margin-bottom:18px;animation:aaoGlow 3s ease-in-out infinite;text-transform:uppercase}
@keyframes aaoGlow{0%,100%{text-shadow:0 0 8px rgba(214,168,74,0.3)}50%{text-shadow:0 0 18px rgba(214,168,74,0.6),0 0 30px rgba(214,168,74,0.2)}}
@keyframes aaoFadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
@keyframes aaoGrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.aao-tier{animation:aaoFadeUp .5s ease both}
.aao-tier-header{display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:13px;font-weight:600;color:#e6edf3}
.aao-tier-header .aao-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
.aao-tier-header .aao-label{margin-left:auto;font-size:11px;font-weight:400;color:#8b949e;font-style:italic}
.aao-boxes{display:grid;gap:8px;margin-bottom:4px}
.aao-boxes-4{grid-template-columns:repeat(4,1fr)}
.aao-boxes-3{grid-template-columns:repeat(3,1fr)}
.aao-box{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px;text-align:center;transition:transform .2s,box-shadow .2s;cursor:default}
.aao-box:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.3)}
.aao-box-title{font-size:12px;font-weight:600;color:#e6edf3;margin-bottom:4px}
.aao-box-sub{font-size:10px;color:#8b949e;line-height:1.4}
.aao-arrow{display:flex;flex-direction:column;align-items:center;padding:6px 0;animation:aaoFadeUp .5s ease both}
.aao-arrow-line{width:2px;height:28px;background:linear-gradient(180deg,#D6A84A,#B8743A);transform-origin:top;animation:aaoGrow .3s ease both}
.aao-arrow-head{width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:7px solid #B8743A}
.aao-arrow-label{font-size:10px;color:#D6A84A;margin-top:2px;letter-spacing:0.5px}
.aao-nlp-banner{background:linear-gradient(135deg,rgba(56,139,66,0.15),rgba(56,139,66,0.05));border:1px solid rgba(56,139,66,0.3);border-radius:6px;padding:10px;text-align:center;margin-top:8px;animation:aaoFadeUp .5s ease both}
.aao-nlp-banner-title{font-size:11px;font-weight:600;color:#3fb950;margin-bottom:3px}
.aao-nlp-banner-sub{font-size:10px;color:#8b949e}
.aao-t1{animation-delay:.2s}.aao-t2{animation-delay:.9s}.aao-t3{animation-delay:1.6s}
.aao-a1{animation-delay:.7s}.aao-a1 .aao-arrow-line{animation-delay:.7s}
.aao-a2{animation-delay:1.4s}.aao-a2 .aao-arrow-line{animation-delay:1.4s}
.aao-nlp-d{animation-delay:1.3s}
</style>
<div class="aao-title">AEGIS System Architecture</div>
<div class="aao-tier aao-t1">
<div class="aao-tier-header"><span class="aao-dot" style="background:#3fb950"></span>Browser Client<span class="aao-label">Vanilla JS &middot; No Framework</span></div>
<div class="aao-boxes aao-boxes-4">
<div class="aao-box"><div class="aao-box-title">app.js</div><div class="aao-box-sub">16,000+ LOC<br>Core Logic<br>Modal System</div></div>
<div class="aao-box"><div class="aao-box-title">features/</div><div class="aao-box-sub">Roles Studio<br>Statement Forge<br>Metrics &middot; Guide</div></div>
<div class="aao-box"><div class="aao-box-title">ui/</div><div class="aao-box-sub">State &middot; Events<br>Modals &middot; Toast<br>Renderers</div></div>
<div class="aao-box"><div class="aao-box-title">vendor/</div><div class="aao-box-sub">D3.js &middot; Chart.js<br>Lucide &middot; PDF.js<br>Diff-Match-Patch</div></div>
</div>
</div>
<div class="aao-arrow aao-a1"><div class="aao-arrow-line"></div><div class="aao-arrow-head"></div><div class="aao-arrow-label">HTTP / JSON + CSRF</div></div>
<div class="aao-tier aao-t2">
<div class="aao-tier-header"><span class="aao-dot" style="background:#58a6ff"></span>Flask Server (Python 3.10)<span class="aao-label">Waitress WSGI &middot; 4 threads</span></div>
<div class="aao-boxes aao-boxes-3">
<div class="aao-box"><div class="aao-box-title">routes/ (Blueprints)</div><div class="aao-box-sub">core &middot; review &middot; roles<br>data &middot; config</div></div>
<div class="aao-box"><div class="aao-box-title">core.py (AEGISEngine)</div><div class="aao-box-sub">Extraction &middot; NLP<br>105+ Checkers</div></div>
<div class="aao-box"><div class="aao-box-title">Specialized Modules</div><div class="aao-box-sub">Statement Forge &middot; HV<br>Export &middot; Reports</div></div>
</div>
<div class="aao-nlp-banner aao-nlp-d">
<div class="aao-nlp-banner-title">NLP Stack: spaCy &middot; Sentence-Transformers &middot; NLTK &middot; SymSpell &middot; rapidfuzz</div>
<div class="aao-nlp-banner-sub">Offline Models &middot; Singleton Caching &middot; ThreadPoolExecutor for Batch</div>
</div>
</div>
<div class="aao-arrow aao-a2"><div class="aao-arrow-line"></div><div class="aao-arrow-head"></div></div>
<div class="aao-tier aao-t3">
<div class="aao-tier-header"><span class="aao-dot" style="background:#D6A84A"></span>Data Layer</div>
<div class="aao-boxes aao-boxes-3">
<div class="aao-box"><div class="aao-box-title">scan_history.db</div><div class="aao-box-sub">SQLite</div></div>
<div class="aao-box"><div class="aao-box-title">config.json &middot; version.json</div><div class="aao-box-sub">Settings &middot; Metadata</div></div>
<div class="aao-box"><div class="aao-box-title">logs/ &middot; backups/ &middot; updates/</div><div class="aao-box-sub">Runtime Data</div></div>
</div>
</div>
</div>
</div>

<h2><i data-lucide="folder"></i> Directory Structure</h2>
<pre class="help-code">
AEGIS/                          # Main application folder
├── app.py                      # Flask entry point + middleware (6,000+ LOC)
├── core.py                     # AEGISEngine: extraction + 105+ checkers (2,400+ LOC)
├── role_extractor_v3.py        # AI role extraction (94.7% precision, v3.5.0)
├── review_report.py            # PDF report generator (reportlab, AEGIS branding)
├── scan_history.py             # SQLite database operations + WAL mode
├── *_checker.py                # 30+ quality checker modules
├── routes/                     # Flask Blueprints
│   ├── core_routes.py          # Version, index, middleware
│   ├── review_routes.py        # Document review + folder scan
│   ├── roles_routes.py         # Roles Studio API
│   ├── data_routes.py          # Reports, analytics, export
│   └── config_routes.py        # Settings, diagnostics, updates
├── statement_forge/            # Statement extraction module
│   ├── routes.py               # API endpoints
│   ├── extractor.py            # RequirementsExtractor + WorkInstructionExtractor
│   └── export.py               # CSV/JSON/PDF export
├── hyperlink_validator/        # Link validation module
│   ├── routes.py               # Validation + rescan endpoints
│   ├── validator.py            # URL checking engine
│   ├── headless_validator.py   # Playwright deep validation
│   └── storage.py              # Exclusions + history persistence
├── document_compare/           # Scan-to-scan comparison module
├── nlp/                        # NLP integration layer
│   ├── spacy/                  # spaCy analyzers + checkers
│   ├── spelling/               # SymSpell + Enchant
│   ├── semantics/              # WordNet + sentence-transformers
│   └── style/                  # Proselint + custom style rules
├── static/                     # Frontend assets
│   ├── js/                     # JavaScript modules
│   │   ├── app.js              # Main application + state manager
│   │   ├── features/           # 15+ IIFE feature modules
│   │   ├── ui/                 # UI components (modals, state, events)
│   │   └── vendor/             # D3.js, Chart.js, Lucide, PDF.js
│   ├── css/                    # Modular stylesheets (20+ files)
│   │   ├── style.css           # Main (imports all modules)
│   │   ├── dark-mode.css       # Dark mode variables
│   │   └── features/           # Per-feature CSS modules
│   └── audio/demo/             # Pre-generated TTS narration clips
├── templates/
│   └── index.html              # Single-page application
├── wheels/                     # 240 pre-built wheels (offline install)
├── updates/                    # Drop update files here
├── backups/                    # Auto-created before updates
├── logs/                       # Rotating application logs
├── version.json                # Version info (single source of truth)
├── config.json                 # User configuration
├── Install_AEGIS_OneClick.bat  # Windows one-click installer
└── restart_aegis.sh            # macOS server restart script
</pre>

<h2><i data-lucide="cog"></i> Key Technologies</h2>
<table class="help-table">
    <thead><tr><th>Component</th><th>Technology</th><th>Purpose</th></tr></thead>
    <tbody>
        <tr><td>Backend</td><td>Python 3.10+ / Flask</td><td>API server, document processing</td></tr>
        <tr><td>Frontend</td><td>Vanilla JavaScript</td><td>UI, no framework dependencies</td></tr>
        <tr><td>Visualization</td><td>D3.js, Chart.js</td><td>Graphs and charts</td></tr>
        <tr><td>Icons</td><td>Lucide</td><td>UI icons</td></tr>
        <tr><td>WSGI Server</td><td>Waitress</td><td>Production-ready, Windows-native</td></tr>
        <tr><td>Document Parsing</td><td>Docling AI, mammoth, pymupdf4llm</td><td>DOCX/PDF extraction with fallback chain</td></tr>
        <tr><td>NLP</td><td>spaCy, NLTK, SymSpell, rapidfuzz</td><td>Language analysis, semantic checking</td></tr>
        <tr><td>ML/AI</td><td>sentence-transformers, scikit-learn</td><td>Duplicate detection, similarity scoring</td></tr>
        <tr><td>Reports</td><td>reportlab, openpyxl</td><td>PDF/XLSX report generation</td></tr>
    </tbody>
</table>

<h2><i data-lucide="shield"></i> Air-Gapped Design</h2>
<p>AEGIS is designed for deployment on classified, ITAR-controlled, and air-gapped networks where internet access is unavailable.</p>
<ul>
    <li><strong>Zero external API calls</strong> — All NLP, AI, and analysis processing runs 100% locally on your machine</li>
    <li><strong>240 pre-built wheels</strong> — Complete Python dependency set for offline Windows installation</li>
    <li><strong>Offline NLP models</strong> — spaCy en_core_web_sm, sentence-transformers, NLTK data, and SymSpell dictionaries all bundled</li>
    <li><strong>Vendor JavaScript</strong> — D3.js, Chart.js, Lucide, PDF.js, Diff-Match-Patch all included locally</li>
    <li><strong>Local update system</strong> — Drop files in the updates/ folder, apply via Settings with automatic backup</li>
    <li><strong>No telemetry or analytics</strong> — AEGIS sends zero data outside your machine, ever</li>
    <li><strong>SQLite database</strong> — All data stored in a single local file (scan_history.db) with WAL journaling</li>
</ul>
`
};

// ============================================================================
// TECHNICAL - CHECKER ENGINE
// ============================================================================
HelpDocs.content['tech-checkers'] = {
    title: 'Checker Engine',
    subtitle: 'How the 105+ quality checkers work',
    html: `
<h2><i data-lucide="cog"></i> Checker Architecture</h2>
<p>AEGIS runs <strong>105+ quality checkers</strong> across 12 categories. Each checker is a Python class with a factory registration pattern:</p>

<pre class="help-code">
class AcronymChecker(BaseChecker):
    name = "Acronym Checker"
    category = "Acronyms"

    def check(self, document):
        issues = []
        for para_idx, paragraph in enumerate(document.paragraphs):
            acronyms = self.find_acronyms(paragraph.text)
            for acronym in acronyms:
                if not self.is_defined(acronym, document):
                    issues.append(ReviewIssue(
                        severity="high",
                        message=f"Undefined acronym: {acronym}",
                        flagged_text=acronym,
                        paragraph_index=para_idx,
                        suggestion="Define on first use"
                    ))
        return issues

def create_checker():
    return {'acronym': AcronymChecker()}
</pre>

<h2><i data-lucide="list"></i> Checker Categories</h2>
<div style="width:100%;overflow-x:auto;padding:12px 0;">
<div class="acc-root">
<style>
.acc-root{max-width:720px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e6edf3}
.acc-title{text-align:center;font-size:15px;font-weight:700;letter-spacing:2.5px;color:#D6A84A;margin-bottom:16px;animation:accGlow 3s ease-in-out infinite;text-transform:uppercase}
@keyframes accGlow{0%,100%{text-shadow:0 0 8px rgba(214,168,74,0.3)}50%{text-shadow:0 0 18px rgba(214,168,74,0.6),0 0 30px rgba(214,168,74,0.2)}}
@keyframes accFadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.acc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}
.acc-card{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 10px 10px 14px;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s;cursor:default;animation:accFadeUp .5s ease both}
.acc-card:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.3)}
.acc-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px}
.acc-card-title{font-size:11px;font-weight:600;color:#e6edf3;margin-bottom:3px}
.acc-card-sub{font-size:10px;color:#8b949e;line-height:1.3}
.acc-bar{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 14px;text-align:center;animation:accFadeUp .5s ease both}
.acc-bar-title{font-size:11px;font-weight:600;color:#e6edf3;margin-bottom:3px}
.acc-bar-sub{font-size:10px;color:#8b949e}
.acc-r1c1{animation-delay:.3s}.acc-r1c2{animation-delay:.5s}.acc-r1c3{animation-delay:.7s}.acc-r1c4{animation-delay:.9s}
.acc-r2c1{animation-delay:1.1s}.acc-r2c2{animation-delay:1.3s}.acc-r2c3{animation-delay:1.5s}.acc-r2c4{animation-delay:1.7s}
.acc-r3c1{animation-delay:1.9s}.acc-r3c2{animation-delay:2.1s}.acc-r3c3{animation-delay:2.3s}.acc-r3c4{animation-delay:2.5s}
.acc-bar-d{animation-delay:2.8s}
</style>
<div class="acc-title">105+ Quality Checkers</div>
<div class="acc-grid">
<div class="acc-card acc-r1c1" style="--c:#3fb950"><style>.acc-r1c1::before{background:#3fb950}</style><div class="acc-card-title">Grammar &amp; Spelling</div><div class="acc-card-sub">LanguageTool &middot; SymSpell</div></div>
<div class="acc-card acc-r1c2" style="--c:#d29922"><style>.acc-r1c2::before{background:#d29922}</style><div class="acc-card-title">Requirements</div><div class="acc-card-sub">INCOSE &middot; Directives &middot; Scope</div></div>
<div class="acc-card acc-r1c3" style="--c:#58a6ff"><style>.acc-r1c3::before{background:#58a6ff}</style><div class="acc-card-title">Writing Quality</div><div class="acc-card-sub">Passive &middot; Readability &middot; Tone</div></div>
<div class="acc-card acc-r1c4" style="--c:#bc8cff"><style>.acc-r1c4::before{background:#bc8cff}</style><div class="acc-card-title">Acronyms</div><div class="acc-card-sub">1,767 database &middot; First-use</div></div>

<div class="acc-card acc-r2c1"><style>.acc-r2c1::before{background:#f85149}</style><div class="acc-card-title">Hyperlink Health</div><div class="acc-card-sub">URL check &middot; Deep Validate</div></div>
<div class="acc-card acc-r2c2"><style>.acc-r2c2::before{background:#e3b341}</style><div class="acc-card-title">Document Structure</div><div class="acc-card-sub">Headings &middot; Tables &middot; Lists</div></div>
<div class="acc-card acc-r2c3"><style>.acc-r2c3::before{background:#39d3c5}</style><div class="acc-card-title">Style Consistency</div><div class="acc-card-sub">ASD-STE100 &middot; Style Guides</div></div>
<div class="acc-card acc-r2c4"><style>.acc-r2c4::before{background:#f778ba}</style><div class="acc-card-title">Semantic Analysis</div><div class="acc-card-sub">Duplicates &middot; Similarity</div></div>

<div class="acc-card acc-r3c1"><style>.acc-r3c1::before{background:#3fb950}</style><div class="acc-card-title">Terminology</div><div class="acc-card-sub">Consistency &middot; WordNet</div></div>
<div class="acc-card acc-r3c2"><style>.acc-r3c2::before{background:#d29922}</style><div class="acc-card-title">Punctuation</div><div class="acc-card-sub">Spacing &middot; Quotes &middot; Dashes</div></div>
<div class="acc-card acc-r3c3"><style>.acc-r3c3::before{background:#58a6ff}</style><div class="acc-card-title">Standards</div><div class="acc-card-sub">MIL-STD &middot; INCOSE &middot; IEEE</div></div>
<div class="acc-card acc-r3c4"><style>.acc-r3c4::before{background:#bc8cff}</style><div class="acc-card-title">Readability</div><div class="acc-card-sub">Flesch &middot; Dale-Chall &middot; FOG</div></div>
</div>
<div class="acc-bar acc-bar-d">
<div class="acc-bar-title">Sequential Execution &rarr; Cross-Checker Deduplication &rarr; Category Normalization &rarr; Scoring</div>
<div class="acc-bar-sub">98 UI-toggleable checkers + 7 always-on &middot; Document-type suppression for requirements docs</div>
</div>
</div>
</div>

<h2><i data-lucide="play"></i> Execution Flow</h2>
<ol>
    <li><strong>Document Load</strong> — <code>core.py</code> extracts text via Docling/mammoth/pymupdf4llm chain</li>
    <li><strong>Checker Selection</strong> — UI sends enabled checker IDs via <code>option_mapping</code> + <code>additional_checkers</code></li>
    <li><strong>Sequential Execution</strong> — Checkers run sequentially (not parallel — shared NLP state is not thread-safe)</li>
    <li><strong>Cross-Checker Dedup</strong> — <code>_deduplicate_issues()</code> normalizes 27+ category pairs to catch overlaps</li>
    <li><strong>Document-Type Suppression</strong> — Requirements docs downgrade noise categories (readability, noun density) to Info</li>
    <li><strong>Scoring</strong> — Category concentration discount (logarithmic diminishing returns per category)</li>
    <li><strong>Response</strong> — JSON with issues, grade, score, and metadata sent to frontend</li>
</ol>

<h2><i data-lucide="plus"></i> Adding New Checkers</h2>
<ol>
    <li>Create <code>my_checker.py</code> with a <code>create_checker()</code> factory function</li>
    <li>Implement <code>check(document)</code> method returning <code>ReviewIssue</code> instances</li>
    <li>Register in <code>_init_checkers()</code> import block in <code>core.py</code></li>
    <li>Add to <code>option_mapping</code> (if UI toggle) or <code>additional_checkers</code> (if always-on)</li>
    <li>Add UI checkbox in <code>index.html</code> Settings > Document Profiles</li>
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
<div style="width:100%;overflow-x:auto;padding:20px 0;">
<div class="aep-root">
<style>
.aep-root{max-width:720px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e6edf3;display:flex;flex-direction:column;align-items:center}
.aep-title{text-align:center;font-size:15px;font-weight:700;letter-spacing:2.5px;color:#D6A84A;margin-bottom:18px;animation:aepGlow 3s ease-in-out infinite;text-transform:uppercase}
@keyframes aepGlow{0%,100%{text-shadow:0 0 8px rgba(214,168,74,0.3)}50%{text-shadow:0 0 18px rgba(214,168,74,0.6),0 0 30px rgba(214,168,74,0.2)}}
@keyframes aepFadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
@keyframes aepGrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.aep-pill{background:linear-gradient(135deg,#D6A84A,#B8743A);color:#0d1117;font-size:12px;font-weight:700;padding:8px 24px;border-radius:20px;text-align:center;animation:aepFadeUp .5s ease both;display:inline-block}
.aep-pill:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.4)}
.aep-arrow{display:flex;flex-direction:column;align-items:center;padding:4px 0;animation:aepFadeUp .5s ease both}
.aep-arrow-line{width:2px;height:22px;background:linear-gradient(180deg,#D6A84A,#B8743A);transform-origin:top;animation:aepGrow .3s ease both}
.aep-arrow-head{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #B8743A}
.aep-arrow-label{font-size:9px;color:#8b949e;margin-top:2px;font-style:italic}
.aep-arrow-dashed .aep-arrow-line{background:repeating-linear-gradient(180deg,#D6A84A 0,#D6A84A 4px,transparent 4px,transparent 8px)}
.aep-box{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 16px;width:100%;max-width:480px;text-align:center;animation:aepFadeUp .5s ease both;transition:transform .2s,box-shadow .2s;cursor:default;position:relative}
.aep-box:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.3)}
.aep-box-title{font-size:12px;font-weight:600;color:#e6edf3;margin-bottom:3px}
.aep-box-sub{font-size:10px;color:#8b949e;line-height:1.4}
.aep-priority{border-left:3px solid #D6A84A;padding-left:14px;text-align:left}
.aep-priority-label{position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:9px;color:#D6A84A;font-weight:600;letter-spacing:0.5px}
.aep-priority-pills{display:flex;gap:8px;justify-content:center;margin-top:6px}
.aep-mini-pill{background:rgba(63,185,80,0.15);border:1px solid rgba(63,185,80,0.3);color:#3fb950;font-size:10px;padding:3px 10px;border-radius:10px;font-weight:500}
.aep-mini-pill-label{font-size:9px;color:#8b949e;text-align:center;margin-top:2px}
.aep-d0{animation-delay:.2s}.aep-d1{animation-delay:.5s}.aep-d1 .aep-arrow-line{animation-delay:.5s}
.aep-d2{animation-delay:.8s}.aep-d3{animation-delay:1.1s}.aep-d3 .aep-arrow-line{animation-delay:1.1s}
.aep-d4{animation-delay:1.4s}.aep-d5{animation-delay:1.7s}.aep-d5 .aep-arrow-line{animation-delay:1.7s}
.aep-d6{animation-delay:2.0s}.aep-d7{animation-delay:2.3s}.aep-d7 .aep-arrow-line{animation-delay:2.3s}
.aep-d8{animation-delay:2.6s}.aep-d9{animation-delay:2.9s}.aep-d9 .aep-arrow-line{animation-delay:2.9s}
.aep-d10{animation-delay:3.2s}.aep-d11{animation-delay:3.5s}.aep-d11 .aep-arrow-line{animation-delay:3.5s}
.aep-d12{animation-delay:3.8s}
</style>
<div class="aep-title">Document Extraction Pipeline</div>
<div class="aep-pill aep-d0">Document Upload</div>
<div class="aep-arrow aep-d1"><div class="aep-arrow-line"></div><div class="aep-arrow-head"></div></div>
<div class="aep-box aep-d2"><div class="aep-box-title">Format Detection</div><div class="aep-box-sub">.docx &middot; .pdf &middot; .pptx &middot; .xlsx &middot; .html</div></div>
<div class="aep-arrow aep-d3"><div class="aep-arrow-line"></div><div class="aep-arrow-head"></div></div>
<div class="aep-box aep-priority aep-d4"><div class="aep-box-title">Priority 1: Docling AI Engine</div><div class="aep-box-sub">AI-powered table recognition &middot; Layout analysis<br>Subprocess with 120s timeout</div><div class="aep-priority-label">Best Quality</div></div>
<div class="aep-arrow aep-arrow-dashed aep-d5"><div class="aep-arrow-line"></div><div class="aep-arrow-head"></div><div class="aep-arrow-label">fallback</div></div>
<div class="aep-box aep-priority aep-d6"><div class="aep-box-title">Priority 2: Format-Specific Parsers</div><div class="aep-priority-pills"><div style="text-align:center"><div class="aep-mini-pill">mammoth</div><div class="aep-mini-pill-label">DOCX &rarr; HTML</div></div><div style="text-align:center"><div class="aep-mini-pill">pymupdf4llm</div><div class="aep-mini-pill-label">PDF &rarr; Markdown</div></div></div></div>
<div class="aep-arrow aep-arrow-dashed aep-d7"><div class="aep-arrow-line"></div><div class="aep-arrow-head"></div><div class="aep-arrow-label">fallback</div></div>
<div class="aep-box aep-priority aep-d8"><div class="aep-box-title">Priority 3: Legacy Extractors</div><div class="aep-box-sub">python-docx &middot; pdfplumber &middot; PyMuPDF &middot; Tesseract OCR</div><div class="aep-priority-label">Fallback</div></div>
<div class="aep-arrow aep-d9"><div class="aep-arrow-line"></div><div class="aep-arrow-head"></div></div>
<div class="aep-box aep-d10"><div class="aep-box-title">html_preview Generation</div><div class="aep-box-sub">Rich HTML rendering for all extraction paths</div></div>
<div class="aep-arrow aep-d11"><div class="aep-arrow-line"></div><div class="aep-arrow-head"></div></div>
<div class="aep-box aep-d10" style="animation-delay:3.2s"><div class="aep-box-title">NLP Enhancement + Role Detection</div><div class="aep-box-sub">spaCy &middot; scikit-learn &middot; Statement Forge &middot; 105+ Quality Checkers</div></div>
<div class="aep-arrow aep-d11" style="animation-delay:3.5s"><div class="aep-arrow-line" style="animation-delay:3.5s"></div><div class="aep-arrow-head"></div></div>
<div class="aep-pill aep-d12">Unified Review Results</div>
</div>
</div>

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
<div style="width:100%;overflow-x:auto;padding:10px 0;">
<div class="adb-root">
<style>
.adb-root{max-width:480px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e6edf3;display:flex;flex-direction:column;align-items:center}
@keyframes adbFadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
@keyframes adbGrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes adbGrowH{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.adb-pill{background:linear-gradient(135deg,#D6A84A,#B8743A);color:#0d1117;font-size:12px;font-weight:700;padding:8px 24px;border-radius:20px;text-align:center;animation:adbFadeUp .5s ease both;display:inline-block}
.adb-pill:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.4)}
.adb-arrow{display:flex;flex-direction:column;align-items:center;padding:4px 0;animation:adbFadeUp .5s ease both}
.adb-arrow-line{width:2px;height:22px;background:linear-gradient(180deg,#D6A84A,#B8743A);transform-origin:top;animation:adbGrow .3s ease both}
.adb-arrow-head{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #B8743A}
.adb-diamond{width:180px;height:72px;position:relative;animation:adbFadeUp .5s ease both;margin:4px 0}
.adb-diamond-inner{position:absolute;inset:0;background:#161b22;border:2px solid #D6A84A;transform:rotate(0deg);clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);display:flex;align-items:center;justify-content:center}
.adb-diamond-text{font-size:12px;font-weight:600;color:#D6A84A;text-align:center;padding:0 20px}
.adb-branch{display:flex;align-items:flex-start;justify-content:center;gap:40px;width:100%;margin:8px 0;animation:adbFadeUp .5s ease both}
.adb-branch-arm{display:flex;flex-direction:column;align-items:center;gap:4px}
.adb-branch-label{font-size:10px;font-weight:700;letter-spacing:0.5px;margin-bottom:2px}
.adb-branch-label-yes{color:#3fb950}
.adb-branch-label-no{color:#f85149}
.adb-branch-line{width:2px;height:18px;transform-origin:top;animation:adbGrow .3s ease both}
.adb-branch-line-yes{background:#3fb950}
.adb-branch-line-no{background:#f85149}
.adb-branch-head-yes{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #3fb950}
.adb-branch-head-no{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #f85149}
.adb-box{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 16px;text-align:center;transition:transform .2s,box-shadow .2s;cursor:default;animation:adbFadeUp .5s ease both;min-width:120px}
.adb-box:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.3)}
.adb-box-title{font-size:12px;font-weight:600;color:#e6edf3;margin-bottom:2px}
.adb-box-sub{font-size:10px;color:#8b949e}
.adb-converge{display:flex;align-items:flex-start;justify-content:center;gap:40px;width:100%;position:relative;margin:4px 0;animation:adbFadeUp .5s ease both}
.adb-converge-arm{width:2px;height:20px;background:linear-gradient(180deg,#30363d,#D6A84A);transform-origin:top;animation:adbGrow .3s ease both}
.adb-converge-head{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #B8743A}
.adb-result{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 20px;text-align:center;animation:adbFadeUp .5s ease both;transition:transform .2s,box-shadow .2s;cursor:default}
.adb-result:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.3)}
.adb-result-title{font-size:12px;font-weight:600;color:#e6edf3;margin-bottom:2px}
.adb-result-sub{font-size:10px;color:#8b949e}
.adb-d0{animation-delay:.2s}.adb-d1{animation-delay:.5s}.adb-d1 .adb-arrow-line{animation-delay:.5s}
.adb-d2{animation-delay:.8s}.adb-d3{animation-delay:1.2s}.adb-d3 .adb-branch-line{animation-delay:1.2s}
.adb-d4{animation-delay:1.6s}.adb-d4 .adb-converge-arm{animation-delay:1.6s}
.adb-d5{animation-delay:2.0s}
</style>
<div class="adb-pill adb-d0">Document Upload</div>
<div class="adb-arrow adb-d1"><div class="adb-arrow-line"></div><div class="adb-arrow-head"></div></div>
<div class="adb-diamond adb-d2"><div class="adb-diamond-inner"><div class="adb-diamond-text">Docling<br>Available?</div></div></div>
<div class="adb-branch adb-d3">
<div class="adb-branch-arm"><div class="adb-branch-label adb-branch-label-yes">YES</div><div class="adb-branch-line adb-branch-line-yes"></div><div class="adb-branch-head-yes"></div><div class="adb-box" style="border-left:3px solid #3fb950"><div class="adb-box-title">Docling AI</div><div class="adb-box-sub">Best quality</div></div></div>
<div class="adb-branch-arm"><div class="adb-branch-label adb-branch-label-no">NO</div><div class="adb-branch-line adb-branch-line-no"></div><div class="adb-branch-head-no"></div><div class="adb-box" style="border-left:3px solid #f85149"><div class="adb-box-title">Legacy Parser</div><div class="adb-box-sub">Fallback</div></div></div>
</div>
<div class="adb-converge adb-d4">
<div style="display:flex;flex-direction:column;align-items:center"><div class="adb-converge-arm"></div></div>
<div style="display:flex;flex-direction:column;align-items:center"><div class="adb-converge-arm"></div></div>
</div>
<div style="display:flex;flex-direction:column;align-items:center;animation:adbFadeUp .5s ease both;animation-delay:1.8s"><div class="adb-arrow-head" style="border-top-color:#B8743A"></div></div>
<div class="adb-result adb-d5"><div class="adb-result-title">Role Extraction</div><div class="adb-result-sub">Quality Analysis &middot; RACI Detection</div></div>
</div>
</div>

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

<div style="width:100%;overflow-x:auto;padding:10px 0;">
<div class="rep-root">
<style>
.rep-root{max-width:520px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e6edf3;display:flex;flex-direction:column;align-items:center;gap:0;padding:16px 0}
@keyframes repFadeUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
@keyframes repGrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.rep-pill{background:linear-gradient(135deg,#D6A84A,#B8743A);color:#0d1117;font-size:12px;font-weight:700;padding:8px 28px;border-radius:20px;text-align:center;animation:repFadeUp .5s ease both;display:inline-block}
.rep-pill:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.4)}
.rep-arrow{display:flex;flex-direction:column;align-items:center;padding:2px 0;animation:repFadeUp .5s ease both}
.rep-arrow-line{width:2px;height:16px;background:linear-gradient(180deg,#D6A84A,#B8743A);transform-origin:top;animation:repGrow .3s ease both}
.rep-arrow-head{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #B8743A}
.rep-step{display:flex;align-items:center;gap:14px;width:100%;animation:repFadeUp .5s ease both}
.rep-num{min-width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#D6A84A,#B8743A);color:#0d1117;font-size:11px;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.rep-card{flex:1;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px 14px;transition:transform .2s,box-shadow .2s;cursor:default;border-left:3px solid #D6A84A}
.rep-card:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.25)}
.rep-card-title{font-size:12px;font-weight:600;color:#e6edf3;margin-bottom:2px}
.rep-card-desc{font-size:10px;color:#8b949e;line-height:1.4}
.rep-card-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:5px}
.rep-tag{font-size:9px;padding:2px 7px;border-radius:10px;background:rgba(214,168,74,0.12);color:#D6A84A;border:1px solid rgba(214,168,74,0.2)}
.rep-result{background:#161b22;border:2px solid #D6A84A;border-radius:8px;padding:12px 24px;text-align:center;animation:repFadeUp .5s ease both;transition:transform .2s,box-shadow .2s;cursor:default}
.rep-result:hover{transform:scale(1.02);box-shadow:0 0 24px rgba(214,168,74,0.35)}
.rep-result-title{font-size:13px;font-weight:700;color:#D6A84A;margin-bottom:2px}
.rep-result-sub{font-size:10px;color:#8b949e}
.rep-d0{animation-delay:.15s}.rep-d1{animation-delay:.35s}.rep-d1 .rep-arrow-line{animation-delay:.35s}
.rep-d2{animation-delay:.55s}.rep-d3{animation-delay:.75s}.rep-d3 .rep-arrow-line{animation-delay:.75s}
.rep-d4{animation-delay:.95s}.rep-d5{animation-delay:1.15s}.rep-d5 .rep-arrow-line{animation-delay:1.15s}
.rep-d6{animation-delay:1.35s}.rep-d7{animation-delay:1.55s}.rep-d7 .rep-arrow-line{animation-delay:1.55s}
.rep-d8{animation-delay:1.75s}.rep-d9{animation-delay:1.95s}.rep-d9 .rep-arrow-line{animation-delay:1.95s}
.rep-d10{animation-delay:2.15s}.rep-d11{animation-delay:2.35s}.rep-d11 .rep-arrow-line{animation-delay:2.35s}
.rep-d12{animation-delay:2.55s}.rep-d13{animation-delay:2.75s}.rep-d13 .rep-arrow-line{animation-delay:2.75s}
.rep-d14{animation-delay:2.95s}
</style>
<div class="rep-pill rep-d0">Document Text</div>
<div class="rep-arrow rep-d1"><div class="rep-arrow-line"></div><div class="rep-arrow-head"></div></div>
<div class="rep-step rep-d2"><div class="rep-num">1</div><div class="rep-card"><div class="rep-card-title">Pre-processing</div><div class="rep-card-desc">Normalize text, split paragraphs, clean whitespace</div></div></div>
<div class="rep-arrow rep-d3"><div class="rep-arrow-line"></div><div class="rep-arrow-head"></div></div>
<div class="rep-step rep-d4"><div class="rep-num">2</div><div class="rep-card"><div class="rep-card-title">Pattern Matching</div><div class="rep-card-desc">20+ regex patterns for role indicators</div><div class="rep-card-tags"><span class="rep-tag">Job Titles</span><span class="rep-tag">Org Patterns</span><span class="rep-tag">Acronyms</span></div></div></div>
<div class="rep-arrow rep-d5"><div class="rep-arrow-line"></div><div class="rep-arrow-head"></div></div>
<div class="rep-step rep-d6"><div class="rep-num">3</div><div class="rep-card"><div class="rep-card-title">Known Roles Scan</div><div class="rep-card-desc">228+ pre-defined roles with alias matching</div></div></div>
<div class="rep-arrow rep-d7"><div class="rep-arrow-line"></div><div class="rep-arrow-head"></div></div>
<div class="rep-step rep-d8"><div class="rep-num">4</div><div class="rep-card" style="border-left-color:#f85149"><div class="rep-card-title">False Positive Filtering</div><div class="rep-card-desc">192+ exclusions for facilities, processes, and generic terms</div></div></div>
<div class="rep-arrow rep-d9"><div class="rep-arrow-line"></div><div class="rep-arrow-head"></div></div>
<div class="rep-step rep-d10"><div class="rep-num">5</div><div class="rep-card" style="border-left-color:#3fb950"><div class="rep-card-title">Table Boosting</div><div class="rep-card-desc">+20% confidence for roles in RACI and responsibility tables</div></div></div>
<div class="rep-arrow rep-d11"><div class="rep-arrow-line"></div><div class="rep-arrow-head"></div></div>
<div class="rep-step rep-d12"><div class="rep-num">6</div><div class="rep-card"><div class="rep-card-title">Canonical Name Resolution</div><div class="rep-card-desc">Consolidate variations &mdash; PM, Proj. Mgr &rarr; Project Manager</div></div></div>
<div class="rep-arrow rep-d13"><div class="rep-arrow-line"></div><div class="rep-arrow-head"></div></div>
<div class="rep-step rep-d14" style="animation-delay:2.95s"><div class="rep-num">7</div><div class="rep-card"><div class="rep-card-title">Confidence Scoring</div><div class="rep-card-desc">0.0 to 1.0 based on context, position, and frequency</div></div></div>
<div class="rep-arrow" style="animation:repFadeUp .5s ease both;animation-delay:3.15s"><div class="rep-arrow-line" style="animation-delay:3.15s"></div><div class="rep-arrow-head"></div></div>
<div class="rep-result" style="animation-delay:3.35s"><div class="rep-result-title">Extracted Roles</div><div class="rep-result-sub">Named &middot; Scored &middot; Deduplicated &middot; Ready for Adjudication</div></div>
</div>
</div>

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

<h2><i data-lucide="brain"></i> Enhanced Processing Pipeline (v5.9)</h2>

<div style="width:100%;overflow-x:auto;padding:20px 0;">
<div class="anp-root">
<style>
.anp-root{max-width:720px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#e6edf3;display:flex;flex-direction:column;align-items:center}
.anp-title{text-align:center;font-size:15px;font-weight:700;letter-spacing:2.5px;color:#D6A84A;margin-bottom:18px;animation:anpGlow 3s ease-in-out infinite;text-transform:uppercase}
@keyframes anpGlow{0%,100%{text-shadow:0 0 8px rgba(214,168,74,0.3)}50%{text-shadow:0 0 18px rgba(214,168,74,0.6),0 0 30px rgba(214,168,74,0.2)}}
@keyframes anpFadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
@keyframes anpGrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes anpPulse{0%,100%{box-shadow:0 0 0 0 rgba(214,168,74,0.3)}50%{box-shadow:0 0 12px 3px rgba(214,168,74,0.15)}}
.anp-pill{background:linear-gradient(135deg,#D6A84A,#B8743A);color:#0d1117;font-size:12px;font-weight:700;padding:8px 24px;border-radius:20px;text-align:center;animation:anpFadeUp .5s ease both;display:inline-block}
.anp-pill:hover{transform:scale(1.02);box-shadow:0 0 20px rgba(214,168,74,0.4)}
.anp-arrow{display:flex;flex-direction:column;align-items:center;padding:4px 0;animation:anpFadeUp .5s ease both}
.anp-arrow-line{width:2px;height:20px;background:linear-gradient(180deg,#D6A84A,#B8743A);transform-origin:top;animation:anpGrow .3s ease both}
.anp-arrow-head{width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:6px solid #B8743A}
.anp-stage{display:flex;align-items:center;width:100%;max-width:560px;gap:12px;animation:anpFadeUp .5s ease both;position:relative;transition:transform .2s,box-shadow .2s;cursor:default}
.anp-stage:hover{transform:scale(1.02)}
.anp-stage:hover .anp-stage-body{box-shadow:0 0 20px rgba(214,168,74,0.3)}
.anp-stage-icon{width:38px;height:38px;border-radius:50%;background:#161b22;border:2px solid #D6A84A;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;animation:anpPulse 3s ease-in-out infinite}
.anp-stage-body{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px 14px;flex:1;transition:box-shadow .2s}
.anp-stage-title{font-size:12px;font-weight:600;color:#e6edf3;margin-bottom:3px}
.anp-stage-sub{font-size:10px;color:#8b949e;line-height:1.4}
.anp-stage-num{font-size:9px;font-weight:700;color:#D6A84A;letter-spacing:1px;text-transform:uppercase;position:absolute;right:-60px;top:50%;transform:translateY(-50%)}
.anp-d0{animation-delay:.2s}.anp-d1{animation-delay:.5s}.anp-d1 .anp-arrow-line{animation-delay:.5s}
.anp-d2{animation-delay:.8s}.anp-d3{animation-delay:1.1s}.anp-d3 .anp-arrow-line{animation-delay:1.1s}
.anp-d4{animation-delay:1.4s}.anp-d5{animation-delay:1.7s}.anp-d5 .anp-arrow-line{animation-delay:1.7s}
.anp-d6{animation-delay:2.0s}.anp-d7{animation-delay:2.3s}.anp-d7 .anp-arrow-line{animation-delay:2.3s}
.anp-d8{animation-delay:2.6s}.anp-d9{animation-delay:2.9s}.anp-d9 .anp-arrow-line{animation-delay:2.9s}
.anp-d10{animation-delay:3.2s}.anp-d11{animation-delay:3.5s}.anp-d11 .anp-arrow-line{animation-delay:3.5s}
.anp-d12{animation-delay:3.8s}
</style>
<div class="anp-title">NLP Processing Pipeline</div>
<div class="anp-pill anp-d0">Raw Document Text</div>
<div class="anp-arrow anp-d1"><div class="anp-arrow-line"></div><div class="anp-arrow-head"></div></div>
<div class="anp-stage anp-d2"><div class="anp-stage-icon">&#x1F4D6;</div><div class="anp-stage-body"><div class="anp-stage-title">Technical Dictionary</div><div class="anp-stage-sub">10,000+ aerospace, defense, government &amp; IT terms</div></div><div class="anp-stage-num">Stage 1</div></div>
<div class="anp-arrow anp-d3"><div class="anp-arrow-line"></div><div class="anp-arrow-head"></div></div>
<div class="anp-stage anp-d4"><div class="anp-stage-icon">&#x1F9E0;</div><div class="anp-stage-body"><div class="anp-stage-title">spaCy Transformer NLP</div><div class="anp-stage-sub">en_core_web_sm &middot; Tokenization &middot; POS &middot; NER &middot; Dependencies</div></div><div class="anp-stage-num">Stage 2</div></div>
<div class="anp-arrow anp-d5"><div class="anp-arrow-line"></div><div class="anp-arrow-head"></div></div>
<div class="anp-stage anp-d6"><div class="anp-stage-icon">&#x1F50D;</div><div class="anp-stage-body"><div class="anp-stage-title">Entity &amp; Pattern Matching</div><div class="anp-stage-sub">EntityRuler (100+ patterns) &middot; PhraseMatcher (150+ roles)</div></div><div class="anp-stage-num">Stage 3</div></div>
<div class="anp-arrow anp-d7"><div class="anp-arrow-line"></div><div class="anp-arrow-head"></div></div>
<div class="anp-stage anp-d8"><div class="anp-stage-icon">&#x2699;</div><div class="anp-stage-body"><div class="anp-stage-title">Ensemble Extraction Engine</div><div class="anp-stage-sub">Combine NER + Patterns + Dependency Parse + Context</div></div><div class="anp-stage-num">Stage 4</div></div>
<div class="anp-arrow anp-d9"><div class="anp-arrow-line"></div><div class="anp-arrow-head"></div></div>
<div class="anp-stage anp-d10"><div class="anp-stage-icon">&#x2714;</div><div class="anp-stage-body"><div class="anp-stage-title">105+ Quality Checkers</div><div class="anp-stage-sub">Grammar &middot; Spelling &middot; Requirements &middot; Structure &middot; Acronyms &middot; Style</div></div><div class="anp-stage-num">Stage 5</div></div>
<div class="anp-arrow anp-d11"><div class="anp-arrow-line"></div><div class="anp-arrow-head"></div></div>
<div class="anp-stage anp-d12" style="animation-delay:3.8s"><div class="anp-stage-icon">&#x1F504;</div><div class="anp-stage-body"><div class="anp-stage-title">Adaptive Learning &amp; Dedup</div><div class="anp-stage-sub">Confidence boosting &middot; Cross-checker dedup &middot; Category normalization</div></div><div class="anp-stage-num">Stage 6</div></div>
<div class="anp-arrow" style="animation:anpFadeUp .5s ease both;animation-delay:4.1s"><div class="anp-arrow-line" style="animation-delay:4.1s"></div><div class="anp-arrow-head"></div></div>
<div class="anp-pill" style="animation:anpFadeUp .5s ease both;animation-delay:4.4s">Roles &middot; Issues &middot; Statements &middot; Confidence Scores</div>
</div>
</div>

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
        <h3>v6.1.10 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>SharePoint Connect &amp; Scan &mdash; Progress Indicator</strong></p>
        <ul>
            <li><strong>ENH: Animated progress indicator</strong> &mdash; SharePoint Connect &amp; Scan now shows a gold-themed progress animation during the 15&ndash;45 second SSO authentication and file discovery phase. Eliminates the appearance of a frozen tool during the blocking backend request</li>
            <li><strong>ENH: Seven-phase progress</strong> &mdash; Cycles through connection stages: Initializing &rarr; Authenticating via Windows SSO &rarr; SSO redirect chain &rarr; Verifying authentication &rarr; Detecting library structure &rarr; Listing documents &rarr; Processing results</li>
            <li><strong>ENH: Live elapsed timer</strong> &mdash; Shows seconds since connection started, updating every second. Progress bar advances smoothly through phases</li>
            <li><strong>ENH: Button status cycling</strong> &mdash; The Connect &amp; Scan button text itself cycles through short status labels (Connecting &rarr; Authenticating &rarr; SSO in progress &rarr; Verifying &rarr; Detecting &rarr; Listing files &rarr; Processing) so even the button indicates active progress</li>
            <li><strong>ENH: Expectation setting</strong> &mdash; Informational subtitle tells user &ldquo;This may take 15&ndash;45 seconds while Windows SSO completes&rdquo; to set expectations upfront</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.9 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>SharePoint Subsite (Sub-Web) Detection &mdash; API Routing Fix</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; Subsite detection for document libraries</strong> &mdash; When a document library lives under a SharePoint subsite (e.g., <code>/sites/AS-ENG/PAL/SITE</code> where <code>PAL</code> is a subsite), all API calls were targeting the parent web (<code>/sites/AS-ENG/_api/web/...</code>) instead of the subsite web (<code>/sites/AS-ENG/PAL/_api/web/...</code>). This caused <code>/Files</code>, <code>/Folders</code>, and all List Items API fallback strategies to return empty results or HTTP 500 &ldquo;Incorrect function&rdquo; errors. New <code>_detect_subweb()</code> method probes intermediate path segments with <code>/_api/web</code> to discover subsites, then re-routes the API base URL to the correct web context</li>
            <li><strong>FIX: Both connectors updated</strong> &mdash; Subweb detection added to both HeadlessSP and REST connectors as Step 2b in <code>connect_and_discover()</code>, between folder path validation and file listing</li>
            <li><strong>FIX: NLTK data packages bundled offline</strong> &mdash; 8 NLTK data packages now bundled as offline ZIP files in <code>nltk_data/</code> directory (<code>punkt</code>, <code>punkt_tab</code>, <code>averaged_perceptron_tagger</code>, <code>averaged_perceptron_tagger_eng</code>, <code>stopwords</code>, <code>wordnet</code>, <code>omw-1.4</code>, <code>cmudict</code>). Apply script downloads ZIPs from GitHub and extracts locally &mdash; no runtime <code>nltk.download()</code> calls needed, fully air-gap compatible. Updated installer, repair tool, and <code>install_nlp.py</code> to use bundled data as primary source</li>
            <li><strong>ENH: Deepest-first probing</strong> &mdash; Subweb detection probes path segments from deepest to shallowest to find the closest subweb to the document library. Handles multiple levels of nested subsites correctly</li>
            <li><strong>ENH: Full diagnostic logging</strong> &mdash; Every subweb probe result (success/failure with HTTP status) and the final re-route decision are logged to <code>sharepoint.log</code></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.8 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>SharePoint List Items API Fallback &mdash; Zero-File Discovery Fix</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; Document library returns 0 files</strong> &mdash; SharePoint&rsquo;s <code>/Files</code> REST endpoint only returns files stored as traditional file-system entries. When content is stored as list items (SharePoint&rsquo;s modern document management mode) or exists only in nested hidden subfolders, <code>/Files</code> returns an empty array even though <code>ItemCount</code> shows 69+ items. Added a 3-strategy List Items API fallback cascade that automatically triggers when both <code>/Files</code> and <code>/Folders</code> return empty at the library root level</li>
            <li><strong>NEW: Strategy 1 &mdash; GetList Items API</strong> &mdash; <code>GetList(path)/Items?$expand=File&amp;$filter=FSObjType eq 0</code> queries the document library as a SharePoint list, returning all file items regardless of how they&rsquo;re stored internally. Works when the target path IS the document library root</li>
            <li><strong>NEW: Strategy 2 &mdash; Walk-up parent discovery</strong> &mdash; When the target path is a subfolder within a library, walks up the path tree to find the library root (using <code>validate_folder_path</code> at each level), then queries all Items via <code>GetList</code> and filters by <code>FileDirRef</code> to match only files in the target subfolder. Handles deeply nested paths like <code>/sites/X/Docs/SubA/SubB</code></li>
            <li><strong>NEW: Strategy 3 &mdash; RenderListDataAsStream</strong> &mdash; Last-resort fallback using the same POST API that SharePoint&rsquo;s web UI uses internally. Gets an <code>X-RequestDigest</code> token via <code>/_api/contextinfo</code>, then POSTs to <code>GetList/RenderListDataAsStream</code> with <code>RecursiveAll</code> scope. Handles edge cases where the Items API is restricted</li>
            <li><strong>FIX: Both connectors updated</strong> &mdash; The List Items API fallback is implemented in both the HeadlessSP connector (Playwright browser) and the REST connector (requests-based) for full feature parity</li>
            <li><strong>ENH: Detailed fallback logging</strong> &mdash; Every step of the fallback chain is logged to <code>sharepoint.log</code>: which strategy is attempted, how many items were found, parsing results, and skip reasons. Enables rapid diagnosis if the fallback path is needed</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.7 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>HeadlessSP Document Discovery Diagnostics</strong></p>
        <ul>
            <li><strong>DIAG: Comprehensive path tracing</strong> &mdash; Added detailed logging throughout the HeadlessSP document discovery chain: <code>connect_and_discover()</code>, <code>validate_folder_path()</code>, and <code>_list_files_recursive()</code> now log exact paths, encoded URLs, API responses, file counts, subfolder names, and validation results at every step. Check <code>logs/sharepoint.log</code> for full diagnostics</li>
            <li><strong>FIX: Defensive URL-decode</strong> &mdash; If <code>library_path</code> arrives still percent-encoded (e.g., <code>T%26E</code> instead of <code>T&amp;E</code>), <code>connect_and_discover()</code> now automatically decodes it before folder validation. Prevents silent failures when special characters in folder names are double-encoded</li>
            <li><strong>ENH: Route-level logging</strong> &mdash; The <code>sharepoint-connect-and-scan</code> endpoint now logs the parsed <code>site_url</code> and <code>library_path</code> before calling the connector, providing end-to-end traceability from HTTP request to SharePoint API call</li>
            <li><strong>FIX: URL guard on all folder endpoints</strong> &mdash; The SharePoint URL detection guard (from v6.1.2) was only on the async <code>folder-scan-start</code> endpoint. Now added to all 3 folder scan endpoints (sync, async, preview) &mdash; pasting a SharePoint URL into the local folder field now shows a clear error message instead of &ldquo;Folder not found&rdquo;</li>
            <li><strong>FIX: Statement History 500 errors</strong> &mdash; Deploys <code>scan_history.py</code> with the <code>get_statement_review_stats()</code> method that was missing on the Windows machine. Resolves the repeated <code>AttributeError: 'ScanHistoryDB' object has no attribute 'get_statement_review_stats'</code> errors (5 occurrences in recent diagnostic logs)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.6 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>HeadlessSP SSO Authentication Fix &mdash; 3 Root Causes</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; chrome-headless-shell lacks SSPI</strong> &mdash; The bundled Playwright binary (<code>chrome-headless-shell</code>) is a stripped-down wrapper around Chromium&rsquo;s content module that lacks full SSPI/Negotiate Windows authentication support. Now uses system Microsoft Edge (<code>channel='msedge'</code>) which ships with Windows 10/11 and runs in the &ldquo;new headless mode&rdquo; &mdash; a full browser binary with complete networking and auth stack. Falls back to Chrome, then bundled Chromium</li>
            <li><strong>FIX: CRITICAL &mdash; Incognito ambient auth disabled</strong> &mdash; Chrome 81+ disabled ambient NTLM/Negotiate authentication in incognito/private profiles. Playwright&rsquo;s <code>new_context()</code> creates ephemeral contexts that behave like incognito. Switched to <code>launchPersistentContext()</code> with a temp <code>user_data_dir</code> which creates a regular profile where ambient auth is enabled by default (Playwright issue #1707, Chromium issue #458369)</li>
            <li><strong>FIX: User-Agent for AD FS</strong> &mdash; Updated User-Agent string to include Edge identifier (<code>Edg/131.0.0.0</code>) for proper <code>WiaSupportedUserAgents</code> matching on AD FS servers that gate Windows Integrated Auth by browser string</li>
            <li><strong>ENH: Ambient auth feature flag</strong> &mdash; Added <code>--enable-features=EnableAmbientAuthenticationInIncognito</code> as belt-and-suspenders to explicitly enable ambient NTLM/Negotiate auth even if the profile is treated as private</li>
            <li><strong>ENH: Temp profile cleanup</strong> &mdash; <code>close()</code> now cleans up the temporary <code>user_data_dir</code> via <code>shutil.rmtree()</code> to prevent disk accumulation from browser profiles</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.5 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>Offline Chromium Browser Install &amp; Auth Allowlist Dedup</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; Offline Chromium installation</strong> &mdash; The apply script no longer calls <code>playwright install chromium</code> (which requires internet access to <code>playwright.azureedge.net</code>). Instead, it downloads the Chromium headless shell binary (~109MB) from the AEGIS GitHub Release and extracts it directly to the Playwright browser cache (<code>%LOCALAPPDATA%\ms-playwright\chromium_headless_shell-1208</code>). Creates required marker files (<code>DEPENDENCIES_VALIDATED</code>, <code>INSTALLATION_COMPLETE</code>) for Playwright to recognize the installation. Fully air-gapped compatible</li>
            <li><strong>FIX: Auth allowlist deduplication</strong> &mdash; The <code>--auth-server-allowlist</code> Chromium flag now deduplicates domain entries before passing to the browser. Previously, overlapping entries from <code>CORP_AUTH_DOMAINS</code> and identity provider extras could cause the allowlist to exceed command-line length limits</li>
            <li><strong>ENH: Multi-source Chromium zip detection</strong> &mdash; The installer searches multiple local directories (<code>browsers/</code>, <code>packaging/browsers/</code>, <code>wheels/</code>, <code>packaging/wheels/</code>, AEGIS root) for a pre-placed Chromium zip before attempting a GitHub Release download. Supports fully offline deployment when the zip is pre-staged</li>
            <li><strong>ENH: Embedded Python auto-detection</strong> &mdash; The apply script now auto-detects the embedded Python at <code>python/python.exe</code> (OneClick installer layout) before falling back to <code>sys.executable</code>, ensuring packages install to the correct Python environment</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.4 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>Headless SharePoint: Federated SSO Fix &amp; Diagnostics</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; Federated SSO authentication</strong> &mdash; HeadlessSPConnector authentication completely rewritten for federated SSO (Azure AD + ADFS). Previous version navigated to <code>/_api/web</code> which immediately redirected to <code>login.microsoftonline.us</code> &mdash; the login URL was detected and returned failure before SSO could complete. Now uses three-phase auth: (1) navigate to site homepage to trigger SSO, (2) wait for redirect chain to complete (up to 30s), (3) verify via <code>page.evaluate(fetch())</code></li>
            <li><strong>FIX: Auth allowlist expanded</strong> &mdash; Added identity provider domains (<code>*.microsoftonline.com</code>, <code>*.microsoftonline.us</code>, <code>*.windows.net</code>, <code>*.adfs.*</code>) to <code>--auth-server-allowlist</code>. The Kerberos/Negotiate challenge happens on the ADFS server during federated auth, not on SharePoint &mdash; the ADFS domain must be in the allowlist or SSO silently fails</li>
            <li><strong>NEW: SharePoint diagnostic logging</strong> &mdash; <code>aegis.sharepoint</code> logger now writes to <code>logs/sharepoint.log</code> (5MB rotating, 2 backups). Previously all connector messages went to stdout only, making them invisible in exported log files</li>
            <li><strong>ENH: Detailed SSO failure diagnostics</strong> &mdash; Detects and reports: login form with password field (Windows Integrated Auth not configured on ADFS), SSO timeout (auth server unreachable), unexpected redirect URL. All logged to <code>sharepoint.log</code> for troubleshooting</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.3 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>Headless Browser SharePoint Connector</strong></p>
        <ul>
            <li><strong>NEW: HeadlessSPConnector</strong> &mdash; When SharePoint REST API authentication fails (e.g., AADSTS65002 error in GCC High where first-party OAuth client IDs are blocked), AEGIS now automatically falls back to a Playwright-powered headless browser that uses the same Windows SSO credentials as Chrome. Zero OAuth tokens, zero config.json editing, zero IT admin involvement required</li>
            <li><strong>NEW: Browser-based REST API calls</strong> &mdash; The headless connector uses <code>page.evaluate(fetch(...))</code> to call SharePoint REST API endpoints from within the browser&rsquo;s authenticated JavaScript context. This produces identical JSON responses to the standard REST-based connector, maintaining full compatibility with the existing scan pipeline</li>
            <li><strong>NEW: HEADLESS_SP_AVAILABLE flag</strong> &mdash; Playwright availability checked at module load time. If Playwright is not installed, the headless fallback is silently skipped and the standard auth cascade continues as before</li>
            <li><strong>ENH: Transparent auto-fallback</strong> &mdash; The Connect &amp; Scan endpoint automatically tries the headless browser when REST API auth fails. The frontend is completely unchanged &mdash; the user just sees &ldquo;Connected via headless browser (Windows SSO)&rdquo; instead of an authentication error</li>
            <li><strong>ENH: Three-strategy file download</strong> &mdash; (A) fetch() as base64 via page.evaluate, (B) Playwright download API via page navigation, (C) response.body() direct extraction. Falls through strategies until one succeeds</li>
            <li><strong>ENH: Thread-safe batch downloads</strong> &mdash; Headless connector automatically forces <code>max_workers=1</code> in ThreadPoolExecutor since Playwright&rsquo;s sync API is single-threaded. Sequential downloads through one authenticated browser session are still much faster than failing on every file</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.2 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>SharePoint Device Code Flow UI &amp; URL Misroute Fix</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; URL misroute guard</strong> &mdash; SharePoint URLs pasted into the local folder scan field now show a clear error message directing users to the &ldquo;Paste SharePoint link&rdquo; field below. Previously showed misleading &ldquo;Folder not found&rdquo; error with the full URL as if it were a filesystem path</li>
            <li><strong>NEW: Device code flow UI</strong> &mdash; When SharePoint Online requires browser-based OAuth authentication, the Connect &amp; Scan panel now displays a styled authentication panel with the verification URL (<code>microsoft.com/devicelogin</code>) and the device code. Users complete authentication in their browser, then click &ldquo;I&rsquo;ve Completed Authentication&rdquo; to retry the connection</li>
            <li><strong>NEW: Device code completion endpoint</strong> &mdash; <code>/api/review/sharepoint-device-code-complete</code> waits up to 120 seconds for the user to enter the code at microsoft.com/devicelogin, then returns the token acquisition status</li>
            <li><strong>ENH: Connect &amp; Scan error response</strong> &mdash; When OAuth device code flow is initiated, the error response now includes the <code>device_code</code> object with <code>verification_uri</code> and <code>user_code</code> so the frontend can display them immediately</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.1 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>Fix: MSAL GCC High Authority Validation &amp; Corporate SSL</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; instance_discovery=False</strong> &mdash; MSAL&rsquo;s PublicClientApplication constructor validates the authority URL against the COMMERCIAL cloud&rsquo;s instance discovery endpoint by default. For GCC High (.microsoftonline.us), this validation always fails because the commercial endpoint doesn&rsquo;t know about government authorities. Setting <code>instance_discovery=False</code> tells MSAL to trust the authority URL directly</li>
            <li><strong>FIX: CRITICAL &mdash; verify=False for MSAL</strong> &mdash; Corporate SSL inspection (proxy/WAF) replaces TLS certificates with internal CA certs that Python&rsquo;s certifi bundle doesn&rsquo;t trust. MSAL uses requests internally, and without <code>verify=False</code>, its HTTPS calls to login.microsoftonline.us fail silently</li>
            <li><strong>FIX: OIDC discovery SSL</strong> &mdash; Tenant GUID discovery endpoint also now uses verify=False for the same corporate SSL inspection reason</li>
            <li><strong>FIX: Removed dead IWA code</strong> &mdash; <code>acquire_token_by_integrated_windows_auth()</code> does not exist in MSAL Python (only in MSAL.NET). Was always silently skipped via <code>hasattr</code> check since v6.0.5. Replaced with clear logging about device code flow availability</li>
            <li><strong>ENH: MSAL version compatibility</strong> &mdash; TypeError fallback for older MSAL versions that don&rsquo;t support <code>instance_discovery</code> or <code>verify</code> kwargs</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.1.0 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>Fix: SharePoint OAuth Tenant Discovery</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; OAuth tenant identifier format</strong> &mdash; The bare tenant name extracted from the SharePoint URL (e.g., &lsquo;ngc&rsquo; from ngc.sharepoint.us) is NOT a valid Azure AD identifier. MSAL authority discovery failed with &ldquo;Unable to get authority configuration.&rdquo; Now uses proper format: <code>ngc.onmicrosoft.us</code> for GCC High or discovered tenant GUID via OIDC endpoint</li>
            <li><strong>NEW: Automatic tenant GUID discovery</strong> &mdash; Queries Microsoft&rsquo;s public OpenID Connect discovery endpoint to resolve the actual tenant GUID. Zero configuration required &mdash; works automatically for both GCC High (.sharepoint.us) and commercial (.sharepoint.com)</li>
            <li><strong>NEW: Fallback tenant discovery</strong> &mdash; If OIDC fails, tries SharePoint 401 Bearer realm header to extract tenant GUID. Multiple fallback authorities ensure maximum compatibility</li>
            <li><strong>ENH: Enhanced auth diagnostics</strong> &mdash; Startup logging now shows all active auth strategies, primary method, and tenant discovery results for easier troubleshooting</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.9 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>Fix: OAuth Dependency Installation</strong></p>
        <ul>
            <li><strong>FIX: CRITICAL &mdash; OAuth packages now install correctly</strong> &mdash; Previous apply scripts used <code>--no-index</code> (offline-only pip install) which silently failed when wheel files were not present on the Windows machine. v6.0.9 tries offline first, then falls back to online PyPI install</li>
            <li><strong>FIX: Clear install verification</strong> &mdash; Apply script now shows explicit INSTALLED / NOT INSTALLED status for each auth package (msal, PyJWT, pywin32)</li>
            <li><strong>FIX: pip availability check</strong> &mdash; Apply script verifies pip exists and shows version before attempting package installs</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.8 <span class="changelog-date">February 25, 2026</span></h3>
        <p><strong>SharePoint Zero-Config OAuth &amp; UI Fix</strong></p>
        <ul>
            <li><strong>NEW: Zero-config OAuth auto-detection</strong> &mdash; MSAL OAuth now auto-detects tenant ID from SharePoint URL and uses Microsoft&rsquo;s well-known Office client ID. No config.json editing required for enterprise rollout</li>
            <li><strong>NEW: Multi-strategy token acquisition</strong> &mdash; tries Integrated Windows Auth (IWA) first for seamless SSO, then device code flow as fallback. All automatic, no user configuration</li>
            <li><strong>FIX: UI freeze after connection failure</strong> &mdash; all SharePoint buttons now properly re-enabled after a failed Connect &amp; Scan attempt</li>
            <li><strong>FIX: Error messages no longer reference config.json</strong> &mdash; all user-facing messages updated to reflect zero-config design for enterprise deployment</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.7 <span class="changelog-date">February 24, 2026</span></h3>
        <p><strong>SharePoint Auth Dependencies Fix</strong></p>
        <ul>
            <li><strong>FIX: pywin32 missing for preemptive SSPI</strong> &mdash; pywin32 (sspi + win32security) was never explicitly installed, causing the primary SharePoint Online auth strategy to silently fail</li>
            <li><strong>FIX: Embedded Python detection</strong> &mdash; apply script now detects the OneClick installer&rsquo;s embedded Python (python/python.exe) instead of installing packages to the wrong system Python</li>
            <li><strong>FIX: Offline-only dependency install</strong> &mdash; all packages installed from local wheels directory only, no internet fallback (air-gapped compatible)</li>
            <li><strong>ENH: Auth strategy summary</strong> &mdash; apply script shows which of the 3 auth strategies (Preemptive SSPI, Standard Negotiate, MSAL OAuth) are available after install</li>
            <li><strong>DEP: Added pywin32&gt;=300</strong> &mdash; Windows-only dependency for SSPI preemptive authentication</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.6 <span class="changelog-date">February 24, 2026</span></h3>
        <p><strong>SharePoint Folder Validation Auth Fix</strong></p>
        <ul>
            <li><strong>FIX: validate_folder_path auth bypass</strong> &mdash; folder validation was using raw session.get() which bypassed preemptive SSPI token and OAuth Bearer token injection</li>
            <li><strong>FIX: Folder validation now uses _api_get()</strong> &mdash; consistent authentication across all SharePoint API calls</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.5 <span class="changelog-date">February 24, 2026</span></h3>
        <p><strong>SharePoint Online Modern Auth</strong></p>
        <ul>
            <li><strong>FIX: SharePoint Online 401 with empty WWW-Authenticate</strong> &mdash; resolved auth failure on GCC High (.sharepoint.us) where Microsoft disabled legacy NTLM/Negotiate auth as of February 2026</li>
            <li><strong>NEW: Preemptive SSPI Negotiate token</strong> &mdash; generates Windows SSO token via SSPI before the first request, bypassing the server&rsquo;s empty auth challenge header</li>
            <li><strong>NEW: MSAL OAuth 2.0 integration</strong> &mdash; Microsoft Authentication Library support for modern auth with Azure AD/Entra, using client credentials or Integrated Windows Auth flows</li>
            <li><strong>NEW: Multi-strategy auth cascade</strong> &mdash; preemptive Negotiate → standard Negotiate → OAuth Bearer → diagnostic messaging, with automatic fallback between strategies</li>
            <li><strong>NEW: Auto-detect SharePoint Online</strong> &mdash; detects .sharepoint.com/.sharepoint.us domains and routes to modern auth. GCC High uses login.microsoftonline.us authority</li>
            <li><strong>ENH: Enhanced 401 diagnostics</strong> &mdash; detailed error messages include auth method attempted, MSAL availability, OAuth config status, and SharePoint Online detection</li>
            <li><strong>DEP: Added msal&gt;=1.20.0 and PyJWT&gt;=2.0.0</strong> &mdash; pure Python wheels included for offline installation</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.4 <span class="changelog-date">February 24, 2026</span></h3>
        <p><strong>PDF Viewer Fix &amp; Proposal Duplicate Detection</strong></p>
        <ul>
            <li><strong>FIX: PDF viewer zoom preserves viewport center</strong> &mdash; zooming in/out keeps your focus point in view instead of jumping to the top-left corner</li>
            <li><strong>FIX: PDF click-and-drag panning scrolls correctly</strong> &mdash; panning now scrolls the container (not the canvas) with a grab cursor for natural navigation</li>
            <li><strong>FIX: PDF auto-fits to container width on render</strong> &mdash; initial render now calculates the optimal scale to fill the viewer panel width</li>
            <li><strong>NEW: Proposal Compare duplicate detection</strong> &mdash; two-stage detection catches duplicate files on upload (by filename) and duplicate vendors post-extraction (by company name)</li>
            <li><strong>ENH: Duplicate upload prompt (replace/keep)</strong> &mdash; when duplicates are detected, a confirmation dialog shows amounts for comparison and lets you replace or keep the existing proposal</li>
            <li><strong>ENH: Post-extraction project duplicate check</strong> &mdash; after extraction, new proposals are cross-checked against existing project proposals to prevent double-counting</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.3 <span class="changelog-date">February 24, 2026</span></h3>
        <p><strong>SharePoint Batch Auth Fix</strong></p>
        <ul>
            <li><strong>FIX: SharePoint batch scan 401 auth errors</strong> &mdash; each file download now uses its own fresh session for thread-safe NTLM/Negotiate authentication instead of sharing a single session across worker threads</li>
            <li><strong>ENH: 401/403 retry with fresh auth session</strong> &mdash; failed downloads automatically retry once with a brand-new SSO session, matching the hyperlink validator pattern</li>
            <li><strong>ENH: Refactored download into helper methods</strong> &mdash; _create_download_session() and _download_with_session() provide clean separation of concerns</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.2 <span class="changelog-date">February 23, 2026</span></h3>
        <p><strong>Fix Assistant Mode Toggle &amp; Quality Improvements</strong></p>
        <ul>
            <li><strong>NEW: Fix Assistant Reviewer/Owner mode toggle</strong> &mdash; Document Owners get Track Changes; Reviewers get recommendation comments without modifying text</li>
            <li><strong>NEW: US English dictionary for spelling checker</strong> &mdash; 200+ British-to-American spelling corrections added</li>
            <li><strong>FIX: Proposal Compare Add Proposal erased previous batch</strong> &mdash; multi-batch uploads now preserve previously extracted proposals</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v6.0.0 <span class="changelog-date">February 22, 2026</span></h3>
        <p><strong>Major Release &mdash; 5-Module Learning System, Proposal Compare v2, Enhanced Security</strong></p>
        <ul>
            <li><strong>NEW: Universal Learning System (v5.9.50)</strong> &mdash; 5 independent learning modules (Document Review, Statement Forge, Roles, HV, Proposal Compare) that remember your corrections. All data stays 100% local</li>
            <li><strong>NEW: Settings Learning Tab (v5.9.52)</strong> &mdash; dedicated management dashboard with per-module View/Export/Clear, global toggle, and pattern viewer</li>
            <li><strong>NEW: Proposal Compare v2 (v5.9.40)</strong> &mdash; 8-tab analysis (executive summary, comparison matrix, categories, red flags, heatmap, vendor scores, details, raw tables)</li>
            <li><strong>NEW: Multi-Term Comparison (v5.9.46)</strong> &mdash; auto-groups proposals by contract term, separate analysis per term group, All Terms Summary cross-comparison</li>
            <li><strong>NEW: Proposal Structure Analyzer (v5.9.47)</strong> &mdash; privacy-safe parser diagnostics with redacted structural reports</li>
            <li><strong>NEW: Local Pattern Learning (v5.9.49)</strong> &mdash; learned category overrides, company patterns, and financial table signatures from user corrections</li>
            <li><strong>NEW: Interactive HTML Export</strong> &mdash; self-contained HTML reports with inline SVG charts, sortable tables, dark/light toggle, print support</li>
            <li><strong>NEW: PDF HiDPI Rendering + Zoom + Magnifier</strong> &mdash; crisp text on Retina/4K, zoom controls, magnifier loupe for document review</li>
            <li><strong>NEW: Project Management Dashboard</strong> &mdash; create projects, group proposals, tag-to-project, project financial summary</li>
            <li><strong>NEW: SharePoint Connector</strong> &mdash; browse and scan SharePoint document libraries with Windows SSO authentication</li>
            <li><strong>NEW: Headless Browser Rewrite (v5.9.44)</strong> &mdash; resource blocking, parallel validation (5 concurrent), Windows SSO passthrough, login page detection</li>
            <li><strong>NEW: Per-Domain Rate Limiting</strong> &mdash; thread-safe semaphores prevent 429 errors during batch validation</li>
            <li><strong>NEW: OS Truststore Integration</strong> &mdash; Python truststore module uses OS certificate store, eliminating corporate SSL errors</li>
            <li><strong>NEW: Content-Type Mismatch Detection</strong> &mdash; catches silent login redirects where document URLs return HTML instead of the expected file type</li>
            <li><strong>NEW: Multi-Strategy SSL Fallback</strong> &mdash; cascade of verify-false + fresh SSO + headless for corporate CA certificates</li>
            <li><strong>NEW: /api/capabilities Endpoint</strong> &mdash; reports server capabilities (excel, pdf, docling, mammoth, spacy, proposal_compare, sharepoint)</li>
            <li><strong>NEW: Batch Scan Minimize/Restore</strong> &mdash; floating badge with progress ring when batch modal is minimized</li>
            <li><strong>NEW: Metrics &amp; Analytics Proposals Tab</strong> &mdash; cross-module dashboard with lazy-loaded proposal metrics</li>
            <li><strong>ENH: 79 overview demo scenes + 93 sub-demos with ~471 deep-dive scenes across all modules</strong></li>
            <li><strong>ENH: Voice narration with 545+ pre-generated MP3 clips (JennyNeural) + Web Speech API fallback</strong></li>
            <li><strong>ENH: Guided Tour auto-advance, demo picker UI, sub-demo breadcrumbs</strong></li>
            <li><strong>ENH: Persistent Docling Worker Pool for batch performance (3-6x faster)</strong></li>
            <li><strong>FIX: Export Highlighted Windows Werkzeug 413 compatibility (read-only property workaround)</strong></li>
            <li><strong>FIX: Batch scan time window mismatch (card vs detail view)</strong></li>
            <li><strong>FIX: Update button display:none never toggled visible</strong></li>
            <li><strong>FIX: Cross-checker dedup with category normalization</strong></li>
            <li><strong>FIX: coreferee compatibility guard for spaCy 3.6+</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.53 <span class="changelog-date">February 22, 2026</span></h3>
        <p><strong>Project Financial Dashboard</strong></p>
        <ul>
            <li><strong>NEW: Project Financial Dashboard</strong> &mdash; rich financial summary with vendor cards, price range, categories, risk flags, and contract terms when opening a project from the landing page</li>
            <li><strong>NEW: Landing page Proposal Compare tile project dropdown</strong> &mdash; select a project and navigate directly to financial analysis</li>
            <li><strong>NEW: openProject() and openProjectWithResults() public API methods on ProposalCompare IIFE for external navigation</strong></li>
            <li><strong>NEW: GET /api/proposal-compare/projects/&lt;id&gt;/financial-summary endpoint aggregates vendor totals, grades, categories, and risk flags from latest comparison</strong></li>
            <li><strong>NEW: View Full Analysis button in project financial dashboard loads complete 8-tab comparison results</strong></li>
            <li><strong>NEW: Export Report button in financial dashboard exports interactive HTML report directly from project view</strong></li>
            <li><strong>ENH: Project dashboard cards now show Total Value alongside Proposals, Line Items, and Last Updated</strong></li>
            <li><strong>ENH: Vendor cards in financial dashboard sorted by total (lowest first) with trophy badge on lowest bidder</strong></li>
            <li><strong>ENH: Price range visualization with gradient bar and average marker</strong></li>
            <li><strong>ENH: Category breakdown table shows per-vendor amounts across all cost categories</strong></li>
            <li><strong>FIX: Learning tab loading spinner stuck when no patterns exist (server restart required)</strong></li>
            <li><strong>FIX: Settings Clear All Learning Data button missing base btn class</strong> &mdash; now styled correctly</li>
            <li><strong>FIX: SharePoint Connect &amp; Scan CSRF token stale after debug reload</strong> &mdash; uses _freshCSRF() helper</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.52 <span class="changelog-date">February 22, 2026</span></h3>
        <p><strong>Learning System UI</strong></p>
        <ul>
            <li><strong>NEW: Settings Learning tab</strong> &mdash; dedicated UI for managing the Pattern Learning system across all 5 AEGIS modules</li>
            <li><strong>NEW: Per-module learning cards with pattern count, last learned date, View/Export/Clear actions</strong></li>
            <li><strong>NEW: Global 'Enable Pattern Learning' toggle</strong> &mdash; persists to both localStorage and backend config.json</li>
            <li><strong>NEW: Pattern Viewer modal</strong> &mdash; read-only JSON viewer for inspecting learned patterns per module</li>
            <li><strong>NEW: Export All Patterns</strong> &mdash; downloads combined JSON of all 5 modules' learned patterns</li>
            <li><strong>NEW: Clear All Learning Data</strong> &mdash; double-confirmation bulk clear across all modules</li>
            <li><strong>NEW: 7 backend API endpoints for learning management (GET/DELETE patterns, export per-module and all)</strong></li>
            <li><strong>ENH: All 5 learner modules respect learning-enabled toggle</strong> &mdash; disabled learning skips all triggers</li>
            <li><strong>ENH: Data Management 'Clear Learning Data' button now also clears v5.9.50 pattern files</strong></li>
            <li><strong>FIX: Added is_learning_enabled() utility in routes/_shared.py for backend config checking</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.51 <span class="changelog-date">February 22, 2026</span></h3>
        <ul>
            <li><strong>NEW: Proposal Compare Pattern Learning demo</strong> &mdash; 4-scene sub-demo walks through how AEGIS learns from extraction corrections, snapshots, diffs, and local pattern application</li>
            <li><strong>NEW: Universal Learning System demo</strong> &mdash; 6-scene sub-demo in Settings covers all 5 learning modules (Review, Forge, Roles, HV, Proposals), safety thresholds, and data management</li>
            <li><strong>ENH: Updated Hyperlink Validator demo scenes to mention automatic learning for domain exclusions, trusted domains, and headless routing</strong></li>
            <li><strong>ENH: Updated Settings Data Management overview to describe Learning System pattern files and Clear Learning Data functionality</strong></li>
            <li><strong>NEW: 10 pre-generated MP3 audio clips (JennyNeural) for new demo scenes</strong> &mdash; pattern_learning (4 clips) + learning_system (6 clips)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.50 <span class="changelog-date">February 22, 2026</span></h3>
        <ul>
            <li><strong>NEW: Universal Learning System</strong> &mdash; AEGIS now learns from user behavior across ALL modules, not just Proposal Compare. Each module has its own local pattern file that never leaves your machine</li>
            <li><strong>NEW: Document Review Learner</strong> &mdash; learns from dismissed issues and Fix Assistant corrections. Categories you consistently ignore get auto-downgraded to Info severity in future reviews</li>
            <li><strong>NEW: Statement Forge Learner</strong> &mdash; learns from directive corrections (should→shall), role assignments, and deletion patterns. Extraction results improve with each edit session</li>
            <li><strong>NEW: Roles Adjudication Learner</strong> &mdash; learns from adjudication decisions. Category assignments, deliverable patterns, and role type predictions improve as you adjudicate more roles</li>
            <li><strong>NEW: Hyperlink Validator Learner</strong> &mdash; learns from status overrides, exclusion patterns, and Deep Validate results. Domains that need headless validation are auto-prioritized in future scans</li>
            <li><strong>NEW: Learning Stats API</strong> &mdash; GET /api/learning/stats returns pattern counts across all 5 learner modules for dashboard integration</li>
            <li><strong>ENH: Review engine applies learned suppressions</strong> &mdash; categories dismissed ≥2 times are auto-downgraded to Info, with document-type-aware context</li>
            <li><strong>ENH: All learners use safety threshold (count ≥ 2) to prevent learning from one-off mistakes</strong></li>
            <li><strong>ENH: All pattern files use atomic writes (write to .tmp then os.replace) for crash safety</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.49 <span class="changelog-date">February 22, 2026</span></h3>
        <ul>
            <li><strong>NEW: Local Pattern Learning System</strong> &mdash; AEGIS now learns from your corrections during Proposal Compare and applies them to future parses. All learned data stays in parser_patterns.json on your machine, never uploaded</li>
            <li><strong>ENH: Expanded Software/License category patterns</strong> &mdash; standalone keywords for VMware, Citrix, Palo Alto, Splunk, CrowdStrike, Office 365, ServiceNow, Jira, Confluence, Tableau, and 20+ more products now auto-categorize correctly</li>
            <li><strong>ENH: Filename-based contract term detection</strong> &mdash; files named with '3-year', '5-year', etc. now auto-detect contract period without relying on document text</li>
            <li><strong>ENH: Improved financial table detection</strong> &mdash; column-focused analysis catches tables with dollar columns even when headers are generic (e.g., SHI PDF-from-Excel files)</li>
            <li><strong>ENH: Relaxed column inference thresholds</strong> &mdash; secondary pass with lower thresholds catches sparse PDF-from-Excel tables that previously failed extraction</li>
            <li><strong>ENH: Dynamic confidence scoring</strong> &mdash; confidence now reflects how many columns were successfully inferred (0.6-0.85 range) instead of a fixed 0.8</li>
            <li><strong>ENH: Learned category overrides</strong> &mdash; when you correct a line item category twice, the keyword-to-category mapping is remembered for future files</li>
            <li><strong>ENH: Learned company name patterns</strong> &mdash; when you correct a detected company name, the filename-to-company mapping is saved locally</li>
            <li><strong>ENH: Learned financial table headers</strong> &mdash; header signatures from verified tables are remembered so similar tables are auto-detected in future parses</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.48 <span class="changelog-date">February 21, 2026</span></h3>
        <ul>
            <li><strong>ENH: Batch Structure Analysis</strong> &mdash; Analyze Structure button now processes ALL selected files (1-20) and downloads a single combined JSON report</li>
            <li><strong>ENH: New batch endpoint POST /api/proposal-compare/analyze-batch-structure accepts multiple files via files[] multipart field</strong></li>
            <li><strong>ENH: Cross-file summary in batch analysis</strong> &mdash; aggregates tables found, category distribution, column patterns, extraction quality, and common parser issues across all files</li>
            <li><strong>ENH: Analyze Structure button shows file count when multiple files selected (e.g., 'Analyze Structure (3 files)')</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.47 <span class="changelog-date">February 21, 2026</span></h3>
        <ul>
            <li><strong>ENH: Proposal Structure Analyzer</strong> &mdash; privacy-safe structural analysis tool that parses proposals and reports table shapes, column patterns, category distribution, and extraction diagnostics WITHOUT exposing dollar amounts, company names, or proprietary content</li>
            <li><strong>ENH: Analyze Structure button in Proposal Compare upload phase</strong> &mdash; select a file and click to download a .json structural report safe for sharing with developers</li>
            <li><strong>ENH: API endpoint POST /api/proposal-compare/analyze-structure</strong> &mdash; accepts a single proposal file, returns redacted structural JSON with ?download=1 option for file download</li>
            <li><strong>ENH: Structure report includes per-table column data patterns, line item confidence histograms, amount bucket distributions, description pattern analysis, field coverage percentages, and parser improvement suggestions</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.46 <span class="changelog-date">February 21, 2026</span></h3>
        <ul>
            <li><strong>ENH: Multi-term comparison</strong> &mdash; proposals are automatically grouped by contract term (e.g., '3 Year', '5 Year') and compared separately within each term group</li>
            <li><strong>ENH: Term selector bar</strong> &mdash; gold pill-based UI above 8-tab results lets you switch between term groups or view All Terms Summary</li>
            <li><strong>ENH: All Terms Summary view</strong> &mdash; cross-term vendor comparison table showing cost per vendor per term, lowest-term highlighting, and vendor presence matrix</li>
            <li><strong>ENH: Review phase term indicator</strong> &mdash; 'Multi-term detected' preview bar with term badges and group counts shown before comparison</li>
            <li><strong>ENH: Compare button adapts</strong> &mdash; shows 'Compare by Term (N groups)' when multi-term is detected, 'Compare All' otherwise</li>
            <li><strong>ENH: Excluded proposals notice</strong> &mdash; single-vendor term groups are excluded from comparison with visible explanation</li>
            <li><strong>ENH: Export support</strong> &mdash; XLSX and HTML exports include term label suffix in filename when in multi-term mode</li>
            <li><strong>ENH: History integration</strong> &mdash; each term comparison saves independently with 'Term: X' label in history notes</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.45 <span class="changelog-date">February 21, 2026</span></h3>
        <ul>
            <li><strong>FIX: Proposal Compare heatmap</strong> &mdash; single-vendor cells now show 'only vendor' label instead of empty deviation; legend uses runtime dark mode color functions with 'Only Vendor' swatch</li>
            <li><strong>FIX: Proposal Compare categories chart</strong> &mdash; switched from stacked to grouped bars so small vendor values are visible alongside large ones</li>
            <li><strong>FIX: Proposal Compare tornado chart</strong> &mdash; styled empty state message with icon instead of silently hiding parent element; improved bar sizing (barPercentage 0.85)</li>
            <li><strong>FIX: Proposal Compare radar chart</strong> &mdash; increased canvas height (300→380), suggestedMax instead of hard max, better point label sizing and padding, removed label backdrops</li>
            <li><strong>FIX: Proposal Compare score bars</strong> &mdash; zero-value scores now show 'N/A' with muted fill instead of an invisible empty bar</li>
            <li><strong>FIX: Proposal Compare score components chart</strong> &mdash; vendor name truncation (25 chars) with tooltip for full name, controlled axis rotation (35° max)</li>
            <li><strong>FIX: Proposal Compare chart grid colors</strong> &mdash; all Chart.js charts now use _getChartGridColor() helper for correct dark mode grid lines</li>
            <li><strong>ENH: Pre-comparison validation</strong> &mdash; _validateBeforeCompare() checks for &lt;2 proposals, empty line items, missing company names, duplicate vendor names, and very low item counts with confirm dialog</li>
            <li><strong>FIX: get_statement_review_stats()</strong> &mdash; defensive method with PRAGMA table_info introspection; handles missing scan_statements table, missing review_status/confirmed columns gracefully</li>
            <li><strong>FIX: Docling artifacts_path</strong> &mdash; invalid env var paths now auto-cleared from os.environ so Docling internals don't re-read stale DOCLING_ARTIFACTS_PATH values</li>
            <li><strong>ENH: Demo system</strong> &mdash; added 2 new Proposal Compare sub-demos (Category Breakdown, Project Dashboard) and expanded Export sub-demo to cover Interactive HTML export</li>
            <li><strong>ENH: Help docs</strong> &mdash; added v5.9.45 features to Proposal Compare analytics, export, and review sections with pre-comparison validation details</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.44 <span class="changelog-date">February 21, 2026</span></h3>
        <ul>
            <li><strong>FIX: Role Doc Matrix</strong> &mdash; wrong API URL /api/roles/function-categories (404) corrected to /api/function-categories in app.js boot sequence</li>
            <li><strong>ENH: Role Doc Matrix safety valve</strong> &mdash; auto-truncates matrices over 10,000 cells (shows top N roles by document coverage) to prevent browser freeze on large datasets</li>
            <li><strong>ENH: HV headless browser rewrite</strong> &mdash; resource blocking (images/CSS/fonts), parallel validation (5x throughput), Windows SSO passthrough via auth-server-allowlist flags, login page detection, soft 404 detection</li>
            <li><strong>ENH: HV per-domain rate limiting</strong> &mdash; thread-safe semaphore-based limiter (max 3 concurrent per domain, 0.2s min delay) prevents 429/IP blocks during batch validation</li>
            <li><strong>ENH: HV content-type mismatch detection</strong> &mdash; catches login redirects where document URLs (.pdf/.docx) return text/html instead of expected content type</li>
            <li><strong>ENH: HV login page URL detection</strong> &mdash; identifies silent SSO redirects to ADFS/Azure AD/SAML login pages that return HTTP 200 instead of 302</li>
            <li><strong>ENH: HV truststore integration</strong> &mdash; uses OS certificate store when available, eliminating most corporate SSL errors without verify=False</li>
            <li><strong>ENH: Voice narration for all demos</strong> &mdash; Pre-generated MP3 audio clips (Jenny Neural voice via edge-tts) for all 11 sections with 37+ audio files. Three-tier provider chain: MP3 → Web Speech API → silent timer</li>
            <li><strong>ENH: Audio manifest system</strong> &mdash; manifest.json tracks all pre-generated audio with text hashes for cache invalidation and automatic regeneration when narration text changes</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.43 <span class="changelog-date">February 21, 2026</span></h3>
        <ul>
            <li><strong>FIX: HV export URL matching</strong> &mdash; 3-strategy approach (row-level source map, sheet-level hyperlinks, cell fallback) fixes 3,742 'No URL' rows from openpyxl ws.hyperlinks vs cell.hyperlink discrepancy</li>
            <li><strong>FIX: HV ValidationSummary counting</strong> &mdash; AUTH_REQUIRED, SSL_WARNING, RATE_LIMITED now have explicit counters instead of falling to 'unknown'</li>
            <li><strong>FIX: Proposal contract term preserved through comparison</strong> &mdash; routes.py ProposalData reconstruction now includes contract_term and extraction_text fields</li>
            <li><strong>FIX: False 'missing line items' flags</strong> &mdash; multi-term comparison awareness detects same-company proposals (e.g. 3-year vs 5-year) and marks term-specific items as info, not critical</li>
            <li><strong>FIX: Vendor count accuracy</strong> &mdash; unique vendors computed by company name dedup (case-insensitive), separate from proposal count</li>
            <li><strong>FIX: HTML export readability</strong> &mdash; replaced confusing donut chart with horizontal category bars, improved stacked bar label sizes, fixed heatmap cell text contrast</li>
            <li><strong>FIX: Proposal ID disambiguation</strong> &mdash; falls back to filename when no contract term exists for same-company proposals</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.42 <span class="changelog-date">February 21, 2026</span></h3>
        <ul>
            <li><strong>ENH: Project Dashboard</strong> &mdash; centralized hub for browsing all projects with 2-column card grid, drill-down to project detail with proposals and comparison history</li>
            <li><strong>ENH: Project Detail View</strong> &mdash; view all proposals and comparisons for a project, edit in-place, move between projects, start new comparisons</li>
            <li><strong>ENH: Edit persistence</strong> &mdash; review phase edits (company name, line items, totals, contract term) auto-save to database via fire-and-forget PUT, survive modal close/reopen</li>
            <li><strong>ENH: Tag to project</strong> &mdash; assign any proposal to any project via positioned dropdown, even after review, with move support between projects</li>
            <li><strong>ENH: Proposal Compare v2.2</strong> &mdash; License category, vendor color badges, currency formatting, dark mode chart text fixes</li>
            <li><strong>ENH: PDF viewer v2.0</strong> &mdash; HiDPI/Retina rendering, zoom controls (+/−/fit), magnifier loupe at 3× zoom on hover</li>
            <li><strong>ENH: Review phase quality indicators</strong> &mdash; green check/amber warning badges for company, line items, total, contract term</li>
            <li><strong>ENH: Comparison preview card</strong> &mdash; shows proposal count, vendors identified, total line items, readiness status before Compare</li>
            <li><strong>ENH: Review phase project selector</strong> &mdash; change/assign project at any point before comparing</li>
            <li><strong>ENH: Enhanced XLSX export</strong> &mdash; 8 sheets (added Heatmap, Rate Analysis, Raw Line Items), grade coloring, conditional formatting</li>
            <li><strong>ENH: Interactive HTML export</strong> &mdash; standalone self-contained HTML report with SVG charts, dark/light toggle, sortable tables, tab navigation</li>
            <li><strong>ENH: Export Interactive HTML button</strong> &mdash; alongside XLSX export with gold accent styling</li>
            <li><strong>ENH: Vendor color badges in comparison table headers, executive ranking, and score cards for disambiguation</strong></li>
            <li><strong>ENH: Expanded category list</strong> &mdash; Labor, Material, Software, License, Travel, Training, ODC, Subcontract, Overhead, Fee, Other</li>
            <li><strong>ENH: Live demo scenes</strong> &mdash; Proposal Compare demos inject simulated results (executive summary, comparison matrix, heatmap, vendor scores, red flags, categories)</li>
            <li><strong>ENH: fresh_install.py</strong> &mdash; comprehensive installer downloads ~230 code files from GitHub without touching dependencies, databases, or config</li>
            <li><strong>FIX: Dark mode chart text</strong> &mdash; all Chart.js instances now read fresh computed CSS vars via helper functions</li>
            <li><strong>FIX: Currency formatting</strong> &mdash; explicit en-US locale in formatMoney() for consistent $X,XXX.XX display</li>
            <li><strong>FIX: HV blueprint import</strong> &mdash; changed except ImportError to except Exception to handle config_logging init failures on Windows (PermissionError/OSError from OneDrive paths)</li>
            <li><strong>FIX: Tag-to-project bug</strong> &mdash; proposals now correctly attach to selected project instead of previously-selected project</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.41 <span class="changelog-date">February 20, 2026</span></h3>
        <ul>
            <li><strong>ENH: Proposal Compare Review Phase</strong> &mdash; split-pane view with inline document viewer (PDF.js, DOCX text, XLSX tables) and editable metadata panel</li>
            <li><strong>ENH: Line item editor</strong> &mdash; expand accordion to add/remove/edit individual cost items with category dropdowns, amounts, quantities</li>
            <li><strong>ENH: Comparison History</strong> &mdash; auto-save all comparisons, browse past analyses, reload full results, delete old entries</li>
            <li><strong>ENH: Back to Review</strong> &mdash; return from results to the review phase with proposals preserved, adjust metadata and re-compare</li>
            <li><strong>ENH: Four-phase workflow</strong> &mdash; Upload → Extract → Review → Compare with visual progress indicator</li>
            <li><strong>ENH: PDF extraction overhaul</strong> &mdash; text extraction before tables, 5-strategy company name detection with filename fallback</li>
            <li><strong>ENH: Radar chart in Vendor Scores tab</strong> &mdash; overlays all vendors on spider plot for at-a-glance comparison</li>
            <li><strong>ENH: Tornado chart in Executive Summary</strong> &mdash; horizontal bar chart showing biggest price spreads for negotiation focus</li>
            <li><strong>ENH: Stacked bar chart in Categories tab</strong> &mdash; shows cost structure breakdown per vendor with tooltip totals</li>
            <li><strong>ENH: Configurable evaluation weight sliders</strong> &mdash; drag Price/Completeness/Risk/Data Quality weights, scores recalculate in real-time</li>
            <li><strong>ENH: Sortable comparison table</strong> &mdash; click any column header to sort, category/variance dropdown filters, item count display</li>
            <li><strong>ENH: Enhanced red flags</strong> &mdash; identical pricing detection, missing category gaps, FAR 15.404 price reasonableness (z-score outliers)</li>
            <li><strong>ENH: Guided demos updated</strong> &mdash; 2 new sub-demos (Review &amp; Edit, History) covering editable review phase and comparison history</li>
            <li><strong>ENH: Contract term detection</strong> &mdash; auto-extracts 'X Year', 'Base + N Options', 'N Months' from proposal text and Excel sheet tabs</li>
            <li><strong>ENH: Multi-term vendor disambiguation</strong> &mdash; same company with 3yr vs 5yr proposals get unique IDs in comparison</li>
            <li><strong>ENH: Indirect rate analysis</strong> &mdash; detects fringe, overhead, G&amp;A, fee/profit and flags rates outside typical ranges</li>
            <li><strong>ENH: Auto-calculation of missing financial fields</strong> &mdash; qty × unit_price = amount (and inverse) in parser and frontend</li>
            <li><strong>ENH: Currency auto-format</strong> &mdash; dollar amounts auto-format on blur with $ prefix and commas</li>
            <li><strong>ENH: Click-to-populate</strong> &mdash; select text in doc viewer, click 'Use' button to populate last-focused form field</li>
            <li><strong>ENH: HV auth diagnostic endpoint</strong> &mdash; POST /api/hyperlink-validator/diagnose-auth reports SSO status, method, and init errors</li>
            <li><strong>ENH: HV auth status badge</strong> &mdash; green 'Windows SSO' or red 'Anonymous' badge in HV modal header</li>
            <li><strong>ENH: Headless-first routing for .mil/.gov</strong> &mdash; bypasses 10-30s timeout, routes directly to headless browser queue</li>
            <li><strong>ENH: SharePoint auto-SSL bypass for corporate domains (sharepoint.us, .ngc., .myngc., .northgrum.)</strong></li>
            <li><strong>ENH: SharePoint download retry on 404</strong> &mdash; fresh session retry for transient 404s</li>
            <li><strong>FIX: Parser thresholds lowered</strong> &mdash; DOCX inline $1000→$50, PDF inline $100→$10, captures more financial data</li>
            <li><strong>FIX: PDF/DOCX page limits expanded from 10→50 pages for long proposals</strong></li>
            <li><strong>FIX: Inline amounts always captured (even when tables found) with dedup against table-derived items</strong></li>
            <li><strong>FIX: Auth logging</strong> &mdash; replaced silent ImportError catch with verbose logging in validator.py and sharepoint_connector.py</li>
            <li><strong>FIX: Comparison history loading</strong> &mdash; unwraps nested result.result from get_comparison() response</li>
            <li><strong>FIX: Centralized proposal ID generation prevents mismatched IDs between align and compare functions</strong></li>
            <li><strong>FIX: Totals computed from aligned items instead of raw extraction total for accurate comparison</strong></li>
            <li><strong>FIX: Frontend ID fallback prevents undefined errors when comparison results lack proposal IDs</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.40 <span class="changelog-date">February 20, 2026</span></h3>
        <ul>
            <li><strong>ENH: Proposal Compare v2.0</strong> &mdash; expanded from 4 to 8 result tabs with executive summary, red flags, heatmap, and vendor scores</li>
            <li><strong>ENH: Executive Summary tab with hero stats, price/score rankings, key findings, and negotiation opportunities table</strong></li>
            <li><strong>ENH: Red Flags tab showing automated risk checks per vendor with critical/warning/info severity badges</strong></li>
            <li><strong>ENH: Heatmap tab with color-coded deviation grid (green=below avg, red=above avg) and legend</strong></li>
            <li><strong>ENH: Vendor Scores tab with letter grades (A-F), overall scores, and 4 weighted component bars (Price 40%, Completeness 25%, Risk 25%, Data Quality 10%)</strong></li>
            <li><strong>ENH: Project management</strong> &mdash; create named projects, group proposals, add new proposals to existing projects</li>
            <li><strong>ENH: Chart.js integration</strong> &mdash; optional bar charts in Categories and Vendor Scores tabs (graceful degradation)</li>
            <li><strong>ENH: Full CSS suite for all new components with dark mode support</strong></li>
            <li><strong>ENH: Metrics &amp; Analytics Proposals tab</strong> &mdash; 4 hero stats, value distribution, file types, vendor frequency, category doughnut, and recent activity table with drill-down</li>
            <li><strong>ENH: Proposal metrics API endpoint (/api/proposal-compare/metrics) with lazy loading and 5-minute cache in M&amp;A dashboard</strong></li>
            <li><strong>FIX: Batch scan performance</strong> &mdash; Docling persistent worker daemon=False for Windows (daemon procs can't spawn children)</li>
            <li><strong>FIX: Docling artifacts_path validation with auto-detection fallback when env var points to invalid directory</strong></li>
            <li><strong>FIX: Session-broken flag prevents repeated 60s Docling timeouts across batch files (skip instantly after first failure)</strong></li>
            <li><strong>FIX: Folder scan chunk size reduced from 8→5 and workers from 4→3 for stable Windows+OneDrive performance</strong></li>
            <li><strong>FIX: Export Highlighted crash on Windows</strong> &mdash; request.max_content_length is read-only on some Werkzeug versions (wrapped in try/except at 3 locations)</li>
            <li><strong>FIX: Boot error</strong> &mdash; added missing /api/capabilities endpoint (checkCapabilities() was silently failing, export buttons showed disabled)</li>
            <li><strong>FIX: Proposal Compare z-index bumped from 10001 to 15000</strong> &mdash; modal was behind landing page tiles on Windows Chrome with backdrop-filter</li>
            <li><strong>ENH: Guide system updated with comprehensive Proposal Compare v2.0 demos</strong> &mdash; 8 overview scenes + 7 sub-demos covering all new tabs</li>
            <li><strong>FIX: Apply Updates button in Settings never appeared</strong> &mdash; update-functions.js now toggles #btn-apply-updates visible when updates detected</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.39 <span class="changelog-date">February 20, 2026</span></h3>
        <ul>
            <li><strong>ENH: Batch scan minimize/restore</strong> &mdash; minimize button in modal header hides to floating progress badge</li>
            <li><strong>ENH: Floating mini badge with SVG progress ring shows scan % while working in other areas</strong></li>
            <li><strong>ENH: Click mini badge to restore full scan dashboard</strong> &mdash; works for batch, folder, and SharePoint scans</li>
            <li><strong>ENH: Auto-minimize when clicking outside scan modal during active scan (prevents accidental close)</strong></li>
            <li><strong>FIX: Portfolio batch document count mismatch</strong> &mdash; detail view used ±5min window vs card's 30sec window</li>
            <li><strong>FIX: Portfolio batch detail now uses consistent 30-second batch grouping window</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.38 <span class="changelog-date">February 20, 2026</span></h3>
        <ul>
            <li><strong>FIX: SharePoint connector</strong> &mdash; improved error diagnostics with categorized messages (SSL, DNS, proxy, timeout, reset)</li>
            <li><strong>FIX: SharePoint connector</strong> &mdash; increased default timeout from 30s→45s for corporate networks</li>
            <li><strong>FIX: SharePoint connector</strong> &mdash; auto-tries verify=False on all ConnectionErrors (not just SSL-related ones)</li>
            <li><strong>FIX: SharePoint connector</strong> &mdash; creates fresh session with SSO on connection retry for better recovery</li>
            <li><strong>ENH: One-click 'Connect &amp; Scan' button combines test + auto-detect library + discover files + start scan</strong></li>
            <li><strong>ENH: Library path auto-populates from URL paste and server-side detection</strong> &mdash; no manual entry needed</li>
            <li><strong>ENH: SharePoint batch scans now use batch_mode for faster processing (skips html_preview generation)</strong></li>
            <li><strong>ENH: New /api/review/sharepoint-connect-and-scan endpoint replaces multi-step Test → Preview → Scan flow</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.37 <span class="changelog-date">February 20, 2026</span></h3>
        <ul>
            <li><strong>PERF: Persistent Docling worker pool</strong> &mdash; eliminates 15-30s Python startup overhead per document during batch scans</li>
            <li><strong>PERF: Docling initialization (torch, transformers, DocumentConverter) happens ONCE, not per-document</strong></li>
            <li><strong>PERF: batch_mode option skips html_preview and clean_full_text generation during batch/folder scans</strong></li>
            <li><strong>PERF: Increased folder scan workers from 3→4 and chunk size from 5→8 for better throughput</strong></li>
            <li><strong>FIX: Increased per-file timeout from 300s→480s to prevent false timeout errors on complex PDFs</strong></li>
            <li><strong>FIX: Persistent worker auto-restarts if it dies, with automatic fallback to legacy per-document subprocess</strong></li>
            <li><strong>ENH: Docling worker pool is thread-safe</strong> &mdash; multiple batch threads share a single persistent worker</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.36 <span class="changelog-date">February 20, 2026</span></h3>
        <ul>
            <li><strong>NEW: Proposal Compare tool</strong> &mdash; upload 2-10 vendor proposals (DOCX/PDF/XLSX) and compare financial data side-by-side</li>
            <li><strong>NEW: Proposal parser extracts tables, dollar amounts, line items, company names, and totals from mixed document types</strong></li>
            <li><strong>NEW: Comparison engine aligns line items across proposals using text similarity matching with category-aware scoring</strong></li>
            <li><strong>NEW: Side-by-side matrix with green/red highlighting for lowest/highest costs and variance percentage column</strong></li>
            <li><strong>NEW: Category summaries group costs by Labor, Material, Travel, ODC, Overhead, and Fee across all vendors</strong></li>
            <li><strong>NEW: Export comparison to formatted XLSX with 3 sheets</strong> &mdash; Comparison, Category Summary, and Proposal Details</li>
            <li><strong>NEW: Proposal Compare landing page tile with purple accent color (#8B5CF6)</strong></li>
            <li><strong>NEW: Proposal Compare demo scenes</strong> &mdash; 6 overview + 10 sub-demo narrated walkthroughs with pre-generated audio</li>
            <li><strong>NEW: Batch scan progress dashboard now shows running Issues and Roles counters alongside document count</strong></li>
            <li><strong>ENH: Batch/folder/SharePoint scan completion lines now show: words • issues • roles • Score format</strong></li>
            <li><strong>ENH: Guide system _navigateToSection() support for proposal-compare modal</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.35 <span class="changelog-date">February 20, 2026</span></h3>
        <ul>
            <li><strong>FIX: Batch/folder scan now shows accurate word count instead of 0</strong> &mdash; was reading from wrong location in review results</li>
            <li><strong>FIX: SharePoint batch scan SSL errors</strong> &mdash; multi-layer SSL fallback for corporate CA certificates (verify=True → verify=False → fresh session)</li>
            <li><strong>FIX: SharePoint library path auto-detection after successful connection test</strong></li>
            <li><strong>FIX: Exclusion list removeExclusion() now calls DELETE API</strong> &mdash; removed exclusions no longer reappear after page refresh</li>
            <li><strong>FIX: ExclusionRule matching improved</strong> &mdash; trailing slash and protocol normalization for exact match type</li>
            <li><strong>FIX: Export Highlighted error reporting</strong> &mdash; full traceback returned in response for debugging</li>
            <li><strong>FIX: Loading screen SYSTEMS ONLINE no longer shows before app is ready</strong> &mdash; now triggers at actual boot completion</li>
            <li><strong>FIX: HV header layout</strong> &mdash; mode/depth selector pushed right with margin-left:auto, title no longer clipped</li>
            <li><strong>FIX: HV Upload tab now auto-opens file browse dialog when clicked</strong></li>
            <li><strong>FIX: Statement Forge sub-modal z-index raised to 10500 (above Statement History 10000)</strong></li>
            <li><strong>FIX: Document Review dropzone click restricted to icon area</strong> &mdash; no more accidental file browse on panel click</li>
            <li><strong>FIX: Statement Source Viewer save edit now validates required fields and shows warning toast on failure</strong></li>
            <li><strong>NEW: 478 pre-generated MP3 narration clips with Microsoft Jenny Neural voice for all demo scenes</strong></li>
            <li><strong>NEW: Voice narration manifest supports sub-demo audio lookup by subDemoId</strong></li>
            <li><strong>NEW: SharePoint REST API validation strategy added to Hyperlink Validator retest phase</strong></li>
            <li><strong>NEW: Document viewer toggle</strong> &mdash; switch between Preview (formatted HTML) and Text (plain) views for any document</li>
            <li><strong>NEW: Start_AEGIS.bat</strong> &mdash; launches server minimized via PowerShell with auto-wait and browser open</li>
            <li>IMPROVE: HV scan modes simplified from 3 to 2 — removed Quick (Format Only) mode</li>
            <li>IMPROVE: Loading screen hex grid brighter (6% → 14% opacity) with pulse animation</li>
            <li>IMPROVE: Real boot progress tracking — modules report loading stages to progress bar</li>
            <li>IMPROVE: SharePoint URL auto-parse now triggers on paste event in addition to change</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.34 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: Resolved persistent 413 Request Entity Too Large error that blocked all Excel/DOCX exports on Windows</strong></li>
            <li><strong>FIX: Removed global MAX_CONTENT_LENGTH limit entirely</strong> &mdash; AEGIS is a local-only tool with no need for upload size restrictions</li>
            <li><strong>FIX: Added belt-and-suspenders MAX_CONTENT_LENGTH=None override at 3 levels: app config, before_request hook, and inline before request.files access</strong></li>
            <li><strong>FIX: Added try/except RequestEntityTooLarge wrapper around request.files access with diagnostic logging</strong></li>
            <li>IMPROVE: Export endpoints now log MAX_CONTENT_LENGTH state before parsing for easier debugging</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.33 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>NEW: Multi-color status highlighting for Excel export</strong> &mdash; rows color-coded by validation status: green (working), yellow (SSL/redirect warning), orange (auth required/blocked), red (broken/timeout/DNS failed), grey (no URL)</li>
            <li><strong>NEW: 'Link Status' and 'Link Details' columns auto-added to exported Excel with status label and error details per row</strong></li>
            <li><strong>NEW: Summary sheet ('Link Validation Summary') added to exported Excel with category counts, detailed status breakdown, and color legend</strong></li>
            <li>CHANGE: Export Highlighted button now enabled whenever results exist (not just broken links) — every row gets color-coded regardless of status</li>
            <li>CHANGE: Frontend sends ALL validation results to backend for multicolor export (was sending only broken/issue results)</li>
            <li>CHANGE: Results slimmed to essential fields (url, status, status_code, message) before sending to reduce payload size</li>
            <li><strong>FIX: Windows NamedTemporaryFile compatibility</strong> &mdash; close temp handle before file.save() to avoid file locking conflicts</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.32 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: Corporate SSLERROR false positives</strong> &mdash; multi-strategy SSL fallback replaces single HEAD-with-verify=False attempt; Strategy 1: GET with verify=False + stream=True (corporate servers reject HEAD); Strategy 2: fresh SSO session + verify=False for internal links needing both SSL bypass and Windows auth; headless browser priority list expanded to include NGC corporate domains</li>
            <li><strong>FIX: cyber.mil/STIG and .mil/.gov bot-protected links now marked BLOCKED (not BROKEN)</strong> &mdash; eligible for headless browser retest; DoD WAF/Cloudflare 403s no longer count as broken links</li>
            <li><strong>FIX: SSL_WARNING messages cleaned up</strong> &mdash; removed verbose HTTPSConnectionPool error text; now shows human-readable reasons (certificate not trusted, expired, self-signed, etc.)</li>
            <li><strong>FIX: Export Highlighted error handler now catches RequestEntityTooLarge specifically with helpful message instead of generic 'internal error'; error messages now include exception type for easier debugging</strong></li>
            <li>ARCH: Retest phase gains Strategy 2b (get_no_ssl_fresh_auth) combining verify=False with fresh Windows SSO for corporate SSLERROR links</li>
            <li>ARCH: urllib3 InsecureRequestWarning suppressed for deliberate verify=False corporate CA bypass</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.30 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: Export Highlighted Excel 413 error</strong> &mdash; Werkzeug multipart parser rejected large payloads because app-level MAX_CONTENT_LENGTH wasn't disabled; now temporarily sets both request-level and app-config-level limits to None for export endpoints with automatic restoration</li>
            <li><strong>FIX: File download links falsely flagged as BROKEN</strong> &mdash; added GET fallback for 401/403 responses; when HEAD returns auth error, retries with GET+stream to detect Content-Disposition/Content-Type file downloads; links serving files now correctly marked WORKING</li>
            <li><strong>FIX: TTS narration voice changed from robotic male (GuyNeural) to natural female (JennyNeural)</strong> &mdash; updated edge-tts default, pyttsx3 fallback now prioritizes female voices (Zira/Jenny/Samantha), Web Speech API voice priority rewritten to prefer Windows neural female voices and macOS Samantha</li>
            <li>ARCH: HV post-validation revised to DNS-only corporate domain downgrades — HTTP errors on corporate domains are now genuine after GET fallback testing; only DNSFAILED and BLOCKED on known corporate domains reclassified to AUTH_REQUIRED</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.29 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: Export Highlighted button showed 1200+ broken links when only 80 were broken</strong> &mdash; AUTH_REQUIRED was incorrectly included in broken status count; removed from 4 locations across JS and Python</li>
            <li>FEATURE: Robust Windows SSO auth for internal link validation — 6-tier cascade: pre-validation auth probe, per-URL fresh session retry on 401/403, SharePoint login redirect detection, DNS-only corporate domain downgrade (removed blanket downgrades that masked real broken links), AUTH_REQUIRED now included in retest phase</li>
            <li>FEATURE: SharePoint Online document library scanning — new SharePoint tab in batch upload modal; connects via REST API with Windows SSO (zero new dependencies); discovers documents, downloads to temp, reviews with full AEGIS engine; real-time progress dashboard with per-file status</li>
            <li>ARCH: New _probe_windows_auth() pre-validation probe tests SSO against internal URLs before bulk validation starts</li>
            <li>ARCH: New _retry_with_fresh_auth() creates fresh requests.Session per auth retry — NTLM/Negotiate is connection-specific, shared sessions across threads corrupt handshake state</li>
            <li>ARCH: New _is_login_page_redirect() detects SharePoint/ADFS/Azure AD login page redirects and marks as AUTH_REQUIRED instead of REDIRECT</li>
            <li>ARCH: Replaced blanket corporate/document domain downgrades (v5.0.5-v5.9.1) with DNS-only — only DNSFAILED on corporate domains gets downgraded to AUTH_REQUIRED; HTTP errors (BROKEN/TIMEOUT/BLOCKED) are now genuine after Tier 2 auth retry</li>
            <li>ARCH: New sharepoint_connector.py — SharePointConnector class with REST API discovery, file download, and Windows SSO authentication</li>
            <li>ARCH: SharePoint scan reuses existing folder scan state management and progress polling endpoint — zero frontend infrastructure changes needed for progress tracking</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.28 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: Settings presets not enforced</strong> &mdash; 9 checkers in additional_checkers bypassed UI toggles; moved all to option_mapping so Aerospace/Requirements/General presets properly control checker count</li>
            <li><strong>FIX: Adjudication freeze on save</strong> &mdash; missing return path in roles_routes.py when function_tags empty caused 500 error; added error handling to frontend fetch call</li>
            <li><strong>FIX: Link History panel blank</strong> &mdash; API returns data.scans but code expected data.history; added fallback key lookup</li>
            <li><strong>FIX: Metrics Top Ten Roles blank</strong> &mdash; legacy SQL queried non-existent total_mentions column; rewrote with JOIN through document_roles table</li>
            <li><strong>FIX: Scan History panel blank when opened from landing page tile</strong> &mdash; added loadHistoryData() call after modal show</li>
            <li><strong>FIX: HV Excel export 413 payload too large</strong> &mdash; now sends only broken/issue results instead of all results (reduced payload from ~50MB to ~500KB); also raised global upload limit to 200MB</li>
            <li><strong>FIX: Rebranding</strong> &mdash; replaced all remaining 'TechWriter Review' references with 'AEGIS' in index.html, app.js, config_routes.py, review_routes.py, core.py, report_generator.py</li>
            <li><strong>FIX: Help tabs blank</strong> &mdash; added 5 missing Settings help sections (Review, Network, Profiles, Display, Data Management) to help-docs.js</li>
            <li><strong>FIX: HV broken link count mismatch</strong> &mdash; summary tile now groups BROKEN+INVALID+DNSFAILED+SSLERROR consistently with frontend state (backend sent separate counts)</li>
            <li><strong>FIX: Annotation alignment</strong> &mdash; document viewer now searches adjacent paragraphs (+/-2) when flagged text not found in target paragraph (extraction boundary offset)</li>
            <li><strong>FIX: Particle effects not updating on nav bar theme toggle</strong> &mdash; exposed updateParticleTheme() from landing page IIFE; alpha, radius, and color all sync on mode switch</li>
            <li>UI: SOW Generator document selection now shows gold highlight + left border on checked documents for visual feedback</li>
            <li>UI: Added 2 missing checker toggles for Directive Verb Consistency and Unresolved Cross-References in Settings panel</li>
            <li>UI: Scan progress dashboard shows default detail text for each phase immediately on activation</li>
            <li>NLP: Added defense contractor abbreviations (NG, NGC, NGIS, BAE, GD, SAIC, etc.) to spelling skip list and defense dictionary</li>
            <li>UI: CSS-only loading indicator (gold spinner + AEGIS text) shows during initial page load, auto-dismissed when JS initializes</li>
            <li>UI: Landing page responsive — added 1200px intermediate breakpoint for smoother grid transitions on tablets/narrow laptops</li>
            <li>UI: Metrics analytics modal — fixed responsive width (was incorrectly widening to 99vw at 1000px), added 1200px breakpoint and border-radius reduction at small sizes</li>
            <li>UI: Scan ETA now uses historical step durations for early estimates (blends stored averages with live rate as progress increases)</li>
            <li>UI: Graph export visual polish — label background rects for readability, smooth CSS transitions for dim/highlight, boundary-aware tooltips, gold glow on highlighted nodes, smart ellipsis truncation</li>
            <li>UI: Adjudication HTML export — added Category and Function Tag filter dropdowns with checkboxes, active filter badges, and combined filtering (search + status + category + tags)</li>
            <li>UI: Role extraction pipeline stats shown in scan progress dashboard — candidates found, duplicates removed, unique roles, deliverables (parsed from backend PIPELINE: progress message)</li>
            <li>BACKEND: core.py sends PIPELINE: progress message with extraction stats (roles_found|dupes|roles|deliverables) during postprocessing phase</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.27 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: Roles Studio 403 on save</strong> &mdash; added missing CSRF token (X-CSRF-Token header) to all 3 bulk-update-statements calls in statement-source-viewer.js (review status, notes, text edit)</li>
            <li><strong>FIX: Hyperlink Validator Excel export 413</strong> &mdash; raised upload limit to 200MB for export-highlighted endpoints (large Excel + results JSON exceeded 50MB default)</li>
            <li><strong>FIX: /api/version 34-124s delay</strong> &mdash; cached checker count after first AEGISEngine init instead of re-creating engine on every version API call</li>
            <li><strong>FIX: get_statement_review_stats AttributeError</strong> &mdash; method exists in scan_history.py but Windows deployment had stale copy (5 errors in diagnostics cleared by update)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.26 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li>FEATURE: SOW Generator API endpoints — added GET /api/sow/data and POST /api/sow/generate backend routes, SOW Generator is now fully functional</li>
            <li>FEATURE: Document Compare HTML export — standalone HTML report with AEGIS branding, color-coded diff rows, interactive filter buttons, print-optimized styling</li>
            <li><strong>FIX: Added symspellpy, editdistpy, and en_core_web_sm wheels to wheels/ directory for complete offline installation</strong></li>
            <li><strong>FIX: Windows MIME type error</strong> &mdash; added explicit MIME type registration for .css, .js, .json, .svg to prevent 'refused to apply style' browser errors</li>
            <li><strong>FIX: POST /api/diagnostics/frontend 404</strong> &mdash; added endpoint for frontend-logger.js diagnostic log sync (was firing every 60s with no backend route)</li>
            <li><strong>FIX: POST /api/diagnostics/frontend-logs 404</strong> &mdash; added endpoint for console-capture.js log sync</li>
            <li><strong>FIX: Created static/audio/demo/manifest.json</strong> &mdash; empty manifest to prevent 404 on every page load</li>
            <li><strong>FIX: Ensured static/images/logo.svg is included in distribution for proper logo display</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.25 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: install_nlp.py rewritten</strong> &mdash; now installs all 7 required NLP models (spaCy en_core_web_sm + 6 NLTK data packages: punkt, punkt_tab, averaged_perceptron_tagger, averaged_perceptron_tagger_eng, stopwords, wordnet) to match health check requirements</li>
            <li><strong>FIX: NLTK wordnet zip extraction bug</strong> &mdash; installer now auto-extracts downloaded zip files that NLTK fails to extract, preventing 'wordnet missing' health check failure</li>
            <li>UPDATE: Install_AEGIS_OneClick.bat v5.9.25 — Step 7 now downloads and verifies all NLTK data packages with fallback extraction, runs NLP health check at end of install</li>
            <li>UPDATE: install_offline.bat v5.9.25 — added Step 5/6 for NLP model installation with spaCy download + NLTK data download + wordnet extraction fix</li>
            <li>UPDATE: Install_AEGIS.bat v5.9.25 — added NLTK data download for both offline and online install paths, added install_nlp.py --verify step</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.24 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li><strong>FIX: Overview 'Export All Roles (CSV)' and 'Export All Roles (JSON)' now correctly extract roles from /api/roles/aggregated response</strong> &mdash; data is a direct array, not {roles: [...]}</li>
            <li><strong>FIX: Overview 'Export Current Document (CSV)' now works</strong> &mdash; Cache.overview was never populated, added assignment in renderOverview() after filter application</li>
            <li>ENHANCE: 'Export Current Document (CSV)' now includes Documents, Mentions, Responsibilities, Category, Source columns (was only Name, Mentions, Statements) and reflects document filter in filename</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.23 <span class="changelog-date">February 19, 2026</span></h3>
        <ul>
            <li>REBUILD: Documents by Owner HTML report — added generate_comprehensive_owners_report() to report_html_generator.py with executive summary, Chart.js charts, search/sort/filter, expandable owner cards, dark mode, print support</li>
            <li><strong>FIX: Documents by Owner report no longer falls back to basic static HTML</strong> &mdash; the missing advanced generator function has been implemented</li>
            <li>REBUILD: Relationship diagram HTML export — enhanced with directional relationship arrows (inherits-from, uses-tool, co-performs, supplies-to, receives-from), node sizing by connection count, info panel on click, dark/light theme toggle, link type color coding and dash patterns, relationship data from role_relationships table now included</li>
            <li><strong>FIX: Graph export endpoint now queries role_relationships table and includes directional relationship links alongside co-occurrence links</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.22 <span class="changelog-date">February 18, 2026</span></h3>
        <ul>
            <li><strong>FIX: Statement editor Save button now works</strong> &mdash; fixed boolean vs dict return type mismatch in routes.py</li>
            <li><strong>FIX: Acronym checker no longer flags 'NG' from inside words like 'engineering'</strong> &mdash; replaced \b word boundary with negative lookahead/lookbehind in all 3 acronym checker files</li>
            <li><strong>FIX: Z-index audit</strong> &mdash; Role Source Viewer (50000), Auto Classify overlay (50000) now open ABOVE parent Roles Studio modal (10000)</li>
            <li><strong>FIX: Blinking text cursors eliminated globally</strong> &mdash; added caret-color: transparent on non-input elements, removed cursor:text from statement-history.css</li>
            <li><strong>FIX: Issues by Category legend now sticky at bottom of scrollable panel, removed fixed max-height so panels match Fix Analyzer height</strong></li>
            <li><strong>FIX: Missing get_statement_review_stats() method added to scan_history.py</strong> &mdash; was declared in v4.6.0 changelog but never implemented</li>
            <li><strong>FIX: Settings Stored Data now populates all 4 spans (scan history, statements, roles, learning data) instead of showing 'Loading'</strong></li>
            <li><strong>FIX: HV User-Agent updated to Chrome 131 with Sec-Fetch headers</strong> &mdash; fixes false-positive broken links for YouTube, wikis, .mil/.gov sites</li>
            <li><strong>FIX: Auto Classify modal widened from 520px to 720px, results area expanded from 300px to 50vh for long role names/descriptions</strong></li>
            <li><strong>FIX: Auto Classify deliverable detection now excludes organizational groups (teams, boards, committees, panels) from being flagged as deliverables</strong></li>
            <li><strong>FIX: Batch scan now includes Statement Forge extraction</strong> &mdash; statements extracted and persisted during batch/folder scan alongside regular review</li>
            <li><strong>FIX: Data Explorer 'View in Document'</strong> &mdash; fixed race condition by closing DE first, then opening Role Source Viewer after delay</li>
            <li><strong>FIX: Statement Forge file picker</strong> &mdash; added .txt/.md to valid types, added fresh CSRF token refresh before upload to prevent stale token failures</li>
            <li><strong>FIX: Edge bundling node click now triggers drill-down filter (applyDrillDownFilter) in addition to select/highlight</strong></li>
            <li><strong>FIX: Graph smart search onSelect now also calls selectNode to show details panel with drill-down</strong></li>
            <li>UX: SIPOC Step 5 'Done' label in step indicator now clickable to close the wizard modal</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.21 <span class="changelog-date">February 18, 2026</span></h3>
        <ul>
            <li><strong>ENH: Replaced 5 static PNG diagrams in Help Documentation with animated HTML/CSS diagrams</strong> &mdash; Architecture Overview, Checker Categories, Extraction Pipeline, Docling Backend Selection, NLP Processing Pipeline</li>
            <li><strong>ENH: Animated diagrams use staggered fade-in + slide-up animations, gold glow title shimmer, hover scale effects, and connector grow-in animations</strong></li>
            <li><strong>ENH: All diagram CSS scoped with unique prefixes (aao-, acc-, aep-, adb-, anp-) to prevent style conflicts with existing UI</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.20 <span class="changelog-date">February 18, 2026</span></h3>
        <ul>
            <li><strong>FIX: Data Explorer stat card clicks now open properly above Roles Studio</strong> &mdash; z-index bumped from 10000 to 15000 to layer above modal backdrop (10001)</li>
            <li><strong>ENH: Particles now visible through Data Explorer backdrop</strong> &mdash; reduced overlay opacity from 0.85 to 0.45 (dark) and 0.6 to 0.4 (light), removed backdrop-filter blur(10px)</li>
            <li><strong>ENH: Email Diagnostics now generates .eml file with logs ATTACHED</strong> &mdash; replaces old mailto: approach that required manual file drag-drop. Double-clicking the .eml opens Outlook/Mail with diagnostic JSON + aegis.log already attached</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.19 <span class="changelog-date">February 18, 2026</span></h3>
        <ul>
            <li><strong>FIX: Light mode metric card drill-downs now have proper text visibility</strong> &mdash; added 16 CSS overrides for expanded content (labels, bars, counts, chips, stats, rings) using warm stone color palette instead of white-on-white</li>
            <li><strong>FIX: Metric cards now properly collapse when clicking outside</strong> &mdash; closeAllDrillDowns() was missing classList.remove('lp-metric-expanded') leaving cards in expanded visual state</li>
            <li><strong>ENH: Settings tabs now show scroll indicators</strong> &mdash; gradient fades and arrow buttons appear when tabs overflow the container, active tab auto-scrolls into view on switch</li>
            <li><strong>ENH: Particle canvas moved to body level as global background</strong> &mdash; visible through semi-transparent modal backdrops and any UI gaps. Body background set to transparent with html element as fallback</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.18 <span class="changelog-date">February 18, 2026</span></h3>
        <ul>
            <li><strong>FIX: Help beacon (?) now hides during demo playback so it no longer overlays the X stop button and demo controls. Beacon reappears automatically when demo ends or is stopped</strong></li>
            <li><strong>FIX: All 5 Document Compare sub-demo preActions now use _navigateToSection('compare') to auto-open DocCompare with a real document instead of clicking #nav-compare which showed the picker overlay</strong></li>
            <li>QA: All 5 Document Compare sub-demos re-verified — document_selection, diff_views, change_navigation, compare_export, compare_doc_switcher all open the actual comparison modal correctly with no picker overlay</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.17 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: BUG #9</strong> &mdash; Narration speed race condition resolved. Changing playback speed mid-demo now properly syncs all active components: Web Speech utterances are cancelled and restarted at new rate, pending step timers are rescheduled with adjusted delays, typewriter effect restarts from current position at new speed, and audio element playbackRate updates immediately</li>
            <li><strong>FIX: Compare demo now opens the actual Document Comparison modal with auto-selected document instead of showing the document picker overlay</strong></li>
            <li><strong>FIX: Compare document picker X button not closing</strong> &mdash; duplicate overlay bug caused by repeated openCompareFromNav() calls stacking multiple picker overlays with same ID; now removes existing picker before creating new one</li>
            <li><strong>FIX: Particle canvas moved inside #aegis-landing-page with z-index:0 so particles render behind all tiles, cards, and modals instead of floating on top (was z-index:100000 on body)</strong></li>
            <li>QA: Full demo verification complete — all 12 sections (79 overview scenes + 93 sub-demos with ~471 scenes) tested and passing across 4 QA sessions</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.16 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>NEW: SOW Generator template upload</strong> &mdash; upload a DOCX template with {{PLACEHOLDER}} markers ({{TITLE}}, {{REQUIREMENTS}}, {{ROLES}}, etc.) and AEGIS populates it with extracted data, returning a ready-to-use DOCX</li>
            <li><strong>NEW: Graph View export</strong> &mdash; Export button with dropdown menu for PNG (high-res 3x), SVG (vector), and Interactive HTML formats</li>
            <li><strong>NEW: Interactive HTML graph export</strong> &mdash; standalone D3.js force-directed graph with pan/zoom, search, tooltip details, and filter by function tag, role type, and org group</li>
            <li><strong>NEW: SOW Generator promoted to its own guide section with dedicated demoScenes, subDemos (document_config, output_preview, template_upload), and navigation handler</strong></li>
            <li><strong>NEW: DemoSimulator module</strong> &mdash; IIFE for injecting mock DOM elements during live demos (progress dashboard, simulated results, SOW preview, batch results, graph drag animation)</li>
            <li><strong>FIX: All 11 overview demoScenes rewritten with diverse targets matching narration content</strong> &mdash; eliminated 'same-target syndrome' where all scenes spotlighted the same element</li>
            <li><strong>FIX: 20+ sub-demos updated with correct preActions (DemoSimulator data injection, module API calls), diverse scene targets, and proper navigate properties</strong></li>
            <li><strong>FIX: advanced-settings-panel ID corrected to advanced-panel throughout guide-system.js (global replace)</strong></li>
            <li><strong>FIX: DemoSimulator.cleanupAll() called in both stopDemo() and _navigateToSection() to remove injected elements</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.15 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: 9 BAD sub-demos now force-show their target modals (export, triage, score breakdown, function tags, 5 portfolio) with preAction display:flex + zIndex:148000 pattern and automatic cleanup on demo stop/section switch</strong></li>
            <li><strong>FIX: 18 PARTIAL sub-demos updated with varied scene targets instead of all pointing at same trigger button</strong> &mdash; forge (4), HV (5), settings (3), review (1), history (1), batch (2), help (2)</li>
            <li><strong>FIX: Portfolio sub-demos use Portfolio.open() API instead of nav button click</strong> &mdash; targets now spotlight actual content (.pf-header, #pf-stats-mini, #pf-batch-grid, #pf-singles-grid, #pf-activity-feed)</li>
            <li><strong>FIX: Function tags sub-demo uses TWR.FunctionTags.showModal() with cleanup that removes dynamically-created modal</strong></li>
            <li><strong>FIX: Help/keyboard sub-demos force-show #modal-help with cleanup pattern; accessibility sub-demo opens Settings display tab</strong></li>
            <li><strong>FIX: Forge history_overview target #sf-sidebar corrected to .sf-sidebar (class selector</strong> &mdash; element has no ID)</li>
            <li><strong>FIX: Added 5 cleanup functions (_exportCleanup, _triageCleanup, _scoreCleanup, _funcTagsCleanup, _helpCleanup) called in both stopDemo() and _navigateToSection()</strong></li>
            <li>VERIFY: All 27 fixed sub-demo targets confirmed existing in live DOM via browser MCP testing</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.14 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: Exposed MetricsAnalytics.switchTab() in public API</strong> &mdash; programmatic .click() on IIFE-scoped tab buttons didn't trigger event delegation, breaking all 5 metrics sub-demo preActions</li>
            <li><strong>FIX: _navigateToSection('metrics') now uses MetricsAnalytics.open() instead of generic showModal()</strong> &mdash; ensures data is loaded before tab switching</li>
            <li><strong>FIX: All metrics sub-demo preActions now call MetricsAnalytics.switchTab() directly instead of .click() on tab buttons</strong></li>
            <li><strong>FIX: Corrected MetricsAnalytics references from TWR.MetricsAnalytics to window.MetricsAnalytics (IIFE is on window, not TWR namespace)</strong></li>
            <li><strong>FIX: SOW generator sub-demo preAction used non-existent #sf-btn-sow</strong> &mdash; now calls SowGenerator.open() API directly</li>
            <li><strong>FIX: Fix Assistant sub-demo target #btn-fix-assistant corrected to #btn-open-fix-assistant (actual element ID in HTML)</strong></li>
            <li><strong>FIX: Added missing id='format-csv-card' and id='format-json-card' to export format cards in index.html for sub-demo spotlight targeting</strong></li>
            <li><strong>FIX: Fix Assistant sub-demo now shows the actual FA modal (#fav2-modal) with scenes targeting the change preview, action buttons, and progress bar</strong> &mdash; previously all 4 scenes pointed at the small launcher button</li>
            <li><strong>FIX: FA modal shown via display:flex for demo with automatic cleanup on stopDemo() and section navigation</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.13 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: Comprehensive sub-demo target audit</strong> &mdash; rewrote ALL 93 sub-demo scene targets across 11 sections to spotlight the correct, visible UI elements instead of generic nav buttons or hidden modal elements</li>
            <li><strong>FIX: Metrics sub-demos</strong> &mdash; 4 preActions were clicking #ma-tab-btn-overview instead of their correct tab buttons (#ma-tab-btn-quality, #ma-tab-btn-statements, #ma-tab-btn-roles, #ma-tab-btn-documents). All scene targets now point to tab-specific chart and content elements</li>
            <li><strong>FIX: Batch sub-demos</strong> &mdash; all scenes targeted #btn-batch-load. Now target #batch-dropzone, #folder-scan-path, #batch-file-list, #batch-progress, #batch-results for each workflow phase</li>
            <li><strong>FIX: Compare sub-demos</strong> &mdash; all scenes targeted #nav-compare. Now target #dc-doc-select, #dc-old-scan, #dc-new-scan, #dc-stats, #dc-minimap, #dc-btn-compare</li>
            <li><strong>FIX: History sub-demos</strong> &mdash; all scenes targeted #nav-history. Now target #scan-history-body, #history-search, #modal-scan-history</li>
            <li><strong>FIX: Settings sub-demos</strong> &mdash; 9 original sub-demos all targeted #btn-settings with no tab navigation. Each now clicks its specific settings tab (general, review, profiles, network, display, sharing, updates, troubleshoot, data-management) and targets tab-specific elements</li>
            <li><strong>FIX: Roles sub-demos</strong> &mdash; adjudication_exports/sharing targeted hidden dropdown items. Now target visible toolbar buttons (#adj-export-dropdown, #adj-share-dropdown). dictionary_imports targets #btn-import-dictionary and #dict-content-area. edit_role targets visible dictionary elements</li>
            <li><strong>FIX: dictionary_exports #hierarchy-export-modal target changed to #btn-export-hierarchy (button is visible, modal is not)</strong></li>
            <li><strong>FIX: checker_categories #btn-toggle-advanced target changed to [data-tab='review'] (the toggle is in the review sidebar, not settings)</strong></li>
            <li><strong>FIX: profile_management #btn-preset-reqs target changed to #btn-profile-reset-default (preset buttons are in review sidebar, not settings)</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.12 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: Demo picker sub-demo cards were invisible</strong> &mdash; missing CSS rules for .panel-help-content.hidden and .panel-footer.hidden caused help content to remain visible and push picker cards below the scroll viewport</li>
            <li>ROOT CAUSE: The JS code used classList.add('hidden') on help content and footer, but no CSS rule existed to set display:none on those elements when the hidden class was applied — only component-specific selectors like .demo-picker.hidden existed</li>
            <li><strong>FIX: Sub-demos that use navigate property (e.g., graph_view) no longer reset back to Overview tab</strong> &mdash; _showDemoStep now skips redundant _navigateToSection when already in the correct section during sub-demo playback</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.11 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: Rewrote all 35 new sub-demo scene targets to use specific UI element selectors instead of generic section containers</strong></li>
            <li><strong>FIX: Export sub-demos (DOCX, PDF, Excel/CSV, Filters) now spotlight actual export modal elements</strong> &mdash; format cards, filter chips, preview bar, and export button</li>
            <li><strong>FIX: Export preActions now open the export modal automatically so scenes spotlight elements within it</strong></li>
            <li><strong>FIX: Adjudication sub-demos target #btn-export-adjudication, .adj-export-item[data-action=csv/html/pdf/import], #btn-share-adjudication, #btn-auto-adjudicate, #btn-undo-adj, #adj-select-all</strong></li>
            <li><strong>FIX: Dictionary sub-demos target #btn-import-dictionary, .dict-import-option, #btn-export-dictionary, #btn-download-template, #btn-export-hierarchy</strong></li>
            <li><strong>FIX: Function Tags targets #btn-function-tags, #btn-role-reports; Graph targets #graph-max-nodes, #graph-layout, #graph-labels, #graph-weight-filter, #graph-info-panel</strong></li>
            <li><strong>FIX: Role Editing targets #edit-role-modal, #edit-role-category, #edit-role-tag-select, #btn-save-role</strong></li>
            <li><strong>FIX: Forge sub-modals target #sf-btn-add, #sf-btn-renumber, #sf-btn-merge, #sf-btn-split, #modal-sf-role-mapping; SOW targets #modal-sow-generator, #sow-title, #sow-btn-generate</strong></li>
            <li><strong>FIX: HV Export targets #hv-btn-export-csv, #hv-btn-export-json, #hv-btn-export-html, #hv-btn-export-highlighted</strong></li>
            <li><strong>FIX: Compare Switcher targets #dc-doc-select, #dc-old-scan, #dc-new-scan, #dc-btn-compare</strong></li>
            <li><strong>FIX: Metrics targets #severity-chart-card, #category-chart-card, #ma-tab-btn-quality/statements/roles/documents</strong></li>
            <li><strong>FIX: Settings targets #btn-toggle-advanced, #btn-diag-refresh/health-check/export-json/export-txt/email, #btn-load-backups, #btn-factory-reset, #btn-save-profile</strong></li>
            <li><strong>FIX: Scan History targets #modal-scan-history; Folder Scan targets #folder-scan-path, #btn-folder-discover, #btn-folder-scan, #folder-scan-dashboard</strong></li>
            <li><strong>FIX: Triage targets #modal-triage, #btn-triage-keep/prev/next; Score targets #modal-score-breakdown, #score-breakdown-value/grade</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.10 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>FEATURE: Total sub-demo coverage expansion — 35 new sub-demos with ~159 new scenes for complete end-to-end feature coverage</li>
            <li>FEATURE: Document Review deep-dives — Review Presets, Triage Mode, Family Patterns, Score Breakdown, Selection Tools, DOCX/PDF/Excel/CSV export formats, Export Filters</li>
            <li>FEATURE: Roles Studio deep-dives — Adjudication Exports, Sharing &amp; Collaboration, Auto-Classify &amp; Undo, Dictionary Imports (CSV/SIPOC/Package), Dictionary Exports (CSV/Template/Hierarchy), Function Tags &amp; Reports, Graph Controls, Role Editing</li>
            <li>FEATURE: Additional deep-dives — Server Folder Scan, Forge Advanced Ops, SOW Generator, HV Export Formats, Doc Compare Switcher, Chart Drill-Down, Metrics Insights, Checker Categories, Profile Management, Diagnostics, Backup &amp; Recovery, Scan Actions, Statement History Link, Batch Groups, Portfolio Actions</li>
            <li>FEATURE: Help system deep-dives — Keyboard Shortcuts, Help Navigation, Accessibility Features</li>
            <li>ENHANCED: All new preActions wrapped in try/catch for defensive error handling</li>
            <li>ARCH: Combined total: 79 overview + ~471 sub-demo scenes = ~550 total demo scenes across 93 sub-demos</li>
            <li><strong>FIX: Fixed bare 'logger' references in scan_history.py</strong> &mdash; 12+ instances changed to _log() helper</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.9 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>FEATURE: Deep-dive sub-demo system — 58 sub-demos with ~312 narrated scenes covering every sub-function</li>
            <li>FEATURE: Demo picker UI — when clicking Watch Demo, users see a picker with overview card + sub-demo grid</li>
            <li>FEATURE: Sub-demos for all 11 modules: Dashboard (3), Review (6), Batch (4), Roles (8), Forge (6), HV (7), Compare (4), Metrics (5), History (3), Settings (9), Portfolio (3)</li>
            <li>FEATURE: Each sub-demo has preAction that navigates to the correct tab before scenes play</li>
            <li>FEATURE: Demo bar shows breadcrumb title during sub-demo playback (e.g. 'Roles Studio › RACI Matrix')</li>
            <li>FEATURE: Estimated duration display on each sub-demo card in the picker</li>
            <li><strong>FIX: Replaced offsetParent visibility check with getBoundingClientRect().width for elements inside fixed modals</strong></li>
            <li>ARCH: guide-system.js v2.3.0 — hierarchical sub-demo architecture with startSubDemo(), _showDemoPicker(), _hideDemoPicker()</li>
            <li>ARCH: Combined total: 79 overview scenes + 312 sub-demo scenes = ~391 total demo scenes</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.8 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>ENHANCED: Super-detailed demo scenes — expanded from 31 to 79 narrated walkthrough scenes across all 11 modules</li>
            <li>ENHANCED: Full demo now runs ~10 minutes with detailed narration covering every feature and sub-feature in AEGIS</li>
            <li>ENHANCED: Dashboard demo expanded from 4 to 7 scenes — covers metrics, tiles, getting started, recent docs</li>
            <li>ENHANCED: Document Review demo expanded from 6 to 10 scenes — covers batch, checkers, Fix Assistant, export suite</li>
            <li>ENHANCED: Batch Scan demo expanded from 2 to 6 scenes — covers file picker, folder scan, preview, progress, fault tolerance</li>
            <li>ENHANCED: Roles Studio demo expanded from 5 to 10 scenes — covers all 7 tabs, adjudication export, sharing</li>
            <li>ENHANCED: Statement Forge demo expanded from 4 to 8 scenes — covers extraction pipeline, filtering, bulk ops, history</li>
            <li>ENHANCED: Hyperlink Validator demo expanded from 3 to 7 scenes — covers modes, Deep Validate, exclusions, domain filter</li>
            <li>ENHANCED: Document Compare demo expanded from 1 to 6 scenes — covers auto-compare, diff highlighting, statement tracking</li>
            <li>ENHANCED: Metrics demo expanded from 3 to 7 scenes — covers all 4 tabs, severity and category analysis</li>
            <li>ENHANCED: Scan History demo expanded from 1 to 5 scenes — covers reload, progression tracking, data management</li>
            <li>ENHANCED: Settings demo expanded from 2 to 8 scenes — covers all 9 tabs individually</li>
            <li>ENHANCED: Portfolio demo expanded from 1 to 5 scenes — covers sorting, filtering, grade visualization</li>
            <li>ARCH: guide-system.js v2.2.0 — comprehensive narrated walkthrough system</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.7 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>NEW FEATURE: Voice Narration System for Live Demo player — guide-system.js v2.1.0</li>
            <li><strong>NEW: Audio provider chain</strong> &mdash; Pre-generated MP3 → Web Speech API → Silent timer fallback</li>
            <li><strong>NEW: Narration toggle button with AEGIS gold pulse indicator in demo bar</strong></li>
            <li><strong>NEW: Volume slider control with persistent localStorage preferences</strong></li>
            <li><strong>NEW: Chrome 15-second TTS bug workaround</strong> &mdash; automatic sentence chunking for Web Speech API</li>
            <li><strong>NEW: Voice selection system</strong> &mdash; auto-detects best available TTS voice (Google US &gt; Samantha &gt; system)</li>
            <li><strong>NEW: Pre-generated audio manifest system at /static/audio/demo/manifest.json</strong></li>
            <li><strong>NEW: Server-side TTS generation endpoints</strong> &mdash; /api/demo/audio/status, /api/demo/audio/generate, /api/demo/audio/voices</li>
            <li><strong>NEW: demo_audio_generator.py</strong> &mdash; supports edge-tts (neural) and pyttsx3 (offline) providers</li>
            <li><strong>NEW: Audio playback speed syncs with demo speed selector (0.5x to 2x)</strong></li>
            <li><strong>NEW: Narration pauses/resumes with demo player pause/resume</strong></li>
            <li>ARCH: Progressive enhancement — demo works identically with or without audio enabled</li>
            <li>ARCH: Audio narration layer is completely optional — zero new required dependencies</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.6 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>VISUAL: Complete warm palette deep pass — all CSS variable fallback values updated from cool gray to warm stone/cream tones across 15+ CSS files</li>
            <li>VISUAL: Hyperlink Validator light mode progress bar overhauled — gold gradient replaces blue/purple, warm particles and orbs</li>
            <li>VISUAL: Roles Studio export dialog, smart search, function tree, and report builder all updated to gold accent palette</li>
            <li>VISUAL: Data Explorer light mode backgrounds warmed — cards, stats, tables, nav buttons all use cream/stone palette</li>
            <li>VISUAL: Fix Assistant fallback values updated — borders, backgrounds, tertiary surfaces all use warm tones</li>
            <li>VISUAL: Charts, components, and layout fallback values synchronized to warm palette</li>
            <li>VISUAL: 40+ CSS variable fallback values corrected from cool (#f8fafc, #e2e8f0, #e5e7eb) to warm (#f0ebe3, #cfc7b8, #e8e2d8)</li>
            <li>PRESERVE: Semantic blue preserved for RACI types, directive colors, severity-info badges, redirect status, per-tool icons, and dark mode styles</li>
            <li><strong>FIX: Body data-theme attribute now synced on theme toggle</strong> &mdash; fixes light mode CSS variable inheritance (Lesson 46)</li>
            <li><strong>FIX: Help docs print button uses hidden iframe instead of window.open()</strong> &mdash; eliminates popup blocker errors (Lesson 47)</li>
            <li><strong>FIX: FOUC inline style clearing expanded to cover both html and body elements on light mode initialization</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.5 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>VISUAL: Cinematic inline SVG diagrams replace ASCII art in Help docs — NLP Pipeline (7 stages), System Architecture (3-tier), Document Extraction (priority chain)</li>
            <li>VISUAL: Enterprise Grade callout boxes changed from green to AEGIS gold/bronze branding across all 8 instances</li>
            <li>VISUAL: Light mode warm palette overhaul — cream/stone/gold tones replace harsh whites across base, landing page, modals, settings</li>
            <li>VISUAL: Light mode accent colors changed from blue to gold across Roles Studio, settings, hyperlink validator, metrics, export suite</li>
            <li>VISUAL: Landing page particles increased to 140 count with deep gold coloring and warm gradient background</li>
            <li><strong>FIX: Windows CSV exports now include UTF-8 BOM and CRLF line endings for Excel compatibility (app.js, roles-tabs-fix.js, hyperlink-validator-state.js, doc-compare.js, roles-export-fix.js)</strong></li>
            <li><strong>FIX: Settings modal enlarged to 860px with visible gold-accented scrollbar for better navigation</strong></li>
            <li><strong>FIX: Sharing tab Connection Status now shows actual result instead of stuck 'Checking...' state</strong></li>
            <li><strong>FIX: Email to Support auto-downloads diagnostic file and includes inline health check data in email body</strong></li>
            <li><strong>FIX: Dashboard counter accuracy</strong> &mdash; dynamic checker count replaces hardcoded values</li>
            <li>UPGRADE: Help documentation version updated to 5.9.5 with refreshed content across all sections</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.4 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>FLAGSHIP: Complete export suite rebuild — 5 format options (DOCX, PDF Report, Excel, CSV, JSON) with pre-export filtering</li>
            <li><strong>NEW: PDF Report export</strong> &mdash; server-side reportlab generation with AEGIS branded cover page, executive summary, severity/category breakdown, full issue details</li>
            <li><strong>NEW: Pre-export filter panel</strong> &mdash; filter by severity and category with chip-based multi-select and live preview count</li>
            <li><strong>NEW: Excel (XLSX) format card added to export modal</strong> &mdash; detailed multi-sheet workbook with charts and metadata</li>
            <li><strong>NEW: Export progress overlay</strong> &mdash; glassmorphism card with animated progress bar and format-specific messaging</li>
            <li><strong>NEW: review_report.py module</strong> &mdash; ReviewReportGenerator class with cover page, severity distribution, category breakdown, issue detail tables</li>
            <li><strong>NEW: export-suite.css</strong> &mdash; dedicated stylesheet for export modal enhancements, filter chips, progress overlay, dark mode support</li>
            <li><strong>NEW: POST /api/export/pdf endpoint</strong> &mdash; server-side PDF generation with filter support and AEGIS branding</li>
            <li><strong>FIX: PDF source files now default to PDF Report format instead of disabled DOCX</strong></li>
            <li><strong>FIX: Export filters (severity + category) applied client-side before sending to any backend endpoint</strong></li>
            <li><strong>FIX: JSON export now includes filters_applied metadata when filters are active</strong></li>
            <li><strong>FIX: Fix Assistant v2 field mapping</strong> &mdash; normalized original_text/replacement_text with safe fallbacks for both v2 and legacy formats</li>
            <li><strong>FIX: Fix Assistant Done event now properly updates export modal launcher stats (selected count, fixable count)</strong></li>
            <li><strong>FIX: Fix Assistant close/done now re-shows export modal (was lost because FA's showModal() closes other modals)</strong></li>
            <li><strong>FIX: Rejected fixes from Fix Assistant now sent as comment_only_issues for DOCX margin comments</strong></li>
            <li><strong>FIX: Fix Assistant state persistence</strong> &mdash; re-opening export modal restores previous review stats</li>
            <li><strong>FIX: handleFinishReview() now correctly populates State.selectedFixes using actual fix indices from decisions Map</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.3 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>REDESIGN: Settings modal completely rebuilt — 9 organized tabs with card-based layout, toggle switches, glassmorphism styling</li>
            <li><strong>NEW: Dedicated Network &amp; Auth settings tab</strong> &mdash; SSL/proxy, client certificates, hyperlink validation mode consolidated</li>
            <li><strong>NEW: Settings use CSS class-based tab switching (.active-tab) instead of inline display styles (Lesson 2)</strong></li>
            <li><strong>NEW: Data Management tab compact redesign with danger zone for factory reset</strong></li>
            <li><strong>NEW: Diagnostics tab shows error/warning/request stat cards with health check and email-to-support button</strong></li>
            <li><strong>NEW: Role template JSON import</strong> &mdash; Import Decisions now accepts role_dictionary_import format from exported HTML templates</li>
            <li><strong>FIX: Function category grandchild badges show parent code abbreviation (e.g., PS-FFS shows 'PS' not 'PF')</strong></li>
            <li><strong>FIX: Review page category filters populated correctly</strong> &mdash; legacy dead containers replaced with unified dropdown route</li>
            <li><strong>FIX: FileRouter now covers routes/, hyperlink_validator/, and nlp/ flat-file prefixes for updates</strong></li>
            <li><strong>FIX: Role source viewer category change and tag removal now show error toasts on failure</strong></li>
            <li><strong>FIX: Settings delete buttons show correct short labels in finally blocks matching new compact UI</strong></li>
            <li><strong>FIX: Installer scripts updated to v5.9.3</strong> &mdash; uses packaging/requirements-windows.txt, verifies auth packages, OneDrive path note added</li>
            <li><strong>FIX: Offline installer version bumped to v5.9.3 with auth package verification</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.2 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: Scan history 'Load this scan' no longer shows [object Object]</strong> &mdash; structured error objects now properly extracted (Lesson 13)</li>
            <li><strong>FIX: Statement source viewer edit mode no longer gets stuck after save failure</strong> &mdash; editMode resets on all exit paths</li>
            <li><strong>FIX: SIPOC role_source column migration uses PRAGMA table_info() check instead of catching ALTER TABLE errors</strong></li>
            <li><strong>FIX: Fix Impact Analysis text no longer truncated</strong> &mdash; removed overflow:hidden, max-height caps, and nowrap/ellipsis from category names</li>
            <li><strong>FIX: Scan re-upload now works after first scan completes</strong> &mdash; resetUploadState() called on all completion/failure/cancel paths</li>
            <li><strong>FIX: Statement Forge auto-extraction now shows toast feedback: count of statements found or warning if module unavailable</strong></li>
            <li><strong>FIX: Metrics &amp; Analytics shows descriptive empty state messages instead of blank panel when data is missing or API fails</strong></li>
            <li><strong>FIX: DOCX export now falls back to lxml XML-based comments when COM/Word unavailable, with detailed error propagation</strong></li>
            <li><strong>FIX: Export error messages now include specific engine errors instead of generic 'Failed to create marked document'</strong></li>
            <li><strong>FIX: Frontend export handler safely parses non-JSON error responses and validates blob size before download</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.1 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: Corporate network URLs (*.northgrum.com, *.myngc.com) no longer marked BROKEN</strong> &mdash; reclassified as AUTH_REQUIRED with 'requires VPN' message</li>
            <li><strong>FIX: ConnectionError classification improved</strong> &mdash; timeout-like errors now correctly categorized as TIMEOUT instead of BROKEN</li>
            <li>ENHANCEMENT: categorize_domain() now recognizes NGC corporate domains (myngc.com, northgrum.com, sharepoint.us) as 'internal'</li>
            <li>ENHANCEMENT: HTML export report and donut chart now include Auth Required as a separate status category</li>
            <li>ENHANCEMENT: UI warning banner when Windows Auth mode is selected but requests-negotiate-sspi not installed</li>
            <li>PACKAGING: Added requests-negotiate-sspi, requests-ntlm, pyspnego, pywin32 wheels for Windows SSO auth</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.9.0 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>FIX (CRITICAL): SemanticAnalyzer duplicate detection was silently broken — wrapper called dict methods on List[DuplicateGroup], now iterates dataclass objects correctly</li>
            <li><strong>FIX: Added response.ok checks to 12 unprotected fetch() calls across 7 JS files</strong> &mdash; prevents silent failures on HTTP errors</li>
            <li><strong>FIX: Null guards added to 3 querySelector calls in role-source-viewer.js that could crash on missing DOM elements</strong></li>
            <li><strong>FIX: Dark mode contrast for .batch-score.grade-c</strong> &mdash; dark text on gold was unreadable, now white</li>
            <li>ENHANCEMENT: Cross-checker dedup normalization expanded from 8 to 27 entries — covers passive voice, grammar, spelling, references, prose style, and acronym variants</li>
            <li>ENHANCEMENT: Scoring algorithm now applies category concentration discount — 10 issues of the same type count less than 10 diverse issues (diminishing returns via logarithmic scaling)</li>
            <li>ACCESSIBILITY: Dark mode consistency for progress-3d-text and progress-3d-info indicators</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.8.2 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li><strong>FIX: ReportLab PDF crash on role names with HTML-like text</strong> &mdash; added XML entity sanitization</li>
            <li><strong>FIX: CSRF header typo in mass-statement-review.js (X-CSRFToken → X-CSRF-Token)</strong></li>
            <li><strong>FIX: Help docs referenced non-existent /api/metrics/analytics endpoint</strong></li>
            <li>ACCESSIBILITY: prefers-reduced-motion added to 10 additional CSS feature files (19 total)</li>
            <li>ENHANCEMENT: SVO extraction now uses spaCy dependency parsing for better requirement analysis</li>
            <li>AUDIT: Full production hardening — backend routes, security, frontend, library integration</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.8.1 <span class="changelog-date">February 17, 2026</span></h3>
        <ul>
            <li>FEATURE: Document Compare now includes a master document selector dropdown — switch between any comparable document without closing the modal</li>
            <li><strong>FIX: Document Compare no longer locks you into the pre-selected document</strong> &mdash; all 15+ documents with multiple scans are accessible from the header dropdown</li>
            <li>UI: New document selector styled for both light and dark mode, auto-selects newest scan pair on document switch</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.8.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li>FEATURE: Cross-checker deduplication now normalizes categories — issues flagged by multiple checkers under different category names (e.g., 'Requirement Traceability' + 'INCOSE Compliance') are properly deduplicated</li>
            <li>FEATURE: Document-type-aware suppression — requirements documents auto-suppress noise issues (noun phrase density, readability scores for domain vocabulary, per-paragraph INCOSE repeats)</li>
            <li>NEW CHECKER: Directive Verb Consistency — flags documents that mix shall/should/must/will/require without a definitions section explaining the convention</li>
            <li>NEW CHECKER: Unresolved Cross-Reference — flags dangling references like 'the approved procurement schedule' or 'applicable safety requirements' that don't cite specific document IDs</li>
            <li><strong>FIX: Spelling dictionary expanded with aerospace/PM terms</strong> &mdash; 'deliverables', 'baselines', 'procurement', 'workaround', NASA acronyms (CDR, PDR, SRR, FMEA, etc.)</li>
            <li>Total checkers: 111 (was 109)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.7.2 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li><strong>FIX: detectCurrentSection() no longer falsely matches Statement Forge</strong> &mdash; removed el.style.display check, uses only .active class like all other modals</li>
            <li><strong>FIX: Landing page detection now uses body.classList.contains('landing-active') instead of offsetParent (which fails on position:fixed elements)</strong></li>
            <li><strong>FIX: Help panel section nav now dismisses landing page before opening modals</strong> &mdash; modals no longer hidden behind landing overlay</li>
            <li><strong>FIX: Added batch and portfolio to detectCurrentSection() checks array (were missing)</strong></li>
            <li>REFACTOR: Moved landing page dismissal to top of _navigateToSection() for all non-landing sections</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.7.1 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li><strong>FIX: Folder scan background thread no longer stalls</strong> &mdash; added per-file timeout (5 min), chunk-level timeout, and try/except around future.result()</li>
            <li><strong>FIX: Elapsed time now computed LIVE in progress endpoint from started_at</strong> &mdash; no longer freezes when a file takes a long time</li>
            <li>REFACTOR: Extracted _update_scan_state_with_result() helper — cleaner code, eliminates deep indentation in background thread</li>
            <li><strong>FIX: Current file now shows chunk contents (up to 3 filenames) while processing, not just last-completed file</strong></li>
            <li><strong>FIX: Chunk timeout gracefully marks remaining files as errors and continues to next chunk instead of crashing</strong></li>
            <li><strong>FIX: Spotlight CSS overlay background set to transparent</strong> &mdash; eliminates double-dimming over SVG mask cutout</li>
            <li><strong>FIX: Tooltip positionTooltip() rewrite</strong> &mdash; centers on target, prefers target-edge alignment, flips vertically, final viewport safety clamp</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.7.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li><strong>PERF: Flask debug mode now runs with threaded=True</strong> &mdash; server no longer blocks during long-running folder scans</li>
            <li>FEAT: Async folder scan with real-time progress polling — POST /folder-scan-start returns scan_id immediately, GET /folder-scan-progress/&lt;scan_id&gt; provides per-file updates</li>
            <li>UI: Folder scan progress dashboard — live per-file status rows, progress bar, elapsed/remaining time, speed, chunk tracking (reuses bpd-* batch dashboard CSS)</li>
            <li><strong>FIX: Acronym dedup key simplified to (paragraph_index, category, flagged_text)</strong> &mdash; removes rule_id and message so cross-checker duplicates are properly caught (~20-30% fewer duplicate issues)</li>
            <li><strong>FIX: Removed broken option_mapping 'check_enhanced_acronyms' → 'enhanced_acronyms' (non-existent checker key)</strong></li>
            <li><strong>FIX: Hardcoded Mac paths replaced with pathlib-based relative paths in run_enhancement_analysis.py, defense_role_analysis.py, defense_role_analysis_expanded.py</strong></li>
            <li><strong>NEW: restart_aegis.bat for Windows</strong> &mdash; stops port 5050 process and restarts with debug mode</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.6.1 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li><strong>FIX: ReviewIssue .get() crash in core.py</strong> &mdash; non-NLP checkers produce dataclass objects but scoring/dedup/ID-assignment used dict .get(). Added normalization step in review_document() postprocessing</li>
            <li><strong>FIX: Folder scan _review_single() also normalizes issues to dicts for aggregation and JSON serialization</strong></li>
            <li><strong>FIX: All downstream code (_calculate_score, _deduplicate_issues, _assign_issue_ids, _count_by_severity, _count_by_category, enhance_issue_context) now receives dicts</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.6.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li>GUIDE: Complete rewrite of guide-system.js v2.0.0 — real content for all 11 sections (landing, review, batch, roles, forge, validator, compare, metrics, history, settings, portfolio)</li>
            <li>GUIDE: Animated Demo Player system — auto-playing live walkthroughs with typewriter narration, spotlight overlay, and step-by-step scene navigation</li>
            <li>GUIDE: Demo player controls — play/pause, previous/next, speed selector (0.5x–2x), progress bar with step counter, LIVE DEMO badge</li>
            <li>GUIDE: SVG mask spotlight system for tour and demo element highlighting with smooth transitions</li>
            <li>GUIDE: Section navigation grid in help panel — click any section to jump directly to its content</li>
            <li>GUIDE: Contextual help beacon with pulse animation, auto-detects current section</li>
            <li>GUIDE: Full Tour and Full Demo modes — walk through every section sequentially with auto-navigation between modals</li>
            <li>GUIDE: Each section includes whatIsThis descriptions, keyActions with icons, proTips, tourSteps targeting real DOM selectors, and demoScenes</li>
            <li>UI: Settings toggle to globally enable/disable guide system (Settings &gt; General &gt; Show help guide &amp; tours)</li>
            <li>UI: Guide enabled state persisted via localStorage, synced with settings checkbox on page load</li>
            <li>CSS: Guide system z-index hierarchy — beacon=150000, demoBar=149800, panel=149500, spotlight=149000 (above all app modals)</li>
            <li>CSS: Demo bar with glass-morphism dark UI, gradient progress bar, animated LIVE DEMO badge</li>
            <li>CSS: Section navigation grid with hover effects and active state indicators</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.5.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li>BATCH: Server-side recursive folder scanning — scan entire document repositories with nested subdirectories</li>
            <li>BATCH: New /api/review/folder-scan endpoint with chunked ThreadPoolExecutor processing and per-chunk gc.collect()</li>
            <li>BATCH: New /api/review/folder-discover endpoint for dry-run preview before committing to full scan</li>
            <li>BATCH: Smart file discovery — skips hidden dirs, empty files, files &gt;100MB, common non-doc directories</li>
            <li>BATCH: Folder scan UI in batch upload modal — enter a server path, preview files, then scan all</li>
            <li>BATCH: Increased batch limits from 10/100MB to 50/500MB per upload batch for large repositories</li>
            <li>BATCH: Chunked processing (5 files per chunk, 3 concurrent) with memory cleanup between chunks</li>
            <li>BATCH: Comprehensive results aggregation — grade distribution, severity breakdown, role discovery across all docs</li>
            <li>BATCH: Graceful error handling — individual file errors don't stop the whole scan</li>
            <li>TEST: Local test script (test_scan_local.py) for single file × 5 and batch folder verification</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.4.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li>PERFORMANCE: Eliminated dark mode flash of light content (FOUC) — inline CSS variables + data-theme attribute set before any stylesheet loads</li>
            <li>PERFORMANCE: Deferred 30+ feature module scripts with defer attribute — initial paint 40-60% faster</li>
            <li>PERFORMANCE: Async CSS loading for 13 feature stylesheets using media='print' onload pattern — only critical CSS blocks render</li>
            <li>PERFORMANCE: Batch scan processing now multi-threaded via ThreadPoolExecutor (up to 3 concurrent documents)</li>
            <li><strong>FIX: Resolved terminology_consistency naming conflict</strong> &mdash; v3.3.0 and v5.3.0 checkers now have distinct keys (terminology_consistency vs wordnet_terminology)</li>
            <li>NLP: 11 new v5.3.0 spaCy Ecosystem checkers fully integrated with UI toggles</li>
            <li>NLP: 6 new v5.2.0 Advanced NLP Enhancement Suite checkers with graceful fallback</li>
            <li>NLP: 8 new checker files: negation, text_metrics, terminology_consistency, subjectivity, vocabulary, yake, similarity, advanced_analysis</li>
            <li>NLP: New libraries integrated: negspacy, textdescriptives, spacy-wordnet, spacytextblob, lexical_diversity, yake</li>
            <li>CHECKERS: Total checker count now 100+ (98 UI-controlled + 7 always-on)</li>
            <li>INSTALL: Windows x64 wheels for all new NLP dependencies included for air-gapped deployment</li>
            <li>UI: v5.3.0 spaCy Deep Analysis section in Settings with 4 subcategories and 11 checkboxes</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.3.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li>NLP: spaCy Ecosystem &amp; Deep Analysis Suite — 8 new checker files with 11 checker keys</li>
            <li>NLP: Negation detection using negspacy + spaCy dependency tree for scope analysis</li>
            <li>NLP: Text quality metrics via textdescriptives pipeline (readability, coherence, POS, quality)</li>
            <li>NLP: Sentence complexity scoring using dependency tree depth and clause count</li>
            <li>NLP: Terminology consistency via spacy-wordnet synonym detection + curated aerospace groups</li>
            <li>NLP: Subjectivity and tone detection using spacytextblob sentiment analysis</li>
            <li>NLP: Lexical diversity metrics (MTLD, HD-D, TTR) for boilerplate and copy-paste detection</li>
            <li>NLP: YAKE statistical keyword extraction with domain coverage and distribution analysis</li>
            <li>NLP: Requirement similarity using sentence-transformers with TF-IDF fallback</li>
            <li>NLP: Cross-sentence coherence, defined-before-used enforcement, quantifier precision checking</li>
            <li>INSTALL: 6 new dependencies: negspacy, textdescriptives, spacy-wordnet, spacytextblob, lexical_diversity, yake</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.2.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li>NLP: Advanced NLP Enhancement Suite — 6 optional checkers with graceful fallback</li>
            <li>NLP: Coreference resolution using coreferee for ambiguous pronoun detection</li>
            <li>NLP: Advanced prose quality checking using proselint (clichés, hedging, redundancy)</li>
            <li>NLP: Document verbosity and summarization analysis using sumy</li>
            <li>NLP: Keyword extraction and complexity analysis using textacy (SGRANK algorithm)</li>
            <li>NLP: INCOSE requirements compliance checking</li>
            <li>NLP: Semantic role labeling for requirement structure analysis</li>
            <li><strong>FIX: Excel/CSV export BytesIO bug</strong> &mdash; make_response pattern for binary content</li>
            <li><strong>FIX: UTF-8 BOM added to CSV exports for Windows Excel compatibility</strong></li>
            <li><strong>FIX: HTML report charset meta tag for proper encoding display</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.1.0 <span class="changelog-date">February 16, 2026</span></h3>
        <ul>
            <li>SECURITY: Added @require_csrf to 9 unprotected POST routes (SOW, presets, analyzers, diagnostics)</li>
            <li>SECURITY: Fixed CSRF token handling in 18+ JavaScript functions using fresh token pattern</li>
            <li>SECURITY: Added _getFreshCsrf() helper for data management operations</li>
            <li>ARCHITECTURE: Fixed spaCy singleton pattern for shared model instances (performance improvement)</li>
            <li>QUALITY: Improved issue deduplication key (50→80 chars with rule_id)</li>
            <li>QUALITY: Added 18 aerospace adjectival participles to passive voice whitelist</li>
            <li>QUALITY: All 83 checkers verified working with 14 new UI toggles added</li>
            <li>ACCESSIBILITY: Added 134 aria-label attributes across all UI elements</li>
            <li>ACCESSIBILITY: Added role='dialog' and aria-modal to 28 modals</li>
            <li>ACCESSIBILITY: Added role='tablist/tab/tabpanel' to all tab navigation systems</li>
            <li>ACCESSIBILITY: Added aria-hidden to 116 decorative icons</li>
            <li>ACCESSIBILITY: WCAG 2.1 Level A compliance improvements</li>
            <li>PRINT: New print.css stylesheet for optimized document printing</li>
            <li>PRINT: Hides non-printable elements (sidebar, toolbar, toasts)</li>
            <li>PRINT: Optimizes tables, typography, and page breaks for print</li>
            <li>PRINT: Includes URL display after links for reference</li>
            <li>UI: Fixed folder browse button - now opens native OS folder picker via backend API</li>
            <li>UI: Fixed dropdown z-index conflict with toast notifications</li>
            <li>UI: Added dark mode overrides for modal radio card components</li>
            <li>UI: Fixed popup blocker vulnerability in statement history exports</li>
            <li>DATA: Fixed all 5 data management handlers to use fresh CSRF tokens</li>
            <li>DATA: Clear scan history, statements, roles, learning, and factory reset all fixed</li>
            <li>INSTALL: Added 195 Windows x64 wheel files for air-gapped offline installation</li>
            <li>INSTALL: Includes numpy, pandas, scipy, scikit-learn, spaCy, docling, and more</li>
            <li>INSTALL: torch (139MB) available via GitHub Release download</li>
            <li>INSTALL: Added download_win_wheels.py script for connected Windows environments</li>
            <li>INSTALL: Updated install_offline.bat to support both wheel directories</li>
            <li><strong>FIX: Landing page showing 0 roles (fallback from role_dictionary to roles table)</strong></li>
            <li><strong>FIX: Source document not loading when clicking roles in viewer</strong></li>
            <li><strong>FIX: Updater spinning forever (15s timeout with abort controller)</strong></li>
            <li><strong>FIX: Diagnostic email export (GET→POST with fresh CSRF)</strong></li>
            <li><strong>FIX: Version display stale after update (import-time caching)</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v5.0.0 <span class="changelog-date">February 15, 2026</span></h3>
        <ul>
            <li>ARCHITECTURE: Review jobs now run in separate PROCESS (multiprocessing.Process) instead of threading.Thread</li>
            <li>ARCHITECTURE: Flask server stays fully responsive during large document analysis (separate GIL)</li>
            <li>ARCHITECTURE: Worker process crash isolation — if review crashes, Flask keeps running</li>
            <li>ARCHITECTURE: Per-document timeout (600s default) with graceful process termination</li>
            <li>ARCHITECTURE: Progress updates via multiprocessing.Queue with monitor thread bridge pattern</li>
            <li>ARCHITECTURE: Results written to temp JSON file (handles large documents without queue limits)</li>
            <li>ARCHITECTURE: Legacy threading fallback if multiprocessing unavailable</li>
            <li><strong>FIX: Role extraction 'Validation' false positive</strong> &mdash; single-word variants no longer verify compound roles</li>
            <li><strong>FIX: Removed 'nasa' and 'government' from KNOWN_ROLES (moved to ORGANIZATION_ENTITIES filter)</strong></li>
            <li><strong>FIX: Removed duplicate role entries (contracting officer, contractor, technical authority, government)</strong></li>
            <li><strong>FIX: Discovery mode now filters organization entities, low-confidence roles, and stopword roles</strong></li>
            <li><strong>FIX: PDF multi-column layout detection with extraction quality warning</strong></li>
            <li><strong>NEW: ORGANIZATION_ENTITIES filter set</strong> &mdash; prevents organizations from being extracted as roles</li>
            <li><strong>NEW: 30+ missing aerospace roles added (technical fellow, mission systems engineer, failure review board, etc.)</strong></li>
            <li><strong>NEW: 50+ expanded SINGLE_WORD_EXCLUSIONS preventing common English words from extraction</strong></li>
            <li><strong>NEW: Confidence threshold filter (&lt; 0.4) removes low-quality role extractions</strong></li>
            <li><strong>NEW: Document type classification in Statement Forge export (requirements/guidance/descriptive/informational)</strong></li>
            <li><strong>NEW: Document classification detail text explaining directive distribution</strong></li>
            <li><strong>NEW: Column layout detection in PDF extraction with quality warnings</strong></li>
            <li>IMPROVED: Role extractor v3.5.0 with 3-layer post-verification filtering</li>
            <li>IMPROVED: STRICT mode also skips organization entities</li>
            <li>IMPROVED: pymupdf4llm extraction uses write_images=False for faster processing</li>
            <li>TESTED: Full NASA SE Handbook (297 pages) — role false positives reduced from 44% to &lt;5%</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.9.9 <span class="changelog-date">February 15, 2026</span></h3>
        <ul>
            <li>FEATURE: Statement Source Viewer with highlight-to-select editing for inline statement creation</li>
            <li><strong>FIX: SOW generation 500 error</strong> &mdash; missing timezone import in datetime operations (timezone.utc)</li>
            <li><strong>FIX: Document Compare now auto-selects oldest doc on left, newest on right when opened</strong></li>
            <li><strong>FIX: Document Compare auto-comparison triggers immediately without manual selection</strong></li>
            <li><strong>FIX: API error responses now include structured format with proper message extraction</strong></li>
            <li><strong>FIX: Toast notifications show meaningful error text instead of '[object Object]'</strong></li>
            <li><strong>FIX: Template files now correctly extract error.message from structured error objects</strong></li>
            <li><strong>NEW: getErrorMessage() utility function for safe message extraction from error objects</strong></li>
            <li><strong>NEW: Statement Source Viewer integrates with Statement Forge history context</strong></li>
            <li><strong>NEW: Document profile settings now persist across server restarts</strong></li>
            <li><strong>NEW: User preferences cached in localStorage with server-side backup</strong></li>
            <li>IMPROVED: Particle effects transparency adjusted for dark background visibility</li>
            <li>IMPROVED: Batch review rendering performance for 100+ statements</li>
            <li>IMPROVED: Session logging with correlation IDs for API response tracking</li>
            <li>IMPROVED: Windows compatibility — file permission operations (chmod) now platform-aware</li>
            <li>IMPROVED: Windows platform detection using os.name == 'nt' for Windows-specific paths</li>
            <li>IMPROVED: Cross-platform path handling with pathlib.Path throughout codebase</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.9.5 <span class="changelog-date">February 15, 2026</span></h3>
        <ul>
            <li><strong>FIX: Version display stuck on 4.7</strong> &mdash; root cause was duplicate version.json files (root vs static/)</li>
            <li><strong>FIX: Import-time version caching in config_logging.py</strong> &mdash; VERSION constant was stale after updates</li>
            <li><strong>FIX: Cache-busting regex in core_routes.py now handles existing ?v= params and adds missing ones</strong></li>
            <li><strong>FIX: Stripped all hardcoded ?v= params from index.html</strong> &mdash; middleware handles cache-busting dynamically</li>
            <li><strong>NEW: get_version() function in config_logging.py</strong> &mdash; reads version.json fresh from disk every call</li>
            <li><strong>NEW: Client-side version fetch priority changed to /api/version first, /static/version.json as fallback</strong></li>
            <li>IMPROVED: core_routes.py index() middleware uses regex for consistent ?v= injection on all JS/CSS</li>
            <li>IMPROVED: /api/version and /api/health endpoints now use get_version() instead of stale constant</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.9.0 <span class="changelog-date">February 15, 2026</span></h3>
        <ul>
            <li><strong>FIX: Landing page tiles/metrics empty on load</strong> &mdash; async init race condition in show()/init() chain</li>
            <li><strong>FIX: Session restore path skipped init(), leaving landing page uninitialized for later navigation</strong></li>
            <li><strong>FIX: Made show() async with await init(); removed redundant init() call in app.js</strong></li>
            <li><strong>FIX: Toast z-index too low (2500)</strong> &mdash; raised to 200000 so toasts always appear above modals (z-index 10000)</li>
            <li>IMPROVED: Offline wheel packaging for air-gapped deployment (bundled .whl files for all dependencies)</li>
            <li>IMPROVED: restart_aegis.sh script for one-click server restart on macOS</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.8.0 <span class="changelog-date">February 14, 2026</span></h3>
        <ul>
            <li><strong>FIX: Flask blueprint import scope</strong> &mdash; data_routes.py used bare app.logger instead of current_app.logger</li>
            <li><strong>FIX: Report download popup blocked</strong> &mdash; replaced window.open() after await with hidden iframe approach</li>
            <li><strong>FIX: Report generation 500 errors</strong> &mdash; catch Exception instead of just ImportError in three report endpoints</li>
            <li><strong>FIX: Generate Reports SQL queries referenced non-existent roles.document_id</strong> &mdash; now JOINs through document_roles</li>
            <li><strong>FIX: Roles Studio Overview empty from dashboard tile</strong> &mdash; landing-page.js now calls showRolesModal() override</li>
            <li><strong>FIX: Inline style.display conflicts with CSS !important</strong> &mdash; replaced with classList and removeProperty('display')</li>
            <li>IMPROVED: Production logging with structured error tracking and correlation IDs</li>
            <li>IMPROVED: E2E audit across all features — verified all entry points (sidebar + dashboard tiles) call same functions</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.7.0 <span class="changelog-date">February 14, 2026</span></h3>
        <ul>
            <li>REFACTOR: Database Access Layer — replaced 99 scattered sqlite3.connect() calls across 7 files with db_connection() context manager pattern</li>
            <li><strong>NEW: db_connection() context manager in scan_history.py</strong> &mdash; auto-commits on success, rolls back on exception, always closes, sets row_factory=sqlite3.Row and PRAGMA journal_mode=WAL</li>
            <li><strong>NEW: ScanHistoryDB.connection() convenience method wrapping db_connection(self.db_path)</strong></li>
            <li><strong>NEW: HyperlinkValidatorStorage.connection() method with local db_connection context manager</strong></li>
            <li>MIGRATED: scan_history.py — 23 calls converted to self.connection()</li>
            <li>MIGRATED: app.py — 49 calls converted to db.connection() / db_connection(path)</li>
            <li>MIGRATED: hyperlink_validator/storage.py — 17 calls converted to self.connection()</li>
            <li>MIGRATED: document_compare/routes.py — 6 calls with import fallback pattern</li>
            <li>MIGRATED: role_extractor_v3.py — 2 calls with local context manager</li>
            <li>MIGRATED: update_manager.py — 1 call via imported db_connection</li>
            <li>MIGRATED: diagnostic_export.py — 1 call with local context manager</li>
            <li><strong>FIX: Eliminated ~60% of DB calls that lacked proper exception handling</strong></li>
            <li><strong>FIX: Eliminated ~65% of DB calls that risked connection leaks (no finally: conn.close())</strong></li>
            <li><strong>FIX: Removed decompiler artifact __import__('sqlite3').connect() pattern in app.py</strong></li>
            <li><strong>FIX: CSRF header typo in roles.js and role-source-viewer.js</strong> &mdash; X-CSRFToken corrected to X-CSRF-Token (3 occurrences)</li>
            <li><strong>FIX: Scan history missing statement_count field in get_scan_history()</strong></li>
            <li><strong>FIX: Document compare missing compare_scan_statements method</strong></li>
            <li><strong>FIX: Heatmap flickering</strong> &mdash; switched from display:none to visibility:hidden for smooth transitions</li>
            <li><strong>FIX: Graph layout buttons missing event listeners after decompiler recovery</strong></li>
            <li><strong>FIX: Generate reports buttons not working after decompiler recovery</strong></li>
            <li><strong>FIX: RACI matrix and module hover flickering caused by transition:all</strong></li>
            <li><strong>FIX: Role-Doc Matrix Excel export was producing CSV instead of XLSX</strong></li>
            <li>IMPROVED: All database operations now have consistent error handling and automatic cleanup</li>
            <li>IMPROVED: WAL journal mode applied uniformly via context manager (was inconsistent before)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.6.2 <span class="changelog-date">February 13, 2026</span></h3>
        <ul>
            <li>FEATURE: Deep Validate — headless browser rescan now merges recovered URLs back into results, updating stats, filters, and visualizations in real time</li>
            <li>FEATURE: Domain Filter Dropdown — filter validation results by specific domain with searchable dropdown and clear button</li>
            <li>FEATURE: Clickable Stat Tiles — click any summary stat (Excellent, Broken, Blocked, etc.) to filter results to that status category</li>
            <li><strong>NEW: Export Highlighted fix</strong> &mdash; ArrayBuffer backup ensures DOCX export works even when original file blob is unavailable</li>
            <li><strong>NEW: Exclusion persistence to server</strong> &mdash; exclusions created from result rows are saved to the database via API, surviving sessions</li>
            <li><strong>NEW: False positive URL validation</strong> &mdash; backend test confirmed dcma.mil, faa.gov, tenable.com, cyber.mil all recover via headless browser</li>
            <li><strong>NEW: Status filter pills</strong> &mdash; click status badges in results to filter by that status type</li>
            <li><strong>NEW: _updateRescanSection() helper</strong> &mdash; dynamically shows/hides Deep Validate button based on rescan-eligible URL count</li>
            <li><strong>NEW: RESCAN_ELIGIBLE_STATUSES constant</strong> &mdash; BLOCKED, TIMEOUT, DNSFAILED, AUTH_REQUIRED, SSLERROR all eligible for deep validation</li>
            <li><strong>FIX: Headless rescan results were never merged back into state (TODO comment at line 1668</strong> &mdash; now fully implemented)</li>
            <li><strong>FIX: Rescan eligibility was too narrow</strong> &mdash; only BLOCKED/TIMEOUT/DNSFAILED; now includes AUTH_REQUIRED and SSLERROR</li>
            <li><strong>FIX: Rescan section missing from non-Excel validation flow</strong> &mdash; renderSummary() now also updates rescan section</li>
            <li><strong>FIX: History panel compressing HV layout on wide displays</strong> &mdash; translateX(100%) insufficient on 2500px+ viewports; now uses display:none when closed</li>
            <li><strong>FIX: Stat count accuracy</strong> &mdash; summary counts now correctly reflect merged rescan results</li>
            <li>IMPROVED: Deep Validate UI — renamed from 'Rescan Blocked' to 'Deep Validate' with scan-search icon and purple accent</li>
            <li>IMPROVED: Rescan section description updated to mention blocked, timeout, and auth-wall URLs</li>
            <li>IMPROVED: Domain filter repopulates after rescan to reflect recovered URL domains</li>
            <li>IMPROVED: Recovered URLs preserve Excel-specific fields (sheet_name, cell_address, display_text, link_source, context)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.6.1 <span class="changelog-date">February 13, 2026</span></h3>
        <ul>
            <li>FEATURE: Metrics &amp; Analytics Command Center — standalone modal with 4-tab layout (Overview, Quality, Roles, Documents)</li>
            <li><strong>NEW: Overview tab with hero stats, quality trend chart, score distribution, severity breakdown, scan activity heatmap</strong></li>
            <li><strong>NEW: Quality tab with score distribution bar chart, issue category radar, top issues table</strong></li>
            <li><strong>NEW: Roles tab with role frequency chart, deliverables vs non-deliverables comparison</strong></li>
            <li><strong>NEW: Documents tab with per-document score history, detail drill-down panels</strong></li>
            <li><strong>NEW: Scan activity heatmap with custom SVG tooltip and hover overlay</strong></li>
            <li><strong>NEW: Drill-down panels on hero stats and document cards for detailed breakdowns</strong></li>
            <li><strong>FIX: Scan cancel button not working</strong> &mdash; cancelCurrentJob was not exposed as global function</li>
            <li><strong>FIX: Scan Progress Dashboard cancel leaves UI hung</strong> &mdash; loading overlay and progress dashboard now cleaned up on cancel</li>
            <li><strong>FIX: Scan History/Roles Studio showing doc review background</strong> &mdash; modals now keep dashboard visible behind them</li>
            <li><strong>FIX: Landing page tiles hiding dashboard when opening modals</strong> &mdash; stopped calling hide() for windowed module modals</li>
            <li><strong>FIX: Nav bar module buttons not restoring dashboard background</strong> &mdash; now show landing page when not already active</li>
            <li><strong>FIX: Heatmap hover flicker</strong> &mdash; SVG overlay rect moved after cells (was rendering behind), tooltip transition removed</li>
            <li>IMPROVED: Heatmap tooltip shows instantly (no CSS opacity transition that caused rapid show/hide flicker)</li>
            <li>IMPROVED: Scan cancel cleanup is comprehensive — destroys progress dashboard, resets loading tracker, clears job state</li>
            <li>BACKEND: GET /api/metrics/analytics — aggregated analytics data from scan history</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.6.0 <span class="changelog-date">February 12, 2026</span></h3>
        <ul>
            <li>FEATURE: Statement Lifecycle Management — deduplication, review, and cleanup system for extracted statements</li>
            <li>FEATURE: Role-Statement Responsibility Interface — view, reassign, and remove statements per role in Roles Studio</li>
            <li>FEATURE: Statement Review Badges — tool-wide review status indicators (Pending/Reviewed/Rejected/Unchanged)</li>
            <li><strong>NEW: Statement fingerprinting and deduplication on rescan (unchanged statements tagged, new ones flagged)</strong></li>
            <li><strong>NEW: Statement duplicate cleanup utility</strong> &mdash; find and remove duplicate statement groups</li>
            <li><strong>NEW: Bulk statement review</strong> &mdash; batch approve/reject pending statements from overview dashboard</li>
            <li><strong>NEW: Role statements panel (S key)</strong> &mdash; modal showing all statements for a role, grouped by document</li>
            <li><strong>NEW: Bulk reassign/remove statements</strong> &mdash; select statements and reassign to different roles or remove</li>
            <li><strong>NEW: Generic role warning</strong> &mdash; banner for generic names (Personnel, Staff, etc.) that likely have misassigned statements</li>
            <li><strong>NEW: Statement-to-role tagging with autocomplete during statement edit in Document Viewer</strong></li>
            <li><strong>NEW: AEGIS.StatementReviewLookup global utility</strong> &mdash; badge rendering with 15s TTL cache</li>
            <li><strong>NEW: Clear Statement Data in Settings → Data Management</strong></li>
            <li><strong>NEW: Clear Role Dictionary handler wired up in Settings → Data Management</strong></li>
            <li><strong>NEW: Clear Learning Data handler wired up in Settings → Data Management</strong></li>
            <li><strong>NEW: Data counts displayed in Data Management (statement count, role count)</strong></li>
            <li><strong>FIX: Impact Analyzer readability</strong> &mdash; increased font sizes and padding for path-to-100 bars</li>
            <li><strong>FIX: Factory reset now clears ALL tables (was missing role_function_tags, role_relationships, function_categories, etc.)</strong></li>
            <li><strong>FIX: Compare feature CSRF failures</strong> &mdash; added /status endpoint + retry-after-refresh logic</li>
            <li><strong>FIX: Settings save UX</strong> &mdash; dirty tracking with pulse animation, unsaved changes warning on close</li>
            <li>BACKEND: 11 new API endpoints for statement review, dedup, role statements, and data management</li>
            <li>BACKEND: Schema migration adds review_status, confirmed, reviewed_by, reviewed_at, fingerprint to scan_statements</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.5.2 <span class="changelog-date">February 10, 2026</span></h3>
        <ul>
            <li><strong>FIX: Quality score always showing N/A</strong> &mdash; frontend used wrong field name (quality_score vs score)</li>
            <li><strong>FIX: .doc files now return clear error message instead of failing silently when LibreOffice unavailable</strong></li>
            <li><strong>FIX: Infinite recursion crash in _log() fallback when config_logging import fails</strong></li>
            <li><strong>FIX: SessionManager.set() AttributeError</strong> &mdash; method didn't exist, replaced with update()</li>
            <li><strong>FIX: DoclingAdapter crash when table headers are None</strong> &mdash; added null-safe guards</li>
            <li><strong>FIX: Missing @app.route decorator on /api/filter endpoint</strong> &mdash; function was unreachable</li>
            <li><strong>FIX: File handle leaks in html_preview ZIP detection</strong> &mdash; now uses context manager</li>
            <li><strong>FIX: Docling subprocess queue race condition</strong> &mdash; replaced empty()+get_nowait() with get(timeout=2)</li>
            <li><strong>FIX: fitz.Document handle leak on corrupt PDFs</strong> &mdash; now uses context manager</li>
            <li><strong>FIX: Empty/unreadable documents now return a clear warning instead of false 100 score</strong></li>
            <li>IMPROVED: DOCX Docling timeout reduced to 60s (from 120s) — DOCX extracts faster than PDFs</li>
            <li>REMOVED: Deprecated _run_with_timeout() function and ThreadPoolExecutor import (dead code cleanup)</li>
            <li>REMOVED: Unused concurrent.futures import that caused confusion about parallel checker support</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.5.1 <span class="changelog-date">February 10, 2026</span></h3>
        <ul>
            <li>FEATURE: Hierarchical Edge Bundling (HEB) — new default relationship graph layout with circular node arrangement and bundled edges</li>
            <li>FEATURE: Semantic Zoom (Level-of-Detail) — zoom-based progressive disclosure graph with 3 LOD levels</li>
            <li><strong>NEW: Bundling Tension slider</strong> &mdash; adjusts edge bundling from 0 (straight lines) to 1 (maximum bundling)</li>
            <li><strong>NEW: Document group arcs</strong> &mdash; colored arc segments around the circle showing which document each role belongs to</li>
            <li><strong>NEW: Bridge role visualization</strong> &mdash; cross-document relationships appear as long bundled curves spanning the circle</li>
            <li><strong>NEW: Layout dropdown updated with Edge Bundling (default), Semantic Zoom, Force-Directed (Classic), Bipartite options</strong></li>
            <li><strong>NEW: HEB-specific legend with arc, bundled edge, and brightness indicators</strong></li>
            <li><strong>NEW: HEB minimap</strong> &mdash; circular dot minimap with colored document group arcs</li>
            <li>IMPROVED: All 15 existing interactions preserved in HEB (node click, hover, drill-down, breadcrumbs, weight slider, search, labels, zoom, keyboard, minimap, adjudication badges, performance mode)</li>
            <li>IMPROVED: Semantic Zoom LOD 1 (clusters), LOD 2 (nodes), LOD 3 (labels) with smooth transitions</li>
            <li>IMPROVED: HEB is inherently faster than force-directed (no simulation), thresholds raised to 300/600</li>
            <li>IMPROVED: Dark mode support for all HEB and Semantic Zoom elements</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.5.0 <span class="changelog-date">February 9, 2026</span></h3>
        <ul>
            <li>FEATURE: Scan Progress Dashboard — step-by-step checklist with sub-progress, ETA, and animations</li>
            <li>FEATURE: Landing Page Dashboard — tool launcher cards, recent documents, system stats</li>
            <li>IMPROVED: Granular progress reporting during checker execution phase</li>
            <li><strong>FIX: Statement extraction pipe artifacts (||||||) in PDFs processed by Docling</strong></li>
            <li><strong>FIX: Compare Viewer dark mode</strong> &mdash; replaced [data-theme=dark] with body.dark-mode selectors</li>
            <li><strong>FIX: Compare Viewer CSRF 403 errors</strong> &mdash; syncs token from GET responses</li>
            <li><strong>FIX: Document Viewer highlight scroll alignment</strong> &mdash; uses scrollIntoView with center positioning</li>
            <li><strong>FIX: PDF.js toggle 'not available'</strong> &mdash; added .mjs to allowed vendor extensions</li>
            <li><strong>FIX: Role Interactions empty page on drill</strong> &mdash; shows empty state when no data available</li>
            <li><strong>FIX: History tab action column cutoff</strong> &mdash; fixed table layout with explicit column widths</li>
            <li><strong>FIX: Scan processing hanging</strong> &mdash; improved cancellation checks between phases</li>
            <li>IMPROVED: Matrix animation is now default for batch processing (slower, more cinematic)</li>
            <li>IMPROVED: Batch processing dark mode text visibility</li>
            <li>IMPROVED: Removed .txt extension bypass from documentation</li>
            <li><strong>NEW: TWR.ScanProgress module</strong> &mdash; 7-step weighted progress with localStorage ETA history</li>
            <li><strong>NEW: TWR.LandingDashboard module</strong> &mdash; 6 tool cards with responsive grid layout</li>
            <li><strong>NEW: _sanitize_for_statements() fallback for Docling PDF text cleanup</strong></li>
            <li>IMPROVED: Better progress reporting during checker execution phase</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.4.0 <span class="changelog-date">February 9, 2026</span></h3>
        <ul>
            <li>FEATURE: Statement Quality Improvement — clean text for Statement Forge extraction</li>
            <li><strong>NEW: clean_full_text via mammoth when Docling is primary extractor (eliminates | and ** artifacts)</strong></li>
            <li><strong>NEW: Statement Diff Export</strong> &mdash; CSV and PDF export from Compare Viewer with AEGIS-branded report</li>
            <li><strong>NEW: Statement Search</strong> &mdash; cross-scan full-text search with debounced UI and directive filtering</li>
            <li><strong>NEW: Bulk Statement Editing</strong> &mdash; multi-select statements with batch directive/role updates</li>
            <li><strong>NEW: PDF.js Viewer</strong> &mdash; pixel-perfect PDF canvas rendering toggle in Document Viewer</li>
            <li><strong>NEW: PDF/HTML view toggle for PDF documents in Statement History</strong></li>
            <li>IMPROVED: Compare Viewer state reset prevents stale document cache between viewer sessions</li>
            <li>IMPROVED: Compare Viewer diff indicators in HTML content no longer inherit strikethrough</li>
            <li>BACKEND: GET /api/scan-history/statements/search — full-text search across all scans</li>
            <li>BACKEND: PUT /api/scan-history/statements/batch — batch update statement fields</li>
            <li>BACKEND: GET /api/scan-history/document-file — serve original document for PDF.js</li>
            <li>BACKEND: GET /api/statement-forge/compare/{id1}/{id2}/export-csv — diff export as CSV</li>
            <li>BACKEND: GET /api/statement-forge/compare/{id1}/{id2}/export-pdf — diff export as PDF</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.3.0 <span class="changelog-date">February 9, 2026</span></h3>
        <ul>
            <li>FEATURE: Document Extraction Overhaul — mammoth for DOCX→HTML, pymupdf4llm for PDF→Markdown</li>
            <li><strong>NEW: MammothDocumentExtractor class with clean semantic HTML output (no table artifacts)</strong></li>
            <li><strong>NEW: Pymupdf4llmExtractor class with structured Markdown extraction for PDFs</strong></li>
            <li><strong>NEW: html_preview field stored in scan results for rich document rendering</strong></li>
            <li><strong>NEW: HTML-based Document Viewer in Statement History with proper tables, headings, formatting</strong></li>
            <li><strong>NEW: DOM text node walking for reliable highlight positioning in HTML content</strong></li>
            <li><strong>NEW: Cross-extractor normalized matching (strips **, |,</strong> &mdash; -, # artifacts for highlight matching)</li>
            <li><strong>NEW: Install_AEGIS.bat</strong> &mdash; 7-step Windows installer with user-selectable location (default C:\AEGIS)</li>
            <li><strong>NEW: Start_AEGIS.bat and Stop_AEGIS.bat launcher scripts with offline dependency installation</strong></li>
            <li>IMPROVED: package_for_distribution.bat renamed to AEGIS_Distribution with mammoth wheel bundling</li>
            <li>IMPROVED: /api/scan-history/document-text returns html_preview and format fields</li>
            <li>IMPROVED: Extraction fallback chain: Docling → mammoth/pymupdf4llm → legacy extractors</li>
            <li>IMPROVED: Old scans gracefully fall back to plain-text highlighting (backward compatible)</li>
            <li>BACKEND: mammoth&gt;=1.6.0 added to requirements.txt</li>
            <li>BACKEND: MAMMOTH_AVAILABLE and PYMUPDF4LLM_AVAILABLE import flags with graceful fallback</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.2.0 <span class="changelog-date">February 9, 2026</span></h3>
        <ul>
            <li>FEATURE: Statement Forge History — track statement extraction results across scans with comparison and document viewer</li>
            <li><strong>NEW: Statement History overview dashboard with stat tiles, trend chart, directive donut, scan timeline</strong></li>
            <li><strong>NEW: Document Viewer with split-panel layout</strong> &mdash; source text with highlighted statements + detail panel</li>
            <li><strong>NEW: Directive-specific highlight colors (blue=shall, red=must, amber=will, green=should, purple=may)</strong></li>
            <li><strong>NEW: Highlight-to-create</strong> &mdash; select text in document to create new statements with auto-detected directive</li>
            <li><strong>NEW: Statement editing via inline form with PUT API save</strong></li>
            <li><strong>NEW: Unified Compare Viewer</strong> &mdash; single document with diff-aware highlights (added/removed/modified/unchanged)</li>
            <li><strong>NEW: Diff summary bar with counts, dual filter system (directive + diff status), field-level diff for modified statements</strong></li>
            <li><strong>NEW: Compare keyboard shortcuts: a=next added, r=next removed, m=next modified</strong></li>
            <li><strong>NEW: Backend compare_scan_statements() enhanced with two-tier fingerprint matching for modified detection</strong></li>
            <li><strong>NEW: _diff_status injection on statements for diff-aware rendering</strong></li>
            <li><strong>FIX: Overlapping statements now share highlight marks via data-stmt-indices attribute with findMarkForIndex() helper</strong></li>
            <li><strong>FIX: Document scroll positioning uses getBoundingClientRect() instead of unreliable offsetTop for cross-container accuracy</strong></li>
            <li><strong>FIX: Forge History button correctly opens history for current document</strong></li>
            <li><strong>FIX: Dark mode highlights, navigation buttons, close button, Escape key handling all fixed</strong></li>
            <li>VERIFIED: Statement extraction logic (statement_forge/extractor.py) confirmed intact and unmodified</li>
            <li>VERIFIED: All changes Windows-compatible (pathlib.Path, proper env var fallbacks, no hardcoded paths)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.1.0 <span class="changelog-date">February 8, 2026</span></h3>
        <ul>
            <li>FEATURE: Nimbus SIPOC Import - parse Nimbus process model SIPOC exports to build role inheritance</li>
            <li><strong>NEW: Role Inheritance from Resource column with context-dependent parsing modes</strong></li>
            <li><strong>NEW: Hierarchy mode (Roles Hierarchy map)</strong> &mdash; inherits-from relationships from Resources column</li>
            <li><strong>NEW: Process mode (fallback)</strong> &mdash; co-performs, supplies-to, receives-from relationships from all columns</li>
            <li><strong>NEW: Auto-fallback when Roles Hierarchy map path not found</strong> &mdash; processes all rows in process mode</li>
            <li><strong>NEW: Interactive HTML Role Inheritance Map (renamed from Hierarchy) with 4 views: Dashboard, Tree, Graph, Table</strong></li>
            <li><strong>NEW: Inline editing in Inheritance Map</strong> &mdash; edit all role fields, track changes, export diffs as JSON</li>
            <li><strong>NEW: Export-back workflow</strong> &mdash; drop edited JSON in updates/ folder, Check for Updates auto-imports changes</li>
            <li><strong>NEW: Function Tag Distribution donut chart with accurate counts from role_function_tags join table</strong></li>
            <li><strong>NEW: Graph View animations</strong> &mdash; staggered card entrance, SVG node pop-in, arrow draw-in, center pulse</li>
            <li><strong>NEW: Dashboard stat cards with animated counters, Health Metrics, Role Types breakdown</strong></li>
            <li><strong>NEW: Interactive HTML Role Import Template</strong> &mdash; downloadable standalone form for manual role entry</li>
            <li><strong>NEW: Template supports bulk paste from Excel, CSV, semicolons, or one-per-line with auto-format detection</strong></li>
            <li><strong>NEW: Template exports JSON for re-import into AEGIS with all extended fields</strong></li>
            <li><strong>NEW: SIPOC import wizard with 5-step flow (upload, preview, options, import, complete)</strong></li>
            <li><strong>NEW: Hierarchy view mode in dictionary - collapsible tree visualization of role inheritance</strong></li>
            <li><strong>NEW: Pre-export filter modal - filter by org group, disposition, baselined status before exporting</strong></li>
            <li><strong>NEW: Role Disposition tracking (Sanctioned, To Be Retired, TBD) with visual differentiation</strong></li>
            <li><strong>NEW: Baselined status tracking with green checkmark indicators</strong></li>
            <li><strong>NEW: Role Type classification (Singular-Specific, Singular-Aggregate, Group-Specific, Group-Aggregate)</strong></li>
            <li><strong>NEW: Import dropdown menu - CSV/Excel import and Nimbus SIPOC Import as separate options</strong></li>
            <li><strong>NEW: Template download button in dictionary toolbar for blank role entry form</strong></li>
            <li><strong>NEW: role_relationships database table with inherits-from, uses-tool, co-performs, supplies-to, receives-from types</strong></li>
            <li><strong>NEW: role_template_export.py standalone HTML generator for interactive role import template</strong></li>
            <li><strong>NEW: 6 new API endpoints (import-sipoc, relationships, hierarchy, hierarchy/export-html, clear-sipoc, export-template)</strong></li>
            <li><strong>NEW: sipoc_parser.py standalone module for SIPOC Excel parsing with dual-mode logic</strong></li>
            <li><strong>NEW: hierarchy_export.py standalone HTML generator for offline hierarchy visualization</strong></li>
            <li>IMPROVED: Dictionary cards and table rows show disposition, baselined, and role type badges</li>
            <li>IMPROVED: To Be Retired roles shown with strikethrough, faded, and amber warning styling</li>
            <li>IMPROVED: SIPOC fallback notice — yellow/green info boxes showing parsing mode in preview</li>
            <li>IMPROVED: Extended field import support (role_type, role_disposition, org_group, baselined) from template JSON</li>
            <li>IMPROVED: SIPOC re-import now auto-removes stale roles no longer present in the new SIPOC file</li>
            <li>IMPROVED: Diff-based cleanup compares new SIPOC against existing source='sipoc' roles and removes orphans</li>
            <li>IMPROVED: Import results show removal counts (roles, relationships, tags removed)</li>
            <li><strong>FIX: Dictionary keyboard hints bar no longer overlaps table rows</strong> &mdash; uses flexbox layout instead of fixed height</li>
            <li><strong>FIX: RACI Matrix click handling</strong> &mdash; drilldown modal now opens correctly (was silently failing due to showModal signature mismatch)</li>
            <li><strong>FIX: Adjudication card body click now opens Source Viewer</strong> &mdash; added fallback handler for clicks outside specific buttons</li>
            <li><strong>FIX: Adjudication kanban card click now opens Source Viewer</strong> &mdash; kanban cards previously had no click handlers</li>
            <li><strong>FIX: Context toggle class name mismatch fixed (adj-card-context-toggle vs adj-context-toggle)</strong></li>
            <li><strong>NEW: showContentModal() function in modals.js for dynamic content modals without pre-existing DOM elements</strong></li>
            <li><strong>FIX: Data Explorer chart.canvas null reference error when switching tabs rapidly</strong></li>
            <li>VERIFIED: All 8 Roles Studio tabs tested end-to-end with zero console errors</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.5 <span class="changelog-date">February 8, 2026</span></h3>
        <ul>
            <li>OVERHAUL: Complete rewrite of Role Dictionary tab with dashboard, card view, and bulk operations</li>
            <li><strong>NEW: Dictionary Dashboard - 4 stat tiles (total, deliverables, adjudicated, health score) with donut chart</strong></li>
            <li><strong>NEW: Card View toggle - rich role cards with color-coded adjudication borders and inline actions</strong></li>
            <li><strong>NEW: Bulk Operations - select multiple roles with checkboxes, batch activate/deactivate/delete/set category/mark deliverable</strong></li>
            <li><strong>NEW: Inline Quick Actions - click category badge to change, star toggle for deliverable, click name to copy</strong></li>
            <li><strong>NEW: Role Cloning - duplicate any role with one click for quick creation of similar roles</strong></li>
            <li><strong>NEW: Duplicate Detection - warns when saving roles with similar names or matching aliases</strong></li>
            <li><strong>NEW: Keyboard Navigation - j/k or arrows to navigate, Enter to edit, Space to select, T to toggle view, / to search</strong></li>
            <li><strong>NEW: Enhanced Filtering - filter by adjudication status, has description, has function tags</strong></li>
            <li><strong>NEW: Audit Trail display - shows time ago, updated by info with full date tooltips</strong></li>
            <li><strong>NEW: Sortable columns with sort direction arrows (role name, category, modified date)</strong></li>
            <li>IMPROVED: Adjudication badges on every dictionary row showing confirmed/deliverable/rejected/pending status</li>
            <li>IMPROVED: Health score metric tracking description and tag completeness across the dictionary</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.4 <span class="changelog-date">February 8, 2026</span></h3>
        <ul>
            <li><strong>NEW: Dictionary Diff Preview - preview what will change before importing adjudication decisions</strong></li>
            <li><strong>NEW: Package versioning - warns when importing packages from newer AEGIS versions</strong></li>
            <li><strong>NEW: PDF adjudication report export (Export → PDF Report)</strong></li>
            <li>IMPROVED: Import progress indicators with spinner overlay during import operations</li>
            <li>IMPROVED: Two-step import flow: preview diff → confirm → import</li>
            <li>BACKEND: POST /api/roles/adjudication/import-preview - diff preview endpoint</li>
            <li>BACKEND: GET /api/roles/adjudication/export-pdf - PDF report generation</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.3 <span class="changelog-date">February 8, 2026</span></h3>
        <ul>
            <li><strong>NEW: Global adjudication badges (✓ Adjudicated, ★ Deliverable, ✗ Rejected) on all role displays tool-wide</strong></li>
            <li><strong>NEW: AEGIS.AdjudicationLookup global utility - fetches role dictionary, caches, provides badge HTML</strong></li>
            <li><strong>NEW: adjudication-lookup.js - standalone utility for any JS file to display adjudication status</strong></li>
            <li>IMPROVED: Adjudication stats shown as green subtitle under Unique Roles tile (not separate tile)</li>
            <li><strong>FIX: Critical dark-mode.css not loading - CSS @import ordering violation in style.css</strong></li>
            <li><strong>FIX: Data Explorer donut chart center text alignment with Chart.js animation timing</strong></li>
            <li>OVERHAUL: Complete rewrite of Adjudication tab in Roles &amp; Responsibilities Studio</li>
            <li><strong>NEW: Auto-Classify button - AI-assisted role classification with pattern matching and confidence scoring</strong></li>
            <li><strong>NEW: Kanban board view with drag-and-drop between Pending/Confirmed/Deliverable/Rejected columns</strong></li>
            <li><strong>NEW: Mini dashboard with animated stat cards, SVG progress ring, and click-to-filter</strong></li>
            <li><strong>NEW: Function tag pills on role cards - assign hierarchical function categories inline</strong></li>
            <li><strong>NEW: Confidence gauge (SVG ring) on each role card showing classification confidence</strong></li>
            <li><strong>NEW: Document chips showing which scanned documents contain each role</strong></li>
            <li><strong>NEW: Undo/Redo system for all adjudication actions (Ctrl+Z / Ctrl+Y)</strong></li>
            <li><strong>NEW: Keyboard navigation (Arrow keys, C=Confirm, D=Deliverable, R=Reject, V=View Source)</strong></li>
            <li><strong>NEW: Batch adjudication API endpoint for processing multiple roles in single transaction</strong></li>
            <li><strong>NEW: Auto-adjudicate API endpoint with deliverable/role pattern matching</strong></li>
            <li><strong>NEW: Adjudication summary API endpoint with status counts and recent activity</strong></li>
            <li><strong>NEW: CSV export of adjudication data with role, status, confidence, documents</strong></li>
            <li><strong>NEW: Bulk selection with select-all checkbox and batch confirm/reject/deliverable</strong></li>
            <li><strong>NEW: View toggle between list and kanban views with localStorage persistence</strong></li>
            <li><strong>NEW: Function tag section in Role Source Viewer with Add/Remove tags and custom tag creation</strong></li>
            <li>IMPROVED: Role cards show context preview with expandable full context</li>
            <li>IMPROVED: Function tags assignable/removable directly from role cards</li>
            <li>IMPROVED: Enhanced search and filter with status, confidence, and tag filtering</li>
            <li><strong>FIX: CSRF token sync between page load and fetch sessions</strong></li>
            <li><strong>FIX: Persistent secret key survives server restarts</strong></li>
            <li><strong>FIX: Localhost server switched from Waitress to Flask threaded (Secure cookie flag fix)</strong></li>
            <li><strong>FIX: Kanban view toggle properly shows/hides list and board containers</strong></li>
            <li>BACKEND: batch_adjudicate() method in scan_history.py for transactional batch operations</li>
            <li>BACKEND: get_adjudication_summary() method for dashboard statistics</li>
            <li>BACKEND: Enhanced /api/roles/adjudicate endpoint with function_tags parameter</li>
            <li><strong>NEW: Interactive HTML Export - standalone kanban board with drag-drop, tags, categories, notes, and import file generation</strong></li>
            <li><strong>NEW: Import Decisions - import adjudication decisions from JSON files generated by HTML board</strong></li>
            <li><strong>NEW: Export dropdown menu with CSV, Interactive HTML Board, and Import options</strong></li>
            <li><strong>NEW: Share button with Export to Shared Folder and Email Package options</strong></li>
            <li><strong>NEW: .aegis-roles package format for team sharing of role dictionaries with function tags</strong></li>
            <li><strong>NEW: Settings &gt; Sharing &gt; Import Package for .aegis-roles file upload</strong></li>
            <li><strong>NEW: FileRouter auto-imports .aegis-roles files from updates/ folder</strong></li>
            <li>IMPROVED: Master file export now includes function_tags per role</li>
            <li>IMPROVED: Master file sync now imports function_tags during sync</li>
            <li>BACKEND: GET /api/roles/adjudication/export-html endpoint</li>
            <li>BACKEND: POST /api/roles/adjudication/import endpoint</li>
            <li>BACKEND: POST /api/roles/share/package endpoint</li>
            <li>BACKEND: POST /api/roles/share/import-package endpoint</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.1 <span class="changelog-date">February 4, 2026</span></h3>
        <ul>
            <li>ACCURACY: Role extraction v3.3.3 achieves 99%+ recall across all document types</li>
            <li>ACCURACY: Added ~70 new roles (OSHA, academic, defense, aerospace)</li>
            <li>ACCURACY: Added ~25 false positive filters, removed 3 incorrect entries (contractor, government, quality control)</li>
            <li>ACCURACY: Added domain-specific validation (worker_terms, defense_terms, academic_terms)</li>
            <li>VALIDATED: FAA, OSHA, Stanford documents - 103% average recall</li>
            <li>VALIDATED: Defense/Government (MIL-STD, NIST) - 99.5% average recall</li>
            <li>VALIDATED: Aerospace (NASA, FAA, KSC) - 99.0% average recall</li>
            <li><strong>NEW: defense_role_analysis.py, aerospace_role_analysis.py test scripts</strong></li>
            <li>DOC: Updated ROLE_EXTRACTION_IMPROVEMENTS.md, ROLE_EXTRACTION_TEST_RESULTS.md</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v4.0.0 <span class="changelog-date">February 4, 2026</span></h3>
        <ul>
            <li>REBRAND: Complete rebrand from TechWriterReview to AEGIS (Aerospace Engineering Governance &amp; Inspection System)</li>
            <li>REBRAND: Updated 163+ files across codebase with new branding</li>
            <li>REBRAND: New AEGIS shield logo with gold/bronze gradient</li>
            <li>REBRAND: Gold accent color palette (#D6A84A, #B8743A) throughout UI</li>
            <li>REBRAND: Updated browser title, navigation, and all UI text</li>
            <li>ACCURACY: Fixed critical GRM002 'Capitalize I' false positives matching 'i' inside words</li>
            <li>ACCURACY: Grammar checker v2.6.0 with case-sensitive lowercase 'i' detection</li>
            <li>ACCURACY: Punctuation checker v2.7.0 filters TOC/table of contents entries</li>
            <li>ACCURACY: Prose linter v1.1.0 with nominalization exceptions for 40+ technical terms</li>
            <li>ACCURACY: Base checker v2.5.0 with word boundary validation for single-char matches</li>
            <li><strong>NEW: Bokeh visualization library added to requirements for interactive charts</strong></li>
            <li>IMPROVED: Dark mode AEGIS brand colors for better visibility</li>
            <li>IMPROVED: Active navigation tabs use gold accent underline</li>
            <li>TEST: All 42 v3.4.0 checker tests passing</li>
            <li>TEST: All 117 core tests passing</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.5 <span class="changelog-date">February 4, 2026</span></h3>
        <ul>
            <li>UI: Added 23 new v3.4.0 checker checkboxes to Settings &gt; Document Profiles</li>
            <li>UI: New checker categories - Readability, Procedural Writing, Product &amp; Code, Standards &amp; Compliance</li>
            <li>UI: Style Guide Preset selector in Settings &gt; Review Options (8 presets)</li>
            <li><strong>NEW: static/js/features/style-presets.js - Preset UI module with localStorage persistence</strong></li>
            <li><strong>NEW: tests/test_checker_performance.py - Performance benchmark suite for 84 checkers</strong></li>
            <li><strong>FIX: BUG-M09 - Hyperlink validator HTML export summary now properly handles undefined values</strong></li>
            <li>IMPROVED: Checker grid CSS with scrollable categories and compact layout</li>
            <li>VERIFIED: 84 checkers registered and available for document analysis</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.4 <span class="changelog-date">February 4, 2026</span></h3>
        <ul>
            <li>DATABASE: Added universal_acronyms.json with 1,767 well-known acronyms</li>
            <li>DATABASE: Sources include UK MOJ, DOD Dictionary, FDA, IEEE/ISO/ANSI, common tech writing</li>
            <li>DATABASE: Acronyms categorized (technology, government, military, medical, finance, etc.)</li>
            <li>IMPROVED: Acronym checker v4.6.0 now loads external acronym database</li>
            <li>IMPROVED: External database used in permissive mode to auto-skip well-known acronyms</li>
            <li>IMPROVED: Database loading is cached for performance (loaded once per session)</li>
            <li>OFFLINE: All 1,767 acronyms available offline for air-gapped deployments</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.3 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li>ACCURACY: Comprehensive batch testing across 10+ document types</li>
            <li>ACCURACY: Added ALL CAPS sentence detection to prevent false acronym flags</li>
            <li>ACCURACY: Added 50+ well-known regulatory acronyms (NIOSH, CDC, NIH, etc.)</li>
            <li>ACCURACY: Added 30+ engineering/process acronyms (PID, PLC, SCADA, etc.)</li>
            <li>ACCURACY: Added 60+ common words in ALL CAPS instructions (HARD, MUST, etc.)</li>
            <li>ACCURACY: Reduced passive voice false positives with 50+ technical terms</li>
            <li>ACCURACY: Fixed 'is need' and similar false positive patterns</li>
            <li>IMPROVED: Acronym checker v4.5.2 with better ALL CAPS detection</li>
            <li>IMPROVED: Grammar checker v2.6.2 with comprehensive false positive list</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.2 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li>ACCURACY: Reduced false positives in acronym detection by 40%+</li>
            <li>ACCURACY: Section reference codes (A1, B2, C3...) no longer flagged as undefined acronyms</li>
            <li>ACCURACY: Template/instruction text in brackets [GREEN TEXT] now filtered out</li>
            <li>ACCURACY: Added 80+ domain-specific skip words (ROBOTICS, REST, COVID, LASER, etc.)</li>
            <li>ACCURACY: Improved passive voice detection - added 50+ technical/SOP terms to false positives</li>
            <li><strong>FIX: Phantom passive voice detections (are prohibited, must be contacted, etc.) eliminated</strong></li>
            <li>IMPROVED: Acronym checker v4.5.1 with smarter section reference detection</li>
            <li>IMPROVED: Grammar checker v2.6.1 with expanded technical vocabulary</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.1 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li><strong>NEW: Style Guide Presets - One-click configuration for Microsoft, Google, Plain Language, ASD-STE100, Government, Aerospace styles</strong></li>
            <li><strong>NEW: style_presets.py - 8 pre-built style guide configurations with checker settings</strong></li>
            <li><strong>NEW: Full CLI Mode - Run all 84 checkers from command line (python -m AEGIS document.docx)</strong></li>
            <li><strong>NEW: __main__.py - Complete CLI with batch processing, preset selection, JSON/CSV/XLSX export</strong></li>
            <li><strong>NEW: Auto-Fix Engine - Foundation for automatic issue correction</strong></li>
            <li><strong>NEW: auto_fixer.py - Fix generators for Latin abbreviations, contractions, wordy phrases, product names, second person, future tense, link text</strong></li>
            <li><strong>NEW: ASD-STE100 Approved Words - data/ste100_approved_words.json with 875 approved words and writing rules</strong></li>
            <li><strong>NEW: API /api/presets - List and apply style guide presets</strong></li>
            <li><strong>NEW: API /api/presets/&lt;name&gt; - Get specific preset configuration</strong></li>
            <li><strong>NEW: API /api/presets/&lt;name&gt;/apply - Apply preset with custom overrides</strong></li>
            <li><strong>NEW: API /api/auto-fix/preview - Preview available auto-fixes for issues</strong></li>
            <li>CLI: --preset flag for style guide selection (microsoft, google, plain_language, asd_ste100, government, aerospace)</li>
            <li>CLI: --batch flag for processing multiple documents</li>
            <li>CLI: --format flag for output format (json, csv, xlsx, text)</li>
            <li>CLI: --list-presets and --list-checkers info commands</li>
            <li>IMPROVED: Vale-style preset configurations matching industry standards</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.4.0 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li><strong>NEW: Maximum Coverage Suite - 23 new offline-only checkers for comprehensive analysis</strong></li>
            <li><strong>NEW: style_consistency_checkers.py - 6 checkers (heading case, contractions, Oxford comma, ARI, Spache, Dale-Chall)</strong></li>
            <li><strong>NEW: clarity_checkers.py - 5 checkers (future tense, Latin abbreviations, sentence-initial conjunctions, directional language, time-sensitive language)</strong></li>
            <li><strong>NEW: acronym_enhanced_checkers.py - 2 checkers (first-use enforcement, multiple definition detection)</strong></li>
            <li><strong>NEW: procedural_writing_checkers.py - 3 checkers (imperative mood, second person preference, link text quality)</strong></li>
            <li><strong>NEW: document_quality_checkers.py - 4 checkers (numbered list sequence, product name consistency, cross-reference targets, code formatting)</strong></li>
            <li><strong>NEW: compliance_checkers.py - 3 checkers (MIL-STD-40051, S1000D basic, AS9100 documentation)</strong></li>
            <li><strong>NEW: data/dale_chall_3000.json - Full 3000-word Dale-Chall easy word list for readability analysis</strong></li>
            <li><strong>NEW: data/spache_easy_words.json - 1000+ word Spache formula word list</strong></li>
            <li><strong>NEW: data/product_names.json - 250+ product/technology name capitalizations</strong></li>
            <li><strong>NEW: data/mil_std_40051_patterns.json - MIL-STD-40051-2 compliance patterns and rules</strong></li>
            <li><strong>NEW: data/s1000d_basic_rules.json - S1000D Issue 5.0 structural requirements</strong></li>
            <li><strong>NEW: data/as9100_doc_requirements.json - AS9100D documentation requirements</strong></li>
            <li><strong>NEW: Option mappings for all 23 checkers in core.py for UI checkbox control</strong></li>
            <li>IMPROVED: Vale-style style guide compliance (Microsoft, Google, ASD-STE100)</li>
            <li>IMPROVED: Readability formulas (ARI, Spache, enhanced Dale-Chall)</li>
            <li>IMPROVED: Procedural writing validation per technical writing best practices</li>
            <li>IMPROVED: Aerospace/defense compliance checking (MIL-STD, S1000D, AS9100)</li>
            <li>TEST: Comprehensive unit tests for all 23 new checkers</li>
            <li>TEST: Integration tests verifying checkers load in core.py</li>
            <li>TEST: Data file validation tests</li>
            <li>OFFLINE: All 23 checkers 100% offline-capable with no external API dependencies</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.3.0 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li><strong>NEW: Maximum Accuracy NLP Enhancement Suite for near-100% accuracy</strong></li>
            <li><strong>NEW: technical_dictionary.py - 10,000+ term master dictionary with aerospace/defense terminology</strong></li>
            <li><strong>NEW: adaptive_learner.py - Unified learning system with SQLite persistence for role/acronym/grammar decisions</strong></li>
            <li><strong>NEW: nlp_enhanced.py - Enhanced NLP processor with EntityRuler, PhraseMatcher, transformer support</strong></li>
            <li><strong>NEW: enhanced_passive_checker.py - Dependency parsing-based passive voice detection (not regex)</strong></li>
            <li><strong>NEW: fragment_checker.py - Syntactic parsing for sentence fragment detection</strong></li>
            <li><strong>NEW: requirements_analyzer.py - Atomicity, testability, escape clause, ambiguous term checking</strong></li>
            <li><strong>NEW: terminology_checker.py - Spelling variant, British/American, abbreviation consistency</strong></li>
            <li><strong>NEW: cross_reference_validator.py - Section/table/figure/requirement reference validation</strong></li>
            <li><strong>NEW: data/aerospace_patterns.json - 80+ EntityRuler patterns for aerospace/defense</strong></li>
            <li><strong>NEW: 300+ adjectival participles whitelist for passive voice false positive reduction</strong></li>
            <li><strong>NEW: 60+ ambiguous terms database for requirements analysis</strong></li>
            <li><strong>NEW: 100+ British/American word pairs for terminology consistency</strong></li>
            <li><strong>NEW: Ensemble extraction combining NER, patterns, and dependency parsing</strong></li>
            <li><strong>NEW: Context-aware confidence boosting from user decisions</strong></li>
            <li><strong>NEW: Export/import JSON for team sharing of learned patterns</strong></li>
            <li>IMPROVED: Role extraction target accuracy 95%+ (from 56.7%)</li>
            <li>IMPROVED: Acronym detection target accuracy 95%+ (from 75%)</li>
            <li>IMPROVED: Passive voice detection target accuracy 88%+ (from 70%)</li>
            <li>IMPROVED: Spelling accuracy target 98%+ (from 85%)</li>
            <li>TEST: 167 new unit tests (40+34+30+35+28) across 5 test files</li>
            <li>TEST: All 356 tests passing (189 existing + 167 new)</li>
            <li>OFFLINE: All features 100% offline-capable for air-gapped deployment</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.5 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li>IMPROVED: Role extraction now filters phone number patterns (###-####, (###), etc.)</li>
            <li>IMPROVED: Role extraction now filters candidates starting with digits</li>
            <li>IMPROVED: Role extraction now filters candidates with &gt;30% numeric characters</li>
            <li>IMPROVED: Role extraction now filters candidates containing ZIP codes</li>
            <li>IMPROVED: Role extraction maximum length validation (&gt;60 chars rejected)</li>
            <li>IMPROVED: Acronyms in parentheses now extracted with roles (e.g., 'Project Manager (PM)' extracts PM)</li>
            <li>IMPROVED: Acronym pattern extended to support 6-word role names and &amp; in acronyms</li>
            <li>IMPROVED: NLP extraction now captures acronyms from context</li>
            <li>IMPROVED: Filter run-together words from PDF extraction (e.g., 'Byasafetydepartment')</li>
            <li>IMPROVED: Filter slash-separated alternatives (e.g., 'Owner/Manager')</li>
            <li>IMPROVED: Filter section headers (e.g., 'C. Scalability')</li>
            <li>IMPROVED: Filter address/location patterns (e.g., 'Suite 670', 'Atlanta Federal Center')</li>
            <li>IMPROVED: More conservative NLP override - requires role indicators to trust NLP</li>
            <li>IMPROVED: Added 20+ single-word exclusions (user, owner, chief, team, group, etc.)</li>
            <li>IMPROVED: Filter 'Other X' and 'Own X' patterns</li>
            <li><strong>NEW: 25+ FAA/Aviation-specific roles (accountable executive, certificate holder, flight crew, etc.)</strong></li>
            <li><strong>NEW: 25+ OSHA/Safety-specific roles (process safety coordinator, plant manager, shift supervisor, etc.)</strong></li>
            <li>ACCURACY: Reduced false positives by 78% (9 → 2) in test documents</li>
            <li>ACCURACY: Improved accuracy from 36.7% to 56.7% on FAA/OSHA documents</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.4 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li>IMPROVED: Enhanced spaCy integration for role extraction (BUG-M11)</li>
            <li>IMPROVED: NLPProcessor v1.1.0 with better noun chunk analysis</li>
            <li>IMPROVED: Added compound noun detection for multi-word roles</li>
            <li>IMPROVED: Added passive voice subject detection for roles</li>
            <li>IMPROVED: Added role-verb association detection (approve, review, coordinate, etc.)</li>
            <li>IMPROVED: Enhanced confidence scoring based on POS tags and linguistic features</li>
            <li>IMPROVED: Better sentence-based context extraction using spaCy</li>
            <li>IMPROVED: Lower threshold for high-confidence NLP detections</li>
            <li>IMPROVED: Added 45+ new role suffixes and modifiers for aerospace/defense</li>
            <li>IMPROVED: Added org unit indicators (directorate, center, facility, etc.)</li>
            <li>IMPROVED: Fuzzy matching in NLP enhancement to boost existing roles</li>
            <li><strong>NEW: semantic_analyzer.py - Sentence-Transformers for semantic similarity</strong></li>
            <li><strong>NEW: acronym_extractor.py - Schwartz-Hearst algorithm for acronym extraction</strong></li>
            <li><strong>NEW: prose_linter.py - Vale-style rules for technical writing</strong></li>
            <li><strong>NEW: structure_analyzer.py - Document structure and cross-reference analysis</strong></li>
            <li><strong>NEW: text_statistics.py - Comprehensive readability and text metrics</strong></li>
            <li><strong>NEW: Semantic similarity search for finding related content</strong></li>
            <li><strong>NEW: Duplicate/near-duplicate detection in documents</strong></li>
            <li><strong>NEW: Sentence clustering for content organization</strong></li>
            <li><strong>NEW: 100+ standard aerospace/defense acronyms in acronym extractor</strong></li>
            <li><strong>NEW: Passive voice, nominalization, and wordy phrase detection</strong></li>
            <li><strong>NEW: Government/aerospace style guide compliance checking</strong></li>
            <li><strong>NEW: Heading hierarchy and cross-reference validation</strong></li>
            <li><strong>NEW: Vocabulary richness metrics (TTR, Hapax Legomena, Yule's K)</strong></li>
            <li><strong>NEW: TF-IDF and noun phrase keyword extraction</strong></li>
            <li><strong>NEW: Technical writing metrics (shall/will/must usage, jargon density)</strong></li>
            <li>UPDATED: requirements.txt with sentence-transformers and rapidfuzz</li>
            <li><strong>NEW: enhanced_analyzers.py - Integration wrapper for all new modules</strong></li>
            <li>INTEGRATED: All 5 analyzers registered as checkers in core.py</li>
            <li>INTEGRATED: Option mappings for UI checkbox control</li>
            <li><strong>NEW: /api/analyzers/status endpoint for analyzer availability</strong></li>
            <li><strong>NEW: /api/analyzers/semantic/similar endpoint for similarity search</strong></li>
            <li><strong>NEW: /api/analyzers/acronyms/extract endpoint for acronym extraction</strong></li>
            <li><strong>NEW: /api/analyzers/statistics endpoint for text metrics</strong></li>
            <li><strong>NEW: /api/analyzers/lint endpoint for prose quality checking</strong></li>
            <li><strong>NEW: Enhanced analyzer metrics in review results</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.3 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li><strong>FIX: BUG-M09 - HTML export now properly escapes URLs and handles None values</strong></li>
            <li><strong>FIX: BUG-M09 - HTML export generates summary from results when summary object is None</strong></li>
            <li><strong>FIX: BUG-M07 - Soft 404 detection less aggressive (removed generic 'error' from title check)</strong></li>
            <li><strong>FIX: BUG-M23 - Version numbers synchronized across all UI components to 3.2.3</strong></li>
            <li><strong>FIX: BUG-M26 - Duplicate element IDs in troubleshooting panel renamed to prevent conflicts</strong></li>
            <li><strong>FIX: BUG-M25 - Troubleshooting export buttons now properly find their elements</strong></li>
            <li>IMPROVED: Hyperlink validator HTML export includes import for html escaping module</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.2 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li><strong>FIX: Adjudicated roles now properly saved to role dictionary via both primary and backup API paths</strong></li>
            <li><strong>FIX: Adjudicated roles removed from pending list - list refreshes correctly after adjudication</strong></li>
            <li><strong>FIX: Adjudication sync now properly updates AdjudicationState.decisions Map with all required fields</strong></li>
            <li><strong>FIX: Role Dictionary delete button now shows proper icon instead of red box</strong></li>
            <li><strong>FIX: Dictionary table action buttons styled correctly (edit, toggle, delete)</strong></li>
            <li><strong>FIX: Status badges (active/inactive) now styled correctly in dictionary table</strong></li>
            <li><strong>NEW: Backup dictionary save via /api/roles/dictionary if primary endpoint fails</strong></li>
            <li>IMPROVED: Better logging for adjudication sync to help diagnose issues</li>
            <li>IMPROVED: State.adjudicatedRoles properly updated for graph visualization sync</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.1 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li><strong>FIX: Per-role adjudication persistence - each role now tracks its own adjudication state</strong></li>
            <li><strong>NEW: API endpoint /api/roles/adjudicate - saves adjudication to role dictionary</strong></li>
            <li><strong>NEW: API endpoint /api/roles/adjudication-status - retrieves saved adjudication state</strong></li>
            <li><strong>NEW: API endpoint /api/roles/update-category - updates role category classification</strong></li>
            <li><strong>NEW: get_role_by_name() method in scan_history.py for role lookup</strong></li>
            <li><strong>NEW: Role extractor learns from rejections - rejected roles added to false_positives</strong></li>
            <li><strong>NEW: Confirmed roles added to known_roles for higher confidence matching</strong></li>
            <li>IMPROVED: Role Source Viewer resets adjudication panel when opening new role</li>
            <li>IMPROVED: Role extraction becomes smarter over time through adjudication feedback</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.2.0 <span class="changelog-date">February 3, 2026</span></h3>
        <ul>
            <li><strong>NEW: Role Source Viewer with Adjudication Controls - unified role review interface</strong></li>
            <li><strong>NEW: View actual document text with highlighted role mentions from historical scans</strong></li>
            <li><strong>NEW: Adjudication panel with Confirm Role, Mark Deliverable, and Reject buttons</strong></li>
            <li><strong>NEW: Status badges showing adjudication state (Pending/Confirmed/Deliverable/Rejected)</strong></li>
            <li><strong>NEW: Category dropdown for role classification (Role, Management, Technical, Organization, Custom)</strong></li>
            <li><strong>NEW: Notes textarea for adjudication comments</strong></li>
            <li><strong>NEW: Multi-document navigation with occurrence counter</strong></li>
            <li><strong>NEW: Click any highlight to jump to that mention</strong></li>
            <li><strong>NEW: API endpoint /api/scan-history/document-text for historical document retrieval</strong></li>
            <li><strong>NEW: Full document text retrieved from results_json.full_text in scan history</strong></li>
            <li><strong>FIX: Document Compare modal sizing - now 95vw × 90vh with proper constraints</strong></li>
            <li><strong>FIX: Browser cache-busting with versioned script loading</strong></li>
            <li>IMPROVED: Role Source Viewer styling with split-panel design matching Statement Review Mode</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.9 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li><strong>NEW: Molten Progress Bar system - scalable Rive-inspired progress bars</strong></li>
            <li><strong>NEW: 4 size variants (mini 4px, small 8px, medium 16px, large 28px)</strong></li>
            <li><strong>NEW: 3 color themes (orange, blue, green) with molten gradients</strong></li>
            <li><strong>NEW: Optional reflection glow and trailing effects</strong></li>
            <li><strong>NEW: Indeterminate loading state (contained within bar)</strong></li>
            <li><strong>NEW: MoltenProgress JavaScript API for dynamic creation</strong></li>
            <li>INTEGRATED: Molten progress in batch document rows (mini)</li>
            <li>INTEGRATED: Molten progress in loading overlay (medium with reflection)</li>
            <li>INTEGRATED: Molten progress in hyperlink validator (small with reflection)</li>
            <li>INTEGRATED: Molten progress in cinematic modal (small with reflection)</li>
            <li><strong>FIX: AEGIS loader no longer blocks clicks after fade-out (pointer-events fix)</strong></li>
            <li>REMOVED: Initial startup loader (app loads fast enough without it)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.8 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li><strong>NEW: AEGIS Cinematic Loader - Full-screen startup animation</strong></li>
            <li><strong>NEW: Cinematic 28px progress bar with glow effects</strong></li>
            <li><strong>NEW: Particle background canvas with 170 animated particles</strong></li>
            <li><strong>NEW: Blue/gold color scheme with grid overlay</strong></li>
            <li><strong>NEW: Sheen sweep animation with skew effect</strong></li>
            <li><strong>NEW: Progress orb with trailing glow</strong></li>
            <li><strong>NEW: Status text and percentage display</strong></li>
            <li><strong>NEW: Cinematic vignette and film grain overlays</strong></li>
            <li><strong>NEW: Boot sequence simulation during app initialization</strong></li>
            <li><strong>NEW: Smooth fade-out on completion</strong></li>
            <li>IMPROVED: App initialization now shows real-time progress stages</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.7 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li>ENHANCED: Cinematic Progress Animation System - Major visual upgrade</li>
            <li><strong>NEW: Particle trails - 30% of particles now leave fading motion trails</strong></li>
            <li><strong>NEW: Particle connections - Web-like lines between nearby particles</strong></li>
            <li><strong>NEW: Milestone celebrations - Burst effects at 25%, 50%, 75%, 100%</strong></li>
            <li><strong>NEW: Lightning bolts for Circuit theme - Random electrical arcs</strong></li>
            <li><strong>NEW: Twinkling star field for Cosmic theme - 50 stars with cross-shine</strong></li>
            <li><strong>NEW: Rising ember particles for Fire theme - 30 glowing embers</strong></li>
            <li><strong>NEW: Enhanced energy trail - Sparks, ripple effects, larger orb</strong></li>
            <li><strong>NEW: Faster Matrix streams - Depth effect, character trails, speed boost near progress</strong></li>
            <li><strong>NEW: Grand finale explosion at 100% - 80 burst particles with container pulse</strong></li>
            <li><strong>NEW: onMilestone callback for custom milestone handling</strong></li>
            <li>IMPROVED: Energy trail now spawns 8 sparks continuously</li>
            <li>IMPROVED: Matrix characters include full katakana set (46 chars)</li>
            <li>IMPROVED: Percentage display animation with scale bounce on milestones</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.6 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li><strong>NEW: Cinematic Progress Animation System with Lottie + GSAP + Rive + Canvas integration</strong></li>
            <li><strong>NEW: 5 cinematic themes - Circuit (orange), Cosmic (purple), Matrix (green), Energy (teal), Fire (red)</strong></li>
            <li><strong>NEW: Particle system with 150+ animated particles and theme-specific behaviors</strong></li>
            <li><strong>NEW: Energy trail effect that follows progress bar with glowing path</strong></li>
            <li><strong>NEW: Matrix-style data stream effect (configurable per theme)</strong></li>
            <li><strong>NEW: Theme selector with localStorage persistence</strong></li>
            <li><strong>NEW: CDN fallbacks for air-gapped compatibility</strong></li>
            <li>ADDED: static/js/features/cinematic-progress.js (825 lines)</li>
            <li>ADDED: static/css/features/cinematic-progress.css (782 lines)</li>
            <li>ADDED: static/js/vendor/gsap.min.js (72KB)</li>
            <li>ADDED: static/js/vendor/rive.min.js (164KB)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.5 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li><strong>NEW: Circuit board themed batch progress display with dark navy/orange glow effects</strong></li>
            <li><strong>NEW: Elapsed time counter, estimated remaining time, and processing speed displays</strong></li>
            <li><strong>NEW: Animated percentage counter with smooth counting animation</strong></li>
            <li><strong>NEW: Real-time per-document status labels (QUEUED → UPLOADING → ANALYZING → DONE)</strong></li>
            <li><strong>NEW: Sound notification toggle for batch completion (speaker icon)</strong></li>
            <li><strong>FIX: Dual file dialog bug - Select Files/Select Folder no longer trigger both dialogs</strong></li>
            <li>IMPROVED: Simplified circuit board visuals for cleaner appearance</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.4 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li><strong>NEW: ENH-010 - Clean upgrade path with automatic backup and restore</strong></li>
            <li><strong>NEW: UpgradeManager class for version comparison and update application</strong></li>
            <li><strong>NEW: Automatic user data backup before upgrades (scan_history.db, settings, dictionaries)</strong></li>
            <li><strong>NEW: Rollback capability on upgrade failure</strong></li>
            <li><strong>NEW: update.bat (Windows) and update.sh (macOS/Linux) scripts for easy upgrades</strong></li>
            <li><strong>NEW: CLI interface for backup, restore, list-backups, create-package commands</strong></li>
            <li><strong>NEW: Update package creation with configurable exclusions</strong></li>
            <li>TEST: Comprehensive E2E test suite expanded (75 tests) - all passing</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.3 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li><strong>NEW: ENH-005 - Universal Role Source Viewer for viewing role context in source documents</strong></li>
            <li><strong>NEW: ENH-006 - Statement Forge Review Mode with source context and statement creation</strong></li>
            <li><strong>NEW: ENH-009 - Comprehensive diagnostics/logging system with circular buffer and async queue</strong></li>
            <li><strong>NEW: Frontend logger (frontend-logger.js) with API call timing, action tracking, backend sync</strong></li>
            <li><strong>NEW: Backend diagnostics (diagnostics.py) with performance timer decorator and sampling</strong></li>
            <li><strong>NEW: Statement model extended with source context fields (source_document, char offsets, context)</strong></li>
            <li><strong>NEW: Review mode navigation (prev/next) with keyboard shortcuts</strong></li>
            <li><strong>NEW: Approve/reject/save actions in Statement Review mode</strong></li>
            <li><strong>NEW: Create statement from text selection in source viewer</strong></li>
            <li>TEST: Comprehensive E2E test suite expanded (68 tests) - all passing</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.1.2 <span class="changelog-date">February 2, 2026</span></h3>
        <ul>
            <li><strong>FIX: BUG-C01 - Expanded passive voice FALSE_POSITIVES from ~38 to 300+ words (technical/engineering terms)</strong></li>
            <li><strong>FIX: BUG-C02 - Diagnostic export timeout increased to 60s, errors limited to 500</strong></li>
            <li><strong>FIX: BUG-M10 - Hyperlink flags now include the actual broken URL in error messages</strong></li>
            <li><strong>FIX: BUG-M14 - Document comparison shows helpful message when no documents available</strong></li>
            <li><strong>FIX: BUG-M15 - Portfolio batch categorization time window reduced from 5min to 30sec</strong></li>
            <li><strong>FIX: BUG-M16 - Poll frequency increased from 500ms to 2000ms to prevent rate limiting</strong></li>
            <li><strong>FIX: BUG-M18 - Sidebar collapsed width reduced from 56px to 44px with fully-collapsed mode</strong></li>
            <li><strong>FIX: BUG-M19 - Hyperlink validator history now properly logs with excluded/duration_ms fields</strong></li>
            <li><strong>FIX: BUG-M20 - Carousel dark mode styling added to dark-mode.css</strong></li>
            <li><strong>FIX: BUG-M21 - Heatmap dark mode contrast improvements with white text and shadows</strong></li>
            <li><strong>FIX: BUG-M22 - Docling status check uses AbortController with 5-second timeout</strong></li>
            <li><strong>FIX: BUG-M27 - Print section null reference check added</strong></li>
            <li><strong>FIX: BUG-M28 - Scan profiles load failure null check added</strong></li>
            <li><strong>FIX: BUG-M29 - SortableJS now loaded locally to avoid CSP blocking</strong></li>
            <li><strong>FIX: BUG-M30 - HelpContent click handler uses requestAnimationFrame for performance</strong></li>
            <li><strong>FIX: BUG-L10 - Passive event listeners added to touch/scroll handlers</strong></li>
            <li><strong>NEW: ENH-001 - Role consolidation engine with 25+ built-in rules, fuzzy matching, abbreviations</strong></li>
            <li><strong>NEW: ENH-003 - Graph export module for PNG/SVG export of Chart.js and D3.js visualizations</strong></li>
            <li><strong>NEW: ENH-004 - Role comparison module for multi-document side-by-side role analysis</strong></li>
            <li><strong>NEW: ENH-008 - NLP integration (spaCy) for improved role/deliverable/acronym detection</strong></li>
            <li>TEST: Comprehensive E2E test suite (48 tests) - all passing</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.125 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li>UI: Comprehensive Hyperlink Validator visual overhaul with modern glassmorphism design</li>
            <li><strong>NEW: Animated stat cards with color-coded status icons and hover effects</strong></li>
            <li><strong>NEW: Donut chart showing URL status distribution with smooth animations</strong></li>
            <li><strong>NEW: Response time histogram with color-coded speed bands</strong></li>
            <li><strong>NEW: Domain health heatmap showing success rates by domain (clickable to filter)</strong></li>
            <li><strong>NEW: Enhanced progress bar with shimmer animation and speed stats</strong></li>
            <li><strong>NEW: Expandable error detail panels with redirect chain visualization</strong></li>
            <li><strong>NEW: Real-time streaming indicator showing current URL being validated</strong></li>
            <li><strong>NEW: Skeleton loading states for better UX during data fetching</strong></li>
            <li><strong>NEW: Rescan button UI for bot-protected sites with visual styling</strong></li>
            <li><strong>NEW: 3D Domain Health Carousel - interactive rotating cards showing domain health status</strong></li>
            <li><strong>NEW: Carousel features: drag-to-spin, click-to-filter, auto-rotate, health rings with percentages</strong></li>
            <li><strong>NEW: Domain filter clear functionality with indicator badges</strong></li>
            <li><strong>NEW: Large dataset support - shows top 15 domains with search and expand options</strong></li>
            <li><strong>FIX: History panel can now be collapsed/expanded with toggle button</strong></li>
            <li><strong>FIX: URL text no longer cut off - full URLs display with word wrap</strong></li>
            <li><strong>FIX: Modal window properly centered on screen</strong></li>
            <li>IMPROVED: Setup.bat now includes Playwright installation (Step 8/8)</li>
            <li>CSS: 900+ lines of modern CSS with gradients, animations, dark mode support</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.124 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li>FEATURE: Headless Browser Rescan for bot-protected sites (defense.gov, dla.mil, etc.)</li>
            <li><strong>NEW: /api/hyperlink-validator/rescan endpoint to retry failed URLs with real Chrome browser</strong></li>
            <li><strong>NEW: /api/hyperlink-validator/rescan/job/&lt;id&gt; to rescan all failures from a validation job</strong></li>
            <li><strong>NEW: Stealth mode bypasses sophisticated bot detection (Akamai, Cloudflare, etc.)</strong></li>
            <li><strong>NEW: Automatic HEAD→GET fallback when sites block HEAD requests</strong></li>
            <li>IMPROVED: Uses real Chrome browser channel for better bot protection bypass</li>
            <li>REQUIRES: pip install playwright &amp;&amp; playwright install chromium (optional, for rescan feature)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.123 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li>FEATURE: CAC/PIV Client Certificate Authentication for .mil sites and federal PKI resources</li>
            <li>FEATURE: Custom CA Bundle support for DoD/Federal PKI certificate validation</li>
            <li>FEATURE: Proxy Server support for enterprise network environments</li>
            <li>IMPROVED: Simplified Hyperlink Validation to two modes: Offline (format only) and Validator (full HTTP)</li>
            <li>IMPROVED: Validator mode optimized for government (.mil/.gov) and enterprise sites</li>
            <li><strong>NEW: Advanced Authentication Settings panel in Settings → Hyperlink Validation</strong></li>
            <li><strong>NEW: Windows SSO (NTLM/Negotiate) always enabled when available</strong></li>
            <li><strong>NEW: Extended timeouts and realistic browser headers for slow government servers</strong></li>
            <li><strong>NEW: HEAD/GET fallback when HEAD requests are blocked (common on government sites)</strong></li>
            <li><strong>NEW: Auth Required (401) and Rate Limited (429) status types with appropriate handling</strong></li>
            <li>REMOVED: ps1_validator mode (consolidated into enhanced validator mode)</li>
            <li>DOCS: Comprehensive authentication options documentation with CAC/PIV setup guide</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.122 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li>FEATURE: Persistent Link Exclusions - URL exclusion rules stored in SQLite database</li>
            <li>FEATURE: Scan History Storage - Historical hyperlink scans recorded with summary statistics</li>
            <li><strong>NEW: Link History modal with Exclusions and Scans tabs via 'Links' nav button</strong></li>
            <li><strong>NEW: API endpoints /api/hyperlink-validator/exclusions/* and /history/*</strong></li>
            <li><strong>NEW: HyperlinkValidatorStorage class for database operations</strong></li>
            <li><strong>NEW: Match types: contains, exact, prefix, suffix, regex</strong></li>
            <li>IMPROVED: HyperlinkValidatorState loads exclusions from database on init</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.121 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li><strong>FIX: Portfolio 'Open in Review' now correctly loads documents with full UI display</strong></li>
            <li>IMPROVED: Responsive Hyperlinks Panel - viewport-relative heights (50vh/25vh)</li>
            <li>IMPROVED: Clickable Hyperlinks - click any row to open URL in new tab for verification</li>
            <li><strong>NEW: Visual hover feedback with external-link icon on hyperlink rows</strong></li>
            <li><strong>NEW: Test document hyperlink_test.docx with working and broken link examples</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.120 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li>FEATURE: 3D Carousel for Issues by Section in Document Analytics</li>
            <li><strong>NEW: Drag-to-spin rotation and slider navigation for section boxes</strong></li>
            <li><strong>NEW: Click on carousel box to filter issues to that section</strong></li>
            <li><strong>NEW: Color-coded borders based on issue density (none/low/medium/high)</strong></li>
            <li>IMPROVED: Touch support for mobile devices</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.119 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li><strong>FIX: Document Filter Dropdown - correctly filters roles by document in Roles Studio</strong></li>
            <li><strong>FIX: CSS selector bug in roles tab switching (.roles-nav-btn.active → .roles-nav-item.active)</strong></li>
            <li>IMPROVED: Help Modal sizing - 85vw × 80vh with opaque backdrop</li>
            <li>DOCS: Comprehensive Help Documentation Overhaul with Fix Assistant v2, Hyperlink Health, Batch Processing sections</li>
            <li>DOCS: Added 8 Core Capabilities cards, Checker List table, Keyboard shortcuts tables</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.116 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li><strong>FIX: Batch memory - streaming file uploads to reduce memory usage (BUG-M02)</strong></li>
            <li><strong>FIX: SessionManager - automatic cleanup thread prevents memory growth (BUG-M03)</strong></li>
            <li><strong>FIX: Batch errors - full tracebacks now logged for debugging (BUG-M04)</strong></li>
            <li><strong>FIX: localStorage key collision - unique document IDs prevent overwriting (BUG-M05)</strong></li>
            <li><strong>NEW: MAX_BATCH_SIZE (10) and MAX_BATCH_TOTAL_SIZE (100MB) constants defined (BUG-L07)</strong></li>
            <li><strong>NEW: SessionManager.start_auto_cleanup() runs hourly to remove sessions &gt; 24h old</strong></li>
            <li><strong>NEW: FixAssistantState.generateDocumentId() creates collision-free storage keys</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.115 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li>FEATURE: Document Type Profiles - Customize which checks are performed for PrOP, PAL, FGOST, SOW</li>
            <li><strong>NEW: Settings &gt; Document Profiles tab with checker grid for each document type</strong></li>
            <li><strong>NEW: Custom profiles persist in localStorage across sessions (user-specific)</strong></li>
            <li><strong>NEW: Select All, Clear All, Reset to Default buttons for profile management</strong></li>
            <li><strong>NEW: First-time user prompt to configure document profiles on initial app launch</strong></li>
            <li>IMPROVED: applyPreset now uses custom profiles when available for document type presets</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.110 <span class="changelog-date">February 1, 2026</span></h3>
        <ul>
            <li>FEATURE: Hyperlink Validator - Export highlighted DOCX with broken links marked in red/yellow/strikethrough</li>
            <li>FEATURE: Hyperlink Validator - Export highlighted Excel with broken link rows in red background</li>
            <li><strong>NEW: API endpoints /api/hyperlink-validator/export-highlighted/docx and /excel</strong></li>
            <li><strong>NEW: 'Export Highlighted' button in Hyperlink Validator modal (enabled after file validation)</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.109 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>FIX: Batch Modal - Now opens correctly (Issue #1)</strong></li>
            <li><strong>FIX: Hyperlinks - Now extracts HYPERLINK field codes from DOCX files (Issue #2)</strong></li>
            <li><strong>FIX: Acronym Highlighting - Uses word boundary regex to prevent false positives (Issue #3)</strong></li>
            <li><strong>FIX: Fix Assistant Premium - Complete implementation with working controls (Issue #4)</strong></li>
            <li><strong>FIX: Statement Forge - 'No document loaded' fixed with consistent state checks (Issue #5)</strong></li>
            <li><strong>FIX: Scan History - Added /stats, /clear, /recall API endpoints (Issue #6)</strong></li>
            <li><strong>FIX: Triage Mode - State.documentId now set after fresh review (Issue #7)</strong></li>
            <li><strong>FIX: Document Filter - Now populates from scan history (Issue #8)</strong></li>
            <li><strong>FIX: Role-Document Matrix - Improved response validation and error handling (Issue #9)</strong></li>
            <li><strong>FIX: Export Modal Badge Overflow - Badges now wrap and truncate properly (Issue #10)</strong></li>
            <li><strong>FIX: Comment Placement - Smart quote normalization and multi-strategy matching (Issue #11)</strong></li>
            <li><strong>FIX: Version History - Added missing versions to help documentation (Issue #12)</strong></li>
            <li><strong>FIX: Updater Rollback - Uses correct endpoint, button enable/disable fixed (Issue #13)</strong></li>
            <li><strong>FIX: No Updates Empty State - Proper centered styling with icon (Issue #14)</strong></li>
            <li><strong>FIX: Logo 404 - Fixed missing logo reference (Issue #15)</strong></li>
            <li>IMPROVED: Statement extraction patterns - added responsibility/accountability phrases</li>
            <li>IMPROVED: Fallback extraction for documents without clear section structure</li>
            <li>IMPROVED: Role-Document Matrix error display with retry button</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.108 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>FIX: Document filter dropdown now populates with scanned document names (BUG-009)</strong></li>
            <li><strong>FIX: Added source_documents field to role extraction data</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.107 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>FIX: Role Details tab now shows sample_contexts from documents (BUG-007)</strong></li>
            <li><strong>FIX: Role-Doc Matrix shows helpful guidance when empty instead of stuck loading (BUG-008)</strong></li>
            <li>UX: Matrix tab explains how to populate cross-document data</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.106 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>FIX: Fix Assistant v2 Document Viewer empty - paragraphs/page_map/headings now returned from core.py (BUG-006)</strong></li>
            <li><strong>FIX: Remaining deprecated datetime.utcnow() calls in config_logging.py (BUG-M01)</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.105 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>FIX: Report generator API signature mismatch - generate() now returns bytes when output_path not provided (BUG-001)</strong></li>
            <li><strong>FIX: Learner stats endpoint now uses standard {success, data} response envelope (BUG-002)</strong></li>
            <li><strong>FIX: Acronym checker mode handling - strict mode now properly flags common acronyms (BUG-003)</strong></li>
            <li><strong>FIX: Role classification tiebreak - 'Report Engineer' now correctly classified as role (BUG-004)</strong></li>
            <li><strong>FIX: Comment pack now includes location hints from hyperlink_info (BUG-005)</strong></li>
            <li>MAINT: Updated deprecated datetime.utcnow() calls to datetime.now(timezone.utc) (WARN-001)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.104 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>FIX: Fix Assistant v2 load failure - BodyText style conflict resolved</strong></li>
            <li><strong>FIX: Logger reserved keyword conflict in static file security</strong></li>
            <li>TEST: Updated test expectations for static file security responses</li>
            <li>TEST: Fixed CSS test locations for modularized stylesheets</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.103 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li>SECURITY: innerHTML safety audit - all 143 usages documented and verified (Task A)</li>
            <li>REFACTOR: CSS modularized into 10 logical files for maintainability (Task B)</li>
            <li>QUALITY: Test suite modernized with docstrings and FAV2 API tests (Task C)</li>
            <li>QUALITY: Exception handling refined with specific catches (Task D)</li>
            <li>DOCS: Added comprehensive code comments throughout JavaScript</li>
            <li>TESTS: Added TestFixAssistantV2API, TestBatchLimits, TestSessionCleanup classes</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.102 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li>STABILIZATION: Intermediate release between 3.0.101 and 3.0.103</li>
            <li><strong>FIX: Minor adjustments to error handling patterns</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.101 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li>REFACTOR: Standardized API error responses with correlation IDs (ISSUE-004)</li>
            <li>REFACTOR: Centralized document type detection into get_document_extractor() helper (ISSUE-008)</li>
            <li>REFACTOR: Centralized user-facing strings into STRINGS constant (ISSUE-009)</li>
            <li>DOCS: Added comprehensive JSDoc comments to feature modules (ISSUE-010)</li>
            <li>CODE REVIEW: Completed remaining 4 of 12 issues from comprehensive code review audit</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.100 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li>SECURITY: Added ReDoS protection with safe regex wrappers (ISSUE-001)</li>
            <li>PERFORMANCE: Enabled WAL mode for SQLite with busy_timeout for concurrent access (ISSUE-002)</li>
            <li>PERFORMANCE: Added file size validation for large document protection (ISSUE-003)</li>
            <li>SECURITY: Enhanced input validation on learner dictionary API (ISSUE-005)</li>
            <li><strong>FIX: State.entities now properly reset on new document load (ISSUE-006)</strong></li>
            <li><strong>FIX: Added cleanup() function to FixAssistantState to prevent memory leaks (ISSUE-007)</strong></li>
            <li>CODE REVIEW: Addressed 7 of 12 issues from comprehensive code review audit</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.99 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li>STABILIZATION: Intermediate release between 3.0.98 and 3.0.100</li>
            <li><strong>FIX: Minor bug fixes from 3.0.98 testing</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.98 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>FIX: Export modal crash (BUG-002)</strong></li>
            <li><strong>FIX: Context highlighting showing wrong text (BUG-003)</strong></li>
            <li><strong>FIX: Restored hyperlink status panel (BUG-004)</strong></li>
            <li><strong>FIX: Restored Role-Document matrix tab (BUG-009)</strong></li>
            <li><strong>FIX: Double browser tab on startup (BUG-001)</strong></li>
            <li><strong>FIX: Version history gaps in Help (BUG-005)</strong></li>
            <li>IMPROVED: Role Details tab with context preview (BUG-007)</li>
            <li>IMPROVED: Document filter dropdown in Role Studio (BUG-008)</li>
            <li>IMPROVED: Comprehensive TWR_LESSONS_LEARNED.md updates (BUG-006)</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.97 <span class="changelog-date">January 28, 2026</span></h3>
        <ul>
            <li><strong>NEW: Fix Assistant v2 - Complete premium document review interface</strong></li>
            <li><strong>NEW: Two-panel document viewer with page navigation and highlighting</strong></li>
            <li><strong>NEW: Mini-map showing document overview with fix position markers</strong></li>
            <li><strong>NEW: Undo/redo capability for all review decisions</strong></li>
            <li><strong>NEW: Search and filter fixes by text, category, or confidence</strong></li>
            <li><strong>NEW: Save progress and continue later (localStorage persistence)</strong></li>
            <li><strong>NEW: Learning from user decisions (pattern tracking, no AI)</strong></li>
            <li><strong>NEW: Custom dictionary for terms to always skip</strong></li>
            <li><strong>NEW: Live preview mode showing changes inline</strong></li>
            <li><strong>NEW: Split-screen view (original vs fixed document)</strong></li>
            <li><strong>NEW: PDF summary report generation</strong></li>
            <li><strong>NEW: Accessibility features (high contrast, screen reader support)</strong></li>
            <li><strong>NEW: Enhanced keyboard shortcuts (A=accept, R=reject, S=skip, U=undo)</strong></li>
            <li><strong>NEW: Optional sound effects for actions (Web Audio API)</strong></li>
            <li><strong>NEW: Rejected fixes exported as document comments with reviewer notes</strong></li>
            <li>IMPROVED: Export now handles both accepted fixes (track changes) and rejected fixes (comments)</li>
            <li>API: Added /api/learner/* endpoints for pattern learning</li>
            <li>API: Added /api/report/generate endpoint for PDF reports</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.96 <span class="changelog-date">January 27, 2026</span></h3>
        <ul>
            <li><strong>NEW: Fix Assistant - premium triage-style interface for reviewing automatic fixes</strong></li>
            <li><strong>NEW: Keyboard shortcuts in Fix Assistant (A=accept, R=reject, S=skip, arrows=nav)</strong></li>
            <li><strong>NEW: Confidence tiers (Safe/Review/Caution) for each proposed fix</strong></li>
            <li><strong>NEW: Context display showing surrounding text with highlighted change</strong></li>
            <li><strong>NEW: Before/After comparison with clear visual distinction</strong></li>
            <li><strong>NEW: Bulk actions (Accept All Safe, Accept All, Reject All)</strong></li>
            <li>IMPROVED: Export now uses Fix Assistant selections instead of all fixes</li>
            <li>IMPROVED: Progress tracking shows reviewed/total count</li>
            <li>UI: Premium styling with confidence badges, progress bar, keyboard hints</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.95 <span class="changelog-date">January 27, 2026</span></h3>
        <ul>
            <li><strong>FIX: Version display consistency - all UI components now show same version</strong></li>
            <li><strong>FIX: About section simplified - shows only author name</strong></li>
            <li><strong>FIX: Heatmap clicking - Category × Severity heatmap now filters issues on click</strong></li>
            <li><strong>NEW: Hyperlink status panel - visual display of checked hyperlinks and validation status</strong></li>
            <li>IMPROVED: Section heatmap click feedback with toast messages</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.94 <span class="changelog-date">January 27, 2026</span></h3>
        <ul>
            <li>STABILIZATION: Intermediate release between 3.0.93 and 3.0.95</li>
            <li><strong>FIX: Refinements to acronym detection logic</strong></li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.93 <span class="changelog-date">January 27, 2026</span></h3>
        <ul>
            <li>ACRONYM: Added 100+ common ALL CAPS words to COMMON_CAPS_SKIP</li>
            <li>ACRONYM: Added PDF word fragment detection</li>
            <li>TESTING: Reduced false positive acronym flagging by ~55%</li>
        </ul>
    </div>
    <div class="changelog-version">
        <h3>v3.0.92 <span class="changelog-date">January 27, 2026</span></h3>
        <ul>
            <li>FIXED: PDF punctuation false positives</li>
            <li>FIXED: Acronym false positives</li>
            <li>ADDED: PDF hyperlink extraction via PyMuPDF</li>
        </ul>
    </div>
</div>
`
};

// ============================================================================
// CINEMATIC TECHNOLOGY SHOWCASE
// ============================================================================
HelpDocs.content['cinema-showcase'] = {
    title: 'Behind the Scenes',
    subtitle: 'Watch AEGIS come alive in an animated cinematic showcase',
    html: `
<div class="help-hero">
    <div class="help-hero-icon"><i data-lucide="clapperboard"></i></div>
    <h2>Cinematic Technology Showcase</h2>
    <p>A full-screen animated video that tells the AEGIS story — from the problem it solves to every module in action. Built entirely with HTML5 Canvas, no pre-recorded video files needed.</p>
</div>

<div class="help-section">
    <h3><i data-lucide="play-circle"></i> Launching the Showcase</h3>
    <p>Click the <strong>Behind the Scenes</strong> tile on the AEGIS landing page. The cinematic opens in full-screen overlay with animated Canvas visuals and voice narration.</p>
    <div class="help-tip">
        <strong>Screen Recording:</strong> Use QuickTime Player (Mac) or OBS (Windows) to capture the showcase as a shareable .mp4 video.
    </div>
</div>

<div class="help-section">
    <h3><i data-lucide="film"></i> Story Structure (6 Acts, 18 Scenes)</h3>
    <ul>
        <li><strong>Act 1 — The Problem:</strong> Document chaos, endless standards, breaking point</li>
        <li><strong>Act 2 — The Solution:</strong> AEGIS boot sequence, HUD activation, document scanning</li>
        <li><strong>Act 3 — Deep Dive:</strong> Review engine, Statement Forge, Roles Studio, Proposal Compare, Hyperlink Validator, Learning System</li>
        <li><strong>Act 4 — The Numbers:</strong> Stats cascade, architecture overview</li>
        <li><strong>Act 5 — Air-Gapped:</strong> Fortress security, classified readiness</li>
        <li><strong>Act 6 — Finale:</strong> Module convergence, logo reveal</li>
    </ul>
    <p>Total runtime: approximately 6-8 minutes at 1x speed.</p>
</div>

<div class="help-section">
    <h3><i data-lucide="monitor"></i> Controls</h3>
    <ul>
        <li><strong>Play/Pause:</strong> Click the play button or press <kbd>Space</kbd></li>
        <li><strong>Seek:</strong> Click anywhere on the progress bar to jump to that point</li>
        <li><strong>Volume:</strong> Adjust the slider or mute narration</li>
        <li><strong>Fullscreen:</strong> Toggle browser fullscreen mode</li>
        <li><strong>Close:</strong> Click X or press <kbd>Escape</kbd></li>
    </ul>
    <p>Controls appear on hover and stay visible when paused.</p>
</div>

<div class="help-section">
    <h3><i data-lucide="sparkles"></i> Visual Style</h3>
    <p>Cyberpunk HUD aesthetic — dark backgrounds with glowing gold wireframes, holographic data streams, particle effects, scan lines, and vignette. Every frame is rendered programmatically via Canvas 2D.</p>
</div>

<div class="help-section">
    <h3><i data-lucide="volume-2"></i> Voice Narration</h3>
    <p>Each scene has a pre-generated MP3 narration clip (Microsoft JennyNeural voice). If audio files are unavailable, the system falls back to browser Web Speech API, then silent typewriter subtitles.</p>
</div>
`
};

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
            <p>Build Date: February 18, 2026</p>
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

console.log('[HelpDocs] Module loaded v5.9.21');
