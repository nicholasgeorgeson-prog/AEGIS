/**
 * PDF.js Viewer Module
 * v4.5.0: Lightweight IIFE that renders PDF pages into canvas elements.
 * Used as a toggle option in Statement History for pixel-perfect PDF viewing.
 */
window.TWR = window.TWR || {};
TWR.PDFViewer = (function() {
    'use strict';

    let pdfjsLib = null;
    let isLoaded = false;
    let lastError = null;

    async function init() {
        if (isLoaded) return true;
        try {
            // v4.5.0: Pre-check that the .mjs file is accessible before attempting ESM import
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
     * Render a PDF into a container element.
     * @param {HTMLElement} container - Target container
     * @param {string} url - URL to the PDF file
     * @param {object} options - { scale: 1.2 }
     */
    async function render(container, url, options = {}) {
        if (!await init()) {
            const errMsg = lastError || 'Unknown error';
            console.error('[PDFViewer] Init failed:', errMsg);
            container.innerHTML = `<div class="pdfv-error">PDF.js could not be loaded: ${errMsg}.<br><small>Falling back to HTML view.</small></div>`;
            throw new Error('PDF.js init failed: ' + errMsg);
        }

        container.innerHTML = '<div class="pdfv-loading"><div class="sfh-spinner"></div><p>Loading PDF...</p></div>';

        try {
            const pdf = await pdfjsLib.getDocument(url).promise;
            container.innerHTML = '';

            const scale = options.scale || 1.2;
            const wrapper = document.createElement('div');
            wrapper.className = 'pdfv-wrapper';
            container.appendChild(wrapper);

            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const viewport = page.getViewport({ scale });

                const pageDiv = document.createElement('div');
                pageDiv.className = 'pdfv-page';
                pageDiv.dataset.pageNum = i;

                // Page number label
                const label = document.createElement('div');
                label.className = 'pdfv-page-label';
                label.textContent = `Page ${i} of ${pdf.numPages}`;
                pageDiv.appendChild(label);

                const canvas = document.createElement('canvas');
                canvas.width = viewport.width;
                canvas.height = viewport.height;
                pageDiv.appendChild(canvas);

                wrapper.appendChild(pageDiv);

                await page.render({
                    canvasContext: canvas.getContext('2d'),
                    viewport
                }).promise;
            }
        } catch (e) {
            console.error('[PDFViewer] Render error:', e);
            container.innerHTML = `<div class="pdfv-error">Failed to render PDF: ${e.message}<br><small>The original file may no longer be available.</small></div>`;
            throw e;  // Re-throw so callers can provide fallback content
        }
    }

    return {
        init,
        render,
        isAvailable: () => isLoaded,
        getError: () => lastError
    };
})();
