/**
 * AEGIS - Roles Feature Module
 * 
 * Extracted in v3.0.19 from app.js (~1,600 LOC)
 * 
 * v3.0.80: Added comprehensive roles export - All/Current/Selected document CSV/JSON export
 * v3.0.77: Self-explanatory graph - visible weak nodes, distinct link types, enhanced legend
 * v3.0.76: Iterative peripheral node pruning - removes nodes with <2 connections to eliminate phantom lines
 * v3.0.73: Fixed dangling graph links - now filters links to ensure both endpoints exist
 * 
 * Contains:
 * - Role summary and modal UI
 * - RACI matrix functionality
 * - Role adjudication system
 * - D3.js interactive graph visualization
 * - Role export functionality
 * 
 * Dependencies:
 * - TWR.Utils (escapeHtml, truncate, debounce)
 * - TWR.State (State object)
 * - TWR.API (api function)
 * - TWR.Modals (toast, showModal)
 * - D3.js (optional, for graph visualization)
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Roles = (function() {
    // ============================================================
    // GRAPH STATE & CONSTANTS
    // ============================================================
    
    const GraphState = {
        data: null,
        simulation: null,
        svg: null,
        zoom: null,             // v4.1.0: D3 zoom behavior
        selectedNode: null,
        highlightedNodes: new Set(),
        isD3Available: false,
        isPinned: false,
        labelMode: 'selected',
        fallbackRows: [],
        fallbackData: null,
        performanceMode: false,
        animationsEnabled: true,
        linkStylesEnabled: true,
        glowEnabled: true,
        isLoading: false,
        // v4.0.2: Drill-down filter state
        filterStack: [],        // Stack of applied filters [{type, id, label}]
        filteredNodeIds: null,  // Set of visible node IDs when filtered, null = show all
        originalData: null,     // Original unfiltered data for reset
        // v4.1.0: Enhanced filtering features
        filterHistory: [],      // History of filter states for back navigation
        filterForwardStack: [], // Forward stack for redo after going back
        savedFilters: [],       // Saved/bookmarked filter paths
        keyboardNavEnabled: true, // Enable keyboard navigation
        // v4.5.1: HEB (Hierarchical Edge Bundling) + Semantic Zoom state
        currentLayout: 'heb',         // 'heb' | 'semantic-zoom' | 'force' | 'bipartite'
        bundlingTension: 0.85,        // 0.0-1.0 for d3.curveBundle.beta()
        hierarchyRoot: null,          // d3.hierarchy root node
        leafNodeMap: new Map(),       // Maps node.id → hierarchy leaf node
        documentGroups: [],           // [{docId, docLabel, roles[], startAngle, endAngle, color}]
        lodLevel: 1                   // Current LOD level for semantic zoom (1=far, 2=mid, 3=near)
    };
    
    const LINK_STYLES = {
        'role-role': { dashArray: '6,3', label: 'Roles Co-occur', color: '#7c3aed' },
        'role-document': { dashArray: 'none', label: 'Role in Document', color: '#4A90D9' },
        'role-deliverable': { dashArray: '8,4', label: 'Role-Deliverable', color: '#F59E0B' },
        'approval': { dashArray: '4,4', label: 'Approval', color: '#EC4899' },
        'coordination': { dashArray: '2,4', label: 'Coordination', color: '#06b6d4' },
        'reports-to': { dashArray: '12,4,4,4', label: 'Reports To', color: '#6366f1' },
        'supports': { dashArray: '4,2', label: 'Supports', color: '#22c55e' },
        'default': { dashArray: 'none', label: 'Connection', color: '#888' }
    };
    
    const GRAPH_PERFORMANCE = {
        nodeThreshold: 150,  // v4.0.2: Force-directed thresholds
        linkThreshold: 300,
        animationThreshold: 100,
        glowThreshold: 120,
        // v4.5.1: HEB thresholds (HEB is inherently more performant — no simulation)
        hebNodeThreshold: 300,
        hebLinkThreshold: 600
    };
    
    const AdjudicationState = {
        decisions: new Map(),
        filter: 'pending',
        search: ''
    };
    
    let activeRaciDropdown = null;
    
    // ============================================================
    // UTILITY IMPORTS
    // ============================================================
    
    function getEscapeHtml() {
        return window.TWR?.Utils?.escapeHtml || window.escapeHtml || function(str) {
            if (str == null) return '';
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        };
    }
    
    function getTruncate() {
        return window.TWR?.Utils?.truncate || window.truncate || function(str, len) {
            if (!str) return '';
            return str.length > len ? str.substring(0, len - 3) + '...' : str;
        };
    }
    
    function getDebounce() {
        return window.TWR?.Utils?.debounce || window.debounce || function(fn, wait) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => fn.apply(this, args), wait);
            };
        };
    }
    
    function getApi() { return window.TWR?.API?.api || window.api; }
    function getToast() { return window.TWR?.Modals?.toast || window.toast || function(t, m) { console.log(`[${t}] ${m}`); }; }
    function getShowModal() { return window.TWR?.Modals?.showModal || window.showModal; }
    function getState() { return window.TWR?.State?.State || window.State || {}; }
    function getSetLoading() { return window.TWR?.Modals?.showLoading || window.setLoading || function() {}; }

    // ============================================================
    // v4.3.0: SMART SEARCH AUTOCOMPLETE SYSTEM
    // ============================================================

    const SmartSearch = {
        instances: new Map(),
        recentSearches: new Map(), // Per-input recent searches

        /**
         * Initialize SmartSearch on an input element
         * @param {string} inputId - ID of the input element
         * @param {Object} config - Configuration object
         * @param {Function} config.getItems - Function returning array of searchable items
         * @param {Function} config.onSelect - Callback when item is selected
         * @param {string} config.itemType - Type for icon styling (role, document, issue, link, statement)
         * @param {Function} config.renderItem - Optional custom item renderer
         * @param {number} config.maxResults - Max results to show (default 8)
         * @param {boolean} config.showRecent - Show recent searches (default true)
         */
        init: function(inputId, config) {
            const input = document.getElementById(inputId);
            if (!input) {
                console.log(`[SmartSearch] Input #${inputId} not found, skipping`);
                return null;
            }

            console.log(`[SmartSearch] Initializing on #${inputId}`);

            // Prevent double initialization
            if (this.instances.has(inputId)) {
                this.destroy(inputId);
            }

            const escapeHtml = getEscapeHtml();
            const debounce = getDebounce();

            // Create wrapper if not exists - but only wrap inline inputs, not ones inside complex layouts
            let wrapper = input.parentElement;
            if (!wrapper.classList.contains('smart-search-wrapper')) {
                // Check if parent is a simple container we can wrap
                const parentDisplay = window.getComputedStyle(wrapper).display;
                if (parentDisplay === 'flex' || parentDisplay === 'grid' || wrapper.children.length > 3) {
                    // Complex parent layout - add wrapper as sibling approach
                    wrapper = document.createElement('div');
                    wrapper.className = 'smart-search-wrapper';
                    wrapper.style.position = 'relative';
                    wrapper.style.display = 'inline-block';
                    wrapper.style.width = '100%';
                    input.parentNode.insertBefore(wrapper, input);
                    wrapper.appendChild(input);
                } else {
                    // Simple parent - wrap the input
                    wrapper = document.createElement('div');
                    wrapper.className = 'smart-search-wrapper';
                    input.parentNode.insertBefore(wrapper, input);
                    wrapper.appendChild(input);
                }
            }

            // Create dropdown
            const dropdown = document.createElement('div');
            dropdown.className = 'smart-search-dropdown';
            dropdown.id = `${inputId}-dropdown`;
            wrapper.appendChild(dropdown);

            console.log(`[SmartSearch] Created dropdown for #${inputId}`);

            // Initialize recent searches from localStorage
            const storageKey = `smartSearch_recent_${inputId}`;
            let recentSearches = [];
            try {
                recentSearches = JSON.parse(localStorage.getItem(storageKey) || '[]').slice(0, 5);
            } catch (e) {}
            this.recentSearches.set(inputId, recentSearches);

            const instance = {
                input,
                dropdown,
                config: {
                    getItems: config.getItems || (() => []),
                    onSelect: config.onSelect || (() => {}),
                    itemType: config.itemType || 'default',
                    renderItem: config.renderItem,
                    maxResults: config.maxResults || 8,
                    showRecent: config.showRecent !== false,
                    minChars: config.minChars || 0
                },
                highlightIndex: -1,
                items: [],
                isOpen: false
            };

            // Event handlers
            const handleInput = debounce(() => {
                this.search(inputId, input.value);
            }, 150);

            const handleFocus = () => {
                if (input.value.length >= instance.config.minChars) {
                    this.search(inputId, input.value);
                } else if (instance.config.showRecent && this.recentSearches.get(inputId)?.length > 0) {
                    this.showRecentSearches(inputId);
                }
            };

            const handleBlur = (e) => {
                // Delay to allow click on dropdown items
                setTimeout(() => {
                    if (!dropdown.contains(document.activeElement)) {
                        this.close(inputId);
                    }
                }, 200);
            };

            const handleKeydown = (e) => {
                if (!instance.isOpen) return;

                switch (e.key) {
                    case 'ArrowDown':
                        e.preventDefault();
                        this.highlightNext(inputId);
                        break;
                    case 'ArrowUp':
                        e.preventDefault();
                        this.highlightPrev(inputId);
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (instance.highlightIndex >= 0) {
                            this.selectHighlighted(inputId);
                        }
                        break;
                    case 'Escape':
                        this.close(inputId);
                        break;
                    case 'Tab':
                        if (instance.highlightIndex >= 0) {
                            e.preventDefault();
                            this.selectHighlighted(inputId);
                        }
                        break;
                }
            };

            input.addEventListener('input', handleInput);
            input.addEventListener('focus', handleFocus);
            input.addEventListener('blur', handleBlur);
            input.addEventListener('keydown', handleKeydown);

            instance.handlers = { handleInput, handleFocus, handleBlur, handleKeydown };

            this.instances.set(inputId, instance);
            return instance;
        },

        search: function(inputId, query) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const escapeHtml = getEscapeHtml();
            const { dropdown, config } = instance;
            const trimmedQuery = (query || '').trim().toLowerCase();

            // Get items from data source
            let items = [];
            try {
                items = config.getItems() || [];
            } catch (e) {
                console.error('[SmartSearch] Error getting items:', e);
            }

            // Filter items
            let filtered = [];
            if (trimmedQuery.length > 0) {
                filtered = items.filter(item => {
                    const label = (item.label || item.name || item.title || '').toLowerCase();
                    const meta = (item.meta || item.description || '').toLowerCase();
                    return label.includes(trimmedQuery) || meta.includes(trimmedQuery);
                });

                // Sort by relevance (starts with > contains)
                filtered.sort((a, b) => {
                    const aLabel = (a.label || a.name || a.title || '').toLowerCase();
                    const bLabel = (b.label || b.name || b.title || '').toLowerCase();
                    const aStarts = aLabel.startsWith(trimmedQuery);
                    const bStarts = bLabel.startsWith(trimmedQuery);
                    if (aStarts && !bStarts) return -1;
                    if (bStarts && !aStarts) return 1;
                    return aLabel.localeCompare(bLabel);
                });

                filtered = filtered.slice(0, config.maxResults);
            }

            instance.items = filtered;
            instance.highlightIndex = -1;

            // Render dropdown
            if (filtered.length === 0 && trimmedQuery.length > 0) {
                dropdown.innerHTML = `
                    <div class="smart-search-empty">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>
                        </svg>
                        <div>No results for "${escapeHtml(query)}"</div>
                    </div>
                `;
                this.open(inputId);
            } else if (filtered.length > 0) {
                dropdown.innerHTML =
                    `<div class="smart-search-header">
                        <span class="smart-search-header-title">${filtered.length} suggestion${filtered.length !== 1 ? 's' : ''}</span>
                        <span class="smart-search-header-hint">Click or press Enter to select</span>
                    </div>` +
                    filtered.map((item, idx) => this.renderItem(item, idx, trimmedQuery, config)).join('') +
                    `<div class="smart-search-footer">
                        <span><kbd>↑</kbd><kbd>↓</kbd> Navigate</span>
                        <span><kbd>Enter</kbd> Select</span>
                        <span><kbd>Esc</kbd> Close</span>
                    </div>`;

                // Add click handlers - use mousedown to fire before blur
                dropdown.querySelectorAll('.smart-search-item').forEach((el, idx) => {
                    el.addEventListener('mousedown', (e) => {
                        e.preventDefault(); // Prevent blur from firing
                        this.selectItem(inputId, idx);
                    });
                    el.addEventListener('mouseenter', () => {
                        this.setHighlight(inputId, idx);
                    });
                });

                this.open(inputId);
            } else if (config.showRecent && this.recentSearches.get(inputId)?.length > 0) {
                this.showRecentSearches(inputId);
            } else {
                this.close(inputId);
            }
        },

        renderItem: function(item, index, query, config) {
            const escapeHtml = getEscapeHtml();

            // Use custom renderer if provided
            if (config.renderItem) {
                return config.renderItem(item, index, query);
            }

            const label = item.label || item.name || item.title || 'Unknown';
            const meta = item.meta || item.description || '';
            const badge = item.badge || item.count || '';
            const type = item.type || config.itemType || 'default';

            // Highlight matching text
            const highlightedLabel = this.highlightMatch(escapeHtml(label), query);

            // Get icon based on type
            const icon = this.getIcon(type);

            return `
                <div class="smart-search-item" data-index="${index}">
                    <div class="smart-search-icon type-${type}">${icon}</div>
                    <div class="smart-search-content">
                        <div class="smart-search-title">${highlightedLabel}</div>
                        ${meta ? `<div class="smart-search-meta">${escapeHtml(meta)}</div>` : ''}
                    </div>
                    ${badge ? `<span class="smart-search-badge">${escapeHtml(String(badge))}</span>` : ''}
                </div>
            `;
        },

        highlightMatch: function(text, query) {
            if (!query) return text;
            const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            return text.replace(regex, '<mark>$1</mark>');
        },

        getIcon: function(type) {
            const icons = {
                role: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="10" r="3"/><path d="M12 13c-4 0-6 2-6 5h12c0-3-2-5-6-5"/></svg>',
                document: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
                issue: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
                link: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
                statement: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="17" y1="18" x2="3" y2="18"/></svg>',
                default: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><path d="m21 21-4.3-4.3"/></svg>'
            };
            return icons[type] || icons.default;
        },

        showRecentSearches: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const escapeHtml = getEscapeHtml();
            const recent = this.recentSearches.get(inputId) || [];

            if (recent.length === 0) return;

            instance.dropdown.innerHTML = `
                <div class="smart-search-recent">
                    <div class="smart-search-recent-header">
                        <span>Recent Searches</span>
                        <span class="smart-search-recent-clear" onclick="TWR.Roles.SmartSearch.clearRecent('${inputId}')">Clear</span>
                    </div>
                    <div class="smart-search-recent-tags">
                        ${recent.map(term => `<span class="smart-search-recent-tag" onclick="TWR.Roles.SmartSearch.applyRecent('${inputId}', '${escapeHtml(term)}')">${escapeHtml(term)}</span>`).join('')}
                    </div>
                </div>
            `;

            this.open(inputId);
        },

        applyRecent: function(inputId, term) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            instance.input.value = term;
            instance.input.dispatchEvent(new Event('input', { bubbles: true }));
            this.search(inputId, term);
        },

        clearRecent: function(inputId) {
            this.recentSearches.set(inputId, []);
            localStorage.removeItem(`smartSearch_recent_${inputId}`);
            this.close(inputId);
        },

        addToRecent: function(inputId, term) {
            if (!term || term.length < 2) return;

            let recent = this.recentSearches.get(inputId) || [];
            recent = recent.filter(t => t !== term);
            recent.unshift(term);
            recent = recent.slice(0, 5);

            this.recentSearches.set(inputId, recent);
            try {
                localStorage.setItem(`smartSearch_recent_${inputId}`, JSON.stringify(recent));
            } catch (e) {}
        },

        open: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            instance.dropdown.classList.add('visible');
            instance.isOpen = true;
        },

        close: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            instance.dropdown.classList.remove('visible');
            instance.isOpen = false;
            instance.highlightIndex = -1;
        },

        setHighlight: function(inputId, index) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const items = instance.dropdown.querySelectorAll('.smart-search-item');
            items.forEach((el, i) => el.classList.toggle('highlighted', i === index));
            instance.highlightIndex = index;
        },

        highlightNext: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const max = instance.items.length - 1;
            const next = instance.highlightIndex >= max ? 0 : instance.highlightIndex + 1;
            this.setHighlight(inputId, next);
            this.scrollToHighlighted(inputId);
        },

        highlightPrev: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const max = instance.items.length - 1;
            const prev = instance.highlightIndex <= 0 ? max : instance.highlightIndex - 1;
            this.setHighlight(inputId, prev);
            this.scrollToHighlighted(inputId);
        },

        scrollToHighlighted: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const highlighted = instance.dropdown.querySelector('.smart-search-item.highlighted');
            if (highlighted) {
                highlighted.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            }
        },

        selectHighlighted: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance || instance.highlightIndex < 0) return;

            this.selectItem(inputId, instance.highlightIndex);
        },

        selectItem: function(inputId, index) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const item = instance.items[index];
            if (!item) return;

            const label = item.label || item.name || item.title || '';

            // Update input value
            instance.input.value = label;

            // Add to recent searches
            this.addToRecent(inputId, label);

            // Close dropdown
            this.close(inputId);

            // Call onSelect callback
            instance.config.onSelect(item, instance.input);

            // Trigger input event for any other listeners
            instance.input.dispatchEvent(new Event('input', { bubbles: true }));
        },

        destroy: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance) return;

            const { input, dropdown, handlers } = instance;

            input.removeEventListener('input', handlers.handleInput);
            input.removeEventListener('focus', handlers.handleFocus);
            input.removeEventListener('blur', handlers.handleBlur);
            input.removeEventListener('keydown', handlers.handleKeydown);

            dropdown.remove();
            this.instances.delete(inputId);
        },

        // Refresh items for an existing instance
        refresh: function(inputId) {
            const instance = this.instances.get(inputId);
            if (!instance || !instance.isOpen) return;

            this.search(inputId, instance.input.value);
        }
    };

    // ============================================================
    // ROLES SUMMARY & MODAL
    // ============================================================
    
    async function renderRolesSummary() {
        const escapeHtml = getEscapeHtml();
        const State = getState();
        const container = document.getElementById('roles-summary');
        if (!container || !State.roles) return;

        let rolesData = State.roles;
        if (State.roles.roles) rolesData = State.roles.roles;

        const roleEntries = Object.entries(rolesData);
        if (roleEntries.length === 0) {
            container.innerHTML = '<p class="text-muted">No roles detected</p>'; // SAFE: static HTML
            return;
        }

        // v4.0.3: Load adjudication cache for badges
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        roleEntries.sort((a, b) => {
            const countA = typeof a[1] === 'object' ? (a[1].frequency || a[1].count || a[1].occurrence_count || 1) : 1;
            const countB = typeof b[1] === 'object' ? (b[1].frequency || b[1].count || b[1].occurrence_count || 1) : 1;
            return countB - countA;
        });

        const topRoles = roleEntries.slice(0, 6);

        // v4.0.3: Get adjudication counts for summary
        const adjStats = adjLookup ? adjLookup.getStats() : { total: 0 };
        const adjSummary = adjStats.total > 0
            ? `<span class="adj-summary-counter" title="${adjStats.confirmed} confirmed, ${adjStats.rejected} rejected">
                   <span class="adj-count-confirmed">✓${adjStats.confirmed + (adjStats.deliverable || 0)}</span>
                   ${adjStats.rejected > 0 ? `<span class="adj-count-rejected">✗${adjStats.rejected}</span>` : ''}
               </span>`
            : '';

        // v3.4.0: Add header with explanation of what the count means
        let headerHtml = `
            <div class="roles-summary-header" style="display:flex;justify-content:space-between;align-items:center;padding:4px 0 8px 0;border-bottom:1px solid var(--border-default);margin-bottom:8px;">
                <span style="font-size:11px;color:var(--text-muted);font-weight:500;">Role ${adjSummary}</span>
                <span style="font-size:11px;color:var(--text-muted);font-weight:500;" title="Number of responsibility statements found">Count</span>
            </div>
        `;

        // SAFE: displayName, truncatedName escaped via escapeHtml(); count is numeric
        container.innerHTML = headerHtml + topRoles.map(([name, data]) => {
            const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
            const count = typeof data === 'object' ? (data.frequency || data.count || data.occurrence_count || 1) : 1;
            const truncatedName = displayName.length > 30 ? displayName.substring(0, 27) + '...' : displayName;
            const needsTooltip = displayName.length > 30;
            // v3.4.0: Add tooltip explaining what the count represents
            const countTooltip = `${count} responsibility statements found for "${displayName}"`;
            // v4.0.3: Adjudication badge
            const adjBadge = adjLookup ? adjLookup.getBadge(displayName, { compact: true, size: 'sm' }) : '';
            return `<div class="role-item" style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border-default);">
                <span class="role-name" style="font-size:13px;${needsTooltip ? 'cursor:help;' : ''}" ${needsTooltip ? `title="${escapeHtml(displayName)}"` : ''}>${escapeHtml(truncatedName)}${adjBadge}</span>
                <span class="role-count" style="background:var(--bg-secondary);padding:2px 8px;border-radius:10px;font-size:11px;cursor:help;" title="${escapeHtml(countTooltip)}">${count}</span>
            </div>`;
        }).join('');

        if (roleEntries.length > 6) {
            container.innerHTML += `<div style="text-align:center;padding-top:10px;">
                <button class="btn btn-sm btn-ghost" onclick="TWR.Roles.showRolesModal()">View all ${roleEntries.length} roles</button>
            </div>`;
        }
    }

    async function showRolesModal() {
        const State = getState();
        const toast = getToast();
        const showModal = getShowModal();
        
        if (!State.roles || Object.keys(State.roles).length === 0) {
            toast('warning', 'No roles detected in document');
            return;
        }

        showModal('modal-roles');
        initRolesTabs();
        initDocumentFilter(); // v3.0.98: Initialize document filter dropdown
        initExportDropdown(); // v3.0.80: Initialize export dropdown
        initGlobalSearch(); // v4.5.1: Initialize global search autocomplete
        renderRolesOverview();
        renderRolesDetails();
        renderRolesMatrix();
        renderDocumentLog();
        loadAdjudication();
        initAdjudication();

        if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
    }

    /**
     * v4.5.1: Initialize global search with SmartSearch autocomplete
     */
    function initGlobalSearch() {
        const searchInput = document.getElementById('roles-global-search');
        if (!searchInput) return;

        // Initialize SmartSearch on the global search input
        initSmartSearchInputs();

        // Add Enter key handler for manual search
        if (!searchInput._globalSearchInit) {
            searchInput._globalSearchInit = true;

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    applyGlobalRoleSearch(searchInput.value);
                }
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    clearGlobalRoleSearch();
                }
            });

            // Clear search on input clear (when user deletes all text)
            searchInput.addEventListener('input', (e) => {
                if (searchInput.value === '') {
                    clearGlobalRoleSearch();
                }
            });
        }
    }

    function initRolesTabs() {
        const navItems = document.querySelectorAll('.roles-nav-item, .roles-tab');
        
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const tabName = item.dataset.tab;
                
                document.querySelectorAll('.roles-nav-item, .roles-tab').forEach(t => {
                    t.classList.remove('active');
                    t.setAttribute('aria-selected', 'false');
                });
                item.classList.add('active');
                item.setAttribute('aria-selected', 'true');
                
                // v3.0.116: Use .active class instead of inline styles (CSS has !important rules)
                document.querySelectorAll('.roles-section').forEach(s => s.classList.remove('active'));
                document.getElementById(`roles-${tabName}`)?.classList.add('active');
                
                if (tabName === 'graph') renderRolesGraph();
                if (tabName === 'matrix') initRaciMatrixControls();
                if (tabName === 'roledocmatrix') renderRoleDocMatrix();
                if (tabName === 'adjudication') initBulkAdjudication();
            });
        });
        
        initGraphControls();
        updateRolesSidebarStats();
    }

    function updateRolesSidebarStats() {
        const State = getState();
        const rolesData = State.roles?.roles || State.roles || {};
        const roleEntries = Object.entries(rolesData);
        const totalRoles = roleEntries.length;
        let totalResp = 0;
        roleEntries.forEach(([name, data]) => {
            if (typeof data === 'object') totalResp += data.responsibilities?.length || data.count || 1;
        });
        
        const rolesCountEl = document.getElementById('sidebar-roles-count');
        const respCountEl = document.getElementById('sidebar-resp-count');
        if (rolesCountEl) rolesCountEl.textContent = totalRoles;
        if (respCountEl) respCountEl.textContent = totalResp;
    }

    // ============================================================
    // RACI MATRIX
    // ============================================================
    
    function initRaciMatrixControls() {
        const State = getState();
        
        const filterCritical = document.getElementById('matrix-filter-critical');
        if (filterCritical && !filterCritical._initialized) {
            filterCritical.addEventListener('change', () => {
                State.matrixFilterCritical = filterCritical.checked;
                renderRolesMatrix();
            });
            filterCritical._initialized = true;
        }
        
        const sortSelect = document.getElementById('matrix-sort');
        if (sortSelect && !sortSelect._initialized) {
            sortSelect.addEventListener('change', () => {
                State.matrixSort = sortSelect.value;
                renderRolesMatrix();
            });
            sortSelect._initialized = true;
        }
        
        const resetBtn = document.getElementById('btn-raci-reset');
        if (resetBtn && !resetBtn._initialized) {
            resetBtn.addEventListener('click', resetRaciEdits);
            resetBtn._initialized = true;
        }
        
        const exportBtn = document.getElementById('btn-raci-export');
        if (exportBtn && !exportBtn._initialized) {
            exportBtn.addEventListener('click', toggleExportMenu);
            exportBtn._initialized = true;
            // Close menu on outside click
            document.addEventListener('click', (e) => {
                const wrapper = document.querySelector('.raci-export-wrapper');
                if (wrapper && !wrapper.contains(e.target)) {
                    const menu = document.getElementById('raci-export-menu');
                    if (menu) menu.classList.remove('open');
                }
            });
        }

        // v4.5.2: Dictionary filter
        const dictFilter = document.getElementById('matrix-dict-filter');
        if (dictFilter && !dictFilter._initialized) {
            dictFilter.addEventListener('change', () => {
                State.matrixDictFilter = dictFilter.value;
                renderRolesMatrix();
            });
            dictFilter._initialized = true;
        }
    }

    function resetRaciEdits() {
        const State = getState();
        const toast = getToast();
        State.raciEdits = {};
        renderRolesMatrix();
        toast('success', 'RACI matrix reset to detected values');
    }

    function initBulkAdjudication() {
        const selectAll = document.getElementById('adj-select-all');
        if (selectAll && !selectAll._initialized) {
            selectAll.addEventListener('change', () => {
                const items = document.querySelectorAll('.adjudication-item');
                items.forEach(item => {
                    const checkbox = item.querySelector('.adj-item-checkbox');
                    if (checkbox) checkbox.checked = selectAll.checked;
                    item.classList.toggle('selected', selectAll.checked);
                });
                updateBulkActionVisibility();
            });
            selectAll._initialized = true;
        }
    }

    function updateBulkActionVisibility() {
        const selectedItems = document.querySelectorAll('.adjudication-item.selected');
        const bulkActions = document.getElementById('adj-bulk-actions');
        const selectionInfo = document.getElementById('adj-selection-info');
        if (bulkActions) bulkActions.style.display = selectedItems.length > 0 ? 'flex' : 'none';
        if (selectionInfo) selectionInfo.textContent = `${selectedItems.length} selected`;
    }

    function bulkAdjudicate(status) {
        const toast = getToast();
        const selectedItems = document.querySelectorAll('.adjudication-item.selected');
        let count = 0;
        
        selectedItems.forEach(item => {
            const roleName = item.dataset.role;
            if (roleName) {
                const decision = AdjudicationState.decisions.get(roleName);
                if (decision) {
                    decision.status = status;
                    count++;
                }
            }
        });
        
        if (count > 0) {
            renderAdjudicationList();
            updateAdjudicationStats();
            toast('success', `Updated ${count} items to ${status}`);
        }
    }

    // ============================================================
    // ROLES VIEWS
    // ============================================================
    
    async function renderRolesOverview() {
        const escapeHtml = getEscapeHtml();
        const State = getState();
        const container = document.getElementById('roles-overview-content');
        if (!container) return;

        // v4.0.3: Load adjudication data
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        const rolesData = State.roles?.roles || State.roles || {};
        let roleEntries = Object.entries(rolesData);

        if (roleEntries.length === 0) {
            container.innerHTML = '<p class="text-muted">No roles detected in document</p>';
            return;
        }

        // v3.0.98: Apply document filter
        const docFilter = document.getElementById('roles-document-filter')?.value || 'all';
        if (docFilter !== 'all') {
            roleEntries = roleEntries.filter(([name, data]) => {
                const sourceDocs = data.source_documents || [];
                return sourceDocs.some(doc => doc === docFilter || doc.includes(docFilter));
            });
        }

        roleEntries.sort((a, b) => {
            const countA = typeof a[1] === 'object' ? (a[1].frequency || a[1].count || 1) : 1;
            const countB = typeof b[1] === 'object' ? (b[1].frequency || b[1].count || 1) : 1;
            return countB - countA;
        });

        const totalMentions = roleEntries.reduce((sum, [, data]) => {
            return sum + (typeof data === 'object' ? (data.frequency || data.count || 1) : 1);
        }, 0);

        // v4.0.3: Get adjudication stats for overview
        const adjStats = adjLookup ? adjLookup.getStats() : { total: 0, confirmed: 0, rejected: 0, deliverable: 0 };
        const adjTotal = adjStats.confirmed + (adjStats.deliverable || 0);

        // v3.4.0: Enhanced overview with Data Explorer integration
        container.innerHTML = `
            <div class="roles-overview-stats" style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px;">
                <div class="stat-card stat-card-clickable" onclick="TWR.DataExplorer?.open('roles')" title="Click to explore all roles in detail">
                    <div class="stat-value">${roleEntries.length}</div>
                    <div class="stat-label">Unique Roles${docFilter !== 'all' ? ' (Filtered)' : ''}</div>
                    ${adjTotal > 0 ? `<div style="font-size:11px;color:#22c55e;margin-top:2px;">✓ ${adjTotal} adjudicated${adjStats.deliverable > 0 ? ` · ${adjStats.deliverable} deliverable` : ''}</div>` : ''}
                    <div class="stat-hint">Click to explore →</div>
                </div>
                <div class="stat-card stat-card-clickable" onclick="TWR.DataExplorer?.open('mentions')" title="Click to see how mentions are calculated">
                    <div class="stat-value">${totalMentions}</div>
                    <div class="stat-label">Responsibility Statements</div>
                    <div class="stat-hint">Click to explore →</div>
                </div>
                <div class="stat-card" title="Average responsibility statements per role">
                    <div class="stat-value">${(totalMentions / Math.max(1, roleEntries.length)).toFixed(1)}</div>
                    <div class="stat-label">Avg per Role</div>
                </div>
            </div>
            <div class="explore-btn-container" style="text-align:center;margin-bottom:20px;">
                <button class="btn btn-primary btn-explore" onclick="TWR.DataExplorer?.open()" style="padding:10px 24px;font-size:14px;">
                    🔍 Open Data Explorer
                </button>
                <p style="font-size:12px;color:var(--text-muted);margin-top:8px;">Deep dive into your role data with interactive visualizations</p>
            </div>
            <div class="roles-chart-container" style="height:300px;margin-bottom:24px;"><canvas id="roles-distribution-chart"></canvas></div>
            <div class="roles-top-list"><h4>Top Roles by Frequency</h4>
                <div class="top-roles-grid" style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;">
                    ${roleEntries.slice(0, 10).map(([name, data], i) => {
                        const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
                        const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
                        const pct = ((count / totalMentions) * 100).toFixed(1);
                        const adjBadge = adjLookup ? adjLookup.getBadge(displayName, { compact: true, size: 'sm' }) : '';
                        return `<div class="top-role-item top-role-clickable" data-role="${escapeHtml(name)}" style="display:flex;align-items:center;gap:10px;padding:8px;background:var(--bg-secondary);border-radius:6px;cursor:pointer;transition:all 0.2s;" title="Click to explore ${escapeHtml(displayName)}">
                            <span class="rank" style="font-weight:bold;color:var(--accent);width:24px;">${i + 1}</span>
                            <span class="name" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(displayName)}${adjBadge}</span>
                            <span class="count" style="font-size:12px;color:var(--text-muted);">${count} (${pct}%)</span>
                            <span class="explore-arrow" style="opacity:0;transition:opacity 0.2s;">→</span>
                        </div>`;
                    }).join('')}
                </div>
            </div>`;

        // v3.4.0: Add click handlers for top roles to open Data Explorer
        container.querySelectorAll('.top-role-clickable').forEach(item => {
            item.addEventListener('mouseenter', () => {
                item.style.background = 'var(--bg-elevated)';
                item.style.transform = 'translateX(4px)';
                item.querySelector('.explore-arrow').style.opacity = '1';
            });
            item.addEventListener('mouseleave', () => {
                item.style.background = 'var(--bg-secondary)';
                item.style.transform = 'translateX(0)';
                item.querySelector('.explore-arrow').style.opacity = '0';
            });
            item.addEventListener('click', () => {
                const roleName = item.dataset.role;
                if (TWR.DataExplorer) {
                    TWR.DataExplorer.open();
                    setTimeout(() => {
                        TWR.DataExplorer.drillInto('role', roleName, roleEntries.find(([n]) => n === roleName)?.[1] || {});
                    }, 600);
                }
            });
        });

        if (typeof Chart !== 'undefined') {
            const ctx = document.getElementById('roles-distribution-chart');
            if (ctx) {
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: roleEntries.slice(0, 15).map(([name, data]) => {
                            const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
                            return displayName.length > 20 ? displayName.substring(0, 17) + '...' : displayName;
                        }),
                        datasets: [{
                            label: 'Mentions',
                            data: roleEntries.slice(0, 15).map(([, data]) => typeof data === 'object' ? (data.frequency || data.count || 1) : 1),
                            backgroundColor: 'rgba(74, 144, 217, 0.7)',
                            borderColor: 'rgba(74, 144, 217, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
                });
            }
        }
    }

    async function renderRolesDetails() {
        const escapeHtml = getEscapeHtml();
        const truncate = getTruncate();
        const debounce = getDebounce();
        const State = getState();

        // v4.0.3: Load adjudication data
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();
        // v4.4.0: Support multiple container IDs - roles-report-content is the actual content area
        let container = document.getElementById('roles-details-content') ||
                        document.getElementById('roles-report-content') ||
                        document.getElementById('roles-details');
        if (!container) return;

        const rolesData = State.roles?.roles || State.roles || {};
        let roleEntries = Object.entries(rolesData);

        if (roleEntries.length === 0) {
            container.innerHTML = '<p class="text-muted">No roles detected</p>';
            return;
        }

        // v3.0.98: Apply document filter
        const docFilter = document.getElementById('roles-document-filter')?.value || 'all';
        if (docFilter !== 'all') {
            roleEntries = roleEntries.filter(([name, data]) => {
                const sourceDocs = data.source_documents || [];
                return sourceDocs.some(doc => doc === docFilter || doc.includes(docFilter));
            });
        }

        roleEntries.sort((a, b) => {
            const countA = typeof a[1] === 'object' ? (a[1].frequency || a[1].count || 1) : 1;
            const countB = typeof b[1] === 'object' ? (b[1].frequency || b[1].count || 1) : 1;
            return countB - countA;
        });

        // v4.4.0: Calculate aggregate statistics
        const totalRoles = roleEntries.length;
        const totalMentions = roleEntries.reduce((sum, [, data]) => sum + (typeof data === 'object' ? (data.frequency || data.count || 1) : 1), 0);
        const totalResponsibilities = roleEntries.reduce((sum, [, data]) => {
            const resps = typeof data === 'object' ? (data.responsibilities || []) : [];
            const mapped = typeof data === 'object' ? (data.mapped_statements || []) : [];
            return sum + resps.length + mapped.length;
        }, 0);

        // Get unique categories
        const categoryStats = {};
        roleEntries.forEach(([name, data]) => {
            const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
            const category = getCategoryForRole(displayName);
            if (!categoryStats[category]) {
                categoryStats[category] = { count: 0, color: getCategoryColorForRole(category) };
            }
            categoryStats[category].count++;
        });

        // Build searchable items including responsibilities
        const searchableItems = [];
        roleEntries.forEach(([name, data]) => {
            const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
            const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
            const category = getCategoryForRole(displayName);
            const responsibilities = typeof data === 'object' ? (data.responsibilities || []) : [];
            const mappedStatements = typeof data === 'object' ? (data.mapped_statements || []) : [];

            // Add role itself
            searchableItems.push({
                type: 'role',
                id: name,
                name: displayName,
                category: category,
                count: count,
                responsibilityCount: responsibilities.length + mappedStatements.length,
                searchText: `${displayName} ${category}`.toLowerCase()
            });

            // Add responsibilities as searchable items
            responsibilities.forEach((resp, idx) => {
                searchableItems.push({
                    type: 'responsibility',
                    id: `${name}-resp-${idx}`,
                    roleId: name,
                    roleName: displayName,
                    text: String(resp),
                    category: category,
                    searchText: String(resp).toLowerCase()
                });
            });

            // Add mapped statements as searchable items
            mappedStatements.forEach((stmt, idx) => {
                searchableItems.push({
                    type: 'statement',
                    id: `${name}-stmt-${idx}`,
                    roleId: name,
                    roleName: displayName,
                    text: stmt.description || '',
                    directive: stmt.directive || '',
                    number: stmt.number || '',
                    category: category,
                    searchText: `${stmt.description || ''} ${stmt.directive || ''} ${stmt.number || ''}`.toLowerCase()
                });
            });
        });

        container.innerHTML = `
            <!-- v4.4.0: Enhanced Role Details Header -->
            <div class="rd-header">
                <div class="rd-stats-bar">
                    <div class="rd-stat rd-stat-animated">
                        <div class="rd-stat-icon">👥</div>
                        <div class="rd-stat-content">
                            <div class="rd-stat-value">${totalRoles}</div>
                            <div class="rd-stat-label">Roles</div>
                            ${(() => {
                                const adjS = adjLookup ? adjLookup.getStats() : { total: 0 };
                                const adjC = adjS.confirmed + (adjS.deliverable || 0);
                                if (adjC > 0) {
                                    const parts = [`${adjC} adjudicated`];
                                    if (adjS.deliverable > 0) parts.push(`${adjS.deliverable} deliverable`);
                                    return `<div style="font-size:10px;color:#22c55e;margin-top:1px;">✓ ${parts.join(' · ')}</div>`;
                                }
                                return '';
                            })()}
                        </div>
                    </div>
                    <div class="rd-stat rd-stat-animated" style="animation-delay: 0.1s;">
                        <div class="rd-stat-icon">💬</div>
                        <div class="rd-stat-content">
                            <div class="rd-stat-value">${totalMentions}</div>
                            <div class="rd-stat-label">Mentions</div>
                        </div>
                    </div>
                    <div class="rd-stat rd-stat-animated" style="animation-delay: 0.2s;">
                        <div class="rd-stat-icon">📋</div>
                        <div class="rd-stat-content">
                            <div class="rd-stat-value">${totalResponsibilities}</div>
                            <div class="rd-stat-label">Responsibilities</div>
                        </div>
                    </div>
                    <div class="rd-stat rd-stat-animated" style="animation-delay: 0.3s;">
                        <div class="rd-stat-icon">📁</div>
                        <div class="rd-stat-content">
                            <div class="rd-stat-value">${Object.keys(categoryStats).length}</div>
                            <div class="rd-stat-label">Categories</div>
                        </div>
                    </div>
                </div>

                <!-- Category Filter Pills -->
                <div class="rd-category-filters">
                    <button class="rd-category-pill rd-category-pill-active" data-category="all">
                        <span class="rd-pill-icon">🔍</span>
                        <span class="rd-pill-label">All</span>
                        <span class="rd-pill-count">${totalRoles}</span>
                    </button>
                    ${Object.entries(categoryStats).sort((a, b) => b[1].count - a[1].count).map(([cat, stats]) => `
                        <button class="rd-category-pill" data-category="${escapeHtml(cat)}" style="--pill-color: ${stats.color};">
                            <span class="rd-pill-dot" style="background: ${stats.color};"></span>
                            <span class="rd-pill-label">${escapeHtml(cat)}</span>
                            <span class="rd-pill-count">${stats.count}</span>
                        </button>
                    `).join('')}
                </div>

                <!-- Enhanced Search -->
                <div class="rd-search-container">
                    <div class="rd-search-wrapper">
                        <svg class="rd-search-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
                        <input type="text" id="roles-detail-search" class="rd-search-input" placeholder="Search roles, responsibilities, statements..." autocomplete="off">
                        <div class="rd-search-hints">
                            <kbd>↑↓</kbd> navigate <kbd>↵</kbd> select <kbd>esc</kbd> close
                        </div>
                    </div>
                </div>

                <!-- View Controls -->
                <div class="rd-view-controls">
                    <div class="rd-view-toggle">
                        <button class="rd-view-btn rd-view-btn-active" data-view="cards" title="Card View">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
                        </button>
                        <button class="rd-view-btn" data-view="compact" title="Compact View">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
                        </button>
                        <button class="rd-view-btn" data-view="expanded" title="Expanded View">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/></svg>
                        </button>
                    </div>
                    <button class="rd-expand-all-btn" id="rd-expand-all">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                        <span>Expand All</span>
                    </button>
                </div>
            </div>

            <!-- Role Cards Container -->
            <div class="rd-cards-container" id="roles-detail-list" data-view="cards">
                ${roleEntries.map(([name, data], index) => {
                    const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
                    const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
                    const responsibilities = typeof data === 'object' ? (data.responsibilities || []) : [];
                    const actionTypes = typeof data === 'object' ? (data.action_types || {}) : {};
                    const sampleContexts = typeof data === 'object' ? (data.sample_contexts || []) : [];
                    const mappedStatements = typeof data === 'object' ? (data.mapped_statements || []) : [];
                    const category = getCategoryForRole(displayName);
                    const color = getCategoryColorForRole(category);
                    const totalResps = responsibilities.length + mappedStatements.length;

                    // Calculate responsibility breakdown
                    const directiveCounts = {};
                    mappedStatements.forEach(stmt => {
                        const d = (stmt.directive || 'other').toLowerCase();
                        directiveCounts[d] = (directiveCounts[d] || 0) + 1;
                    });

                    return `
                    <div class="rd-card rd-card-animated" data-role="${escapeHtml(name)}" data-category="${escapeHtml(category)}" style="--card-color: ${color}; --card-index: ${index};">
                        <!-- Card Header -->
                        <div class="rd-card-header">
                            <div class="rd-card-avatar" style="background: linear-gradient(135deg, ${color}20, ${color}40);">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="10" r="3"/><path d="M12 13c-4 0-6 2-6 5h12c0-3-2-5-6-5"/></svg>
                            </div>
                            <div class="rd-card-title-section">
                                <h4 class="rd-card-title">${escapeHtml(displayName)}${adjLookup ? adjLookup.getBadge(displayName, { size: 'sm' }) : ''}</h4>
                                <div class="rd-card-subtitle">
                                    <span class="rd-card-category" style="color: ${color};">${category}</span>
                                    <span class="rd-card-separator">•</span>
                                    <span class="rd-card-mentions">${count} mention${count !== 1 ? 's' : ''}</span>
                                </div>
                            </div>
                            <div class="rd-card-badges">
                                ${totalResps > 0 ? `<span class="rd-badge rd-badge-responsibilities" title="${totalResps} responsibilities">${totalResps}</span>` : ''}
                                ${Object.keys(actionTypes).length > 0 ? `<span class="rd-badge rd-badge-actions" title="${Object.keys(actionTypes).length} action types">${Object.keys(actionTypes).length}</span>` : ''}
                            </div>
                            <button class="rd-card-explore" data-role="${escapeHtml(name)}" aria-label="Open in Data Explorer" title="Open in Data Explorer">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                            </button>
                            <button class="rd-card-expand" aria-label="Expand card">
                                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                            </button>
                        </div>

                        <!-- Quick Stats Bar -->
                        <div class="rd-card-quick-stats">
                            ${Object.entries(directiveCounts).slice(0, 4).map(([directive, cnt]) => {
                                const dColors = { 'shall': '#ef4444', 'must': '#f97316', 'will': '#3b82f6', 'should': '#eab308', 'may': '#22c55e' };
                                const dColor = dColors[directive] || '#64748b';
                                return `<span class="rd-quick-stat" style="--stat-color: ${dColor};" title="${directive}: ${cnt}">
                                    <span class="rd-quick-stat-dot"></span>
                                    <span class="rd-quick-stat-label">${directive}</span>
                                    <span class="rd-quick-stat-value">${cnt}</span>
                                </span>`;
                            }).join('')}
                            ${Object.keys(actionTypes).length > 0 && Object.keys(directiveCounts).length === 0 ?
                                Object.entries(actionTypes).slice(0, 4).map(([action, cnt]) => `
                                    <span class="rd-quick-stat" style="--stat-color: ${color};">
                                        <span class="rd-quick-stat-label">${action}</span>
                                        <span class="rd-quick-stat-value">${cnt}</span>
                                    </span>
                                `).join('') : ''}
                        </div>

                        <!-- Expandable Content -->
                        <div class="rd-card-content">
                            ${sampleContexts.length > 0 ? `
                            <div class="rd-section rd-section-context">
                                <div class="rd-section-header">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                    <span>Document Context</span>
                                    <span class="rd-section-count">${sampleContexts.length}</span>
                                </div>
                                <div class="rd-context-list">
                                    ${sampleContexts.slice(0, 3).map(ctx => `
                                        <div class="rd-context-item" style="--context-color: ${color};">
                                            <div class="rd-context-quote">"</div>
                                            <div class="rd-context-text">${highlightRoleInContext(ctx, displayName)}</div>
                                        </div>
                                    `).join('')}
                                    ${sampleContexts.length > 3 ? `<button class="rd-show-more" data-type="context">Show ${sampleContexts.length - 3} more contexts</button>` : ''}
                                </div>
                            </div>` : ''}

                            ${responsibilities.length > 0 ? `
                            <div class="rd-section rd-section-responsibilities">
                                <div class="rd-section-header">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                                    <span>Responsibilities</span>
                                    <span class="rd-section-count">${responsibilities.length}</span>
                                </div>
                                <div class="rd-responsibility-list">
                                    ${responsibilities.slice(0, 5).map((r, i) => `
                                        <div class="rd-responsibility-item" style="--resp-index: ${i}; --resp-color: ${color};">
                                            <div class="rd-responsibility-bullet"></div>
                                            <div class="rd-responsibility-text">${escapeHtml(String(r))}</div>
                                        </div>
                                    `).join('')}
                                    ${responsibilities.length > 5 ? `<button class="rd-show-more" data-type="responsibilities">Show ${responsibilities.length - 5} more</button>` : ''}
                                </div>
                            </div>` : ''}

                            ${mappedStatements.length > 0 ? `
                            <div class="rd-section rd-section-statements">
                                <div class="rd-section-header">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                                    <span>Extracted Statements</span>
                                    <span class="rd-section-count">${mappedStatements.length}</span>
                                </div>
                                <div class="rd-statements-list">
                                    ${mappedStatements.slice(0, 5).map((stmt, i) => {
                                        const directive = (stmt.directive || '').toLowerCase();
                                        const dColors = { 'shall': '#ef4444', 'must': '#f97316', 'will': '#3b82f6', 'should': '#eab308', 'may': '#22c55e' };
                                        const dColor = dColors[directive] || '#64748b';
                                        return `
                                        <div class="rd-statement-item" style="--stmt-index: ${i}; --stmt-color: ${dColor};">
                                            <div class="rd-statement-header">
                                                ${directive ? `<span class="rd-statement-directive" style="background: ${dColor};">${directive.toUpperCase()}</span>` : ''}
                                                ${stmt.number ? `<span class="rd-statement-number">§ ${escapeHtml(stmt.number)}</span>` : ''}
                                            </div>
                                            <div class="rd-statement-text">${escapeHtml(stmt.description || '')}</div>
                                        </div>`;
                                    }).join('')}
                                    ${mappedStatements.length > 5 ? `<button class="rd-show-more" data-type="statements">Show ${mappedStatements.length - 5} more statements</button>` : ''}
                                </div>
                            </div>` : ''}

                            ${Object.keys(actionTypes).length > 0 ? `
                            <div class="rd-section rd-section-actions">
                                <div class="rd-section-header">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                                    <span>Action Types</span>
                                </div>
                                <div class="rd-action-chips">
                                    ${Object.entries(actionTypes).map(([action, cnt]) => `
                                        <span class="rd-action-chip" style="--chip-color: ${color};">
                                            <span class="rd-action-name">${escapeHtml(action)}</span>
                                            <span class="rd-action-count">${cnt}</span>
                                        </span>
                                    `).join('')}
                                </div>
                            </div>` : ''}

                            <!-- Card Footer Actions -->
                            <div class="rd-card-footer">
                                <button class="rd-footer-btn rd-footer-btn-primary" data-action="explore" data-role="${escapeHtml(name)}">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                                    <span>Deep Dive</span>
                                </button>
                                <button class="rd-footer-btn" data-action="connections" data-role="${escapeHtml(name)}">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="12" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><line x1="8.7" y1="10.7" x2="15.3" y2="7.3"/><line x1="8.7" y1="13.3" x2="15.3" y2="16.7"/></svg>
                                    <span>Connections</span>
                                </button>
                            </div>
                        </div>
                    </div>`;
                }).join('')}
            </div>

            <!-- No Results State -->
            <div class="rd-no-results" id="rd-no-results" style="display: none;">
                <div class="rd-no-results-icon">🔍</div>
                <div class="rd-no-results-title">No roles found</div>
                <div class="rd-no-results-text">Try adjusting your search or filters</div>
                <button class="rd-no-results-btn" id="rd-clear-filters">Clear Filters</button>
            </div>
        `;

        // v4.4.0: Initialize SmartSearch with enhanced functionality
        SmartSearch.init('roles-detail-search', {
            itemType: 'role',
            maxResults: 12,
            showRecent: true,
            getItems: () => searchableItems,
            onSelect: (item) => {
                // Scroll to and highlight the selected role card
                const roleId = item.type === 'role' ? item.id : item.roleId;
                const card = document.querySelector(`.rd-card[data-role="${roleId}"]`);
                if (card) {
                    // Clear filters first
                    document.querySelectorAll('.rd-card').forEach(c => c.style.display = '');
                    document.querySelectorAll('.rd-category-pill').forEach(p => p.classList.remove('rd-category-pill-active'));
                    document.querySelector('.rd-category-pill[data-category="all"]')?.classList.add('rd-category-pill-active');

                    // Expand the card if collapsed
                    card.classList.add('rd-card-expanded');

                    // Scroll to card
                    setTimeout(() => {
                        card.scrollIntoView({ behavior: 'smooth', block: 'center' });

                        // Cinematic highlight effect
                        card.classList.add('rd-card-highlight');
                        setTimeout(() => card.classList.remove('rd-card-highlight'), 2000);
                    }, 100);
                }
            },
            renderItem: (item, index, query) => {
                if (item.type === 'role') {
                    const color = getCategoryColorForRole(item.category);
                    const highlighted = SmartSearch.highlightMatch(item.name, query);
                    return `
                        <div class="smart-search-item" data-index="${index}">
                            <div class="smart-search-icon" style="background: linear-gradient(135deg, ${color}20, ${color}30);">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="10" r="3"/><path d="M12 13c-4 0-6 2-6 5h12c0-3-2-5-6-5"/></svg>
                            </div>
                            <div class="smart-search-content">
                                <div class="smart-search-title">${highlighted}</div>
                                <div class="smart-search-meta">
                                    <span class="smart-search-category" style="color:${color};">${item.category}</span>
                                    <span class="smart-search-count">${item.count} mentions</span>
                                    ${item.responsibilityCount > 0 ? `<span class="smart-search-count">${item.responsibilityCount} responsibilities</span>` : ''}
                                </div>
                            </div>
                            <div class="smart-search-badge" style="background: ${color};">Role</div>
                        </div>
                    `;
                } else if (item.type === 'responsibility') {
                    const color = getCategoryColorForRole(item.category);
                    const highlighted = SmartSearch.highlightMatch(truncate(item.text, 60), query);
                    return `
                        <div class="smart-search-item" data-index="${index}">
                            <div class="smart-search-icon" style="background: rgba(34, 197, 94, 0.15);">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                            </div>
                            <div class="smart-search-content">
                                <div class="smart-search-title">${highlighted}</div>
                                <div class="smart-search-meta">
                                    <span style="color:${color};">↳ ${item.roleName}</span>
                                </div>
                            </div>
                            <div class="smart-search-badge" style="background: #22c55e;">Resp</div>
                        </div>
                    `;
                } else if (item.type === 'statement') {
                    const dColors = { 'shall': '#ef4444', 'must': '#f97316', 'will': '#3b82f6', 'should': '#eab308', 'may': '#22c55e' };
                    const dColor = dColors[item.directive?.toLowerCase()] || '#64748b';
                    const highlighted = SmartSearch.highlightMatch(truncate(item.text, 60), query);
                    return `
                        <div class="smart-search-item" data-index="${index}">
                            <div class="smart-search-icon" style="background: ${dColor}20;">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${dColor}" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><line x1="16" y1="13" x2="8" y2="13"/></svg>
                            </div>
                            <div class="smart-search-content">
                                <div class="smart-search-title">${highlighted}</div>
                                <div class="smart-search-meta">
                                    <span style="color:${dColor}; font-weight: 600;">${item.directive?.toUpperCase() || ''}</span>
                                    <span>↳ ${item.roleName}</span>
                                </div>
                            </div>
                            <div class="smart-search-badge" style="background: ${dColor};">Stmt</div>
                        </div>
                    `;
                }
                return '';
            }
        });

        // Attach event handlers
        attachRoleDetailsEventHandlers(roleEntries);
    }

    /**
     * v4.4.0: Attach event handlers for enhanced role details
     */
    function attachRoleDetailsEventHandlers(roleEntries) {
        const debounce = getDebounce();

        // Category filter pills
        document.querySelectorAll('.rd-category-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                const category = pill.dataset.category;

                // Update active state
                document.querySelectorAll('.rd-category-pill').forEach(p => p.classList.remove('rd-category-pill-active'));
                pill.classList.add('rd-category-pill-active');

                // Filter cards
                const cards = document.querySelectorAll('.rd-card');
                let visibleCount = 0;
                cards.forEach(card => {
                    if (category === 'all' || card.dataset.category === category) {
                        card.style.display = '';
                        visibleCount++;
                    } else {
                        card.style.display = 'none';
                    }
                });

                // Show/hide no results
                document.getElementById('rd-no-results').style.display = visibleCount === 0 ? 'flex' : 'none';
            });
        });

        // View toggle buttons
        document.querySelectorAll('.rd-view-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.view;
                document.querySelectorAll('.rd-view-btn').forEach(b => b.classList.remove('rd-view-btn-active'));
                btn.classList.add('rd-view-btn-active');
                document.getElementById('roles-detail-list').dataset.view = view;

                // Auto-expand/collapse based on view
                if (view === 'expanded') {
                    document.querySelectorAll('.rd-card').forEach(c => c.classList.add('rd-card-expanded'));
                } else if (view === 'compact') {
                    document.querySelectorAll('.rd-card').forEach(c => c.classList.remove('rd-card-expanded'));
                }
            });
        });

        // Expand all button
        const expandAllBtn = document.getElementById('rd-expand-all');
        if (expandAllBtn) {
            expandAllBtn.addEventListener('click', () => {
                const cards = document.querySelectorAll('.rd-card');
                const allExpanded = Array.from(cards).every(c => c.classList.contains('rd-card-expanded'));

                cards.forEach(c => {
                    if (allExpanded) {
                        c.classList.remove('rd-card-expanded');
                    } else {
                        c.classList.add('rd-card-expanded');
                    }
                });

                // Update button text
                expandAllBtn.querySelector('span').textContent = allExpanded ? 'Expand All' : 'Collapse All';
                expandAllBtn.querySelector('svg').style.transform = allExpanded ? '' : 'rotate(180deg)';
            });
        }

        // Card expand buttons
        document.querySelectorAll('.rd-card-expand').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const card = btn.closest('.rd-card');
                card.classList.toggle('rd-card-expanded');
            });
        });

        // Card header click to expand
        document.querySelectorAll('.rd-card-header').forEach(header => {
            header.addEventListener('click', () => {
                const card = header.closest('.rd-card');
                card.classList.toggle('rd-card-expanded');
            });
        });

        // Show more buttons
        document.querySelectorAll('.rd-show-more').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const section = btn.closest('.rd-section');
                section.classList.toggle('rd-section-expanded');
                btn.style.display = 'none';
            });
        });

        // Clear filters button
        const clearFiltersBtn = document.getElementById('rd-clear-filters');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                // Reset search
                const searchInput = document.getElementById('roles-detail-search');
                if (searchInput) searchInput.value = '';

                // Reset category filter
                document.querySelectorAll('.rd-category-pill').forEach(p => p.classList.remove('rd-category-pill-active'));
                document.querySelector('.rd-category-pill[data-category="all"]')?.classList.add('rd-category-pill-active');

                // Show all cards
                document.querySelectorAll('.rd-card').forEach(c => c.style.display = '');
                document.getElementById('rd-no-results').style.display = 'none';
            });
        }

        // Footer action buttons - link to Data Explorer
        document.querySelectorAll('.rd-footer-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const roleName = btn.dataset.role;
                const roleData = roleEntries.find(([name]) => name === roleName)?.[1] || {};

                if (action === 'explore' && TWR.DataExplorer) {
                    TWR.DataExplorer.open();
                    setTimeout(() => {
                        TWR.DataExplorer.drillInto('role', roleName, roleData);
                    }, 600);
                } else if (action === 'connections' && TWR.DataExplorer) {
                    TWR.DataExplorer.open();
                    setTimeout(() => {
                        TWR.DataExplorer.drillInto('role-connections', roleName, { name: roleName });
                    }, 600);
                }
            });
        });

        // Explore button in card header - opens Data Explorer
        document.querySelectorAll('.rd-card-explore').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const roleName = btn.dataset.role;
                const roleData = roleEntries.find(([name]) => name === roleName)?.[1] || {};
                if (TWR.DataExplorer) {
                    TWR.DataExplorer.open();
                    setTimeout(() => {
                        TWR.DataExplorer.drillInto('role', roleName, roleData);
                    }, 600);
                }
            });
        });

        // Search input filtering
        const searchInput = document.getElementById('roles-detail-search');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(function() {
                const query = this.value.toLowerCase().trim();
                if (!query) {
                    document.querySelectorAll('.rd-card').forEach(card => {
                        card.style.display = '';
                    });
                    document.getElementById('rd-no-results').style.display = 'none';
                    return;
                }

                let visibleCount = 0;
                document.querySelectorAll('.rd-card').forEach(card => {
                    const roleName = card.dataset.role.toLowerCase();
                    const displayName = card.querySelector('.rd-card-title')?.textContent?.toLowerCase() || '';
                    const category = card.dataset.category.toLowerCase();
                    const content = card.textContent.toLowerCase();

                    const matches = roleName.includes(query) || displayName.includes(query) ||
                                   category.includes(query) || content.includes(query);

                    card.style.display = matches ? '' : 'none';
                    if (matches) visibleCount++;
                });

                document.getElementById('rd-no-results').style.display = visibleCount === 0 ? 'flex' : 'none';
            }, 200));
        }
    }
    
    /**
     * v3.0.98: Highlight role name within context text
     */
    function highlightRoleInContext(context, roleName) {
        const escapeHtml = getEscapeHtml();
        if (!context || !roleName) return escapeHtml(context);

        // Escape the context first
        const safeContext = escapeHtml(context);
        const safeRoleName = escapeHtml(roleName);

        // Create regex to find role name (case insensitive)
        try {
            const regex = new RegExp(`(${safeRoleName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
            return safeContext.replace(regex, '<mark class="role-highlight" style="background:rgba(74,144,217,0.3);padding:1px 2px;border-radius:2px;">$1</mark>');
        } catch (e) {
            return safeContext;
        }
    }

    /**
     * v3.0.114: Render mapped statements for a role from Statement Forge
     */
    function renderMappedStatements(roleData, roleName, escapeHtml, truncate) {
        // Check for mapped statements from auto-mapping
        const mappedStatements = roleData.mapped_statements || [];

        // Also check global State for mapping
        const State = getState();
        const globalMapping = State.roleStatementMapping?.role_to_statements || {};
        const globalStmts = globalMapping[roleName] || [];

        // Combine (prefer roleData.mapped_statements if available)
        const statements = mappedStatements.length > 0 ? mappedStatements : globalStmts;

        if (statements.length === 0) {
            return '';
        }

        // Color mapping for directive badges
        const directiveColors = {
            'shall': '#ef4444',
            'must': '#f97316',
            'will': '#3b82f6',
            'should': '#eab308',
            'may': '#22c55e'
        };

        return `
            <div class="mapped-statements" style="margin-top:16px;border-top:1px solid var(--border-default);padding-top:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <strong style="font-size:12px;color:var(--text-muted);">
                        <i data-lucide="file-text" style="width:14px;height:14px;vertical-align:middle;margin-right:4px;"></i>
                        Extracted Statements (${statements.length})
                    </strong>
                    <button class="btn btn-ghost btn-xs toggle-statements-btn" onclick="this.closest('.mapped-statements').classList.toggle('collapsed')" style="font-size:11px;">
                        <span class="show-text">Show</span>
                        <span class="hide-text" style="display:none;">Hide</span>
                    </button>
                </div>
                <div class="statements-list" style="display:none;">
                    ${statements.slice(0, 10).map(stmt => {
                        const directive = (stmt.directive || '').toLowerCase();
                        const color = directiveColors[directive] || 'var(--text-muted)';
                        return `
                            <div class="statement-item" style="background:var(--bg-tertiary);padding:8px 12px;border-radius:4px;margin-bottom:6px;font-size:13px;border-left:3px solid ${color};">
                                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
                                    <span style="flex:1;">${escapeHtml(truncate(stmt.description || '', 200))}</span>
                                    ${directive ? `<span style="background:${color};color:#fff;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:600;text-transform:uppercase;white-space:nowrap;">${directive}</span>` : ''}
                                </div>
                                ${stmt.number ? `<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">§ ${escapeHtml(stmt.number)}</div>` : ''}
                            </div>
                        `;
                    }).join('')}
                    ${statements.length > 10 ? `<div style="color:var(--text-muted);font-size:12px;padding:4px;">...and ${statements.length - 10} more statements</div>` : ''}
                </div>
            </div>
            <style>
                .mapped-statements .statements-list { display: none; }
                .mapped-statements:not(.collapsed) .statements-list { display: block; }
                .mapped-statements:not(.collapsed) .show-text { display: none; }
                .mapped-statements:not(.collapsed) .hide-text { display: inline !important; }
            </style>
        `;
    }

    /**
     * v3.0.98: Initialize document filter dropdown
     * v3.0.107: Fixed to populate from source_documents or current filename
     * v3.0.116: Also fetch from scan history API for complete document list
     */
    async function initDocumentFilter() {
        const State = getState();
        const api = getApi();
        const filterSelect = document.getElementById('roles-document-filter');
        if (!filterSelect) return;

        // Build list of unique documents
        const rolesData = State.roles?.roles || State.roles || {};
        const documents = new Set();

        // v3.0.107: Get current filename as fallback
        const currentFilename = State.filename || State.currentFilename || '';

        // Get documents from roles source_documents
        Object.values(rolesData).forEach(data => {
            const sourceDocs = data.source_documents || [];
            if (sourceDocs.length > 0) {
                sourceDocs.forEach(doc => documents.add(doc));
            }
        });

        // v3.0.116: Also fetch from scan history API
        try {
            console.log('[TWR Roles] Fetching scan history for document filter...');
            const response = await fetch('/api/scan-history?limit=50');
            const result = await response.json();
            console.log('[TWR Roles] Scan history response:', result);
            if (result.success && result.data) {
                result.data.forEach(scan => {
                    if (scan.filename) {
                        documents.add(scan.filename);
                        console.log('[TWR Roles] Added document from scan history:', scan.filename);
                    }
                });
            }
        } catch (e) {
            console.warn('[TWR Roles] Could not fetch scan history for document filter:', e);
        }

        console.log('[TWR Roles] Total documents for filter:', documents.size, Array.from(documents));

        // Add current filename if we have one
        if (currentFilename) {
            documents.add(currentFilename);
        }

        // Clear and populate options
        filterSelect.innerHTML = '<option value="all">All Documents</option>';

        Array.from(documents).sort().forEach(doc => {
            const option = document.createElement('option');
            option.value = doc;
            option.textContent = doc.length > 40 ? doc.substring(0, 37) + '...' : doc;
            option.title = doc;
            filterSelect.appendChild(option);
        });

        // Add change handler
        if (!filterSelect._initialized) {
            filterSelect.addEventListener('change', () => {
                // Re-render all tabs with filter applied
                renderRolesOverview();
                renderRolesDetails();
                renderRolesMatrix();
            });
            filterSelect._initialized = true;
        }
    }

    // v3.1.10: Enhanced RACI state for caching API data
    let _raciApiCache = null;
    let _raciApiLoading = false;

    /**
     * Enhanced RACI Matrix Renderer
     * v3.1.10: Now uses backend API for comprehensive RACI computation from stored data.
     * Falls back to local computation if API unavailable or no historical data.
     */
    async function renderRolesMatrix() {
        const escapeHtml = getEscapeHtml();
        const State = getState();
        const container = document.getElementById('matrix-container');
        if (!container) return;

        // v4.0.3: Load adjudication data
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        const filterCritical = State.matrixFilterCritical || false;
        const sortBy = State.matrixSort || 'total';

        // First try to get data from new RACI API (for historical/aggregated data)
        let raciData = null;
        let usingApiData = false;

        // Only fetch from API if we don't have realtime scan data with action_types
        const rolesData = State.roles?.roles || State.roles || {};
        const roleEntries = Object.entries(rolesData);
        // Check if any role has actual action_types data (from real-time scan, not aggregated)
        const hasActionTypes = roleEntries.some(([, data]) =>
            typeof data === 'object' && data.action_types && Object.keys(data.action_types).length > 0
        );
        console.log('[RACI] State check - roleEntries:', roleEntries.length, 'hasActionTypes:', hasActionTypes);

        // v3.1.10: Fetch RACI data with fallback to aggregated roles
        if (!_raciApiLoading && !hasActionTypes) {
            try {
                if (!_raciApiCache) {
                    _raciApiLoading = true;

                    // Try new RACI endpoint first, fallback to aggregated
                    let response = await fetch('/api/roles/raci');
                    let result = await response.json();

                    if (result.success && result.data?.roles && Object.keys(result.data.roles).length > 0) {
                        _raciApiCache = result.data;
                    } else {
                        // Fallback: Use aggregated roles
                        response = await fetch('/api/roles/aggregated?include_deliverables=false');
                        result = await response.json();

                        if (result.success && result.data && result.data.length > 0) {
                            const roles = {};
                            const summary = { type_distribution: { R: 0, A: 0, C: 0, I: 0 } };

                            result.data.forEach(role => {
                                const respCount = role.responsibility_count || role.total_mentions || 1;
                                // Estimate RACI distribution from responsibility count
                                const r = Math.ceil(respCount * 0.7);
                                const c = Math.floor(respCount * 0.2);
                                const i = Math.floor(respCount * 0.1);

                                roles[role.role_name] = {
                                    R: r, A: 0, C: c, I: i,
                                    normalized_name: role.normalized_name,
                                    category: role.category,
                                    documents: role.documents || [],
                                    total_mentions: role.total_mentions,
                                    primary_type: 'R'
                                };

                                summary.type_distribution.R += r;
                                summary.type_distribution.C += c;
                                summary.type_distribution.I += i;
                            });

                            _raciApiCache = { roles, summary };
                        }
                    }
                    _raciApiLoading = false;
                }

                raciData = _raciApiCache;
                const apiRoleCount = Object.keys(raciData?.roles || {}).length;
                usingApiData = apiRoleCount > 0;
            } catch (e) {
                console.error('[RACI] API error:', e);
                _raciApiLoading = false;
            }
        }

        // Build RACI matrix
        const raciMatrix = {};

        if (usingApiData && raciData?.roles) {
            // Use API data - already computed from stored responsibilities
            console.log('[RACI] Populating matrix from API data with', Object.keys(raciData.roles).length, 'roles');
            Object.entries(raciData.roles).forEach(([name, data]) => {
                raciMatrix[name] = {
                    R: data.R || 0,
                    A: data.A || 0,
                    C: data.C || 0,
                    I: data.I || 0,
                    normalized_name: data.normalized_name,
                    category: data.category,
                    documents: data.documents || [],
                    primary_type: data.primary_type,
                    document_breakdown: data.document_breakdown,
                    action_types: data.action_types || {}
                };

                // Apply user edits
                if (State.raciEdits && State.raciEdits[name]) {
                    Object.entries(State.raciEdits[name]).forEach(([type, value]) => {
                        raciMatrix[name][type] = value;
                    });
                }
            });
            console.log('[RACI] Matrix populated, first role sample:', Object.entries(raciMatrix)[0]);
        } else if (roleEntries.length > 0) {
            // Fall back to local computation from State.roles
            console.log('[RACI] Using local fallback with', roleEntries.length, 'roles');
            roleEntries.forEach(([name, data]) => {
                const actionTypes = typeof data === 'object' ? (data.action_types || {}) : {};

                raciMatrix[name] = { R: 0, A: 0, C: 0, I: 0 };

                // If we have action_types, use them for RACI computation
                if (Object.keys(actionTypes).length > 0) {
                    Object.entries(actionTypes).forEach(([action, count]) => {
                        const actionLower = action.toLowerCase();

                        if (/^(perform|execute|implement|develop|define|lead|ensure|maintain|conduct|create|prepare|manage|oversee|verif|valid)/i.test(actionLower)) {
                            raciMatrix[name].R += count;
                        } else if (/^(approv|authoriz|sign|certif|accept)/i.test(actionLower)) {
                            raciMatrix[name].A += count;
                        } else if (/^(review|coordinat|support|consult|advis|assist|collaborat)/i.test(actionLower)) {
                            raciMatrix[name].C += count;
                        } else if (/^(receiv|report|monitor|inform|notif|communicat|track|provid)/i.test(actionLower)) {
                            raciMatrix[name].I += count;
                        } else {
                            raciMatrix[name].R += count;
                        }
                    });
                } else {
                    // No action_types - use total_mentions as rough R count
                    const mentions = typeof data === 'object' ? (data.total_mentions || data.mention_count || data.count || 0) : 0;
                    if (mentions > 0) {
                        raciMatrix[name].R = mentions;
                    }
                    raciMatrix[name]._noActionTypes = true;
                }

                if (State.raciEdits && State.raciEdits[name]) {
                    Object.entries(State.raciEdits[name]).forEach(([type, value]) => {
                        raciMatrix[name][type] = value;
                    });
                }
            });
        }

        // v4.5.2: Enrich with dictionary roles that may not be in scan data
        // This ensures ALL known roles appear in the RACI chart
        if (adjLookup) {
            const dictCache = adjLookup.getCached();
            if (dictCache) {
                // dictCache keys are normalized (lowercase) names, values have is_active, is_deliverable, category
                // We need to add dictionary roles not already in the matrix
                // First build a lowercase lookup of existing matrix roles
                const existingLower = new Set(Object.keys(raciMatrix).map(n => n.toLowerCase().trim()));

                Object.entries(dictCache).forEach(([normalizedKey, dictEntry]) => {
                    if (!existingLower.has(normalizedKey) && dictEntry.is_active) {
                        // This dictionary role is not in scan data - add it with zero RACI
                        // Use the normalized key as display name (capitalize first letters)
                        const displayName = normalizedKey.replace(/\b\w/g, c => c.toUpperCase());
                        raciMatrix[displayName] = {
                            R: 0, A: 0, C: 0, I: 0,
                            normalized_name: displayName,
                            category: dictEntry.category || 'Dictionary',
                            documents: [],
                            primary_type: null,
                            _dictionaryOnly: true,
                            _noActionTypes: true
                        };
                    }
                });
            }
        }

        // v4.5.2: Mark all roles with their dictionary status
        Object.keys(raciMatrix).forEach(name => {
            const adj = adjLookup ? adjLookup.lookup(name) : null;
            raciMatrix[name]._inDictionary = !!adj;
            raciMatrix[name]._isDeliverable = adj?.is_deliverable || false;
        });

        if (Object.keys(raciMatrix).length === 0) {
            container.innerHTML = `
                <div class="raci-empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <line x1="3" y1="9" x2="21" y2="9"/>
                        <line x1="9" y1="21" x2="9" y2="9"/>
                    </svg>
                    <h4>No RACI Data Available</h4>
                    <p class="text-muted">Scan documents to extract roles and build the RACI matrix.</p>
                </div>`;
            return;
        }

        State.raciMatrix = raciMatrix;

        // v4.5.2: Dictionary filter support
        const dictFilter = State.matrixDictFilter || 'all'; // 'all', 'dictionary', 'discovered'
        let roleNames = Object.keys(raciMatrix);

        if (dictFilter === 'dictionary') {
            roleNames = roleNames.filter(name => raciMatrix[name]._inDictionary);
        } else if (dictFilter === 'discovered') {
            roleNames = roleNames.filter(name => !raciMatrix[name]._dictionaryOnly);
        }

        if (filterCritical) {
            roleNames = roleNames.filter(name => {
                const raci = raciMatrix[name];
                return raci.R > 0 || raci.A > 0;
            });
        }

        roleNames.sort((a, b) => {
            const raciA = raciMatrix[a];
            const raciB = raciMatrix[b];
            const totalA = raciA.R + raciA.A + raciA.C + raciA.I;
            const totalB = raciB.R + raciB.A + raciB.C + raciB.I;

            switch (sortBy) {
                case 'name': return a.localeCompare(b);
                case 'responsible': return raciB.R - raciA.R;
                case 'accountable': return raciB.A - raciA.A;
                default: return totalB - totalA;
            }
        });

        State.matrixRoleNames = roleNames;

        // Calculate summary stats — always compute from actual raciMatrix for accuracy
        const summary = _computeRaciSummary(raciMatrix);

        // Build enhanced HTML with summary dashboard
        let html = `
            <div class="raci-dashboard">
                <div class="raci-summary-cards">
                    <div class="raci-summary-card raci-card-r" title="Roles with Responsible assignments">
                        <div class="raci-card-icon">R</div>
                        <div class="raci-card-content">
                            <span class="raci-card-value">${summary.type_distribution?.R || 0}</span>
                            <span class="raci-card-label">Responsible</span>
                        </div>
                    </div>
                    <div class="raci-summary-card raci-card-a" title="Roles with Accountable assignments">
                        <div class="raci-card-icon">A</div>
                        <div class="raci-card-content">
                            <span class="raci-card-value">${summary.type_distribution?.A || 0}</span>
                            <span class="raci-card-label">Accountable</span>
                        </div>
                    </div>
                    <div class="raci-summary-card raci-card-c" title="Roles with Consulted assignments">
                        <div class="raci-card-icon">C</div>
                        <div class="raci-card-content">
                            <span class="raci-card-value">${summary.type_distribution?.C || 0}</span>
                            <span class="raci-card-label">Consulted</span>
                        </div>
                    </div>
                    <div class="raci-summary-card raci-card-i" title="Roles with Informed assignments">
                        <div class="raci-card-icon">I</div>
                        <div class="raci-card-content">
                            <span class="raci-card-value">${summary.type_distribution?.I || 0}</span>
                            <span class="raci-card-label">Informed</span>
                        </div>
                    </div>
                </div>
                <div class="raci-distribution-bar" title="RACI Distribution">
                    ${_buildRaciDistributionBar(summary.type_distribution)}
                </div>
            </div>
            <table class="raci-matrix-table"><thead><tr>
                <th>Role</th>
                <th class="raci-header raci-r" title="Responsible - performs the work">R</th>
                <th class="raci-header raci-a" title="Accountable - approves the work">A</th>
                <th class="raci-header raci-c" title="Consulted - provides input">C</th>
                <th class="raci-header raci-i" title="Informed - kept in the loop">I</th>
                <th>Total</th>
                <th class="raci-heatmap-col" title="Visual distribution">Distribution</th>
            </tr></thead><tbody>`;

        // Calculate max for heatmap scaling
        const maxTotal = Math.max(...roleNames.map(n => {
            const r = raciMatrix[n];
            return r.R + r.A + r.C + r.I;
        }), 1);

        roleNames.forEach(roleName => {
            const raci = raciMatrix[roleName];
            const displayName = raci.normalized_name || (typeof rolesData[roleName] === 'object' ? (rolesData[roleName].canonical_name || roleName) : roleName);
            const total = raci.R + raci.A + raci.C + raci.I;
            const hasREdit = State.raciEdits?.[roleName]?.R !== undefined;
            const hasAEdit = State.raciEdits?.[roleName]?.A !== undefined;
            const hasCEdit = State.raciEdits?.[roleName]?.C !== undefined;
            const hasIEdit = State.raciEdits?.[roleName]?.I !== undefined;
            const docCount = raci.documents?.length || 0;

            // Escape role name for onclick (handle quotes)
            const escapedRoleName = roleName.replace(/'/g, "\\'").replace(/"/g, "&quot;");

            // Build mini heatmap bar
            const heatmapBar = _buildRaciHeatmapBar(raci, maxTotal);

            // v4.5.2: Dictionary indicator
            const inDict = raci._inDictionary;
            const dictOnlyRole = raci._dictionaryOnly;
            const dictBadge = inDict
                ? `<span class="raci-dict-badge" title="In Role Dictionary">D</span>`
                : '';

            html += `<tr data-role="${escapeHtml(roleName)}" class="${raci.primary_type ? 'raci-primary-' + raci.primary_type.toLowerCase() : ''} ${dictOnlyRole ? 'raci-dict-only' : ''}">
                <td class="role-name raci-role-clickable" title="Click for details: ${escapeHtml(roleName)}${docCount ? ' (' + docCount + ' docs)' : ''}${inDict ? ' [In Dictionary]' : ''}" onclick="TWR.Roles.showRaciDrilldown('${escapedRoleName}')">
                    ${dictBadge}${escapeHtml(displayName)}${adjLookup ? adjLookup.getBadge(displayName, { compact: true, size: 'sm' }) : ''}
                    ${docCount ? `<span class="raci-doc-count" title="${docCount} documents">${docCount}</span>` : ''}
                </td>
                <td class="raci-cell ${raci.R > 0 ? 'raci-r' : ''} ${hasREdit ? 'edited' : ''}" onclick="TWR.Roles.editRaciCell('${escapedRoleName}', 'R', this)" title="Click to edit">${raci.R > 0 ? `<span class="raci-cell-badge raci-badge-r">${raci.R}</span>` : '-'}</td>
                <td class="raci-cell ${raci.A > 0 ? 'raci-a' : ''} ${hasAEdit ? 'edited' : ''}" onclick="TWR.Roles.editRaciCell('${escapedRoleName}', 'A', this)" title="Click to edit">${raci.A > 0 ? `<span class="raci-cell-badge raci-badge-a">${raci.A}</span>` : '-'}</td>
                <td class="raci-cell ${raci.C > 0 ? 'raci-c' : ''} ${hasCEdit ? 'edited' : ''}" onclick="TWR.Roles.editRaciCell('${escapedRoleName}', 'C', this)" title="Click to edit">${raci.C > 0 ? `<span class="raci-cell-badge raci-badge-c">${raci.C}</span>` : '-'}</td>
                <td class="raci-cell ${raci.I > 0 ? 'raci-i' : ''} ${hasIEdit ? 'edited' : ''}" onclick="TWR.Roles.editRaciCell('${escapedRoleName}', 'I', this)" title="Click to edit">${raci.I > 0 ? `<span class="raci-cell-badge raci-badge-i">${raci.I}</span>` : '-'}</td>
                <td class="raci-total">${total}</td>
                <td class="raci-heatmap-cell">${heatmapBar}</td>
            </tr>`;
        });

        html += '</tbody></table>';

        // Add data source indicator
        // v4.5.2: Show dictionary/discovered breakdown
        const dictCount = roleNames.filter(n => raciMatrix[n]._inDictionary).length;
        const discoveredCount = roleNames.filter(n => !raciMatrix[n]._dictionaryOnly).length;
        const dictOnlyCount = roleNames.filter(n => raciMatrix[n]._dictionaryOnly).length;

        html += `
            <div class="raci-footer">
                <div class="raci-footer-top">
                    <span class="raci-source-badge ${usingApiData ? 'raci-source-historical' : 'raci-source-realtime'}">
                        ${usingApiData ? 'Historical Data' : 'Real-time Scan'}
                    </span>
                    <span class="raci-role-count">${roleNames.length} roles</span>
                    ${dictCount > 0 ? `<span class="raci-dict-count" title="${dictCount} roles in dictionary, ${dictOnlyCount} dictionary-only"><span class="raci-dict-badge" style="position:static;margin-right:4px;">D</span>${dictCount} in dictionary</span>` : ''}
                </div>
            </div>`;

        container.innerHTML = html;
    }

    /**
     * Compute RACI summary from local matrix data
     */
    function _computeRaciSummary(raciMatrix) {
        const distribution = { R: 0, A: 0, C: 0, I: 0 };
        Object.values(raciMatrix).forEach(raci => {
            distribution.R += raci.R || 0;
            distribution.A += raci.A || 0;
            distribution.C += raci.C || 0;
            distribution.I += raci.I || 0;
        });
        return { type_distribution: distribution };
    }

    /**
     * Build RACI distribution bar HTML
     */
    function _buildRaciDistributionBar(dist) {
        if (!dist) return '';
        const total = (dist.R || 0) + (dist.A || 0) + (dist.C || 0) + (dist.I || 0);
        if (total === 0) return '<div class="raci-dist-empty">No data</div>';

        const rPct = ((dist.R || 0) / total * 100).toFixed(1);
        const aPct = ((dist.A || 0) / total * 100).toFixed(1);
        const cPct = ((dist.C || 0) / total * 100).toFixed(1);
        const iPct = ((dist.I || 0) / total * 100).toFixed(1);

        return `
            <div class="raci-dist-segment raci-dist-r" style="width: ${rPct}%" title="Responsible: ${rPct}%"></div>
            <div class="raci-dist-segment raci-dist-a" style="width: ${aPct}%" title="Accountable: ${aPct}%"></div>
            <div class="raci-dist-segment raci-dist-c" style="width: ${cPct}%" title="Consulted: ${cPct}%"></div>
            <div class="raci-dist-segment raci-dist-i" style="width: ${iPct}%" title="Informed: ${iPct}%"></div>
        `;
    }

    /**
     * Build mini heatmap bar for a single role
     */
    function _buildRaciHeatmapBar(raci, maxTotal) {
        const total = raci.R + raci.A + raci.C + raci.I;
        if (total === 0) return '<div class="raci-heatmap-empty">-</div>';

        const rPct = (raci.R / total * 100).toFixed(0);
        const aPct = (raci.A / total * 100).toFixed(0);
        const cPct = (raci.C / total * 100).toFixed(0);
        const iPct = (raci.I / total * 100).toFixed(0);

        // Scale width based on total relative to max
        const widthPct = Math.max(20, (total / maxTotal) * 100);

        return `
            <div class="raci-heatmap-bar" style="width: ${widthPct}%">
                ${raci.R > 0 ? `<div class="raci-heat-r" style="width: ${rPct}%"></div>` : ''}
                ${raci.A > 0 ? `<div class="raci-heat-a" style="width: ${aPct}%"></div>` : ''}
                ${raci.C > 0 ? `<div class="raci-heat-c" style="width: ${cPct}%"></div>` : ''}
                ${raci.I > 0 ? `<div class="raci-heat-i" style="width: ${iPct}%"></div>` : ''}
            </div>
        `;
    }

    /**
     * Clear RACI cache (call when new data is loaded)
     */
    function clearRaciCache() {
        console.log('[RACI] Cache cleared');
        _raciApiCache = null;
        _raciApiLoading = false;
    }

    /**
     * Show RACI drilldown modal for a specific role
     * v3.1.10: Shows per-document breakdown with mini charts
     */
    function showRaciDrilldown(roleName) {
        const escapeHtml = getEscapeHtml();
        const showModal = getShowModal();
        const State = getState();

        const raci = State.raciMatrix?.[roleName];
        if (!raci) {
            console.warn('[RACI] No data for role:', roleName);
            return;
        }

        const total = raci.R + raci.A + raci.C + raci.I;
        const docs = raci.document_breakdown || {};

        // Build document breakdown table
        let docRows = '';
        Object.entries(docs).forEach(([docId, docData]) => {
            const docTotal = docData.R + docData.A + docData.C + docData.I;
            docRows += `
                <tr>
                    <td class="doc-name" title="${escapeHtml(docData.filename)}">${escapeHtml(docData.filename)}</td>
                    <td class="raci-val ${docData.R > 0 ? 'raci-r' : ''}">${docData.R || '-'}</td>
                    <td class="raci-val ${docData.A > 0 ? 'raci-a' : ''}">${docData.A || '-'}</td>
                    <td class="raci-val ${docData.C > 0 ? 'raci-c' : ''}">${docData.C || '-'}</td>
                    <td class="raci-val ${docData.I > 0 ? 'raci-i' : ''}">${docData.I || '-'}</td>
                    <td class="doc-total">${docTotal}</td>
                </tr>`;
        });

        if (!docRows) {
            docRows = '<tr><td colspan="6" class="text-muted text-center">No per-document breakdown available</td></tr>';
        }

        // Build pie chart data for primary visual
        const chartId = 'raci-drilldown-chart-' + Date.now();

        const modalContent = `
            <div class="raci-drilldown-modal">
                <div class="raci-drilldown-header">
                    <h3>${escapeHtml(raci.normalized_name || roleName)}</h3>
                    <span class="raci-drilldown-category">${escapeHtml(raci.category || 'Role')}</span>
                </div>

                <div class="raci-drilldown-summary">
                    <div class="raci-drilldown-chart">
                        <canvas id="${chartId}" width="180" height="180"></canvas>
                    </div>
                    <div class="raci-drilldown-stats">
                        <div class="raci-stat-row">
                            <span class="raci-stat-dot raci-r"></span>
                            <span class="raci-stat-label">Responsible</span>
                            <span class="raci-stat-value">${raci.R}</span>
                            <span class="raci-stat-pct">${total > 0 ? ((raci.R / total) * 100).toFixed(0) : 0}%</span>
                        </div>
                        <div class="raci-stat-row">
                            <span class="raci-stat-dot raci-a"></span>
                            <span class="raci-stat-label">Accountable</span>
                            <span class="raci-stat-value">${raci.A}</span>
                            <span class="raci-stat-pct">${total > 0 ? ((raci.A / total) * 100).toFixed(0) : 0}%</span>
                        </div>
                        <div class="raci-stat-row">
                            <span class="raci-stat-dot raci-c"></span>
                            <span class="raci-stat-label">Consulted</span>
                            <span class="raci-stat-value">${raci.C}</span>
                            <span class="raci-stat-pct">${total > 0 ? ((raci.C / total) * 100).toFixed(0) : 0}%</span>
                        </div>
                        <div class="raci-stat-row">
                            <span class="raci-stat-dot raci-i"></span>
                            <span class="raci-stat-label">Informed</span>
                            <span class="raci-stat-value">${raci.I}</span>
                            <span class="raci-stat-pct">${total > 0 ? ((raci.I / total) * 100).toFixed(0) : 0}%</span>
                        </div>
                        <div class="raci-stat-total">
                            <span class="raci-stat-label">Total Assignments</span>
                            <span class="raci-stat-value">${total}</span>
                        </div>
                    </div>
                </div>

                <div class="raci-drilldown-docs">
                    <h4>Document Breakdown</h4>
                    <div class="raci-docs-table-wrapper">
                        <table class="raci-docs-table">
                            <thead>
                                <tr>
                                    <th>Document</th>
                                    <th class="raci-th-r">R</th>
                                    <th class="raci-th-a">A</th>
                                    <th class="raci-th-c">C</th>
                                    <th class="raci-th-i">I</th>
                                    <th>Total</th>
                                </tr>
                            </thead>
                            <tbody>${docRows}</tbody>
                        </table>
                    </div>
                </div>

                <div class="raci-drilldown-insights">
                    <h4>Insights</h4>
                    <ul>
                        ${raci.primary_type ? `<li>Primary Role Type: <strong>${_getRaciTypeName(raci.primary_type)}</strong></li>` : ''}
                        ${raci.documents?.length ? `<li>Appears in <strong>${raci.documents.length}</strong> document${raci.documents.length > 1 ? 's' : ''}</li>` : ''}
                        ${raci.A > 0 ? `<li><span class="insight-important">Has approval/sign-off authority</span></li>` : ''}
                        ${raci.R > raci.C + raci.I ? '<li>Primarily an execution-focused role</li>' : ''}
                        ${raci.C + raci.I > raci.R + raci.A ? '<li>Primarily a support/advisory role</li>' : ''}
                    </ul>
                </div>
            </div>`;

        showContentModal('RACI Analysis: ' + (raci.normalized_name || roleName), modalContent, {
            size: 'large',
            onShown: () => {
                // Render Chart.js pie chart if available
                _renderRaciDrilldownChart(chartId, raci);
            }
        });
    }

    /**
     * Get human-readable RACI type name
     */
    function _getRaciTypeName(type) {
        const names = { R: 'Responsible', A: 'Accountable', C: 'Consulted', I: 'Informed' };
        return names[type] || type;
    }

    /**
     * Render Chart.js pie chart for RACI drilldown
     */
    function _renderRaciDrilldownChart(chartId, raci) {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;

        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            // Fallback: simple CSS pie chart
            const total = raci.R + raci.A + raci.C + raci.I;
            if (total === 0) {
                canvas.parentElement.innerHTML = '<div class="raci-chart-empty">No data</div>';
                return;
            }

            const rPct = (raci.R / total) * 100;
            const aPct = (raci.A / total) * 100;
            const cPct = (raci.C / total) * 100;
            const iPct = (raci.I / total) * 100;

            canvas.parentElement.innerHTML = `
                <div class="raci-css-pie" style="background: conic-gradient(
                    #3498db 0% ${rPct}%,
                    #9b59b6 ${rPct}% ${rPct + aPct}%,
                    #2ecc71 ${rPct + aPct}% ${rPct + aPct + cPct}%,
                    #f39c12 ${rPct + aPct + cPct}% 100%
                )"></div>`;
            return;
        }

        // Chart.js doughnut chart
        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Responsible', 'Accountable', 'Consulted', 'Informed'],
                datasets: [{
                    data: [raci.R, raci.A, raci.C, raci.I],
                    backgroundColor: ['#3498db', '#9b59b6', '#2ecc71', '#f39c12'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                cutout: '60%',
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    function editRaciCell(roleName, raciType, cellElement) {
        // v3.4.0: Show a detailed modal with actual responsibilities before allowing reclassification
        showRaciResponsibilitiesModal(roleName, raciType);
    }

    /**
     * v5.1.0: Enhanced RACI detail popup with action verb breakdown, document sources, and statements
     */
    async function showRaciResponsibilitiesModal(roleName, raciType) {
        const escapeHtml = getEscapeHtml();
        const showModal = getShowModal();
        const State = getState();
        const toast = getToast();

        const raciNames = { 'R': 'Responsible', 'A': 'Accountable', 'C': 'Consulted', 'I': 'Informed' };
        const raciDescriptions = {
            'R': 'Performs the work to complete the task',
            'A': 'Has final authority and approval',
            'C': 'Provides input before decisions are made',
            'I': 'Is kept informed of progress and outcomes'
        };
        const raciColors = {
            'R': { gradient: 'linear-gradient(135deg, #3498db, #2980b9)', bg: 'rgba(52,152,219,0.08)', border: '#3498db' },
            'A': { gradient: 'linear-gradient(135deg, #9b59b6, #8e44ad)', bg: 'rgba(155,89,182,0.08)', border: '#9b59b6' },
            'C': { gradient: 'linear-gradient(135deg, #2ecc71, #27ae60)', bg: 'rgba(46,204,113,0.08)', border: '#2ecc71' },
            'I': { gradient: 'linear-gradient(135deg, #f39c12, #e67e22)', bg: 'rgba(243,156,18,0.08)', border: '#f39c12' }
        };

        // Regex patterns matching lines 1939-1949 for classifying verbs into RACI types
        const raciPatterns = {
            'R': /^(perform|execute|implement|develop|define|lead|ensure|maintain|conduct|create|prepare|manage|oversee|verif|valid)/i,
            'A': /^(approv|authoriz|sign|certif|accept)/i,
            'C': /^(review|coordinat|support|consult|advis|assist|collaborat)/i,
            'I': /^(receiv|report|monitor|inform|notif|communicat|track|provid)/i
        };

        const raci = State.raciMatrix?.[roleName];
        if (!raci) { toast('warning', `No RACI data found for ${roleName}`); return; }

        const count = raci[raciType] || 0;
        const colors = raciColors[raciType];
        const typeLower = raciType.toLowerCase();

        // ── Action Verb Breakdown ──
        // v5.0.0: Prefer action_types from RACI API data (computed from DB), fall back to roles state
        const rolesData = State.roles?.roles || State.roles || {};
        const roleData = typeof rolesData[roleName] === 'object' ? rolesData[roleName] : {};
        const raciActionTypes = raci.action_types || {};
        const roleActionTypes = roleData.action_types || {};
        const actionTypes = Object.keys(raciActionTypes).length > 0 ? raciActionTypes : roleActionTypes;

        // Filter verbs that match THIS RACI type
        const matchingVerbs = [];
        let verbTotal = 0;
        Object.entries(actionTypes).forEach(([verb, cnt]) => {
            if (raciPatterns[raciType]?.test(verb.toLowerCase())) {
                matchingVerbs.push({ verb, count: cnt });
                verbTotal += cnt;
            } else if (raciType === 'R' && !raciPatterns.A.test(verb) && !raciPatterns.C.test(verb) && !raciPatterns.I.test(verb)) {
                // Default bucket goes to R
                matchingVerbs.push({ verb, count: cnt });
                verbTotal += cnt;
            }
        });
        matchingVerbs.sort((a, b) => b.count - a.count);
        const topVerbs = matchingVerbs.slice(0, 8); // Show top 8
        const maxVerbCount = topVerbs.length > 0 ? topVerbs[0].count : 1;

        let verbChartHtml = '';
        if (topVerbs.length > 0) {
            verbChartHtml = `<div class="raci-detail-section">
                <div class="raci-detail-section-title">Action Verb Breakdown</div>
                <div class="raci-verb-chart">
                    ${topVerbs.map(v => {
                        const pct = ((v.count / verbTotal) * 100).toFixed(0);
                        const barW = ((v.count / maxVerbCount) * 100).toFixed(1);
                        return `<div class="raci-verb-row">
                            <span class="raci-verb-label">${escapeHtml(v.verb)}</span>
                            <div class="raci-verb-track">
                                <div class="raci-verb-bar raci-verb-${typeLower}" style="width:0%" data-width="${barW}%"></div>
                            </div>
                            <span class="raci-verb-count">${v.count} <span class="raci-verb-pct">(${pct}%)</span></span>
                        </div>`;
                    }).join('')}
                    ${matchingVerbs.length > 8 ? `<div class="raci-verb-more">+ ${matchingVerbs.length - 8} more verbs</div>` : ''}
                </div>
            </div>`;
        } else {
            verbChartHtml = `<div class="raci-detail-section">
                <div class="raci-detail-section-title">Action Verb Breakdown</div>
                <div class="raci-verb-empty">No individual action verb data available. Count is based on aggregated analysis.</div>
            </div>`;
        }

        // ── Source Documents ──
        const docs = raci.documents || roleData.documents || [];
        let docsHtml = '';
        if (docs.length > 0) {
            const shown = docs.slice(0, 6);
            const remaining = docs.length - 6;
            docsHtml = `<div class="raci-detail-section">
                <div class="raci-detail-section-title">Source Documents</div>
                <div class="raci-doc-chips">
                    ${shown.map(d => `<span class="raci-doc-chip" title="${escapeHtml(d)}">${escapeHtml(d.length > 28 ? d.substring(0, 25) + '...' : d)}</span>`).join('')}
                    ${remaining > 0 ? `<span class="raci-doc-chip raci-doc-more">+${remaining} more</span>` : ''}
                </div>
            </div>`;
        }

        // ── Responsibility Statements (async, loaded after modal opens) ──
        const statementsId = `raci-stmts-${Date.now()}`;
        const statementsHtml = `<div class="raci-detail-section">
            <div class="raci-stmt-toggle" onclick="this.parentElement.classList.toggle('expanded')">
                <span class="raci-detail-section-title">Responsibility Statements</span>
                <span class="raci-stmt-badge" id="${statementsId}-count">loading...</span>
                <span class="raci-stmt-chevron">▸</span>
            </div>
            <div class="raci-stmt-list" id="${statementsId}">
                <div class="raci-stmt-loading">Loading statements...</div>
            </div>
        </div>`;

        // ── Reclassify Actions ──
        const escName = escapeHtml(roleName);
        const reclassifyHtml = `<div class="raci-detail-section raci-detail-actions">
            <div class="raci-detail-section-title">Reclassify</div>
            <div class="raci-edit-buttons raci-edit-buttons-modal">
                ${['R', 'A', 'C', 'I'].map(t => {
                    const isCurrent = t === raciType;
                    const targetArg = t === raciType ? '' : `, '${t}'`;
                    return `<button class="raci-edit-btn raci-btn-${t.toLowerCase()} ${isCurrent ? 'current disabled' : ''}"
                        onclick="TWR.Roles.setRaciValue('${escName}', '${raciType}', 1${targetArg}); TWR.Modal && TWR.Modal.close();"
                        ${isCurrent ? 'disabled' : ''} title="${isCurrent ? 'Current type' : `Reclassify as ${raciNames[t]}`}">
                        ${t} — ${raciNames[t]}
                    </button>`;
                }).join('')}
                <button class="raci-edit-btn raci-btn-clear"
                    onclick="TWR.Roles.setRaciValue('${escName}', '${raciType}', 0); TWR.Modal && TWR.Modal.close();"
                    title="Clear this classification">× Clear</button>
            </div>
            <div class="raci-revert-actions">
                <button class="raci-revert-btn"
                    onclick="TWR.Roles.revertRaciRole('${escName}'); TWR.Modal && TWR.Modal.close();"
                    title="Revert all changes for this role">↩ Revert "${escName}"</button>
            </div>
        </div>`;

        // ── Assemble Modal ──
        const modalContent = `
            <div class="raci-detail-panel raci-detail-${typeLower}">
                <div class="raci-detail-header" style="border-left: 4px solid ${colors.border}; background: ${colors.bg};">
                    <div class="raci-detail-header-top">
                        <span class="raci-detail-badge" style="background:${colors.gradient};">${raciType}</span>
                        <div class="raci-detail-header-text">
                            <h3 class="raci-detail-role">${escapeHtml(roleName)}</h3>
                            <p class="raci-detail-type">${raciNames[raciType]} — ${raciDescriptions[raciType]}</p>
                        </div>
                        <span class="raci-detail-count">${count}</span>
                    </div>
                </div>
                ${verbChartHtml}
                ${docsHtml}
                ${statementsHtml}
                ${reclassifyHtml}
            </div>`;

        showContentModal(`${raciNames[raciType]} Details: ${roleName}`, modalContent);

        // Animate bars after modal is visible
        requestAnimationFrame(() => {
            setTimeout(() => {
                document.querySelectorAll('.raci-verb-bar[data-width]').forEach(bar => {
                    bar.style.width = bar.dataset.width;
                });
            }, 50);
        });

        // Load responsibility statements async — filter to match the clicked RACI type
        const raciTypePatterns = {
            'R': /\b(shall|must|will|should|may)\s+(perform|execute|implement|develop|define|lead|ensure|maintain|conduct|create|prepare|manage|oversee|verif|valid)/i,
            'A': /\b(shall|must|will|should|may)\s+(approv|authoriz|sign|certif|accept)/i,
            'C': /\b(shall|must|will|should|may)\s+(review|coordinat|support|consult|advis|assist|collaborat)/i,
            'I': /\b(shall|must|will|should|may)\s+(receiv|report|monitor|inform|notif|communicat|track|provid)/i
        };
        try {
            const response = await fetch(`/api/roles/context?role=${encodeURIComponent(roleName)}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();

            // Find container — wait a tick if needed (modal might still be rendering)
            let stmtContainer = document.getElementById(statementsId);
            let stmtCount = document.getElementById(`${statementsId}-count`);
            if (!stmtContainer) {
                await new Promise(r => setTimeout(r, 100));
                stmtContainer = document.getElementById(statementsId);
                stmtCount = document.getElementById(`${statementsId}-count`);
            }
            if (!stmtContainer) { console.warn('[RACI Detail] Statement container lost'); return; }

            // Extract occurrences from whichever response shape we get
            const allResps = result.occurrences || result.data?.occurrences || result.data?.responsibilities || [];

            // Filter to only statements matching THIS RACI type's verb pattern
            const typePattern = raciTypePatterns[raciType];
            const filtered = allResps.filter(resp => {
                const text = typeof resp === 'string' ? resp : (resp.text || resp.responsibility || '');
                if (!text) return false;
                // Check if the text matches this RACI type's verb pattern
                if (typePattern && typePattern.test(text)) return true;
                // For R type, also include statements that don't match any other type (default bucket)
                if (raciType === 'R') {
                    const matchesOther = ['A', 'C', 'I'].some(t => raciTypePatterns[t]?.test(text));
                    return !matchesOther;
                }
                return false;
            });

            if (filtered.length > 0) {
                if (stmtCount) stmtCount.textContent = filtered.length;
                stmtContainer.innerHTML = filtered.map((resp, idx) => {
                    const text = typeof resp === 'string' ? resp : (resp.text || resp.responsibility || JSON.stringify(resp));
                    const doc = typeof resp === 'object' ? resp.document : '';
                    const truncated = text.length > 180 ? text.substring(0, 180) + '...' : text;
                    return `<div class="raci-stmt-item">
                        <span class="raci-stmt-num">${idx + 1}</span>
                        <span class="raci-stmt-text" title="${escapeHtml(text)}">${escapeHtml(truncated)}</span>
                        ${doc ? `<span class="raci-stmt-doc">${escapeHtml(doc)}</span>` : ''}
                    </div>`;
                }).join('');
            } else if (allResps.length > 0) {
                // Had statements but none matched this RACI type filter
                if (stmtCount) stmtCount.textContent = allResps.length;
                stmtContainer.innerHTML = `<div class="raci-stmt-empty">${allResps.length} total statements found. Showing unfiltered:</div>` +
                    allResps.slice(0, 20).map((resp, idx) => {
                        const text = typeof resp === 'string' ? resp : (resp.text || resp.responsibility || JSON.stringify(resp));
                        const truncated = text.length > 180 ? text.substring(0, 180) + '...' : text;
                        return `<div class="raci-stmt-item">
                            <span class="raci-stmt-num">${idx + 1}</span>
                            <span class="raci-stmt-text" title="${escapeHtml(text)}">${escapeHtml(truncated)}</span>
                        </div>`;
                    }).join('');
            } else {
                if (stmtCount) stmtCount.textContent = '0';
                stmtContainer.innerHTML = `<div class="raci-stmt-empty">No responsibility statements found in database. Count based on action verb frequency analysis.</div>`;
            }
        } catch (e) {
            console.warn('[RACI Detail] Statements fetch error:', e);
            const sc = document.getElementById(statementsId);
            if (sc) sc.innerHTML = `<div class="raci-stmt-empty">Could not load statements: ${escapeHtml(e.message)}</div>`;
            const scCount = document.getElementById(`${statementsId}-count`);
            if (scCount) scCount.textContent = '!';
        }
    }

    function closeRaciDropdown() {
        if (activeRaciDropdown) {
            activeRaciDropdown.element.remove();
            activeRaciDropdown.cell.classList.remove('editing');
            activeRaciDropdown = null;
            document.removeEventListener('click', closeRaciDropdownOnClickOutside);
        }
    }

    function closeRaciDropdownOnClickOutside(e) {
        if (activeRaciDropdown && !activeRaciDropdown.element.contains(e.target)) closeRaciDropdown();
    }

    function setRaciValue(roleName, originalType, value, newType) {
        const State = getState();
        const toast = getToast();

        if (!State.raciEdits) State.raciEdits = {};
        if (!State.raciEdits[roleName]) State.raciEdits[roleName] = {};

        const targetType = newType || originalType;

        // v3.4.0: Build user-friendly message about the change
        const raciNames = { R: 'Responsible', A: 'Accountable', C: 'Consulted', I: 'Informed' };
        let message = '';

        if (value === 0) {
            message = `Cleared ${raciNames[originalType]} classification for "${roleName}"`;
            State.raciEdits[roleName][originalType] = 0;
        } else if (newType && newType !== originalType) {
            message = `Reclassified "${roleName}" from ${raciNames[originalType]} to ${raciNames[newType]}`;
            State.raciEdits[roleName][originalType] = 0;
            State.raciEdits[roleName][targetType] = value;
        } else {
            message = `Set "${roleName}" as ${raciNames[targetType]}`;
            State.raciEdits[roleName][targetType] = value;
        }

        closeRaciDropdown();
        renderRolesMatrix();

        // Show feedback to user
        toast('info', message);
    }

    /**
     * v3.4.0: Revert RACI edits for a specific role
     */
    function revertRaciRole(roleName) {
        const State = getState();
        const toast = getToast();

        if (State.raciEdits && State.raciEdits[roleName]) {
            delete State.raciEdits[roleName];
            renderRolesMatrix();
            toast('success', `Reverted all changes for "${roleName}"`);
        } else {
            toast('info', `No changes to revert for "${roleName}"`);
        }
    }

    /**
     * v3.4.0: Revert all RACI edits back to original values
     */
    function revertAllRaciEdits() {
        const State = getState();
        const toast = getToast();

        const editCount = State.raciEdits ? Object.keys(State.raciEdits).length : 0;

        if (editCount > 0) {
            State.raciEdits = {};
            renderRolesMatrix();
            toast('success', `Reverted all RACI changes (${editCount} roles reset)`);
        } else {
            toast('info', 'No changes to revert');
        }
    }

    /**
     * v3.4.0: Get count of edited roles
     */
    function getRaciEditCount() {
        const State = getState();
        return State.raciEdits ? Object.keys(State.raciEdits).length : 0;
    }

    function toggleMatrixCriticalFilter() {
        const State = getState();
        State.matrixFilterCritical = document.getElementById('matrix-filter-critical')?.checked || false;
        renderRolesMatrix();
    }

    function changeMatrixSort(value) {
        const State = getState();
        State.matrixSort = value;
        renderRolesMatrix();
    }

    /**
     * v5.1.0: Toggle the export dropdown menu with function category filters
     */
    async function toggleExportMenu(e) {
        e.stopPropagation();
        const menu = document.getElementById('raci-export-menu');
        if (!menu) return;

        // If already open, close it
        if (menu.classList.contains('open')) {
            menu.classList.remove('open');
            return;
        }

        const escapeHtml = getEscapeHtml();

        // Load function categories if available
        let categories = [];
        let roleTags = [];
        try {
            if (window.TWR?.FunctionTags) {
                const ftState = TWR.FunctionTags.getState();
                categories = ftState.categories || [];
                roleTags = ftState.roleTags || [];

                // If categories not loaded yet, try loading them
                if (categories.length === 0 && TWR.FunctionTags.loadFunctionCategories) {
                    categories = await TWR.FunctionTags.loadFunctionCategories() || [];
                }
                if (roleTags.length === 0 && TWR.FunctionTags.loadRoleFunctionTags) {
                    await TWR.FunctionTags.loadRoleFunctionTags();
                    roleTags = TWR.FunctionTags.getState().roleTags || [];
                }
            }
        } catch (err) {
            console.warn('[RACI Export] Could not load function categories:', err);
        }

        // Count roles per category for the badges
        const State = getState();
        const roleNames = State.matrixRoleNames || [];
        const roleNamesLower = new Set(roleNames.map(n => n.toLowerCase().trim()));

        const catCounts = {};
        if (roleTags.length > 0) {
            roleTags.forEach(tag => {
                const rn = (tag.role_name || '').toLowerCase().trim();
                if (roleNamesLower.has(rn)) {
                    catCounts[tag.function_code] = (catCounts[tag.function_code] || 0) + 1;
                }
            });
        }

        // Build menu HTML
        let html = `<div class="raci-export-item" data-filter="" title="Export all ${roleNames.length} roles">
            <span class="raci-export-icon" style="background:var(--accent);">✱</span>
            <span class="raci-export-label">All Roles</span>
            <span class="raci-export-count">${roleNames.length}</span>
        </div>`;

        if (categories.length > 0) {
            html += '<div class="raci-export-divider"></div>';
            // Sort by sort_order then name
            const sorted = [...categories].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0) || (a.name || '').localeCompare(b.name || ''));
            sorted.forEach(cat => {
                const count = catCounts[cat.code] || 0;
                if (count === 0) return; // Skip categories with no matching roles
                const color = cat.color || 'var(--text-muted)';
                html += `<div class="raci-export-item" data-filter="${escapeHtml(cat.code)}" title="${escapeHtml(cat.name)} — ${count} roles">
                    <span class="raci-export-icon" style="background:${color};"></span>
                    <span class="raci-export-label">${escapeHtml(cat.code)} — ${escapeHtml(cat.name)}</span>
                    <span class="raci-export-count">${count}</span>
                </div>`;
            });
        }

        menu.innerHTML = html;

        // Wire click handlers
        menu.querySelectorAll('.raci-export-item').forEach(item => {
            item.addEventListener('click', (ev) => {
                ev.stopPropagation();
                const filterCode = item.dataset.filter || '';
                const filterName = item.querySelector('.raci-export-label')?.textContent || 'All Roles';
                menu.classList.remove('open');
                exportRaciMatrix(filterCode, filterName);
            });
        });

        menu.classList.add('open');
    }

    async function exportRaciMatrix(filterCode, filterLabel) {
        const State = getState();
        const toast = getToast();

        if (!State.raciMatrix || !State.matrixRoleNames) {
            toast('warning', 'No matrix data to export');
            return;
        }

        // Determine which roles to export
        let roleNames = [...State.matrixRoleNames];
        if (filterCode) {
            // Get role tags and filter
            const roleTags = window.TWR?.FunctionTags?.getState()?.roleTags || [];
            const taggedRoles = new Set(
                roleTags
                    .filter(t => t.function_code === filterCode)
                    .map(t => (t.role_name || '').toLowerCase().trim())
            );
            roleNames = roleNames.filter(rn => taggedRoles.has(rn.toLowerCase().trim()));
        }

        if (roleNames.length === 0) {
            toast('warning', `No roles found for filter: ${filterLabel || filterCode}`);
            return;
        }

        const rolesData = State.roles?.roles || State.roles || {};

        // v3.1.10: Human-readable date format for export
        const now = new Date();
        const dateStr = now.toLocaleDateString('en-US', {
            year: 'numeric', month: 'long', day: 'numeric'
        });
        const timeStr = now.toLocaleTimeString('en-US', {
            hour: '2-digit', minute: '2-digit'
        });

        // Build CSV with header info
        let csv = `RACI Matrix Export\n`;
        csv += `Generated: ${dateStr} at ${timeStr}\n`;
        csv += `Filter: ${filterCode ? (filterLabel || filterCode) : 'All Roles'}\n`;
        csv += `Total Roles: ${roleNames.length}\n\n`;

        // Column headers matching the view
        csv += 'Role Name,Category,Responsible (R),Accountable (A),Consulted (C),Informed (I),Total,Primary Type,Documents\n';

        roleNames.forEach(roleName => {
            const raci = State.raciMatrix[roleName];
            if (!raci) return;
            const roleData = rolesData[roleName] || {};
            const displayName = raci.normalized_name || (typeof roleData === 'object' ? (roleData.canonical_name || roleName) : roleName);
            const category = raci.category || roleData.category || 'Unknown';
            const documents = (raci.documents || roleData.documents || []).join('; ');
            const total = raci.R + raci.A + raci.C + raci.I;

            let primaryType = '-';
            const max = Math.max(raci.R, raci.A, raci.C, raci.I);
            if (max > 0) {
                if (raci.R === max) primaryType = 'Responsible';
                else if (raci.A === max) primaryType = 'Accountable';
                else if (raci.C === max) primaryType = 'Consulted';
                else if (raci.I === max) primaryType = 'Informed';
            }

            // Escape quotes in fields
            const escapeCsv = (str) => `"${(str || '').replace(/"/g, '""')}"`;

            csv += `${escapeCsv(displayName)},${escapeCsv(category)},${raci.R},${raci.A},${raci.C},${raci.I},${total},${primaryType},${escapeCsv(documents)}\n`;
        });

        csv += '\n';
        csv += 'Legend:\n';
        csv += 'R (Responsible): Performs the work - shall, must, perform, execute, implement\n';
        csv += 'A (Accountable): Approves/authorizes - approve, authorize, sign, certify\n';
        csv += 'C (Consulted): Provides input - review, coordinate, support, consult, advise\n';
        csv += 'I (Informed): Kept in loop - receive, report, monitor, inform, notify\n';

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        // Use readable date in filename too
        const fileDate = now.toISOString().slice(0, 10); // YYYY-MM-DD
        const filterSuffix = filterCode ? `_${filterCode}` : '';
        a.download = `RACI_Matrix_${State.filename || 'All_Roles'}${filterSuffix}_${fileDate}.csv`;
        a.click();
        URL.revokeObjectURL(url);

        toast('success', `Exported ${roleNames.length} roles${filterCode ? ` (${filterLabel || filterCode})` : ''} to CSV`);
    }

    async function renderDocumentLog() {
        const escapeHtml = getEscapeHtml();
        const State = getState();
        const api = getApi();
        const tbody = document.getElementById('document-log-body');
        const emptyMsg = document.getElementById('document-log-empty');
        
        if (!State.roleDocuments || State.roleDocuments.length === 0) {
            try {
                const response = await api('/scan-history?limit=20', 'GET');
                if (response && response.success && response.data && response.data.length > 0) {
                    State.roleDocuments = response.data.map(scan => ({
                        filename: scan.filename,
                        analyzed: scan.scanned_at || scan.timestamp,
                        roles: scan.role_count || 0,
                        responsibilities: scan.responsibility_count || scan.issue_count || 0,
                        score: scan.score,
                        grade: scan.grade
                    }));
                    const countEl = document.getElementById('total-documents-count');
                    if (countEl) countEl.textContent = State.roleDocuments.length;
                }
            } catch (e) {
                console.warn('[TWR Roles] Could not load scan history:', e);
            }
        }
        
        const documents = State.roleDocuments || [{
            filename: State.filename || 'Current Document',
            analyzed: new Date().toISOString(),
            roles: Object.keys(State.roles.roles || State.roles).length,
            responsibilities: Object.values(State.roles.roles || State.roles).reduce((sum, r) => sum + (r.responsibilities?.length || r.count || 1), 0)
        }];
        
        if (documents.length === 0) {
            if (emptyMsg) emptyMsg.style.display = 'block';
            if (tbody) tbody.innerHTML = '';
            return;
        }
        
        if (emptyMsg) emptyMsg.style.display = 'none';
        
        if (tbody) {
            tbody.innerHTML = documents.map(doc => {
                const date = new Date(doc.analyzed);
                const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                return `<tr>
                    <td><strong>${escapeHtml(doc.filename)}</strong></td>
                    <td>${dateStr}</td>
                    <td>${doc.roles}</td>
                    <td>${doc.responsibilities}</td>
                    <td><button class="btn btn-xs btn-ghost" onclick="TWR.Roles.viewDocumentRoles('${escapeHtml(doc.filename)}')" title="View roles"><i data-lucide="eye"></i></button></td>
                </tr>`;
            }).join('');
        }
    }

    function viewDocumentRoles(filename) {
        const toast = getToast();
        toast('info', `Viewing roles from: ${filename}`);
        document.querySelector('.roles-tab[data-tab="details"]')?.click();
    }

    // ============================================================
    // ROLE-DOCUMENT MATRIX (v3.0.97)
    // ============================================================
    
    let roleDocMatrixData = null;
    
    async function renderRoleDocMatrix() {
        const escapeHtml = getEscapeHtml();
        const api = getApi();
        const toast = getToast();
        const State = getState();
        const container = document.getElementById('roledoc-matrix-container');
        const emptyMsg = document.getElementById('roledoc-empty');

        if (!container) return;

        // v4.0.3: Load adjudication data
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();
        
        container.innerHTML = '<p class="text-muted"><i data-lucide="loader" class="spin"></i> Loading matrix data...</p>';
        if (typeof lucide !== 'undefined') lucide.createIcons();
        
        try {
            const response = await api('/roles/matrix', 'GET');
            
            console.log('[TWR Roles] Matrix API response:', response);
            
            // v3.0.109: Improved response validation - check for actual data content
            if (!response.success) {
                container.innerHTML = `<div class="text-muted" style="padding:20px;text-align:center;">
                    <p><i data-lucide="database" style="width:32px;height:32px;opacity:0.5;"></i></p>
                    <p><strong>Role-Document Matrix Not Available</strong></p>
                    <p style="font-size:13px;">${escapeHtml(response.error || 'Unable to load matrix data')}</p>
                </div>`;
                if (typeof lucide !== 'undefined') lucide.createIcons();
                return;
            }
            
            // v3.0.109: Handle case where response.data might be null/undefined
            const data = response.data || {};
            roleDocMatrixData = data;
            
            const documents = data.documents || {};
            const roles = data.roles || {};
            const connections = data.connections || {};
            
            const docIds = Object.keys(documents);
            const roleIds = Object.keys(roles);
            
            console.log('[TWR Roles] Matrix data:', { 
                docCount: docIds.length, 
                roleCount: roleIds.length,
                connectionCount: Object.keys(connections).length 
            });
            
            if (roleIds.length === 0 || docIds.length < 1) {
                // v3.0.106: Show current session roles if matrix is empty but we have session data
                const sessionRoles = State.roles?.roles || State.roles || {};
                const sessionRoleCount = Object.keys(sessionRoles).length;
                
                if (sessionRoleCount > 0) {
                    container.innerHTML = `<div class="text-muted" style="padding:20px;text-align:center;">
                        <p><i data-lucide="file-search" style="width:32px;height:32px;opacity:0.5;"></i></p>
                        <p><strong>No Cross-Document Data Yet</strong></p>
                        <p style="font-size:13px;">Found <strong>${sessionRoleCount} roles</strong> in current document.</p>
                        <p style="font-size:12px;margin-top:8px;">Review more documents to build the cross-document matrix.<br>
                        Use the <strong>Details</strong> tab to see roles from the current document.</p>
                    </div>`;
                } else {
                    container.innerHTML = `<div class="text-muted" style="padding:20px;text-align:center;">
                        <p><i data-lucide="database" style="width:32px;height:32px;opacity:0.5;"></i></p>
                        <p><strong>Role-Document Matrix Not Available</strong></p>
                        <p style="font-size:13px;">The matrix requires scan history data from multiple document reviews.</p>
                        <p style="font-size:12px;margin-top:12px;">To populate this matrix:<br>
                        1. Review documents using the main review feature<br>
                        2. Scan history will automatically record roles found<br>
                        3. Return here to see cross-document role analysis</p>
                    </div>`;
                    if (emptyMsg) emptyMsg.style.display = 'block';
                }
                if (typeof lucide !== 'undefined') lucide.createIcons();
                return;
            }
            
            if (emptyMsg) emptyMsg.style.display = 'none';
            
            const showCounts = document.getElementById('roledoc-show-counts')?.checked || false;
            
            // Build header row
            let html = '<div class="roledoc-table-wrapper"><table class="roledoc-matrix-table"><thead><tr>';
            html += '<th class="roledoc-role-header">Role</th>';
            
            docIds.forEach(docId => {
                const docName = documents[docId] || 'Unknown';
                const shortName = docName.length > 20 ? docName.substring(0, 17) + '...' : docName;
                html += `<th class="roledoc-doc-header" title="${escapeHtml(docName)}">${escapeHtml(shortName)}</th>`;
            });
            
            html += '<th class="roledoc-total-header">Total</th></tr></thead><tbody>';
            
            // Sort roles alphabetically
            const sortedRoleIds = roleIds.sort((a, b) => {
                return (roles[a] || '').localeCompare(roles[b] || '');
            });
            
            // Build data rows
            sortedRoleIds.forEach(roleId => {
                const roleName = roles[roleId] || 'Unknown';
                const roleConnections = connections[roleId] || {};
                let totalDocs = 0;
                
                html += `<tr data-role-id="${escapeHtml(roleId)}">`;
                html += `<td class="roledoc-role-name" title="${escapeHtml(roleName)}">${escapeHtml(roleName)}${adjLookup ? adjLookup.getBadge(roleName, { compact: true, size: 'sm' }) : ''}</td>`;
                
                docIds.forEach(docId => {
                    const count = roleConnections[docId] || 0;
                    if (count > 0) {
                        totalDocs++;
                        if (showCounts) {
                            html += `<td class="roledoc-cell roledoc-present" title="${count} mentions">${count}</td>`;
                        } else {
                            html += `<td class="roledoc-cell roledoc-present" title="${count} mentions">✓</td>`;
                        }
                    } else {
                        html += `<td class="roledoc-cell roledoc-absent">-</td>`;
                    }
                });
                
                html += `<td class="roledoc-total">${totalDocs}</td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table></div>';
            
            // Summary stats
            const matrixAdjCount = adjLookup ? adjLookup.countAdjudicated(sortedRoleIds.map(id => roles[id] || '')) : { adjudicated: 0 };
            html += `<div class="roledoc-summary">
                <span><strong>${roleIds.length}</strong> roles</span>
                <span><strong>${docIds.length}</strong> documents</span>
                ${matrixAdjCount.adjudicated > 0 ? `<span><strong style="color:#22c55e;">${matrixAdjCount.confirmed}</strong> adjudicated${matrixAdjCount.rejected > 0 ? `, <strong style="color:#ef4444;">${matrixAdjCount.rejected}</strong> rejected` : ''}</span>` : ''}
            </div>`;
            
            container.innerHTML = html;
            
            // Initialize controls
            initRoleDocMatrixControls();
            
        } catch (e) {
            console.error('[TWR Roles] Failed to load role-document matrix:', e);
            // v3.0.109: Better error display with retry button
            container.innerHTML = `<div class="text-muted" style="padding:20px;text-align:center;">
                <p><i data-lucide="alert-circle" style="width:32px;height:32px;opacity:0.5;color:var(--danger);"></i></p>
                <p class="text-error"><strong>Error Loading Matrix</strong></p>
                <p style="font-size:13px;">${getEscapeHtml()(e.message || 'Unknown error')}</p>
                <p style="margin-top:12px;">
                    <button class="btn btn-sm btn-secondary" onclick="TWR.Roles.renderRoleDocMatrix()">
                        <i data-lucide="refresh-cw"></i> Retry
                    </button>
                </p>
            </div>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }
    
    function initRoleDocMatrixControls() {
        const showCountsCheckbox = document.getElementById('roledoc-show-counts');
        const refreshBtn = document.getElementById('btn-roledoc-refresh');
        const exportCsvBtn = document.getElementById('btn-roledoc-export-csv');
        const exportExcelBtn = document.getElementById('btn-roledoc-export-excel');
        
        if (showCountsCheckbox && !showCountsCheckbox._initialized) {
            showCountsCheckbox._initialized = true;
            showCountsCheckbox.addEventListener('change', () => {
                renderRoleDocMatrix();
            });
        }
        
        if (refreshBtn && !refreshBtn._initialized) {
            refreshBtn._initialized = true;
            refreshBtn.addEventListener('click', () => {
                roleDocMatrixData = null;
                renderRoleDocMatrix();
            });
        }
        
        if (exportCsvBtn && !exportCsvBtn._initialized) {
            exportCsvBtn._initialized = true;
            exportCsvBtn.addEventListener('click', exportRoleDocMatrixCSV);
        }
        
        if (exportExcelBtn && !exportExcelBtn._initialized) {
            exportExcelBtn._initialized = true;
            exportExcelBtn.addEventListener('click', exportRoleDocMatrixExcel);
        }
    }
    
    function exportRoleDocMatrixCSV() {
        const toast = getToast();
        
        if (!roleDocMatrixData) {
            toast('warning', 'No matrix data to export. Refresh the matrix first.');
            return;
        }
        
        const { documents, roles, connections } = roleDocMatrixData;
        const docIds = Object.keys(documents);
        const roleIds = Object.keys(roles);
        
        if (roleIds.length === 0) {
            toast('warning', 'No roles to export');
            return;
        }
        
        // Build CSV
        let csv = 'Role';
        docIds.forEach(docId => {
            const docName = (documents[docId] || 'Unknown').replace(/"/g, '""');
            csv += `,"${docName}"`;
        });
        csv += ',Total Documents\n';
        
        roleIds.sort((a, b) => (roles[a] || '').localeCompare(roles[b] || '')).forEach(roleId => {
            const roleName = (roles[roleId] || 'Unknown').replace(/"/g, '""');
            csv += `"${roleName}"`;
            
            let totalDocs = 0;
            const roleConnections = connections[roleId] || {};
            
            docIds.forEach(docId => {
                const count = roleConnections[docId] || 0;
                csv += `,${count > 0 ? count : ''}`;
                if (count > 0) totalDocs++;
            });
            
            csv += `,${totalDocs}\n`;
        });
        
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        downloadBlob(blob, `Role_Document_Matrix_${getTimestamp()}.csv`);
        
        toast('success', 'Role-Document Matrix exported to CSV');
    }
    
    async function exportRoleDocMatrixExcel() {
        const toast = getToast();
        const api = getApi();
        const setLoading = getSetLoading();
        
        if (!roleDocMatrixData) {
            toast('warning', 'No matrix data to export. Refresh the matrix first.');
            return;
        }
        
        const State = getState();
        if (!State.capabilities?.excel_export) {
            // Fallback to CSV if Excel not available
            toast('info', 'Excel export not available, exporting as CSV instead');
            exportRoleDocMatrixCSV();
            return;
        }
        
        setLoading(true, 'Generating Excel file...');
        
        try {
            const response = await fetch('/api/roles/matrix/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': State.csrfToken || document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify({ format: 'xlsx' })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                downloadBlob(blob, `Role_Document_Matrix_${getTimestamp()}.xlsx`);
                toast('success', 'Role-Document Matrix exported to Excel');
            } else {
                // Fallback to CSV
                toast('info', 'Excel export failed, exporting as CSV instead');
                exportRoleDocMatrixCSV();
            }
        } catch (e) {
            console.error('[TWR Roles] Excel export failed:', e);
            toast('info', 'Excel export not available, exporting as CSV instead');
            exportRoleDocMatrixCSV();
        }
        
        setLoading(false);
    }

    // ============================================================
    // ADJUDICATION
    // ============================================================
    
    function initAdjudication() {
        const State = getState();
        const debounce = getDebounce();
        const rolesData = State.roles?.roles || State.roles || {};
        
        Object.keys(rolesData).forEach(roleName => {
            if (!AdjudicationState.decisions.has(roleName)) {
                const data = rolesData[roleName];
                const confidence = typeof data === 'object' ? (data.avg_confidence || data.confidence || 0.8) : 0.8;
                
                AdjudicationState.decisions.set(roleName, {
                    status: 'pending',
                    confidence: confidence,
                    notes: '',
                    isDeliverable: detectDeliverable(roleName, data),
                    suggestedType: suggestRoleType(roleName, data)
                });
            }
        });
        
        document.getElementById('adj-filter')?.addEventListener('change', renderAdjudicationList);
        document.getElementById('adj-search')?.addEventListener('input', debounce(renderAdjudicationList, 300));
        
        renderAdjudicationList();
        updateAdjudicationStats();
    }

    function detectDeliverable(roleName, data) {
        const deliverablePatterns = [
            /\b(document|report|plan|specification|analysis|review|audit|assessment)\b/i,
            /\b(drawing|schematic|diagram|model|prototype)\b/i,
            /\b(database|repository|archive|library)\b/i,
            /\b(schedule|timeline|roadmap|milestone)\b/i,
            /\b(budget|estimate|proposal|contract)\b/i,
            /\b(test|verification|validation)\s+(report|results|data)\b/i,
            /\b(requirements|interface|design)\s+(document|spec)/i,
            /\bICD\b|\bSRS\b|\bSDD\b|\bCDRL\b|\bDID\b/i
        ];
        const name = roleName.toLowerCase();
        return deliverablePatterns.some(p => p.test(name));
    }

    function suggestRoleType(roleName, data) {
        const name = roleName.toLowerCase();
        const rolePatterns = [
            /\b(engineer|manager|lead|director|officer|specialist|analyst)\b/i,
            /\b(coordinator|administrator|supervisor|inspector|reviewer)\b/i,
            /\b(team|group|committee|board|panel|council)\b/i
        ];
        
        if (rolePatterns.some(p => p.test(name))) return 'role';
        if (detectDeliverable(roleName, data)) return 'deliverable';
        
        const actionTypes = typeof data === 'object' ? (data.action_types || {}) : {};
        const hasActions = Object.values(actionTypes).some(v => v > 0);
        return hasActions ? 'role' : 'unknown';
    }

    function renderAdjudicationList() {
        const escapeHtml = getEscapeHtml();
        const State = getState();
        const container = document.getElementById('adjudication-list');
        if (!container) return;
        
        const rolesData = State.roles?.roles || State.roles || {};
        const filter = document.getElementById('adj-filter')?.value || 'pending';
        const search = (document.getElementById('adj-search')?.value || '').toLowerCase();
        
        AdjudicationState.filter = filter;
        AdjudicationState.search = search;
        
        let roleEntries = Object.entries(rolesData).filter(([name, data]) => {
            const decision = AdjudicationState.decisions.get(name) || { status: 'pending', confidence: 0.8 };
            if (filter === 'pending' && decision.status !== 'pending') return false;
            if (filter === 'confirmed' && decision.status !== 'confirmed') return false;
            if (filter === 'deliverable' && decision.status !== 'deliverable') return false;
            if (filter === 'rejected' && decision.status !== 'rejected') return false;
            if (filter === 'low-confidence' && decision.confidence >= 0.7) return false;
            if (search && !name.toLowerCase().includes(search)) return false;
            return true;
        });
        
        roleEntries.sort((a, b) => {
            const confA = AdjudicationState.decisions.get(a[0])?.confidence || 0.8;
            const confB = AdjudicationState.decisions.get(b[0])?.confidence || 0.8;
            return confA - confB;
        });
        
        if (roleEntries.length === 0) {
            container.innerHTML = `<div class="empty-state" style="padding:40px;text-align:center;">
                <i data-lucide="check-circle" style="width:48px;height:48px;color:var(--success);margin-bottom:16px;"></i>
                <p>No items match the current filter.</p>
            </div>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }
        
        container.innerHTML = roleEntries.map(([name, data]) => {
            const decision = AdjudicationState.decisions.get(name) || { status: 'pending', confidence: 0.8 };
            const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
            const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
            const confidence = (decision.confidence * 100).toFixed(0);
            const suggestedType = decision.suggestedType || 'unknown';
            
            const statusClass = { 'pending': 'status-pending', 'confirmed': 'status-confirmed', 'deliverable': 'status-deliverable', 'rejected': 'status-rejected' }[decision.status] || 'status-pending';
            const statusIcon = { 'pending': 'clock', 'confirmed': 'check-circle', 'deliverable': 'file-text', 'rejected': 'x-circle' }[decision.status] || 'clock';
            
            return `<div class="adjudication-item selectable ${statusClass}" data-role="${escapeHtml(name)}">
                <input type="checkbox" class="adj-item-checkbox" onchange="TWR.Roles.toggleAdjItemSelection(this)">
                <div class="adj-item-main">
                    <div class="adj-item-header">
                        <span class="adj-item-name" title="${escapeHtml(name)}" data-original="${escapeHtml(name)}">${escapeHtml(displayName)}</span>
                        <button class="btn btn-xs btn-ghost adj-edit-btn" onclick="TWR.Roles.editRoleName('${escapeHtml(name)}')" title="Edit role name"><i data-lucide="edit-2"></i></button>
                    </div>
                    <div class="adj-item-meta">
                        <span class="confidence-badge ${confidence < 70 ? 'low' : ''}">${confidence}%</span>
                        <span class="count-badge">${count} occurrences</span>
                        ${suggestedType === 'deliverable' ? '<span class="suggested-badge deliverable">Likely Deliverable</span>' : ''}
                    </div>
                    <div class="adj-item-status"><i data-lucide="${statusIcon}"></i><span>${decision.status.charAt(0).toUpperCase() + decision.status.slice(1)}</span></div>
                </div>
                <div class="adj-item-actions">
                    <button class="btn btn-xs ${decision.status === 'confirmed' ? 'btn-success' : 'btn-ghost'}" onclick="TWR.Roles.setAdjudicationStatus('${escapeHtml(name)}', 'confirmed')" title="Confirm as Role"><i data-lucide="user-check"></i><span class="btn-label">Role</span></button>
                    <button class="btn btn-xs ${decision.status === 'deliverable' ? 'btn-info' : 'btn-ghost'}" onclick="TWR.Roles.setAdjudicationStatus('${escapeHtml(name)}', 'deliverable')" title="Mark as Deliverable"><i data-lucide="file-text"></i><span class="btn-label">Doc</span></button>
                    <button class="btn btn-xs ${decision.status === 'rejected' ? 'btn-error' : 'btn-ghost'}" onclick="TWR.Roles.setAdjudicationStatus('${escapeHtml(name)}', 'rejected')" title="Reject (False Positive)"><i data-lucide="x-circle"></i><span class="btn-label">Reject</span></button>
                </div>
                ${(typeof data === 'object' && data.sample_contexts && data.sample_contexts.length > 0) ? `
                <div class="adj-item-contexts">
                    <button class="btn btn-xs btn-ghost adj-context-toggle" onclick="TWR.Roles.toggleAdjContext(this)" title="Show context sentences"><i data-lucide="chevron-down"></i> Show context</button>
                    <div class="adj-context-list" style="display:none;">${data.sample_contexts.map(ctx => `<div class="adj-context-sentence">"${escapeHtml(ctx)}"</div>`).join('')}</div>
                </div>` : ''}
            </div>`;
        }).join('');
        
        if (typeof lucide !== 'undefined') lucide.createIcons();
        updateAdjudicationStats();
        
        const selectAll = document.getElementById('adj-select-all');
        if (selectAll) selectAll.checked = false;
        updateBulkActionVisibility();
    }

    function toggleAdjItemSelection(checkbox) {
        const item = checkbox.closest('.adjudication-item');
        if (item) item.classList.toggle('selected', checkbox.checked);
        updateBulkActionVisibility();
        
        const allCheckboxes = document.querySelectorAll('.adj-item-checkbox');
        const checkedCount = document.querySelectorAll('.adj-item-checkbox:checked').length;
        const selectAll = document.getElementById('adj-select-all');
        if (selectAll) {
            selectAll.checked = checkedCount === allCheckboxes.length && allCheckboxes.length > 0;
            selectAll.indeterminate = checkedCount > 0 && checkedCount < allCheckboxes.length;
        }
    }

    function toggleAdjContext(btn) {
        const contextList = btn.nextElementSibling;
        if (contextList) {
            const isHidden = contextList.style.display === 'none';
            contextList.style.display = isHidden ? 'block' : 'none';
            btn.innerHTML = isHidden ? '<i data-lucide="chevron-up"></i> Hide context' : '<i data-lucide="chevron-down"></i> Show context';
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }

    function editRoleName(originalName) {
        const toast = getToast();
        const item = document.querySelector(`.adjudication-item[data-role="${CSS.escape(originalName)}"]`);
        if (!item) return;
        
        const nameSpan = item.querySelector('.adj-item-name');
        if (!nameSpan) return;
        
        const currentName = nameSpan.textContent.trim();
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'adj-edit-input form-input';
        input.value = currentName;
        input.style.width = '200px';
        
        nameSpan.style.display = 'none';
        nameSpan.parentNode.insertBefore(input, nameSpan);
        input.focus();
        input.select();
        
        const saveEdit = () => {
            const newName = input.value.trim();
            if (newName && newName !== originalName) {
                const decision = AdjudicationState.decisions.get(originalName);
                if (decision) {
                    AdjudicationState.decisions.delete(originalName);
                    decision.editedName = newName;
                    decision.originalName = originalName;
                    AdjudicationState.decisions.set(newName, decision);
                    item.setAttribute('data-role', newName);
                    nameSpan.textContent = newName;
                    nameSpan.setAttribute('data-original', originalName);
                    nameSpan.title = `${newName} (originally: ${originalName})`;
                    toast('success', `Renamed "${originalName}" to "${newName}"`);
                }
            }
            input.remove();
            nameSpan.style.display = '';
        };
        
        const cancelEdit = () => { input.remove(); nameSpan.style.display = ''; };
        
        input.addEventListener('blur', saveEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); saveEdit(); }
            else if (e.key === 'Escape') { e.preventDefault(); cancelEdit(); }
        });
    }

    function setAdjudicationStatus(roleName, status) {
        const State = getState();
        const decision = AdjudicationState.decisions.get(roleName);
        if (decision) {
            decision.status = decision.status === status ? 'pending' : status;
            renderAdjudicationList();
            updateAdjudicationStats();
            
            if (GraphState.svg && GraphState.data) {
                const confirmed = [], deliverables = [], rejected = [];
                AdjudicationState.decisions.forEach((dec, name) => {
                    switch (dec.status) {
                        case 'confirmed': confirmed.push(name); break;
                        case 'deliverable': deliverables.push(name); break;
                        case 'rejected': rejected.push(name); break;
                    }
                });
                State.adjudicatedRoles = { confirmed, deliverables, rejected, timestamp: new Date().toISOString() };
                updateGraphWithAdjudication();
            }
            
            if (status === 'confirmed' || status === 'deliverable') {
                addAdjudicatedRoleToDictionary(roleName, status === 'deliverable');
            }
        }
    }

    async function addAdjudicatedRoleToDictionary(roleName, isDeliverable) {
        const State = getState();
        try {
            const response = await fetch('/api/roles/dictionary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': window.CSRF_TOKEN || State.csrfToken || '' },
                body: JSON.stringify({
                    role_name: roleName,
                    source: 'adjudication',
                    source_document: State.filename || '',
                    is_deliverable: isDeliverable,
                    category: isDeliverable ? 'Deliverable' : 'Custom',
                    notes: `Added via adjudication on ${new Date().toLocaleDateString()}`
                })
            });
            const result = await response.json();
            if (result.success) console.log(`[TWR Roles] Added "${roleName}" to dictionary`);
        } catch (e) {
            console.warn(`[TWR Roles] Could not add "${roleName}" to dictionary:`, e);
        }
    }

    function updateAdjudicationStats() {
        let pending = 0, confirmed = 0, deliverable = 0, rejected = 0;
        AdjudicationState.decisions.forEach(decision => {
            switch (decision.status) {
                case 'pending': pending++; break;
                case 'confirmed': confirmed++; break;
                case 'deliverable': deliverable++; break;
                case 'rejected': rejected++; break;
            }
        });
        const el = (id) => document.getElementById(id);
        if (el('adj-pending-count')) el('adj-pending-count').textContent = pending;
        if (el('adj-confirmed-count')) el('adj-confirmed-count').textContent = confirmed;
        if (el('adj-deliverable-count')) el('adj-deliverable-count').textContent = deliverable;
        if (el('adj-rejected-count')) el('adj-rejected-count').textContent = rejected;
    }

    function saveAdjudication() {
        const State = getState();
        const toast = getToast();
        const decisions = {};
        AdjudicationState.decisions.forEach((value, key) => { decisions[key] = value; });
        
        const saveData = { filename: State.filename, timestamp: new Date().toISOString(), decisions: decisions };
        
        try {
            const key = `twr_adjudication_${State.filename || 'default'}`;
            localStorage.setItem(key, JSON.stringify(saveData));
            const masterKey = 'twr_adjudication_master';
            const master = JSON.parse(localStorage.getItem(masterKey) || '{}');
            Object.assign(master, decisions);
            localStorage.setItem(masterKey, JSON.stringify(master));
            toast('success', 'Adjudication decisions saved');
        } catch (e) {
            console.error('[TWR Roles] Failed to save adjudication:', e);
            toast('error', 'Failed to save decisions');
        }
    }

    function loadAdjudication() {
        const State = getState();
        const toast = getToast();
        try {
            const key = `twr_adjudication_${State.filename || 'default'}`;
            const saved = localStorage.getItem(key);
            if (saved) {
                const data = JSON.parse(saved);
                Object.entries(data.decisions || {}).forEach(([name, decision]) => {
                    AdjudicationState.decisions.set(name, decision);
                });
                toast('info', 'Loaded previous adjudication decisions');
            }
        } catch (e) {
            console.warn('[TWR Roles] Could not load adjudication:', e);
        }
    }

    function resetAdjudication() {
        const toast = getToast();
        if (!confirm('Reset all adjudication decisions to pending?')) return;
        AdjudicationState.decisions.forEach((decision, key) => { decision.status = 'pending'; });
        renderAdjudicationList();
        toast('info', 'All decisions reset to pending');
    }

    function exportAdjudication() {
        const State = getState();
        const toast = getToast();
        const rolesData = State.roles?.roles || State.roles || {};
        
        let csv = 'Role Name,Status,Confidence,Occurrences,Suggested Type,Notes\n';
        AdjudicationState.decisions.forEach((decision, roleName) => {
            const data = rolesData[roleName] || {};
            const displayName = typeof data === 'object' ? (data.canonical_name || roleName) : roleName;
            const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
            csv += `"${displayName}",${decision.status},${(decision.confidence * 100).toFixed(0)}%,${count},${decision.suggestedType || 'unknown'},"${decision.notes || ''}"\n`;
        });
        
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `role_adjudication_${State.filename || 'roles'}_${getTimestamp()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
        toast('success', 'Adjudication exported to CSV');
    }

    function applyAdjudicationToDocument() {
        const State = getState();
        const toast = getToast();
        const confirmed = [], deliverables = [], rejected = [];
        
        AdjudicationState.decisions.forEach((decision, roleName) => {
            switch (decision.status) {
                case 'confirmed': confirmed.push(roleName); break;
                case 'deliverable': deliverables.push(roleName); break;
                case 'rejected': rejected.push(roleName); break;
            }
        });
        
        State.adjudicatedRoles = { confirmed, deliverables, rejected, timestamp: new Date().toISOString() };
        if (GraphState.data && GraphState.svg) updateGraphWithAdjudication();
        toast('success', `Applied: ${confirmed.length} roles, ${deliverables.length} deliverables, ${rejected.length} rejected`);
    }

    function updateGraphWithAdjudication() {
        const State = getState();
        if (!GraphState.svg) return;
        
        if (!State.adjudicatedRoles && AdjudicationState.decisions && AdjudicationState.decisions.size > 0) {
            const confirmed = [], deliverables = [], rejected = [];
            AdjudicationState.decisions.forEach((dec, name) => {
                switch (dec.status) {
                    case 'confirmed': confirmed.push(name); break;
                    case 'deliverable': deliverables.push(name); break;
                    case 'rejected': rejected.push(name); break;
                }
            });
            State.adjudicatedRoles = { confirmed, deliverables, rejected, timestamp: new Date().toISOString() };
        }
        
        if (!State.adjudicatedRoles) return;
        
        const { confirmed, deliverables, rejected } = State.adjudicatedRoles;
        const confirmedSet = new Set(confirmed.map(r => r.toLowerCase()));
        const deliverableSet = new Set(deliverables.map(r => r.toLowerCase()));
        const rejectedSet = new Set(rejected.map(r => r.toLowerCase()));
        
        const ADJUDICATION_COLORS = { confirmed: '#10B981', deliverable: '#F59E0B', rejected: '#95A5A6', role: '#4A90D9', document: '#27AE60' };
        
        GraphState.svg.selectAll('.graph-node')
            .classed('role-confirmed', d => d.type === 'role' && confirmedSet.has((d.label || '').toLowerCase()))
            .classed('role-deliverable', d => d.type === 'role' && deliverableSet.has((d.label || '').toLowerCase()))
            .classed('role-rejected', d => d.type === 'role' && rejectedSet.has((d.label || '').toLowerCase()));
        
        GraphState.svg.selectAll('.graph-node circle')
            .attr('fill', d => {
                if (d.type !== 'role') return ADJUDICATION_COLORS.document;
                const label = (d.label || '').toLowerCase();
                if (confirmedSet.has(label)) return ADJUDICATION_COLORS.confirmed;
                if (deliverableSet.has(label)) return ADJUDICATION_COLORS.deliverable;
                if (rejectedSet.has(label)) return ADJUDICATION_COLORS.rejected;
                return ADJUDICATION_COLORS.role;
            })
            .attr('stroke', d => d.type === 'role' && confirmedSet.has((d.label || '').toLowerCase()) ? '#fff' : null)
            .attr('stroke-width', d => d.type === 'role' && confirmedSet.has((d.label || '').toLowerCase()) ? 2 : 0);
        
        const hideRejected = document.getElementById('graph-hide-rejected')?.checked;
        if (hideRejected) {
            GraphState.svg.selectAll('.graph-node.role-rejected').style('display', 'none');
            GraphState.svg.selectAll('.graph-link').style('display', d => {
                const sourceLabel = (typeof d.source === 'object' ? d.source.label : d.source || '').toLowerCase();
                const targetLabel = (typeof d.target === 'object' ? d.target.label : d.target || '').toLowerCase();
                return rejectedSet.has(sourceLabel) || rejectedSet.has(targetLabel) ? 'none' : null;
            });
        } else {
            GraphState.svg.selectAll('.graph-node.role-rejected').style('display', null);
            GraphState.svg.selectAll('.graph-link').style('display', null);
        }
        
        console.log('[TWR Graph] Updated with adjudication:', { confirmed: confirmed.length, deliverables: deliverables.length, rejected: rejected.length });
    }

    // ============================================================
    // D3 GRAPH VISUALIZATION
    // ============================================================

    /**
     * v4.5.1: Update UI elements (legend, bundling slider, hint) based on selected layout
     */
    function updateGraphLayoutUI(layout) {
        // Toggle bundling slider visibility
        const bundlingGroup = document.getElementById('bundling-tension-group');
        if (bundlingGroup) {
            bundlingGroup.classList.toggle('hidden', layout !== 'heb' && layout !== 'semantic-zoom');
        }

        // Toggle legends
        const forceLegend = document.getElementById('graph-legend-force');
        const hebLegend = document.getElementById('graph-legend-heb');
        if (forceLegend) forceLegend.style.display = (layout === 'force' || layout === 'bipartite') ? '' : 'none';
        if (hebLegend) hebLegend.style.display = (layout === 'heb' || layout === 'semantic-zoom') ? '' : 'none';

        // Update graph container data attribute for CSS hooks
        const container = document.getElementById('roles-graph-container');
        if (container) container.setAttribute('data-layout', layout);

        // v4.5.2: Keep layout switcher buttons in sync
        syncLayoutSwitcher(layout);

        // Update hint text
        const hint = document.getElementById('graph-first-time-hint');
        if (hint) {
            const span = hint.querySelector('span:not(.dismiss-hint)');
            if (span) {
                if (layout === 'heb' || layout === 'semantic-zoom') {
                    span.innerHTML = '<strong>Tip:</strong> Hover nodes to highlight connections. Click to drill down. Adjust bundling slider for clarity.';
                } else {
                    span.innerHTML = '<strong>Tip:</strong> Click any node to see details. Drag to rearrange. Scroll to zoom.';
                }
            }
        }
    }

    function initGraphControls() {
        const debounce = getDebounce();
        const toast = getToast();
        
        const weightSlider = document.getElementById('graph-weight-filter');
        const weightValue = document.getElementById('graph-weight-value');
        if (weightSlider && weightValue) {
            weightSlider.addEventListener('input', function() { weightValue.textContent = this.value; updateGraphStats(); });
            weightSlider.addEventListener('change', function() { updateGraphVisibility(); });
        }
        
        document.getElementById('graph-max-nodes')?.addEventListener('change', () => renderRolesGraph());
        document.getElementById('graph-layout')?.addEventListener('change', function() {
            // v4.5.1: Toggle bundling slider and legend visibility based on layout
            const layout = this.value;
            updateGraphLayoutUI(layout);
            syncLayoutSwitcher(layout);
            renderRolesGraph(false, layout);
        });
        document.getElementById('graph-labels')?.addEventListener('change', function() { GraphState.labelMode = this.value; updateGraphLabelVisibility(); });

        // v4.5.2: Layout switcher button bar
        const layoutSwitcher = document.getElementById('graph-layout-switcher');
        if (layoutSwitcher) {
            layoutSwitcher.addEventListener('click', function(e) {
                const btn = e.target.closest('.layout-btn');
                if (!btn) return;
                const layout = btn.dataset.layout;
                if (!layout) return;

                // Update button active states
                layoutSwitcher.querySelectorAll('.layout-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Sync with the hidden select dropdown
                const select = document.getElementById('graph-layout');
                if (select) select.value = layout;

                updateGraphLayoutUI(layout);
                renderRolesGraph(false, layout);
            });
        }

        // v4.5.1: Bundling tension slider
        const bundlingSlider = document.getElementById('graph-bundling');
        const bundlingValue = document.getElementById('graph-bundling-value');
        if (bundlingSlider && bundlingValue) {
            bundlingSlider.addEventListener('input', function() {
                const beta = parseInt(this.value) / 100;
                bundlingValue.textContent = beta.toFixed(2);
                GraphState.bundlingTension = beta;
            });
            bundlingSlider.addEventListener('change', debounce(function() {
                const beta = parseInt(this.value) / 100;
                updateBundlingTension(beta);
            }, 50));
        }

        // Initialize layout UI for default layout
        updateGraphLayoutUI(document.getElementById('graph-layout')?.value || 'heb');
        
        const searchInput = document.getElementById('graph-search');
        if (searchInput) searchInput.addEventListener('input', debounce(function() { highlightSearchMatches(this.value); }, 300));
        
        document.getElementById('btn-refresh-graph')?.addEventListener('click', function() { renderRolesGraph(true); });
        document.getElementById('btn-reset-graph-view')?.addEventListener('click', resetGraphView);
        document.getElementById('btn-clear-graph-selection')?.addEventListener('click', function() { GraphState.isPinned = false; updatePinButton(); clearNodeSelection(true); });
        // v4.5.0: Toggle info panel button (slide in/out)
        document.getElementById('btn-toggle-info-panel')?.addEventListener('click', function() {
            const panel = document.getElementById('graph-info-panel');
            if (panel) {
                panel.classList.toggle('hidden');
                const isHidden = panel.classList.contains('hidden');
                // When hidden: left arrow (click to expand/show panel)
                // When visible: right arrow (click to collapse/hide panel)
                const newIcon = isHidden ? 'chevron-left' : 'chevron-right';
                this.innerHTML = `<i data-lucide="${newIcon}"></i>`;
                if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [this] });
                this.title = isHidden ? 'Show panel' : 'Hide panel';
            }
        });
        document.getElementById('btn-graph-help')?.addEventListener('click', function(e) {
            e.stopPropagation();
            const popup = document.getElementById('graph-help-popup');
            if (popup) popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
        });
        document.getElementById('btn-close-graph-help')?.addEventListener('click', function() { document.getElementById('graph-help-popup').style.display = 'none'; });

        // v4.0.2: Initialize drill-down filtering handlers
        initDrillDownHandlers();

        // v4.3.0: Initialize smart search autocomplete
        initSmartSearchInputs();

        document.getElementById('fallback-role-search')?.addEventListener('input', debounce(renderFallbackRows, 300));
        document.getElementById('fallback-doc-search')?.addEventListener('input', debounce(renderFallbackRows, 300));
        document.getElementById('fallback-sort')?.addEventListener('change', renderFallbackRows);
        document.getElementById('fallback-match-selection')?.addEventListener('change', renderFallbackRows);
    }

    /**
     * v4.5.2: Sync the layout switcher button bar with the selected layout value.
     */
    function syncLayoutSwitcher(layout) {
        const switcher = document.getElementById('graph-layout-switcher');
        if (!switcher) return;
        switcher.querySelectorAll('.layout-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.layout === layout);
        });
    }

    function updatePinButton() {
        // v4.5.0: Pin button removed, now using minimize button instead
        // Kept for backwards compatibility
    }

    function updateGraphLabelVisibility() {
        const container = document.getElementById('roles-graph-container');
        if (!container) return;
        container.classList.remove('labels-all', 'labels-hover', 'labels-selected', 'labels-none');
        container.classList.add(`labels-${GraphState.labelMode}`);

        // v5.1.1: For semantic zoom labels, control visibility via inline styles
        // (CSS :hover doesn't reliably work on SVG elements, so we use D3 mouseover handlers instead)
        const szLabels = container.querySelectorAll('.sz-role-label');
        if (GraphState.labelMode === 'all') {
            szLabels.forEach(el => { el.style.opacity = '1'; });
        } else if (GraphState.labelMode === 'none') {
            szLabels.forEach(el => { el.style.opacity = '0'; });
        } else {
            // 'hover' and 'selected' — labels hidden by default, shown by JS handlers
            szLabels.forEach(el => { el.style.opacity = '0'; });
        }
    }

    function resetGraphView() {
        const toast = getToast();
        if (!GraphState.svg) return;
        GraphState.svg.transition().duration(750).call(d3.zoom().transform, d3.zoomIdentity);
        if (GraphState.simulation) GraphState.simulation.alpha(0.3).restart();
        toast('info', 'Graph view reset');
    }

    function updateGraphStats() {
        if (!GraphState.data) return;
        const minWeight = parseInt(document.getElementById('graph-weight-filter')?.value || '1');
        const visibleLinks = GraphState.data.links.filter(l => l.weight >= minWeight).length;
        
        const nodeCount = document.getElementById('graph-node-count');
        const linkCount = document.getElementById('graph-link-count');
        const visibleCount = document.getElementById('graph-visible-links');
        const threshold = document.getElementById('graph-threshold');
        
        if (nodeCount) nodeCount.textContent = GraphState.data.nodes.length;
        if (linkCount) linkCount.textContent = GraphState.data.links.length;
        if (visibleCount) visibleCount.textContent = visibleLinks;
        if (threshold) threshold.textContent = minWeight;
    }

    function updateGraphVisibility() {
        if (!GraphState.svg || !GraphState.data) return;
        const minWeight = parseInt(document.getElementById('graph-weight-filter')?.value || '1');

        // v4.5.1: HEB/Semantic Zoom weight filtering
        if (GraphState.currentLayout === 'heb' || GraphState.currentLayout === 'semantic-zoom') {
            GraphState.svg.selectAll('.heb-edge').each(function(d) {
                d3.select(this).classed('weight-hidden', d.weight < minWeight);
            });
            GraphState.svg.selectAll('.lod-cluster-edge').each(function(d) {
                d3.select(this).classed('weight-hidden', (d.weight || 0) < minWeight);
            });
            const connectedNodes = new Set();
            GraphState.data.links.forEach(link => {
                if (link.weight >= minWeight) {
                    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                    connectedNodes.add(sourceId);
                    connectedNodes.add(targetId);
                }
            });
            GraphState.svg.selectAll('.heb-node').classed('dimmed', d => !connectedNodes.has(d.id) && minWeight > 1);
            updateGraphStats();
            return;
        }

        // v3.0.73: Only change opacity for links that are not hidden (display != none)
        GraphState.svg.selectAll('.graph-link').each(function(d) {
            const el = d3.select(this);
            // Don't change links that were hidden due to invalid endpoints
            if (el.style('display') !== 'none') {
                el.style('opacity', d.weight >= minWeight ? 0.6 : 0);
            }
        });

        const connectedNodes = new Set();
        GraphState.data.links.forEach(link => {
            if (link.weight >= minWeight) {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                connectedNodes.add(sourceId);
                connectedNodes.add(targetId);
            }
        });

        GraphState.svg.selectAll('.graph-node').classed('dimmed', d => !connectedNodes.has(d.id) && minWeight > 1);
        updateGraphStats();
    }

    async function renderRolesGraph(forceRefresh = false, overrideLayout = null) {
        const api = getApi();
        const toast = getToast();
        
        if (GraphState.isLoading) { console.log('[TWR] Graph already loading, skipping duplicate call'); return; }
        GraphState.isLoading = true;
        
        const container = document.getElementById('roles-graph-container');
        const svgElement = document.getElementById('roles-graph-svg');
        const loading = document.getElementById('graph-loading');
        const fallback = document.getElementById('graph-fallback');
        const weightSlider = document.getElementById('graph-weight-filter');
        const maxWeightDisplay = document.getElementById('graph-max-weight');
        
        if (!container || !svgElement) { GraphState.isLoading = false; return; }
        if (weightSlider) weightSlider.disabled = true;
        
        GraphState.isD3Available = typeof d3 !== 'undefined';
        
        if (!GraphState.isD3Available) {
            console.warn('[TWR Roles] D3.js not available, showing fallback table');
            container.style.display = 'none';
            fallback.style.display = 'block';
            await renderGraphFallbackTable();
            GraphState.isLoading = false;
            return;
        }
        
        loading.style.display = 'flex';
        fallback.style.display = 'none';
        container.style.display = 'block';
        
        try {
            const maxNodes = parseInt(document.getElementById('graph-max-nodes')?.value || '100');
            const minWeight = parseInt(weightSlider?.value || '1');
            const layout = overrideLayout || document.getElementById('graph-layout')?.value || 'force';

            // v4.5.1: Force refresh clears drill-down filters for a clean state
            if (forceRefresh) {
                GraphState.filterStack = [];
                GraphState.filterForwardStack = [];
                GraphState.filteredNodeIds = null;
                GraphState.selectedNode = null;
                GraphState.hierarchyRoot = null;
                GraphState.leafNodeMap = new Map();
                GraphState.documentGroups = [];
                GraphState.lodLevel = 1;
                updateFilterBreadcrumbs();
            }

            const useCache = !forceRefresh;
            const response = await api(`/roles/graph?max_nodes=${maxNodes}&min_weight=${minWeight}&use_cache=${useCache}`);
            
            if (!response.success || !response.data) {
                const errMsg = typeof response.error === 'object'
                    ? (response.error.message || JSON.stringify(response.error))
                    : (response.error || 'Failed to load graph data');
                throw new Error(errMsg);
            }
            
            GraphState.data = response.data;

            // v5.0.2: Safety check — if no nodes/links, show fallback immediately
            if (!response.data.nodes || response.data.nodes.length === 0) {
                console.warn('[TWR Roles] Graph data has no nodes, showing fallback');
                container.style.display = 'none';
                fallback.style.display = 'block';
                await renderGraphFallbackTable();
                return;
            }

            const maxEdgeWeight = Math.max(...(response.data.links || []).map(l => l.weight), 1);
            if (weightSlider) { weightSlider.max = Math.min(maxEdgeWeight, 100); weightSlider.disabled = false; }
            if (maxWeightDisplay) maxWeightDisplay.textContent = maxEdgeWeight;
            
            updateGraphStats();
            updateGraphLabelVisibility();
            renderD3Graph(svgElement, response.data, layout);
            
            if (loading) loading.style.display = 'none';
            setTimeout(() => updateGraphWithAdjudication(), 100);
        } catch (error) {
            console.error('[TWR Roles] Graph rendering error:', error);
            toast('error', 'Failed to render graph: ' + error.message);
            if (weightSlider) weightSlider.disabled = false;
            container.style.display = 'none';
            fallback.style.display = 'block';
            await renderGraphFallbackTable();
        } finally {
            if (loading) loading.style.display = 'none';
            if (typeof lucide !== 'undefined') { try { lucide.createIcons(); } catch(e) {} }
            GraphState.isLoading = false;
            // v4.0.2: Ensure drill-down handlers are initialized after graph renders
            initDrillDownHandlers();
            // v4.1.0: Initialize enhanced features
            initKeyboardNavigation();
            createMiniMap();
            loadSavedFilters();
            loadFilterFromURL();
            // Apply filter from URL if present
            if (GraphState.filterStack.length > 0) {
                setTimeout(() => recomputeFilterFromStack(), 500);
            }
        }
    }

    // =========================================================================
    // v4.5.1: HIERARCHICAL EDGE BUNDLING (HEB) + SEMANTIC ZOOM
    // =========================================================================

    /** Color palette for document groups */
    const HEB_GROUP_COLORS = [
        '#27AE60', '#4A90D9', '#E74C3C', '#F39C12', '#9B59B6',
        '#1ABC9C', '#E67E22', '#06b6d4', '#EC4899', '#6366f1'
    ];

    /**
     * Build a D3 hierarchy from flat graph data (nodes + links).
     * Groups roles by their primary document (highest-weight role-document link).
     * Returns the hierarchy root, a leaf-node map, and document group metadata.
     */
    function buildHierarchyFromGraphData(data) {
        const { nodes, links } = data;
        const docNodes = nodes.filter(n => n.type === 'document');
        const roleNodes = nodes.filter(n => n.type !== 'document');

        // Step 1: Find primary document for each role (highest weight role-document link)
        const rolePrimaryDoc = new Map(); // roleId -> {docId, weight}
        const roleBridgeDocs = new Map(); // roleId -> [{docId, weight}, ...]
        links.forEach(link => {
            if (link.link_type !== 'role-document') return;
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            const roleId = srcId.startsWith('role_') ? srcId : tgtId;
            const docId = srcId.startsWith('doc_') ? srcId : tgtId;
            const weight = link.weight || 1;
            if (!roleBridgeDocs.has(roleId)) roleBridgeDocs.set(roleId, []);
            roleBridgeDocs.get(roleId).push({ docId, weight });
            const current = rolePrimaryDoc.get(roleId);
            if (!current || weight > current.weight) {
                rolePrimaryDoc.set(roleId, { docId, weight });
            }
        });

        // Step 2: Group roles by primary document
        const docGroupMap = new Map();
        docNodes.forEach(doc => {
            docGroupMap.set(doc.id, { docId: doc.id, docLabel: doc.label, docNode: doc, roles: [] });
        });
        const orphans = [];
        roleNodes.forEach(role => {
            const primary = rolePrimaryDoc.get(role.id);
            if (primary && docGroupMap.has(primary.docId)) {
                docGroupMap.get(primary.docId).roles.push(role);
            } else {
                orphans.push(role);
            }
        });

        // Step 3: Build D3 hierarchy input
        const children = [];
        const groupsArr = [];
        [...docGroupMap.values()].filter(g => g.roles.length > 0).forEach((g, i) => {
            const groupColor = HEB_GROUP_COLORS[i % HEB_GROUP_COLORS.length];
            children.push({
                name: g.docLabel,
                docId: g.docId,
                isGroup: true,
                color: groupColor,
                children: [
                    // Include doc node as a leaf too
                    { name: g.docLabel, nodeId: g.docId, nodeData: g.docNode, isDocLeaf: true },
                    ...g.roles.map(r => ({
                        name: r.label,
                        nodeId: r.id,
                        nodeData: r,
                        isBridge: (roleBridgeDocs.get(r.id) || []).length > 1
                    }))
                ]
            });
            groupsArr.push({ docId: g.docId, docLabel: g.docLabel, roles: g.roles, color: groupColor });
        });
        if (orphans.length > 0) {
            const orphanColor = '#6B7280';
            children.push({
                name: 'Other Roles',
                docId: '_orphans',
                isGroup: true,
                color: orphanColor,
                children: orphans.map(r => ({
                    name: r.label, nodeId: r.id, nodeData: r, isBridge: false
                }))
            });
            groupsArr.push({ docId: '_orphans', docLabel: 'Other Roles', roles: orphans, color: orphanColor });
        }

        const hierarchyData = { name: 'root', children };
        const root = d3.hierarchy(hierarchyData);

        // Step 4: Build leaf node map
        const leafMap = new Map();
        root.leaves().forEach(leaf => {
            if (leaf.data.nodeId) leafMap.set(leaf.data.nodeId, leaf);
        });

        return { root, leafMap, groups: groupsArr };
    }

    /**
     * Render the Hierarchical Edge Bundling (HEB) circular graph.
     * Nodes arranged in a circle grouped by document. Edges are bundled bezier curves.
     */
    function renderHEBGraph(svgElement, data) {
        const escapeHtml = getEscapeHtml();
        const truncate = getTruncate();
        let { nodes, links } = data;

        // v4.5.1: Ensure legend + UI reflects HEB layout on every render
        updateGraphLayoutUI('heb');

        if (!nodes || nodes.length === 0) {
            svgElement.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#888">No graph data available</text>';
            return;
        }

        // Filter links to ensure both endpoints exist
        const nodeIds = new Set(nodes.map(n => n.id));
        links = (links || []).filter(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            return nodeIds.has(srcId) && nodeIds.has(tgtId);
        });

        // Build hierarchy
        const { root, leafMap, groups } = buildHierarchyFromGraphData({ nodes, links });
        GraphState.hierarchyRoot = root;
        GraphState.leafNodeMap = leafMap;
        GraphState.documentGroups = groups;
        GraphState.currentLayout = 'heb';

        // Clear SVG
        d3.select(svgElement).selectAll('*').remove();
        const container = svgElement.parentElement;
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 500;
        const radius = Math.min(width, height) / 2 - 100;

        const svg = d3.select(svgElement)
            .attr('width', width).attr('height', height)
            .attr('viewBox', [0, 0, width, height]);
        GraphState.svg = svg;

        const g = svg.append('g').attr('transform', `translate(${width/2},${height/2})`);

        // Zoom + pan
        const zoom = d3.zoom().scaleExtent([0.3, 5]).on('zoom', (event) => {
            g.attr('transform', `translate(${width/2 + event.transform.x},${height/2 + event.transform.y}) scale(${event.transform.k})`);
        });
        svg.call(zoom);
        GraphState.zoom = zoom;

        // Compute circular layout
        d3.cluster().size([360, radius]).separation((a, b) => a.parent === b.parent ? 1 : 2)(root);

        const leaves = root.leaves();

        // Performance mode check
        const nodeCount = leaves.length;
        const linkCount = links.length;
        GraphState.performanceMode = nodeCount > GRAPH_PERFORMANCE.hebNodeThreshold || linkCount > GRAPH_PERFORMANCE.hebLinkThreshold;

        // --- Document group arcs ---
        const groupArcG = g.append('g').attr('class', 'heb-group-arcs');
        const groupChildren = root.children || [];
        groupChildren.forEach((groupNode, gi) => {
            const groupLeaves = groupNode.leaves();
            if (groupLeaves.length === 0) return;
            const angles = groupLeaves.map(l => l.x);
            const minAngle = Math.min(...angles) - 2;
            const maxAngle = Math.max(...angles) + 2;
            const groupColor = groupNode.data.color || HEB_GROUP_COLORS[gi % HEB_GROUP_COLORS.length];

            // Store angle ranges on document groups
            const gIdx = groups.findIndex(gr => gr.docId === groupNode.data.docId);
            if (gIdx >= 0) {
                groups[gIdx].startAngle = minAngle;
                groups[gIdx].endAngle = maxAngle;
            }

            // Arc path
            const arc = d3.arc()
                .innerRadius(radius + 4)
                .outerRadius(radius + 16)
                .startAngle((minAngle) * Math.PI / 180)
                .endAngle((maxAngle) * Math.PI / 180);

            groupArcG.append('path')
                .attr('class', 'heb-group-arc')
                .attr('d', arc)
                .attr('fill', groupColor)
                .attr('stroke', groupColor)
                .attr('data-doc-id', groupNode.data.docId)
                .on('click', function(event) {
                    event.stopPropagation();
                    applyDrillDownFilter(groupNode.data.docId, 'document', groupNode.data.name);
                })
                .on('mouseover', function() { d3.select(this).classed('active', true); })
                .on('mouseout', function() { d3.select(this).classed('active', false); });

            // Group label
            const midAngle = (minAngle + maxAngle) / 2;
            const labelR = radius + 28;
            const labelAngle = midAngle * Math.PI / 180 - Math.PI / 2;
            const lx = Math.cos(labelAngle) * labelR;
            const ly = Math.sin(labelAngle) * labelR;
            const flip = midAngle > 90 && midAngle < 270;

            groupArcG.append('text')
                .attr('class', 'heb-group-label')
                .attr('x', lx).attr('y', ly)
                .attr('text-anchor', flip ? 'end' : 'start')
                .attr('transform', `rotate(${flip ? midAngle - 180 : midAngle}, ${lx}, ${ly})`)
                .attr('fill', groupColor)
                .text(truncate(groupNode.data.name, 22));
        });

        // --- Bundled edges ---
        const line = d3.lineRadial()
            .curve(d3.curveBundle.beta(GraphState.bundlingTension))
            .radius(d => d.y)
            .angle(d => d.x * Math.PI / 180);

        const edgeG = g.append('g').attr('class', 'heb-edges');

        links.forEach(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            const srcLeaf = leafMap.get(srcId);
            const tgtLeaf = leafMap.get(tgtId);
            if (!srcLeaf || !tgtLeaf) return;

            // Get path through hierarchy: source → LCA → target
            const pathNodes = srcLeaf.path(tgtLeaf);
            const linkStyle = LINK_STYLES[link.link_type] || LINK_STYLES['default'];
            const weight = link.weight || 1;

            edgeG.append('path')
                .datum(link)
                .attr('class', 'heb-edge')
                .attr('d', line(pathNodes))
                .attr('stroke', linkStyle.color)
                .attr('stroke-width', Math.max(1, Math.min(weight / 3, 4)))
                .attr('data-source', srcId)
                .attr('data-target', tgtId)
                .attr('data-weight', weight)
                .attr('data-link-type', link.link_type || 'default');
        });

        // --- Role nodes ---
        const nodeG = g.append('g').attr('class', 'heb-nodes');
        const colorScale = { 'role': '#4A90D9', 'document': '#27AE60', 'deliverable': '#F59E0B', 'system': '#8B5CF6', 'tool': '#8B5CF6', 'organization': '#EC4899', 'org': '#EC4899' };

        const tooltip = d3.select('body').selectAll('.graph-tooltip').data([0]).join('div')
            .attr('class', 'graph-tooltip').style('opacity', 0).style('position', 'absolute').style('pointer-events', 'none');

        leaves.forEach(leaf => {
            if (!leaf.data.nodeData) return;
            const nd = leaf.data.nodeData;
            const angle = leaf.x * Math.PI / 180 - Math.PI / 2;
            const px = Math.cos(angle) * leaf.y;
            const py = Math.sin(angle) * leaf.y;
            const mentions = nd.total_mentions || nd.role_count || 1;
            const nodeR = nd.type === 'document' ? Math.max(5, Math.min(8, 4 + Math.sqrt(mentions) * 0.5)) : Math.max(4, Math.min(10, 3 + Math.sqrt(mentions) * 1.2));

            const nodeEl = nodeG.append('g')
                .attr('class', `heb-node graph-node`)
                .attr('transform', `translate(${px},${py})`)
                .attr('data-node-id', nd.id)
                .datum(nd);

            nodeEl.append('circle')
                .attr('r', nodeR)
                .attr('fill', colorScale[nd.type] || '#888')
                .attr('stroke', colorScale[nd.type] || '#888')
                .attr('stroke-width', 1);

            // Label (radially oriented)
            const flip = leaf.x > 90 && leaf.x < 270;
            const labelAngle = flip ? leaf.x - 180 : leaf.x;
            const labelOffset = nodeR + 4;
            nodeEl.append('text')
                .attr('class', 'heb-node-label graph-node-label')
                .attr('transform', `rotate(${labelAngle})`)
                .attr('x', flip ? -labelOffset : labelOffset)
                .attr('dy', '0.35em')
                .attr('text-anchor', flip ? 'end' : 'start')
                .text(truncate(nd.label, 18));

            // Hover
            nodeEl.on('mouseover', function(event) {
                hebHighlightNode(nd.id, links, leafMap, true);
                const stats = nd.type === 'role'
                    ? `Documents: ${nd.document_count || 0}<br>Mentions: ${nd.total_mentions || 0}`
                    : `Roles: ${nd.role_count || 0}<br>Mentions: ${nd.total_mentions || 0}`;
                tooltip.transition().duration(200).style('opacity', 1);
                tooltip.html(`<div class="tooltip-title">${escapeHtml(nd.label)}</div><div class="tooltip-type">${nd.type}</div><div class="tooltip-stats">${stats}</div>`)
                    .style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 10) + 'px');
            }).on('mouseout', function() {
                if (!GraphState.selectedNode || GraphState.selectedNode.id !== nd.id) {
                    hebHighlightNode(null, links, leafMap, false);
                }
                tooltip.transition().duration(300).style('opacity', 0);
            }).on('click', function(event) {
                event.stopPropagation();
                // Use existing selectNode for details panel
                selectNode(nd, links);
                hebHighlightNode(nd.id, links, leafMap, true);
            });
        });

        // Edge hover
        edgeG.selectAll('.heb-edge').on('mouseover', function(event, link) {
            d3.select(this).classed('highlighted', true);
            const srcLabel = leafMap.get(link.source)?.data?.name || link.source;
            const tgtLabel = leafMap.get(link.target)?.data?.name || link.target;
            const linkStyle = LINK_STYLES[link.link_type] || LINK_STYLES['default'];
            tooltip.transition().duration(200).style('opacity', 1);
            tooltip.html(`<div class="tooltip-title">Connection</div><div class="tooltip-connection"><span class="tooltip-role">${escapeHtml(srcLabel)}</span><span class="tooltip-arrow">↔</span><span class="tooltip-role">${escapeHtml(tgtLabel)}</span></div><div class="tooltip-stats">Type: ${linkStyle.label}<br>Weight: ${link.weight || 1}</div>`)
                .style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 10) + 'px');
        }).on('mouseout', function() {
            d3.select(this).classed('highlighted', false);
            tooltip.transition().duration(300).style('opacity', 0);
        });

        // Click on empty space clears selection
        svg.on('click', function() {
            clearNodeSelection();
            hebHighlightNode(null, links, leafMap, false);
        });

        // Update graph stats
        updateGraphStats();
        updateGraphLabelVisibility();

        console.log(`[TWR Graph] HEB rendered: ${leaves.length} nodes, ${links.length} links, ${groups.length} document groups`);
    }

    /**
     * Highlight a node and its connections in the HEB layout.
     * When nodeId is null, reset all highlights.
     */
    function hebHighlightNode(nodeId, links, leafMap, highlight) {
        if (!GraphState.svg) return;

        if (!highlight || !nodeId) {
            // Reset all
            GraphState.svg.selectAll('.heb-edge').classed('highlighted', false).classed('dimmed', false);
            GraphState.svg.selectAll('.heb-node').classed('highlighted', false).classed('dimmed', false);
            return;
        }

        // Find connected node IDs
        const connectedIds = new Set([nodeId]);
        links.forEach(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            if (srcId === nodeId) connectedIds.add(tgtId);
            if (tgtId === nodeId) connectedIds.add(srcId);
        });

        // Highlight/dim edges
        GraphState.svg.selectAll('.heb-edge').each(function(link) {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            const connected = srcId === nodeId || tgtId === nodeId;
            d3.select(this).classed('highlighted', connected).classed('dimmed', !connected);
        });

        // Highlight/dim nodes
        GraphState.svg.selectAll('.heb-node').each(function(nd) {
            const isConnected = connectedIds.has(nd.id);
            d3.select(this).classed('highlighted', isConnected).classed('dimmed', !isConnected);
        });
    }

    /**
     * Update bundling tension on all HEB edges.
     * Called when the bundling slider changes.
     */
    function updateBundlingTension(beta) {
        GraphState.bundlingTension = beta;
        if (!GraphState.svg || GraphState.currentLayout !== 'heb') return;
        if (!GraphState.hierarchyRoot || !GraphState.leafNodeMap) return;

        const line = d3.lineRadial()
            .curve(d3.curveBundle.beta(beta))
            .radius(d => d.y)
            .angle(d => d.x * Math.PI / 180);

        const leafMap = GraphState.leafNodeMap;

        GraphState.svg.selectAll('.heb-edge').each(function(link) {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            const srcLeaf = leafMap.get(srcId);
            const tgtLeaf = leafMap.get(tgtId);
            if (!srcLeaf || !tgtLeaf) return;
            const pathNodes = srcLeaf.path(tgtLeaf);
            d3.select(this).transition().duration(200).attr('d', line(pathNodes));
        });
    }

    /**
     * Render the Semantic Zoom (Level-of-Detail) graph.
     * At low zoom: document cluster circles. At medium: individual nodes. At high: labels.
     */
    function renderSemanticZoomGraph(svgElement, data) {
        const escapeHtml = getEscapeHtml();
        const truncate = getTruncate();
        let { nodes, links } = data;

        // v4.5.1: Ensure legend + UI reflects semantic-zoom layout on every render
        updateGraphLayoutUI('semantic-zoom');

        if (!nodes || nodes.length === 0) {
            svgElement.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#888">No graph data available</text>';
            return;
        }

        // Filter links
        const nodeIds = new Set(nodes.map(n => n.id));
        links = (links || []).filter(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            return nodeIds.has(srcId) && nodeIds.has(tgtId);
        });

        // Build hierarchy (same as HEB)
        const { root, leafMap, groups } = buildHierarchyFromGraphData({ nodes, links });
        GraphState.hierarchyRoot = root;
        GraphState.leafNodeMap = leafMap;
        GraphState.documentGroups = groups;
        GraphState.currentLayout = 'semantic-zoom';
        GraphState.lodLevel = 1;

        d3.select(svgElement).selectAll('*').remove();
        const container = svgElement.parentElement;
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 500;
        const radius = Math.min(width, height) / 2 - 100;

        const svg = d3.select(svgElement)
            .attr('width', width).attr('height', height)
            .attr('viewBox', [0, 0, width, height]);
        GraphState.svg = svg;

        const g = svg.append('g').attr('transform', `translate(${width/2},${height/2})`);

        // Compute cluster positions (force simulation on document groups)
        const clusterData = groups.map((gr, i) => ({
            ...gr,
            x: Math.cos((i / groups.length) * Math.PI * 2) * radius * 0.5,
            y: Math.sin((i / groups.length) * Math.PI * 2) * radius * 0.5,
            r: Math.max(30, Math.min(Math.sqrt(gr.roles.length + 1) * 18, 80))
        }));

        // Compute HEB layout for LOD 2/3
        d3.cluster().size([360, radius]).separation((a, b) => a.parent === b.parent ? 1 : 2)(root);
        const leaves = root.leaves();

        // Compute inter-cluster links
        const interClusterMap = new Map();
        links.forEach(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            const srcGroup = groups.find(gr => gr.roles.some(r => r.id === srcId) || gr.docId === srcId);
            const tgtGroup = groups.find(gr => gr.roles.some(r => r.id === tgtId) || gr.docId === tgtId);
            if (!srcGroup || !tgtGroup || srcGroup.docId === tgtGroup.docId) return;
            const key = [srcGroup.docId, tgtGroup.docId].sort().join('|');
            const existing = interClusterMap.get(key);
            if (existing) { existing.weight += (link.weight || 1); existing.count++; }
            else interClusterMap.set(key, { src: srcGroup.docId, tgt: tgtGroup.docId, weight: link.weight || 1, count: 1 });
        });

        // --- LOD 1: Cluster circles (visible when zoomed out) ---
        const clusterG = g.append('g').attr('class', 'lod-clusters');

        // Inter-cluster edges
        const interEdgeG = clusterG.append('g').attr('class', 'lod-inter-edges');
        interClusterMap.forEach(ice => {
            const src = clusterData.find(c => c.docId === ice.src);
            const tgt = clusterData.find(c => c.docId === ice.tgt);
            if (!src || !tgt) return;
            interEdgeG.append('line')
                .attr('class', 'lod-cluster-edge')
                .attr('x1', src.x).attr('y1', src.y)
                .attr('x2', tgt.x).attr('y2', tgt.y)
                .attr('stroke', 'rgba(214,168,74,0.25)')
                .attr('stroke-width', Math.max(2, Math.min(Math.log2(ice.weight + 1) * 2, 8)));
        });

        // Cluster circles
        const tooltip = d3.select('body').selectAll('.graph-tooltip').data([0]).join('div')
            .attr('class', 'graph-tooltip').style('opacity', 0).style('position', 'absolute').style('pointer-events', 'none');

        clusterData.forEach(cl => {
            const cg = clusterG.append('g')
                .attr('class', 'lod-cluster-group')
                .attr('transform', `translate(${cl.x},${cl.y})`)
                .style('cursor', 'pointer');

            cg.append('circle')
                .attr('class', 'lod-cluster')
                .attr('r', cl.r)
                .attr('fill', cl.color + '18')
                .attr('stroke', cl.color)
                .attr('stroke-width', 2);

            // Internal dots (galaxy scatter)
            cl.roles.forEach((role, i) => {
                const a = i * 2.39996;
                const d = Math.sqrt(i / Math.max(1, cl.roles.length)) * (cl.r - 8);
                cg.append('circle')
                    .attr('class', 'lod-inner-dot')
                    .attr('cx', Math.cos(a) * d).attr('cy', Math.sin(a) * d)
                    .attr('r', 2.5)
                    .attr('fill', cl.color + '88');
            });

            cg.append('text')
                .attr('class', 'lod-cluster-label')
                .attr('text-anchor', 'middle').attr('dy', -4)
                .attr('fill', '#fff')
                .text(truncate(cl.docLabel, 18));

            cg.append('text')
                .attr('class', 'lod-cluster-count')
                .attr('text-anchor', 'middle').attr('dy', 12)
                .attr('fill', '#999').attr('font-size', '10px')
                .text(`${cl.roles.length} roles`);

            cg.on('click', function(event) {
                event.stopPropagation();
                applyDrillDownFilter(cl.docId, 'document', cl.docLabel);
            }).on('mouseover', function(event) {
                d3.select(this).select('.lod-cluster').attr('stroke-width', 3);
                tooltip.transition().duration(200).style('opacity', 1);
                tooltip.html(`<div class="tooltip-title">${escapeHtml(cl.docLabel)}</div><div class="tooltip-stats">Roles: ${cl.roles.length}<br>Click to drill down</div>`)
                    .style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 10) + 'px');
            }).on('mouseout', function() {
                d3.select(this).select('.lod-cluster').attr('stroke-width', 2);
                tooltip.transition().duration(300).style('opacity', 0);
            });
        });

        // --- LOD 2/3: Force-directed relationship graph with document containers ---
        // v5.1.0: True relationship graph — documents as containers, roles inside, cross-doc links visible
        const detailG = g.append('g').attr('class', 'lod-detail').style('opacity', 0);
        const colorScale = { 'role': '#4A90D9', 'document': '#27AE60', 'deliverable': '#F59E0B', 'system': '#8B5CF6', 'tool': '#8B5CF6', 'organization': '#EC4899', 'org': '#EC4899' };

        // --- Build per-group positions: arrange document containers in a grid/circle ---
        const containerPadding = 24;
        const roleNodeR = 6;
        const maxGroupCols = Math.min(groups.length, 4);
        const groupSpacing = radius * 1.1;

        // Position groups in a grid layout centered at origin
        const gridCols = Math.ceil(Math.sqrt(groups.length));
        const gridRows = Math.ceil(groups.length / gridCols);
        const cellW = groupSpacing;
        const cellH = groupSpacing * 0.8;
        const gridOriginX = -(gridCols * cellW) / 2;
        const gridOriginY = -(gridRows * cellH) / 2;

        const groupPositions = clusterData.map((cl, i) => {
            const col = i % gridCols;
            const row = Math.floor(i / gridCols);
            const cx = gridOriginX + (col + 0.5) * cellW;
            const cy = gridOriginY + (row + 0.5) * cellH;
            // Calculate container size based on number of roles
            const nRoles = cl.roles.length;
            const innerCols = Math.ceil(Math.sqrt(nRoles));
            const innerRows = Math.ceil(nRoles / innerCols);
            const boxW = Math.max(120, innerCols * 28 + containerPadding * 2);
            const boxH = Math.max(70, innerRows * 28 + containerPadding * 2 + 24); // +24 for header
            return { ...cl, cx, cy, boxW, boxH, innerCols, innerRows };
        });

        // --- Compute role positions within each container ---
        const rolePositionMap = new Map(); // roleId -> {x, y, groupIdx, color}
        groupPositions.forEach((gp, gi) => {
            const nRoles = gp.roles.length;
            const innerCols = gp.innerCols;
            const startX = gp.cx - (gp.boxW / 2) + containerPadding;
            const startY = gp.cy - (gp.boxH / 2) + containerPadding + 22; // +22 for header
            gp.roles.forEach((role, ri) => {
                const col = ri % innerCols;
                const row = Math.floor(ri / innerCols);
                const rx = startX + col * 28 + 14;
                const ry = startY + row * 28 + 14;
                rolePositionMap.set(role.id, { x: rx, y: ry, groupIdx: gi, color: gp.color });
            });
        });

        // --- Draw document containers ---
        const containersG = detailG.append('g').attr('class', 'sz-containers');
        groupPositions.forEach((gp, gi) => {
            const cg = containersG.append('g').attr('class', 'sz-container-group');

            // Container background (rounded rect)
            cg.append('rect')
                .attr('class', 'sz-container-bg')
                .attr('x', gp.cx - gp.boxW / 2)
                .attr('y', gp.cy - gp.boxH / 2)
                .attr('width', gp.boxW)
                .attr('height', gp.boxH)
                .attr('rx', 10).attr('ry', 10)
                .attr('fill', gp.color + '12')
                .attr('stroke', gp.color + '55')
                .attr('stroke-width', 1.5);

            // Container header bar
            cg.append('rect')
                .attr('class', 'sz-container-header')
                .attr('x', gp.cx - gp.boxW / 2)
                .attr('y', gp.cy - gp.boxH / 2)
                .attr('width', gp.boxW)
                .attr('height', 22)
                .attr('rx', 10).attr('ry', 10)
                .attr('fill', gp.color + '30');

            // Clip the header bottom corners
            cg.append('rect')
                .attr('x', gp.cx - gp.boxW / 2)
                .attr('y', gp.cy - gp.boxH / 2 + 12)
                .attr('width', gp.boxW)
                .attr('height', 10)
                .attr('fill', gp.color + '30');

            // Container label
            cg.append('text')
                .attr('class', 'sz-container-label')
                .attr('x', gp.cx)
                .attr('y', gp.cy - gp.boxH / 2 + 15)
                .attr('text-anchor', 'middle')
                .attr('fill', '#fff')
                .attr('font-size', '11px')
                .attr('font-weight', '600')
                .text(truncate(gp.docLabel, 28));

            // Role count badge
            cg.append('text')
                .attr('class', 'sz-container-count')
                .attr('x', gp.cx + gp.boxW / 2 - 8)
                .attr('y', gp.cy - gp.boxH / 2 + 15)
                .attr('text-anchor', 'end')
                .attr('fill', gp.color)
                .attr('font-size', '10px')
                .attr('font-weight', 'bold')
                .text(gp.roles.length);
        });

        // --- Draw cross-document relationship links ---
        const crossLinksG = detailG.append('g').attr('class', 'sz-cross-links');

        // Find cross-document role-role links
        const crossDocLinks = links.filter(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            const srcPos = rolePositionMap.get(srcId);
            const tgtPos = rolePositionMap.get(tgtId);
            if (!srcPos || !tgtPos) return false;
            return srcPos.groupIdx !== tgtPos.groupIdx; // Only cross-document
        });

        crossDocLinks.forEach(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            const srcPos = rolePositionMap.get(srcId);
            const tgtPos = rolePositionMap.get(tgtId);
            if (!srcPos || !tgtPos) return;

            const linkStyle = LINK_STYLES[link.link_type] || LINK_STYLES['default'];
            const midX = (srcPos.x + tgtPos.x) / 2;
            const midY = (srcPos.y + tgtPos.y) / 2;
            const dx = tgtPos.x - srcPos.x;
            const dy = tgtPos.y - srcPos.y;
            // Curve the link outward
            const curvature = 0.2;
            const cx = midX - dy * curvature;
            const cy = midY + dx * curvature;

            crossLinksG.append('path')
                .datum(link)
                .attr('class', 'sz-cross-link')
                .attr('d', `M${srcPos.x},${srcPos.y} Q${cx},${cy} ${tgtPos.x},${tgtPos.y}`)
                .attr('fill', 'none')
                .attr('stroke', linkStyle.color)
                .attr('stroke-opacity', 0.4)
                .attr('stroke-width', Math.max(1, Math.min((link.weight || 1) / 3, 3)))
                .attr('stroke-dasharray', linkStyle.dashArray);
        });

        // --- Draw role nodes inside containers ---
        const roleNodesG = detailG.append('g').attr('class', 'sz-role-nodes');
        const allRolesFlat = [];
        groupPositions.forEach(gp => {
            gp.roles.forEach(role => {
                const pos = rolePositionMap.get(role.id);
                if (!pos) return;
                allRolesFlat.push({ ...role, px: pos.x, py: pos.y, groupColor: pos.color });
            });
        });

        allRolesFlat.forEach(role => {
            const mentions = role.total_mentions || role.role_count || 1;
            const nr = Math.max(4, Math.min(10, 3 + Math.sqrt(mentions)));

            const nodeEl = roleNodesG.append('g')
                .attr('class', 'sz-role-node graph-node')
                .attr('transform', `translate(${role.px},${role.py})`)
                .datum(role);

            nodeEl.append('circle').attr('r', nr)
                .attr('fill', role.groupColor + 'CC')
                .attr('stroke', '#fff').attr('stroke-width', 1);

            // Label (visible at LOD 3)
            nodeEl.append('text')
                .attr('class', 'sz-role-label graph-node-label lod-label-3')
                .attr('x', nr + 3).attr('dy', '0.35em')
                .attr('text-anchor', 'start')
                .attr('fill', '#ccc')
                .attr('font-size', '9px')
                .style('opacity', 0)
                .text(truncate(role.label, 16));

            nodeEl.on('mouseover', function(event) {
                d3.select(this).select('circle').attr('stroke', '#fff').attr('stroke-width', 2.5);
                // v5.1.1: Show label on hover when label mode is 'hover' or 'all'
                const lm = GraphState.labelMode || 'selected';
                if (lm === 'hover' || lm === 'all') {
                    d3.select(this).select('.sz-role-label').transition().duration(150).style('opacity', 1);
                }
                // Highlight connected cross-doc links
                crossLinksG.selectAll('.sz-cross-link').each(function(d) {
                    const sid = typeof d.source === 'object' ? d.source.id : d.source;
                    const tid = typeof d.target === 'object' ? d.target.id : d.target;
                    const connected = sid === role.id || tid === role.id;
                    d3.select(this)
                        .attr('stroke-opacity', connected ? 0.9 : 0.08)
                        .attr('stroke-width', connected ? 3 : 1);
                });
                tooltip.transition().duration(200).style('opacity', 1);
                const stats = role.type === 'role'
                    ? `Documents: ${role.document_count || 0}<br>Mentions: ${role.total_mentions || 0}`
                    : `Roles: ${role.role_count || 0}`;
                tooltip.html(`<div class="tooltip-title">${escapeHtml(role.label)}</div><div class="tooltip-type">${role.type}</div><div class="tooltip-stats">${stats}</div>`)
                    .style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 10) + 'px');
            }).on('mouseout', function() {
                d3.select(this).select('circle').attr('stroke', '#fff').attr('stroke-width', 1);
                // v5.1.1: Hide label on mouseout when not in 'all' mode and not at LOD 3
                const lm = GraphState.labelMode || 'selected';
                if (lm !== 'all' && GraphState.lodLevel < 3) {
                    d3.select(this).select('.sz-role-label').transition().duration(200).style('opacity', 0);
                }
                crossLinksG.selectAll('.sz-cross-link')
                    .attr('stroke-opacity', 0.4)
                    .attr('stroke-width', function(d) { return Math.max(1, Math.min((d.weight || 1) / 3, 3)); });
                tooltip.transition().duration(300).style('opacity', 0);
            }).on('click', function(event) {
                event.stopPropagation();
                // v5.1.1: Enhanced selection with animation
                szSelectRole(role, links, crossLinksG, roleNodesG, containersG, rolePositionMap, groupPositions);
                selectNode(role, links);
            });
        });

        // --- Zoom-based LOD transitions ---
        // v5.1.0: Lower threshold so less zooming needed to see relationship graph
        const zoomBehavior = d3.zoom()
            .scaleExtent([0.3, 5])
            .filter(event => {
                // Allow wheel events on the SVG (prevent page scroll stealing them)
                if (event.type === 'wheel') return true;
                return !event.ctrlKey && !event.button;
            })
            .on('zoom', (event) => {
                const k = event.transform.k;
                g.attr('transform', `translate(${width/2 + event.transform.x},${height/2 + event.transform.y}) scale(${k})`);

                // LOD transitions: LOD 1 < 0.8x, LOD 2 0.8x-2.0x, LOD 3 > 2.0x
                const newLevel = k < 0.8 ? 1 : k < 2.0 ? 2 : 3;
                if (newLevel !== GraphState.lodLevel) {
                    GraphState.lodLevel = newLevel;

                    // LOD 1: Clusters visible, detail hidden
                    clusterG.transition().duration(400).style('opacity', newLevel === 1 ? 1 : 0);
                    // LOD 2+: Detail (relationship graph) visible
                    detailG.transition().duration(400).style('opacity', newLevel >= 2 ? 1 : 0);
                    // LOD 3: Labels visible on role nodes (unless label mode overrides)
                    const labelMode = GraphState.labelMode || 'selected';
                    if (labelMode !== 'all' && labelMode !== 'hover') {
                        detailG.selectAll('.lod-label-3').transition().duration(300)
                            .style('opacity', newLevel >= 3 ? 1 : 0);
                    }

                    console.log(`[TWR Graph] LOD transition: ${newLevel} (scale=${k.toFixed(2)})`);
                }
            });
        svg.call(zoomBehavior);
        // Prevent page scroll when wheel is over the SVG
        svg.on('wheel.zoom', function(event) { event.preventDefault(); });
        GraphState.zoom = zoomBehavior;

        // v5.1.0: Start at LOD 2 (relationship graph) by default — zoom to 1.0 which triggers LOD 2
        // This gives users the relationship view immediately
        svg.call(zoomBehavior.transform, d3.zoomIdentity.scale(1.0));
        GraphState.lodLevel = 2;
        clusterG.style('opacity', 0);
        detailG.style('opacity', 1);

        // Click empty space — clear both standard + semantic zoom selections
        svg.on('click', function() {
            clearNodeSelection();
            szClearSelection(crossLinksG, roleNodesG, containersG);
        });

        updateGraphStats();
        console.log(`[TWR Graph] Semantic Zoom rendered: ${leaves.length} nodes, ${links.length} links, ${groups.length} clusters, LOD=2 (relationship graph)`);
    }

    // =========================================================================
    // v5.1.1: SEMANTIC ZOOM SELECTION HELPERS
    // =========================================================================

    /**
     * Highlight selected role and its connections in the semantic zoom view.
     * Dims unrelated nodes and containers, brightens connected ones, and
     * smoothly pans the view to center on the selected role.
     */
    function szSelectRole(role, links, crossLinksG, roleNodesG, containersG, rolePositionMap, groupPositions) {
        // Find connected role IDs
        const connectedIds = new Set();
        connectedIds.add(role.id);
        links.forEach(link => {
            const srcId = typeof link.source === 'object' ? link.source.id : link.source;
            const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
            if (srcId === role.id) connectedIds.add(tgtId);
            if (tgtId === role.id) connectedIds.add(srcId);
        });

        // Find which container groups are active (contain the selected or connected roles)
        const activeGroupIndices = new Set();
        connectedIds.forEach(cid => {
            const pos = rolePositionMap.get(cid);
            if (pos) activeGroupIndices.add(pos.groupIdx);
        });

        // Animate role nodes
        roleNodesG.selectAll('.sz-role-node')
            .classed('sz-selected', false)
            .classed('sz-connected', false)
            .classed('sz-dimmed', false)
            .each(function(d) {
                const node = d3.select(this);
                if (d.id === role.id) {
                    node.classed('sz-selected', true);
                } else if (connectedIds.has(d.id)) {
                    node.classed('sz-connected', true);
                } else {
                    node.classed('sz-dimmed', true);
                }
            });

        // Animate role node circles with d3 transitions
        roleNodesG.selectAll('.sz-role-node').each(function(d) {
            const circle = d3.select(this).select('circle');
            if (d.id === role.id) {
                circle.transition().duration(400)
                    .attr('stroke', '#ffd700').attr('stroke-width', 3)
                    .attr('r', function() { return parseFloat(d3.select(this).attr('r')) * 1.3; });
            } else if (connectedIds.has(d.id)) {
                circle.transition().duration(400)
                    .attr('stroke', '#fff').attr('stroke-width', 2);
            } else {
                circle.transition().duration(400)
                    .attr('stroke', '#666').attr('stroke-width', 0.5);
            }
        });

        // Animate labels — show for selected + connected, hide for dimmed
        roleNodesG.selectAll('.sz-role-node .sz-role-label').each(function() {
            const parentData = d3.select(this.parentNode).datum();
            d3.select(this).transition().duration(300)
                .style('opacity', connectedIds.has(parentData.id) ? 1 : 0);
        });

        // Animate cross-document links
        crossLinksG.selectAll('.sz-cross-link').each(function(d) {
            const srcId = typeof d.source === 'object' ? d.source.id : d.source;
            const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
            const isConnected = srcId === role.id || tgtId === role.id;
            d3.select(this).transition().duration(400)
                .attr('stroke-opacity', isConnected ? 0.9 : 0.04)
                .attr('stroke-width', isConnected ? 3.5 : 0.5);
        });

        // Animate containers — active vs dimmed
        containersG.selectAll('.sz-container-group')
            .classed('sz-container-dimmed', false)
            .classed('sz-container-active', false)
            .each(function(d, i) {
                const cg = d3.select(this);
                if (activeGroupIndices.has(i)) {
                    cg.classed('sz-container-active', true);
                    cg.select('.sz-container-bg').transition().duration(400)
                        .attr('stroke-opacity', 1);
                } else {
                    cg.classed('sz-container-dimmed', true);
                    cg.select('.sz-container-bg').transition().duration(400)
                        .attr('stroke-opacity', 0.15);
                }
            });

        // Smooth pan to center on selected role
        const rolePos = rolePositionMap.get(role.id);
        if (rolePos && GraphState.zoom) {
            const svg = GraphState.svg;
            const width = parseInt(svg.attr('width'));
            const height = parseInt(svg.attr('height'));
            const currentTransform = d3.zoomTransform(svg.node());
            const targetX = -rolePos.x * currentTransform.k;
            const targetY = -rolePos.y * currentTransform.k;
            const newTransform = d3.zoomIdentity
                .translate(targetX, targetY)
                .scale(currentTransform.k);
            svg.transition().duration(600).ease(d3.easeCubicOut)
                .call(GraphState.zoom.transform, newTransform);
        }

        // v5.1.2: Store selection state in GraphState for minimap
        GraphState.szSelectedId = role.id;
        GraphState.szConnectedIds = connectedIds;
        GraphState.szActiveGroups = activeGroupIndices;

        // Update minimap to reflect selection
        setTimeout(() => updateMiniMap(), 100);

        console.log(`[TWR Graph] SZ selected: ${role.label} — ${connectedIds.size} connected nodes, ${activeGroupIndices.size} active containers`);
    }

    /**
     * Clear semantic zoom selection — restore all nodes and containers to default.
     */
    function szClearSelection(crossLinksG, roleNodesG, containersG) {
        if (!roleNodesG || !crossLinksG || !containersG) return;

        roleNodesG.selectAll('.sz-role-node')
            .classed('sz-selected', false)
            .classed('sz-connected', false)
            .classed('sz-dimmed', false);

        // Restore circle styles
        roleNodesG.selectAll('.sz-role-node').each(function(d) {
            const mentions = d.total_mentions || d.role_count || 1;
            const nr = Math.max(4, Math.min(10, 3 + Math.sqrt(mentions)));
            d3.select(this).select('circle').transition().duration(300)
                .attr('stroke', '#fff').attr('stroke-width', 1)
                .attr('r', nr);
        });

        // Restore labels to LOD-based visibility
        roleNodesG.selectAll('.sz-role-node .sz-role-label').transition().duration(300)
            .style('opacity', GraphState.lodLevel >= 3 ? 1 : 0);

        // Restore cross links
        crossLinksG.selectAll('.sz-cross-link').transition().duration(300)
            .attr('stroke-opacity', 0.4)
            .attr('stroke-width', function(d) { return Math.max(1, Math.min((d.weight || 1) / 3, 3)); });

        // Restore containers
        containersG.selectAll('.sz-container-group')
            .classed('sz-container-dimmed', false)
            .classed('sz-container-active', false);
        containersG.selectAll('.sz-container-bg').transition().duration(300)
            .attr('stroke-opacity', 1);

        // v5.1.2: Clear selection state from GraphState and refresh minimap
        GraphState.szSelectedId = null;
        GraphState.szConnectedIds = null;
        GraphState.szActiveGroups = null;
        setTimeout(() => updateMiniMap(), 100);
    }

    // =========================================================================
    // END v4.5.1: HEB + SEMANTIC ZOOM
    // =========================================================================

    function renderD3Graph(svgElement, data, layout = 'force') {
        const escapeHtml = getEscapeHtml();
        const truncate = getTruncate();
        let { nodes } = data;
        
        if (!nodes || nodes.length === 0) {
            svgElement.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#888">No graph data available</text>';
            return;
        }
        
        // v3.0.73: Filter links to ensure both endpoints exist in nodes array
        const nodeIds = new Set(nodes.map(n => n.id));
        const originalLinkCount = (data.links || []).length;
        let links = (data.links || []).filter(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            return nodeIds.has(sourceId) && nodeIds.has(targetId);
        });
        
        // v3.0.76: Iterative peripheral node pruning
        // Remove nodes with insufficient connections (not just orphans)
        // This eliminates "phantom lines" going to barely-connected peripheral nodes
        const MIN_CONNECTIONS = 2; // Nodes need at least 2 connections to be shown
        const originalNodeCount = nodes.length;
        
        // Iteratively prune until stable
        let pruneIterations = 0;
        let nodesRemoved = true;
        while (nodesRemoved && pruneIterations < 10) {
            pruneIterations++;
            nodesRemoved = false;
            
            // Count connections per node
            const connectionCount = new Map();
            nodes.forEach(n => connectionCount.set(n.id, 0));
            
            links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                if (connectionCount.has(sourceId)) {
                    connectionCount.set(sourceId, connectionCount.get(sourceId) + 1);
                }
                if (connectionCount.has(targetId)) {
                    connectionCount.set(targetId, connectionCount.get(targetId) + 1);
                }
            });
            
            // Store connection counts on nodes for styling (v3.0.77)
            nodes.forEach(n => {
                n.connectionCount = connectionCount.get(n.id) || 0;
            });
            
            // Filter nodes with insufficient connections
            const prevNodeCount = nodes.length;
            nodes = nodes.filter(n => connectionCount.get(n.id) >= MIN_CONNECTIONS);
            
            if (nodes.length < prevNodeCount) {
                nodesRemoved = true;
                // Re-filter links to only include those between remaining nodes
                const remainingNodeIds = new Set(nodes.map(n => n.id));
                links = links.filter(link => {
                    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                    return remainingNodeIds.has(sourceId) && remainingNodeIds.has(targetId);
                });
            }
        }
        
        const filteredLinkCount = originalLinkCount - links.length;
        const filteredNodeCount = originalNodeCount - nodes.length;
        
        if (filteredLinkCount > 0 || filteredNodeCount > 0) {
            console.log(`[TWR Graph] Pruned in ${pruneIterations} iterations: ${filteredNodeCount} peripheral nodes, ${filteredLinkCount} links (MIN_CONNECTIONS=${MIN_CONNECTIONS})`);
        }
        console.log(`[TWR Graph] Rendering ${nodes.length} nodes, ${links.length} links (layout=${layout})`);

        // Check if we have anything to render after filtering
        if (nodes.length === 0) {
            svgElement.innerHTML = '<text x="50%" y="50%" text-anchor="middle" fill="#888">No connected nodes to display</text>';
            return;
        }

        // v4.5.1: Route to HEB or Semantic Zoom renderers
        GraphState.currentLayout = layout;
        if (layout === 'heb') {
            renderHEBGraph(svgElement, { nodes, links });
            return;
        }
        if (layout === 'semantic-zoom') {
            renderSemanticZoomGraph(svgElement, { nodes, links });
            return;
        }

        // v4.5.2: Stop any previous simulation to prevent leaked tick handlers
        if (GraphState.simulation) {
            GraphState.simulation.stop();
            GraphState.simulation = null;
        }

        d3.select(svgElement).selectAll('*').remove();

        const container = svgElement.parentElement;
        const width = container.clientWidth || 800;
        const height = container.clientHeight || 500;

        const svg = d3.select(svgElement).attr('width', width).attr('height', height).attr('viewBox', [0, 0, width, height]);
        GraphState.svg = svg;

        const g = svg.append('g');
        const zoom = d3.zoom().scaleExtent([0.2, 4]).on('zoom', (event) => { g.attr('transform', event.transform); });
        svg.call(zoom);
        // v4.1.0: Store zoom behavior for animated transitions
        GraphState.zoom = zoom;

        const colorScale = { 'role': '#4A90D9', 'document': '#27AE60', 'deliverable': '#F59E0B', 'system': '#8B5CF6', 'tool': '#8B5CF6', 'organization': '#EC4899', 'org': '#EC4899' };

        // v4.5.2: Added alphaDecay/alphaMin to cool simulation faster and stop ticking
        let simulation;
        if (layout === 'bipartite') {
            const roles = nodes.filter(n => n.type === 'role');
            const docs = nodes.filter(n => n.type === 'document');
            roles.forEach((n, i) => { n.fx = width * 0.25; n.y = (height / (roles.length + 1)) * (i + 1); });
            docs.forEach((n, i) => { n.fx = width * 0.75; n.y = (height / (docs.length + 1)) * (i + 1); });
            simulation = d3.forceSimulation(nodes)
                .alphaDecay(0.05).alphaMin(0.01).velocityDecay(0.4)
                .force('link', d3.forceLink(links).id(d => d.id).strength(0.1))
                .force('y', d3.forceY(d => d.y).strength(0.5))
                .force('collision', d3.forceCollide().radius(20));
        } else {
            simulation = d3.forceSimulation(nodes)
                .alphaDecay(0.04).alphaMin(0.01).velocityDecay(0.35)
                .force('link', d3.forceLink(links).id(d => d.id).distance(100).strength(d => Math.min(d.weight / 10, 1)))
                .force('charge', d3.forceManyBody().strength(-200))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(30));
        }
        GraphState.simulation = simulation;
        
        const nodeCount = nodes.length;
        const linkCount = links.length;
        GraphState.performanceMode = nodeCount > GRAPH_PERFORMANCE.nodeThreshold || linkCount > GRAPH_PERFORMANCE.linkThreshold;
        GraphState.glowEnabled = nodeCount <= GRAPH_PERFORMANCE.glowThreshold;
        
        const graphContainer = document.getElementById('roles-graph-container');
        if (graphContainer) {
            graphContainer.classList.toggle('performance-mode', GraphState.performanceMode);
            graphContainer.classList.toggle('glow-enabled', GraphState.glowEnabled);
        }

        // v4.0.2: Create/remove performance notice dynamically based on mode
        let perfNotice = document.getElementById('graph-performance-notice');
        if (GraphState.performanceMode) {
            if (!perfNotice && graphContainer) {
                perfNotice = document.createElement('div');
                perfNotice.id = 'graph-performance-notice';
                perfNotice.className = 'graph-performance-notice';
                perfNotice.innerHTML = '<i data-lucide="zap"></i><span>Performance mode</span>';
                perfNotice.style.display = 'flex';
                graphContainer.appendChild(perfNotice);
                if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [perfNotice] });
            } else if (perfNotice) {
                perfNotice.style.display = 'flex';
            }
        } else if (perfNotice) {
            perfNotice.remove();
        }
        
        // v3.0.77: Links with distinct colors for different relationship types
        const link = g.append('g').attr('class', 'links').selectAll('line').data(links).join('line')
            .attr('class', d => `graph-link link-${d.link_type || 'role-document'}`)
            .attr('stroke', d => { const style = LINK_STYLES[d.link_type] || LINK_STYLES['default']; return style.color || '#888'; })
            .attr('stroke-width', d => { const w = d.weight || 1; const base = GraphState.performanceMode ? 1 : 1.5; return Math.max(base, Math.min(w / 2, 6)); })
            .attr('stroke-dasharray', d => { if (!GraphState.linkStylesEnabled || GraphState.performanceMode) return 'none'; const style = LINK_STYLES[d.link_type] || LINK_STYLES['default']; return style.dashArray; })
            .attr('data-weight', d => d.weight || 1).attr('data-link-type', d => d.link_type || 'role-document');
        
        const node = g.append('g').attr('class', 'nodes').selectAll('g').data(nodes).join('g')
            .attr('class', d => {
                let classes = 'graph-node';
                if (GraphState.glowEnabled) classes += ' glow-enabled';
                // v3.0.77: Mark weakly-connected nodes for visual distinction
                if (d.connectionCount <= 2) classes += ' weak-connection';
                return classes;
            })
            .call(d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended));
        
        if (GraphState.glowEnabled && !svg.select('defs').node()) {
            const defs = svg.append('defs');
            const glowFilter = defs.append('filter').attr('id', 'node-glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
            glowFilter.append('feGaussianBlur').attr('stdDeviation', '3').attr('result', 'coloredBlur');
            const feMerge = glowFilter.append('feMerge'); feMerge.append('feMergeNode').attr('in', 'coloredBlur'); feMerge.append('feMergeNode').attr('in', 'SourceGraphic');
            const highlightFilter = defs.append('filter').attr('id', 'node-highlight-glow').attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
            highlightFilter.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'coloredBlur');
            const highlightMerge = highlightFilter.append('feMerge'); highlightMerge.append('feMergeNode').attr('in', 'coloredBlur'); highlightMerge.append('feMergeNode').attr('in', 'SourceGraphic');
        }

        // v3.0.77: Node circles with minimum size and proper visibility for weak nodes
        node.append('circle')
            .attr('r', d => {
                const baseSize = d.type === 'role' ? 12 : 10;
                const mentions = d.total_mentions || d.role_count || 1;
                const calculatedSize = baseSize + Math.sqrt(mentions) * 2;
                // Minimum size of 10px ensures all nodes are clearly visible
                return Math.max(10, Math.min(calculatedSize, 25));
            })
            .attr('fill', d => colorScale[d.type] || '#888')
            .attr('fill-opacity', d => d.connectionCount <= 2 ? 0.5 : 1)
            .attr('stroke', d => colorScale[d.type] || '#888')
            .attr('stroke-width', d => d.connectionCount <= 2 ? 2.5 : 1)
            .attr('stroke-opacity', 1)
            .attr('stroke-dasharray', d => d.connectionCount <= 2 ? '4,2' : 'none');
        
        node.append('text').attr('class', 'graph-node-label').attr('dy', d => (d.type === 'role' ? 12 : 10) + 12).text(d => truncate(d.label, 15));
        
        // v4.5.2: Use data join to avoid accumulating tooltip divs on re-render
        const tooltip = d3.select('body').selectAll('.graph-tooltip').data([0]).join('div').attr('class', 'graph-tooltip').style('opacity', 0).style('position', 'absolute').style('pointer-events', 'none');
        
        link.on('mouseover', function(event, d) {
            d3.select(this).attr('stroke', '#4dabf7').attr('stroke-width', function() { return (parseFloat(d3.select(this).attr('stroke-width')) || 2) + 2; });
            const sourceLabel = typeof d.source === 'object' ? d.source.label : d.source;
            const targetLabel = typeof d.target === 'object' ? d.target.label : d.target;
            const linkStyle = LINK_STYLES[d.link_type] || LINK_STYLES['default'];
            tooltip.transition().duration(200).style('opacity', 1);
            tooltip.html(`<div class="tooltip-title">Connection</div><div class="tooltip-connection"><span class="tooltip-role">${escapeHtml(sourceLabel)}</span><span class="tooltip-arrow">↔</span><span class="tooltip-role">${escapeHtml(targetLabel)}</span></div><div class="tooltip-stats">Type: ${linkStyle.label}<br>Co-occurrences: ${d.weight || 1}${d.shared_paragraphs ? `<br>Shared paragraphs: ${d.shared_paragraphs}` : ''}</div>`).style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 10) + 'px');
        }).on('mouseout', function(event, d) {
            d3.select(this).attr('stroke', null).attr('stroke-width', function() { const w = d.weight || 1; const base = GraphState.performanceMode ? 1 : 1.5; return Math.max(base, Math.min(w / 2, 6)); });
            tooltip.transition().duration(500).style('opacity', 0);
        });
        
        node.on('mouseover', function(event, d) {
            tooltip.transition().duration(200).style('opacity', 1);
            let stats = d.type === 'role' ? `Documents: ${d.document_count || 0}<br>Mentions: ${d.total_mentions || 0}` : `Roles: ${d.role_count || 0}<br>Mentions: ${d.total_mentions || 0}`;
            tooltip.html(`<div class="tooltip-title">${escapeHtml(d.label)}</div><div class="tooltip-type">${d.type}</div><div class="tooltip-stats">${stats}</div>`).style('left', (event.pageX + 10) + 'px').style('top', (event.pageY - 10) + 'px');
        }).on('mouseout', function() { tooltip.transition().duration(500).style('opacity', 0); }).on('click', function(event, d) {
            event.stopPropagation();
            // Apply drill-down filter when clicking a node
            applyDrillDownFilter(d.id, d.type, d.label);
        });
        
        svg.on('click', function() { clearNodeSelection(); });

        // v3.0.73: Enhanced tick handler with safety checks for invalid coordinates
        simulation.on('tick', () => {
            link.each(function(d) {
                const el = d3.select(this);
                // Check if source and target are resolved node objects with valid coordinates
                const sourceValid = d.source && typeof d.source === 'object' &&
                                   isFinite(d.source.x) && isFinite(d.source.y);
                const targetValid = d.target && typeof d.target === 'object' &&
                                   isFinite(d.target.x) && isFinite(d.target.y);

                if (sourceValid && targetValid) {
                    el.attr('x1', d.source.x)
                      .attr('y1', d.source.y)
                      .attr('x2', d.target.x)
                      .attr('y2', d.target.y)
                      .style('display', null);  // Show valid links
                } else {
                    // Hide links with invalid endpoints (dangling links)
                    el.style('display', 'none');
                }
            });
            node.attr('transform', d => {
                // Safety check for node positions
                const x = isFinite(d.x) ? d.x : 0;
                const y = isFinite(d.y) ? d.y : 0;
                return `translate(${x},${y})`;
            });
        });

        function dragstarted(event, d) { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
        function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
        function dragended(event, d) { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }
    }

    function selectNode(d, links) {
        const escapeHtml = getEscapeHtml();
        const truncate = getTruncate();
        const toast = getToast();
        
        GraphState.selectedNode = d;
        
        // Highlight the selected node and its connections
        const connectedIds = new Set();
        connectedIds.add(d.id);
        
        links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            if (sourceId === d.id) connectedIds.add(targetId);
            if (targetId === d.id) connectedIds.add(sourceId);
        });
        
        GraphState.svg.selectAll('.graph-node')
            .classed('selected', node => node.id === d.id)
            .classed('connected', node => node.id !== d.id && connectedIds.has(node.id))
            .classed('dimmed', node => !connectedIds.has(node.id));
        
        GraphState.svg.selectAll('.graph-link')
            .classed('highlighted', link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return sourceId === d.id || targetId === d.id;
            })
            .classed('dimmed', link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return sourceId !== d.id && targetId !== d.id;
            });
        
        // v4.0.2: Build enhanced details panel content
        const panel = document.getElementById('graph-info-panel');
        const title = document.getElementById('info-panel-title');
        const subtitle = document.getElementById('details-panel-subtitle');
        const iconContainer = document.getElementById('details-panel-icon');
        const body = document.getElementById('info-panel-body');

        if (!panel || !body) return;

        // v3.1.0: Ensure panel is visible (may have been hidden by close button)
        panel.style.display = 'flex';

        const isRole = d.type === 'role';
        const typeIcon = isRole ? 'user' : 'file-text';
        const typeLabel = isRole ? 'Role / Entity' : 'Document';

        // Update header
        // v4.6.1: Use original_name as fallback before d.id to avoid showing internal IDs
        title.textContent = d.label || d.original_name || d.id;
        subtitle.textContent = typeLabel;
        iconContainer.className = `details-panel-icon ${isRole ? '' : 'document'}`;
        iconContainer.innerHTML = `<i data-lucide="${typeIcon}"></i>`;

        // Separate connections by type
        const docConnections = [];
        const roleConnections = [];
        let maxWeight = 1;

        // v4.6.1: Build node lookup so connection labels never fall back to raw IDs
        const allNodes = GraphState.data?.nodes || [];
        const nodeMap = new Map(allNodes.map(n => [n.id, n]));

        links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            const sourceNode = typeof link.source === 'object' ? link.source : nodeMap.get(sourceId);
            const targetNode = typeof link.target === 'object' ? link.target : nodeMap.get(targetId);
            const sourceLabel = sourceNode?.label || sourceNode?.original_name || link.source;
            const targetLabel = targetNode?.label || targetNode?.original_name || link.target;
            const sourceType = sourceNode ? sourceNode.type : (String(sourceId).startsWith('role_') ? 'role' : 'document');
            const targetType = targetNode ? targetNode.type : (String(targetId).startsWith('role_') ? 'role' : 'document');

            if (sourceId === d.id || targetId === d.id) {
                const connectedId = sourceId === d.id ? targetId : sourceId;
                const connectedLabel = sourceId === d.id ? targetLabel : sourceLabel;
                const connectedType = sourceId === d.id ? targetType : sourceType;
                const weight = link.weight || 1;
                maxWeight = Math.max(maxWeight, weight);

                const conn = {
                    id: connectedId,
                    label: connectedLabel,
                    weight: weight,
                    type: connectedType,
                    topTerms: link.top_terms || [],
                    linkType: link.link_type || 'role-document'
                };

                if (connectedType === 'document') {
                    docConnections.push(conn);
                } else {
                    roleConnections.push(conn);
                }
            }
        });

        // Sort by weight
        docConnections.sort((a, b) => b.weight - a.weight);
        roleConnections.sort((a, b) => b.weight - a.weight);

        // Build enhanced HTML
        let html = '';

        if (isRole) {
            // Role-specific info
            const category = d.category || 'Unknown';
            const categoryColors = {
                'Organization': { bg: 'rgba(236, 72, 153, 0.12)', text: '#EC4899', border: 'rgba(236, 72, 153, 0.3)' },
                'System': { bg: 'rgba(139, 92, 246, 0.12)', text: '#8B5CF6', border: 'rgba(139, 92, 246, 0.3)' },
                'Process': { bg: 'rgba(245, 158, 11, 0.12)', text: '#F59E0B', border: 'rgba(245, 158, 11, 0.3)' },
                'Human': { bg: 'rgba(74, 144, 217, 0.12)', text: '#4A90D9', border: 'rgba(74, 144, 217, 0.3)' },
                'Unknown': { bg: 'rgba(107, 114, 128, 0.12)', text: '#6B7280', border: 'rgba(107, 114, 128, 0.3)' }
            };
            const catStyle = categoryColors[category] || categoryColors['Unknown'];

            // Stats Row
            html += `
                <div class="details-stats-row">
                    <div class="details-stat-card">
                        <div class="details-stat-value accent">${d.document_count || 0}</div>
                        <div class="details-stat-label">Documents</div>
                    </div>
                    <div class="details-stat-card">
                        <div class="details-stat-value">${d.total_mentions || 0}</div>
                        <div class="details-stat-label">Total Mentions</div>
                    </div>
                </div>
            `;

            // Category Badge
            html += `
                <div class="details-category-badge" style="background: ${catStyle.bg}; color: ${catStyle.text}; border-color: ${catStyle.border};">
                    <i data-lucide="tag" style="width:14px;height:14px;"></i>
                    ${escapeHtml(category)} Category
                </div>
            `;

            // Explanation
            const categoryDesc = category.toLowerCase() === 'organization' ? 'organization/team' :
                                 category.toLowerCase() === 'system' ? 'system/tool' :
                                 category.toLowerCase() === 'process' ? 'process/activity' : 'role';
            html += `
                <div class="details-explanation">
                    <i data-lucide="lightbulb"></i>
                    <p>This ${categoryDesc} appears in <strong>${d.document_count || 0} document${(d.document_count || 0) !== 1 ? 's' : ''}</strong>
                    with <strong>${d.total_mentions || 0} total mention${(d.total_mentions || 0) !== 1 ? 's' : ''}</strong>.
                    ${roleConnections.length > 0 ? `It frequently co-occurs with <strong>${roleConnections.length} other role${roleConnections.length !== 1 ? 's' : ''}</strong>.` : ''}</p>
                </div>
            `;

            // Connected Documents - v4.0.2: Clickable for drill-down filtering
            if (docConnections.length > 0) {
                html += `
                    <div class="details-section">
                        <div class="details-section-header" style="color: #27AE60;">
                            <i data-lucide="file-text"></i>
                            Found in Documents
                            <span class="section-count">${docConnections.length}</span>
                        </div>
                        <p class="details-filter-hint"><i data-lucide="mouse-pointer-click"></i> Click to filter graph</p>
                        <div class="details-connection-list">
                `;
                docConnections.slice(0, 6).forEach(c => {
                    const pct = Math.round((c.weight / maxWeight) * 100);
                    const terms = c.topTerms.length > 0 ? c.topTerms.slice(0, 3).join(', ') : '';
                    // v4.0.2: Escape quotes in ID/label for onclick handler
                    const safeId = String(c.id).replace(/'/g, "\\'");
                    const safeLabel = String(c.label).replace(/'/g, "\\'");
                    html += `
                        <div class="details-connection-item drilldown-target" onclick="TWR.Roles.applyDrillDownFilter('${safeId}', 'document', '${safeLabel}')" title="Click to filter graph to this document">
                            <div class="details-conn-header">
                                <span class="details-conn-name">${escapeHtml(c.label)}</span>
                                <span class="details-conn-badge mentions">${c.weight} mention${c.weight !== 1 ? 's' : ''}</span>
                            </div>
                            <div class="details-conn-bar"><div class="details-conn-bar-fill document" style="width:${pct}%;"></div></div>
                            ${terms ? `<div class="details-conn-terms">Key terms: ${escapeHtml(terms)}</div>` : ''}
                            <div class="drilldown-indicator"><i data-lucide="filter"></i></div>
                        </div>
                    `;
                });
                if (docConnections.length > 6) {
                    html += `<div class="details-show-more drilldown-expand" data-show-type="documents">+ ${docConnections.length - 6} more documents</div>`;
                }
                html += `</div></div>`;
            }

            // Connected Roles (co-occurrence) - v4.0.2: Clickable for drill-down filtering
            if (roleConnections.length > 0) {
                html += `
                    <div class="details-section">
                        <div class="details-section-header" style="color: #4A90D9;">
                            <i data-lucide="users"></i>
                            Works With
                            <span class="section-count">${roleConnections.length}</span>
                        </div>
                        <p style="font-size:12px;color:var(--text-muted);margin:0 0 8px;">Roles that appear in the same documents</p>
                        <p class="details-filter-hint"><i data-lucide="mouse-pointer-click"></i> Click to filter graph</p>
                        <div class="details-connection-list">
                `;
                roleConnections.slice(0, 5).forEach(c => {
                    const pct = Math.round((c.weight / maxWeight) * 100);
                    // v4.0.2: Escape quotes in ID/label for onclick handler
                    const safeId = String(c.id).replace(/'/g, "\\'");
                    const safeLabel = String(c.label).replace(/'/g, "\\'");
                    html += `
                        <div class="details-connection-item drilldown-target" onclick="TWR.Roles.applyDrillDownFilter('${safeId}', 'role', '${safeLabel}')" title="Click to filter graph to this role">
                            <div class="details-conn-header">
                                <span class="details-conn-name">${escapeHtml(c.label)}</span>
                                <span class="details-conn-badge shared">${c.weight} shared</span>
                            </div>
                            <div class="details-conn-bar"><div class="details-conn-bar-fill role" style="width:${pct}%;"></div></div>
                            <div class="drilldown-indicator"><i data-lucide="filter"></i></div>
                        </div>
                    `;
                });
                if (roleConnections.length > 5) {
                    html += `<div class="details-show-more drilldown-expand" data-show-type="roles">+ ${roleConnections.length - 5} more related roles</div>`;
                }
                html += `</div></div>`;
            }

        } else {
            // Document-specific info
            html += `
                <div class="details-stats-row">
                    <div class="details-stat-card">
                        <div class="details-stat-value accent">${d.role_count || roleConnections.length || 0}</div>
                        <div class="details-stat-label">Unique Roles</div>
                    </div>
                    <div class="details-stat-card">
                        <div class="details-stat-value">${d.total_mentions || 0}</div>
                        <div class="details-stat-label">Total Mentions</div>
                    </div>
                </div>
            `;

            // Explanation
            html += `
                <div class="details-explanation">
                    <i data-lucide="lightbulb"></i>
                    <p>This document contains <strong>${d.role_count || roleConnections.length || 0} unique role${(d.role_count || roleConnections.length || 0) !== 1 ? 's' : ''}</strong>
                    mentioned <strong>${d.total_mentions || 0} time${(d.total_mentions || 0) !== 1 ? 's' : ''}</strong> throughout the content.</p>
                </div>
            `;

            // Roles in this document - v4.0.2: Clickable for drill-down filtering
            if (roleConnections.length > 0) {
                html += `
                    <div class="details-section">
                        <div class="details-section-header" style="color: #4A90D9;">
                            <i data-lucide="users"></i>
                            Roles in Document
                            <span class="section-count">${roleConnections.length}</span>
                        </div>
                        <p class="details-filter-hint"><i data-lucide="mouse-pointer-click"></i> Click to filter graph</p>
                        <div class="details-connection-list">
                `;
                roleConnections.slice(0, 8).forEach(c => {
                    const pct = Math.round((c.weight / maxWeight) * 100);
                    const terms = c.topTerms.length > 0 ? c.topTerms.slice(0, 3).join(', ') : '';
                    // v4.0.2: Escape quotes in ID/label for onclick handler
                    const safeId = String(c.id).replace(/'/g, "\\'");
                    const safeLabel = String(c.label).replace(/'/g, "\\'");
                    html += `
                        <div class="details-connection-item drilldown-target" onclick="TWR.Roles.applyDrillDownFilter('${safeId}', 'role', '${safeLabel}')" title="Click to filter graph to this role">
                            <div class="details-conn-header">
                                <span class="details-conn-name">${escapeHtml(c.label)}</span>
                                <span class="details-conn-badge mentions">${c.weight} mention${c.weight !== 1 ? 's' : ''}</span>
                            </div>
                            <div class="details-conn-bar"><div class="details-conn-bar-fill role" style="width:${pct}%;"></div></div>
                            ${terms ? `<div class="details-conn-terms">Key terms: ${escapeHtml(terms)}</div>` : ''}
                            <div class="drilldown-indicator"><i data-lucide="filter"></i></div>
                        </div>
                    `;
                });
                if (roleConnections.length > 8) {
                    html += `<div class="details-show-more drilldown-expand" data-show-type="roles">+ ${roleConnections.length - 8} more roles</div>`;
                }
                html += `</div></div>`;
            }
        }

        // Legend footer
        html += `
            <div class="details-legend">
                <div class="details-legend-title">Graph Legend</div>
                <div class="details-legend-items">
                    <div class="details-legend-item"><span class="details-legend-dot role"></span> Roles/Entities</div>
                    <div class="details-legend-item"><span class="details-legend-dot document"></span> Documents</div>
                    <div class="details-legend-item"><span class="details-legend-line"></span> Connection strength</div>
                </div>
            </div>
        `;

        body.innerHTML = html;
        
        // Refresh Lucide icons in the panel
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ icons: lucide.icons, attrs: { class: '' } }); } catch(e) {}
        }
    }

    function clearNodeSelection(force = false) {
        if (GraphState.isPinned && !force) return;

        GraphState.selectedNode = null;

        if (GraphState.svg) {
            GraphState.svg.selectAll('.graph-node')
                .classed('selected', false)
                .classed('connected', false)
                .classed('dimmed', false);

            GraphState.svg.selectAll('.graph-link')
                .classed('highlighted', false)
                .classed('dimmed', false);
        }

        // v4.0.2: Reset panel to empty state instead of hiding
        const title = document.getElementById('info-panel-title');
        const subtitle = document.getElementById('details-panel-subtitle');
        const iconContainer = document.getElementById('details-panel-icon');
        const body = document.getElementById('info-panel-body');

        if (title) title.textContent = 'Select a Node';
        if (subtitle) subtitle.textContent = 'Click any node to view details';
        if (iconContainer) {
            iconContainer.className = 'details-panel-icon';
            iconContainer.innerHTML = '<i data-lucide="mouse-pointer-click"></i>';
        }
        if (body) {
            body.innerHTML = `
                <div class="details-empty-state">
                    <div class="details-empty-icon">
                        <i data-lucide="mouse-pointer-click"></i>
                    </div>
                    <p>Click on any node in the graph to see detailed information about roles, documents, and their connections.</p>
                </div>
            `;
        }

        // Refresh icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }

    // =========================================================================
    // v4.0.2: DRILL-DOWN FILTERING SYSTEM
    // =========================================================================

    /**
     * Apply a drill-down filter to focus the graph on a specific node and its connections
     * @param {string} nodeId - ID of the node to filter to
     * @param {string} nodeType - Type of node ('role' or 'document')
     * @param {string} nodeLabel - Label for display in breadcrumb
     */
    function applyDrillDownFilter(nodeId, nodeType, nodeLabel) {
        console.log('[TWR Graph] applyDrillDownFilter called:', { nodeId, nodeType, nodeLabel });

        if (!GraphState.data || !GraphState.svg) {
            console.warn('[TWR Graph] Cannot filter - data or svg not ready');
            return;
        }

        // Store original data if this is the first filter
        if (!GraphState.originalData) {
            GraphState.originalData = JSON.parse(JSON.stringify(GraphState.data));
        }

        // Add to filter stack and clear forward stack (new action breaks forward history)
        GraphState.filterStack.push({ id: nodeId, type: nodeType, label: nodeLabel });
        GraphState.filterForwardStack = [];

        // Find all connected nodes
        const connectedNodeIds = new Set([nodeId]);
        GraphState.data.links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            if (sourceId === nodeId) connectedNodeIds.add(targetId);
            if (targetId === nodeId) connectedNodeIds.add(sourceId);
        });

        GraphState.filteredNodeIds = connectedNodeIds;

        // Apply visual filter
        applyFilterVisualization();
        updateFilterBreadcrumbs();

        // Auto-select the filtered node
        const node = GraphState.data.nodes.find(n => n.id === nodeId);
        if (node) {
            selectNode(node, GraphState.data.links);
        }

        console.log(`[TWR Graph] Applied drill-down filter: ${nodeLabel} (${connectedNodeIds.size} nodes visible)`);
    }

    /**
     * Apply visual filtering - dim/hide non-matching nodes
     */
    function applyFilterVisualization() {
        if (!GraphState.svg || !GraphState.filteredNodeIds) return;

        const filteredIds = GraphState.filteredNodeIds;
        const isFiltered = filteredIds && filteredIds.size > 0;

        // v4.5.1: HEB/Semantic Zoom drill-down — re-render with filtered data
        if (GraphState.currentLayout === 'heb' || GraphState.currentLayout === 'semantic-zoom') {
            if (!isFiltered || !GraphState.data) return;
            // Build filtered data with only visible nodes and their links
            const filteredNodes = GraphState.data.nodes.filter(n => filteredIds.has(n.id));
            const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
            const filteredLinks = GraphState.data.links.filter(link => {
                const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                return filteredNodeIds.has(srcId) && filteredNodeIds.has(tgtId);
            });
            const svgElement = document.getElementById('roles-graph-svg');
            if (!svgElement) return;
            if (GraphState.currentLayout === 'heb') {
                renderHEBGraph(svgElement, { nodes: filteredNodes, links: filteredLinks });
            } else {
                renderSemanticZoomGraph(svgElement, { nodes: filteredNodes, links: filteredLinks });
            }
            console.log(`[TWR Graph] HEB drill-down: ${filteredNodes.length} nodes, ${filteredLinks.length} links`);
            return;
        }

        // Update nodes with enhanced visuals
        GraphState.svg.selectAll('.graph-node')
            .classed('filter-hidden', d => isFiltered && !filteredIds.has(d.id))
            .classed('filter-visible', d => isFiltered && filteredIds.has(d.id))
            .each(function(d) {
                const node = d3.select(this);
                const isVisible = !isFiltered || filteredIds.has(d.id);
                const isRole = d.type !== 'document';

                // v4.0.2: Add/update icon overlay for filtered visible nodes
                let iconGroup = node.select('.node-icon-group');
                if (isFiltered && isVisible) {
                    if (iconGroup.empty()) {
                        iconGroup = node.append('g').attr('class', 'node-icon-group');
                        // Use white person bust silhouette for roles, document emoji for docs
                        const iconChar = isRole ? '👤' : '📄';
                        const iconClass = isRole ? 'node-icon-char node-icon-person' : 'node-icon-char node-icon-document';
                        const fontSize = '18px';
                        iconGroup.append('text')
                            .attr('class', iconClass)
                            .attr('text-anchor', 'middle')
                            .attr('dominant-baseline', 'central')
                            .attr('font-size', fontSize)
                            .attr('pointer-events', 'none')
                            .style('filter', isRole
                                ? 'brightness(10) drop-shadow(0 1px 2px rgba(0,0,0,0.6))'
                                : 'drop-shadow(0 1px 2px rgba(0,0,0,0.3))')
                            .text(iconChar);
                    }
                    iconGroup.style('opacity', 1);
                } else if (iconGroup.size()) {
                    iconGroup.style('opacity', 0);
                }
            })
            .transition()
            .duration(400)
            .ease(d3.easeCubicOut)
            .style('opacity', d => {
                if (!isFiltered) return 1;
                return filteredIds.has(d.id) ? 1 : 0.08;
            });

        // v4.0.2: Keep circles visible, enlarge filtered nodes to fit icons
        GraphState.svg.selectAll('.graph-node')
            .select('circle')
            .transition()
            .duration(400)
            .attr('stroke-width', d => {
                if (!isFiltered) return 2;
                return filteredIds.has(d.id) ? 2.5 : 1;
            })
            .attr('r', d => {
                const baseRadius = Math.max(8, Math.min(d.size || 10, 25));
                if (!isFiltered) return baseRadius;
                // Enlarge visible nodes to fit icons nicely
                return filteredIds.has(d.id) ? Math.max(baseRadius * 1.3, 14) : baseRadius * 0.7;
            })
            .style('opacity', d => {
                if (!isFiltered) return 1;
                // Keep circles visible, just fade hidden nodes
                return filteredIds.has(d.id) ? 1 : 0.15;
            });

        // Update links with smoother transitions
        GraphState.svg.selectAll('.graph-link')
            .classed('filter-hidden', d => {
                if (!isFiltered) return false;
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                return !filteredIds.has(sourceId) || !filteredIds.has(targetId);
            })
            .transition()
            .duration(400)
            .ease(d3.easeCubicOut)
            .style('opacity', d => {
                if (!isFiltered) return 0.6;
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                return (filteredIds.has(sourceId) && filteredIds.has(targetId)) ? 0.85 : 0.03;
            })
            .attr('stroke-width', d => {
                if (!isFiltered) return Math.max(1, Math.min((d.weight || 1) / 2, 6));
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                const visible = filteredIds.has(sourceId) && filteredIds.has(targetId);
                return visible ? Math.max(2, Math.min((d.weight || 1) / 1.5, 8)) : 0.5;
            });

        // Update labels visibility - show all labels for visible nodes
        GraphState.svg.selectAll('.graph-node text')
            .transition()
            .duration(400)
            .style('opacity', d => {
                if (!isFiltered) return null; // Use CSS default
                return filteredIds.has(d.id) ? 1 : 0;
            })
            .style('font-weight', d => {
                if (!isFiltered) return null;
                return filteredIds.has(d.id) ? '600' : null;
            });

        // Add filtered class to container for CSS hooks
        const container = document.getElementById('roles-graph-container');
        if (container) {
            container.classList.toggle('graph-filtered', isFiltered);
        }

        // v4.1.0: Enhanced visual effects
        if (isFiltered) {
            // Zoom to fit filtered nodes
            setTimeout(() => zoomToFilteredNodes(), 450);

            // Pulse the active node
            const lastFilter = GraphState.filterStack[GraphState.filterStack.length - 1];
            if (lastFilter) {
                setTimeout(() => pulseActiveNode(lastFilter.id), 500);
            }

            // Animate connections
            setTimeout(() => animateConnections(), 400);

            // Update mini-map
            setTimeout(() => updateMiniMap(), 500);
        }
    }

    /**
     * Clear one level of filtering (go back)
     */
    function popDrillDownFilter() {
        if (GraphState.filterStack.length === 0) return;

        GraphState.filterStack.pop();

        if (GraphState.filterStack.length === 0) {
            // Fully clear filters
            clearAllFilters();
        } else {
            // Recompute filter from remaining stack
            recomputeFilterFromStack();
        }
    }

    /**
     * Clear all filters and restore original view
     */
    function clearAllFilters() {
        GraphState.filterStack = [];
        GraphState.filterForwardStack = [];  // Clear forward history too
        GraphState.filteredNodeIds = null;

        // v4.5.1: Reset HEB state
        GraphState.hierarchyRoot = null;
        GraphState.leafNodeMap = new Map();
        GraphState.documentGroups = [];
        GraphState.lodLevel = 1;

        // v4.5.1: For HEB/Semantic Zoom, re-render from full data
        if ((GraphState.currentLayout === 'heb' || GraphState.currentLayout === 'semantic-zoom') && GraphState.data) {
            const svgElement = document.getElementById('roles-graph-svg');
            if (svgElement) {
                if (GraphState.currentLayout === 'heb') {
                    renderHEBGraph(svgElement, GraphState.data);
                } else {
                    renderSemanticZoomGraph(svgElement, GraphState.data);
                }
            }
            updateFilterBreadcrumbs();
            clearNodeSelection(true);
            console.log('[TWR Graph] Cleared all filters (HEB/Semantic Zoom re-rendered)');
            return;
        }

        // Restore visualization (force/bipartite)
        if (GraphState.svg) {
            // Reset nodes
            GraphState.svg.selectAll('.graph-node')
                .classed('filter-hidden', false)
                .classed('filter-visible', false)
                .each(function() {
                    // Hide icon overlays
                    d3.select(this).select('.node-icon-group').style('opacity', 0);
                })
                .transition()
                .duration(400)
                .ease(d3.easeCubicOut)
                .style('opacity', 1);

            // Reset circle sizes
            GraphState.svg.selectAll('.graph-node circle')
                .transition()
                .duration(400)
                .attr('stroke-width', 2)
                .attr('r', d => Math.max(8, Math.min(d.size || 10, 25)));

            // Reset links
            GraphState.svg.selectAll('.graph-link')
                .classed('filter-hidden', false)
                .transition()
                .duration(400)
                .style('opacity', 0.6)
                .attr('stroke-width', d => Math.max(1, Math.min((d.weight || 1) / 2, 6)));

            // Reset labels
            GraphState.svg.selectAll('.graph-node text')
                .transition()
                .duration(400)
                .style('opacity', null)
                .style('font-weight', null);
        }

        const container = document.getElementById('roles-graph-container');
        if (container) {
            container.classList.remove('graph-filtered');
        }

        updateFilterBreadcrumbs();
        clearNodeSelection(true);

        // Center the view on all nodes after a brief delay for animations
        setTimeout(() => {
            resetZoomToFit();
        }, 450);

        console.log('[TWR Graph] Cleared all filters');
    }

    /**
     * Recompute visible nodes based on current filter stack
     */
    function recomputeFilterFromStack() {
        if (GraphState.filterStack.length === 0 || !GraphState.data) {
            clearAllFilters();
            return;
        }

        // Start with nodes connected to all filters (intersection)
        let visibleNodeIds = null;

        GraphState.filterStack.forEach((filter, index) => {
            const connectedToThis = new Set([filter.id]);
            GraphState.data.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                if (sourceId === filter.id) connectedToThis.add(targetId);
                if (targetId === filter.id) connectedToThis.add(sourceId);
            });

            if (index === 0) {
                visibleNodeIds = connectedToThis;
            } else {
                // Intersect with previous
                visibleNodeIds = new Set([...visibleNodeIds].filter(id => connectedToThis.has(id)));
                // Always keep the filter nodes themselves visible
                visibleNodeIds.add(filter.id);
            }
        });

        GraphState.filteredNodeIds = visibleNodeIds;
        applyFilterVisualization();
        updateFilterBreadcrumbs();

        // Select the last filter node
        const lastFilter = GraphState.filterStack[GraphState.filterStack.length - 1];
        const node = GraphState.data.nodes.find(n => n.id === lastFilter.id);
        if (node) {
            selectNode(node, GraphState.data.links);
        }
    }

    /**
     * Update the filter bar display - v4.0.2: Minimal, compact design
     */
    function updateFilterBreadcrumbs() {
        const escapeHtml = getEscapeHtml();
        let filterBar = document.getElementById('graph-filter-bar');

        if (!filterBar) {
            // Create filter bar if it doesn't exist
            const graphContainer = document.getElementById('roles-graph-container');
            if (!graphContainer) return;

            filterBar = document.createElement('div');
            filterBar.id = 'graph-filter-bar';
            filterBar.className = 'graph-filter-bar';
            graphContainer.appendChild(filterBar);
        }

        if (GraphState.filterStack.length === 0) {
            // If there's forward history, show just the forward button
            if (GraphState.filterForwardStack.length > 0) {
                filterBar.innerHTML = '';
                updateFilterBarWithHistory();
            } else {
                filterBar.innerHTML = '';
            }
            return;
        }

        const visibleCount = GraphState.filteredNodeIds ? GraphState.filteredNodeIds.size : 0;
        const truncate = (str, len) => str.length > len ? str.substring(0, len) + '…' : str;

        let html = '<div class="filter-bar-path">';

        // Home button
        html += `<div class="filter-bar-item home" onclick="TWR.Roles.clearAllFilters()" title="Show all nodes"><i data-lucide="grid-3x3"></i></div>`;

        // Filter path items with emoji icons for better visibility
        GraphState.filterStack.forEach((filter, index) => {
            const icon = filter.type === 'document' ? '📄' : '👤';
            const isLast = index === GraphState.filterStack.length - 1;
            const label = truncate(filter.label, 16);

            html += `<span class="filter-bar-sep">›</span>`;
            html += `<div class="filter-bar-item ${filter.type}${isLast ? ' active' : ''}"
                         onclick="TWR.Roles.navigateToFilter(${index})"
                         title="${escapeHtml(filter.label)}">
                        <span class="filter-bar-icon">${icon}</span>
                        <span class="filter-bar-label">${escapeHtml(label)}</span>
                    </div>`;
        });

        html += '</div>';

        // Node count badge
        html += `<span class="filter-bar-count">${visibleCount}</span>`;

        // v4.1.0: Action buttons (export, share, save)
        html += `<div class="filter-bar-actions">`;
        html += `<button class="filter-bar-action" onclick="TWR.Roles.exportFilteredView()" title="Export as image (PNG)"><i data-lucide="download"></i></button>`;
        html += `<button class="filter-bar-action" onclick="TWR.Roles.copyFilterLink()" title="Copy shareable link"><i data-lucide="share-2"></i></button>`;
        html += `<button class="filter-bar-action" onclick="TWR.Roles.saveCurrentFilter()" title="Save filter (Ctrl+S)"><i data-lucide="bookmark"></i></button>`;
        html += `</div>`;

        // Close button
        html += `<button class="filter-bar-close" onclick="TWR.Roles.clearAllFilters()" title="Clear filter (Esc)"><i data-lucide="x"></i></button>`;

        filterBar.innerHTML = html;

        // Refresh Lucide icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [filterBar] }); } catch(e) {}
        }

        // Update history navigation
        updateFilterBarWithHistory();
    }

    /**
     * Navigate to a specific filter level (clicking breadcrumb)
     */
    function navigateToFilter(index) {
        if (index < 0 || index >= GraphState.filterStack.length) return;

        // Store removed filters in forward stack for redo capability
        const removedFilters = GraphState.filterStack.slice(index + 1);
        GraphState.filterForwardStack = removedFilters.reverse();

        // Remove all filters after this index
        GraphState.filterStack = GraphState.filterStack.slice(0, index + 1);
        recomputeFilterFromStack();
    }

    // ============================================================
    // v4.1.0: ENHANCED FILTERING FEATURES
    // ============================================================

    /**
     * Zoom and pan to center on filtered nodes with smooth animation
     */
    function zoomToFilteredNodes() {
        if (!GraphState.svg || !GraphState.filteredNodeIds || GraphState.filteredNodeIds.size === 0) return;

        const container = document.getElementById('roles-graph-container');
        if (!container) return;

        const width = container.clientWidth;
        const height = container.clientHeight;

        // Calculate bounding box of filtered nodes
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

        GraphState.data.nodes.forEach(node => {
            if (GraphState.filteredNodeIds.has(node.id)) {
                minX = Math.min(minX, node.x || 0);
                maxX = Math.max(maxX, node.x || 0);
                minY = Math.min(minY, node.y || 0);
                maxY = Math.max(maxY, node.y || 0);
            }
        });

        if (minX === Infinity) return;

        // Add padding
        const padding = 60;
        minX -= padding; maxX += padding; minY -= padding; maxY += padding;

        const boxWidth = maxX - minX;
        const boxHeight = maxY - minY;
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;

        // Calculate scale to fit
        const scale = Math.min(
            0.9 * width / boxWidth,
            0.9 * height / boxHeight,
            2.5  // Max zoom
        );

        // Apply zoom transform with animation
        if (GraphState.zoom && typeof d3 !== 'undefined') {
            const svg = d3.select('#roles-graph-container svg');
            const transform = d3.zoomIdentity
                .translate(width / 2, height / 2)
                .scale(Math.max(0.5, scale))
                .translate(-centerX, -centerY);

            svg.transition()
                .duration(750)
                .ease(d3.easeCubicInOut)
                .call(GraphState.zoom.transform, transform);
        }
    }

    /**
     * Add pulse animation to the active/selected node
     */
    function pulseActiveNode(nodeId) {
        if (!GraphState.svg) return;

        // Remove existing pulse
        GraphState.svg.selectAll('.pulse-ring').remove();

        // Find the node
        const nodeEl = GraphState.svg.selectAll('.graph-node')
            .filter(d => d.id === nodeId);

        if (nodeEl.empty()) return;

        const nodeData = nodeEl.datum();
        const radius = Math.max(8, Math.min(nodeData.size || 10, 25)) * 1.3;

        // Add pulse rings
        const pulseGroup = nodeEl.insert('g', ':first-child').attr('class', 'pulse-ring');

        for (let i = 0; i < 3; i++) {
            pulseGroup.append('circle')
                .attr('r', radius)
                .attr('fill', 'none')
                .attr('stroke', nodeData.type === 'document' ? '#27AE60' : '#4A90D9')
                .attr('stroke-width', 2)
                .attr('opacity', 0.6)
                .transition()
                .delay(i * 400)
                .duration(1500)
                .ease(d3.easeCubicOut)
                .attr('r', radius * 3)
                .attr('opacity', 0)
                .attr('stroke-width', 0.5)
                .on('end', function() {
                    if (i === 2) d3.select(this.parentNode).remove();
                });
        }
    }

    /**
     * Animate connection lines with a flowing/glowing effect
     */
    function animateConnections() {
        if (!GraphState.svg || !GraphState.filteredNodeIds) return;

        const filteredIds = GraphState.filteredNodeIds;

        // v4.5.2: Add link-animated class to visible filtered links only.
        // The CSS .graph-link.link-animated handles the animation styling.
        GraphState.svg.selectAll('.graph-link')
            .filter(d => {
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                return filteredIds.has(sourceId) && filteredIds.has(targetId);
            })
            .classed('link-animated', true);
    }

    /**
     * Show relationship label on link hover
     */
    function showLinkTooltip(event, linkData) {
        const escapeHtml = getEscapeHtml();
        let tooltip = document.getElementById('graph-link-tooltip');

        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'graph-link-tooltip';
            tooltip.className = 'graph-link-tooltip';
            document.body.appendChild(tooltip);
        }

        const sourceLabel = typeof linkData.source === 'object' ? linkData.source.label : linkData.source;
        const targetLabel = typeof linkData.target === 'object' ? linkData.target.label : linkData.target;
        const linkType = LINK_STYLES[linkData.type] || LINK_STYLES['default'];

        tooltip.innerHTML = `
            <div class="link-tooltip-header">${escapeHtml(linkType.label)}</div>
            <div class="link-tooltip-nodes">
                <span>${escapeHtml(sourceLabel)}</span>
                <span class="link-tooltip-arrow">↔</span>
                <span>${escapeHtml(targetLabel)}</span>
            </div>
            ${linkData.weight ? `<div class="link-tooltip-weight">Strength: ${linkData.weight}</div>` : ''}
        `;

        tooltip.style.left = (event.pageX + 10) + 'px';
        tooltip.style.top = (event.pageY - 10) + 'px';
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
    }

    function hideLinkTooltip() {
        const tooltip = document.getElementById('graph-link-tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        }
    }

    /**
     * Show quick stats tooltip on node hover
     */
    function showNodeTooltip(event, nodeData) {
        const escapeHtml = getEscapeHtml();
        let tooltip = document.getElementById('graph-node-tooltip');

        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'graph-node-tooltip';
            tooltip.className = 'graph-node-tooltip';
            document.body.appendChild(tooltip);
        }

        // Count connections
        let docCount = 0, roleCount = 0;
        if (GraphState.data && GraphState.data.links) {
            GraphState.data.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                if (sourceId === nodeData.id || targetId === nodeData.id) {
                    const otherId = sourceId === nodeData.id ? targetId : sourceId;
                    const otherNode = GraphState.data.nodes.find(n => n.id === otherId);
                    if (otherNode) {
                        if (otherNode.type === 'document') docCount++;
                        else roleCount++;
                    }
                }
            });
        }

        const icon = nodeData.type === 'document' ? '📄' : '👤';
        const typeLabel = nodeData.type === 'document' ? 'Document' : 'Role';

        tooltip.innerHTML = `
            <div class="node-tooltip-header">
                <span class="node-tooltip-icon">${icon}</span>
                <span class="node-tooltip-label">${escapeHtml(nodeData.label)}</span>
            </div>
            <div class="node-tooltip-type">${typeLabel}</div>
            <div class="node-tooltip-stats">
                ${docCount > 0 ? `<span>📄 ${docCount} document${docCount !== 1 ? 's' : ''}</span>` : ''}
                ${roleCount > 0 ? `<span>👤 ${roleCount} role${roleCount !== 1 ? 's' : ''}</span>` : ''}
            </div>
            <div class="node-tooltip-hint">Click to drill down</div>
        `;

        tooltip.style.left = (event.pageX + 15) + 'px';
        tooltip.style.top = (event.pageY - 10) + 'px';
        tooltip.style.opacity = '1';
        tooltip.style.visibility = 'visible';
    }

    function hideNodeTooltip() {
        const tooltip = document.getElementById('graph-node-tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.visibility = 'hidden';
        }
    }

    /**
     * Keyboard navigation for the graph
     */
    function initKeyboardNavigation() {
        document.addEventListener('keydown', function(e) {
            if (!GraphState.keyboardNavEnabled) return;

            const container = document.getElementById('roles-graph-container');
            if (!container || !container.closest('.modal.show')) return;

            // Escape - clear filters or close selection
            if (e.key === 'Escape') {
                e.preventDefault();
                if (GraphState.filterStack.length > 0) {
                    popDrillDownFilter();
                } else if (GraphState.selectedNode) {
                    clearNodeSelection(true);
                }
            }

            // Backspace - go back one filter level, Shift+Backspace - go forward
            if (e.key === 'Backspace' && !e.target.matches('input, textarea')) {
                e.preventDefault();
                if (e.shiftKey && GraphState.filterForwardStack.length > 0) {
                    goForwardInHistory();
                } else if (GraphState.filterStack.length > 0) {
                    goBackInHistory();
                }
            }

            // Arrow keys - navigate between connected nodes
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
                navigateToAdjacentNode(e.key);
            }

            // Enter - drill down on selected node
            if (e.key === 'Enter' && GraphState.selectedNode) {
                e.preventDefault();
                const nodeType = GraphState.selectedNode.type === 'document' ? 'document' : 'role';
                applyDrillDownFilter(GraphState.selectedNode.id, nodeType, GraphState.selectedNode.label);
            }

            // S key - save current filter
            if (e.key === 's' && (e.ctrlKey || e.metaKey) && GraphState.filterStack.length > 0) {
                e.preventDefault();
                saveCurrentFilter();
            }
        });
    }

    /**
     * Navigate to an adjacent node using arrow keys
     */
    function navigateToAdjacentNode(direction) {
        if (!GraphState.selectedNode || !GraphState.data) return;

        // Get connected nodes
        const connectedNodes = [];
        GraphState.data.links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            if (sourceId === GraphState.selectedNode.id) {
                const node = GraphState.data.nodes.find(n => n.id === targetId);
                if (node && (!GraphState.filteredNodeIds || GraphState.filteredNodeIds.has(node.id))) {
                    connectedNodes.push(node);
                }
            } else if (targetId === GraphState.selectedNode.id) {
                const node = GraphState.data.nodes.find(n => n.id === sourceId);
                if (node && (!GraphState.filteredNodeIds || GraphState.filteredNodeIds.has(node.id))) {
                    connectedNodes.push(node);
                }
            }
        });

        if (connectedNodes.length === 0) return;

        // Sort by direction
        const currentX = GraphState.selectedNode.x || 0;
        const currentY = GraphState.selectedNode.y || 0;

        connectedNodes.sort((a, b) => {
            const ax = a.x || 0, ay = a.y || 0;
            const bx = b.x || 0, by = b.y || 0;

            if (direction === 'ArrowUp') return ay - by;
            if (direction === 'ArrowDown') return by - ay;
            if (direction === 'ArrowLeft') return ax - bx;
            if (direction === 'ArrowRight') return bx - ax;
            return 0;
        });

        // Filter by direction
        const validNodes = connectedNodes.filter(node => {
            const dx = (node.x || 0) - currentX;
            const dy = (node.y || 0) - currentY;

            if (direction === 'ArrowUp') return dy < -10;
            if (direction === 'ArrowDown') return dy > 10;
            if (direction === 'ArrowLeft') return dx < -10;
            if (direction === 'ArrowRight') return dx > 10;
            return false;
        });

        const nextNode = validNodes[0] || connectedNodes[0];
        if (nextNode) {
            selectNode(nextNode, GraphState.data.links);
        }
    }

    /**
     * Save current filter state to history
     */
    function saveFilterToHistory() {
        if (GraphState.filterStack.length === 0) return;

        const state = {
            stack: [...GraphState.filterStack],
            timestamp: Date.now()
        };

        GraphState.filterHistory.push(state);

        // Keep only last 20 states
        if (GraphState.filterHistory.length > 20) {
            GraphState.filterHistory.shift();
        }

        updateFilterBarWithHistory();
    }

    /**
     * Go back one step in the drill-down filter
     */
    function goBackInHistory() {
        // If no filters, nothing to go back from
        if (GraphState.filterStack.length === 0) {
            return;
        }

        // Save current filter to forward stack before going back
        const currentFilter = GraphState.filterStack.pop();
        if (currentFilter) {
            GraphState.filterForwardStack.push(currentFilter);
        }

        // If stack is now empty, return to full graph with refresh
        if (GraphState.filterStack.length === 0) {
            // Preserve forward stack (don't call clearAllFilters which clears it)
            GraphState.filteredNodeIds = null;

            // Force refresh the graph to show all nodes
            renderRolesGraph(true);

            // Update filter bar (will show empty but with forward button available)
            updateFilterBar();

            // Show toast notification
            const toast = getToast();
            if (toast) toast('info', 'Returned to full graph view');
        } else {
            recomputeFilterFromStack();
        }

        updateFilterBarWithHistory();
    }

    /**
     * Go forward one step (redo) in the drill-down filter
     */
    function goForwardInHistory() {
        // If no forward history, nothing to redo
        if (GraphState.filterForwardStack.length === 0) {
            return;
        }

        // Pop from forward stack and push to filter stack
        const nextFilter = GraphState.filterForwardStack.pop();
        if (nextFilter) {
            GraphState.filterStack.push(nextFilter);
            recomputeFilterFromStack();
        }

        updateFilterBarWithHistory();
    }

    /**
     * Save current filter as a bookmark
     */
    function saveCurrentFilter() {
        if (GraphState.filterStack.length === 0) return;

        const name = prompt('Name this filter path:', GraphState.filterStack.map(f => f.label).join(' → '));
        if (!name) return;

        const saved = {
            name: name,
            stack: [...GraphState.filterStack],
            timestamp: Date.now()
        };

        GraphState.savedFilters.push(saved);

        // Store in localStorage
        try {
            localStorage.setItem('aegis_saved_filters', JSON.stringify(GraphState.savedFilters));
        } catch (e) { console.warn('Could not save filter to localStorage'); }

        showToast('Filter saved: ' + name, 'success');
    }

    /**
     * Load saved filters from localStorage
     */
    function loadSavedFilters() {
        try {
            const saved = localStorage.getItem('aegis_saved_filters');
            if (saved) {
                GraphState.savedFilters = JSON.parse(saved);
            }
        } catch (e) { console.warn('Could not load saved filters'); }
    }

    /**
     * Apply a saved filter
     */
    function applySavedFilter(index) {
        const saved = GraphState.savedFilters[index];
        if (!saved) return;

        saveFilterToHistory();
        GraphState.filterStack = [...saved.stack];
        GraphState.filterForwardStack = [];  // Clear forward history
        recomputeFilterFromStack();

        // Close the panel and show feedback
        toggleSavedFiltersPanel();
        showToast(`Applied filter: ${saved.name}`, 'success');
    }

    /**
     * Update filter bar to include history navigation (back/forward buttons)
     */
    function updateFilterBarWithHistory() {
        const filterBar = document.getElementById('graph-filter-bar');
        if (!filterBar) return;

        // Get or create navigation container
        let navContainer = filterBar.querySelector('.filter-bar-nav');
        if (!navContainer) {
            navContainer = document.createElement('div');
            navContainer.className = 'filter-bar-nav';
            filterBar.insertBefore(navContainer, filterBar.firstChild);
        }

        // Determine button states
        const canGoBack = GraphState.filterStack.length > 0;
        const canGoForward = GraphState.filterForwardStack.length > 0;

        // Build navigation HTML
        navContainer.innerHTML = `
            <button class="filter-bar-back ${canGoBack ? '' : 'disabled'}"
                    ${canGoBack ? '' : 'disabled'}
                    title="Go back one step (Backspace)">
                <i data-lucide="arrow-left"></i>
            </button>
            <button class="filter-bar-forward ${canGoForward ? '' : 'disabled'}"
                    ${canGoForward ? '' : 'disabled'}
                    title="Go forward one step (Shift+Backspace)">
                <i data-lucide="arrow-right"></i>
            </button>
        `;

        // Attach event listeners
        const backBtn = navContainer.querySelector('.filter-bar-back');
        const forwardBtn = navContainer.querySelector('.filter-bar-forward');

        if (backBtn && canGoBack) {
            backBtn.onclick = goBackInHistory;
        }
        if (forwardBtn && canGoForward) {
            forwardBtn.onclick = goForwardInHistory;
        }

        // Refresh Lucide icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [navContainer] }); } catch(e) {}
        }
    }

    /**
     * Multi-select filtering - add node to filter without replacing
     */
    function addToMultiFilter(nodeId, nodeType, nodeLabel) {
        // Check if already in filter
        if (GraphState.filterStack.some(f => f.id === nodeId)) return;

        saveFilterToHistory();

        GraphState.filterStack.push({ id: nodeId, type: nodeType, label: nodeLabel });

        // Compute union of all filtered nodes
        const allConnected = new Set();
        GraphState.filterStack.forEach(filter => {
            allConnected.add(filter.id);
            GraphState.data.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                if (sourceId === filter.id) allConnected.add(targetId);
                if (targetId === filter.id) allConnected.add(sourceId);
            });
        });

        GraphState.filteredNodeIds = allConnected;
        applyFilterVisualization();
        updateFilterBreadcrumbs();
        zoomToFilteredNodes();
    }

    /**
     * Export filtered view - comprehensive data export with image and detailed report
     */
    function exportFilteredView() {
        if (!GraphState.data) {
            showToast('No graph data to export', 'error');
            return;
        }

        try {
            // Gather comprehensive data about the current view
            const exportData = generateComprehensiveExport();

            // Show export options dialog
            showExportDialog(exportData);
        } catch (err) {
            console.error('[TWR Export] Error:', err);
            showToast('Export failed: ' + err.message, 'error');
        }
    }

    /**
     * Generate comprehensive export data
     */
    function generateComprehensiveExport() {
        const data = GraphState.data;
        const filteredNodeIds = GraphState.filteredNodeIds;
        const filterStack = GraphState.filterStack;

        // Get visible nodes
        const visibleNodes = filteredNodeIds
            ? data.nodes.filter(n => filteredNodeIds.has(n.id))
            : data.nodes;

        // Separate roles and documents
        const roles = visibleNodes.filter(n => n.type !== 'document');
        const documents = visibleNodes.filter(n => n.type === 'document');

        // Get visible links
        const visibleNodeIdSet = new Set(visibleNodes.map(n => n.id));
        const visibleLinks = data.links.filter(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            return visibleNodeIdSet.has(sourceId) && visibleNodeIdSet.has(targetId);
        });

        // Build relationship matrix
        const relationships = [];
        visibleLinks.forEach(link => {
            const sourceNode = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
            const targetNode = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
            if (sourceNode && targetNode) {
                relationships.push({
                    source: sourceNode.label || sourceNode.id,
                    sourceType: sourceNode.type || 'role',
                    target: targetNode.label || targetNode.id,
                    targetType: targetNode.type || 'role',
                    weight: link.weight || 1,
                    relationshipType: link.type || 'connection'
                });
            }
        });

        // Calculate statistics
        const stats = {
            totalNodes: visibleNodes.length,
            totalRoles: roles.length,
            totalDocuments: documents.length,
            totalConnections: visibleLinks.length,
            avgConnectionsPerRole: roles.length > 0 ? (visibleLinks.length / roles.length).toFixed(2) : 0,
            filterPath: filterStack.map(f => `${f.type === 'role' ? '👤' : '📄'} ${f.label}`).join(' → ') || 'All nodes (unfiltered)'
        };

        // Build role details
        const roleDetails = roles.map(role => {
            const roleConnections = visibleLinks.filter(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return sourceId === role.id || targetId === role.id;
            });

            const connectedDocs = roleConnections.filter(link => {
                const sourceNode = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
                const targetNode = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
                const otherNode = sourceNode.id === role.id ? targetNode : sourceNode;
                return otherNode && otherNode.type === 'document';
            }).map(link => {
                const sourceNode = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
                const targetNode = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
                const otherNode = sourceNode.id === role.id ? targetNode : sourceNode;
                return otherNode.label || otherNode.id;
            });

            const connectedRoles = roleConnections.filter(link => {
                const sourceNode = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
                const targetNode = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
                const otherNode = sourceNode.id === role.id ? targetNode : sourceNode;
                return otherNode && otherNode.type !== 'document';
            }).map(link => {
                const sourceNode = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
                const targetNode = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
                const otherNode = sourceNode.id === role.id ? targetNode : sourceNode;
                return otherNode.label || otherNode.id;
            });

            return {
                name: role.label || role.id,
                category: role.category || 'Uncategorized',
                totalMentions: role.mentions || role.weight || 1,
                documentsAppearsIn: [...new Set(connectedDocs)],
                coOccurringRoles: [...new Set(connectedRoles)],
                connectionCount: roleConnections.length
            };
        });

        // Build document details
        const documentDetails = documents.map(doc => {
            const docConnections = visibleLinks.filter(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return sourceId === doc.id || targetId === doc.id;
            });

            const rolesInDoc = docConnections.map(link => {
                const sourceNode = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
                const targetNode = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
                const otherNode = sourceNode.id === doc.id ? targetNode : sourceNode;
                return {
                    role: otherNode.label || otherNode.id,
                    mentions: link.weight || 1
                };
            });

            return {
                name: doc.label || doc.id,
                totalRoles: rolesInDoc.length,
                totalMentions: rolesInDoc.reduce((sum, r) => sum + r.mentions, 0),
                roles: rolesInDoc
            };
        });

        // Determine the focused entity (the last item in filter stack)
        const focusedFilter = filterStack.length > 0 ? filterStack[filterStack.length - 1] : null;
        let focusedEntity = null;

        if (focusedFilter) {
            const focusedNode = visibleNodes.find(n => n.id === focusedFilter.id);
            if (focusedNode) {
                const isRole = focusedNode.type !== 'document';
                const focusedConnections = visibleLinks.filter(link => {
                    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                    return sourceId === focusedNode.id || targetId === focusedNode.id;
                });

                // Build detailed info about the focused entity
                const connectedEntities = focusedConnections.map(link => {
                    const sourceNode = typeof link.source === 'object' ? link.source : data.nodes.find(n => n.id === link.source);
                    const targetNode = typeof link.target === 'object' ? link.target : data.nodes.find(n => n.id === link.target);
                    const otherNode = sourceNode.id === focusedNode.id ? targetNode : sourceNode;
                    return {
                        id: otherNode.id,
                        name: otherNode.label || otherNode.id,
                        type: otherNode.type || 'role',
                        weight: link.weight || 1,
                        category: otherNode.category || 'Uncategorized'
                    };
                });

                focusedEntity = {
                    id: focusedNode.id,
                    name: focusedNode.label || focusedNode.id,
                    type: focusedNode.type || 'role',
                    category: focusedNode.category || 'Uncategorized',
                    mentions: focusedNode.mentions || focusedNode.total_mentions || focusedNode.weight || 0,
                    connectionCount: focusedConnections.length,
                    connectedRoles: connectedEntities.filter(e => e.type !== 'document').sort((a, b) => b.weight - a.weight),
                    connectedDocuments: connectedEntities.filter(e => e.type === 'document').sort((a, b) => b.weight - a.weight),
                    isRole: isRole
                };
            }
        }

        // Capture graph SVG snapshot
        let graphSvgData = null;
        const svg = document.querySelector('#roles-graph-container svg');
        if (svg) {
            try {
                const clone = svg.cloneNode(true);
                clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

                // Set explicit dimensions
                const width = svg.clientWidth || 800;
                const height = svg.clientHeight || 600;
                clone.setAttribute('width', width);
                clone.setAttribute('height', height);
                clone.setAttribute('viewBox', `0 0 ${width} ${height}`);

                // Add white background
                const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                bg.setAttribute('width', '100%');
                bg.setAttribute('height', '100%');
                bg.setAttribute('fill', '#f8fafc');
                clone.insertBefore(bg, clone.firstChild);

                // Inline critical styles for standalone SVG
                const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
                styleEl.textContent = `
                    .graph-node text { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; fill: #475569; }
                    .graph-link { stroke-opacity: 0.6; }
                    .graph-node circle { stroke-width: 2px; }
                `;
                clone.insertBefore(styleEl, clone.firstChild.nextSibling);

                graphSvgData = new XMLSerializer().serializeToString(clone);
            } catch (e) {
                console.warn('[TWR Export] Could not capture SVG:', e);
            }
        }

        return {
            exportDate: new Date().toISOString(),
            filterPath: stats.filterPath,
            filterStack: filterStack,
            focusedEntity: focusedEntity,
            graphSvg: graphSvgData,
            summary: stats,
            roles: roleDetails.sort((a, b) => b.connectionCount - a.connectionCount),
            documents: documentDetails.sort((a, b) => b.totalRoles - a.totalRoles),
            relationships: relationships
        };
    }

    /**
     * Show export dialog with options
     */
    function showExportDialog(exportData) {
        const escapeHtml = getEscapeHtml();

        const dialogHtml = `
            <div class="export-dialog-overlay" id="export-dialog-overlay">
                <div class="export-dialog">
                    <div class="export-dialog-header">
                        <h3><i data-lucide="download"></i> Export Roles Graph</h3>
                        <button class="export-dialog-close" onclick="document.getElementById('export-dialog-overlay').remove()">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="export-dialog-content">
                        <div class="export-summary">
                            <div class="export-stat"><strong>${exportData.summary.totalRoles}</strong> Roles</div>
                            <div class="export-stat"><strong>${exportData.summary.totalDocuments}</strong> Documents</div>
                            <div class="export-stat"><strong>${exportData.summary.totalConnections}</strong> Connections</div>
                        </div>
                        <p class="export-filter-path">Filter: ${escapeHtml(exportData.filterPath)}</p>

                        <div class="export-options">
                            <button class="export-option-btn" onclick="TWR.Roles.downloadAsJSON()">
                                <i data-lucide="file-json"></i>
                                <span>JSON Data</span>
                                <small>Complete data with all relationships</small>
                            </button>
                            <button class="export-option-btn" onclick="TWR.Roles.downloadAsCSV()">
                                <i data-lucide="file-spreadsheet"></i>
                                <span>CSV Spreadsheet</span>
                                <small>Role-document matrix for Excel</small>
                            </button>
                            <button class="export-option-btn" onclick="TWR.Roles.downloadAsPNG()">
                                <i data-lucide="image"></i>
                                <span>PNG Image</span>
                                <small>High-resolution graph snapshot</small>
                            </button>
                            <button class="export-option-btn" onclick="TWR.Roles.downloadAsHTML()">
                                <i data-lucide="file-text"></i>
                                <span>HTML Report</span>
                                <small>Detailed interactive report</small>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add dialog to page
        const container = document.createElement('div');
        container.innerHTML = dialogHtml;
        document.body.appendChild(container.firstElementChild);

        // Store export data for download functions
        window._rolesExportData = exportData;

        // Initialize Lucide icons in dialog
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    /**
     * Download export as JSON
     */
    function downloadAsJSON() {
        const data = window._rolesExportData;
        if (!data) return;

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `roles-export-${Date.now()}.json`);
        showToast('JSON exported successfully!', 'success');
        document.getElementById('export-dialog-overlay')?.remove();
    }

    /**
     * Download export as CSV
     */
    function downloadAsCSV() {
        const data = window._rolesExportData;
        if (!data) return;

        // Create CSV with role-document relationships
        let csv = 'Role,Category,Document,Mentions,Co-occurring Roles\n';

        data.roles.forEach(role => {
            role.documentsAppearsIn.forEach(doc => {
                const coRoles = role.coOccurringRoles.slice(0, 5).join('; ');
                csv += `"${role.name}","${role.category}","${doc}",${role.totalMentions},"${coRoles}"\n`;
            });
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        downloadBlob(blob, `roles-export-${Date.now()}.csv`);
        showToast('CSV exported successfully!', 'success');
        document.getElementById('export-dialog-overlay')?.remove();
    }

    /**
     * Download export as PNG image
     */
    function downloadAsPNG() {
        const svg = document.querySelector('#roles-graph-container svg');
        if (!svg) {
            showToast('No graph to export', 'error');
            return;
        }

        // Clone SVG and prepare for export
        const clone = svg.cloneNode(true);
        clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

        // Set explicit dimensions
        const width = svg.clientWidth || 800;
        const height = svg.clientHeight || 600;
        clone.setAttribute('width', width);
        clone.setAttribute('height', height);

        // Add white background
        const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bg.setAttribute('width', '100%');
        bg.setAttribute('height', '100%');
        bg.setAttribute('fill', '#f8fafc');
        clone.insertBefore(bg, clone.firstChild);

        // Convert to data URL
        const svgData = new XMLSerializer().serializeToString(clone);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);

        // Create canvas and draw
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            canvas.width = width * 2;  // 2x for retina
            canvas.height = height * 2;
            const ctx = canvas.getContext('2d');
            ctx.scale(2, 2);
            ctx.fillStyle = '#f8fafc';
            ctx.fillRect(0, 0, width, height);
            ctx.drawImage(img, 0, 0, width, height);

            // Download
            const link = document.createElement('a');
            link.download = `roles-graph-${Date.now()}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();

            URL.revokeObjectURL(url);
            showToast('PNG exported successfully!', 'success');
            document.getElementById('export-dialog-overlay')?.remove();
        };
        img.onerror = function() {
            showToast('Failed to generate image', 'error');
            URL.revokeObjectURL(url);
        };
        img.src = url;
    }

    /**
     * Download export as HTML report
     */
    function downloadAsHTML() {
        const data = window._rolesExportData;
        if (!data) return;

        const html = generateHTMLReport(data);
        const blob = new Blob([html], { type: 'text/html' });
        downloadBlob(blob, `roles-report-${Date.now()}.html`);
        showToast('HTML report exported successfully!', 'success');
        document.getElementById('export-dialog-overlay')?.remove();
    }

    /**
     * Generate comprehensive interactive HTML report
     */
    function generateHTMLReport(data) {
        const escapeHtml = getEscapeHtml();

        // Compute advanced analytics
        const analytics = computeReportAnalytics(data);

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Roles & Responsibilities Analysis - ${new Date().toLocaleDateString()}</title>
    <style>
        :root {
            --primary: #3b82f6;
            --primary-dark: #1d4ed8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --purple: #8b5cf6;
            --pink: #ec4899;
            --gray-50: #f8fafc;
            --gray-100: #f1f5f9;
            --gray-200: #e2e8f0;
            --gray-300: #cbd5e1;
            --gray-400: #94a3b8;
            --gray-500: #64748b;
            --gray-600: #475569;
            --gray-700: #334155;
            --gray-800: #1e293b;
            --gray-900: #0f172a;
            --radius: 12px;
            --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: var(--gray-800); background: var(--gray-50); }

        /* Header */
        .report-header {
            background: linear-gradient(135deg, var(--gray-900) 0%, var(--gray-800) 100%);
            color: white;
            padding: 2.5rem 2rem;
        }
        .report-header .container { max-width: 1400px; margin: 0 auto; }
        .report-header h1 { font-size: 1.875rem; font-weight: 700; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.75rem; }
        .report-header .subtitle { color: var(--gray-400); font-size: 0.9375rem; }
        .report-header .meta { display: flex; gap: 2rem; margin-top: 1.5rem; flex-wrap: wrap; }
        .report-header .meta-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--gray-300); }
        .report-header .meta-item svg { width: 16px; height: 16px; opacity: 0.7; }

        /* Navigation Tabs */
        .nav-tabs {
            background: white;
            border-bottom: 1px solid var(--gray-200);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow);
        }
        .nav-tabs .container { max-width: 1400px; margin: 0 auto; display: flex; gap: 0; overflow-x: auto; }
        .nav-tab {
            padding: 1rem 1.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--gray-500);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .nav-tab:hover { color: var(--gray-700); background: var(--gray-50); }
        .nav-tab.active { color: var(--primary); border-bottom-color: var(--primary); }
        .nav-tab svg { width: 16px; height: 16px; }

        /* Main Content */
        .main-content { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .tab-content { display: none; animation: fadeIn 0.3s ease; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* Cards */
        .card { background: white; border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; }
        .card-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--gray-100); display: flex; justify-content: space-between; align-items: center; }
        .card-header h2 { font-size: 1.125rem; font-weight: 600; color: var(--gray-800); display: flex; align-items: center; gap: 0.5rem; }
        .card-header h2 svg { width: 20px; height: 20px; color: var(--primary); }
        .card-body { padding: 1.5rem; }

        /* Stats Grid */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .stat-card { background: white; border-radius: var(--radius); padding: 1.5rem; box-shadow: var(--shadow); position: relative; overflow: hidden; }
        .stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px; }
        .stat-card.blue::before { background: var(--primary); }
        .stat-card.green::before { background: var(--success); }
        .stat-card.purple::before { background: var(--purple); }
        .stat-card.orange::before { background: var(--warning); }
        .stat-card.pink::before { background: var(--pink); }
        .stat-value { font-size: 2.25rem; font-weight: 700; color: var(--gray-900); line-height: 1.2; }
        .stat-label { font-size: 0.875rem; color: var(--gray-500); margin-top: 0.25rem; }
        .stat-change { font-size: 0.75rem; margin-top: 0.75rem; display: flex; align-items: center; gap: 0.25rem; }
        .stat-change.positive { color: var(--success); }
        .stat-change.neutral { color: var(--gray-500); }

        /* Insight Cards */
        .insights-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .insight-card {
            background: white;
            border-radius: var(--radius);
            padding: 1.5rem 1.5rem 1.75rem;
            box-shadow: var(--shadow);
            border-left: 4px solid var(--primary);
            display: flex;
            flex-direction: column;
            min-height: 180px;
        }
        .insight-card.warning { border-left-color: var(--warning); }
        .insight-card.success { border-left-color: var(--success); }
        .insight-card.info { border-left-color: var(--purple); }
        .insight-title { font-weight: 600; color: var(--gray-800); margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
        .insight-title svg { width: 18px; height: 18px; flex-shrink: 0; }
        .insight-text { font-size: 0.9375rem; color: var(--gray-600); line-height: 1.6; margin-bottom: 0.5rem; }
        .insight-metric {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--gray-700);
            margin-top: auto;
            padding-top: 0.75rem;
            border-top: 1px solid var(--gray-100);
            word-wrap: break-word;
            overflow-wrap: break-word;
            line-height: 1.3;
        }

        /* Charts */
        .chart-container { height: 300px; position: relative; }
        .chart-bar { display: flex; align-items: flex-end; height: 100%; gap: 8px; padding: 20px 0; }
        .bar-item { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; max-width: 60px; }
        .bar { width: 100%; background: linear-gradient(to top, var(--primary), #60a5fa); border-radius: 4px 4px 0 0; transition: all 0.3s; cursor: pointer; min-height: 4px; }
        .bar:hover { background: linear-gradient(to top, var(--primary-dark), var(--primary)); transform: scaleY(1.02); }
        .bar-label { font-size: 0.6875rem; color: var(--gray-500); text-align: center; writing-mode: vertical-rl; transform: rotate(180deg); max-height: 80px; overflow: hidden; text-overflow: ellipsis; }
        .bar-value { font-size: 0.75rem; font-weight: 600; color: var(--gray-700); }

        /* Horizontal Bar Chart */
        .h-bar-chart { display: flex; flex-direction: column; gap: 12px; }
        .h-bar-item { display: flex; align-items: center; gap: 12px; }
        .h-bar-label { width: 150px; font-size: 0.8125rem; color: var(--gray-700); text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex-shrink: 0; }
        .h-bar-track { flex: 1; height: 24px; background: var(--gray-100); border-radius: 4px; overflow: hidden; position: relative; }
        .h-bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; }
        .h-bar-fill span { font-size: 0.75rem; font-weight: 600; color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }

        /* Donut Chart */
        .donut-chart { width: 200px; height: 200px; margin: 0 auto; }
        .donut-legend { display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; margin-top: 1.5rem; }
        .legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8125rem; color: var(--gray-600); }
        .legend-dot { width: 12px; height: 12px; border-radius: 50%; }

        /* Tables */
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table th, .data-table td { padding: 0.875rem 1rem; text-align: left; border-bottom: 1px solid var(--gray-100); }
        .data-table th { background: var(--gray-50); font-weight: 600; color: var(--gray-600); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; position: sticky; top: 0; cursor: pointer; }
        .data-table th:hover { background: var(--gray-100); }
        .data-table th svg { width: 14px; height: 14px; opacity: 0.5; vertical-align: middle; margin-left: 4px; }
        .data-table tbody tr { transition: background 0.15s; }
        .data-table tbody tr:hover { background: var(--gray-50); }
        .data-table td { font-size: 0.875rem; color: var(--gray-700); }

        /* Table Controls */
        .table-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; gap: 1rem; flex-wrap: wrap; }
        .search-box { position: relative; }
        .search-box input { padding: 0.625rem 1rem 0.625rem 2.5rem; border: 1px solid var(--gray-200); border-radius: 8px; font-size: 0.875rem; width: 280px; transition: all 0.2s; }
        .search-box input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
        .search-box svg { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); width: 16px; height: 16px; color: var(--gray-400); }
        .table-info { font-size: 0.8125rem; color: var(--gray-500); }

        /* Badges */
        .badge { display: inline-flex; align-items: center; padding: 0.25rem 0.625rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; }
        .badge-blue { background: #dbeafe; color: #1d4ed8; }
        .badge-green { background: #dcfce7; color: #15803d; }
        .badge-purple { background: #f3e8ff; color: #7c3aed; }
        .badge-orange { background: #ffedd5; color: #c2410c; }
        .badge-pink { background: #fce7f3; color: #be185d; }
        .badge-gray { background: var(--gray-100); color: var(--gray-600); }

        /* Tags */
        .tag-list { display: flex; flex-wrap: wrap; gap: 0.375rem; }
        .tag { background: var(--gray-100); color: var(--gray-600); padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
        .tag.clickable { cursor: pointer; transition: all 0.15s; }
        .tag.clickable:hover { background: var(--gray-200); }

        /* Progress Bars */
        .progress-bar { height: 8px; background: var(--gray-100); border-radius: 4px; overflow: hidden; }
        .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }

        /* Network Stats */
        .network-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; padding: 1rem; background: var(--gray-50); border-radius: 8px; margin-bottom: 1.5rem; }
        .network-stat { text-align: center; }
        .network-stat-value { font-size: 1.5rem; font-weight: 700; color: var(--gray-900); }
        .network-stat-label { font-size: 0.75rem; color: var(--gray-500); }

        /* Two Column Layout */
        .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
        @media (max-width: 900px) { .two-col { grid-template-columns: 1fr; } }

        /* Top Items List */
        .top-list { display: flex; flex-direction: column; gap: 0.75rem; }
        .top-item { display: flex; align-items: center; gap: 1rem; padding: 0.75rem; background: var(--gray-50); border-radius: 8px; transition: all 0.15s; }
        .top-item:hover { background: var(--gray-100); }
        .top-rank { width: 28px; height: 28px; background: var(--primary); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8125rem; font-weight: 600; flex-shrink: 0; }
        .top-rank.gold { background: linear-gradient(135deg, #fbbf24, #f59e0b); }
        .top-rank.silver { background: linear-gradient(135deg, #9ca3af, #6b7280); }
        .top-rank.bronze { background: linear-gradient(135deg, #d97706, #b45309); }
        .top-item-content { flex: 1; min-width: 0; }
        .top-item-name { font-weight: 500; color: var(--gray-800); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .top-item-meta { font-size: 0.75rem; color: var(--gray-500); }
        .top-item-value { font-weight: 600; color: var(--gray-700); }

        /* Print Styles */
        @media print {
            .nav-tabs { display: none; }
            .tab-content { display: block !important; page-break-inside: avoid; margin-bottom: 2rem; }
            .report-header { background: var(--gray-800); -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .card { box-shadow: none; border: 1px solid var(--gray-200); }
            .stat-card { box-shadow: none; border: 1px solid var(--gray-200); }
        }

        /* Scrollable Table Container */
        .table-scroll { max-height: 500px; overflow-y: auto; border-radius: 8px; border: 1px solid var(--gray-200); }
        .table-scroll .data-table th { position: sticky; top: 0; z-index: 10; }

        /* Tooltip */
        [data-tooltip] { position: relative; cursor: help; }
        [data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            padding: 0.5rem 0.75rem;
            background: var(--gray-900);
            color: white;
            font-size: 0.75rem;
            border-radius: 6px;
            white-space: nowrap;
            z-index: 1000;
            margin-bottom: 4px;
        }
        /* Focused Entity Hero */
        .focus-hero {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 2rem;
            border-radius: var(--radius);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }
        .focus-hero::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        }
        .focus-hero-content { position: relative; z-index: 1; }
        .focus-hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        .focus-hero h2 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .focus-hero-meta {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            margin-top: 1.5rem;
        }
        .focus-hero-stat {
            text-align: center;
        }
        .focus-hero-stat-value {
            font-size: 1.75rem;
            font-weight: 700;
        }
        .focus-hero-stat-label {
            font-size: 0.75rem;
            opacity: 0.8;
        }

        /* Connection Cards */
        .connection-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
        }
        .connection-card {
            background: white;
            border-radius: var(--radius);
            padding: 1rem;
            box-shadow: var(--shadow);
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: all 0.2s;
        }
        .connection-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        .connection-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .connection-icon.role { background: #dbeafe; color: #1d4ed8; }
        .connection-icon.document { background: #dcfce7; color: #15803d; }
        .connection-icon svg { width: 20px; height: 20px; }
        .connection-info { flex: 1; min-width: 0; }
        .connection-name { font-weight: 600; color: var(--gray-800); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .connection-meta { font-size: 0.75rem; color: var(--gray-500); }
        .connection-weight {
            background: var(--gray-100);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--gray-600);
        }

        /* Graph Snapshot */
        .graph-snapshot-container {
            border: 1px solid var(--gray-200);
            background: linear-gradient(135deg, var(--gray-50) 0%, #f0f4f8 100%);
        }
        .graph-snapshot {
            overflow: hidden;
        }
        .graph-snapshot svg {
            display: block;
            max-width: none;
        }
        .graph-snapshot-controls button {
            transition: all 0.15s;
        }
        .graph-snapshot-controls button:hover {
            background: var(--gray-100);
            transform: scale(1.05);
        }
        .graph-snapshot-controls button:active {
            transform: scale(0.95);
        }

        @media print {
            .graph-snapshot-controls { display: none !important; }
            .graph-snapshot-container { height: auto !important; min-height: 400px; }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="report-header">
        <div class="container">
            <h1>
                ${data.focusedEntity ? `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:28px;height:28px">${data.focusedEntity.isRole ? '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle>' : '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline>'}</svg>
                ${escapeHtml(data.focusedEntity.name)} - Analysis Report
                ` : `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:28px;height:28px"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                Roles & Responsibilities Analysis
                `}
            </h1>
            <p class="subtitle">${data.focusedEntity ? `Detailed analysis of ${data.focusedEntity.isRole ? 'role' : 'document'} connections and relationships` : 'Comprehensive analysis of organizational roles, documents, and their relationships'}</p>
            <div class="meta">
                <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    Generated: ${new Date().toLocaleString()}
                </div>
                <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    ${data.focusedEntity ? `Focus: ${escapeHtml(data.focusedEntity.name)}` : `View: ${escapeHtml(data.filterPath)}`}
                </div>
                <div class="meta-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    AEGIS Analysis Report
                </div>
            </div>
        </div>
    </header>

    <!-- Navigation Tabs -->
    <nav class="nav-tabs">
        <div class="container">
            ${data.focusedEntity ? `
            <div class="nav-tab active" onclick="showTab('focus')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>
                ${escapeHtml(data.focusedEntity.name)}
            </div>
            ` : ''}
            <div class="nav-tab ${data.focusedEntity ? '' : 'active'}" onclick="showTab('overview')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                Statistics
            </div>
            <div class="nav-tab" onclick="showTab('insights')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                Insights
            </div>
            <div class="nav-tab" onclick="showTab('roles')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                Roles (${data.roles.length})
            </div>
            <div class="nav-tab" onclick="showTab('documents')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                Documents (${data.documents.length})
            </div>
            <div class="nav-tab" onclick="showTab('relationships')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                Relationships (${data.relationships.length})
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
        ${data.focusedEntity ? `
        <!-- Focus Tab - Specific to Selected Entity -->
        <div id="tab-focus" class="tab-content active">
            <!-- Hero Section for Focused Entity -->
            <div class="focus-hero">
                <div class="focus-hero-content">
                    <div class="focus-hero-badge">
                        ${data.focusedEntity.isRole ? `
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        Role / Entity
                        ` : `
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                        Document
                        `}
                    </div>
                    <h2>${escapeHtml(data.focusedEntity.name)}</h2>
                    <p style="opacity: 0.8; margin-top: 0.5rem;">${data.focusedEntity.isRole ? `Category: ${escapeHtml(data.focusedEntity.category)}` : 'Document Analysis'}</p>
                    <div class="focus-hero-meta">
                        <div class="focus-hero-stat">
                            <div class="focus-hero-stat-value">${data.focusedEntity.connectionCount}</div>
                            <div class="focus-hero-stat-label">Total Connections</div>
                        </div>
                        <div class="focus-hero-stat">
                            <div class="focus-hero-stat-value">${data.focusedEntity.connectedRoles.length}</div>
                            <div class="focus-hero-stat-label">Connected Roles</div>
                        </div>
                        <div class="focus-hero-stat">
                            <div class="focus-hero-stat-value">${data.focusedEntity.connectedDocuments.length}</div>
                            <div class="focus-hero-stat-label">Connected Documents</div>
                        </div>
                        ${data.focusedEntity.mentions ? `
                        <div class="focus-hero-stat">
                            <div class="focus-hero-stat-value">${data.focusedEntity.mentions}</div>
                            <div class="focus-hero-stat-label">Total Mentions</div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>

            <div class="two-col">
                <!-- Connected Roles -->
                <div class="card">
                    <div class="card-header">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                            Connected Roles (${data.focusedEntity.connectedRoles.length})
                        </h2>
                    </div>
                    <div class="card-body">
                        ${data.focusedEntity.connectedRoles.length > 0 ? `
                        <div class="connection-grid">
                            ${data.focusedEntity.connectedRoles.map(conn => `
                            <div class="connection-card">
                                <div class="connection-icon role">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                                </div>
                                <div class="connection-info">
                                    <div class="connection-name" title="${escapeHtml(conn.name)}">${escapeHtml(conn.name)}</div>
                                    <div class="connection-meta">${escapeHtml(conn.category || 'Role')}</div>
                                </div>
                                <div class="connection-weight">${conn.weight}×</div>
                            </div>
                            `).join('')}
                        </div>
                        ` : '<p style="color: var(--gray-500); text-align: center; padding: 2rem;">No connected roles</p>'}
                    </div>
                </div>

                <!-- Connected Documents -->
                <div class="card">
                    <div class="card-header">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                            Connected Documents (${data.focusedEntity.connectedDocuments.length})
                        </h2>
                    </div>
                    <div class="card-body">
                        ${data.focusedEntity.connectedDocuments.length > 0 ? `
                        <div class="connection-grid">
                            ${data.focusedEntity.connectedDocuments.map(conn => `
                            <div class="connection-card">
                                <div class="connection-icon document">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                                </div>
                                <div class="connection-info">
                                    <div class="connection-name" title="${escapeHtml(conn.name)}">${escapeHtml(conn.name)}</div>
                                    <div class="connection-meta">Document</div>
                                </div>
                                <div class="connection-weight">${conn.weight}×</div>
                            </div>
                            `).join('')}
                        </div>
                        ` : '<p style="color: var(--gray-500); text-align: center; padding: 2rem;">No connected documents</p>'}
                    </div>
                </div>
            </div>

            <!-- Connection Strength Analysis -->
            <div class="card" style="margin-top: 1.5rem;">
                <div class="card-header">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                        Connection Strength Analysis
                    </h2>
                </div>
                <div class="card-body">
                    <div class="h-bar-chart">
                        ${[...data.focusedEntity.connectedRoles, ...data.focusedEntity.connectedDocuments]
                            .sort((a, b) => b.weight - a.weight)
                            .slice(0, 10)
                            .map((conn, i) => {
                                const maxWeight = Math.max(...[...data.focusedEntity.connectedRoles, ...data.focusedEntity.connectedDocuments].map(c => c.weight), 1);
                                const percentage = (conn.weight / maxWeight) * 100;
                                const isDoc = conn.type === 'document';
                                return `
                                <div class="h-bar-item">
                                    <div class="h-bar-label" title="${escapeHtml(conn.name)}">${isDoc ? '📄' : '👤'} ${escapeHtml(conn.name.substring(0, 18))}${conn.name.length > 18 ? '...' : ''}</div>
                                    <div class="h-bar-track">
                                        <div class="h-bar-fill" style="width: ${percentage}%; background: linear-gradient(90deg, ${isDoc ? 'var(--success)' : 'var(--primary)'}, ${isDoc ? '#34d399' : '#60a5fa'});">
                                            <span>${conn.weight}</span>
                                        </div>
                                    </div>
                                </div>
                                `;
                            }).join('')}
                    </div>
                </div>
            </div>

            <!-- Relationship Graph Snapshot -->
            ${data.graphSvg ? `
            <div class="card" style="margin-top: 1.5rem;">
                <div class="card-header">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                        Relationship Graph
                    </h2>
                    <span class="badge badge-blue">Interactive Snapshot</span>
                </div>
                <div class="card-body" style="padding: 0; overflow: hidden; border-radius: 0 0 var(--radius) var(--radius);">
                    <div class="graph-snapshot-container" style="width: 100%; height: 500px; background: var(--gray-50); display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative;">
                        <div class="graph-snapshot" style="width: 100%; height: 100%;">
                            ${data.graphSvg}
                        </div>
                        <div class="graph-snapshot-controls" style="position: absolute; bottom: 12px; right: 12px; display: flex; gap: 8px;">
                            <button onclick="zoomGraph(-0.2)" style="width: 32px; height: 32px; border: none; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); cursor: pointer; font-size: 18px;">−</button>
                            <button onclick="zoomGraph(0.2)" style="width: 32px; height: 32px; border: none; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); cursor: pointer; font-size: 18px;">+</button>
                            <button onclick="resetGraphZoom()" style="width: 32px; height: 32px; border: none; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); cursor: pointer; font-size: 14px;">⟲</button>
                        </div>
                        <div class="graph-snapshot-legend" style="position: absolute; bottom: 12px; left: 12px; background: white; padding: 8px 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 11px; display: flex; gap: 12px;">
                            <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 10px; height: 10px; background: #4A90D9; border-radius: 50%;"></span> Role</span>
                            <span style="display: flex; align-items: center; gap: 4px;"><span style="width: 10px; height: 10px; background: #27AE60; border-radius: 50%;"></span> Document</span>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
        </div>
        ` : ''}

        <!-- Statistics Tab -->
        <div id="tab-overview" class="tab-content ${data.focusedEntity ? '' : 'active'}">
            <div class="stats-grid">
                <div class="stat-card blue">
                    <div class="stat-value">${data.summary.totalRoles}</div>
                    <div class="stat-label">Total Roles Identified</div>
                    <div class="stat-change neutral">Across ${data.summary.totalDocuments} documents</div>
                </div>
                <div class="stat-card green">
                    <div class="stat-value">${data.summary.totalDocuments}</div>
                    <div class="stat-label">Documents Analyzed</div>
                    <div class="stat-change neutral">${analytics.avgRolesPerDoc} avg roles each</div>
                </div>
                <div class="stat-card purple">
                    <div class="stat-value">${data.summary.totalConnections}</div>
                    <div class="stat-label">Total Connections</div>
                    <div class="stat-change neutral">Network density: ${analytics.networkDensity}%</div>
                </div>
                <div class="stat-card orange">
                    <div class="stat-value">${data.summary.avgConnectionsPerRole}</div>
                    <div class="stat-label">Avg Connections/Role</div>
                    <div class="stat-change neutral">Most connected: ${analytics.mostConnectedRole}</div>
                </div>
            </div>

            <div class="two-col">
                <div class="card">
                    <div class="card-header">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                            Top Roles by Mentions
                        </h2>
                    </div>
                    <div class="card-body">
                        <div class="h-bar-chart">
                            ${analytics.topRolesByMentions.slice(0, 8).map((r, i) => `
                            <div class="h-bar-item">
                                <div class="h-bar-label" title="${escapeHtml(r.name)}">${escapeHtml(r.name.substring(0, 20))}${r.name.length > 20 ? '...' : ''}</div>
                                <div class="h-bar-track">
                                    <div class="h-bar-fill" style="width: ${r.percentage}%; background: linear-gradient(90deg, var(--primary), #60a5fa);">
                                        <span>${r.mentions}</span>
                                    </div>
                                </div>
                            </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>
                            Roles by Category
                        </h2>
                    </div>
                    <div class="card-body">
                        <svg class="donut-chart" viewBox="0 0 100 100">
                            ${analytics.categoryBreakdown.map((cat, i) => {
                                const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1'];
                                return `<circle cx="50" cy="50" r="40" fill="none" stroke="${colors[i % colors.length]}" stroke-width="20"
                                    stroke-dasharray="${cat.percentage * 2.51} 251.2"
                                    stroke-dashoffset="${-analytics.categoryBreakdown.slice(0, i).reduce((a, c) => a + c.percentage * 2.51, 0)}"
                                    transform="rotate(-90 50 50)"/>`;
                            }).join('')}
                            <text x="50" y="47" text-anchor="middle" style="font-size:16px;font-weight:700;fill:var(--gray-900)">${data.roles.length}</text>
                            <text x="50" y="60" text-anchor="middle" style="font-size:7px;fill:var(--gray-500)">ROLES</text>
                        </svg>
                        <div class="donut-legend">
                            ${analytics.categoryBreakdown.map((cat, i) => {
                                const colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#6366f1'];
                                return `<div class="legend-item">
                                    <div class="legend-dot" style="background:${colors[i % colors.length]}"></div>
                                    ${escapeHtml(cat.name)} (${cat.count})
                                </div>`;
                            }).join('')}
                        </div>
                    </div>
                </div>
            </div>

            <div class="two-col" style="margin-top: 1.5rem;">
                <div class="card">
                    <div class="card-header">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                            Most Connected Roles
                        </h2>
                    </div>
                    <div class="card-body">
                        <div class="top-list">
                            ${analytics.mostConnectedRoles.slice(0, 5).map((r, i) => `
                            <div class="top-item">
                                <div class="top-rank ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : ''}">${i + 1}</div>
                                <div class="top-item-content">
                                    <div class="top-item-name">${escapeHtml(r.name)}</div>
                                    <div class="top-item-meta">${r.docCount} documents, ${r.mentions} mentions</div>
                                </div>
                                <div class="top-item-value">${r.connections} connections</div>
                            </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                            Documents with Most Roles
                        </h2>
                    </div>
                    <div class="card-body">
                        <div class="top-list">
                            ${analytics.docsWithMostRoles.slice(0, 5).map((d, i) => `
                            <div class="top-item">
                                <div class="top-rank ${i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : ''}">${i + 1}</div>
                                <div class="top-item-content">
                                    <div class="top-item-name">${escapeHtml(d.name)}</div>
                                    <div class="top-item-meta">${d.mentions} total mentions</div>
                                </div>
                                <div class="top-item-value">${d.roles} roles</div>
                            </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Insights Tab -->
        <div id="tab-insights" class="tab-content">
            <div class="insights-grid">
                ${analytics.insights.map(insight => `
                <div class="insight-card ${insight.type}">
                    <div class="insight-title">
                        ${insight.icon}
                        ${escapeHtml(insight.title)}
                    </div>
                    <div class="insight-text">${escapeHtml(insight.text)}</div>
                    ${insight.metric ? `<div class="insight-metric">${escapeHtml(insight.metric)}</div>` : ''}
                </div>
                `).join('')}
            </div>

            <div class="card" style="margin-top: 2rem;">
                <div class="card-header">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                        Potential Issues & Recommendations
                    </h2>
                </div>
                <div class="card-body">
                    <div class="top-list">
                        ${analytics.recommendations.map((rec, i) => `
                        <div class="top-item" style="border-left: 3px solid ${rec.severity === 'warning' ? 'var(--warning)' : rec.severity === 'info' ? 'var(--primary)' : 'var(--success)'};">
                            <div class="top-item-content">
                                <div class="top-item-name">${escapeHtml(rec.title)}</div>
                                <div class="top-item-meta" style="margin-top: 0.25rem;">${escapeHtml(rec.description)}</div>
                            </div>
                            <span class="badge badge-${rec.severity === 'warning' ? 'orange' : rec.severity === 'info' ? 'blue' : 'green'}">${rec.severity}</span>
                        </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>

        <!-- Roles Tab -->
        <div id="tab-roles" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        All Roles
                    </h2>
                </div>
                <div class="card-body">
                    <div class="table-controls">
                        <div class="search-box">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                            <input type="text" id="roles-search" placeholder="Search roles..." onkeyup="filterTable('roles')">
                        </div>
                        <div class="table-info">Showing <span id="roles-count">${data.roles.length}</span> of ${data.roles.length} roles</div>
                    </div>
                    <div class="table-scroll">
                        <table class="data-table" id="roles-table">
                            <thead>
                                <tr>
                                    <th onclick="sortTable('roles', 0)">Role Name <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th onclick="sortTable('roles', 1)">Category <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th onclick="sortTable('roles', 2)">Mentions <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th onclick="sortTable('roles', 3)">Documents <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th>Co-occurring Roles</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.roles.map(role => `
                                <tr>
                                    <td><strong>${escapeHtml(role.name)}</strong></td>
                                    <td><span class="badge badge-blue">${escapeHtml(role.category)}</span></td>
                                    <td>${role.totalMentions}</td>
                                    <td>${role.documentsAppearsIn.length}</td>
                                    <td>
                                        <div class="tag-list">
                                            ${role.coOccurringRoles.slice(0, 4).map(r => `<span class="tag">${escapeHtml(r)}</span>`).join('')}
                                            ${role.coOccurringRoles.length > 4 ? `<span class="tag badge-gray">+${role.coOccurringRoles.length - 4}</span>` : ''}
                                        </div>
                                    </td>
                                </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Documents Tab -->
        <div id="tab-documents" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                        All Documents
                    </h2>
                </div>
                <div class="card-body">
                    <div class="table-controls">
                        <div class="search-box">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                            <input type="text" id="docs-search" placeholder="Search documents..." onkeyup="filterTable('docs')">
                        </div>
                        <div class="table-info">Showing <span id="docs-count">${data.documents.length}</span> of ${data.documents.length} documents</div>
                    </div>
                    <div class="table-scroll">
                        <table class="data-table" id="docs-table">
                            <thead>
                                <tr>
                                    <th onclick="sortTable('docs', 0)">Document <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th onclick="sortTable('docs', 1)">Roles <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th onclick="sortTable('docs', 2)">Mentions <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th>Key Roles</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.documents.map(doc => `
                                <tr>
                                    <td><strong>${escapeHtml(doc.name)}</strong></td>
                                    <td><span class="badge badge-green">${doc.totalRoles}</span></td>
                                    <td>${doc.totalMentions}</td>
                                    <td>
                                        <div class="tag-list">
                                            ${doc.roles.slice(0, 5).map(r => `<span class="tag">${escapeHtml(r.role)} (${r.mentions})</span>`).join('')}
                                            ${doc.roles.length > 5 ? `<span class="tag badge-gray">+${doc.roles.length - 5}</span>` : ''}
                                        </div>
                                    </td>
                                </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Relationships Tab -->
        <div id="tab-relationships" class="tab-content">
            <div class="network-stats">
                <div class="network-stat">
                    <div class="network-stat-value">${data.relationships.length}</div>
                    <div class="network-stat-label">Total Connections</div>
                </div>
                <div class="network-stat">
                    <div class="network-stat-value">${analytics.networkDensity}%</div>
                    <div class="network-stat-label">Network Density</div>
                </div>
                <div class="network-stat">
                    <div class="network-stat-value">${analytics.avgWeight}</div>
                    <div class="network-stat-label">Avg Connection Strength</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
                        Relationship Matrix
                    </h2>
                </div>
                <div class="card-body">
                    <div class="table-controls">
                        <div class="search-box">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                            <input type="text" id="rels-search" placeholder="Search relationships..." onkeyup="filterTable('rels')">
                        </div>
                        <div class="table-info">Showing <span id="rels-count">${data.relationships.length}</span> of ${data.relationships.length} relationships</div>
                    </div>
                    <div class="table-scroll">
                        <table class="data-table" id="rels-table">
                            <thead>
                                <tr>
                                    <th onclick="sortTable('rels', 0)">Source <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th>Type</th>
                                    <th onclick="sortTable('rels', 2)">Target <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                    <th>Type</th>
                                    <th onclick="sortTable('rels', 4)">Strength <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg></th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.relationships.map(rel => `
                                <tr>
                                    <td>${escapeHtml(rel.source)}</td>
                                    <td><span class="badge ${rel.sourceType === 'document' ? 'badge-green' : 'badge-blue'}">${rel.sourceType}</span></td>
                                    <td>${escapeHtml(rel.target)}</td>
                                    <td><span class="badge ${rel.targetType === 'document' ? 'badge-green' : 'badge-blue'}">${rel.targetType}</span></td>
                                    <td>
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <div class="progress-bar" style="width: 60px;">
                                                <div class="progress-fill" style="width: ${Math.min(rel.weight / analytics.maxWeight * 100, 100)}%; background: var(--primary);"></div>
                                            </div>
                                            <span>${rel.weight}</span>
                                        </div>
                                    </td>
                                </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer style="text-align: center; color: var(--gray-400); padding: 2rem; border-top: 1px solid var(--gray-200); margin-top: 2rem;">
        <p>Generated by <strong>AEGIS</strong> - Aerospace Engineering Governance & Inspection System</p>
        <p style="font-size: 0.8125rem; margin-top: 0.5rem;">© ${new Date().getFullYear()} Technical Writer Review Tool</p>
    </footer>

    <script>
        // Tab Navigation
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(nav => nav.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }

        // Table Filtering
        function filterTable(tableId) {
            const input = document.getElementById(tableId + '-search');
            const filter = input.value.toLowerCase();
            const table = document.getElementById(tableId + '-table');
            const rows = table.querySelectorAll('tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const visible = text.includes(filter);
                row.style.display = visible ? '' : 'none';
                if (visible) visibleCount++;
            });

            document.getElementById(tableId + '-count').textContent = visibleCount;
        }

        // Table Sorting
        let sortDirections = {};
        function sortTable(tableId, columnIndex) {
            const table = document.getElementById(tableId + '-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const key = tableId + '-' + columnIndex;

            sortDirections[key] = !sortDirections[key];
            const direction = sortDirections[key] ? 1 : -1;

            rows.sort((a, b) => {
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();

                // Try numeric sort
                const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return (aNum - bNum) * direction;
                }
                return aVal.localeCompare(bVal) * direction;
            });

            rows.forEach(row => tbody.appendChild(row));
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            // Add animation to bars
            document.querySelectorAll('.h-bar-fill').forEach((bar, i) => {
                const width = bar.style.width;
                bar.style.width = '0';
                setTimeout(() => { bar.style.width = width; }, i * 50);
            });

            // Initialize graph snapshot if present
            initGraphSnapshot();
        });

        // Graph snapshot zoom functionality
        let graphZoom = 1;
        let graphPan = { x: 0, y: 0 };
        let isDragging = false;
        let dragStart = { x: 0, y: 0 };

        function initGraphSnapshot() {
            const container = document.querySelector('.graph-snapshot');
            if (!container) return;

            const svg = container.querySelector('svg');
            if (!svg) return;

            // Make SVG responsive
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.transformOrigin = 'center center';
            svg.style.transition = 'transform 0.2s ease';

            // Add pan functionality
            container.addEventListener('mousedown', (e) => {
                isDragging = true;
                dragStart = { x: e.clientX - graphPan.x, y: e.clientY - graphPan.y };
                container.style.cursor = 'grabbing';
            });

            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                graphPan.x = e.clientX - dragStart.x;
                graphPan.y = e.clientY - dragStart.y;
                updateGraphTransform();
            });

            document.addEventListener('mouseup', () => {
                isDragging = false;
                const container = document.querySelector('.graph-snapshot');
                if (container) container.style.cursor = 'grab';
            });

            // Add wheel zoom
            container.addEventListener('wheel', (e) => {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.1 : 0.1;
                zoomGraph(delta);
            });

            container.style.cursor = 'grab';
        }

        function zoomGraph(delta) {
            graphZoom = Math.max(0.3, Math.min(3, graphZoom + delta));
            updateGraphTransform();
        }

        function resetGraphZoom() {
            graphZoom = 1;
            graphPan = { x: 0, y: 0 };
            updateGraphTransform();
        }

        function updateGraphTransform() {
            const svg = document.querySelector('.graph-snapshot svg');
            if (svg) {
                svg.style.transform = \`scale(\${graphZoom}) translate(\${graphPan.x / graphZoom}px, \${graphPan.y / graphZoom}px)\`;
            }
        }
    </script>
</body>
</html>`;
    }

    /**
     * Compute advanced analytics for the report
     */
    function computeReportAnalytics(data) {
        const analytics = {};

        // Basic calculations
        analytics.avgRolesPerDoc = data.documents.length > 0
            ? (data.roles.reduce((sum, r) => sum + r.documentsAppearsIn.length, 0) / data.documents.length).toFixed(1)
            : '0';

        // Network density (actual connections / possible connections)
        const possibleConnections = (data.summary.totalRoles * (data.summary.totalRoles - 1)) / 2 +
                                   (data.summary.totalRoles * data.summary.totalDocuments);
        analytics.networkDensity = possibleConnections > 0
            ? ((data.relationships.length / possibleConnections) * 100).toFixed(1)
            : '0';

        // Top roles by mentions
        const maxMentions = Math.max(...data.roles.map(r => r.totalMentions), 1);
        analytics.topRolesByMentions = data.roles
            .map(r => ({ name: r.name, mentions: r.totalMentions, percentage: (r.totalMentions / maxMentions) * 100 }))
            .sort((a, b) => b.mentions - a.mentions)
            .slice(0, 10);

        // Most connected roles
        analytics.mostConnectedRoles = data.roles
            .map(r => ({
                name: r.name,
                connections: r.coOccurringRoles.length + r.documentsAppearsIn.length,
                docCount: r.documentsAppearsIn.length,
                mentions: r.totalMentions
            }))
            .sort((a, b) => b.connections - a.connections)
            .slice(0, 10);

        analytics.mostConnectedRole = analytics.mostConnectedRoles[0]?.name || 'N/A';

        // Documents with most roles
        analytics.docsWithMostRoles = data.documents
            .map(d => ({ name: d.name, roles: d.totalRoles, mentions: d.totalMentions }))
            .sort((a, b) => b.roles - a.roles)
            .slice(0, 10);

        // Category breakdown
        const categoryMap = {};
        data.roles.forEach(r => {
            const cat = r.category || 'Uncategorized';
            categoryMap[cat] = (categoryMap[cat] || 0) + 1;
        });
        const totalRoles = data.roles.length || 1;
        analytics.categoryBreakdown = Object.entries(categoryMap)
            .map(([name, count]) => ({ name, count, percentage: (count / totalRoles) * 100 }))
            .sort((a, b) => b.count - a.count);

        // Relationship stats
        analytics.maxWeight = Math.max(...data.relationships.map(r => r.weight), 1);
        analytics.avgWeight = data.relationships.length > 0
            ? (data.relationships.reduce((sum, r) => sum + r.weight, 0) / data.relationships.length).toFixed(1)
            : '0';

        // Generate insights
        analytics.insights = [];

        // Hub roles insight
        const hubRoles = analytics.mostConnectedRoles.filter(r => r.connections > data.summary.avgConnectionsPerRole * 2);
        if (hubRoles.length > 0) {
            analytics.insights.push({
                type: 'info',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--purple)"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>',
                title: 'Hub Roles Identified',
                text: `${hubRoles.length} role(s) act as central hubs with significantly more connections than average. These roles are critical coordination points.`,
                metric: hubRoles.slice(0, 3).map(r => r.name).join(', ')
            });
        }

        // Isolated roles insight
        const isolatedRoles = data.roles.filter(r => r.coOccurringRoles.length === 0);
        if (isolatedRoles.length > 0) {
            analytics.insights.push({
                type: 'warning',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--warning)"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
                title: 'Isolated Roles Found',
                text: `${isolatedRoles.length} role(s) have no co-occurring relationships with other roles. This may indicate documentation gaps or siloed responsibilities.`,
                metric: isolatedRoles.slice(0, 3).map(r => r.name).join(', ')
            });
        }

        // Document coverage insight
        const avgDocsPerRole = data.roles.reduce((sum, r) => sum + r.documentsAppearsIn.length, 0) / (data.roles.length || 1);
        analytics.insights.push({
            type: 'success',
            icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--success)"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
            title: 'Document Coverage',
            text: `Roles appear in an average of ${avgDocsPerRole.toFixed(1)} documents. ${avgDocsPerRole >= 2 ? 'Good cross-referencing detected.' : 'Consider improving cross-document references.'}`,
            metric: `${avgDocsPerRole.toFixed(1)} docs/role avg`
        });

        // Category distribution insight
        if (analytics.categoryBreakdown.length > 0) {
            const topCategory = analytics.categoryBreakdown[0];
            analytics.insights.push({
                type: 'info',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--primary)"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>',
                title: 'Category Distribution',
                text: `"${topCategory.name}" is the dominant category with ${topCategory.percentage.toFixed(0)}% of all roles. ${analytics.categoryBreakdown.length} total categories identified.`,
                metric: `${analytics.categoryBreakdown.length} categories`
            });
        }

        // Generate recommendations
        analytics.recommendations = [];

        if (isolatedRoles.length > 0) {
            analytics.recommendations.push({
                severity: 'warning',
                title: 'Review Isolated Roles',
                description: `${isolatedRoles.length} roles have no connections to other roles. Review "${isolatedRoles[0]?.name}" and others to ensure proper documentation.`
            });
        }

        const singleDocRoles = data.roles.filter(r => r.documentsAppearsIn.length === 1);
        if (singleDocRoles.length > data.roles.length * 0.3) {
            analytics.recommendations.push({
                severity: 'info',
                title: 'Improve Cross-Referencing',
                description: `${singleDocRoles.length} roles (${((singleDocRoles.length / data.roles.length) * 100).toFixed(0)}%) appear in only one document. Consider adding references in related documents.`
            });
        }

        if (analytics.networkDensity < 5) {
            analytics.recommendations.push({
                severity: 'info',
                title: 'Low Network Density',
                description: `Network density is ${analytics.networkDensity}%. This may indicate siloed documentation. Consider documenting more inter-role relationships.`
            });
        }

        if (hubRoles.length > 0) {
            analytics.recommendations.push({
                severity: 'success',
                title: 'Central Coordination Points',
                description: `${hubRoles.length} highly connected hub roles identified. Ensure these critical roles have comprehensive documentation.`
            });
        }

        if (analytics.recommendations.length === 0) {
            analytics.recommendations.push({
                severity: 'success',
                title: 'Documentation Looks Good',
                description: 'No significant issues detected. Role relationships and documentation coverage appear well-structured.'
            });
        }

        // Add focused entity-specific insights if available
        if (data.focusedEntity) {
            const fe = data.focusedEntity;

            // Clear generic insights and add focused ones
            analytics.insights = [];

            // Connection strength insight
            const strongConnections = [...fe.connectedRoles, ...fe.connectedDocuments].filter(c => c.weight > 2);
            if (strongConnections.length > 0) {
                analytics.insights.push({
                    type: 'success',
                    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--success)"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
                    title: 'Strong Connections',
                    text: `${fe.name} has ${strongConnections.length} strong connection(s) with weight > 2, indicating frequent co-occurrence or close collaboration.`,
                    metric: strongConnections.slice(0, 3).map(c => c.name).join(', ')
                });
            }

            // Role vs Document balance
            const roleRatio = fe.connectedRoles.length / (fe.connectionCount || 1) * 100;
            analytics.insights.push({
                type: 'info',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--primary)"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>',
                title: 'Connection Balance',
                text: `${roleRatio.toFixed(0)}% of connections are with other roles, ${(100 - roleRatio).toFixed(0)}% with documents. ${roleRatio > 60 ? 'This indicates a collaborative role.' : roleRatio < 40 ? 'Primarily document-focused.' : 'Well-balanced connections.'}`,
                metric: `${fe.connectedRoles.length} roles / ${fe.connectedDocuments.length} docs`
            });

            // Centrality insight
            if (fe.connectionCount > data.summary.avgConnectionsPerRole * 1.5) {
                analytics.insights.push({
                    type: 'info',
                    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--purple)"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
                    title: 'Central Hub',
                    text: `${fe.name} has ${fe.connectionCount} connections, significantly above the average of ${data.summary.avgConnectionsPerRole}. This is a key coordination point.`,
                    metric: `${((fe.connectionCount / data.summary.avgConnectionsPerRole) * 100 - 100).toFixed(0)}% above average`
                });
            } else if (fe.connectionCount < data.summary.avgConnectionsPerRole * 0.5) {
                analytics.insights.push({
                    type: 'warning',
                    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--warning)"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
                    title: 'Limited Connectivity',
                    text: `${fe.name} has fewer connections (${fe.connectionCount}) than average (${data.summary.avgConnectionsPerRole}). Consider reviewing documentation for missing relationships.`,
                    metric: `${fe.connectionCount} connections`
                });
            }

            // Top collaborator insight
            const topConnection = [...fe.connectedRoles, ...fe.connectedDocuments].sort((a, b) => b.weight - a.weight)[0];
            if (topConnection) {
                analytics.insights.push({
                    type: 'success',
                    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:18px;height:18px;color:var(--success)"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
                    title: 'Strongest Connection',
                    text: `The strongest relationship is with "${topConnection.name}" (weight: ${topConnection.weight}). This indicates frequent co-occurrence or close collaboration.`,
                    metric: topConnection.name
                });
            }

            // Update recommendations for focused entity
            analytics.recommendations = [];

            if (fe.connectedDocuments.length === 0 && fe.isRole) {
                analytics.recommendations.push({
                    severity: 'warning',
                    title: 'No Document Connections',
                    description: `${fe.name} is not directly connected to any documents. Ensure this role is properly documented.`
                });
            }

            if (fe.connectedRoles.length === 0 && fe.isRole) {
                analytics.recommendations.push({
                    severity: 'info',
                    title: 'No Role Collaborations',
                    description: `${fe.name} has no direct connections to other roles. Consider documenting collaboration relationships.`
                });
            }

            const weakConnections = [...fe.connectedRoles, ...fe.connectedDocuments].filter(c => c.weight === 1);
            if (weakConnections.length > fe.connectionCount * 0.7) {
                analytics.recommendations.push({
                    severity: 'info',
                    title: 'Mostly Weak Connections',
                    description: `${weakConnections.length} of ${fe.connectionCount} connections have minimal weight. These may need documentation review.`
                });
            }

            if (analytics.recommendations.length === 0) {
                analytics.recommendations.push({
                    severity: 'success',
                    title: 'Well-Connected Entity',
                    description: `${fe.name} has a healthy connection profile with ${fe.connectionCount} relationships across roles and documents.`
                });
            }
        }

        return analytics;
    }

    /**
     * Helper to download blob as file
     */
    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    /**
     * Copy shareable link to current filter state
     */
    function copyFilterLink() {
        if (GraphState.filterStack.length === 0) {
            showToast('No filter to share', 'info');
            return;
        }

        // Encode filter state in URL hash
        const filterData = GraphState.filterStack.map(f => `${f.type}:${encodeURIComponent(f.id)}:${encodeURIComponent(f.label)}`).join('|');
        const url = `${window.location.origin}${window.location.pathname}#roles-filter=${filterData}`;

        navigator.clipboard.writeText(url).then(() => {
            showToast('Filter link copied!', 'success');
        }).catch(() => {
            showToast('Could not copy link', 'error');
        });
    }

    /**
     * Load filter from URL hash
     */
    function loadFilterFromURL() {
        const hash = window.location.hash;
        if (!hash.includes('roles-filter=')) return;

        try {
            const filterData = hash.split('roles-filter=')[1];
            const filters = filterData.split('|').map(f => {
                const [type, id, label] = f.split(':');
                return { type, id: decodeURIComponent(id), label: decodeURIComponent(label) };
            });

            if (filters.length > 0) {
                GraphState.filterStack = filters;
                // Will be applied after graph loads
            }
        } catch (e) {
            console.warn('Could not parse filter from URL', e);
        }
    }

    /**
     * Create mini-map overview
     */
    function createMiniMap() {
        const container = document.getElementById('roles-graph-container');
        if (!container || document.getElementById('graph-minimap')) return;

        const minimap = document.createElement('div');
        minimap.id = 'graph-minimap';
        minimap.className = 'graph-minimap';
        minimap.innerHTML = `
            <div id="minimap-context-panel" class="minimap-context-panel" style="display:none;"></div>
            <canvas id="minimap-canvas" width="150" height="100"></canvas>
            <div class="minimap-viewport"></div>
            <div class="minimap-label">Click to reset view</div>
        `;
        container.appendChild(minimap);

        // Click on mini-map always clears ALL filters and refreshes the graph completely
        minimap.addEventListener('click', function() {
            // Clear all filter state
            GraphState.filterStack = [];
            GraphState.filterForwardStack = [];
            GraphState.filteredNodeIds = null;

            // Update filter bar (will hide it since no filters)
            updateFilterBreadcrumbs();

            // Force a complete re-render of the graph
            renderRolesGraph(true);

            TWR.Modals?.toast?.('info', 'Returned to full graph view');
        });

        // Add cursor style to indicate clickable
        minimap.style.cursor = 'pointer';

        updateMiniMap();

        // Create saved filters button
        createSavedFiltersButton(container);
    }

    /**
     * Create saved filters button and panel
     */
    function createSavedFiltersButton(container) {
        if (!container || document.getElementById('saved-filters-btn')) return;

        // Create the button
        const btn = document.createElement('button');
        btn.id = 'saved-filters-btn';
        btn.className = 'saved-filters-btn';
        btn.innerHTML = `<i data-lucide="bookmark"></i><span>Saved</span>`;
        btn.title = 'View saved filters';
        btn.onclick = toggleSavedFiltersPanel;
        container.appendChild(btn);

        // Create the panel
        const panel = document.createElement('div');
        panel.id = 'saved-filters-panel';
        panel.className = 'saved-filters-panel';
        panel.innerHTML = `
            <div class="saved-filters-header">
                <h3><i data-lucide="bookmark"></i> Saved Filters</h3>
                <button class="saved-filters-close" onclick="TWR.Roles.toggleSavedFiltersPanel()">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="saved-filters-list" id="saved-filters-list">
                <!-- Populated dynamically -->
            </div>
            <div class="saved-filters-empty" id="saved-filters-empty">
                <i data-lucide="bookmark-x"></i>
                <p>No saved filters yet</p>
                <span>Use the bookmark button in the filter bar to save your current view</span>
            </div>
        `;
        container.appendChild(panel);

        // Initialize icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [btn, panel] }); } catch(e) {}
        }

        // Load and display saved filters
        loadSavedFilters();
        updateSavedFiltersPanel();
    }

    /**
     * Toggle saved filters panel visibility
     */
    function toggleSavedFiltersPanel() {
        const panel = document.getElementById('saved-filters-panel');
        const btn = document.getElementById('saved-filters-btn');
        if (!panel) return;

        const isVisible = panel.classList.contains('visible');
        panel.classList.toggle('visible', !isVisible);
        btn?.classList.toggle('active', !isVisible);

        if (!isVisible) {
            updateSavedFiltersPanel();
        }
    }

    /**
     * Update saved filters panel content
     */
    function updateSavedFiltersPanel() {
        const list = document.getElementById('saved-filters-list');
        const empty = document.getElementById('saved-filters-empty');
        if (!list || !empty) return;

        const escapeHtml = getEscapeHtml();

        if (GraphState.savedFilters.length === 0) {
            list.style.display = 'none';
            empty.style.display = 'flex';
            return;
        }

        list.style.display = 'block';
        empty.style.display = 'none';

        list.innerHTML = GraphState.savedFilters.map((filter, index) => {
            const path = filter.stack.map(f => {
                const icon = f.type === 'document' ? '📄' : '👤';
                return `${icon} ${f.label}`;
            }).join(' → ');

            const date = new Date(filter.timestamp).toLocaleDateString();

            return `
                <div class="saved-filter-card" onclick="TWR.Roles.applySavedFilter(${index})">
                    <div class="saved-filter-info">
                        <div class="saved-filter-name">${escapeHtml(filter.name)}</div>
                        <div class="saved-filter-path">${escapeHtml(path)}</div>
                        <div class="saved-filter-date">Saved ${date}</div>
                    </div>
                    <button class="saved-filter-delete" onclick="event.stopPropagation(); TWR.Roles.deleteSavedFilter(${index})" title="Delete">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            `;
        }).join('');

        // Initialize icons
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [list] }); } catch(e) {}
        }
    }

    /**
     * Delete a saved filter
     */
    function deleteSavedFilter(index) {
        if (index < 0 || index >= GraphState.savedFilters.length) return;

        const filter = GraphState.savedFilters[index];
        if (!confirm(`Delete saved filter "${filter.name}"?`)) return;

        GraphState.savedFilters.splice(index, 1);

        // Update localStorage
        try {
            localStorage.setItem('aegis_saved_filters', JSON.stringify(GraphState.savedFilters));
        } catch (e) { console.warn('Could not save to localStorage'); }

        updateSavedFiltersPanel();
        showToast('Filter deleted', 'info');
    }

    /**
     * Reset zoom to fit all nodes in view
     */
    function resetZoomToFit() {
        if (!GraphState.zoom || !GraphState.data || typeof d3 === 'undefined') return;

        const svg = d3.select('#roles-graph-container svg');
        const container = document.getElementById('roles-graph-container');
        if (!svg.node() || !container) return;

        const width = container.clientWidth;
        const height = container.clientHeight;

        // Find bounds of all nodes
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        GraphState.data.nodes.forEach(node => {
            minX = Math.min(minX, node.x || 0);
            maxX = Math.max(maxX, node.x || 0);
            minY = Math.min(minY, node.y || 0);
            maxY = Math.max(maxY, node.y || 0);
        });

        const padding = 60;
        const graphWidth = maxX - minX + padding * 2;
        const graphHeight = maxY - minY + padding * 2;
        const centerX = (minX + maxX) / 2;
        const centerY = (minY + maxY) / 2;

        const scale = Math.min(
            0.9,
            Math.min(width / graphWidth, height / graphHeight) * 0.85
        );

        const transform = d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(scale)
            .translate(-centerX, -centerY);

        svg.transition()
            .duration(750)
            .ease(d3.easeCubicInOut)
            .call(GraphState.zoom.transform, transform);
    }

    /**
     * v5.1.2: Truncate a label string for minimap display
     */
    function truncateLabel(text, maxLen) {
        if (!text) return '';
        text = String(text).trim();
        if (text.length <= maxLen) return text;
        return text.substring(0, maxLen - 1) + '…';
    }

    /**
     * Update mini-map display
     */
    function updateMiniMap() {
        const canvas = document.getElementById('minimap-canvas');
        if (!canvas || !GraphState.data) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        // v5.1.2: Enhanced HEB/semantic-zoom minimap with selection state + role names
        if (GraphState.currentLayout === 'heb' || GraphState.currentLayout === 'semantic-zoom') {
            const hasSelection = !!GraphState.szSelectedId;
            const selectedId = GraphState.szSelectedId;
            const connectedIds = GraphState.szConnectedIds;

            const w = canvas.width;
            const h = canvas.height;
            ctx.clearRect(0, 0, w, h);

            // Circle area — full width (role names shown in HTML panel above)
            const cx = w / 2;
            const cy = h / 2;
            const radius = Math.min(cx, cy) - 10;

            // Draw document group arcs
            if (GraphState.documentGroups && GraphState.documentGroups.length > 0) {
                GraphState.documentGroups.forEach((g, gi) => {
                    const startAngle = (g.startAngle * Math.PI / 180) - Math.PI / 2;
                    const endAngle = (g.endAngle * Math.PI / 180) - Math.PI / 2;
                    const isActive = !hasSelection || (GraphState.szActiveGroups && GraphState.szActiveGroups.has(gi));
                    ctx.beginPath();
                    ctx.arc(cx, cy, radius, startAngle, endAngle);
                    ctx.strokeStyle = g.color;
                    ctx.lineWidth = isActive ? 4 : 2;
                    ctx.globalAlpha = isActive ? 0.7 : 0.12;
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                });
            }

            // Draw node dots around circle
            const nodes = GraphState.data.nodes.filter(n => n.type !== 'document');
            const angleStep = (2 * Math.PI) / Math.max(nodes.length, 1);
            nodes.forEach((node, i) => {
                const angle = angleStep * i - Math.PI / 2;
                const nx = cx + Math.cos(angle) * (radius - 2);
                const ny = cy + Math.sin(angle) * (radius - 2);
                const isFiltered = !GraphState.filteredNodeIds || GraphState.filteredNodeIds.has(node.id);

                if (hasSelection) {
                    // Selection-aware rendering
                    if (node.id === selectedId) {
                        // Selected node — gold, larger
                        ctx.beginPath();
                        ctx.arc(nx, ny, 4, 0, Math.PI * 2);
                        ctx.fillStyle = '#ffd700';
                        ctx.fill();
                        ctx.strokeStyle = '#fff';
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    } else if (connectedIds && connectedIds.has(node.id)) {
                        // Connected node — bright blue, medium
                        ctx.beginPath();
                        ctx.arc(nx, ny, 2.5, 0, Math.PI * 2);
                        ctx.fillStyle = '#4A90D9';
                        ctx.fill();
                    } else {
                        // Dimmed node — faint
                        ctx.beginPath();
                        ctx.arc(nx, ny, 1, 0, Math.PI * 2);
                        ctx.fillStyle = 'rgba(168,197,229,0.25)';
                        ctx.fill();
                    }
                } else {
                    // Default (no selection) rendering
                    ctx.beginPath();
                    ctx.arc(nx, ny, isFiltered ? 2 : 1, 0, Math.PI * 2);
                    ctx.fillStyle = isFiltered ? '#4A90D9' : '#a8c5e5';
                    ctx.fill();
                }
            });

            // Draw connection lines from selected to connected in minimap
            if (hasSelection && connectedIds) {
                const selectedIdx = nodes.findIndex(n => n.id === selectedId);
                if (selectedIdx >= 0) {
                    const selAngle = angleStep * selectedIdx - Math.PI / 2;
                    const selX = cx + Math.cos(selAngle) * (radius - 2);
                    const selY = cy + Math.sin(selAngle) * (radius - 2);

                    nodes.forEach((node, i) => {
                        if (node.id !== selectedId && connectedIds.has(node.id)) {
                            const nAngle = angleStep * i - Math.PI / 2;
                            const nX = cx + Math.cos(nAngle) * (radius - 2);
                            const nY = cy + Math.sin(nAngle) * (radius - 2);

                            // Curved line through center
                            ctx.beginPath();
                            ctx.moveTo(selX, selY);
                            ctx.quadraticCurveTo(cx, cy, nX, nY);
                            ctx.strokeStyle = 'rgba(74,144,217,0.35)';
                            ctx.lineWidth = 1;
                            ctx.stroke();
                        }
                    });
                }
            }

            // v5.1.2: HTML context panel with role names
            const contextPanel = document.getElementById('minimap-context-panel');
            if (contextPanel) {
                if (hasSelection && connectedIds) {
                    const escapeHtml = getEscapeHtml();
                    const selectedNode = nodes.find(n => n.id === selectedId);
                    const connectedNodes = nodes.filter(n => n.id !== selectedId && connectedIds.has(n.id));
                    const selLabel = selectedNode ? escapeHtml(selectedNode.label) : '?';
                    const maxShow = 15;

                    let html = `<div class="mcp-selected"><span class="mcp-dot mcp-gold">●</span> ${selLabel}</div>`;
                    if (connectedNodes.length > 0) {
                        html += `<div class="mcp-divider"></div>`;
                        html += `<div class="mcp-connected-header">${connectedNodes.length} connected role${connectedNodes.length !== 1 ? 's' : ''}</div>`;
                        connectedNodes.slice(0, maxShow).forEach(n => {
                            html += `<div class="mcp-connected"><span class="mcp-dot mcp-blue">◦</span> ${escapeHtml(n.label)}</div>`;
                        });
                        if (connectedNodes.length > maxShow) {
                            html += `<div class="mcp-more">+${connectedNodes.length - maxShow} more</div>`;
                        }
                    }
                    contextPanel.innerHTML = html;
                    contextPanel.style.display = 'block';
                } else {
                    contextPanel.style.display = 'none';
                    contextPanel.innerHTML = '';
                }
            }

            // Update viewport indicator
            const viewport = document.querySelector('.minimap-viewport');
            if (viewport) viewport.style.display = (GraphState.filteredNodeIds || hasSelection) ? 'block' : 'none';
            return;
        }

        // Force/bipartite minimap (original)
        // Find bounds
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        GraphState.data.nodes.forEach(node => {
            minX = Math.min(minX, node.x || 0);
            maxX = Math.max(maxX, node.x || 0);
            minY = Math.min(minY, node.y || 0);
            maxY = Math.max(maxY, node.y || 0);
        });

        const padding = 20;
        const scaleX = (width - padding * 2) / (maxX - minX || 1);
        const scaleY = (height - padding * 2) / (maxY - minY || 1);
        const scale = Math.min(scaleX, scaleY);

        // Draw links
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 0.5;
        GraphState.data.links.forEach(link => {
            const source = typeof link.source === 'object' ? link.source : GraphState.data.nodes.find(n => n.id === link.source);
            const target = typeof link.target === 'object' ? link.target : GraphState.data.nodes.find(n => n.id === link.target);
            if (source && target) {
                ctx.beginPath();
                ctx.moveTo(padding + (source.x - minX) * scale, padding + (source.y - minY) * scale);
                ctx.lineTo(padding + (target.x - minX) * scale, padding + (target.y - minY) * scale);
                ctx.stroke();
            }
        });

        // Draw nodes
        GraphState.data.nodes.forEach(node => {
            const x = padding + ((node.x || 0) - minX) * scale;
            const y = padding + ((node.y || 0) - minY) * scale;
            const isFiltered = !GraphState.filteredNodeIds || GraphState.filteredNodeIds.has(node.id);

            ctx.beginPath();
            ctx.arc(x, y, isFiltered ? 3 : 1.5, 0, Math.PI * 2);
            ctx.fillStyle = node.type === 'document'
                ? (isFiltered ? '#27AE60' : '#a8d5ba')
                : (isFiltered ? '#4A90D9' : '#a8c5e5');
            ctx.fill();
        });

        // Update viewport indicator
        const viewport = document.querySelector('.minimap-viewport');
        if (viewport && GraphState.zoom) {
            // This would show the current view position - simplified for now
            viewport.style.display = GraphState.filteredNodeIds ? 'block' : 'none';
        }
    }

    /**
     * Search within current filtered nodes
     */
    function searchInFilter(query) {
        if (!GraphState.svg || !GraphState.data) return;

        query = (query || '').toLowerCase().trim();

        if (!query) {
            // Clear search highlighting
            GraphState.svg.selectAll('.graph-node').classed('search-match', false);
            return [];
        }

        const matches = [];
        const filteredIds = GraphState.filteredNodeIds;

        GraphState.data.nodes.forEach(node => {
            // Only search within filtered nodes
            if (filteredIds && !filteredIds.has(node.id)) return;

            const label = (node.label || '').toLowerCase();
            if (label.includes(query)) {
                matches.push(node);
            }
        });

        // Highlight matches
        GraphState.svg.selectAll('.graph-node')
            .classed('search-match', d => matches.some(m => m.id === d.id));

        return matches;
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'info') {
        if (typeof TWR.Modals?.toast === 'function') {
            TWR.Modals.toast(message, type);
        } else {
            console.log(`[Toast] ${type}: ${message}`);
        }
    }

    /**
     * Initialize drill-down click handlers for the details panel
     */
    let drilldownHandlersInitialized = false;

    function initDrillDownHandlers() {
        if (drilldownHandlersInitialized) return;

        const panelBody = document.getElementById('info-panel-body');
        if (!panelBody) {
            console.log('[TWR Graph] Drill-down: Panel body not found, will retry on graph render');
            return;
        }

        // v4.0.2: Event delegation removed - using inline onclick handlers instead
        // The inline onclick on .drilldown-target elements calls TWR.Roles.applyDrillDownFilter directly
        console.log('[TWR Graph] Drill-down handlers ready (using inline onclick)');

        drilldownHandlersInitialized = true;
        console.log('[TWR Graph] Drill-down handlers initialized');
    }

    function highlightSearchMatches(searchText) {
        if (!GraphState.svg || !GraphState.data) { console.warn('[TWR Graph] Cannot highlight - svg or data not ready'); return; }

        const query = searchText.toLowerCase().trim();

        if (!query) {
            // Clear search highlights for all layout types
            GraphState.svg.selectAll('.graph-node').classed('highlighted', false).classed('dimmed', false);
            GraphState.svg.selectAll('.graph-link').classed('highlighted', false).classed('dimmed', false);
            GraphState.svg.selectAll('.heb-node').classed('search-match', false).classed('dimmed', false);
            GraphState.svg.selectAll('.heb-edge').classed('search-match', false).classed('dimmed', false);
            GraphState.svg.selectAll('.heb-node-label').classed('dimmed', false);
            GraphState.highlightedNodes.clear();
            const countEl = document.getElementById('graph-search-count');
            if (countEl) countEl.textContent = '';
            return;
        }

        GraphState.highlightedNodes.clear();
        const matchingIds = new Set();

        GraphState.data.nodes.forEach(node => {
            const label = (node.label || '').toLowerCase();
            const nodeType = (node.type || '').toLowerCase();
            if (label.includes(query) || nodeType.includes(query)) {
                matchingIds.add(node.id);
                GraphState.highlightedNodes.add(node.id);
            }
        });

        const connectedIds = new Set();
        if (matchingIds.size > 0) {
            GraphState.data.links.forEach(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                if (matchingIds.has(sourceId)) connectedIds.add(targetId);
                if (matchingIds.has(targetId)) connectedIds.add(sourceId);
            });
        }

        // v4.5.1: HEB/Semantic Zoom search highlighting
        if (GraphState.currentLayout === 'heb' || GraphState.currentLayout === 'semantic-zoom') {
            GraphState.svg.selectAll('.heb-node')
                .classed('search-match', d => matchingIds.has(d.data?.nodeId || d.id))
                .classed('dimmed', d => matchingIds.size > 0 && !matchingIds.has(d.data?.nodeId || d.id) && !connectedIds.has(d.data?.nodeId || d.id));
            GraphState.svg.selectAll('.heb-edge')
                .classed('search-match', d => {
                    const srcId = typeof d.source === 'object' ? d.source.id : d.source;
                    const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
                    return matchingIds.has(srcId) || matchingIds.has(tgtId);
                })
                .classed('dimmed', d => {
                    const srcId = typeof d.source === 'object' ? d.source.id : d.source;
                    const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
                    return matchingIds.size > 0 && !matchingIds.has(srcId) && !matchingIds.has(tgtId);
                });
            GraphState.svg.selectAll('.heb-node-label')
                .classed('dimmed', function() {
                    const nodeEl = d3.select(this.parentNode);
                    const d = nodeEl.datum();
                    const nodeId = d?.data?.nodeId || d?.id;
                    return matchingIds.size > 0 && !matchingIds.has(nodeId) && !connectedIds.has(nodeId);
                });
        } else {
            // Force/bipartite search
            GraphState.svg.selectAll('.graph-node')
                .classed('highlighted', d => matchingIds.has(d.id))
                .classed('dimmed', d => matchingIds.size > 0 && !matchingIds.has(d.id) && !connectedIds.has(d.id));

            GraphState.svg.selectAll('.graph-link')
                .classed('highlighted', d => {
                    const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                    const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                    return matchingIds.has(sourceId) || matchingIds.has(targetId);
                })
                .classed('dimmed', d => {
                    const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                    const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                    return matchingIds.size > 0 && !matchingIds.has(sourceId) && !matchingIds.has(targetId);
                });
        }

        const countEl = document.getElementById('graph-search-count');
        if (countEl) countEl.textContent = matchingIds.size > 0 ? `${matchingIds.size} found` : 'No matches';
        console.log(`[TWR Graph] Search "${query}": ${matchingIds.size} matches, ${connectedIds.size} connected`);
    }

    async function renderGraphFallbackTable() {
        const escapeHtml = getEscapeHtml();
        const api = getApi();
        const tbody = document.getElementById('graph-fallback-body');
        if (!tbody) return;
        
        try {
            const response = await api('/roles/graph?max_nodes=200&min_weight=1');
            if (!response.success || !response.data) { tbody.innerHTML = '<tr><td colspan="4">Failed to load data</td></tr>'; return; }
            
            const { nodes, links } = response.data;
            GraphState.fallbackData = { nodes, links };
            
            const nodeMap = {};
            nodes.forEach(n => nodeMap[n.id] = n);
            
            GraphState.fallbackRows = links.map(link => {
                const source = nodeMap[link.source] || { label: link.source };
                const target = nodeMap[link.target] || { label: link.target };
                const role = source.type === 'role' ? source : target;
                const doc = source.type === 'document' ? source : target;
                return { role: role.label || 'Unknown', doc: doc.label || 'Unknown', weight: link.weight, terms: (link.top_terms || []).join(', ') || '-' };
            });
            
            renderFallbackRows();
        } catch (error) {
            console.error('[TWR Roles] Fallback table error:', error);
            tbody.innerHTML = '<tr><td colspan="4">Error loading data</td></tr>';
        }
    }

    function renderFallbackRows() {
        const escapeHtml = getEscapeHtml();
        const tbody = document.getElementById('graph-fallback-body');
        if (!tbody || !GraphState.fallbackRows) return;
        
        let rows = [...GraphState.fallbackRows];
        
        const roleSearch = (document.getElementById('fallback-role-search')?.value || '').toLowerCase().trim();
        if (roleSearch) rows = rows.filter(r => r.role.toLowerCase().includes(roleSearch));
        
        const docSearch = (document.getElementById('fallback-doc-search')?.value || '').toLowerCase().trim();
        if (docSearch) rows = rows.filter(r => r.doc.toLowerCase().includes(docSearch));
        
        const matchSelection = document.getElementById('fallback-match-selection')?.checked;
        if (matchSelection && GraphState.selectedNode) {
            const selectedLabel = GraphState.selectedNode.label?.toLowerCase();
            if (selectedLabel) rows = rows.filter(r => r.role.toLowerCase() === selectedLabel || r.doc.toLowerCase() === selectedLabel);
        }
        
        const sortValue = document.getElementById('fallback-sort')?.value || 'weight-desc';
        const [sortKey, sortDir] = sortValue.split('-');
        rows.sort((a, b) => {
            let cmp = 0;
            if (sortKey === 'weight') cmp = a.weight - b.weight;
            else if (sortKey === 'role') cmp = a.role.localeCompare(b.role);
            else if (sortKey === 'doc') cmp = a.doc.localeCompare(b.doc);
            return sortDir === 'asc' ? cmp : -cmp;
        });
        
        tbody.innerHTML = rows.slice(0, 100).map(row => `<tr><td>${escapeHtml(row.role)}</td><td>${escapeHtml(row.doc)}</td><td>${row.weight}</td><td>${escapeHtml(row.terms)}</td></tr>`).join('');
        
        if (rows.length > 100) tbody.innerHTML += `<tr><td colspan="4" style="text-align:center;font-style:italic;">Showing top 100 of ${rows.length} connections</td></tr>`;
        if (rows.length === 0) tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No matching connections</td></tr>';
    }

    function filterFallbackTable() { renderFallbackRows(); }
    function sortFallbackTable() { renderFallbackRows(); }

    // ============================================================
    // UTILITY FUNCTIONS
    // ============================================================
    
    function getCategoryForRole(roleName) {
        const name = (roleName || '').toLowerCase();
        if (/manager|director|lead|chief|head|supervisor|executive|officer/.test(name)) return 'Management';
        if (/engineer|developer|architect|designer|analyst|technical/.test(name)) return 'Engineering';
        if (/quality|qa|inspector|auditor|test|verification|validation/.test(name)) return 'Quality';
        if (/supplier|vendor|contractor|subcontractor|provider/.test(name)) return 'Supplier';
        if (/customer|client|user|operator|government|buyer/.test(name)) return 'Customer';
        if (/production|manufacturing|assembly|fabrication|operations/.test(name)) return 'Production';
        return 'General';
    }

    function getCategoryColorForRole(category) {
        const colors = { 'Management': '#E74C3C', 'Engineering': '#3498DB', 'Quality': '#9B59B6', 'Supplier': '#F39C12', 'Customer': '#27AE60', 'Production': '#1ABC9C', 'General': '#7F8C8D' };
        return colors[category] || colors['General'];
    }

    /**
     * v4.5.1: Apply global role search across all tabs in Roles & Responsibilities Studio
     * Highlights matching roles in the current view and scrolls to first match
     */
    function applyGlobalRoleSearch(searchTerm) {
        if (!searchTerm || searchTerm.trim() === '') {
            clearGlobalRoleSearch();
            return;
        }

        const term = searchTerm.toLowerCase().trim();
        const toast = getToast();
        let matchCount = 0;

        // Find all role elements across the current tab
        const roleElements = document.querySelectorAll(`
            #modal-roles .role-card,
            #modal-roles .role-row,
            #modal-roles .role-item,
            #modal-roles .adj-entity-row,
            #modal-roles .raci-role-row,
            #modal-roles [data-role-name],
            #modal-roles .graph-node
        `);

        let firstMatch = null;

        roleElements.forEach(el => {
            const roleName = (
                el.getAttribute('data-role-name') ||
                el.querySelector('.role-name, .role-title, .adj-entity-name')?.textContent ||
                el.textContent
            ).toLowerCase();

            if (roleName.includes(term)) {
                el.classList.add('search-highlight');
                el.style.boxShadow = '0 0 0 2px var(--accent), 0 0 8px var(--accent)';
                matchCount++;
                if (!firstMatch) firstMatch = el;
            } else {
                el.classList.remove('search-highlight');
                el.style.boxShadow = '';
            }
        });

        // Also highlight in the graph if visible
        if (GraphState.svg) {
            highlightSearchMatches(searchTerm);
        }

        // Scroll to first match
        if (firstMatch) {
            firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        // Show feedback
        if (matchCount > 0) {
            toast('info', `Found ${matchCount} matching role${matchCount > 1 ? 's' : ''}`);
        } else {
            toast('warning', `No roles found matching "${searchTerm}"`);
        }
    }

    /**
     * v4.5.1: Clear global role search highlights
     */
    function clearGlobalRoleSearch() {
        document.querySelectorAll('#modal-roles .search-highlight').forEach(el => {
            el.classList.remove('search-highlight');
            el.style.boxShadow = '';
        });

        // Clear graph highlights too
        if (GraphState.svg) {
            GraphState.highlightedNodes.clear();
            updateNodeHighlights();
        }
    }

    function showRoleDetails(node) {
        const escapeHtml = getEscapeHtml();
        const truncate = getTruncate();
        const State = getState();
        const panel = document.getElementById('role-details');
        if (!panel) return;

        const roleData = State.roles[node.id] || State.roles[node.label] || {};
        const responsibilities = roleData.responsibilities || [];
        const actionTypes = roleData.action_types || {};

        panel.innerHTML = `<h4>${escapeHtml(node.label || node.id)}</h4>
            <div class="role-detail-section"><strong>Occurrences:</strong> ${node.count || 1}</div>
            ${responsibilities.length > 0 ? `<div class="role-detail-section"><strong>Responsibilities:</strong><ul>${responsibilities.slice(0, 5).map(r => `<li>${escapeHtml(truncate(String(r), 80))}</li>`).join('')}</ul></div>` : ''}
            ${Object.keys(actionTypes).length > 0 ? `<div class="role-detail-section"><strong>Action Types:</strong><div class="action-types">${Object.entries(actionTypes).slice(0, 5).map(([action, count]) => `<span class="action-badge">${action}: ${count}</span>`).join('')}</div></div>` : ''}`;
    }

    async function exportRoles(format = 'csv') {
        const State = getState();
        const toast = getToast();
        const setLoading = getSetLoading();
        
        const rolesList = State.entities?.roles || [];
        let rolesData;
        
        if (rolesList.length > 0) {
            rolesData = rolesList.map(role => ({
                name: role.canonical_name || role.name,
                count: role.frequency || role.occurrence_count || 1,
                category: getCategoryForRole(role.canonical_name || role.name),
                responsibilities: (role.responsibilities || []).join('; '),
                confidence: (role.kind_confidence || 0).toFixed(2)
            }));
        } else if (State.roles && Object.keys(State.roles).length > 0) {
            const roles = Object.entries(State.roles).filter(([name, data]) => {
                if (typeof data === 'object') {
                    if (data.entity_kind === 'deliverable' || data.entity_kind === 'unknown' || !data.entity_kind) return false;
                }
                return true;
            });
            rolesData = roles.map(([name, data]) => {
                const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
                const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
                const responsibilities = typeof data === 'object' ? (data.responsibilities || []).join('; ') : '';
                return { name: displayName, count: count, category: getCategoryForRole(displayName), responsibilities: responsibilities, confidence: typeof data === 'object' ? (data.kind_confidence || 0).toFixed(2) : '0.00' };
            });
        } else {
            toast('warning', 'No roles to export');
            return;
        }
        
        if (rolesData.length === 0) { toast('warning', 'No roles to export (only deliverables/unknown found)'); return; }

        setLoading(true, 'Exporting roles...');

        try {
            if (format === 'csv') {
                const headers = ['Role Name', 'Occurrences', 'Category', 'Responsibilities', 'Confidence'];
                const rows = rolesData.map(r => [`"${r.name.replace(/"/g, '""')}"`, r.count, r.category, `"${r.responsibilities.replace(/"/g, '""')}"`, r.confidence]);
                const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                downloadBlob(blob, `${State.filename || 'document'}_roles_${getTimestamp()}.csv`);
                toast('success', `Exported ${rolesData.length} roles to CSV`);
            } else if (format === 'json') {
                const json = JSON.stringify(rolesData, null, 2);
                const blob = new Blob([json], { type: 'application/json' });
                downloadBlob(blob, `${State.filename || 'document'}_roles_${getTimestamp()}.json`);
                toast('success', `Exported ${rolesData.length} roles to JSON`);
            }
        } catch (e) {
            console.error('[TWR Roles] Export failed:', e);
            toast('error', 'Export failed: ' + e.message);
        }

        setLoading(false);
    }

    async function exportDeliverables(format = 'csv') {
        const State = getState();
        const toast = getToast();
        const setLoading = getSetLoading();
        const deliverablesList = State.entities?.deliverables || [];
        
        if (deliverablesList.length === 0) { toast('warning', 'No deliverables to export'); return; }

        setLoading(true, 'Exporting deliverables...');

        try {
            const data = deliverablesList.map(d => ({ name: d.canonical_name || d.name, count: d.frequency || d.occurrence_count || 1, confidence: (d.kind_confidence || 0).toFixed(2), variants: (d.variants || []).join('; ') }));

            if (format === 'csv') {
                const headers = ['Deliverable Name', 'Occurrences', 'Confidence', 'Variants'];
                const rows = data.map(d => [`"${d.name.replace(/"/g, '""')}"`, d.count, d.confidence, `"${d.variants.replace(/"/g, '""')}"`]);
                const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                downloadBlob(blob, `${State.filename || 'document'}_deliverables_${getTimestamp()}.csv`);
                toast('success', `Exported ${data.length} deliverables to CSV`);
            } else if (format === 'json') {
                const json = JSON.stringify(data, null, 2);
                const blob = new Blob([json], { type: 'application/json' });
                downloadBlob(blob, `${State.filename || 'document'}_deliverables_${getTimestamp()}.json`);
                toast('success', `Exported ${data.length} deliverables to JSON`);
            }
        } catch (e) {
            console.error('[TWR Roles] Export failed:', e);
            toast('error', 'Export failed: ' + e.message);
        }

        setLoading(false);
    }

    // ============================================================
    // v3.0.80: ROLES EXPORT FUNCTIONALITY
    // ============================================================
    
    function initExportDropdown() {
        const dropdownBtn = document.getElementById('btn-export-roles-report');
        const dropdownMenu = document.getElementById('roles-export-menu');
        
        if (!dropdownBtn || !dropdownMenu) return;
        
        // Toggle dropdown on button click
        dropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('#roles-export-dropdown')) {
                dropdownMenu.classList.remove('show');
            }
        });
        
        // Export All Roles (CSV)
        document.getElementById('btn-export-all-csv')?.addEventListener('click', function() {
            dropdownMenu.classList.remove('show');
            exportAllRolesCSV();
        });
        
        // Export Current Document (CSV)
        document.getElementById('btn-export-current-csv')?.addEventListener('click', function() {
            dropdownMenu.classList.remove('show');
            exportCurrentDocumentCSV();
        });
        
        // Export All Roles (JSON)
        document.getElementById('btn-export-all-json')?.addEventListener('click', function() {
            dropdownMenu.classList.remove('show');
            exportAllRolesJSON();
        });
        
        // Export Selected Document
        document.getElementById('btn-export-selected-doc-csv')?.addEventListener('click', function() {
            dropdownMenu.classList.remove('show');
            showDocumentExportPicker();
        });
        
        console.log('[TWR Roles] Export dropdown initialized');
    }
    
    async function exportAllRolesCSV() {
        const toast = getToast();
        const setLoading = getSetLoading();
        
        setLoading(true, 'Fetching all roles from database...');
        
        try {
            const response = await fetch('/api/roles/aggregated?include_deliverables=false');
            const result = await response.json();
            
            if (!result.success) {
                const errMsg = typeof result.error === 'object'
                    ? (result.error.message || JSON.stringify(result.error))
                    : (result.error || 'Failed to fetch roles');
                toast('error', errMsg);
                setLoading(false);
                return;
            }
            
            if (!result.data || result.data.length === 0) {
                toast('warning', 'No roles found in database. Scan some documents first and ensure they are saved to history.');
                setLoading(false);
                return;
            }
            
            const roles = result.data;

            // Build CSV with comprehensive data including function tags
            const headers = ['Role Name', 'Normalized Name', 'Category', 'Function Tags', 'Document Count', 'Total Mentions', 'Responsibility Count', 'Documents'];
            const rows = roles.map(r => {
                // v3.1.10: Format function tags as semicolon-separated list
                const tags = (r.function_tags || []).map(t => t.code || t).join('; ');
                return [
                    `"${(r.role_name || '').replace(/"/g, '""')}"`,
                    `"${(r.normalized_name || '').replace(/"/g, '""')}"`,
                    r.category || 'unknown',
                    `"${tags}"`,
                    r.unique_document_count || r.document_count || 0,
                    r.total_mentions || 0,
                    r.responsibility_count || 0,
                    `"${(r.documents || []).join('; ').replace(/"/g, '""')}"`
                ];
            });
            
            const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            downloadBlob(blob, `TWR_All_Roles_${getTimestamp()}.csv`);
            
            toast('success', `Exported ${roles.length} roles to CSV`);
        } catch (e) {
            console.error('[TWR Roles] Export all roles failed:', e);
            toast('error', 'Export failed: ' + e.message);
        }
        
        setLoading(false);
    }
    
    async function exportAllRolesJSON() {
        const toast = getToast();
        const setLoading = getSetLoading();
        
        setLoading(true, 'Fetching all roles...');
        
        try {
            const response = await fetch('/api/roles/aggregated?include_deliverables=false');
            const result = await response.json();
            
            if (!result.success || !result.data || result.data.length === 0) {
                toast('warning', 'No roles found in database. Scan some documents first.');
                setLoading(false);
                return;
            }
            
            const exportData = {
                export_date: new Date().toISOString(),
                total_roles: result.data.length,
                roles: result.data
            };
            
            const json = JSON.stringify(exportData, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            downloadBlob(blob, `TWR_All_Roles_${getTimestamp()}.json`);
            
            toast('success', `Exported ${result.data.length} roles to JSON`);
        } catch (e) {
            console.error('[TWR Roles] Export all roles JSON failed:', e);
            toast('error', 'Export failed: ' + e.message);
        }
        
        setLoading(false);
    }
    
    function exportCurrentDocumentCSV() {
        const State = getState();
        const toast = getToast();
        
        // Use the SAME data source as renderRolesDetails (line 399)
        const rolesData = State.roles?.roles || State.roles || {};
        const roleEntries = Object.entries(rolesData);
        
        if (roleEntries.length === 0) {
            toast('warning', 'No roles found. Run a review first.');
            return;
        }
        
        // Build CSV from the role entries
        const headers = ['Role Name', 'Category', 'Frequency', 'Responsibilities', 'Action Types'];
        const rows = roleEntries.map(([name, data]) => {
            const displayName = typeof data === 'object' ? (data.canonical_name || name) : name;
            const count = typeof data === 'object' ? (data.frequency || data.count || 1) : 1;
            const responsibilities = typeof data === 'object' ? (data.responsibilities || []) : [];
            const actionTypes = typeof data === 'object' ? (data.action_types || {}) : {};
            const category = getCategoryForRole(displayName);
            
            return [
                `"${displayName.replace(/"/g, '""')}"`,
                category,
                count,
                `"${responsibilities.map(r => String(r)).join('; ').replace(/"/g, '""')}"`,
                `"${Object.keys(actionTypes).join(', ')}"`
            ];
        });
        
        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const filename = State.filename || State.original_filename || 'document';
        const safeFilename = filename.replace(/\.[^/.]+$/, '').replace(/[^a-zA-Z0-9.-]/g, '_');
        downloadBlob(blob, `${safeFilename}_roles_${getTimestamp()}.csv`);
        
        toast('success', `Exported ${roleEntries.length} roles to CSV`);
    }
    
    async function showDocumentExportPicker() {
        const toast = getToast();
        const setLoading = getSetLoading();
        
        setLoading(true, 'Loading document list...');
        
        try {
            // Fetch scan history to get document list
            const response = await fetch('/api/scan-history?limit=100');
            const result = await response.json();
            
            if (!result.success || !result.data || result.data.length === 0) {
                toast('warning', 'No scanned documents found.');
                setLoading(false);
                return;
            }
            
            // Get unique documents
            const docs = result.data;
            const uniqueDocs = [];
            const seenFilenames = new Set();
            for (const doc of docs) {
                if (!seenFilenames.has(doc.filename)) {
                    seenFilenames.add(doc.filename);
                    uniqueDocs.push(doc);
                }
            }
            
            // Create picker modal
            const modal = document.createElement('div');
            modal.className = 'modal-overlay';
            modal.id = 'doc-export-picker-modal';
            modal.innerHTML = `
                <div class="modal-container" style="max-width: 500px;">
                    <div class="modal-header">
                        <h3>Select Document to Export</h3>
                        <button class="btn btn-ghost modal-close" aria-label="Close">
                            <i data-lucide="x"></i>
                        </button>
                    </div>
                    <div class="modal-body" style="max-height: 400px; overflow-y: auto;">
                        <div class="document-picker-list">
                            ${uniqueDocs.map(doc => `
                                <div class="document-picker-item" data-doc-id="${doc.id}" data-filename="${escapeHtml(doc.filename)}">
                                    <i data-lucide="file-text"></i>
                                    <div class="doc-info">
                                        <div class="doc-name">${escapeHtml(doc.filename)}</div>
                                        <div class="doc-meta">${doc.role_count || 0} roles • Scanned ${new Date(doc.scan_time).toLocaleDateString()}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            if (typeof lucide !== 'undefined') lucide.createIcons();
            
            // Add click handlers
            modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.remove();
            });
            
            modal.querySelectorAll('.document-picker-item').forEach(item => {
                item.addEventListener('click', async () => {
                    const docId = item.dataset.docId;
                    const filename = item.dataset.filename;
                    modal.remove();
                    await exportDocumentRolesById(docId, filename);
                });
            });
            
        } catch (e) {
            console.error('[TWR Roles] Document picker failed:', e);
            toast('error', 'Failed to load documents: ' + e.message);
        }
        
        setLoading(false);
    }
    
    async function exportDocumentRolesById(docId, filename) {
        const toast = getToast();
        const setLoading = getSetLoading();
        
        setLoading(true, `Exporting roles from ${filename}...`);
        
        try {
            // Fetch roles for specific document
            const response = await fetch(`/api/scan-history/document/${docId}/roles`);
            if (!response.ok) throw new Error(`Document roles fetch failed: ${response.status}`);
            const result = await response.json();
            
            if (!result.success || !result.data || result.data.length === 0) {
                toast('warning', `No roles found in ${filename}`);
                setLoading(false);
                return;
            }
            
            const roles = result.data;
            
            const headers = ['Role Name', 'Normalized Name', 'Category', 'Mention Count', 'Responsibilities'];
            const rows = roles.map(r => [
                `"${(r.role_name || '').replace(/"/g, '""')}"`,
                `"${(r.normalized_name || '').replace(/"/g, '""')}"`,
                r.category || 'unknown',
                r.mention_count || 0,
                `"${(r.responsibilities || []).join('; ').replace(/"/g, '""')}"`
            ]);
            
            const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const safeFilename = filename.replace(/[^a-zA-Z0-9.-]/g, '_');
            downloadBlob(blob, `${safeFilename}_roles_${getTimestamp()}.csv`);
            
            toast('success', `Exported ${roles.length} roles from ${filename}`);
        } catch (e) {
            console.error('[TWR Roles] Export document roles failed:', e);
            toast('error', 'Export failed: ' + e.message);
        }
        
        setLoading(false);
    }

    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function getTimestamp() {
        return new Date().toISOString().slice(0, 10).replace(/-/g, '');
    }

    // ============================================================
    // v4.3.0: SMART SEARCH INITIALIZATION
    // ============================================================

    /**
     * Initialize SmartSearch autocomplete on all search inputs across the tool
     * Call this after the relevant content is loaded
     */
    function initSmartSearchInputs() {
        const State = getState();
        console.log('[TWR SmartSearch] initSmartSearchInputs called');

        // v4.5.1: Global roles search in top bar - suggests all roles across all tabs
        SmartSearch.init('roles-global-search', {
            itemType: 'role',
            maxResults: 12,
            getItems: () => {
                const items = [];
                const seenRoles = new Set();

                // Try State.roles first (most common source)
                if (State.roles) {
                    const rolesData = State.roles.roles || State.roles;
                    Object.entries(rolesData).forEach(([name, data]) => {
                        if (!seenRoles.has(name.toLowerCase())) {
                            seenRoles.add(name.toLowerCase());
                            items.push({
                                label: name,
                                type: 'role',
                                meta: `${data.count || 1} occurrences`,
                                badge: data.count || 1,
                                category: getCategoryForRole(name)
                            });
                        }
                    });
                }

                // Also include entities.roles if available
                if (State.entities?.roles) {
                    State.entities.roles.forEach(r => {
                        const name = r.canonical_name || r.name;
                        if (name && !seenRoles.has(name.toLowerCase())) {
                            seenRoles.add(name.toLowerCase());
                            items.push({
                                label: name,
                                type: 'role',
                                meta: `${r.frequency || r.occurrence_count || 1} occurrences`,
                                badge: r.frequency || r.occurrence_count || 1,
                                category: getCategoryForRole(name)
                            });
                        }
                    });
                }

                // Try RolesTabs cache as fallback
                if (items.length === 0 && window.TWR?.RolesTabs?.getAggregatedRoles) {
                    const aggregated = window.TWR.RolesTabs.getAggregatedRoles();
                    if (aggregated && aggregated.length > 0) {
                        aggregated.forEach(r => {
                            const name = r.role_name || r.name;
                            if (name && !seenRoles.has(name.toLowerCase())) {
                                seenRoles.add(name.toLowerCase());
                                items.push({
                                    label: name,
                                    type: 'role',
                                    meta: `${r.occurrence_count || 1} occurrences`,
                                    badge: r.occurrence_count || 1,
                                    category: getCategoryForRole(name)
                                });
                            }
                        });
                    }
                }

                // Sort by occurrence count (badge) descending
                return items.sort((a, b) => (b.badge || 0) - (a.badge || 0));
            },
            onSelect: (item, input) => {
                // When a role is selected, highlight it across the tool
                const searchTerm = item.label;
                input.value = searchTerm;

                // Trigger the global search functionality
                applyGlobalRoleSearch(searchTerm);
            }
        });

        // Graph search - suggest nodes (roles and documents)
        SmartSearch.init('graph-search', {
            itemType: 'role',
            getItems: () => {
                if (!GraphState.data?.nodes) return [];
                return GraphState.data.nodes.map(n => ({
                    id: n.id,
                    label: n.label || n.id,
                    type: n.type === 'role' ? 'role' : 'document',
                    meta: `${n.type} • ${n.count || 1} connections`,
                    badge: n.count || 1
                }));
            },
            onSelect: (item, input) => {
                highlightSearchMatches(item.label);
            }
        });

        // Adjudication search - handled by roles-tabs-fix.js (native filtering, no SmartSearch overlay)

        // Roles detail search - suggest roles
        SmartSearch.init('roles-detail-search', {
            itemType: 'role',
            getItems: () => {
                const entities = State.entities?.roles || [];
                return entities.map(r => ({
                    label: r.canonical_name || r.name,
                    type: 'role',
                    meta: getCategoryForRole(r.canonical_name || r.name),
                    badge: r.frequency || r.occurrence_count || 1
                }));
            },
            onSelect: (item, input) => {
                renderRolesDetails();
            }
        });

        // Fallback role search - suggest roles from fallback data
        SmartSearch.init('fallback-role-search', {
            itemType: 'role',
            getItems: () => {
                if (!GraphState.fallbackRows) return [];
                const uniqueRoles = [...new Set(GraphState.fallbackRows.map(r => r.role))];
                return uniqueRoles.map(role => ({
                    label: role,
                    type: 'role',
                    meta: 'Role'
                }));
            },
            onSelect: (item, input) => {
                renderFallbackRows();
            }
        });

        // Fallback document search - suggest documents from fallback data
        SmartSearch.init('fallback-doc-search', {
            itemType: 'document',
            getItems: () => {
                if (!GraphState.fallbackRows) return [];
                const uniqueDocs = [...new Set(GraphState.fallbackRows.map(r => r.doc))];
                return uniqueDocs.map(doc => ({
                    label: doc,
                    type: 'document',
                    meta: 'Document'
                }));
            },
            onSelect: (item, input) => {
                renderFallbackRows();
            }
        });

        console.log('[TWR SmartSearch] Initialized autocomplete on roles module inputs');
    }

    /**
     * Initialize SmartSearch on external inputs (from other modules)
     * Can be called from other modules to add autocomplete to their search inputs
     */
    function initExternalSmartSearch(inputId, config) {
        return SmartSearch.init(inputId, config);
    }

    // ============================================================
    // MODULE EXPORTS
    // ============================================================
    
    return {
        // State access
        GraphState: GraphState,
        AdjudicationState: AdjudicationState,

        // v4.3.0: Smart Search Autocomplete
        SmartSearch: SmartSearch,
        initSmartSearchInputs: initSmartSearchInputs,
        initExternalSmartSearch: initExternalSmartSearch,

        // v4.5.1: Global Role Search
        initGlobalSearch: initGlobalSearch,
        applyGlobalRoleSearch: applyGlobalRoleSearch,
        clearGlobalRoleSearch: clearGlobalRoleSearch,

        // Roles Summary & Modal
        renderRolesSummary: renderRolesSummary,
        showRolesModal: showRolesModal,
        initRolesTabs: initRolesTabs,
        updateRolesSidebarStats: updateRolesSidebarStats,
        
        // Roles Views
        renderRolesOverview: renderRolesOverview,
        renderRolesDetails: renderRolesDetails,
        renderRolesMatrix: renderRolesMatrix,
        renderDocumentLog: renderDocumentLog,
        viewDocumentRoles: viewDocumentRoles,
        
        // v3.0.98: Document Filter
        initDocumentFilter: initDocumentFilter,
        highlightRoleInContext: highlightRoleInContext,
        
        // Role-Document Matrix (v3.0.97)
        renderRoleDocMatrix: renderRoleDocMatrix,
        initRoleDocMatrixControls: initRoleDocMatrixControls,
        exportRoleDocMatrixCSV: exportRoleDocMatrixCSV,
        exportRoleDocMatrixExcel: exportRoleDocMatrixExcel,
        
        // RACI Matrix
        initRaciMatrixControls: initRaciMatrixControls,
        resetRaciEdits: resetRaciEdits,
        editRaciCell: editRaciCell,
        closeRaciDropdown: closeRaciDropdown,
        setRaciValue: setRaciValue,
        revertRaciRole: revertRaciRole,
        revertAllRaciEdits: revertAllRaciEdits,
        getRaciEditCount: getRaciEditCount,
        toggleMatrixCriticalFilter: toggleMatrixCriticalFilter,
        changeMatrixSort: changeMatrixSort,
        exportRaciMatrix: exportRaciMatrix,
        toggleExportMenu: toggleExportMenu,
        clearRaciCache: clearRaciCache,
        showRaciDrilldown: showRaciDrilldown,
        
        // Adjudication
        initAdjudication: initAdjudication,
        initBulkAdjudication: initBulkAdjudication,
        updateBulkActionVisibility: updateBulkActionVisibility,
        bulkAdjudicate: bulkAdjudicate,
        renderAdjudicationList: renderAdjudicationList,
        toggleAdjItemSelection: toggleAdjItemSelection,
        toggleAdjContext: toggleAdjContext,
        editRoleName: editRoleName,
        setAdjudicationStatus: setAdjudicationStatus,
        updateAdjudicationStats: updateAdjudicationStats,
        saveAdjudication: saveAdjudication,
        loadAdjudication: loadAdjudication,
        resetAdjudication: resetAdjudication,
        exportAdjudication: exportAdjudication,
        applyAdjudicationToDocument: applyAdjudicationToDocument,
        updateGraphWithAdjudication: updateGraphWithAdjudication,
        detectDeliverable: detectDeliverable,
        suggestRoleType: suggestRoleType,
        
        // Graph Visualization
        initGraphControls: initGraphControls,
        updatePinButton: updatePinButton,
        updateGraphLabelVisibility: updateGraphLabelVisibility,
        updateGraphLayoutUI: updateGraphLayoutUI,
        resetGraphView: resetGraphView,
        updateGraphStats: updateGraphStats,
        updateGraphVisibility: updateGraphVisibility,
        renderRolesGraph: renderRolesGraph,
        renderD3Graph: renderD3Graph,
        // v4.5.1: HEB + Semantic Zoom
        renderHEBGraph: renderHEBGraph,
        renderSemanticZoomGraph: renderSemanticZoomGraph,
        updateBundlingTension: updateBundlingTension,
        buildHierarchyFromGraphData: buildHierarchyFromGraphData,
        selectNode: selectNode,
        clearNodeSelection: clearNodeSelection,
        highlightSearchMatches: highlightSearchMatches,
        // v4.0.2: Drill-down filtering
        applyDrillDownFilter: applyDrillDownFilter,
        popDrillDownFilter: popDrillDownFilter,
        clearAllFilters: clearAllFilters,
        navigateToFilter: navigateToFilter,
        initDrillDownHandlers: initDrillDownHandlers,
        // v4.1.0: Enhanced filtering features
        zoomToFilteredNodes: zoomToFilteredNodes,
        pulseActiveNode: pulseActiveNode,
        animateConnections: animateConnections,
        goBackInHistory: goBackInHistory,
        goForwardInHistory: goForwardInHistory,
        saveCurrentFilter: saveCurrentFilter,
        applySavedFilter: applySavedFilter,
        deleteSavedFilter: deleteSavedFilter,
        toggleSavedFiltersPanel: toggleSavedFiltersPanel,
        updateSavedFiltersPanel: updateSavedFiltersPanel,
        addToMultiFilter: addToMultiFilter,
        exportFilteredView: exportFilteredView,
        copyFilterLink: copyFilterLink,
        downloadAsJSON: downloadAsJSON,
        downloadAsCSV: downloadAsCSV,
        downloadAsPNG: downloadAsPNG,
        downloadAsHTML: downloadAsHTML,
        createMiniMap: createMiniMap,
        updateMiniMap: updateMiniMap,
        searchInFilter: searchInFilter,
        initKeyboardNavigation: initKeyboardNavigation,
        renderGraphFallbackTable: renderGraphFallbackTable,
        renderFallbackRows: renderFallbackRows,
        filterFallbackTable: filterFallbackTable,
        sortFallbackTable: sortFallbackTable,
        
        // Utilities
        getCategoryForRole: getCategoryForRole,
        getCategoryColorForRole: getCategoryColorForRole,
        showRoleDetails: showRoleDetails,
        exportRoles: exportRoles,
        exportDeliverables: exportDeliverables,
        downloadBlob: downloadBlob,
        getTimestamp: getTimestamp
    };
})();

// ============================================================
// GLOBAL ALIASES FOR BACKWARD COMPATIBILITY
// ============================================================

// Roles Summary & Modal
window.renderRolesSummary = TWR.Roles.renderRolesSummary;
window.showRolesModal = TWR.Roles.showRolesModal;

// RACI Matrix
window.editRaciCell = TWR.Roles.editRaciCell;
window.setRaciValue = TWR.Roles.setRaciValue;
window.revertRaciRole = TWR.Roles.revertRaciRole;
window.revertAllRaciEdits = TWR.Roles.revertAllRaciEdits;
window.getRaciEditCount = TWR.Roles.getRaciEditCount;
window.toggleMatrixCriticalFilter = TWR.Roles.toggleMatrixCriticalFilter;
window.changeMatrixSort = TWR.Roles.changeMatrixSort;
window.exportRaciMatrix = TWR.Roles.exportRaciMatrix;

// Adjudication
window.toggleAdjItemSelection = TWR.Roles.toggleAdjItemSelection;
window.toggleAdjContext = TWR.Roles.toggleAdjContext;
window.bulkAdjudicate = TWR.Roles.bulkAdjudicate;

// Graph
window.renderRolesGraph = TWR.Roles.renderRolesGraph;
window.clearNodeSelection = TWR.Roles.clearNodeSelection;
window.resetGraphView = TWR.Roles.resetGraphView;
window.filterFallbackTable = TWR.Roles.filterFallbackTable;
window.sortFallbackTable = TWR.Roles.sortFallbackTable;

// v4.0.2: Drill-down filtering
window.applyDrillDownFilter = TWR.Roles.applyDrillDownFilter;
window.popDrillDownFilter = TWR.Roles.popDrillDownFilter;
window.clearAllFilters = TWR.Roles.clearAllFilters;

// Utilities
window.viewDocumentRoles = TWR.Roles.viewDocumentRoles;
window.showRoleDetails = TWR.Roles.showRoleDetails;
window.exportRoles = TWR.Roles.exportRoles;
window.exportDeliverables = TWR.Roles.exportDeliverables;

console.log('[TWR] Roles module loaded');
