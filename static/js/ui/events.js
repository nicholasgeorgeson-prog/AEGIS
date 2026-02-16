/**
 * AEGIS - Event Handling Module
 * @version 3.0.47
 *
 * Centralized event listener setup, keyboard navigation, and drag-drop handling.
 *
 * v3.0.47: Fixed file processing race condition with try-finally, added aria-expanded to sidebar
 * v3.0.46: Migrated to TWR.Storage for unified localStorage management
 * v3.0.45: Added ? key for shortcuts modal
 * v3.0.44: Added collapsible sidebar toggle (Ctrl+B), migrated SF role mapping onclick
 * v3.0.32: Added top nav handlers and run state indicator
 * v3.0.29: Added validation filter toggle event handlers
 *
 * Dependencies:
 *   - TWR.Storage (localStorage management)
 *   - TWR.Utils (debounce, show, hide)
 *   - TWR.State (State, FilterState)
 *   - TWR.Modals (closeModals, toast, showModal)
 *   - TWR.API (not directly used, but some handlers call API functions)
 *
 * Note: This module registers event listeners that call functions defined in app.js.
 * Those functions remain in app.js as they have complex dependencies on rendering,
 * filtering, and other subsystems.
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Events = (function() {
    
    // ========================================
    // STATE
    // ========================================
    
    // Keyboard navigation state for issue list
    let keyboardSelectedIndex = -1;
    
    // ========================================
    // MAIN EVENT LISTENERS
    // ========================================
    
    /**
     * Initialize all event listeners
     * Call once on DOMContentLoaded
     */
    function initEventListeners() {
        // File handling
        // v3.0.47: Fixed race condition - ensure _TWR_fileProcessing flag is always reset
        const fileInput = document.getElementById('file-input');
        fileInput?.addEventListener('change', async e => {
            // Guard against duplicate file processing
            const now = Date.now();
            if (window._TWR_fileProcessing || (now - window._TWR_lastFileTime) < 1000) {
                console.log('[TWR] Ignoring duplicate file change event');
                e.target.value = ''; // Reset input
                return;
            }
            if (e.target.files[0]) {
                window._TWR_lastFileTime = now;
                if (typeof handleFileUpload === 'function') {
                    // v3.0.47: Use try-finally to ensure flag is always reset
                    try {
                        window._TWR_fileProcessing = true;
                        await handleFileUpload(e.target.files[0]);
                    } catch (err) {
                        console.error('[TWR] File upload error:', err);
                        const toast = window.TWR?.Modals?.toast || window.toast;
                        if (toast) toast('error', 'File upload failed: ' + err.message);
                    } finally {
                        window._TWR_fileProcessing = false;
                    }
                }
            }
        });

        document.getElementById('btn-open')?.addEventListener('click', () => {
            document.getElementById('file-input')?.click();
        });

        // Preset buttons
        document.querySelectorAll('[id^="btn-preset-"]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('[id^="btn-preset-"]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                if (typeof applyPreset === 'function') {
                    applyPreset(btn.id.replace('btn-preset-', ''));
                }
            });
        });

        // Collapsible sections
        document.querySelectorAll('.nav-section-title.collapsible').forEach(title => {
            title.addEventListener('click', () => {
                if (typeof toggleSection === 'function') {
                    toggleSection(title);
                }
            });
        });

        // v2.9.8: Super-section collapsible headers
        document.querySelectorAll('.super-section-header').forEach(header => {
            header.addEventListener('click', () => {
                if (typeof toggleSuperSection === 'function') {
                    toggleSuperSection(header);
                }
            });
        });
        
        // Restore super-section collapse state from localStorage
        if (typeof restoreSuperSectionState === 'function') {
            restoreSuperSectionState();
        }

        // Main action buttons
        document.getElementById('btn-review')?.addEventListener('click', () => {
            if (typeof runReview === 'function') runReview();
        });
        document.getElementById('btn-export')?.addEventListener('click', () => {
            if (typeof showExportModal === 'function') showExportModal();
        });

        // Filter controls
        const searchInput = document.getElementById('issue-search');
        const debounce = window.TWR?.Utils?.debounce || window.debounce;
        if (searchInput && debounce) {
            searchInput.addEventListener('input', debounce(() => {
                if (typeof applyFilters === 'function') applyFilters();
            }, 300));
        }
        
        document.getElementById('btn-clear-search')?.addEventListener('click', () => {
            const input = document.getElementById('issue-search');
            if (input) {
                input.value = '';
                if (typeof applyFilters === 'function') applyFilters();
            }
        });

        // Severity filters
        document.querySelectorAll('.sev-filter input').forEach(cb => {
            cb.addEventListener('change', () => {
                if (typeof applyFilters === 'function') applyFilters();
            });
        });

        // Selection controls
        document.getElementById('btn-select-all')?.addEventListener('click', () => {
            if (typeof selectIssues === 'function') selectIssues('all');
        });
        document.getElementById('btn-select-none')?.addEventListener('click', () => {
            if (typeof selectIssues === 'function') selectIssues('none');
        });

        // View toggle
        document.getElementById('btn-view-table')?.addEventListener('click', () => {
            if (typeof setView === 'function') setView('table');
        });
        document.getElementById('btn-view-cards')?.addEventListener('click', () => {
            if (typeof setView === 'function') setView('cards');
        });

        // Pagination
        document.getElementById('btn-prev-page')?.addEventListener('click', () => {
            if (typeof changePage === 'function') changePage(-1);
        });
        document.getElementById('btn-next-page')?.addEventListener('click', () => {
            if (typeof changePage === 'function') changePage(1);
        });

        // Sortable columns
        document.querySelectorAll('.sortable').forEach(col => {
            col.addEventListener('click', () => {
                if (typeof sortByColumn === 'function') sortByColumn(col.dataset.sort);
            });
            // Keyboard support
            col.addEventListener('keydown', e => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    if (typeof sortByColumn === 'function') sortByColumn(col.dataset.sort);
                }
            });
        });

        // Modal close buttons - only close the specific parent modal, not all modals
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                // Find and close only the parent modal
                const parentModal = this.closest('.modal');
                if (parentModal) {
                    parentModal.classList.remove('active');
                    // Only remove modal-open class if no other modals are active
                    const otherActiveModals = document.querySelectorAll('.modal.active');
                    if (otherActiveModals.length === 0) {
                        document.body.classList.remove('modal-open');
                    }
                }
            });
        });
        
        // Export modal
        document.getElementById('btn-do-export')?.addEventListener('click', () => {
            if (typeof executeExport === 'function') executeExport();
        });
        
        // Export format change
        document.querySelectorAll('input[name="export-format"]').forEach(radio => {
            radio.addEventListener('change', () => {
                if (typeof updateExportOptions === 'function') updateExportOptions();
            });
        });

        // Settings
        document.getElementById('btn-settings')?.addEventListener('click', () => {
            if (typeof showSettingsModal === 'function') showSettingsModal();
        });
        document.getElementById('btn-save-settings')?.addEventListener('click', () => {
            if (typeof saveSettings === 'function') saveSettings();
        });

        // Settings tabs
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (typeof switchSettingsTab === 'function') switchSettingsTab(tab.dataset.tab);
            });
        });

        // Help
        document.getElementById('btn-help')?.addEventListener('click', () => {
            if (typeof showHelpModal === 'function') showHelpModal();
        });
        document.querySelectorAll('.help-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (typeof switchHelpTab === 'function') switchHelpTab(tab.dataset.tab);
            });
        });

        // Roles button
        document.getElementById('btn-roles-report')?.addEventListener('click', () => {
            if (typeof showRolesModal === 'function') showRolesModal();
        });
        document.getElementById('btn-view-roles')?.addEventListener('click', () => {
            if (typeof showRolesModal === 'function') showRolesModal();
        });
        
        // Export roles button in modal
        document.getElementById('btn-export-roles')?.addEventListener('click', () => {
            if (typeof exportRoles === 'function') exportRoles('csv');
        });
        
        // Export RACI matrix button
        document.getElementById('btn-export-matrix')?.addEventListener('click', () => {
            if (typeof exportRaciMatrix === 'function') exportRaciMatrix();
        });
        
        // Roles search and sort
        if (debounce) {
            document.getElementById('roles-search')?.addEventListener('input', debounce(() => {
                if (typeof renderRolesDetails === 'function') renderRolesDetails();
            }, 300));
        }
        document.getElementById('roles-sort')?.addEventListener('change', () => {
            if (typeof renderRolesDetails === 'function') renderRolesDetails();
        });

        // Apply fixes checkbox
        document.getElementById('export-apply-fixes')?.addEventListener('change', e => {
            const preview = document.getElementById('fix-preview');
            if (preview) preview.style.display = e.target.checked ? 'block' : 'none';
        });
        
        // === NEW UX ENHANCEMENTS ===
        
        // v3.0.13: Analytics accordion toggle
        document.getElementById('analytics-header')?.addEventListener('click', () => {
            if (typeof toggleAnalytics === 'function') toggleAnalytics();
        });
        
        // v3.0.13: Unified filter bar - severity toggles
        document.querySelectorAll('#unified-severity-toggles .sev-toggle').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.classList.toggle('active');
                if (typeof applyUnifiedFilters === 'function') applyUnifiedFilters();
            });
        });

        // v5.0.5: Sidebar severity pill click handlers - filter issues by severity
        document.querySelectorAll('.sidebar .severity-pill').forEach(pill => {
            pill.style.cursor = 'pointer';
            pill.addEventListener('click', () => {
                // Determine which severity was clicked from the pill's class
                const sev = pill.classList.contains('critical') ? 'critical' :
                            pill.classList.contains('high') ? 'high' :
                            pill.classList.contains('medium') ? 'medium' :
                            pill.classList.contains('low') ? 'low' :
                            pill.classList.contains('info') ? 'info' : null;
                if (!sev) return;

                // Toggle active state on pill
                const wasActive = pill.classList.contains('active');

                if (wasActive) {
                    // Deactivate - show all severities
                    pill.classList.remove('active');
                    // Also sync unified filter bar: activate all toggles
                    document.querySelectorAll('#unified-severity-toggles .sev-toggle').forEach(btn => {
                        btn.classList.add('active');
                    });
                } else {
                    // Activate this pill, deactivate others
                    document.querySelectorAll('.sidebar .severity-pill').forEach(p => p.classList.remove('active'));
                    pill.classList.add('active');
                    // Also sync unified filter bar: only activate matching toggle
                    document.querySelectorAll('#unified-severity-toggles .sev-toggle').forEach(btn => {
                        const btnSev = btn.dataset.severity || btn.textContent.trim().toLowerCase();
                        if (btnSev === sev) {
                            btn.classList.add('active');
                        } else {
                            btn.classList.remove('active');
                        }
                    });
                }

                if (typeof applyUnifiedFilters === 'function') {
                    applyUnifiedFilters();
                } else if (typeof filterIssuesBySeverity === 'function' && !wasActive) {
                    filterIssuesBySeverity(sev);
                }
            });
        });

        // v3.0.13: Category dropdown toggle
        document.getElementById('btn-category-dropdown')?.addEventListener('click', (e) => {
            e.stopPropagation();
            const panel = document.getElementById('category-dropdown-panel');
            if (panel) {
                const isVisible = panel.style.display !== 'none';
                panel.style.display = isVisible ? 'none' : 'block';
            }
        });
        
        // Close category dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.querySelector('.category-dropdown');
            const panel = document.getElementById('category-dropdown-panel');
            if (panel && dropdown && !dropdown.contains(e.target)) {
                panel.style.display = 'none';
            }
        });
        
        // v3.0.13: Unified category quick actions
        document.getElementById('unified-cat-all')?.addEventListener('click', () => {
            document.querySelectorAll('#unified-category-list input').forEach(cb => cb.checked = true);
            if (typeof updateCategoryActiveCount === 'function') updateCategoryActiveCount();
            if (typeof applyUnifiedFilters === 'function') applyUnifiedFilters();
        });
        
        document.getElementById('unified-cat-none')?.addEventListener('click', () => {
            document.querySelectorAll('#unified-category-list input').forEach(cb => cb.checked = false);
            if (typeof updateCategoryActiveCount === 'function') updateCategoryActiveCount();
            if (typeof applyUnifiedFilters === 'function') applyUnifiedFilters();
        });
        
        // v3.0.13: Unified category search
        if (debounce) {
            document.getElementById('unified-category-search')?.addEventListener('input', debounce(() => {
                const search = (document.getElementById('unified-category-search')?.value || '').toLowerCase().trim();
                document.querySelectorAll('#unified-category-list label').forEach(label => {
                    const text = label.textContent.toLowerCase();
                    label.style.display = !search || text.includes(search) ? '' : 'none';
                });
            }, 200));
        }
        
        // v3.0.13: Clear all unified filters
        document.getElementById('btn-clear-filters')?.addEventListener('click', () => {
            if (typeof clearAllUnifiedFilters === 'function') clearAllUnifiedFilters();
        });
        
        // v3.0.29: Validation filter toggle buttons
        document.querySelectorAll('.validation-filter-toggle .validation-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const FilterState = window.TWR?.State?.FilterState || window.FilterState;
                const value = btn.dataset.validation;
                
                // Update active state
                document.querySelectorAll('.validation-filter-toggle .validation-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Set filter
                if (FilterState) {
                    FilterState.setValidationFilter(value === 'all' ? null : value);
                }
                
                // Apply filters
                if (typeof applyUnifiedFilters === 'function') {
                    applyUnifiedFilters();
                } else if (typeof applyFilters === 'function') {
                    applyFilters();
                }
            });
        });
        
        // Chart filter clear button
        document.getElementById('btn-clear-chart-filter')?.addEventListener('click', () => {
            if (typeof clearChartFilter === 'function') clearChartFilter();
        });
        
        // Clear all filters
        document.getElementById('btn-clear-all-filters')?.addEventListener('click', () => {
            // Reset severity filters
            document.querySelectorAll('.sev-filter input').forEach(cb => cb.checked = true);
            // Reset category filters
            document.querySelectorAll('#category-list input, #category-pinned input').forEach(cb => cb.checked = false);
            // Clear chart filter
            const FilterState = window.TWR?.State?.FilterState || window.FilterState;
            if (FilterState) FilterState.chartFilter = null;
            // Clear search
            const searchInput = document.getElementById('issue-search');
            if (searchInput) searchInput.value = '';
            if (typeof applyFilters === 'function') applyFilters();
        });
        
        // Category quick toggles
        document.getElementById('btn-cat-all')?.addEventListener('click', () => {
            document.querySelectorAll('#category-list input, #category-pinned input').forEach(cb => cb.checked = true);
            if (typeof applyFilters === 'function') applyFilters();
        });
        
        document.getElementById('btn-cat-none')?.addEventListener('click', () => {
            document.querySelectorAll('#category-list input, #category-pinned input').forEach(cb => cb.checked = false);
            if (typeof applyFilters === 'function') applyFilters();
        });
        
        document.getElementById('btn-cat-invert')?.addEventListener('click', () => {
            document.querySelectorAll('#category-list input, #category-pinned input').forEach(cb => cb.checked = !cb.checked);
            if (typeof applyFilters === 'function') applyFilters();
        });
        
        // Category search
        if (debounce) {
            document.getElementById('category-search')?.addEventListener('input', debounce(filterCategoryList, 200));
        }
        
        // Density toggle
        document.querySelectorAll('.density-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.density-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                setTableDensity(btn.dataset.density);
            });
        });
        
        // Keyboard navigation for issue list
        initIssueKeyboardNav();
        
        // Restore saved filters
        const FilterState = window.TWR?.State?.FilterState || window.FilterState;
        if (FilterState && typeof FilterState.restore === 'function') {
            FilterState.restore();
        }
        
        // ============================================================
        // v3.0.15: Migrated onclick handlers to addEventListener
        // ============================================================
        
        // --- Sidebar Buttons ---
        document.getElementById('btn-statement-forge')?.addEventListener('click', () => {
            const showModal = window.TWR?.Modals?.showModal || window.showModal;
            if (showModal) showModal('modal-statement-forge');
        });
        document.getElementById('btn-diagnostics')?.addEventListener('click', () => {
            if (typeof showDiagnosticsModal === 'function') showDiagnosticsModal();
        });
        
        // --- Header Action Buttons ---
        document.getElementById('btn-batch-load')?.addEventListener('click', () => {
            const showModal = window.TWR?.Modals?.showModal || window.showModal;
            if (showModal) showModal('batch-upload-modal');
        });
        
        // --- Stats Bar ---
        document.getElementById('stat-score-container')?.addEventListener('click', () => {
            if (typeof showScoreBreakdown === 'function') showScoreBreakdown();
        });
        
        // --- Issue Families Panel ---
        document.getElementById('btn-families-expand')?.addEventListener('click', () => {
            const showModal = window.TWR?.Modals?.showModal || window.showModal;
            if (showModal) showModal('modal-families');
        });
        document.getElementById('btn-families')?.addEventListener('click', () => {
            if (typeof showIssueFamilies === 'function') showIssueFamilies();
        });
        document.getElementById('btn-review-log')?.addEventListener('click', () => {
            if (typeof showReviewLog === 'function') showReviewLog();
        });
        
        // --- Loading Overlay ---
        document.getElementById('loading-cancel')?.addEventListener('click', () => {
            if (typeof cancelCurrentOperation === 'function') cancelCurrentOperation();
        });
        
        // --- Export Modal ---
        document.getElementById('btn-review-before-export')?.addEventListener('click', () => {
            if (typeof openExportReview === 'function') openExportReview();
        });
        
        // --- Export Review Modal ---
        document.getElementById('btn-approve-all-visible')?.addEventListener('click', () => {
            if (typeof ExportReview !== 'undefined' && ExportReview.approveAllVisible) {
                ExportReview.approveAllVisible();
            }
        });
        document.getElementById('btn-reject-all-visible')?.addEventListener('click', () => {
            if (typeof ExportReview !== 'undefined' && ExportReview.rejectAllVisible) {
                ExportReview.rejectAllVisible();
            }
        });
        document.getElementById('btn-export-approved')?.addEventListener('click', () => {
            if (typeof ExportReview !== 'undefined' && ExportReview.exportApproved) {
                ExportReview.exportApproved();
            }
        });
        
        // --- Settings Modal: Updates Tab ---
        document.getElementById('btn-check-updates')?.addEventListener('click', () => {
            if (typeof checkForUpdates === 'function') checkForUpdates();
        });
        document.getElementById('btn-apply-updates')?.addEventListener('click', () => {
            if (typeof applyUpdates === 'function') applyUpdates();
        });
        document.getElementById('btn-load-backups')?.addEventListener('click', () => {
            if (typeof loadBackups === 'function') loadBackups();
        });
        document.getElementById('btn-rollback')?.addEventListener('click', () => {
            if (typeof showRollbackConfirm === 'function') showRollbackConfirm();
        });
        
        // --- Help Modal ---
        document.getElementById('btn-help-print')?.addEventListener('click', () => {
            if (typeof HelpContent !== 'undefined' && HelpContent.printSection) {
                HelpContent.printSection();
            }
        });
        
        // --- Roles Modal: Adjudication Tab ---
        document.getElementById('btn-bulk-confirm')?.addEventListener('click', () => {
            if (typeof bulkAdjudicate === 'function') bulkAdjudicate('confirmed');
        });
        document.getElementById('btn-bulk-deliverable')?.addEventListener('click', () => {
            if (typeof bulkAdjudicate === 'function') bulkAdjudicate('deliverable');
        });
        document.getElementById('btn-bulk-reject')?.addEventListener('click', () => {
            if (typeof bulkAdjudicate === 'function') bulkAdjudicate('rejected');
        });
        document.getElementById('btn-bulk-pending')?.addEventListener('click', () => {
            if (typeof bulkAdjudicate === 'function') bulkAdjudicate('pending');
        });
        document.getElementById('btn-export-adjudication')?.addEventListener('click', () => {
            if (typeof exportAdjudication === 'function') exportAdjudication();
        });
        document.getElementById('btn-save-adjudication')?.addEventListener('click', () => {
            if (typeof saveAdjudication === 'function') saveAdjudication();
        });
        document.getElementById('btn-reset-adjudication')?.addEventListener('click', () => {
            if (typeof resetAdjudication === 'function') resetAdjudication();
        });
        document.getElementById('btn-apply-adjudication')?.addEventListener('click', () => {
            if (typeof applyAdjudicationToDocument === 'function') applyAdjudicationToDocument();
        });
        
        // --- Diagnostics Modal ---
        document.getElementById('btn-ai-troubleshoot-json')?.addEventListener('click', () => {
            if (typeof AITroubleshoot !== 'undefined' && AITroubleshoot.exportPackage) {
                AITroubleshoot.exportPackage('json');
            }
        });
        document.getElementById('btn-ai-troubleshoot-txt')?.addEventListener('click', () => {
            if (typeof AITroubleshoot !== 'undefined' && AITroubleshoot.exportPackage) {
                AITroubleshoot.exportPackage('txt');
            }
        });
        document.getElementById('btn-capture-state')?.addEventListener('click', () => {
            if (typeof captureFrontendState === 'function') captureFrontendState();
        });
        document.getElementById('btn-email-diagnostics')?.addEventListener('click', () => {
            if (typeof emailDiagnosticsViaOutlook === 'function') emailDiagnosticsViaOutlook();
        });
        document.getElementById('btn-export-diagnostics')?.addEventListener('click', () => {
            if (typeof exportDiagnostics === 'function') exportDiagnostics();
        });
        
        // --- Statement Forge Modal ---
        document.getElementById('btn-sf-extract')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.extractStatements) {
                StatementForge.extractStatements();
            }
        });
        document.getElementById('btn-sf-add-manual')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.addStatement) {
                StatementForge.addStatement();
            }
        });
        document.getElementById('sf-modal-merge-btn')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.mergeSelected) {
                StatementForge.mergeSelected();
            }
        });
        document.getElementById('sf-modal-delete-btn')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.deleteSelected) {
                StatementForge.deleteSelected();
            }
        });
        document.getElementById('sf-modal-export-btn')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.toggleExportMenu) {
                StatementForge.toggleExportMenu('sf-modal-export-menu');
            }
        });
        document.getElementById('btn-sf-export-csv')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.exportAs) {
                StatementForge.exportAs('csv');
            }
        });
        document.getElementById('btn-sf-export-excel')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.exportAs) {
                StatementForge.exportAs('excel');
            }
        });
        document.getElementById('btn-sf-export-json')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.exportAs) {
                StatementForge.exportAs('json');
            }
        });
        document.getElementById('btn-sf-export-word')?.addEventListener('click', () => {
            if (typeof StatementForge !== 'undefined' && StatementForge.exportAs) {
                StatementForge.exportAs('word');
            }
        });
        
        // --- Score Breakdown Modal ---
        document.getElementById('btn-score-breakdown-close')?.addEventListener('click', () => {
            const closeModals = window.TWR?.Modals?.closeModals || window.closeModals;
            if (closeModals) closeModals();
        });
        
        // ============================================================
        // v3.0.44: Sidebar Collapse Toggle
        // ============================================================
        document.getElementById('btn-sidebar-collapse')?.addEventListener('click', () => {
            toggleSidebar();
        });
        
        console.log('[TWR Events] Event listeners initialized');
    }
    
    // ========================================
    // CATEGORY LIST FILTERING
    // ========================================
    
    /**
     * Filter category list by search input
     */
    function filterCategoryList() {
        const search = (document.getElementById('category-search')?.value || '').toLowerCase().trim();
        const items = document.querySelectorAll('#category-list .checkbox-label');
        
        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            item.style.display = !search || text.includes(search) ? '' : 'none';
        });
    }
    
    // ========================================
    // TABLE DENSITY
    // ========================================
    
    /**
     * Set table density (compact/comfortable)
     * @param {string} density - 'compact' or 'comfortable'
     */
    function setTableDensity(density) {
        const tableBody = document.getElementById('issues-list');
        if (!tableBody) return;
        
        tableBody.classList.remove('density-compact', 'density-comfortable');
        tableBody.classList.add(`density-${density}`);
        
        // Save preference via unified storage
        if (window.TWR?.Storage?.ui) {
            TWR.Storage.ui.setDensity(density);
        }
    }
    
    // ========================================
    // KEYBOARD NAVIGATION FOR ISSUES
    // ========================================
    
    /**
     * Initialize keyboard navigation for issue list
     */
    function initIssueKeyboardNav() {
        const container = document.getElementById('issues-list');
        if (!container) return;
        
        container.setAttribute('tabindex', '0');
        
        container.addEventListener('keydown', e => {
            const rows = container.querySelectorAll('.issue-row');
            if (rows.length === 0) return;
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                keyboardSelectedIndex = Math.min(keyboardSelectedIndex + 1, rows.length - 1);
                updateKeyboardSelection(rows);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                keyboardSelectedIndex = Math.max(keyboardSelectedIndex - 1, 0);
                updateKeyboardSelection(rows);
            } else if (e.key === 'Enter' && keyboardSelectedIndex >= 0) {
                e.preventDefault();
                // Toggle expand on selected row
                const row = rows[keyboardSelectedIndex];
                const index = parseInt(row?.dataset?.index);
                if (!isNaN(index) && typeof toggleIssueExpand === 'function') {
                    toggleIssueExpand(index);
                }
            } else if (e.key === ' ' && keyboardSelectedIndex >= 0) {
                e.preventDefault();
                // Toggle selection on selected row
                const row = rows[keyboardSelectedIndex];
                const index = parseInt(row?.dataset?.index);
                if (!isNaN(index)) {
                    if (typeof toggleIssueSelection === 'function') {
                        toggleIssueSelection(index);
                    }
                    if (typeof renderIssuesList === 'function') {
                        renderIssuesList(); // Re-render to update checkbox state
                    }
                }
            } else if (e.key === 'Escape') {
                keyboardSelectedIndex = -1;
                updateKeyboardSelection(rows);
                // Also collapse any expanded rows
                document.querySelectorAll('.issue-row.expanded').forEach(r => {
                    const idx = parseInt(r.dataset?.index);
                    if (!isNaN(idx) && typeof toggleIssueExpand === 'function') {
                        toggleIssueExpand(idx);
                    }
                });
            }
        });
        
        container.addEventListener('focus', () => {
            const hint = document.getElementById('keyboard-hint');
            if (hint) hint.style.display = 'flex';
        });
        
        container.addEventListener('blur', () => {
            const hint = document.getElementById('keyboard-hint');
            if (hint) hint.style.display = 'none';
        });
    }
    
    /**
     * Update visual keyboard selection on rows
     * @param {NodeList} rows - Issue row elements
     */
    function updateKeyboardSelection(rows) {
        rows.forEach((row, i) => {
            row.classList.toggle('keyboard-selected', i === keyboardSelectedIndex);
            if (i === keyboardSelectedIndex) {
                row.scrollIntoView({ block: 'nearest' });
            }
        });
    }
    
    /**
     * Reset keyboard selection index
     * Called when issue list is re-rendered
     */
    function resetKeyboardSelection() {
        keyboardSelectedIndex = -1;
    }
    
    /**
     * Get current keyboard selection index
     * @returns {number}
     */
    function getKeyboardSelectedIndex() {
        return keyboardSelectedIndex;
    }
    
    // ========================================
    // DRAG AND DROP
    // ========================================
    
    /**
     * Initialize drag-and-drop file handling
     */
    function initDragDrop() {
        // Make entire empty-state area the dropzone, not just the icon
        const dropzone = document.getElementById('empty-state');
        const mainContent = document.querySelector('.content-area');
        
        // Global drop handler for the entire content area
        const dropTargets = [dropzone, mainContent].filter(Boolean);

        // Prevent default for all drag events on entire document
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.body.addEventListener(eventName, e => {
                e.preventDefault();
                e.stopPropagation();
            });
            dropTargets.forEach(target => {
                if (target) {
                    target.addEventListener(eventName, e => {
                        e.preventDefault();
                        e.stopPropagation();
                    });
                }
            });
        });

        // Visual feedback for dropzone
        if (dropzone) {
            dropzone.addEventListener('dragenter', () => {
                dropzone.classList.add('drag-over');
                dropzone.style.background = 'rgba(88, 166, 255, 0.1)';
                dropzone.style.border = '2px dashed var(--accent)';
            });
            
            dropzone.addEventListener('dragleave', e => {
                // Only remove if leaving the dropzone entirely
                if (!dropzone.contains(e.relatedTarget)) {
                    dropzone.classList.remove('drag-over');
                    dropzone.style.background = '';
                    dropzone.style.border = '';
                }
            });

            dropzone.addEventListener('drop', e => {
                dropzone.classList.remove('drag-over');
                dropzone.style.background = '';
                dropzone.style.border = '';
                
                const file = e.dataTransfer?.files?.[0];
                if (file) {
                    if (typeof isValidFileType === 'function' && isValidFileType(file.name)) {
                        if (typeof handleFileUpload === 'function') {
                            handleFileUpload(file);
                        }
                    } else {
                        const toast = window.TWR?.Modals?.toast || window.toast;
                        if (toast) toast('error', 'Please drop a .docx, .doc, or .pdf file');
                    }
                }
            });

            // Also make the dropzone clickable
            dropzone.style.cursor = 'pointer';
            dropzone.addEventListener('click', (e) => {
                // Don't trigger if clicking on buttons inside
                if (e.target.closest('.btn') || e.target.closest('button')) return;
                // Don't trigger if file processing in progress
                if (window._TWR_fileProcessing) return;
                document.getElementById('file-input')?.click();
            });
        }
        
        // Also handle drop on main content area (when empty-state is hidden)
        if (mainContent) {
            mainContent.addEventListener('drop', e => {
                const file = e.dataTransfer?.files?.[0];
                if (file) {
                    if (typeof isValidFileType === 'function' && isValidFileType(file.name)) {
                        if (typeof handleFileUpload === 'function') {
                            handleFileUpload(file);
                        }
                    } else {
                        const toast = window.TWR?.Modals?.toast || window.toast;
                        if (toast) toast('error', 'Please drop a .docx, .doc, or .pdf file');
                    }
                }
            });
        }
        
        console.log('[TWR Events] Drag-drop initialized');
    }
    
    // ========================================
    // GLOBAL KEYBOARD SHORTCUTS
    // ========================================
    
    /**
     * Initialize global keyboard shortcuts
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', e => {
            const State = window.TWR?.State?.State || window.State;
            
            // Ctrl+O - Open file
            if (e.ctrlKey && e.key === 'o') {
                e.preventDefault();
                document.getElementById('file-input')?.click();
            }
            // Ctrl+R - Run review
            if (e.ctrlKey && e.key === 'r' && State?.filename) {
                e.preventDefault();
                if (typeof runReview === 'function') runReview();
            }
            // Ctrl+E - Export
            if (e.ctrlKey && e.key === 'e' && State?.reviewResults) {
                e.preventDefault();
                if (typeof showExportModal === 'function') showExportModal();
            }
            // Ctrl+A - Select all
            if (e.ctrlKey && e.key === 'a' && State?.filteredIssues?.length > 0) {
                e.preventDefault();
                if (typeof selectIssues === 'function') selectIssues('all');
            }
            // Escape - Deselect / Close modal
            if (e.key === 'Escape') {
                if (document.querySelector('.modal.show, .modal.active')) {
                    const closeModals = window.TWR?.Modals?.closeModals || window.closeModals;
                    if (closeModals) closeModals();
                } else {
                    if (typeof selectIssues === 'function') selectIssues('none');
                }
            }
            // F1 - Help
            if (e.key === 'F1') {
                e.preventDefault();
                if (typeof showHelpModal === 'function') showHelpModal();
            }
            // J/K - Navigate issues
            if (e.key === 'j' || e.key === 'k') {
                if (typeof navigateIssues === 'function') {
                    navigateIssues(e.key === 'j' ? 1 : -1);
                }
            }
            // v3.0.44: Ctrl+B - Toggle sidebar
            if (e.ctrlKey && e.key === 'b') {
                e.preventDefault();
                toggleSidebar();
            }
            // v3.0.45: ? - Show keyboard shortcuts (only when not typing)
            if (e.key === '?' && !e.target.matches('input, textarea, [contenteditable]')) {
                e.preventDefault();
                const showModal = window.TWR?.Modals?.showModal || window.showModal;
                if (showModal) showModal('modal-shortcuts');
            }
        });
        
        console.log('[TWR Events] Keyboard shortcuts initialized');
    }
    
    // ========================================
    // RUN STATE INDICATOR (v3.0.32: Thread 9)
    // ========================================
    
    /**
     * Update the run state indicator in the top nav
     * @param {string} state - 'idle'|'extracting'|'checking'|'running'|'complete'|'error'
     * @param {string} label - Display label (optional)
     */
    function setRunState(state, label = null) {
        const indicator = document.getElementById('run-state-indicator');
        const icon = document.getElementById('run-state-icon');
        const labelEl = document.getElementById('run-state-label');
        
        if (!indicator) return;
        
        // Remove all state classes
        indicator.classList.remove('idle', 'extracting', 'checking', 'running', 'complete', 'error');
        indicator.classList.add(state);
        
        // Update icon based on state
        const iconMap = {
            'idle': 'circle',
            'extracting': 'loader',
            'checking': 'search',
            'running': 'loader',
            'complete': 'check-circle',
            'error': 'alert-circle'
        };
        
        if (icon) {
            const iconEl = icon.querySelector('svg, i[data-lucide]');
            if (iconEl) {
                iconEl.setAttribute('data-lucide', iconMap[state] || 'circle');
                iconEl.classList.remove('state-idle');
                if (state === 'idle') iconEl.classList.add('state-idle');
            }
        }
        
        // Update label
        const defaultLabels = {
            'idle': 'Idle',
            'extracting': 'Extracting...',
            'checking': 'Checking...',
            'running': 'Running...',
            'complete': 'Complete',
            'error': 'Error'
        };
        
        if (labelEl) {
            labelEl.textContent = label || defaultLabels[state] || state;
        }
        
        // Refresh icons
        if (window.TWR?.Utils?.refreshIcons) {
            TWR.Utils.refreshIcons();
        } else if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }
    
    /**
     * Initialize top nav bar event handlers
     */
    function initTopNav() {
        // v4.5.1: Click AEGIS logo to return to landing page (dashboard)
        const brand = document.querySelector('.top-nav-brand');
        if (brand) {
            brand.addEventListener('click', () => {
                if (typeof TWR !== 'undefined' && TWR.LandingPage) {
                    // Close any open modals first
                    if (typeof closeModals === 'function') closeModals({ skipDashboard: true });
                    TWR.LandingPage.show();
                }
            });
        }

        // v4.6.1: Dashboard button — return to landing page
        const navDashboard = document.getElementById('nav-dashboard');
        if (navDashboard) {
            navDashboard.addEventListener('click', () => {
                if (typeof TWR !== 'undefined' && TWR.LandingPage) {
                    if (typeof closeModals === 'function') closeModals({ skipDashboard: true });
                    TWR.LandingPage.show();
                }
            });
        }

        // v4.6.1: Hidden nav buttons still handle programmatic clicks from landing page tiles
        document.querySelectorAll('[data-view]').forEach(link => {
            link.addEventListener('click', () => {
                const view = link.dataset.view;

                // Handle view switching
                switch (view) {
                    case 'review':
                        // Default view - show main content, close modals without returning to dashboard
                        if (typeof closeModals === 'function') closeModals({ skipDashboard: true });
                        break;
                    case 'forge':
                        // v4.6.1: Ensure dashboard background is visible behind modal
                        if (typeof TWR !== 'undefined' && TWR.LandingPage && !document.body.classList.contains('landing-active')) {
                            TWR.LandingPage.show();
                        }
                        if (typeof showModal === 'function') showModal('modal-statement-forge');
                        // v3.0.110: Update document status and render pre-extracted statements
                        if (window.StatementForge) {
                            setTimeout(() => {
                                window.StatementForge.updateDocumentStatus();
                                // Load any pre-extracted statements from session
                                window.StatementForge.loadFromSession();
                            }, 100);
                        }
                        break;
                    case 'metrics':
                        // Toggle analytics visibility (v3.0.49 fix: correct ID)
                        const analyticsAccordion = document.getElementById('analytics-accordion');
                        const analyticsBody = document.getElementById('analytics-body');
                        if (analyticsAccordion && analyticsBody) {
                            const isHidden = analyticsAccordion.style.display === 'none';
                            analyticsAccordion.style.display = isHidden ? 'block' : 'none';
                            if (isHidden) {
                                analyticsBody.style.display = 'block';
                                document.getElementById('analytics-chevron')?.classList.add('rotated');
                            }
                        }
                        break;
                    case 'history':
                        // v4.6.1: Ensure dashboard background is visible behind modal
                        if (typeof TWR !== 'undefined' && TWR.LandingPage && !document.body.classList.contains('landing-active')) {
                            TWR.LandingPage.show();
                        }
                        if (typeof showModal === 'function') showModal('modal-scan-history');
                        break;
                    case 'roles':
                        // v4.6.1: Ensure dashboard background is visible behind modal
                        if (typeof TWR !== 'undefined' && TWR.LandingPage && !document.body.classList.contains('landing-active')) {
                            TWR.LandingPage.show();
                        }
                        if (typeof showModal === 'function') showModal('modal-roles');
                        break;
                }
            });
        });

        // Quick help button
        document.getElementById('btn-help-quick')?.addEventListener('click', () => {
            if (typeof showModal === 'function') showModal('modal-help');
        });

        // Quick settings button
        document.getElementById('btn-settings-quick')?.addEventListener('click', () => {
            if (typeof showModal === 'function') showModal('modal-settings');
        });
    }
    
    // ========================================
    // SIDEBAR COLLAPSE (v3.0.44, v3.0.46: uses TWR.Storage)
    // ========================================
    
    /**
     * Toggle sidebar collapsed state
     * v3.0.47: Added aria-expanded attribute for accessibility
     * v4.0.2: Use chevron icons that point in the direction the panel will move
     */
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;

        const isCollapsed = sidebar.classList.toggle('collapsed');

        // Persist state via unified storage
        if (window.TWR?.Storage?.ui) {
            TWR.Storage.ui.setSidebarCollapsed(isCollapsed);
        }

        // Update button icon and accessibility
        // v4.0.2: chevron-right when collapsed (will expand right), chevron-left when expanded (will collapse left)
        const btn = document.getElementById('btn-sidebar-collapse');
        if (btn) {
            btn.setAttribute('aria-expanded', !isCollapsed);
            btn.setAttribute('aria-label', isCollapsed ? 'Expand sidebar' : 'Collapse sidebar');
            btn.setAttribute('title', isCollapsed ? 'Expand sidebar (Ctrl+B)' : 'Collapse sidebar (Ctrl+B)');

            // v4.0.2: Replace icon - must remove existing SVG for lucide to recreate
            const newIconName = isCollapsed ? 'chevron-right' : 'chevron-left';
            const existingSvg = btn.querySelector('svg');
            if (existingSvg) {
                existingSvg.remove();
            }
            // Create or update the i element
            let icon = btn.querySelector('i[data-lucide]');
            if (!icon) {
                icon = document.createElement('i');
                icon.setAttribute('aria-hidden', 'true');
                btn.appendChild(icon);
            }
            icon.setAttribute('data-lucide', newIconName);
        }

        // Refresh icons after removing old SVG
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }

        console.log('[TWR Events] Sidebar collapsed:', isCollapsed);
    }
    
    /**
     * Initialize sidebar state from storage
     * v3.0.47: Added aria-expanded attribute for accessibility
     * v4.0.2: Use chevron icons and call lucide.createIcons() to refresh
     */
    function initSidebarState() {
        // Use unified storage if available
        const collapsed = window.TWR?.Storage?.ui
            ? TWR.Storage.ui.isSidebarCollapsed()
            : false;

        if (collapsed) {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.add('collapsed');
                // Update button icon and accessibility
                const btn = document.getElementById('btn-sidebar-collapse');
                if (btn) {
                    btn.setAttribute('aria-expanded', 'false');
                    btn.setAttribute('aria-label', 'Expand sidebar');
                    btn.setAttribute('title', 'Expand sidebar (Ctrl+B)');

                    // v4.0.2: Replace icon - must remove existing SVG for lucide to recreate
                    const existingSvg = btn.querySelector('svg');
                    if (existingSvg) {
                        existingSvg.remove();
                    }
                    let icon = btn.querySelector('i[data-lucide]');
                    if (!icon) {
                        icon = document.createElement('i');
                        icon.setAttribute('aria-hidden', 'true');
                        btn.appendChild(icon);
                    }
                    icon.setAttribute('data-lucide', 'chevron-right');
                }
                // Refresh icons after removing old SVG
                if (typeof lucide !== 'undefined') {
                    try { lucide.createIcons(); } catch(e) {}
                }
            }
        }
    }
    
    // ========================================
    // PUBLIC API
    // ========================================
    
    return {
        // Main initialization
        initEventListeners,
        initDragDrop,
        initKeyboardShortcuts,
        initTopNav,  // v3.0.32

        // Keyboard navigation
        initIssueKeyboardNav,
        updateKeyboardSelection,
        resetKeyboardSelection,
        getKeyboardSelectedIndex,

        // Helpers
        filterCategoryList,
        setTableDensity,
        setRunState,  // v3.0.32

        // v3.0.44: Sidebar collapse
        toggleSidebar,
        initSidebarState
    };
})();

// ========================================
// v4.3.0: SMART SEARCH INITIALIZATION
// ========================================

/**
 * Initialize SmartSearch autocomplete for issue search and other main searches
 * Should be called after document analysis is complete
 */
TWR.Events.initSmartSearchForIssues = function() {
    // Check if SmartSearch is available from roles module
    if (!window.TWR?.Roles?.SmartSearch) {
        console.log('[TWR Events] SmartSearch not available, skipping autocomplete');
        return;
    }

    const SmartSearch = window.TWR.Roles.SmartSearch;
    const State = window.TWR?.State?.State || window.State || {};

    // Issue search - suggest issues by text content, category, and severity
    SmartSearch.init('issue-search', {
        itemType: 'issue',
        getItems: () => {
            const issues = State.issues || [];
            if (issues.length === 0) return [];

            // Get unique categories and severities
            const categories = new Map();
            const severities = new Map();

            issues.forEach(issue => {
                if (issue.category && !categories.has(issue.category)) {
                    const count = issues.filter(i => i.category === issue.category).length;
                    categories.set(issue.category, {
                        label: issue.category,
                        type: 'issue',
                        meta: `${count} issues in this category`,
                        badge: count,
                        searchType: 'category'
                    });
                }
                if (issue.severity && !severities.has(issue.severity)) {
                    const count = issues.filter(i => i.severity === issue.severity).length;
                    severities.set(issue.severity, {
                        label: issue.severity,
                        type: 'issue',
                        meta: `${count} ${issue.severity.toLowerCase()} severity issues`,
                        badge: count,
                        searchType: 'severity'
                    });
                }
            });

            // Get sample issues (unique issue texts, limited)
            const sampleIssues = issues.slice(0, 30).map(issue => ({
                label: issue.issue || issue.text || issue.description || 'Issue',
                type: 'issue',
                meta: `${issue.severity || 'Unknown'} • ${issue.category || 'Uncategorized'}`,
                searchType: 'text'
            }));

            // Return categories first, then severities, then sample issues
            return [
                ...Array.from(categories.values()),
                ...Array.from(severities.values()),
                ...sampleIssues.slice(0, 10)
            ];
        },
        onSelect: (item, input) => {
            if (typeof applyFilters === 'function') applyFilters();
        },
        maxResults: 10,
        minChars: 1
    });

    console.log('[TWR Events] SmartSearch initialized for issue-search');
};

// ========================================
// GLOBAL ALIASES (for backward compatibility)
// ========================================

window.initEventListeners = TWR.Events.initEventListeners;
window.initDragDrop = TWR.Events.initDragDrop;
window.initKeyboardShortcuts = TWR.Events.initKeyboardShortcuts;
window.initTopNav = TWR.Events.initTopNav;  // v3.0.32
window.initIssueKeyboardNav = TWR.Events.initIssueKeyboardNav;
window.filterCategoryList = TWR.Events.filterCategoryList;
window.setTableDensity = TWR.Events.setTableDensity;
window.setRunState = TWR.Events.setRunState;  // v3.0.32
window.toggleSidebar = TWR.Events.toggleSidebar;  // v3.0.44
window.initSidebarState = TWR.Events.initSidebarState;  // v3.0.44
window.initSmartSearchForIssues = TWR.Events.initSmartSearchForIssues;  // v4.3.0

console.log('[TWR] Events module loaded');
