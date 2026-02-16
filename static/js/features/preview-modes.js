// v3.0.97: Fix Assistant v2 - Preview Modes
// WP9: Live Preview and Split Screen View

const PreviewModes = (function() {
    'use strict';

    // ═══════════════════════════════════════════════════════════════════════════
    // STATE
    // ═══════════════════════════════════════════════════════════════════════════

    const state = {
        containerEl: null,
        paragraphs: [],
        fixes: [],
        getDecisions: null,
        onModeChange: null,
        livePreviewEnabled: false,
        splitScreenEnabled: false,
        currentFix: null,
        scrollListeners: []
    };

    // ═══════════════════════════════════════════════════════════════════════════
    // HELPERS
    // ═══════════════════════════════════════════════════════════════════════════

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML; // SAFE: escapeHtml function output
    }

    function escapeRegex(string) {
        if (!string) return '';
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function log(message, ...args) {
        console.log(`[TWR PreviewModes] ${message}`, ...args);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════════════════════

    function init(options = {}) {
        log('Initializing...');
        
        state.containerEl = options.containerEl || document.body;
        state.paragraphs = options.paragraphs || [];
        state.fixes = options.fixes || [];
        state.getDecisions = options.getDecisions || (() => new Map());
        state.onModeChange = options.onModeChange || null;
        state.livePreviewEnabled = false;
        state.splitScreenEnabled = false;
        state.currentFix = null;
        state.scrollListeners = [];

        log('Initialized with', state.paragraphs.length, 'paragraphs and', state.fixes.length, 'fixes');
    }

    function destroy() {
        log('Destroying...');
        clearFixPreview();
        setSplitScreen(false);
        removeScrollListeners();
        state.containerEl = null;
        state.paragraphs = [];
        state.fixes = [];
        state.getDecisions = null;
        state.onModeChange = null;
        state.currentFix = null;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // LIVE PREVIEW
    // ═══════════════════════════════════════════════════════════════════════════

    function setLivePreview(enabled) {
        const wasEnabled = state.livePreviewEnabled;
        state.livePreviewEnabled = !!enabled;
        
        if (!enabled) {
            clearFixPreview();
        } else if (state.currentFix) {
            showFixPreview(state.currentFix);
        }
        
        if (wasEnabled !== state.livePreviewEnabled && state.onModeChange) {
            state.onModeChange({ livePreview: state.livePreviewEnabled });
        }
        
        log('Live preview', enabled ? 'enabled' : 'disabled');
    }

    function isLivePreviewEnabled() {
        return state.livePreviewEnabled;
    }

    function showFixPreview(fix) {
        state.currentFix = fix;
        
        if (!state.livePreviewEnabled || !fix) return;
        
        clearFixPreview();
        
        const paraEl = document.querySelector(
            `.fav2-paragraph[data-index="${fix.paragraph_index}"]`
        );
        if (!paraEl) {
            log('Paragraph element not found for index:', fix.paragraph_index);
            return;
        }
        
        // Store original HTML for restoration
        if (!paraEl.dataset.originalHtml) {
            paraEl.dataset.originalHtml = paraEl.innerHTML;
        }
        
        const original = fix.flagged_text;
        const replacement = fix.suggestion;
        
        if (!original) {
            log('No flagged_text in fix');
            return;
        }
        
        // Escape special regex characters
        const escaped = escapeRegex(original);
        const regex = new RegExp(`(${escaped})`, 'gi');
        
        // Replace with preview markup
        let html = paraEl.dataset.originalHtml;
        html = html.replace(regex, (match) => {
            return `<span class="fav2-preview-change">` +
                   `<del class="fav2-preview-original">${escapeHtml(match)}</del>` +
                   `<ins class="fav2-preview-replacement">${escapeHtml(replacement)}</ins>` +
                   `</span>`;
        });
        
        // SAFE: match and replacement escaped via escapeHtml()
        paraEl.innerHTML = html;
        paraEl.classList.add('fav2-preview-active');
        
        log('Preview shown for fix:', fix.index);
    }

    function clearFixPreview() {
        const previewEls = document.querySelectorAll('.fav2-preview-active');
        previewEls.forEach(el => {
            if (el.dataset.originalHtml) {
                el.innerHTML = el.dataset.originalHtml; // SAFE: restoring saved content
                delete el.dataset.originalHtml;
            }
            el.classList.remove('fav2-preview-active');
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // SPLIT SCREEN
    // ═══════════════════════════════════════════════════════════════════════════

    function setSplitScreen(enabled) {
        const wasEnabled = state.splitScreenEnabled;
        state.splitScreenEnabled = !!enabled;
        
        if (enabled) {
            createSplitView();
            updateSplitScreen();
        } else {
            removeSplitView();
        }
        
        if (wasEnabled !== state.splitScreenEnabled && state.onModeChange) {
            state.onModeChange({ splitScreen: state.splitScreenEnabled });
        }
        
        log('Split screen', enabled ? 'enabled' : 'disabled');
    }

    function isSplitScreenEnabled() {
        return state.splitScreenEnabled;
    }

    function createSplitView() {
        // Remove existing if present
        removeSplitView();
        
        const html = `
            <div class="fav2-split-view" id="fav2-split-view">
                <div class="fav2-split-panel fav2-split-original">
                    <div class="fav2-split-header">
                        <span class="fav2-split-title">Original Document</span>
                    </div>
                    <div class="fav2-split-content" id="fav2-split-original-content"></div>
                </div>
                <div class="fav2-split-divider"></div>
                <div class="fav2-split-panel fav2-split-fixed">
                    <div class="fav2-split-header">
                        <span class="fav2-split-title">With Accepted Fixes</span>
                        <span class="fav2-split-count">0 changes</span>
                    </div>
                    <div class="fav2-split-content" id="fav2-split-fixed-content"></div>
                </div>
            </div>
        `;
        
        if (state.containerEl) {
            state.containerEl.insertAdjacentHTML('beforeend', html);
        }
    }

    function removeSplitView() {
        removeScrollListeners();
        const existing = document.getElementById('fav2-split-view');
        if (existing) {
            existing.remove();
        }
    }

    function updateSplitScreen() {
        if (!state.splitScreenEnabled) return;
        
        const originalContent = document.getElementById('fav2-split-original-content');
        const fixedContent = document.getElementById('fav2-split-fixed-content');
        
        if (!originalContent || !fixedContent) {
            log('Split screen containers not found');
            return;
        }
        
        const decisions = state.getDecisions ? state.getDecisions() : new Map();
        let changeCount = 0;
        
        // Build paragraphs with fixes applied
        const fixedParagraphs = state.paragraphs.map(para => {
            const originalText = para.text || '';
            const fixedText = applyFixesToParagraph(para.index, originalText, decisions);
            const changed = originalText !== fixedText;
            if (changed) changeCount++;
            return { ...para, originalText, fixedText, changed };
        });
        
        // Render original side
        // SAFE: p.text escaped via escapeHtml()
        originalContent.innerHTML = state.paragraphs.map(p => 
            `<div class="fav2-split-para" data-index="${p.index}">${escapeHtml(p.text || '')}</div>`
        ).join('');
        
        // Render fixed side with diff highlighting
        // SAFE: originalText escaped via escapeHtml(); renderDiff uses escapeHtml()
        fixedContent.innerHTML = fixedParagraphs.map(p => {
            const classes = `fav2-split-para${p.changed ? ' fav2-changed' : ''}`;
            const content = p.changed 
                ? renderDiff(p.originalText, p.fixedText)
                : escapeHtml(p.originalText);
            return `<div class="${classes}" data-index="${p.index}">${content}</div>`;
        }).join('');
        
        // Update change count
        const countEl = document.querySelector('.fav2-split-count');
        if (countEl) {
            countEl.textContent = `${changeCount} change${changeCount !== 1 ? 's' : ''}`;
        }
        
        // Setup scroll sync
        setupScrollSync();
        
        log('Split screen updated:', changeCount, 'changes');
    }

    function applyFixesToParagraph(paraIndex, text, decisions) {
        if (!text) return '';
        
        // Find all accepted fixes for this paragraph
        const acceptedFixes = state.fixes.filter(f => 
            f.paragraph_index === paraIndex && 
            decisions.get(f.index)?.decision === 'accepted'
        );
        
        if (acceptedFixes.length === 0) return text;
        
        // Sort by position (longest match first to avoid partial replacements)
        acceptedFixes.sort((a, b) => (b.flagged_text?.length || 0) - (a.flagged_text?.length || 0));
        
        // Apply each fix
        let result = text;
        acceptedFixes.forEach(fix => {
            if (!fix.flagged_text) return;
            const regex = new RegExp(escapeRegex(fix.flagged_text), 'gi');
            result = result.replace(regex, fix.suggestion || '');
        });
        
        return result;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // SCROLL SYNCHRONIZATION
    // ═══════════════════════════════════════════════════════════════════════════

    function removeScrollListeners() {
        state.scrollListeners.forEach(({ el, handler }) => {
            el.removeEventListener('scroll', handler);
        });
        state.scrollListeners = [];
    }

    function setupScrollSync() {
        removeScrollListeners();
        
        const original = document.getElementById('fav2-split-original-content');
        const fixed = document.getElementById('fav2-split-fixed-content');
        
        if (!original || !fixed) return;
        
        let isSyncing = false;
        
        const syncScroll = (source, target) => {
            if (isSyncing) return;
            isSyncing = true;
            
            const maxScroll = source.scrollHeight - source.clientHeight;
            const scrollPercent = maxScroll > 0 ? source.scrollTop / maxScroll : 0;
            const targetMax = target.scrollHeight - target.clientHeight;
            target.scrollTop = scrollPercent * targetMax;
            
            requestAnimationFrame(() => { isSyncing = false; });
        };
        
        const origHandler = () => syncScroll(original, fixed);
        const fixedHandler = () => syncScroll(fixed, original);
        
        // BUG-L10 FIX: Added { passive: true } to prevent scroll-blocking violations
        original.addEventListener('scroll', origHandler, { passive: true });
        fixed.addEventListener('scroll', fixedHandler, { passive: true });
        
        state.scrollListeners.push({ el: original, handler: origHandler });
        state.scrollListeners.push({ el: fixed, handler: fixedHandler });
    }

    function syncScroll(scrollTop) {
        const original = document.getElementById('fav2-split-original-content');
        const fixed = document.getElementById('fav2-split-fixed-content');
        
        if (original) original.scrollTop = scrollTop;
        if (fixed) fixed.scrollTop = scrollTop;
    }

    function scrollToInSplit(paraIndex) {
        const original = document.getElementById('fav2-split-original-content');
        const fixed = document.getElementById('fav2-split-fixed-content');
        
        if (!original || !fixed) return;
        
        const targetEl = original.querySelector(`.fav2-split-para[data-index="${paraIndex}"]`);
        if (targetEl) {
            const offset = targetEl.offsetTop - 50;
            original.scrollTop = offset;
            fixed.scrollTop = offset;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // DIFF RENDERING
    // ═══════════════════════════════════════════════════════════════════════════

    function renderDiff(original, fixed) {
        if (!original && !fixed) return '';
        if (!original) return `<ins class="fav2-diff-added">${escapeHtml(fixed)}</ins>`;
        if (!fixed) return `<del class="fav2-diff-removed">${escapeHtml(original)}</del>`;
        
        // Word-level diff
        const origWords = original.split(/(\s+)/);
        const fixedWords = fixed.split(/(\s+)/);
        
        let result = [];
        let i = 0, j = 0;
        
        while (i < origWords.length || j < fixedWords.length) {
            if (i >= origWords.length) {
                result.push(`<ins class="fav2-diff-added">${escapeHtml(fixedWords[j])}</ins>`);
                j++;
            } else if (j >= fixedWords.length) {
                result.push(`<del class="fav2-diff-removed">${escapeHtml(origWords[i])}</del>`);
                i++;
            } else if (origWords[i] === fixedWords[j]) {
                result.push(escapeHtml(origWords[i]));
                i++; j++;
            } else {
                result.push(`<del class="fav2-diff-removed">${escapeHtml(origWords[i])}</del>`);
                result.push(`<ins class="fav2-diff-added">${escapeHtml(fixedWords[j])}</ins>`);
                i++; j++;
            }
        }
        
        return result.join('');
    }

    function applyFixes(text, fixes, decisions) {
        if (!text || !fixes || !decisions) return text || '';
        
        let result = text;
        const acceptedFixes = fixes.filter(f => 
            decisions.get(f.index)?.decision === 'accepted'
        );
        
        acceptedFixes.forEach(fix => {
            if (!fix.flagged_text) return;
            const regex = new RegExp(escapeRegex(fix.flagged_text), 'gi');
            result = result.replace(regex, fix.suggestion || '');
        });
        
        return result;
    }

    function getFixedDocument() {
        const decisions = state.getDecisions ? state.getDecisions() : new Map();
        
        return state.paragraphs.map(para => {
            const originalText = para.text || '';
            const fixedText = applyFixesToParagraph(para.index, originalText, decisions);
            return {
                index: para.index,
                originalText,
                fixedText,
                changed: originalText !== fixedText
            };
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════

    return {
        init,
        destroy,
        setLivePreview,
        isLivePreviewEnabled,
        showFixPreview,
        clearFixPreview,
        setSplitScreen,
        isSplitScreenEnabled,
        updateSplitScreen,
        syncScroll,
        scrollToInSplit,
        renderDiff,
        applyFixes,
        getFixedDocument
    };
})();

window.PreviewModes = PreviewModes;
console.log('[TWR PreviewModes] Module loaded v3.0.97');
