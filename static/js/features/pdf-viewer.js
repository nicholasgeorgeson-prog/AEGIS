/**
 * PDF.js Viewer Module v2.0
 * Renders PDF pages into canvas elements with:
 * - HiDPI/Retina-aware rendering (devicePixelRatio)
 * - Zoom controls (+/−/fit width)
 * - Magnifier loupe on hover
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
     * @param {object} options - { scale: 2.0, showZoomBar: true, showMagnifier: true }
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

            // Create state for this viewer
            const state = {
                pdf: pdf,
                url: url,
                currentScale: baseScale,
                minScale: 0.5,
                maxScale: 4.0,
                magnifierActive: false,
                container: container,
                wrapper: null,
                zoomLabel: null,
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

            // Render all pages
            await _renderPages(state);

        } catch (e) {
            console.error('[PDFViewer] Render error:', e);
            container.innerHTML = `<div class="pdfv-error">Failed to render PDF: ${e.message}<br><small>The original file may no longer be available.</small></div>`;
            throw e;
        }
    }

    async function _renderPages(state) {
        const { pdf, currentScale, wrapper } = state;
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
        }
    }

    function _setZoom(state, newScale) {
        state.currentScale = newScale;
        if (state.zoomLabel) {
            state.zoomLabel.textContent = Math.round(newScale * 50) + '%';
        }
        _renderPages(state);
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
