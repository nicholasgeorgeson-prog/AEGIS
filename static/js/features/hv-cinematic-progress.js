/**
 * HV Cinematic Progress Dashboard
 * ================================
 * v4.6.2: Full-screen cinematic progress overlay for hyperlink validation.
 * Shows live stats, domain breakdown, animated counters, current URL activity,
 * accurate ETA, and allows user to navigate away and return.
 *
 * Inspired by TWR.ScanProgress but purpose-built for link validation.
 */
window.HVCinematicProgress = (function() {
    'use strict';

    // =========================================================================
    // STATE
    // =========================================================================

    let overlay = null;
    let canvasCtx = null;
    let particleAnimId = null;
    let pulseAnimId = null;

    const state = {
        active: false,
        startTime: null,
        filename: '',
        phase: 'idle', // idle, extracting, validating, finalizing, complete
        totalUrls: 0,
        uniqueUrls: 0,
        completedUrls: 0,
        // Live status counts
        working: 0,
        broken: 0,
        blocked: 0,
        timeout: 0,
        redirect: 0,
        sslError: 0,
        dnsFailed: 0,
        // Domain tracking
        domains: {}, // domain -> { working, broken, total, category }
        domainOrder: [], // order of first appearance
        // Timing
        avgResponseMs: 0,
        minResponseMs: Infinity,
        maxResponseMs: 0,
        urlsPerSecond: 0,
        // Activity feed
        activityLog: [], // last 10 completed URLs
        currentUrl: '',
        // ETA
        eta: null,
        etaHistory: [], // for smoothing
        elapsedFormatted: '',
        // v5.0.5: Retest phase tracking
        retestTotal: 0,
        retestCompleted: 0
    };

    // Particles for background animation
    const particles = [];
    const PARTICLE_COUNT = 40;

    // =========================================================================
    // CREATE / DESTROY
    // =========================================================================

    function show(filename, totalUrls, uniqueUrls) {
        if (overlay) destroy();

        state.active = true;
        state.startTime = Date.now();
        state.filename = filename || 'URLs';
        state.phase = 'extracting';
        state.totalUrls = totalUrls || 0;
        state.uniqueUrls = uniqueUrls || 0;
        state.completedUrls = 0;
        state.working = 0;
        state.broken = 0;
        state.blocked = 0;
        state.timeout = 0;
        state.redirect = 0;
        state.sslError = 0;
        state.dnsFailed = 0;
        state.domains = {};
        state.domainOrder = [];
        state.avgResponseMs = 0;
        state.minResponseMs = Infinity;
        state.maxResponseMs = 0;
        state.urlsPerSecond = 0;
        state.activityLog = [];
        state.currentUrl = '';
        state.eta = null;
        state.etaHistory = [];
        state.retestTotal = 0;
        state.retestCompleted = 0;

        overlay = document.createElement('div');
        overlay.className = 'hvcp-overlay';
        overlay.id = 'hvcp-overlay';
        overlay.innerHTML = buildHTML();
        document.body.appendChild(overlay);

        // Initialize canvas particles
        initParticles();

        // Animate in
        requestAnimationFrame(() => {
            overlay.classList.add('hvcp-visible');
        });

        // Wire cancel button
        const cancelBtn = overlay.querySelector('.hvcp-cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                if (typeof HyperlinkValidatorState !== 'undefined' && HyperlinkValidatorState.cancelValidation) {
                    HyperlinkValidatorState.cancelValidation();
                }
                destroy();
            });
        }

        // Wire minimize buttons (top-right + bottom)
        overlay.querySelectorAll('.hvcp-minimize-btn').forEach(btn => {
            btn.addEventListener('click', minimize);
        });

        // Start counter update loop
        startCounterLoop();
    }

    function buildHTML() {
        const displayName = state.filename.length > 45
            ? state.filename.substring(0, 42) + '...'
            : state.filename;

        return `
            <canvas class="hvcp-particle-canvas" id="hvcp-canvas"></canvas>

            <div class="hvcp-container">
                <!-- Header -->
                <div class="hvcp-header">
                    <div class="hvcp-header-left">
                        <div class="hvcp-icon-pulse">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                            </svg>
                        </div>
                        <div>
                            <h2 class="hvcp-title">Hyperlink Validation</h2>
                            <div class="hvcp-filename">${escapeHtml(displayName)}</div>
                        </div>
                    </div>
                    <div class="hvcp-header-right">
                        <button class="hvcp-minimize-btn" title="Minimize — continue in background">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
                            </svg>
                            <span>Minimize</span>
                        </button>
                    </div>
                </div>

                <!-- Phase Indicator -->
                <div class="hvcp-phases">
                    <div class="hvcp-phase hvcp-phase-active" data-phase="extracting">
                        <div class="hvcp-phase-dot"></div>
                        <span>Extract</span>
                    </div>
                    <div class="hvcp-phase-line"></div>
                    <div class="hvcp-phase" data-phase="validating">
                        <div class="hvcp-phase-dot"></div>
                        <span>Validate</span>
                    </div>
                    <div class="hvcp-phase-line"></div>
                    <div class="hvcp-phase" data-phase="finalizing">
                        <div class="hvcp-phase-dot"></div>
                        <span>Finalize</span>
                    </div>
                </div>

                <!-- Main Progress Ring + Stats -->
                <div class="hvcp-main-row">
                    <!-- Central progress ring -->
                    <div class="hvcp-ring-container">
                        <svg class="hvcp-ring" viewBox="0 0 200 200">
                            <circle class="hvcp-ring-bg" cx="100" cy="100" r="85" />
                            <circle class="hvcp-ring-fill" cx="100" cy="100" r="85"
                                stroke-dasharray="534.07"
                                stroke-dashoffset="534.07"
                                id="hvcp-ring-fill" />
                        </svg>
                        <div class="hvcp-ring-center">
                            <div class="hvcp-ring-pct" id="hvcp-ring-pct">0%</div>
                            <div class="hvcp-ring-label" id="hvcp-ring-label">Starting...</div>
                        </div>
                    </div>

                    <!-- Status cards -->
                    <div class="hvcp-status-grid">
                        <div class="hvcp-stat-card hvcp-stat-working">
                            <div class="hvcp-stat-icon">✓</div>
                            <div class="hvcp-stat-value" id="hvcp-working">0</div>
                            <div class="hvcp-stat-label">Working</div>
                        </div>
                        <div class="hvcp-stat-card hvcp-stat-broken">
                            <div class="hvcp-stat-icon">✗</div>
                            <div class="hvcp-stat-value" id="hvcp-broken">0</div>
                            <div class="hvcp-stat-label">Broken</div>
                        </div>
                        <div class="hvcp-stat-card hvcp-stat-blocked">
                            <div class="hvcp-stat-icon">⊘</div>
                            <div class="hvcp-stat-value" id="hvcp-blocked">0</div>
                            <div class="hvcp-stat-label">Blocked</div>
                        </div>
                        <div class="hvcp-stat-card hvcp-stat-other">
                            <div class="hvcp-stat-icon">⏱</div>
                            <div class="hvcp-stat-value" id="hvcp-other">0</div>
                            <div class="hvcp-stat-label">Other</div>
                        </div>
                    </div>
                </div>

                <!-- Progress bar -->
                <div class="hvcp-progress-row">
                    <div class="hvcp-progress-bar">
                        <div class="hvcp-progress-fill" id="hvcp-progress-fill">
                            <div class="hvcp-progress-glow"></div>
                        </div>
                        <div class="hvcp-progress-segments" id="hvcp-progress-segments"></div>
                    </div>
                    <div class="hvcp-progress-meta">
                        <span id="hvcp-completed-count">0</span> / <span id="hvcp-total-count">0</span> URLs
                        <span class="hvcp-separator">·</span>
                        <span id="hvcp-rate">—</span> URLs/sec
                    </div>
                </div>

                <!-- Timing & ETA -->
                <div class="hvcp-timing-row">
                    <div class="hvcp-timing-item">
                        <span class="hvcp-timing-label">Elapsed</span>
                        <span class="hvcp-timing-value" id="hvcp-elapsed">0s</span>
                    </div>
                    <div class="hvcp-timing-item">
                        <span class="hvcp-timing-label">Avg Response</span>
                        <span class="hvcp-timing-value" id="hvcp-avg-response">—</span>
                    </div>
                    <div class="hvcp-timing-item hvcp-timing-eta">
                        <span class="hvcp-timing-label">Estimated Remaining</span>
                        <span class="hvcp-timing-value hvcp-eta-value" id="hvcp-eta">Calculating...</span>
                    </div>
                </div>

                <!-- Activity Feed -->
                <div class="hvcp-activity-section">
                    <div class="hvcp-activity-header">
                        <span>Live Activity</span>
                        <span class="hvcp-activity-badge" id="hvcp-domain-count">0 domains</span>
                    </div>
                    <div class="hvcp-activity-feed" id="hvcp-activity-feed">
                        <div class="hvcp-activity-empty">Waiting for results...</div>
                    </div>
                </div>

                <!-- Domain Health Strip -->
                <div class="hvcp-domains-section">
                    <div class="hvcp-domains-header">
                        <span>Domain Health</span>
                    </div>
                    <div class="hvcp-domains-strip" id="hvcp-domains-strip">
                        <div class="hvcp-domains-empty">Domains will appear as they are checked...</div>
                    </div>
                </div>

                <!-- Bottom controls -->
                <div class="hvcp-controls">
                    <button class="hvcp-cancel-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                            <circle cx="12" cy="12" r="10"/><path d="m15 9-6 6M9 9l6 6"/>
                        </svg>
                        Cancel Scan
                    </button>
                    <button class="hvcp-minimize-btn hvcp-minimize-bottom" title="Continue in background">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/>
                            <line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/>
                        </svg>
                        Minimize
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // PARTICLE ANIMATION
    // =========================================================================

    function initParticles() {
        const canvas = overlay?.querySelector('#hvcp-canvas');
        if (!canvas) return;

        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        canvasCtx = canvas.getContext('2d');

        particles.length = 0;
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                r: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.1,
                color: Math.random() > 0.5 ? '#D6A84A' : '#3b82f6'
            });
        }

        animateParticles();
    }

    function animateParticles() {
        if (!canvasCtx || !overlay) return;

        const canvas = canvasCtx.canvas;
        canvasCtx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    canvasCtx.beginPath();
                    canvasCtx.strokeStyle = `rgba(214, 168, 74, ${0.1 * (1 - dist / 120)})`;
                    canvasCtx.lineWidth = 0.5;
                    canvasCtx.moveTo(particles[i].x, particles[i].y);
                    canvasCtx.lineTo(particles[j].x, particles[j].y);
                    canvasCtx.stroke();
                }
            }
        }

        // Draw and move particles
        for (const p of particles) {
            canvasCtx.beginPath();
            canvasCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            canvasCtx.fillStyle = p.color.replace(')', `, ${p.opacity})`).replace('rgb', 'rgba').replace('#D6A84A', 'rgba(214,168,74').replace('#3b82f6', 'rgba(59,130,246');
            // Simplified fill with opacity
            canvasCtx.globalAlpha = p.opacity;
            canvasCtx.fillStyle = p.color;
            canvasCtx.fill();
            canvasCtx.globalAlpha = 1;

            p.x += p.vx;
            p.y += p.vy;

            // Bounce off edges
            if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        }

        particleAnimId = requestAnimationFrame(animateParticles);
    }

    // =========================================================================
    // UPDATE METHODS
    // =========================================================================

    /**
     * Called on each progress poll from HyperlinkValidatorState.
     * @param {Object} progress - { phase, overallProgress, urlsCompleted, urlsTotal, currentUrl, eta }
     * @param {Object} liveStats - Optional rich stats from backend { working, broken, blocked, ... }
     */
    function onProgress(progress, liveStats) {
        if (!state.active || !overlay) return;

        // Update phase
        if (progress.phase) {
            const newPhase = mapPhase(progress.phase);
            if (newPhase !== state.phase) {
                state.phase = newPhase;
                updatePhaseIndicator();
            }
        }

        // Update counts from progress
        state.completedUrls = progress.urlsCompleted || state.completedUrls;
        state.totalUrls = progress.urlsTotal || state.totalUrls;
        state.currentUrl = progress.currentUrl || state.currentUrl;

        // Update from live stats if available
        if (liveStats) {
            state.working = liveStats.working || 0;
            state.broken = liveStats.broken || 0;
            state.blocked = liveStats.blocked || 0;
            state.timeout = liveStats.timeout || 0;
            state.redirect = liveStats.redirect || 0;
            state.sslError = liveStats.ssl_error || 0;
            state.dnsFailed = liveStats.dns_failed || 0;

            if (liveStats.avg_response_ms) state.avgResponseMs = liveStats.avg_response_ms;
            if (liveStats.min_response_ms && liveStats.min_response_ms < Infinity) state.minResponseMs = liveStats.min_response_ms;
            if (liveStats.max_response_ms) state.maxResponseMs = liveStats.max_response_ms;
            if (liveStats.urls_per_second) state.urlsPerSecond = liveStats.urls_per_second;
            // v5.0.5: Track retest phase progress
            if (liveStats.retest_total) state.retestTotal = liveStats.retest_total;
            if (liveStats.retest_completed !== undefined) state.retestCompleted = liveStats.retest_completed;

            // Update domains
            if (liveStats.domains_checked) {
                for (const [domain, info] of Object.entries(liveStats.domains_checked)) {
                    if (!state.domains[domain]) {
                        state.domainOrder.push(domain);
                    }
                    state.domains[domain] = info;
                }
            }

            // Activity log
            if (liveStats.last_completed_url && liveStats.last_completed_status) {
                addActivityItem(liveStats.last_completed_url, liveStats.last_completed_status);
            }
        }

        // Calculate rate and ETA from our own tracking
        const elapsed = (Date.now() - state.startTime) / 1000;
        if (state.completedUrls > 0 && elapsed > 0) {
            state.urlsPerSecond = state.completedUrls / elapsed;
        }

        // Update all UI elements
        updateRing(progress.overallProgress || 0);
        updateStatusCards();
        updateProgressBar(progress.overallProgress || 0);
        updateTimingRow();
        updateDomainStrip();
        updateCountLabels();
    }

    /**
     * Set the phase to validating (called after extraction completes).
     */
    function setPhaseValidating(totalUrls, uniqueUrls) {
        state.phase = 'validating';
        state.totalUrls = totalUrls || state.totalUrls;
        state.uniqueUrls = uniqueUrls || state.uniqueUrls;
        updatePhaseIndicator();

        // Update total count label
        const totalEl = overlay?.querySelector('#hvcp-total-count');
        if (totalEl) totalEl.textContent = state.uniqueUrls || state.totalUrls;

        // Update ring label
        const ringLabel = overlay?.querySelector('#hvcp-ring-label');
        if (ringLabel) ringLabel.textContent = 'Validating...';
    }

    /**
     * Mark validation complete.
     */
    function complete(summary) {
        state.phase = 'complete';
        state.completedUrls = state.totalUrls;

        updatePhaseIndicator();
        updateRing(100);

        const ringLabel = overlay?.querySelector('#hvcp-ring-label');
        if (ringLabel) ringLabel.textContent = 'Complete!';

        const etaEl = overlay?.querySelector('#hvcp-eta');
        if (etaEl) etaEl.textContent = 'Done';

        // Final update of stat cards from summary
        if (summary) {
            state.working = summary.working || state.working;
            state.broken = summary.broken || state.broken;
            state.blocked = summary.blocked || state.blocked;
            state.timeout = summary.timeout || state.timeout;
            state.redirect = summary.redirect || state.redirect;
            updateStatusCards();
        }

        // Auto-dismiss after delay
        setTimeout(() => destroy(), 1500);
    }

    // =========================================================================
    // UI UPDATE HELPERS
    // =========================================================================

    function updatePhaseIndicator() {
        if (!overlay) return;

        const phases = ['extracting', 'validating', 'finalizing', 'complete'];
        const currentIdx = phases.indexOf(state.phase);

        overlay.querySelectorAll('.hvcp-phase').forEach(el => {
            const phase = el.dataset.phase;
            const idx = phases.indexOf(phase);
            el.classList.remove('hvcp-phase-active', 'hvcp-phase-done');
            if (idx < currentIdx || state.phase === 'complete') {
                el.classList.add('hvcp-phase-done');
            } else if (idx === currentIdx) {
                el.classList.add('hvcp-phase-active');
            }
        });

        // Update phase lines
        overlay.querySelectorAll('.hvcp-phase-line').forEach((line, i) => {
            line.classList.toggle('hvcp-phase-line-done', i < currentIdx || state.phase === 'complete');
        });
    }

    function updateRing(pct) {
        const ringFill = overlay?.querySelector('#hvcp-ring-fill');
        const ringPct = overlay?.querySelector('#hvcp-ring-pct');
        if (!ringFill || !ringPct) return;

        const circumference = 2 * Math.PI * 85; // r=85
        const offset = circumference - (pct / 100) * circumference;
        ringFill.style.strokeDashoffset = offset;

        ringPct.textContent = `${Math.round(pct)}%`;
    }

    function updateStatusCards() {
        setCounter('hvcp-working', state.working);
        setCounter('hvcp-broken', state.broken);
        setCounter('hvcp-blocked', state.blocked);
        setCounter('hvcp-other', state.timeout + state.redirect + state.sslError + state.dnsFailed);
    }

    function setCounter(id, value) {
        const el = overlay?.querySelector(`#${id}`);
        if (!el) return;
        const current = parseInt(el.textContent) || 0;
        if (current !== value) {
            el.textContent = value;
            // Only animate if there's a meaningful jump (not every +1 during rapid polling)
            if (!el._bumpTimeout) {
                el.classList.add('hvcp-counter-bump');
                el._bumpTimeout = setTimeout(() => {
                    el.classList.remove('hvcp-counter-bump');
                    el._bumpTimeout = null;
                }, 350);
            }
        }
    }

    function updateProgressBar(pct) {
        const fill = overlay?.querySelector('#hvcp-progress-fill');
        if (fill) fill.style.width = `${pct}%`;

        // Update colored segments to show status breakdown
        const segEl = overlay?.querySelector('#hvcp-progress-segments');
        if (segEl && state.completedUrls > 0) {
            const total = state.completedUrls;
            const w = (state.working / total * 100).toFixed(1);
            const b = (state.broken / total * 100).toFixed(1);
            const bl = (state.blocked / total * 100).toFixed(1);
            const o = (100 - parseFloat(w) - parseFloat(b) - parseFloat(bl)).toFixed(1);

            segEl.style.background = `linear-gradient(90deg,
                #22c55e 0%, #22c55e ${w}%,
                #ef4444 ${w}%, #ef4444 ${parseFloat(w) + parseFloat(b)}%,
                #8b5cf6 ${parseFloat(w) + parseFloat(b)}%, #8b5cf6 ${parseFloat(w) + parseFloat(b) + parseFloat(bl)}%,
                #6b7280 ${parseFloat(w) + parseFloat(b) + parseFloat(bl)}%, #6b7280 100%
            )`;
            segEl.style.width = `${pct}%`;
            segEl.style.opacity = '0.3';
        }
    }

    function updateCountLabels() {
        setText('#hvcp-completed-count', state.completedUrls);
        if (state.totalUrls > 0) setText('#hvcp-total-count', state.uniqueUrls || state.totalUrls);
        setText('#hvcp-rate', state.urlsPerSecond > 0 ? state.urlsPerSecond.toFixed(1) : '—');
    }

    /** Set text only if it actually changed — prevents unnecessary repaints */
    function setText(selector, value) {
        const el = overlay?.querySelector(selector);
        if (!el) return;
        const str = String(value);
        if (el.textContent !== str) el.textContent = str;
    }

    function updateTimingRow() {
        const elapsed = (Date.now() - state.startTime) / 1000;

        // Elapsed
        setText('#hvcp-elapsed', formatDuration(elapsed));

        // Avg response
        setText('#hvcp-avg-response', state.avgResponseMs > 0 ? `${Math.round(state.avgResponseMs)}ms` : '—');

        // ETA calculation
        if (state.completedUrls > 5 && state.totalUrls > 0) {
            const total = state.uniqueUrls || state.totalUrls;
            const remaining = total - state.completedUrls;
            // v5.0.5: Show retest progress instead of "Almost done" when in retesting phase
            if (remaining <= 0 && state.retestTotal > 0 && state.retestCompleted < state.retestTotal) {
                const retestRemaining = state.retestTotal - state.retestCompleted;
                setText('#hvcp-eta', `Re-testing ${retestRemaining} of ${state.retestTotal} failed links...`);
            } else if (remaining <= 0) {
                setText('#hvcp-eta', 'Finalizing...');
            } else {
                const rate = state.completedUrls / elapsed;
                const etaSeconds = remaining / rate;

                // Smooth ETA with exponential moving average
                state.etaHistory.push(etaSeconds);
                if (state.etaHistory.length > 5) state.etaHistory.shift();
                const smoothedEta = state.etaHistory.reduce((a, b) => a + b, 0) / state.etaHistory.length;

                setText('#hvcp-eta', formatDuration(smoothedEta));
            }
        }

        // Domain count
        const count = state.domainOrder.length;
        setText('#hvcp-domain-count', `${count} domain${count !== 1 ? 's' : ''}`);
    }

    function addActivityItem(url, status) {
        // Deduplicate consecutive same-url entries
        if (state.activityLog.length > 0 && state.activityLog[0].url === url) return;

        state.activityLog.unshift({ url, status, time: Date.now() });
        if (state.activityLog.length > 8) state.activityLog.pop();

        renderActivityFeed();
    }

    function renderActivityFeed() {
        const feedEl = overlay?.querySelector('#hvcp-activity-feed');
        if (!feedEl) return;
        if (state.activityLog.length === 0) return;

        // Remove the empty placeholder if present
        const emptyEl = feedEl.querySelector('.hvcp-activity-empty');
        if (emptyEl) emptyEl.remove();

        // Incremental DOM update — only prepend new items and remove excess
        const existingItems = feedEl.querySelectorAll('.hvcp-activity-item');
        const existingUrls = Array.from(existingItems).map(el => el.getAttribute('data-url'));

        // Check if the newest item is already rendered
        const newest = state.activityLog[0];
        if (newest && existingUrls[0] === newest.url) {
            // Just update opacity on existing items
            existingItems.forEach((el, i) => {
                el.style.opacity = Math.max(0.4, 1 - (i * 0.1));
            });
            return;
        }

        // Prepend new item(s) at the top
        const newItems = [];
        for (const item of state.activityLog) {
            if (existingUrls.includes(item.url)) break;
            newItems.push(item);
        }

        // Create new DOM nodes and prepend
        for (let i = newItems.length - 1; i >= 0; i--) {
            const item = newItems[i];
            const statusClass = getStatusClass(item.status);
            const displayUrl = truncateUrl(item.url, 60);

            const div = document.createElement('div');
            div.className = 'hvcp-activity-item hvcp-item-enter';
            div.setAttribute('data-url', item.url);
            div.innerHTML = `
                <span class="hvcp-activity-status hvcp-act-${statusClass}">${getStatusIcon(item.status)}</span>
                <span class="hvcp-activity-url" title="${escapeHtml(item.url)}">${escapeHtml(displayUrl)}</span>
            `;
            feedEl.insertBefore(div, feedEl.firstChild);
        }

        // Trim excess items (keep max 8)
        const allItems = feedEl.querySelectorAll('.hvcp-activity-item');
        for (let i = 8; i < allItems.length; i++) {
            allItems[i].style.opacity = '0';
            allItems[i].style.transform = 'translateY(4px)';
            // Remove after transition
            setTimeout(() => allItems[i]?.remove(), 400);
        }

        // Update opacity on all visible items
        const visibleItems = feedEl.querySelectorAll('.hvcp-activity-item');
        visibleItems.forEach((el, i) => {
            if (i < 8) el.style.opacity = Math.max(0.4, 1 - (i * 0.1));
        });
    }

    function updateDomainStrip() {
        const stripEl = overlay?.querySelector('#hvcp-domains-strip');
        if (!stripEl || state.domainOrder.length === 0) return;

        // Remove empty placeholder
        const emptyEl = stripEl.querySelector('.hvcp-domains-empty');
        if (emptyEl) emptyEl.remove();

        // Show top 12 domains by total count
        const sorted = [...state.domainOrder]
            .filter(d => state.domains[d])
            .sort((a, b) => (state.domains[b]?.total || 0) - (state.domains[a]?.total || 0))
            .slice(0, 12);

        const existingPills = stripEl.querySelectorAll('.hvcp-domain-pill');
        const existingMap = {};
        existingPills.forEach(pill => {
            const domain = pill.getAttribute('data-domain');
            if (domain) existingMap[domain] = pill;
        });

        // Track which domains should be in the strip
        const targetSet = new Set(sorted);

        // Update existing or create new pills
        sorted.forEach(domain => {
            const info = state.domains[domain];
            const w = info.working || 0;
            const b = (info.broken || 0) + (info.blocked || 0);
            const t = info.total || 1;
            const healthPct = (w / t * 100).toFixed(0);
            const healthClass = healthPct >= 80 ? 'healthy' : healthPct >= 50 ? 'mixed' : 'unhealthy';

            if (existingMap[domain]) {
                // Update in place — no flicker
                const pill = existingMap[domain];
                const healthEl = pill.querySelector('.hvcp-domain-health');
                const barFill = pill.querySelector('.hvcp-domain-bar-fill');
                if (healthEl) healthEl.textContent = `${w}/${t}`;
                if (barFill) barFill.style.width = `${healthPct}%`;

                // Update health class smoothly
                pill.classList.remove('hvcp-domain-healthy', 'hvcp-domain-mixed', 'hvcp-domain-unhealthy');
                pill.classList.add(`hvcp-domain-${healthClass}`);
                pill.title = `${domain}: ${w}/${t} working`;
            } else {
                // Create new pill with entrance animation
                const pill = document.createElement('div');
                pill.className = `hvcp-domain-pill hvcp-domain-${healthClass} hvcp-pill-new`;
                pill.setAttribute('data-domain', domain);
                pill.title = `${domain}: ${w}/${t} working`;
                pill.innerHTML = `
                    <span class="hvcp-domain-name">${escapeHtml(truncateDomain(domain))}</span>
                    <span class="hvcp-domain-health">${w}/${t}</span>
                    <div class="hvcp-domain-bar">
                        <div class="hvcp-domain-bar-fill" style="width:${healthPct}%"></div>
                    </div>
                `;
                stripEl.appendChild(pill);
                // Remove animation class after it plays
                setTimeout(() => pill.classList.remove('hvcp-pill-new'), 450);
            }
        });

        // Remove pills that are no longer in top 12
        existingPills.forEach(pill => {
            const domain = pill.getAttribute('data-domain');
            if (domain && !targetSet.has(domain)) {
                pill.style.opacity = '0';
                pill.style.transform = 'scale(0.85)';
                setTimeout(() => pill.remove(), 350);
            }
        });
    }

    // =========================================================================
    // COUNTER LOOP (runs every second for elapsed timer)
    // =========================================================================

    let counterInterval = null;

    function startCounterLoop() {
        counterInterval = setInterval(() => {
            if (!state.active || !overlay) {
                clearInterval(counterInterval);
                return;
            }
            updateTimingRow();
        }, 1000);
    }

    // =========================================================================
    // MINIMIZE / RESTORE
    // =========================================================================

    function minimize() {
        if (!overlay) return;
        overlay.classList.add('hvcp-minimized');

        // Create a floating mini badge
        let badge = document.getElementById('hvcp-mini-badge');
        if (!badge) {
            badge = document.createElement('div');
            badge.className = 'hvcp-mini-badge';
            badge.id = 'hvcp-mini-badge';
            badge.innerHTML = `
                <div class="hvcp-mini-ring">
                    <svg viewBox="0 0 36 36">
                        <circle class="hvcp-mini-ring-bg" cx="18" cy="18" r="15.9"/>
                        <circle class="hvcp-mini-ring-fill" cx="18" cy="18" r="15.9" id="hvcp-mini-ring-fill"/>
                    </svg>
                </div>
                <div class="hvcp-mini-info">
                    <span class="hvcp-mini-pct" id="hvcp-mini-pct">0%</span>
                    <span class="hvcp-mini-text">Scanning Links</span>
                </div>
            `;
            badge.addEventListener('click', restore);
            document.body.appendChild(badge);

            requestAnimationFrame(() => badge.classList.add('hvcp-mini-badge-visible'));
        }

        // Start mini badge update loop
        startMiniBadgeLoop();
    }

    let miniBadgeInterval = null;

    function startMiniBadgeLoop() {
        if (miniBadgeInterval) clearInterval(miniBadgeInterval);
        miniBadgeInterval = setInterval(() => {
            if (!state.active) {
                clearInterval(miniBadgeInterval);
                const badge = document.getElementById('hvcp-mini-badge');
                if (badge) badge.remove();
                return;
            }
            updateMiniBadge();
        }, 1000);
    }

    function updateMiniBadge() {
        const pctEl = document.getElementById('hvcp-mini-pct');
        const ringFill = document.getElementById('hvcp-mini-ring-fill');
        if (!pctEl || !ringFill) return;

        const pct = state.totalUrls > 0
            ? Math.round((state.completedUrls / (state.uniqueUrls || state.totalUrls)) * 100)
            : 0;

        pctEl.textContent = `${pct}%`;

        const circumference = 2 * Math.PI * 15.9;
        ringFill.style.strokeDasharray = `${circumference}`;
        ringFill.style.strokeDashoffset = `${circumference - (pct / 100) * circumference}`;
    }

    function restore() {
        if (!overlay) return;
        overlay.classList.remove('hvcp-minimized');

        const badge = document.getElementById('hvcp-mini-badge');
        if (badge) badge.remove();

        if (miniBadgeInterval) {
            clearInterval(miniBadgeInterval);
            miniBadgeInterval = null;
        }
    }

    // =========================================================================
    // DESTROY
    // =========================================================================

    function destroy() {
        state.active = false;

        if (particleAnimId) {
            cancelAnimationFrame(particleAnimId);
            particleAnimId = null;
        }

        if (counterInterval) {
            clearInterval(counterInterval);
            counterInterval = null;
        }

        if (miniBadgeInterval) {
            clearInterval(miniBadgeInterval);
            miniBadgeInterval = null;
        }

        const badge = document.getElementById('hvcp-mini-badge');
        if (badge) badge.remove();

        if (overlay) {
            overlay.classList.remove('hvcp-visible');
            setTimeout(() => {
                overlay?.remove();
                overlay = null;
                canvasCtx = null;
            }, 400);
        }
    }

    function isActive() {
        return state.active;
    }

    // =========================================================================
    // UTILITIES
    // =========================================================================

    function mapPhase(backendPhase) {
        const lower = (backendPhase || '').toLowerCase();
        if (lower === 'complete' || lower === 'finalizing') return 'finalizing';
        if (lower === 'retesting') return 'validating'; // v5.0.5: retest maps to validating phase visually
        if (lower === 'checking' || lower === 'running' || lower === 'validating') return 'validating';
        if (lower === 'extracting' || lower === 'starting') return 'extracting';
        return state.phase; // keep current
    }

    function formatDuration(seconds) {
        if (seconds < 2) return 'wrapping up';
        if (seconds < 60) return `${Math.round(seconds)}s`;
        const mins = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        return `${mins}m ${secs}s`;
    }

    function getStatusClass(status) {
        const s = (status || '').toUpperCase();
        if (s === 'WORKING') return 'working';
        if (s === 'BROKEN' || s === 'INVALID') return 'broken';
        if (s === 'BLOCKED') return 'blocked';
        if (s === 'TIMEOUT') return 'timeout';
        if (s === 'REDIRECT') return 'redirect';
        return 'other';
    }

    function getStatusIcon(status) {
        const s = (status || '').toUpperCase();
        if (s === 'WORKING') return '✓';
        if (s === 'BROKEN' || s === 'INVALID') return '✗';
        if (s === 'BLOCKED') return '⊘';
        if (s === 'TIMEOUT') return '⏱';
        if (s === 'REDIRECT') return '→';
        return '?';
    }

    function truncateUrl(url, maxLen) {
        if (!url || url.length <= maxLen) return url;
        try {
            const parsed = new URL(url);
            const host = parsed.hostname;
            const path = parsed.pathname;
            if (host.length + path.length <= maxLen) return host + path;
            return host + path.substring(0, maxLen - host.length - 3) + '...';
        } catch {
            return url.substring(0, maxLen - 3) + '...';
        }
    }

    function truncateDomain(domain) {
        if (domain.length <= 20) return domain;
        // Remove common prefixes
        let d = domain.replace(/^www\./, '').replace(/^oursites\./, '');
        if (d.length <= 20) return d;
        return d.substring(0, 17) + '...';
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================

    return {
        show,
        onProgress,
        setPhaseValidating,
        complete,
        minimize,
        restore,
        destroy,
        isActive,
        addActivityItem
    };
})();