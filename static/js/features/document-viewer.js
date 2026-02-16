// v3.0.109: Fixed acronym highlighting false positives using word boundary regex
// v3.0.97: Fix Assistant v2 - Document Viewer Component
// WP2a: Page-based document rendering with navigation and highlighting

const DocumentViewer = (function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE STATE
    // ═══════════════════════════════════════════════════════════════════════════

    const state = {
        container: null,
        content: null,
        currentPage: 1,
        totalPages: 0,
        activeParagraph: null,
        paragraphsByPage: {},
        callbacks: {
            pageChange: [],
            paragraphClick: []
        },
        elements: {
            header: null,
            prevBtn: null,
            nextBtn: null,
            pageInput: null,
            pageCurrent: null,
            pageTotal: null,
            contentArea: null
        }
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE UTILITY METHODS
    // ═══════════════════════════════════════════════════════════════════════════

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML; // SAFE: escapeHtml function output
    }

    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function emit(event, data) {
        state.callbacks[event]?.forEach(cb => {
            try {
                cb(data);
            } catch (e) {
                console.error('[TWR DocumentViewer] Callback error:', e);
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE DATA METHODS
    // ═══════════════════════════════════════════════════════════════════════════

    function buildParagraphsByPage() {
        state.paragraphsByPage = {};
        if (!state.content?.paragraphs) return;

        state.content.paragraphs.forEach(para => {
            const page = para.page || 1;
            if (!state.paragraphsByPage[page]) {
                state.paragraphsByPage[page] = [];
            }
            state.paragraphsByPage[page].push(para);
        });
    }

    function computeTotalPages() {
        if (state.content?.page_count) {
            return state.content.page_count;
        }
        // Compute from paragraphs if page_count not provided
        let maxPage = 1;
        state.content?.paragraphs?.forEach(para => {
            if (para.page && para.page > maxPage) {
                maxPage = para.page;
            }
        });
        return maxPage;
    }

    function getPageForParagraph(paraIndex) {
        if (state.content?.page_map && state.content.page_map[paraIndex] !== undefined) {
            return state.content.page_map[paraIndex];
        }
        // Fallback: search paragraphs
        const para = state.content?.paragraphs?.find(p => p.index === paraIndex);
        return para?.page || 1;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE RENDER METHODS
    // ═══════════════════════════════════════════════════════════════════════════

    function renderParagraph(para) {
        const classes = ['fav2-paragraph'];
        if (para.is_heading) {
            classes.push('fav2-heading');
            const level = para.heading_level || 1;
            classes.push(`fav2-heading-${level}`);
        }

        return `<div class="${classes.join(' ')}" data-index="${para.index}">${escapeHtml(para.text)}</div>`;
    }

    function renderPage(pageNum) {
        const paragraphs = state.paragraphsByPage[pageNum] || [];
        const isCurrentPage = pageNum === state.currentPage;

        const paragraphsHtml = paragraphs.map(renderParagraph).join('\n            ');

        return `
        <div class="fav2-page" data-page="${pageNum}" style="display: ${isCurrentPage ? 'block' : 'none'};">
            ${paragraphsHtml || '<div class="fav2-empty-page">No content on this page</div>'}
        </div>`;
    }

    function render() {
        if (!state.container) {
            console.error('[TWR DocumentViewer] No container element');
            return;
        }

        // Handle empty document
        if (!state.content?.paragraphs?.length) {
            // SAFE: static HTML
            state.container.innerHTML = `
                <div class="fav2-document-viewer">
                    <div class="fav2-viewer-content">
                        <div class="fav2-empty-document">No content available</div>
                    </div>
                </div>`;
            console.warn('[TWR DocumentViewer] Empty document rendered');
            return;
        }

        const showNav = state.totalPages > 1;

        // Build all pages
        const pagesHtml = [];
        for (let p = 1; p <= state.totalPages; p++) {
            pagesHtml.push(renderPage(p));
        }

        // SAFE: pagesHtml built from renderParagraph which uses escapeHtml; numeric values
        state.container.innerHTML = `
        <div class="fav2-document-viewer">
            <div class="fav2-viewer-header" ${!showNav ? 'style="display: none;"' : ''}>
                <button class="fav2-page-btn fav2-page-prev" ${state.currentPage === 1 ? 'disabled' : ''} title="Previous page">
                    <span>◀</span>
                </button>
                <div class="fav2-page-indicator">
                    <span>Page </span>
                    <span class="fav2-page-current">${state.currentPage}</span>
                    <span class="fav2-page-sep"> / </span>
                    <span class="fav2-page-total">${state.totalPages}</span>
                </div>
                <button class="fav2-page-btn fav2-page-next" ${state.currentPage === state.totalPages ? 'disabled' : ''} title="Next page">
                    <span>▶</span>
                </button>
                <input type="number" class="fav2-page-jump" min="1" max="${state.totalPages}" placeholder="Go to..." title="Jump to page">
            </div>
            <div class="fav2-viewer-content">
                ${pagesHtml.join('\n')}
            </div>
        </div>`;

        // Cache element references
        cacheElements();
    }

    function cacheElements() {
        const viewer = state.container.querySelector('.fav2-document-viewer');
        if (!viewer) return;

        state.elements = {
            header: viewer.querySelector('.fav2-viewer-header'),
            prevBtn: viewer.querySelector('.fav2-page-prev'),
            nextBtn: viewer.querySelector('.fav2-page-next'),
            pageInput: viewer.querySelector('.fav2-page-jump'),
            pageCurrent: viewer.querySelector('.fav2-page-current'),
            pageTotal: viewer.querySelector('.fav2-page-total'),
            contentArea: viewer.querySelector('.fav2-viewer-content')
        };
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE NAVIGATION METHODS
    // ═══════════════════════════════════════════════════════════════════════════

    function showPage(pageNum) {
        const pages = state.container.querySelectorAll('.fav2-page');
        pages.forEach(page => {
            const pNum = parseInt(page.dataset.page, 10);
            page.style.display = pNum === pageNum ? 'block' : 'none';
        });
    }

    function updateNavButtons() {
        if (state.elements.prevBtn) {
            state.elements.prevBtn.disabled = state.currentPage <= 1;
        }
        if (state.elements.nextBtn) {
            state.elements.nextBtn.disabled = state.currentPage >= state.totalPages;
        }
        if (state.elements.pageCurrent) {
            state.elements.pageCurrent.textContent = state.currentPage;
        }
    }

    function navigateToPage(pageNum, scrollToTop = true) {
        const newPage = clamp(pageNum, 1, state.totalPages);
        if (newPage === state.currentPage) return;

        state.currentPage = newPage;
        showPage(newPage);
        updateNavButtons();

        if (scrollToTop && state.elements.contentArea) {
            state.elements.contentArea.scrollTop = 0;
        }

        emit('pageChange', newPage);
        console.log(`[TWR DocumentViewer] Navigated to page ${newPage}`);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE EVENT HANDLERS
    // ═══════════════════════════════════════════════════════════════════════════

    function handlePrevClick() {
        if (state.currentPage > 1) {
            navigateToPage(state.currentPage - 1);
        }
    }

    function handleNextClick() {
        if (state.currentPage < state.totalPages) {
            navigateToPage(state.currentPage + 1);
        }
    }

    function handlePageJump(e) {
        if (e.type === 'keydown' && e.key !== 'Enter') return;

        const input = e.target;
        const pageNum = parseInt(input.value, 10);

        if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= state.totalPages) {
            navigateToPage(pageNum);
        }
        input.value = '';
    }

    function handleParagraphClick(e) {
        const paraEl = e.target.closest('.fav2-paragraph');
        if (!paraEl) return;

        const paraIndex = parseInt(paraEl.dataset.index, 10);
        if (isNaN(paraIndex)) return;

        emit('paragraphClick', { index: paraIndex, event: e });
    }

    function setupEventListeners() {
        if (state.elements.prevBtn) {
            state.elements.prevBtn.addEventListener('click', handlePrevClick);
        }
        if (state.elements.nextBtn) {
            state.elements.nextBtn.addEventListener('click', handleNextClick);
        }
        if (state.elements.pageInput) {
            state.elements.pageInput.addEventListener('keydown', handlePageJump);
            state.elements.pageInput.addEventListener('blur', handlePageJump);
        }
        if (state.elements.contentArea) {
            state.elements.contentArea.addEventListener('click', handleParagraphClick);
        }
    }

    function removeEventListeners() {
        if (state.elements.prevBtn) {
            state.elements.prevBtn.removeEventListener('click', handlePrevClick);
        }
        if (state.elements.nextBtn) {
            state.elements.nextBtn.removeEventListener('click', handleNextClick);
        }
        if (state.elements.pageInput) {
            state.elements.pageInput.removeEventListener('keydown', handlePageJump);
            state.elements.pageInput.removeEventListener('blur', handlePageJump);
        }
        if (state.elements.contentArea) {
            state.elements.contentArea.removeEventListener('click', handleParagraphClick);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE HIGHLIGHT METHODS
    // ═══════════════════════════════════════════════════════════════════════════

    function clearAllHighlights() {
        // Remove active class from all paragraphs
        const activeParagraphs = state.container.querySelectorAll('.fav2-paragraph.fav2-active');
        activeParagraphs.forEach(el => el.classList.remove('fav2-active'));

        // Remove highlight marks - restore original text
        const highlightedParagraphs = state.container.querySelectorAll('.fav2-paragraph');
        highlightedParagraphs.forEach(el => {
            const marks = el.querySelectorAll('mark.fav2-highlight');
            marks.forEach(mark => {
                const textNode = document.createTextNode(mark.textContent);
                mark.parentNode.replaceChild(textNode, mark);
            });
            // Normalize to merge adjacent text nodes
            el.normalize();
        });

        state.activeParagraph = null;
    }

    // v3.0.112: Added decision parameter for color-coded highlights
    function highlightTextInElement(element, searchText, decision = 'pending') {
        if (!searchText || !element) return false;

        const originalHtml = element.innerHTML;
        const escapedSearch = escapeRegex(searchText);
        // v3.0.109: Use word boundary regex to avoid false positive highlighting
        // (e.g., prevent "NDA" from being highlighted inside "staNDArds")
        const regex = new RegExp(`\\b(${escapedSearch})\\b`, 'i');

        // v3.0.112: Build class list based on decision
        const decisionClass = decision ? `fav2-decision-${decision}` : '';
        const highlightClasses = `fav2-highlight fav2-current ${decisionClass}`.trim();

        // Get text content and find match
        const textContent = element.textContent;
        const match = textContent.match(regex);

        if (!match) {
            // v3.0.109: Fallback to non-word-boundary match if whole-word not found
            // This handles edge cases where flagged text may span word boundaries
            const fallbackRegex = new RegExp(`(${escapedSearch})`, 'i');
            const fallbackMatch = textContent.match(fallbackRegex);
            if (!fallbackMatch) {
                console.warn(`[TWR DocumentViewer] Highlight text "${searchText}" not found in paragraph`);
                return false;
            }
            // Use fallback match
            const matchedText = fallbackMatch[1];
            const index = textContent.indexOf(matchedText);
            if (index === -1) return false;

            const before = escapeHtml(textContent.substring(0, index));
            const highlighted = `<mark class="${highlightClasses}">${escapeHtml(matchedText)}</mark>`;
            const after = escapeHtml(textContent.substring(index + matchedText.length));
            element.innerHTML = before + highlighted + after;
            return true;
        }

        // Replace only first occurrence, preserving case
        const matchedText = match[1];
        const index = textContent.indexOf(matchedText);

        if (index === -1) return false;

        // Reconstruct with highlight - only first occurrence
        const before = escapeHtml(textContent.substring(0, index));
        const highlighted = `<mark class="${highlightClasses}">${escapeHtml(matchedText)}</mark>`;
        const after = escapeHtml(textContent.substring(index + matchedText.length));

        // SAFE: all parts escaped via escapeHtml()
        element.innerHTML = before + highlighted + after;
        return true;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // v3.0.101: Added comprehensive JSDoc documentation (ISSUE-010)
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Initialize the document viewer with content.
     * @param {HTMLElement} containerEl - The DOM element to render into
     * @param {Object} documentContent - Document data object
     * @param {Array} documentContent.paragraphs - Array of paragraph objects with text, index, page
     * @param {number} [documentContent.page_count] - Total number of pages
     * @param {Object} [documentContent.page_map] - Mapping of paragraph index to page number
     * @param {Object} [options={}] - Configuration options
     * @param {Function} [options.onPageChange] - Callback when page changes: (pageNum) => void
     * @param {Function} [options.onParagraphClick] - Callback when paragraph clicked: ({index, text}) => void
     * @returns {void}
     * @example
     * DocumentViewer.init(document.getElementById('viewer'), docData, {
     *   onPageChange: (page) => console.log('Now on page', page)
     * });
     */
    function init(containerEl, documentContent, options = {}) {
        if (!containerEl) {
            console.error('[TWR DocumentViewer] init() requires a container element');
            return;
        }

        if (!documentContent) {
            console.error('[TWR DocumentViewer] init() requires documentContent');
            return;
        }

        // Reset state
        state.container = containerEl;
        state.content = documentContent;
        state.currentPage = 1;
        state.activeParagraph = null;
        state.callbacks = { pageChange: [], paragraphClick: [] };

        // Build internal data structures
        buildParagraphsByPage();
        state.totalPages = computeTotalPages();

        // Render
        render();

        // Setup events
        setupEventListeners();

        // Register option callbacks
        if (typeof options.onPageChange === 'function') {
            state.callbacks.pageChange.push(options.onPageChange);
        }
        if (typeof options.onParagraphClick === 'function') {
            state.callbacks.paragraphClick.push(options.onParagraphClick);
        }

        console.log(`[TWR DocumentViewer] Initialized with ${state.content.paragraphs?.length || 0} paragraphs, ${state.totalPages} pages`);
    }

    /**
     * Destroy the viewer and clean up resources.
     * Removes all event listeners and clears the container.
     * @returns {void}
     */
    function destroy() {
        removeEventListeners();

        if (state.container) {
            state.container.innerHTML = ''; // SAFE: clearing element
        }

        // Reset state
        state.container = null;
        state.content = null;
        state.currentPage = 1;
        state.totalPages = 0;
        state.activeParagraph = null;
        state.paragraphsByPage = {};
        state.callbacks = { pageChange: [], paragraphClick: [] };
        state.elements = {};

        console.log('[TWR DocumentViewer] Destroyed');
    }

    /**
     * Navigate to a specific page number.
     * @param {number} pageNum - The 1-indexed page number to navigate to
     * @returns {void}
     * @throws {Warning} If pageNum is not a valid number
     */
    function goToPage(pageNum) {
        if (typeof pageNum !== 'number' || isNaN(pageNum)) {
            console.warn('[TWR DocumentViewer] goToPage() requires a valid page number');
            return;
        }
        navigateToPage(pageNum);
    }

    /**
     * Scroll to and highlight a specific paragraph.
     * @param {number} paraIndex - The 0-indexed paragraph index
     * @param {string|null} [highlightText=null] - Text within paragraph to highlight
     * @param {string} [decision='pending'] - Decision status: 'pending', 'accepted', 'rejected', 'skipped'
     * @returns {boolean} True if successful, false if paragraph not found
     */
    function scrollToParagraph(paraIndex, highlightText = null, decision = 'pending') {
        if (typeof paraIndex !== 'number' || isNaN(paraIndex)) {
            console.warn('[TWR DocumentViewer] scrollToParagraph() requires a valid paragraph index');
            return false;
        }

        // Clear existing highlights
        clearAllHighlights();

        // Find the page containing this paragraph
        const targetPage = getPageForParagraph(paraIndex);

        // Navigate to page if needed (without scrolling to top)
        if (targetPage !== state.currentPage) {
            state.currentPage = targetPage;
            showPage(targetPage);
            updateNavButtons();
            emit('pageChange', targetPage);
        }

        // Find the paragraph element
        const paraEl = state.container.querySelector(`.fav2-paragraph[data-index="${paraIndex}"]`);
        if (!paraEl) {
            console.warn(`[TWR DocumentViewer] Paragraph ${paraIndex} not found`);
            return false;
        }

        // Add active class
        paraEl.classList.add('fav2-active');
        state.activeParagraph = paraIndex;

        // Highlight text if provided
        if (highlightText) {
            highlightTextInElement(paraEl, highlightText, decision);
        }

        // v3.0.111: Scroll to the highlight element if it exists, otherwise scroll to paragraph
        // This ensures the specific flagged text is visible, not just the paragraph
        const highlightEl = paraEl.querySelector('.fav2-highlight');
        if (highlightEl) {
            highlightEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log(`[TWR DocumentViewer] Scrolled to highlight "${highlightText}" in paragraph ${paraIndex} (${decision})`);
        } else {
            paraEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log(`[TWR DocumentViewer] Scrolled to paragraph ${paraIndex}${highlightText ? ` (highlight "${highlightText}" not found)` : ''}`);
        }
        return true;
    }

    /**
     * Set a paragraph as active (visually highlighted) without scrolling.
     * @param {number} paraIndex - The 0-indexed paragraph index
     * @returns {void}
     */
    function setActiveParagraph(paraIndex) {
        if (typeof paraIndex !== 'number' || isNaN(paraIndex)) {
            console.warn('[TWR DocumentViewer] setActiveParagraph() requires a valid paragraph index');
            return;
        }

        // Remove active from previous
        if (state.activeParagraph !== null) {
            const prevEl = state.container.querySelector(`.fav2-paragraph[data-index="${state.activeParagraph}"]`);
            if (prevEl) {
                prevEl.classList.remove('fav2-active');
            }
        }

        // Add active to new
        const paraEl = state.container.querySelector(`.fav2-paragraph[data-index="${paraIndex}"]`);
        if (paraEl) {
            paraEl.classList.add('fav2-active');
            state.activeParagraph = paraIndex;
        } else {
            console.warn(`[TWR DocumentViewer] Paragraph ${paraIndex} not found for setActiveParagraph`);
        }
    }

    /**
     * Clear all text highlights from the document.
     * @returns {void}
     */
    function clearHighlights() {
        clearAllHighlights();
        console.log('[TWR DocumentViewer] Highlights cleared');
    }

    /**
     * Get the current page number.
     * @returns {number} Current page number (1-indexed)
     */
    function getCurrentPage() {
        return state.currentPage;
    }

    /**
     * Get the total number of pages.
     * @returns {number} Total page count
     */
    function getTotalPages() {
        return state.totalPages;
    }

    /**
     * Get all paragraphs on a specific page.
     * @param {number} pageNum - The 1-indexed page number
     * @returns {Array} Array of paragraph objects on that page
     */
    function getParagraphsOnPage(pageNum) {
        return state.paragraphsByPage[pageNum] || [];
    }

    /**
     * Register a callback for page change events.
     * @param {Function} callback - Callback function: (pageNum) => void
     * @returns {void}
     */
    function onPageChange(callback) {
        if (typeof callback === 'function') {
            state.callbacks.pageChange.push(callback);
        }
    }

    /**
     * Register a callback for paragraph click events.
     * @param {Function} callback - Callback function: ({index, text}) => void
     * @returns {void}
     */
    function onParagraphClick(callback) {
        if (typeof callback === 'function') {
            state.callbacks.paragraphClick.push(callback);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // RETURN PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════

    return {
        init,
        destroy,
        goToPage,
        scrollToParagraph,
        setActiveParagraph,
        clearHighlights,
        getCurrentPage,
        getTotalPages,
        getParagraphsOnPage,
        onPageChange,
        onParagraphClick
    };
})();

// Export globally
window.DocumentViewer = DocumentViewer;
console.log('[TWR DocumentViewer] Module loaded v3.0.97');
