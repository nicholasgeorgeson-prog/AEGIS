/**
 * AEGIS - Roles Tabs Fix (Robust Version)
 * v3.0.119 - Document filter selector fix (.roles-nav-item not .roles-nav-btn)
 *
 * CHANGELOG v3.0.117:
 * - Fixed: Document filter dropdown now properly populates with documents
 * - Fixed: onModalOpen() is now async to await initDocumentFilterDropdown()
 * - Added: Multiple data sources for document filter (scan history + aggregated roles + State)
 * - Added: Enhanced logging for debugging document filter
 *
 * CHANGELOG v3.0.73:
 * - Fixed: Pin selection button now works (was missing from v3.0.63 takeover)
 * - Fixed: Close info panel (X) button now works (was missing from v3.0.63 takeover)
 * - Added: Proper GraphState.isPinned toggle with visual feedback
 * - Added: Clear selection on panel close when not pinned
 * 
 * CHANGELOG v3.0.72:
 * - Fixed: Tab content areas now fill available vertical space
 * - Fixed: Graph, Adjudication, RACI Matrix expand to fill modal
 * - Changed: .roles-section.active uses display: flex for expansion
 * - Removed: max-height constraints that caused white space
 * 
 * CHANGELOG v3.0.71:
 * - Fixed: Navigation now displays as horizontal tabs (not vertical sidebar)
 * - Changed: .roles-sidebar uses flex-direction: row
 * - Removed: width constraints from responsive breakpoints
 * 
 * CHANGELOG v3.0.70:
 * - CRITICAL: CSS rules were missing in style.css!
 * - Added to style.css: #modal-roles .roles-section { display: none !important; }
 * - Added to style.css: #modal-roles .roles-section.active { display: block !important; }
 * - This completes the v3.0.68 fix that was incomplete
 * 
 * CHANGELOG v3.0.69:
 * - Fixed: "Top Roles by Responsibility Count" now shows actual responsibility count
 * - Fixed: Document tag shows unique document count, not total scan count
 * - Fixed: Summary cards show responsibility count, not mention count
 * - Added: responsibility_count field from backend API
 * - Added: unique_document_count field from backend API
 * - Changed: Sorting now uses responsibility_count (primary) then unique docs (secondary)
 * 
 * CHANGELOG v3.0.68:
 * - ROOT CAUSE: CSS uses `#modal-roles .roles-section { display: none !important; }`
 * - ROOT CAUSE: Visibility requires `.active` class, not inline style
 * - Fixed: Now uses classList.add('active') / classList.remove('active')
 * - Removed: All the inline style.display manipulations that were being overridden
 * 
 * CHANGELOG v3.0.67:
 * - Added: Enhanced diagnostic logging to all render functions
 * - Added: Try-catch wrappers to identify render errors
 * - Added: Container existence checks with clear error messages
 * 
 * CHANGELOG v3.0.65:
 * - Fixed: Labels dropdown now sets GraphState.labelMode before calling update
 * 
 * CHANGELOG v3.0.64:
 * - Fixed: initGraphControls now in main export block (was being overwritten)
 * 
 * CHANGELOG v3.0.63:
 * - Fixed: Graph controls now use _tabsFixInitialized flag (same as RACI, Details, Adjudication)
 * - Fixed: initGraphControls follows exact same pattern as initRaciControls
 * - Removed: Dependency on TWR.Roles.initGraphControls - we handle it ourselves
 * 
 * CHANGELOG v3.0.62:
 * - Fixed: Section visibility now uses inline display:block/none (not CSS classes)
 * - This matches the original roles.js behavior and ensures graph renders properly
 * 
 * CHANGELOG v3.0.61:
 * - Fixed: Graph controls (search, dropdowns, buttons) not working
 * - Added: initGraphControlsFallback() for when roles.js function unavailable
 * 
 * CHANGELOG v3.0.60:
 * - Enhanced console logging with [TWR RolesTabs] prefix
 * - Added explicit handler attachment verification
 * - Improved event delegation for adjudication buttons
 * - Added error boundary around click handlers
 * 
 * ISSUES FIXED:
 * 1. Tabs not switching properly
 * 2. No data loading when State.roles is empty
 * 3. Missing empty states for tabs without data
 * 4. Adjudication button clicks not responding (v3.0.59-60)
 * 5. Graph controls not working (v3.0.61-63)
 * 6. Graph section not visible when switching tabs (v3.0.62)
 * 7. Responsibility count not displayed correctly (v3.0.69)
 */

(function() {
    'use strict';

    // v4.7.0-fix: Prevent duplicate initialization on SPA navigation
    if (window.__TWR_rolesTabsFixLoaded) return;
    window.__TWR_rolesTabsFixLoaded = true;

    console.log('[TWR RolesTabs] Loading v3.0.119 (document filter selector fix)...');

    // Cache for API data
    const Cache = {
        aggregated: null,
        matrix: null,
        scanHistory: null,
        dictionary: null  // v3.0.56: fallback to dictionary when no scan data
    };

    // v3.0.118: Current document filter selection
    let currentDocumentFilter = 'all';
    
    /**
     * Escape HTML special characters
     */
    function escapeHtml(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
    
    /**
     * Show toast notification
     */
    function showToast(type, message) {
        if (typeof window.toast === 'function') {
            window.toast(type, message);
        } else if (window.TWR?.Modals?.toast) {
            window.TWR.Modals.toast(type, message);
        } else {
            console.log(`[TWR ${type}] ${message}`);
        }
    }
    
    /**
     * v4.0.3: Sync CSRF token from response headers.
     * Ensures the meta tag, window.CSRF_TOKEN, and State all stay in sync
     * with the server's session token (which may differ from the page-load token).
     */
    function syncCSRFFromResponse(response) {
        const newToken = response.headers.get('X-CSRF-Token');
        if (newToken) {
            window.CSRF_TOKEN = newToken;
            if (window.State) window.State.csrfToken = newToken;
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) meta.setAttribute('content', newToken);
        }
    }

    /** Get the current CSRF token (prefers synced token over meta tag) */
    function getCSRFToken() {
        return window.CSRF_TOKEN || window.State?.csrfToken || document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    /**
     * Fetch dictionary roles (fallback when no scan data)
     */
    async function fetchDictionary() {
        if (Cache.dictionary !== null) return Cache.dictionary;
        
        try {
            const response = await fetch('/api/roles/dictionary?include_inactive=false');
            syncCSRFFromResponse(response);
            const result = await response.json();
            
            if (result.success) {
                Cache.dictionary = result.data?.roles || [];
                console.log('[TWR RolesTabs] Loaded', Cache.dictionary.length, 'dictionary roles');
            } else {
                Cache.dictionary = [];
            }
        } catch (error) {
            console.error('[TWR RolesTabs] Dictionary fetch error:', error);
            Cache.dictionary = [];
        }
        
        return Cache.dictionary;
    }
    
    /**
     * Fetch aggregated roles from API
     */
    async function fetchAggregatedRoles() {
        if (Cache.aggregated !== null) return Cache.aggregated;
        
        try {
            const response = await fetch('/api/roles/aggregated?include_deliverables=true');
            syncCSRFFromResponse(response);
            const result = await response.json();
            
            if (result.success) {
                Cache.aggregated = result.data || [];
                console.log('[TWR RolesTabs] Loaded', Cache.aggregated.length, 'aggregated roles');
            } else {
                console.warn('[TWR RolesTabs] API returned error:', result.error);
                Cache.aggregated = [];
            }
        } catch (error) {
            console.error('[TWR RolesTabs] Fetch error:', error);
            Cache.aggregated = [];
        }
        
        return Cache.aggregated;
    }
    
    /**
     * Fetch role-document matrix from API
     */
    async function fetchMatrix() {
        if (Cache.matrix !== null) return Cache.matrix;
        
        try {
            const response = await fetch('/api/roles/matrix');
            syncCSRFFromResponse(response);
            const result = await response.json();
            
            if (result.success) {
                Cache.matrix = result.data || {};
                console.log('[TWR RolesTabs] Loaded matrix data');
            } else {
                Cache.matrix = {};
            }
        } catch (error) {
            console.error('[TWR RolesTabs] Matrix fetch error:', error);
            Cache.matrix = {};
        }
        
        return Cache.matrix;
    }
    
    /**
     * Fetch scan history from API
     */
    async function fetchScanHistory() {
        if (Cache.scanHistory !== null) return Cache.scanHistory;
        
        try {
            const response = await fetch('/api/scan-history?limit=50');
            syncCSRFFromResponse(response);
            const result = await response.json();
            
            if (result.success) {
                Cache.scanHistory = result.data || [];
                console.log('[TWR RolesTabs] Loaded', Cache.scanHistory.length, 'scan history items');
            } else {
                Cache.scanHistory = [];
            }
        } catch (error) {
            console.error('[TWR RolesTabs] Scan history fetch error:', error);
            Cache.scanHistory = [];
        }
        
        return Cache.scanHistory;
    }
    
    /**
     * Create empty state HTML
     */
    function emptyState(icon, title, message) {
        return `
            <div class="empty-state" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 20px;text-align:center;color:var(--text-muted);">
                <i data-lucide="${icon}" style="width:48px;height:48px;margin-bottom:16px;opacity:0.5;"></i>
                <h4 style="margin:0 0 8px 0;color:var(--text-secondary);">${title}</h4>
                <p style="margin:0;max-width:400px;">${message}</p>
            </div>
        `;
    }
    
    // =========================================================================
    // TAB RENDERERS
    // =========================================================================
    
    /**
     * Get category color for visualization
     */
    function getCategoryColor(category) {
        const colors = {
            'Management': '#1976d2',
            'Technical': '#388e3c',
            'Program': '#7b1fa2',
            'Engineering': '#f57c00',
            'Quality': '#c2185b',
            'Support': '#0097a7',
            'Operations': '#5d4037',
            'Custom': '#607d8b',
            'Role': '#9e9e9e',
            'Governance': '#6a1b9a',
            'Organization': '#00695c',
            'Safety': '#d32f2f',
            'Compliance': '#e65100',
            'Procurement': '#33691e',
            'Deliverable': '#0277bd'
        };
        return colors[category] || colors['Role'];
    }

    /**
     * v3.0.118: Populate document filter dropdown with scan history filenames
     * Called directly from renderOverview after fetching history
     */
    function populateDocumentFilter(history) {
        const filterSelect = document.getElementById('roles-document-filter');
        if (!filterSelect) {
            console.warn('[TWR RolesTabs] roles-document-filter element not found');
            return;
        }

        // Extract unique filenames from scan history
        const documents = new Set();
        if (history && history.length > 0) {
            history.forEach(scan => {
                if (scan.filename) {
                    documents.add(scan.filename);
                }
            });
        }

        // Also add current filename from State if available
        const State = window.State || window.TWR?.State?.State || {};
        const currentFilename = State.filename || State.currentFilename || '';
        if (currentFilename) {
            documents.add(currentFilename);
        }

        // Clear and populate options
        filterSelect.innerHTML = '<option value="all">All Documents</option>';

        const docArray = Array.from(documents).sort();
        console.log('[TWR RolesTabs] Populating document filter with:', docArray);

        docArray.forEach(doc => {
            const option = document.createElement('option');
            option.value = doc;
            option.textContent = doc.length > 40 ? doc.substring(0, 37) + '...' : doc;
            option.title = doc;
            filterSelect.appendChild(option);
        });

        console.log('[TWR RolesTabs] Document filter populated with', documents.size, 'documents');

        // v3.0.118: Add change event listener for filtering
        if (!filterSelect._filterInitialized) {
            filterSelect._filterInitialized = true;
            filterSelect.addEventListener('change', (e) => {
                currentDocumentFilter = e.target.value;
                console.log('[TWR RolesTabs] Document filter changed to:', currentDocumentFilter);
                // Re-render the current tab with the new filter
                // v3.0.119: Fixed selector - use .roles-nav-item not .roles-nav-btn
                const activeTab = document.querySelector('.roles-nav-item.active');
                if (activeTab) {
                    const tabName = activeTab.dataset.tab;
                    console.log('[TWR RolesTabs] Re-rendering tab:', tabName);
                    switchToTab(tabName);
                } else {
                    // Fallback to overview
                    console.log('[TWR RolesTabs] No active tab found, defaulting to overview');
                    switchToTab('overview');
                }
            });
        }

        // Restore previous selection if it exists in the new list
        if (currentDocumentFilter !== 'all' && docArray.includes(currentDocumentFilter)) {
            filterSelect.value = currentDocumentFilter;
        } else {
            currentDocumentFilter = 'all';
            filterSelect.value = 'all';
        }
    }

    /**
     * v3.0.118: Filter roles by document
     * Returns roles that have the specified document in their sources
     */
    function filterRolesByDocument(roles, documentFilter) {
        if (!documentFilter || documentFilter === 'all') {
            return roles;
        }

        return roles.filter(role => {
            // Check sources array
            if (role.sources && Array.isArray(role.sources)) {
                if (role.sources.some(src => src.filename === documentFilter || src.document === documentFilter)) {
                    return true;
                }
            }
            // Check documents array
            if (role.documents && Array.isArray(role.documents)) {
                if (role.documents.some(doc =>
                    (typeof doc === 'string' && doc === documentFilter) ||
                    (doc.filename === documentFilter)
                )) {
                    return true;
                }
            }
            // Check source field
            if (role.source === documentFilter) {
                return true;
            }
            return false;
        });
    }

    /**
     * v3.0.118: Filter scan history by document
     */
    function filterHistoryByDocument(history, documentFilter) {
        if (!documentFilter || documentFilter === 'all') {
            return history;
        }
        return history.filter(scan => scan.filename === documentFilter);
    }

    /**
     * Render Overview tab
     */
    async function renderOverview() {
        console.log('[TWR RolesTabs] === renderOverview START ===');

        // v4.0.3: Load adjudication cache for badges
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        try {
            console.log('[TWR RolesTabs] Fetching aggregated roles...');
            let roles = await fetchAggregatedRoles();
            console.log('[TWR RolesTabs] Aggregated roles fetched:', roles?.length || 0);

            console.log('[TWR RolesTabs] Fetching scan history...');
            const history = await fetchScanHistory();
            console.log('[TWR RolesTabs] Scan history fetched:', history?.length || 0);
            let dataSource = 'scans';

            // v3.0.117: Populate document filter dropdown with scan history
            populateDocumentFilter(history);
        
        // Fallback to dictionary if no aggregated roles
        if (roles.length === 0) {
            console.log('[TWR RolesTabs] No aggregated roles, falling back to dictionary...');
            roles = await fetchDictionary();
            dataSource = 'dictionary';
            console.log('[TWR RolesTabs] Dictionary roles loaded:', roles?.length || 0);
        }

        // v3.0.118: Apply document filter
        const filteredRoles = filterRolesByDocument(roles, currentDocumentFilter);
        const filteredHistory = filterHistoryByDocument(history, currentDocumentFilter);
        console.log('[TWR RolesTabs] Filter applied:', currentDocumentFilter, '- roles:', filteredRoles.length, '/', roles.length);

        // Update stat cards (use filtered data)
        const totalRoles = filteredRoles.length;
        // v3.0.69: Sum actual responsibility counts, not mentions
        const totalResponsibilities = filteredRoles.reduce((sum, r) => sum + (r.responsibility_count || 0), 0);
        // v3.0.58: Count unique documents by filename, not total scan instances
        const totalDocs = new Set(filteredHistory.map(h => h.filename)).size || 0;

        // Get unique categories
        const categories = new Set(filteredRoles.map(r => r.category).filter(Boolean));
        
        console.log('[TWR RolesTabs] Stats computed: roles=', totalRoles, 'responsibilities=', totalResponsibilities, 'docs=', totalDocs, 'categories=', categories.size);
        
        // Update elements
        const els = {
            roles: document.getElementById('total-roles-count'),
            resp: document.getElementById('total-responsibilities-count'),
            docs: document.getElementById('total-documents-count'),
            interactions: document.getElementById('total-interactions-count'),
            sidebarRoles: document.getElementById('sidebar-roles-count'),
            sidebarResp: document.getElementById('sidebar-resp-count')
        };
        
        console.log('[TWR RolesTabs] DOM elements found:', 
            'roles=', !!els.roles, 
            'resp=', !!els.resp, 
            'docs=', !!els.docs, 
            'interactions=', !!els.interactions);
        
        if (els.roles) els.roles.textContent = totalRoles;
        if (els.resp) els.resp.textContent = totalResponsibilities;
        if (els.docs) els.docs.textContent = totalDocs;
        if (els.interactions) els.interactions.textContent = categories.size;
        if (els.sidebarRoles) els.sidebarRoles.textContent = totalRoles;
        if (els.sidebarResp) els.sidebarResp.textContent = totalResponsibilities;

        // v4.0.3: Update adjudication subtitle under Unique Roles
        const adjStats = adjLookup ? adjLookup.getStats() : { total: 0, confirmed: 0, rejected: 0, deliverable: 0 };
        const adjConfirmed = adjStats.confirmed + (adjStats.deliverable || 0);
        const adjSubtitle = document.getElementById('adjudicated-subtitle');
        const adjSubText = document.getElementById('adjudicated-subtitle-text');
        if (adjSubtitle && adjSubText && adjConfirmed > 0) {
            const parts = [`${adjConfirmed} adjudicated`];
            if (adjStats.deliverable > 0) parts.push(`${adjStats.deliverable} deliverable`);
            adjSubText.textContent = parts.join(' · ');
            adjSubtitle.style.display = '';
        }

        // Show data source indicator
        const topRolesList = document.getElementById('top-roles-list');
        console.log('[TWR RolesTabs] top-roles-list found:', !!topRolesList);
        if (topRolesList) {
            let sourceNote = '';
            if (dataSource === 'dictionary') {
                sourceNote = `
                    <div style="padding:12px;background:var(--bg-tertiary,#fff3cd);border-radius:6px;margin-bottom:12px;font-size:12px;border:1px solid #ffc107;">
                        <i data-lucide="info" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:6px;color:#856404;"></i>
                        <strong>Showing dictionary roles.</strong> Scan documents with "Role Extraction" enabled to see extracted roles with context and RACI data.
                    </div>
                `;
            }
            
            if (filteredRoles.length > 0) {
                // v3.0.69: Sort by responsibility_count (primary) then unique_document_count (secondary)
                const sorted = [...filteredRoles].sort((a, b) => {
                    const respDiff = (b.responsibility_count || 0) - (a.responsibility_count || 0);
                    if (respDiff !== 0) return respDiff;
                    return (b.unique_document_count || b.documents?.length || b.document_count || 1) -
                           (a.unique_document_count || a.documents?.length || a.document_count || 1);
                });
                // v3.0.118: Show filter indicator if filtering
                let filterNote = '';
                if (currentDocumentFilter !== 'all') {
                    filterNote = `<div style="padding:8px 12px;background:rgba(77,171,247,0.1);border-radius:6px;margin-bottom:12px;font-size:12px;border:1px solid var(--accent-blue);">
                        <i data-lucide="filter" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:6px;color:var(--accent-blue);"></i>
                        Filtered by: <strong>${escapeHtml(currentDocumentFilter)}</strong>
                    </div>`;
                }
                topRolesList.innerHTML = sourceNote + filterNote + sorted.slice(0, 10).map((role, i) => {
                    const catColor = getCategoryColor(role.category);
                    // v3.0.69: Show unique document count, not total scan count
                    const uniqueDocCount = role.unique_document_count || role.documents?.length || 0;
                    const docInfo = uniqueDocCount > 0 ? `${uniqueDocCount} doc${uniqueDocCount !== 1 ? 's' : ''}` : (role.source || 'dictionary');
                    // v3.0.69: Show responsibility count on far right
                    const respCount = role.responsibility_count || 0;
                    // v3.1.9: Make role name clickable to view source context
                    const hasSourceContext = uniqueDocCount > 0;
                    // v4.0.3: Adjudication badge
                    const adjBadge = adjLookup ? adjLookup.getBadge(role.role_name, { compact: true, size: 'sm' }) : '';
                    const roleNameHtml = hasSourceContext
                        ? `<span class="role-clickable" data-role-source="${escapeHtml(role.role_name)}" title="Click to view source context" style="cursor:pointer;">${escapeHtml(role.role_name)}</span>`
                        : escapeHtml(role.role_name);
                    return `
                    <div style="display:flex;align-items:center;gap:12px;padding:10px 12px;background:var(--bg-secondary);border-radius:6px;margin-bottom:8px;border-left:3px solid ${catColor};">
                        <span style="font-weight:bold;color:var(--accent);min-width:24px;">${i + 1}</span>
                        <div style="flex:1;min-width:0;">
                            <div style="font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${roleNameHtml}${adjBadge}</div>
                            <div style="font-size:11px;color:var(--text-muted);">
                                <span style="padding:1px 6px;background:${catColor}20;color:${catColor};border-radius:3px;margin-right:6px;">${role.category || 'Role'}</span>
                                ${docInfo}
                            </div>
                        </div>
                        <div style="font-size:14px;font-weight:600;color:var(--accent);" title="${respCount} responsibilities">${respCount}</div>
                    </div>
                `}).join('');
            } else {
                // v3.0.118: Different message for filtered vs unfiltered empty state
                const emptyMsg = currentDocumentFilter !== 'all'
                    ? `No roles found in document "${escapeHtml(currentDocumentFilter)}". Try selecting "All Documents" or a different document.`
                    : 'No roles found. Seed the dictionary or scan documents with "Role Extraction" enabled.';
                topRolesList.innerHTML = `<p class="text-muted" style="padding:20px;text-align:center;">${emptyMsg}</p>`;
            }
        }
        
        // Render distribution chart by category
        const chartContainer = document.getElementById('roles-distribution-chart');
        if (chartContainer && filteredRoles.length > 0) {
            // Group by category
            const categoryCount = {};
            filteredRoles.forEach(r => {
                const cat = r.category || 'Uncategorized';
                categoryCount[cat] = (categoryCount[cat] || 0) + 1;
            });
            
            const sortedCategories = Object.entries(categoryCount).sort((a, b) => b[1] - a[1]);
            const maxVal = Math.max(...sortedCategories.map(([, count]) => count));
            
            chartContainer.innerHTML = sortedCategories.map(([cat, count]) => {
                const pct = Math.max(5, (count / maxVal * 100));
                const color = getCategoryColor(cat);
                return `
                    <div class="role-bar-row">
                        <span class="role-label" title="${escapeHtml(cat)}">${escapeHtml(cat)}</span>
                        <div class="role-bar-container">
                            <div class="role-bar" style="width:${pct}%;background:linear-gradient(90deg, ${color}, ${color}dd);"></div>
                        </div>
                        <span class="role-count">${count}</span>
                    </div>
                `;
            }).join('');
        } else if (chartContainer) {
            chartContainer.innerHTML = '<p class="text-muted text-center">No data for chart</p>';
        }
        
        console.log('[TWR RolesTabs] === renderOverview COMPLETE ===');
        refreshIcons();
        } catch (error) {
            console.error('[TWR RolesTabs] === renderOverview ERROR ===', error);
            throw error;
        }
    }
    
    /**
     * Render Details tab - shows rich role information
     */
    /**
     * Initialize Role Details controls (search input, sort dropdown)
     * v3.0.57: Ensures controls work when details tab is rendered
     */
    function initDetailsControls() {
        const State = window.State || window.TWR?.State?.get?.() || {};
        
        // Search input
        const searchInput = document.getElementById('roles-search');
        if (searchInput && !searchInput._tabsFixInitialized) {
            searchInput._tabsFixInitialized = true;
            searchInput.addEventListener('input', () => {
                filterDetailsRoles(searchInput.value);
            });
        }
        
        // Sort dropdown
        const sortSelect = document.getElementById('roles-sort');
        if (sortSelect && !sortSelect._tabsFixInitialized) {
            sortSelect._tabsFixInitialized = true;
            sortSelect.addEventListener('change', () => {
                State.detailsSort = sortSelect.value;
                console.log('[TWR RolesTabs] Details sort changed to:', sortSelect.value);
                renderDetails();
            });
        }
        
        console.log('[TWR RolesTabs] Details controls initialized');
    }
    
    /**
     * Filter role cards by search text
     */
    function filterDetailsRoles(searchText) {
        const filter = searchText.toLowerCase().trim();
        const cards = document.querySelectorAll('#roles-report-content > div[style*="border"]');
        
        cards.forEach(card => {
            const roleNameEl = card.querySelector('h4');
            const roleName = roleNameEl?.textContent?.toLowerCase() || '';
            const cardText = card.textContent?.toLowerCase() || '';
            
            if (!filter || roleName.includes(filter) || cardText.includes(filter)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
        
        console.log('[TWR RolesTabs] Filtered roles by:', filter || '(none)');
    }
    
    async function renderDetails() {
        console.log('[TWR RolesTabs] === renderDetails START ===');

        // v4.0.3: Load adjudication cache for badges
        const adjLookup = window.AEGIS?.AdjudicationLookup;
        if (adjLookup) await adjLookup.ensureLoaded();

        try {
            const container = document.getElementById('roles-report-content');
            console.log('[TWR RolesTabs] roles-report-content found:', !!container);
            if (!container) {
                console.error('[TWR RolesTabs] CRITICAL: roles-report-content container NOT FOUND');
                return;
            }

            // Initialize controls
            initDetailsControls();
            
            console.log('[TWR RolesTabs] Fetching roles for Details...');
            let roles = await fetchAggregatedRoles();
            let dataSource = 'scans';
            console.log('[TWR RolesTabs] Aggregated roles:', roles?.length || 0);
            
            // Fallback to dictionary if no aggregated roles
            if (roles.length === 0) {
                console.log('[TWR RolesTabs] Falling back to dictionary...');
                roles = await fetchDictionary();
                dataSource = 'dictionary';
                console.log('[TWR RolesTabs] Dictionary roles:', roles?.length || 0);
            }

            // v3.0.118: Apply document filter
            const filteredRoles = filterRolesByDocument(roles, currentDocumentFilter);
            console.log('[TWR RolesTabs] Details filter applied:', currentDocumentFilter, '- roles:', filteredRoles.length, '/', roles.length);

            if (filteredRoles.length === 0) {
                console.log('[TWR RolesTabs] No roles found, showing empty state');
                const emptyMsg = currentDocumentFilter !== 'all'
                    ? `No roles found in document "${escapeHtml(currentDocumentFilter)}". Try selecting "All Documents" or a different document.`
                    : 'Seed the Role Dictionary or scan documents with "Role Extraction" enabled to detect organizational roles.';
                container.innerHTML = emptyState('users', 'No Roles Found', emptyMsg);
                refreshIcons();
                return;
            }

        // Source indicator
        let sourceNote = '';
        if (dataSource === 'dictionary') {
            sourceNote = `
                <div style="padding:12px;background:var(--bg-tertiary,#fff3cd);border-radius:6px;margin-bottom:16px;font-size:12px;border:1px solid #ffc107;">
                    <i data-lucide="info" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:6px;color:#856404;"></i>
                    <strong>Showing dictionary roles.</strong> Scan documents to see extracted context, responsibilities, and document associations.
                </div>
            `;
        }
        
        // Get sort preference
        const State = window.State || window.TWR?.State?.get?.() || {};
        const sortBy = State.detailsSort || document.getElementById('roles-sort')?.value || 'count-desc';
        
        // Sort roles based on selection (use filteredRoles)
        // v5.0.1: Sort by responsibility_count (matching Overview tab behavior)
        const sorted = [...filteredRoles].sort((a, b) => {
            switch (sortBy) {
                case 'count-asc':
                    return (a.responsibility_count || 0) - (b.responsibility_count || 0);
                case 'alpha':
                    return (a.role_name || '').localeCompare(b.role_name || '');
                case 'count-desc':
                default: {
                    const respDiff = (b.responsibility_count || 0) - (a.responsibility_count || 0);
                    if (respDiff !== 0) return respDiff;
                    return (b.unique_document_count || b.document_count || 0) - (a.unique_document_count || a.document_count || 0);
                }
            }
        });

        // v3.0.118: Show filter indicator
        let filterNote = '';
        if (currentDocumentFilter !== 'all') {
            filterNote = `<div style="padding:8px 12px;background:rgba(77,171,247,0.1);border-radius:6px;margin-bottom:12px;font-size:12px;border:1px solid var(--accent-blue);">
                <i data-lucide="filter" style="width:14px;height:14px;display:inline-block;vertical-align:middle;margin-right:6px;color:var(--accent-blue);"></i>
                Showing roles from: <strong>${escapeHtml(currentDocumentFilter)}</strong> (${filteredRoles.length} of ${roles.length} roles)
            </div>`;
        }

        container.innerHTML = sourceNote + filterNote + sorted.map(role => {
            const catColor = getCategoryColor(role.category);
            const aliases = role.aliases?.length > 0 ? role.aliases.join(', ') : null;
            const description = role.description || null;
            const documents = role.documents?.length > 0 ? role.documents : null;
            
            return `
            <div style="border:1px solid var(--border-default);border-radius:8px;padding:16px;margin-bottom:12px;border-left:4px solid ${catColor};" data-role-name="${escapeHtml(role.role_name)}">
                <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:10px;">
                    <div>
                        <h4 style="margin:0 0 6px 0;font-size:16px;"><span class="role-clickable" data-role-source="${escapeHtml(role.role_name)}" title="Click to view source context" style="cursor:pointer;">${escapeHtml(role.role_name)}</span>${adjLookup ? adjLookup.getBadge(role.role_name) : ''}</h4>
                        <div style="display:flex;gap:8px;flex-wrap:wrap;">
                            <span style="font-size:11px;padding:2px 8px;background:${catColor}20;color:${catColor};border-radius:4px;font-weight:500;">${escapeHtml(role.category || 'Role')}</span>
                            ${role.source ? `<span style="font-size:11px;padding:2px 8px;background:var(--bg-secondary);border-radius:4px;">Source: ${escapeHtml(role.source)}</span>` : ''}
                            ${role.is_deliverable ? '<span style="font-size:11px;padding:2px 8px;background:#e3f2fd;color:#1976d2;border-radius:4px;">Deliverable</span>' : ''}
                        </div>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <button class="rd-explore-btn" data-role="${escapeHtml(role.role_name)}" title="Explore in Data Explorer" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:transparent;border:1px solid var(--border-default);border-radius:8px;color:var(--text-muted);cursor:pointer;transition:all 0.2s;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
                        </button>
                        <div style="text-align:right;">
                            <div style="font-size:24px;font-weight:bold;color:var(--accent);">${role.responsibility_count || 0}</div>
                            <div style="font-size:11px;color:var(--text-muted);">responsibilities</div>
                        </div>
                    </div>
                </div>

                ${description ? `
                <div style="margin-bottom:10px;padding:10px;background:var(--bg-secondary);border-radius:6px;">
                    <div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:0.5px;">Description</div>
                    <div style="font-size:13px;">${escapeHtml(description)}</div>
                </div>
                ` : ''}

                ${aliases ? `
                <div style="margin-bottom:10px;">
                    <span style="font-size:12px;color:var(--text-muted);margin-right:8px;">Also known as:</span>
                    <span style="font-size:12px;">${escapeHtml(aliases)}</span>
                </div>
                ` : ''}

                ${documents ? `
                <div style="font-size:12px;">
                    <span style="color:var(--text-muted);margin-right:8px;">Found in:</span>
                    <span>${documents.slice(0, 5).map(d => `<span style="padding:2px 6px;background:var(--bg-secondary);border-radius:3px;margin-right:4px;">${escapeHtml(d)}</span>`).join('')}${documents.length > 5 ? `<span style="color:var(--text-muted);">+${documents.length - 5} more</span>` : ''}</span>
                </div>
                ` : ''}

                <div style="font-size:13px;color:var(--text-secondary);margin-top:8px;">
                    <strong>${role.unique_document_count || documents?.length || role.document_count || 0}</strong> document${(role.unique_document_count || documents?.length || role.document_count || 0) !== 1 ? 's' : ''}
                    &nbsp;·&nbsp; <strong>${role.total_mentions || 0}</strong> mention${(role.total_mentions || 0) !== 1 ? 's' : ''}
                </div>
            </div>
        `}).join('');
        
        // Re-apply any existing search filter
        const searchInput = document.getElementById('roles-search');
        if (searchInput?.value) {
            filterDetailsRoles(searchInput.value);
        }

        // v4.4.0: Add click handlers for Explore buttons to open Data Explorer
        container.querySelectorAll('.rd-explore-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const roleName = btn.dataset.role;
                if (window.TWR?.DataExplorer) {
                    window.TWR.DataExplorer.open();
                    setTimeout(() => {
                        window.TWR.DataExplorer.drillInto('role', roleName, { name: roleName });
                    }, 600);
                }
            });
            // Hover effect
            btn.addEventListener('mouseenter', () => {
                btn.style.background = 'rgba(74, 144, 217, 0.15)';
                btn.style.borderColor = 'var(--accent, #4a90d9)';
                btn.style.color = 'var(--accent, #4a90d9)';
                btn.style.transform = 'scale(1.1)';
            });
            btn.addEventListener('mouseleave', () => {
                btn.style.background = 'transparent';
                btn.style.borderColor = 'var(--border-default)';
                btn.style.color = 'var(--text-muted)';
                btn.style.transform = 'scale(1)';
            });
        });

        console.log('[TWR RolesTabs] === renderDetails COMPLETE ===');
        // Scoped icon refresh — only process icons inside this tab's container
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [container] }); } catch (_) { refreshIcons(); }
        }
        } catch (error) {
            console.error('[TWR RolesTabs] === renderDetails ERROR ===', error);
            throw error;
        }
    }
    
    /**
     * Render Cross-Reference tab (Role × Document count matrix)
     * NOTE: This tab requires actual scan data - dictionary roles don't have document associations
     */
    async function renderCrossRef() {
        console.log('[TWR RolesTabs] Rendering Cross-Reference...');
        
        const container = document.getElementById('crossref-matrix');
        if (!container) return;
        
        const matrix = await fetchMatrix();
        
        if (!matrix || !matrix.roles || Object.keys(matrix.roles).length === 0) {
            // Check if dictionary has data to show helpful message
            const dictRoles = await fetchDictionary();
            const hasDict = dictRoles.length > 0;
            
            container.innerHTML = `
                <div class="empty-state" style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 20px;text-align:center;color:var(--text-muted);">
                    <i data-lucide="table" style="width:48px;height:48px;margin-bottom:16px;opacity:0.5;"></i>
                    <h4 style="margin:0 0 8px 0;color:var(--text-secondary);">No Cross-Reference Data</h4>
                    <p style="margin:0 0 16px 0;max-width:450px;">
                        ${hasDict 
                            ? `You have <strong>${dictRoles.length} roles</strong> in your dictionary, but Cross-Reference requires scan data to show which roles appear in which documents.`
                            : 'Scan documents with "Role Extraction" enabled to see role distribution across documents.'
                        }
                    </p>
                    <div style="background:var(--bg-secondary);padding:16px;border-radius:8px;text-align:left;max-width:400px;">
                        <div style="font-weight:600;margin-bottom:8px;color:var(--text-primary);">To populate this tab:</div>
                        <ol style="margin:0;padding-left:20px;color:var(--text-secondary);font-size:13px;">
                            <li>Open a document (.docx or .pdf)</li>
                            <li>Enable "Role Extraction" in the sidebar</li>
                            <li>Click "Run Review"</li>
                            <li>Return here to see the matrix</li>
                        </ol>
                    </div>
                </div>
            `;
            refreshIcons();
            return;
        }
        
        const { documents = {}, roles = {}, connections = {} } = matrix;
        const docList = Object.entries(documents);
        const roleList = Object.entries(roles);
        
        if (roleList.length === 0 || docList.length === 0) {
            container.innerHTML = emptyState('table', 'Insufficient Data', 
                'Need at least one role and one document to display cross-reference.');
            refreshIcons();
            return;
        }
        
        // Sort roles by total mentions across all docs
        const roleTotals = {};
        roleList.forEach(([roleId, roleName]) => {
            let total = 0;
            if (connections[roleId]) {
                Object.values(connections[roleId]).forEach(count => total += count);
            }
            roleTotals[roleId] = total;
        });
        
        roleList.sort((a, b) => (roleTotals[b[0]] || 0) - (roleTotals[a[0]] || 0));
        
        // Calculate column totals for documents
        const docTotals = {};
        docList.forEach(([docId]) => {
            let total = 0;
            roleList.forEach(([roleId]) => {
                total += connections[roleId]?.[docId] || 0;
            });
            docTotals[docId] = total;
        });
        
        // Helper function for heatmap color
        function getHeatmapColor(count) {
            if (count === 0) return '';
            if (count <= 2) return 'background:#e3f2fd;';
            if (count <= 5) return 'background:#90caf9;';
            if (count <= 10) return 'background:#42a5f5;color:white;';
            return 'background:#1976d2;color:white;';
        }
        
        // Build table
        let html = `
            <table class="crossref-table" style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead>
                    <tr>
                        <th style="text-align:left;padding:10px;border-bottom:2px solid var(--border-default);background:var(--bg-surface);position:sticky;left:0;top:0;z-index:2;min-width:160px;">
                            Role
                        </th>
        `;
        
        // Document headers
        docList.forEach(([docId, docName]) => {
            const shortName = docName.length > 18 ? docName.slice(0, 15) + '...' : docName;
            html += `
                <th style="padding:10px;border-bottom:2px solid var(--border-default);background:var(--bg-surface);position:sticky;top:0;z-index:1;min-width:80px;max-width:120px;text-align:center;" 
                    title="${escapeHtml(docName)}">
                    ${escapeHtml(shortName)}
                </th>
            `;
        });
        
        // Total column header
        html += `
            <th style="padding:10px;border-bottom:2px solid var(--border-default);background:var(--bg-tertiary,#f5f5f5);position:sticky;top:0;z-index:1;min-width:60px;text-align:center;font-weight:bold;">
                Total
            </th>
        </tr></thead><tbody>`;
        
        // Role rows
        roleList.forEach(([roleId, roleName]) => {
            const rowTotal = roleTotals[roleId] || 0;
            // v3.1.9: Make role name clickable to view source context
            const roleNameHtml = `<span class="role-clickable" data-role-source="${escapeHtml(roleName)}" title="Click to view source context" style="cursor:pointer;">${escapeHtml(roleName)}</span>`;
            html += `
                <tr class="crossref-row" data-role="${escapeHtml(roleName)}">
                    <td style="padding:10px;border-bottom:1px solid var(--border-default);background:var(--bg-surface);position:sticky;left:0;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px;"
                        title="${escapeHtml(roleName)}">
                        ${roleNameHtml}
                    </td>
            `;
            
            // Cell for each document
            docList.forEach(([docId]) => {
                const count = connections[roleId]?.[docId] || 0;
                const colorStyle = getHeatmapColor(count);
                html += `
                    <td style="padding:10px;text-align:center;border-bottom:1px solid var(--border-default);${colorStyle}">
                        ${count || '-'}
                    </td>
                `;
            });
            
            // Row total
            html += `
                <td style="padding:10px;text-align:center;border-bottom:1px solid var(--border-default);background:var(--bg-tertiary,#f5f5f5);font-weight:bold;">
                    ${rowTotal}
                </td>
            </tr>`;
        });
        
        // Footer row with column totals
        html += `
            <tr class="crossref-totals" style="font-weight:bold;">
                <td style="padding:10px;border-top:2px solid var(--border-default);background:var(--bg-tertiary,#f5f5f5);position:sticky;left:0;">
                    Total
                </td>
        `;
        
        let grandTotal = 0;
        docList.forEach(([docId]) => {
            const colTotal = docTotals[docId] || 0;
            grandTotal += colTotal;
            html += `
                <td style="padding:10px;text-align:center;border-top:2px solid var(--border-default);background:var(--bg-tertiary,#f5f5f5);">
                    ${colTotal}
                </td>
            `;
        });
        
        html += `
            <td style="padding:10px;text-align:center;border-top:2px solid var(--border-default);background:var(--bg-tertiary,#f0f0f0);">
                ${grandTotal}
            </td>
        </tr></tbody></table>`;
        
        container.innerHTML = html;
        
        // Setup search filter
        const searchInput = document.getElementById('crossref-search');
        if (searchInput && !searchInput._filterInitialized) {
            searchInput._filterInitialized = true;
            searchInput.addEventListener('input', function() {
                const filter = this.value.toLowerCase();
                document.querySelectorAll('.crossref-row').forEach(row => {
                    const roleName = row.dataset.role?.toLowerCase() || '';
                    row.style.display = roleName.includes(filter) ? '' : 'none';
                });
            });
        }
        
        // Setup CSV export
        const exportBtn = document.getElementById('btn-crossref-export');
        if (exportBtn && !exportBtn._exportInitialized) {
            exportBtn._exportInitialized = true;
            exportBtn.addEventListener('click', function() {
                exportCrossRefCSV(roleList, docList, connections, roleTotals, docTotals);
            });
        }
        
        console.log('[TWR RolesTabs] Cross-Reference rendered with', roleList.length, 'roles ×', docList.length, 'documents');
    }
    
    /**
     * Export Cross-Reference as CSV
     */
    function exportCrossRefCSV(roleList, docList, connections, roleTotals, docTotals) {
        let csv = 'Role,' + docList.map(([, name]) => `"${name.replace(/"/g, '""')}"`).join(',') + ',Total\n';
        
        roleList.forEach(([roleId, roleName]) => {
            const row = [`"${roleName.replace(/"/g, '""')}"`];
            docList.forEach(([docId]) => {
                row.push(connections[roleId]?.[docId] || 0);
            });
            row.push(roleTotals[roleId] || 0);
            csv += row.join(',') + '\n';
        });
        
        // Totals row
        const totalsRow = ['Total'];
        let grandTotal = 0;
        docList.forEach(([docId]) => {
            totalsRow.push(docTotals[docId] || 0);
            grandTotal += docTotals[docId] || 0;
        });
        totalsRow.push(grandTotal);
        csv += totalsRow.join(',') + '\n';
        
        // Download
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'role_crossref_' + new Date().toISOString().slice(0, 10) + '.csv';
        link.click();
        URL.revokeObjectURL(url);
        
        showToast('success', 'Cross-reference exported to CSV');
    }
    
    /**
     * Initialize RACI matrix controls (sort dropdown, filter checkbox)
     * v3.0.57: Ensures controls work when matrix is rendered via roles-tabs-fix.js
     */
    function initRaciControls() {
        const State = window.State || window.TWR?.State?.get?.() || {};
        
        // Sort dropdown
        const sortSelect = document.getElementById('matrix-sort');
        if (sortSelect && !sortSelect._tabsFixInitialized) {
            sortSelect._tabsFixInitialized = true;
            sortSelect.addEventListener('change', () => {
                State.matrixSort = sortSelect.value;
                console.log('[TWR RolesTabs] Sort changed to:', sortSelect.value);
                // Re-render the matrix
                if (typeof window.TWR?.Roles?.renderRolesMatrix === 'function') {
                    window.TWR.Roles.renderRolesMatrix();
                } else if (typeof window.renderRolesMatrix === 'function') {
                    window.renderRolesMatrix();
                }
            });
        }
        
        // Filter checkbox
        const filterCritical = document.getElementById('matrix-filter-critical');
        if (filterCritical && !filterCritical._tabsFixInitialized) {
            filterCritical._tabsFixInitialized = true;
            filterCritical.addEventListener('change', () => {
                State.matrixFilterCritical = filterCritical.checked;
                console.log('[TWR RolesTabs] Filter critical changed to:', filterCritical.checked);
                // Re-render the matrix
                if (typeof window.TWR?.Roles?.renderRolesMatrix === 'function') {
                    window.TWR.Roles.renderRolesMatrix();
                } else if (typeof window.renderRolesMatrix === 'function') {
                    window.renderRolesMatrix();
                }
            });
        }
        
        // Reset button
        const resetBtn = document.getElementById('btn-raci-reset');
        if (resetBtn && !resetBtn._tabsFixInitialized) {
            resetBtn._tabsFixInitialized = true;
            resetBtn.addEventListener('click', () => {
                State.raciEdits = {};
                showToast('success', 'RACI matrix reset to detected values');
                if (typeof window.TWR?.Roles?.renderRolesMatrix === 'function') {
                    window.TWR.Roles.renderRolesMatrix();
                } else if (typeof window.renderRolesMatrix === 'function') {
                    window.renderRolesMatrix();
                }
            });
        }
        
        // Export button - v5.0.0: Use toggleExportMenu for function category filter dropdown
        const exportBtn = document.getElementById('btn-raci-export');
        if (exportBtn && !exportBtn._tabsFixInitialized) {
            exportBtn._tabsFixInitialized = true;
            exportBtn.addEventListener('click', (e) => {
                if (typeof window.TWR?.Roles?.toggleExportMenu === 'function') {
                    window.TWR.Roles.toggleExportMenu(e);
                } else if (typeof window.TWR?.Roles?.exportRaciMatrix === 'function') {
                    window.TWR.Roles.exportRaciMatrix();
                } else {
                    showToast('info', 'Export requires scan data');
                }
            });
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
        if (dictFilter && !dictFilter._tabsFixInitialized) {
            dictFilter._tabsFixInitialized = true;
            dictFilter.addEventListener('change', () => {
                State.matrixDictFilter = dictFilter.value;
                console.log('[TWR RolesTabs] Dict filter changed to:', dictFilter.value);
                if (typeof window.TWR?.Roles?.renderRolesMatrix === 'function') {
                    window.TWR.Roles.renderRolesMatrix();
                } else if (typeof window.renderRolesMatrix === 'function') {
                    window.renderRolesMatrix();
                }
            });
        }

        console.log('[TWR RolesTabs] RACI controls initialized');
    }
    
    /**
     * Render Matrix tab - RACI assignments
     * RACI data requires actual document scans with action verb analysis.
     */
    async function renderMatrix() {
        console.log('[TWR RolesTabs] Rendering RACI Matrix...');

        const container = document.getElementById('responsibility-matrix');
        if (!container) {
            console.warn('[TWR RolesTabs] responsibility-matrix container not found');
            return;
        }

        // v3.1.0: Get State reference and try to populate from aggregated if empty
        const State = window.State || window.TWR?.State?.get?.() || {};

        // v3.1.0: If State.roles is empty but we have aggregated data, populate State.roles
        if (!State.roles || Object.keys(State.roles).length === 0) {
            console.log('[TWR RolesTabs] State.roles empty, trying to populate from aggregated...');
            const aggregated = await fetchAggregatedRoles();

            if (aggregated && aggregated.length > 0) {
                // Convert aggregated array to State.roles format
                const rolesObj = {};
                aggregated.forEach(role => {
                    const roleName = role.role_name || role.name;
                    if (roleName) {
                        rolesObj[roleName] = {
                            name: roleName,
                            count: role.occurrence_count || role.count || 1,
                            responsibilities: role.responsibilities || [],
                            action_types: role.action_types || {},
                            sources: role.sources || role.documents || []
                        };
                    }
                });

                // Try to set State.roles
                if (window.State) {
                    window.State.roles = rolesObj;
                } else if (window.TWR?.State?.set) {
                    window.TWR.State.set('roles', rolesObj);
                }

                console.log('[TWR RolesTabs] Populated State.roles with', Object.keys(rolesObj).length, 'roles from aggregated');
            }
        }

        // Re-check State.roles after potential population
        const stateRoles = window.State?.roles || State.roles || {};

        if (stateRoles && Object.keys(stateRoles).length > 0) {
            // Check if we have actual RACI data (action_types)
            const hasActionTypes = Object.values(stateRoles).some(r =>
                r.action_types && Object.keys(r.action_types).length > 0
            );

            // v3.1.0: Always try to render if we have roles, even without action_types
            // Original renderer uses 'matrix-container' but our HTML has 'responsibility-matrix'
            let matrixContainer = document.getElementById('matrix-container');
            if (!matrixContainer) {
                container.innerHTML = '<div id="matrix-container"></div>';
                matrixContainer = document.getElementById('matrix-container');
            }

            if (typeof window.TWR?.Roles?.renderRolesMatrix === 'function') {
                // v3.1.10: Await the async renderRolesMatrix function
                await window.TWR.Roles.renderRolesMatrix();
                initRaciControls();  // v3.0.57: Initialize controls after render
                return;
            } else if (typeof window.renderRolesMatrix === 'function') {
                await window.renderRolesMatrix();
                initRaciControls();  // v3.0.57: Initialize controls after render
                return;
            }
        }

        // Initialize controls even when showing fallback (for when data loads later)
        initRaciControls();

        // Check for dictionary data to show helpful guidance
        let roles = await fetchAggregatedRoles();
        let dataSource = 'scans';
        
        if (roles.length === 0) {
            roles = await fetchDictionary();
            dataSource = 'dictionary';
        }
        
        if (roles.length === 0) {
            container.innerHTML = emptyState('grid-3x3', 'No RACI Data Available',
                'Scan a document with "Role Extraction" enabled to generate RACI assignments.');
            refreshIcons();
            return;
        }
        
        // Show explanation and role list without RACI assignments
        const catColors = {};
        roles.forEach(r => {
            if (r.category && !catColors[r.category]) {
                catColors[r.category] = getCategoryColor(r.category);
            }
        });
        
        let html = `
            <div style="padding:16px;background:var(--bg-tertiary,#fff3cd);border-radius:8px;margin-bottom:20px;border:1px solid #ffc107;">
                <div style="display:flex;align-items:start;gap:12px;">
                    <i data-lucide="alert-triangle" style="width:24px;height:24px;color:#856404;flex-shrink:0;margin-top:2px;"></i>
                    <div>
                        <div style="font-weight:600;color:#856404;margin-bottom:8px;">RACI Matrix Requires Document Scans</div>
                        <p style="margin:0 0 12px 0;font-size:13px;color:#856404;">
                            ${dataSource === 'dictionary' 
                                ? `You have <strong>${roles.length} roles</strong> in your dictionary, but RACI assignments (R/A/C/I) are computed by analyzing action verbs in documents.`
                                : 'RACI assignments are computed from action verbs like "shall perform", "approve", "review", "notify".'
                            }
                        </p>
                        <div style="font-size:12px;color:#856404;">
                            <strong>How RACI is detected:</strong>
                            <ul style="margin:8px 0 0 0;padding-left:20px;">
                                <li><strong>R</strong> (Responsible): "shall perform", "executes", "develops", "creates"</li>
                                <li><strong>A</strong> (Accountable): "approves", "authorizes", "owns", "certifies"</li>
                                <li><strong>C</strong> (Consulted): "reviews", "advises", "coordinates", "supports"</li>
                                <li><strong>I</strong> (Informed): "is notified", "receives reports", "monitors"</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <h4 style="margin:0 0 12px 0;color:var(--text-secondary);">
                ${dataSource === 'dictionary' ? 'Dictionary Roles' : 'Known Roles'} (${roles.length})
            </h4>
            
            <div style="display:flex;flex-wrap:wrap;gap:8px;">
        `;
        
        // Show roles as chips grouped by category
        const byCategory = {};
        roles.forEach(r => {
            const cat = r.category || 'Uncategorized';
            if (!byCategory[cat]) byCategory[cat] = [];
            byCategory[cat].push(r);
        });
        
        Object.entries(byCategory).sort((a, b) => b[1].length - a[1].length).slice(0, 10).forEach(([cat, catRoles]) => {
            const color = getCategoryColor(cat);
            html += `
                <div style="margin-bottom:12px;width:100%;">
                    <div style="font-size:12px;font-weight:600;color:${color};margin-bottom:6px;">${escapeHtml(cat)} (${catRoles.length})</div>
                    <div style="display:flex;flex-wrap:wrap;gap:6px;">
                        ${catRoles.slice(0, 15).map(r => `
                            <span class="role-clickable" data-role-source="${escapeHtml(r.role_name)}" title="Click to view source context" style="padding:4px 10px;background:${color}15;border:1px solid ${color}40;border-radius:4px;font-size:12px;cursor:pointer;">${escapeHtml(r.role_name)}</span>
                        `).join('')}
                        ${catRoles.length > 15 ? `<span style="padding:4px 10px;color:var(--text-muted);font-size:12px;">+${catRoles.length - 15} more</span>` : ''}
                    </div>
                </div>
            `;
        });
        
        if (Object.keys(byCategory).length > 10) {
            html += `<div style="width:100%;color:var(--text-muted);font-size:12px;margin-top:8px;">+${Object.keys(byCategory).length - 10} more categories</div>`;
        }
        
        html += '</div>';

        container.innerHTML = html;
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [container] }); } catch (_) { refreshIcons(); }
        }
    }
    
    // ============================================================
    // ADJUDICATION v4.0.3 - COMPLETE OVERHAUL
    // Dashboard, Kanban, Auto-Classify, Function Tags, Keyboard Nav, Undo/Redo
    // ============================================================

    // --- Adjudication State ---
    const AdjState = {
        roles: [],              // Current roles data
        functionCategories: [], // All function categories
        viewMode: localStorage.getItem('adj-view-mode') || 'list',
        focusIndex: -1,         // Currently focused card index
        activeFilter: 'pending',
        searchText: '',
        selectedRoles: new Set(),
        tagDropdownOpen: null   // Role name of open tag dropdown
    };

    // --- Undo/Redo History ---
    const AdjHistory = {
        stack: [],
        position: -1,
        maxSize: 50,
        push(entry) {
            // Remove any redo entries
            this.stack = this.stack.slice(0, this.position + 1);
            this.stack.push({ ...entry, timestamp: Date.now() });
            if (this.stack.length > this.maxSize) this.stack.shift();
            this.position = this.stack.length - 1;
            this._updateButtons();
        },
        undo() {
            if (!this.canUndo()) return null;
            const entry = this.stack[this.position];
            this.position--;
            this._updateButtons();
            return entry;
        },
        redo() {
            if (!this.canRedo()) return null;
            this.position++;
            const entry = this.stack[this.position];
            this._updateButtons();
            return entry;
        },
        canUndo() { return this.position >= 0; },
        canRedo() { return this.position < this.stack.length - 1; },
        _updateButtons() {
            const undoBtn = document.getElementById('btn-undo-adj');
            const redoBtn = document.getElementById('btn-redo-adj');
            if (undoBtn) undoBtn.disabled = !this.canUndo();
            if (redoBtn) redoBtn.disabled = !this.canRedo();
        }
    };

    // --- Confidence Ring SVG ---
    function renderConfidenceRing(confidence) {
        const pct = Math.round((confidence || 0.5) * 100);
        const r = 18;
        const circumference = 2 * Math.PI * r;
        const offset = circumference - (pct / 100) * circumference;
        const color = pct >= 80 ? 'var(--success)' : pct >= 60 ? '#d29922' : 'var(--error)';
        return `<div class="adj-confidence-ring">
            <svg viewBox="0 0 44 44">
                <circle class="ring-bg" cx="22" cy="22" r="${r}"/>
                <circle class="ring-fill" cx="22" cy="22" r="${r}"
                    stroke="${color}" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"/>
            </svg>
            <span class="ring-text" style="color:${color}">${pct}%</span>
        </div>`;
    }

    // --- Progress Ring (Dashboard) ---
    function renderProgressRing(adjudicated, total) {
        const pct = total > 0 ? Math.round((adjudicated / total) * 100) : 0;
        const r = 22;
        const circumference = 2 * Math.PI * r;
        const offset = circumference - (pct / 100) * circumference;
        const container = document.getElementById('adj-progress-ring');
        if (!container) return;
        container.innerHTML = `<div class="adj-confidence-ring" style="width:52px;height:52px;">
            <svg viewBox="0 0 52 52">
                <circle class="ring-bg" cx="26" cy="26" r="${r}"/>
                <circle class="ring-fill" cx="26" cy="26" r="${r}"
                    stroke="var(--aegis-gold, #D6A84A)" stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"/>
            </svg>
            <span class="ring-text" style="font-size:13px;font-weight:700;color:var(--aegis-gold, #D6A84A);">${pct}%</span>
        </div>`;
    }

    // --- Get status for a role ---
    function getRoleStatus(role) {
        // Check AdjudicationState from roles.js first
        if (window.TWR?.Roles?.AdjudicationState?.decisions) {
            const decision = window.TWR.Roles.AdjudicationState.decisions.get(role.role_name);
            if (decision && decision.status !== 'pending') return decision.status;
        }
        // Check role data
        if (role.status && role.status !== 'pending') return role.status;
        if (role.is_active === false || role.is_active === 0) return 'rejected';
        if (role.is_deliverable) return 'deliverable';
        // v4.6.2-fix: DEFECT-006 — 'rename' source also means confirmed
        if (role.source === 'adjudication' || role.source === 'builtin' || role.source === 'sipoc' || role.source === 'rename') return 'confirmed';
        return 'pending';
    }

    // --- Get confidence for a role ---
    function getRoleConfidence(role) {
        if (window.TWR?.Roles?.AdjudicationState?.decisions) {
            const d = window.TWR.Roles.AdjudicationState.decisions.get(role.role_name);
            if (d && d.confidence) return d.confidence;
        }
        // Heuristic confidence based on data richness
        let conf = 0.5;
        const docCount = role.unique_document_count || role.document_count || 0;
        const mentions = role.total_mentions || 0;
        const respCount = role.responsibility_count || 0;
        if (docCount >= 3) conf += 0.15;
        else if (docCount >= 1) conf += 0.05;
        if (mentions >= 5) conf += 0.1;
        else if (mentions >= 2) conf += 0.05;
        if (respCount >= 2) conf += 0.15;
        else if (respCount >= 1) conf += 0.05;
        // Role name pattern bonus
        const nameLC = role.role_name.toLowerCase();
        if (/\b(engineer|manager|lead|director|officer|specialist|analyst|coordinator|supervisor)\b/.test(nameLC)) {
            conf += 0.1;
        }
        return Math.min(conf, 0.99);
    }

    // --- Render a single role card (List View) ---
    function renderAdjRoleCard(role, index) {
        const status = getRoleStatus(role);
        const confidence = getRoleConfidence(role);
        const catColor = getCategoryColor(role.category);
        const documents = role.documents?.slice(0, 3) || [];
        const tags = role.function_tags || [];
        const isFocused = AdjState.focusIndex === index;
        const isSelected = AdjState.selectedRoles.has(role.role_name);

        // Context sentences
        const contexts = [];
        if (role.sample_contexts?.length) {
            role.sample_contexts.slice(0, 5).forEach(c => contexts.push(c));
        }

        return `<div class="adj-role-card status-${status}${isFocused ? ' adj-focused' : ''}"
                     data-role="${escapeHtml(role.role_name)}" data-role-id="${role.id || ''}"
                     data-index="${index}" data-status="${status}">
            <div class="adj-card-checkbox">
                <input type="checkbox" class="adj-item-checkbox" ${isSelected ? 'checked' : ''}>
            </div>
            ${renderConfidenceRing(confidence)}
            <div class="adj-card-body">
                <div class="adj-card-title-row">
                    <span class="adj-card-name role-clickable" data-role-source="${escapeHtml(role.role_name)}"
                          title="Click to view in Source Viewer">${escapeHtml(role.role_name)}</span>
                    <span class="adj-card-category" style="background:${catColor}18;color:${catColor};border:1px solid ${catColor}30;">${escapeHtml(role.category || 'Role')}</span>
                    ${status !== 'pending' ? `<span class="adj-status-badge status-${status}">${status.charAt(0).toUpperCase() + status.slice(1)}</span>` : ''}
                </div>
                <div class="adj-tag-pills" style="position:relative;">
                    ${tags.map(t => `<span class="adj-tag-pill" style="background:${t.color || '#3b82f6'}18;color:${t.color || '#3b82f6'};border-color:${t.color || '#3b82f6'}30;">
                        ${escapeHtml(t.name || t.code)}
                        <span class="adj-tag-remove" data-role="${escapeHtml(role.role_name)}" data-tag-id="${t.id || ''}" data-code="${escapeHtml(t.code)}" title="Remove tag">&times;</span>
                    </span>`).join('')}
                    <button class="adj-tag-add-btn" data-role="${escapeHtml(role.role_name)}" title="Add function tag">
                        <i data-lucide="tag" style="width:13px;height:13px;"></i> Add Tag
                    </button>
                </div>
                ${documents.length > 0 ? `<div class="adj-doc-chips">
                    ${documents.map(d => `<span class="adj-doc-chip" title="${escapeHtml(d)}">${escapeHtml(d.length > 25 ? d.slice(0, 22) + '...' : d)}</span>`).join('')}
                    ${(role.documents?.length || 0) > 3 ? `<span class="adj-doc-chip">+${role.documents.length - 3} more</span>` : ''}
                </div>` : ''}
                <div class="adj-card-meta">
                    ${role.unique_document_count ? `<span><strong>${role.unique_document_count}</strong> docs</span>` : ''}
                    ${role.total_mentions ? `<span><strong>${role.total_mentions}</strong> mentions</span>` : ''}
                    ${role.responsibility_count ? `<span><strong>${role.responsibility_count}</strong> responsibilities</span>` : ''}
                    ${role.source ? `<span>src: ${escapeHtml(role.source)}</span>` : ''}
                </div>
                ${contexts.length > 0 ? `<div class="adj-card-context">
                    <div class="adj-card-context-text">${escapeHtml(contexts[0])}</div>
                    ${contexts.length > 1 ? `<button class="adj-card-context-toggle" data-role="${escapeHtml(role.role_name)}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
                        ${contexts.length - 1} more context${contexts.length > 2 ? 's' : ''}
                    </button>
                    <div class="adj-card-context-expanded" style="display:none;">
                        ${contexts.slice(1).map(c => `<div class="adj-card-context-sentence">${escapeHtml(c)}</div>`).join('')}
                    </div>` : ''}
                </div>` : ''}
            </div>
            <div class="adj-card-actions">
                <button class="adj-action-btn adj-btn-confirm${status === 'confirmed' ? ' adj-active-confirm' : ''}" title="Confirm as Role (C)" data-action="confirmed">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>
                </button>
                <button class="adj-action-btn adj-btn-deliverable${status === 'deliverable' ? ' adj-active-deliverable' : ''}" title="Mark as Deliverable (D)" data-action="deliverable">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
                </button>
                <button class="adj-action-btn adj-btn-reject${status === 'rejected' ? ' adj-active-reject' : ''}" title="Reject (R)" data-action="rejected">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>
                </button>
                <button class="adj-action-btn adj-btn-view" title="View in Source Viewer (V)" data-action="view">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
                <button class="adj-action-btn adj-btn-statements" title="View Statements (S)" data-action="statements">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                </button>
            </div>
        </div>`;
    }

    // --- Render Kanban Card ---
    function renderKanbanCard(role) {
        const tags = role.function_tags || [];
        return `<div class="adj-kanban-card" draggable="true" data-role="${escapeHtml(role.role_name)}" data-role-id="${role.id || ''}">
            <div class="adj-kanban-card-name">${escapeHtml(role.role_name)}</div>
            <div class="adj-kanban-card-meta">
                ${role.unique_document_count ? `<span>${role.unique_document_count} docs</span>` : ''}
                ${role.total_mentions ? `<span>${role.total_mentions} mentions</span>` : ''}
            </div>
            ${tags.length > 0 ? `<div class="adj-kanban-card-tags">
                ${tags.slice(0, 3).map(t => `<span class="adj-kanban-card-tag" style="background:${t.color || '#3b82f6'}20;color:${t.color || '#3b82f6'};">${escapeHtml(t.code || t.name)}</span>`).join('')}
            </div>` : ''}
        </div>`;
    }

    // --- Update Dashboard Stats ---
    function updateAdjDashboard(roles) {
        let pending = 0, confirmed = 0, deliverable = 0, rejected = 0;
        roles.forEach(r => {
            const s = getRoleStatus(r);
            if (s === 'confirmed') confirmed++;
            else if (s === 'deliverable') deliverable++;
            else if (s === 'rejected') rejected++;
            else pending++;
        });

        const updateEl = (id, val) => {
            const el = document.getElementById(id);
            if (el && el.textContent !== String(val)) {
                el.textContent = val;
                el.classList.remove('adj-count-updated');
                void el.offsetWidth; // Force reflow
                el.classList.add('adj-count-updated');
            }
        };
        updateEl('adj-pending-count', pending);
        updateEl('adj-confirmed-count', confirmed);
        updateEl('adj-deliverable-count', deliverable);
        updateEl('adj-rejected-count', rejected);

        // Progress ring
        const adjudicated = confirmed + deliverable + rejected;
        renderProgressRing(adjudicated, roles.length);

        // Update kanban counts
        updateEl('adj-kanban-pending', pending);
        updateEl('adj-kanban-confirmed', confirmed);
        updateEl('adj-kanban-deliverable', deliverable);
        updateEl('adj-kanban-rejected', rejected);
    }

    // --- Filter roles ---
    function getFilteredRoles(roles) {
        const filter = AdjState.activeFilter;
        const search = AdjState.searchText;

        return roles.filter(role => {
            const status = getRoleStatus(role);
            // Status filter
            if (filter === 'pending' && status !== 'pending') return false;
            if (filter === 'confirmed' && status !== 'confirmed') return false;
            if (filter === 'deliverable' && status !== 'deliverable') return false;
            if (filter === 'rejected' && status !== 'rejected') return false;
            if (filter === 'low-confidence' && getRoleConfidence(role) >= 0.7) return false;
            if (filter === 'has-tags' && !(role.function_tags?.length > 0)) return false;
            if (filter === 'no-tags' && (role.function_tags?.length > 0)) return false;
            // Search
            if (search) {
                const q = search.toLowerCase();
                const name = role.role_name.toLowerCase();
                const cat = (role.category || '').toLowerCase();
                const docs = (role.documents || []).join(' ').toLowerCase();
                if (!name.includes(q) && !cat.includes(q) && !docs.includes(q)) return false;
            }
            return true;
        });
    }

    // --- Render List View ---
    function renderAdjListView(roles) {
        const container = document.getElementById('adjudication-list');
        if (!container) return;

        const filtered = getFilteredRoles(roles);

        if (filtered.length === 0) {
            container.innerHTML = emptyState('check-circle', 'No Roles Match Filter',
                AdjState.activeFilter === 'pending' && roles.length > 0
                    ? 'All roles have been adjudicated. Change the filter to view them.'
                    : 'Scan documents with "Role Extraction" enabled to detect roles for review.');
            refreshIcons();
            return;
        }

        // Sort: pending first, then by confidence descending (highest confidence first)
        filtered.sort((a, b) => {
            const sa = getRoleStatus(a), sb = getRoleStatus(b);
            if (sa === 'pending' && sb !== 'pending') return -1;
            if (sa !== 'pending' && sb === 'pending') return 1;
            return getRoleConfidence(b) - getRoleConfidence(a);
        });

        container.innerHTML = filtered.map((role, i) => renderAdjRoleCard(role, i)).join('');

        if (filtered.length < roles.length) {
            container.innerHTML += `<p style="text-align:center;color:var(--text-muted);font-size:12px;margin-top:8px;">
                Showing ${filtered.length} of ${roles.length} roles</p>`;
        }

        // Scoped icon refresh — only process icons inside adjudication container
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons({ nodes: [container] }); } catch (_) { refreshIcons(); }
        }
    }

    // --- Render Kanban View ---
    function renderAdjKanbanView(roles) {
        const columns = {
            pending: document.getElementById('adj-kanban-cards-pending'),
            confirmed: document.getElementById('adj-kanban-cards-confirmed'),
            deliverable: document.getElementById('adj-kanban-cards-deliverable'),
            rejected: document.getElementById('adj-kanban-cards-rejected')
        };

        Object.values(columns).forEach(c => { if (c) c.innerHTML = ''; });

        // Apply search filter so kanban cards match the search box
        const search = AdjState.searchText;
        const filtered = search ? roles.filter(role => {
            const q = search.toLowerCase();
            const name = role.role_name.toLowerCase();
            const cat = (role.category || '').toLowerCase();
            const docs = (role.documents || []).join(' ').toLowerCase();
            return name.includes(q) || cat.includes(q) || docs.includes(q);
        }) : roles;

        filtered.forEach(role => {
            const status = getRoleStatus(role);
            const col = columns[status] || columns.pending;
            if (col) col.innerHTML += renderKanbanCard(role);
        });

        // Update column counts to reflect filtered results
        const counts = { pending: 0, confirmed: 0, deliverable: 0, rejected: 0 };
        filtered.forEach(r => { const s = getRoleStatus(r); counts[s] = (counts[s] || 0) + 1; });
        const updateCount = (id, n) => { const el = document.getElementById(id); if (el) el.textContent = n; };
        updateCount('adj-kanban-pending', counts.pending);
        updateCount('adj-kanban-confirmed', counts.confirmed);
        updateCount('adj-kanban-deliverable', counts.deliverable);
        updateCount('adj-kanban-rejected', counts.rejected);

        // Init drag and drop
        initKanbanDragDrop();
        initKanbanClickHandlers();  // v4.1.0: Add click handlers to kanban cards
    }

    // --- Kanban Drag and Drop ---
    function initKanbanDragDrop() {
        const cards = document.querySelectorAll('.adj-kanban-card');
        const columns = document.querySelectorAll('.adj-kanban-cards');

        cards.forEach(card => {
            card.addEventListener('dragstart', (e) => {
                card.classList.add('dragging');
                e.dataTransfer.setData('text/plain', card.dataset.role);
                e.dataTransfer.effectAllowed = 'move';
            });
            card.addEventListener('dragend', () => {
                card.classList.remove('dragging');
                document.querySelectorAll('.adj-kanban-column').forEach(c => c.classList.remove('drag-over'));
            });
        });

        columns.forEach(col => {
            col.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                col.closest('.adj-kanban-column')?.classList.add('drag-over');
            });
            col.addEventListener('dragleave', () => {
                col.closest('.adj-kanban-column')?.classList.remove('drag-over');
            });
            col.addEventListener('drop', (e) => {
                e.preventDefault();
                const column = col.closest('.adj-kanban-column');
                column?.classList.remove('drag-over');
                const roleName = e.dataTransfer.getData('text/plain');
                const newStatus = column?.dataset.status;
                if (roleName && newStatus) {
                    adjudicateRole(roleName, newStatus);
                }
            });
        });
    }

    // v4.1.0: Kanban card click handlers — open source viewer on click
    function initKanbanClickHandlers() {
        const kanbanView = document.getElementById('adj-kanban-view');
        if (kanbanView && !kanbanView._kanbanClickInit) {
            kanbanView._kanbanClickInit = true;
            kanbanView.addEventListener('click', (e) => {
                const card = e.target.closest('.adj-kanban-card');
                if (!card) return;
                // Don't open source viewer if user is dragging
                if (card.classList.contains('dragging')) return;
                const roleName = card.dataset.role;
                if (roleName) {
                    openRoleSourceViewer(roleName);
                }
            });
        }
    }

    // --- Core Adjudication Action ---
    async function adjudicateRole(roleName, action, options = {}) {
        const prevStatus = getRoleStatus(AdjState.roles.find(r => r.role_name === roleName) || {});

        // Record for undo
        if (!options.skipHistory) {
            AdjHistory.push({ action: 'status', roleName, prevStatus, newStatus: action });
        }

        // Update AdjudicationState in roles.js
        if (window.TWR?.Roles?.AdjudicationState?.decisions) {
            const decisions = window.TWR.Roles.AdjudicationState.decisions;
            const existing = decisions.get(roleName) || { status: 'pending', confidence: 0.5 };
            existing.status = action;
            decisions.set(roleName, existing);
        }

        // Persist to backend
        try {
            const csrfToken = getCSRFToken();
            await fetch('/api/roles/adjudicate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({
                    role_name: roleName,
                    action: action,
                    notes: options.notes || `Adjudicated as ${action} via Roles Studio`,
                    function_tags: options.functionTags || []
                })
            });
        } catch (e) {
            console.warn('[TWR RolesTabs] Failed to persist adjudication:', e);
        }

        // v4.6.1: Update status in-place in AdjState.roles so re-render reflects changes
        const roleInArr = AdjState.roles.find(r => r.role_name === roleName);
        if (roleInArr) {
            roleInArr.status = action;
            if (action === 'rejected') roleInArr.is_active = 0;
            if (action === 'deliverable') roleInArr.is_deliverable = 1;
            if (action === 'confirmed') { roleInArr.is_active = 1; roleInArr.is_deliverable = 0; }
        }

        // Sync with Role Source Viewer if it has a sync function
        if (window.TWR?.RoleSourceViewer?.syncFromAdjudication) {
            window.TWR.RoleSourceViewer.syncFromAdjudication(roleName, action);
        }

        // Update graph visualization
        if (window.TWR?.Roles?.updateGraphWithAdjudication) {
            try { window.TWR.Roles.updateGraphWithAdjudication(); } catch(e) {}
        }

        // v4.0.3: Invalidate global adjudication cache so badges update everywhere
        if (window.AEGIS?.AdjudicationLookup) {
            AEGIS.AdjudicationLookup.invalidate();
        }

        // Re-render
        renderAdjCurrentView();
        updateAdjDashboard(AdjState.roles);

        if (!options.silent) {
            showToast('success', `"${roleName}" marked as ${action}`);
        }
    }

    // --- Render current view (list or kanban) ---
    function renderAdjCurrentView() {
        const listView = document.getElementById('adj-list-view');
        const kanbanView = document.getElementById('adj-kanban-view');
        if (AdjState.viewMode === 'kanban') {
            if (listView) listView.style.display = 'none';
            if (kanbanView) kanbanView.style.display = '';
            renderAdjKanbanView(AdjState.roles);
        } else {
            if (listView) listView.style.display = '';
            if (kanbanView) kanbanView.style.display = 'none';
            renderAdjListView(AdjState.roles);
        }
    }

    // --- Function Tag Assignment ---
    function showTagDropdown(roleName, anchorEl) {
        // Close any existing dropdown
        closeTagDropdown();
        AdjState.tagDropdownOpen = roleName;

        const cats = AdjState.functionCategories;
        if (!cats.length) {
            showToast('info', 'No function categories available');
            return;
        }

        // Build full hierarchy: top-level → children → grandchildren
        const childMap = {};
        cats.forEach(c => {
            if (c.parent_code) {
                if (!childMap[c.parent_code]) childMap[c.parent_code] = [];
                childMap[c.parent_code].push(c);
            }
        });
        const topLevel = cats.filter(c => !c.parent_code);

        let itemsHtml = '';
        topLevel.forEach(parent => {
            const pColor = parent.color || '#3b82f6';
            itemsHtml += `<div class="adj-tag-dropdown-header">${escapeHtml(parent.name)}</div>`;
            itemsHtml += `<div class="adj-tag-dropdown-item" data-code="${escapeHtml(parent.code)}" data-role="${escapeHtml(roleName)}">
                <span class="adj-tag-dot" style="background:${pColor}"></span>
                <span>${escapeHtml(parent.code)} - ${escapeHtml(parent.name)}</span>
            </div>`;
            // Children (level 2)
            (childMap[parent.code] || []).forEach(child => {
                const cColor = child.color || pColor;
                itemsHtml += `<div class="adj-tag-dropdown-item adj-tag-level-2" data-code="${escapeHtml(child.code)}" data-role="${escapeHtml(roleName)}">
                    <span class="adj-tag-dot" style="background:${cColor}"></span>
                    <span>${escapeHtml(child.code)} - ${escapeHtml(child.name)}</span>
                </div>`;
                // Grandchildren (level 3)
                (childMap[child.code] || []).forEach(grandchild => {
                    const gColor = grandchild.color || cColor;
                    itemsHtml += `<div class="adj-tag-dropdown-item adj-tag-level-3" data-code="${escapeHtml(grandchild.code)}" data-role="${escapeHtml(roleName)}">
                        <span class="adj-tag-dot" style="background:${gColor}"></span>
                        <span>${escapeHtml(grandchild.code)} - ${escapeHtml(grandchild.name)}</span>
                    </div>`;
                });
            });
        });

        const dropdown = document.createElement('div');
        dropdown.className = 'adj-tag-dropdown';
        dropdown.id = 'adj-active-tag-dropdown';
        dropdown.innerHTML = `
            <div class="adj-tag-dropdown-search">
                <input type="text" class="adj-tag-search-input" placeholder="Search tags..." autocomplete="off">
            </div>
            <div class="adj-tag-dropdown-list">${itemsHtml}</div>`;

        // Position relative to anchor
        const pillsContainer = anchorEl.closest('.adj-tag-pills');
        if (pillsContainer) {
            pillsContainer.appendChild(dropdown);
        }

        // Search filter
        const searchInput = dropdown.querySelector('.adj-tag-search-input');
        if (searchInput) {
            searchInput.focus();
            searchInput.addEventListener('input', () => {
                const q = searchInput.value.toLowerCase();
                dropdown.querySelectorAll('.adj-tag-dropdown-item, .adj-tag-dropdown-header').forEach(el => {
                    const text = el.textContent.toLowerCase();
                    el.style.display = (!q || text.includes(q)) ? '' : 'none';
                });
            });
            searchInput.addEventListener('click', (e) => e.stopPropagation());
        }

        // Click handler for items
        dropdown.addEventListener('click', async (e) => {
            const item = e.target.closest('.adj-tag-dropdown-item');
            if (!item) return;
            const code = item.dataset.code;
            const role = item.dataset.role;
            await assignFunctionTag(role, code);
            closeTagDropdown();
        });

        // Close on outside click
        setTimeout(() => {
            document.addEventListener('click', closeTagDropdownOnOutside, { once: true });
        }, 10);
    }

    function closeTagDropdown() {
        const existing = document.getElementById('adj-active-tag-dropdown');
        if (existing) existing.remove();
        AdjState.tagDropdownOpen = null;
    }

    function closeTagDropdownOnOutside(e) {
        if (!e.target.closest('.adj-tag-dropdown') && !e.target.closest('.adj-tag-add-btn')) {
            closeTagDropdown();
        }
    }

    async function assignFunctionTag(roleName, functionCode) {
        try {
            const csrfToken = getCSRFToken();
            const resp = await fetch('/api/role-function-tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ role_name: roleName, function_code: functionCode, assigned_by: 'adjudication' })
            });
            const result = await resp.json();
            if (result.success) {
                // Update local data
                const role = AdjState.roles.find(r => r.role_name === roleName);
                if (role) {
                    if (!role.function_tags) role.function_tags = [];
                    const cat = AdjState.functionCategories.find(c => c.code === functionCode);
                    role.function_tags.push({
                        code: functionCode,
                        name: cat?.name || functionCode,
                        color: cat?.color || '#3b82f6'
                    });
                }
                renderAdjCurrentView();
                showToast('success', `Tag "${functionCode}" assigned to "${roleName}"`);
            } else {
                const errMsg = typeof result.error === 'object' ? (result.error?.message || JSON.stringify(result.error)) : (result.error || 'Tag assignment failed');
                showToast('info', errMsg);
            }
        } catch (e) {
            console.warn('[TWR RolesTabs] Tag assignment error:', e);
        }
    }

    async function removeFunctionTag(roleName, tagCode) {
        try {
            // Find tag ID from role data
            const role = AdjState.roles.find(r => r.role_name === roleName);

            // Fetch tag record from API to get the ID
            const resp = await fetch(`/api/role-function-tags?role_name=${encodeURIComponent(roleName)}&function_code=${encodeURIComponent(tagCode)}`);
            const data = await resp.json();
            // API returns { success, data: { tags: [...], total } }
            const tags = data?.data?.tags || data?.data || [];
            const tagRecords = Array.isArray(tags) ? tags : [];

            if (data.success && tagRecords.length > 0) {
                const tagId = tagRecords[0].id;
                const csrfToken = getCSRFToken();
                const delResp = await fetch(`/api/role-function-tags/${tagId}`, {
                    method: 'DELETE',
                    headers: { 'X-CSRF-Token': csrfToken }
                });
                const delData = await delResp.json();

                if (delData.success !== false) {
                    // Update local data
                    if (role?.function_tags) {
                        role.function_tags = role.function_tags.filter(t => t.code !== tagCode);
                    }
                    renderAdjCurrentView();
                    showToast('success', `Tag "${tagCode}" removed from "${roleName}"`);
                } else {
                    showToast('error', delData.error || 'Failed to remove tag');
                }
            } else {
                // Tag not found in DB - just remove locally
                if (role?.function_tags) {
                    role.function_tags = role.function_tags.filter(t => t.code !== tagCode);
                }
                renderAdjCurrentView();
                showToast('info', `Tag "${tagCode}" removed from card`);
            }
        } catch (e) {
            console.warn('[TWR RolesTabs] Tag removal error:', e);
            showToast('error', 'Failed to remove tag: ' + e.message);
        }
    }

    // Remove a function tag by its database ID (fallback when code is missing)
    async function removeFunctionTagById(roleName, tagId) {
        try {
            const csrfToken = getCSRFToken();
            const delResp = await fetch(`/api/role-function-tags/${tagId}`, {
                method: 'DELETE',
                headers: { 'X-CSRF-Token': csrfToken }
            });
            const delData = await delResp.json();
            if (delData.success !== false) {
                const role = AdjState.roles.find(r => r.role_name === roleName);
                if (role?.function_tags) {
                    role.function_tags = role.function_tags.filter(t => String(t.id) !== String(tagId));
                }
                renderAdjCurrentView();
                showToast('success', `Tag removed from "${roleName}"`);
            } else {
                showToast('error', delData.error || 'Failed to remove tag');
            }
        } catch (e) {
            console.warn('[TWR RolesTabs] Tag removal by ID error:', e);
            showToast('error', 'Failed to remove tag: ' + e.message);
        }
    }

    // --- Auto-Classify ---
    async function handleAutoAdjudicate() {
        const btn = document.getElementById('btn-auto-adjudicate');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader"></i> Classifying...'; refreshIcons(); }

        try {
            const csrfToken = getCSRFToken();
            const resp = await fetch('/api/roles/auto-adjudicate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ apply: false })
            });
            const result = await resp.json();

            if (result.success) {
                const suggestions = result.suggestions.filter(s => !s.already_adjudicated && s.suggested_status !== 'pending');

                if (suggestions.length === 0) {
                    showToast('info', 'No auto-classifications available. All roles need manual review.');
                    return;
                }

                // Show confirmation modal
                showAutoClassifyModal(suggestions);
            }
        } catch (e) {
            showToast('error', 'Auto-classify failed: ' + e.message);
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="sparkles"></i> Auto-Classify'; refreshIcons(); }
        }
    }

    function showAutoClassifyModal(suggestions) {
        const overlay = document.createElement('div');
        overlay.className = 'adj-auto-overlay';
        overlay.id = 'adj-auto-overlay';

        const statusIcon = { confirmed: '&#x2705;', deliverable: '&#x1F4E6;', rejected: '&#x274C;' };
        const statusOptions = ['confirmed', 'deliverable', 'rejected'];

        // Track editable state per suggestion — ALL suggestions, no truncation
        const editState = suggestions.map((s, i) => ({
            idx: i,
            selected: true,
            role_name: s.role_name,
            original_name: s.role_name,
            status: s.suggested_status,
            reason: s.reason,
            confidence: s.confidence
        }));

        // Pagination state
        const PAGE_SIZE = 50;
        let currentPage = 0;
        let searchFilter = '';
        let statusFilter = 'all'; // 'all', 'confirmed', 'deliverable', 'rejected'

        function getFilteredIndices() {
            return editState.filter(s => {
                if (searchFilter) {
                    const q = searchFilter.toLowerCase();
                    if (!s.role_name.toLowerCase().includes(q) && !s.reason.toLowerCase().includes(q)) return false;
                }
                if (statusFilter !== 'all' && s.status !== statusFilter) return false;
                return true;
            }).map(s => s.idx);
        }

        function updateApplyCount() {
            const count = editState.filter(s => s.selected).length;
            const applyBtn = document.getElementById('adj-auto-apply');
            if (applyBtn) {
                applyBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Apply ${count} Selected`;
                applyBtn.disabled = count === 0;
            }
        }

        function renderPage() {
            const container = document.getElementById('adj-auto-results-list');
            if (!container) return;

            const filtered = getFilteredIndices();
            const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
            if (currentPage >= totalPages) currentPage = totalPages - 1;
            if (currentPage < 0) currentPage = 0;

            const start = currentPage * PAGE_SIZE;
            const pageItems = filtered.slice(start, start + PAGE_SIZE);

            container.innerHTML = pageItems.map(idx => {
                const s = editState[idx];
                return `<div class="adj-auto-item" data-idx="${idx}" style="gap:8px;align-items:center;${s.selected ? '' : 'opacity:0.4;'}">
                    <input type="checkbox" class="adj-auto-check" data-idx="${idx}" ${s.selected ? 'checked' : ''} style="flex-shrink:0;width:16px;height:16px;cursor:pointer;">
                    <span style="font-size:16px;flex-shrink:0;">${statusIcon[s.status] || ''}</span>
                    <input type="text" class="adj-auto-name-input" data-idx="${idx}" value="${escapeHtml(s.role_name)}" style="flex:1;min-width:120px;padding:3px 6px;border:1px solid var(--border-default,#ccc);border-radius:4px;font-size:13px;font-weight:500;background:var(--bg-surface,#fff);color:var(--text-primary,#333);">
                    <select class="adj-auto-status-select" data-idx="${idx}" style="padding:3px 4px;border:1px solid var(--border-default,#ccc);border-radius:4px;font-size:11px;background:var(--bg-surface,#fff);color:var(--text-primary,#333);cursor:pointer;">
                        ${statusOptions.map(opt => `<option value="${opt}" ${opt === s.status ? 'selected' : ''}>${opt.charAt(0).toUpperCase() + opt.slice(1)}</option>`).join('')}
                    </select>
                    <span style="font-size:11px;color:var(--text-muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(s.reason)}">${escapeHtml(s.reason)}</span>
                    <span style="font-size:12px;font-weight:600;flex-shrink:0;">${Math.round(s.confidence * 100)}%</span>
                </div>`;
            }).join('');

            // Update pagination info
            const pageInfo = document.getElementById('adj-auto-page-info');
            if (pageInfo) {
                const rangeStart = filtered.length > 0 ? start + 1 : 0;
                const rangeEnd = Math.min(start + PAGE_SIZE, filtered.length);
                pageInfo.textContent = `${rangeStart}-${rangeEnd} of ${filtered.length}${filtered.length !== suggestions.length ? ` (${suggestions.length} total)` : ''}`;
            }
            const prevBtn = document.getElementById('adj-auto-prev');
            const nextBtn = document.getElementById('adj-auto-next');
            if (prevBtn) prevBtn.disabled = currentPage === 0;
            if (nextBtn) nextBtn.disabled = currentPage >= totalPages - 1;

            // Update status filter counts
            const confirmedCount = editState.filter(s => s.status === 'confirmed').length;
            const deliverableCount = editState.filter(s => s.status === 'deliverable').length;
            const rejectedCount = editState.filter(s => s.status === 'rejected').length;
            const filterInfo = document.getElementById('adj-auto-filter-counts');
            if (filterInfo) {
                filterInfo.innerHTML = `
                    <button class="btn btn-sm ${statusFilter === 'all' ? 'btn-primary' : 'btn-ghost'}" data-filter="all" style="font-size:11px;padding:2px 8px;">All (${suggestions.length})</button>
                    <button class="btn btn-sm ${statusFilter === 'confirmed' ? 'btn-primary' : 'btn-ghost'}" data-filter="confirmed" style="font-size:11px;padding:2px 8px;">Confirmed (${confirmedCount})</button>
                    <button class="btn btn-sm ${statusFilter === 'deliverable' ? 'btn-primary' : 'btn-ghost'}" data-filter="deliverable" style="font-size:11px;padding:2px 8px;">Deliverable (${deliverableCount})</button>
                    <button class="btn btn-sm ${statusFilter === 'rejected' ? 'btn-primary' : 'btn-ghost'}" data-filter="rejected" style="font-size:11px;padding:2px 8px;">Rejected (${rejectedCount})</button>
                `;
            }

            updateApplyCount();
        }

        overlay.innerHTML = `<div class="adj-auto-modal" style="max-width:780px;">
            <div class="adj-auto-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                Auto-Classify Results
            </div>
            <p style="color:var(--text-secondary);font-size:13px;margin-bottom:8px;">
                Review <strong>all ${suggestions.length}</strong> classifications below. Uncheck items to exclude, edit names, or change classification.
            </p>
            <div style="display:flex;gap:8px;margin-bottom:8px;align-items:center;flex-wrap:wrap;">
                <input type="text" id="adj-auto-search" placeholder="Search roles..." style="flex:1;min-width:180px;padding:5px 10px;border:1px solid var(--border-default,#ccc);border-radius:4px;font-size:13px;background:var(--bg-surface,#fff);color:var(--text-primary,#333);">
                <button class="btn btn-sm btn-ghost" id="adj-auto-select-all">Select All Visible</button>
                <button class="btn btn-sm btn-ghost" id="adj-auto-deselect-all">Deselect All Visible</button>
            </div>
            <div id="adj-auto-filter-counts" style="display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap;"></div>
            <div class="adj-auto-results" style="max-height:50vh;">
                <div id="adj-auto-results-list"></div>
            </div>
            <div style="display:flex;align-items:center;justify-content:center;gap:12px;padding:8px 0 4px;">
                <button class="btn btn-sm btn-ghost" id="adj-auto-prev" disabled>&laquo; Previous</button>
                <span id="adj-auto-page-info" style="font-size:12px;color:var(--text-secondary);min-width:120px;text-align:center;"></span>
                <button class="btn btn-sm btn-ghost" id="adj-auto-next">Next &raquo;</button>
            </div>
            <div class="adj-auto-actions">
                <button class="btn btn-ghost" id="adj-auto-cancel">Cancel</button>
                <button class="btn btn-success" id="adj-auto-apply">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                    Apply ${suggestions.length} Selected
                </button>
            </div>
        </div>`;

        document.body.appendChild(overlay);

        // Render initial page
        renderPage();

        // Event delegation for dynamic content inside results list
        const resultsList = document.getElementById('adj-auto-results-list');
        if (resultsList) {
            resultsList.addEventListener('change', (e) => {
                const idx = parseInt(e.target.dataset.idx);
                if (e.target.classList.contains('adj-auto-check')) {
                    if (editState[idx]) editState[idx].selected = e.target.checked;
                    const row = e.target.closest('.adj-auto-item');
                    if (row) row.style.opacity = e.target.checked ? '1' : '0.4';
                    updateApplyCount();
                } else if (e.target.classList.contains('adj-auto-name-input')) {
                    if (editState[idx]) editState[idx].role_name = e.target.value.trim() || editState[idx].original_name;
                } else if (e.target.classList.contains('adj-auto-status-select')) {
                    if (editState[idx]) editState[idx].status = e.target.value;
                    const row = e.target.closest('.adj-auto-item');
                    const iconSpan = row?.querySelector('span:not(:first-child)');
                    if (iconSpan) iconSpan.innerHTML = statusIcon[e.target.value] || '';
                }
            });
            // Name input change on blur
            resultsList.addEventListener('focusout', (e) => {
                if (e.target.classList.contains('adj-auto-name-input')) {
                    const idx = parseInt(e.target.dataset.idx);
                    if (editState[idx]) editState[idx].role_name = e.target.value.trim() || editState[idx].original_name;
                }
            });
        }

        // Search filter
        const searchInput = document.getElementById('adj-auto-search');
        let searchTimeout;
        searchInput?.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchFilter = searchInput.value.trim();
                currentPage = 0;
                renderPage();
            }, 200);
        });

        // Status filter delegation
        document.getElementById('adj-auto-filter-counts')?.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-filter]');
            if (!btn) return;
            statusFilter = btn.dataset.filter;
            currentPage = 0;
            renderPage();
        });

        // Pagination
        document.getElementById('adj-auto-prev')?.addEventListener('click', () => {
            if (currentPage > 0) { currentPage--; renderPage(); }
        });
        document.getElementById('adj-auto-next')?.addEventListener('click', () => {
            currentPage++;
            renderPage();
        });

        // Select / Deselect all visible (applies to ALL filtered items, not just current page)
        document.getElementById('adj-auto-select-all')?.addEventListener('click', () => {
            const filtered = getFilteredIndices();
            filtered.forEach(idx => { editState[idx].selected = true; });
            renderPage();
        });
        document.getElementById('adj-auto-deselect-all')?.addEventListener('click', () => {
            const filtered = getFilteredIndices();
            filtered.forEach(idx => { editState[idx].selected = false; });
            renderPage();
        });

        document.getElementById('adj-auto-cancel')?.addEventListener('click', () => overlay.remove());
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });

        document.getElementById('adj-auto-apply')?.addEventListener('click', async () => {
            const applyBtn = document.getElementById('adj-auto-apply');
            if (applyBtn) { applyBtn.disabled = true; applyBtn.textContent = 'Applying...'; }

            const selected = editState.filter(s => s.selected);

            // Handle renames first
            const renames = selected.filter(s => s.role_name !== s.original_name);
            for (const r of renames) {
                try {
                    const csrfToken = getCSRFToken();
                    await fetch('/api/roles/rename', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                        body: JSON.stringify({ old_name: r.original_name, new_name: r.role_name })
                    });
                } catch (e) {
                    console.warn('[TWR] Rename failed for', r.original_name, e);
                }
            }

            const decisions = selected.map(s => ({
                role_name: s.role_name,
                action: s.status,
                notes: `Auto-classified: ${s.reason} (${Math.round(s.confidence * 100)}%)`
            }));

            try {
                const csrfToken = getCSRFToken();
                await fetch('/api/roles/adjudicate/batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify({ decisions })
                });

                // Update local state
                selected.forEach(s => {
                    if (window.TWR?.Roles?.AdjudicationState?.decisions) {
                        const d = window.TWR.Roles.AdjudicationState.decisions.get(s.role_name) || {};
                        d.status = s.status;
                        window.TWR.Roles.AdjudicationState.decisions.set(s.role_name, d);
                    }
                    // v4.6.1: Update AdjState.roles in-place for status changes
                    const roleInArr = AdjState.roles.find(r => r.role_name === s.original_name || r.role_name === s.role_name);
                    if (roleInArr) {
                        roleInArr.status = s.status;
                        if (s.role_name !== s.original_name) {
                            roleInArr.role_name = s.role_name;
                        }
                        if (s.status === 'rejected') roleInArr.is_active = 0;
                        if (s.status === 'deliverable') roleInArr.is_deliverable = 1;
                        if (s.status === 'confirmed') { roleInArr.is_active = 1; roleInArr.is_deliverable = 0; }
                    }
                });

                // v4.6.1: If renames occurred, also update the decisions Map with new names
                renames.forEach(r => {
                    if (window.TWR?.Roles?.AdjudicationState?.decisions) {
                        const decisions = window.TWR.Roles.AdjudicationState.decisions;
                        const oldDecision = decisions.get(r.original_name);
                        if (oldDecision) {
                            decisions.delete(r.original_name);
                            decisions.set(r.role_name, oldDecision);
                        }
                    }
                });

                overlay.remove();
                renderAdjCurrentView();
                updateAdjDashboard(AdjState.roles);
                if (window.AEGIS?.AdjudicationLookup) AEGIS.AdjudicationLookup.invalidate();
                showToast('success', `Applied ${selected.length} classifications${renames.length ? ` (${renames.length} renamed)` : ''}`);
            } catch (e) {
                showToast('error', 'Batch apply failed: ' + e.message);
                if (applyBtn) { applyBtn.disabled = false; applyBtn.textContent = 'Retry'; }
            }
        });
    }

    // --- Keyboard Navigation ---
    function initAdjKeyboard() {
        // Use document-level listener since the adjudication section div is not focusable
        if (document._adjKeyboardInit) return;
        document._adjKeyboardInit = true;

        document.addEventListener('keydown', (e) => {
            // Only handle when Roles modal is open and adjudication tab is visible
            const rolesModal = document.getElementById('modal-roles');
            if (!rolesModal || !rolesModal.classList.contains('active')) return;
            const adjSection = document.getElementById('roles-adjudication');
            if (!adjSection || !adjSection.classList.contains('active')) return;
            // Don't intercept when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
            // Don't intercept when a modal/overlay is open (Source Viewer, auto-classify, etc.)
            if (document.querySelector('.rsv-overlay[style*="flex"], .adj-auto-classify-overlay, .modal-overlay[style*="flex"]')) return;

            const cards = document.querySelectorAll('.adj-role-card');
            if (!cards.length) return;

            switch(e.key) {
                case 'ArrowDown':
                case 'j':
                    e.preventDefault();
                    AdjState.focusIndex = Math.min(AdjState.focusIndex + 1, cards.length - 1);
                    updateFocusedCard(cards);
                    break;
                case 'ArrowUp':
                case 'k':
                    e.preventDefault();
                    AdjState.focusIndex = Math.max(AdjState.focusIndex - 1, 0);
                    updateFocusedCard(cards);
                    break;
                case 'c':
                case 'C':
                    if (AdjState.focusIndex >= 0 && AdjState.focusIndex < cards.length) {
                        e.preventDefault();
                        adjudicateRole(cards[AdjState.focusIndex].dataset.role, 'confirmed');
                    }
                    break;
                case 'd':
                    if (AdjState.focusIndex >= 0 && AdjState.focusIndex < cards.length) {
                        e.preventDefault();
                        adjudicateRole(cards[AdjState.focusIndex].dataset.role, 'deliverable');
                    }
                    break;
                case 'r':
                    if (AdjState.focusIndex >= 0 && AdjState.focusIndex < cards.length) {
                        e.preventDefault();
                        adjudicateRole(cards[AdjState.focusIndex].dataset.role, 'rejected');
                    }
                    break;
                case ' ':
                    if (AdjState.focusIndex >= 0 && AdjState.focusIndex < cards.length) {
                        e.preventDefault();
                        const cb = cards[AdjState.focusIndex].querySelector('.adj-item-checkbox');
                        if (cb) { cb.checked = !cb.checked; toggleRoleSelection(cards[AdjState.focusIndex]); }
                    }
                    break;
                case 'v':
                case 'V':
                    if (AdjState.focusIndex >= 0 && AdjState.focusIndex < cards.length) {
                        e.preventDefault();
                        openRoleSourceViewer(cards[AdjState.focusIndex].dataset.role);
                    }
                    break;
                case 's':
                case 'S':
                    if (!e.ctrlKey && !e.metaKey && AdjState.focusIndex >= 0 && AdjState.focusIndex < cards.length) {
                        e.preventDefault();
                        showRoleStatements(cards[AdjState.focusIndex].dataset.role);
                    }
                    break;
                case 'z':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        if (e.shiftKey) handleRedo(); else handleUndo();
                    }
                    break;
                case 'y':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        handleRedo();
                    }
                    break;
                case 'a':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        const selectAll = document.getElementById('adj-select-all');
                        if (selectAll) { selectAll.checked = !selectAll.checked; selectAll.dispatchEvent(new Event('change')); }
                    }
                    break;
            }
        });
    }

    let _adjLastNavTime = 0;
    function updateFocusedCard(cards) {
        cards.forEach((c, i) => {
            c.classList.toggle('adj-focused', i === AdjState.focusIndex);
        });
        if (AdjState.focusIndex >= 0 && cards[AdjState.focusIndex]) {
            // Use instant scroll when navigating rapidly (< 200ms between keypresses)
            const now = Date.now();
            const isRapid = (now - _adjLastNavTime) < 200;
            _adjLastNavTime = now;
            cards[AdjState.focusIndex].scrollIntoView({ block: 'nearest', behavior: isRapid ? 'auto' : 'smooth' });
        }
    }

    function openRoleSourceViewer(roleName) {
        if (window.TWR?.RoleSourceViewer?.open) {
            window.TWR.RoleSourceViewer.open(roleName);
        }
    }

    // --- v4.6.0: Role Statements Panel ---
    const GENERIC_ROLES = ['personnel', 'staff', 'employee', 'user', 'operator', 'worker', 'individual', 'person', 'member', 'team'];

    function showRoleStatements(roleName) {
        // Remove any existing panel
        document.getElementById('role-stmt-overlay')?.remove();

        const overlay = document.createElement('div');
        overlay.id = 'role-stmt-overlay';
        overlay.className = 'role-stmt-overlay';
        overlay.innerHTML = `
            <div class="role-stmt-panel">
                <div class="role-stmt-header">
                    <div class="role-stmt-title-row">
                        <h3 class="role-stmt-title">
                            <i data-lucide="file-text" style="width:20px;height:20px;"></i>
                            Statements for "${escapeHtml(roleName)}"
                        </h3>
                        <button class="role-stmt-close" title="Close (Esc)">&times;</button>
                    </div>
                    <div class="role-stmt-toolbar" id="role-stmt-toolbar"></div>
                </div>
                <div class="role-stmt-body" id="role-stmt-body">
                    <div class="role-stmt-loading">Loading statements...</div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // Close handlers
        overlay.querySelector('.role-stmt-close').addEventListener('click', () => overlay.remove());
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.remove();
        });
        const escHandler = (e) => {
            if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', escHandler); }
        };
        document.addEventListener('keydown', escHandler);

        // Fetch statements
        _fetchRoleStatements(roleName, overlay);
    }

    async function _fetchRoleStatements(roleName, overlay) {
        const body = overlay.querySelector('#role-stmt-body');
        const toolbar = overlay.querySelector('#role-stmt-toolbar');
        try {
            const encodedName = encodeURIComponent(roleName);
            const resp = await fetch(`/api/roles/${encodedName}/statements`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const json = await resp.json();
            if (!json.success) throw new Error(json.error || 'Failed to load');
            const statements = json.data || [];
            _renderRoleStatementsUI(roleName, statements, body, toolbar, overlay);
        } catch (err) {
            body.innerHTML = `<div class="role-stmt-empty">Failed to load statements: ${escapeHtml(err.message)}</div>`;
        }
    }

    function _renderRoleStatementsUI(roleName, statements, body, toolbar, overlay) {
        const isGeneric = GENERIC_ROLES.includes(roleName.toLowerCase().trim());
        const selectedIds = new Set();

        // Build role list for reassign dropdown (from AdjState if available)
        const roleNames = (AdjState.roles || []).map(r => r.role_name).filter(n => n.toLowerCase() !== roleName.toLowerCase()).sort();

        // Group by document
        const groups = {};
        statements.forEach(s => {
            const doc = s.document_name || 'Unknown Document';
            if (!groups[doc]) groups[doc] = [];
            groups[doc].push(s);
        });

        // Toolbar
        toolbar.innerHTML = `
            <div class="role-stmt-stats">
                <span><strong>${statements.length}</strong> statement${statements.length !== 1 ? 's' : ''}</span>
                <span><strong>${Object.keys(groups).length}</strong> document${Object.keys(groups).length !== 1 ? 's' : ''}</span>
            </div>
            <div class="role-stmt-actions">
                <label class="role-stmt-select-all-label">
                    <input type="checkbox" id="role-stmt-select-all"> Select All
                </label>
                <select id="role-stmt-reassign-target" class="role-stmt-reassign-select" disabled>
                    <option value="">Reassign to...</option>
                    ${roleNames.map(n => `<option value="${escapeHtml(n)}">${escapeHtml(n)}</option>`).join('')}
                </select>
                <button id="role-stmt-reassign-btn" class="role-stmt-btn role-stmt-btn-primary" disabled>Reassign Selected</button>
                <button id="role-stmt-remove-btn" class="role-stmt-btn role-stmt-btn-danger" disabled>Remove Role</button>
            </div>
        `;

        // Body content
        let html = '';
        if (isGeneric) {
            html += `<div class="role-stmt-warning">
                <i data-lucide="alert-triangle" style="width:16px;height:16px;flex-shrink:0;"></i>
                <span><strong>"${escapeHtml(roleName)}"</strong> is a generic role name. Statements assigned to generic roles are often auto-extracted and may need to be reassigned to more specific roles.</span>
            </div>`;
        }

        if (statements.length === 0) {
            html += '<div class="role-stmt-empty">No statements found for this role.</div>';
        } else {
            for (const [docName, stmts] of Object.entries(groups)) {
                html += `<div class="role-stmt-group">
                    <div class="role-stmt-group-header">
                        <i data-lucide="file" style="width:14px;height:14px;"></i>
                        <span class="role-stmt-group-name">${escapeHtml(docName)}</span>
                        <span class="role-stmt-group-count">${stmts.length}</span>
                    </div>
                    <div class="role-stmt-group-items">`;
                stmts.forEach(s => {
                    const directiveClass = (s.directive || '').toLowerCase().replace(/\s+/g, '-');
                    const reviewBadge = _getReviewBadgeHTML(s.review_status);
                    html += `<div class="role-stmt-item" data-stmt-id="${s.id}">
                        <input type="checkbox" class="role-stmt-cb" data-stmt-id="${s.id}">
                        <span class="role-stmt-num">${escapeHtml(s.number || '#')}</span>
                        <span class="sfh-directive-chip sfh-dir-${directiveClass}">${escapeHtml(s.directive || '—')}</span>
                        <span class="role-stmt-desc">${escapeHtml(s.description?.slice(0, 200) || '(no description)')}</span>
                        ${reviewBadge}
                    </div>`;
                });
                html += `</div></div>`;
            }
        }
        body.innerHTML = html;
        if (typeof lucide !== 'undefined') lucide.createIcons();

        // --- Event wiring ---
        const selectAll = toolbar.querySelector('#role-stmt-select-all');
        const reassignSelect = toolbar.querySelector('#role-stmt-reassign-target');
        const reassignBtn = toolbar.querySelector('#role-stmt-reassign-btn');
        const removeBtn = toolbar.querySelector('#role-stmt-remove-btn');

        function updateToolbarState() {
            const hasSelection = selectedIds.size > 0;
            reassignSelect.disabled = !hasSelection;
            reassignBtn.disabled = !hasSelection || !reassignSelect.value;
            removeBtn.disabled = !hasSelection;
        }

        // Checkbox delegation
        body.addEventListener('change', (e) => {
            if (!e.target.classList.contains('role-stmt-cb')) return;
            const id = parseInt(e.target.dataset.stmtId);
            if (e.target.checked) selectedIds.add(id);
            else selectedIds.delete(id);
            updateToolbarState();
        });

        selectAll?.addEventListener('change', () => {
            const cbs = body.querySelectorAll('.role-stmt-cb');
            cbs.forEach(cb => {
                cb.checked = selectAll.checked;
                const id = parseInt(cb.dataset.stmtId);
                if (selectAll.checked) selectedIds.add(id);
                else selectedIds.delete(id);
            });
            updateToolbarState();
        });

        reassignSelect?.addEventListener('change', updateToolbarState);

        // Reassign action
        reassignBtn?.addEventListener('click', async () => {
            const newRole = reassignSelect.value;
            if (!newRole || selectedIds.size === 0) return;
            const count = selectedIds.size;
            if (!confirm(`Reassign ${count} statement${count !== 1 ? 's' : ''} from "${roleName}" to "${newRole}"?`)) return;
            reassignBtn.disabled = true;
            reassignBtn.textContent = 'Reassigning...';
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
                const resp = await fetch(`/api/roles/${encodeURIComponent(roleName)}/statements/bulk-reassign`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify({ statement_ids: Array.from(selectedIds), new_role: newRole })
                });
                const json = await resp.json();
                if (json.success) {
                    showToast('success', `Reassigned ${json.updated} statement${json.updated !== 1 ? 's' : ''} to "${newRole}"`);
                    _fetchRoleStatements(roleName, overlay); // Refresh
                } else {
                    showToast('error', json.error || 'Reassign failed');
                }
            } catch (err) {
                showToast('error', 'Reassign error: ' + err.message);
            }
            reassignBtn.textContent = 'Reassign Selected';
            updateToolbarState();
        });

        // Remove role (reassign to empty string)
        removeBtn?.addEventListener('click', async () => {
            const count = selectedIds.size;
            if (!confirm(`Remove role assignment from ${count} statement${count !== 1 ? 's' : ''}? They will become unassigned.`)) return;
            removeBtn.disabled = true;
            removeBtn.textContent = 'Removing...';
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || window.CSRF_TOKEN || '';
                const resp = await fetch(`/api/roles/${encodeURIComponent(roleName)}/statements/bulk-reassign`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                    body: JSON.stringify({ statement_ids: Array.from(selectedIds), new_role: '' })
                });
                const json = await resp.json();
                if (json.success) {
                    showToast('success', `Removed role from ${json.updated} statement${json.updated !== 1 ? 's' : ''}`);
                    _fetchRoleStatements(roleName, overlay);
                } else {
                    showToast('error', json.error || 'Remove failed');
                }
            } catch (err) {
                showToast('error', 'Remove error: ' + err.message);
            }
            removeBtn.textContent = 'Remove Role';
            updateToolbarState();
        });
    }

    function _getReviewBadgeHTML(status) {
        if (!status || status === 'pending') return '<span class="stmt-badge stmt-pending">Pending</span>';
        if (status === 'reviewed') return '<span class="stmt-badge stmt-reviewed">Reviewed</span>';
        if (status === 'rejected') return '<span class="stmt-badge stmt-rejected">Rejected</span>';
        if (status === 'unchanged') return '<span class="stmt-badge stmt-unchanged">Unchanged</span>';
        return '';
    }

    // --- Undo/Redo Handlers ---
    function handleUndo() {
        const entry = AdjHistory.undo();
        if (!entry) return;
        if (entry.action === 'status') {
            adjudicateRole(entry.roleName, entry.prevStatus, { skipHistory: true, silent: true });
            showToast('info', `Undo: "${entry.roleName}" back to ${entry.prevStatus}`);
        }
    }

    function handleRedo() {
        const entry = AdjHistory.redo();
        if (!entry) return;
        if (entry.action === 'status') {
            adjudicateRole(entry.roleName, entry.newStatus, { skipHistory: true, silent: true });
            showToast('info', `Redo: "${entry.roleName}" to ${entry.newStatus}`);
        }
    }

    // --- Selection Management ---
    function toggleRoleSelection(cardEl) {
        const roleName = cardEl.dataset.role;
        const cb = cardEl.querySelector('.adj-item-checkbox');
        if (cb?.checked) {
            AdjState.selectedRoles.add(roleName);
        } else {
            AdjState.selectedRoles.delete(roleName);
        }
        updateBulkVisibility();
    }

    function updateBulkVisibility() {
        const count = AdjState.selectedRoles.size;
        const bulkEl = document.getElementById('adj-bulk-actions');
        const countEl = document.getElementById('adj-selected-count');
        if (bulkEl) bulkEl.style.display = count > 0 ? 'flex' : 'none';
        if (countEl) countEl.textContent = count;
    }

    async function bulkAdjudicateSelected(action) {
        const roles = [...AdjState.selectedRoles];
        if (!roles.length) return;

        const decisions = roles.map(r => ({ role_name: r, action }));

        try {
            const csrfToken = getCSRFToken();
            await fetch('/api/roles/adjudicate/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: JSON.stringify({ decisions })
            });

            // Update local state
            roles.forEach(roleName => {
                if (window.TWR?.Roles?.AdjudicationState?.decisions) {
                    const d = window.TWR.Roles.AdjudicationState.decisions.get(roleName) || {};
                    d.status = action;
                    window.TWR.Roles.AdjudicationState.decisions.set(roleName, d);
                }
            });

            AdjState.selectedRoles.clear();
            const selectAll = document.getElementById('adj-select-all');
            if (selectAll) selectAll.checked = false;

            renderAdjCurrentView();
            updateAdjDashboard(AdjState.roles);
            updateBulkVisibility();
            showToast('success', `${roles.length} roles marked as ${action}`);
        } catch (e) {
            showToast('error', 'Batch operation failed');
        }
    }

    // --- Initialize all adjudication controls (v4.0.3 overhaul) ---
    function initAdjudicationControls() {
        console.log('[TWR Adj v4.0.3] Initializing adjudication controls...');

        // Filter dropdown
        const filterSelect = document.getElementById('adj-filter');
        if (filterSelect && !filterSelect._adjV4Init) {
            filterSelect._adjV4Init = true;
            filterSelect.addEventListener('change', () => {
                AdjState.activeFilter = filterSelect.value;
                renderAdjCurrentView();
            });
        }

        // Search input with debounce - filters roles as you type
        const searchInput = document.getElementById('adj-search');
        if (searchInput && !searchInput._adjV4Init) {
            searchInput._adjV4Init = true;
            let searchTimer = null;
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimer);
                searchTimer = setTimeout(() => {
                    const val = searchInput.value.trim().toLowerCase();
                    AdjState.searchText = val;
                    // Auto-switch to "All Items" when user types a search query for broader results
                    if (val && AdjState.activeFilter !== 'all') {
                        AdjState._preSearchFilter = AdjState.activeFilter;
                        AdjState.activeFilter = 'all';
                        const filterSelect = document.getElementById('adj-filter');
                        if (filterSelect) filterSelect.value = 'all';
                    } else if (!val && AdjState._preSearchFilter) {
                        // Restore previous filter when search is cleared
                        AdjState.activeFilter = AdjState._preSearchFilter;
                        const filterSelect = document.getElementById('adj-filter');
                        if (filterSelect) filterSelect.value = AdjState._preSearchFilter;
                        delete AdjState._preSearchFilter;
                    }
                    renderAdjCurrentView();
                }, 200);
            });
            // Clear search on Escape key
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    e.stopPropagation();
                    searchInput.value = '';
                    AdjState.searchText = '';
                    // Restore previous filter
                    if (AdjState._preSearchFilter) {
                        AdjState.activeFilter = AdjState._preSearchFilter;
                        const filterSelect = document.getElementById('adj-filter');
                        if (filterSelect) filterSelect.value = AdjState._preSearchFilter;
                        delete AdjState._preSearchFilter;
                    }
                    renderAdjCurrentView();
                }
            });
        }

        // Select All checkbox
        const selectAllCheckbox = document.getElementById('adj-select-all');
        if (selectAllCheckbox && !selectAllCheckbox._adjV4Init) {
            selectAllCheckbox._adjV4Init = true;
            selectAllCheckbox.addEventListener('change', () => {
                const cards = document.querySelectorAll('.adj-role-card:not([style*="display: none"])');
                cards.forEach(card => {
                    const roleName = card.dataset.role;
                    const cb = card.querySelector('.adj-item-checkbox');
                    if (selectAllCheckbox.checked) {
                        AdjState.selectedRoles.add(roleName);
                        if (cb) cb.checked = true;
                    } else {
                        AdjState.selectedRoles.delete(roleName);
                        if (cb) cb.checked = false;
                    }
                });
                updateBulkVisibility();
            });
        }

        // View toggle buttons
        const viewBtns = document.querySelectorAll('.adj-view-btn');
        viewBtns.forEach(btn => {
            if (btn._adjV4Init) return;
            btn._adjV4Init = true;
            btn.addEventListener('click', () => {
                const newView = btn.dataset.view;
                AdjState.viewMode = newView;
                localStorage.setItem('adj-view-mode', newView);
                viewBtns.forEach(b => b.classList.toggle('active', b.dataset.view === newView));
                renderAdjCurrentView();
            });
        });

        // Auto-classify button
        const autoBtn = document.getElementById('btn-auto-adjudicate');
        if (autoBtn && !autoBtn._adjV4Init) {
            autoBtn._adjV4Init = true;
            autoBtn.addEventListener('click', handleAutoAdjudicate);
        }

        // Undo/Redo buttons
        const undoBtn = document.getElementById('btn-undo-adj');
        const redoBtn = document.getElementById('btn-redo-adj');
        if (undoBtn && !undoBtn._adjV4Init) {
            undoBtn._adjV4Init = true;
            undoBtn.addEventListener('click', handleUndo);
        }
        if (redoBtn && !redoBtn._adjV4Init) {
            redoBtn._adjV4Init = true;
            redoBtn.addEventListener('click', handleRedo);
        }

        // Export dropdown button
        const exportBtn = document.getElementById('btn-export-adjudication');
        if (exportBtn && !exportBtn._adjV4Init) {
            exportBtn._adjV4Init = true;
            exportBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const menu = document.getElementById('adj-export-menu');
                if (menu) {
                    const isVisible = menu.style.display !== 'none';
                    // Close all dropdowns first
                    closeAllAdjDropdowns();
                    if (!isVisible) menu.style.display = 'block';
                }
            });
        }

        // Export menu items
        const exportMenu = document.getElementById('adj-export-menu');
        if (exportMenu && !exportMenu._adjV4Init) {
            exportMenu._adjV4Init = true;
            exportMenu.addEventListener('click', (e) => {
                const item = e.target.closest('.adj-export-item');
                if (!item) return;
                const action = item.dataset.action;
                closeAllAdjDropdowns();
                if (action === 'csv') handleExportCSV();
                else if (action === 'html') handleExportHTML();
                else if (action === 'pdf') handleExportPDF();
                else if (action === 'import') handleImportDecisions();
            });
        }

        // Import file input
        const importFileInput = document.getElementById('adj-import-file');
        if (importFileInput && !importFileInput._adjV4Init) {
            importFileInput._adjV4Init = true;
            importFileInput.addEventListener('change', handleImportFileSelected);
        }

        // Share dropdown button
        const shareBtn = document.getElementById('btn-share-adjudication');
        if (shareBtn && !shareBtn._adjV4Init) {
            shareBtn._adjV4Init = true;
            shareBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const menu = document.getElementById('adj-share-menu');
                if (menu) {
                    const isVisible = menu.style.display !== 'none';
                    closeAllAdjDropdowns();
                    if (!isVisible) menu.style.display = 'block';
                }
            });
        }

        // Share menu items
        const shareMenu = document.getElementById('adj-share-menu');
        if (shareMenu && !shareMenu._adjV4Init) {
            shareMenu._adjV4Init = true;
            shareMenu.addEventListener('click', (e) => {
                const item = e.target.closest('.adj-share-item');
                if (!item) return;
                const action = item.dataset.action;
                closeAllAdjDropdowns();
                if (action === 'shared-folder') handleShareToFolder();
                else if (action === 'email-package') handleShareEmailPackage();
            });
        }

        // Close dropdowns on outside click
        if (!document._adjDropdownClose) {
            document._adjDropdownClose = true;
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.adj-export-dropdown') && !e.target.closest('.adj-share-dropdown')) {
                    closeAllAdjDropdowns();
                }
            });
        }

        // Settings: Import Package button
        const importPkgBtn = document.getElementById('btn-import-roles-package');
        if (importPkgBtn && !importPkgBtn._adjV4Init) {
            importPkgBtn._adjV4Init = true;
            importPkgBtn.addEventListener('click', () => {
                const input = document.getElementById('import-roles-package');
                if (input) input.click();
            });
        }
        const importPkgInput = document.getElementById('import-roles-package');
        if (importPkgInput && !importPkgInput._adjV4Init) {
            importPkgInput._adjV4Init = true;
            importPkgInput.addEventListener('change', handleImportPackageFile);
        }

        // Bulk action buttons
        const bulkConfirmBtn = document.getElementById('adj-bulk-confirm');
        const bulkDeliverableBtn = document.getElementById('adj-bulk-deliverable');
        const bulkRejectBtn = document.getElementById('adj-bulk-reject');
        if (bulkConfirmBtn && !bulkConfirmBtn._adjV4Init) {
            bulkConfirmBtn._adjV4Init = true;
            bulkConfirmBtn.addEventListener('click', () => bulkAdjudicateSelected('confirmed'));
        }
        if (bulkDeliverableBtn && !bulkDeliverableBtn._adjV4Init) {
            bulkDeliverableBtn._adjV4Init = true;
            bulkDeliverableBtn.addEventListener('click', () => bulkAdjudicateSelected('deliverable'));
        }
        if (bulkRejectBtn && !bulkRejectBtn._adjV4Init) {
            bulkRejectBtn._adjV4Init = true;
            bulkRejectBtn.addEventListener('click', () => bulkAdjudicateSelected('rejected'));
        }

        // Stat card click-to-filter
        const statCards = document.querySelectorAll('.adj-stat-card[data-filter]');
        statCards.forEach(card => {
            if (card._adjV4Init) return;
            card._adjV4Init = true;
            card.addEventListener('click', () => {
                const filterVal = card.dataset.filter;
                const filterEl = document.getElementById('adj-filter');
                if (filterEl) {
                    filterEl.value = filterVal;
                    AdjState.activeFilter = filterVal;
                    renderAdjCurrentView();
                }
                // Highlight active stat card
                statCards.forEach(c => c.classList.remove('adj-stat-active'));
                card.classList.add('adj-stat-active');
            });
        });

        // Save & Apply button
        const saveBtn = document.getElementById('btn-save-adjudication');
        if (saveBtn && !saveBtn._adjV4Init) {
            saveBtn._adjV4Init = true;
            saveBtn.addEventListener('click', async () => {
                const decisions = [];
                if (window.TWR?.Roles?.AdjudicationState?.decisions) {
                    window.TWR.Roles.AdjudicationState.decisions.forEach((statusOrObj, roleName) => {
                        const action = typeof statusOrObj === 'string' ? statusOrObj : statusOrObj.status;
                        if (action && action !== 'pending') {
                            decisions.push({ role_name: roleName, action: action });
                        }
                    });
                }
                if (decisions.length === 0) {
                    showToast('info', 'No adjudication changes to save');
                    return;
                }
                try {
                    const csrfToken = getCSRFToken();
                    const resp = await fetch('/api/roles/adjudicate/batch', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                        body: JSON.stringify({ decisions })
                    });
                    const result = await resp.json();
                    showToast('success', `Saved ${result.processed || decisions.length} adjudication decisions`);
                } catch (e) {
                    showToast('error', 'Failed to save adjudication decisions');
                }
            });
        }

        // Reset button
        const resetBtn = document.getElementById('btn-reset-adjudication');
        if (resetBtn && !resetBtn._adjV4Init) {
            resetBtn._adjV4Init = true;
            resetBtn.addEventListener('click', () => {
                AdjHistory.stack = [];
                AdjHistory.position = -1;
                AdjHistory._updateButtons();
                AdjState.selectedRoles.clear();
                AdjState.focusIndex = -1;
                if (window.TWR?.Roles?.AdjudicationState?.decisions) {
                    window.TWR.Roles.AdjudicationState.decisions.clear();
                }
                renderAdjudication();
                showToast('info', 'Adjudication reset');
            });
        }

        // Event delegation on adjudication-list for card interactions
        const container = document.getElementById('adjudication-list');
        if (container && !container._adjV4ClickInit) {
            container._adjV4ClickInit = true;
            container.addEventListener('click', (e) => {
                const card = e.target.closest('.adj-role-card');
                if (!card) return;
                const roleName = card.dataset.role;

                // Checkbox (div.adj-card-checkbox or input.adj-item-checkbox inside it)
                if (e.target.closest('.adj-card-checkbox')) {
                    toggleRoleSelection(card);
                    return;
                }

                // Action buttons (classes: adj-btn-confirm, adj-btn-deliverable, adj-btn-reject, adj-btn-view)
                if (e.target.closest('.adj-btn-confirm')) {
                    adjudicateRole(roleName, 'confirmed');
                    return;
                }
                if (e.target.closest('.adj-btn-deliverable')) {
                    adjudicateRole(roleName, 'deliverable');
                    return;
                }
                if (e.target.closest('.adj-btn-reject')) {
                    adjudicateRole(roleName, 'rejected');
                    return;
                }
                if (e.target.closest('.adj-btn-view')) {
                    openRoleSourceViewer(roleName);
                    return;
                }
                if (e.target.closest('.adj-btn-statements')) {
                    showRoleStatements(roleName);
                    return;
                }

                // Role name click → open source viewer
                if (e.target.closest('.adj-card-name')) {
                    openRoleSourceViewer(roleName);
                    return;
                }

                // Add tag button
                if (e.target.closest('.adj-tag-add-btn')) {
                    const anchor = e.target.closest('.adj-tag-add-btn');
                    showTagDropdown(roleName, anchor);
                    return;
                }

                // Remove tag button
                if (e.target.closest('.adj-tag-remove')) {
                    const removeBtn = e.target.closest('.adj-tag-remove');
                    const tagCode = removeBtn?.dataset.code;
                    const tagId = removeBtn?.dataset.tagId;
                    if (tagCode) {
                        removeFunctionTag(roleName, tagCode);
                    } else if (tagId) {
                        // Fallback: remove by tag ID directly
                        removeFunctionTagById(roleName, tagId);
                    } else {
                        // Last resort: remove from local data only
                        const role = AdjState.roles.find(r => r.role_name === roleName);
                        if (role?.function_tags) {
                            const idx = Array.from(card.querySelectorAll('.adj-tag-remove')).indexOf(removeBtn);
                            if (idx >= 0 && idx < role.function_tags.length) {
                                role.function_tags.splice(idx, 1);
                                renderAdjCurrentView();
                                showToast('info', 'Tag removed from card');
                            }
                        }
                    }
                    return;
                }

                // Context expand toggle (v4.1.0: fixed class name to match rendered HTML)
                if (e.target.closest('.adj-card-context-toggle')) {
                    const contextEl = card.querySelector('.adj-card-context-expanded');
                    const toggleEl = e.target.closest('.adj-card-context-toggle');
                    if (contextEl) {
                        const expanded = contextEl.style.display !== 'none';
                        contextEl.style.display = expanded ? 'none' : 'block';
                        if (toggleEl) {
                            toggleEl.innerHTML = expanded
                                ? '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg> Show more'
                                : '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"/></svg> Show less';
                        }
                    }
                    return;
                }

                // v4.1.0: Fallback — clicking anywhere else on card body opens source viewer
                openRoleSourceViewer(roleName);
            }, true);
        }

        // Initialize keyboard navigation
        initAdjKeyboard();

        console.log('[TWR Adj v4.0.3] Controls initialized');
    }

    // ===== v4.0.3: Export/Import/Share Helper Functions =====

    function closeAllAdjDropdowns() {
        const menus = ['adj-export-menu', 'adj-share-menu'];
        menus.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    }

    function handleExportCSV() {
        const data = AdjState.roles.map(r => ({
            role_name: r.role_name,
            status: getRoleStatus(r),
            category: r.category || 'Role',
            confidence: getRoleConfidence(r),
            documents: r.documents?.join(', ') || r.source_document || '',
            mentions: r.total_mentions || 0,
            function_tags: (r.function_tags || []).map(t => typeof t === 'object' ? t.code : t).join('; ')
        }));
        const csv = ['Role Name,Status,Category,Confidence,Documents,Mentions,Function Tags']
            .concat(data.map(d => `"${d.role_name}","${d.status}","${d.category}",${d.confidence},"${d.documents}",${d.mentions},"${d.function_tags}"`))
            .join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `adjudication_export_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(a.href);
        showToast('success', 'Adjudication data exported as CSV');
    }

    async function handleExportHTML() {
        try {
            showToast('info', 'Generating interactive HTML board...');
            const resp = await fetch('/api/roles/adjudication/export-html');
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(typeof err.error === 'string' ? err.error : err.error?.message || `HTTP ${resp.status}`);
            }
            const blob = await resp.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            const cd = resp.headers.get('Content-Disposition') || '';
            const match = cd.match(/filename=(.+)/);
            a.download = match ? match[1] : `aegis_adjudication_board_${new Date().toISOString().slice(0, 10)}.html`;
            a.click();
            URL.revokeObjectURL(a.href);
            showToast('success', 'Interactive HTML board downloaded');
        } catch (e) {
            console.error('[TWR Adj] HTML export error:', e);
            showToast('error', 'Failed to export HTML board: ' + e.message);
        }
    }

    async function handleExportPDF() {
        try {
            showToast('info', 'Generating PDF report...');
            const resp = await fetch('/api/roles/adjudication/export-pdf');
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(typeof err.error === 'string' ? err.error : err.error?.message || `HTTP ${resp.status}`);
            }
            const blob = await resp.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            const cd = resp.headers.get('Content-Disposition') || '';
            const match = cd.match(/filename=(.+)/);
            a.download = match ? match[1] : `aegis_adjudication_report_${new Date().toISOString().slice(0, 10)}.pdf`;
            a.click();
            URL.revokeObjectURL(a.href);
            showToast('success', 'PDF report downloaded');
        } catch (e) {
            console.error('[TWR Adj] PDF export error:', e);
            showToast('error', 'Failed to export PDF: ' + e.message);
        }
    }

    function handleImportDecisions() {
        const input = document.getElementById('adj-import-file');
        if (input) {
            input.value = ''; // Reset so same file can be re-selected
            input.click();
        }
    }

    async function handleImportFileSelected(e) {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            // Validate format
            if (data.export_type !== 'adjudication_decisions') {
                showToast('error', 'Invalid file format. Expected adjudication decisions JSON.');
                return;
            }

            const count = data.decisions?.length || 0;
            if (count === 0) {
                showToast('info', 'No decisions found in file');
                return;
            }

            // v4.0.4: Package version check
            const packageVersion = data.aegis_version;
            if (packageVersion) {
                const currentVersion = document.querySelector('meta[name="aegis-version"]')?.content || '0.0.0';
                if (_compareVersions(packageVersion, currentVersion) > 0) {
                    const proceed = confirm(
                        `This file was created with AEGIS v${packageVersion} ` +
                        `(you are running v${currentVersion}).\n\n` +
                        `Some features may not be fully supported. Import anyway?`
                    );
                    if (!proceed) return;
                }
            }

            // v4.0.4: Get diff preview before importing
            showToast('info', 'Analyzing import file...');
            const csrfToken = getCSRFToken();
            const previewResp = await fetch('/api/roles/adjudication/import-preview', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
                body: text
            });
            const preview = await previewResp.json();

            if (!preview.success) {
                showToast('error', 'Preview failed: ' + (preview.error || 'Unknown error'));
                return;
            }

            // Show diff modal and wait for user confirmation
            const confirmed = await showImportDiffModal(preview);
            if (!confirmed) {
                showToast('info', 'Import cancelled');
                return;
            }

            // v4.0.4: Show progress overlay during import
            const container = document.getElementById('adjudication-content') || document.getElementById('tab-adjudication');
            let progressOverlay = null;
            if (container) {
                container.style.position = 'relative';
                progressOverlay = document.createElement('div');
                progressOverlay.id = 'import-progress-overlay';
                progressOverlay.style.cssText = 'position:absolute;inset:0;background:var(--bg-surface,#fff);opacity:0.92;z-index:100;display:flex;align-items:center;justify-content:center;border-radius:8px;';
                progressOverlay.innerHTML = `
                    <div style="text-align:center;padding:40px;">
                        <div style="margin:0 auto 16px;width:40px;height:40px;border:3px solid var(--border-default,#e5e7eb);border-top-color:var(--accent,#D6A84A);border-radius:50%;animation:spin 0.8s linear infinite;"></div>
                        <div style="font-size:14px;color:var(--text-primary,#1f2937);font-weight:500;">Importing ${count} decisions...</div>
                        <div style="font-size:12px;color:var(--text-muted,#6b7280);margin-top:4px;">This may take a moment for large imports.</div>
                    </div>`;
                container.appendChild(progressOverlay);
            }

            try {
                const resp = await fetch('/api/roles/adjudication/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': getCSRFToken()
                    },
                    body: text
                });

                const result = await resp.json();
                if (result.success) {
                    showToast('success', `Imported ${result.processed || count} decisions successfully`);
                    await renderAdjudication();
                } else {
                    showToast('error', 'Import failed: ' + (result.error || 'Unknown error'));
                }
            } finally {
                if (progressOverlay) progressOverlay.remove();
            }
        } catch (e) {
            console.error('[TWR Adj] Import error:', e);
            showToast('error', 'Failed to import decisions: ' + e.message);
            const overlay = document.getElementById('import-progress-overlay');
            if (overlay) overlay.remove();
        }
    }

    /**
     * v4.0.4: Compare two semver strings. Returns -1, 0, or 1.
     */
    function _compareVersions(v1, v2) {
        const p1 = v1.split('.').map(Number);
        const p2 = v2.split('.').map(Number);
        for (let i = 0; i < Math.max(p1.length, p2.length); i++) {
            const a = p1[i] || 0, b = p2[i] || 0;
            if (a > b) return 1;
            if (a < b) return -1;
        }
        return 0;
    }

    /**
     * v4.0.4: Show import diff preview modal.
     * Returns Promise<boolean> - true if user confirms, false if cancelled.
     */
    function showImportDiffModal(preview) {
        return new Promise((resolve) => {
            const { diff, summary } = preview;

            // Build sections HTML
            let sectionsHtml = '';

            // New roles section
            if (diff.new_roles.length > 0) {
                const items = diff.new_roles.map(r =>
                    `<div class="diff-item diff-new"><span class="diff-role-name">${_escHtml(r.role_name)}</span><span class="diff-detail">New &mdash; ${_escHtml(r.action || 'pending')}</span></div>`
                ).join('');
                sectionsHtml += `
                    <div class="diff-section">
                        <div class="diff-section-header diff-section-new" onclick="this.parentElement.classList.toggle('collapsed')">
                            <span class="diff-section-arrow">&#9662;</span>
                            <span class="diff-section-badge" style="background:#10b981;">+${diff.new_roles.length}</span>
                            New Roles
                        </div>
                        <div class="diff-section-body">${items}</div>
                    </div>`;
            }

            // Changed roles section
            if (diff.changed.length > 0) {
                const items = diff.changed.map(r => {
                    const changeDetail = (r.changes || []).join(', ');
                    return `<div class="diff-item diff-changed"><span class="diff-role-name">${_escHtml(r.role_name)}</span><span class="diff-detail">${_escHtml(changeDetail)}</span></div>`;
                }).join('');
                sectionsHtml += `
                    <div class="diff-section">
                        <div class="diff-section-header diff-section-changed" onclick="this.parentElement.classList.toggle('collapsed')">
                            <span class="diff-section-arrow">&#9662;</span>
                            <span class="diff-section-badge" style="background:#f59e0b;">~${diff.changed.length}</span>
                            Changed Roles
                        </div>
                        <div class="diff-section-body">${items}</div>
                    </div>`;
            }

            // Unchanged roles section (collapsed by default)
            if (diff.unchanged.length > 0) {
                const items = diff.unchanged.map(r =>
                    `<div class="diff-item diff-unchanged"><span class="diff-role-name">${_escHtml(r.role_name)}</span><span class="diff-detail">${_escHtml(r.status || '')}</span></div>`
                ).join('');
                sectionsHtml += `
                    <div class="diff-section collapsed">
                        <div class="diff-section-header diff-section-unchanged" onclick="this.parentElement.classList.toggle('collapsed')">
                            <span class="diff-section-arrow">&#9662;</span>
                            <span class="diff-section-badge" style="background:#6b7280;">=${diff.unchanged.length}</span>
                            Unchanged Roles
                        </div>
                        <div class="diff-section-body">${items}</div>
                    </div>`;
            }

            // Build modal
            const overlay = document.createElement('div');
            overlay.className = 'import-diff-overlay';
            overlay.innerHTML = `
                <div class="import-diff-modal">
                    <div class="import-diff-header">
                        <h3>Import Preview</h3>
                        <button class="import-diff-close" title="Cancel">&times;</button>
                    </div>
                    <div class="import-diff-summary">
                        <span class="diff-stat diff-stat-new"><strong>+${summary.new}</strong> new</span>
                        <span class="diff-stat diff-stat-changed"><strong>~${summary.changed}</strong> changed</span>
                        <span class="diff-stat diff-stat-unchanged"><strong>=${summary.unchanged}</strong> unchanged</span>
                        <span class="diff-stat diff-stat-total">${summary.total} total</span>
                    </div>
                    <div class="import-diff-body">${sectionsHtml || '<div style="padding:20px;text-align:center;color:var(--text-muted);">No changes detected</div>'}</div>
                    <div class="import-diff-actions">
                        <button class="btn btn-ghost import-diff-cancel">Cancel</button>
                        <button class="btn btn-primary import-diff-confirm" ${summary.new + summary.changed === 0 ? 'disabled' : ''}>
                            Import ${summary.new + summary.changed} Change${summary.new + summary.changed !== 1 ? 's' : ''}
                        </button>
                    </div>
                </div>`;

            document.body.appendChild(overlay);

            // Event handlers
            const cleanup = (result) => {
                overlay.remove();
                resolve(result);
            };

            overlay.querySelector('.import-diff-close').addEventListener('click', () => cleanup(false));
            overlay.querySelector('.import-diff-cancel').addEventListener('click', () => cleanup(false));
            overlay.querySelector('.import-diff-confirm').addEventListener('click', () => cleanup(true));
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) cleanup(false);
            });
        });
    }

    /** Escape HTML for diff modal display */
    function _escHtml(str) {
        const d = document.createElement('div');
        d.textContent = str || '';
        return d.innerHTML;
    }

    async function handleShareToFolder() {
        try {
            showToast('info', 'Exporting to shared folder...');
            const csrfToken = getCSRFToken();
            const resp = await fetch('/api/roles/dictionary/export-master', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({ include_inactive: false })
            });
            const result = await resp.json();
            if (result.success) {
                showToast('success', `Exported ${result.count || 0} roles to master file`);
            } else {
                showToast('error', 'Export failed: ' + (result.error || 'Unknown error'));
            }
        } catch (e) {
            console.error('[TWR Adj] Share to folder error:', e);
            showToast('error', 'Failed to export to shared folder');
        }
    }

    async function handleShareEmailPackage() {
        try {
            showToast('info', 'Creating roles package...');
            const csrfToken = getCSRFToken();
            const resp = await fetch('/api/roles/share/package', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({})
            });
            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(typeof err.error === 'string' ? err.error : err.error?.message || `HTTP ${resp.status}`);
            }
            // Download the package file first
            const blob = await resp.blob();
            const blobUrl = URL.createObjectURL(blob);
            const cd = resp.headers.get('Content-Disposition') || '';
            const match = cd.match(/filename=(.+)/);
            const filename = match ? match[1] : `aegis_roles_${new Date().toISOString().slice(0, 10)}.aegis-roles`;
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = filename;
            a.click();

            // Build email mailto link (without attachment - mailto cannot attach files)
            const subject = encodeURIComponent('AEGIS Role Dictionary Package');
            const body = encodeURIComponent(
                `Hi,\n\nPlease find the attached AEGIS roles package (${filename}).\n\n` +
                `To import into your AEGIS installation:\n` +
                `1. Save the attached .aegis-roles file\n` +
                `2. Place it in your AEGIS updates/ folder, OR\n` +
                `3. Go to Settings > Sharing > Import Package and select the file\n\n` +
                `Then restart AEGIS or click "Check for Updates" to import.\n\n` +
                `Best regards`
            );
            const mailtoUrl = `mailto:?subject=${subject}&body=${body}`;

            // Show attachment instructions modal instead of immediately opening email
            const existing = document.getElementById('adj-email-attach-modal');
            if (existing) existing.remove();

            const modal = document.createElement('div');
            modal.id = 'adj-email-attach-modal';
            modal.className = 'adj-auto-overlay';
            modal.innerHTML = `
                <div class="adj-auto-modal" style="max-width:520px;text-align:center;">
                    <div class="adj-auto-title" style="justify-content:center;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
                        Attach File to Email
                    </div>
                    <div style="margin:16px 0;padding:16px;background:var(--bg-secondary,#f5f5f5);border-radius:8px;border:1px solid var(--border-default,#ccc);">
                        <p style="margin:0 0 8px;color:var(--text-secondary);font-size:13px;">
                            The package file has been downloaded to your computer:
                        </p>
                        <div style="font-family:monospace;font-size:14px;font-weight:600;color:var(--text-primary,#333);word-break:break-all;padding:8px;background:var(--bg-primary,#fff);border-radius:4px;">
                            ${escapeHtml(filename)}
                        </div>
                    </div>
                    <p style="color:var(--text-secondary);font-size:13px;margin:12px 0;">
                        Click the button below to open your email client, then <strong>manually attach</strong> the downloaded file before sending.
                    </p>
                    <div style="display:flex;gap:8px;justify-content:center;margin-top:16px;">
                        <button class="btn btn-ghost" id="adj-email-modal-close">Close</button>
                        <button class="btn btn-primary" id="adj-email-modal-open" style="gap:6px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                            Open Email Client
                        </button>
                    </div>
                </div>`;
            document.body.appendChild(modal);

            document.getElementById('adj-email-modal-close')?.addEventListener('click', () => {
                modal.remove();
                URL.revokeObjectURL(blobUrl);
            });
            document.getElementById('adj-email-modal-open')?.addEventListener('click', () => {
                window.open(mailtoUrl, '_self');
                showToast('info', 'Remember to attach the downloaded file to your email.');
            });
            modal.addEventListener('click', (e) => {
                if (e.target === modal) { modal.remove(); URL.revokeObjectURL(blobUrl); }
            });

            showToast('success', 'Package downloaded. Attach it to your email.');
        } catch (e) {
            console.error('[TWR Adj] Email package error:', e);
            showToast('error', 'Failed to create package: ' + e.message);
        }
    }

    async function handleImportPackageFile(e) {
        const file = e.target.files?.[0];
        if (!file) return;
        const statusEl = document.getElementById('import-package-status');

        try {
            if (statusEl) statusEl.textContent = 'Importing...';
            showToast('info', 'Importing roles package...');

            const formData = new FormData();
            formData.append('file', file);

            const csrfToken = getCSRFToken();
            const resp = await fetch('/api/roles/share/import-package', {
                method: 'POST',
                headers: { 'X-CSRF-Token': csrfToken },
                body: formData
            });

            const result = await resp.json();
            if (result.success) {
                const msg = `Imported: ${result.roles_added || 0} roles, ${result.categories_added || 0} categories` +
                           (result.roles_skipped ? ` (${result.roles_skipped} skipped)` : '');
                if (statusEl) statusEl.textContent = msg;
                showToast('success', msg);
                // Refresh adjudication if visible
                if (document.getElementById('roles-adjudication')?.style.display !== 'none') {
                    await renderAdjudication();
                }
            } else {
                const errMsg = 'Import failed: ' + (result.error || 'Unknown error');
                if (statusEl) statusEl.textContent = errMsg;
                showToast('error', errMsg);
            }
        } catch (e) {
            console.error('[TWR Adj] Package import error:', e);
            const errMsg = 'Import failed: ' + e.message;
            if (statusEl) statusEl.textContent = errMsg;
            showToast('error', errMsg);
        }
    }

    /**
     * v4.0.3: Render Adjudication tab - Complete overhaul with dashboard,
     * kanban view, auto-classify, function tags, and keyboard navigation
     */
    async function renderAdjudication() {
        console.log('[TWR Adj v4.0.3] Rendering Adjudication...');

        const container = document.getElementById('adjudication-list');
        if (!container) return;

        // Show loading state
        container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">
            <div class="loading-spinner" style="margin:0 auto 12px;width:32px;height:32px;border:3px solid var(--border-default);border-top-color:var(--accent);border-radius:50%;animation:spin 0.8s linear infinite;"></div>
            Loading roles for adjudication...
        </div>`;

        try {
            // Fetch roles from API
            let roles = await fetchAggregatedRoles();
            let dataSource = 'scans';

            // Fallback to dictionary
            if (roles.length === 0) {
                roles = await fetchDictionary();
                dataSource = 'dictionary';
            }

            // Fetch function categories
            try {
                const catResp = await fetch('/api/function-categories');
                syncCSRFFromResponse(catResp);
                if (catResp.ok) {
                    const catData = await catResp.json();
                    AdjState.functionCategories = catData?.data?.categories || catData?.categories || (Array.isArray(catData) ? catData : []);
                }
            } catch (e) {
                console.warn('[TWR Adj] Could not fetch function categories:', e);
            }

            // Fetch function tags for roles
            try {
                const tagsResp = await fetch('/api/role-function-tags');
                syncCSRFFromResponse(tagsResp);
                if (tagsResp.ok) {
                    const tagsData = await tagsResp.json();
                    const tagsList = tagsData?.data?.tags || (Array.isArray(tagsData) ? tagsData : []);
                    // Build a map of role_name → tags
                    const tagMap = {};
                    if (Array.isArray(tagsList)) {
                        tagsList.forEach(t => {
                            if (!tagMap[t.role_name]) tagMap[t.role_name] = [];
                            // Normalize API fields: function_code→code, function_name→name, function_color→color
                            tagMap[t.role_name].push({
                                id: t.id,
                                role_name: t.role_name,
                                code: t.function_code || t.code || '',
                                name: t.function_name || t.name || t.function_code || t.code || '',
                                color: t.function_color || t.color || '#3b82f6'
                            });
                        });
                    }
                    // Attach tags to roles
                    roles.forEach(r => {
                        r.function_tags = tagMap[r.role_name] || [];
                    });
                }
            } catch (e) {
                console.warn('[TWR Adj] Could not fetch role function tags:', e);
            }

            // Store in state
            AdjState.roles = roles;

            // If dictionary-only source, show info banner
            if (dataSource === 'dictionary' && roles.length > 0) {
                const banner = document.createElement('div');
                banner.className = 'adj-source-banner';
                banner.innerHTML = `<i data-lucide="info" style="width:14px;height:14px;"></i>
                    <span><strong>Showing dictionary roles.</strong> Scan documents to see extracted roles with context.</span>`;
                banner.style.cssText = 'display:flex;align-items:center;gap:8px;padding:10px 14px;background:var(--bg-tertiary);border-radius:8px;margin-bottom:12px;font-size:12px;color:var(--text-secondary);border:1px solid var(--border-default);';
                const adjContent = document.getElementById('adj-content');
                if (adjContent) {
                    adjContent.insertBefore(banner, adjContent.firstChild);
                }
            }

            if (roles.length === 0) {
                container.innerHTML = emptyState('shield-check', 'No Roles to Adjudicate',
                    'Seed the Role Dictionary or scan documents with "Role Extraction" enabled to detect roles for review.');
                refreshIcons();
                // Zero out stats
                updateAdjDashboard([]);
                return;
            }

            // Update dashboard stats
            updateAdjDashboard(roles);

            // Set initial view mode toggle
            const viewBtns = document.querySelectorAll('.adj-view-btn');
            viewBtns.forEach(b => b.classList.toggle('active', b.dataset.view === AdjState.viewMode));

            // Render the appropriate view
            renderAdjCurrentView();

            // Initialize all controls
            initAdjudicationControls();

            // Refresh lucide icons
            refreshIcons();

            console.log(`[TWR Adj v4.0.3] Rendered ${roles.length} roles in ${AdjState.viewMode} view`);
        } catch (error) {
            console.error('[TWR Adj v4.0.3] Error rendering adjudication:', error);
            container.innerHTML = emptyState('alert-triangle', 'Error Loading Roles',
                'Could not load roles for adjudication. Please try refreshing.');
            refreshIcons();
        }
    }
    
    /**
     * Render Documents tab
     * v3.0.59: Fixed to show role_count from API, added action buttons
     */
    async function renderDocuments() {
        console.log('[TWR RolesTabs] === renderDocuments START ===');
        
        try {
            const tbody = document.getElementById('document-log-body');
            console.log('[TWR RolesTabs] document-log-body found:', !!tbody);
            if (!tbody) {
                console.error('[TWR RolesTabs] CRITICAL: document-log-body NOT FOUND');
                return;
            }
            
            console.log('[TWR RolesTabs] Fetching scan history...');
            const history = await fetchScanHistory();
            console.log('[TWR RolesTabs] History fetched:', history?.length || 0);
            
            if (history.length === 0) {
                console.log('[TWR RolesTabs] No history, showing empty state');
                tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-muted);">
                    <i data-lucide="file-text" style="display:block;margin:0 auto 12px;width:32px;height:32px;opacity:0.5;"></i>
                    No scan history. Open and scan documents to see them here.
                </td></tr>`;
                refreshIcons();
                return;
            }
            
            // v3.1.0: Fetch document categories to match Function column
            let docCategories = {};
            try {
                const catRes = await fetch('/api/document-categories');
                const catData = await catRes.json();
                if (catData.success && catData.data?.categories) {
                    catData.data.categories.forEach(cat => {
                        docCategories[cat.document_name] = {
                            function_code: cat.function_code,
                            function_name: cat.function_name,
                            category_type: cat.category_type
                        };
                    });
                }
            } catch (e) {
                console.warn('[TWR RolesTabs] Could not load document categories:', e);
            }

            console.log('[TWR RolesTabs] Rendering', history.length, 'history items with', Object.keys(docCategories).length, 'categories...');
            tbody.innerHTML = history.map(scan => {
                const date = new Date(scan.scan_time || scan.scanned_at || scan.created_at);
                const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                const roleCount = scan.role_count ?? 0;

                // v3.1.0: Get function and category from document categories
                const docCat = docCategories[scan.filename] || {};
                const functionCode = docCat.function_code || '-';
                const categoryType = docCat.category_type || '-';

            return `<tr data-scan-id="${scan.scan_id}" data-doc-id="${scan.document_id || ''}">
                <td style="padding:10px;"><strong>${escapeHtml(scan.filename || 'Unknown')}</strong></td>
                <td style="padding:10px;">${escapeHtml(functionCode)}</td>
                <td style="padding:10px;">${escapeHtml(categoryType)}</td>
                <td style="padding:10px;">${dateStr}</td>
                <td style="padding:10px;text-align:center;">${roleCount}</td>
                <td style="padding:10px;text-align:center;">
                    <button class="btn btn-ghost btn-xs doc-log-view-roles" title="View roles from this document" data-filename="${escapeHtml(scan.filename || '')}">
                        <i data-lucide="users" style="width:14px;height:14px;"></i>
                    </button>
                    <button class="btn btn-ghost btn-xs doc-log-delete" title="Remove from history" data-scan-id="${scan.scan_id}">
                        <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
                    </button>
                </td>
            </tr>`;
        }).join('');
        
        console.log('[TWR RolesTabs] === renderDocuments COMPLETE ===');
        refreshIcons();
        initDocumentLogActions();
        } catch (error) {
            console.error('[TWR RolesTabs] === renderDocuments ERROR ===', error);
            throw error;
        }
    }
    
    /**
     * Initialize Document Log action button handlers
     * v3.0.59: Added event delegation for view roles and delete buttons
     */
    function initDocumentLogActions() {
        const tbody = document.getElementById('document-log-body');
        if (!tbody || tbody._docLogInitialized) return;
        tbody._docLogInitialized = true;
        
        tbody.addEventListener('click', async (e) => {
            const viewBtn = e.target.closest('.doc-log-view-roles');
            const deleteBtn = e.target.closest('.doc-log-delete');
            
            if (viewBtn) {
                const filename = viewBtn.dataset.filename;
                if (filename) {
                    // Switch to Details tab and filter by this document
                    showToast('info', `Filtering roles from: ${filename}`);
                    await switchToTab('details');
                    const searchInput = document.getElementById('details-search');
                    if (searchInput) {
                        searchInput.value = filename;
                        searchInput.dispatchEvent(new Event('input'));
                    }
                }
            }
            
            if (deleteBtn) {
                const scanId = deleteBtn.dataset.scanId;
                if (scanId && confirm('Remove this scan from history?')) {
                    try {
                        const csrfToken = getCSRFToken();
                        const response = await fetch(`/api/scan-history/${scanId}`, {
                            method: 'DELETE',
                            headers: { 'X-CSRF-Token': csrfToken }
                        });
                        const result = await response.json();
                        if (result.success) {
                            // Remove from cache and re-render
                            Cache.scanHistory = null;
                            await renderDocuments();
                            showToast('success', 'Scan removed from history');
                        } else {
                            showToast('error', 'Failed to delete: ' + (result.error || 'Unknown error'));
                        }
                    } catch (err) {
                        showToast('error', 'Error deleting scan: ' + err.message);
                    }
                }
            }
        });
    }
    
    /**
     * Refresh Lucide icons
     */
    function refreshIcons() {
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            try { lucide.createIcons(); } catch(e) { console.warn('Icon refresh failed:', e); }
        }
    }
    
    // =========================================================================
    // TAB SWITCHING
    // =========================================================================
    
    /**
     * Switch to a tab and render its content
     * v3.0.68: FIXED - Use .active class instead of inline display (CSS uses !important)
     */
    async function switchToTab(tabName) {
        console.log('[TWR RolesTabs] === Switching to tab:', tabName, '===');
        
        // Update nav item active states
        const navItems = document.querySelectorAll('.roles-nav-item');
        console.log('[TWR RolesTabs] Updating', navItems.length, 'nav items');
        navItems.forEach(item => {
            const isActive = item.dataset.tab === tabName;
            item.classList.toggle('active', isActive);
            item.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });
        
        // v3.0.68: Use .active CLASS instead of inline style
        // CSS has: #modal-roles .roles-section { display: none !important; }
        // CSS has: #modal-roles .roles-section.active { display: block !important; }
        const allSections = document.querySelectorAll('#modal-roles .roles-section');
        console.log('[TWR RolesTabs] Managing', allSections.length, 'sections via .active class');
        allSections.forEach(section => {
            section.classList.remove('active');
            // v4.7.0-fix: Clear any lingering inline display styles
            section.style.removeProperty('display');
        });
        
        // Show ONLY the target section by adding .active class
        const targetSection = document.getElementById(`roles-${tabName}`);
        if (!targetSection) {
            console.warn('[TWR RolesTabs] Section not found: roles-' + tabName);
            return;
        }

        // v4.7.0-fix: Clear any inline display style that may conflict with CSS .active rule
        targetSection.style.removeProperty('display');
        targetSection.classList.add('active');
        console.log('[TWR RolesTabs] Activated section: roles-' + tabName);
        
        // Render tab content
        try {
            console.log('[TWR RolesTabs] Starting render for tab:', tabName);
            switch (tabName) {
                case 'overview':
                    await renderOverview();
                    break;
                case 'details':
                    await renderDetails();
                    break;
                case 'matrix':
                    // v3.1.10: Clear RACI cache to ensure fresh data from API
                    if (typeof window.TWR?.Roles?.clearRaciCache === 'function') {
                        window.TWR.Roles.clearRaciCache();
                    }
                    await renderMatrix();
                    break;
                case 'adjudication':
                    await renderAdjudication();
                    break;
                case 'documents':
                    await renderDocuments();
                    break;
                case 'graph':
                    // v3.0.63: Use our own initGraphControls (same pattern as other tabs)
                    initGraphControls();
                    // Render the graph
                    if (typeof window.TWR?.Roles?.renderRolesGraph === 'function') {
                        window.TWR.Roles.renderRolesGraph();
                    } else if (typeof window.renderRolesGraph === 'function') {
                        window.renderRolesGraph();
                    } else {
                        console.warn('[TWR RolesTabs] renderRolesGraph not available');
                    }
                    break;
                case 'dictionary':
                    // Dictionary uses our other fix
                    if (typeof window.TWR?.DictFix?.loadDictionary === 'function') {
                        window.TWR.DictFix.loadDictionary();
                    }
                    break;
                case 'crossref':
                    await renderCrossRef();
                    break;
                case 'roledocmatrix':
                    // v3.0.116: Role-Document Matrix tab
                    if (typeof window.TWR?.Roles?.renderRoleDocMatrix === 'function') {
                        await window.TWR.Roles.renderRoleDocMatrix();
                    } else {
                        console.warn('[TWR RolesTabs] renderRoleDocMatrix not available');
                    }
                    break;
            }
            console.log('[TWR RolesTabs] Render complete for tab:', tabName);
        } catch (error) {
            console.error('[TWR RolesTabs] ERROR rendering tab:', tabName, error);
        }
        
        console.log('[TWR RolesTabs] === Tab switch complete ===');
    }
    
    /**
     * Initialize tab click handlers using event delegation
     * This is more robust than attaching to individual buttons
     */
    function initTabHandlers() {
        const modal = document.getElementById('modal-roles');
        if (!modal) {
            console.warn('[TWR RolesTabs] modal-roles not found for tab handlers');
            return;
        }
        
        // Count nav items for debugging
        const navItems = modal.querySelectorAll('.roles-nav-item');
        console.log('[TWR RolesTabs] Found', navItems.length, 'nav items');
        
        // Remove any existing delegation handler
        if (modal._tabDelegationHandler) {
            modal.removeEventListener('click', modal._tabDelegationHandler, true);
        }
        
        // Create delegation handler
        modal._tabDelegationHandler = async function(e) {
            // Find if we clicked on a nav item or inside one
            const navItem = e.target.closest('.roles-nav-item');
            if (!navItem) return;
            
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            const tabName = navItem.dataset.tab;
            console.log('[TWR RolesTabs] Tab clicked:', tabName, 'element:', navItem);
            
            if (tabName) {
                await switchToTab(tabName);
            }
        };
        
        // Attach with capture phase to run before other handlers
        modal.addEventListener('click', modal._tabDelegationHandler, true);
        
        console.log('[TWR RolesTabs] Tab delegation handler attached to modal');
    }
    
    /**
     * Initialize when modal opens
     */
    async function onModalOpen() {
        console.log('[TWR RolesTabs] Modal opened, loading initial data...');

        // Clear cache to get fresh data
        Cache.aggregated = null;
        Cache.dictionary = null;
        Cache.matrix = null;
        Cache.scanHistory = null;

        // v4.7.0-fix: Remove inline display styles so CSS .active rule works cleanly
        const modal = document.getElementById('modal-roles');
        if (modal) {
            modal.querySelectorAll('.roles-section').forEach(section => {
                section.style.removeProperty('display');
            });
        }

        // v4.7.0-fix: Await switchToTab to ensure overview renders on first open
        await switchToTab('overview');
    }

    /**
     * Setup modal observer
     */
    function setupModalObserver() {
        const modal = document.getElementById('modal-roles');
        if (!modal) {
            console.warn('[TWR RolesTabs] modal-roles not found');
            return;
        }
        
        // Watch for modal visibility changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes') {
                    const isVisible = modal.style.display !== 'none' && 
                                     !modal.classList.contains('hidden') &&
                                     modal.offsetParent !== null;
                    
                    if (isVisible && !modal._rolesTabsLoaded) {
                        modal._rolesTabsLoaded = true;
                        onModalOpen();
                    } else if (!isVisible) {
                        modal._rolesTabsLoaded = false;
                    }
                }
            });
        });
        
        observer.observe(modal, { attributes: true, attributeFilter: ['style', 'class'] });
        
        // Also check if already visible
        if (modal.style.display !== 'none' && modal.offsetParent !== null) {
            onModalOpen();
        }
    }
    
    /**
     * Setup modal close handlers
     */
    function setupCloseHandlers() {
        const modal = document.getElementById('modal-roles');
        if (!modal) return;
        
        // Close button
        modal.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', function() {
                modal.style.display = 'none';
                modal.classList.remove('active');
                document.body.classList.remove('modal-open');
            });
        });
        
        // Click outside to close (on the modal backdrop)
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
                modal.classList.remove('active');
                document.body.classList.remove('modal-open');
            }
        });
        
        // Escape key to close
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.style.display !== 'none') {
                modal.style.display = 'none';
                modal.classList.remove('active');
                document.body.classList.remove('modal-open');
            }
        });
    }
    
    // =========================================================================
    // INIT
    // =========================================================================
    
    function init() {
        initTabHandlers();
        setupModalObserver();
        setupCloseHandlers();
        console.log('[TWR RolesTabs] Fully initialized');
    }
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose API
    window.TWR = window.TWR || {};
    window.TWR.RolesTabs = {
        switchToTab,
        renderOverview,
        renderDetails,
        renderMatrix,
        renderCrossRef,
        renderAdjudication,
        renderDocuments,
        fetchAggregatedRoles,
        fetchMatrix,
        fetchScanHistory,
        fetchDictionary,
        getCategoryColor,
        exportCrossRefCSV,
        initRaciControls,
        initDetailsControls,
        filterDetailsRoles,
        // v4.0.3: Adjudication controls (overhauled)
        initAdjudicationControls,
        renderAdjudication,
        // v3.0.59: Document Log
        initDocumentLogActions,
        // v3.0.63: Graph controls
        initGraphControls,
        // v3.1.0: Sync getter for cached aggregated roles
        getAggregatedRoles: () => Cache.aggregated || []
    };
    
    // =========================================================================
    // GRAPH CONTROLS (v3.0.63)
    // Following the same pattern as initRaciControls/initDetailsControls
    // =========================================================================
    
    function initGraphControls() {
        console.log('[TWR RolesTabs] Initializing graph controls v3.0.63...');
        
        // Max nodes dropdown
        const maxNodesSelect = document.getElementById('graph-max-nodes');
        if (maxNodesSelect && !maxNodesSelect._tabsFixInitialized) {
            maxNodesSelect._tabsFixInitialized = true;
            maxNodesSelect.addEventListener('change', function() {
                console.log('[TWR RolesTabs] Max nodes changed to:', this.value);
                if (typeof window.TWR?.Roles?.renderRolesGraph === 'function') {
                    window.TWR.Roles.renderRolesGraph();
                } else if (typeof window.renderRolesGraph === 'function') {
                    window.renderRolesGraph();
                }
            });
            console.log('[TWR RolesTabs] ✓ Max nodes dropdown initialized');
        }
        
        // Layout dropdown
        const layoutSelect = document.getElementById('graph-layout');
        if (layoutSelect && !layoutSelect._tabsFixInitialized) {
            layoutSelect._tabsFixInitialized = true;
            layoutSelect.addEventListener('change', function() {
                console.log('[TWR RolesTabs] Layout changed to:', this.value);
                // v4.5.1: Update UI for layout change (legend, bundling slider)
                if (typeof window.TWR?.Roles?.updateGraphLayoutUI === 'function') {
                    window.TWR.Roles.updateGraphLayoutUI(this.value);
                }
                if (typeof window.TWR?.Roles?.renderRolesGraph === 'function') {
                    window.TWR.Roles.renderRolesGraph();
                } else if (typeof window.renderRolesGraph === 'function') {
                    window.renderRolesGraph();
                }
            });
            console.log('[TWR RolesTabs] ✓ Layout dropdown initialized');
        }
        
        // Labels dropdown
        const labelsSelect = document.getElementById('graph-labels');
        if (labelsSelect && !labelsSelect._tabsFixInitialized) {
            labelsSelect._tabsFixInitialized = true;
            labelsSelect.addEventListener('change', function() {
                console.log('[TWR RolesTabs] Labels changed to:', this.value);
                // Must set GraphState.labelMode before calling updateGraphLabelVisibility
                if (window.TWR?.Roles?.GraphState) {
                    window.TWR.Roles.GraphState.labelMode = this.value;
                }
                if (typeof window.TWR?.Roles?.updateGraphLabelVisibility === 'function') {
                    window.TWR.Roles.updateGraphLabelVisibility();
                }
            });
            console.log('[TWR RolesTabs] ✓ Labels dropdown initialized');
        }
        
        // Weight slider
        const weightSlider = document.getElementById('graph-weight-filter');
        const weightValue = document.getElementById('graph-weight-value');
        if (weightSlider && !weightSlider._tabsFixInitialized) {
            weightSlider._tabsFixInitialized = true;
            weightSlider.addEventListener('input', function() {
                if (weightValue) weightValue.textContent = this.value;
                console.log('[TWR RolesTabs] Weight slider:', this.value);
            });
            weightSlider.addEventListener('change', function() {
                console.log('[TWR RolesTabs] Weight filter applied:', this.value);
                if (typeof window.TWR?.Roles?.updateGraphVisibility === 'function') {
                    window.TWR.Roles.updateGraphVisibility();
                }
            });
            console.log('[TWR RolesTabs] ✓ Weight slider initialized');
        }

        // v4.5.1: Bundling tension slider
        const bundlingSlider = document.getElementById('graph-bundling');
        const bundlingValue = document.getElementById('graph-bundling-value');
        if (bundlingSlider && !bundlingSlider._tabsFixInitialized) {
            bundlingSlider._tabsFixInitialized = true;
            bundlingSlider.addEventListener('input', function() {
                const beta = parseInt(this.value) / 100;
                if (bundlingValue) bundlingValue.textContent = beta.toFixed(2);
                if (window.TWR?.Roles?.GraphState) {
                    window.TWR.Roles.GraphState.bundlingTension = beta;
                }
            });
            bundlingSlider.addEventListener('change', function() {
                const beta = parseInt(this.value) / 100;
                console.log('[TWR RolesTabs] Bundling tension:', beta);
                if (typeof window.TWR?.Roles?.updateBundlingTension === 'function') {
                    window.TWR.Roles.updateBundlingTension(beta);
                }
            });
            console.log('[TWR RolesTabs] ✓ Bundling tension slider initialized');
        }

        // Search input
        const searchInput = document.getElementById('graph-search');
        if (searchInput && !searchInput._tabsFixInitialized) {
            searchInput._tabsFixInitialized = true;
            let searchTimeout = null;
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                const value = this.value;
                searchTimeout = setTimeout(() => {
                    console.log('[TWR RolesTabs] Graph search:', value);
                    if (typeof window.TWR?.Roles?.highlightSearchMatches === 'function') {
                        window.TWR.Roles.highlightSearchMatches(value);
                    }
                }, 300);
            });
            console.log('[TWR RolesTabs] ✓ Search input initialized');
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('btn-refresh-graph');
        if (refreshBtn && !refreshBtn._tabsFixInitialized) {
            refreshBtn._tabsFixInitialized = true;
            refreshBtn.addEventListener('click', function() {
                console.log('[TWR RolesTabs] Refresh graph clicked');
                if (typeof window.TWR?.Roles?.renderRolesGraph === 'function') {
                    window.TWR.Roles.renderRolesGraph(true);
                } else if (typeof window.renderRolesGraph === 'function') {
                    window.renderRolesGraph(true);
                }
            });
            console.log('[TWR RolesTabs] ✓ Refresh button initialized');
        }
        
        // Reset view button
        const resetBtn = document.getElementById('btn-reset-graph-view');
        if (resetBtn && !resetBtn._tabsFixInitialized) {
            resetBtn._tabsFixInitialized = true;
            resetBtn.addEventListener('click', function() {
                console.log('[TWR RolesTabs] Reset view clicked');
                if (typeof window.TWR?.Roles?.resetGraphView === 'function') {
                    window.TWR.Roles.resetGraphView();
                } else if (typeof window.resetGraphView === 'function') {
                    window.resetGraphView();
                }
            });
            console.log('[TWR RolesTabs] ✓ Reset view button initialized');
        }
        
        // Clear selection button — v4.5.1: also clears drill-down filters
        const clearBtn = document.getElementById('btn-clear-graph-selection');
        if (clearBtn && !clearBtn._tabsFixInitialized) {
            clearBtn._tabsFixInitialized = true;
            clearBtn.addEventListener('click', function() {
                console.log('[TWR RolesTabs] Clear clicked');
                // v4.5.1: Clear drill-down filters if any are active
                const hasFilters = window.TWR?.Roles?.GraphState?.filterStack?.length > 0;
                if (hasFilters && typeof window.TWR?.Roles?.clearAllFilters === 'function') {
                    window.TWR.Roles.clearAllFilters();
                } else if (typeof window.TWR?.Roles?.clearNodeSelection === 'function') {
                    window.TWR.Roles.clearNodeSelection(true);
                } else if (typeof window.clearNodeSelection === 'function') {
                    window.clearNodeSelection(true);
                }
            });
            console.log('[TWR RolesTabs] ✓ Clear button initialized');
        }
        
        // Help button
        const helpBtn = document.getElementById('btn-graph-help');
        if (helpBtn && !helpBtn._tabsFixInitialized) {
            helpBtn._tabsFixInitialized = true;
            helpBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                const popup = document.getElementById('graph-help-popup');
                if (popup) {
                    popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
                }
                console.log('[TWR RolesTabs] Help toggled');
            });
            console.log('[TWR RolesTabs] ✓ Help button initialized');
        }
        
        // Close help button
        const closeHelpBtn = document.getElementById('btn-close-graph-help');
        if (closeHelpBtn && !closeHelpBtn._tabsFixInitialized) {
            closeHelpBtn._tabsFixInitialized = true;
            closeHelpBtn.addEventListener('click', function() {
                const popup = document.getElementById('graph-help-popup');
                if (popup) popup.style.display = 'none';
            });
        }
        
        // v4.5.0: Toggle info panel button (slide in/out)
        const toggleBtn = document.getElementById('btn-toggle-info-panel');
        if (toggleBtn && !toggleBtn._tabsFixInitialized) {
            toggleBtn._tabsFixInitialized = true;
            toggleBtn.addEventListener('click', function() {
                console.log('[TWR RolesTabs] Toggle info panel clicked');
                const panel = document.getElementById('graph-info-panel');
                if (panel) {
                    panel.classList.toggle('hidden');
                    const isHidden = panel.classList.contains('hidden');
                    // Update button icon (chevron direction)
                    // When hidden: left arrow (click to expand/show panel)
                    // When visible: right arrow (click to collapse/hide panel)
                    const newIcon = isHidden ? 'chevron-left' : 'chevron-right';
                    toggleBtn.innerHTML = `<i data-lucide="${newIcon}"></i>`;
                    if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [toggleBtn] });
                    toggleBtn.title = isHidden ? 'Show panel' : 'Hide panel';
                }
            });
            console.log('[TWR RolesTabs] ✓ Toggle info panel button initialized');
        }

        // v4.7.0: Layout button bar (Force-Directed, Bipartite, Semantic Zoom, Edge Bundling)
        const layoutSwitcher = document.getElementById('graph-layout-switcher');
        if (layoutSwitcher && !layoutSwitcher._tabsFixInitialized) {
            layoutSwitcher._tabsFixInitialized = true;
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

                // Update UI and re-render
                if (typeof window.TWR?.Roles?.updateGraphLayoutUI === 'function') {
                    window.TWR.Roles.updateGraphLayoutUI(layout);
                }
                if (typeof window.TWR?.Roles?.renderRolesGraph === 'function') {
                    window.TWR.Roles.renderRolesGraph(false, layout);
                } else if (typeof window.renderRolesGraph === 'function') {
                    window.renderRolesGraph(false, layout);
                }
                console.log('[TWR RolesTabs] Layout button switched to:', layout);
            });
            console.log('[TWR RolesTabs] ✓ Layout button bar initialized');
        }

        // v4.3.0: Initialize SmartSearch autocomplete for graph search
        if (typeof window.TWR?.Roles?.initSmartSearchInputs === 'function') {
            window.TWR.Roles.initSmartSearchInputs();
            console.log('[TWR RolesTabs] ✓ SmartSearch initialized');
        }

        console.log('[TWR RolesTabs] Graph controls initialization complete');
    }
    
    // =========================================================================
    // OVERRIDE: Allow opening Roles modal without a scan
    // The original showRolesModal() in roles.js blocks if State.roles is empty
    // =========================================================================
    
    /**
     * Show Roles modal - bypasses the "no roles detected" check
     * v4.7.0-fix: Made async, removed inline display:none (CSS handles visibility),
     * and await switchToTab to ensure overview renders on first open.
     */
    async function showRolesModalOverride() {
        console.log('[TWR RolesTabs] Opening Roles modal (override)...');

        const modal = document.getElementById('modal-roles');
        if (!modal) {
            console.error('[TWR RolesTabs] modal-roles not found');
            return;
        }

        // Ensure tab handlers are attached
        initTabHandlers();

        // Show the modal
        modal.style.display = 'flex';
        modal.classList.add('active');
        document.body.classList.add('modal-open');

        // v4.7.0-fix: Remove any inline display styles on sections so CSS .active rule works cleanly
        // (Previously set inline display:none which conflicted with CSS !important on first load)
        modal.querySelectorAll('.roles-section').forEach(section => {
            section.style.removeProperty('display');
            section.classList.remove('active');
        });

        // Clear cache and trigger data load
        Cache.aggregated = null;
        Cache.dictionary = null;
        Cache.matrix = null;
        Cache.scanHistory = null;
        modal._rolesTabsLoaded = true;

        // v4.7.0-fix: Await switchToTab to ensure overview renders fully on first open
        await switchToTab('overview');

        // Refresh icons
        refreshIcons();

        // v4.5.1: Initialize SmartSearch on the global search input
        if (window.TWR?.Roles?.initGlobalSearch) {
            window.TWR.Roles.initGlobalSearch();
            console.log('[TWR RolesTabs] initGlobalSearch called');
        }

        // v4.7.0: Initialize export dropdown for Overview tab
        initOverviewExportDropdown();
    }

    /**
     * Initialize the Overview tab export dropdown.
     * roles.js initExportDropdown() is not exposed, so we replicate here.
     */
    function initOverviewExportDropdown() {
        const dropdownBtn = document.getElementById('btn-export-roles-report');
        const dropdownMenu = document.getElementById('roles-export-menu');
        if (!dropdownBtn || !dropdownMenu || dropdownBtn._tabsFixExport) return;
        dropdownBtn._tabsFixExport = true;

        dropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('show');
        });

        document.getElementById('btn-export-all-csv')?.addEventListener('click', async function() {
            dropdownMenu.classList.remove('show');
            try {
                showToast('info', 'Exporting all roles...');
                const resp = await fetch('/api/roles/aggregated');
                const json = await resp.json();
                const roles = json?.data?.roles || json?.roles || [];
                if (!roles.length) { showToast('warning', 'No roles to export'); return; }
                const csv = ['Role Name,Documents,Mentions,Category,Source,Adjudicated,Deliverable']
                    .concat(roles.map(r => `"${(r.role_name||'').replace(/"/g,'""')}",${r.document_count||0},${r.total_mentions||0},"${r.category||''}","${r.source||''}",${r.is_active?'Yes':'No'},${r.is_deliverable?'Yes':'No'}`))
                    .join('\n');
                const blob = new Blob([csv], { type: 'text/csv' });
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `AEGIS_All_Roles_${new Date().toISOString().slice(0,10)}.csv`;
                a.click(); URL.revokeObjectURL(a.href);
                showToast('success', `Exported ${roles.length} roles as CSV`);
            } catch(e) { showToast('error', 'Export failed: ' + e.message); }
        });
        document.getElementById('btn-export-current-csv')?.addEventListener('click', function() {
            dropdownMenu.classList.remove('show');
            const roles = Cache.overview || [];
            if (!roles.length) { showToast('warning', 'No roles loaded for current document'); return; }
            const csv = ['Role Name,Mentions,Statements'].concat(
                roles.map(r => `"${(r.role_name||'').replace(/"/g,'""')}",${r.total_mentions||0},${r.statement_count||0}`)
            ).join('\n');
            const blob = new Blob([csv], { type: 'text/csv' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `AEGIS_Roles_${new Date().toISOString().slice(0,10)}.csv`;
            a.click(); URL.revokeObjectURL(a.href);
            showToast('success', `Exported ${roles.length} roles as CSV`);
        });
        document.getElementById('btn-export-all-json')?.addEventListener('click', async function() {
            dropdownMenu.classList.remove('show');
            try {
                showToast('info', 'Exporting all roles as JSON...');
                const resp = await fetch('/api/roles/aggregated');
                const json = await resp.json();
                const roles = json?.data?.roles || json?.roles || [];
                const blob = new Blob([JSON.stringify(roles, null, 2)], { type: 'application/json' });
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `AEGIS_All_Roles_${new Date().toISOString().slice(0,10)}.json`;
                a.click(); URL.revokeObjectURL(a.href);
                showToast('success', `Exported ${roles.length} roles as JSON`);
            } catch(e) { showToast('error', 'Export failed: ' + e.message); }
        });
        document.getElementById('btn-export-selected-doc-csv')?.addEventListener('click', function() {
            dropdownMenu.classList.remove('show');
            showToast('info', 'Use the document filter dropdown to select a document first, then export');
        });
        console.log('[TWR RolesTabs] ✓ Overview export dropdown initialized');
    }
    
    /**
     * Override the global showRolesModal function
     */
    function installShowModalOverride() {
        // Override the global function
        window.showRolesModal = showRolesModalOverride;
        
        // Also override in TWR.Roles if it exists
        if (window.TWR?.Roles) {
            window.TWR.Roles.showRolesModal = showRolesModalOverride;
        }
        
        // Re-attach click handler to nav-roles button
        const navRoles = document.getElementById('nav-roles');
        if (navRoles) {
            // Remove any existing listeners by cloning
            const newNavRoles = navRoles.cloneNode(true);
            navRoles.parentNode.replaceChild(newNavRoles, navRoles);
            
            newNavRoles.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                showRolesModalOverride();
            });
            
            console.log('[TWR RolesTabs] nav-roles click handler installed');
        }
        
        // Also handle the footer button
        const btnRolesReport = document.getElementById('btn-roles-report');
        if (btnRolesReport) {
            // Enable the button
            btnRolesReport.disabled = false;
            btnRolesReport.removeAttribute('disabled');
            
            // Clone to remove existing handlers
            const newBtn = btnRolesReport.cloneNode(true);
            newBtn.disabled = false;
            btnRolesReport.parentNode.replaceChild(newBtn, btnRolesReport);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                showRolesModalOverride();
            });
            
            console.log('[TWR RolesTabs] btn-roles-report enabled and handler installed');
        }
        
        console.log('[TWR RolesTabs] showRolesModal override installed');
    }
    
    // Install override after a short delay to ensure other scripts have loaded
    setTimeout(installShowModalOverride, 100);
    
    console.log('[TWR RolesTabs] Module loaded v3.0.72 (full height content) - exposed at window.TWR.RolesTabs');
    
})();
