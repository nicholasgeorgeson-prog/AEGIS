/**
 * AEGIS - Statement Forge Review Mode
 * ===============================================
 * ENH-006: Review mode with source context and statement creation.
 *
 * Features:
 * - View source document context for any extracted statement
 * - Navigate between statements and their source locations
 * - Highlight text in document to create new statements
 * - Full editing capabilities with Statement Forge features
 *
 * Version: 1.0.0
 * Date: 2026-02-02
 */

'use strict';

window.TWR = window.TWR || {};

TWR.StatementReviewMode = (function() {
    const VERSION = '1.0.0';
    const LOG_PREFIX = '[TWR StatementReviewMode]';

    // ============================================================
    // STATE
    // ============================================================

    const State = {
        isOpen: false,
        currentStatementId: null,
        currentStatementIndex: -1,
        statements: [],
        documentText: '',
        documentName: '',
        selection: null,
        modal: null
    };

    // ============================================================
    // MODAL CREATION
    // ============================================================

    function createModal() {
        if (State.modal) return State.modal;

        const modal = document.createElement('div');
        modal.id = 'statement-review-modal';
        modal.className = 'sf-review-modal';
        modal.innerHTML = `
            <div class="sf-review-overlay"></div>
            <div class="sf-review-container">
                <div class="sf-review-header">
                    <h2>Statement Review Mode</h2>
                    <div class="sf-review-nav">
                        <button class="sf-review-btn sf-review-prev" title="Previous Statement">
                            <span class="arrow">&larr;</span> Previous
                        </button>
                        <span class="sf-review-counter">
                            Statement <span class="current">0</span> of <span class="total">0</span>
                        </span>
                        <button class="sf-review-btn sf-review-next" title="Next Statement">
                            Next <span class="arrow">&rarr;</span>
                        </button>
                    </div>
                    <button class="sf-review-close" title="Close">&times;</button>
                </div>

                <div class="sf-review-body">
                    <!-- Left Panel: Document Source -->
                    <div class="sf-review-source-panel">
                        <div class="sf-review-source-header">
                            <h3>Source Document</h3>
                            <span class="sf-review-doc-name"></span>
                        </div>
                        <div class="sf-review-source-info">
                            <span class="sf-review-section-title"></span>
                            <span class="sf-review-page-info"></span>
                        </div>
                        <div class="sf-review-source-content">
                            <div class="sf-review-context-before"></div>
                            <div class="sf-review-highlight"></div>
                            <div class="sf-review-context-after"></div>
                        </div>
                        <div class="sf-review-source-actions">
                            <button class="sf-review-btn sf-create-from-selection" disabled>
                                Create Statement from Selection
                            </button>
                        </div>
                    </div>

                    <!-- Right Panel: Statement Details -->
                    <div class="sf-review-details-panel">
                        <div class="sf-review-details-header">
                            <h3>Statement Details</h3>
                            <div class="sf-review-status">
                                <span class="sf-review-status-badge"></span>
                            </div>
                        </div>

                        <div class="sf-review-form">
                            <div class="sf-review-field">
                                <label>Number</label>
                                <input type="text" class="sf-review-input" id="review-number" readonly>
                            </div>

                            <div class="sf-review-field">
                                <label>Title</label>
                                <input type="text" class="sf-review-input" id="review-title">
                            </div>

                            <div class="sf-review-field">
                                <label>Directive</label>
                                <select class="sf-review-select" id="review-directive">
                                    <option value="">None</option>
                                    <option value="shall">Shall</option>
                                    <option value="must">Must</option>
                                    <option value="will">Will</option>
                                    <option value="should">Should</option>
                                    <option value="may">May</option>
                                </select>
                            </div>

                            <div class="sf-review-field">
                                <label>Role</label>
                                <input type="text" class="sf-review-input" id="review-role">
                            </div>

                            <div class="sf-review-field sf-review-field-full">
                                <label>Description</label>
                                <textarea class="sf-review-textarea" id="review-description" rows="6"></textarea>
                            </div>

                            <div class="sf-review-field">
                                <label>Level</label>
                                <select class="sf-review-select" id="review-level">
                                    <option value="1">Level 1</option>
                                    <option value="2">Level 2</option>
                                    <option value="3">Level 3</option>
                                    <option value="4">Level 4</option>
                                    <option value="5">Level 5</option>
                                    <option value="6">Level 6</option>
                                </select>
                            </div>

                            <div class="sf-review-field">
                                <label>Section</label>
                                <input type="text" class="sf-review-input" id="review-section">
                            </div>
                        </div>

                        <div class="sf-review-actions">
                            <button class="sf-review-btn sf-review-btn-primary sf-save-statement">
                                Save Changes
                            </button>
                            <button class="sf-review-btn sf-review-btn-secondary sf-approve-statement">
                                Approve
                            </button>
                            <button class="sf-review-btn sf-review-btn-danger sf-reject-statement">
                                Reject
                            </button>
                        </div>
                    </div>
                </div>

                <div class="sf-review-footer">
                    <div class="sf-review-shortcuts">
                        <span><kbd>←</kbd> Previous</span>
                        <span><kbd>→</kbd> Next</span>
                        <span><kbd>S</kbd> Save</span>
                        <span><kbd>A</kbd> Approve</span>
                        <span><kbd>R</kbd> Reject</span>
                        <span><kbd>Esc</kbd> Close</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        State.modal = modal;

        // Attach event listeners
        attachEventListeners(modal);

        return modal;
    }

    // ============================================================
    // EVENT LISTENERS
    // ============================================================

    function attachEventListeners(modal) {
        // Close button
        modal.querySelector('.sf-review-close').addEventListener('click', close);
        modal.querySelector('.sf-review-overlay').addEventListener('click', close);

        // Navigation
        modal.querySelector('.sf-review-prev').addEventListener('click', previousStatement);
        modal.querySelector('.sf-review-next').addEventListener('click', nextStatement);

        // Actions
        modal.querySelector('.sf-save-statement').addEventListener('click', saveStatement);
        modal.querySelector('.sf-approve-statement').addEventListener('click', approveStatement);
        modal.querySelector('.sf-reject-statement').addEventListener('click', rejectStatement);
        modal.querySelector('.sf-create-from-selection').addEventListener('click', createFromSelection);

        // Text selection in source panel
        const sourceContent = modal.querySelector('.sf-review-source-content');
        sourceContent.addEventListener('mouseup', handleTextSelection);

        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeydown);
    }

    function handleKeydown(e) {
        if (!State.isOpen) return;

        // Ignore if user is typing in an input
        if (e.target.matches('input, textarea, select')) {
            if (e.key === 'Escape') {
                e.target.blur();
            }
            return;
        }

        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                previousStatement();
                break;
            case 'ArrowRight':
                e.preventDefault();
                nextStatement();
                break;
            case 's':
            case 'S':
                e.preventDefault();
                saveStatement();
                break;
            case 'a':
            case 'A':
                e.preventDefault();
                approveStatement();
                break;
            case 'r':
            case 'R':
                e.preventDefault();
                rejectStatement();
                break;
            case 'Escape':
                e.preventDefault();
                close();
                break;
        }
    }

    function handleTextSelection() {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();

        State.selection = selectedText.length > 0 ? {
            text: selectedText,
            range: selection.getRangeAt(0).cloneRange()
        } : null;

        // Enable/disable create button
        const createBtn = State.modal.querySelector('.sf-create-from-selection');
        createBtn.disabled = !State.selection;
    }

    // ============================================================
    // NAVIGATION
    // ============================================================

    function previousStatement() {
        if (State.currentStatementIndex > 0) {
            showStatement(State.currentStatementIndex - 1);
        }
    }

    function nextStatement() {
        if (State.currentStatementIndex < State.statements.length - 1) {
            showStatement(State.currentStatementIndex + 1);
        }
    }

    function showStatement(index) {
        if (index < 0 || index >= State.statements.length) return;

        State.currentStatementIndex = index;
        const stmt = State.statements[index];
        State.currentStatementId = stmt.id;

        updateUI(stmt);
        updateNavigation();

        // Log for diagnostics
        if (TWR.Logger) {
            TWR.Logger.logAction('review_statement', { statementId: stmt.id, index });
        }
    }

    // ============================================================
    // UI UPDATES
    // ============================================================

    function updateUI(stmt) {
        const modal = State.modal;

        // Update source panel
        modal.querySelector('.sf-review-doc-name').textContent = stmt.source_document || State.documentName || 'Unknown';
        modal.querySelector('.sf-review-section-title').textContent = stmt.source_section_title || stmt.section || '';
        modal.querySelector('.sf-review-page-info').textContent = stmt.source_page ? `Page ${stmt.source_page}` : '';

        // Update context display
        const contextBefore = modal.querySelector('.sf-review-context-before');
        const highlight = modal.querySelector('.sf-review-highlight');
        const contextAfter = modal.querySelector('.sf-review-context-after');

        contextBefore.textContent = stmt.source_context_before || '';
        highlight.textContent = stmt.description || '';
        contextAfter.textContent = stmt.source_context_after || '';

        // Update form fields
        modal.querySelector('#review-number').value = stmt.number || '';
        modal.querySelector('#review-title').value = stmt.title || '';
        modal.querySelector('#review-directive').value = stmt.directive || '';
        modal.querySelector('#review-role').value = stmt.role || '';
        modal.querySelector('#review-description').value = stmt.description || '';
        modal.querySelector('#review-level').value = stmt.level || 1;
        modal.querySelector('#review-section').value = stmt.section || '';

        // Update status badge
        const statusBadge = modal.querySelector('.sf-review-status-badge');
        if (stmt.modified) {
            statusBadge.textContent = 'Modified';
            statusBadge.className = 'sf-review-status-badge status-modified';
        } else if (stmt.approved) {
            statusBadge.textContent = 'Approved';
            statusBadge.className = 'sf-review-status-badge status-approved';
        } else if (stmt.rejected) {
            statusBadge.textContent = 'Rejected';
            statusBadge.className = 'sf-review-status-badge status-rejected';
        } else {
            statusBadge.textContent = 'Pending';
            statusBadge.className = 'sf-review-status-badge status-pending';
        }
    }

    function updateNavigation() {
        const modal = State.modal;

        modal.querySelector('.sf-review-counter .current').textContent = State.currentStatementIndex + 1;
        modal.querySelector('.sf-review-counter .total').textContent = State.statements.length;

        // Enable/disable nav buttons
        modal.querySelector('.sf-review-prev').disabled = State.currentStatementIndex === 0;
        modal.querySelector('.sf-review-next').disabled = State.currentStatementIndex === State.statements.length - 1;
    }

    // ============================================================
    // ACTIONS
    // ============================================================

    async function saveStatement() {
        const modal = State.modal;
        const stmt = State.statements[State.currentStatementIndex];

        // Gather form data
        const updates = {
            title: modal.querySelector('#review-title').value,
            directive: modal.querySelector('#review-directive').value,
            role: modal.querySelector('#review-role').value,
            description: modal.querySelector('#review-description').value,
            level: parseInt(modal.querySelector('#review-level').value, 10),
            section: modal.querySelector('#review-section').value,
            modified: true
        };

        // Update local state
        Object.assign(stmt, updates);

        // Send to backend
        try {
            const response = await fetch(`/api/statement-forge/statements/${stmt.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRFToken()
                },
                body: JSON.stringify(updates)
            });

            if (response.ok) {
                showToast('Statement saved successfully', 'success');
                updateUI(stmt);

                // Notify Statement Forge to refresh if open
                if (window.StatementForge && typeof window.StatementForge.refresh === 'function') {
                    window.StatementForge.refresh();
                }
            } else {
                throw new Error('Failed to save');
            }
        } catch (error) {
            console.error(LOG_PREFIX, 'Save error:', error);
            showToast('Failed to save statement', 'error');
        }
    }

    function approveStatement() {
        const stmt = State.statements[State.currentStatementIndex];
        stmt.approved = true;
        stmt.rejected = false;
        updateUI(stmt);
        showToast('Statement approved', 'success');

        // Auto-advance to next
        if (State.currentStatementIndex < State.statements.length - 1) {
            setTimeout(() => nextStatement(), 300);
        }
    }

    function rejectStatement() {
        const stmt = State.statements[State.currentStatementIndex];
        stmt.approved = false;
        stmt.rejected = true;
        updateUI(stmt);
        showToast('Statement rejected', 'warning');

        // Auto-advance to next
        if (State.currentStatementIndex < State.statements.length - 1) {
            setTimeout(() => nextStatement(), 300);
        }
    }

    async function createFromSelection() {
        if (!State.selection) return;

        const selectedText = State.selection.text;

        // Create new statement from selection
        const newStatement = {
            title: selectedText.substring(0, 50) + (selectedText.length > 50 ? '...' : ''),
            description: selectedText,
            level: 1,
            section: '',
            directive: detectDirective(selectedText),
            role: '',
            source_document: State.documentName,
            source_context_before: '',
            source_context_after: '',
            modified: true
        };

        try {
            const response = await fetch('/api/statement-forge/statements/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRFToken()
                },
                body: JSON.stringify(newStatement)
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success && result.statement) {
                    State.statements.push(result.statement);
                    showToast('Statement created from selection', 'success');

                    // Show the new statement
                    showStatement(State.statements.length - 1);

                    // Clear selection
                    window.getSelection().removeAllRanges();
                    State.selection = null;
                    State.modal.querySelector('.sf-create-from-selection').disabled = true;
                }
            } else {
                throw new Error('Failed to create');
            }
        } catch (error) {
            console.error(LOG_PREFIX, 'Create error:', error);
            showToast('Failed to create statement', 'error');
        }
    }

    // ============================================================
    // UTILITIES
    // ============================================================

    function detectDirective(text) {
        const lowerText = text.toLowerCase();
        const directives = ['shall', 'must', 'will', 'should', 'may'];
        for (const d of directives) {
            if (lowerText.includes(d)) return d;
        }
        return '';
    }

    function getCSRFToken() {
        // Try to get from meta tag
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');

        // Try to get from cookie
        const match = document.cookie.match(/csrf_token=([^;]+)/);
        return match ? match[1] : '';
    }

    function showToast(message, type = 'info') {
        // Use existing toast system if available
        if (window.showToast) {
            window.showToast(message, type);
            return;
        }

        // Simple fallback toast
        const toast = document.createElement('div');
        toast.className = `sf-review-toast sf-review-toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // ============================================================
    // PUBLIC API
    // ============================================================

    /**
     * Open review mode for a specific statement.
     * @param {string} statementId - ID of statement to show
     * @param {Array} statements - All statements array
     * @param {string} documentName - Source document name
     */
    function open(statementId, statements, documentName = '') {
        State.statements = statements || [];
        State.documentName = documentName;

        // Find the statement index
        let index = 0;
        if (statementId) {
            index = State.statements.findIndex(s => s.id === statementId);
            if (index === -1) index = 0;
        }

        createModal();
        State.modal.classList.add('open');
        State.isOpen = true;

        showStatement(index);

        console.log(LOG_PREFIX, 'Review mode opened for statement:', statementId);
    }

    /**
     * Open review mode at a specific index.
     * @param {number} index - Statement index
     * @param {Array} statements - All statements array
     * @param {string} documentName - Source document name
     */
    function openAtIndex(index, statements, documentName = '') {
        State.statements = statements || [];
        State.documentName = documentName;

        createModal();
        State.modal.classList.add('open');
        State.isOpen = true;

        showStatement(index);
    }

    /**
     * Close review mode.
     */
    function close() {
        if (State.modal) {
            State.modal.classList.remove('open');
        }
        State.isOpen = false;
        State.currentStatementId = null;
        State.currentStatementIndex = -1;

        console.log(LOG_PREFIX, 'Review mode closed');
    }

    /**
     * Check if review mode is open.
     */
    function isOpen() {
        return State.isOpen;
    }

    /**
     * Get the current statement being reviewed.
     */
    function getCurrentStatement() {
        if (State.currentStatementIndex >= 0 && State.currentStatementIndex < State.statements.length) {
            return State.statements[State.currentStatementIndex];
        }
        return null;
    }

    /**
     * Initialize module (attach CSS if needed).
     */
    function init() {
        // Add CSS if not already present
        if (!document.getElementById('sf-review-mode-styles')) {
            const style = document.createElement('style');
            style.id = 'sf-review-mode-styles';
            style.textContent = getCSS();
            document.head.appendChild(style);
        }

        console.log(LOG_PREFIX, 'Module initialized v' + VERSION);
    }

    // ============================================================
    // CSS STYLES
    // ============================================================

    function getCSS() {
        return `
/* Statement Forge Review Mode Styles */
.sf-review-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10000;
}

.sf-review-modal.open {
    display: flex;
    align-items: center;
    justify-content: center;
}

.sf-review-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
}

.sf-review-container {
    position: relative;
    width: 95%;
    max-width: 1400px;
    height: 90%;
    max-height: 900px;
    background: var(--bg-primary, #fff);
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.sf-review-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f5f5f5);
}

.sf-review-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary, #333);
}

.sf-review-nav {
    display: flex;
    align-items: center;
    gap: 16px;
}

.sf-review-counter {
    font-size: 0.875rem;
    color: var(--text-secondary, #666);
}

.sf-review-close {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: var(--text-secondary, #666);
    padding: 4px 8px;
}

.sf-review-close:hover {
    color: var(--text-primary, #333);
}

.sf-review-body {
    flex: 1;
    display: flex;
    overflow: hidden;
}

/* Source Panel */
.sf-review-source-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border-color, #e0e0e0);
}

.sf-review-source-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-tertiary, #fafafa);
}

.sf-review-source-header h3 {
    margin: 0 0 4px 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sf-review-doc-name {
    font-size: 0.875rem;
    color: var(--text-primary, #333);
}

.sf-review-source-info {
    padding: 8px 16px;
    display: flex;
    gap: 16px;
    font-size: 0.813rem;
    color: var(--text-secondary, #666);
    border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.sf-review-source-content {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 1rem;
    line-height: 1.8;
    color: var(--text-primary, #333);
}

.sf-review-context-before,
.sf-review-context-after {
    color: var(--text-secondary, #666);
}

.sf-review-highlight {
    background: linear-gradient(180deg, rgba(255, 235, 59, 0.3) 0%, rgba(255, 235, 59, 0.5) 100%);
    padding: 8px 12px;
    margin: 8px 0;
    border-left: 4px solid #ffc107;
    border-radius: 4px;
}

.sf-review-source-actions {
    padding: 12px 16px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-tertiary, #fafafa);
}

/* Details Panel */
.sf-review-details-panel {
    width: 400px;
    display: flex;
    flex-direction: column;
    background: var(--bg-secondary, #f9f9f9);
}

.sf-review-details-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.sf-review-details-header h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sf-review-status-badge {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.sf-review-status-badge.status-pending {
    background: #e3f2fd;
    color: #1976d2;
}

.sf-review-status-badge.status-approved {
    background: #e8f5e9;
    color: #388e3c;
}

.sf-review-status-badge.status-rejected {
    background: #ffebee;
    color: #d32f2f;
}

.sf-review-status-badge.status-modified {
    background: #fff3e0;
    color: #f57c00;
}

.sf-review-form {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.sf-review-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.sf-review-field-full {
    flex: 1;
}

.sf-review-field label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.sf-review-input,
.sf-review-select,
.sf-review-textarea {
    padding: 8px 12px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 6px;
    font-size: 0.875rem;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #333);
}

.sf-review-input:focus,
.sf-review-select:focus,
.sf-review-textarea:focus {
    outline: none;
    border-color: #2196f3;
    box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.sf-review-textarea {
    resize: vertical;
    min-height: 100px;
    flex: 1;
}

.sf-review-actions {
    padding: 16px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    display: flex;
    gap: 8px;
}

/* Buttons */
.sf-review-btn {
    padding: 8px 16px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 6px;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #333);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.sf-review-btn:hover:not(:disabled) {
    background: var(--bg-secondary, #f5f5f5);
}

.sf-review-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.sf-review-btn-primary {
    background: #2196f3;
    border-color: #2196f3;
    color: #fff;
}

.sf-review-btn-primary:hover:not(:disabled) {
    background: #1976d2;
}

.sf-review-btn-secondary {
    background: #4caf50;
    border-color: #4caf50;
    color: #fff;
}

.sf-review-btn-secondary:hover:not(:disabled) {
    background: #388e3c;
}

.sf-review-btn-danger {
    background: #f44336;
    border-color: #f44336;
    color: #fff;
}

.sf-review-btn-danger:hover:not(:disabled) {
    background: #d32f2f;
}

/* Footer */
.sf-review-footer {
    padding: 12px 24px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f5f5f5);
}

.sf-review-shortcuts {
    display: flex;
    gap: 24px;
    font-size: 0.75rem;
    color: var(--text-secondary, #666);
}

.sf-review-shortcuts kbd {
    display: inline-block;
    padding: 2px 6px;
    margin-right: 4px;
    background: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.75rem;
}

/* Toast */
.sf-review-toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    padding: 12px 24px;
    border-radius: 8px;
    background: #333;
    color: #fff;
    font-size: 0.875rem;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.3s;
    z-index: 10001;
}

.sf-review-toast.show {
    opacity: 1;
    transform: translateY(0);
}

.sf-review-toast-success { background: #4caf50; }
.sf-review-toast-error { background: #f44336; }
.sf-review-toast-warning { background: #ff9800; }
.sf-review-toast-info { background: #2196f3; }

/* Dark Mode Support */
.dark-mode .sf-review-container {
    background: #1e1e1e;
}

.dark-mode .sf-review-header,
.dark-mode .sf-review-footer,
.dark-mode .sf-review-source-header,
.dark-mode .sf-review-source-actions,
.dark-mode .sf-review-details-panel {
    background: #252525;
}

.dark-mode .sf-review-input,
.dark-mode .sf-review-select,
.dark-mode .sf-review-textarea {
    background: #333;
    border-color: #444;
    color: #eee;
}

.dark-mode .sf-review-highlight {
    background: linear-gradient(180deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 193, 7, 0.3) 100%);
}
`;
    }

    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ============================================================
    // PUBLIC INTERFACE
    // ============================================================

    return {
        VERSION,
        open,
        openAtIndex,
        close,
        isOpen,
        getCurrentStatement,
        init
    };
})();

console.log('[TWR StatementReviewMode] Module loaded v' + TWR.StatementReviewMode.VERSION);
