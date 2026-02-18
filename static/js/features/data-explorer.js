/**
 * AEGIS Data Explorer - Cinematic Data Drill-Down Experience
 * ===========================================================
 * Version: 1.0.0
 *
 * A high-end, immersive data exploration system that allows users to
 * drill deep into any metric, understand aggregations, and navigate
 * through data relationships with beautiful visualizations.
 *
 * Features:
 * - Cinematic modal with layered navigation (breadcrumbs)
 * - Interactive visualizations (charts, treemaps, sankey diagrams)
 * - Smooth animations and transitions
 * - Deep drill-down with unlimited depth
 * - Forward/backward navigation with history
 * - Context preservation across drill levels
 * - Beautiful, polished UI with glassmorphism effects
 * - Responsive and accessible design
 */

'use strict';

window.TWR = window.TWR || {};

TWR.DataExplorer = (function() {
    const VERSION = '1.0.0';
    const LOG_PREFIX = '[DataExplorer]';

    // ============================================================
    // STATE MANAGEMENT
    // ============================================================

    const State = {
        isOpen: false,
        history: [],           // Navigation history stack
        currentLevel: 0,       // Current depth in drill-down
        currentData: null,     // Current view data
        animating: false,      // Animation lock
        charts: {},            // Active Chart.js instances
        modal: null,           // Modal DOM element
        listeners: [],         // Event listeners for cleanup
        isLightMode: false     // Theme mode detection
    };

    // ============================================================
    // THEME DETECTION & MANAGEMENT
    // ============================================================

    function detectThemeMode() {
        // Check for dark-mode class on body (common pattern)
        const hasDarkMode = document.body.classList.contains('dark-mode');
        const hasLightMode = document.body.classList.contains('light-mode');

        // If explicit class, use that
        if (hasLightMode) return true;  // light mode
        if (hasDarkMode) return false;  // dark mode

        // Check data attribute
        const dataTheme = document.body.dataset.theme || document.documentElement.dataset.theme;
        if (dataTheme === 'light') return true;
        if (dataTheme === 'dark') return false;

        // Check localStorage preference
        const stored = localStorage.getItem('theme') || localStorage.getItem('twr-theme');
        if (stored === 'light') return true;
        if (stored === 'dark') return false;

        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return true;
        }

        // Default to dark mode (original design)
        return false;
    }

    function applyThemeToModal() {
        State.isLightMode = detectThemeMode();

        if (State.modal) {
            if (State.isLightMode) {
                State.modal.classList.add('de-light-mode');
            } else {
                State.modal.classList.remove('de-light-mode');
            }
        }

        log(`Theme mode: ${State.isLightMode ? 'light' : 'dark'}`);
    }

    function getChartColors() {
        const isLight = State.isLightMode;
        return {
            text: isLight ? '#475569' : 'rgba(255, 255, 255, 0.8)',
            textMuted: isLight ? '#94a3b8' : 'rgba(255, 255, 255, 0.5)',
            grid: isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.1)',
            tooltipBg: isLight ? 'rgba(255, 255, 255, 0.98)' : 'rgba(0, 0, 0, 0.85)',
            tooltipText: isLight ? '#1e293b' : '#ffffff',
            border: isLight ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.1)'
        };
    }

    // ============================================================
    // CONSTANTS & CONFIGURATION
    // ============================================================

    const CONFIG = {
        animationDuration: 400,
        maxHistoryDepth: 20,
        chartColors: {
            primary: ['#4A90D9', '#50C878', '#FFB347', '#FF6B6B', '#9B59B6', '#1ABC9C', '#E74C3C', '#3498DB'],
            gradient: {
                blue: ['rgba(74, 144, 217, 0.8)', 'rgba(74, 144, 217, 0.2)'],
                green: ['rgba(80, 200, 120, 0.8)', 'rgba(80, 200, 120, 0.2)'],
                orange: ['rgba(255, 179, 71, 0.8)', 'rgba(255, 179, 71, 0.2)'],
                red: ['rgba(255, 107, 107, 0.8)', 'rgba(255, 107, 107, 0.2)']
            }
        },
        icons: {
            role: '👤',
            document: '📄',
            responsibility: '✓',
            mention: '💬',
            category: '📁',
            action: '⚡',
            chart: '📊',
            back: '←',
            forward: '→',
            close: '✕',
            expand: '🔍',
            collapse: '📌',
            interaction: '🔗',
            connection: '🤝'
        }
    };

    // ============================================================
    // UTILITY FUNCTIONS
    // ============================================================

    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    function truncate(str, len = 50) {
        if (!str || str.length <= len) return str;
        return str.substring(0, len - 3) + '...';
    }

    function getCSRFToken() {
        if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
        if (window.State?.csrfToken) return window.State.csrfToken;
        if (window.TWR?.State?.csrfToken) return window.TWR.State.csrfToken;
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.content : '';
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function log(message, level = 'info') {
        console[level](`${LOG_PREFIX} ${message}`);
    }

    // ============================================================
    // ANIMATION HELPERS
    // ============================================================

    function animateIn(element, direction = 'right') {
        return new Promise(resolve => {
            element.style.opacity = '0';
            element.style.transform = direction === 'right'
                ? 'translateX(30px)'
                : 'translateX(-30px)';

            requestAnimationFrame(() => {
                element.style.transition = `all ${CONFIG.animationDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
                element.style.opacity = '1';
                element.style.transform = 'translateX(0)';

                setTimeout(resolve, CONFIG.animationDuration);
            });
        });
    }

    function animateOut(element, direction = 'left') {
        return new Promise(resolve => {
            element.style.transition = `all ${CONFIG.animationDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
            element.style.opacity = '0';
            element.style.transform = direction === 'left'
                ? 'translateX(-30px)'
                : 'translateX(30px)';

            setTimeout(resolve, CONFIG.animationDuration);
        });
    }

    function pulseElement(element) {
        element.classList.add('de-pulse');
        setTimeout(() => element.classList.remove('de-pulse'), 600);
    }

    // ============================================================
    // CHART MANAGEMENT
    // ============================================================

    function destroyCharts() {
        Object.values(State.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        State.charts = {};
    }

    function createDonutChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return null;

        const ctx = canvas.getContext('2d');
        const colors = getChartColors();

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: options.colors || CONFIG.chartColors.primary.slice(0, data.values.length),
                    borderWidth: 2,
                    borderColor: colors.border,
                    hoverBorderColor: State.isLightMode ? 'rgba(0, 0, 0, 0.3)' : 'rgba(255, 255, 255, 0.5)',
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        display: options.showLegend !== false,
                        position: 'right',
                        labels: {
                            color: colors.text,
                            padding: 15,
                            font: { size: 12 },
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: colors.tooltipBg,
                        titleColor: colors.tooltipText,
                        bodyColor: colors.tooltipText,
                        padding: 12,
                        cornerRadius: 8,
                        borderColor: colors.border,
                        borderWidth: State.isLightMode ? 1 : 0,
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.raw / total) * 100).toFixed(1);
                                return `${context.label}: ${context.raw} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 800,
                    easing: 'easeOutQuart',
                    onComplete: () => centerDonutText(chart)
                },
                onClick: options.onClick || null
            }
        });

        State.charts[canvasId] = chart;

        // Center the overlay text on the actual doughnut area (not the full canvas which includes legend)
        // Run immediately and again after animation completes (via onComplete above)
        centerDonutText(chart);

        return chart;
    }

    /**
     * Adjust .de-chart-center-text position to align with the actual doughnut drawing area.
     * The Chart.js legend (position: 'right') shifts the doughnut left, but the CSS overlay
     * is centered on the full container. This recalculates based on chartArea.
     */
    function centerDonutText(chart) {
        if (!chart || !chart.canvas) return;
        const container = chart.canvas.closest('.de-chart-container');
        if (!container) return;
        const centerText = container.querySelector('.de-chart-center-text');
        if (!centerText) return;

        // Use setTimeout to ensure Chart.js has completed its layout pass
        setTimeout(() => {
            const area = chart.chartArea;
            if (!area || !chart.canvas) return;
            const canvasW = chart.canvas.getBoundingClientRect().width;
            const canvasH = chart.canvas.getBoundingClientRect().height;
            if (!canvasW || !canvasH) return;

            // Calculate the center of the doughnut as a percentage of the container
            const centerXPct = ((area.left + area.right) / 2 / canvasW * 100);
            const centerYPct = ((area.top + area.bottom) / 2 / canvasH * 100);

            centerText.style.left = centerXPct.toFixed(1) + '%';
            centerText.style.top = centerYPct.toFixed(1) + '%';
        }, 50);
    }

    function createBarChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') return null;

        const ctx = canvas.getContext('2d');
        const colors = getChartColors();

        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, CONFIG.chartColors.gradient.blue[0]);
        gradient.addColorStop(1, CONFIG.chartColors.gradient.blue[1]);

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: data.label || 'Count',
                    data: data.values,
                    backgroundColor: gradient,
                    borderColor: 'rgba(74, 144, 217, 1)',
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: options.horizontal ? 'y' : 'x',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: colors.tooltipBg,
                        titleColor: colors.tooltipText,
                        bodyColor: colors.tooltipText,
                        padding: 12,
                        cornerRadius: 8,
                        borderColor: colors.border,
                        borderWidth: State.isLightMode ? 1 : 0
                    }
                },
                scales: {
                    x: {
                        grid: { color: colors.grid },
                        ticks: {
                            color: colors.text,
                            maxRotation: 45,
                            minRotation: 0
                        }
                    },
                    y: {
                        grid: { color: colors.grid },
                        ticks: { color: colors.text },
                        beginAtZero: true
                    }
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutQuart'
                },
                onClick: options.onClick || null
            }
        });

        State.charts[canvasId] = chart;
        return chart;
    }

    function createTreemap(containerId, data) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Simple CSS-based treemap (D3 not required)
        const total = data.reduce((sum, d) => sum + d.value, 0);

        // Store item data for click handlers
        const itemDataMap = {};

        let html = '<div class="de-treemap">';
        data.forEach((item, i) => {
            const pct = (item.value / total) * 100;
            const color = CONFIG.chartColors.primary[i % CONFIG.chartColors.primary.length];
            // Store role data for later retrieval
            itemDataMap[item.id] = item.roleData || null;
            html += `
                <div class="de-treemap-cell"
                     style="flex-basis: ${Math.max(pct, 8)}%; background: ${color};"
                     data-id="${escapeHtml(item.id)}"
                     data-type="${escapeHtml(item.type)}"
                     title="${escapeHtml(item.label)}: ${item.value}">
                    <div class="de-treemap-label">${escapeHtml(truncate(item.label, 20))}</div>
                    <div class="de-treemap-value">${formatNumber(item.value)}</div>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;

        // Add click handlers with access to role data
        container.querySelectorAll('.de-treemap-cell').forEach(cell => {
            cell.addEventListener('click', () => {
                const id = cell.dataset.id;
                const type = cell.dataset.type;
                const roleData = itemDataMap[id];
                drillInto(type, id, roleData);
            });
        });
    }

    // ============================================================
    // DATA FETCHING & PROCESSING
    // ============================================================

    async function fetchRolesData() {
        try {
            // Strategy 1: Try aggregated API endpoint
            let response = await fetch('/api/roles/aggregated?include_deliverables=false');
            let result = await response.json();

            // Handle array format from API (most common)
            if (result.data && Array.isArray(result.data) && result.data.length > 0) {
                const rolesObj = {};
                result.data.forEach(role => {
                    const name = role.role_name || role.normalized_name || role.name;
                    if (name) {
                        rolesObj[name] = {
                            canonical_name: role.role_name || name,
                            normalized_name: role.normalized_name || name.toLowerCase(),
                            frequency: role.total_mentions || role.document_count || 1,
                            count: role.total_mentions || role.document_count || 1,
                            category: role.category || getCategoryForRole(name),
                            responsibilities: [],
                            responsibility_count: role.responsibility_count || 0,
                            action_types: {},
                            source_documents: role.documents || [],
                            document_count: role.document_count || role.unique_document_count || 0
                        };
                    }
                });
                if (Object.keys(rolesObj).length > 0) {
                    log(`Fetched ${Object.keys(rolesObj).length} roles from aggregated API (array format)`);

                    // Also fetch RACI data to get action type breakdown (R/A/C/I counts)
                    try {
                        const raciResponse = await fetch('/api/roles/raci');
                        const raciResult = await raciResponse.json();
                        if (raciResult.success && raciResult.data?.roles) {
                            Object.entries(raciResult.data.roles).forEach(([raciName, raciData]) => {
                                // Try to match with existing role (case-insensitive)
                                const matchingKey = Object.keys(rolesObj).find(
                                    k => k.toLowerCase() === raciName.toLowerCase() ||
                                         rolesObj[k].normalized_name === raciName.toLowerCase()
                                );
                                if (matchingKey) {
                                    // Add R/A/C/I data directly to the role
                                    rolesObj[matchingKey].R = raciData.R || 0;
                                    rolesObj[matchingKey].A = raciData.A || 0;
                                    rolesObj[matchingKey].C = raciData.C || 0;
                                    rolesObj[matchingKey].I = raciData.I || 0;
                                    rolesObj[matchingKey].primary_type = raciData.primary_type || '';
                                }
                            });
                            log(`Merged RACI data for action types`);
                        }
                    } catch (raciErr) {
                        log(`Could not fetch RACI data: ${raciErr.message}`);
                    }

                    return rolesObj;
                }
            }

            // Handle object format (fallback)
            if (result.success && result.data && typeof result.data === 'object' && !Array.isArray(result.data) && Object.keys(result.data).length > 0) {
                log(`Fetched ${Object.keys(result.data).length} roles from aggregated API (object format)`);
                return result.data;
            }

            // Strategy 2: Try the RACI endpoint (has rich role data)
            response = await fetch('/api/roles/raci');
            if (!response.ok) throw new Error(`RACI fetch failed: ${response.status}`);
            result = await response.json();

            if (result.success && result.data?.roles) {
                const raciRoles = {};
                Object.entries(result.data.roles).forEach(([name, roleData]) => {
                    raciRoles[name] = {
                        canonical_name: name,
                        frequency: roleData.total_count || roleData.mentions || 1,
                        count: roleData.total_count || roleData.mentions || 1,
                        category: roleData.category || getCategoryForRole(name),
                        responsibilities: roleData.responsibilities || [],
                        action_types: roleData.action_types || roleData.raci_breakdown || {},
                        source_documents: roleData.documents || []
                    };
                });
                if (Object.keys(raciRoles).length > 0) {
                    log(`Fetched ${Object.keys(raciRoles).length} roles from RACI API`);
                    return raciRoles;
                }
            }

            // Strategy 3: Fallback to current session state
            const twrState = window.TWR?.State || {};
            const sessionRoles = twrState.roles?.roles || twrState.roles || twrState.extractedRoles || {};

            if (Object.keys(sessionRoles).length > 0) {
                log(`Using ${Object.keys(sessionRoles).length} roles from session state`);
                return sessionRoles;
            }

            // Strategy 4: Try the scan history for recent document roles
            response = await fetch('/api/scan-history?limit=10');
            result = await response.json();

            if (result.success && result.data?.length > 0) {
                const historyRoles = {};
                result.data.forEach(doc => {
                    if (doc.roles_found && typeof doc.roles_found === 'object') {
                        Object.entries(doc.roles_found).forEach(([name, data]) => {
                            if (!historyRoles[name]) {
                                historyRoles[name] = {
                                    canonical_name: name,
                                    frequency: 0,
                                    responsibilities: [],
                                    action_types: {},
                                    source_documents: []
                                };
                            }
                            historyRoles[name].frequency += data.count || data.frequency || 1;
                            historyRoles[name].source_documents.push(doc.filename);
                            if (data.responsibilities) {
                                historyRoles[name].responsibilities.push(...data.responsibilities);
                            }
                        });
                    }
                });
                if (Object.keys(historyRoles).length > 0) {
                    log(`Fetched ${Object.keys(historyRoles).length} roles from scan history`);
                    return historyRoles;
                }
            }

            log('No roles data found from any source', 'warn');
            return {};
        } catch (e) {
            log('Failed to fetch roles data: ' + e, 'error');
            return {};
        }
    }

    async function fetchDocumentData() {
        try {
            const response = await fetch('/api/scan-history?limit=100');
            const result = await response.json();
            return result.success ? result.data : [];
        } catch (e) {
            log('Failed to fetch document data: ' + e, 'error');
            return [];
        }
    }

    async function fetchRoleContext(roleName) {
        try {
            // Try the context API endpoint - returns detailed occurrences
            let response = await fetch(`/api/roles/context?role=${encodeURIComponent(roleName)}`);
            if (!response.ok) throw new Error(`Role context fetch failed: ${response.status}`);
            let result = await response.json();

            if (result.success) {
                // The API spreads context directly into response
                // Extract responsibilities from occurrences
                // IMPORTANT: Only include items with actual responsibility text (not placeholder entries)
                const occurrences = result.occurrences || [];
                const responsibilities = occurrences
                    .filter(o => o.responsibility && o.responsibility.trim())  // Must have actual responsibility text
                    .map(o => ({
                        text: o.responsibility || '',
                        action_type: o.action_type || '',
                        document: o.document || '',
                        section: o.section || '',
                        confidence: o.confidence || 0,
                        statement_index: o.statement_index ?? -1,
                        review_status: o.review_status || '',
                        notes: o.notes || ''
                    }));

                return {
                    role_name: result.role_name,
                    category: result.category,
                    documents: result.documents || [],
                    occurrences: occurrences,
                    responsibilities: responsibilities,
                    responsibility_count: responsibilities.length,
                    total_mentions: result.total_mentions || 0,
                    document_count: result.document_count || 0
                };
            }

            // Fallback: Try to get from RACI data
            response = await fetch('/api/roles/raci');
            result = await response.json();

            if (result.success && result.data?.roles?.[roleName]) {
                const roleData = result.data.roles[roleName];
                return {
                    responsibilities: roleData.responsibilities || [],
                    action_types: roleData.action_types || roleData.raci_breakdown || {},
                    documents: roleData.documents || [],
                    sample_contexts: roleData.contexts || roleData.sample_texts || []
                };
            }

            return null;
        } catch (e) {
            log('Failed to fetch role context: ' + e, 'error');
            return null;
        }
    }

    async function fetchRaciData() {
        try {
            const response = await fetch('/api/roles/raci');
            const result = await response.json();
            return result.success ? result.data : null;
        } catch (e) {
            log('Failed to fetch RACI data: ' + e, 'error');
            return null;
        }
    }

    async function fetchRoleGraphData() {
        try {
            const response = await fetch('/api/roles/graph?max_nodes=200');
            const result = await response.json();
            return result.success ? result.data : null;
        } catch (e) {
            log('Failed to fetch role graph data: ' + e, 'error');
            return null;
        }
    }

    async function fetchRoleMatrixData() {
        try {
            const response = await fetch('/api/roles/matrix');
            const result = await response.json();
            return result.success ? result.data : null;
        } catch (e) {
            log('Failed to fetch role matrix data: ' + e, 'error');
            return null;
        }
    }

    function processRolesForOverview(rolesData) {
        // Handle empty or invalid data
        if (!rolesData || typeof rolesData !== 'object') {
            log('No valid roles data to process', 'warn');
            return createEmptyOverview();
        }

        const roles = Object.entries(rolesData);

        if (roles.length === 0) {
            log('Roles data is empty', 'warn');
            return createEmptyOverview();
        }

        // Calculate aggregations with robust field access
        const totalRoles = roles.length;

        // Count total mentions (frequency of role appearances)
        const totalMentions = roles.reduce((sum, [, data]) => {
            return sum + getFrequency(data);
        }, 0);

        // Count total responsibilities (actual extracted statements)
        const totalResponsibilities = roles.reduce((sum, [, data]) => {
            // Use responsibility_count if available, otherwise count from array
            const respCount = data.responsibility_count || (data.responsibilities || []).length || 0;
            return sum + respCount;
        }, 0);

        // Collect all unique documents across all roles
        const allDocuments = new Set();
        roles.forEach(([, data]) => {
            const docs = data.source_documents || data.documents || [];
            docs.forEach(doc => {
                if (doc) allDocuments.add(typeof doc === 'string' ? doc : doc.filename || doc.name || doc);
            });
        });
        const uniqueDocumentCount = allDocuments.size;

        // Category breakdown
        const categoryBreakdown = {};
        roles.forEach(([name, data]) => {
            const category = data.category || getCategoryForRole(name);
            if (!categoryBreakdown[category]) {
                categoryBreakdown[category] = { count: 0, mentions: 0, roles: [] };
            }
            categoryBreakdown[category].count++;
            categoryBreakdown[category].mentions += getFrequency(data);
            categoryBreakdown[category].roles.push({ name, ...normalizeRoleData(name, data) });
        });

        // Action type breakdown - check multiple possible field names
        const actionBreakdown = {};
        roles.forEach(([name, data]) => {
            // First check for named action objects
            let actions = data.action_types || data.raci_breakdown || data.actions || {};

            // Also check for direct R/A/C/I properties (RACI matrix format)
            if (Object.keys(actions).length === 0) {
                const raciKeys = ['R', 'A', 'C', 'I'];
                const hasRaciData = raciKeys.some(key => typeof data[key] === 'number' && data[key] > 0);
                if (hasRaciData) {
                    actions = {};
                    raciKeys.forEach(key => {
                        if (typeof data[key] === 'number' && data[key] > 0) {
                            actions[key] = data[key];
                        }
                    });
                }
            }

            if (actions && typeof actions === 'object') {
                Object.entries(actions).forEach(([action, count]) => {
                    const actionCount = typeof count === 'number' ? count : (count?.count || 1);
                    if (!actionBreakdown[action]) {
                        actionBreakdown[action] = { count: 0, roles: [] };
                    }
                    actionBreakdown[action].count += actionCount;
                    actionBreakdown[action].roles.push({ name, count: actionCount });
                });
            }
        });

        // If no action types found, try to derive from responsibilities
        if (Object.keys(actionBreakdown).length === 0) {
            roles.forEach(([name, data]) => {
                const responsibilities = getResponsibilities(data);
                responsibilities.forEach(resp => {
                    const action = deriveActionFromText(resp);
                    if (action) {
                        if (!actionBreakdown[action]) {
                            actionBreakdown[action] = { count: 0, roles: [] };
                        }
                        actionBreakdown[action].count++;
                        actionBreakdown[action].roles.push({ name, count: 1 });
                    }
                });
            });
        }

        // Top roles
        const topRoles = roles
            .map(([name, data]) => ({
                name: data.canonical_name || data.name || name,
                frequency: getFrequency(data),
                responsibilities: getResponsibilities(data).length,
                category: data.category || getCategoryForRole(name),
                data: normalizeRoleData(name, data)
            }))
            .sort((a, b) => b.frequency - a.frequency)
            .slice(0, 15);

        return {
            totalRoles,
            totalMentions,
            totalResponsibilities,
            uniqueDocumentCount,
            avgMentionsPerRole: totalRoles > 0 ? (totalMentions / totalRoles).toFixed(1) : 0,
            avgResponsibilitiesPerRole: totalRoles > 0 ? (totalResponsibilities / totalRoles).toFixed(1) : 0,
            categoryBreakdown,
            actionBreakdown,
            topRoles,
            allRoles: roles.map(([name, data]) => [name, normalizeRoleData(name, data)])
        };
    }

    function createEmptyOverview() {
        return {
            totalRoles: 0,
            totalMentions: 0,
            totalResponsibilities: 0,
            uniqueDocumentCount: 0,
            avgMentionsPerRole: 0,
            avgResponsibilitiesPerRole: 0,
            categoryBreakdown: {},
            actionBreakdown: {},
            topRoles: [],
            allRoles: []
        };
    }

    function getFrequency(data) {
        if (!data || typeof data !== 'object') return 1;
        return data.frequency || data.count || data.occurrence_count ||
               data.mentions || data.total_count || 1;
    }

    function getResponsibilities(data) {
        if (!data) return [];
        // If we have a responsibility_count, create a placeholder array of that length
        if (data.responsibility_count && data.responsibility_count > 0) {
            return new Array(data.responsibility_count).fill('');
        }
        const resp = data.responsibilities || data.statements || data.contexts || [];
        return Array.isArray(resp) ? resp : [];
    }

    function normalizeRoleData(name, data) {
        if (!data || typeof data !== 'object') {
            return {
                canonical_name: name,
                frequency: 1,
                count: 1,
                category: getCategoryForRole(name),
                responsibilities: [],
                responsibility_count: 0,
                action_types: {},
                source_documents: [],
                document_count: 0
            };
        }

        const respCount = data.responsibility_count || (data.responsibilities || []).length || 0;

        // Build action_types from various possible sources
        let actionTypes = data.action_types || data.raci_breakdown || data.actions || {};

        // Also check for direct R/A/C/I properties (RACI matrix format)
        if (Object.keys(actionTypes).length === 0) {
            const raciKeys = ['R', 'A', 'C', 'I'];
            raciKeys.forEach(key => {
                if (typeof data[key] === 'number' && data[key] > 0) {
                    actionTypes[key] = data[key];
                }
            });
        }

        return {
            canonical_name: data.canonical_name || data.role_name || data.name || name,
            frequency: getFrequency(data),
            count: getFrequency(data),
            category: data.category || getCategoryForRole(name),
            responsibilities: getResponsibilities(data),
            responsibility_count: respCount,
            action_types: actionTypes,
            // Also preserve the raw R/A/C/I values for drill-down views
            R: data.R || 0,
            A: data.A || 0,
            C: data.C || 0,
            I: data.I || 0,
            primary_type: data.primary_type || '',
            source_documents: data.source_documents || data.documents || [],
            document_count: data.document_count || data.unique_document_count || (data.source_documents || data.documents || []).length || 0
        };
    }

    function deriveActionFromText(text) {
        if (!text || typeof text !== 'string') return null;
        const lower = text.toLowerCase();

        if (lower.includes('responsible') || lower.includes('perform') || lower.includes('execute')) {
            return 'Responsible';
        }
        if (lower.includes('accountable') || lower.includes('approve') || lower.includes('sign off')) {
            return 'Accountable';
        }
        if (lower.includes('consult') || lower.includes('advise') || lower.includes('review')) {
            return 'Consulted';
        }
        if (lower.includes('inform') || lower.includes('notify') || lower.includes('update')) {
            return 'Informed';
        }
        if (lower.includes('manage') || lower.includes('lead') || lower.includes('oversee')) {
            return 'Manages';
        }
        if (lower.includes('support') || lower.includes('assist') || lower.includes('help')) {
            return 'Supports';
        }

        return null;
    }

    function getCategoryForRole(roleName) {
        const name = roleName.toLowerCase();
        if (name.includes('manager') || name.includes('lead') || name.includes('director')) {
            return 'Management';
        }
        if (name.includes('engineer') || name.includes('analyst') || name.includes('specialist')) {
            return 'Technical';
        }
        if (name.includes('board') || name.includes('committee') || name.includes('panel')) {
            return 'Governance';
        }
        if (name.includes('team') || name.includes('group')) {
            return 'Teams';
        }
        return 'Other';
    }

    // ============================================================
    // VIEW RENDERERS
    // ============================================================

    async function renderOverviewLevel(data) {
        const content = State.modal.querySelector('.de-content');

        // v4.0.3: Load adjudication data
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        // Handle empty data case
        if (!data || data.totalRoles === 0) {
            content.innerHTML = `
                <div class="de-empty-state">
                    <div class="de-empty-icon">📊</div>
                    <h2>No Role Data Available</h2>
                    <p>No roles have been extracted yet. Please scan a document first to see data exploration.</p>
                    <div class="de-empty-actions">
                        <button class="de-action-btn de-primary" onclick="TWR.DataExplorer.close();">
                            Close and Scan Document
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        const categoryCount = Object.keys(data.categoryBreakdown).length;
        const actionCount = Object.keys(data.actionBreakdown).length;
        const hasCategories = categoryCount > 0;
        const hasActions = actionCount > 0;
        const hasTopRoles = data.topRoles && data.topRoles.length > 0;

        content.innerHTML = `
            <div class="de-overview">
                <!-- Hero Stats -->
                <div class="de-hero-stats">
                    <div class="de-hero-stat de-clickable" data-drill="roles-list" data-metric="total-roles">
                        <div class="de-hero-icon">${CONFIG.icons.role}</div>
                        <div class="de-hero-value">${formatNumber(data.totalRoles)}</div>
                        <div class="de-hero-label">Unique Roles</div>
                        ${(() => {
                            const as = adjLookup ? adjLookup.getStats() : { total: 0 };
                            const ac = as.confirmed + (as.deliverable || 0);
                            if (ac > 0) {
                                const parts = [`${ac} adjudicated`];
                                if (as.deliverable > 0) parts.push(`${as.deliverable} deliverable`);
                                return `<div class="de-hero-hint" style="color:#22c55e;opacity:1;transform:none;">✓ ${parts.join(' · ')}</div>`;
                            }
                            return `<div class="de-hero-hint">Click to explore all roles</div>`;
                        })()}
                    </div>
                    <div class="de-hero-stat de-clickable" data-drill="mentions-breakdown" data-metric="total-responsibilities">
                        <div class="de-hero-icon">${CONFIG.icons.mention}</div>
                        <div class="de-hero-value">${formatNumber(data.totalResponsibilities)}</div>
                        <div class="de-hero-label">Responsibility Statements</div>
                        <div class="de-hero-hint">Click to see breakdown</div>
                    </div>
                    <div class="de-hero-stat de-clickable" data-drill="documents" data-metric="documents">
                        <div class="de-hero-icon">📄</div>
                        <div class="de-hero-value">${formatNumber(data.uniqueDocumentCount || data.document_count || data.source_documents?.length || 0)}</div>
                        <div class="de-hero-label">Documents</div>
                        <div class="de-hero-hint">View analyzed documents</div>
                    </div>
                    <div class="de-hero-stat de-clickable" data-drill="interactions" data-metric="interactions">
                        <div class="de-hero-icon">🔗</div>
                        <div class="de-hero-value">${formatNumber(data.totalRoles || 0)}</div>
                        <div class="de-hero-label">Role Interactions</div>
                        <div class="de-hero-hint">Explore role relationships</div>
                    </div>
                </div>

                <!-- Main Visualization Grid -->
                <div class="de-viz-grid">
                    <!-- Category Breakdown -->
                    <div class="de-viz-card de-viz-large">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.category} Role Categories</h3>
                            <span class="de-viz-subtitle">${hasCategories ? 'Click any segment to explore' : 'No categories detected'}</span>
                        </div>
                        <div class="de-viz-body">
                            ${hasCategories ? `
                                <div class="de-chart-container">
                                    <canvas id="de-category-chart" height="250"></canvas>
                                    <div class="de-chart-center-text">
                                        <div class="de-chart-center-value">${Object.keys(data.categoryBreakdown).length}</div>
                                        <div class="de-chart-center-label">Categories</div>
                                    </div>
                                </div>
                            ` : `
                                <div class="de-empty-viz">
                                    <span class="de-empty-viz-icon">📁</span>
                                    <span>Category data will appear after document analysis</span>
                                </div>
                            `}
                            <div class="de-category-legend" id="de-category-legend"></div>
                        </div>
                    </div>

                    <!-- Top Roles -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.role} Top Roles by Frequency</h3>
                            <span class="de-viz-subtitle">${hasTopRoles ? 'Most mentioned roles' : 'No roles detected'}</span>
                        </div>
                        <div class="de-viz-body de-scrollable">
                            ${hasTopRoles ? `
                                <div class="de-top-roles-list" id="de-top-roles"></div>
                            ` : `
                                <div class="de-empty-viz">
                                    <span class="de-empty-viz-icon">👤</span>
                                    <span>Role frequency data will appear after analysis</span>
                                </div>
                            `}
                        </div>
                    </div>

                    <!-- Action Distribution -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.action} Action Types</h3>
                            <span class="de-viz-subtitle">${hasActions ? 'How roles are assigned work' : 'No action types detected'}</span>
                        </div>
                        <div class="de-viz-body">
                            ${hasActions ? `
                                <div class="de-chart-container">
                                    <canvas id="de-action-chart" height="200"></canvas>
                                </div>
                            ` : `
                                <div class="de-empty-viz">
                                    <span class="de-empty-viz-icon">⚡</span>
                                    <span>Action types (R/A/C/I) will appear after RACI analysis</span>
                                </div>
                            `}
                        </div>
                    </div>

                    <!-- Treemap Visualization -->
                    <div class="de-viz-card de-viz-wide">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.expand} Role Distribution Map</h3>
                            <span class="de-viz-subtitle">${hasTopRoles ? 'Proportional view of all roles' : 'Treemap will appear with data'}</span>
                        </div>
                        <div class="de-viz-body">
                            ${hasTopRoles ? `
                                <div id="de-treemap-container"></div>
                            ` : `
                                <div class="de-empty-viz">
                                    <span class="de-empty-viz-icon">🗺️</span>
                                    <span>Role distribution map will appear after analysis</span>
                                </div>
                            `}
                        </div>
                    </div>
                </div>

                <!-- Quick Stats Footer -->
                <div class="de-quick-stats">
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Categories:</span>
                        <span class="de-quick-value">${Object.keys(data.categoryBreakdown).length}</span>
                    </div>
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Action Types:</span>
                        <span class="de-quick-value">${Object.keys(data.actionBreakdown).length}</span>
                    </div>
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Largest Category:</span>
                        <span class="de-quick-value">${Object.entries(data.categoryBreakdown)
                            .sort((a, b) => b[1].count - a[1].count)[0]?.[0] || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;

        // Render charts after DOM update
        setTimeout(() => {
            renderCategoryChart(data);
            renderTopRolesList(data.topRoles);
            renderActionChart(data);
            renderTreemap(data);
            attachOverviewListeners(data);
        }, 50);
    }

    function renderCategoryChart(data) {
        const categories = Object.entries(data.categoryBreakdown || {});

        // Skip if no categories
        if (categories.length === 0) {
            log('No categories to render chart');
            return;
        }

        createDonutChart('de-category-chart', {
            labels: categories.map(([name]) => name),
            values: categories.map(([, data]) => data.count)
        }, {
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const category = categories[index][0];
                    drillInto('category', category, data.categoryBreakdown[category]);
                }
            }
        });

        // Render custom legend
        const legendContainer = document.getElementById('de-category-legend');
        if (legendContainer) {
            legendContainer.innerHTML = categories.map(([name, catData], i) => `
                <div class="de-legend-item de-clickable" data-category="${escapeHtml(name)}">
                    <span class="de-legend-color" style="background: ${CONFIG.chartColors.primary[i]}"></span>
                    <span class="de-legend-name">${escapeHtml(name)}</span>
                    <span class="de-legend-count">${catData.count} roles</span>
                    <span class="de-legend-mentions">${formatNumber(catData.mentions)} mentions</span>
                </div>
            `).join('');

            legendContainer.querySelectorAll('.de-legend-item').forEach(item => {
                item.addEventListener('click', () => {
                    const category = item.dataset.category;
                    drillInto('category', category, data.categoryBreakdown[category]);
                });
            });
        }
    }

    function renderTopRolesList(topRoles) {
        const container = document.getElementById('de-top-roles');
        if (!container) return;

        // Handle empty list
        if (!topRoles || topRoles.length === 0) {
            container.innerHTML = '<div class="de-empty-viz"><span>No roles to display</span></div>';
            return;
        }

        // v4.0.3: Adjudication badges
        const adjLookup = window.AEGIS?.AdjudicationLookup;

        container.innerHTML = topRoles.map((role, i) => `
            <div class="de-role-item de-clickable" data-role="${escapeHtml(role.name)}">
                <div class="de-role-rank">${i + 1}</div>
                <div class="de-role-info">
                    <div class="de-role-name">${escapeHtml(role.name)}${adjLookup ? adjLookup.getBadge(role.name, { compact: true, size: 'sm' }) : ''}</div>
                    <div class="de-role-meta">
                        <span class="de-role-category">${escapeHtml(role.category)}</span>
                        <span class="de-role-resp">${role.responsibilities} responsibilities</span>
                    </div>
                </div>
                <div class="de-role-freq">
                    <div class="de-role-freq-value">${formatNumber(role.frequency)}</div>
                    <div class="de-role-freq-label">mentions</div>
                </div>
                <div class="de-role-arrow">${CONFIG.icons.forward}</div>
            </div>
        `).join('');

        container.querySelectorAll('.de-role-item').forEach(item => {
            item.addEventListener('click', () => {
                const roleName = item.dataset.role;
                const roleEntry = topRoles.find(r => r.name === roleName);
                // Merge the nested 'data' properties into roleData for drill-down
                const roleData = roleEntry ? { ...roleEntry, ...(roleEntry.data || {}) } : roleEntry;
                drillInto('role', roleName, roleData);
            });
        });
    }

    function renderActionChart(data) {
        const actions = Object.entries(data.actionBreakdown || {})
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 8);

        // Skip if no actions
        if (actions.length === 0) {
            log('No action types to render chart');
            return;
        }

        createBarChart('de-action-chart', {
            labels: actions.map(([name]) => name),
            values: actions.map(([, data]) => data.count),
            label: 'Occurrences'
        }, {
            horizontal: true,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const action = actions[index][0];
                    drillInto('action', action, data.actionBreakdown[action]);
                }
            }
        });
    }

    function renderTreemap(data) {
        const container = document.getElementById('de-treemap-container');
        if (!container) return;

        // Handle empty data
        if (!data.topRoles || data.topRoles.length === 0) {
            log('No roles for treemap');
            return;
        }

        const treemapData = data.topRoles.slice(0, 12).map(role => ({
            id: role.name,
            label: role.name,
            value: role.frequency,
            type: 'role',
            // Include full role data for drill-down (with nested data merged)
            roleData: { ...role, ...(role.data || {}) }
        }));

        createTreemap('de-treemap-container', treemapData);
    }

    function attachOverviewListeners(data) {
        // Hero stat clicks
        State.modal.querySelectorAll('.de-hero-stat.de-clickable').forEach(stat => {
            stat.addEventListener('click', () => {
                const drill = stat.dataset.drill;
                if (drill === 'roles-list') {
                    drillInto('roles-list', 'all', { allRoles: data.allRoles });
                } else if (drill === 'mentions-breakdown') {
                    drillInto('mentions-breakdown', 'all', data);
                } else if (drill === 'documents') {
                    drillInto('documents', 'all', data);
                } else if (drill === 'interactions') {
                    drillInto('interactions', 'all', data);
                }
            });
        });
    }

    // ============================================================
    // DRILL-DOWN VIEWS
    // ============================================================

    async function renderCategoryDrill(category, categoryData) {
        const content = State.modal.querySelector('.de-content');

        // v4.0.3: Adjudication lookup
        const adjLookup = window.AEGIS?.AdjudicationLookup;

        content.innerHTML = `
            <div class="de-drill-view">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.category}</div>
                    <div class="de-drill-title">
                        <h2>${escapeHtml(category)}</h2>
                        <p>${categoryData.count} roles with ${formatNumber(categoryData.mentions)} total mentions</p>
                    </div>
                </div>

                <div class="de-drill-stats">
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${categoryData.count}</div>
                        <div class="de-mini-label">Roles</div>
                    </div>
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${formatNumber(categoryData.mentions)}</div>
                        <div class="de-mini-label">Mentions</div>
                    </div>
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${(categoryData.mentions / categoryData.count).toFixed(1)}</div>
                        <div class="de-mini-label">Avg/Role</div>
                    </div>
                </div>

                <div class="de-viz-grid de-drill-grid">
                    <div class="de-viz-card de-viz-full">
                        <div class="de-viz-header">
                            <h3>Roles in ${escapeHtml(category)}</h3>
                        </div>
                        <div class="de-viz-body">
                            <canvas id="de-category-roles-chart" height="300"></canvas>
                        </div>
                    </div>

                    <div class="de-viz-card de-viz-full">
                        <div class="de-viz-header">
                            <h3>All Roles</h3>
                        </div>
                        <div class="de-viz-body de-scrollable de-role-grid">
                            ${categoryData.roles.map(role => `
                                <div class="de-role-card de-clickable" data-role="${escapeHtml(role.name)}">
                                    <div class="de-role-card-name">${escapeHtml(role.canonical_name || role.name)}${adjLookup ? adjLookup.getBadge(role.canonical_name || role.name, { compact: true, size: 'sm' }) : ''}</div>
                                    <div class="de-role-card-stats">
                                        <span>${role.frequency || role.count || 1} mentions</span>
                                        <span>${(role.responsibilities || []).length} responsibilities</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Render chart
        setTimeout(() => {
            const topInCategory = categoryData.roles
                .sort((a, b) => (b.frequency || b.count || 1) - (a.frequency || a.count || 1))
                .slice(0, 10);

            createBarChart('de-category-roles-chart', {
                labels: topInCategory.map(r => truncate(r.canonical_name || r.name, 25)),
                values: topInCategory.map(r => r.frequency || r.count || 1)
            });

            // Attach role click handlers
            content.querySelectorAll('.de-role-card').forEach(card => {
                card.addEventListener('click', () => {
                    const roleName = card.dataset.role;
                    const roleData = categoryData.roles.find(r => r.name === roleName);
                    drillInto('role', roleName, roleData);
                });
            });
        }, 50);
    }

    async function renderRoleDrill(roleName, roleData) {
        const content = State.modal.querySelector('.de-content');

        // Fetch detailed context from database - this has the actual responsibility statements
        const context = await fetchRoleContext(roleName);

        // v4.5.0: Show empty state when no context data is available at all
        if (!context && (!roleData || Object.keys(roleData).length <= 1)) {
            content.innerHTML = `
                <div class="de-drill-view de-role-drill">
                    <div class="de-drill-header">
                        <div class="de-drill-icon">${CONFIG.icons.role}</div>
                        <div class="de-drill-title">
                            <h2>${escapeHtml(roleName)}</h2>
                        </div>
                    </div>
                    <div class="de-empty-state" style="text-align:center;padding:48px 24px;">
                        <div style="font-size:48px;margin-bottom:16px;opacity:0.4;">
                            <i data-lucide="user-x" style="width:48px;height:48px;"></i>
                        </div>
                        <h3 style="margin-bottom:8px;color:var(--text-secondary);">No Detailed Data Available</h3>
                        <p style="color:var(--text-muted);max-width:400px;margin:0 auto;">
                            This role was detected in the document but no detailed responsibility statements,
                            action types, or document context could be retrieved. Try running a fresh scan to
                            capture more detail.
                        </p>
                    </div>
                </div>`;
            animateIn(content, 'left');
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        // Get responsibilities from context (which comes from database occurrences)
        // These are the actual extracted statements with full text
        let responsibilities = [];
        if (context?.responsibilities && Array.isArray(context.responsibilities)) {
            // Filter to only include items with actual text content and deduplicate
            const seen = new Set();
            responsibilities = context.responsibilities.filter(r => {
                const text = typeof r === 'string' ? r : (r?.text || r?.responsibility || '');
                if (!text || !text.trim()) return false;

                // Create a normalized key for deduplication (trim and lowercase)
                const normalizedText = text.trim().toLowerCase().substring(0, 100);
                if (seen.has(normalizedText)) return false;
                seen.add(normalizedText);
                return true;
            });
        }

        // The count should reflect actual unique tangible statements we have
        const responsibilityCount = responsibilities.length;

        // Build action types from roleData or responsibilities
        let actionTypes = roleData?.action_types || {};

        // Check for direct R/A/C/I properties (RACI matrix format)
        if (Object.keys(actionTypes).length === 0 && roleData) {
            const raciKeys = ['R', 'A', 'C', 'I'];
            raciKeys.forEach(key => {
                if (typeof roleData[key] === 'number' && roleData[key] > 0) {
                    actionTypes[key] = roleData[key];
                }
            });
        }

        // If still no action types, fetch from RACI API
        if (Object.keys(actionTypes).length === 0) {
            try {
                const raciResponse = await fetch('/api/roles/raci');
                const raciResult = await raciResponse.json();
                if (raciResult.success && raciResult.data?.roles) {
                    // Find this role in RACI data (case-insensitive match)
                    const raciRoleEntry = Object.entries(raciResult.data.roles).find(
                        ([name]) => name.toLowerCase() === roleName.toLowerCase()
                    );
                    if (raciRoleEntry) {
                        const raciData = raciRoleEntry[1];
                        const raciKeys = ['R', 'A', 'C', 'I'];
                        raciKeys.forEach(key => {
                            if (typeof raciData[key] === 'number' && raciData[key] > 0) {
                                actionTypes[key] = raciData[key];
                            }
                        });
                        log(`Fetched RACI data for ${roleName}: R=${raciData.R}, A=${raciData.A}, C=${raciData.C}, I=${raciData.I}`);
                    }
                }
            } catch (err) {
                log(`Could not fetch RACI data for role: ${err.message}`);
            }
        }

        // If still no action types, try to extract from responsibilities
        if (Object.keys(actionTypes).length === 0 && responsibilities.length > 0) {
            // First try stored action_type, then fall back to RACI pattern classification
            responsibilities.forEach(resp => {
                const text = typeof resp === 'string' ? resp : (resp?.text || resp?.responsibility || '');
                let actionType = typeof resp === 'object' ? resp.action_type : '';
                // If no stored action_type, classify using RACI patterns
                if (!actionType && text) {
                    actionType = classifyResponsibilityAction(text);
                }
                if (actionType) {
                    actionTypes[actionType] = (actionTypes[actionType] || 0) + 1;
                }
            });
        }

        // Get documents from context
        const documents = context?.documents || roleData?.source_documents || [];

        // v4.0.3: Adjudication badge for role drill
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        const roleDrillBadge = adjLookup ? adjLookup.getBadge(roleData?.canonical_name || roleName) : '';

        content.innerHTML = `
            <div class="de-drill-view de-role-drill">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.role}</div>
                    <div class="de-drill-title">
                        <h2>${escapeHtml(roleData?.canonical_name || roleName)}${roleDrillBadge}</h2>
                        <p class="de-role-category-tag">${escapeHtml(roleData?.category || getCategoryForRole(roleName))}</p>
                    </div>
                </div>

                <div class="de-drill-stats">
                    <div class="de-mini-stat de-clickable" data-drill="mentions">
                        <div class="de-mini-value">${formatNumber(roleData?.frequency || roleData?.count || 1)}</div>
                        <div class="de-mini-label">Mentions</div>
                    </div>
                    <div class="de-mini-stat de-clickable" data-drill="responsibilities">
                        <div class="de-mini-value">${responsibilityCount}</div>
                        <div class="de-mini-label">Responsibilities</div>
                    </div>
                    <div class="de-mini-stat de-clickable" data-drill="documents">
                        <div class="de-mini-value">${documents.length || 1}</div>
                        <div class="de-mini-label">Documents</div>
                    </div>
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${Object.keys(actionTypes).length}</div>
                        <div class="de-mini-label">Action Types</div>
                    </div>
                </div>

                <!-- Two-column layout: content + editing panel -->
                <div class="de-role-layout">
                    <!-- Left: Data cards -->
                    <div class="de-role-content">
                        <div class="de-viz-grid de-drill-grid">
                            <!-- Responsibilities Section -->
                            <div class="de-viz-card de-viz-large">
                                <div class="de-viz-header">
                                    <h3>${CONFIG.icons.responsibility} Responsibility Statements</h3>
                                    <span class="de-viz-count">${responsibilityCount} found</span>
                                </div>
                                <div class="de-viz-body de-scrollable de-resp-list">
                                    ${(() => {
                                        if (responsibilities.length > 0) {
                                            return responsibilities.map((resp, i) => {
                                                const text = typeof resp === 'string' ? resp : (resp?.text || resp?.responsibility || '');
                                                const doc = typeof resp === 'object' ? resp.document : '';
                                                const actionType = typeof resp === 'object' ? resp.action_type : '';
                                                const stmtIdx = typeof resp === 'object' ? (resp.statement_index ?? -1) : -1;
                                                const reviewStatus = typeof resp === 'object' ? (resp.review_status || '') : '';
                                                const notes = typeof resp === 'object' ? (resp.notes || '') : '';
                                                const statusIcon = reviewStatus === 'approved' ? '✓' : reviewStatus === 'rejected' ? '✗' : '';
                                                const statusClass = reviewStatus ? ` de-stmt-${reviewStatus}` : '';

                                                return `
                                                    <div class="de-resp-item de-clickable de-stmt-select${statusClass}" data-resp-idx="${i}" data-stmt-idx="${stmtIdx}" data-stmt-text="${escapeHtml(text)}" data-stmt-doc="${escapeHtml(doc)}" data-stmt-role="${escapeHtml(roleName)}" data-stmt-action="${escapeHtml(actionType)}" data-stmt-status="${escapeHtml(reviewStatus)}" data-stmt-notes="${escapeHtml(notes)}" title="Click to edit this statement">
                                                        <span class="de-resp-num${statusClass}">${statusIcon || (i + 1)}</span>
                                                        <div class="de-resp-content">
                                                            <span class="de-resp-text">${escapeHtml(truncate(text, 200))}</span>
                                                            ${(doc || actionType) ? `
                                                                <div class="de-resp-meta">
                                                                    ${actionType ? `<span class="de-resp-action">${escapeHtml(actionType)}</span>` : ''}
                                                                    ${doc ? `<span class="de-resp-doc">${escapeHtml(truncate(doc, 30))}</span>` : ''}
                                                                </div>
                                                            ` : ''}
                                                        </div>
                                                    </div>
                                                `;
                                            }).join('');
                                        } else {
                                            return '<div class="de-empty">No responsibility statements captured</div>';
                                        }
                                    })()}
                                </div>
                            </div>

                            <!-- Action Types -->
                            <div class="de-viz-card">
                                <div class="de-viz-header">
                                    <h3>${CONFIG.icons.action} Action Types</h3>
                                </div>
                                <div class="de-viz-body">
                                    ${Object.keys(actionTypes).length > 0 ? `
                                        <div class="de-action-tags">
                                            ${Object.entries(actionTypes).map(([action, count]) => `
                                                <div class="de-action-tag de-clickable" data-action="${escapeHtml(action)}">
                                                    <span class="de-action-name">${escapeHtml(action)}</span>
                                                    <span class="de-action-count">${count}</span>
                                                </div>
                                            `).join('')}
                                        </div>
                                    ` : '<div class="de-empty">No action types detected</div>'}
                                </div>
                            </div>

                            <!-- Documents -->
                            <div class="de-viz-card">
                                <div class="de-viz-header">
                                    <h3>${CONFIG.icons.document} Source Documents</h3>
                                </div>
                                <div class="de-viz-body de-scrollable">
                                    ${documents.length > 0 ? documents.map(doc => `
                                        <div class="de-doc-item de-clickable" data-doc="${escapeHtml(doc)}">
                                            <span class="de-doc-icon">${CONFIG.icons.document}</span>
                                            <span class="de-doc-name">${escapeHtml(truncate(doc, 40))}</span>
                                        </div>
                                    `).join('') : `
                                        <div class="de-doc-item">
                                            <span class="de-doc-icon">${CONFIG.icons.document}</span>
                                            <span class="de-doc-name">Current document</span>
                                        </div>
                                    `}
                                </div>
                            </div>

                            <!-- Sample Context -->
                            ${context?.sample_contexts?.length > 0 ? `
                                <div class="de-viz-card de-viz-wide">
                                    <div class="de-viz-header">
                                        <h3>${CONFIG.icons.expand} Sample Context</h3>
                                    </div>
                                    <div class="de-viz-body de-scrollable">
                                        ${context.sample_contexts.slice(0, 3).map(ctx => `
                                            <div class="de-context-sample">
                                                ${highlightRoleInContext(ctx, roleName)}
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Right: Role Editing Panel -->
                    <div class="de-role-edit-panel">
                        <div class="de-edit-panel-header de-clickable" title="Toggle editing panel">
                            <span class="de-edit-panel-title">
                                <svg class="de-edit-caret" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                                Role Actions
                            </span>
                        </div>
                        <div class="de-edit-panel-body de-collapsed">
                        <div class="de-edit-section">
                            <label class="de-edit-label">Adjudication</label>
                            <div class="de-adj-status">
                                <span class="de-adj-badge" data-status="pending">Pending Review</span>
                            </div>
                            <div class="de-adj-actions">
                                <button class="de-adj-btn de-adj-confirm" data-action="confirmed" title="Confirm as valid role">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                                    Confirm
                                </button>
                                <button class="de-adj-btn de-adj-deliverable" data-action="deliverable" title="Mark as deliverable">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
                                    Deliverable
                                </button>
                                <button class="de-adj-btn de-adj-reject" data-action="rejected" title="Reject role">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>
                                    Reject
                                </button>
                            </div>
                        </div>

                        <div class="de-edit-section">
                            <label class="de-edit-label">Category</label>
                            <select class="de-category-select">
                                <option value="Role">Role</option>
                                <option value="Management">Management</option>
                                <option value="Technical">Technical</option>
                                <option value="Organization">Organization</option>
                                <option value="Governance">Governance</option>
                                <option value="Engineering">Engineering</option>
                                <option value="Quality">Quality</option>
                                <option value="Safety">Safety</option>
                                <option value="Operations">Operations</option>
                                <option value="Support">Support</option>
                                <option value="Compliance">Compliance</option>
                                <option value="Procurement">Procurement</option>
                                <option value="Deliverable">Deliverable</option>
                            </select>
                        </div>

                        <div class="de-edit-section">
                            <label class="de-edit-label">Notes</label>
                            <textarea class="de-notes-input" placeholder="Add notes about this role..." rows="3"></textarea>
                        </div>

                        <div class="de-edit-section">
                            <label class="de-edit-label">Function Tags</label>
                            <div class="de-tags-container">
                                <div class="de-tag-pills"></div>
                                <button class="de-add-tag-btn" title="Add function tag">
                                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/><path d="M7 7h.01"/></svg>
                                    Add Tag
                                </button>
                            </div>
                            <div class="de-tag-dropdown-anchor" style="position:relative;"></div>
                        </div>

                        <div class="de-edit-divider"></div>

                        <div class="de-edit-section">
                            <button class="de-action-btn de-primary de-view-in-doc-btn" style="width:100%;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                                View in Document
                            </button>
                        </div>
                        </div><!-- /de-edit-panel-body -->
                    </div>
                </div>
            </div>
        `;

        // ============================================================
        // EDITING PANEL HANDLERS
        // ============================================================

        const editPanel = content.querySelector('.de-role-edit-panel');
        const canonicalName = roleData?.canonical_name || roleName;

        // --- Toggle collapse/expand for edit panel ---
        const panelHeader = editPanel?.querySelector('.de-edit-panel-header');
        const panelBody = editPanel?.querySelector('.de-edit-panel-body');
        if (panelHeader && panelBody) {
            // Default collapsed
            editPanel.classList.add('de-panel-collapsed');
            panelHeader.addEventListener('click', () => {
                const isCollapsed = panelBody.classList.toggle('de-collapsed');
                editPanel.classList.toggle('de-panel-collapsed', isCollapsed);
                const caret = panelHeader.querySelector('.de-edit-caret');
                if (caret) {
                    caret.classList.toggle('de-caret-open', !isCollapsed);
                }
            });
        }

        // --- Load current adjudication status ---
        (async () => {
            try {
                const resp = await fetch(`/api/roles/adjudication-status?role_name=${encodeURIComponent(canonicalName)}`);
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.success) {
                        // Update badge
                        const badge = editPanel.querySelector('.de-adj-badge');
                        if (badge) {
                            badge.dataset.status = data.status || 'pending';
                            const labels = { 'pending': 'Pending Review', 'confirmed': 'Confirmed Role', 'deliverable': 'Deliverable', 'rejected': 'Rejected' };
                            badge.textContent = labels[data.status] || 'Pending Review';
                        }
                        // Highlight active button
                        if (data.status && data.status !== 'pending') {
                            editPanel.querySelectorAll('.de-adj-btn').forEach(b => b.classList.remove('de-adj-active'));
                            const activeBtn = editPanel.querySelector(`.de-adj-${data.status === 'confirmed' ? 'confirm' : data.status}`);
                            if (activeBtn) activeBtn.classList.add('de-adj-active');
                        }
                        // Set category
                        const catSelect = editPanel.querySelector('.de-category-select');
                        if (catSelect && data.category) {
                            if (!catSelect.querySelector(`option[value="${data.category}"]`)) {
                                const opt = document.createElement('option');
                                opt.value = data.category;
                                opt.textContent = data.category;
                                catSelect.appendChild(opt);
                            }
                            catSelect.value = data.category;
                        }
                        // Set notes
                        const notesInput = editPanel.querySelector('.de-notes-input');
                        if (notesInput && data.notes) notesInput.value = data.notes;
                    }
                }
            } catch (e) { log('Could not load adjudication status: ' + e); }
        })();

        // --- Load function tags ---
        let _deCurrentTags = [];
        async function loadDeTags() {
            _deCurrentTags = [];
            try {
                const resp = await fetch(`/api/role-function-tags?role_name=${encodeURIComponent(canonicalName)}`);
                if (resp.ok) {
                    const data = await resp.json();
                    _deCurrentTags = data?.data?.tags || (Array.isArray(data) ? data : []);
                }
            } catch (e) { /* silent */ }
            renderDeTagPills();
        }

        function renderDeTagPills() {
            const container = editPanel.querySelector('.de-tag-pills');
            if (!container) return;
            if (!_deCurrentTags.length) {
                container.innerHTML = '<span style="color:var(--text-muted);font-size:11px;">No tags assigned</span>';
                return;
            }
            container.innerHTML = _deCurrentTags.map(t => {
                const color = t.function_color || '#3b82f6';
                return `<span class="de-tag-pill" style="background:${color}18;color:${color};border:1px solid ${color}30;display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:10px;font-size:11px;margin:2px;">
                    ${escapeHtml(t.function_name || t.function_code)}
                    <span class="de-tag-remove" data-tag-id="${t.id}" style="cursor:pointer;opacity:0.7;font-size:13px;" title="Remove">&times;</span>
                </span>`;
            }).join('');

            container.querySelectorAll('.de-tag-remove').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    try {
                        const resp = await fetch(`/api/role-function-tags/${btn.dataset.tagId}`, {
                            method: 'DELETE',
                            headers: { 'X-CSRF-Token': getCSRFToken() }
                        });
                        if (resp.ok) {
                            if (typeof showToast === 'function') showToast('Tag removed', 'success');
                            await loadDeTags();
                        }
                    } catch (err) { log('Tag removal error: ' + err); }
                });
            });
        }

        loadDeTags();

        // --- Adjudication button handlers ---
        editPanel.querySelectorAll('.de-adj-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const action = btn.dataset.action;
                const notes = editPanel.querySelector('.de-notes-input')?.value || '';
                const category = editPanel.querySelector('.de-category-select')?.value || 'Role';

                // Update UI immediately
                const badge = editPanel.querySelector('.de-adj-badge');
                if (badge) {
                    badge.dataset.status = action;
                    const labels = { 'confirmed': 'Confirmed Role', 'deliverable': 'Deliverable', 'rejected': 'Rejected' };
                    badge.textContent = labels[action] || action;
                }
                editPanel.querySelectorAll('.de-adj-btn').forEach(b => b.classList.remove('de-adj-active'));
                btn.classList.add('de-adj-active');

                try {
                    const resp = await fetch('/api/roles/adjudicate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken() },
                        body: JSON.stringify({
                            role_name: canonicalName,
                            action: action,
                            category: category,
                            notes: notes,
                            is_deliverable: action === 'deliverable'
                        })
                    });
                    const result = await resp.json();
                    if (result.success) {
                        const label = action === 'confirmed' ? 'confirmed' : action === 'deliverable' ? 'marked as deliverable' : 'rejected';
                        if (typeof showToast === 'function') showToast(`Role "${canonicalName}" ${label}`, 'success');
                    }
                } catch (err) {
                    log('Adjudication error: ' + err);
                    if (typeof showToast === 'function') showToast('Adjudication saved locally', 'info');
                }

                // Sync with Roles Studio
                if (window.TWR?.RolesAdjudication?.adjudicateRole) {
                    window.TWR.RolesAdjudication.adjudicateRole(canonicalName, action);
                }
            });
        });

        // --- Add Tag button ---
        const addTagBtn = editPanel.querySelector('.de-add-tag-btn');
        if (addTagBtn) {
            addTagBtn.addEventListener('click', async () => {
                const anchor = editPanel.querySelector('.de-tag-dropdown-anchor');
                const existing = anchor?.querySelector('.adj-tag-dropdown');
                if (existing) { existing.remove(); return; }

                // Fetch function categories
                let cats = [];
                try {
                    const resp = await fetch('/api/function-categories');
                    if (resp.ok) {
                        const data = await resp.json();
                        cats = data?.data || data?.categories || (Array.isArray(data) ? data : []);
                    }
                } catch (e) { /* silent */ }

                if (!cats.length) {
                    if (typeof showToast === 'function') showToast('No function categories available', 'info');
                    return;
                }

                // Build hierarchy
                const childMap = {};
                cats.forEach(c => { if (c.parent_code) { if (!childMap[c.parent_code]) childMap[c.parent_code] = []; childMap[c.parent_code].push(c); } });
                const topLevel = cats.filter(c => !c.parent_code);

                let itemsHtml = '';
                topLevel.forEach(parent => {
                    const pColor = parent.color || '#3b82f6';
                    itemsHtml += `<div class="adj-tag-dropdown-header">${escapeHtml(parent.name)}</div>`;
                    itemsHtml += `<div class="adj-tag-dropdown-item" data-code="${escapeHtml(parent.code)}">
                        <span class="adj-tag-dot" style="background:${pColor}"></span>
                        <span>${escapeHtml(parent.code)} - ${escapeHtml(parent.name)}</span>
                    </div>`;
                    (childMap[parent.code] || []).forEach(child => {
                        const cColor = child.color || pColor;
                        itemsHtml += `<div class="adj-tag-dropdown-item adj-tag-level-2" data-code="${escapeHtml(child.code)}">
                            <span class="adj-tag-dot" style="background:${cColor}"></span>
                            <span>${escapeHtml(child.code)} - ${escapeHtml(child.name)}</span>
                        </div>`;
                        (childMap[child.code] || []).forEach(gc => {
                            const gColor = gc.color || cColor;
                            itemsHtml += `<div class="adj-tag-dropdown-item adj-tag-level-3" data-code="${escapeHtml(gc.code)}">
                                <span class="adj-tag-dot" style="background:${gColor}"></span>
                                <span>${escapeHtml(gc.code)} - ${escapeHtml(gc.name)}</span>
                            </div>`;
                        });
                    });
                });

                const dropdown = document.createElement('div');
                dropdown.className = 'adj-tag-dropdown de-tag-dropdown-active';
                dropdown.innerHTML = `
                    <div class="adj-tag-dropdown-search">
                        <input type="text" class="adj-tag-search-input" placeholder="Search tags..." autocomplete="off">
                    </div>
                    <div class="adj-tag-dropdown-list">${itemsHtml}</div>`;
                if (anchor) anchor.appendChild(dropdown);

                // Search filter
                const searchInput = dropdown.querySelector('.adj-tag-search-input');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.addEventListener('input', () => {
                        const q = searchInput.value.toLowerCase();
                        dropdown.querySelectorAll('.adj-tag-dropdown-item, .adj-tag-dropdown-header').forEach(el => {
                            el.style.display = (!q || el.textContent.toLowerCase().includes(q)) ? '' : 'none';
                        });
                    });
                    searchInput.addEventListener('click', (e) => e.stopPropagation());
                }

                // Item click
                dropdown.addEventListener('click', async (e) => {
                    const item = e.target.closest('.adj-tag-dropdown-item');
                    if (!item) return;
                    const code = item.dataset.code;
                    if (code) {
                        try {
                            const resp = await fetch('/api/role-function-tags', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken() },
                                body: JSON.stringify({ role_name: canonicalName, function_code: code, assigned_by: 'data-explorer' })
                            });
                            const result = await resp.json();
                            if (result.success) {
                                if (typeof showToast === 'function') showToast(`Tag "${code}" assigned`, 'success');
                                await loadDeTags();
                            } else {
                                if (typeof showToast === 'function') showToast(result.error || 'Already assigned', 'info');
                            }
                        } catch (err) { log('Tag assignment error: ' + err); }
                        dropdown.remove();
                    }
                });

                // Close on outside click
                setTimeout(() => {
                    const closer = (e) => {
                        if (!dropdown.contains(e.target) && !addTagBtn.contains(e.target)) {
                            dropdown.remove();
                            document.removeEventListener('click', closer);
                        }
                    };
                    document.addEventListener('click', closer);
                }, 10);
            });
        }

        // --- View in Document button ---
        const viewInDocBtn = content.querySelector('.de-view-in-doc-btn');
        if (viewInDocBtn) {
            viewInDocBtn.addEventListener('click', () => {
                if (TWR.RoleSourceViewer?.open) {
                    TWR.RoleSourceViewer.open(canonicalName);
                    TWR.DataExplorer.close();
                }
            });
        }

        // --- Per-Statement editing: click a statement to edit in the right panel ---
        let _activeStmtIdx = -1;

        function showStatementEditor(item) {
            const text = item.dataset.stmtText || '';
            const doc = item.dataset.stmtDoc || '';
            const role = item.dataset.stmtRole || '';
            const actionType = item.dataset.stmtAction || '';
            const reviewStatus = item.dataset.stmtStatus || '';
            const notes = item.dataset.stmtNotes || '';
            const stmtIdx = parseInt(item.dataset.stmtIdx || '-1');
            const respIdx = parseInt(item.dataset.respIdx || '0');

            _activeStmtIdx = respIdx;

            // Highlight active statement
            content.querySelectorAll('.de-stmt-select').forEach(el => el.classList.remove('de-stmt-active'));
            item.classList.add('de-stmt-active');

            // Replace right panel body with statement editor (keep header)
            let panelBodyEl = editPanel.querySelector('.de-edit-panel-body');
            if (!panelBodyEl) {
                // Panel was already replaced (e.g. from another stmt click) — use editPanel directly
                editPanel.innerHTML = `
                    <div class="de-edit-panel-header de-clickable" title="Toggle editing panel">
                        <span class="de-edit-panel-title">
                            <svg class="de-edit-caret de-caret-open" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
                            Statement Editor
                        </span>
                    </div>
                    <div class="de-edit-panel-body"></div>`;
                panelBodyEl = editPanel.querySelector('.de-edit-panel-body');
                // Re-attach toggle handler
                editPanel.querySelector('.de-edit-panel-header').addEventListener('click', () => {
                    const isCollapsed = panelBodyEl.classList.toggle('de-collapsed');
                    editPanel.classList.toggle('de-panel-collapsed', isCollapsed);
                    const caret = editPanel.querySelector('.de-edit-caret');
                    if (caret) caret.classList.toggle('de-caret-open', !isCollapsed);
                });
            }
            // Expand panel and update header
            panelBodyEl.classList.remove('de-collapsed');
            editPanel.classList.remove('de-panel-collapsed');
            const caretEl = editPanel.querySelector('.de-edit-caret');
            if (caretEl) caretEl.classList.add('de-caret-open');
            const titleEl = editPanel.querySelector('.de-edit-panel-title');
            if (titleEl) titleEl.lastChild.textContent = ' Statement Editor';

            panelBodyEl.innerHTML = `
                <div class="de-edit-section">
                    <label class="de-edit-label">Statement #${respIdx + 1}
                        <button class="de-stmt-edit-text-btn" title="Edit statement text" style="float:right;background:none;border:none;color:var(--de-accent,#4A90D9);cursor:pointer;font-size:12px;padding:0;">✏️ Edit Text</button>
                    </label>
                    <div class="de-stmt-full-text">${escapeHtml(text)}</div>
                    <textarea class="de-stmt-text-edit" style="display:none;width:100%;min-height:60px;background:rgba(255,255,255,0.06);border:1px solid var(--de-accent,#4A90D9);color:var(--de-text-primary,#fff);padding:6px 8px;border-radius:4px;font-size:13px;font-family:inherit;resize:vertical;">${escapeHtml(text)}</textarea>
                </div>

                <div class="de-edit-section">
                    <label class="de-edit-label">Review Status</label>
                    <div class="de-stmt-review-actions">
                        <button class="de-stmt-review-btn de-stmt-approve${reviewStatus === 'approved' ? ' de-stmt-review-active' : ''}" data-status="approved" title="Approve this statement">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                            Approve
                        </button>
                        <button class="de-stmt-review-btn de-stmt-reject-btn${reviewStatus === 'rejected' ? ' de-stmt-review-active' : ''}" data-status="rejected" title="Reject this statement">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>
                            Reject
                        </button>
                    </div>
                </div>

                <div class="de-edit-section">
                    <label class="de-edit-label">Action Type</label>
                    <select class="de-stmt-action-select">
                        <option value=""${!actionType ? ' selected' : ''}>Auto-detect</option>
                        <option value="R"${actionType === 'R' ? ' selected' : ''}>R - Responsible</option>
                        <option value="A"${actionType === 'A' ? ' selected' : ''}>A - Accountable</option>
                        <option value="C"${actionType === 'C' ? ' selected' : ''}>C - Consulted</option>
                        <option value="I"${actionType === 'I' ? ' selected' : ''}>I - Informed</option>
                    </select>
                </div>

                <div class="de-edit-section">
                    <label class="de-edit-label">Notes</label>
                    <textarea class="de-stmt-notes" placeholder="Add notes about this statement..." rows="3">${escapeHtml(notes)}</textarea>
                </div>

                <div class="de-edit-section">
                    <label class="de-edit-label">Source</label>
                    <div class="de-stmt-source">${doc ? escapeHtml(truncate(doc, 45)) : 'Unknown document'}</div>
                </div>

                <div class="de-edit-divider"></div>

                <div class="de-edit-section" style="display:flex;flex-direction:column;gap:6px;">
                    <button class="de-action-btn de-primary de-stmt-save-btn" style="width:100%;padding:8px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                        Save Changes
                    </button>
                    <button class="de-action-btn de-stmt-view-doc-btn" style="width:100%;padding:8px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                        View in Document
                    </button>
                    <button class="de-action-btn de-stmt-back-btn" style="width:100%;padding:8px;">
                        ← Back to Role
                    </button>
                </div>
            `;

            // --- Statement review button handlers ---
            let currentStatus = reviewStatus;
            editPanel.querySelectorAll('.de-stmt-review-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const newStatus = btn.dataset.status;
                    // Toggle off if already active
                    if (currentStatus === newStatus) {
                        currentStatus = '';
                        editPanel.querySelectorAll('.de-stmt-review-btn').forEach(b => b.classList.remove('de-stmt-review-active'));
                    } else {
                        currentStatus = newStatus;
                        editPanel.querySelectorAll('.de-stmt-review-btn').forEach(b => b.classList.remove('de-stmt-review-active'));
                        btn.classList.add('de-stmt-review-active');
                    }
                });
            });

            // --- Edit Text toggle ---
            editPanel.querySelector('.de-stmt-edit-text-btn')?.addEventListener('click', () => {
                const fullTextEl = editPanel.querySelector('.de-stmt-full-text');
                const textEditEl = editPanel.querySelector('.de-stmt-text-edit');
                const editBtn = editPanel.querySelector('.de-stmt-edit-text-btn');
                if (fullTextEl && textEditEl) {
                    const isEditing = textEditEl.style.display !== 'none';
                    fullTextEl.style.display = isEditing ? '' : 'none';
                    textEditEl.style.display = isEditing ? 'none' : '';
                    editBtn.textContent = isEditing ? '✏️ Edit Text' : '✏️ Cancel Edit';
                    if (!isEditing) textEditEl.focus();
                }
            });

            // --- Save button ---
            editPanel.querySelector('.de-stmt-save-btn')?.addEventListener('click', async () => {
                const newAction = editPanel.querySelector('.de-stmt-action-select')?.value || '';
                const newNotes = editPanel.querySelector('.de-stmt-notes')?.value || '';
                // v4.9.5: Include text edit if textarea is visible
                const textEditEl = editPanel.querySelector('.de-stmt-text-edit');
                const isEditingText = textEditEl && textEditEl.style.display !== 'none';
                const newText = isEditingText ? textEditEl.value.trim() : '';

                if (stmtIdx < 0 || !doc) {
                    if (typeof showToast === 'function') showToast('Cannot save: missing document reference', 'error');
                    return;
                }

                try {
                    const resp = await fetch('/api/roles/responsibility', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken() },
                        body: JSON.stringify({
                            role_name: canonicalName,
                            document: doc,
                            statement_index: stmtIdx,
                            updates: Object.assign(
                                { action_type: newAction, review_status: currentStatus, notes: newNotes },
                                newText ? { text: newText } : {}
                            )
                        })
                    });
                    const result = await resp.json();
                    if (result.success) {
                        if (typeof showToast === 'function') showToast('Statement updated', 'success');

                        // Update the list item visuals
                        item.dataset.stmtAction = newAction;
                        item.dataset.stmtStatus = currentStatus;
                        item.dataset.stmtNotes = newNotes;

                        // Update status class on the item
                        item.classList.remove('de-stmt-approved', 'de-stmt-rejected');
                        if (currentStatus) item.classList.add('de-stmt-' + currentStatus);

                        // Update the number badge
                        const numBadge = item.querySelector('.de-resp-num');
                        if (numBadge) {
                            numBadge.classList.remove('de-stmt-approved', 'de-stmt-rejected');
                            if (currentStatus === 'approved') {
                                numBadge.textContent = '✓';
                                numBadge.classList.add('de-stmt-approved');
                            } else if (currentStatus === 'rejected') {
                                numBadge.textContent = '✗';
                                numBadge.classList.add('de-stmt-rejected');
                            } else {
                                numBadge.textContent = respIdx + 1;
                            }
                        }

                        // Update action type in meta if present
                        const actionEl = item.querySelector('.de-resp-action');
                        if (actionEl && newAction) actionEl.textContent = newAction;

                        // v4.9.5: Update statement text in list if edited
                        if (newText) {
                            const respTextEl = item.querySelector('.de-resp-text');
                            if (respTextEl) respTextEl.textContent = newText.length > 120 ? newText.substring(0, 120) + '...' : newText;
                            // Update full text display in editor
                            const fullTextEl = editPanel.querySelector('.de-stmt-full-text');
                            if (fullTextEl) fullTextEl.textContent = newText;
                            // Hide textarea, show static text
                            const textEditEl2 = editPanel.querySelector('.de-stmt-text-edit');
                            if (textEditEl2) textEditEl2.style.display = 'none';
                            if (fullTextEl) fullTextEl.style.display = '';
                            const editBtn2 = editPanel.querySelector('.de-stmt-edit-text-btn');
                            if (editBtn2) editBtn2.textContent = '✏️ Edit Text';
                        }
                    } else {
                        if (typeof showToast === 'function') showToast(result.error || 'Save failed', 'error');
                    }
                } catch (err) {
                    log('Statement save error: ' + err);
                    if (typeof showToast === 'function') showToast('Save failed: ' + err.message, 'error');
                }
            });

            // --- View in Document button --- v5.1.2: Use Statement Source Viewer instead of Role Source Viewer
            editPanel.querySelector('.de-stmt-view-doc-btn')?.addEventListener('click', () => {
                if (TWR.StatementSourceViewer?.open) {
                    const stmtData = {
                        text: text,
                        document: doc,
                        role_name: role,
                        action_type: actionType,
                        review_status: reviewStatus,
                        notes: notes,
                        statement_index: stmtIdx
                    };
                    TWR.StatementSourceViewer.open(stmtData);
                    TWR.DataExplorer.close();
                } else if (TWR.RoleSourceViewer?.open) {
                    // Fallback to Role Source Viewer if Statement Source Viewer not loaded
                    TWR.RoleSourceViewer.open(role, { searchText: text, sourceDocument: doc });
                    TWR.DataExplorer.close();
                }
            });

            // --- Back to Role button ---
            editPanel.querySelector('.de-stmt-back-btn')?.addEventListener('click', () => {
                content.querySelectorAll('.de-stmt-select').forEach(el => el.classList.remove('de-stmt-active'));
                _activeStmtIdx = -1;
                // Re-render the role edit panel (re-run renderRoleDrill would be heavy, just reload)
                renderRoleDrill(roleName, roleData);
            });
        }

        content.querySelectorAll('.de-stmt-select').forEach(item => {
            item.addEventListener('click', () => showStatementEditor(item));
        });

        // Attach handlers for action type drill-down
        content.querySelectorAll('.de-action-tag').forEach(tag => {
            tag.addEventListener('click', () => {
                const action = tag.dataset.action;
                const count = parseInt(tag.querySelector('.de-action-count')?.textContent || '0');
                renderRoleActionDrill(roleName, action, count, responsibilities, context);
            });
        });
    }

    // RACI pattern matchers (same logic as backend scan_history.py)
    const RACI_PATTERNS = {
        'R': /\b(shall|must|perform|execute|implement|develop|define|lead|ensure|maintain|conduct|create|prepare|manage|oversee|verify|validate|complete|deliver|produce|design|build|configure|install|test|deploy)\b/i,
        'A': /\b(approv|authoriz|sign|certif|accept|endors|sanction|confirm|ratif)\b/i,
        'C': /\b(review|coordinat|support|consult|advis|assist|collaborat|recommend|suggest|evaluate|assess|examine|input|feedback|comment)\b/i,
        'I': /\b(receiv|report|monitor|inform|notif|communicat|track|provid|aware|brief|updat|acknowledg|distribut)\b/i
    };

    function classifyResponsibilityAction(text) {
        if (!text || typeof text !== 'string') return 'R'; // Default
        const lower = text.toLowerCase();

        // Check in priority order (A is most specific, then R, C, I)
        if (RACI_PATTERNS['A'].test(lower)) return 'A';
        if (RACI_PATTERNS['R'].test(lower)) return 'R';
        if (RACI_PATTERNS['C'].test(lower)) return 'C';
        if (RACI_PATTERNS['I'].test(lower)) return 'I';

        return 'R'; // Default to Responsible
    }

    // New function to show responsibilities filtered by action type within a role
    async function renderRoleActionDrill(roleName, actionType, count, responsibilities, context) {
        const content = State.modal.querySelector('.de-content');

        // Get action type full name
        const actionNames = {
            'R': 'Responsible',
            'A': 'Accountable',
            'C': 'Consulted',
            'I': 'Informed'
        };
        const actionFullName = actionNames[actionType] || actionType;

        // Classify all responsibilities by action type using the same logic as backend
        let allClassified = responsibilities.map(r => {
            const text = typeof r === 'string' ? r : (r?.text || r?.responsibility || '');
            const storedAction = typeof r === 'object' ? (r.action_type || '') : '';
            const doc = typeof r === 'object' ? (r.document || '') : '';
            const section = typeof r === 'object' ? (r.section || '') : '';
            const respContext = typeof r === 'object' ? (r.context || '') : '';

            // Use stored action type if available and matches RACI, otherwise classify
            let computedAction = storedAction.toUpperCase();
            if (!['R', 'A', 'C', 'I'].includes(computedAction)) {
                computedAction = classifyResponsibilityAction(text);
            }

            return {
                text,
                action_type: computedAction,
                document: doc,
                section,
                context: respContext
            };
        });

        // Filter to only the requested action type
        let filteredResponsibilities = allClassified.filter(r =>
            r.action_type.toUpperCase() === actionType.toUpperCase()
        );

        log(`Action drill for ${roleName} - ${actionType}: ${filteredResponsibilities.length} of ${allClassified.length} responsibilities`);

        // If we still don't have data, try to get from context occurrences
        if (filteredResponsibilities.length === 0 && context?.occurrences) {
            log(`Trying context occurrences for ${actionType}`);
            allClassified = context.occurrences.map(o => {
                const text = o.responsibility || o.text || o.context || '';
                const storedAction = o.action_type || '';
                let computedAction = storedAction.toUpperCase();
                if (!['R', 'A', 'C', 'I'].includes(computedAction)) {
                    computedAction = classifyResponsibilityAction(text);
                }
                return {
                    text,
                    action_type: computedAction,
                    document: o.document || '',
                    section: o.section || '',
                    context: o.context || ''
                };
            });
            filteredResponsibilities = allClassified.filter(r =>
                r.action_type.toUpperCase() === actionType.toUpperCase()
            );
            log(`Found ${filteredResponsibilities.length} from context occurrences`);
        }

        // Update state and breadcrumbs (same pattern as drillInto)
        State.history.push({
            type: State.currentData?.type || 'role',
            id: State.currentData?.id || roleName,
            data: State.currentData?.data,
            scrollPosition: State.modal?.querySelector('.de-content')?.scrollTop || 0
        });
        State.currentLevel++;
        State.currentData = {
            type: 'role-action',
            id: `${roleName}-${actionType}`,
            data: { roleName, actionType, count, responsibilities, context }
        };
        updateBreadcrumbs();

        content.innerHTML = `
            <div class="de-drill-view de-action-drill">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.action}</div>
                    <div class="de-drill-title">
                        <h2>${escapeHtml(roleName)}: ${escapeHtml(actionFullName)} (${actionType})</h2>
                        <p>${count} responsibility statements with this action type</p>
                    </div>
                </div>

                <div class="de-explanation-box">
                    <h4>What does "${escapeHtml(actionFullName)}" mean?</h4>
                    <p>${getActionDescription(actionType)}</p>
                </div>

                <div class="de-drill-stats">
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${count}</div>
                        <div class="de-mini-label">Statements</div>
                    </div>
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${new Set(filteredResponsibilities.map(r => r.document).filter(Boolean)).size || 1}</div>
                        <div class="de-mini-label">Documents</div>
                    </div>
                </div>

                <div class="de-viz-card de-viz-full">
                    <div class="de-viz-header">
                        <h3>${CONFIG.icons.responsibility} ${escapeHtml(actionFullName)} Statements for ${escapeHtml(roleName)}</h3>
                        <span class="de-viz-count">${filteredResponsibilities.length} found</span>
                    </div>
                    <div class="de-viz-body de-scrollable de-resp-list">
                        ${filteredResponsibilities.length > 0 ? filteredResponsibilities.map((resp, i) => {
                            const text = typeof resp === 'string' ? resp : (resp?.text || resp?.responsibility || '');
                            const doc = typeof resp === 'object' ? (resp.document || resp.source_document || '') : '';
                            const section = typeof resp === 'object' ? (resp.section || '') : '';
                            const respContext = typeof resp === 'object' ? (resp.context || '') : '';

                            return `
                                <div class="de-resp-item de-resp-detailed">
                                    <span class="de-resp-num">${i + 1}</span>
                                    <div class="de-resp-content">
                                        <span class="de-resp-text">${escapeHtml(text)}</span>
                                        <div class="de-resp-meta">
                                            <span class="de-resp-action de-action-${actionType.toLowerCase()}">${escapeHtml(actionType)}</span>
                                            ${doc ? `<span class="de-resp-doc" title="${escapeHtml(doc)}">${CONFIG.icons.document} ${escapeHtml(truncate(doc, 40))}</span>` : ''}
                                            ${section ? `<span class="de-resp-section">§ ${escapeHtml(truncate(section, 30))}</span>` : ''}
                                        </div>
                                        ${respContext ? `
                                            <div class="de-resp-context">
                                                <span class="de-context-label">Context:</span>
                                                <span class="de-context-text">${escapeHtml(truncate(respContext, 200))}</span>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            `;
                        }).join('') : `
                            <div class="de-empty">
                                <p>No detailed responsibility statements available for this action type.</p>
                                <p class="de-empty-hint">The count of ${count} comes from the RACI analysis. To see detailed statements, ensure the RACI matrix has been run with full context extraction.</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;
    }

    async function renderRolesListDrill(data) {
        const content = State.modal.querySelector('.de-content');
        const roles = data.allRoles || [];

        // v4.0.3: Use shared adjudication lookup utility
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        function getAdjBadge(roleName) {
            return adjLookup ? adjLookup.getBadge(roleName) : '';
        }

        const adjStats = adjLookup ? adjLookup.getStats() : { total: 0, confirmed: 0, deliverable: 0, rejected: 0 };
        const adjCount = adjStats.confirmed + (adjStats.deliverable || 0);

        content.innerHTML = `
            <div class="de-drill-view">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.role}</div>
                    <div class="de-drill-title">
                        <h2>All Roles</h2>
                        <p>${roles.length} unique roles discovered · ${adjCount} adjudicated</p>
                    </div>
                </div>

                <div class="de-search-bar">
                    <input type="text" id="de-roles-search" class="de-search-input" placeholder="Search roles...">
                </div>

                <div class="de-roles-table-container">
                    <table class="de-roles-table">
                        <thead>
                            <tr>
                                <th data-sort="name">Role Name</th>
                                <th data-sort="category">Category</th>
                                <th data-sort="frequency">Mentions</th>
                                <th data-sort="responsibilities">Responsibilities</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="de-roles-tbody">
                            ${roles.map(([name, roleData]) => `
                                <tr class="de-clickable" data-role="${escapeHtml(name)}">
                                    <td class="de-role-name-cell">
                                        ${escapeHtml(roleData.canonical_name || roleData.role_name || name)}
                                        ${getAdjBadge(roleData.canonical_name || roleData.role_name || name)}
                                    </td>
                                    <td><span class="de-cat-badge">${escapeHtml(roleData.category || getCategoryForRole(name))}</span></td>
                                    <td class="de-num-cell">${formatNumber(roleData.frequency || roleData.count || 1)}</td>
                                    <td class="de-num-cell">${roleData.responsibility_count || (roleData.responsibilities || []).length}</td>
                                    <td class="de-arrow-cell">${CONFIG.icons.forward}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        // Search handler
        const searchInput = document.getElementById('de-roles-search');
        const tbody = document.getElementById('de-roles-tbody');

        searchInput.addEventListener('input', debounce((e) => {
            const query = e.target.value.toLowerCase();
            tbody.querySelectorAll('tr').forEach(row => {
                const name = row.dataset.role.toLowerCase();
                row.style.display = name.includes(query) ? '' : 'none';
            });
        }, 200));

        // Row click handlers
        tbody.querySelectorAll('tr').forEach(row => {
            row.addEventListener('click', () => {
                const roleName = row.dataset.role;
                const roleData = roles.find(([n]) => n === roleName)?.[1];
                drillInto('role', roleName, { name: roleName, ...roleData });
            });
        });

        // Sort handlers
        content.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                // Simple sort implementation
                const sortKey = th.dataset.sort;
                const rows = Array.from(tbody.querySelectorAll('tr'));

                rows.sort((a, b) => {
                    const aVal = a.cells[getColumnIndex(sortKey)].textContent;
                    const bVal = b.cells[getColumnIndex(sortKey)].textContent;
                    return sortKey === 'name' ? aVal.localeCompare(bVal) : Number(bVal) - Number(aVal);
                });

                rows.forEach(row => tbody.appendChild(row));
            });
        });

        function getColumnIndex(sortKey) {
            const map = { name: 0, category: 1, frequency: 2, responsibilities: 3 };
            return map[sortKey] || 0;
        }
    }

    async function renderMentionsBreakdown(data) {
        const content = State.modal.querySelector('.de-content');

        content.innerHTML = `
            <div class="de-drill-view">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.mention}</div>
                    <div class="de-drill-title">
                        <h2>Responsibility Statements Breakdown</h2>
                        <p>${formatNumber(data.totalResponsibilities)} total statements across ${data.totalRoles} roles</p>
                    </div>
                </div>

                <div class="de-explanation-box">
                    <h4>What is a "Responsibility Statement"?</h4>
                    <p>A responsibility statement is a sentence where a role is assigned work.
                       These are identified by action verbs like:</p>
                    <div class="de-action-examples">
                        <span class="de-action-example"><strong>"shall"</strong> - mandatory action</span>
                        <span class="de-action-example"><strong>"must"</strong> - required action</span>
                        <span class="de-action-example"><strong>"is responsible for"</strong> - ownership</span>
                        <span class="de-action-example"><strong>"will"</strong> - planned action</span>
                    </div>
                    <p class="de-note">Note: This count differs from "text occurrences" which counts
                       every time a role name appears, regardless of context.</p>
                </div>

                <div class="de-viz-grid">
                    <div class="de-viz-card de-viz-large">
                        <div class="de-viz-header">
                            <h3>Distribution by Category</h3>
                        </div>
                        <div class="de-viz-body">
                            <div class="de-chart-container">
                                <canvas id="de-mentions-cat-chart" height="300"></canvas>
                                <div class="de-chart-center-text">
                                    <div class="de-chart-center-value">${formatNumber(data.totalResponsibilities)}</div>
                                    <div class="de-chart-center-label">Statements</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>Top 10 by Statements</h3>
                        </div>
                        <div class="de-viz-body de-scrollable">
                            ${data.topRoles.map((role, i) => `
                                <div class="de-role-item de-clickable" data-role="${escapeHtml(role.name)}">
                                    <div class="de-role-rank">${i + 1}</div>
                                    <div class="de-role-info">
                                        <div class="de-role-name">${escapeHtml(role.name)}</div>
                                    </div>
                                    <div class="de-role-freq">
                                        <div class="de-role-freq-value">${role.frequency}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Render chart
        setTimeout(() => {
            const categories = Object.entries(data.categoryBreakdown);
            createDonutChart('de-mentions-cat-chart', {
                labels: categories.map(([name]) => name),
                values: categories.map(([, data]) => data.mentions)
            }, {
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const category = categories[index][0];
                        drillInto('category', category, data.categoryBreakdown[category]);
                    }
                }
            });

            content.querySelectorAll('.de-role-item').forEach(item => {
                item.addEventListener('click', () => {
                    const roleName = item.dataset.role;
                    const roleEntry = data.topRoles.find(r => r.name === roleName);
                    // Merge the nested 'data' properties into roleData for drill-down
                    const roleData = roleEntry ? { ...roleEntry, ...(roleEntry.data || {}) } : roleEntry;
                    drillInto('role', roleName, roleData);
                });
            });
        }, 50);
    }

    async function renderActionDrill(actionName, actionData) {
        const content = State.modal.querySelector('.de-content');

        // Ensure actionData has required properties
        const safeActionData = actionData || {};
        const count = safeActionData.count || 0;
        const roles = safeActionData.roles || [];

        content.innerHTML = `
            <div class="de-drill-view">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.action}</div>
                    <div class="de-drill-title">
                        <h2>Action: "${escapeHtml(actionName)}"</h2>
                        <p>${formatNumber(count)} occurrences across ${roles.length} roles</p>
                    </div>
                </div>

                <div class="de-explanation-box">
                    <h4>What does "${escapeHtml(actionName)}" mean?</h4>
                    <p>${getActionDescription(actionName)}</p>
                </div>

                <div class="de-viz-card de-viz-full">
                    <div class="de-viz-header">
                        <h3>Roles with this Action</h3>
                        <span class="de-viz-count">${roles.length} roles</span>
                    </div>
                    <div class="de-viz-body de-scrollable de-role-grid">
                        ${roles.length > 0 ? roles.map(role => `
                            <div class="de-role-card de-clickable" data-role="${escapeHtml(role.name)}">
                                <div class="de-role-card-name">${escapeHtml(role.name)}</div>
                                <div class="de-role-card-stats">
                                    <span>${role.count || 1} times</span>
                                </div>
                            </div>
                        `).join('') : '<div class="de-empty">No roles found with this action type</div>'}
                    </div>
                </div>
            </div>
        `;

        content.querySelectorAll('.de-role-card').forEach(card => {
            card.addEventListener('click', () => {
                const roleName = card.dataset.role;
                // Pass action info so the role view knows which action we came from
                drillInto('role', roleName, { name: roleName, fromAction: actionName });
            });
        });
    }

    function getActionDescription(action) {
        const descriptions = {
            'shall': 'Indicates a mandatory requirement. The role MUST perform this action.',
            'must': 'Indicates a strict requirement. The role is obligated to perform this action.',
            'will': 'Indicates a planned or expected action. The role is expected to perform this.',
            'is responsible': 'Indicates ownership of a task or outcome.',
            'may': 'Indicates optional or discretionary action.',
            'should': 'Indicates a recommendation or best practice.'
        };

        for (const [key, desc] of Object.entries(descriptions)) {
            if (action.toLowerCase().includes(key)) return desc;
        }
        return 'This action type indicates a specific type of responsibility assignment.';
    }

    function highlightRoleInContext(text, roleName) {
        if (!text || !roleName) return escapeHtml(text);
        const regex = new RegExp(`(${escapeRegExp(roleName)})`, 'gi');
        return escapeHtml(text).replace(regex, '<mark class="de-highlight">$1</mark>');
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // ============================================================
    // DOCUMENTS LANDING PAGE
    // ============================================================

    async function renderDocumentsLanding(data) {
        const content = State.modal.querySelector('.de-content');

        // Fetch document data
        const documents = await fetchDocumentData();
        const matrixData = await fetchRoleMatrixData();

        if (!documents || documents.length === 0) {
            content.innerHTML = `
                <div class="de-empty-state">
                    <div class="de-empty-icon">📄</div>
                    <h2>No Documents Analyzed</h2>
                    <p>No documents have been scanned yet. Please analyze a document first.</p>
                </div>
            `;
            return;
        }

        // Process document statistics
        const totalDocs = documents.length;
        const uniqueDocs = [...new Set(documents.map(d => d.filename))].length;
        const totalRolesAcrossDocs = documents.reduce((sum, d) => sum + (d.role_count || 0), 0);
        const avgRolesPerDoc = totalDocs > 0 ? (totalRolesAcrossDocs / totalDocs).toFixed(1) : 0;
        const totalIssues = documents.reduce((sum, d) => sum + (d.issue_count || 0), 0);

        // Calculate grade distribution
        const gradeDistribution = {};
        documents.forEach(doc => {
            const grade = doc.grade || 'N/A';
            gradeDistribution[grade] = (gradeDistribution[grade] || 0) + 1;
        });

        // Get most recent scans (unique by filename, most recent first)
        const seenFiles = new Set();
        const recentDocs = documents.filter(doc => {
            if (seenFiles.has(doc.filename)) return false;
            seenFiles.add(doc.filename);
            return true;
        }).slice(0, 10);

        // Calculate roles per document for chart
        const rolesPerDoc = recentDocs.map(d => ({
            name: truncate(d.filename.replace(/\.[^/.]+$/, ''), 25),
            value: d.role_count || 0,
            fullName: d.filename,
            docId: d.document_id
        }));

        content.innerHTML = `
            <div class="de-drill-view de-documents-landing">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.document}</div>
                    <div class="de-drill-title">
                        <h2>Documents Analyzed</h2>
                        <p class="de-drill-subtitle">Complete overview of all scanned documents and their role coverage</p>
                    </div>
                </div>

                <!-- Hero Stats -->
                <div class="de-hero-stats">
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">📄</div>
                        <div class="de-hero-value">${uniqueDocs}</div>
                        <div class="de-hero-label">Unique Documents</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">🔄</div>
                        <div class="de-hero-value">${totalDocs}</div>
                        <div class="de-hero-label">Total Scans</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">${CONFIG.icons.role}</div>
                        <div class="de-hero-value">${totalRolesAcrossDocs}</div>
                        <div class="de-hero-label">Roles Detected</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">${CONFIG.icons.chart}</div>
                        <div class="de-hero-value">${avgRolesPerDoc}</div>
                        <div class="de-hero-label">Avg Roles/Doc</div>
                    </div>
                </div>

                <div class="de-viz-grid de-drill-grid">
                    <!-- Grade Distribution Chart -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>📊 Quality Grade Distribution</h3>
                            <span class="de-viz-subtitle">Document quality scores</span>
                        </div>
                        <div class="de-viz-body">
                            <div class="de-chart-container">
                                <canvas id="de-grade-chart" height="200"></canvas>
                                <div class="de-chart-center-text">
                                    <div class="de-chart-center-value">${uniqueDocs}</div>
                                    <div class="de-chart-center-label">Documents</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Roles Per Document Chart -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.role} Roles Per Document</h3>
                            <span class="de-viz-subtitle">Role density across documents</span>
                        </div>
                        <div class="de-viz-body">
                            <div class="de-chart-container">
                                <canvas id="de-roles-per-doc-chart" height="200"></canvas>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Documents List -->
                    <div class="de-viz-card de-viz-wide">
                        <div class="de-viz-header">
                            <h3>📋 Document Details</h3>
                            <span class="de-viz-subtitle">${uniqueDocs} unique documents analyzed</span>
                        </div>
                        <div class="de-viz-body de-scrollable">
                            <table class="de-docs-table">
                                <thead>
                                    <tr>
                                        <th>Document</th>
                                        <th class="de-num-cell">Roles</th>
                                        <th class="de-num-cell">Issues</th>
                                        <th class="de-num-cell">Score</th>
                                        <th>Grade</th>
                                        <th>Last Scan</th>
                                        <th></th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${recentDocs.map(doc => `
                                        <tr class="de-clickable" data-doc-id="${doc.document_id}" data-filename="${escapeHtml(doc.filename)}">
                                            <td class="de-doc-name-cell" title="${escapeHtml(doc.filename)}">
                                                <span class="de-doc-icon">📄</span>
                                                ${escapeHtml(truncate(doc.filename, 40))}
                                            </td>
                                            <td class="de-num-cell">${doc.role_count || 0}</td>
                                            <td class="de-num-cell">${doc.issue_count || 0}</td>
                                            <td class="de-num-cell">${doc.score || 'N/A'}</td>
                                            <td>
                                                <span class="de-grade-badge de-grade-${(doc.grade || 'na').toLowerCase()}">${doc.grade || 'N/A'}</span>
                                            </td>
                                            <td class="de-date-cell">${formatDate(doc.scan_time)}</td>
                                            <td class="de-arrow-cell">${CONFIG.icons.forward}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Document-Role Coverage Matrix Preview -->
                    ${matrixData ? `
                        <div class="de-viz-card de-viz-wide">
                            <div class="de-viz-header">
                                <h3>🔗 Role Coverage Matrix</h3>
                                <span class="de-viz-subtitle">Which roles appear in which documents</span>
                            </div>
                            <div class="de-viz-body">
                                <div class="de-matrix-preview">
                                    ${renderMatrixPreview(matrixData)}
                                </div>
                            </div>
                        </div>
                    ` : ''}
                </div>

                <!-- Quick Stats Footer -->
                <div class="de-quick-stats">
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Total Issues Found:</span>
                        <span class="de-quick-value">${totalIssues}</span>
                    </div>
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Best Grade:</span>
                        <span class="de-quick-value">${getBestGrade(gradeDistribution)}</span>
                    </div>
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Most Common Grade:</span>
                        <span class="de-quick-value">${getMostCommonGrade(gradeDistribution)}</span>
                    </div>
                </div>
            </div>
        `;

        // Render charts
        setTimeout(() => {
            renderGradeChart(gradeDistribution);
            renderRolesPerDocChart(rolesPerDoc);
            attachDocumentListeners();
        }, 50);
    }

    function formatDate(dateStr) {
        if (!dateStr) return 'N/A';
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        } catch (e) {
            return dateStr;
        }
    }

    function getBestGrade(distribution) {
        const grades = ['A', 'B', 'C', 'D', 'F'];
        for (const grade of grades) {
            if (distribution[grade] > 0) return grade;
        }
        return 'N/A';
    }

    function getMostCommonGrade(distribution) {
        let maxCount = 0;
        let mostCommon = 'N/A';
        for (const [grade, count] of Object.entries(distribution)) {
            if (count > maxCount) {
                maxCount = count;
                mostCommon = grade;
            }
        }
        return mostCommon;
    }

    function renderMatrixPreview(matrixData) {
        const docs = Object.entries(matrixData.documents || {}).slice(0, 5);
        const roles = Object.entries(matrixData.roles || {}).slice(0, 8);
        const connections = matrixData.connections || {};

        if (docs.length === 0 || roles.length === 0) {
            return '<div class="de-empty">No coverage data available</div>';
        }

        let html = '<div class="de-matrix-grid">';

        // Header row with document names
        html += '<div class="de-matrix-header-row">';
        html += '<div class="de-matrix-corner"></div>';
        docs.forEach(([docId, filename]) => {
            html += `<div class="de-matrix-doc-header" title="${escapeHtml(filename)}">${escapeHtml(truncate(filename.replace(/\.[^/.]+$/, ''), 12))}</div>`;
        });
        html += '</div>';

        // Role rows
        roles.forEach(([roleId, roleName]) => {
            html += '<div class="de-matrix-row">';
            html += `<div class="de-matrix-role-header" title="${escapeHtml(roleName)}">${escapeHtml(truncate(roleName, 15))}</div>`;
            docs.forEach(([docId]) => {
                const hasConnection = connections[roleId] && connections[roleId][docId];
                const count = hasConnection ? connections[roleId][docId] : 0;
                html += `<div class="de-matrix-cell ${hasConnection ? 'de-has-connection' : ''}" title="${count} mentions">${count > 0 ? count : ''}</div>`;
            });
            html += '</div>';
        });

        html += '</div>';

        if (Object.keys(matrixData.roles).length > 8 || Object.keys(matrixData.documents).length > 5) {
            html += `<div class="de-matrix-more">Showing ${Math.min(8, roles.length)} of ${Object.keys(matrixData.roles).length} roles × ${Math.min(5, docs.length)} of ${Object.keys(matrixData.documents).length} documents</div>`;
        }

        return html;
    }

    function renderGradeChart(distribution) {
        const grades = ['A', 'B', 'C', 'D', 'F'];
        const gradeColors = {
            'A': '#22c55e',
            'B': '#84cc16',
            'C': '#eab308',
            'D': '#f97316',
            'F': '#ef4444'
        };

        const labels = grades.filter(g => distribution[g] > 0);
        const values = labels.map(g => distribution[g]);
        const colors = labels.map(g => gradeColors[g]);

        if (labels.length === 0) {
            const container = document.getElementById('de-grade-chart');
            if (container) {
                container.parentElement.innerHTML = '<div class="de-empty">No grade data available</div>';
            }
            return;
        }

        createDonutChart('de-grade-chart', { labels, values }, { colors });
    }

    function renderRolesPerDocChart(rolesPerDoc) {
        if (!rolesPerDoc || rolesPerDoc.length === 0) {
            const container = document.getElementById('de-roles-per-doc-chart');
            if (container) {
                container.parentElement.innerHTML = '<div class="de-empty">No document data available</div>';
            }
            return;
        }

        createBarChart('de-roles-per-doc-chart', {
            labels: rolesPerDoc.map(d => d.name),
            values: rolesPerDoc.map(d => d.value),
            label: 'Roles'
        }, {
            horizontal: true,
            onClick: (event, elements) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const doc = rolesPerDoc[index];
                    drillInto('document', doc.fullName, { docId: doc.docId, filename: doc.fullName });
                }
            }
        });
    }

    function attachDocumentListeners() {
        // Document row clicks
        State.modal.querySelectorAll('.de-docs-table tr.de-clickable').forEach(row => {
            row.addEventListener('click', () => {
                const docId = row.dataset.docId;
                const filename = row.dataset.filename;
                drillInto('document', filename, { docId, filename });
            });
        });
    }

    // ============================================================
    // SINGLE DOCUMENT DRILL-DOWN
    // ============================================================

    async function renderDocumentDrill(docName, docData) {
        const content = State.modal.querySelector('.de-content');
        const docId = docData?.docId;

        // v4.0.3: Adjudication lookup
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        // Fetch roles for this specific document
        let docRoles = [];
        if (docId) {
            try {
                const response = await fetch(`/api/scan-history/document/${docId}/roles`);
                const result = await response.json();
                if (result.success) {
                    docRoles = result.data || [];
                }
            } catch (e) {
                log('Failed to fetch document roles: ' + e, 'error');
            }
        }

        // Also try to get document details from scan history
        const documents = await fetchDocumentData();
        const docDetails = documents.find(d => d.filename === docName || d.document_id == docId) || {};

        // Process role categories
        const categoryBreakdown = {};
        docRoles.forEach(role => {
            const cat = role.category || 'Other';
            if (!categoryBreakdown[cat]) {
                categoryBreakdown[cat] = { count: 0, roles: [] };
            }
            categoryBreakdown[cat].count++;
            categoryBreakdown[cat].roles.push(role);
        });

        // Count RACI types
        const raciCounts = { R: 0, A: 0, C: 0, I: 0 };
        docRoles.forEach(role => {
            if (role.R) raciCounts.R += role.R;
            if (role.A) raciCounts.A += role.A;
            if (role.C) raciCounts.C += role.C;
            if (role.I) raciCounts.I += role.I;
        });

        content.innerHTML = `
            <div class="de-drill-view de-document-drill">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.document}</div>
                    <div class="de-drill-title">
                        <h2>${escapeHtml(truncate(docName, 60))}</h2>
                        <p class="de-drill-subtitle">Document analysis details</p>
                    </div>
                </div>

                <div class="de-drill-stats">
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${docRoles.length}</div>
                        <div class="de-mini-label">Roles Found</div>
                    </div>
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${docDetails.issue_count || 0}</div>
                        <div class="de-mini-label">Issues</div>
                    </div>
                    <div class="de-mini-stat">
                        <div class="de-mini-value">${docDetails.score || 'N/A'}</div>
                        <div class="de-mini-label">Score</div>
                    </div>
                    <div class="de-mini-stat">
                        <div class="de-mini-value de-grade-badge de-grade-${(docDetails.grade || 'na').toLowerCase()}">${docDetails.grade || 'N/A'}</div>
                        <div class="de-mini-label">Grade</div>
                    </div>
                </div>

                <div class="de-viz-grid de-drill-grid">
                    <!-- Role Categories in this Document -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.category} Role Categories</h3>
                        </div>
                        <div class="de-viz-body">
                            ${Object.keys(categoryBreakdown).length > 0 ? `
                                <div class="de-chart-container">
                                    <canvas id="de-doc-category-chart" height="200"></canvas>
                                    <div class="de-chart-center-text">
                                        <div class="de-chart-center-value">${docRoles.length}</div>
                                        <div class="de-chart-center-label">Roles</div>
                                    </div>
                                </div>
                            ` : '<div class="de-empty">No category data</div>'}
                        </div>
                    </div>

                    <!-- RACI Distribution -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.action} RACI Distribution</h3>
                        </div>
                        <div class="de-viz-body">
                            <div class="de-action-tags de-doc-raci">
                                ${['R', 'A', 'C', 'I'].map(type => `
                                    <div class="de-action-tag de-raci-${type.toLowerCase()}">
                                        <span class="de-action-name">${type}</span>
                                        <span class="de-action-count">${raciCounts[type]}</span>
                                    </div>
                                `).join('')}
                            </div>
                            <div class="de-raci-legend">
                                <div>R = Responsible</div>
                                <div>A = Accountable</div>
                                <div>C = Consulted</div>
                                <div>I = Informed</div>
                            </div>
                        </div>
                    </div>

                    <!-- Roles List -->
                    <div class="de-viz-card de-viz-wide">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.role} Roles in Document</h3>
                            <span class="de-viz-count">${docRoles.length} roles</span>
                        </div>
                        <div class="de-viz-body de-scrollable">
                            ${docRoles.length > 0 ? `
                                <table class="de-roles-table">
                                    <thead>
                                        <tr>
                                            <th>Role</th>
                                            <th>Category</th>
                                            <th class="de-num-cell">Mentions</th>
                                            <th class="de-num-cell">Responsibilities</th>
                                            <th></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${docRoles.map(role => `
                                            <tr class="de-clickable" data-role="${escapeHtml(role.role_name || role.name)}">
                                                <td class="de-role-name-cell">${escapeHtml(role.role_name || role.name)}${adjLookup ? adjLookup.getBadge(role.role_name || role.name, { compact: true, size: 'sm' }) : ''}</td>
                                                <td><span class="de-category-tag">${escapeHtml(role.category || 'Other')}</span></td>
                                                <td class="de-num-cell">${role.mentions || role.mention_count || 0}</td>
                                                <td class="de-num-cell">${role.responsibilities || role.responsibility_count || 0}</td>
                                                <td class="de-arrow-cell">${CONFIG.icons.forward}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            ` : '<div class="de-empty">No roles detected in this document</div>'}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Render charts and attach listeners
        setTimeout(() => {
            if (Object.keys(categoryBreakdown).length > 0) {
                const categories = Object.entries(categoryBreakdown);
                createDonutChart('de-doc-category-chart', {
                    labels: categories.map(([name]) => name),
                    values: categories.map(([, data]) => data.count)
                });
            }

            // Attach role click handlers
            State.modal.querySelectorAll('.de-roles-table tr.de-clickable').forEach(row => {
                row.addEventListener('click', () => {
                    const roleName = row.dataset.role;
                    drillInto('role', roleName, { name: roleName });
                });
            });
        }, 50);
    }

    // ============================================================
    // ROLE INTERACTIONS LANDING PAGE
    // ============================================================

    async function renderInteractionsLanding(data) {
        const content = State.modal.querySelector('.de-content');

        // v4.0.3: Adjudication lookup
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        // Fetch graph and matrix data
        const graphData = await fetchRoleGraphData();
        const matrixData = await fetchRoleMatrixData();
        const raciData = await fetchRaciData();

        if (!graphData && !matrixData) {
            content.innerHTML = `
                <div class="de-empty-state">
                    <div class="de-empty-icon">🔗</div>
                    <h2>No Interaction Data</h2>
                    <p>Role interaction data is not available. Please analyze documents first.</p>
                </div>
            `;
            return;
        }

        // Process interaction statistics
        const nodes = graphData?.nodes || [];
        const links = graphData?.links || [];
        const roleNodes = nodes.filter(n => n.type === 'role');
        const docNodes = nodes.filter(n => n.type === 'document');

        // Calculate connectivity metrics
        const roleLinkCounts = {};
        links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            roleLinkCounts[sourceId] = (roleLinkCounts[sourceId] || 0) + (link.weight || 1);
            roleLinkCounts[targetId] = (roleLinkCounts[targetId] || 0) + (link.weight || 1);
        });

        // Find most connected roles
        const topConnected = roleNodes
            .map(node => ({ ...node, connections: roleLinkCounts[node.id] || 0 }))
            .sort((a, b) => b.connections - a.connections)
            .slice(0, 10);

        // Find roles that appear together most often (co-occurrence)
        const coOccurrence = calculateCoOccurrence(matrixData);

        // RACI summary - backend returns type_distribution: {R, A, C, I}
        const raciSummary = raciData?.summary || {};
        const raciDist = raciSummary.type_distribution || {};
        const raciTotal = (raciDist.R || 0) + (raciDist.A || 0) + (raciDist.C || 0) + (raciDist.I || 0);
        const raciRolesWithResp = Object.values(raciData?.roles || {}).filter(r => (r.total || 0) > 0).length;

        content.innerHTML = `
            <div class="de-drill-view de-interactions-landing">
                <div class="de-drill-header">
                    <div class="de-drill-icon">🔗</div>
                    <div class="de-drill-title">
                        <h2>Role Interactions</h2>
                        <p class="de-drill-subtitle">Analyze how roles relate to each other across documents</p>
                    </div>
                </div>

                <!-- Hero Stats -->
                <div class="de-hero-stats">
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">${CONFIG.icons.role}</div>
                        <div class="de-hero-value">${roleNodes.length}</div>
                        <div class="de-hero-label">Roles Tracked</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">📄</div>
                        <div class="de-hero-value">${docNodes.length}</div>
                        <div class="de-hero-label">Documents</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">🔗</div>
                        <div class="de-hero-value">${links.length}</div>
                        <div class="de-hero-label">Connections</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">${CONFIG.icons.chart}</div>
                        <div class="de-hero-value">${roleNodes.length > 0 ? (links.length / roleNodes.length).toFixed(1) : 0}</div>
                        <div class="de-hero-label">Avg Links/Role</div>
                    </div>
                </div>

                <div class="de-viz-grid de-drill-grid">
                    <!-- RACI Overview -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.action} RACI Summary</h3>
                            <span class="de-viz-subtitle">Responsibility distribution</span>
                        </div>
                        <div class="de-viz-body">
                            <div class="de-raci-overview">
                                <div class="de-raci-stat de-raci-r">
                                    <div class="de-raci-letter">R</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${raciDist.R || 0}</div>
                                        <div class="de-raci-label">Responsible</div>
                                    </div>
                                </div>
                                <div class="de-raci-stat de-raci-a">
                                    <div class="de-raci-letter">A</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${raciDist.A || 0}</div>
                                        <div class="de-raci-label">Accountable</div>
                                    </div>
                                </div>
                                <div class="de-raci-stat de-raci-c">
                                    <div class="de-raci-letter">C</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${raciDist.C || 0}</div>
                                        <div class="de-raci-label">Consulted</div>
                                    </div>
                                </div>
                                <div class="de-raci-stat de-raci-i">
                                    <div class="de-raci-letter">I</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${raciDist.I || 0}</div>
                                        <div class="de-raci-label">Informed</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Most Connected Roles -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>🌟 Most Connected Roles</h3>
                            <span class="de-viz-subtitle">Roles with most document appearances</span>
                        </div>
                        <div class="de-viz-body de-scrollable">
                            <div class="de-connected-roles">
                                ${topConnected.map((role, i) => {
                                    const rName = role.label || role.original_name || role.name || role.id;
                                    return `
                                    <div class="de-connected-item de-clickable" data-role="${escapeHtml(rName)}">
                                        <div class="de-connected-rank">${i + 1}</div>
                                        <div class="de-connected-info">
                                            <div class="de-connected-name">${escapeHtml(rName)}${adjLookup ? adjLookup.getBadge(rName, { compact: true, size: 'sm' }) : ''}</div>
                                            <div class="de-connected-meta">${role.connections} connections</div>
                                        </div>
                                        <div class="de-connected-bar">
                                            <div class="de-connected-fill" style="width: ${(role.connections / (topConnected[0]?.connections || 1)) * 100}%"></div>
                                        </div>
                                    </div>`;
                                }).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- Role Co-occurrence -->
                    <div class="de-viz-card de-viz-wide">
                        <div class="de-viz-header">
                            <h3>🤝 Common Role Pairs</h3>
                            <span class="de-viz-subtitle">Roles that frequently appear together in documents</span>
                        </div>
                        <div class="de-viz-body">
                            ${coOccurrence.length > 0 ? `
                                <div class="de-cooccurrence-grid">
                                    ${coOccurrence.slice(0, 8).map(pair => `
                                        <div class="de-cooccurrence-pair">
                                            <div class="de-pair-roles">
                                                <span class="de-pair-role de-clickable" data-role="${escapeHtml(pair.role1)}">${escapeHtml(truncate(pair.role1, 20))}</span>
                                                <span class="de-pair-connector">↔</span>
                                                <span class="de-pair-role de-clickable" data-role="${escapeHtml(pair.role2)}">${escapeHtml(truncate(pair.role2, 20))}</span>
                                            </div>
                                            <div class="de-pair-count">${pair.count} docs</div>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : '<div class="de-empty">Analyze more documents to see role co-occurrence patterns</div>'}
                        </div>
                    </div>

                    <!-- Document Coverage Heatmap -->
                    <div class="de-viz-card de-viz-wide">
                        <div class="de-viz-header">
                            <h3>📊 Role-Document Coverage</h3>
                            <span class="de-viz-subtitle">Visual matrix of role appearances across documents</span>
                        </div>
                        <div class="de-viz-body">
                            ${matrixData ? renderInteractionMatrix(matrixData) : '<div class="de-empty">No matrix data available</div>'}
                        </div>
                    </div>
                </div>

                <!-- Quick Stats Footer -->
                <div class="de-quick-stats">
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Total Responsibilities:</span>
                        <span class="de-quick-value">${formatNumber(raciTotal)}</span>
                    </div>
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Primary Type:</span>
                        <span class="de-quick-value">${getMostCommonRaciType(raciSummary)}</span>
                    </div>
                    <div class="de-quick-stat">
                        <span class="de-quick-label">Roles with Responsibilities:</span>
                        <span class="de-quick-value">${raciRolesWithResp}</span>
                    </div>
                </div>
            </div>
        `;

        // Attach listeners
        setTimeout(() => {
            attachInteractionListeners();
        }, 50);
    }

    function calculateCoOccurrence(matrixData) {
        if (!matrixData || !matrixData.connections) return [];

        const roleIds = Object.keys(matrixData.connections);
        const rolePairs = [];

        // For each pair of roles, count how many documents they share
        for (let i = 0; i < roleIds.length; i++) {
            for (let j = i + 1; j < roleIds.length; j++) {
                const role1Id = roleIds[i];
                const role2Id = roleIds[j];
                const role1Docs = new Set(Object.keys(matrixData.connections[role1Id] || {}));
                const role2Docs = new Set(Object.keys(matrixData.connections[role2Id] || {}));

                // Find intersection
                const sharedDocs = [...role1Docs].filter(d => role2Docs.has(d));

                if (sharedDocs.length > 0) {
                    rolePairs.push({
                        role1: matrixData.roles[role1Id],
                        role2: matrixData.roles[role2Id],
                        count: sharedDocs.length
                    });
                }
            }
        }

        return rolePairs.sort((a, b) => b.count - a.count);
    }

    function renderInteractionMatrix(matrixData) {
        const docs = Object.entries(matrixData.documents || {}).slice(0, 8);
        const roles = Object.entries(matrixData.roles || {}).slice(0, 12);
        const connections = matrixData.connections || {};

        if (docs.length === 0 || roles.length === 0) {
            return '<div class="de-empty">No coverage data available</div>';
        }

        let html = '<div class="de-interaction-matrix">';

        // Header row with document names
        html += '<div class="de-matrix-header-row">';
        html += '<div class="de-matrix-corner"></div>';
        docs.forEach(([docId, filename]) => {
            html += `<div class="de-matrix-doc-header" title="${escapeHtml(filename)}">${escapeHtml(truncate(filename.replace(/\.[^/.]+$/, ''), 10))}</div>`;
        });
        html += '</div>';

        // Role rows with colored cells based on count
        roles.forEach(([roleId, roleName]) => {
            html += '<div class="de-matrix-row">';
            html += `<div class="de-matrix-role-header de-clickable" data-role="${escapeHtml(roleName)}" title="${escapeHtml(roleName)}">${escapeHtml(truncate(roleName, 15))}</div>`;
            docs.forEach(([docId]) => {
                const count = connections[roleId]?.[docId] || 0;
                const intensity = Math.min(count / 5, 1); // Normalize to 0-1
                const bgColor = count > 0 ? `rgba(74, 144, 217, ${0.2 + intensity * 0.6})` : '';
                html += `<div class="de-matrix-cell ${count > 0 ? 'de-has-connection' : ''}" style="${bgColor ? 'background:' + bgColor : ''}" title="${count} mentions">${count > 0 ? count : ''}</div>`;
            });
            html += '</div>';
        });

        html += '</div>';

        const totalRoles = Object.keys(matrixData.roles).length;
        const totalDocs = Object.keys(matrixData.documents).length;
        if (totalRoles > 12 || totalDocs > 8) {
            html += `<div class="de-matrix-more">Showing top ${Math.min(12, roles.length)} roles × ${Math.min(8, docs.length)} documents (${totalRoles} total roles, ${totalDocs} total documents)</div>`;
        }

        return html;
    }

    function getMostCommonRaciType(summary) {
        const dist = summary.type_distribution || {};
        const types = [
            { type: 'R (Responsible)', count: dist.R || 0 },
            { type: 'A (Accountable)', count: dist.A || 0 },
            { type: 'C (Consulted)', count: dist.C || 0 },
            { type: 'I (Informed)', count: dist.I || 0 }
        ];
        types.sort((a, b) => b.count - a.count);
        return types[0].count > 0 ? types[0].type : 'N/A';
    }

    async function renderRoleConnectionsDrill(roleId, data) {
        const content = State.modal.querySelector('.de-content');
        const roleName = data.name || roleId;

        // v4.0.3: Adjudication lookup
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        // Fetch graph and matrix data
        const graphData = await fetchRoleGraphData();
        const matrixData = await fetchRoleMatrixData();

        if (!graphData && !matrixData) {
            content.innerHTML = `
                <div class="de-empty-state">
                    <div class="de-empty-icon">🔗</div>
                    <h2>No Connection Data</h2>
                    <p>Connection data is not available for this role.</p>
                </div>
            `;
            return;
        }

        const nodes = graphData?.nodes || [];
        const links = graphData?.links || [];
        const roleNodes = nodes.filter(n => n.type === 'role');
        const docNodes = nodes.filter(n => n.type === 'document');

        // Find this role's node
        const thisRole = roleNodes.find(n =>
            (n.label || n.original_name || n.name || n.id) === roleName
        );

        if (!thisRole) {
            content.innerHTML = `
                <div class="de-empty-state">
                    <div class="de-empty-icon">🔍</div>
                    <h2>Role Not Found</h2>
                    <p>Could not find connection data for "${escapeHtml(roleName)}".</p>
                </div>
            `;
            return;
        }

        // Find all documents this role connects to
        const roleDocLinks = links.filter(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            return sourceId === thisRole.id || targetId === thisRole.id;
        });

        // Get connected documents
        const connectedDocIds = new Set();
        roleDocLinks.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            const otherId = sourceId === thisRole.id ? targetId : sourceId;
            const otherNode = nodes.find(n => n.id === otherId);
            if (otherNode && otherNode.type === 'document') {
                connectedDocIds.add(otherId);
            }
        });

        // Find all roles that share documents with this role
        const connectedRoles = [];
        roleNodes.forEach(otherRole => {
            if (otherRole.id === thisRole.id) return;

            // Get documents this other role connects to
            const otherRoleDocLinks = links.filter(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return sourceId === otherRole.id || targetId === otherRole.id;
            });

            const otherDocIds = new Set();
            otherRoleDocLinks.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                const otherId = sourceId === otherRole.id ? targetId : sourceId;
                const otherNode = nodes.find(n => n.id === otherId);
                if (otherNode && otherNode.type === 'document') {
                    otherDocIds.add(otherId);
                }
            });

            // Find shared documents
            const sharedDocs = [...connectedDocIds].filter(docId => otherDocIds.has(docId));
            if (sharedDocs.length > 0) {
                // Get document names
                const sharedDocNames = sharedDocs.map(docId => {
                    const docNode = docNodes.find(d => d.id === docId);
                    return docNode ? (docNode.label || docNode.original_name || docNode.name || docId) : docId;
                });

                connectedRoles.push({
                    id: otherRole.id,
                    name: otherRole.label || otherRole.original_name || otherRole.name || otherRole.id,
                    sharedCount: sharedDocs.length,
                    sharedDocs: sharedDocNames
                });
            }
        });

        // Sort by shared count
        connectedRoles.sort((a, b) => b.sharedCount - a.sharedCount);

        // Get RACI data for connection types if available
        const raciData = await fetchRaciData();
        const roleRaciInfo = {};

        // RACI API returns roles as an object with role names as keys
        const raciRoles = raciData?.roles || {};
        Object.entries(raciRoles).forEach(([rName, roleData]) => {
            roleRaciInfo[rName.toLowerCase()] = {
                R: roleData.R || 0,
                A: roleData.A || 0,
                C: roleData.C || 0,
                I: roleData.I || 0
            };
        });

        // Get this role's RACI profile (case-insensitive lookup)
        const thisRoleRaci = roleRaciInfo[roleName.toLowerCase()] || { R: 0, A: 0, C: 0, I: 0 };
        const totalRaci = thisRoleRaci.R + thisRoleRaci.A + thisRoleRaci.C + thisRoleRaci.I;

        content.innerHTML = `
            <div class="de-drill-view de-role-connections">
                <div class="de-drill-header">
                    <div class="de-drill-icon">${CONFIG.icons.role}</div>
                    <div class="de-drill-title">
                        <h2>${escapeHtml(roleName)}${adjLookup ? adjLookup.getBadge(roleName) : ''}</h2>
                        <p class="de-drill-subtitle">Role connections and relationships</p>
                    </div>
                </div>

                <!-- Hero Stats -->
                <div class="de-hero-stats">
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">🔗</div>
                        <div class="de-hero-value">${connectedRoles.length}</div>
                        <div class="de-hero-label">Connected Roles</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">📄</div>
                        <div class="de-hero-value">${connectedDocIds.size}</div>
                        <div class="de-hero-label">Documents</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">📊</div>
                        <div class="de-hero-value">${roleDocLinks.length}</div>
                        <div class="de-hero-label">Total Links</div>
                    </div>
                    <div class="de-hero-stat">
                        <div class="de-hero-icon">${CONFIG.icons.action}</div>
                        <div class="de-hero-value">${totalRaci}</div>
                        <div class="de-hero-label">RACI Entries</div>
                    </div>
                </div>

                <div class="de-viz-grid de-drill-grid">
                    <!-- This Role's RACI Profile -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>${CONFIG.icons.action} RACI Profile</h3>
                            <span class="de-viz-subtitle">How this role participates</span>
                        </div>
                        <div class="de-viz-body">
                            <div class="de-raci-overview">
                                <div class="de-raci-stat de-raci-r">
                                    <div class="de-raci-letter">R</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${thisRoleRaci.R}</div>
                                        <div class="de-raci-label">Responsible</div>
                                    </div>
                                </div>
                                <div class="de-raci-stat de-raci-a">
                                    <div class="de-raci-letter">A</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${thisRoleRaci.A}</div>
                                        <div class="de-raci-label">Accountable</div>
                                    </div>
                                </div>
                                <div class="de-raci-stat de-raci-c">
                                    <div class="de-raci-letter">C</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${thisRoleRaci.C}</div>
                                        <div class="de-raci-label">Consulted</div>
                                    </div>
                                </div>
                                <div class="de-raci-stat de-raci-i">
                                    <div class="de-raci-letter">I</div>
                                    <div class="de-raci-info">
                                        <div class="de-raci-count">${thisRoleRaci.I}</div>
                                        <div class="de-raci-label">Informed</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Connection Strength Summary -->
                    <div class="de-viz-card">
                        <div class="de-viz-header">
                            <h3>📊 Connection Strength</h3>
                            <span class="de-viz-subtitle">Top connections by shared documents</span>
                        </div>
                        <div class="de-viz-body">
                            <div class="de-connection-bars">
                                ${connectedRoles.slice(0, 5).map(role => `
                                    <div class="de-connection-bar-item">
                                        <div class="de-connection-bar-label">${escapeHtml(role.name)}${adjLookup ? adjLookup.getBadge(role.name, { compact: true, size: 'sm' }) : ''}</div>
                                        <div class="de-connection-bar-track">
                                            <div class="de-connection-bar-fill" style="width: ${(role.sharedCount / (connectedRoles[0]?.sharedCount || 1)) * 100}%"></div>
                                        </div>
                                        <div class="de-connection-bar-value">${role.sharedCount}</div>
                                    </div>
                                `).join('') || '<div class="de-empty">No connections found</div>'}
                            </div>
                        </div>
                    </div>

                    <!-- Connected Roles List -->
                    <div class="de-viz-card de-viz-wide">
                        <div class="de-viz-header">
                            <h3>🤝 Connected Roles</h3>
                            <span class="de-viz-subtitle">All roles that share documents with ${escapeHtml(roleName)}</span>
                        </div>
                        <div class="de-viz-body de-scrollable">
                            ${connectedRoles.length > 0 ? `
                                <div class="de-connections-search">
                                    <input type="text"
                                           class="de-connections-search-input"
                                           placeholder="Search ${connectedRoles.length} connected roles..."
                                           id="connections-search">
                                    <span class="de-connections-count" id="connections-count">${connectedRoles.length} roles</span>
                                </div>
                                <div class="de-role-connections-list" id="connections-list">
                                    ${connectedRoles.map(role => {
                                        const otherRaci = roleRaciInfo[role.name.toLowerCase()] || { R: 0, A: 0, C: 0, I: 0 };
                                        const primaryRaci = Object.entries(otherRaci).reduce((a, b) => b[1] > a[1] ? b : a, ['', 0]);
                                        return `
                                            <div class="de-role-connection-card de-clickable" data-role="${escapeHtml(role.name)}" data-search="${escapeHtml(role.name.toLowerCase())}">
                                                <div class="de-role-connection-header">
                                                    <div class="de-role-connection-name">${escapeHtml(role.name)}${adjLookup ? adjLookup.getBadge(role.name, { compact: true, size: 'sm' }) : ''}</div>
                                                    <div class="de-role-connection-badge">${role.sharedCount} shared doc${role.sharedCount !== 1 ? 's' : ''}</div>
                                                </div>
                                                <div class="de-role-connection-raci">
                                                    ${primaryRaci[1] > 0 ? `
                                                        <span class="de-raci-mini de-raci-${primaryRaci[0].toLowerCase()}">
                                                            ${primaryRaci[0]}
                                                        </span>
                                                        <span class="de-raci-label-mini">Primary: ${primaryRaci[0] === 'R' ? 'Responsible' : primaryRaci[0] === 'A' ? 'Accountable' : primaryRaci[0] === 'C' ? 'Consulted' : 'Informed'}</span>
                                                    ` : '<span class="de-raci-label-mini">No RACI data</span>'}
                                                </div>
                                                <div class="de-role-connection-docs">
                                                    <div class="de-connection-docs-label">Shared in:</div>
                                                    <div class="de-connection-docs-list">
                                                        ${role.sharedDocs.slice(0, 3).map(doc => `
                                                            <span class="de-connection-doc-tag">${escapeHtml(doc.length > 25 ? doc.substring(0, 22) + '...' : doc)}</span>
                                                        `).join('')}
                                                        ${role.sharedDocs.length > 3 ? `<span class="de-connection-doc-more">+${role.sharedDocs.length - 3} more</span>` : ''}
                                                    </div>
                                                </div>
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            ` : `
                                <div class="de-empty">
                                    <div class="de-empty-icon">🔗</div>
                                    <p>No connected roles found</p>
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Attach listeners
        setTimeout(() => {
            attachRoleConnectionsListeners();
        }, 50);
    }

    function attachRoleConnectionsListeners() {
        // Click on connected role to view its connections
        State.modal.querySelectorAll('.de-role-connection-card.de-clickable').forEach(item => {
            item.addEventListener('click', () => {
                const roleName = item.dataset.role;
                drillInto('role-connections', roleName, { name: roleName });
            });
        });

        // Search functionality for connected roles
        const searchInput = State.modal.querySelector('#connections-search');
        const countDisplay = State.modal.querySelector('#connections-count');
        const connectionsList = State.modal.querySelector('#connections-list');

        if (searchInput && connectionsList) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase().trim();
                const cards = connectionsList.querySelectorAll('.de-role-connection-card');
                let visibleCount = 0;

                cards.forEach(card => {
                    const searchText = card.dataset.search || '';
                    const matches = !query || searchText.includes(query);
                    card.style.display = matches ? '' : 'none';
                    if (matches) visibleCount++;
                });

                if (countDisplay) {
                    countDisplay.textContent = query
                        ? `${visibleCount} of ${cards.length} roles`
                        : `${cards.length} roles`;
                }
            });

            // Clear search on Escape key
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    searchInput.dispatchEvent(new Event('input'));
                    searchInput.blur();
                }
            });
        }
    }

    function attachInteractionListeners() {
        // Connected role clicks - now goes to role-connections view
        State.modal.querySelectorAll('.de-connected-item.de-clickable').forEach(item => {
            item.addEventListener('click', () => {
                const roleName = item.dataset.role;
                drillInto('role-connections', roleName, { name: roleName });
            });
        });

        // Role pair clicks
        State.modal.querySelectorAll('.de-pair-role.de-clickable').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const roleName = item.dataset.role;
                drillInto('role', roleName, { name: roleName });
            });
        });

        // Matrix role header clicks
        State.modal.querySelectorAll('.de-matrix-role-header.de-clickable').forEach(item => {
            item.addEventListener('click', () => {
                const roleName = item.dataset.role;
                drillInto('role', roleName, { name: roleName });
            });
        });
    }

    // ============================================================
    // NAVIGATION
    // ============================================================

    async function drillInto(type, id, data) {
        if (State.animating) return;
        State.animating = true;

        // Save current state to history
        State.history.push({
            type: State.currentData?.type || 'overview',
            id: State.currentData?.id || 'main',
            data: State.currentData?.data,
            scrollPosition: State.modal?.querySelector('.de-content')?.scrollTop || 0
        });

        if (State.history.length > CONFIG.maxHistoryDepth) {
            State.history.shift();
        }

        State.currentLevel++;
        State.currentData = { type, id, data };

        // Update breadcrumbs
        updateBreadcrumbs();

        // Animate transition
        const content = State.modal.querySelector('.de-content');
        await animateOut(content, 'left');

        destroyCharts();

        // Render new view
        switch (type) {
            case 'category':
                await renderCategoryDrill(id, data);
                break;
            case 'role':
                await renderRoleDrill(id, data);
                break;
            case 'roles-list':
                await renderRolesListDrill(data);
                break;
            case 'mentions-breakdown':
                await renderMentionsBreakdown(data);
                break;
            case 'action':
                await renderActionDrill(id, data);
                break;
            case 'documents':
                await renderDocumentsLanding(data);
                break;
            case 'document':
                await renderDocumentDrill(id, data);
                break;
            case 'interactions':
                await renderInteractionsLanding(data);
                break;
            case 'role-connections':
                await renderRoleConnectionsDrill(id, data);
                break;
            default:
                log('Unknown drill type: ' + type, 'warn');
        }

        await animateIn(content, 'right');
        State.animating = false;

        // Update nav buttons
        updateNavButtons();
    }

    async function goBack() {
        if (State.history.length === 0 || State.animating) return;
        State.animating = true;

        const previous = State.history.pop();
        State.currentLevel--;

        // Animate transition
        const content = State.modal.querySelector('.de-content');
        await animateOut(content, 'right');

        destroyCharts();

        // Render previous view
        if (previous.type === 'overview' || State.history.length === 0) {
            const rolesData = await fetchRolesData();
            const processed = processRolesForOverview(rolesData);
            State.currentData = { type: 'overview', id: 'main', data: processed };
            renderOverviewLevel(processed);
        } else {
            State.currentData = previous;
            switch (previous.type) {
                case 'category':
                    await renderCategoryDrill(previous.id, previous.data);
                    break;
                case 'role':
                    await renderRoleDrill(previous.id, previous.data);
                    break;
                case 'roles-list':
                    await renderRolesListDrill(previous.data);
                    break;
                case 'mentions-breakdown':
                    await renderMentionsBreakdown(previous.data);
                    break;
                case 'action':
                    await renderActionDrill(previous.id, previous.data);
                    break;
                case 'documents':
                    await renderDocumentsLanding(previous.data);
                    break;
                case 'document':
                    await renderDocumentDrill(previous.id, previous.data);
                    break;
                case 'interactions':
                    await renderInteractionsLanding(previous.data);
                    break;
                case 'role-connections':
                    await renderRoleConnectionsDrill(previous.id, previous.data);
                    break;
            }
        }

        await animateIn(content, 'left');

        // Restore scroll position
        if (previous.scrollPosition) {
            content.scrollTop = previous.scrollPosition;
        }

        updateBreadcrumbs();
        updateNavButtons();
        State.animating = false;
    }

    async function goHome() {
        if (State.animating) return;
        State.animating = true;

        State.history = [];
        State.currentLevel = 0;

        const content = State.modal.querySelector('.de-content');
        await animateOut(content, 'right');

        destroyCharts();

        const rolesData = await fetchRolesData();
        const processed = processRolesForOverview(rolesData);
        State.currentData = { type: 'overview', id: 'main', data: processed };
        renderOverviewLevel(processed);

        await animateIn(content, 'left');

        updateBreadcrumbs();
        updateNavButtons();
        State.animating = false;
    }

    function updateBreadcrumbs() {
        const breadcrumbs = State.modal.querySelector('.de-breadcrumbs');
        if (!breadcrumbs) return;

        let html = `<span class="de-breadcrumb de-clickable" data-level="0">Overview</span>`;

        State.history.forEach((item, i) => {
            if (item.type !== 'overview') {
                html += `<span class="de-breadcrumb-sep">›</span>`;
                html += `<span class="de-breadcrumb de-clickable" data-level="${i + 1}">${escapeHtml(item.id)}</span>`;
            }
        });

        if (State.currentData && State.currentData.type !== 'overview') {
            html += `<span class="de-breadcrumb-sep">›</span>`;
            html += `<span class="de-breadcrumb de-current">${escapeHtml(State.currentData.id)}</span>`;
        }

        breadcrumbs.innerHTML = html;

        // Attach click handlers for navigation
        breadcrumbs.querySelectorAll('.de-breadcrumb.de-clickable').forEach(crumb => {
            crumb.addEventListener('click', async () => {
                const level = parseInt(crumb.dataset.level);
                if (level === 0) {
                    await goHome();
                } else {
                    // Navigate to specific history level
                    while (State.history.length > level) {
                        await goBack();
                    }
                }
            });
        });
    }

    function updateNavButtons() {
        const backBtn = State.modal.querySelector('.de-nav-back');
        const homeBtn = State.modal.querySelector('.de-nav-home');

        if (backBtn) {
            backBtn.disabled = State.history.length === 0;
            backBtn.style.opacity = State.history.length === 0 ? '0.5' : '1';
        }

        if (homeBtn) {
            homeBtn.disabled = State.history.length === 0;
            homeBtn.style.opacity = State.history.length === 0 ? '0.5' : '1';
        }
    }

    // ============================================================
    // MODAL MANAGEMENT
    // ============================================================

    function createModal() {
        // Detect and apply theme before creating modal
        applyThemeToModal();

        const modal = document.createElement('div');
        modal.className = 'de-modal-overlay' + (State.isLightMode ? ' de-light-mode' : '');
        modal.innerHTML = `
            <div class="de-modal">
                <div class="de-modal-header">
                    <div class="de-nav-controls">
                        <button class="de-nav-btn de-nav-back" title="Go Back (←)">
                            ${CONFIG.icons.back}
                        </button>
                        <button class="de-nav-btn de-nav-home" title="Go to Overview">
                            🏠
                        </button>
                    </div>
                    <div class="de-breadcrumbs">
                        <span class="de-breadcrumb de-current">Overview</span>
                    </div>
                    <div class="de-modal-actions">
                        <button class="de-close-btn" title="Close (Esc)">
                            ${CONFIG.icons.close}
                        </button>
                    </div>
                </div>
                <div class="de-modal-body">
                    <div class="de-content">
                        <div class="de-loading">
                            <div class="de-spinner"></div>
                            <p>Loading data exploration...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        State.modal = modal;

        // Attach event listeners
        modal.querySelector('.de-close-btn').addEventListener('click', close);
        modal.querySelector('.de-nav-back').addEventListener('click', goBack);
        modal.querySelector('.de-nav-home').addEventListener('click', goHome);

        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) close();
        });

        // Keyboard navigation
        const keyHandler = (e) => {
            if (!State.isOpen) return;

            // Don't intercept keys when user is typing in an input field
            const activeElement = document.activeElement;
            const isTyping = activeElement && (
                activeElement.tagName === 'INPUT' ||
                activeElement.tagName === 'TEXTAREA' ||
                activeElement.isContentEditable
            );

            if (e.key === 'Escape') close();
            if ((e.key === 'ArrowLeft' || e.key === 'Backspace') && !isTyping) goBack();
        };
        document.addEventListener('keydown', keyHandler);
        State.listeners.push({ type: 'keydown', handler: keyHandler });

        return modal;
    }

    async function open(initialMetric = null) {
        if (State.isOpen) return;

        log('Opening Data Explorer');
        State.isOpen = true;
        State.history = [];
        State.currentLevel = 0;

        if (!State.modal) {
            createModal();
        } else {
            // Refresh theme on each open in case user changed it
            applyThemeToModal();
        }

        State.modal.classList.add('de-visible');
        document.body.style.overflow = 'hidden';

        // Fetch and render data
        try {
            const rolesData = await fetchRolesData();
            const processed = processRolesForOverview(rolesData);
            State.currentData = { type: 'overview', id: 'main', data: processed };

            renderOverviewLevel(processed);
            updateNavButtons();

            // If initial metric specified, drill into it
            if (initialMetric) {
                setTimeout(() => {
                    if (initialMetric === 'roles') {
                        drillInto('roles-list', 'all', { allRoles: processed.allRoles });
                    } else if (initialMetric === 'mentions') {
                        drillInto('mentions-breakdown', 'all', processed);
                    }
                }, 500);
            }
        } catch (e) {
            log('Error loading data: ' + e, 'error');
            State.modal.querySelector('.de-content').innerHTML = `
                <div class="de-error">
                    <p>Failed to load data. Please try again.</p>
                    <button onclick="TWR.DataExplorer.close()">Close</button>
                </div>
            `;
        }
    }

    function close() {
        if (!State.isOpen) return;

        log('Closing Data Explorer');
        State.isOpen = false;

        if (State.modal) {
            State.modal.classList.remove('de-visible');
        }

        document.body.style.overflow = '';
        destroyCharts();

        // Cleanup listeners
        State.listeners.forEach(({ type, handler }) => {
            document.removeEventListener(type, handler);
        });
        State.listeners = [];
    }

    // ============================================================
    // PUBLIC API
    // ============================================================

    return {
        VERSION,
        open,
        close,
        goBack,
        goHome,
        drillInto,
        getState: () => ({ ...State })
    };

})();

// Global shortcut
window.openDataExplorer = TWR.DataExplorer.open;

console.log('[TWR] DataExplorer module loaded v' + TWR.DataExplorer.VERSION);
