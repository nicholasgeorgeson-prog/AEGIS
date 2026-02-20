/**
 * AEGIS - Statement Source Viewer
 * =====================================
 * Split-panel viewer for viewing statement source context in documents.
 * Mirrors the Role Source Viewer (RSV) design but focused on statements.
 *
 * Features:
 * - Split-panel design matching Role Source Viewer
 * - Left panel: Source document with highlighted statement text
 * - Right panel: Statement details, role info, adjudication
 * - Multi-document navigation with dropdown selector
 * - Statement text highlighting with scroll-to-view
 * - Keyboard shortcuts for navigation
 * - Review status actions (Approve/Reject/Reset)
 * - Statement text editing
 *
 * Version: 1.0.0
 * Date: 2026-02-15
 */

'use strict';

window.TWR = window.TWR || {};

TWR.StatementSourceViewer = (function() {
    const VERSION = '1.1.0';
    const LOG_PREFIX = '[TWR StatementSourceViewer]';

    // ============================================================
    // STATE
    // ============================================================

    const State = {
        isOpen: false,
        modal: null,
        currentStatement: null,     // { role_name, document, text, statement_index, action_type, review_status, notes, confidence, flags }
        documentText: '',           // Full document text
        documentTextCache: {},      // Per-document text cache
        matchPositions: [],         // Array of { start, end } positions where statement text was found
        currentMatchIndex: 0,       // Which match we're currently viewing
        isEditing: false,           // Whether we're in text-edit mode
        isSelectingText: false,     // Whether highlight-to-select mode is active
        selectedTextFromDoc: null,  // Text selected from document panel
        allStatements: [],          // All statements passed for navigation (optional)
        currentStmtNavIndex: 0      // Index into allStatements for prev/next statement nav
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

    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // ============================================================
    // STYLES
    // ============================================================

    function injectStyles() {
        if (document.getElementById('statement-source-viewer-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'statement-source-viewer-styles';
        styles.textContent = `
/* Statement Source Viewer - Split Panel */
.ssv-modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 55000;
}

.ssv-modal.open {
    display: flex;
    align-items: center;
    justify-content: center;
}

.ssv-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(ellipse at 30% 20%, rgba(15, 25, 45, 0.82), rgba(5, 8, 18, 0.85));
}

.ssv-container {
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
    border: 1px solid rgba(214, 168, 74, 0.2);
}

/* Header */
.ssv-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f5f5f5);
}

.ssv-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #D6A84A;
}

.ssv-nav {
    display: flex;
    align-items: center;
    gap: 16px;
}

.ssv-counter {
    font-size: 0.875rem;
    color: var(--text-secondary, #666);
}

.ssv-close {
    background: none;
    border: none;
    font-size: 28px;
    cursor: pointer;
    color: var(--text-secondary, #666);
    padding: 4px 8px;
    line-height: 1;
}

.ssv-close:hover {
    color: var(--text-primary, #333);
}

/* Body - Split Panel */
.ssv-body {
    flex: 1;
    display: flex;
    overflow: hidden;
}

/* Source Panel (Left) */
.ssv-source-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 1px solid var(--border-color, #e0e0e0);
    min-width: 0;
}

.ssv-source-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-tertiary, #fafafa);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.ssv-source-header h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.ssv-source-info {
    padding: 8px 16px;
    display: flex;
    justify-content: space-between;
    font-size: 0.813rem;
    color: var(--text-secondary, #666);
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f9f9f9);
}

.ssv-source-content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 1rem;
    line-height: 1.8;
    color: var(--text-primary, #333);
}

.ssv-document-text {
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Statement highlight styling */
.ssv-stmt-highlight {
    background: linear-gradient(180deg, rgba(214, 168, 74, 0.25) 0%, rgba(214, 168, 74, 0.45) 100%);
    padding: 2px 4px;
    border-radius: 3px;
    font-weight: 600;
    color: var(--text-primary, #333);
    cursor: pointer;
    transition: all 0.2s;
    border-bottom: 2px solid rgba(214, 168, 74, 0.6);
}

.ssv-stmt-highlight:hover {
    background: linear-gradient(180deg, rgba(214, 168, 74, 0.4) 0%, rgba(214, 168, 74, 0.6) 100%);
}

.ssv-stmt-highlight.ssv-current {
    background: linear-gradient(180deg, rgba(214, 168, 74, 0.5) 0%, rgba(245, 158, 11, 0.7) 100%);
    box-shadow: 0 0 0 3px rgba(214, 168, 74, 0.3);
    animation: ssv-pulse 1.5s ease-in-out;
}

@keyframes ssv-pulse {
    0%, 100% { box-shadow: 0 0 0 3px rgba(214, 168, 74, 0.3); }
    50% { box-shadow: 0 0 0 6px rgba(214, 168, 74, 0.15); }
}

/* Role mention styling (secondary highlight) */
.ssv-role-mention {
    background: rgba(99, 102, 241, 0.15);
    padding: 1px 3px;
    border-radius: 2px;
    font-weight: 500;
    color: var(--text-primary, #333);
    border-bottom: 1px dotted rgba(99, 102, 241, 0.5);
}

.ssv-source-actions {
    padding: 12px 16px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-tertiary, #fafafa);
    font-size: 0.85rem;
    color: var(--text-secondary, #666);
}

.ssv-no-document,
.ssv-loading {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted, #9ca3af);
}

.ssv-no-document p,
.ssv-loading p {
    margin: 0 0 8px 0;
}

.ssv-loading {
    animation: ssv-fade 1s ease-in-out infinite alternate;
}

@keyframes ssv-fade {
    from { opacity: 0.5; }
    to { opacity: 1; }
}

/* Details Panel (Right) */
.ssv-details-panel {
    width: 380px;
    display: flex;
    flex-direction: column;
    background: var(--bg-secondary, #f9f9f9);
    flex-shrink: 0;
}

.ssv-details-header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.ssv-details-header h3 {
    margin: 0;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.ssv-details-content {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
}

.ssv-detail-section {
    margin-bottom: 20px;
}

.ssv-detail-section label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.ssv-detail-value {
    font-size: 0.95rem;
    color: var(--text-primary, #333);
}

/* Statement text display */
.ssv-stmt-text-box {
    background: var(--bg-tertiary, #f3f4f6);
    border: 1px solid var(--border-color, #e0e0e0);
    border-left: 3px solid #D6A84A;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 0.9rem;
    line-height: 1.5;
    color: var(--text-primary, #333);
    max-height: 150px;
    overflow-y: auto;
}

.ssv-stmt-text-edit {
    width: 100%;
    min-height: 80px;
    padding: 10px 12px;
    border: 1px solid #D6A84A;
    border-radius: 6px;
    font-size: 0.9rem;
    line-height: 1.5;
    resize: vertical;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #333);
    font-family: inherit;
    box-sizing: border-box;
    display: none;
}

.ssv-edit-actions {
    display: none;
    gap: 8px;
    margin-top: 8px;
}

.ssv-edit-actions.visible {
    display: flex;
}

/* Role badge */
.ssv-role-badge {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    cursor: pointer;
    transition: opacity 0.15s;
}
.ssv-role-badge:hover { opacity: 0.85; }

/* Adjudication Section */
.ssv-adjudication-section {
    background: var(--bg-tertiary, #f3f4f6);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.ssv-adjudication-section > label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
}

.ssv-status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    margin-bottom: 12px;
}
.ssv-status-badge[data-status="approved"] { background: #dcfce7; color: #166534; }
.ssv-status-badge[data-status="rejected"] { background: #fee2e2; color: #991b1b; }
.ssv-status-badge[data-status="pending"] { background: #fef3c7; color: #92400e; }
.ssv-status-badge[data-status="unreviewed"] { background: #e5e7eb; color: #4b5563; }

.ssv-adj-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.ssv-adj-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 8px;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #333);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
}
.ssv-adj-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.ssv-adj-btn.ssv-adj-approve { border-color: #22c55e; color: #16a34a; }
.ssv-adj-btn.ssv-adj-approve:hover { background: #f0fdf4; }
.ssv-adj-btn.ssv-adj-approve.active { background: #22c55e; color: white; }
.ssv-adj-btn.ssv-adj-reject { border-color: #ef4444; color: #dc2626; }
.ssv-adj-btn.ssv-adj-reject:hover { background: #fef2f2; }
.ssv-adj-btn.ssv-adj-reject.active { background: #ef4444; color: white; }
.ssv-adj-btn.ssv-adj-reset { border-color: #9ca3af; color: #6b7280; }
.ssv-adj-btn.ssv-adj-reset:hover { background: #f9fafb; }

/* Flag badges */
.ssv-flag-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    margin: 2px 4px 2px 0;
}
.ssv-flag-fragment { background: rgba(245, 158, 11, 0.15); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.3); }
.ssv-flag-wrong { background: rgba(239, 68, 68, 0.15); color: #dc2626; border: 1px solid rgba(239, 68, 68, 0.3); }
.ssv-flag-low-conf { background: rgba(99, 102, 241, 0.15); color: #6366f1; border: 1px solid rgba(99, 102, 241, 0.3); }

/* Notes section */
.ssv-notes-textarea {
    width: 100%;
    min-height: 60px;
    padding: 8px 10px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 6px;
    font-size: 0.85rem;
    resize: vertical;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #333);
    font-family: inherit;
    box-sizing: border-box;
}

/* Buttons */
.ssv-btn {
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
.ssv-btn:hover:not(:disabled) {
    background: var(--bg-secondary, #f5f5f5);
}
.ssv-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}
.ssv-btn-primary {
    background: #D6A84A;
    color: #1a1f2e;
    border-color: #D6A84A;
    font-weight: 600;
}
.ssv-btn-primary:hover:not(:disabled) {
    background: #c49a3f;
}
.ssv-btn-sm {
    padding: 5px 10px;
    font-size: 0.8rem;
}
.ssv-btn-danger {
    background: #ef4444;
    color: white;
    border-color: #ef4444;
}
.ssv-btn-danger:hover:not(:disabled) {
    background: #dc2626;
}

/* Divider */
.ssv-divider {
    height: 1px;
    background: var(--border-color, #e0e0e0);
    margin: 16px 0;
}

/* Footer */
.ssv-footer {
    padding: 12px 24px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f5f5f5);
}

.ssv-shortcuts {
    display: flex;
    gap: 24px;
    font-size: 0.75rem;
    color: var(--text-secondary, #666);
}

.ssv-shortcuts kbd {
    display: inline-block;
    padding: 2px 6px;
    margin-right: 4px;
    background: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.75rem;
}

/* Dark mode overrides */
[data-theme="dark"] .ssv-container {
    background: #1a1f2e;
    border-color: rgba(214, 168, 74, 0.25);
}
[data-theme="dark"] .ssv-header {
    background: #141825;
    border-color: rgba(255,255,255,0.08);
}
[data-theme="dark"] .ssv-source-header,
[data-theme="dark"] .ssv-source-actions {
    background: #141825;
    border-color: rgba(255,255,255,0.08);
}
[data-theme="dark"] .ssv-source-info {
    background: #161a28;
    border-color: rgba(255,255,255,0.08);
}
[data-theme="dark"] .ssv-source-content {
    color: #e0e0e0;
}
[data-theme="dark"] .ssv-details-panel {
    background: #141825;
}
[data-theme="dark"] .ssv-details-header {
    border-color: rgba(255,255,255,0.08);
}
[data-theme="dark"] .ssv-adjudication-section {
    background: rgba(255,255,255,0.04);
}
[data-theme="dark"] .ssv-stmt-text-box {
    background: rgba(255,255,255,0.05);
    border-color: rgba(255,255,255,0.1);
    color: #e0e0e0;
}
[data-theme="dark"] .ssv-stmt-text-edit {
    background: #1a1f2e;
    color: #e0e0e0;
    border-color: #D6A84A;
}
[data-theme="dark"] .ssv-notes-textarea {
    background: #1a1f2e;
    color: #e0e0e0;
    border-color: rgba(255,255,255,0.15);
}
[data-theme="dark"] .ssv-adj-btn {
    background: rgba(255,255,255,0.05);
    color: #ccc;
    border-color: rgba(255,255,255,0.15);
}
[data-theme="dark"] .ssv-adj-btn.ssv-adj-approve { color: #4ade80; border-color: #22c55e; }
[data-theme="dark"] .ssv-adj-btn.ssv-adj-approve:hover { background: rgba(34,197,94,0.15); }
[data-theme="dark"] .ssv-adj-btn.ssv-adj-approve.active { background: #22c55e; color: white; }
[data-theme="dark"] .ssv-adj-btn.ssv-adj-reject { color: #f87171; border-color: #ef4444; }
[data-theme="dark"] .ssv-adj-btn.ssv-adj-reject:hover { background: rgba(239,68,68,0.15); }
[data-theme="dark"] .ssv-adj-btn.ssv-adj-reject.active { background: #ef4444; color: white; }
[data-theme="dark"] .ssv-btn {
    background: rgba(255,255,255,0.06);
    color: #ccc;
    border-color: rgba(255,255,255,0.15);
}
[data-theme="dark"] .ssv-btn:hover:not(:disabled) {
    background: rgba(255,255,255,0.1);
}
[data-theme="dark"] .ssv-footer {
    background: #141825;
    border-color: rgba(255,255,255,0.08);
}
[data-theme="dark"] .ssv-shortcuts kbd {
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,255,255,0.15);
    color: #aaa;
}
[data-theme="dark"] .ssv-stmt-highlight {
    color: #f0e6d2;
}
[data-theme="dark"] .ssv-stmt-highlight.ssv-current {
    color: #fff;
}
[data-theme="dark"] .ssv-role-mention {
    color: #c7d2fe;
}
[data-theme="dark"] .ssv-status-badge[data-status="approved"] { background: rgba(34,197,94,0.2); color: #4ade80; }
[data-theme="dark"] .ssv-status-badge[data-status="rejected"] { background: rgba(239,68,68,0.2); color: #f87171; }
[data-theme="dark"] .ssv-status-badge[data-status="pending"] { background: rgba(245,158,11,0.2); color: #fbbf24; }
[data-theme="dark"] .ssv-status-badge[data-status="unreviewed"] { background: rgba(255,255,255,0.1); color: #9ca3af; }
[data-theme="dark"] .ssv-detail-section label {
    color: #9ca3af;
}
[data-theme="dark"] .ssv-detail-value {
    color: #e0e0e0;
}
[data-theme="dark"] .ssv-source-panel {
    border-color: rgba(255,255,255,0.08);
}

/* Highlight-to-select mode */
.ssv-source-content.ssv-selection-mode {
    user-select: text !important;
    cursor: text !important;
}
.ssv-source-content.ssv-selection-mode .ssv-document-text {
    user-select: text !important;
}
.ssv-source-content.ssv-selection-mode .ssv-stmt-highlight,
.ssv-source-content.ssv-selection-mode .ssv-role-mention {
    user-select: text !important;
    cursor: text !important;
}
.ssv-source-content.ssv-selection-mode::selection,
.ssv-source-content.ssv-selection-mode *::selection {
    background: rgba(214, 168, 74, 0.4);
    color: inherit;
}

.ssv-selection-indicator {
    display: none;
    padding: 8px 12px;
    margin-bottom: 0;
    font-size: 0.82rem;
    border-radius: 6px;
    background: rgba(214, 168, 74, 0.08);
    border: 1px dashed rgba(214, 168, 74, 0.4);
    color: var(--text-secondary, #666);
    transition: all 0.2s;
}
.ssv-selection-indicator.active {
    display: block;
}
.ssv-selection-indicator.has-selection {
    background: rgba(214, 168, 74, 0.15);
    border-color: rgba(214, 168, 74, 0.6);
    color: var(--text-primary, #333);
    font-weight: 500;
}

.ssv-edit-mode-label {
    transition: all 0.15s;
}

[data-theme="dark"] .ssv-selection-indicator {
    background: rgba(214, 168, 74, 0.06);
    border-color: rgba(214, 168, 74, 0.3);
    color: #9ca3af;
}
[data-theme="dark"] .ssv-selection-indicator.has-selection {
    background: rgba(214, 168, 74, 0.12);
    border-color: rgba(214, 168, 74, 0.5);
    color: #e0e0e0;
}
[data-theme="dark"] .ssv-source-content.ssv-selection-mode::selection,
[data-theme="dark"] .ssv-source-content.ssv-selection-mode *::selection {
    background: rgba(214, 168, 74, 0.5);
}
        `;
        document.head.appendChild(styles);
    }

    // ============================================================
    // MODAL CREATION
    // ============================================================

    function createModal() {
        if (State.modal) return State.modal;

        const modal = document.createElement('div');
        modal.id = 'statement-source-viewer-modal';
        modal.className = 'ssv-modal';
        modal.innerHTML = `
            <div class="ssv-overlay"></div>
            <div class="ssv-container">
                <div class="ssv-header">
                    <h2>Statement Source Viewer</h2>
                    <div class="ssv-nav">
                        <button class="ssv-btn ssv-prev-match" title="Previous Match">
                            <span class="arrow">&larr;</span> Previous
                        </button>
                        <span class="ssv-counter">
                            Match <span class="ssv-current-num">0</span> of <span class="ssv-total-num">0</span>
                        </span>
                        <button class="ssv-btn ssv-next-match" title="Next Match">
                            Next <span class="arrow">&rarr;</span>
                        </button>
                    </div>
                    <button class="ssv-close" title="Close (Esc)">&times;</button>
                </div>

                <div class="ssv-body">
                    <!-- Left Panel: Document Source -->
                    <div class="ssv-source-panel">
                        <div class="ssv-source-header">
                            <h3>Source Document</h3>
                            <span class="ssv-doc-name-display"></span>
                        </div>
                        <div class="ssv-source-info">
                            <span class="ssv-doc-info-left"></span>
                            <span class="ssv-doc-info-right"></span>
                        </div>
                        <div class="ssv-source-content">
                            <div class="ssv-document-text"></div>
                        </div>
                        <div class="ssv-source-actions">
                            <span class="ssv-context-status"></span>
                        </div>
                    </div>

                    <!-- Right Panel: Statement Details -->
                    <div class="ssv-details-panel">
                        <div class="ssv-details-header">
                            <h3>Statement Details</h3>
                        </div>

                        <div class="ssv-details-content">
                            <!-- Role -->
                            <div class="ssv-detail-section">
                                <label>Role</label>
                                <div class="ssv-role-badge ssv-role-name-badge"></div>
                            </div>

                            <!-- Statement Text -->
                            <div class="ssv-detail-section">
                                <label>Statement Text
                                    <button class="ssv-btn ssv-btn-sm ssv-edit-text-btn" style="float:right;border:none;background:none;color:#D6A84A;cursor:pointer;font-size:0.75rem;padding:0;"><span class="ssv-edit-mode-label">✏️ Edit</span></button>
                                </label>
                                <div class="ssv-stmt-text-box ssv-stmt-text-display"></div>
                                <div class="ssv-selection-indicator">🖱️ Highlight text in the document to set as statement text</div>
                                <textarea class="ssv-stmt-text-edit" placeholder="Highlight text in the document, or type here..."></textarea>
                                <div class="ssv-edit-actions">
                                    <button class="ssv-btn ssv-btn-sm ssv-btn-primary ssv-save-text-btn">Save</button>
                                    <button class="ssv-btn ssv-btn-sm ssv-cancel-text-btn">Cancel</button>
                                </div>
                            </div>

                            <!-- Flags -->
                            <div class="ssv-detail-section ssv-flags-section" style="display:none;">
                                <label>Flags</label>
                                <div class="ssv-flags-container"></div>
                            </div>

                            <div class="ssv-divider"></div>

                            <!-- Adjudication -->
                            <div class="ssv-adjudication-section">
                                <label>Review Status</label>
                                <div class="ssv-status-indicator">
                                    <span class="ssv-status-badge" data-status="unreviewed">Unreviewed</span>
                                </div>
                                <div class="ssv-adj-actions">
                                    <button class="ssv-adj-btn ssv-adj-approve" title="Approve this statement">
                                        ✓ Approve
                                    </button>
                                    <button class="ssv-adj-btn ssv-adj-reject" title="Reject this statement">
                                        ✕ Reject
                                    </button>
                                    <button class="ssv-adj-btn ssv-adj-reset" title="Reset to unreviewed">
                                        ↺ Reset
                                    </button>
                                </div>
                            </div>

                            <!-- Action Type -->
                            <div class="ssv-detail-section">
                                <label>Action Type</label>
                                <div class="ssv-detail-value ssv-action-type">—</div>
                            </div>

                            <!-- Confidence -->
                            <div class="ssv-detail-section">
                                <label>Confidence</label>
                                <div class="ssv-detail-value ssv-confidence">—</div>
                            </div>

                            <!-- Notes -->
                            <div class="ssv-detail-section">
                                <label>Notes</label>
                                <textarea class="ssv-notes-textarea" placeholder="Add notes about this statement..."></textarea>
                            </div>

                            <div class="ssv-divider"></div>

                            <!-- Statement Navigation (if opened from list) -->
                            <div class="ssv-detail-section ssv-stmt-nav-section" style="display:none;">
                                <label>Statement Navigation</label>
                                <div style="display:flex;gap:8px;">
                                    <button class="ssv-btn ssv-btn-sm ssv-prev-stmt" title="Previous Statement">← Prev Statement</button>
                                    <span class="ssv-stmt-nav-counter" style="font-size:0.8rem;color:var(--text-secondary,#666);display:flex;align-items:center;"></span>
                                    <button class="ssv-btn ssv-btn-sm ssv-next-stmt" title="Next Statement">Next Statement →</button>
                                </div>
                            </div>

                            <!-- Delete -->
                            <div class="ssv-detail-section">
                                <button class="ssv-btn ssv-btn-sm ssv-btn-danger ssv-delete-stmt-btn">🗑️ Delete Statement</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="ssv-footer">
                    <div class="ssv-shortcuts">
                        <span><kbd>&larr;</kbd> Prev Match</span>
                        <span><kbd>&rarr;</kbd> Next Match</span>
                        <span><kbd>Esc</kbd> Close</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        State.modal = modal;
        attachEventListeners(modal);

        return modal;
    }

    // ============================================================
    // EVENT LISTENERS
    // ============================================================

    function attachEventListeners(modal) {
        modal.querySelector('.ssv-close').addEventListener('click', close);
        modal.querySelector('.ssv-overlay').addEventListener('click', close);

        // Match navigation
        modal.querySelector('.ssv-prev-match').addEventListener('click', () => navigateMatch(-1));
        modal.querySelector('.ssv-next-match').addEventListener('click', () => navigateMatch(1));

        // Adjudication buttons
        modal.querySelector('.ssv-adj-approve').addEventListener('click', () => setReviewStatus('approved'));
        modal.querySelector('.ssv-adj-reject').addEventListener('click', () => setReviewStatus('rejected'));
        modal.querySelector('.ssv-adj-reset').addEventListener('click', () => setReviewStatus('unreviewed'));

        // Edit text toggle
        modal.querySelector('.ssv-edit-text-btn').addEventListener('click', toggleEditMode);
        modal.querySelector('.ssv-save-text-btn').addEventListener('click', saveTextEdit);
        modal.querySelector('.ssv-cancel-text-btn').addEventListener('click', cancelEditMode);

        // Notes auto-save on blur
        modal.querySelector('.ssv-notes-textarea').addEventListener('blur', saveNotes);

        // Delete button
        modal.querySelector('.ssv-delete-stmt-btn').addEventListener('click', deleteStatement);

        // Statement navigation
        modal.querySelector('.ssv-prev-stmt').addEventListener('click', () => navigateStatement(-1));
        modal.querySelector('.ssv-next-stmt').addEventListener('click', () => navigateStatement(1));

        // Role badge click -> open RSV
        modal.querySelector('.ssv-role-name-badge').addEventListener('click', openRoleViewer);

        // Highlight-to-select: listen for text selection in document panel
        modal.querySelector('.ssv-source-content').addEventListener('mouseup', handleDocumentTextSelection);

        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeyboard);
    }

    function handleKeyboard(e) {
        if (!State.isOpen) return;

        if (e.key === 'Escape') {
            close();
            e.preventDefault();
        } else if (e.key === 'ArrowLeft' && !State.isEditing) {
            navigateMatch(-1);
            e.preventDefault();
        } else if (e.key === 'ArrowRight' && !State.isEditing) {
            navigateMatch(1);
            e.preventDefault();
        }
    }

    // ============================================================
    // OPEN / CLOSE
    // ============================================================

    async function open(stmt, options) {
        console.log(LOG_PREFIX, 'Opening for statement:', stmt?.text?.substring(0, 60), 'in', stmt?.document);

        if (!stmt || !stmt.text || !stmt.document || !stmt.role_name) {
            console.error(LOG_PREFIX, 'Invalid statement data:', stmt);
            return;
        }

        injectStyles();
        createModal();

        // Store statement data
        State.currentStatement = { ...stmt };
        State.matchPositions = [];
        State.currentMatchIndex = 0;
        State.isEditing = false;

        // Handle statement list navigation
        if (options?.statements && Array.isArray(options.statements)) {
            State.allStatements = options.statements;
            State.currentStmtNavIndex = options.currentIndex || 0;
            const navSection = State.modal.querySelector('.ssv-stmt-nav-section');
            if (navSection) navSection.style.display = '';
        } else {
            State.allStatements = [];
            const navSection = State.modal.querySelector('.ssv-stmt-nav-section');
            if (navSection) navSection.style.display = 'none';
        }

        // Show modal
        State.modal.classList.add('open');
        State.isOpen = true;
        document.body.style.overflow = 'hidden';

        // Populate right panel immediately
        updateDetailsPanel();

        // Show loading in document panel
        const docTextEl = State.modal.querySelector('.ssv-document-text');
        if (docTextEl) {
            docTextEl.innerHTML = `<div class="ssv-loading"><p>Loading document...</p><p>${escapeHtml(stmt.document)}</p></div>`;
        }

        // Update header doc name
        const docNameEl = State.modal.querySelector('.ssv-doc-name-display');
        if (docNameEl) docNameEl.textContent = stmt.document;

        // Load document text
        await loadAndRenderDocument();

        console.log(LOG_PREFIX, 'Opened successfully');
    }

    function close() {
        if (!State.isOpen) return;

        State.modal.classList.remove('open');
        State.isOpen = false;
        State.isEditing = false;
        document.body.style.overflow = '';

        console.log(LOG_PREFIX, 'Closed');
    }

    // ============================================================
    // DOCUMENT LOADING & RENDERING
    // ============================================================

    async function loadAndRenderDocument() {
        const stmt = State.currentStatement;
        if (!stmt) return;

        const docName = stmt.document;
        let documentText = '';

        // Check cache first
        if (State.documentTextCache[docName]) {
            documentText = State.documentTextCache[docName];
        } else {
            // Fetch from API
            try {
                const response = await fetch(`/api/scan-history/document-text?filename=${encodeURIComponent(docName)}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.text) {
                        documentText = data.text;
                        State.documentTextCache[docName] = documentText;
                    }
                }
            } catch (e) {
                console.log(LOG_PREFIX, 'Could not fetch document text:', e);
            }
        }

        if (!documentText) {
            const docTextEl = State.modal.querySelector('.ssv-document-text');
            if (docTextEl) {
                docTextEl.innerHTML = `
                    <div class="ssv-no-document">
                        <p>No document text available.</p>
                        <p style="font-size:0.85rem;font-style:italic;">The original document file may have been moved or deleted.</p>
                    </div>
                `;
            }
            return;
        }

        State.documentText = documentText;
        renderDocumentWithHighlights(documentText, stmt);
    }

    function renderDocumentWithHighlights(documentText, stmt) {
        const container = State.modal.querySelector('.ssv-document-text');
        if (!container) return;

        const stmtText = stmt.text.trim();
        const roleName = stmt.role_name;

        // Find all positions of the statement text in the document
        const stmtPositions = findTextPositions(documentText, stmtText);
        State.matchPositions = stmtPositions;

        // Find all role name positions (secondary highlight)
        const rolePositions = findTextPositions(documentText, roleName);

        console.log(LOG_PREFIX, `Found ${stmtPositions.length} statement matches, ${rolePositions.length} role mentions`);

        // Build merged highlight map
        // Each position: { start, end, type: 'statement'|'role', matchIndex }
        let highlights = [];
        stmtPositions.forEach((pos, idx) => {
            highlights.push({ start: pos.start, end: pos.end, type: 'statement', matchIndex: idx });
        });
        rolePositions.forEach((pos, idx) => {
            // Don't add role highlights that overlap with statement highlights
            const overlaps = stmtPositions.some(sp =>
                (pos.start >= sp.start && pos.start < sp.end) ||
                (pos.end > sp.start && pos.end <= sp.end)
            );
            if (!overlaps) {
                highlights.push({ start: pos.start, end: pos.end, type: 'role', matchIndex: idx });
            }
        });

        // Sort by position
        highlights.sort((a, b) => a.start - b.start);

        // Build HTML
        let html = '';
        let lastIndex = 0;

        for (const hl of highlights) {
            // Add text before this highlight
            if (hl.start > lastIndex) {
                html += escapeHtml(documentText.substring(lastIndex, hl.start));
            }

            const matchedText = documentText.substring(hl.start, hl.end);

            if (hl.type === 'statement') {
                const isCurrent = hl.matchIndex === State.currentMatchIndex;
                html += `<mark class="ssv-stmt-highlight ${isCurrent ? 'ssv-current' : ''}" data-match-index="${hl.matchIndex}">${escapeHtml(matchedText)}</mark>`;
            } else {
                html += `<mark class="ssv-role-mention">${escapeHtml(matchedText)}</mark>`;
            }

            lastIndex = hl.end;
        }

        // Add remaining text
        if (lastIndex < documentText.length) {
            html += escapeHtml(documentText.substring(lastIndex));
        }

        // Convert newlines to line breaks
        html = html.replace(/\n/g, '<br>');

        container.innerHTML = html;

        // Update counter
        updateMatchCounter();

        // Update info bar
        const infoLeft = State.modal.querySelector('.ssv-doc-info-left');
        const infoRight = State.modal.querySelector('.ssv-doc-info-right');
        if (infoLeft) infoLeft.textContent = `${documentText.length.toLocaleString()} characters`;
        if (infoRight) infoRight.textContent = `${stmtPositions.length} match${stmtPositions.length !== 1 ? 'es' : ''} found`;

        // Add click handlers to statement highlights
        container.querySelectorAll('.ssv-stmt-highlight').forEach(el => {
            el.addEventListener('click', () => {
                const idx = parseInt(el.dataset.matchIndex, 10);
                if (!isNaN(idx) && idx !== State.currentMatchIndex) {
                    State.currentMatchIndex = idx;
                    updateActiveHighlight();
                }
            });
        });

        // Scroll to current match
        scrollToCurrentMatch();

        // Update context status
        const statusEl = State.modal.querySelector('.ssv-context-status');
        if (statusEl) {
            if (stmtPositions.length === 0) {
                statusEl.textContent = '⚠️ Statement text not found in document — it may have been extracted from a different section or modified.';
            } else {
                statusEl.textContent = `✓ Statement located in document (${stmtPositions.length} occurrence${stmtPositions.length !== 1 ? 's' : ''})`;
            }
        }
    }

    function findTextPositions(text, searchStr) {
        if (!text || !searchStr) return [];

        const positions = [];
        const searchNorm = searchStr.trim().toLowerCase();
        const textNorm = text.toLowerCase();

        if (searchNorm.length < 3) return positions;

        // Try exact match first
        let idx = textNorm.indexOf(searchNorm);
        while (idx >= 0) {
            positions.push({ start: idx, end: idx + searchNorm.length });
            idx = textNorm.indexOf(searchNorm, idx + 1);
        }

        // If no exact match, try progressive substring matching
        if (positions.length === 0) {
            const chunks = [
                searchNorm.substring(0, Math.min(80, searchNorm.length)),
                searchNorm.substring(0, Math.min(60, searchNorm.length)),
                searchNorm.substring(0, Math.min(40, searchNorm.length)),
                searchNorm.substring(0, Math.min(25, searchNorm.length))
            ];

            for (const chunk of chunks) {
                if (chunk.length < 10) continue;
                idx = textNorm.indexOf(chunk);
                while (idx >= 0) {
                    positions.push({ start: idx, end: idx + chunk.length });
                    idx = textNorm.indexOf(chunk, idx + 1);
                }
                if (positions.length > 0) break;
            }
        }

        return positions;
    }

    // ============================================================
    // NAVIGATION
    // ============================================================

    function navigateMatch(direction) {
        if (State.matchPositions.length <= 1) return;

        State.currentMatchIndex += direction;
        if (State.currentMatchIndex < 0) State.currentMatchIndex = State.matchPositions.length - 1;
        if (State.currentMatchIndex >= State.matchPositions.length) State.currentMatchIndex = 0;

        updateActiveHighlight();
    }

    function updateActiveHighlight() {
        const container = State.modal.querySelector('.ssv-document-text');
        if (!container) return;

        // Remove current class from all
        container.querySelectorAll('.ssv-stmt-highlight.ssv-current').forEach(el => el.classList.remove('ssv-current'));

        // Add current class to active match
        const active = container.querySelector(`.ssv-stmt-highlight[data-match-index="${State.currentMatchIndex}"]`);
        if (active) {
            active.classList.add('ssv-current');
            active.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        updateMatchCounter();
    }

    function scrollToCurrentMatch() {
        setTimeout(() => {
            const container = State.modal.querySelector('.ssv-document-text');
            if (!container) return;
            const current = container.querySelector('.ssv-stmt-highlight.ssv-current');
            if (current) {
                current.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }

    function updateMatchCounter() {
        const currentEl = State.modal.querySelector('.ssv-current-num');
        const totalEl = State.modal.querySelector('.ssv-total-num');
        if (currentEl) currentEl.textContent = State.matchPositions.length > 0 ? State.currentMatchIndex + 1 : 0;
        if (totalEl) totalEl.textContent = State.matchPositions.length;

        // Update button states
        const prevBtn = State.modal.querySelector('.ssv-prev-match');
        const nextBtn = State.modal.querySelector('.ssv-next-match');
        if (prevBtn) prevBtn.disabled = State.matchPositions.length <= 1;
        if (nextBtn) nextBtn.disabled = State.matchPositions.length <= 1;
    }

    // Statement navigation (prev/next statement from the list)
    function navigateStatement(direction) {
        if (!State.allStatements || State.allStatements.length === 0) return;

        State.currentStmtNavIndex += direction;
        if (State.currentStmtNavIndex < 0) State.currentStmtNavIndex = State.allStatements.length - 1;
        if (State.currentStmtNavIndex >= State.allStatements.length) State.currentStmtNavIndex = 0;

        const nextStmt = State.allStatements[State.currentStmtNavIndex];
        if (nextStmt) {
            open(nextStmt, {
                statements: State.allStatements,
                currentIndex: State.currentStmtNavIndex
            });
        }
    }

    // ============================================================
    // DETAILS PANEL
    // ============================================================

    function updateDetailsPanel() {
        const stmt = State.currentStatement;
        if (!stmt) return;

        // Role badge
        const roleBadge = State.modal.querySelector('.ssv-role-name-badge');
        if (roleBadge) roleBadge.textContent = stmt.role_name;

        // Statement text
        const textDisplay = State.modal.querySelector('.ssv-stmt-text-display');
        if (textDisplay) textDisplay.textContent = stmt.text;

        // Action type
        const actionEl = State.modal.querySelector('.ssv-action-type');
        if (actionEl) actionEl.textContent = stmt.action_type || '—';

        // Confidence
        const confEl = State.modal.querySelector('.ssv-confidence');
        if (confEl) {
            const conf = stmt.confidence;
            if (conf != null && conf !== undefined) {
                const pct = Math.round(conf * 100);
                const color = pct >= 80 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';
                confEl.innerHTML = `<span style="color:${color};font-weight:600;">${pct}%</span>`;
            } else {
                confEl.textContent = '—';
            }
        }

        // Status badge
        const status = stmt.review_status || 'unreviewed';
        updateStatusBadge(status);

        // Flags
        const flagsSection = State.modal.querySelector('.ssv-flags-section');
        const flagsContainer = State.modal.querySelector('.ssv-flags-container');
        if (flagsSection && flagsContainer) {
            const flags = stmt.flags || [];
            if (flags.length > 0) {
                flagsSection.style.display = '';
                flagsContainer.innerHTML = flags.map(f => {
                    let cls = 'ssv-flag-fragment';
                    if (f.startsWith('wrong_')) cls = 'ssv-flag-wrong';
                    if (f === 'low_confidence') cls = 'ssv-flag-low-conf';
                    const label = f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    return `<span class="ssv-flag-badge ${cls}">⚠ ${label}</span>`;
                }).join('');
            } else {
                flagsSection.style.display = 'none';
            }
        }

        // Notes
        const notesEl = State.modal.querySelector('.ssv-notes-textarea');
        if (notesEl) notesEl.value = stmt.notes || '';

        // Statement nav counter
        if (State.allStatements.length > 0) {
            const navCounter = State.modal.querySelector('.ssv-stmt-nav-counter');
            if (navCounter) navCounter.textContent = `${State.currentStmtNavIndex + 1} / ${State.allStatements.length}`;
        }

        // Reset edit mode
        cancelEditMode();
    }

    function updateStatusBadge(status) {
        const badge = State.modal.querySelector('.ssv-status-badge');
        if (!badge) return;

        badge.setAttribute('data-status', status);
        const labels = {
            'approved': 'Approved', 'reviewed': 'Approved',
            'rejected': 'Rejected',
            'pending': 'Pending',
            'unreviewed': 'Unreviewed'
        };
        badge.textContent = labels[status] || status;

        // Update button active states
        const approveBtn = State.modal.querySelector('.ssv-adj-approve');
        const rejectBtn = State.modal.querySelector('.ssv-adj-reject');
        if (approveBtn) approveBtn.classList.toggle('active', status === 'approved' || status === 'reviewed');
        if (rejectBtn) rejectBtn.classList.toggle('active', status === 'rejected');
    }

    // ============================================================
    // ACTIONS
    // ============================================================

    async function setReviewStatus(newStatus) {
        const stmt = State.currentStatement;
        if (!stmt) return;

        console.log(LOG_PREFIX, `Setting review status to "${newStatus}" for statement:`, stmt.text?.substring(0, 40));

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            const headers = { 'Content-Type': 'application/json' };
            if (csrfToken) headers['X-CSRF-Token'] = csrfToken;

            const resp = await fetch('/api/roles/bulk-update-statements', {
                method: 'PUT',
                headers,
                body: JSON.stringify({
                    statements: [{
                        role_name: stmt.role_name,
                        document: stmt.document,
                        statement_index: stmt.statement_index
                    }],
                    updates: { review_status: newStatus }
                })
            });

            if (resp.ok) {
                State.currentStatement.review_status = newStatus;
                updateStatusBadge(newStatus);

                // Update the statement in allStatements if present
                if (State.allStatements[State.currentStmtNavIndex]) {
                    State.allStatements[State.currentStmtNavIndex].review_status = newStatus;
                }

                if (typeof showToast === 'function') {
                    showToast('success', `Statement ${newStatus}`);
                }
            } else {
                throw new Error(`HTTP ${resp.status}`);
            }
        } catch (e) {
            console.error(LOG_PREFIX, 'Failed to update status:', e);
            if (typeof showToast === 'function') {
                showToast('error', 'Failed to update status');
            }
        }
    }

    async function saveNotes() {
        const stmt = State.currentStatement;
        if (!stmt) return;

        const notesEl = State.modal.querySelector('.ssv-notes-textarea');
        const newNotes = notesEl?.value?.trim() || '';

        if (newNotes === (stmt.notes || '')) return; // No change

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            const headers = { 'Content-Type': 'application/json' };
            if (csrfToken) headers['X-CSRF-Token'] = csrfToken;

            await fetch('/api/roles/bulk-update-statements', {
                method: 'PUT',
                headers,
                body: JSON.stringify({
                    statements: [{
                        role_name: stmt.role_name,
                        document: stmt.document,
                        statement_index: stmt.statement_index
                    }],
                    updates: { notes: newNotes }
                })
            });
            State.currentStatement.notes = newNotes;
            console.log(LOG_PREFIX, 'Notes saved');
        } catch (e) {
            console.error(LOG_PREFIX, 'Failed to save notes:', e);
        }
    }

    function toggleEditMode() {
        const textDisplay = State.modal.querySelector('.ssv-stmt-text-display');
        const textEdit = State.modal.querySelector('.ssv-stmt-text-edit');
        const editActions = State.modal.querySelector('.ssv-edit-actions');
        const sourceContent = State.modal.querySelector('.ssv-source-content');
        const indicator = State.modal.querySelector('.ssv-selection-indicator');
        const modeLabel = State.modal.querySelector('.ssv-edit-mode-label');

        if (State.isEditing) {
            cancelEditMode();
        } else {
            State.isEditing = true;
            State.isSelectingText = true;
            State.selectedTextFromDoc = null;

            if (textDisplay) textDisplay.style.display = 'none';
            if (textEdit) {
                textEdit.style.display = '';
                textEdit.value = State.currentStatement?.text || '';
            }
            if (editActions) editActions.classList.add('visible');
            if (sourceContent) sourceContent.classList.add('ssv-selection-mode');
            if (indicator) {
                indicator.classList.add('active');
                indicator.classList.remove('has-selection');
                indicator.textContent = '🖱️ Highlight text in the document to set as statement text';
            }
            if (modeLabel) modeLabel.textContent = '🖱️ Selecting...';

            console.log(LOG_PREFIX, 'Edit mode activated with highlight-to-select');
        }
    }

    function cancelEditMode() {
        State.isEditing = false;
        State.isSelectingText = false;
        State.selectedTextFromDoc = null;

        const textDisplay = State.modal.querySelector('.ssv-stmt-text-display');
        const textEdit = State.modal.querySelector('.ssv-stmt-text-edit');
        const editActions = State.modal.querySelector('.ssv-edit-actions');
        const sourceContent = State.modal.querySelector('.ssv-source-content');
        const indicator = State.modal.querySelector('.ssv-selection-indicator');
        const modeLabel = State.modal.querySelector('.ssv-edit-mode-label');

        if (textDisplay) textDisplay.style.display = '';
        if (textEdit) textEdit.style.display = 'none';
        if (editActions) editActions.classList.remove('visible');
        if (sourceContent) sourceContent.classList.remove('ssv-selection-mode');
        if (indicator) {
            indicator.classList.remove('active');
            indicator.classList.remove('has-selection');
        }
        if (modeLabel) modeLabel.textContent = '✏️ Edit';

        // Clear any browser selection
        window.getSelection()?.removeAllRanges();
    }

    /**
     * Handle text selection in the document panel during edit mode.
     * When user highlights text in the document, it populates the textarea.
     */
    function handleDocumentTextSelection() {
        if (!State.isSelectingText) return;

        const selection = window.getSelection();
        const selectedText = selection?.toString()?.trim();

        if (!selectedText || selectedText.length < 3) return;

        State.selectedTextFromDoc = selectedText;

        // Update the textarea with selected text
        const textEdit = State.modal.querySelector('.ssv-stmt-text-edit');
        if (textEdit) {
            textEdit.value = selectedText;
        }

        // Update visual indicator
        const indicator = State.modal.querySelector('.ssv-selection-indicator');
        if (indicator) {
            indicator.classList.add('has-selection');
            const preview = selectedText.length > 80
                ? selectedText.substring(0, 80) + '...'
                : selectedText;
            indicator.textContent = `✓ Selected: "${preview}"`;
        }

        console.log(LOG_PREFIX, `Highlight-to-select: captured ${selectedText.length} chars`);
    }

    async function saveTextEdit() {
        const textEdit = State.modal.querySelector('.ssv-stmt-text-edit');
        const newText = textEdit?.value?.trim();
        if (!newText || !State.currentStatement) {
            console.warn(LOG_PREFIX, 'saveTextEdit: no text or no current statement',
                { newText: !!newText, stmt: !!State.currentStatement });
            if (typeof showToast === 'function') showToast('warning', 'No text to save or no statement selected');
            return;
        }

        const stmt = State.currentStatement;
        // v5.9.35: Validate required fields before API call
        if (!stmt.role_name || !stmt.document || stmt.statement_index == null) {
            console.warn(LOG_PREFIX, 'saveTextEdit: missing required fields', {
                role_name: stmt.role_name, document: stmt.document, statement_index: stmt.statement_index
            });
            if (typeof showToast === 'function') showToast('warning', 'Cannot save — missing statement context (role, document, or index)');
            return;
        }

        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            const headers = { 'Content-Type': 'application/json' };
            if (csrfToken) headers['X-CSRF-Token'] = csrfToken;

            const resp = await fetch('/api/roles/bulk-update-statements', {
                method: 'PUT',
                headers,
                body: JSON.stringify({
                    statements: [{
                        role_name: stmt.role_name,
                        document: stmt.document,
                        statement_index: stmt.statement_index
                    }],
                    updates: { text: newText }
                })
            });

            if (resp.ok) {
                State.currentStatement.text = newText;

                // Update display
                const textDisplay = State.modal.querySelector('.ssv-stmt-text-display');
                if (textDisplay) textDisplay.textContent = newText;

                cancelEditMode();

                // Re-render document highlights with new text
                if (State.documentText) {
                    renderDocumentWithHighlights(State.documentText, State.currentStatement);
                }

                if (typeof showToast === 'function') {
                    showToast('success', 'Statement text updated');
                }
            } else {
                throw new Error(`HTTP ${resp.status}`);
            }
        } catch (e) {
            console.error(LOG_PREFIX, 'Failed to save text:', e);
            if (typeof showToast === 'function') {
                showToast('error', 'Failed to save text edit');
            }
        }
    }

    async function deleteStatement() {
        const stmt = State.currentStatement;
        if (!stmt) return;

        if (!confirm(`Delete this statement?\n\n"${stmt.text.substring(0, 100)}${stmt.text.length > 100 ? '...' : ''}"\n\nThis cannot be undone.`)) {
            return;
        }

        try {
            const resp = await fetch('/api/roles/bulk-delete-statements', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    deletions: [{
                        role_name: stmt.role_name,
                        document: stmt.document,
                        statement_index: stmt.statement_index
                    }]
                })
            });

            if (resp.ok) {
                if (typeof showToast === 'function') {
                    showToast('success', 'Statement deleted');
                }

                // If navigating through statements, go to next
                if (State.allStatements.length > 1) {
                    State.allStatements.splice(State.currentStmtNavIndex, 1);
                    if (State.currentStmtNavIndex >= State.allStatements.length) {
                        State.currentStmtNavIndex = 0;
                    }
                    const nextStmt = State.allStatements[State.currentStmtNavIndex];
                    if (nextStmt) {
                        open(nextStmt, {
                            statements: State.allStatements,
                            currentIndex: State.currentStmtNavIndex
                        });
                    } else {
                        close();
                    }
                } else {
                    close();
                }
            } else {
                throw new Error(`HTTP ${resp.status}`);
            }
        } catch (e) {
            console.error(LOG_PREFIX, 'Failed to delete:', e);
            if (typeof showToast === 'function') {
                showToast('error', 'Failed to delete statement');
            }
        }
    }

    function openRoleViewer() {
        const stmt = State.currentStatement;
        if (!stmt) return;

        // Open the Role Source Viewer for this role
        if (window.TWR?.RoleSourceViewer?.open) {
            window.TWR.RoleSourceViewer.open(stmt.role_name, {
                sourceDocument: stmt.document,
                searchText: stmt.text
            });
        }
    }

    // ============================================================
    // INITIALIZATION
    // ============================================================

    function init() {
        injectStyles();
        console.log(LOG_PREFIX, 'Initialized v' + VERSION);
    }

    // Auto-init when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ============================================================
    // PUBLIC API
    // ============================================================

    return {
        VERSION,
        open,
        close,
        getState: () => ({ ...State, isOpen: State.isOpen })
    };

})();
