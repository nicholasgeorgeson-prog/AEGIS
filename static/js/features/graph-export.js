/**
 * AEGIS - Graph Export Module
 * ======================================
 * ENH-003: Export charts and graphs as PNG/SVG for reports and presentations.
 *
 * Features:
 * - Export Chart.js charts to PNG
 * - Export D3.js visualizations to SVG
 * - Export HTML canvas elements
 * - High-resolution export options
 * - Automatic filename generation
 *
 * Version: 1.0.0
 */

window.GraphExport = (function() {
    'use strict';

    const VERSION = '1.0.0';
    const LOG_PREFIX = '[TWR GraphExport]';

    // Default export settings
    const DEFAULT_SETTINGS = {
        scale: 2,              // Scale factor for high-res PNG
        backgroundColor: '#ffffff',
        format: 'png',         // 'png' or 'svg'
        filename: 'chart',
        quality: 0.92          // JPEG quality (not used for PNG)
    };

    /**
     * Export a Chart.js chart to PNG.
     * @param {Chart} chart - Chart.js chart instance
     * @param {Object} options - Export options
     */
    function exportChartToPng(chart, options = {}) {
        if (!chart || !chart.canvas) {
            console.error(LOG_PREFIX, 'Invalid chart instance');
            return;
        }

        const settings = { ...DEFAULT_SETTINGS, ...options };
        const canvas = chart.canvas;

        // Create high-res canvas
        const exportCanvas = document.createElement('canvas');
        const ctx = exportCanvas.getContext('2d');
        const width = canvas.width * settings.scale;
        const height = canvas.height * settings.scale;

        exportCanvas.width = width;
        exportCanvas.height = height;

        // Fill background
        ctx.fillStyle = settings.backgroundColor;
        ctx.fillRect(0, 0, width, height);

        // Scale and draw chart
        ctx.scale(settings.scale, settings.scale);
        ctx.drawImage(canvas, 0, 0);

        // Convert to blob and download
        exportCanvas.toBlob((blob) => {
            downloadBlob(blob, `${settings.filename}.png`);
            console.log(LOG_PREFIX, `Exported chart as ${settings.filename}.png`);
        }, 'image/png');
    }

    /**
     * Export an SVG element to SVG file.
     * @param {SVGElement} svgElement - SVG DOM element
     * @param {Object} options - Export options
     */
    function exportSvgToFile(svgElement, options = {}) {
        if (!svgElement || svgElement.tagName.toLowerCase() !== 'svg') {
            console.error(LOG_PREFIX, 'Invalid SVG element');
            return;
        }

        const settings = { ...DEFAULT_SETTINGS, ...options };

        // Clone the SVG to avoid modifying the original
        const svgClone = svgElement.cloneNode(true);

        // Ensure proper namespaces
        svgClone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        svgClone.setAttribute('xmlns:xlink', 'http://www.w3.org/1999/xlink');

        // Add viewBox if missing
        if (!svgClone.hasAttribute('viewBox')) {
            const bbox = svgElement.getBBox();
            svgClone.setAttribute('viewBox', `${bbox.x} ${bbox.y} ${bbox.width} ${bbox.height}`);
        }

        // Inline all styles for portability
        inlineStyles(svgClone);

        // Serialize to string
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svgClone);

        // Create blob and download
        const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        downloadBlob(blob, `${settings.filename}.svg`);

        console.log(LOG_PREFIX, `Exported SVG as ${settings.filename}.svg`);
    }

    /**
     * Export an SVG element to PNG.
     * @param {SVGElement} svgElement - SVG DOM element
     * @param {Object} options - Export options
     */
    function exportSvgToPng(svgElement, options = {}) {
        if (!svgElement || svgElement.tagName.toLowerCase() !== 'svg') {
            console.error(LOG_PREFIX, 'Invalid SVG element');
            return;
        }

        const settings = { ...DEFAULT_SETTINGS, ...options };

        // Get SVG dimensions
        const bbox = svgElement.getBBox();
        const width = (svgElement.width?.baseVal?.value || bbox.width || 800) * settings.scale;
        const height = (svgElement.height?.baseVal?.value || bbox.height || 600) * settings.scale;

        // Clone and inline styles
        const svgClone = svgElement.cloneNode(true);
        svgClone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        inlineStyles(svgClone);

        // Serialize
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svgClone);
        const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);

        // Draw to canvas
        const img = new Image();
        img.onload = function() {
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;

            const ctx = canvas.getContext('2d');
            ctx.fillStyle = settings.backgroundColor;
            ctx.fillRect(0, 0, width, height);
            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob((blob) => {
                downloadBlob(blob, `${settings.filename}.png`);
                URL.revokeObjectURL(url);
                console.log(LOG_PREFIX, `Exported SVG to ${settings.filename}.png`);
            }, 'image/png');
        };
        img.onerror = function() {
            console.error(LOG_PREFIX, 'Failed to load SVG for PNG conversion');
            URL.revokeObjectURL(url);
        };
        img.src = url;
    }

    /**
     * Export a canvas element to PNG.
     * @param {HTMLCanvasElement} canvas - Canvas element
     * @param {Object} options - Export options
     */
    function exportCanvasToPng(canvas, options = {}) {
        if (!canvas || canvas.tagName.toLowerCase() !== 'canvas') {
            console.error(LOG_PREFIX, 'Invalid canvas element');
            return;
        }

        const settings = { ...DEFAULT_SETTINGS, ...options };

        canvas.toBlob((blob) => {
            downloadBlob(blob, `${settings.filename}.png`);
            console.log(LOG_PREFIX, `Exported canvas as ${settings.filename}.png`);
        }, 'image/png');
    }

    /**
     * Export any DOM element by rendering to canvas.
     * Uses html2canvas-like approach (basic implementation).
     * @param {HTMLElement} element - DOM element to export
     * @param {Object} options - Export options
     */
    function exportElementToPng(element, options = {}) {
        const settings = { ...DEFAULT_SETTINGS, ...options };

        // Check if it's an SVG
        if (element.tagName?.toLowerCase() === 'svg') {
            return exportSvgToPng(element, options);
        }

        // Check if it's a canvas
        if (element.tagName?.toLowerCase() === 'canvas') {
            return exportCanvasToPng(element, options);
        }

        // Check if it contains a canvas (Chart.js)
        const canvas = element.querySelector('canvas');
        if (canvas) {
            return exportCanvasToPng(canvas, options);
        }

        // Check if it contains an SVG (D3.js)
        const svg = element.querySelector('svg');
        if (svg) {
            return exportSvgToPng(svg, options);
        }

        console.warn(LOG_PREFIX, 'Element does not contain exportable content (canvas or SVG)');
    }

    /**
     * Inline computed styles into SVG elements for portability.
     * @param {SVGElement} svg - SVG element to process
     */
    function inlineStyles(svg) {
        const elements = svg.querySelectorAll('*');

        elements.forEach(el => {
            const computedStyle = window.getComputedStyle(el);
            const importantStyles = [
                'fill', 'stroke', 'stroke-width', 'stroke-dasharray',
                'font-family', 'font-size', 'font-weight', 'text-anchor',
                'opacity', 'fill-opacity', 'stroke-opacity'
            ];

            importantStyles.forEach(prop => {
                const value = computedStyle.getPropertyValue(prop);
                if (value && value !== 'none' && value !== '') {
                    el.style[prop] = value;
                }
            });
        });
    }

    /**
     * Download a blob as a file.
     * @param {Blob} blob - Blob to download
     * @param {string} filename - Filename for download
     */
    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    /**
     * Generate a filename based on content type and timestamp.
     * @param {string} prefix - Filename prefix
     * @returns {string} Generated filename (without extension)
     */
    function generateFilename(prefix = 'chart') {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
        return `${prefix}_${timestamp}`;
    }

    /**
     * Add export button to a chart container.
     * @param {HTMLElement} container - Container element
     * @param {Object} options - Button and export options
     */
    function addExportButton(container, options = {}) {
        const settings = {
            buttonText: 'Export',
            buttonClass: 'btn btn-sm btn-secondary',
            position: 'top-right',
            formats: ['png', 'svg'],
            ...options
        };

        const button = document.createElement('button');
        button.className = settings.buttonClass;
        button.innerHTML = `<i data-lucide="download"></i> ${settings.buttonText}`;
        button.style.position = 'absolute';
        button.style.zIndex = '10';

        // Position the button
        switch (settings.position) {
            case 'top-right':
                button.style.top = '10px';
                button.style.right = '10px';
                break;
            case 'top-left':
                button.style.top = '10px';
                button.style.left = '10px';
                break;
            case 'bottom-right':
                button.style.bottom = '10px';
                button.style.right = '10px';
                break;
            case 'bottom-left':
                button.style.bottom = '10px';
                button.style.left = '10px';
                break;
        }

        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const filename = generateFilename(options.filenamePrefix || 'chart');

            // Find exportable content
            const canvas = container.querySelector('canvas');
            const svg = container.querySelector('svg');

            if (canvas) {
                exportCanvasToPng(canvas, { filename, ...options });
            } else if (svg) {
                if (settings.formats.includes('svg')) {
                    exportSvgToFile(svg, { filename, ...options });
                } else {
                    exportSvgToPng(svg, { filename, ...options });
                }
            } else {
                console.warn(LOG_PREFIX, 'No exportable content found in container');
            }
        });

        // Make container relative if not already
        const containerStyle = window.getComputedStyle(container);
        if (containerStyle.position === 'static') {
            container.style.position = 'relative';
        }

        container.appendChild(button);

        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons({ attrs: { class: 'lucide-icon' } });
        }

        return button;
    }

    // Public API
    return {
        VERSION,

        // Export functions
        exportChartToPng,
        exportSvgToFile,
        exportSvgToPng,
        exportCanvasToPng,
        exportElementToPng,

        // Utilities
        generateFilename,
        addExportButton,
        downloadBlob
    };
})();

console.log('[TWR GraphExport] Module loaded v' + window.GraphExport.VERSION);
