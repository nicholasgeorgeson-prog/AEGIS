/**
 * PDF.js Viewer Module v3.1 (v6.0.4)
 * Renders PDF pages into canvas elements with:
 * - HiDPI/Retina-aware rendering (devicePixelRatio)
 * - Zoom controls (+/−/fit width) with viewport center preservation
 * - Magnifier loupe on hover
 * - Click-to-drag panning when zoomed (scrolls wrapper, not parent)
 * - Auto-fit-width on initial render
 * - Text layer for selectable text (enables click-to-populate)
 * Used in Statement History and Proposal Compare doc viewer.
 */
window.TWR = window.TWR || {};
TWR.PDFViewer = (function() {
    'use strict';

    let pdfjsLib = null;
    let isLoaded = false;
    let lastError = null;

    // State for active viewer instance
    let _activeState = null;

    async function init() {
        if (isLoaded) return true;
        try {
            const check = await fetch('/static/js/vendor/pdfjs/pdf.min.mjs', { method: 'HEAD' });
            if (!check.ok) {
                lastError = `PDF.js library not found (HTTP ${check.status})`;
                console.warn('[PDFViewer]', lastError);
                return false;
            }
            pdfjsLib = await import('/static/js/vendor/pdfjs/pdf.min.mjs');
            pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/js/vendor/pdfjs/pdf.worker.min.mjs';
            isLoaded = true;
            lastError = null;
            return true;
        } catch (e) {
            lastError = e.message || 'Unknown error loading PDF.js';
            console.warn('[PDFViewer] Failed to load pdf.js:', e);
            return false;
        }
    }

    /**
     * Render a PDF into a container element with zoom controls.
     * @param {HTMLElement} container - Target container
     * @param {string} url - URL to the PDF file
     * @param {object} options - { scale: 2.0, showZoomBar: true, showMagnifier: true, enableTextLayer: true }
     */
    async function render(container, url, options = {}) {
        if (!await init()) {
            const errMsg = lastError || 'Unknown error';
            console.error('[PDFViewer] Init failed:', errMsg);
            container.innerHTML = `<div class="pdfv-error">PDF.js could not be loaded: ${errMsg}.<br><small>Falling back to text view.</small></div>`;
            throw new Error('PDF.js init failed: ' + errMsg);
        }

        container.innerHTML = '<div class="pdfv-loading"><div class="sfh-spinner"></div><p>Loading PDF...</p></div>';

        try {
            const pdf = await pdfjsLib.getDocument(url).promise;
            container.innerHTML = '';

            const baseScale = options.scale || 2.0;
            const showZoomBar = options.showZoomBar !== false;
            const showMagnifier = options.showMagnifier !== false;
            const enableTextLayer = options.enableTextLayer !== false;

            // Create state for this viewer
            const state = {
                pdf: pdf,
                url: url,
                currentScale: baseScale,
                minScale: 0.5,
                maxScale: 4.0,
                magnifierActive: false,
                panMode: false,
                container: container,
                wrapper: null,
                zoomLabel: null,
                enableTextLayer: enableTextLayer,
            };
            _activeState = state;

            // Zoom control bar
            if (showZoomBar) {
                const zoomBar = document.createElement('div');
                zoomBar.className = 'pdfv-zoom-bar';
                zoomBar.innerHTML = `
                    <button class="pdfv-zoom-btn" data-action="zoom-out" title="Zoom Out">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    </button>
                    <span class="pdfv-zoom-label">${Math.round(baseScale * 50)}%</span>
                    <button class="pdfv-zoom-btn" data-action="zoom-in" title="Zoom In">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    </button>
                    <button class="pdfv-zoom-btn" data-action="fit-width" title="Fit Width">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
                    </button>
                    ${showMagnifier ? `<button class="pdfv-zoom-btn pdfv-mag-toggle" data-action="magnifier" title="Toggle Magnifier">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    </button>` : ''}
                `;
                container.appendChild(zoomBar);
                state.zoomLabel = zoomBar.querySelector('.pdfv-zoom-label');

                // Zoom bar events
                zoomBar.addEventListener('click', function(e) {
                    const btn = e.target.closest('[data-action]');
                    if (!btn) return;
                    const action = btn.dataset.action;
                    if (action === 'zoom-in') {
                        _setZoom(state, Math.min(state.currentScale + 0.25, state.maxScale));
                    } else if (action === 'zoom-out') {
                        _setZoom(state, Math.max(state.currentScale - 0.25, state.minScale));
                    } else if (action === 'fit-width') {
                        _fitWidth(state);
                    } else if (action === 'magnifier') {
                        state.magnifierActive = !state.magnifierActive;
                        btn.classList.toggle('pdfv-mag-active', state.magnifierActive);
                        _toggleMagnifier(state);
                    }
                });
            }

            // Pages wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'pdfv-wrapper';
            container.appendChild(wrapper);
            state.wrapper = wrapper;

            // v5.9.53: Click-to-drag panning
            _initPanDrag(state);

            // v6.0.4: Auto-fit to container width on initial render
            // Get first page to compute fit scale
            const firstPage = await pdf.getPage(1);
            const baseViewport = firstPage.getViewport({ scale: 1.0 });
            const containerWidth = container.clientWidth - 32; // minus padding
            if (containerWidth > 0 && baseViewport.width > 0) {
                const fitScale = containerWidth / baseViewport.width;
                state.currentScale = Math.max(state.minScale, Math.min(fitScale, state.maxScale));
                if (state.zoomLabel) {
                    state.zoomLabel.textContent = Math.round(state.currentScale * 50) + '%';
                }
            }

            // Render all pages
            await _renderPages(state);

        } catch (e) {
            console.error('[PDFViewer] Render error:', e);
            container.innerHTML = `<div class="pdfv-error">Failed to render PDF: ${e.message}<br><small>The original file may no longer be available.</small></div>`;
            throw e;
        }
    }

    async function _renderPages(state) {
        const { pdf, currentScale, wrapper, enableTextLayer } = state;
        wrapper.innerHTML = '';

        const dpr = window.devicePixelRatio || 1;

        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            // Render at high res (scale * dpr), display at CSS scale
            const renderScale = currentScale * dpr;
            const viewport = page.getViewport({ scale: renderScale });
            const displayViewport = page.getViewport({ scale: currentScale });

            const pageDiv = document.createElement('div');
            pageDiv.className = 'pdfv-page';
            pageDiv.style.position = 'relative';
            pageDiv.dataset.pageNum = i;

            const label = document.createElement('div');
            label.className = 'pdfv-page-label';
            label.textContent = `Page ${i} of ${pdf.numPages}`;
            pageDiv.appendChild(label);

            const canvas = document.createElement('canvas');
            // Canvas internal resolution = high DPI
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            // CSS display size = logical pixels
            canvas.style.width = displayViewport.width + 'px';
            canvas.style.height = displayViewport.height + 'px';
            canvas.style.imageRendering = 'auto';
            canvas.dataset.pageNum = i;
            canvas.dataset.renderScale = renderScale;
            pageDiv.appendChild(canvas);

            wrapper.appendChild(pageDiv);

            await page.render({
                canvasContext: canvas.getContext('2d'),
                viewport: viewport,
            }).promise;

            // v5.9.53: Render text layer for selectable text (enables click-to-populate)
            if (enableTextLayer) {
                try {
                    await _renderTextLayer(page, pageDiv, displayViewport);
                } catch (e) {
                    console.warn('[PDFViewer] Text layer render failed for page ' + i + ':', e);
                }
            }
        }
    }

    /**
     * v5.9.53: Render a transparent, selectable text layer on top of the canvas.
     * This enables window.getSelection() to work on PDF content,
     * which is required for click-to-populate in Proposal Compare.
     */
    async function _renderTextLayer(page, pageDiv, displayViewport) {
        const textContent = await page.getTextContent();
        if (!textContent || !textContent.items || textContent.items.length === 0) return;

        const textLayerDiv = document.createElement('div');
        textLayerDiv.className = 'pdfv-text-layer';
        textLayerDiv.style.width = displayViewport.width + 'px';
        textLayerDiv.style.height = displayViewport.height + 'px';
        pageDiv.appendChild(textLayerDiv);

        // Position each text item as a span
        textContent.items.forEach(function(item) {
            if (!item.str || !item.str.trim()) return;

            const tx = pdfjsLib.Util.transform(displayViewport.transform, item.transform);
            const span = document.createElement('span');
            span.textContent = item.str;
            span.style.position = 'absolute';
            span.style.left = tx[4] + 'px';
            span.style.top = (displayViewport.height - tx[5]) + 'px';
            span.style.fontSize = Math.abs(tx[0]) + 'px';
            span.style.fontFamily = item.fontName || 'sans-serif';
            // Scale width to approximate PDF text spacing
            if (item.width && Math.abs(tx[0]) > 0) {
                const scaledWidth = item.width * displayViewport.scale;
                span.style.width = scaledWidth + 'px';
                span.style.display = 'inline-block';
            }
            textLayerDiv.appendChild(span);
        });
    }

    /**
     * v6.0.4: Click-to-drag panning for zoomed PDFs.
     * Only activates when NOT in magnifier mode and NOT selecting text.
     * Uses middle-click (always) or left-click with >5px movement threshold.
     * Scrolls the wrapper element itself (which has overflow: auto).
     */
    function _initPanDrag(state) {
        const wrapper = state.wrapper;
        if (!wrapper) return;

        let isDragging = false;
        let startX = 0, startY = 0;
        let scrollStartX = 0, scrollStartY = 0;
        let moved = false;

        wrapper.addEventListener('mousedown', function(e) {
            // Skip if magnifier active or if clicking a button/control
            if (state.magnifierActive) return;
            if (e.target.closest('.pdfv-zoom-bar, button, a')) return;

            // Middle-click always starts pan; left-click starts potential pan
            if (e.button === 1 || e.button === 0) {
                isDragging = true;
                moved = false;
                startX = e.clientX;
                startY = e.clientY;
                // v6.0.4: Scroll the wrapper itself (has overflow: auto), not its parent
                scrollStartX = wrapper.scrollLeft;
                scrollStartY = wrapper.scrollTop;
                e.preventDefault();
            }
        });

        wrapper.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            // Movement threshold of 5px before activating pan (prevents blocking text selection)
            if (!moved && Math.abs(dx) < 5 && Math.abs(dy) < 5) return;
            moved = true;

            wrapper.style.cursor = 'grabbing';
            // v6.0.4: Scroll wrapper directly
            wrapper.scrollLeft = scrollStartX - dx;
            wrapper.scrollTop = scrollStartY - dy;
        });

        function endDrag() {
            if (isDragging) {
                isDragging = false;
                wrapper.style.cursor = '';
            }
        }

        wrapper.addEventListener('mouseup', endDrag);
        wrapper.addEventListener('mouseleave', endDrag);
    }

    async function _setZoom(state, newScale) {
        const wrapper = state.wrapper;
        const oldScale = state.currentScale;

        // v6.0.4: Track viewport center before re-render so we can restore it
        let centerFractionX = 0.5, centerFractionY = 0;
        if (wrapper && wrapper.scrollWidth > 0 && wrapper.scrollHeight > 0) {
            // Center of current viewport as fraction of total scroll content
            centerFractionX = (wrapper.scrollLeft + wrapper.clientWidth / 2) / wrapper.scrollWidth;
            centerFractionY = (wrapper.scrollTop + wrapper.clientHeight / 2) / wrapper.scrollHeight;
        }

        state.currentScale = newScale;
        if (state.zoomLabel) {
            state.zoomLabel.textContent = Math.round(newScale * 50) + '%';
        }

        await _renderPages(state);

        // v6.0.4: Restore viewport center after re-render
        if (wrapper && wrapper.scrollWidth > 0) {
            wrapper.scrollLeft = centerFractionX * wrapper.scrollWidth - wrapper.clientWidth / 2;
            wrapper.scrollTop = centerFractionY * wrapper.scrollHeight - wrapper.clientHeight / 2;
        }
    }

    function _fitWidth(state) {
        if (!state.wrapper || !state.pdf) return;
        // Get container width (minus padding)
        const containerWidth = state.wrapper.parentElement.clientWidth - 32;
        // Get first page to determine base width
        state.pdf.getPage(1).then(function(page) {
            const baseViewport = page.getViewport({ scale: 1.0 });
            const fitScale = containerWidth / baseViewport.width;
            _setZoom(state, Math.max(state.minScale, Math.min(fitScale, state.maxScale)));
        });
    }

    function _toggleMagnifier(state) {
        const wrapper = state.wrapper;
        if (!wrapper) return;

        // Remove existing magnifier
        const existing = wrapper.querySelector('.pdfv-magnifier');
        if (existing) existing.remove();

        if (!state.magnifierActive) {
            // Remove listeners
            wrapper.removeEventListener('mousemove', wrapper._magMove);
            wrapper.removeEventListener('mouseleave', wrapper._magLeave);
            return;
        }

        // Create magnifier element
        const mag = document.createElement('div');
        mag.className = 'pdfv-magnifier';
        mag.style.display = 'none';
        wrapper.appendChild(mag);

        const magCanvas = document.createElement('canvas');
        const magSize = 180;
        const magZoom = 3;
        magCanvas.width = magSize * (window.devicePixelRatio || 1);
        magCanvas.height = magSize * (window.devicePixelRatio || 1);
        magCanvas.style.width = magSize + 'px';
        magCanvas.style.height = magSize + 'px';
        mag.appendChild(magCanvas);

        wrapper._magMove = function(e) {
            const canvas = e.target.closest('canvas');
            if (!canvas) {
                mag.style.display = 'none';
                return;
            }

            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Position magnifier
            const wrapRect = wrapper.getBoundingClientRect();
            mag.style.display = 'block';
            mag.style.left = (e.clientX - wrapRect.left - magSize / 2) + 'px';
            mag.style.top = (e.clientY - wrapRect.top - magSize / 2) + 'px';

            // Draw zoomed portion of source canvas
            const ctx = magCanvas.getContext('2d');
            const dpr = window.devicePixelRatio || 1;
            const srcX = (x / parseFloat(canvas.style.width || canvas.width)) * canvas.width;
            const srcY = (y / parseFloat(canvas.style.height || canvas.height)) * canvas.height;
            const srcSize = (magSize * dpr) / magZoom;

            ctx.clearRect(0, 0, magCanvas.width, magCanvas.height);
            ctx.drawImage(
                canvas,
                srcX - srcSize / 2, srcY - srcSize / 2, srcSize, srcSize,
                0, 0, magCanvas.width, magCanvas.height
            );
        };

        wrapper._magLeave = function() {
            mag.style.display = 'none';
        };

        wrapper.addEventListener('mousemove', wrapper._magMove);
        wrapper.addEventListener('mouseleave', wrapper._magLeave);
    }

    return {
        init,
        render,
        isAvailable: () => isLoaded,
        getError: () => lastError,
        getActiveState: () => _activeState,
    };
})();
