/**
 * AEGIS Guide System - Cinematic Contextual Help & Guided Tour
 * ============================================================
 * A floating help beacon + guided tour system that helps users understand
 * each section of the AEGIS tool with contextual, interactive tours.
 *
 * Features:
 * - Floating pulsing "?" beacon (bottom-right, always visible)
 * - Contextual help slideout panel (right-side glass-morphism)
 * - Spotlight overlay guided tours (dark overlay with element cutout)
 * - Section-specific tours with step-by-step guidance
 * - Getting Started landing card with quick tour trigger
 * - Smooth animations and full dark mode support
 *
 * Version: 1.0.0
 */

'use strict';

const AEGISGuide = {
    // Configuration
    config: {
        beaconZIndex: 1500,      // Below toast (2500), above everything else
        spotlightZIndex: 1400,
        panelZIndex: 1450,
        animationDuration: 300,
        spotlightAnimDuration: 400
    },

    // State
    state: {
        panelOpen: false,
        tourActive: false,
        currentTourIndex: 0,
        currentSection: null,
        currentTour: null
    },

    // DOM references
    refs: {
        beacon: null,
        panel: null,
        spotlight: null,
        panelContent: null
    },

    /**
     * Section definitions with help content and tour steps
     */
    sections: {
        landing: {
            id: 'landing',
            title: 'Dashboard',
            icon: 'layout-dashboard',
            whatIsThis: 'Your mission control center. See document quality at a glance, recent activity, and quick access to all AEGIS features. Drop documents here to begin analysis.',
            keyActions: [
                { icon: 'file-text', text: 'Click any feature tile to jump to that tool' },
                { icon: 'bar-chart-2', text: 'View quality metrics and document statistics' },
                { icon: 'upload', text: 'Drag & drop or click to upload a document' }
            ],
            proTips: [
                'The quality score updates as you review more documents',
                'Each tile shows real-time statistics from your database',
                'Use the search bar to quickly find documents by name or type'
            ],
            tourSteps: [
                {
                    target: '.lp-hero',
                    title: 'Start Here',
                    description: 'Drag and drop your document here or click to browse. Supports .docx, .doc, and .pdf files.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '#lp-metrics',
                    title: 'Quick Metrics',
                    description: 'At-a-glance statistics about your documents, roles, quality scores, and review progress.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '#lp-tiles',
                    title: 'Feature Tiles',
                    description: 'Each tile represents a major AEGIS feature. Click any tile to jump directly to it. Or use the Dashboard button in the header to return here.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                }
            ]
        },

        review: {
            id: 'review',
            title: 'Document Review',
            icon: 'file-check',
            whatIsThis: 'Upload and review documents for quality, completeness, and compliance issues. AEGIS automatically checks for 100+ technical writing issues across grammar, clarity, consistency, and aerospace-specific requirements.',
            keyActions: [
                { icon: 'upload', text: 'Upload a document to begin review' },
                { icon: 'sliders-horizontal', text: 'Configure which checkers to run' },
                { icon: 'play', text: 'Run review to scan for issues' },
                { icon: 'download', text: 'Export detailed review report' }
            ],
            proTips: [
                'Use the Checkers panel to customize which quality checks run',
                'Results are organized by severity and issue type',
                'You can adjust checker settings per document before running review',
                'Dark mode automatically applies to all review interfaces'
            ],
            tourSteps: [
                {
                    target: '.review-upload-zone',
                    title: 'Upload Area',
                    description: 'Drop your document here or click the upload button. You can also select from previously uploaded documents.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.review-checkers-panel',
                    title: 'Checker Configuration',
                    description: 'Toggle checkers on/off to customize which quality issues are detected. Categories include Grammar, Clarity, Aerospace Requirements, and more.',
                    position: 'left',
                    offset: { x: -20, y: 0 }
                },
                {
                    target: '.review-run-button',
                    title: 'Run Review',
                    description: 'Click to start the analysis. AEGIS will scan your document against all enabled checkers.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.review-results-container',
                    title: 'Review Results',
                    description: 'Issues appear here organized by severity (Critical, Warning, Info). Click any issue to see details and suggested fixes.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                }
            ]
        },

        roles: {
            id: 'roles',
            title: 'Roles Studio',
            icon: 'users-round',
            whatIsThis: 'Analyze and visualize organizational roles found in your documents. View responsibilities, relationships, RACI matrices, and role hierarchies. Adjudicate roles and build a comprehensive role dictionary.',
            keyActions: [
                { icon: 'network', text: 'View role network and relationships' },
                { icon: 'table-2', text: 'Explore RACI matrices by document' },
                { icon: 'check-square', text: 'Adjudicate roles and responsibilities' },
                { icon: 'book', text: 'Build and manage your role dictionary' }
            ],
            proTips: [
                'The Overview tab shows role statistics and responsibilities',
                'RACI Matrix helps understand role interactions and dependencies',
                'Use Adjudication to resolve unclear or duplicate roles',
                'Export your role dictionary for use in other systems'
            ],
            tourSteps: [
                {
                    target: '.roles-tabs-container',
                    title: 'Role Studio Tabs',
                    description: 'Navigate between Overview (statistics), Graph (relationships), RACI Matrix (interactions), Adjudication (verification), and Dictionary (role catalog).',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.roles-overview-section',
                    title: 'Overview Tab',
                    description: 'See aggregate role statistics, top roles by mention count, and responsibility summaries across all documents.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                },
                {
                    target: '.roles-graph-section',
                    title: 'Graph View',
                    description: 'Visualize role relationships and hierarchies as an interactive network. Click nodes to explore role details.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                },
                {
                    target: '.roles-raci-section',
                    title: 'RACI Matrix',
                    description: 'Understand who is Responsible, Accountable, Consulted, and Informed for each function. Select a document to see role interactions.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                }
            ]
        },

        forge: {
            id: 'forge',
            title: 'Statement Forge',
            icon: 'lightbulb',
            whatIsThis: 'Search, review, and manage extracted statements across all documents. View statement history, sources, and context. Perform bulk operations and export findings.',
            keyActions: [
                { icon: 'search', text: 'Search statements by keyword or requirement type' },
                { icon: 'layers', text: 'View statement history and version changes' },
                { icon: 'eye', text: 'See original statement source in document' },
                { icon: 'package', text: 'Export statements for external review' }
            ],
            proTips: [
                'Search supports keywords like "shall", "must", "requirement", etc.',
                'Statement history shows when and how statements have changed',
                'Hover over statements to see highlighted source in the document viewer',
                'Use bulk operations to assign statuses or tags to multiple statements'
            ],
            tourSteps: [
                {
                    target: '.forge-search-bar',
                    title: 'Search Statements',
                    description: 'Type keywords to find specific statements across all documents. Results update as you type.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.forge-filters-panel',
                    title: 'Filter & Sort',
                    description: 'Filter by document, type, requirement class, or custom tags. Sort by relevance, date, or document order.',
                    position: 'left',
                    offset: { x: -20, y: 0 }
                },
                {
                    target: '.forge-statements-list',
                    title: 'Statement Results',
                    description: 'Each result shows the statement text, source document, and matched keywords. Click to view full context.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                },
                {
                    target: '.forge-source-viewer',
                    title: 'Source Viewer',
                    description: 'See exactly where this statement appears in the original document with highlighting.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                }
            ]
        },

        validator: {
            id: 'validator',
            title: 'Hyperlink Validator',
            icon: 'link-2',
            whatIsThis: 'Check hyperlinks in your documents for validity and accessibility. Run single-URL checks or batch validate all links. Test deep link content and detect broken references.',
            keyActions: [
                { icon: 'link', text: 'Check single URL for validity' },
                { icon: 'list', text: 'Batch validate all links in a document' },
                { icon: 'arrow-right', text: 'Deep validate - check content behind links' },
                { icon: 'download', text: 'Export validation report' }
            ],
            proTips: [
                'Use batch mode to quickly validate all links in a document',
                'Deep validation checks if linked content exists and is accessible',
                'Results show HTTP status, response time, and content preview',
                'Broken links are highlighted for quick identification'
            ],
            tourSteps: [
                {
                    target: '.validator-input-area',
                    title: 'URL Input',
                    description: 'Enter a URL or paste multiple URLs (one per line) to validate. Or select a document to check all its links.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.validator-options',
                    title: 'Validation Options',
                    description: 'Choose between quick check (HTTP status only) or deep validation (verify content). Enable SSL verification as needed.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.validator-results',
                    title: 'Results',
                    description: 'Each link shows status (✓ valid, ✗ broken), HTTP code, response time, and content preview. Color-coded by severity.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                }
            ]
        },

        metrics: {
            id: 'metrics',
            title: 'Metrics & Analytics',
            icon: 'bar-chart-3',
            whatIsThis: 'Track document quality trends, role distribution, checker effectiveness, and document metadata. View analytics by document type, quality score, and review progress.',
            keyActions: [
                { icon: 'trending-up', text: 'View quality trends over time' },
                { icon: 'pie-chart', text: 'See role and issue distribution' },
                { icon: 'filter', text: 'Filter analytics by document or date range' },
                { icon: 'download', text: 'Export charts and data' }
            ],
            proTips: [
                'Quality score aggregates across all documents and checkers',
                'You can filter by document type, date range, or specific checker',
                'Charts update automatically as you review more documents',
                'Export to CSV for use in external reporting tools'
            ],
            tourSteps: [
                {
                    target: '.metrics-overview-tab',
                    title: 'Overview Tab',
                    description: 'High-level metrics: total documents, quality score, critical issues, and review progress.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.metrics-quality-chart',
                    title: 'Quality Analytics',
                    description: 'Trend chart showing quality scores over time. See how your documents improve with iterative review.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                },
                {
                    target: '.metrics-distribution-chart',
                    title: 'Role Distribution',
                    description: 'Pie chart showing how roles are distributed across documents. Click to drill down by document.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                }
            ]
        },

        settings: {
            id: 'settings',
            title: 'Settings',
            icon: 'settings',
            whatIsThis: 'Configure AEGIS behavior, manage your data, and customize the user interface. Control theme, checkers, database options, and export/import settings.',
            keyActions: [
                { icon: 'sun-moon', text: 'Toggle dark/light mode' },
                { icon: 'sliders-horizontal', text: 'Configure default checker options' },
                { icon: 'database', text: 'Manage database and backups' },
                { icon: 'download', text: 'Export or import your data' }
            ],
            proTips: [
                'Dark mode automatically applies throughout AEGIS',
                'Your preferences are saved in browser storage',
                'Use data export to backup your work regularly',
                'Import data to transfer between machines'
            ],
            tourSteps: [
                {
                    target: '.settings-appearance-section',
                    title: 'Appearance Settings',
                    description: 'Toggle dark/light mode and customize how AEGIS looks. Changes apply immediately.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.settings-checkers-section',
                    title: 'Checker Defaults',
                    description: 'Set which checkers are enabled by default for new reviews. You can override these per document.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                },
                {
                    target: '.settings-data-section',
                    title: 'Data Management',
                    description: 'Export your analysis results, role dictionary, and document data. Import previously saved data.',
                    position: 'bottom',
                    offset: { x: 0, y: 20 }
                }
            ]
        },

        compare: {
            id: 'compare',
            title: 'Document Compare',
            icon: 'git-compare',
            whatIsThis: 'Compare two documents side-by-side to identify differences, similarities, and content gaps. Perfect for version control and change tracking.',
            keyActions: [
                { icon: 'file-text', text: 'Select two documents to compare' },
                { icon: 'eye', text: 'View differences highlighted side-by-side' },
                { icon: 'download', text: 'Export comparison report' }
            ],
            proTips: [
                'The oldest document typically appears on the left, newest on the right',
                'Changes are color-coded: added (green), removed (red), modified (yellow)',
                'Use comparison to track document versions and identify updates'
            ],
            tourSteps: [
                {
                    target: '.compare-selector-panel',
                    title: 'Select Documents',
                    description: 'Choose which documents to compare. Usually oldest on left, newest on right to show evolution.',
                    position: 'left',
                    offset: { x: -20, y: 0 }
                },
                {
                    target: '.compare-results-area',
                    title: 'Comparison View',
                    description: 'Side-by-side comparison with highlighting. Green = added, Red = removed, Yellow = modified.',
                    position: 'top',
                    offset: { x: 0, y: -20 }
                }
            ]
        }
    },

    /**
     * Initialize the guide system - call on app startup
     */
    init() {
        console.log('[AEGIS Guide] Initializing guide system...');

        // Create DOM elements
        this.createBeacon();
        this.createPanel();
        this.createSpotlight();

        // Attach event listeners
        this.attachEventListeners();

        console.log('[AEGIS Guide] Initialization complete');
    },

    /**
     * Create the floating help beacon
     */
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

    /**
     * Create the contextual help panel
     */
    createPanel() {
        const panel = document.createElement('div');
        panel.id = 'aegis-guide-panel';
        panel.className = 'aegis-guide-panel';

        panel.innerHTML = `
            <div class="panel-header">
                <h2 class="panel-title" id="panel-title">Help</h2>
                <button class="panel-close-btn" aria-label="Close help panel">
                    <svg class="close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>

            <div class="panel-content">
                <div class="panel-section what-is-this">
                    <p class="what-is-text" id="panel-what-is-this"></p>
                </div>

                <div class="panel-section key-actions">
                    <h3 class="section-title">Key Actions</h3>
                    <ul class="actions-list" id="panel-actions"></ul>
                </div>

                <div class="panel-section pro-tips">
                    <button class="tips-toggle" id="tips-toggle">
                        <span class="toggle-icon">▼</span>
                        <span>Pro Tips</span>
                    </button>
                    <ul class="tips-list hidden" id="panel-tips"></ul>
                </div>
            </div>

            <div class="panel-footer">
                <button class="panel-btn secondary-btn" id="tour-btn">
                    <span class="btn-icon">🎬</span>
                    <span>Watch Demo</span>
                </button>
                <button class="panel-btn primary-btn" id="full-tour-btn">
                    <span class="btn-icon">📍</span>
                    <span>Take Tour</span>
                </button>
            </div>
        `;

        document.body.appendChild(panel);
        this.refs.panel = panel;
        this.refs.panelContent = panel;
    },

    /**
     * Create the spotlight overlay for guided tours
     */
    createSpotlight() {
        const spotlight = document.createElement('div');
        spotlight.id = 'aegis-guide-spotlight';
        spotlight.className = 'aegis-guide-spotlight hidden';

        spotlight.innerHTML = `
            <div class="spotlight-overlay"></div>
            <div class="spotlight-tooltip">
                <div class="tooltip-header">
                    <span class="step-counter" id="step-counter">Step 1 of 1</span>
                    <button class="tooltip-close" aria-label="Close tour">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="tooltip-body">
                    <h3 class="tooltip-title" id="tooltip-title"></h3>
                    <p class="tooltip-description" id="tooltip-description"></p>
                </div>
                <div class="tooltip-controls">
                    <button class="control-btn skip-btn">Skip Tour</button>
                    <div class="dot-progress" id="dot-progress"></div>
                    <div class="nav-buttons">
                        <button class="control-btn prev-btn" id="prev-btn">← Back</button>
                        <button class="control-btn next-btn" id="next-btn">Next →</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(spotlight);
        this.refs.spotlight = spotlight;
    },

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Beacon click
        this.refs.beacon.addEventListener('click', () => this.togglePanel());

        // Panel close button
        const closeBtn = this.refs.panel.querySelector('.panel-close-btn');
        closeBtn.addEventListener('click', () => this.closePanel());

        // Pro tips toggle
        const tipsToggle = this.refs.panel.querySelector('#tips-toggle');
        tipsToggle.addEventListener('click', () => this.toggleTips());

        // Tour buttons
        const tourBtn = this.refs.panel.querySelector('#tour-btn');
        tourBtn.addEventListener('click', () => this.startTour());

        const fullTourBtn = this.refs.panel.querySelector('#full-tour-btn');
        fullTourBtn.addEventListener('click', () => this.startFullTour());

        // Spotlight controls
        const spotlight = this.refs.spotlight;
        spotlight.querySelector('.tooltip-close').addEventListener('click', () => this.endTour());
        spotlight.querySelector('.skip-btn').addEventListener('click', () => this.endTour());
        spotlight.querySelector('.prev-btn').addEventListener('click', () => this.previousStep());
        spotlight.querySelector('.next-btn').addEventListener('click', () => this.nextStep());

        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (this.state.panelOpen &&
                !e.target.closest('#aegis-guide-beacon') &&
                !e.target.closest('#aegis-guide-panel')) {
                this.closePanel();
            }
        });
    },

    /**
     * Toggle the help panel
     */
    togglePanel(section = null) {
        if (this.state.panelOpen) {
            this.closePanel();
        } else {
            this.openPanel(section);
        }
    },

    /**
     * Open the help panel with content for a section
     */
    openPanel(section = null) {
        // Detect current section if not provided
        if (!section) {
            section = this.detectCurrentSection();
        }

        if (!section || !this.sections[section]) {
            console.warn('[AEGIS Guide] Unknown section:', section);
            section = 'landing';
        }

        const sectionData = this.sections[section];
        this.state.currentSection = section;

        // Populate panel content
        this.refs.panel.querySelector('#panel-title').textContent = sectionData.title;
        this.refs.panel.querySelector('#panel-what-is-this').textContent = sectionData.whatIsThis;

        // Populate key actions
        const actionsList = this.refs.panel.querySelector('#panel-actions');
        actionsList.innerHTML = sectionData.keyActions
            .map(action => `
                <li class="action-item">
                    <span class="action-icon" data-lucide="${action.icon}"></span>
                    <span class="action-text">${action.text}</span>
                </li>
            `)
            .join('');

        // Populate pro tips
        const tipsList = this.refs.panel.querySelector('#panel-tips');
        tipsList.innerHTML = sectionData.proTips
            .map(tip => `<li class="tip-item">💡 ${tip}</li>`)
            .join('');

        // Show panel
        this.refs.panel.classList.remove('hidden');
        this.state.panelOpen = true;

        // Re-render lucide icons in the panel
        if (window.lucide) {
            window.lucide.createIcons();
        }

        console.log('[AEGIS Guide] Panel opened for section:', section);
    },

    /**
     * Close the help panel
     */
    closePanel() {
        this.refs.panel.classList.add('hidden');
        this.state.panelOpen = false;
        console.log('[AEGIS Guide] Panel closed');
    },

    /**
     * Toggle pro tips visibility
     */
    toggleTips() {
        const tipsList = this.refs.panel.querySelector('#panel-tips');
        const toggle = this.refs.panel.querySelector('#tips-toggle');

        tipsList.classList.toggle('hidden');
        toggle.classList.toggle('expanded');
    },

    /**
     * Start section-specific tour
     */
    startTour() {
        const section = this.state.currentSection;
        const sectionData = this.sections[section];

        if (!sectionData || !sectionData.tourSteps || sectionData.tourSteps.length === 0) {
            console.warn('[AEGIS Guide] No tour steps for section:', section);
            return;
        }

        this.closePanel();
        this.state.tourActive = true;
        this.state.currentTourIndex = 0;
        this.state.currentTour = sectionData.tourSteps;

        this.showStep(0);
        console.log('[AEGIS Guide] Section tour started:', section);
    },

    /**
     * Start full application tour
     */
    startFullTour() {
        // Combine tours from key sections in logical order
        const tourOrder = ['landing', 'review', 'roles', 'forge', 'validator', 'metrics'];
        let fullTour = [];

        tourOrder.forEach(sectionId => {
            const section = this.sections[sectionId];
            if (section && section.tourSteps) {
                fullTour = fullTour.concat(section.tourSteps);
            }
        });

        this.closePanel();
        this.state.tourActive = true;
        this.state.currentTourIndex = 0;
        this.state.currentTour = fullTour;

        this.showStep(0);
        console.log('[AEGIS Guide] Full tour started with', fullTour.length, 'steps');
    },

    /**
     * Show a specific tour step
     */
    showStep(index) {
        if (!this.state.currentTour || index < 0 || index >= this.state.currentTour.length) {
            this.endTour();
            return;
        }

        this.state.currentTourIndex = index;
        const step = this.state.currentTour[index];

        // Find target element
        const target = document.querySelector(step.target);
        if (!target) {
            console.warn('[AEGIS Guide] Tour step target not found:', step.target);
            this.nextStep();
            return;
        }

        // Update tooltip content
        this.refs.spotlight.querySelector('#step-counter').textContent =
            `Step ${index + 1} of ${this.state.currentTour.length}`;
        this.refs.spotlight.querySelector('#tooltip-title').textContent = step.title;
        this.refs.spotlight.querySelector('#tooltip-description').textContent = step.description;

        // Update progress dots
        this.updateProgressDots(index);

        // Show spotlight on target
        this.showSpotlight(target, step.position, step.offset);

        // Show spotlight element
        this.refs.spotlight.classList.remove('hidden');

        console.log('[AEGIS Guide] Showing step', index + 1, 'of', this.state.currentTour.length);
    },

    /**
     * Show spotlight overlay on target element
     */
    showSpotlight(element, position = 'bottom', offset = { x: 0, y: 0 }) {
        const spotlight = this.refs.spotlight;
        const tooltip = spotlight.querySelector('.spotlight-tooltip');
        const rect = element.getBoundingClientRect();

        // Scroll element into view if needed
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });

        // Create cutout for target element
        const padding = 8;
        const cutout = {
            x: rect.left - padding,
            y: rect.top - padding,
            width: rect.width + padding * 2,
            height: rect.height + padding * 2
        };

        // Create SVG mask for spotlight
        const svgNS = 'http://www.w3.org/2000/svg';
        const svg = document.createElementNS(svgNS, 'svg');
        svg.setAttribute('width', window.innerWidth);
        svg.setAttribute('height', window.innerHeight);
        svg.setAttribute('style', 'position: absolute; top: 0; left: 0;');

        const defs = document.createElementNS(svgNS, 'defs');
        const mask = document.createElementNS(svgNS, 'mask');
        mask.setAttribute('id', 'spotlightMask');

        const background = document.createElementNS(svgNS, 'rect');
        background.setAttribute('width', '100%');
        background.setAttribute('height', '100%');
        background.setAttribute('fill', 'white');

        const cutoutRect = document.createElementNS(svgNS, 'rect');
        cutoutRect.setAttribute('x', cutout.x);
        cutoutRect.setAttribute('y', cutout.y);
        cutoutRect.setAttribute('width', cutout.width);
        cutoutRect.setAttribute('height', cutout.height);
        cutoutRect.setAttribute('fill', 'black');
        cutoutRect.setAttribute('rx', '8');

        mask.appendChild(background);
        mask.appendChild(cutoutRect);
        defs.appendChild(mask);
        svg.appendChild(defs);

        const overlay = document.createElementNS(svgNS, 'rect');
        overlay.setAttribute('width', '100%');
        overlay.setAttribute('height', '100%');
        overlay.setAttribute('fill', 'rgba(0, 0, 0, 0.7)');
        overlay.setAttribute('mask', 'url(#spotlightMask)');
        svg.appendChild(overlay);

        // Replace old SVG if exists
        const oldSvg = spotlight.querySelector('svg');
        if (oldSvg) {
            spotlight.removeChild(oldSvg);
        }
        spotlight.insertBefore(svg, spotlight.querySelector('.spotlight-tooltip'));

        // Position tooltip
        this.positionTooltip(tooltip, rect, position, offset);
    },

    /**
     * Position the tooltip relative to the target element
     */
    positionTooltip(tooltip, targetRect, position, offset = { x: 0, y: 0 }) {
        const tooltipRect = tooltip.getBoundingClientRect();
        const margin = 20;
        let top, left;

        switch (position) {
            case 'top':
                top = targetRect.top - tooltipRect.height - margin;
                left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = targetRect.bottom + margin;
                left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.left - tooltipRect.width - margin;
                break;
            case 'right':
                top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.right + margin;
                break;
            default:
                position = 'bottom';
                top = targetRect.bottom + margin;
                left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
        }

        // Apply offset
        top += offset.y || 0;
        left += offset.x || 0;

        // Keep tooltip in viewport
        const viewportPadding = 20;
        if (left < viewportPadding) left = viewportPadding;
        if (left + tooltipRect.width > window.innerWidth - viewportPadding) {
            left = window.innerWidth - tooltipRect.width - viewportPadding;
        }
        if (top < viewportPadding) top = viewportPadding;
        if (top + tooltipRect.height > window.innerHeight - viewportPadding) {
            top = window.innerHeight - tooltipRect.height - viewportPadding;
        }

        tooltip.style.position = 'fixed';
        tooltip.style.top = top + 'px';
        tooltip.style.left = left + 'px';
    },

    /**
     * Update progress dots
     */
    updateProgressDots(currentIndex) {
        const dotsContainer = this.refs.spotlight.querySelector('#dot-progress');
        if (!dotsContainer) return;

        dotsContainer.innerHTML = '';

        for (let i = 0; i < this.state.currentTour.length; i++) {
            const dot = document.createElement('span');
            dot.className = 'progress-dot' + (i === currentIndex ? ' active' : '');
            dotsContainer.appendChild(dot);
        }
    },

    /**
     * Next tour step
     */
    nextStep() {
        if (this.state.tourActive) {
            this.showStep(this.state.currentTourIndex + 1);
        }
    },

    /**
     * Previous tour step
     */
    previousStep() {
        if (this.state.tourActive) {
            this.showStep(this.state.currentTourIndex - 1);
        }
    },

    /**
     * End the tour
     */
    endTour() {
        this.state.tourActive = false;
        this.state.currentTourIndex = 0;
        this.state.currentTour = null;
        this.refs.spotlight.classList.add('hidden');
        console.log('[AEGIS Guide] Tour ended');
    },

    /**
     * Detect which section is currently visible
     */
    detectCurrentSection() {
        // Check which modal or view is currently active
        if (document.getElementById('aegis-landing-page')?.offsetParent !== null) {
            return 'landing';
        }
        if (document.getElementById('modal-review')?.classList.contains('active')) {
            return 'review';
        }
        if (document.getElementById('modal-roles')?.classList.contains('active')) {
            return 'roles';
        }
        if (document.getElementById('modal-forge')?.classList.contains('active')) {
            return 'forge';
        }
        if (document.getElementById('modal-hyperlink')?.classList.contains('active')) {
            return 'validator';
        }
        if (document.getElementById('modal-metrics')?.classList.contains('active')) {
            return 'metrics';
        }
        if (document.getElementById('modal-settings')?.classList.contains('active')) {
            return 'settings';
        }
        if (document.getElementById('modal-compare')?.classList.contains('active')) {
            return 'compare';
        }

        return 'landing';
    },

    /**
     * Open help for a specific section
     * Call from modal open handlers: AEGISGuide.openSectionHelp('review')
     */
    openSectionHelp(sectionId) {
        this.openPanel(sectionId);
    },

    /**
     * Add a help button to a modal header
     * Call from modal initialization: AEGISGuide.addHelpButton(modalElement, 'roles')
     */
    addHelpButton(modalElement, sectionId) {
        if (!modalElement) return;

        const header = modalElement.querySelector('.modal-header');
        if (!header) return;

        // Check if help button already exists
        if (header.querySelector('.modal-help-btn')) return;

        const helpBtn = document.createElement('button');
        helpBtn.className = 'modal-help-btn';
        helpBtn.setAttribute('aria-label', 'Help for this section');
        helpBtn.setAttribute('title', 'Help');
        helpBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 16v-4M12 8h.01"></path>
            </svg>
        `;

        helpBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.openSectionHelp(sectionId);
        });

        // Insert before close button if exists
        const closeBtn = header.querySelector('.modal-close-btn');
        if (closeBtn) {
            header.insertBefore(helpBtn, closeBtn);
        } else {
            header.appendChild(helpBtn);
        }
    }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        AEGISGuide.init();
    });
} else {
    AEGISGuide.init();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AEGISGuide;
}
