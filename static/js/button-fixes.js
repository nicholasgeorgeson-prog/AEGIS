/**
 * AEGIS Button Fixes
 * =============================
 * Binds missing button handlers that were never connected
 * 
 * Version: 3.0.52
 * 
 * Missing buttons found:
 * - btn-browse-shared: Settings shared folder browse
 * - btn-clear-role-history: Roles modal clear history
 * - btn-expand-families: Families panel expand all
 * - btn-export-roles-report: Roles modal export
 * - btn-prev-issue / btn-next-issue: Issue detail modal navigation
 */

(function() {
    'use strict';
    
    console.log('[TWR] Loading button fixes v3.0.52...');
    
    function initButtonFixes() {
        console.log('[TWR] Binding missing button handlers...');
        
        // ============================================================
        // btn-browse-shared - Settings: Browse for shared folder
        // Note: This can't actually browse the filesystem from browser,
        // but we can show a helpful message
        // ============================================================
        document.getElementById('btn-browse-shared')?.addEventListener('click', () => {
            console.log('[TWR] btn-browse-shared clicked');
            if (typeof toast === 'function') {
                toast('info', 'Browser cannot browse local folders. Please paste the path manually (e.g., \\\\\\server\\\\share or S:\\\\folder)');
            } else {
                alert('Please paste the shared folder path manually.\n\nExample: \\\\\\server\\share\\twr or S:\\Team\\TechWriter');
            }
        });
        
        // ============================================================
        // btn-clear-role-history - Roles Modal: Clear document history
        // ============================================================
        document.getElementById('btn-clear-role-history')?.addEventListener('click', async () => {
            console.log('[TWR] btn-clear-role-history clicked');
            
            if (!confirm('Clear all documents from role history? This will reset the cumulative role analysis.')) {
                return;
            }
            
            try {
                const result = await api('/roles/history', 'DELETE');
                if (result && result.success) {
                    if (typeof toast === 'function') {
                        toast('success', 'Role history cleared');
                    }
                    // Refresh the history list
                    const historyList = document.getElementById('role-document-history');
                    if (historyList) {
                        historyList.innerHTML = '<p class="help-text">No documents in history.</p>';
                    }
                } else {
                    if (typeof toast === 'function') {
                        toast('error', result?.error || 'Failed to clear history');
                    }
                }
            } catch (e) {
                console.error('[TWR] Clear role history error:', e);
                if (typeof toast === 'function') {
                    toast('error', 'Error clearing history');
                }
            }
        });
        
        // ============================================================
        // btn-expand-families - Families Panel: Expand/collapse all
        // ============================================================
        let familiesExpanded = false;
        document.getElementById('btn-expand-families')?.addEventListener('click', () => {
            console.log('[TWR] btn-expand-families clicked');
            
            const panel = document.getElementById('families-panel');
            if (!panel) return;
            
            familiesExpanded = !familiesExpanded;
            
            // Toggle all expandable sections
            panel.querySelectorAll('.family-group details').forEach(details => {
                details.open = familiesExpanded;
            });
            
            // Update button icon
            const btn = document.getElementById('btn-expand-families');
            const icon = btn?.querySelector('i[data-lucide]');
            if (icon) {
                icon.setAttribute('data-lucide', familiesExpanded ? 'chevron-up' : 'chevron-down');
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        });
        
        // ============================================================
        // btn-export-roles-report - Roles Modal: Export report
        // ============================================================
        document.getElementById('btn-export-roles-report')?.addEventListener('click', async () => {
            console.log('[TWR] btn-export-roles-report clicked');
            
            // Check if we have roles data
            if (typeof State === 'undefined' || !State.results || !State.results.roles) {
                if (typeof toast === 'function') {
                    toast('warning', 'No roles data to export. Run a review first.');
                }
                return;
            }
            
            try {
                const result = await api('/roles/export', 'POST', {
                    format: 'csv',
                    roles: State.results.roles
                });
                
                if (result && result.success && result.data) {
                    // Download the file
                    const blob = new Blob([result.data], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `roles_report_${new Date().toISOString().slice(0,10)}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    
                    if (typeof toast === 'function') {
                        toast('success', 'Roles report exported');
                    }
                } else {
                    if (typeof toast === 'function') {
                        toast('error', result?.error || 'Export failed');
                    }
                }
            } catch (e) {
                console.error('[TWR] Export roles error:', e);
                if (typeof toast === 'function') {
                    toast('error', 'Error exporting roles');
                }
            }
        });
        
        // ============================================================
        // btn-prev-issue / btn-next-issue - Issue Detail Modal Navigation
        // ============================================================
        let currentIssueIndex = 0;
        
        function navigateIssue(direction) {
            console.log('[TWR] navigateIssue:', direction);
            
            // Get current filtered issues
            if (typeof State === 'undefined' || !State.filteredIssues || State.filteredIssues.length === 0) {
                if (typeof toast === 'function') {
                    toast('warning', 'No issues to navigate');
                }
                return;
            }
            
            const issues = State.filteredIssues;
            
            if (direction === 'next') {
                currentIssueIndex = Math.min(currentIssueIndex + 1, issues.length - 1);
            } else {
                currentIssueIndex = Math.max(currentIssueIndex - 1, 0);
            }
            
            // Show the issue at the new index
            const issue = issues[currentIssueIndex];
            if (issue && typeof showIssueDetail === 'function') {
                showIssueDetail(issue);
            }
            
            // Update button states
            document.getElementById('btn-prev-issue').disabled = currentIssueIndex === 0;
            document.getElementById('btn-next-issue').disabled = currentIssueIndex === issues.length - 1;
        }
        
        document.getElementById('btn-prev-issue')?.addEventListener('click', () => {
            navigateIssue('prev');
        });
        
        document.getElementById('btn-next-issue')?.addEventListener('click', () => {
            navigateIssue('next');
        });
        
        // Track which issue is being viewed
        window.setCurrentIssueIndex = function(index) {
            currentIssueIndex = index;
            // Update button states
            if (typeof State !== 'undefined' && State.filteredIssues) {
                const prevBtn = document.getElementById('btn-prev-issue');
                const nextBtn = document.getElementById('btn-next-issue');
                if (prevBtn) prevBtn.disabled = currentIssueIndex === 0;
                if (nextBtn) nextBtn.disabled = currentIssueIndex === State.filteredIssues.length - 1;
            }
        };
        
        console.log('[TWR] Button fixes applied successfully');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initButtonFixes);
    } else {
        // Small delay to ensure other scripts are loaded
        setTimeout(initButtonFixes, 100);
    }
    
})();

console.log('[TWR] Button fixes module loaded v3.0.52');
