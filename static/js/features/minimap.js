// v3.0.97: Fix Assistant v2 - Mini-map Component
// WP2b: Visual document overview with fix position markers

const MiniMap = (function() {
    'use strict';

    const VERSION = '3.0.97';

    const TIER_COLORS = {
        safe: '#10b981',
        review: '#f59e0b',
        manual: '#ef4444'
    };

    const state = {
        container: null,
        trackEl: null,
        viewportEl: null,
        tooltipEl: null,
        fixes: [],
        totalParagraphs: 0,
        pageCount: 0,
        activeFix: null,
        isDragging: false,
        dragStartY: 0,
        viewportStartTop: 0,
        callbacks: {
            navigate: [],
            hover: []
        }
    };

    // ═══════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS
    // ═══════════════════════════════════════════════════════════════════════

    function render() {
        if (!state.container) return;
        
        // SAFE: static HTML
        state.container.innerHTML = `
            <div class="fav2-minimap-track"></div>
            <div class="fav2-minimap-tooltip" style="display: none;"></div>
        `;
        state.container.classList.add('fav2-minimap');
        state.trackEl = state.container.querySelector('.fav2-minimap-track');
        state.tooltipEl = state.container.querySelector('.fav2-minimap-tooltip');

        renderMarkers();
        renderViewport();
        setupEventListeners();
    }

    function renderMarkers() {
        console.log('[TWR MiniMap] renderMarkers called', {
            hasTrackEl: !!state.trackEl,
            fixCount: state.fixes.length,
            totalParagraphs: state.totalParagraphs
        });

        if (!state.trackEl) {
            console.warn('[TWR MiniMap] No track element, skipping render');
            return;
        }

        // Clear existing markers
        state.trackEl.querySelectorAll('.fav2-minimap-marker').forEach(el => el.remove());

        if (state.totalParagraphs === 0) {
            console.warn('[TWR MiniMap] totalParagraphs is 0, skipping marker render');
            return;
        }

        // Add marker for each fix
        state.fixes.forEach((fix, i) => {
            const position = getMarkerPosition(fix.paragraph_index);
            const marker = document.createElement('div');
            marker.className = `fav2-minimap-marker fav2-tier-${fix.tier || 'review'}`;

            if (fix.index === state.activeFix) {
                marker.classList.add('fav2-marker-active');
            }

            marker.style.top = `${position}%`;
            marker.dataset.fixIndex = fix.index;
            marker.dataset.page = fix.page || 1;
            marker.dataset.para = fix.paragraph_index;

            const tooltipText = fix.flagged_text
                ? `Page ${fix.page || 1}: ${fix.flagged_text}`
                : `Page ${fix.page || 1}: Fix #${fix.index}`;
            marker.title = tooltipText;

            state.trackEl.appendChild(marker);

            if (i === 0) {
                console.log('[TWR MiniMap] First marker created:', {
                    position: `${position}%`,
                    tier: fix.tier || 'review',
                    paragraphIndex: fix.paragraph_index
                });
            }
        });

        console.log(`[TWR MiniMap] Created ${state.fixes.length} markers`);
    }

    function renderViewport() {
        if (!state.trackEl) return;
        
        let viewport = state.trackEl.querySelector('.fav2-minimap-viewport');
        if (!viewport) {
            viewport = document.createElement('div');
            viewport.className = 'fav2-minimap-viewport';
            state.trackEl.appendChild(viewport);
        }
        state.viewportEl = viewport;
    }

    function getMarkerPosition(paragraphIndex) {
        if (state.totalParagraphs === 0) return 0;
        return Math.min(100, Math.max(0, (paragraphIndex / state.totalParagraphs) * 100));
    }

    function getPageAtPosition(percentY) {
        if (state.pageCount === 0) return 1;
        return Math.max(1, Math.min(state.pageCount, Math.ceil((percentY / 100) * state.pageCount)));
    }

    function getParagraphAtPosition(percentY) {
        if (state.totalParagraphs === 0) return 0;
        return Math.floor((percentY / 100) * state.totalParagraphs);
    }

    function getFixCountOnPage(page) {
        return state.fixes.filter(f => f.page === page).length;
    }

    function setupEventListeners() {
        if (!state.trackEl) return;

        state.trackEl.addEventListener('click', handleTrackClick);
        state.trackEl.addEventListener('mousemove', handleMouseMove);
        state.trackEl.addEventListener('mouseleave', handleMouseLeave);

        if (state.viewportEl) {
            state.viewportEl.addEventListener('mousedown', handleViewportDragStart);
        }

        document.addEventListener('mousemove', handleDocumentMouseMove);
        document.addEventListener('mouseup', handleDocumentMouseUp);
    }

    function removeEventListeners() {
        if (state.trackEl) {
            state.trackEl.removeEventListener('click', handleTrackClick);
            state.trackEl.removeEventListener('mousemove', handleMouseMove);
            state.trackEl.removeEventListener('mouseleave', handleMouseLeave);
        }
        if (state.viewportEl) {
            state.viewportEl.removeEventListener('mousedown', handleViewportDragStart);
        }
        document.removeEventListener('mousemove', handleDocumentMouseMove);
        document.removeEventListener('mouseup', handleDocumentMouseUp);
    }

    function handleTrackClick(e) {
        if (state.isDragging) return;
        if (e.target.classList.contains('fav2-minimap-viewport')) return;

        // Check if clicked on a marker
        if (e.target.classList.contains('fav2-minimap-marker')) {
            const fixIndex = parseInt(e.target.dataset.fixIndex, 10);
            const fix = state.fixes.find(f => f.index === fixIndex);
            if (fix) {
                emit('navigate', {
                    page: fix.page || 1,
                    paragraphIndex: fix.paragraph_index,
                    percentY: getMarkerPosition(fix.paragraph_index),
                    fixIndex: fixIndex
                });
            }
            return;
        }

        // Clicked on track background
        const rect = state.trackEl.getBoundingClientRect();
        const clickY = e.clientY - rect.top;
        const percentY = (clickY / rect.height) * 100;
        const clampedPercent = Math.min(100, Math.max(0, percentY));

        emit('navigate', {
            page: getPageAtPosition(clampedPercent),
            paragraphIndex: getParagraphAtPosition(clampedPercent),
            percentY: clampedPercent
        });
    }

    function handleMouseMove(e) {
        if (state.isDragging) return;

        const rect = state.trackEl.getBoundingClientRect();
        const mouseY = e.clientY - rect.top;
        const percentY = Math.min(100, Math.max(0, (mouseY / rect.height) * 100));
        const page = getPageAtPosition(percentY);
        const fixCount = getFixCountOnPage(page);

        // Update tooltip
        if (state.tooltipEl) {
            const fixText = fixCount === 1 ? '1 fix' : `${fixCount} fixes`;
            state.tooltipEl.textContent = `Page ${page} - ${fixText}`;
            state.tooltipEl.style.display = 'block';
            state.tooltipEl.style.top = `${mouseY}px`;
        }

        emit('hover', {
            page,
            fixCount,
            x: e.clientX,
            y: e.clientY
        });
    }

    function handleMouseLeave() {
        if (state.tooltipEl) {
            state.tooltipEl.style.display = 'none';
        }
        emit('hover', null);
    }

    function handleViewportDragStart(e) {
        e.preventDefault();
        e.stopPropagation();
        state.isDragging = true;
        state.dragStartY = e.clientY;
        state.viewportStartTop = parseFloat(state.viewportEl.style.top) || 0;
        state.viewportEl.classList.add('fav2-minimap-viewport-dragging');
    }

    function handleDocumentMouseMove(e) {
        if (!state.isDragging || !state.viewportEl || !state.trackEl) return;

        const rect = state.trackEl.getBoundingClientRect();
        const deltaY = e.clientY - state.dragStartY;
        const deltaPercent = (deltaY / rect.height) * 100;
        const viewportHeight = parseFloat(state.viewportEl.style.height) || 10;
        
        let newTop = state.viewportStartTop + deltaPercent;
        newTop = Math.max(0, Math.min(100 - viewportHeight, newTop));
        
        state.viewportEl.style.top = `${newTop}%`;
    }

    function handleDocumentMouseUp() {
        if (!state.isDragging) return;
        
        state.isDragging = false;
        if (state.viewportEl) {
            state.viewportEl.classList.remove('fav2-minimap-viewport-dragging');
            
            const newTop = parseFloat(state.viewportEl.style.top) || 0;
            const viewportHeight = parseFloat(state.viewportEl.style.height) || 10;
            const centerPercent = newTop + (viewportHeight / 2);

            emit('navigate', {
                page: getPageAtPosition(centerPercent),
                paragraphIndex: getParagraphAtPosition(centerPercent),
                percentY: centerPercent
            });
        }
    }

    function emit(event, data) {
        if (!state.callbacks[event]) return;
        state.callbacks[event].forEach(cb => {
            try {
                cb(data);
            } catch (err) {
                console.error('[TWR MiniMap] Callback error:', err);
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // v3.0.101: Added comprehensive JSDoc documentation (ISSUE-010)
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Initialize the mini-map component.
     * @param {HTMLElement} containerEl - The DOM element to render into
     * @param {Object} [options={}] - Configuration options
     * @param {Function} [options.onNavigate] - Callback when user navigates: ({page, paragraphIndex, percentY, fixIndex?}) => void
     * @param {Function} [options.onHover] - Callback when hovering: ({page, fixCount, x, y}) => void
     * @returns {void}
     */
    function init(containerEl, options = {}) {
        if (!containerEl) {
            console.error('[TWR MiniMap] No container element provided');
            return;
        }

        state.container = containerEl;
        state.callbacks.navigate = options.onNavigate ? [options.onNavigate] : [];
        state.callbacks.hover = options.onHover ? [options.onHover] : [];

        render();
        console.log(`[TWR MiniMap] Initialized v${VERSION}`);
    }

    /**
     * Destroy the mini-map and clean up resources.
     * @returns {void}
     */
    function destroy() {
        removeEventListeners();
        if (state.container) {
            state.container.innerHTML = ''; // SAFE: clearing element
            state.container.classList.remove('fav2-minimap');
        }
        state.container = null;
        state.trackEl = null;
        state.viewportEl = null;
        state.tooltipEl = null;
        state.fixes = [];
        state.callbacks = { navigate: [], hover: [] };
        console.log('[TWR MiniMap] Destroyed');
    }

    /**
     * Set the fixes to display as markers on the mini-map.
     * @param {Array} fixes - Array of fix objects with paragraph_index, tier, page properties
     * @returns {void}
     */
    function setFixes(fixes) {
        state.fixes = Array.isArray(fixes) ? fixes : [];
        renderMarkers();
    }

    /**
     * Set document dimensions for accurate positioning.
     * @param {number} totalParagraphs - Total number of paragraphs in document
     * @param {number} pageCount - Total number of pages in document
     * @returns {void}
     */
    function setDocumentInfo(totalParagraphs, pageCount) {
        state.totalParagraphs = Math.max(0, totalParagraphs || 0);
        state.pageCount = Math.max(0, pageCount || 0);
        renderMarkers();
    }

    /**
     * Update the visible viewport indicator.
     * @param {number} startPara - First visible paragraph index
     * @param {number} endPara - Last visible paragraph index
     * @param {number} [totalParagraphs] - Optional override for total paragraphs
     * @returns {void}
     */
    function setViewport(startPara, endPara, totalParagraphs) {
        if (!state.viewportEl) return;
        
        const total = totalParagraphs || state.totalParagraphs;
        if (total === 0) {
            state.viewportEl.style.top = '0%';
            state.viewportEl.style.height = '100%';
            return;
        }

        const topPercent = (startPara / total) * 100;
        const heightPercent = ((endPara - startPara) / total) * 100;

        state.viewportEl.style.top = `${Math.max(0, topPercent)}%`;
        state.viewportEl.style.height = `${Math.max(2, Math.min(100, heightPercent))}%`;
    }

    /**
     * Set which fix marker should appear active/highlighted.
     * @param {number} fixIndex - The index of the fix to highlight
     * @returns {void}
     */
    function setActiveFix(fixIndex) {
        state.activeFix = fixIndex;
        
        // Update marker classes
        if (state.trackEl) {
            state.trackEl.querySelectorAll('.fav2-minimap-marker').forEach(marker => {
                const idx = parseInt(marker.dataset.fixIndex, 10);
                marker.classList.toggle('fav2-marker-active', idx === fixIndex);
            });
        }
    }

    /**
     * Clear the active fix marker highlight.
     * @returns {void}
     */
    function clearActiveFix() {
        state.activeFix = null;
        if (state.trackEl) {
            state.trackEl.querySelectorAll('.fav2-marker-active').forEach(el => {
                el.classList.remove('fav2-marker-active');
            });
        }
    }

    /**
     * Register a callback for navigation events.
     * @param {Function} callback - Callback: ({page, paragraphIndex, percentY, fixIndex?}) => void
     * @returns {void}
     */
    function onNavigate(callback) {
        if (typeof callback === 'function') {
            state.callbacks.navigate.push(callback);
        }
    }

    /**
     * Register a callback for hover events.
     * @param {Function} callback - Callback: ({page, fixCount, x, y}) => void or null when leaving
     * @returns {void}
     */
    function onHover(callback) {
        if (typeof callback === 'function') {
            state.callbacks.hover.push(callback);
        }
    }

    /**
     * Force a re-render of the mini-map.
     * @returns {void}
     */
    function refresh() {
        render();
    }

    return {
        init,
        destroy,
        setFixes,
        setDocumentInfo,
        setViewport,
        setActiveFix,
        clearActiveFix,
        onNavigate,
        onHover,
        refresh
    };
})();

window.MiniMap = MiniMap;
console.log('[TWR MiniMap] Module loaded v3.0.97');
