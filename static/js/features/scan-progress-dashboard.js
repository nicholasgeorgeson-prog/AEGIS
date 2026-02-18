/**
 * AEGIS Scan Progress Dashboard
 * v4.5.0: Step-by-step scan progress checklist with sub-steps, ETA, and animations.
 * Replaces the simple loading overlay during single-document review.
 */
window.TWR = window.TWR || {};
TWR.ScanProgress = (function() {
    'use strict';

    // Step definitions matching the backend phases
    const STEPS = [
        { id: 'upload',     name: 'Upload Document',              phase: 'upload',          weight: 5 },
        { id: 'extract',    name: 'Extract Content',              phase: 'extracting',      weight: 15 },
        { id: 'parse',      name: 'Parse Document Structure',     phase: 'parsing',         weight: 10 },
        { id: 'quality',    name: 'Run Quality Checks',           phase: 'checking',        weight: 35 },
        { id: 'nlp',        name: 'NLP Analysis',                 phase: 'checking_nlp',    weight: 10 },
        { id: 'roles',      name: 'Extract Roles',                phase: 'postprocessing',  weight: 15 },
        { id: 'finalize',   name: 'Finalize Results',             phase: 'complete',        weight: 10 }
    ];

    let overlay = null;
    let state = {
        active: false,
        currentStepIdx: -1,
        stepStartTimes: {},
        stepDurations: {},
        startTime: null,
        filename: ''
    };

    // Historical averages (updated after each scan)
    let avgDurations = JSON.parse(localStorage.getItem('aegis_step_durations') || '{}');

    function create(filename) {
        destroy(); // Clean up any existing

        state = {
            active: true,
            currentStepIdx: -1,
            stepStartTimes: {},
            stepDurations: {},
            startTime: Date.now(),
            filename: filename || 'document'
        };

        overlay = document.createElement('div');
        overlay.className = 'spd-overlay';
        overlay.id = 'spd-overlay';
        overlay.innerHTML = buildHTML(filename);
        document.body.appendChild(overlay);

        // Animate in
        requestAnimationFrame(() => overlay.classList.add('spd-visible'));

        // Wire cancel button
        const cancelBtn = overlay.querySelector('.spd-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                if (typeof window.cancelCurrentJob === 'function') {
                    // cancelCurrentJob handles UI cleanup including destroy()
                    window.cancelCurrentJob();
                } else {
                    // v4.6.1: Fallback if cancelCurrentJob not wired — still clean up UI
                    console.warn('[ScanProgress] cancelCurrentJob not available, cleaning up UI only');
                    destroy();
                    if (typeof setLoading === 'function') setLoading(false);
                    if (window.LoadingTracker) LoadingTracker.reset();
                }
            });
        }

        // Start on upload step
        activateStep(0);
    }

    function buildHTML(filename) {
        const displayName = filename.length > 50 ? '...' + filename.slice(-47) : filename;
        const stepsHTML = STEPS.map((step, i) => `
            <div class="spd-step spd-pending" data-step-idx="${i}" id="spd-step-${step.id}">
                <div class="spd-step-icon">
                    <div class="spd-pending"></div>
                </div>
                <div class="spd-step-content">
                    <div class="spd-step-name">${step.name}</div>
                    <div class="spd-step-detail" style="display:none;"></div>
                    <div class="spd-step-bar" style="display:none;">
                        <div class="spd-step-bar-fill"></div>
                    </div>
                </div>
                <div class="spd-step-duration"></div>
            </div>
        `).join('');

        return `
            <div class="spd-container">
                <div class="spd-header">
                    <div class="spd-filename">${escapeHtml(displayName)}</div>
                    <h2 class="spd-title">Analyzing Document</h2>
                    <div class="spd-subtitle">Please wait while AEGIS processes your document</div>
                </div>

                <div class="spd-cinematic-slot" id="spd-cinematic-slot"></div>

                <div class="spd-overall">
                    <div class="spd-overall-bar">
                        <div class="spd-overall-fill" id="spd-overall-fill"></div>
                    </div>
                    <div class="spd-overall-pct" id="spd-overall-pct">0%</div>
                </div>

                <div class="spd-steps" id="spd-steps">
                    ${stepsHTML}
                </div>

                <div class="spd-eta">
                    <span>Estimated time remaining</span>
                    <span class="spd-eta-value" id="spd-eta-value">calculating...</span>
                </div>

                <button class="spd-cancel" type="button">Cancel</button>
            </div>
        `;
    }

    function activateStep(idx) {
        if (!overlay || idx < 0 || idx >= STEPS.length) return;
        if (idx === state.currentStepIdx) return;

        // v5.9.4: Complete ALL steps between current and target (not just the previous one)
        // This prevents intermediate steps from appearing "skipped" when the backend
        // jumps phases (e.g., upload → checking skips extract and parse).
        if (state.currentStepIdx >= 0) {
            for (let i = state.currentStepIdx; i < idx; i++) {
                completeStep(i);
            }
        }

        state.currentStepIdx = idx;
        state.stepStartTimes[idx] = Date.now();

        const stepEl = overlay.querySelector(`[data-step-idx="${idx}"]`);
        if (!stepEl) return;

        // Update class
        stepEl.className = 'spd-step spd-active';

        // Show spinner
        const iconDiv = stepEl.querySelector('.spd-step-icon');
        iconDiv.innerHTML = '<div class="spd-spinner"></div>';

        // Show sub-progress bar
        const barEl = stepEl.querySelector('.spd-step-bar');
        if (barEl) barEl.style.display = 'block';

        // Update overall progress
        updateOverallProgress();
    }

    function completeStep(idx) {
        if (!overlay) return;
        const stepEl = overlay.querySelector(`[data-step-idx="${idx}"]`);
        if (!stepEl) return;

        stepEl.className = 'spd-step spd-done';

        // Show check icon
        const iconDiv = stepEl.querySelector('.spd-step-icon');
        iconDiv.innerHTML = `<div class="spd-check"><svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg></div>`;

        // Hide sub-bar
        const barEl = stepEl.querySelector('.spd-step-bar');
        if (barEl) barEl.style.display = 'none';
        const detailEl = stepEl.querySelector('.spd-step-detail');
        if (detailEl) detailEl.style.display = 'none';

        // Show duration
        const startTime = state.stepStartTimes[idx];
        if (startTime) {
            const dur = ((Date.now() - startTime) / 1000).toFixed(1);
            state.stepDurations[idx] = parseFloat(dur);
            const durEl = stepEl.querySelector('.spd-step-duration');
            if (durEl) durEl.textContent = `${dur}s`;
        }
    }

    function updateStepProgress(stepId, progress, detail) {
        if (!overlay) return;

        // Find step index by phase or id
        let idx = STEPS.findIndex(s => s.id === stepId || s.phase === stepId);
        if (idx < 0) return;

        // If this step is ahead of current, activate it
        if (idx > state.currentStepIdx) {
            activateStep(idx);
        }

        const stepEl = overlay.querySelector(`[data-step-idx="${idx}"]`);
        if (!stepEl) return;

        // Update sub-bar
        if (typeof progress === 'number') {
            const fillEl = stepEl.querySelector('.spd-step-bar-fill');
            if (fillEl) fillEl.style.width = `${Math.min(100, progress)}%`;
        }

        // Update detail text
        if (detail) {
            const detailEl = stepEl.querySelector('.spd-step-detail');
            if (detailEl) {
                // v4.6.1: Show checker breakdown during quality checks phase
                const match = detail.match(/Completed\s+(\S+)\s+\((\d+)\/(\d+)\)/);
                if (match && (stepId === 'quality' || stepId === 'checking')) {
                    const checkerName = match[1].replace(/_/g, ' ');
                    const completed = parseInt(match[2]);
                    const total = parseInt(match[3]);

                    // Build or update checker list
                    let listEl = stepEl.querySelector('.spd-checker-list');
                    if (!listEl) {
                        listEl = document.createElement('div');
                        listEl.className = 'spd-checker-list';
                        detailEl.parentNode.insertBefore(listEl, detailEl.nextSibling);
                    }

                    // Add completed checker item
                    if (!listEl.querySelector(`[data-checker="${match[1]}"]`)) {
                        const item = document.createElement('div');
                        item.className = 'spd-checker-item spd-checker-done';
                        item.dataset.checker = match[1];
                        item.innerHTML = `<span class="spd-checker-icon">✓</span> <span class="spd-checker-name">${checkerName}</span>`;
                        listEl.appendChild(item);
                        // Auto-scroll to show latest checker
                        listEl.scrollTop = listEl.scrollHeight;
                    }

                    detailEl.textContent = `${completed} of ${total} checks completed`;
                    detailEl.style.display = 'block';
                } else if (detail.match(/^Running quality checks/)) {
                    detailEl.textContent = detail;
                    detailEl.style.display = 'block';
                } else {
                    detailEl.textContent = detail;
                    detailEl.style.display = 'block';
                }
            }
        }

        updateOverallProgress();
    }

    function updateOverallProgress() {
        if (!overlay) return;

        // Calculate weighted overall progress
        let totalWeight = 0;
        let completedWeight = 0;

        STEPS.forEach((step, idx) => {
            totalWeight += step.weight;
            if (idx < state.currentStepIdx) {
                completedWeight += step.weight;
            } else if (idx === state.currentStepIdx) {
                // Partial credit for active step
                const barFill = overlay.querySelector(`[data-step-idx="${idx}"] .spd-step-bar-fill`);
                const pct = barFill ? parseFloat(barFill.style.width) || 0 : 0;
                completedWeight += step.weight * (pct / 100);
            }
        });

        const overall = Math.round((completedWeight / totalWeight) * 100);
        const fillEl = overlay.querySelector('#spd-overall-fill');
        const pctEl = overlay.querySelector('#spd-overall-pct');
        if (fillEl) fillEl.style.width = `${overall}%`;
        if (pctEl) pctEl.textContent = `${overall}%`;

        // Update ETA
        updateETA(overall);
    }

    function updateETA(overallPct) {
        const etaEl = overlay?.querySelector('#spd-eta-value');
        if (!etaEl || overallPct < 5) return;

        const elapsed = (Date.now() - state.startTime) / 1000;
        const rate = overallPct / elapsed; // %/second
        const remaining = (100 - overallPct) / rate;

        if (remaining < 2) {
            etaEl.textContent = 'almost done';
        } else if (remaining < 60) {
            etaEl.textContent = `~${Math.round(remaining)}s`;
        } else {
            const mins = Math.floor(remaining / 60);
            const secs = Math.round(remaining % 60);
            etaEl.textContent = `~${mins}m ${secs}s`;
        }
    }

    /**
     * Map from the backend's progress callback (phase, pct, message) to dashboard steps.
     * Called by the job polling loop.
     */
    function onProgress(phase, pct, message) {
        if (!state.active) return;

        // Map backend phases to step IDs
        const phaseMap = {
            'extracting': 'extract',
            'parsing':    'parse',
            'checking':   'quality',
            'postprocessing': 'roles',
            'exporting':  'finalize',
            'complete':   'finalize'
        };

        const stepId = phaseMap[phase] || phase;

        // NLP sub-phase detection
        if (phase === 'checking' && message && message.toLowerCase().includes('nlp')) {
            updateStepProgress('nlp', pct, message);
            return;
        }

        updateStepProgress(stepId, pct, message);

        // If complete, finish all remaining steps
        if (phase === 'complete') {
            for (let i = state.currentStepIdx; i < STEPS.length; i++) {
                if (i === state.currentStepIdx) completeStep(i);
                else {
                    activateStep(i);
                    completeStep(i);
                }
            }
            // Save timing data for ETA improvements
            saveTimings();
        }
    }

    function saveTimings() {
        try {
            const key = 'aegis_step_durations';
            const saved = JSON.parse(localStorage.getItem(key) || '{}');
            STEPS.forEach((step, idx) => {
                const dur = state.stepDurations[idx];
                if (dur) {
                    // Running average
                    const prev = saved[step.id] || dur;
                    saved[step.id] = (prev * 0.7 + dur * 0.3); // Weighted average
                }
            });
            localStorage.setItem(key, JSON.stringify(saved));
            avgDurations = saved;
        } catch (_) { /* ignore storage errors */ }
    }

    function complete() {
        if (!overlay) return;
        onProgress('complete', 100, 'Done');
        setTimeout(() => destroy(), 800);
    }

    function destroy() {
        if (overlay) {
            overlay.classList.remove('spd-visible');
            setTimeout(() => {
                overlay?.remove();
                overlay = null;
            }, 400);
        }
        state.active = false;
    }

    function isActive() {
        return state.active;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    return {
        create,
        onProgress,
        updateStepProgress,
        complete,
        destroy,
        isActive
    };
})();
