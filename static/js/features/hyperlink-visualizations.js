/**
 * Hyperlink Validator - Enhanced Visualizations
 * ==============================================
 * Advanced visual components for the hyperlink validator.
 * Version: 3.0.125
 */

window.HyperlinkVisualization = (function() {
    'use strict';

    // ==========================================================================
    // CONFIGURATION
    // ==========================================================================

    const CONFIG = {
        colors: {
            working: '#22c55e',
            broken: '#ef4444',
            redirect: '#3b82f6',
            timeout: '#f59e0b',
            blocked: '#8b5cf6',
            unknown: '#6b7280',
            dnsFailed: '#f97316',
            sslError: '#ec4899'
        },
        animation: {
            duration: 600,
            easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
        },
        histogram: {
            buckets: 20,
            maxBarHeight: 100
        }
    };

    // ==========================================================================
    // DONUT CHART
    // ==========================================================================

    /**
     * Create an animated donut chart showing status distribution.
     * @param {HTMLElement} container - The container element
     * @param {Object} data - Status counts {working: n, broken: n, ...}
     */
    function createDonutChart(container, data) {
        const total = Object.values(data).reduce((sum, val) => sum + val, 0);
        if (total === 0) {
            container.innerHTML = '<div class="hv-empty-chart">No data</div>';
            return;
        }

        const size = 180;
        const strokeWidth = 24;
        const radius = (size - strokeWidth) / 2;
        const circumference = 2 * Math.PI * radius;
        const centerX = size / 2;
        const centerY = size / 2;

        // Calculate percentages and create segments
        const segments = [];
        let offset = 0;

        const statusOrder = ['working', 'broken', 'redirect', 'timeout', 'blocked', 'unknown'];

        statusOrder.forEach(status => {
            const count = data[status] || 0;
            if (count > 0) {
                const percentage = count / total;
                const length = percentage * circumference;
                segments.push({
                    status,
                    count,
                    percentage,
                    offset,
                    length,
                    color: CONFIG.colors[status]
                });
                offset += length;
            }
        });

        // Create SVG
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'hv-donut-svg');
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);

        // Add segments with animation
        segments.forEach((seg, idx) => {
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('class', 'hv-donut-segment');
            circle.setAttribute('cx', centerX);
            circle.setAttribute('cy', centerY);
            circle.setAttribute('r', radius);
            circle.setAttribute('stroke', seg.color);
            circle.setAttribute('stroke-dasharray', `0 ${circumference}`);
            circle.setAttribute('stroke-dashoffset', -seg.offset);

            // Animate on load
            requestAnimationFrame(() => {
                setTimeout(() => {
                    circle.style.transition = `stroke-dasharray ${CONFIG.animation.duration}ms ${CONFIG.animation.easing}`;
                    circle.setAttribute('stroke-dasharray', `${seg.length} ${circumference - seg.length}`);
                }, idx * 100);
            });

            svg.appendChild(circle);
        });

        // Calculate success rate for center display
        const successRate = Math.round((data.working || 0) / total * 100);

        container.innerHTML = `
            <div class="hv-donut-container">
                ${svg.outerHTML}
                <div class="hv-donut-center">
                    <div class="hv-donut-center-value">${successRate}%</div>
                    <div class="hv-donut-center-label">Success</div>
                </div>
            </div>
            <div class="hv-chart-legend">
                ${segments.map(seg => `
                    <div class="hv-legend-item">
                        <span class="hv-legend-dot" style="background: ${seg.color}"></span>
                        <span>${seg.status}: ${seg.count}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // ==========================================================================
    // RESPONSE TIME HISTOGRAM
    // ==========================================================================

    /**
     * Create a histogram of response times.
     * @param {HTMLElement} container - The container element
     * @param {Array} results - Array of validation results with response_time_ms
     */
    function createResponseHistogram(container, results) {
        // Extract response times (only successful requests)
        const times = results
            .filter(r => r.response_time_ms && r.response_time_ms > 0)
            .map(r => r.response_time_ms);

        if (times.length === 0) {
            container.innerHTML = '<div class="hv-empty-chart">No response time data</div>';
            return;
        }

        // Calculate statistics
        const min = Math.min(...times);
        const max = Math.max(...times);
        const avg = times.reduce((a, b) => a + b, 0) / times.length;
        const range = max - min || 1;

        // Create buckets
        const numBuckets = CONFIG.histogram.buckets;
        const bucketSize = range / numBuckets;
        const buckets = new Array(numBuckets).fill(0);

        times.forEach(t => {
            const bucketIdx = Math.min(Math.floor((t - min) / bucketSize), numBuckets - 1);
            buckets[bucketIdx]++;
        });

        const maxCount = Math.max(...buckets);

        // Create histogram bars
        const barsHtml = buckets.map((count, idx) => {
            const height = maxCount > 0 ? (count / maxCount) * CONFIG.histogram.maxBarHeight : 0;
            const rangeStart = Math.round(min + idx * bucketSize);
            const rangeEnd = Math.round(min + (idx + 1) * bucketSize);
            const tooltip = `${rangeStart}-${rangeEnd}ms: ${count} URLs`;

            // Color based on speed
            let color;
            if (rangeEnd < 500) color = CONFIG.colors.working;
            else if (rangeEnd < 1500) color = CONFIG.colors.redirect;
            else if (rangeEnd < 3000) color = CONFIG.colors.timeout;
            else color = CONFIG.colors.broken;

            return `<div class="hv-histogram-bar"
                        style="height: ${height}px; background: ${color};"
                        data-tooltip="${tooltip}"></div>`;
        }).join('');

        container.innerHTML = `
            <div class="hv-histogram-header">
                <span class="hv-chart-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 20V10M18 20V4M6 20v-4"/>
                    </svg>
                    Response Times
                </span>
                <div class="hv-histogram-stats">
                    <span>Avg: <strong>${Math.round(avg)}ms</strong></span>
                    <span>Min: ${Math.round(min)}ms</span>
                    <span>Max: ${Math.round(max)}ms</span>
                </div>
            </div>
            <div class="hv-histogram-container">
                ${barsHtml}
            </div>
            <div class="hv-histogram-labels">
                <span>${Math.round(min)}ms</span>
                <span>${Math.round((min + max) / 2)}ms</span>
                <span>${Math.round(max)}ms</span>
            </div>
        `;
    }

    // ==========================================================================
    // 3D DOMAIN HEALTH CAROUSEL
    // ==========================================================================

    /**
     * Create an interactive 3D carousel showing domain health.
     * Each card represents a domain with health-based coloring and glow effects.
     * Features: infinite loop, filterable legend, spread out cards, no auto-rotate.
     * @param {HTMLElement} container - The container element
     * @param {Array} results - Array of validation results
     */
    function createDomainHealthCarousel(container, results) {
        // Group by domain
        const domainStats = {};

        results.forEach(r => {
            let domain = 'unknown';
            try {
                domain = new URL(r.url).hostname;
            } catch {
                return;
            }

            if (!domainStats[domain]) {
                domainStats[domain] = {
                    total: 0,
                    working: 0,
                    broken: 0,
                    redirect: 0,
                    timeout: 0,
                    times: []
                };
            }

            domainStats[domain].total++;

            const status = (r.status || '').toLowerCase();
            if (status === 'working') {
                domainStats[domain].working++;
            } else if (status === 'broken') {
                domainStats[domain].broken++;
            } else if (status === 'redirect') {
                domainStats[domain].redirect++;
            } else if (status === 'timeout') {
                domainStats[domain].timeout++;
            }

            if (r.response_time_ms) {
                domainStats[domain].times.push(r.response_time_ms);
            }
        });

        // Calculate health scores and sort by total URLs
        const allDomains = Object.entries(domainStats)
            .map(([domain, stats]) => {
                const healthScore = stats.total > 0 ? stats.working / stats.total : 0;
                const avgTime = stats.times.length > 0
                    ? stats.times.reduce((a, b) => a + b, 0) / stats.times.length
                    : 0;

                let healthClass, healthLabel, healthGlow, healthCategory;
                if (healthScore >= 0.95) {
                    healthClass = 'carousel-health-excellent';
                    healthLabel = 'Excellent';
                    healthGlow = 'rgba(34, 197, 94, 0.5)';
                    healthCategory = 'excellent';
                } else if (healthScore >= 0.8) {
                    healthClass = 'carousel-health-good';
                    healthLabel = 'Good';
                    healthGlow = 'rgba(132, 204, 22, 0.5)';
                    healthCategory = 'good';
                } else if (healthScore >= 0.5) {
                    healthClass = 'carousel-health-warning';
                    healthLabel = 'Warning';
                    healthGlow = 'rgba(245, 158, 11, 0.5)';
                    healthCategory = 'warning';
                } else {
                    healthClass = 'carousel-health-critical';
                    healthLabel = 'Critical';
                    healthGlow = 'rgba(239, 68, 68, 0.5)';
                    healthCategory = 'critical';
                }

                return {
                    domain,
                    total: stats.total,
                    working: stats.working,
                    broken: stats.broken,
                    healthScore,
                    healthPercent: Math.round(healthScore * 100),
                    avgTime: Math.round(avgTime),
                    healthClass,
                    healthLabel,
                    healthGlow,
                    healthCategory
                };
            })
            .sort((a, b) => b.total - a.total)
            .slice(0, 20); // Show top 20 domains in carousel

        if (allDomains.length === 0) {
            container.innerHTML = '<div class="hv-empty-chart">No domain data</div>';
            return;
        }

        // Count domains by category for legend badges
        const categoryCounts = {
            excellent: allDomains.filter(d => d.healthCategory === 'excellent').length,
            good: allDomains.filter(d => d.healthCategory === 'good').length,
            warning: allDomains.filter(d => d.healthCategory === 'warning').length,
            critical: allDomains.filter(d => d.healthCategory === 'critical').length
        };

        // Generate unique ID for this carousel instance
        const carouselId = 'hv-domain-carousel-' + Date.now();

        // Track active filter
        let activeHealthFilter = null;
        let filteredDomains = [...allDomains];

        // Create the carousel HTML
        function renderCarousel() {
            container.innerHTML = `
                <div class="hv-domain-carousel-wrapper">
                    <div class="hv-carousel-header">
                        <div class="hv-carousel-title">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="2" y1="12" x2="22" y2="12"/>
                                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                            </svg>
                            <span>Domain Health</span>
                            <span class="hv-carousel-count">${filteredDomains.length} domains</span>
                        </div>
                        <div class="hv-carousel-filter-indicator" id="${carouselId}-filter" style="display: none;">
                            <span class="hv-carousel-filter-text"></span>
                            <button class="hv-carousel-filter-clear" title="Clear filter">✕</button>
                        </div>
                    </div>
                    <div class="hv-domain-carousel" id="${carouselId}">
                        <div class="hv-carousel-scene">
                            <div class="hv-carousel-track" id="${carouselId}-track">
                                ${filteredDomains.map((d, idx) => `
                                    <div class="hv-carousel-card ${d.healthClass}"
                                         data-domain="${d.domain}"
                                         data-index="${idx}"
                                         data-category="${d.healthCategory}"
                                         style="--card-glow: ${d.healthGlow}; --card-index: ${idx};">
                                        <div class="hv-card-inner">
                                            <div class="hv-card-front">
                                                <div class="hv-card-health-ring">
                                                    <svg viewBox="0 0 36 36" class="hv-health-circle">
                                                        <path class="hv-health-bg"
                                                            d="M18 2.0845
                                                               a 15.9155 15.9155 0 0 1 0 31.831
                                                               a 15.9155 15.9155 0 0 1 0 -31.831"/>
                                                        <path class="hv-health-fill"
                                                            stroke-dasharray="${d.healthPercent}, 100"
                                                            d="M18 2.0845
                                                               a 15.9155 15.9155 0 0 1 0 31.831
                                                               a 15.9155 15.9155 0 0 1 0 -31.831"/>
                                                    </svg>
                                                    <div class="hv-health-percent">${d.healthPercent}%</div>
                                                </div>
                                                <div class="hv-card-domain">${truncateDomain(d.domain, 12)}</div>
                                                <div class="hv-card-stats">
                                                    <span class="hv-card-stat-ok">${d.working}</span>
                                                    <span class="hv-card-stat-divider">/</span>
                                                    <span class="hv-card-stat-total">${d.total}</span>
                                                </div>
                                                <div class="hv-card-label">${d.healthLabel}</div>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                    <div class="hv-carousel-controls">
                        <button class="hv-carousel-nav hv-carousel-prev" id="${carouselId}-prev">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="15 18 9 12 15 6"/>
                            </svg>
                        </button>
                        <div class="hv-carousel-dots" id="${carouselId}-dots">
                            ${filteredDomains.map((_, idx) => `
                                <button class="hv-carousel-dot ${idx === 0 ? 'active' : ''}" data-index="${idx}"></button>
                            `).join('')}
                        </div>
                        <button class="hv-carousel-nav hv-carousel-next" id="${carouselId}-next">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="9 18 15 12 9 6"/>
                            </svg>
                        </button>
                    </div>
                    <div class="hv-carousel-legend" id="${carouselId}-legend">
                        <button class="hv-legend-btn ${activeHealthFilter === null ? 'active' : ''}" data-filter="all">
                            <span class="hv-legend-dot" style="background: linear-gradient(135deg, #22c55e, #ef4444);"></span>
                            All <span class="hv-legend-count">${allDomains.length}</span>
                        </button>
                        <button class="hv-legend-btn ${activeHealthFilter === 'excellent' ? 'active' : ''}" data-filter="excellent" ${categoryCounts.excellent === 0 ? 'disabled' : ''}>
                            <span class="hv-legend-dot" style="background: #22c55e;"></span>
                            Excellent <span class="hv-legend-count">${categoryCounts.excellent}</span>
                        </button>
                        <button class="hv-legend-btn ${activeHealthFilter === 'good' ? 'active' : ''}" data-filter="good" ${categoryCounts.good === 0 ? 'disabled' : ''}>
                            <span class="hv-legend-dot" style="background: #84cc16;"></span>
                            Good <span class="hv-legend-count">${categoryCounts.good}</span>
                        </button>
                        <button class="hv-legend-btn ${activeHealthFilter === 'warning' ? 'active' : ''}" data-filter="warning" ${categoryCounts.warning === 0 ? 'disabled' : ''}>
                            <span class="hv-legend-dot" style="background: #f59e0b;"></span>
                            Warning <span class="hv-legend-count">${categoryCounts.warning}</span>
                        </button>
                        <button class="hv-legend-btn ${activeHealthFilter === 'critical' ? 'active' : ''}" data-filter="critical" ${categoryCounts.critical === 0 ? 'disabled' : ''}>
                            <span class="hv-legend-dot" style="background: #ef4444;"></span>
                            Critical <span class="hv-legend-count">${categoryCounts.critical}</span>
                        </button>
                    </div>
                </div>
            `;
        }

        // Initial render
        renderCarousel();

        // Initialize carousel state
        let currentIndex = 0;

        function initCarouselBehavior() {
            const totalCards = filteredDomains.length;
            const dots = document.querySelectorAll(`#${carouselId}-dots .hv-carousel-dot`);
            const cards = document.querySelectorAll(`#${carouselId}-track .hv-carousel-card`);
            const carousel = document.getElementById(carouselId);

            if (totalCards === 0) return;

            // Position cards in 3D space - more spread out with infinite loop feel
            function updateCarousel(animated = true) {
                cards.forEach((card, idx) => {
                    // Calculate offset with wrapping for infinite feel
                    let offset = idx - currentIndex;

                    // Wrap around for infinite loop effect
                    if (totalCards > 3) {
                        if (offset > totalCards / 2) offset -= totalCards;
                        if (offset < -totalCards / 2) offset += totalCards;
                    }

                    const absOffset = Math.abs(offset);

                    // Calculate 3D transformations - MORE SPREAD OUT
                    let translateX, translateZ, rotateY, opacity, scale;

                    if (absOffset === 0) {
                        // Center card
                        translateX = 0;
                        translateZ = 60;
                        rotateY = 0;
                        opacity = 1;
                        scale = 1.15;
                    } else if (absOffset <= 3) {
                        // Visible side cards - more spread out (140px instead of 100px)
                        translateX = offset * 140;
                        translateZ = -40 * absOffset;
                        rotateY = offset * -20;
                        opacity = 1 - (absOffset * 0.2);
                        scale = 1 - (absOffset * 0.12);
                    } else {
                        // Hidden cards
                        translateX = offset * 140;
                        translateZ = -150;
                        rotateY = offset * -25;
                        opacity = 0;
                        scale = 0.6;
                    }

                    card.style.transition = animated ? 'all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : 'none';
                    card.style.transform = `translateX(${translateX}px) translateZ(${translateZ}px) rotateY(${rotateY}deg) scale(${scale})`;
                    card.style.opacity = opacity;
                    card.style.zIndex = 10 - absOffset;
                    card.classList.toggle('active', absOffset === 0);
                });

                // Update dots
                dots.forEach((dot, idx) => {
                    dot.classList.toggle('active', idx === currentIndex);
                });
            }

            // Navigation functions with infinite loop
            function goToCard(index) {
                if (totalCards === 0) return;
                // Wrap around for infinite loop
                if (index < 0) {
                    currentIndex = totalCards - 1;
                } else if (index >= totalCards) {
                    currentIndex = 0;
                } else {
                    currentIndex = index;
                }
                updateCarousel();
            }

            function nextCard() {
                goToCard(currentIndex + 1);
            }

            function prevCard() {
                goToCard(currentIndex - 1);
            }

            // Event listeners
            document.getElementById(`${carouselId}-next`)?.addEventListener('click', nextCard);
            document.getElementById(`${carouselId}-prev`)?.addEventListener('click', prevCard);

            dots.forEach(dot => {
                dot.addEventListener('click', () => {
                    goToCard(parseInt(dot.dataset.index));
                });
            });

            // Card click to filter
            cards.forEach(card => {
                card.addEventListener('click', () => {
                    const domain = card.dataset.domain;
                    const idx = parseInt(card.dataset.index);

                    if (idx === currentIndex) {
                        // Click on center card filters
                        filterByDomain(domain);

                        // Show filter indicator
                        const filterEl = document.getElementById(`${carouselId}-filter`);
                        if (filterEl) {
                            filterEl.style.display = 'inline-flex';
                            filterEl.querySelector('.hv-carousel-filter-text').textContent = `Filtered: ${truncateDomain(domain, 15)}`;
                        }

                        // Highlight active card
                        cards.forEach(c => c.classList.remove('hv-card-filtered'));
                        card.classList.add('hv-card-filtered');

                        updateFilterIndicator(domain);
                    } else {
                        // Click on side card navigates
                        goToCard(idx);
                    }
                });
            });

            // Clear filter button
            const clearBtn = document.querySelector(`#${carouselId}-filter .hv-carousel-filter-clear`);
            if (clearBtn) {
                clearBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    clearDomainFilter();

                    const filterEl = document.getElementById(`${carouselId}-filter`);
                    if (filterEl) {
                        filterEl.style.display = 'none';
                    }

                    cards.forEach(c => c.classList.remove('hv-card-filtered'));
                });
            }

            // Keyboard navigation - add tabindex so carousel can receive focus
            if (carousel) {
                carousel.setAttribute('tabindex', '0');
                carousel.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowLeft') { e.preventDefault(); prevCard(); }
                    if (e.key === 'ArrowRight') { e.preventDefault(); nextCard(); }
                });
            }

            // Touch/drag support
            let startX = 0;
            let isDragging = false;

            carousel?.addEventListener('mousedown', (e) => {
                startX = e.clientX;
                isDragging = true;
                carousel.style.cursor = 'grabbing';
            });

            carousel?.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                const diff = e.clientX - startX;
                if (Math.abs(diff) > 50) {
                    if (diff > 0) prevCard();
                    else nextCard();
                    isDragging = false;
                    startX = e.clientX; // Reset for continuous drag
                    carousel.style.cursor = 'grab';
                }
            });

            carousel?.addEventListener('mouseup', () => {
                isDragging = false;
                carousel.style.cursor = 'grab';
            });

            carousel?.addEventListener('mouseleave', () => {
                isDragging = false;
                carousel.style.cursor = 'grab';
            });

            // Touch events
            // BUG-L10 FIX: Added { passive: true } to prevent scroll-blocking violations
            carousel?.addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
            }, { passive: true });

            carousel?.addEventListener('touchend', (e) => {
                const diff = e.changedTouches[0].clientX - startX;
                if (Math.abs(diff) > 50) {
                    if (diff > 0) prevCard();
                    else nextCard();
                }
            }, { passive: true });

            // Initial positioning
            updateCarousel(false);
        }

        // Legend filter click handlers
        function initLegendFilters() {
            const legendBtns = document.querySelectorAll(`#${carouselId}-legend .hv-legend-btn`);

            legendBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const filter = btn.dataset.filter;

                    if (filter === 'all') {
                        activeHealthFilter = null;
                        filteredDomains = [...allDomains];
                    } else {
                        activeHealthFilter = filter;
                        filteredDomains = allDomains.filter(d => d.healthCategory === filter);
                    }

                    // Reset to first card
                    currentIndex = 0;

                    // Re-render and reinit
                    renderCarousel();
                    initCarouselBehavior();
                    initLegendFilters();
                });
            });
        }

        // Initialize behaviors
        initCarouselBehavior();
        initLegendFilters();
    }

    // ==========================================================================
    // DOMAIN HEALTH HEATMAP
    // ==========================================================================

    /**
     * Create a domain health heatmap.
     * @param {HTMLElement} container - The container element
     * @param {Array} results - Array of validation results
     */
    function createDomainHeatmap(container, results) {
        // Group by domain
        const domainStats = {};

        results.forEach(r => {
            let domain = 'unknown';
            try {
                domain = new URL(r.url).hostname;
            } catch {
                return;
            }

            if (!domainStats[domain]) {
                domainStats[domain] = {
                    total: 0,
                    working: 0,
                    broken: 0,
                    avgTime: 0,
                    times: []
                };
            }

            domainStats[domain].total++;

            const status = (r.status || '').toUpperCase();
            if (status === 'WORKING') {
                domainStats[domain].working++;
            } else if (['BROKEN', 'TIMEOUT', 'DNSFAILED', 'SSLERROR'].includes(status)) {
                domainStats[domain].broken++;
            }

            if (r.response_time_ms) {
                domainStats[domain].times.push(r.response_time_ms);
            }
        });

        // Calculate health scores and sort by total URLs
        const domains = Object.entries(domainStats)
            .map(([domain, stats]) => {
                const healthScore = stats.total > 0 ? stats.working / stats.total : 0;
                const avgTime = stats.times.length > 0
                    ? stats.times.reduce((a, b) => a + b, 0) / stats.times.length
                    : 0;

                let healthClass;
                if (healthScore >= 0.95) healthClass = 'health-excellent';
                else if (healthScore >= 0.8) healthClass = 'health-good';
                else if (healthScore >= 0.5) healthClass = 'health-warning';
                else healthClass = 'health-critical';

                return {
                    domain,
                    total: stats.total,
                    working: stats.working,
                    broken: stats.broken,
                    healthScore,
                    avgTime,
                    healthClass
                };
            })
            .sort((a, b) => b.total - a.total);

        // Store all domains for search, but only display top ones
        const allDomains = [...domains];
        const MAX_DISPLAY = 15;
        const displayDomains = domains.slice(0, MAX_DISPLAY);
        const hiddenCount = Math.max(0, allDomains.length - MAX_DISPLAY);

        if (domains.length === 0) {
            container.innerHTML = '<div class="hv-empty-chart">No domain data</div>';
            return;
        }

        const totalUrls = results.length;
        const totalWorking = results.filter(r => r.status === 'working').length;

        // Calculate problem domains (those with issues)
        const problemDomains = allDomains.filter(d => d.healthScore < 1).length;

        container.innerHTML = `
            <div class="hv-chart-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="2" y1="12" x2="22" y2="12"/>
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
                Domain Health
                <span class="hv-domain-count">${allDomains.length} domains${problemDomains > 0 ? ` (${problemDomains} with issues)` : ''}</span>
                <span class="hv-filter-indicator" id="hv-filter-indicator" style="display: none;">
                    <span class="hv-filter-text">Filtered</span>
                    <button class="hv-clear-filter-btn" id="hv-clear-filter-btn" title="Clear filter">✕</button>
                </span>
            </div>
            ${allDomains.length > 5 ? `
            <div class="hv-heatmap-search">
                <input type="text" id="hv-domain-search" placeholder="Search ${allDomains.length} domains..." class="hv-domain-search-input">
            </div>
            ` : ''}
            <div class="hv-heatmap-container" id="hv-heatmap-container">
                <div class="hv-heatmap-cell hv-heatmap-all" data-domain="" title="Show all URLs">
                    <div class="hv-heatmap-domain">All Domains</div>
                    <div class="hv-heatmap-stats">${totalWorking}/${totalUrls} OK</div>
                </div>
                ${displayDomains.map(d => `
                    <div class="hv-heatmap-cell ${d.healthClass}"
                         data-domain="${d.domain}"
                         title="${d.domain}: ${d.working}/${d.total} working (${Math.round(d.healthScore * 100)}%)">
                        <div class="hv-heatmap-domain">${truncateDomain(d.domain)}</div>
                        <div class="hv-heatmap-stats">${d.working}/${d.total} OK</div>
                    </div>
                `).join('')}
                ${hiddenCount > 0 ? `
                <div class="hv-heatmap-more" id="hv-show-more-domains" title="Click to show all domains">
                    <div class="hv-heatmap-domain">+${hiddenCount} more</div>
                    <div class="hv-heatmap-stats">Click to expand</div>
                </div>
                ` : ''}
            </div>
        `;

        // Store all domains for search functionality
        container._allDomains = allDomains;

        // Domain search handler
        const searchInput = document.getElementById('hv-domain-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                const heatmapContainer = document.getElementById('hv-heatmap-container');
                if (!heatmapContainer) return;

                const filtered = query
                    ? allDomains.filter(d => d.domain.toLowerCase().includes(query))
                    : displayDomains;

                // Rebuild heatmap with filtered results
                const cellsHtml = filtered.slice(0, 30).map(d => `
                    <div class="hv-heatmap-cell ${d.healthClass}"
                         data-domain="${d.domain}"
                         title="${d.domain}: ${d.working}/${d.total} working (${Math.round(d.healthScore * 100)}%)">
                        <div class="hv-heatmap-domain">${truncateDomain(d.domain)}</div>
                        <div class="hv-heatmap-stats">${d.working}/${d.total} OK</div>
                    </div>
                `).join('');

                const moreCount = Math.max(0, filtered.length - 30);
                const moreHtml = moreCount > 0 ? `
                    <div class="hv-heatmap-more">
                        <div class="hv-heatmap-domain">+${moreCount} more</div>
                        <div class="hv-heatmap-stats">Refine search</div>
                    </div>
                ` : '';

                heatmapContainer.innerHTML = `
                    <div class="hv-heatmap-cell hv-heatmap-all" data-domain="" title="Show all URLs">
                        <div class="hv-heatmap-domain">All Domains</div>
                        <div class="hv-heatmap-stats">${totalWorking}/${totalUrls} OK</div>
                    </div>
                    ${cellsHtml}
                    ${moreHtml}
                `;

                // Re-attach click handlers
                attachHeatmapClickHandlers(heatmapContainer);
            });
        }

        // Show more domains button
        const showMoreBtn = document.getElementById('hv-show-more-domains');
        if (showMoreBtn) {
            showMoreBtn.addEventListener('click', () => {
                const heatmapContainer = document.getElementById('hv-heatmap-container');
                if (!heatmapContainer) return;

                // Show all domains (up to 50)
                const showDomains = allDomains.slice(0, 50);
                const stillHidden = Math.max(0, allDomains.length - 50);

                const cellsHtml = showDomains.map(d => `
                    <div class="hv-heatmap-cell ${d.healthClass}"
                         data-domain="${d.domain}"
                         title="${d.domain}: ${d.working}/${d.total} working (${Math.round(d.healthScore * 100)}%)">
                        <div class="hv-heatmap-domain">${truncateDomain(d.domain)}</div>
                        <div class="hv-heatmap-stats">${d.working}/${d.total} OK</div>
                    </div>
                `).join('');

                const moreHtml = stillHidden > 0 ? `
                    <div class="hv-heatmap-more">
                        <div class="hv-heatmap-domain">+${stillHidden} more</div>
                        <div class="hv-heatmap-stats">Use search above</div>
                    </div>
                ` : '';

                heatmapContainer.innerHTML = `
                    <div class="hv-heatmap-cell hv-heatmap-all" data-domain="" title="Show all URLs">
                        <div class="hv-heatmap-domain">All Domains</div>
                        <div class="hv-heatmap-stats">${totalWorking}/${totalUrls} OK</div>
                    </div>
                    ${cellsHtml}
                    ${moreHtml}
                `;

                // Re-attach click handlers
                attachHeatmapClickHandlers(heatmapContainer);
            });
        }

        function attachHeatmapClickHandlers(containerEl) {
            containerEl.querySelectorAll('.hv-heatmap-cell').forEach(cell => {
                cell.addEventListener('click', () => {
                    const domain = cell.dataset.domain;
                    if (domain !== undefined) {
                        filterByDomain(domain);
                        updateFilterIndicator(domain);
                    }
                });
            });
        }

        // Add click handlers for filtering
        attachHeatmapClickHandlers(document.getElementById('hv-heatmap-container'));

        // Clear filter button handler
        const clearBtn = document.getElementById('hv-clear-filter-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                clearDomainFilter();
            });
        }
    }

    function truncateDomain(domain, maxLen = 20) {
        if (domain.length > maxLen) {
            return domain.substring(0, maxLen - 2) + '...';
        }
        return domain;
    }

    function filterByDomain(domain) {
        // Trigger filter in main UI
        const searchInput = document.getElementById('hv-filter-search');
        if (searchInput) {
            searchInput.value = domain;
            searchInput.dispatchEvent(new Event('input'));
        }
    }

    function clearDomainFilter() {
        const searchInput = document.getElementById('hv-filter-search');
        if (searchInput) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
        }
        updateFilterIndicator('');
    }

    function updateFilterIndicator(domain) {
        const indicator = document.getElementById('hv-filter-indicator');
        if (indicator) {
            if (domain) {
                indicator.style.display = 'inline-flex';
                const textEl = indicator.querySelector('.hv-filter-text');
                if (textEl) {
                    textEl.textContent = `Filtered: ${truncateDomain(domain)}`;
                }
            } else {
                indicator.style.display = 'none';
            }
        }

        // Update heatmap cell highlighting
        document.querySelectorAll('.hv-heatmap-cell').forEach(cell => {
            cell.classList.remove('hv-heatmap-active');
            if (domain && cell.dataset.domain === domain) {
                cell.classList.add('hv-heatmap-active');
            }
            if (!domain && cell.classList.contains('hv-heatmap-all')) {
                cell.classList.add('hv-heatmap-active');
            }
        });
    }

    // ==========================================================================
    // ANIMATED STAT CARDS
    // ==========================================================================

    /**
     * Create animated stat cards.
     * @param {HTMLElement} container - The container element
     * @param {Object} summary - Summary object with counts
     */
    function createStatCards(container, summary) {
        const stats = [
            { key: 'working', label: 'Working', icon: 'check-circle', value: summary.working || 0 },
            { key: 'broken', label: 'Broken', icon: 'x-circle', value: summary.broken || 0 },
            { key: 'redirect', label: 'Redirects', icon: 'arrow-right-circle', value: summary.redirect || 0 },
            { key: 'timeout', label: 'Timeout', icon: 'clock', value: summary.timeout || 0 },
            { key: 'blocked', label: 'Blocked', icon: 'shield-off', value: summary.blocked || 0 },
            { key: 'unknown', label: 'Other', icon: 'help-circle', value: (summary.unknown || 0) + (summary.dns_failed || 0) + (summary.ssl_error || 0) }
        ];

        container.innerHTML = stats.map(stat => `
            <div class="hv-stat-card stat-${stat.key}">
                <div class="hv-stat-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${getIconPath(stat.icon)}
                    </svg>
                </div>
                <div class="hv-stat-card-value animating" data-target="${stat.value}">0</div>
                <div class="hv-stat-card-label">${stat.label}</div>
            </div>
        `).join('');

        // Animate count up
        container.querySelectorAll('.hv-stat-card-value').forEach(el => {
            animateCounter(el, parseInt(el.dataset.target));
        });
    }

    function getIconPath(icon) {
        const icons = {
            'check-circle': '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
            'x-circle': '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
            'arrow-right-circle': '<circle cx="12" cy="12" r="10"/><polyline points="12 16 16 12 12 8"/><line x1="8" y1="12" x2="16" y2="12"/>',
            'clock': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
            'shield-off': '<path d="M19.69 14a6.9 6.9 0 0 0 .31-2V5l-8-3-3.16 1.18"/><path d="M4.73 4.73 4 5v7c0 6 8 10 8 10a20.29 20.29 0 0 0 5.62-4.38"/><line x1="1" y1="1" x2="23" y2="23"/>',
            'help-circle': '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
        };
        return icons[icon] || '';
    }

    function animateCounter(element, target) {
        const duration = CONFIG.animation.duration;
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (target - start) * easeOut);

            element.textContent = current.toLocaleString();

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                element.classList.remove('animating');
            }
        }

        requestAnimationFrame(update);
    }

    // ==========================================================================
    // STREAMING RESULTS INDICATOR
    // ==========================================================================

    /**
     * Create streaming indicator for real-time results.
     * @param {HTMLElement} container - The container element
     */
    function createStreamingIndicator(container) {
        container.innerHTML = `
            <div class="hv-streaming-indicator">
                <div class="hv-streaming-dot"></div>
                <span class="hv-streaming-text">Validating...</span>
                <span class="hv-streaming-url" id="hv-current-url"></span>
            </div>
        `;
    }

    /**
     * Update the current URL being validated.
     * @param {string} url - The URL currently being validated
     */
    function updateStreamingUrl(url) {
        const urlEl = document.getElementById('hv-current-url');
        if (urlEl) {
            urlEl.textContent = url;
        }
    }

    /**
     * Hide the streaming indicator.
     */
    function hideStreamingIndicator() {
        const indicator = document.querySelector('.hv-streaming-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    // ==========================================================================
    // ENHANCED PROGRESS BAR
    // ==========================================================================

    /**
     * Fun messages to display during progress
     */
    const progressMessages = [
        "Checking links...",
        "Validating URLs...",
        "Pinging servers...",
        "Almost there!",
        "Working hard...",
        "Crunching data...",
        "On it!",
        "Making progress...",
        "Link by link...",
        "Keep going!",
        "You've got this!",
        "Great progress!",
        "So close now!"
    ];

    let lastMessageIndex = -1;
    let lastMilestone = 0;

    /**
     * Get a random fun message (avoiding repeats)
     */
    function getRandomMessage(percent) {
        // Special messages for milestones
        if (percent >= 25 && lastMilestone < 25) {
            lastMilestone = 25;
            return "Quarter way there! 🎯";
        }
        if (percent >= 50 && lastMilestone < 50) {
            lastMilestone = 50;
            return "Halfway done! 🚀";
        }
        if (percent >= 75 && lastMilestone < 75) {
            lastMilestone = 75;
            return "Almost finished! ⚡";
        }
        if (percent >= 90 && lastMilestone < 90) {
            lastMilestone = 90;
            return "Final stretch! 🏁";
        }

        let newIndex;
        do {
            newIndex = Math.floor(Math.random() * progressMessages.length);
        } while (newIndex === lastMessageIndex && progressMessages.length > 1);
        lastMessageIndex = newIndex;
        return progressMessages[newIndex];
    }

    /**
     * Create enhanced progress display with animations.
     * @param {HTMLElement} container - The container element
     * @param {Object} progress - Progress object
     */
    function createEnhancedProgress(container, progress) {
        const percent = progress.overallProgress || 0;
        const completed = progress.urlsCompleted || 0;
        const total = progress.urlsTotal || 0;
        const phase = progress.phase || 'Initializing';
        const currentUrl = progress.currentUrl || '';
        const speed = progress.speed || 0;
        const eta = progress.eta || '';

        // Reset milestone tracker on new validation
        if (percent < 5) {
            lastMilestone = 0;
        }

        const funMessage = getRandomMessage(percent);

        // Truncate URL for display
        const displayUrl = currentUrl.length > 50
            ? currentUrl.substring(0, 47) + '...'
            : currentUrl;

        container.innerHTML = `
            <div class="hv-progress-enhanced" id="hv-progress-enhanced">
                <div class="hv-progress-header">
                    <div class="hv-progress-phase">
                        <div class="hv-progress-phase-dot"></div>
                        <span class="hv-progress-phase-text">${phase}</span>
                        <span class="hv-progress-message" id="hv-progress-message">${funMessage}</span>
                    </div>
                    <div class="hv-progress-stats">
                        <span class="hv-progress-count" id="hv-progress-count">${completed}</span>
                        <span>/ ${total} URLs</span>
                        ${eta ? `
                        <span class="hv-progress-eta">
                            <svg class="hv-progress-eta-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12 6 12 12 16 14"/>
                            </svg>
                            ~${eta}
                        </span>
                        ` : ''}
                    </div>
                </div>
                <div class="molten-progress molten-small molten-with-reflection hv-molten-progress">
                    <div class="molten-rail"></div>
                    <div class="molten-fill hv-progress-bar-fill" style="width: ${percent}%"></div>
                    <div class="molten-orb hv-progress-orb" style="left: ${percent}%"></div>
                </div>
                ${currentUrl ? `
                <div class="hv-progress-current-url">
                    <svg class="hv-progress-url-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                    </svg>
                    <span class="hv-progress-url-text">${displayUrl}</span>
                    ${speed > 0 ? `
                    <span class="hv-progress-speed">
                        <svg class="hv-progress-speed-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                        </svg>
                        ${speed}/s
                    </span>
                    ` : ''}
                </div>
                ` : ''}
                <div class="hv-progress-details">
                    <div class="hv-progress-detail">
                        <div class="hv-progress-detail-value">${Math.round(percent)}%</div>
                        <div class="hv-progress-detail-label">Complete</div>
                    </div>
                    <div class="hv-progress-detail">
                        <div class="hv-progress-detail-value">${completed}</div>
                        <div class="hv-progress-detail-label">Checked</div>
                    </div>
                    <div class="hv-progress-detail">
                        <div class="hv-progress-detail-value">${total - completed}</div>
                        <div class="hv-progress-detail-label">Remaining</div>
                    </div>
                </div>
            </div>
        `;

        // Add milestone celebration if we just hit one
        if (percent >= 25 && percent < 30 && lastMilestone === 25 ||
            percent >= 50 && percent < 55 && lastMilestone === 50 ||
            percent >= 75 && percent < 80 && lastMilestone === 75 ||
            percent >= 90 && percent < 95 && lastMilestone === 90) {
            showMilestoneEmoji(percent);
        }
    }

    /**
     * Show milestone celebration emoji
     */
    function showMilestoneEmoji(percent) {
        const container = document.getElementById('hv-progress-enhanced');
        if (!container) return;

        const emoji = percent >= 90 ? '🏁' : percent >= 75 ? '⚡' : percent >= 50 ? '🚀' : '🎯';
        const milestone = document.createElement('div');
        milestone.className = 'hv-progress-milestone';
        milestone.textContent = emoji;
        container.appendChild(milestone);

        // Remove after animation
        setTimeout(() => milestone.remove(), 600);
    }

    /**
     * Update progress bar fill with animation.
     * @param {number} percent - Percentage complete
     * @param {Object} options - Optional updates (currentUrl, speed, etc.)
     */
    function updateProgress(percent, options = {}) {
        const fill = document.querySelector('.hv-progress-bar-fill');
        if (fill) {
            fill.style.width = `${percent}%`;
            // Update molten orb position
            const orb = document.querySelector('.hv-progress-orb');
            if (orb) orb.style.left = `${percent}%`;
            // Handle complete state
            const moltenProgress = document.querySelector('.hv-molten-progress');
            if (moltenProgress && percent >= 100) {
                moltenProgress.classList.add('molten-complete');
            }
        }

        // Update count with bump animation
        const countEl = document.getElementById('hv-progress-count');
        if (countEl && options.completed !== undefined) {
            countEl.textContent = options.completed;
            countEl.classList.add('counting');
            setTimeout(() => countEl.classList.remove('counting'), 200);
        }

        // Update message occasionally
        const messageEl = document.getElementById('hv-progress-message');
        if (messageEl && Math.random() < 0.1) { // 10% chance to update message
            messageEl.textContent = getRandomMessage(percent);
            messageEl.style.animation = 'none';
            messageEl.offsetHeight; // Trigger reflow
            messageEl.style.animation = 'hv-message-fade 0.3s ease-out';
        }

        // Update current URL if provided
        if (options.currentUrl) {
            const urlText = document.querySelector('.hv-progress-url-text');
            if (urlText) {
                const displayUrl = options.currentUrl.length > 50
                    ? options.currentUrl.substring(0, 47) + '...'
                    : options.currentUrl;
                urlText.textContent = displayUrl;
            }
        }
    }

    // ==========================================================================
    // ERROR DETAIL EXPANSION
    // ==========================================================================

    /**
     * Create expandable error details for a result row.
     * @param {Object} result - The validation result
     * @returns {string} HTML string for the details panel
     */
    function createErrorDetails(result) {
        const details = [];

        // HTTP Status
        if (result.status_code) {
            details.push({
                label: 'HTTP Status',
                value: result.status_code,
                class: result.status_code >= 200 && result.status_code < 400 ? 'success' : 'error'
            });
        }

        // Response Time
        if (result.response_time_ms) {
            details.push({
                label: 'Response Time',
                value: `${Math.round(result.response_time_ms)}ms`,
                class: result.response_time_ms < 1000 ? 'success' : result.response_time_ms < 3000 ? 'warning' : 'error'
            });
        }

        // Final URL (if different)
        if (result.final_url && result.final_url !== result.url) {
            details.push({
                label: 'Final URL',
                value: result.final_url,
                class: ''
            });
        }

        // SSL Info
        if (result.ssl_expiry) {
            const daysUntilExpiry = Math.ceil((new Date(result.ssl_expiry) - new Date()) / (1000 * 60 * 60 * 24));
            details.push({
                label: 'SSL Expires',
                value: `${daysUntilExpiry} days`,
                class: daysUntilExpiry > 30 ? 'success' : daysUntilExpiry > 7 ? 'warning' : 'error'
            });
        }

        // Server
        if (result.server) {
            details.push({
                label: 'Server',
                value: result.server,
                class: ''
            });
        }

        // Content Type
        if (result.content_type) {
            details.push({
                label: 'Content Type',
                value: result.content_type,
                class: ''
            });
        }

        // Error Message
        if (result.error_detail || result.message) {
            details.push({
                label: 'Details',
                value: result.error_detail || result.message,
                class: 'error'
            });
        }

        let html = `
            <div class="hv-result-details">
                <div class="hv-details-grid">
                    ${details.map(d => `
                        <div class="hv-detail-item">
                            <span class="hv-detail-label">${d.label}</span>
                            <span class="hv-detail-value ${d.class}">${escapeHtml(d.value)}</span>
                        </div>
                    `).join('')}
                </div>
        `;

        // Redirect chain
        if (result.redirect_chain && result.redirect_chain.length > 0) {
            html += `
                <div class="hv-redirect-chain">
                    <span class="hv-detail-label">Redirect Chain</span>
                    ${result.redirect_chain.map((step, idx) => `
                        <div class="hv-redirect-step">
                            ${idx > 0 ? '<svg class="hv-redirect-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>' : ''}
                            <span class="hv-redirect-code">${step.status}</span>
                            <span class="hv-redirect-url">${escapeHtml(step.url)}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    // ==========================================================================
    // SKELETON LOADING
    // ==========================================================================

    /**
     * Create skeleton loading placeholders.
     * @param {HTMLElement} container - The container element
     * @param {string} type - Type of skeleton ('stats', 'table', 'chart')
     */
    function createSkeleton(container, type) {
        switch (type) {
            case 'stats':
                container.innerHTML = Array(6).fill(0).map(() =>
                    '<div class="hv-skeleton hv-skeleton-stat"></div>'
                ).join('');
                break;
            case 'table':
                container.innerHTML = Array(5).fill(0).map(() =>
                    '<div class="hv-skeleton hv-skeleton-row"></div>'
                ).join('');
                break;
            case 'chart':
                container.innerHTML = '<div class="hv-skeleton hv-skeleton-chart"></div>';
                break;
        }
    }

    // ==========================================================================
    // UTILITIES
    // ==========================================================================

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ==========================================================================
    // PUBLIC API
    // ==========================================================================

    return {
        createDonutChart,
        createResponseHistogram,
        createDomainHeatmap,
        createDomainHealthCarousel,
        createStatCards,
        createStreamingIndicator,
        updateStreamingUrl,
        hideStreamingIndicator,
        createEnhancedProgress,
        updateProgress,
        createErrorDetails,
        createSkeleton,
        CONFIG
    };

})();
