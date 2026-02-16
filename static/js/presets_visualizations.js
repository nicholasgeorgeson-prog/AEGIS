/**
 * AEGIS v2.9.3 - Presets & Visualizations Module
 * =========================================================
 * 
 * Batch 5 Features:
 * - F09: Interactive Visualizations (progressive disclosure, clickable charts)
 * - F15: Enhanced Roles Card (force-directed network graph, stats cards)
 * - F16: Quick Presets (PrOP, PAL)
 * - F18: FGOST Document Preset
 * 
 * Batch 6 Features:
 * - F19a: Connected/Restricted Mode Toggle UI
 * 
 * This module should be loaded AFTER app.js and integrates with existing functionality.
 */

'use strict';

// ============================================================
// F16/F18: DOCUMENT PRESETS CONFIGURATION
// ============================================================

const DOCUMENT_PRESETS = {
    // PrOP: Procedures & Requirements with Obligations Protocol
    prop: {
        name: 'PrOP',
        fullName: 'Procedures & Requirements with Obligations Protocol',
        description: 'For documents with shall/must/will statements',
        icon: 'file-check',
        checkers: [
            'requirements_language', 'passive_voice', 'weak_language',
            'ambiguous_pronouns', 'testability', 'atomicity', 
            'tbd', 'escape_clauses', 'acronyms', 'terminology',
            'consistency', 'sentence_length'
        ],
        focusAreas: [
            'Passive voice in requirements',
            'Ambiguous terms (adequate, appropriate, etc.)',
            'Missing subjects ("shall be" without actor)',
            'Directive consistency'
        ],
        severity_overrides: {
            'passive_voice': 'high',
            'requirements_language': 'high',
            'ambiguous_pronouns': 'high'
        }
    },
    
    // PAL: Procedures & Actionable Language
    pal: {
        name: 'PAL',
        fullName: 'Procedures & Actionable Language',
        description: 'For work instructions and detailed engineering documents',
        icon: 'list-ordered',
        checkers: [
            'passive_voice', 'weak_language', 'sentence_length',
            'grammar', 'spelling', 'punctuation', 'acronyms',
            'consistency', 'repeated_words', 'capitalization'
        ],
        focusAreas: [
            'Clear action verbs',
            'Complete sentences',
            'Logical flow',
            'Note/warning/caution detection'
        ],
        severity_overrides: {
            'passive_voice': 'medium',
            'requirements_language': 'info'
        }
    },
    
    // FGOST: Flight and Ground Operations Standardization Team
    fgost: {
        name: 'FGOST',
        fullName: 'Flight and Ground Operations Standardization Team',
        description: 'For operations standardization documents',
        icon: 'rocket',
        checkers: [
            'hyperlinks', 'acronyms', 'references', 'roles',
            'grammar', 'spelling', 'consistency', 'terminology',
            'document_structure', 'tables_figures'
        ],
        focusAreas: [
            'Hyperlink validation (critical for ops docs)',
            'Acronym consistency',
            'Cross-reference validation',
            'Safety-critical language'
        ],
        severity_overrides: {
            'hyperlinks': 'critical',
            'references': 'high',
            'passive_voice': 'info'
        },
        custom_acronyms: [
            'FGOST', 'FD', 'GC', 'MCC', 'MOCR', 'FCR',
            'TDRS', 'TDRSS', 'AOS', 'LOS', 'TIG', 'TCA', 'PTC',
            'CAPCOM', 'EECOM', 'GNC', 'PROP', 'EGIL', 'FAO',
            'INCO', 'OSO', 'PAO', 'PDRS', 'ROBO', 'EVA'
        ],
        custom_roles: [
            'Flight Director', 'Ground Controller', 'CAPCOM',
            'Flight Dynamics Officer', 'Guidance Officer',
            'Payload Officer', 'Systems Engineer (Ops)',
            'Mission Control', 'Flight Controller'
        ]
    }
};

/**
 * Detect document type based on content analysis
 */
function detectDocumentType(text) {
    if (!text || text.length < 100) return null;
    
    const textLower = text.toLowerCase();
    
    // Count directive patterns
    const shallCount = (text.match(/\bshall\b/gi) || []).length;
    const mustCount = (text.match(/\bmust\b/gi) || []).length;
    const willCount = (text.match(/\bwill\b/gi) || []).length;
    
    // Count procedure patterns
    const stepPatterns = (text.match(/\bstep\s+\d+|\bprocedure\s+\d+/gi) || []).length;
    const notePatterns = (text.match(/\b(?:note|warning|caution):/gi) || []).length;
    
    // Count FGOST indicators
    const opsTerms = ['flight director', 'mission control', 'ground control', 
                      'telemetry', 'downlink', 'uplink', 'acquisition of signal',
                      'loss of signal', 'orbit', 'trajectory'].filter(term => 
                      textLower.includes(term)).length;
    
    // Score each preset
    const scores = {
        prop: (shallCount * 2) + (mustCount * 1.5) + (willCount * 0.5),
        pal: (stepPatterns * 2) + (notePatterns * 1.5),
        fgost: opsTerms * 3
    };
    
    // Find highest score
    const maxScore = Math.max(...Object.values(scores));
    if (maxScore < 5) return null;
    
    const detected = Object.entries(scores).find(([_, score]) => score === maxScore);
    return detected ? detected[0] : null;
}

/**
 * Show preset suggestion banner after document upload
 */
function showPresetSuggestion(presetKey) {
    const preset = DOCUMENT_PRESETS[presetKey];
    if (!preset) return;
    
    const existing = document.querySelector('.preset-suggestion-banner');
    if (existing) existing.remove();
    
    const banner = document.createElement('div');
    banner.className = 'preset-suggestion-banner';
    banner.innerHTML = `
        <i data-lucide="${preset.icon}"></i>
        <span>💡 This looks like a ${preset.description.toLowerCase()}. Use <strong>${preset.name}</strong> preset?</span>
        <div class="preset-suggestion-actions">
            <button class="btn btn-sm btn-primary" onclick="applyDocumentPreset('${presetKey}'); this.closest('.preset-suggestion-banner').remove();">
                Yes, use ${preset.name}
            </button>
            <button class="btn btn-sm btn-ghost" onclick="this.closest('.preset-suggestion-banner').remove();">
                No thanks
            </button>
        </div>
    `;
    
    const fileInfo = document.querySelector('.file-info') || document.querySelector('.document-panel');
    if (fileInfo) {
        fileInfo.after(banner);
    }
    
    if (typeof lucide !== 'undefined') {
        try { lucide.createIcons(); } catch(e) {}
    }
    
    setTimeout(() => {
        if (banner.parentNode) {
            banner.classList.add('fade-out');
            setTimeout(() => banner.remove(), 300);
        }
    }, 15000);
}

/**
 * Apply a document preset
 */
function applyDocumentPreset(presetKey) {
    const preset = DOCUMENT_PRESETS[presetKey];
    if (!preset) {
        console.warn(`Unknown preset: ${presetKey}`);
        return;
    }
    
    const checkboxes = document.querySelectorAll('[data-checker]');
    checkboxes.forEach(cb => cb.checked = false);
    
    preset.checkers.forEach(checker => {
        const el = document.querySelector(`[data-checker="${checker}"]`);
        if (el) el.checked = true;
    });
    
    document.querySelectorAll('[id^="btn-preset-"]').forEach(b => b.classList.remove('active'));
    const presetBtn = document.getElementById(`btn-preset-${presetKey}`);
    if (presetBtn) presetBtn.classList.add('active');
    
    if (typeof State !== 'undefined') {
        State.activePreset = presetKey;
    }
    
    if (typeof toast === 'function') {
        toast('success', `Applied ${preset.name} preset: ${preset.description}`);
    }
    
    console.log(`[TWR] Applied preset: ${preset.name}`, preset.checkers);
}

// ============================================================
// F19a: NETWORK VALIDATION MODE TOGGLE
// ============================================================

const NetworkValidationMode = {
    RESTRICTED: 'restricted',
    CONNECTED: 'connected'
};

let currentValidationMode = NetworkValidationMode.RESTRICTED;

/**
 * Initialize validation mode toggle UI
 */
function initValidationModeToggle() {
    const container = document.getElementById('validation-mode-container');
    if (!container) {
        console.log('[TWR] Validation mode container not found, skipping init');
        return;
    }
    
    container.innerHTML = `
        <div class="validation-mode-toggle">
            <span class="mode-label">Hyperlink Validation:</span>
            <div class="mode-options">
                <label class="mode-option ${currentValidationMode === 'restricted' ? 'active' : ''}">
                    <input type="radio" name="validation-mode" value="restricted" 
                           ${currentValidationMode === 'restricted' ? 'checked' : ''}>
                    <i data-lucide="shield"></i>
                    <span>Restricted</span>
                </label>
                <label class="mode-option ${currentValidationMode === 'connected' ? 'active' : ''}">
                    <input type="radio" name="validation-mode" value="connected"
                           ${currentValidationMode === 'connected' ? 'checked' : ''}>
                    <i data-lucide="globe"></i>
                    <span>Connected</span>
                </label>
            </div>
            <div class="mode-info">
                <i data-lucide="info" class="info-icon"></i>
                <span class="mode-description">
                    ${currentValidationMode === 'restricted' 
                        ? 'Internal links only - for restricted networks' 
                        : 'Full validation - when external access available'}
                </span>
            </div>
        </div>
    `;
    
    container.querySelectorAll('input[name="validation-mode"]').forEach(radio => {
        radio.addEventListener('change', (e) => setValidationMode(e.target.value));
    });
    
    if (typeof lucide !== 'undefined') {
        try { lucide.createIcons(); } catch(e) {}
    }
}

/**
 * Set validation mode
 */
function setValidationMode(mode) {
    currentValidationMode = mode;
    
    document.querySelectorAll('.mode-option').forEach(opt => {
        opt.classList.toggle('active', opt.querySelector('input').value === mode);
    });
    
    const desc = document.querySelector('.mode-description');
    if (desc) {
        desc.textContent = mode === 'restricted' 
            ? 'Internal links only - for restricted networks' 
            : 'Full validation - when external access available';
    }
    
    try { localStorage.setItem('twr_validation_mode', mode); } catch(e) {}
    
    if (typeof toast === 'function') {
        toast('info', `Validation mode: ${mode === 'restricted' ? 'Restricted (internal only)' : 'Connected (full validation)'}`);
    }
    
    console.log(`[TWR] Validation mode set to: ${mode}`);
}

function getValidationMode() {
    return currentValidationMode;
}

function loadValidationMode() {
    try {
        const saved = localStorage.getItem('twr_validation_mode');
        if (saved && (saved === 'restricted' || saved === 'connected')) {
            currentValidationMode = saved;
        }
    } catch(e) {}
}

// ============================================================
// F09: INTERACTIVE VISUALIZATIONS
// ============================================================

const VisualizationState = {
    severityChart: null,
    categoryChart: null,
    healthGauge: null,
    activeFilter: null
};

/**
 * Enhanced severity chart with center total and click-to-filter
 */
function renderEnhancedSeverityChart(data) {
    const canvas = document.getElementById('chart-severity');
    if (!canvas || typeof Chart === 'undefined') return;
    
    const ctx = canvas.getContext('2d');
    const sevData = data.by_severity || {};
    const total = Object.values(sevData).reduce((a, b) => a + b, 0);
    
    if (VisualizationState.severityChart) {
        VisualizationState.severityChart.destroy();
    }
    
    const SEVERITY_COLORS = {
        'Critical': '#DC3545',
        'High': '#FD7E14', 
        'Medium': '#FFC107',
        'Low': '#28A745',
        'Info': '#17A2B8'
    };
    
    const centerTextPlugin = {
        id: 'centerText',
        afterDraw: (chart) => {
            const {ctx, width, height} = chart;
            ctx.save();
            ctx.font = 'bold 24px system-ui, -apple-system, sans-serif';
            ctx.fillStyle = '#e0e0e0';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(total.toString(), width / 2, height / 2 - 8);
            ctx.font = '12px system-ui, -apple-system, sans-serif';
            ctx.fillStyle = '#a0a0a0';
            ctx.fillText('issues', width / 2, height / 2 + 14);
            ctx.restore();
        }
    };
    
    VisualizationState.severityChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(sevData),
            datasets: [{
                data: Object.values(sevData),
                backgroundColor: Object.keys(sevData).map(s => SEVERITY_COLORS[s] || '#7F8C8D'),
                borderWidth: 2,
                borderColor: 'rgba(26, 26, 46, 0.8)',
                hoverBorderWidth: 3,
                hoverBorderColor: 'rgba(255,255,255,0.5)',
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 500,
                easing: 'easeOutQuart'
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        font: { size: 11 },
                        usePointStyle: true,
                        pointStyle: 'circle',
                        color: '#e0e0e0'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const value = context.raw;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const label = Object.keys(sevData)[index];
                    if (typeof setChartFilter === 'function') {
                        setChartFilter('severity', label);
                    }
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        },
        plugins: [centerTextPlugin]
    });
}

/**
 * Enhanced category chart with click-to-filter
 */
function renderEnhancedCategoryChart(data) {
    const canvas = document.getElementById('chart-categories');
    if (!canvas || typeof Chart === 'undefined') return;
    
    const ctx = canvas.getContext('2d');
    const catData = data.by_category || {};
    const sortedCats = Object.entries(catData).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const fullLabels = sortedCats.map(c => c[0]);
    
    if (VisualizationState.categoryChart) {
        VisualizationState.categoryChart.destroy();
    }
    
    VisualizationState.categoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedCats.map(c => truncateText(c[0], 20)),
            datasets: [{
                data: sortedCats.map(c => c[1]),
                backgroundColor: 'rgba(77, 171, 247, 0.7)',
                borderColor: 'rgba(77, 171, 247, 0.9)',
                borderWidth: 1,
                borderRadius: 4,
                hoverBackgroundColor: 'rgba(77, 171, 247, 0.95)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            animation: { duration: 500, easing: 'easeOutQuart' },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: (items) => fullLabels[items[0].dataIndex],
                        label: (context) => `${context.raw} issues`
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: { precision: 0, color: '#a0a0a0' },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y: {
                    ticks: { font: { size: 11 }, color: '#e0e0e0' },
                    grid: { display: false }
                }
            },
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const label = fullLabels[index];
                    if (typeof setChartFilter === 'function') {
                        setChartFilter('category', label);
                    }
                }
            },
            onHover: (event, elements) => {
                event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
            }
        }
    });
}

/**
 * Document Health Gauge
 */
function renderHealthGauge(score) {
    const container = document.getElementById('health-gauge-container');
    if (!container) return;
    
    let color, label;
    if (score >= 90) { color = '#51cf66'; label = 'Excellent'; }
    else if (score >= 75) { color = '#94d82d'; label = 'Good'; }
    else if (score >= 60) { color = '#ffd43b'; label = 'Fair'; }
    else if (score >= 40) { color = '#ff922b'; label = 'Needs Work'; }
    else { color = '#ff6b6b'; label = 'Poor'; }
    
    const rotation = ((score / 100) * 180) - 90;
    
    container.innerHTML = `
        <div class="health-gauge" title="Document Health Score">
            <svg viewBox="0 0 200 120" class="gauge-svg">
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="20" stroke-linecap="round"/>
                <defs>
                    <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#ff6b6b"/>
                        <stop offset="25%" stop-color="#ff922b"/>
                        <stop offset="50%" stop-color="#ffd43b"/>
                        <stop offset="75%" stop-color="#94d82d"/>
                        <stop offset="100%" stop-color="#51cf66"/>
                    </linearGradient>
                </defs>
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#gaugeGradient)" stroke-width="20" stroke-linecap="round" stroke-dasharray="${(score / 100) * 251.2} 251.2" class="gauge-score-arc"/>
                <g class="gauge-needle" style="transform: rotate(${rotation}deg); transform-origin: 100px 100px; transition: transform 1s cubic-bezier(0.34, 1.56, 0.64, 1);">
                    <line x1="100" y1="100" x2="100" y2="30" stroke="${color}" stroke-width="3" stroke-linecap="round"/>
                    <circle cx="100" cy="100" r="8" fill="${color}"/>
                </g>
                <text x="100" y="85" text-anchor="middle" class="gauge-score" fill="#e0e0e0" font-size="24" font-weight="bold">${score}</text>
                <text x="100" y="105" text-anchor="middle" class="gauge-label" fill="#a0a0a0" font-size="12">${label}</text>
            </svg>
        </div>
    `;
}

/**
 * Issue density heatmap by section
 */
function renderIssueHeatmap(issues) {
    const container = document.getElementById('issue-heatmap-container');
    if (!container || !issues || issues.length === 0) return;
    
    const issuesBySection = {};
    issues.forEach(issue => {
        const section = issue.section || 'Other';
        issuesBySection[section] = (issuesBySection[section] || 0) + 1;
    });
    
    const sortedSections = Object.entries(issuesBySection).sort((a, b) => b[1] - a[1]).slice(0, 8);
    if (sortedSections.length === 0) return;
    
    const maxCount = Math.max(...sortedSections.map(s => s[1]));
    
    container.innerHTML = `
        <div class="heatmap-header">
            <span>Issue Density by Section</span>
        </div>
        <div class="heatmap-rows">
            ${sortedSections.map(([section, count]) => {
                const percentage = (count / maxCount) * 100;
                const intensity = count > maxCount * 0.7 ? 'high' : count > maxCount * 0.3 ? 'med' : 'low';
                return `
                    <div class="heatmap-row" onclick="filterBySection('${escapeHtml(section)}')" title="Click to filter">
                        <span class="heatmap-section">${truncateText(section, 15)}</span>
                        <div class="heatmap-bar-container">
                            <div class="heatmap-bar ${intensity}" style="width: ${percentage}%"></div>
                        </div>
                        <span class="heatmap-count">${count}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function filterBySection(section) {
    if (typeof setChartFilter === 'function') {
        setChartFilter('section', section);
    }
    if (typeof toast === 'function') {
        toast('info', `Filtered to section: ${section}`);
    }
}

// ============================================================
// F15: ENHANCED ROLES CARD
// ============================================================

const ROLE_CATEGORY_COLORS = {
    'Engineering': '#4dabf7',
    'Management': '#51cf66',
    'Quality': '#da77f2',
    'Security': '#ff6b6b',
    'Logistics': '#ffd43b',
    'Customer/Gov': '#20c997',
    'Operations': '#74c0fc',
    'Technical': '#748ffc',
    'default': '#868e96'
};

/**
 * Render enhanced roles card with mini network graph
 */
function renderEnhancedRolesCard(rolesData) {
    const container = document.getElementById('roles-card-enhanced');
    if (!container) return;
    
    const roles = rolesData.roles || rolesData;
    const roleEntries = Object.entries(roles);
    
    if (roleEntries.length === 0) {
        container.innerHTML = '<p class="text-muted">No roles detected in document</p>';
        return;
    }
    
    const totalRoles = roleEntries.length;
    let totalResponsibilities = 0;
    const categories = new Set();
    
    roleEntries.forEach(([_, data]) => {
        if (typeof data === 'object') {
            totalResponsibilities += data.responsibilities?.length || data.count || 1;
            if (data.category) categories.add(data.category);
        }
    });
    
    const confidenceScore = calculateRoleConfidence(roleEntries);
    
    container.innerHTML = `
        <div class="roles-enhanced-header">
            <h3><i data-lucide="users"></i> Roles & Responsibilities</h3>
            <button class="btn btn-sm btn-ghost" onclick="showRolesModal()">
                <i data-lucide="maximize-2"></i> Open Studio
            </button>
        </div>
        
        <div class="roles-network-graph-container" id="roles-mini-graph">
            <div class="graph-loading"><div class="spinner"></div><span>Building network...</span></div>
        </div>
        
        <div class="roles-stats-row">
            <div class="stat-card" title="Total unique roles detected">
                <div class="stat-value">${totalRoles}</div>
                <div class="stat-label">Unique Roles</div>
            </div>
            <div class="stat-card" title="Extraction confidence">
                <div class="stat-value">${confidenceScore}%</div>
                <div class="stat-label">Confidence</div>
            </div>
            <div class="stat-card" title="Role categories">
                <div class="stat-value">${categories.size || '—'}</div>
                <div class="stat-label">Categories</div>
            </div>
        </div>
        
        <div class="roles-top-list">
            <h4>Top Roles</h4>
            ${renderTopRolesChart(roleEntries.slice(0, 5))}
        </div>
        
        <div class="roles-actions-row">
            <button class="btn btn-sm btn-ghost" onclick="exportRoles('raci')" title="Export RACI"><i data-lucide="table"></i> RACI</button>
            <button class="btn btn-sm btn-ghost" onclick="showRolesModal()" title="Analyze"><i data-lucide="bar-chart-3"></i> Analyze</button>
        </div>
    `;
    
    if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    
    setTimeout(() => renderMiniRolesGraph(roleEntries), 100);
}

function calculateRoleConfidence(roleEntries) {
    if (roleEntries.length === 0) return 0;
    let total = 0, count = 0;
    roleEntries.forEach(([_, data]) => {
        total += (typeof data === 'object' && data.confidence !== undefined) ? data.confidence : 0.7;
        count++;
    });
    return Math.round((total / count) * 100);
}

function renderTopRolesChart(topRoles) {
    if (topRoles.length === 0) return '<p class="text-muted">No roles found</p>';

    const maxCount = Math.max(...topRoles.map(([_, d]) => typeof d === 'object' ? (d.frequency || d.count || 1) : 1));

    // v4.0.3: Adjudication badges
    const adjLookup = window.AEGIS?.AdjudicationLookup;

    return `<div class="top-roles-chart">${topRoles.map(([name, data]) => {
        const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
        const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
        const percentage = (count / maxCount) * 100;
        const category = typeof data === 'object' ? data.category : 'default';
        const color = ROLE_CATEGORY_COLORS[category] || ROLE_CATEGORY_COLORS.default;
        const adjBadge = adjLookup ? adjLookup.getBadge(displayName, { compact: true, size: 'sm' }) : '';
        return `
            <div class="role-bar-row" onclick="filterByRole('${escapeHtmlAttr(name)}')" title="Click to filter">
                <span class="role-name">${truncateText(displayName, 20)}${adjBadge}</span>
                <div class="role-bar-container"><div class="role-bar" style="width: ${percentage}%; background: ${color}"></div></div>
                <span class="role-count">${count}</span>
            </div>
        `;
    }).join('')}</div>`;
}

function renderMiniRolesGraph(roleEntries) {
    const container = document.getElementById('roles-mini-graph');
    if (!container || typeof d3 === 'undefined') {
        if (container) container.innerHTML = '<p class="text-muted">Graph unavailable</p>';
        return;
    }
    
    const nodes = [], links = [];
    roleEntries.forEach(([name, data]) => {
        const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
        const category = typeof data === 'object' ? data.category : 'default';
        nodes.push({
            id: name,
            name: typeof data === 'object' ? (data.canonical_name || name) : name,
            count, category,
            radius: Math.max(6, Math.min(16, 4 + Math.sqrt(count) * 2.5))
        });
    });
    
    for (let i = 0; i < nodes.length && i < 15; i++) {
        for (let j = i + 1; j < nodes.length && j < i + 3; j++) {
            links.push({ source: nodes[i].id, target: nodes[j].id, weight: 1 });
        }
    }
    
    container.innerHTML = '';
    const width = container.clientWidth || 280;
    const height = 160;
    
    const svg = d3.select(container).append('svg').attr('width', width).attr('height', height).attr('class', 'mini-graph-svg');
    const g = svg.append('g');
    
    svg.call(d3.zoom().scaleExtent([0.5, 2]).on('zoom', (event) => g.attr('transform', event.transform)));
    
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(40))
        .force('charge', d3.forceManyBody().strength(-80))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.radius + 4));
    
    const link = g.append('g').selectAll('line').data(links).join('line')
        .attr('class', 'mini-graph-link').attr('stroke', 'rgba(255,255,255,0.2)').attr('stroke-width', 1);
    
    const node = g.append('g').selectAll('g').data(nodes).join('g').attr('class', 'mini-graph-node')
        .call(d3.drag()
            .on('start', (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
            .on('end', (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));
    
    node.append('circle').attr('r', d => d.radius)
        .attr('fill', d => ROLE_CATEGORY_COLORS[d.category] || ROLE_CATEGORY_COLORS.default)
        .attr('stroke', '#fff').attr('stroke-width', 1);
    
    node.append('title').text(d => `${d.name} (${d.count})`);
    
    simulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function filterByRole(roleName) {
    if (typeof setChartFilter === 'function') {
        setChartFilter('role', roleName);
    }
    if (typeof toast === 'function') {
        toast('info', `Filtered to role: ${roleName}`);
    }
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length <= maxLength ? text : text.substring(0, maxLength - 3) + '...';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function escapeHtmlAttr(text) {
    return escapeHtml(text).replace(/'/g, '&#39;').replace(/"/g, '&quot;');
}

// ============================================================
// INTEGRATION WITH EXISTING APP.JS
// ============================================================

/**
 * Override renderCharts to use enhanced versions
 */
function enhanceRenderCharts() {
    const originalRenderCharts = window.renderCharts;
    
    window.renderCharts = function(data) {
        // Call enhanced chart renderers
        renderEnhancedSeverityChart(data);
        renderEnhancedCategoryChart(data);
        
        // Render health gauge if score available
        if (data.score !== undefined) {
            renderHealthGauge(data.score);
        }
        
        // Render heatmap if issues available
        if (data.issues && data.issues.length > 0) {
            renderIssueHeatmap(data.issues);
        }
    };
}

/**
 * Override renderRolesSummary to use enhanced version
 */
function enhanceRenderRolesSummary() {
    const originalRenderRolesSummary = window.renderRolesSummary;
    
    window.renderRolesSummary = function() {
        if (typeof State !== 'undefined' && State.roles) {
            renderEnhancedRolesCard(State.roles);
        }
    };
}

/**
 * Hook into document upload to detect type and suggest preset
 */
function hookDocumentUpload() {
    const originalProcessDocument = window.processDocument;
    if (typeof originalProcessDocument !== 'function') return;
    
    window.processDocument = async function(...args) {
        const result = await originalProcessDocument.apply(this, args);
        
        // After document processed, try to detect type
        if (typeof State !== 'undefined' && State.reviewResults) {
            const text = State.reviewResults.document_info?.text_preview || '';
            const detectedType = detectDocumentType(text);
            if (detectedType) {
                setTimeout(() => showPresetSuggestion(detectedType), 500);
            }
        }
        
        return result;
    };
}

// ============================================================
// INITIALIZATION
// ============================================================

function initBatch5And6Features() {
    console.log('[TWR] Initializing Batch 5 & 6 features (v2.9.3)...');
    
    loadValidationMode();
    initValidationModeToggle();
    
    // Enhance existing functions if they exist
    if (typeof window.renderCharts === 'function') {
        enhanceRenderCharts();
    }
    
    if (typeof window.renderRolesSummary === 'function') {
        enhanceRenderRolesSummary();
    }
    
    hookDocumentUpload();
    
    // Add preset button listeners for new presets
    ['prop', 'pal', 'fgost'].forEach(presetKey => {
        const btn = document.getElementById(`btn-preset-${presetKey}`);
        if (btn) {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[id^="btn-preset-"]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                applyDocumentPreset(presetKey);
            });
        }
    });
    
    console.log('[TWR] Batch 5 & 6 features initialized');
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBatch5And6Features);
} else {
    initBatch5And6Features();
}

// Make functions globally available
window.DOCUMENT_PRESETS = DOCUMENT_PRESETS;
window.detectDocumentType = detectDocumentType;
window.showPresetSuggestion = showPresetSuggestion;
window.applyDocumentPreset = applyDocumentPreset;
window.setValidationMode = setValidationMode;
window.getValidationMode = getValidationMode;
window.renderEnhancedSeverityChart = renderEnhancedSeverityChart;
window.renderEnhancedCategoryChart = renderEnhancedCategoryChart;
window.renderHealthGauge = renderHealthGauge;
window.renderIssueHeatmap = renderIssueHeatmap;
window.renderEnhancedRolesCard = renderEnhancedRolesCard;
window.filterBySection = filterBySection;
window.filterByRole = filterByRole;
