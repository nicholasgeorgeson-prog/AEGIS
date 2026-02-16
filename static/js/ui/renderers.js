/**
 * AEGIS - Renderers Module
 * @version 3.0.122
 *
 * Handles all UI rendering: issue list, charts, stats, dashboard components.
 *
 * v3.0.122: Fixed issue expansion showing wrong content (used issues[] instead of filteredIssues[])
 * v3.0.109: Fixed acronym highlighting false positives using word boundary regex
 * v3.0.95: Fixed heatmap click-to-filter, improved section heatmap feedback
 * v3.0.94: Added rich context with page/section info and highlight markers
 * v3.0.29: Added buildValidationMetric() for provenance rate in dashboard
 * v3.0.24: Added renderProvenanceInfo() for source verification display
 * 
 * Dependencies: 
 *   - TWR.Utils (escapeHtml, truncate)
 *   - TWR.State (State, FilterState, SEVERITY_ORDER, SEVERITY_COLORS)
 *   - TWR.Modals (toast) - optional, for user feedback
 *   - Chart.js (external library for charts)
 *   - lucide (external library for icons)
 * 
 * Note: Some render functions call external functions defined in app.js
 * (like applyFilters) because they have complex dependencies.
 */

'use strict';

window.TWR = window.TWR || {};

TWR.Renderers = (function() {
    
    // ========================================
    // PRIVATE STATE
    // ========================================
    
    // Chart instances (managed locally)
    let severityChart = null;
    let categoryChart = null;
    let lastChartData = { severity: null, category: null };
    
    // Keyboard navigation state for issue list
    let keyboardSelectedIndex = -1;
    
    // ========================================
    // HELPER REFERENCES
    // ========================================
    
    // Get helpers from modules or fallback to window
    function getState() {
        return window.TWR?.State?.State || window.State;
    }
    
    function getFilterState() {
        return window.TWR?.State?.FilterState || window.FilterState;
    }
    
    function getSeverityOrder() {
        return window.TWR?.State?.SEVERITY_ORDER || window.SEVERITY_ORDER || 
            { 'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Info': 4 };
    }
    
    function getSeverityColors() {
        return window.TWR?.State?.SEVERITY_COLORS || window.SEVERITY_COLORS || {
            'Critical': '#DC3545',
            'High': '#FD7E14',
            'Medium': '#FFC107',
            'Low': '#28A745',
            'Info': '#17A2B8'
        };
    }
    
    function escapeHtml(str) {
        if (window.TWR?.Utils?.escapeHtml) return window.TWR.Utils.escapeHtml(str);
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML; // SAFE: escapeHtml function output
    }
    
    function truncate(str, maxLen) {
        if (window.TWR?.Utils?.truncate) return window.TWR.Utils.truncate(str, maxLen);
        if (!str) return '';
        return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
    }
    
    function toast(type, message, duration) {
        if (window.TWR?.Modals?.toast) {
            window.TWR.Modals.toast(type, message, duration);
        } else if (typeof window.toast === 'function') {
            window.toast(type, message, duration);
        } else {
            console.log(`[TWR Toast] ${type}: ${message}`);
        }
    }
    
    /**
     * Escape special regex characters in a string.
     * v3.0.109: Added for word boundary regex in highlighting
     * 
     * @param {string} str - String to escape
     * @returns {string} Regex-safe string
     */
    function escapeRegex(str) {
        if (!str) return '';
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    /**
     * Process context text with highlight markers.
     * Converts «...» markers to <mark> tags and escapes HTML.
     * v3.0.94: Added for rich context highlighting
     * 
     * @param {string} context - Context text possibly containing «highlight» markers
     * @param {string} flaggedText - The flagged text to highlight if no markers present
     * @returns {string} HTML with <mark> tags for highlighting
     */
    function processContextWithHighlights(context, flaggedText) {
        if (!context) return '';
        
        // Check for «...» highlight markers from backend
        const hasMarkers = context.includes('«') && context.includes('»');
        
        if (hasMarkers) {
            // Split by markers and escape each part, then wrap marked content
            let result = '';
            let remaining = context;
            
            while (remaining.includes('«')) {
                const startIdx = remaining.indexOf('«');
                const endIdx = remaining.indexOf('»', startIdx);
                
                if (endIdx === -1) break; // No matching end marker
                
                // Add text before marker (escaped)
                result += escapeHtml(remaining.substring(0, startIdx));
                
                // Add highlighted content
                const highlighted = remaining.substring(startIdx + 1, endIdx);
                result += `<mark class="context-highlight">${escapeHtml(highlighted)}</mark>`;
                
                // Continue with remaining text
                remaining = remaining.substring(endIdx + 1);
            }
            
            // Add any remaining text
            result += escapeHtml(remaining);
            return result;
        }
        
        // Fallback: try to highlight flaggedText if present in context
        // v3.0.109: Use word boundary regex to avoid false positive highlighting
        // (e.g., prevent "NDA" from being highlighted inside "staNDArds")
        if (flaggedText) {
            const escapedRegex = escapeRegex(flaggedText);
            // Word boundary regex for whole-word matches only
            const wordBoundaryRegex = new RegExp(`\\b(${escapedRegex})\\b`, 'gi');
            
            if (wordBoundaryRegex.test(context)) {
                // Reset regex lastIndex after test() call
                wordBoundaryRegex.lastIndex = 0;
                
                // Build result by escaping non-matched text and highlighting matches
                let result = '';
                let lastIndex = 0;
                let match;
                
                while ((match = wordBoundaryRegex.exec(context)) !== null) {
                    // Escape and add text before the match
                    result += escapeHtml(context.slice(lastIndex, match.index));
                    // Add the highlighted match (escaped)
                    result += `<mark class="context-highlight">${escapeHtml(match[0])}</mark>`;
                    lastIndex = wordBoundaryRegex.lastIndex;
                }
                // Escape and add remaining text after last match
                result += escapeHtml(context.slice(lastIndex));
                return result;
            }
        }
        
        // No highlighting needed
        return escapeHtml(context);
    }
    
    // ========================================
    // STAT VALUE HELPERS
    // ========================================
    
    /**
     * Set the text content of a stat element.
     * @param {string} id - Element ID
     * @param {number|string} value - Value to display
     */
    function setStatValue(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = typeof value === 'number' ? value.toLocaleString() : value;
    }
    
    /**
     * Update basic stats display (total/filtered issues).
     */
    function updateStats() {
        const State = getState();
        setStatValue('total-issues', State.issues.length);
        setStatValue('filtered-issues', State.filteredIssues.length);
        updateSelectionUI();
    }
    
    /**
     * Update the selection count UI elements.
     */
    function updateSelectionUI() {
        const State = getState();
        const selCount = document.getElementById('selection-count');
        if (selCount) selCount.textContent = `${State.selectedIssues.size} selected`;
        
        // Update export counts
        const countAll = document.getElementById('export-count-all');
        const countFiltered = document.getElementById('export-count-filtered');
        const countSelected = document.getElementById('export-count-selected');
        
        if (countAll) countAll.textContent = State.issues.length;
        if (countFiltered) countFiltered.textContent = State.filteredIssues.length;
        if (countSelected) countSelected.textContent = State.selectedIssues.size;
    }
    
    /**
     * Get the color for a quality score.
     */
    function getScoreColor(score) {
        if (score >= 90) return '#28A745';
        if (score >= 80) return '#17A2B8';
        if (score >= 70) return '#FFC107';
        if (score >= 60) return '#FD7E14';
        return '#DC3545';
    }
    
    // ========================================
    // ISSUE SELECTION HELPERS
    // ========================================
    
    /**
     * Check if an issue is selected.
     * @param {number} index - Index in filteredIssues
     * @returns {boolean}
     */
    function isIssueSelected(index) {
        const State = getState();
        const issue = State.filteredIssues[index];
        const issueId = issue?.issue_id || index;
        return State.selectedIssues.has(issueId);
    }
    
    /**
     * Toggle selection of an issue.
     * @param {number} index - Index in filteredIssues
     */
    function toggleIssueSelection(index) {
        const State = getState();
        const issue = State.filteredIssues[index];
        const issueId = issue?.issue_id || index;
        
        if (State.selectedIssues.has(issueId)) {
            State.selectedIssues.delete(issueId);
        } else {
            State.selectedIssues.add(issueId);
        }
        updateSelectionUI();
    }
    
    /**
     * Select all or none of the filtered issues.
     * @param {string} mode - 'all' or 'none'
     */
    function selectIssues(mode) {
        const State = getState();
        if (mode === 'all') {
            State.filteredIssues.forEach((issue) => {
                const issueId = issue?.issue_id || State.filteredIssues.indexOf(issue);
                State.selectedIssues.add(issueId);
            });
        } else {
            State.selectedIssues.clear();
        }
        updateSelectionUI();
        renderIssuesList();
    }
    
    // ========================================
    // ISSUE LIST RENDERING
    // ========================================
    
    /**
     * Render the issues list with pagination.
     */
    function renderIssuesList() {
        const State = getState();
        const container = document.getElementById('issues-list');
        if (!container) return;

        const pageSize = State.settings.pageSize === 'all' ? State.filteredIssues.length : State.settings.pageSize;
        const start = (State.currentPage - 1) * pageSize;
        const end = Math.min(start + pageSize, State.filteredIssues.length);
        const pageIssues = State.filteredIssues.slice(start, end);

        // Zero issues success state
        if (State.issues.length === 0 && State.reviewResults) {
            // SAFE: static HTML
            container.innerHTML = `
                <div class="success-state">
                    <i data-lucide="check-circle"></i>
                    <h3>All Checks Passed!</h3>
                    <p>No issues were found in this document. Great work!</p>
                </div>
            `;
            refreshIcons();
            updatePagination(0, 0, 0);
            return;
        }

        if (pageIssues.length === 0) {
            // Issues exist but filtered out
            const hiddenCount = State.issues.length - State.filteredIssues.length;
            // SAFE: static HTML with numeric value
            container.innerHTML = `
                <div class="empty-issues">
                    <i data-lucide="search-x"></i>
                    <p>No issues match your filters</p>
                    ${hiddenCount > 0 ? `<p class="text-muted">${hiddenCount} issues hidden by filters</p>` : ''}
                </div>
            `;
            refreshIcons();
            updatePagination(0, 0, 0);
            return;
        }

        // SAFE: category, message escaped via escapeHtml()
        container.innerHTML = pageIssues.map((issue, idx) => {
            const globalIdx = start + idx;
            const isSelected = isIssueSelected(globalIdx);
            const sevClass = issue.severity?.toLowerCase() || 'info';
            
            // Create inline preview (first 50 chars of flagged text)
            const preview = issue.flagged_text 
                ? truncate(issue.flagged_text, 50) 
                : (issue.context ? truncate(issue.context, 50) : '');
            
            // Check if has expandable content
            const hasExpandableContent = issue.flagged_text || issue.context || issue.suggestion;
            
            // Check if issue has been validated via provenance tracking (v3.0.24)
            const isValidated = issue.source?.is_validated === true;
            const validationIndicator = isValidated 
                ? `<span class="validation-indicator" title="Verified in original document" style="color: rgb(139, 92, 246); margin-left: 4px;"><i data-lucide="badge-check" style="width:12px;height:12px;"></i></span>`
                : '';
            
            return `
                <div class="issue-row ${isSelected ? 'selected' : ''}" data-index="${globalIdx}" data-issue-id="${issue.issue_id || ''}"
                     tabindex="0" role="listitem" aria-label="${escapeHtml(issue.category)}: ${escapeHtml(issue.message)}">
                    <div class="col-expand">
                        ${hasExpandableContent ? `
                            <button class="btn btn-ghost btn-xs expand-btn" onclick="toggleIssueExpand(${globalIdx}, event)" 
                                    title="Expand issue details" aria-label="Expand issue details" aria-expanded="false">
                                <i data-lucide="chevron-right"></i>
                            </button>
                        ` : ''}
                    </div>
                    <div class="col-check">
                        <input type="checkbox" ${isSelected ? 'checked' : ''} 
                               onchange="toggleIssueSelection(${globalIdx})" aria-label="Select issue">
                    </div>
                    <div class="col-severity">
                        <span class="severity-badge ${sevClass}">${issue.severity || 'Info'}</span>
                    </div>
                    <div class="col-category">${escapeHtml(issue.category || '')}${validationIndicator}</div>
                    <div class="col-message">
                        <div class="message-text">${escapeHtml(issue.message || '')}</div>
                    </div>
                    <div class="col-actions">
                        <button class="btn btn-ghost btn-xs" onclick="toggleBaseline(${globalIdx})" title="Add to baseline" aria-label="Add to baseline">
                            <i data-lucide="eye-off"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        refreshIcons();
        updatePagination(start + 1, end, State.filteredIssues.length);
        
        // Update filtered total for selection dropdown
        const filteredTotal = document.getElementById('filtered-total');
        if (filteredTotal) filteredTotal.textContent = State.filteredIssues.length;
        
        // Reset keyboard selection
        keyboardSelectedIndex = -1;
    }
    
    /**
     * Update pagination display.
     */
    function updatePagination(start, end, total) {
        const State = getState();
        
        const pageStart = document.getElementById('page-start');
        const pageEnd = document.getElementById('page-end');
        const totalIssues = document.getElementById('total-issues');
        
        if (pageStart) pageStart.textContent = start;
        if (pageEnd) pageEnd.textContent = end;
        if (totalIssues) totalIssues.textContent = total;

        const pageSize = State.settings.pageSize === 'all' ? total : State.settings.pageSize;
        const totalPages = Math.ceil(total / pageSize) || 1;
        
        const currentPage = document.getElementById('current-page');
        const totalPagesEl = document.getElementById('total-pages');
        
        if (currentPage) currentPage.textContent = State.currentPage;
        if (totalPagesEl) totalPagesEl.textContent = totalPages;

        const prevBtn = document.getElementById('btn-prev-page');
        const nextBtn = document.getElementById('btn-next-page');
        
        if (prevBtn) prevBtn.disabled = State.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = State.currentPage >= totalPages;

        const footer = document.getElementById('table-footer');
        if (footer) footer.style.display = total > pageSize ? 'flex' : 'none';
    }
    
    /**
     * Change the current page.
     * @param {number} delta - Pages to move (+1 or -1)
     */
    function changePage(delta) {
        const State = getState();
        const pageSize = State.settings.pageSize === 'all' ? State.filteredIssues.length : State.settings.pageSize;
        const totalPages = Math.ceil(State.filteredIssues.length / pageSize);
        
        State.currentPage = Math.max(1, Math.min(totalPages, State.currentPage + delta));
        renderIssuesList();
    }
    
    /**
     * Navigate through issues (keyboard).
     * @param {number} direction - 1 for next, -1 for previous
     */
    function navigateIssues(direction) {
        const rows = document.querySelectorAll('.issue-row');
        if (rows.length === 0) return;
        
        const current = document.querySelector('.issue-row.focused');
        let nextIdx = 0;
        
        if (current) {
            const currentIdx = Array.from(rows).indexOf(current);
            nextIdx = Math.max(0, Math.min(rows.length - 1, currentIdx + direction));
            current.classList.remove('focused');
        }
        
        rows[nextIdx].classList.add('focused');
        rows[nextIdx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // ========================================
    // ISSUE EXPANSION
    // ========================================
    
    /**
     * Toggle expanded view for an issue.
     * @param {number} index - Issue index
     * @param {Event} event - Click event
     */
    function toggleIssueExpand(index, event) {
        event?.stopPropagation();
        const State = getState();
        
        const row = document.querySelector(`.issue-row[data-index="${index}"]`);
        if (!row) return;
        
        const isExpanded = row.classList.toggle('expanded');
        
        // Create/show expanded content
        let expandedDiv = row.querySelector('.issue-expanded-content');
        
        if (isExpanded && !expandedDiv) {
            // v3.0.122: FIX - Use filteredIssues, not issues array
            // The index parameter is the globalIdx from renderIssuesList which is based on filteredIssues
            const issue = State.filteredIssues[index];
            if (!issue) return;
            
            expandedDiv = document.createElement('div');
            expandedDiv.className = 'issue-expanded-content';
            
            let html = '';
            
            // "Why it matters" section
            const whyItMatters = getWhyItMatters(issue);
            if (whyItMatters) {
                html += `
                    <div class="expanded-why-matters" style="background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: var(--radius-md); padding: var(--space-3); margin-bottom: var(--space-3);">
                        <h5 style="color: var(--info); font-size: var(--font-size-xs); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: var(--space-1);"><i data-lucide="info" style="width:12px;height:12px;display:inline;"></i> Why it matters</h5>
                        <div style="font-size: var(--font-size-sm); color: var(--text-secondary);">${escapeHtml(whyItMatters)}</div>
                    </div>
                `;
            }
            
            // Context with highlighted flagged text
            if (issue.flagged_text || issue.context) {
                const context = issue.context || '';
                const flagged = issue.flagged_text || '';
                
                // v3.0.94: Process highlight markers («...») and escape HTML
                let contextHtml = processContextWithHighlights(context || flagged, flagged);
                
                // v3.0.94: Build location header (page and section)
                let locationHeader = '';
                const locationParts = [];
                if (issue.page) {
                    locationParts.push(`Page ${issue.page}`);
                }
                if (issue.section) {
                    const sectionText = issue.section.length > 50 
                        ? issue.section.substring(0, 47) + '...' 
                        : issue.section;
                    locationParts.push(`§ ${sectionText}`);
                }
                if (locationParts.length > 0) {
                    locationHeader = `
                        <div class="context-location" style="font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: var(--space-2); display: flex; align-items: center; gap: var(--space-2);">
                            <i data-lucide="map-pin" style="width:12px;height:12px;"></i>
                            <span>${escapeHtml(locationParts.join(' • '))}</span>
                        </div>
                    `;
                }
                
                html += `
                    <div class="expanded-context">
                        <h5>Context</h5>
                        ${locationHeader}
                        <div class="expanded-context-text">${contextHtml}</div>
                    </div>
                `;
            }
            
            // Provenance info section (v3.0.24)
            html += renderProvenanceInfo(issue);
            
            // Suggestion with better styling
            if (issue.suggestion) {
                html += `
                    <div class="expanded-suggestion" style="background: rgba(22, 163, 74, 0.08); border: 1px solid rgba(22, 163, 74, 0.2); border-radius: var(--radius-md); padding: var(--space-3); margin-top: var(--space-2);">
                        <h5 style="color: var(--success); font-size: var(--font-size-xs); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: var(--space-1);"><i data-lucide="check-circle" style="width:12px;height:12px;display:inline;"></i> Suggested fix</h5>
                        <div style="font-size: var(--font-size-sm);">${escapeHtml(issue.suggestion)}</div>
                    </div>
                `;
            }
            
            // SAFE: all dynamic content escaped via escapeHtml() or processContextWithHighlights()
            expandedDiv.innerHTML = html;
            row.appendChild(expandedDiv);
            
            refreshIcons();
        }
    }
    
    /**
     * Render provenance information for an issue.
     * Shows validation status and original vs normalized text when relevant.
     * @param {Object} issue - Issue object with optional source field
     * @returns {string} HTML string for provenance section
     */
    function renderProvenanceInfo(issue) {
        if (!issue.source) return '';
        
        const source = issue.source;
        
        // Only show if validated or if there's interesting provenance info
        if (!source.is_validated && !source.original_text) return '';
        
        // Check if original differs from normalized (interesting case)
        const hasDifference = source.original_text && source.normalized_text && 
                             source.original_text !== source.normalized_text;
        
        // Build provenance content
        let content = '';
        
        // Validation status with icon
        if (source.is_validated) {
            content += `
                <div style="display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-2);">
                    <i data-lucide="check-circle" style="width:14px;height:14px;color:var(--success);"></i>
                    <span style="color: var(--success); font-weight: 500;">Validated in original document</span>
                </div>
            `;
        }
        
        // Show original text if different from normalized
        if (hasDifference) {
            content += `
                <div style="margin-top: var(--space-2);">
                    <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: var(--space-1);">Original text:</div>
                    <code style="background: var(--bg-tertiary); padding: 2px 6px; border-radius: 3px; font-size: var(--font-size-sm);">${escapeHtml(source.original_text)}</code>
                </div>
                <div style="margin-top: var(--space-2);">
                    <div style="font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: var(--space-1);">Matched as:</div>
                    <code style="background: var(--bg-tertiary); padding: 2px 6px; border-radius: 3px; font-size: var(--font-size-sm);">${escapeHtml(source.normalized_text)}</code>
                </div>
            `;
        }
        
        // Show validation note if present
        if (source.validation_note) {
            content += `
                <div style="margin-top: var(--space-2); font-size: var(--font-size-xs); color: var(--text-muted); font-style: italic;">
                    ${escapeHtml(source.validation_note)}
                </div>
            `;
        }
        
        // Show location info (paragraph and offsets) - collapsible for power users
        if (typeof source.paragraph_index === 'number' || (source.start_offset >= 0 && source.end_offset >= 0)) {
            const locationParts = [];
            if (typeof source.paragraph_index === 'number') {
                locationParts.push(`Paragraph ${source.paragraph_index}`);
            }
            if (source.start_offset >= 0 && source.end_offset >= 0) {
                locationParts.push(`chars ${source.start_offset}-${source.end_offset}`);
            }
            if (locationParts.length > 0) {
                content += `
                    <div style="margin-top: var(--space-2); font-size: var(--font-size-xs); color: var(--text-muted);">
                        <i data-lucide="map-pin" style="width:10px;height:10px;display:inline;"></i> ${locationParts.join(', ')}
                    </div>
                `;
            }
        }
        
        if (!content) return '';
        
        return `
            <div class="expanded-provenance" style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: var(--radius-md); padding: var(--space-3); margin-top: var(--space-2);">
                <h5 style="color: rgb(139, 92, 246); font-size: var(--font-size-xs); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: var(--space-1);"><i data-lucide="file-search" style="width:12px;height:12px;display:inline;"></i> Source verification</h5>
                ${content}
            </div>
        `;
    }
    
    /**
     * Get "Why it matters" explanation based on issue category/severity.
     * @param {Object} issue - Issue object
     * @returns {string|null}
     */
    function getWhyItMatters(issue) {
        const category = (issue.category || '').toLowerCase();
        const severity = (issue.severity || '').toLowerCase();
        
        // Category-specific explanations
        const categoryExplanations = {
            'undefined acronym': 'Readers may not understand technical acronyms without definitions, leading to confusion and misinterpretation.',
            'acronym': 'Undefined or inconsistent acronyms reduce document clarity and accessibility for new team members.',
            'passive voice': 'Passive voice obscures who is responsible for actions, which can lead to accountability gaps in technical procedures.',
            'ambiguous language': 'Vague terms create interpretation differences between readers, potentially causing implementation errors.',
            'long sentence': 'Long sentences are harder to parse and increase cognitive load, reducing comprehension and retention.',
            'readability': 'Complex writing increases the risk of misunderstanding, especially for international readers or under time pressure.',
            'spelling': 'Spelling errors undermine document credibility and can cause confusion if technical terms are misspelled.',
            'grammar': 'Grammar issues reduce professionalism and can change the intended meaning of requirements.',
            'punctuation': 'Missing or incorrect punctuation can alter meaning, especially in lists and technical specifications.',
            'consistency': 'Inconsistent terminology confuses readers and may indicate incomplete review or multiple authors.',
            'requirement': 'Poorly written requirements lead to implementation defects, rework, and scope disputes.',
            'verb usage': 'Weak or unclear verbs make it difficult to determine what action is actually required.',
            'figure': 'Figure/table reference issues make documents harder to navigate and can break in future revisions.',
            'hyperlink': 'Broken or invalid links prevent readers from accessing referenced information.',
            'structure': 'Structural issues make documents harder to navigate and maintain.',
            'formatting': 'Inconsistent formatting reduces readability and professional appearance.',
            'terminology': 'Inconsistent or undefined terminology creates ambiguity in technical communications.',
            'capitalization': 'Inconsistent capitalization can change meaning and reduces document polish.',
            'duplicate': 'Duplicate content wastes reader time and creates maintenance burden when updates are needed.'
        };
        
        // Check for matching category
        for (const [key, explanation] of Object.entries(categoryExplanations)) {
            if (category.includes(key)) {
                return explanation;
            }
        }
        
        // Severity-based fallback
        if (severity === 'critical') {
            return 'This critical issue could block document approval or cause significant problems in production.';
        } else if (severity === 'high') {
            return 'High severity issues should be addressed before publication to maintain document quality.';
        } else if (severity === 'medium') {
            return 'Addressing this issue will improve document clarity and reduce reader confusion.';
        }
        
        return null;
    }
    
    // ========================================
    // CHART RENDERING
    // ========================================
    
    /**
     * Render severity and category charts.
     * @param {Object} data - Review data with by_severity and by_category
     */
    function renderCharts(data) {
        const State = getState();
        if (!State.settings.showCharts) return;
        
        const SEVERITY_COLORS = getSeverityColors();

        // Skip rebuild if data unchanged
        const sevData = data.by_severity || {};
        const catData = data.by_category || {};
        const sevHash = JSON.stringify(sevData);
        const catHash = JSON.stringify(catData);
        
        // Severity pie chart
        const sevCtx = document.getElementById('chart-severity')?.getContext('2d');
        if (sevCtx && sevHash !== lastChartData.severity) {
            if (severityChart) severityChart.destroy();
            lastChartData.severity = sevHash;
            
            severityChart = new Chart(sevCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(sevData),
                    datasets: [{
                        data: Object.values(sevData),
                        backgroundColor: Object.keys(sevData).map(s => SEVERITY_COLORS[s] || '#7F8C8D'),
                        borderWidth: 2,
                        borderColor: 'rgba(255,255,255,0.15)',
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
                        duration: 800,
                        easing: 'easeOutQuart'
                    },
                    plugins: {
                        legend: { 
                            position: 'bottom', 
                            labels: { 
                                boxWidth: 12, 
                                padding: 14,
                                font: { size: 11, weight: '500' },
                                usePointStyle: true,
                                pointStyle: 'circle'
                            } 
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.85)',
                            titleFont: { size: 13, weight: 'bold' },
                            bodyFont: { size: 12 },
                            padding: 12,
                            cornerRadius: 8,
                            displayColors: true,
                            callbacks: {
                                label: function(context) {
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((context.raw / total) * 100).toFixed(1) : '0.0';
                                    return ` ${context.raw} issues (${percentage}%)`;
                                }
                            }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = Object.keys(sevData)[index];
                            setChartFilter('severity', label);
                            toast('info', `Filtering by ${label} severity`);
                        }
                    },
                    onHover: (event, elements) => {
                        event.native.target.style.cursor = elements.length ? 'pointer' : 'default';
                    }
                }
            });
        }

        // Category bar chart
        const catCtx = document.getElementById('chart-categories')?.getContext('2d');
        if (catCtx && catHash !== lastChartData.category) {
            if (categoryChart) categoryChart.destroy();
            lastChartData.category = catHash;
            
            const sortedCats = Object.entries(catData).sort((a, b) => b[1] - a[1]).slice(0, 8);
            const fullLabels = sortedCats.map(c => c[0]);
            const maxValue = Math.max(...sortedCats.map(c => c[1]));
            
            // Generate gradient colors based on value
            const colors = sortedCats.map((c, i) => {
                const intensity = 0.5 + (c[1] / maxValue) * 0.4;
                return `rgba(74, 144, 217, ${intensity})`;
            });
            
            categoryChart = new Chart(catCtx, {
                type: 'bar',
                data: {
                    labels: sortedCats.map(c => truncate(c[0], 15)),
                    datasets: [{
                        data: sortedCats.map(c => c[1]),
                        backgroundColor: colors,
                        borderColor: 'rgba(74, 144, 217, 0.95)',
                        borderWidth: 1,
                        borderRadius: 4,
                        hoverBackgroundColor: 'rgba(74, 144, 217, 0.95)',
                        hoverBorderColor: '#fff',
                        hoverBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    animation: {
                        duration: 1000,
                        easing: 'easeOutQuart',
                        delay: (context) => context.dataIndex * 80
                    },
                    plugins: { 
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.85)',
                            titleFont: { size: 13, weight: 'bold' },
                            bodyFont: { size: 12 },
                            padding: 12,
                            cornerRadius: 8,
                            callbacks: {
                                title: (items) => fullLabels[items[0].dataIndex],
                                label: function(context) {
                                    return ` ${context.raw} issues`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { 
                            beginAtZero: true, 
                            ticks: { precision: 0 },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        },
                        y: { 
                            ticks: { font: { size: 11 } },
                            grid: { display: false }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = fullLabels[index];
                            setChartFilter('category', label);
                            toast('info', `Filtering by "${label}"`);
                        }
                    },
                    onHover: (event, elements) => {
                        event.native.target.style.cursor = elements.length ? 'pointer' : 'default';
                    }
                }
            });
        }
    }
    
    /**
     * Set a chart-based filter (called by chart click handlers).
     * @param {string} type - 'severity' or 'category'
     * @param {string} value - The value to filter by
     */
    function setChartFilter(type, value) {
        const FilterState = getFilterState();
        if (FilterState) {
            FilterState.chartFilter = { type, value };
        }
        // Call applyFilters from app.js
        if (typeof window.applyFilters === 'function') {
            window.applyFilters();
        }
    }
    
    /**
     * Clear the chart-based filter.
     */
    function clearChartFilter() {
        const FilterState = getFilterState();
        if (FilterState) {
            FilterState.chartFilter = null;
        }
        if (typeof window.applyFilters === 'function') {
            window.applyFilters();
        }
    }
    
    /**
     * Destroy chart instances (for cleanup).
     */
    function destroyCharts() {
        if (severityChart) {
            severityChart.destroy();
            severityChart = null;
        }
        if (categoryChart) {
            categoryChart.destroy();
            categoryChart = null;
        }
        lastChartData = { severity: null, category: null };
    }
    
    // ========================================
    // DASHBOARD COMPONENTS
    // ========================================
    
    /**
     * Render the section heatmap showing issue density across document.
     * @param {Array} issues - Issues array
     * @param {number} totalParagraphs - Total paragraph count
     */
    function renderSectionHeatmap(issues, totalParagraphs) {
        const container = document.getElementById('section-heatmap');
        // v3.0.114: Use combined analytics panel instead of separate wrapper
        const combinedPanel = document.getElementById('issue-analytics-combined');
        const legacyWrapper = document.getElementById('section-heatmap-container');

        if (!container) return;

        // Need at least some issues and paragraphs
        if (!issues || issues.length === 0 || totalParagraphs < 5) {
            // Combined panel visibility is controlled by renderIssueHeatmap
            if (legacyWrapper) legacyWrapper.style.display = 'none';
            return;
        }

        // v3.0.116: 3D Carousel with drag/slider interaction
        // Aim for ~20 paragraphs per section, minimum 5 sections
        const idealSectionSize = 20;
        const numSections = Math.max(5, Math.ceil(totalParagraphs / idealSectionSize));
        const sectionSize = Math.ceil(totalParagraphs / numSections);

        // Count issues per section
        const sectionCounts = new Array(numSections).fill(0);
        issues.forEach(issue => {
            const paraIdx = issue.paragraph_index || 0;
            const sectionIdx = Math.min(numSections - 1, Math.floor(paraIdx / sectionSize));
            sectionCounts[sectionIdx]++;
        });

        // Find max for normalization
        const maxCount = Math.max(...sectionCounts, 1);

        // Build 3D carousel blocks
        const blocks = sectionCounts.map((count, idx) => {
            const intensity = count / maxCount;
            let densityClass = 'density-none';
            if (intensity > 0.7) densityClass = 'density-high';
            else if (intensity > 0.3) densityClass = 'density-medium';
            else if (intensity > 0) densityClass = 'density-low';

            const startPara = idx * sectionSize + 1;
            const endPara = Math.min((idx + 1) * sectionSize, totalParagraphs);

            return `<div class="carousel-block ${densityClass}"
                         data-section="${idx}"
                         data-start="${startPara}"
                         data-end="${endPara}"
                         data-count="${count}">
                        <div class="block-cube">
                            <div class="cube-front">
                                <span class="block-label">§${idx + 1}</span>
                                <span class="block-count">${count}</span>
                                <span class="block-range">¶${startPara}-${endPara}</span>
                            </div>
                        </div>
                    </div>`;
        }).join('');

        // Generate unique ID for this carousel instance
        const carouselId = 'section-carousel-' + Date.now();

        // SAFE: static HTML structure with numeric values
        container.innerHTML = `
            <div class="section-carousel-wrapper">
                <div class="section-carousel" id="${carouselId}">
                    <div class="carousel-track">${blocks}</div>
                </div>
                <div class="carousel-controls">
                    <input type="range" class="carousel-slider" min="0" max="360" value="0" />
                </div>
            </div>
        `;

        // v3.0.114: Combined panel visibility is controlled by renderIssueHeatmap
        if (legacyWrapper) legacyWrapper.style.display = 'none';

        // v3.0.120: Setup 3D horizontal arc carousel (like reference image)
        const carousel = container.querySelector('.section-carousel');
        const track = container.querySelector('.carousel-track');
        const slider = container.querySelector('.carousel-slider');
        const blockElements = container.querySelectorAll('.carousel-block');

        if (carousel && track && slider && blockElements.length > 0) {
            const numBlocks = blockElements.length;
            // Show max 5 blocks at a time in the arc
            const visibleCount = Math.min(5, numBlocks);
            let currentIndex = 0; // Center block index

            // Position blocks in a horizontal arc
            function positionBlocks(centerIdx) {
                blockElements.forEach((block, idx) => {
                    // Calculate distance from center (wrapping around)
                    let offset = idx - centerIdx;
                    // Wrap around for circular behavior
                    if (offset > numBlocks / 2) offset -= numBlocks;
                    if (offset < -numBlocks / 2) offset += numBlocks;

                    // Position calculations
                    const absOffset = Math.abs(offset);
                    const maxVisible = Math.floor(visibleCount / 2);

                    if (absOffset > maxVisible + 0.5) {
                        // Hide blocks too far from center
                        block.style.opacity = '0';
                        block.style.pointerEvents = 'none';
                        block.style.transform = `translateX(${offset * 95}px) translateZ(-200px) scale(0.3)`;
                        block.style.zIndex = '0';
                    } else {
                        // Visible blocks - create arc effect
                        const x = offset * 90; // Horizontal spacing (larger for bigger boxes)
                        const z = -absOffset * absOffset * 22; // Depth (parabolic curve)
                        const scale = 1 - absOffset * 0.12; // Scale down sides
                        const opacity = 1 - absOffset * 0.15; // Fade sides slightly
                        const zIndex = 10 - absOffset;

                        block.style.transform = `translateX(${x}px) translateZ(${z}px) scale(${scale})`;
                        block.style.opacity = opacity.toString();
                        block.style.zIndex = zIndex.toString();
                        block.style.pointerEvents = 'auto';
                    }
                });
            }

            // Initial position - center on first block
            positionBlocks(0);

            // Slider controls which block is centered
            slider.max = numBlocks - 1;
            slider.value = 0;
            slider.addEventListener('input', () => {
                currentIndex = parseInt(slider.value);
                positionBlocks(currentIndex);
            });

            // Continuous spin while dragging
            let isDragging = false;
            let lastX = 0;
            let spinInterval = null;
            let spinDirection = 0;

            function startSpin(direction) {
                if (spinInterval) return;
                spinDirection = direction;
                spinInterval = setInterval(() => {
                    currentIndex = (currentIndex + spinDirection + numBlocks) % numBlocks;
                    slider.value = currentIndex;
                    positionBlocks(currentIndex);
                }, 150); // Spin speed - lower = faster
            }

            function stopSpin() {
                if (spinInterval) {
                    clearInterval(spinInterval);
                    spinInterval = null;
                }
                spinDirection = 0;
            }

            carousel.addEventListener('mousedown', (e) => {
                isDragging = true;
                lastX = e.pageX;
                carousel.style.cursor = 'grabbing';
                e.preventDefault();
            });

            document.addEventListener('mouseup', () => {
                if (isDragging) {
                    isDragging = false;
                    carousel.style.cursor = 'grab';
                    stopSpin();
                }
            });

            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                const diff = e.pageX - lastX;

                // Continuous spinning based on drag direction
                if (Math.abs(diff) > 15) { // Threshold to start spinning
                    const direction = diff > 0 ? -1 : 1; // Drag right = spin left (previous), drag left = spin right (next)
                    if (spinDirection !== direction) {
                        stopSpin();
                        startSpin(direction);
                    }
                    lastX = e.pageX; // Reset for continuous dragging
                }
            });

            // Touch support with continuous spin
            // BUG-L10 FIX: Added { passive: true } to prevent scroll-blocking violations
            let lastTouchX = 0;
            carousel.addEventListener('touchstart', (e) => {
                lastTouchX = e.touches[0].pageX;
            }, { passive: true });

            carousel.addEventListener('touchmove', (e) => {
                const diff = e.touches[0].pageX - lastTouchX;
                if (Math.abs(diff) > 15) {
                    const direction = diff > 0 ? -1 : 1;
                    if (spinDirection !== direction) {
                        stopSpin();
                        startSpin(direction);
                    }
                    lastTouchX = e.touches[0].pageX;
                }
            }, { passive: true });

            carousel.addEventListener('touchend', () => {
                stopSpin();
            });
        }

        // Add click handlers for filtering
        container.querySelectorAll('.carousel-block').forEach(block => {
            block.addEventListener('click', () => {
                const start = parseInt(block.dataset.start);
                const end = parseInt(block.dataset.end);
                filterIssuesByParagraphRange(start, end);
            });
        });
    }
    
    /**
     * Filter issues to show only those in a specific paragraph range.
     * @param {number} start - Start paragraph (1-indexed)
     * @param {number} end - End paragraph (1-indexed)
     */
    function filterIssuesByParagraphRange(start, end) {
        const State = getState();
        State.filteredIssues = State.issues.filter(issue => {
            const paraIdx = (issue.paragraph_index || 0) + 1; // 1-indexed for display
            return paraIdx >= start && paraIdx <= end;
        });
        renderIssuesList();
        toast('info', `Showing issues from paragraphs ${start}-${end}`);
    }
    
    /**
     * Render smart recommendations based on analysis results.
     * @param {Object} data - Full review results object
     */
    function renderSmartRecommendations(data) {
        const container = document.getElementById('recommendations-list');
        const wrapper = document.getElementById('smart-recommendations');
        
        if (!container || !wrapper) return;
        
        const recommendations = generateRecommendations(data);
        
        if (recommendations.length === 0) {
            wrapper.style.display = 'none';
            return;
        }
        
        container.innerHTML = recommendations.map((rec, idx) => `
            <div class="recommendation-item priority-${escapeHtml(rec.priority)}">
                <div class="rec-icon">
                    <i data-lucide="${escapeHtml(rec.icon)}"></i>
                </div>
                <div class="rec-content">
                    <strong>${escapeHtml(rec.title)}</strong>
                    <p>${escapeHtml(rec.description)}</p>
                </div>
                <div class="rec-action">
                    ${rec.action ? `<button class="btn btn-xs btn-primary" onclick="${escapeHtml(rec.action)}">${escapeHtml(rec.actionText)}</button>` : ''}
                </div>
            </div>
        `).join(''); // SAFE: all dynamic content escaped
        
        wrapper.style.display = 'block';
        
        // Setup dismiss button
        document.getElementById('btn-dismiss-recommendations')?.addEventListener('click', () => {
            wrapper.style.display = 'none';
            sessionStorage.setItem('twr_recommendations_dismissed', 'true');
        });
        
        refreshIcons();
    }
    
    /**
     * Generate prioritized recommendations based on analysis patterns.
     * @param {Object} data - Review data
     * @returns {Array} Array of recommendation objects
     */
    function generateRecommendations(data) {
        const recs = [];
        const issues = data.issues || [];
        const byCategory = data.by_category || {};
        const bySeverity = data.by_severity || {};
        const score = data.score || 100;
        
        // Critical issues first
        if ((bySeverity.Critical || 0) > 0) {
            recs.push({
                priority: 'critical',
                icon: 'alert-octagon',
                title: `${bySeverity.Critical} Critical Issue${bySeverity.Critical > 1 ? 's' : ''} Found`,
                description: 'Critical issues should be addressed immediately before publication.',
                action: "setChartFilter('severity', 'Critical')",
                actionText: 'View Critical'
            });
        }
        
        // High frequency category
        const topCategory = Object.entries(byCategory).sort((a, b) => b[1] - a[1])[0];
        if (topCategory && topCategory[1] >= 5) {
            recs.push({
                priority: 'high',
                icon: 'trending-up',
                title: `${topCategory[0]} is Most Common (${topCategory[1]} issues)`,
                description: `Consider focusing on ${topCategory[0].toLowerCase()} issues for maximum impact.`,
                action: `setChartFilter('category', '${topCategory[0].replace(/'/g, "\\'")}')`,
                actionText: 'Filter'
            });
        }
        
        // Readability concerns
        const readability = data.readability || {};
        if (readability.flesch_kincaid_grade > 14) {
            recs.push({
                priority: 'medium',
                icon: 'book-open',
                title: 'High Reading Level Detected',
                description: `Grade level ${readability.flesch_kincaid_grade?.toFixed(1)} may be too complex for general audiences. Consider simplifying sentences.`,
                action: null
            });
        }
        
        // Low score warning
        if (score < 60) {
            recs.push({
                priority: 'high',
                icon: 'alert-triangle',
                title: 'Document Needs Significant Revision',
                description: `Score of ${score} indicates substantial quality issues. Recommend thorough review.`,
                action: null
            });
        }
        
        // Acronym issues
        if ((byCategory['Undefined Acronym'] || byCategory['Acronyms'] || 0) >= 3) {
            const acronymCount = byCategory['Undefined Acronym'] || byCategory['Acronyms'] || 0;
            recs.push({
                priority: 'medium',
                icon: 'file-text',
                title: `${acronymCount} Undefined Acronyms`,
                description: 'Consider adding an acronym list or defining terms on first use.',
                action: null
            });
        }
        
        // Good job message if high score
        if (score >= 90 && issues.length < 10) {
            recs.push({
                priority: 'low',
                icon: 'check-circle',
                title: 'Excellent Document Quality!',
                description: 'Your document is well-written with minimal issues. Great work!',
                action: null
            });
        }
        
        // Limit to top 3 recommendations
        return recs.slice(0, 3);
    }
    
    // ========================================
    // ENHANCED STATS PANEL
    // ========================================
    
    /**
     * Render enhanced statistics panel.
     * @param {Object} enhancedStats - Enhanced stats from core.py
     */
    function renderEnhancedStats(enhancedStats) {
        if (!enhancedStats) return;
        
        const container = document.getElementById('enhanced-stats-panel');
        if (!container) {
            createEnhancedStatsPanel(enhancedStats);
            return;
        }
        
        updateEnhancedStatsPanel(enhancedStats);
    }
    
    /**
     * Create the enhanced stats panel in the dashboard.
     */
    function createEnhancedStatsPanel(stats) {
        const dashboard = document.getElementById('dashboard-container');
        if (!dashboard) return;
        
        // Find insertion point (after existing cards)
        const existingCards = dashboard.querySelector('.dashboard-grid');
        if (!existingCards) return;
        
        const panel = document.createElement('div');
        panel.id = 'enhanced-stats-panel';
        panel.className = 'enhanced-stats-panel';
        
        // SAFE: buildEnhancedStatsHTML escapes all server data
        panel.innerHTML = buildEnhancedStatsHTML(stats);
        
        // Insert after main dashboard grid
        existingCards.parentNode.insertBefore(panel, existingCards.nextSibling);
        
        refreshIcons();
    }
    
    /**
     * Update existing enhanced stats panel.
     */
    function updateEnhancedStatsPanel(stats) {
        const container = document.getElementById('enhanced-stats-panel');
        if (!container) return;
        
        // SAFE: buildEnhancedStatsHTML escapes all server data
        container.innerHTML = buildEnhancedStatsHTML(stats);
        
        refreshIcons();
    }
    
    /**
     * Build HTML for enhanced stats panel.
     */
    function buildEnhancedStatsHTML(stats) {
        const docType = stats.detected_doc_type || { type: 'general', confidence: 0 };
        const health = stats.health_score || { total: 0, breakdown: {}, grade: 'F' };
        const roleSummary = stats.role_summary || { total_unique: 0, high_confidence: 0, top_roles: [] };
        
        // Document type badge color
        const typeColors = {
            'requirements': '#3B82F6',
            'design': '#8B5CF6',
            'test': '#10B981',
            'plan': '#F59E0B',
            'report': '#6366F1',
            'procedure': '#EC4899',
            'general': '#6B7280'
        };
        const typeColor = typeColors[docType.type] || typeColors.general;
        
        // Health grade color
        const gradeColors = { 'A': '#22C55E', 'B': '#3B82F6', 'C': '#F59E0B', 'D': '#F97316', 'F': '#EF4444' };
        const gradeColor = gradeColors[health.grade] || '#6B7280';
        
        return `
            <div class="enhanced-stats-grid">
                <!-- Document Type Detection -->
                <div class="enhanced-stat-card">
                    <div class="stat-card-header">
                        <i data-lucide="file-text"></i>
                        <span>Document Type</span>
                    </div>
                    <div class="stat-card-body">
                        <span class="doc-type-badge" style="background: ${typeColor}">
                            ${escapeHtml(docType.type.charAt(0).toUpperCase() + docType.type.slice(1))}
                        </span>
                        <small>${Math.round(docType.confidence * 100)}% confidence</small>
                    </div>
                </div>
                
                <!-- Health Score Breakdown -->
                <div class="enhanced-stat-card health-breakdown-card">
                    <div class="stat-card-header">
                        <i data-lucide="heart-pulse"></i>
                        <span>Health Breakdown</span>
                    </div>
                    <div class="stat-card-body">
                        <div class="health-grade" style="color: ${gradeColor}">
                            ${health.grade}
                        </div>
                        <div class="health-bars">
                            ${buildHealthBar('Severity', health.breakdown?.severity_impact || 0, 40)}
                            ${buildHealthBar('Readability', health.breakdown?.readability || 0, 20)}
                            ${buildHealthBar('Structure', health.breakdown?.structure || 0, 20)}
                            ${buildHealthBar('Completeness', health.breakdown?.completeness || 0, 20)}
                        </div>
                    </div>
                </div>
                
                <!-- Role Summary -->
                <div class="enhanced-stat-card">
                    <div class="stat-card-header">
                        <i data-lucide="users"></i>
                        <span>Roles Detected</span>
                    </div>
                    <div class="stat-card-body">
                        <div class="role-stats">
                            <div class="role-stat">
                                <span class="role-stat-value">${roleSummary.total_unique}</span>
                                <span class="role-stat-label">Unique</span>
                            </div>
                            <div class="role-stat">
                                <span class="role-stat-value role-high">${roleSummary.high_confidence}</span>
                                <span class="role-stat-label">High Conf.</span>
                            </div>
                        </div>
                        ${roleSummary.top_roles && roleSummary.top_roles.length > 0 ? `
                            <div class="top-roles">
                                ${roleSummary.top_roles.slice(0, 3).map(r => 
                                    `<span class="role-chip">${escapeHtml(r.name)} (${r.count})</span>`
                                ).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
                
                <!-- Issue Metrics -->
                <div class="enhanced-stat-card">
                    <div class="stat-card-header">
                        <i data-lucide="bar-chart-2"></i>
                        <span>Issue Metrics</span>
                    </div>
                    <div class="stat-card-body">
                        <div class="metric-row">
                            <span>Density</span>
                            <span class="metric-value">${stats.issue_density_per_1k_words || 0}/1k words</span>
                        </div>
                        <div class="metric-row">
                            <span>Fixable</span>
                            <span class="metric-value">${stats.fixable_count || 0} auto-fixable</span>
                        </div>
                        <div class="metric-row">
                            <span>Clean §</span>
                            <span class="metric-value">${stats.clean_paragraphs || 0} paragraphs</span>
                        </div>
                        ${buildValidationMetric()}
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Build validation rate metric row for enhanced stats.
     * v3.0.29: Shows provenance validation rate
     */
    function buildValidationMetric() {
        const State = getState();
        if (!State.issues || State.issues.length === 0) return '';
        
        let validated = 0;
        let total = State.issues.length;
        
        State.issues.forEach(issue => {
            if (issue?.source?.is_validated === true) {
                validated++;
            }
        });
        
        const rate = total > 0 ? Math.round((validated / total) * 100) : 0;
        const color = rate >= 80 ? 'var(--success)' : rate >= 50 ? 'var(--warning)' : 'var(--text-muted)';
        
        return `
            <div class="metric-row" title="Percentage of issues with verified source location">
                <span><i data-lucide="check-circle" style="width:12px;height:12px;display:inline;color:${color};"></i> Validated</span>
                <span class="metric-value" style="color:${color};">${validated}/${total} (${rate}%)</span>
            </div>
        `;
    }
    
    /**
     * Build a health score bar component.
     */
    function buildHealthBar(label, value, max) {
        const pct = Math.round((value / max) * 100);
        const color = pct >= 80 ? '#22C55E' : pct >= 60 ? '#3B82F6' : pct >= 40 ? '#F59E0B' : '#EF4444';
        
        return `
            <div class="health-bar-row">
                <span class="health-bar-label">${label}</span>
                <div class="health-bar-track">
                    <div class="health-bar-fill" style="width: ${pct}%; background: ${color}"></div>
                </div>
                <span class="health-bar-value">${Math.round(value)}/${max}</span>
            </div>
        `;
    }
    
    // ========================================
    // ICON REFRESH HELPER
    // ========================================
    
    /**
     * Refresh lucide icons in the DOM.
     */
    function refreshIcons() {
        if (typeof lucide !== 'undefined') {
            try { lucide.createIcons(); } catch(e) {}
        }
    }
    
    // ========================================
    // PUBLIC API
    // ========================================
    
    return {
        // Stats
        setStatValue,
        updateStats,
        updateSelectionUI,
        getScoreColor,
        
        // Selection
        isIssueSelected,
        toggleIssueSelection,
        selectIssues,
        
        // Issue list
        renderIssuesList,
        updatePagination,
        changePage,
        navigateIssues,
        toggleIssueExpand,
        getWhyItMatters,
        renderProvenanceInfo,
        
        // Charts
        renderCharts,
        setChartFilter,
        clearChartFilter,
        destroyCharts,
        
        // Dashboard
        renderSectionHeatmap,
        filterIssuesByParagraphRange,
        renderSmartRecommendations,
        generateRecommendations,
        renderEnhancedStats,
        
        // Utilities
        refreshIcons
    };
})();

// ========================================
// GLOBAL ALIASES (Backward Compatibility)
// ========================================
window.setStatValue = TWR.Renderers.setStatValue;
window.updateStats = TWR.Renderers.updateStats;
window.updateSelectionUI = TWR.Renderers.updateSelectionUI;
window.getScoreColor = TWR.Renderers.getScoreColor;

window.isIssueSelected = TWR.Renderers.isIssueSelected;
window.toggleIssueSelection = TWR.Renderers.toggleIssueSelection;
window.selectIssues = TWR.Renderers.selectIssues;

window.renderIssuesList = TWR.Renderers.renderIssuesList;
window.updatePagination = TWR.Renderers.updatePagination;
window.changePage = TWR.Renderers.changePage;
window.navigateIssues = TWR.Renderers.navigateIssues;
window.toggleIssueExpand = TWR.Renderers.toggleIssueExpand;
window.getWhyItMatters = TWR.Renderers.getWhyItMatters;

window.renderCharts = TWR.Renderers.renderCharts;
window.setChartFilter = TWR.Renderers.setChartFilter;
window.clearChartFilter = TWR.Renderers.clearChartFilter;

window.renderSectionHeatmap = TWR.Renderers.renderSectionHeatmap;
window.filterIssuesByParagraphRange = TWR.Renderers.filterIssuesByParagraphRange;
window.renderSmartRecommendations = TWR.Renderers.renderSmartRecommendations;
window.renderEnhancedStats = TWR.Renderers.renderEnhancedStats;

console.log('[TWR] Renderers module loaded');
