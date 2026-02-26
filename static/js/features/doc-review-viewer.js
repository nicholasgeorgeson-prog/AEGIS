/**
 * AEGIS Document Review — Split-Pane Viewer
 * v6.2.0
 *
 * Provides a "View Document" toggle that shows the scanned document alongside
 * the issues list in a split-pane layout. Supports:
 *   - Mammoth HTML rendering for DOCX (via html_preview)
 *   - PDF.js rendering for PDFs
 *   - Plain-text fallback for other formats
 *   - Click-to-highlight: clicking an issue scrolls to the relevant text in the doc
 *
 * Public API:
 *   DocReviewViewer.init()        — Wire up event listeners (call once on DOMContentLoaded)
 *   DocReviewViewer.canShow()     — Returns true if viewer has content to show
 *   DocReviewViewer.toggle()      — Toggle split-pane on/off
 *   DocReviewViewer.show()        — Open split-pane
 *   DocReviewViewer.hide()        — Close split-pane and restore original layout
 *   DocReviewViewer.destroy()     — Full teardown
 */
window.DocReviewViewer = (function() {
    'use strict';

    // ── State ─────────────────────────────────────────────────────
    var _state = {
        isOpen: false,
        htmlPreview: '',       // Mammoth HTML or pymupdf4llm HTML
        extractionText: '',    // Plain text fallback
        fileType: '',          // 'docx', 'pdf', 'xlsx', etc.
        filename: '',
        filepath: '',          // Server path for PDF.js
        issues: [],
        initialized: false
    };

    // ── DOM refs (cached on init) ─────────────────────────────────
    var _els = {};

    // ── Initialization ────────────────────────────────────────────
    function init() {
        if (_state.initialized) return;

        _els.toggleBtn = document.getElementById('btn-toggle-doc-viewer');
        _els.splitPane = document.getElementById('dr-split-pane');
        _els.docPanel = document.getElementById('dr-doc-panel');
        _els.docContent = document.getElementById('dr-doc-content');
        _els.docFilename = document.getElementById('dr-doc-filename');
        _els.closeBtn = document.getElementById('dr-doc-close');
        _els.issuesPanel = document.getElementById('dr-issues-panel');
        _els.issuesContainer = document.getElementById('issues-container');

        if (!_els.splitPane || !_els.toggleBtn) {
            console.warn('[AEGIS DocReviewViewer] Missing DOM elements — not initialized');
            return;
        }

        // Wire toggle button
        _els.toggleBtn.addEventListener('click', function() {
            toggle();
        });

        // Wire close button
        if (_els.closeBtn) {
            _els.closeBtn.addEventListener('click', function() {
                hide();
            });
        }

        _state.initialized = true;
        console.log('[AEGIS DocReviewViewer] Initialized');
    }

    // ── Data Loading ──────────────────────────────────────────────

    /**
     * Update viewer data from review results.
     * Call this after scan completes with the result data.
     */
    function setData(opts) {
        _state.htmlPreview = opts.htmlPreview || '';
        _state.extractionText = opts.extractionText || '';
        _state.fileType = (opts.fileType || '').toLowerCase();
        _state.filename = opts.filename || 'Document';
        _state.filepath = opts.filepath || '';
        _state.issues = opts.issues || [];

        // Show/hide toggle button based on whether we have content
        if (_els.toggleBtn) {
            _els.toggleBtn.style.display = canShow() ? '' : 'none';
        }
    }

    /**
     * Returns true if we have renderable document content.
     */
    function canShow() {
        return !!(_state.htmlPreview || _state.extractionText ||
                  (_state.fileType === 'pdf' && _state.filepath));
    }

    // ── Toggle / Show / Hide ──────────────────────────────────────

    function toggle() {
        if (_state.isOpen) {
            hide();
        } else {
            show();
        }
    }

    function show() {
        if (!canShow()) {
            console.warn('[AEGIS DocReviewViewer] No document content to show');
            return;
        }
        if (!_els.splitPane || !_els.issuesContainer) return;

        _state.isOpen = true;

        // Update button state
        if (_els.toggleBtn) {
            _els.toggleBtn.classList.add('active');
            var span = _els.toggleBtn.querySelector('span');
            if (span) span.textContent = 'Hide Document';
        }

        // Update filename
        if (_els.docFilename) {
            _els.docFilename.textContent = _state.filename;
        }

        // Render the document content
        _renderDocument();

        // Move issues container into the split pane's right panel
        if (_els.issuesPanel && _els.issuesContainer) {
            _els.issuesContainer._originalParent = _els.issuesContainer.parentElement;
            _els.issuesContainer._originalNextSibling = _els.issuesContainer.nextElementSibling;
            _els.issuesPanel.appendChild(_els.issuesContainer);
            _els.issuesContainer.style.display = '';
            _els.issuesContainer.style.height = '100%';
            _els.issuesContainer.style.overflow = 'auto';
            _els.issuesContainer.style.border = 'none';
            _els.issuesContainer.style.borderRadius = '0';
        }

        // Show split pane
        _els.splitPane.classList.add('active');
        _els.splitPane.style.display = 'flex';

        // Refresh icons
        if (window.lucide) window.lucide.createIcons();

        console.log('[AEGIS DocReviewViewer] Split-pane opened');
    }

    function hide() {
        if (!_els.splitPane) return;

        _state.isOpen = false;

        // Update button state
        if (_els.toggleBtn) {
            _els.toggleBtn.classList.remove('active');
            var span = _els.toggleBtn.querySelector('span');
            if (span) span.textContent = 'View Document';
        }

        // Move issues container back to its original location
        if (_els.issuesContainer && _els.issuesContainer._originalParent) {
            var parent = _els.issuesContainer._originalParent;
            var next = _els.issuesContainer._originalNextSibling;
            if (next && next.parentElement === parent) {
                parent.insertBefore(_els.issuesContainer, next);
            } else {
                parent.appendChild(_els.issuesContainer);
            }
            _els.issuesContainer.style.height = '';
            _els.issuesContainer.style.overflow = '';
            _els.issuesContainer.style.border = '';
            _els.issuesContainer.style.borderRadius = '';
            delete _els.issuesContainer._originalParent;
            delete _els.issuesContainer._originalNextSibling;
        }

        // Hide split pane
        _els.splitPane.classList.remove('active');
        _els.splitPane.style.display = 'none';

        // Clear document content to free memory
        if (_els.docContent) {
            _els.docContent.innerHTML = '';
        }

        console.log('[AEGIS DocReviewViewer] Split-pane closed');
    }

    function destroy() {
        hide();
        _state.htmlPreview = '';
        _state.extractionText = '';
        _state.fileType = '';
        _state.filename = '';
        _state.filepath = '';
        _state.issues = [];
        if (_els.toggleBtn) {
            _els.toggleBtn.style.display = 'none';
        }
    }

    // ── Document Rendering ────────────────────────────────────────

    function _renderDocument() {
        var container = _els.docContent;
        if (!container) return;

        container.innerHTML = '';

        var fileType = _state.fileType;

        // PDF → use PDF.js if available
        if (fileType === 'pdf' && _state.filepath && window.TWR && window.TWR.PDFViewer) {
            try {
                var pdfUrl = _state.filepath;
                // If it's a relative path or server path, construct URL
                if (!pdfUrl.startsWith('http') && !pdfUrl.startsWith('/')) {
                    pdfUrl = '/api/scan-history/document-file?path=' + encodeURIComponent(pdfUrl);
                }
                TWR.PDFViewer.render(container, pdfUrl, { scale: 1.2 }).catch(function(err) {
                    console.warn('[AEGIS DocReviewViewer] PDF.js failed, falling back to text:', err);
                    _renderTextFallback(container);
                });
                return;
            } catch (e) {
                console.warn('[AEGIS DocReviewViewer] PDF.js not available:', e);
            }
        }

        // DOCX/HTML preview → render mammoth HTML
        if (_state.htmlPreview) {
            _renderHtml(container, _state.htmlPreview);
            return;
        }

        // Plain text fallback
        if (_state.extractionText) {
            _renderTextFallback(container);
            return;
        }

        // Empty state
        container.innerHTML =
            '<div class="dr-doc-empty">' +
                '<i data-lucide="file-question"></i>' +
                '<p>No document preview available</p>' +
                '<p class="dr-doc-hint">The document content was not preserved during this scan.</p>' +
            '</div>';
        if (window.lucide) window.lucide.createIcons();
    }

    function _renderHtml(container, html) {
        // Sanitize HTML: strip scripts, styles, event handlers
        var sanitized = html
            .replace(/<script[\s\S]*?<\/script>/gi, '')
            .replace(/<style[\s\S]*?<\/style>/gi, '')
            .replace(/on\w+="[^"]*"/gi, '')
            .replace(/on\w+='[^']*'/gi, '');

        container.innerHTML = '<div class="dr-html-render">' + sanitized + '</div>';
    }

    function _renderTextFallback(container) {
        var text = _state.extractionText || '';
        // Escape HTML
        var div = document.createElement('div');
        div.textContent = text;
        var escaped = div.innerHTML;

        container.innerHTML = '<pre class="dr-text-render">' + escaped + '</pre>';
    }

    // ── Issue ↔ Document Interaction ──────────────────────────────

    /**
     * Scroll the document viewer to text matching a given issue.
     * Called when user clicks an issue row.
     */
    function scrollToIssue(issue) {
        if (!_state.isOpen || !_els.docContent) return;

        var flaggedText = issue.flagged_text || '';
        if (!flaggedText || flaggedText.length < 3) return;

        // Clear previous highlights
        var prev = _els.docContent.querySelectorAll('.dr-highlight-active');
        for (var i = 0; i < prev.length; i++) {
            prev[i].classList.remove('dr-highlight-active');
        }

        // Find the text in the rendered document
        var renderEl = _els.docContent.querySelector('.dr-html-render') ||
                       _els.docContent.querySelector('.dr-text-render');
        if (!renderEl) return;

        // Try to find and highlight the flagged text using TreeWalker
        var found = _highlightText(renderEl, flaggedText);
        if (found) {
            // Scroll to the highlighted element
            var mark = _els.docContent.querySelector('.dr-highlight-active');
            if (mark) {
                mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }

    /**
     * Search text nodes in the container for the target string and wrap it
     * in a <mark> highlight element.
     */
    function _highlightText(container, targetText) {
        // Normalize target text for fuzzy matching
        var normalizedTarget = targetText.trim().toLowerCase()
            .replace(/\s+/g, ' ')
            .substring(0, 200); // Cap search length

        if (normalizedTarget.length < 3) return false;

        // Walk all text nodes
        var walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        var textNodes = [];
        var fullText = '';
        var node;
        while (node = walker.nextNode()) {
            textNodes.push({
                node: node,
                start: fullText.length,
                text: node.textContent
            });
            fullText += node.textContent;
        }

        // Search for the target in the concatenated text
        var normalizedFull = fullText.toLowerCase().replace(/\s+/g, ' ');
        var searchIdx = normalizedFull.indexOf(normalizedTarget);

        if (searchIdx === -1) {
            // Try shorter snippet (first 60 chars)
            var shorter = normalizedTarget.substring(0, 60);
            searchIdx = normalizedFull.indexOf(shorter);
        }

        if (searchIdx === -1) return false;

        // Map back from normalized position to original text position
        // Simple approach: find the text node containing our match start
        var charCount = 0;
        for (var i = 0; i < textNodes.length; i++) {
            var tn = textNodes[i];
            var nodeText = tn.node.textContent;
            var normalizedNodeLen = nodeText.toLowerCase().replace(/\s+/g, ' ').length;

            if (charCount + normalizedNodeLen > searchIdx) {
                // Match starts in this node
                var offsetInNode = searchIdx - charCount;

                try {
                    var range = document.createRange();
                    var endOffset = Math.min(offsetInNode + normalizedTarget.length, nodeText.length);
                    range.setStart(tn.node, Math.min(offsetInNode, nodeText.length));
                    range.setEnd(tn.node, endOffset);

                    var mark = document.createElement('mark');
                    mark.className = 'dr-highlight dr-highlight-active';
                    range.surroundContents(mark);
                    return true;
                } catch (e) {
                    // surroundContents can fail across element boundaries
                    // Fall back to scrolling to the text node's parent
                    if (tn.node.parentElement) {
                        tn.node.parentElement.classList.add('dr-highlight-active');
                        tn.node.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        return true;
                    }
                }
                break;
            }
            charCount += normalizedNodeLen;
        }

        return false;
    }

    // ── Public API ────────────────────────────────────────────────
    return {
        init: init,
        setData: setData,
        canShow: canShow,
        toggle: toggle,
        show: show,
        hide: hide,
        destroy: destroy,
        scrollToIssue: scrollToIssue
    };
})();
