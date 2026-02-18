/**
 * Metrics & Analytics Command Center
 * ====================================
 * Full-featured analytics dashboard with multi-tab layout,
 * Chart.js visualizations, D3 heatmaps/bubbles, drill-down
 * tables, sparklines, and count-up animations.
 *
 * @version 1.0.0 (v4.6.1)
 * @module MetricsAnalytics
 */
window.MetricsAnalytics = (function () {
    'use strict';

    // ── Constants ────────────────────────────────────────────────
    const CHART_PALETTE = ['#3b82f6', '#8b5cf6', '#ec4899', '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4'];
    const GRADE_COLORS = { A: '#22c55e', B: '#84cc16', C: '#eab308', D: '#f97316', F: '#ef4444' };
    const DIRECTIVE_COLORS = { shall: '#ef4444', must: '#ea580c', will: '#3b82f6', should: '#22c55e', may: '#8b5cf6' };
    const COUNTUP_DURATION = 800;

    // ── State ────────────────────────────────────────────────────
    let modal = null;
    let initialized = false;
    let isLoading = false;
    let data = null;             // Cached API response
    let dataTimestamp = null;
    let currentTab = 'overview';
    let charts = {};             // Chart.js instances keyed by canvas ID
    let sortState = {};          // Per-table sort state

    // ── Helpers ──────────────────────────────────────────────────

    function $(sel, ctx) { return (ctx || document).querySelector(sel); }
    function $$(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

    function fmt(n) {
        if (n == null) return '—';
        if (typeof n === 'number') {
            if (Number.isInteger(n)) return n.toLocaleString();
            return n.toFixed(1);
        }
        return String(n);
    }

    function pct(n, total) {
        if (!total) return '0%';
        return ((n / total) * 100).toFixed(1) + '%';
    }

    function gradeFor(score) {
        if (score == null) return '—';
        if (score >= 90) return 'A';
        if (score >= 80) return 'B';
        if (score >= 70) return 'C';
        if (score >= 60) return 'D';
        return 'F';
    }

    function gradeClass(grade) {
        return 'ma-grade ma-grade-' + (grade || 'F');
    }

    function scoreColorClass(score) {
        return 'ma-score-' + gradeFor(score);
    }

    function relTime(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        const diff = Date.now() - d.getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return 'just now';
        if (mins < 60) return mins + 'm ago';
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return hrs + 'h ago';
        const days = Math.floor(hrs / 24);
        return days + 'd ago';
    }

    function truncFile(name, max) {
        max = max || 30;
        if (!name) return '—';
        if (name.length <= max) return name;
        const ext = name.lastIndexOf('.');
        if (ext > 0 && name.length - ext <= 6) {
            const e = name.slice(ext);
            return name.slice(0, max - e.length - 1) + '…' + e;
        }
        return name.slice(0, max - 1) + '…';
    }

    function csrfToken() {
        return window.CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    function isDark() {
        // v4.6.1: Detect dark mode from body class OR landing page (always dark-styled)
        return document.body.classList.contains('dark-mode') ||
               document.body.classList.contains('landing-active');
    }

    function chartTextColor() {
        return isDark() ? '#9ca3af' : '#6b7280';
    }

    function chartGridColor() {
        return isDark() ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    }

    function refreshIcons() {
        if (typeof lucide !== 'undefined' && lucide.createIcons) {
            lucide.createIcons();
        }
    }

    // ── Count-Up Animation ───────────────────────────────────────

    function countUp(el, target, duration) {
        if (!el) return;
        duration = duration || COUNTUP_DURATION;
        const start = performance.now();
        const isFloat = !Number.isInteger(target);
        const from = 0;

        function tick(now) {
            const t = Math.min((now - start) / duration, 1);
            // easeOutCubic
            const ease = 1 - Math.pow(1 - t, 3);
            const val = from + (target - from) * ease;
            el.textContent = isFloat ? val.toFixed(1) : Math.round(val).toLocaleString();
            if (t < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    }

    // ── Sparkline Renderer (inline SVG) ──────────────────────────

    function drawSparkline(svgEl, values, color) {
        if (!svgEl || !values || values.length < 2) {
            if (svgEl) svgEl.innerHTML = '';
            return;
        }
        color = color || '#D6A84A';
        const w = parseInt(svgEl.getAttribute('width')) || 60;
        const h = parseInt(svgEl.getAttribute('height')) || 24;
        const pad = 2;
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;

        const points = values.map((v, i) => {
            const x = pad + (i / (values.length - 1)) * (w - 2 * pad);
            const y = h - pad - ((v - min) / range) * (h - 2 * pad);
            return { x, y };
        });

        const linePath = points.map((p, i) => (i === 0 ? 'M' : 'L') + p.x.toFixed(1) + ',' + p.y.toFixed(1)).join(' ');
        const areaPath = linePath + ' L' + points[points.length - 1].x.toFixed(1) + ',' + h + ' L' + points[0].x.toFixed(1) + ',' + h + ' Z';

        svgEl.innerHTML =
            '<path class="spark-area" d="' + areaPath + '" fill="' + color + '" opacity="0.15"/>' +
            '<path class="spark-line" d="' + linePath + '" fill="none" stroke="' + color + '" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>';
    }

    // ── Chart Utilities ──────────────────────────────────────────

    function destroyChart(id) {
        if (charts[id]) {
            charts[id].destroy();
            delete charts[id];
        }
    }

    function destroyAllCharts() {
        Object.keys(charts).forEach(destroyChart);
    }

    function makeChart(canvasId, config) {
        destroyChart(canvasId);
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        const ctx = canvas.getContext('2d');
        charts[canvasId] = new Chart(ctx, config);
        return charts[canvasId];
    }

    function defaultTooltip() {
        return {
            backgroundColor: isDark() ? '#374151' : '#1f2937',
            titleColor: '#f9fafb',
            bodyColor: '#d1d5db',
            borderColor: isDark() ? '#4b5563' : '#374151',
            borderWidth: 1,
            cornerRadius: 6,
            padding: 8,
            titleFont: { size: 12, weight: 600 },
            bodyFont: { size: 11 },
            displayColors: true,
            boxPadding: 4
        };
    }

    function defaultScales(xLabel, yLabel) {
        return {
            x: {
                ticks: { color: chartTextColor(), font: { size: 10 }, maxRotation: 45 },
                grid: { color: chartGridColor() },
                title: xLabel ? { display: true, text: xLabel, color: chartTextColor(), font: { size: 10 } } : undefined
            },
            y: {
                ticks: { color: chartTextColor(), font: { size: 10 } },
                grid: { color: chartGridColor() },
                beginAtZero: true,
                title: yLabel ? { display: true, text: yLabel, color: chartTextColor(), font: { size: 10 } } : undefined
            }
        };
    }

    // ── Table Builder ────────────────────────────────────────────

    function buildTable(containerId, columns, rows, options) {
        options = options || {};
        const wrap = document.getElementById(containerId);
        if (!wrap) return;
        // v4.6.1: Work on a copy to avoid mutating cached API data when sorting
        rows = rows.slice();

        const tableId = containerId + '-tbl';
        let html = '<table class="ma-table" id="' + tableId + '"><thead><tr>';

        columns.forEach(function (col) {
            const cls = [];
            if (col.num) cls.push('ma-col-num');
            if (col.score) cls.push('ma-col-score');
            html += '<th data-key="' + col.key + '"' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') + '>' + col.label + '</th>';
        });
        html += '</tr></thead><tbody>';

        rows.forEach(function (row, idx) {
            const clickClass = options.clickable ? ' class="ma-clickable"' : '';
            html += '<tr' + clickClass + ' data-idx="' + idx + '">';
            columns.forEach(function (col) {
                const val = row[col.key];
                const cls = [];
                if (col.name) cls.push('ma-col-name');
                if (col.num) cls.push('ma-col-num');
                if (col.score) cls.push('ma-col-score');

                let display = '';
                if (col.render) {
                    display = col.render(val, row);
                } else if (col.score && val != null) {
                    const g = gradeFor(val);
                    display = '<span class="' + scoreColorClass(val) + '">' + Math.round(val) + '</span>';
                } else if (col.grade) {
                    display = '<span class="' + gradeClass(val) + '">' + (val || '—') + '</span>';
                } else {
                    display = fmt(val);
                }
                html += '<td' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') + '>' + display + '</td>';
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        wrap.innerHTML = html;

        // Sort handlers
        const table = document.getElementById(tableId);
        if (table) {
            table.querySelectorAll('th[data-key]').forEach(function (th) {
                th.addEventListener('click', function () {
                    const key = th.getAttribute('data-key');
                    const prev = sortState[tableId];
                    let dir = 'asc';
                    if (prev && prev.key === key && prev.dir === 'asc') dir = 'desc';

                    // Clear sort classes
                    table.querySelectorAll('th').forEach(function (t) { t.classList.remove('sorted-asc', 'sorted-desc'); });
                    th.classList.add('sorted-' + dir);

                    sortState[tableId] = { key: key, dir: dir };

                    rows.sort(function (a, b) {
                        let va = a[key], vb = b[key];
                        if (va == null) va = '';
                        if (vb == null) vb = '';
                        if (typeof va === 'string') va = va.toLowerCase();
                        if (typeof vb === 'string') vb = vb.toLowerCase();
                        if (va < vb) return dir === 'asc' ? -1 : 1;
                        if (va > vb) return dir === 'asc' ? 1 : -1;
                        return 0;
                    });

                    // Re-render tbody
                    const tbody = table.querySelector('tbody');
                    let tbHtml = '';
                    rows.forEach(function (row, idx) {
                        const clickClass = options.clickable ? ' class="ma-clickable"' : '';
                        tbHtml += '<tr' + clickClass + ' data-idx="' + idx + '">';
                        columns.forEach(function (col) {
                            const val = row[col.key];
                            const cls = [];
                            if (col.name) cls.push('ma-col-name');
                            if (col.num) cls.push('ma-col-num');
                            if (col.score) cls.push('ma-col-score');
                            let display = '';
                            if (col.render) display = col.render(val, row);
                            else if (col.score && val != null) {
                                display = '<span class="' + scoreColorClass(val) + '">' + Math.round(val) + '</span>';
                            } else if (col.grade) {
                                display = '<span class="' + gradeClass(val) + '">' + (val || '—') + '</span>';
                            } else display = fmt(val);
                            tbHtml += '<td' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') + '>' + display + '</td>';
                        });
                        tbHtml += '</tr>';
                    });
                    tbody.innerHTML = tbHtml;

                    // Re-attach row click handlers
                    if (options.onRowClick) {
                        tbody.querySelectorAll('tr.ma-clickable').forEach(function (tr) {
                            tr.addEventListener('click', function () {
                                options.onRowClick(rows[parseInt(tr.getAttribute('data-idx'))], tr);
                            });
                        });
                    }
                });
            });

            // Row click handlers
            if (options.onRowClick) {
                table.querySelectorAll('tbody tr.ma-clickable').forEach(function (tr) {
                    tr.addEventListener('click', function () {
                        options.onRowClick(rows[parseInt(tr.getAttribute('data-idx'))], tr);
                    });
                });
            }
        }
    }

    // ── Drill-Down Helpers ───────────────────────────────────────

    function openDrilldown(panelId, title, contentHtml) {
        const panel = document.getElementById(panelId);
        if (!panel) return;
        panel.innerHTML =
            '<div class="ma-drill-header">' +
            '<span class="ma-drill-title">' + title + '</span>' +
            '<button class="ma-drill-close" data-panel="' + panelId + '"><i data-lucide="x"></i> Close</button>' +
            '</div>' +
            '<div class="ma-drill-body">' + contentHtml + '</div>';
        panel.classList.add('open');
        refreshIcons();

        panel.querySelector('.ma-drill-close')?.addEventListener('click', function () {
            closeDrilldown(panelId);
        });
    }

    function closeDrilldown(panelId) {
        const panel = document.getElementById(panelId);
        if (!panel) return;
        panel.classList.remove('open');
        // Reset active rows in parent tables
        $$('.ma-row-active').forEach(function (r) { r.classList.remove('ma-row-active'); });
    }

    // ── Hero Stat Cards Builder ──────────────────────────────────

    function buildHeroStats(containerId, cards) {
        const wrap = document.getElementById(containerId);
        if (!wrap) return;
        wrap.innerHTML = '';
        cards.forEach(function (card) {
            const div = document.createElement('div');
            div.className = 'ma-stat-card' + (card.accent ? ' ma-stat-accent-' + card.accent : '');
            div.innerHTML =
                '<div class="ma-stat-top">' +
                '<span class="ma-stat-label">' + card.label + '</span>' +
                (card.sparkData ? '<svg class="ma-sparkline" width="60" height="24"></svg>' : '') +
                '</div>' +
                '<div class="ma-stat-value">0</div>' +
                '<div class="ma-stat-sub">' + (card.sub || '') + '</div>';
            wrap.appendChild(div);

            // Count-up
            const valEl = div.querySelector('.ma-stat-value');
            countUp(valEl, card.value, COUNTUP_DURATION);

            // Sparkline
            if (card.sparkData) {
                const svg = div.querySelector('.ma-sparkline');
                drawSparkline(svg, card.sparkData, card.sparkColor || '#D6A84A');
            }
        });
    }

    // ══════════════════════════════════════════════════════════════
    //  TAB RENDERERS
    // ══════════════════════════════════════════════════════════════

    // ── Overview Tab ─────────────────────────────────────────────

    function renderOverviewTab() {
        if (!data) return;
        const ov = data.overview || {};
        const scans = data.scans || [];
        const qual = data.quality || {};

        // Hero stats
        const scoreTrend = (qual.score_trend || []).map(function (s) { return s.score; }).slice(-10);
        buildHeroStats('ma-overview-hero', [
            { label: 'Documents', value: ov.total_documents || 0, sub: 'analyzed', accent: 'blue', sparkData: scoreTrend.length > 1 ? scoreTrend : null },
            { label: 'Statements', value: ov.total_statements || 0, sub: 'extracted', accent: 'purple' },
            { label: 'Roles', value: ov.total_roles || 0, sub: 'in dictionary', accent: 'green' },
            { label: 'Avg Score', value: ov.avg_score || 0, sub: 'out of 100', accent: 'amber', sparkData: scoreTrend.length > 1 ? scoreTrend : null, sparkColor: GRADE_COLORS[gradeFor(ov.avg_score)] }
        ]);

        // Score Trend line chart
        var trendData = (qual.score_trend || []).slice(-50);
        if (trendData.length > 0) {
            makeChart('ma-chart-score-trend', {
                type: 'line',
                data: {
                    labels: trendData.map(function (s) { return truncFile(s.filename, 15); }),
                    datasets: [{
                        label: 'Score',
                        data: trendData.map(function (s) { return s.score; }),
                        borderColor: '#D6A84A',
                        backgroundColor: 'rgba(214, 168, 74, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        pointBackgroundColor: trendData.map(function (s) { return GRADE_COLORS[gradeFor(s.score)] || '#D6A84A'; }),
                        pointBorderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: defaultScales(null, 'Score')
                }
            });
        }

        // Grade Distribution doughnut
        var gd = qual.grade_distribution || {};
        var gradeLabels = ['A', 'B', 'C', 'D', 'F'];
        var gradeValues = gradeLabels.map(function (g) { return gd[g] || 0; });
        var gradeTotal = gradeValues.reduce(function (a, b) { return a + b; }, 0);

        if (gradeTotal > 0) {
            makeChart('ma-chart-grade-dist', {
                type: 'doughnut',
                data: {
                    labels: gradeLabels,
                    datasets: [{
                        data: gradeValues,
                        backgroundColor: gradeLabels.map(function (g) { return GRADE_COLORS[g]; }),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '68%',
                    plugins: {
                        legend: { position: 'bottom', labels: { color: chartTextColor(), font: { size: 11 }, padding: 12, usePointStyle: true } },
                        tooltip: defaultTooltip()
                    }
                }
            });
            // Center text
            var centerEl = document.getElementById('ma-grade-center-text');
            if (centerEl) {
                centerEl.innerHTML = '<span class="ma-center-num">' + gradeTotal + '</span><span class="ma-center-label">scans</span>';
            }
        }

        // Activity heatmap (D3)
        renderActivityHeatmap(scans);

        // Mini stats
        var miniData = {
            'ma-mini-words': ov.total_word_count || 0,
            'ma-mini-avgwords': ov.avg_word_count ? Math.round(ov.avg_word_count) : 0,
            'ma-mini-issues': ov.total_issues || 0,
            'ma-mini-adjudicated': (data.roles || {}).total_confirmed || (data.roles || {}).total_adjudicated || 0,
            'ma-mini-deliverables': (data.roles || {}).total_deliverable || 0,
            'ma-mini-scans': ov.total_scans || 0
        };
        Object.keys(miniData).forEach(function (id) {
            var el = document.getElementById(id);
            if (el) countUp(el, miniData[id], COUNTUP_DURATION);
        });

        refreshIcons();
    }

    function renderActivityHeatmap(scans) {
        var container = document.getElementById('ma-heatmap-container');
        if (!container || typeof d3 === 'undefined') return;
        container.innerHTML = '';

        // Count scans per day
        var dayCounts = {};
        (scans || []).forEach(function (s) {
            if (!s.scan_time) return;
            var day = s.scan_time.split(' ')[0].split('T')[0];
            dayCounts[day] = (dayCounts[day] || 0) + 1;
        });

        var now = new Date();
        var startDate = new Date(now);
        startDate.setFullYear(startDate.getFullYear() - 1);
        startDate.setDate(startDate.getDate() - startDate.getDay()); // align to Sunday

        var cellSize = 12;
        var cellPad = 2;
        var weeks = 53;
        var svgW = weeks * (cellSize + cellPad) + 40;
        var svgH = 7 * (cellSize + cellPad) + 30;

        var svg = d3.select(container)
            .append('svg')
            .attr('width', svgW)
            .attr('height', svgH);

        var maxCount = Math.max(1, d3.max(Object.values(dayCounts)) || 1);
        var colorScale = d3.scaleLinear()
            .domain([0, maxCount * 0.25, maxCount * 0.5, maxCount])
            .range(isDark()
                ? ['#161b22', '#0e4429', '#006d32', '#26a641']
                : ['#ebedf0', '#9be9a8', '#40c463', '#30a14e']);

        // Day labels
        var dayNames = ['', 'Mon', '', 'Wed', '', 'Fri', ''];
        svg.selectAll('.day-label')
            .data(dayNames)
            .enter()
            .append('text')
            .attr('class', 'heatmap-label')
            .attr('x', 28)
            .attr('y', function (d, i) { return i * (cellSize + cellPad) + cellSize + 20; })
            .attr('text-anchor', 'end')
            .text(function (d) { return d; });

        // Cells
        var current = new Date(startDate);
        var cells = [];
        while (current <= now) {
            var dateStr = current.toISOString().split('T')[0];
            var dayOfWeek = current.getDay();
            var weekIdx = Math.floor((current - startDate) / (7 * 86400000));
            cells.push({ date: dateStr, day: dayOfWeek, week: weekIdx, count: dayCounts[dateStr] || 0 });
            current.setDate(current.getDate() + 1);
        }

        // Custom tooltip element
        var tooltip = document.getElementById('ma-heatmap-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'ma-heatmap-tooltip';
            tooltip.className = 'ma-heatmap-tooltip';
            document.body.appendChild(tooltip);
        }
        tooltip.classList.remove('visible');

        function formatDate(dateStr) {
            var parts = dateStr.split('-');
            var d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
            var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            var dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            return dayNames[d.getDay()] + ', ' + monthNames[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
        }

        // Build a lookup map: "week,day" → cell data for O(1) hit-testing
        var cellLookup = {};
        cells.forEach(function (c) { cellLookup[c.week + ',' + c.day] = c; });

        // Render cells (no mouse events — handled by overlay)
        svg.selectAll('.heatmap-cell')
            .data(cells)
            .enter()
            .append('rect')
            .attr('class', 'heatmap-cell')
            .attr('x', function (d) { return d.week * (cellSize + cellPad) + 34; })
            .attr('y', function (d) { return d.day * (cellSize + cellPad) + 16; })
            .attr('width', cellSize)
            .attr('height', cellSize)
            .attr('fill', function (d) { return colorScale(d.count); })
            .attr('rx', 2)
            .attr('ry', 2);

        // Hover highlight rect (rendered after cells so it paints on top)
        var hoverStroke = isDark() ? 'rgba(255,255,255,0.5)' : 'rgba(0,0,0,0.4)';
        var hoverRect = svg.append('rect')
            .attr('class', 'heatmap-hover')
            .attr('width', cellSize + 2)
            .attr('height', cellSize + 2)
            .attr('rx', 2).attr('ry', 2)
            .attr('fill', 'none')
            .attr('stroke', hoverStroke)
            .attr('stroke-width', 1.5)
            .style('pointer-events', 'none')
            .style('visibility', 'hidden');

        // v5.9.0: Single transparent overlay for ALL mouse tracking.
        // Per-cell mouseenter/mouseleave caused flickering when crossing the 2px
        // gap between 12px cells — the mouse would leave cell A, enter the gap
        // (no cell), then enter cell B, causing rapid tooltip hide/show cycles.
        // Instead, one overlay catches all mouse movement and uses math to
        // determine which cell the cursor is over. No gap = no flicker.
        var gridOriginX = 34;
        var gridOriginY = 16;
        var lastHitKey = null;

        svg.append('rect')
            .attr('class', 'heatmap-overlay')
            .attr('x', gridOriginX)
            .attr('y', gridOriginY)
            .attr('width', weeks * (cellSize + cellPad))
            .attr('height', 7 * (cellSize + cellPad))
            .attr('fill', 'transparent')
            .on('mousemove', function (event) {
                var e = event || d3.event;
                var svgNode = svg.node();
                var pt = svgNode.createSVGPoint();
                pt.x = e.clientX;
                pt.y = e.clientY;
                var svgPt = pt.matrixTransform(svgNode.getScreenCTM().inverse());

                // Which cell is the mouse over?
                var col = Math.floor((svgPt.x - gridOriginX) / (cellSize + cellPad));
                var row = Math.floor((svgPt.y - gridOriginY) / (cellSize + cellPad));

                // Check if we're actually inside a cell (not in the 2px gap)
                var localX = (svgPt.x - gridOriginX) - col * (cellSize + cellPad);
                var localY = (svgPt.y - gridOriginY) - row * (cellSize + cellPad);
                var inCell = localX >= 0 && localX < cellSize && localY >= 0 && localY < cellSize;

                var hitKey = inCell ? col + ',' + row : null;
                var cellData = hitKey ? cellLookup[hitKey] : null;

                if (cellData) {
                    // Update tooltip only when we enter a different cell
                    if (hitKey !== lastHitKey) {
                        lastHitKey = hitKey;
                        var cx = col * (cellSize + cellPad) + gridOriginX;
                        var cy = row * (cellSize + cellPad) + gridOriginY;
                        hoverRect
                            .attr('x', cx - 1)
                            .attr('y', cy - 1)
                            .style('visibility', 'visible');

                        var countText = cellData.count > 0
                            ? '<span class="htt-count">' + cellData.count + ' scan' + (cellData.count !== 1 ? 's' : '') + '</span>'
                            : '<span class="htt-zero">No scans</span>';
                        tooltip.innerHTML = countText + ' &mdash; ' + formatDate(cellData.date);
                    }
                    tooltip.style.left = (e.clientX + 12) + 'px';
                    tooltip.style.top = (e.clientY - 10) + 'px';
                    tooltip.style.opacity = '1';
                } else {
                    // In a gap or outside grid — hide
                    if (lastHitKey !== null) {
                        lastHitKey = null;
                        hoverRect.style('visibility', 'hidden');
                        tooltip.style.opacity = '0';
                    }
                }
            })
            .on('mouseleave', function () {
                lastHitKey = null;
                hoverRect.style('visibility', 'hidden');
                tooltip.style.opacity = '0';
            });

        // Month labels
        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        var monthPositions = {};
        cells.forEach(function (c) {
            var m = parseInt(c.date.split('-')[1]) - 1;
            if (!(m in monthPositions)) monthPositions[m] = c.week;
        });
        Object.keys(monthPositions).forEach(function (m) {
            svg.append('text')
                .attr('class', 'heatmap-label')
                .attr('x', monthPositions[m] * (cellSize + cellPad) + 34)
                .attr('y', 10)
                .text(months[m]);
        });
    }

    // ── Quality Tab ──────────────────────────────────────────────

    function renderQualityTab() {
        if (!data) return;
        var qual = data.quality || {};
        var docs = data.documents || [];

        // Hero stats
        var scores = docs.filter(function (d) { return d.latest_score != null; }).map(function (d) { return d.latest_score; });
        var bestScore = scores.length ? Math.max.apply(null, scores) : 0;
        var worstScore = scores.length ? Math.min.apply(null, scores) : 0;

        buildHeroStats('ma-quality-hero', [
            { label: 'Avg Score', value: data.overview.avg_score || 0, sub: 'across all scans', accent: 'amber' },
            { label: 'Best Score', value: bestScore, sub: 'highest achieved', accent: 'green' },
            { label: 'Worst Score', value: worstScore, sub: 'needs attention', accent: 'red' },
            { label: 'Total Issues', value: data.overview.total_issues || 0, sub: 'detected', accent: 'purple' }
        ]);

        // Score distribution bar chart
        var sd = qual.score_distribution || [];
        if (sd.length > 0) {
            makeChart('ma-chart-score-dist', {
                type: 'bar',
                data: {
                    labels: sd.map(function (b) { return b.range; }),
                    datasets: [{
                        label: 'Documents',
                        data: sd.map(function (b) { return b.count; }),
                        backgroundColor: sd.map(function (b) {
                            var mid = parseInt(b.range.split('-')[0]) + 5;
                            return GRADE_COLORS[gradeFor(mid)] + 'cc';
                        }),
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: defaultScales('Score Range', 'Count')
                }
            });
        }

        // Issue categories horizontal bar
        var ic = qual.issue_categories || [];
        if (ic.length > 0) {
            makeChart('ma-chart-issue-cats', {
                type: 'bar',
                data: {
                    labels: ic.slice(0, 10).map(function (c) { return c.category || 'Unknown'; }),
                    datasets: [{
                        label: 'Issues',
                        data: ic.slice(0, 10).map(function (c) { return c.count; }),
                        backgroundColor: CHART_PALETTE.slice(0, 10),
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: {
                        x: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() }, beginAtZero: true },
                        y: { ticks: { color: chartTextColor(), font: { size: 10 } }, grid: { display: false } }
                    }
                }
            });
        }

        // Top 10 Issues table
        var topIssues = qual.top_issues || [];
        if (topIssues.length > 0) {
            buildTable('ma-quality-issues-table', [
                { key: 'message', label: 'Issue', name: true },
                { key: 'category', label: 'Category' },
                { key: 'count', label: 'Count', num: true }
            ], topIssues);
        } else {
            document.getElementById('ma-quality-issues-table').innerHTML = '<p style="padding:1rem;color:var(--text-muted)">No issue data available</p>';
        }

        // Document Scores table
        var scoredDocs = docs.filter(function (d) { return d.latest_score != null; });
        buildTable('ma-quality-docs-table', [
            { key: 'filename', label: 'Document', name: true, render: function (v) { return truncFile(v, 40); } },
            { key: 'latest_score', label: 'Score', score: true },
            { key: 'latest_grade', label: 'Grade', grade: true },
            { key: 'issue_count', label: 'Issues', num: true },
            { key: 'scan_count', label: 'Scans', num: true }
        ], scoredDocs, {
            clickable: true,
            onRowClick: function (row, tr) {
                // Toggle active state
                $$('.ma-row-active').forEach(function (r) { r.classList.remove('ma-row-active'); });
                tr.classList.add('ma-row-active');

                // Show drill-down: scan history for this document
                var docScans = (data.scans || []).filter(function (s) { return s.document_id === row.id; });
                if (docScans.length === 0) {
                    openDrilldown('ma-quality-drilldown', row.filename, '<p style="color:var(--text-muted)">No scan history found</p>');
                    return;
                }
                var tblHtml = '<table class="ma-table"><thead><tr><th>Scan Time</th><th>Score</th><th>Grade</th><th>Issues</th></tr></thead><tbody>';
                docScans.forEach(function (s) {
                    var g = gradeFor(s.score);
                    tblHtml += '<tr>';
                    tblHtml += '<td>' + (s.scan_time || '—') + '</td>';
                    tblHtml += '<td class="ma-col-score"><span class="' + scoreColorClass(s.score) + '">' + Math.round(s.score || 0) + '</span></td>';
                    tblHtml += '<td class="ma-col-score"><span class="' + gradeClass(g) + '">' + g + '</span></td>';
                    tblHtml += '<td class="ma-col-num">' + (s.issue_count || 0) + '</td>';
                    tblHtml += '</tr>';
                });
                tblHtml += '</tbody></table>';
                openDrilldown('ma-quality-drilldown', 'Scan History: ' + row.filename, tblHtml);
            }
        });

        refreshIcons();
    }

    // ── Statements Tab ───────────────────────────────────────────

    function renderStatementsTab() {
        if (!data) return;
        var stmts = data.statements || {};

        // Hero stats
        buildHeroStats('ma-statements-hero', [
            { label: 'Total Statements', value: stmts.total || 0, sub: 'extracted', accent: 'blue' },
            { label: 'Shall', value: (stmts.by_directive || {}).shall || 0, sub: 'requirements', accent: 'red' },
            { label: 'Must', value: (stmts.by_directive || {}).must || 0, sub: 'requirements', accent: 'amber' },
            { label: 'Unique Roles', value: (stmts.by_role || []).length, sub: 'assigned', accent: 'purple' }
        ]);

        // Directive doughnut
        var dirs = stmts.by_directive || {};
        var dirLabels = ['Shall', 'Must', 'Will', 'Should', 'May'];
        var dirValues = dirLabels.map(function (d) { return dirs[d.toLowerCase()] || 0; });
        var dirTotal = dirValues.reduce(function (a, b) { return a + b; }, 0);

        if (dirTotal > 0) {
            makeChart('ma-chart-directive-dist', {
                type: 'doughnut',
                data: {
                    labels: dirLabels,
                    datasets: [{
                        data: dirValues,
                        backgroundColor: dirLabels.map(function (d) { return DIRECTIVE_COLORS[d.toLowerCase()]; }),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '68%',
                    plugins: {
                        legend: { position: 'bottom', labels: { color: chartTextColor(), font: { size: 11 }, padding: 12, usePointStyle: true } },
                        tooltip: defaultTooltip()
                    }
                }
            });
            var dCenterEl = document.getElementById('ma-directive-center-text');
            if (dCenterEl) {
                dCenterEl.innerHTML = '<span class="ma-center-num">' + dirTotal + '</span><span class="ma-center-label">total</span>';
            }
        }

        // Level distribution bar
        var levels = stmts.by_level || {};
        var levelLabels = Object.keys(levels).sort();
        if (levelLabels.length > 0) {
            makeChart('ma-chart-level-dist', {
                type: 'bar',
                data: {
                    labels: levelLabels.map(function (l) { return 'Level ' + l; }),
                    datasets: [{
                        label: 'Statements',
                        data: levelLabels.map(function (l) { return levels[l]; }),
                        backgroundColor: ['#3b82f6', '#8b5cf6', '#ec4899', '#ef4444'].slice(0, levelLabels.length),
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: defaultScales(null, 'Count')
                }
            });
        }

        // Statements by Document horizontal bar
        var byDoc = (stmts.by_document || []).slice(0, 15);
        if (byDoc.length > 0) {
            makeChart('ma-chart-stmts-by-doc', {
                type: 'bar',
                data: {
                    labels: byDoc.map(function (d) { return truncFile(d.filename, 20); }),
                    datasets: [{
                        label: 'Statements',
                        data: byDoc.map(function (d) { return d.count; }),
                        backgroundColor: '#3b82f6cc',
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: {
                        x: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() }, beginAtZero: true },
                        y: { ticks: { color: chartTextColor(), font: { size: 10 } }, grid: { display: false } }
                    }
                }
            });
        }

        // Role assignment polar area
        var byRole = (stmts.by_role || []).slice(0, 10);
        if (byRole.length > 0) {
            makeChart('ma-chart-role-assign', {
                type: 'polarArea',
                data: {
                    labels: byRole.map(function (r) { return r.role || 'Unknown'; }),
                    datasets: [{
                        data: byRole.map(function (r) { return r.count; }),
                        backgroundColor: CHART_PALETTE.slice(0, byRole.length).map(function (c) { return c + 'aa'; })
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: chartTextColor(), font: { size: 10 }, padding: 8, usePointStyle: true } },
                        tooltip: defaultTooltip()
                    },
                    scales: {
                        r: { ticks: { display: false }, grid: { color: chartGridColor() } }
                    }
                }
            });
        }

        refreshIcons();
    }

    // ── Roles Tab ────────────────────────────────────────────────

    function renderRolesTab() {
        if (!data) return;
        var roles = data.roles || {};

        // Hero stats — use total_confirmed (not total_adjudicated which includes deliverable+rejected)
        var confirmed = roles.total_confirmed || 0;
        buildHeroStats('ma-roles-hero', [
            { label: 'Total Roles', value: roles.total_extracted || 0, sub: 'in dictionary', accent: 'blue' },
            { label: 'Confirmed', value: confirmed, sub: 'adjudicated', accent: 'green' },
            { label: 'Deliverable', value: roles.total_deliverable || 0, sub: 'active', accent: 'amber' },
            { label: 'Rejected', value: roles.total_rejected || 0, sub: 'excluded', accent: 'red' }
        ]);

        // Adjudication status doughnut
        // total_adjudicated = confirmed + deliverable + rejected (all processed roles)
        var adjProcessed = (roles.total_adjudicated || 0);
        var adjPending = Math.max(0, (roles.total_extracted || 0) - adjProcessed);

        var adjLabels = ['Confirmed', 'Deliverable', 'Rejected', 'Pending'];
        var adjValues = [confirmed, roles.total_deliverable || 0, roles.total_rejected || 0, adjPending];
        var adjColors = ['#22c55e', '#D6A84A', '#ef4444', '#6b7280'];

        if (adjValues.some(function (v) { return v > 0; })) {
            makeChart('ma-chart-adj-status', {
                type: 'doughnut',
                data: {
                    labels: adjLabels,
                    datasets: [{
                        data: adjValues,
                        backgroundColor: adjColors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '68%',
                    plugins: {
                        legend: { position: 'bottom', labels: { color: chartTextColor(), font: { size: 11 }, padding: 12, usePointStyle: true } },
                        tooltip: defaultTooltip()
                    }
                }
            });
            var aCenterEl = document.getElementById('ma-adj-center-text');
            if (aCenterEl) {
                aCenterEl.innerHTML = '<span class="ma-center-num">' + (roles.total_extracted || 0) + '</span><span class="ma-center-label">total</span>';
            }
        }

        // Roles by category horizontal bar
        var byCat = (roles.by_category || []).slice(0, 12);
        if (byCat.length > 0) {
            makeChart('ma-chart-role-cats', {
                type: 'bar',
                data: {
                    labels: byCat.map(function (c) { return c.category || 'Uncategorized'; }),
                    datasets: [{
                        label: 'Roles',
                        data: byCat.map(function (c) { return c.count; }),
                        backgroundColor: CHART_PALETTE.slice(0, byCat.length).map(function (c) { return c + 'cc'; }),
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: {
                        x: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() }, beginAtZero: true },
                        y: { ticks: { color: chartTextColor(), font: { size: 10 } }, grid: { display: false } }
                    }
                }
            });
        }

        // Function coverage bubble chart (D3)
        renderFunctionBubbles(roles.function_coverage || []);

        // Top Roles table
        var topRoles = (roles.top_by_documents || []).slice(0, 20);
        if (topRoles.length > 0) {
            buildTable('ma-roles-top-table', [
                { key: 'role', label: 'Role', name: true },
                { key: 'document_count', label: 'Documents', num: true },
                { key: 'mention_count', label: 'Mentions', num: true }
            ], topRoles, {
                clickable: true,
                onRowClick: function (row, tr) {
                    $$('.ma-row-active').forEach(function (r) { r.classList.remove('ma-row-active'); });
                    tr.classList.add('ma-row-active');
                    // Show summary with stats
                    var avgMentions = row.document_count > 0 ? (row.mention_count / row.document_count).toFixed(1) : 0;
                    var html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-bottom:0.75rem">' +
                        '<div class="ma-stat-card ma-stat-accent-blue" style="padding:0.75rem"><div class="ma-stat-label">Documents</div><div class="ma-stat-value" style="font-size:1.25rem">' + fmt(row.document_count) + '</div></div>' +
                        '<div class="ma-stat-card ma-stat-accent-purple" style="padding:0.75rem"><div class="ma-stat-label">Total Mentions</div><div class="ma-stat-value" style="font-size:1.25rem">' + fmt(row.mention_count) + '</div></div>' +
                        '<div class="ma-stat-card ma-stat-accent-amber" style="padding:0.75rem"><div class="ma-stat-label">Avg per Doc</div><div class="ma-stat-value" style="font-size:1.25rem">' + avgMentions + '</div></div>' +
                        '</div>' +
                        '<p style="color:var(--text-muted);font-size:0.75rem;margin:0">Open Roles Studio from the dashboard to see full role details and document assignments.</p>';
                    openDrilldown('ma-roles-drilldown', 'Role: ' + row.role, html);
                }
            });
        }

        // Relationship types bar
        var rels = data.relationships || {};
        var relTypes = rels.by_type || [];
        if (relTypes.length > 0) {
            makeChart('ma-chart-rel-types', {
                type: 'bar',
                data: {
                    labels: relTypes.map(function (r) { return r.type || 'Unknown'; }),
                    datasets: [{
                        label: 'Count',
                        data: relTypes.map(function (r) { return r.count; }),
                        backgroundColor: CHART_PALETTE.slice(0, relTypes.length),
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: defaultScales(null, 'Count')
                }
            });
        }

        refreshIcons();
    }

    function renderFunctionBubbles(funcCoverage) {
        var container = document.getElementById('ma-func-bubble-container');
        if (!container || typeof d3 === 'undefined' || !funcCoverage || funcCoverage.length === 0) {
            if (container) container.innerHTML = '<p style="padding:1rem;color:var(--text-muted);text-align:center">No function tag data available</p>';
            return;
        }
        container.innerHTML = '';

        var width = container.clientWidth || 400;
        var height = 250;

        var svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        var pack = d3.pack()
            .size([width - 20, height - 20])
            .padding(4);

        var root = d3.hierarchy({ children: funcCoverage })
            .sum(function (d) { return d.role_count || 1; });

        pack(root);

        var nodes = svg.selectAll('.bubble-node')
            .data(root.leaves())
            .enter()
            .append('g')
            .attr('class', 'bubble-node')
            .attr('transform', function (d) { return 'translate(' + (d.x + 10) + ',' + (d.y + 10) + ')'; });

        nodes.append('circle')
            .attr('r', function (d) { return d.r; })
            .attr('fill', function (d) { return d.data.color || '#3b82f6'; })
            .attr('opacity', 0.85);

        nodes.filter(function (d) { return d.r > 18; })
            .append('text')
            .attr('class', 'bubble-label')
            .attr('dy', '-0.2em')
            .text(function (d) { return d.data.code || ''; });

        nodes.filter(function (d) { return d.r > 18; })
            .append('text')
            .attr('class', 'bubble-count')
            .attr('dy', '1em')
            .text(function (d) { return d.data.role_count; });

        nodes.append('title')
            .text(function (d) { return (d.data.name || d.data.code) + ': ' + d.data.role_count + ' roles'; });
    }

    // ── Documents Tab ────────────────────────────────────────────

    function renderDocumentsTab() {
        if (!data) return;
        var docs = data.documents || [];
        var docMeta = data.documents_meta || {};
        var ov = data.overview || {};

        // Hero stats
        var multiScanDocs = docs.filter(function (d) { return d.scan_count >= 2; }).length;
        var scanCoverage = docs.length > 0 ? Math.round((multiScanDocs / docs.length) * 100) : 0;

        buildHeroStats('ma-documents-hero', [
            { label: 'Documents', value: docs.length, sub: 'in system', accent: 'blue' },
            { label: 'Total Words', value: ov.total_word_count || 0, sub: 'across all docs', accent: 'purple' },
            { label: 'Avg Words', value: ov.avg_word_count ? Math.round(ov.avg_word_count) : 0, sub: 'per document', accent: 'amber' },
            { label: 'Multi-Scan', value: scanCoverage, sub: '% with 2+ scans', accent: 'green' }
        ]);

        // Word count distribution bar
        var wcd = docMeta.word_count_distribution || [];
        if (wcd.length > 0) {
            makeChart('ma-chart-word-dist', {
                type: 'bar',
                data: {
                    labels: wcd.map(function (b) { return b.range; }),
                    datasets: [{
                        label: 'Documents',
                        data: wcd.map(function (b) { return b.count; }),
                        backgroundColor: '#3b82f6cc',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: defaultScales(null, 'Documents')
                }
            });
        }

        // Documents by category type pie
        var byCatType = docMeta.by_category_type || [];
        if (byCatType.length > 0) {
            makeChart('ma-chart-doc-cats', {
                type: 'doughnut',
                data: {
                    labels: byCatType.map(function (c) { return c.type || 'Unclassified'; }),
                    datasets: [{
                        data: byCatType.map(function (c) { return c.count; }),
                        backgroundColor: CHART_PALETTE.slice(0, byCatType.length),
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '50%',
                    plugins: {
                        legend: { position: 'bottom', labels: { color: chartTextColor(), font: { size: 10 }, padding: 8, usePointStyle: true } },
                        tooltip: defaultTooltip()
                    }
                }
            });
        }

        // Documents by function horizontal bar
        var byFunc = docMeta.by_function || [];
        if (byFunc.length > 0) {
            makeChart('ma-chart-doc-funcs', {
                type: 'bar',
                data: {
                    labels: byFunc.map(function (f) { return f.code || f.name || 'Unknown'; }),
                    datasets: [{
                        label: 'Documents',
                        data: byFunc.map(function (f) { return f.count; }),
                        backgroundColor: byFunc.map(function (f) { return (f.color || '#3b82f6') + 'cc'; }),
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false }, tooltip: defaultTooltip() },
                    scales: {
                        x: { ticks: { color: chartTextColor() }, grid: { color: chartGridColor() }, beginAtZero: true },
                        y: { ticks: { color: chartTextColor(), font: { size: 10 } }, grid: { display: false } }
                    }
                }
            });
        }

        // Document portfolio table
        buildTable('ma-docs-portfolio-table', [
            { key: 'filename', label: 'Document', name: true, render: function (v) { return truncFile(v, 40); } },
            { key: 'word_count', label: 'Words', num: true },
            { key: 'scan_count', label: 'Scans', num: true },
            { key: 'latest_score', label: 'Score', score: true },
            { key: 'latest_grade', label: 'Grade', grade: true },
            { key: 'role_count', label: 'Roles', num: true },
            { key: 'statement_count', label: 'Stmts', num: true }
        ], docs.slice(), {
            clickable: true,
            onRowClick: function (row) {
                var docScans = (data.scans || []).filter(function (s) { return s.document_id === row.id; });
                var html = '<p style="font-size:0.8125rem;color:var(--text-secondary);margin:0 0 0.5rem">' +
                    '<strong>' + row.filename + '</strong> — ' + fmt(row.word_count) + ' words, ' + row.scan_count + ' scan(s)</p>';
                if (docScans.length > 0) {
                    html += '<table class="ma-table"><thead><tr><th>Time</th><th>Score</th><th>Grade</th><th>Issues</th></tr></thead><tbody>';
                    docScans.forEach(function (s) {
                        var g = gradeFor(s.score);
                        html += '<tr><td>' + (s.scan_time || '') + '</td><td class="ma-col-score"><span class="' + scoreColorClass(s.score) + '">' + Math.round(s.score || 0) + '</span></td><td class="ma-col-score"><span class="' + gradeClass(g) + '">' + g + '</span></td><td class="ma-col-num">' + (s.issue_count || 0) + '</td></tr>';
                    });
                    html += '</tbody></table>';
                } else {
                    html += '<p style="color:var(--text-muted)">No scan history</p>';
                }
                openDrilldown('ma-documents-drilldown', 'Document: ' + row.filename, html);
            }
        });

        refreshIcons();
    }

    // ══════════════════════════════════════════════════════════════
    //  TAB MANAGEMENT
    // ══════════════════════════════════════════════════════════════

    function switchTab(tabName) {
        if (tabName === currentTab && document.querySelector('#ma-tab-' + tabName + '.active')) return;
        currentTab = tabName;

        // Update tab buttons
        $$('.ma-tab', modal).forEach(function (t) {
            t.classList.toggle('active', t.getAttribute('data-tab') === tabName);
            t.setAttribute('aria-selected', t.getAttribute('data-tab') === tabName ? 'true' : 'false');
        });

        // Update tab content panels
        $$('.ma-tab-content', modal).forEach(function (tc) {
            tc.classList.toggle('active', tc.id === 'ma-tab-' + tabName);
        });

        // Close any open drill-downs
        $$('.ma-drilldown.open', modal).forEach(function (dd) { dd.classList.remove('open'); });

        // Destroy current charts and render new tab
        destroyAllCharts();
        renderCurrentTab();
    }

    function renderCurrentTab() {
        switch (currentTab) {
            case 'overview': renderOverviewTab(); break;
            case 'quality': renderQualityTab(); break;
            case 'statements': renderStatementsTab(); break;
            case 'roles': renderRolesTab(); break;
            case 'documents': renderDocumentsTab(); break;
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  DATA LOADING
    // ══════════════════════════════════════════════════════════════

    function showLoading() {
        var el = document.getElementById('ma-loading');
        if (el) el.classList.remove('hidden');
        var empty = document.getElementById('ma-empty');
        if (empty) empty.classList.remove('visible');
        // Hide all tab content while loading
        $$('.ma-tab-content', modal).forEach(function (tc) { tc.style.visibility = 'hidden'; });
    }

    function hideLoading() {
        var el = document.getElementById('ma-loading');
        if (el) el.classList.add('hidden');
        // Show tab content
        $$('.ma-tab-content', modal).forEach(function (tc) { tc.style.visibility = ''; });
    }

    // v5.9.2: Accept optional message for descriptive empty states
    function showEmpty(message) {
        var el = document.getElementById('ma-empty');
        if (el) {
            el.classList.add('visible');
            // Update the message text if provided
            if (message) {
                var msgEl = el.querySelector('.ma-empty-message') || el.querySelector('p');
                if (msgEl) msgEl.textContent = message;
            }
        }
    }

    function loadDashboardData(forceRefresh) {
        if (isLoading) return;
        if (data && !forceRefresh && dataTimestamp && (Date.now() - dataTimestamp) < 300000) {
            // Use cached data (< 5 min old)
            hideLoading();
            renderCurrentTab();
            return;
        }

        isLoading = true;
        showLoading();

        var refreshBtn = document.getElementById('ma-btn-refresh');
        if (refreshBtn) refreshBtn.classList.add('spinning');

        fetch('/api/metrics/dashboard', {
            method: 'GET',
            headers: { 'X-CSRF-Token': csrfToken() }
        })
            .then(function (resp) {
                if (!resp.ok) throw new Error('HTTP ' + resp.status + ' ' + resp.statusText);
                return resp.json();
            })
            .then(function (json) {
                isLoading = false;
                if (refreshBtn) refreshBtn.classList.remove('spinning');

                // v5.9.2: More robust data validation with detailed logging
                console.log('[MetricsAnalytics] API response:', json.success, json.data ? 'has data' : 'no data');

                if (json.success && json.data) {
                    data = json.data;
                    dataTimestamp = Date.now();

                    // Update timestamp
                    var ts = document.getElementById('ma-last-updated');
                    if (ts) ts.textContent = 'Updated ' + new Date().toLocaleTimeString();

                    hideLoading();

                    // v5.9.2: Defensive check — overview might be missing or malformed
                    if (!data.overview || typeof data.overview !== 'object') {
                        console.warn('[MetricsAnalytics] Missing or invalid overview data:', data.overview);
                        showEmpty('No scan data found. Scan some documents to see analytics.');
                    } else if (data.overview.total_documents === 0) {
                        showEmpty('No documents scanned yet. Run your first document scan to start tracking metrics.');
                    } else {
                        renderCurrentTab();
                    }
                } else {
                    hideLoading();
                    console.warn('[MetricsAnalytics] API returned failure:', json.error || 'unknown');
                    showEmpty('Failed to load metrics data. Check server logs.');
                    if (typeof showToast === 'function') showToast('error', json.error || 'Failed to load metrics data');
                }
            })
            .catch(function (err) {
                isLoading = false;
                if (refreshBtn) refreshBtn.classList.remove('spinning');
                hideLoading();
                console.error('[MetricsAnalytics] Load error:', err);
                showEmpty('Error loading metrics: ' + err.message);
                if (typeof showToast === 'function') showToast('error', 'Failed to load metrics: ' + err.message);
            });
    }

    // ══════════════════════════════════════════════════════════════
    //  INIT / OPEN / CLOSE
    // ══════════════════════════════════════════════════════════════

    function init() {
        if (initialized) return;
        modal = document.getElementById('modal-metrics-analytics');
        if (!modal) return;

        // Tab click handlers
        modal.addEventListener('click', function (e) {
            // Tab buttons
            var tab = e.target.closest('.ma-tab');
            if (tab) {
                var tabName = tab.getAttribute('data-tab');
                if (tabName) switchTab(tabName);
                return;
            }

            // Close button
            if (e.target.closest('#ma-btn-close')) {
                close();
                return;
            }

            // Refresh button
            if (e.target.closest('#ma-btn-refresh')) {
                loadDashboardData(true);
                return;
            }

            // Backdrop click
            if (e.target === modal) {
                close();
                return;
            }
        });

        // Keyboard handler
        function onKeyDown(e) {
            if (!modal.classList.contains('active')) return;
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopPropagation();
                close();
            }
        }
        document.addEventListener('keydown', onKeyDown);

        initialized = true;
    }

    function open() {
        init();
        if (!modal) return;

        // v4.6.1: Apply dark styling when dark mode or landing page (always dark) is active
        modal.classList.toggle('ma-dark', isDark());

        modal.classList.add('active');
        document.body.classList.add('modal-open');

        // Reset to overview tab
        currentTab = 'overview';
        $$('.ma-tab', modal).forEach(function (t) {
            t.classList.toggle('active', t.getAttribute('data-tab') === 'overview');
        });
        $$('.ma-tab-content', modal).forEach(function (tc) {
            tc.classList.toggle('active', tc.id === 'ma-tab-overview');
        });

        refreshIcons();
        loadDashboardData(false);
    }

    function close() {
        if (!modal) return;
        modal.classList.remove('active');
        document.body.classList.remove('modal-open');

        // Destroy all charts to free memory
        destroyAllCharts();

        // Hide heatmap tooltip
        var htt = document.getElementById('ma-heatmap-tooltip');
        if (htt) htt.style.opacity = '0';

        // Close drill-downs
        $$('.ma-drilldown.open', modal).forEach(function (dd) { dd.classList.remove('open'); });

        // Return to dashboard
        if (typeof TWR !== 'undefined' && TWR.LandingPage && typeof TWR.LandingPage.show === 'function') {
            TWR.LandingPage.show();
        }
    }

    // ── Public API ───────────────────────────────────────────────
    // v5.9.14: Expose switchTab for guide system preActions
    return { init: init, open: open, close: close, switchTab: switchTab };
})();
