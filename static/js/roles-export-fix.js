/**
 * AEGIS - Roles Export Fix
 * Version: 3.0.85
 * 
 * Fixes the export button in Roles & Responsibilities Studio.
 * 
 * Root Cause: button-fixes.js handles the click but doesn't have export logic.
 * The Role Details tab gets data from /api/roles/aggregated API, not window.State.
 * 
 * Solution: Override the export button handler to fetch from the same API
 * that roles-tabs-fix.js uses, then generate and download CSV.
 */

'use strict';

(function() {
    console.log('[TWR RolesExport] Loading v3.0.85...');
    
    // Wait for DOM to be ready
    function init() {
        // Find the export button - it might be btn-export-roles-report or in a dropdown
        const exportBtn = document.getElementById('btn-export-roles-report');
        
        if (exportBtn) {
            console.log('[TWR RolesExport] Found export button, attaching handler...');
            
            // Remove any existing click handlers by cloning
            const newBtn = exportBtn.cloneNode(true);
            exportBtn.parentNode.replaceChild(newBtn, exportBtn);
            
            // Add our handler
            newBtn.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[TWR RolesExport] Export button clicked');
                await exportRolesCSV();
            });
            
            console.log('[TWR RolesExport] Export handler attached');
        } else {
            console.log('[TWR RolesExport] Export button not found, will retry on modal open');
        }
        
        // Also watch for when the Roles modal opens to attach handler
        document.addEventListener('click', function(e) {
            // Check if clicking on export-related elements
            if (e.target.closest('#btn-export-roles-report') || 
                e.target.closest('.export-roles-btn') ||
                e.target.closest('[data-action="export-roles"]')) {
                e.preventDefault();
                e.stopPropagation();
                console.log('[TWR RolesExport] Export triggered via delegation');
                exportRolesCSV();
            }
        }, true); // Use capture phase to intercept before button-fixes.js
        
        console.log('[TWR RolesExport] Delegation handler attached');
    }
    
    // Main export function - fetches from API and downloads CSV
    async function exportRolesCSV() {
        console.log('[TWR RolesExport] Starting export...');
        
        // Show loading state
        const toast = window.TWR?.Modals?.toast || window.toast || function(t, m) { console.log(`[${t}] ${m}`); };
        toast('info', 'Exporting roles...');
        
        try {
            // Fetch from the same API that Role Details uses
            console.log('[TWR RolesExport] Fetching from /api/roles/aggregated...');
            const response = await fetch('/api/roles/aggregated');
            
            if (!response.ok) {
                throw new Error(`API returned ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('[TWR RolesExport] API response:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'API returned unsuccessful response');
            }
            
            const roles = result.data || result.roles || [];
            console.log('[TWR RolesExport] Roles count:', roles.length);
            
            if (roles.length === 0) {
                toast('warning', 'No roles found to export. Run a document review first.');
                return;
            }
            
            // Build CSV
            const headers = [
                'Role Name',
                'Category', 
                'Document Count',
                'Total Mentions',
                'Responsibility Count',
                'Documents'
            ];
            
            const rows = roles.map(role => {
                const name = role.canonical_name || role.name || role.role_name || 'Unknown';
                const category = role.category || categorizeRole(name);
                const docCount = role.unique_document_count || role.document_count || role.doc_count || 0;
                const mentions = role.total_mentions || role.mention_count || role.frequency || 0;
                const respCount = role.responsibility_count || role.responsibilities?.length || 0;
                const documents = role.documents || role.found_in || '';
                
                return [
                    `"${escapeCSV(name)}"`,
                    `"${escapeCSV(category)}"`,
                    docCount,
                    mentions,
                    respCount,
                    `"${escapeCSV(documents)}"`
                ];
            });
            
            const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
            
            // Generate filename with timestamp
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[T:]/g, '-');
            const filename = `TWR_Roles_Export_${timestamp}.csv`;
            
            // Download
            downloadCSV(csv, filename);
            
            toast('success', `Exported ${roles.length} roles to ${filename}`);
            console.log('[TWR RolesExport] Export complete:', filename);
            
        } catch (error) {
            console.error('[TWR RolesExport] Export failed:', error);
            toast('error', 'Export failed: ' + error.message);
        }
    }
    
    // Helper: Escape CSV values
    function escapeCSV(str) {
        if (str === null || str === undefined) return '';
        return String(str).replace(/"/g, '""');
    }
    
    // Helper: Download CSV file
    function downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
    
    // Helper: Categorize role by name
    function categorizeRole(name) {
        const lower = name.toLowerCase();
        if (lower.includes('engineer') || lower.includes('developer') || lower.includes('architect')) {
            return 'Technical';
        }
        if (lower.includes('manager') || lower.includes('director') || lower.includes('lead') || lower.includes('chief')) {
            return 'Management';
        }
        if (lower.includes('customer') || lower.includes('client') || lower.includes('user') || lower.includes('stakeholder')) {
            return 'Stakeholder';
        }
        if (lower.includes('contractor') || lower.includes('vendor') || lower.includes('supplier')) {
            return 'External';
        }
        return 'Role';
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Also re-initialize when Roles modal opens (MutationObserver approach)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const modal = document.getElementById('modal-roles');
                if (modal && modal.classList.contains('active')) {
                    console.log('[TWR RolesExport] Roles modal opened, checking export button...');
                    setTimeout(function() {
                        const btn = document.getElementById('btn-export-roles-report');
                        if (btn && !btn.dataset.exportFixed) {
                            btn.dataset.exportFixed = 'true';
                            btn.addEventListener('click', async function(e) {
                                e.preventDefault();
                                e.stopPropagation();
                                await exportRolesCSV();
                            }, true);
                            console.log('[TWR RolesExport] Export handler re-attached to modal button');
                        }
                    }, 100);
                }
            }
        });
    });
    
    const modalRoles = document.getElementById('modal-roles');
    if (modalRoles) {
        observer.observe(modalRoles, { attributes: true });
    }
    
    // Expose function globally for testing
    window.TWR = window.TWR || {};
    window.TWR.exportRolesCSV = exportRolesCSV;
    
    console.log('[TWR RolesExport] Module loaded v3.0.85');
    console.log('[TWR RolesExport] You can manually test with: TWR.exportRolesCSV()');
})();
