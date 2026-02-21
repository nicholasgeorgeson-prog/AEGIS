"""
AEGIS Proposal Compare Export - Interactive HTML Generator

Generates a standalone, self-contained HTML file with full comparison analysis.
All CSS and JS inline, data embedded as JSON. NO external dependencies.

Features:
  - 6-tab interactive dashboard (Executive, Comparison, Categories, Vendor Scorecard, Risk, Rates)
  - Dark/light mode with localStorage persistence
  - Inline SVG charts (tornado, stacked bar, radar, donut) — no Canvas/Chart.js
  - Sortable tables, filter chips, search
  - Animated count-up hero stats
  - Print-optimized @media print stylesheet
  - Responsive grid layouts

Usage:
    from proposal_compare_export import generate_proposal_compare_html
    html = generate_proposal_compare_html(comparison_data)

    # comparison_data comes from ComparisonResult.to_dict()
"""

import json
import html as html_module
from datetime import datetime, timezone
from typing import Dict, Any


def generate_proposal_compare_html(comparison_data: dict) -> str:
    """
    Generate a standalone interactive HTML file for proposal comparison analysis.

    Args:
        comparison_data: Dict from ComparisonResult.to_dict() containing:
            - proposals, aligned_items, category_summaries, totals,
            - red_flags, heatmap, rate_analysis, indirect_rates,
            - vendor_scores, executive_summary, cost_breakdown, metadata

    Returns:
        Complete HTML string (standalone, no external dependencies)
    """
    metadata = comparison_data.get('metadata') or {}
    project_name = html_module.escape(str(metadata.get('project_name', 'Proposal Comparison')))
    compared_at = metadata.get('compared_at', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M'))
    version = metadata.get('version', '5.9.41')

    # Safely serialize all data for embedding
    safe_data = json.dumps(comparison_data, default=str)

    html = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS Proposal Comparison — {project_name}</title>
    <style>
{_get_css()}
    </style>
</head>
<body>
    <!-- Embedded comparison data -->
    <script type="application/json" id="comparison-data">{safe_data}</script>

    <div class="app">
        <!-- Header -->
        <header class="header">
            <div class="header-left">
                <div class="aegis-logo">
                    <svg width="36" height="36" viewBox="0 0 100 100">
                        <defs>
                            <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" style="stop-color:#D6A84A"/>
                                <stop offset="100%" style="stop-color:#B8743A"/>
                            </linearGradient>
                        </defs>
                        <path d="M50 5 L90 25 L90 55 C90 75 70 92 50 98 C30 92 10 75 10 55 L10 25 Z"
                              fill="url(#shieldGrad)" stroke="#9A6B2E" stroke-width="2"/>
                        <text x="50" y="62" text-anchor="middle" fill="white" font-size="28"
                              font-weight="bold" font-family="Arial">A</text>
                    </svg>
                </div>
                <div class="header-titles">
                    <h1>AEGIS Proposal Comparison Report</h1>
                    <p class="subtitle">{project_name} &mdash; {html_module.escape(str(compared_at)[:16])}</p>
                </div>
            </div>
            <div class="header-right">
                <button class="btn btn-icon" id="btn-print" onclick="window.print()" title="Print Report">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
                        <rect x="6" y="14" width="12" height="8"/>
                    </svg>
                </button>
                <button class="btn btn-icon" id="btn-theme" onclick="toggleTheme()" title="Toggle dark/light mode">
                    <svg id="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                    <svg id="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                </button>
            </div>
        </header>

        <!-- Tab Navigation -->
        <nav class="tab-nav" id="tab-nav">
            <button class="tab-btn active" data-tab="executive" onclick="switchTab('executive')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
                Executive Dashboard
            </button>
            <button class="tab-btn" data-tab="comparison" onclick="switchTab('comparison')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                Comparison Matrix
            </button>
            <button class="tab-btn" data-tab="categories" onclick="switchTab('categories')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="22" height="5" rx="2"/><rect x="1" y="10" width="16" height="5" rx="2"/><rect x="1" y="17" width="10" height="5" rx="2"/></svg>
                Category Analysis
            </button>
            <button class="tab-btn" data-tab="scorecard" onclick="switchTab('scorecard')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                Vendor Scorecard
            </button>
            <button class="tab-btn" data-tab="risk" onclick="switchTab('risk')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                Risk Analysis
            </button>
            <button class="tab-btn" data-tab="rates" onclick="switchTab('rates')" id="tab-btn-rates" style="display:none">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                Rate Analysis
            </button>
        </nav>

        <!-- Tab Panels -->
        <main class="tab-panels">
            <section class="tab-panel active" id="panel-executive"></section>
            <section class="tab-panel" id="panel-comparison"></section>
            <section class="tab-panel" id="panel-categories"></section>
            <section class="tab-panel" id="panel-scorecard"></section>
            <section class="tab-panel" id="panel-risk"></section>
            <section class="tab-panel" id="panel-rates"></section>
        </main>

        <!-- Footer -->
        <footer class="footer">
            <span>Generated by AEGIS Proposal Compare v{html_module.escape(str(version))} &mdash;
                  {html_module.escape(str(compared_at)[:16])} &mdash; CONFIDENTIAL</span>
        </footer>
    </div>

    <script>
{_get_js()}
    </script>
</body>
</html>'''

    return html


# ──────────────────────────────────────────────────────────
# CSS Generator
# ──────────────────────────────────────────────────────────

def _get_css() -> str:
    return '''
/* ======================================================
   AEGIS Proposal Compare Export — Standalone CSS
   ====================================================== */

:root {
    --gold: #D6A84A;
    --gold-dim: rgba(214, 168, 74, 0.15);
    --bronze: #B8743A;
    --navy: #1B2838;
    --success: #219653;
    --success-bg: rgba(33, 150, 83, 0.12);
    --error: #EB5757;
    --error-bg: rgba(235, 87, 87, 0.12);
    --warning: #F2994A;
    --warning-bg: rgba(242, 153, 74, 0.12);
    --info: #2196f3;
    --info-bg: rgba(33, 150, 243, 0.12);
    --grade-a: #219653;
    --grade-b: #56d68c;
    --grade-c: #F2994A;
    --grade-d: #e67e22;
    --grade-f: #EB5757;
    --radius: 8px;
    --radius-lg: 12px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.12);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.15);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.2);
    --transition: 0.2s ease;
}

[data-theme="dark"] {
    --bg-deep: #0d1117;
    --bg-surface: #161b22;
    --bg-card: #1c2333;
    --bg-card-hover: #222d3f;
    --bg-input: #0d1117;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --text-muted: #6e7681;
    --border-color: #30363d;
    --border-light: #21262d;
    --table-stripe: rgba(255,255,255,0.02);
    --scrollbar-thumb: #30363d;
    --highlight-row: rgba(214,168,74,0.08);
}

[data-theme="light"] {
    --bg-deep: #f0f2f5;
    --bg-surface: #ffffff;
    --bg-card: #ffffff;
    --bg-card-hover: #f8f9fa;
    --bg-input: #f0f2f5;
    --text-primary: #1B2838;
    --text-secondary: #57606a;
    --text-muted: #8b949e;
    --border-color: #d0d7de;
    --border-light: #e8ecf0;
    --table-stripe: rgba(0,0,0,0.02);
    --scrollbar-thumb: #c1c7cd;
    --highlight-row: rgba(214,168,74,0.08);
}

/* Reset */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg-deep);
    color: var(--text-primary);
    line-height: 1.5;
    min-height: 100vh;
}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 4px; }

/* App Shell */
.app {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px 24px;
}

/* ── Header ── */
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 16px;
    gap: 16px;
    flex-wrap: wrap;
}
.header-left {
    display: flex;
    align-items: center;
    gap: 14px;
}
.aegis-logo { flex-shrink: 0; }
.header-titles h1 {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--gold);
    line-height: 1.2;
}
.subtitle {
    font-size: 0.82rem;
    color: var(--text-secondary);
    margin-top: 2px;
}
.header-right {
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 14px;
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    background: var(--bg-card);
    color: var(--text-primary);
    cursor: pointer;
    font-size: 0.82rem;
    transition: background var(--transition), border-color var(--transition);
}
.btn:hover { background: var(--bg-card-hover); border-color: var(--gold); }
.btn-icon { padding: 7px 9px; }

/* ── Tab Navigation ── */
.tab-nav {
    display: flex;
    gap: 4px;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 0;
    margin-bottom: 20px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
.tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    background: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.82rem;
    font-weight: 500;
    white-space: nowrap;
    transition: color var(--transition), border-color var(--transition);
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active {
    color: var(--gold);
    border-bottom-color: var(--gold);
}
.tab-btn svg { opacity: 0.7; }
.tab-btn.active svg { opacity: 1; }

/* Tab Panels */
.tab-panel { display: none; }
.tab-panel.active { display: block; }

/* ── Hero Stats ── */
.hero-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
}
.hero-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 20px;
    text-align: center;
    transition: transform var(--transition), box-shadow var(--transition);
}
.hero-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.hero-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--gold);
    line-height: 1.1;
    font-variant-numeric: tabular-nums;
}
.hero-label {
    font-size: 0.78rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 6px;
}
.hero-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 4px;
}

/* ── Cards / Sections ── */
.section-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 24px;
    margin-bottom: 20px;
}
.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title svg { color: var(--gold); }

/* ── Tables ── */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
}
.data-table th, .data-table td {
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid var(--border-light);
}
.data-table th {
    background: var(--bg-surface);
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    position: sticky;
    top: 0;
    z-index: 2;
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
}
.data-table th:hover { color: var(--gold); }
.data-table th .sort-arrow { margin-left: 4px; opacity: 0.4; font-size: 0.7rem; }
.data-table th.sorted .sort-arrow { opacity: 1; color: var(--gold); }
.data-table tbody tr:nth-child(even) { background: var(--table-stripe); }
.data-table tbody tr:hover { background: var(--highlight-row); }
.data-table .text-right { text-align: right; }
.data-table .text-center { text-align: center; }
.data-table .amount { font-variant-numeric: tabular-nums; font-weight: 500; }
.data-table .amount-lowest { color: var(--success); font-weight: 700; }
.data-table .amount-highest { color: var(--error); font-weight: 700; }
.data-table .total-row { font-weight: 700; background: var(--bg-surface) !important; border-top: 2px solid var(--border-color); }
.data-table .variance-cell { font-weight: 600; }
.table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    border-radius: var(--radius);
    border: 1px solid var(--border-light);
}

/* ── Filter Chips ── */
.filter-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
    align-items: center;
}
.filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 5px 12px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    background: var(--bg-surface);
    color: var(--text-secondary);
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--transition);
    user-select: none;
}
.filter-chip:hover { border-color: var(--gold); color: var(--text-primary); }
.filter-chip.active {
    background: var(--gold-dim);
    border-color: var(--gold);
    color: var(--gold);
    font-weight: 600;
}
.search-input {
    padding: 7px 12px;
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 0.82rem;
    width: 240px;
    outline: none;
    transition: border-color var(--transition);
}
.search-input:focus { border-color: var(--gold); }
.search-input::placeholder { color: var(--text-muted); }
.filter-count {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-left: 8px;
}

/* ── Podium / Rankings ── */
.podium-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
}
.podium-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 18px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.podium-card.rank-1 { border-color: var(--gold); }
.podium-card.rank-1::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--gold), var(--bronze));
}
.podium-rank {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-muted);
    margin-bottom: 4px;
}
.podium-card.rank-1 .podium-rank { color: var(--gold); font-weight: 700; }
.podium-vendor {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 6px;
    word-break: break-word;
}
.podium-amount {
    font-size: 1.25rem;
    font-weight: 800;
    color: var(--gold);
    font-variant-numeric: tabular-nums;
}
.podium-delta {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 4px;
}

/* ── Findings / Opportunities ── */
.finding-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border-light);
}
.finding-item:last-child { border-bottom: none; }
.finding-badge {
    display: inline-flex;
    align-items: center;
    padding: 3px 9px;
    border-radius: 12px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    flex-shrink: 0;
}
.badge-critical { background: var(--error-bg); color: var(--error); }
.badge-warning { background: var(--warning-bg); color: var(--warning); }
.badge-info { background: var(--info-bg); color: var(--info); }
.finding-text { font-size: 0.85rem; color: var(--text-primary); line-height: 1.5; }

/* ── SVG Charts ── */
.chart-container {
    width: 100%;
    margin: 16px 0;
    overflow: visible;
}
.chart-container svg {
    width: 100%;
    height: auto;
    display: block;
}
.chart-tooltip {
    position: fixed;
    padding: 8px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    font-size: 0.78rem;
    color: var(--text-primary);
    pointer-events: none;
    z-index: 1000;
    box-shadow: var(--shadow-md);
    max-width: 280px;
    display: none;
}
.chart-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: center;
    margin-top: 12px;
    font-size: 0.78rem;
    color: var(--text-secondary);
}
.legend-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}
.legend-swatch {
    width: 12px;
    height: 12px;
    border-radius: 3px;
    flex-shrink: 0;
}

/* ── Grade Cards ── */
.scorecard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
}
.score-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 24px;
    position: relative;
    overflow: hidden;
}
.score-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.score-card.grade-A::before { background: var(--grade-a); }
.score-card.grade-B::before { background: var(--grade-b); }
.score-card.grade-C::before { background: var(--grade-c); }
.score-card.grade-D::before { background: var(--grade-d); }
.score-card.grade-F::before { background: var(--grade-f); }
.score-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}
.score-vendor-name {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    word-break: break-word;
}
.score-grade-badge {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    font-weight: 900;
    color: white;
    flex-shrink: 0;
}
.score-overall {
    font-size: 0.78rem;
    color: var(--text-muted);
    text-align: center;
    margin-top: 2px;
}
.score-bar-group {
    margin-bottom: 10px;
}
.score-bar-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-bottom: 4px;
}
.score-bar-track {
    width: 100%;
    height: 6px;
    background: var(--border-light);
    border-radius: 3px;
    overflow: hidden;
}
.score-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.8s ease;
}
.score-flags {
    margin-top: 12px;
    font-size: 0.75rem;
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 4px;
}

/* ── Heatmap Grid ── */
.heatmap-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
.heatmap-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
}
.heatmap-table th, .heatmap-table td {
    padding: 8px 12px;
    text-align: center;
    border: 1px solid var(--border-light);
}
.heatmap-table th {
    background: var(--bg-surface);
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
}
.heatmap-table th.row-header {
    text-align: left;
    min-width: 180px;
}
.heatmap-cell {
    position: relative;
    cursor: default;
    font-variant-numeric: tabular-nums;
    font-weight: 500;
}
.heatmap-cell .dev-pct {
    display: block;
    font-size: 0.65rem;
    opacity: 0.7;
    margin-top: 2px;
}
.heat-very_low { background: rgba(33,150,83,0.25); color: var(--success); }
.heat-low { background: rgba(33,150,83,0.12); }
.heat-neutral { background: transparent; }
.heat-high { background: rgba(235,87,87,0.12); }
.heat-very_high { background: rgba(235,87,87,0.25); color: var(--error); }
.heat-missing { background: var(--table-stripe); color: var(--text-muted); font-style: italic; }

/* ── Rate Analysis ── */
.rate-flag { color: var(--warning); font-weight: 700; }
.rate-ok { color: var(--success); }
.rate-range { font-size: 0.72rem; color: var(--text-muted); }

/* ── Red Flag Cards ── */
.rf-vendor-section { margin-bottom: 24px; }
.rf-vendor-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.rf-vendor-name { font-size: 1rem; font-weight: 700; }
.rf-count-badge {
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--error-bg);
    color: var(--error);
    font-weight: 600;
}
.rf-item {
    padding: 12px 16px;
    border-left: 3px solid var(--border-color);
    margin-bottom: 8px;
    border-radius: 0 var(--radius) var(--radius) 0;
    background: var(--bg-surface);
}
.rf-item.severity-critical { border-left-color: var(--error); }
.rf-item.severity-warning { border-left-color: var(--warning); }
.rf-item.severity-info { border-left-color: var(--info); }
.rf-title {
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.rf-detail { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }

/* ── Two-Column Layout ── */
.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

/* ── Tornado Chart Bars ── */
.tornado-bar-pos { fill: var(--error); opacity: 0.75; }
.tornado-bar-neg { fill: var(--success); opacity: 0.75; }
.tornado-bar-pos:hover, .tornado-bar-neg:hover { opacity: 1; }

/* ── Footer ── */
.footer {
    text-align: center;
    padding: 20px 0;
    font-size: 0.72rem;
    color: var(--text-muted);
    border-top: 1px solid var(--border-light);
    margin-top: 32px;
}

/* ── Print Styles ── */
@media print {
    body { background: white !important; color: #1a1a1a !important; }
    .header-right, .tab-nav, .filter-bar, .search-input { display: none !important; }
    .tab-panel { display: block !important; page-break-before: always; }
    .tab-panel:first-child { page-break-before: auto; }
    .section-card { box-shadow: none !important; border: 1px solid #ddd !important; page-break-inside: avoid; }
    .hero-card { border: 1px solid #ddd !important; }
    .app { max-width: 100%; padding: 0 12px; }
    .footer { position: static; }
    * { color: #1a1a1a !important; background: white !important; }
    .hero-value, .podium-amount, .section-title svg, .tab-btn.active { color: #8B6914 !important; }
    .heat-very_low, .heat-low, .heat-high, .heat-very_high { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}

/* ── Responsive ── */
@media (max-width: 768px) {
    .app { padding: 0 12px 12px; }
    .header { flex-direction: column; align-items: flex-start; }
    .header-titles h1 { font-size: 1.1rem; }
    .tab-nav { gap: 0; }
    .tab-btn { padding: 8px 10px; font-size: 0.75rem; }
    .tab-btn svg { display: none; }
    .two-col { grid-template-columns: 1fr; }
    .hero-grid { grid-template-columns: repeat(2, 1fr); }
    .scorecard-grid { grid-template-columns: 1fr; }
    .podium-grid { grid-template-columns: repeat(2, 1fr); }
    .search-input { width: 100%; }
}
'''


# ──────────────────────────────────────────────────────────
# JavaScript Generator
# ──────────────────────────────────────────────────────────

def _get_js() -> str:
    return r'''
/* ======================================================
   AEGIS Proposal Compare Export — Standalone JS
   ====================================================== */

// ── Data & State ──
const DATA = JSON.parse(document.getElementById('comparison-data').textContent);
const VENDOR_COLORS = ['#D6A84A','#2196f3','#219653','#f44336','#9b59b6','#e67e22','#1abc9c','#34495e','#e74c3c','#2ecc71'];
const GRADE_COLORS = { A: '#219653', B: '#56d68c', C: '#F2994A', D: '#e67e22', F: '#EB5757' };

let vendors = [];
let vendorColorMap = {};
let compState = {
    sortCol: null,
    sortDir: 'none',
    filterCats: new Set(),
    searchText: '',
};

// ── Utilities ──
function esc(s) {
    if (s == null) return '';
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
}

function fmt(n) {
    if (n == null || isNaN(n)) return '--';
    return '$' + Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtShort(n) {
    if (n == null || isNaN(n)) return '--';
    if (Math.abs(n) >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (Math.abs(n) >= 1e3) return '$' + (n / 1e3).toFixed(0) + 'K';
    return '$' + Number(n).toFixed(0);
}

function fmtPct(n) {
    if (n == null || isNaN(n)) return '--';
    return Number(n).toFixed(1) + '%';
}

function vendorColor(v) {
    return vendorColorMap[v] || '#888';
}

// ── Theme Toggle ──
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    document.getElementById('icon-sun').style.display = isDark ? 'none' : '';
    document.getElementById('icon-moon').style.display = isDark ? '' : 'none';
    try { localStorage.setItem('aegis-pc-theme', newTheme); } catch(e) {}
}

function initTheme() {
    try {
        const saved = localStorage.getItem('aegis-pc-theme');
        if (saved) {
            document.documentElement.setAttribute('data-theme', saved);
            document.getElementById('icon-sun').style.display = saved === 'dark' ? '' : 'none';
            document.getElementById('icon-moon').style.display = saved === 'dark' ? 'none' : '';
        }
    } catch(e) {}
}

// ── Tab Switching ──
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tabId));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + tabId));
    try { history.replaceState(null, '', '#' + tabId); } catch(e) {}
}

// ── Animated Count-Up ──
function animateValue(el, target, prefix, suffix, duration) {
    if (target == null || isNaN(target)) { el.textContent = '--'; return; }
    const start = performance.now();
    const isFloat = String(target).includes('.') || Math.abs(target) > 999;
    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // easeOutCubic
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = target * ease;
        if (Math.abs(target) >= 1000) {
            el.textContent = (prefix || '') + Number(current).toLocaleString('en-US', {
                minimumFractionDigits: target >= 100 ? 0 : 2,
                maximumFractionDigits: target >= 100 ? 0 : 2
            }) + (suffix || '');
        } else {
            el.textContent = (prefix || '') + (isFloat ? current.toFixed(1) : Math.round(current)) + (suffix || '');
        }
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ── Table Sorting ──
function sortTable(tableId, colIdx, dataType) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const headers = table.querySelectorAll('th');
    const currentDir = headers[colIdx].dataset.sortDir || 'none';
    let newDir = 'asc';
    if (currentDir === 'asc') newDir = 'desc';
    else if (currentDir === 'desc') newDir = 'none';

    // Reset all headers
    headers.forEach(h => { h.dataset.sortDir = 'none'; h.classList.remove('sorted'); });

    if (newDir === 'none') {
        renderComparisonMatrix();
        return;
    }

    headers[colIdx].dataset.sortDir = newDir;
    headers[colIdx].classList.add('sorted');

    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr:not(.total-row)'));

    rows.sort((a, b) => {
        let aVal = a.cells[colIdx]?.textContent?.trim() || '';
        let bVal = b.cells[colIdx]?.textContent?.trim() || '';
        if (dataType === 'number') {
            aVal = parseFloat(aVal.replace(/[$,%]/g, '')) || 0;
            bVal = parseFloat(bVal.replace(/[$,%]/g, '')) || 0;
        } else {
            aVal = aVal.toLowerCase();
            bVal = bVal.toLowerCase();
        }
        if (aVal < bVal) return newDir === 'asc' ? -1 : 1;
        if (aVal > bVal) return newDir === 'asc' ? 1 : -1;
        return 0;
    });

    // Preserve total row
    const totalRow = tbody.querySelector('.total-row');
    rows.forEach(r => tbody.appendChild(r));
    if (totalRow) tbody.appendChild(totalRow);

    // Update arrows
    const arrow = headers[colIdx].querySelector('.sort-arrow');
    if (arrow) arrow.textContent = newDir === 'asc' ? '\u25B2' : '\u25BC';
}

// ── Tooltip ──
const tooltip = document.createElement('div');
tooltip.className = 'chart-tooltip';
document.body.appendChild(tooltip);

function showTooltip(e, html) {
    tooltip.innerHTML = html;
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 12) + 'px';
    tooltip.style.top = (e.clientY - 8) + 'px';
}
function hideTooltip() { tooltip.style.display = 'none'; }

// ══════════════════════════════════════════════
// EXECUTIVE DASHBOARD
// ══════════════════════════════════════════════

function renderExecutive() {
    const panel = document.getElementById('panel-executive');
    const exec = DATA.executive_summary || {};
    const totals = DATA.totals || {};
    const validTotals = Object.entries(totals).filter(([,v]) => v != null && v > 0);
    const avgCost = validTotals.length ? validTotals.reduce((s,[,v]) => s + v, 0) / validTotals.length : 0;
    const minCost = validTotals.length ? Math.min(...validTotals.map(([,v]) => v)) : 0;
    const maxCost = validTotals.length ? Math.max(...validTotals.map(([,v]) => v)) : 0;
    const spread = maxCost - minCost;
    const totalItems = (DATA.aligned_items || []).length;

    let html = `
    <div class="hero-grid">
        <div class="hero-card">
            <div class="hero-value" data-count="${vendors.length}">${vendors.length}</div>
            <div class="hero-label">Proposals Compared</div>
        </div>
        <div class="hero-card">
            <div class="hero-value" data-count="${totalItems}">${totalItems}</div>
            <div class="hero-label">Aligned Line Items</div>
        </div>
        <div class="hero-card">
            <div class="hero-value" data-count="${avgCost}" data-prefix="$">${fmtShort(avgCost)}</div>
            <div class="hero-label">Average Total Cost</div>
        </div>
        <div class="hero-card">
            <div class="hero-value" data-count="${spread}" data-prefix="$">${fmtShort(spread)}</div>
            <div class="hero-label">Cost Spread</div>
            <div class="hero-sub">${fmtPct(DATA.total_variance_pct)} variance</div>
        </div>
    </div>`;

    // Price Ranking Podium
    const ranking = exec.price_ranking || [];
    if (ranking.length) {
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15l-3-3h6l-3 3z"/><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
            Price Ranking</div><div class="podium-grid">`;
        ranking.forEach((r, i) => {
            const labels = ['Lowest Bidder', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th'];
            html += `<div class="podium-card rank-${i + 1}">
                <div class="podium-rank">${labels[i] || '#' + (i+1)}</div>
                <div class="podium-vendor">${esc(r.vendor)}</div>
                <div class="podium-amount">${fmt(r.total)}</div>
                ${i > 0 ? `<div class="podium-delta">+${fmt(r.delta_from_lowest)} (+${fmtPct(r.delta_pct)})</div>` : ''}
            </div>`;
        });
        html += `</div></div>`;
    }

    // Tornado Chart
    if (validTotals.length >= 2) {
        html += `<div class="section-card">
            <div class="section-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="22" height="5" rx="2"/><rect x="5" y="10" width="14" height="5" rx="2"/><rect x="8" y="17" width="8" height="5" rx="2"/></svg>
                Cost Comparison</div>
            <div class="chart-container" id="tornado-chart"></div>
        </div>`;
    }

    // Key Findings
    const findings = exec.key_findings || [];
    if (findings.length) {
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            Key Findings</div>`;
        findings.forEach(f => {
            html += `<div class="finding-item">
                <span class="finding-badge badge-${f.severity || 'info'}">${esc(f.severity || 'info')}</span>
                <span class="finding-text">${esc(f.text)}</span>
            </div>`;
        });
        html += `</div>`;
    }

    // Negotiation Opportunities
    const opps = exec.negotiation_opportunities || [];
    if (opps.length) {
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Negotiation Opportunities</div>`;
        if (exec.total_potential_savings_formatted) {
            html += `<p style="margin-bottom:12px;font-size:0.85rem;color:var(--text-secondary)">Total potential savings: <strong style="color:var(--success)">${esc(exec.total_potential_savings_formatted)}</strong></p>`;
        }
        html += `<div class="table-wrapper"><table class="data-table">
            <thead><tr><th>Vendor</th><th>Line Item</th><th class="text-right">Current</th><th class="text-right">Avg</th><th class="text-right">Potential Savings</th><th class="text-right">Variance</th></tr></thead><tbody>`;
        opps.forEach(o => {
            html += `<tr>
                <td>${esc(o.vendor)}</td>
                <td>${esc(o.line_item)}</td>
                <td class="text-right amount">${fmt(o.current_amount)}</td>
                <td class="text-right amount">${fmt(o.avg_amount)}</td>
                <td class="text-right amount amount-lowest">${esc(o.savings_formatted)}</td>
                <td class="text-right variance-cell">${fmtPct(o.variance_pct)}</td>
            </tr>`;
        });
        html += `</tbody></table></div></div>`;
    }

    panel.innerHTML = html;

    // Animate hero values
    panel.querySelectorAll('.hero-value[data-count]').forEach(el => {
        const target = parseFloat(el.dataset.count);
        const prefix = el.dataset.prefix || '';
        if (!isNaN(target) && target > 0) {
            animateValue(el, target, prefix, '', 1200);
        }
    });

    // Render tornado chart
    if (validTotals.length >= 2) renderTornadoChart(validTotals, avgCost);
}

function renderTornadoChart(validTotals, avg) {
    const container = document.getElementById('tornado-chart');
    if (!container) return;
    const sorted = [...validTotals].sort((a, b) => b[1] - a[1]);
    const maxDelta = Math.max(...sorted.map(([,v]) => Math.abs(v - avg)));
    const barH = 36;
    const gap = 6;
    const labelW = 140;
    const valueW = 90;
    const chartW = 500;
    const totalW = labelW + chartW + valueW + 20;
    const totalH = sorted.length * (barH + gap) + 20;
    const midX = labelW + chartW / 2;

    let svg = `<svg viewBox="0 0 ${totalW} ${totalH}" xmlns="http://www.w3.org/2000/svg">`;
    // Center line
    svg += `<line x1="${midX}" y1="0" x2="${midX}" y2="${totalH}" stroke="var(--border-color)" stroke-width="1" stroke-dasharray="4,4"/>`;

    sorted.forEach(([vendor, total], i) => {
        const y = i * (barH + gap) + 10;
        const delta = total - avg;
        const barWidth = maxDelta > 0 ? (Math.abs(delta) / maxDelta) * (chartW / 2 - 10) : 0;
        const cls = delta >= 0 ? 'tornado-bar-pos' : 'tornado-bar-neg';
        const barX = delta >= 0 ? midX : midX - barWidth;

        svg += `<text x="${labelW - 8}" y="${y + barH / 2 + 4}" text-anchor="end" fill="var(--text-primary)" font-size="12" font-weight="600">${esc(vendor)}</text>`;
        svg += `<rect class="${cls}" x="${barX}" y="${y}" width="${barWidth}" height="${barH}" rx="4"
                    onmousemove="showTooltip(event, '${esc(vendor)}: ${fmt(total).replace("'", "\\'")} (${delta >= 0 ? '+' : ''}${fmtShort(delta).replace("'", "\\'")} vs avg)')"
                    onmouseleave="hideTooltip()"/>`;
        svg += `<text x="${labelW + chartW + 8}" y="${y + barH / 2 + 4}" fill="var(--text-secondary)" font-size="11" font-weight="500">${fmtShort(total)}</text>`;
    });

    // Avg label
    svg += `<text x="${midX}" y="${totalH - 2}" text-anchor="middle" fill="var(--text-muted)" font-size="10">AVG ${fmtShort(avg)}</text>`;
    svg += `</svg>`;
    container.innerHTML = svg;
}

// ══════════════════════════════════════════════
// COMPARISON MATRIX
// ══════════════════════════════════════════════

function renderComparisonMatrix() {
    const panel = document.getElementById('panel-comparison');
    const items = DATA.aligned_items || [];
    const totals = DATA.totals || {};
    const allCats = [...new Set(items.map(i => i.category || 'Uncategorized'))].sort();

    // Filter bar
    let html = `<div class="filter-bar">
        <input type="text" class="search-input" placeholder="Search descriptions..." oninput="compState.searchText=this.value.toLowerCase();filterCompMatrix();" value="${esc(compState.searchText)}">`;
    allCats.forEach(cat => {
        const active = compState.filterCats.has(cat) ? 'active' : '';
        html += `<span class="filter-chip ${active}" onclick="toggleCatFilter('${esc(cat)}')">${esc(cat)}</span>`;
    });
    html += `<span class="filter-count" id="comp-filter-count"></span></div>`;

    // Table
    html += `<div class="table-wrapper"><table class="data-table" id="comp-table"><thead><tr>
        <th onclick="sortTable('comp-table',0,'text')">Description <span class="sort-arrow">&#9650;</span></th>
        <th onclick="sortTable('comp-table',1,'text')">Category <span class="sort-arrow">&#9650;</span></th>`;
    vendors.forEach((v, vi) => {
        html += `<th class="text-right" onclick="sortTable('comp-table',${vi + 2},'number')">${esc(v)} <span class="sort-arrow">&#9650;</span></th>`;
    });
    html += `<th class="text-right" onclick="sortTable('comp-table',${vendors.length + 2},'number')">Variance <span class="sort-arrow">&#9650;</span></th>`;
    html += `</tr></thead><tbody>`;

    // Filter items
    let filtered = items;
    if (compState.filterCats.size > 0) {
        filtered = filtered.filter(it => compState.filterCats.has(it.category || 'Uncategorized'));
    }
    if (compState.searchText) {
        filtered = filtered.filter(it => (it.description || '').toLowerCase().includes(compState.searchText));
    }

    filtered.forEach(item => {
        const amounts = item.amounts || {};
        const validAmts = Object.values(amounts).filter(a => a != null && a > 0);
        const minA = validAmts.length ? Math.min(...validAmts) : null;
        const maxA = validAmts.length ? Math.max(...validAmts) : null;

        html += `<tr><td>${esc(item.description)}</td><td>${esc(item.category || 'Uncategorized')}</td>`;
        vendors.forEach(v => {
            const a = amounts[v];
            let cls = 'amount';
            if (a != null && validAmts.length > 1) {
                if (a === minA) cls += ' amount-lowest';
                else if (a === maxA) cls += ' amount-highest';
            }
            html += `<td class="text-right ${cls}">${a != null ? fmt(a) : '--'}</td>`;
        });
        const vpc = item.variance_pct;
        let varClass = 'variance-cell';
        if (vpc != null && vpc > 50) varClass += ' amount-highest';
        else if (vpc != null && vpc > 20) varClass += ' rate-flag';
        html += `<td class="text-right ${varClass}">${vpc != null ? fmtPct(vpc) : '--'}</td>`;
        html += `</tr>`;
    });

    // Grand total row
    html += `<tr class="total-row"><td><strong>GRAND TOTAL</strong></td><td></td>`;
    vendors.forEach(v => {
        html += `<td class="text-right amount"><strong>${fmt(totals[v])}</strong></td>`;
    });
    const tVpc = DATA.total_variance_pct;
    html += `<td class="text-right variance-cell"><strong>${tVpc != null ? fmtPct(tVpc) : '--'}</strong></td>`;
    html += `</tr></tbody></table></div>`;

    panel.innerHTML = html;
    document.getElementById('comp-filter-count').textContent = `Showing ${filtered.length} of ${items.length} items`;
}

function toggleCatFilter(cat) {
    if (compState.filterCats.has(cat)) compState.filterCats.delete(cat);
    else compState.filterCats.add(cat);
    renderComparisonMatrix();
}

function filterCompMatrix() { renderComparisonMatrix(); }

// ══════════════════════════════════════════════
// CATEGORY ANALYSIS
// ══════════════════════════════════════════════

function renderCategories() {
    const panel = document.getElementById('panel-categories');
    const cats = DATA.category_summaries || [];
    const totals = DATA.totals || {};
    const grandTotal = Object.values(totals).filter(v => v != null).reduce((s, v) => s + v, 0) / vendors.length || 1;

    let html = `<div class="two-col">`;

    // Stacked Bar Chart
    html += `<div class="section-card">
        <div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="3" width="22" height="5" rx="2"/><rect x="1" y="10" width="16" height="5" rx="2"/><rect x="1" y="17" width="10" height="5" rx="2"/></svg>
            Category Distribution by Vendor</div>
        <div class="chart-container" id="stacked-chart"></div>
        <div class="chart-legend" id="stacked-legend"></div>
    </div>`;

    // Donut Chart
    html += `<div class="section-card">
        <div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg>
            Overall Category Split</div>
        <div class="chart-container" id="donut-chart"></div>
    </div>`;

    html += `</div>`;

    // Category Table
    html += `<div class="section-card"><div class="section-title">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg>
        Category Breakdown</div>
    <div class="table-wrapper"><table class="data-table" id="cat-table"><thead><tr>
        <th>Category</th><th class="text-center">Items</th>`;
    vendors.forEach(v => { html += `<th class="text-right">${esc(v)}</th>`; });
    html += `</tr></thead><tbody>`;

    cats.forEach(c => {
        html += `<tr><td><strong>${esc(c.category)}</strong></td><td class="text-center">${c.item_count || 0}</td>`;
        vendors.forEach(v => {
            html += `<td class="text-right amount">${fmt(c.totals ? c.totals[v] : null)}</td>`;
        });
        html += `</tr>`;
    });
    html += `</tbody></table></div></div>`;

    panel.innerHTML = html;
    renderStackedBarChart(cats);
    renderDonutChart(cats);
}

function renderStackedBarChart(cats) {
    const container = document.getElementById('stacked-chart');
    const legend = document.getElementById('stacked-legend');
    if (!container || !cats.length) return;

    // Find max total across categories for scaling
    let maxCatTotal = 0;
    cats.forEach(c => {
        const catTotal = vendors.reduce((s, v) => s + ((c.totals || {})[v] || 0), 0);
        if (catTotal > maxCatTotal) maxCatTotal = catTotal;
    });
    if (maxCatTotal === 0) maxCatTotal = 1;

    const barH = 28;
    const gap = 8;
    const labelW = 120;
    const chartW = 400;
    const totalW = labelW + chartW + 80;
    const totalH = cats.length * (barH + gap) + 10;

    let svg = `<svg viewBox="0 0 ${totalW} ${totalH}" xmlns="http://www.w3.org/2000/svg">`;

    cats.forEach((c, ci) => {
        const y = ci * (barH + gap) + 5;
        let xOffset = labelW;
        const catLabel = c.category || 'Other';

        svg += `<text x="${labelW - 8}" y="${y + barH / 2 + 4}" text-anchor="end" fill="var(--text-secondary)" font-size="11">${esc(catLabel.length > 14 ? catLabel.slice(0, 13) + '...' : catLabel)}</text>`;

        vendors.forEach((v, vi) => {
            const amt = (c.totals || {})[v] || 0;
            const w = (amt / maxCatTotal) * chartW;
            if (w > 0.5) {
                svg += `<rect x="${xOffset}" y="${y}" width="${w}" height="${barH}" fill="${vendorColor(v)}" rx="2" opacity="0.85"
                    onmousemove="showTooltip(event, '${esc(v)}: ${fmt(amt).replace("'", "\\'")} in ${esc(catLabel).replace("'", "\\'")}')"
                    onmouseleave="hideTooltip()"/>`;
            }
            xOffset += w;
        });

        const catTotal = vendors.reduce((s, v) => s + ((c.totals || {})[v] || 0), 0);
        svg += `<text x="${xOffset + 6}" y="${y + barH / 2 + 4}" fill="var(--text-muted)" font-size="10">${fmtShort(catTotal)}</text>`;
    });

    svg += `</svg>`;
    container.innerHTML = svg;

    // Legend
    legend.innerHTML = vendors.map(v =>
        `<span class="legend-item"><span class="legend-swatch" style="background:${vendorColor(v)}"></span>${esc(v)}</span>`
    ).join('');
}

function renderDonutChart(cats) {
    const container = document.getElementById('donut-chart');
    if (!container || !cats.length) return;

    // Aggregate across all vendors per category
    const catTotals = cats.map(c => ({
        category: c.category || 'Other',
        total: vendors.reduce((s, v) => s + ((c.totals || {})[v] || 0), 0)
    })).filter(c => c.total > 0);

    const grandTotal = catTotals.reduce((s, c) => s + c.total, 0) || 1;
    const catColors = ['#D6A84A','#2196f3','#219653','#f44336','#9b59b6','#e67e22','#1abc9c','#34495e','#e74c3c','#2ecc71','#8e44ad','#3498db'];

    const size = 240;
    const cx = size / 2;
    const cy = size / 2;
    const outerR = 100;
    const innerR = 55;

    let svg = `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" style="max-width:${size}px;margin:0 auto">`;

    let startAngle = -Math.PI / 2;
    catTotals.forEach((ct, i) => {
        const sliceAngle = (ct.total / grandTotal) * 2 * Math.PI;
        const endAngle = startAngle + sliceAngle;
        const largeArc = sliceAngle > Math.PI ? 1 : 0;

        const x1o = cx + outerR * Math.cos(startAngle);
        const y1o = cy + outerR * Math.sin(startAngle);
        const x2o = cx + outerR * Math.cos(endAngle);
        const y2o = cy + outerR * Math.sin(endAngle);
        const x1i = cx + innerR * Math.cos(endAngle);
        const y1i = cy + innerR * Math.sin(endAngle);
        const x2i = cx + innerR * Math.cos(startAngle);
        const y2i = cy + innerR * Math.sin(startAngle);

        const color = catColors[i % catColors.length];
        const pct = (ct.total / grandTotal * 100).toFixed(1);

        svg += `<path d="M${x1o},${y1o} A${outerR},${outerR} 0 ${largeArc} 1 ${x2o},${y2o} L${x1i},${y1i} A${innerR},${innerR} 0 ${largeArc} 0 ${x2i},${y2i} Z"
            fill="${color}" opacity="0.85" stroke="var(--bg-card)" stroke-width="2"
            onmousemove="showTooltip(event, '${esc(ct.category).replace("'","\\'")} — ${fmtShort(ct.total).replace("'","\\'")} (${pct}%)')"
            onmouseleave="hideTooltip()"/>`;

        startAngle = endAngle;
    });

    // Center text
    svg += `<text x="${cx}" y="${cy - 6}" text-anchor="middle" fill="var(--text-primary)" font-size="16" font-weight="800">${catTotals.length}</text>`;
    svg += `<text x="${cx}" y="${cy + 12}" text-anchor="middle" fill="var(--text-muted)" font-size="10">CATEGORIES</text>`;
    svg += `</svg>`;

    // Legend
    svg += `<div class="chart-legend" style="margin-top:16px">`;
    catTotals.forEach((ct, i) => {
        const pct = (ct.total / grandTotal * 100).toFixed(1);
        svg += `<span class="legend-item"><span class="legend-swatch" style="background:${catColors[i % catColors.length]}"></span>${esc(ct.category)} (${pct}%)</span>`;
    });
    svg += `</div>`;

    container.innerHTML = svg;
}

// ══════════════════════════════════════════════
// VENDOR SCORECARD
// ══════════════════════════════════════════════

function renderScorecard() {
    const panel = document.getElementById('panel-scorecard');
    const scores = DATA.vendor_scores || {};
    const sortedVendors = Object.entries(scores).sort((a, b) => b[1].overall - a[1].overall);

    if (!sortedVendors.length) {
        panel.innerHTML = `<div class="section-card"><p style="color:var(--text-muted)">No vendor scores available.</p></div>`;
        return;
    }

    // Grade Cards
    let html = `<div class="scorecard-grid">`;
    sortedVendors.forEach(([vendor, s]) => {
        const gc = GRADE_COLORS[s.grade] || '#888';
        const barColor = vendorColor(vendor);
        const components = [
            { label: 'Price', value: s.price_score, weight: '40%' },
            { label: 'Completeness', value: s.completeness_score, weight: '25%' },
            { label: 'Risk', value: s.risk_score, weight: '25%' },
            { label: 'Data Quality', value: s.data_quality_score, weight: '10%' },
        ];
        html += `<div class="score-card grade-${s.grade}">
            <div class="score-header">
                <div class="score-vendor-name">${esc(vendor)}</div>
                <div>
                    <div class="score-grade-badge" style="background:${gc}">${s.grade}</div>
                    <div class="score-overall">${s.overall}/100</div>
                </div>
            </div>`;
        components.forEach(c => {
            const fillPct = Math.min(100, Math.max(0, c.value || 0));
            html += `<div class="score-bar-group">
                <div class="score-bar-label"><span>${c.label} (${c.weight})</span><span>${c.value}/100</span></div>
                <div class="score-bar-track"><div class="score-bar-fill" style="width:${fillPct}%;background:${barColor}"></div></div>
            </div>`;
        });
        if (s.red_flag_count > 0) {
            html += `<div class="score-flags">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--warning)" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                ${s.red_flag_count} red flag${s.red_flag_count > 1 ? 's' : ''}${s.critical_flags ? ` (${s.critical_flags} critical)` : ''}
            </div>`;
        }
        html += `</div>`;
    });
    html += `</div>`;

    // Radar Chart
    html += `<div class="section-card">
        <div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5"/></svg>
            Component Score Comparison</div>
        <div class="chart-container" id="radar-chart"></div>
        <div class="chart-legend" id="radar-legend"></div>
    </div>`;

    panel.innerHTML = html;
    renderRadarChart(sortedVendors);
}

function renderRadarChart(sortedVendors) {
    const container = document.getElementById('radar-chart');
    const legend = document.getElementById('radar-legend');
    if (!container || !sortedVendors.length) return;

    const axes = ['Price', 'Completeness', 'Risk', 'Data Quality'];
    const keys = ['price_score', 'completeness_score', 'risk_score', 'data_quality_score'];
    const numAxes = axes.length;
    const size = 320;
    const cx = size / 2;
    const cy = size / 2;
    const maxR = 120;
    const angleStep = (2 * Math.PI) / numAxes;
    const startAngle = -Math.PI / 2;

    let svg = `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg" style="max-width:${size}px;margin:0 auto">`;

    // Grid rings
    [20, 40, 60, 80, 100].forEach(level => {
        const r = (level / 100) * maxR;
        let points = [];
        for (let i = 0; i < numAxes; i++) {
            const angle = startAngle + i * angleStep;
            points.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
        }
        svg += `<polygon points="${points.join(' ')}" fill="none" stroke="var(--border-light)" stroke-width="1"/>`;
    });

    // Axis lines + labels
    for (let i = 0; i < numAxes; i++) {
        const angle = startAngle + i * angleStep;
        const x = cx + maxR * Math.cos(angle);
        const y = cy + maxR * Math.sin(angle);
        svg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="var(--border-color)" stroke-width="1"/>`;

        const lx = cx + (maxR + 20) * Math.cos(angle);
        const ly = cy + (maxR + 20) * Math.sin(angle);
        const anchor = Math.abs(Math.cos(angle)) < 0.1 ? 'middle' : (Math.cos(angle) > 0 ? 'start' : 'end');
        svg += `<text x="${lx}" y="${ly + 4}" text-anchor="${anchor}" fill="var(--text-secondary)" font-size="11" font-weight="600">${axes[i]}</text>`;
    }

    // Vendor polygons
    sortedVendors.forEach(([vendor, scores], vi) => {
        let points = [];
        for (let i = 0; i < numAxes; i++) {
            const angle = startAngle + i * angleStep;
            const val = (scores[keys[i]] || 0) / 100;
            const r = val * maxR;
            points.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
        }
        const color = vendorColor(vendor);
        svg += `<polygon points="${points.join(' ')}" fill="${color}" fill-opacity="0.15" stroke="${color}" stroke-width="2.5"/>`;

        // Data points
        for (let i = 0; i < numAxes; i++) {
            const angle = startAngle + i * angleStep;
            const val = (scores[keys[i]] || 0) / 100;
            const r = val * maxR;
            const px = cx + r * Math.cos(angle);
            const py = cy + r * Math.sin(angle);
            svg += `<circle cx="${px}" cy="${py}" r="4" fill="${color}" stroke="var(--bg-card)" stroke-width="2"
                onmousemove="showTooltip(event, '${esc(vendor).replace("'","\\'")} — ${axes[i]}: ${scores[keys[i]]}/100')"
                onmouseleave="hideTooltip()"/>`;
        }
    });

    svg += `</svg>`;
    container.innerHTML = svg;

    legend.innerHTML = sortedVendors.map(([v]) =>
        `<span class="legend-item"><span class="legend-swatch" style="background:${vendorColor(v)}"></span>${esc(v)}</span>`
    ).join('');
}

// ══════════════════════════════════════════════
// RISK ANALYSIS
// ══════════════════════════════════════════════

function renderRisk() {
    const panel = document.getElementById('panel-risk');
    const flags = DATA.red_flags || {};
    const heatmap = DATA.heatmap || {};

    let html = '';

    // Red Flags per Vendor
    const vendorsWithFlags = vendors.filter(v => (flags[v] || []).length > 0);
    if (vendorsWithFlags.length) {
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>
            Red Flags by Vendor</div>`;

        vendorsWithFlags.forEach(v => {
            const vf = flags[v] || [];
            const crits = vf.filter(f => f.severity === 'critical').length;
            const warns = vf.filter(f => f.severity === 'warning').length;

            html += `<div class="rf-vendor-section">
                <div class="rf-vendor-header">
                    <span class="rf-vendor-name" style="color:${vendorColor(v)}">${esc(v)}</span>
                    <span class="rf-count-badge">${vf.length} flag${vf.length > 1 ? 's' : ''}${crits ? ' (' + crits + ' critical)' : ''}</span>
                </div>`;

            // Sort by severity
            const sevOrder = { critical: 0, warning: 1, info: 2 };
            const sorted = [...vf].sort((a, b) => (sevOrder[a.severity] || 3) - (sevOrder[b.severity] || 3));
            sorted.forEach(f => {
                html += `<div class="rf-item severity-${f.severity || 'info'}">
                    <div class="rf-title">
                        <span class="finding-badge badge-${f.severity || 'info'}">${esc(f.severity || 'info')}</span>
                        ${esc(f.title)}
                    </div>
                    <div class="rf-detail">${esc(f.detail)}</div>
                </div>`;
            });
            html += `</div>`;
        });
        html += `</div>`;
    } else {
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            No Red Flags Detected</div>
            <p style="color:var(--text-secondary);font-size:0.85rem">All proposals passed automated risk checks.</p>
        </div>`;
    }

    // Heatmap
    const heatRows = heatmap.rows || [];
    if (heatRows.length) {
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
            Price Deviation Heatmap</div>
        <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:12px">
            Green = below average, Red = above average. Hover for details.</p>
        <div class="heatmap-wrapper"><table class="heatmap-table"><thead><tr>
            <th class="row-header">Line Item</th>`;
        vendors.forEach(v => { html += `<th>${esc(v)}</th>`; });
        html += `<th>Avg</th></tr></thead><tbody>`;

        heatRows.forEach(row => {
            html += `<tr><td class="row-header" title="${esc(row.description)}">${esc((row.description || '').slice(0, 40))}${(row.description || '').length > 40 ? '...' : ''}</td>`;
            vendors.forEach(v => {
                const cell = (row.cells || {})[v] || {};
                const level = cell.level || 'missing';
                const devPct = cell.deviation_pct;
                html += `<td class="heatmap-cell heat-${level}"
                    onmousemove="showTooltip(event, '${esc(v).replace("'","\\'")} — ${esc(row.description).replace("'","\\'")}:\\n${cell.amount != null ? fmt(cell.amount).replace("'","\\'") : 'N/A'} (${devPct != null ? (devPct > 0 ? '+' : '') + devPct + '% vs avg' : 'missing'})')"
                    onmouseleave="hideTooltip()">
                    ${cell.amount != null ? fmtShort(cell.amount) : '--'}
                    ${devPct != null ? '<span class="dev-pct">' + (devPct > 0 ? '+' : '') + devPct + '%</span>' : ''}
                </td>`;
            });
            html += `<td class="text-center" style="color:var(--text-muted);font-size:0.75rem">${fmtShort(row.avg)}</td>`;
            html += `</tr>`;
        });

        html += `</tbody></table></div></div>`;
    }

    panel.innerHTML = html;
}

// ══════════════════════════════════════════════
// RATE ANALYSIS
// ══════════════════════════════════════════════

function renderRates() {
    const panel = document.getElementById('panel-rates');
    const indirect = DATA.indirect_rates || {};
    const rateAnalysis = DATA.rate_analysis || {};

    let html = '';

    // Indirect Rates Table
    const comparison = indirect.comparison || [];
    if (comparison.length) {
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            Indirect Rate Comparison</div>
        <div class="table-wrapper"><table class="data-table"><thead><tr>
            <th>Rate Type</th><th>Typical Range</th>`;
        vendors.forEach(v => { html += `<th class="text-right">${esc(v)}</th>`; });
        html += `</tr></thead><tbody>`;

        comparison.forEach(row => {
            const range = row.typical_range || [0, 100];
            html += `<tr><td><strong>${esc(row.rate_type)}</strong></td>
                <td class="rate-range">${range[0]}% - ${range[1]}%</td>`;
            vendors.forEach(v => {
                const vr = (row.vendors || {})[v];
                if (vr) {
                    const rate = vr.implied_rate_pct;
                    const outside = vr.outside_range;
                    const cls = outside ? 'rate-flag' : 'rate-ok';
                    html += `<td class="text-right ${cls}">
                        ${vr.amount_formatted || '--'}
                        ${rate != null ? '<br><span style="font-size:0.72rem">(' + rate + '%)</span>' : ''}
                        ${outside ? ' <span title="Outside typical range">&#9888;</span>' : ''}
                    </td>`;
                } else {
                    html += `<td class="text-right" style="color:var(--text-muted)">--</td>`;
                }
            });
            html += `</tr>`;
        });
        html += `</tbody></table></div></div>`;
    }

    // Unit Rate Analysis
    const rateItems = (rateAnalysis.items || []);
    if (rateItems.length) {
        const rateSummary = rateAnalysis.summary || {};
        html += `<div class="section-card"><div class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
            Unit Rate Comparison</div>
        <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:12px">
            ${rateSummary.total_rate_items || 0} items with unit rates compared.
            ${rateSummary.items_with_variance_over_20 || 0} have >20% variance.</p>
        <div class="table-wrapper"><table class="data-table"><thead><tr>
            <th>Description</th><th>Category</th>`;
        vendors.forEach(v => { html += `<th class="text-right">${esc(v)}</th>`; });
        html += `<th class="text-right">Variance</th></tr></thead><tbody>`;

        rateItems.slice(0, 30).forEach(item => {
            html += `<tr><td>${esc(item.description)}</td><td>${esc(item.category || '')}</td>`;
            const rates = item.rates || {};
            const rateValues = Object.values(rates).filter(r => r > 0);
            const minRate = rateValues.length ? Math.min(...rateValues) : null;
            const maxRate = rateValues.length ? Math.max(...rateValues) : null;

            vendors.forEach(v => {
                const r = rates[v];
                let cls = 'amount';
                if (r != null && rateValues.length > 1) {
                    if (r === minRate) cls += ' amount-lowest';
                    else if (r === maxRate) cls += ' amount-highest';
                }
                html += `<td class="text-right ${cls}">${r != null ? fmt(r) : '--'}</td>`;
            });

            let varCls = 'variance-cell';
            if (item.variance_pct > 50) varCls += ' amount-highest';
            else if (item.variance_pct > 20) varCls += ' rate-flag';
            html += `<td class="text-right ${varCls}">${fmtPct(item.variance_pct)}</td>`;
            html += `</tr>`;
        });
        html += `</tbody></table></div></div>`;
    }

    if (!comparison.length && !rateItems.length) {
        html += `<div class="section-card"><p style="color:var(--text-muted)">No rate data available for comparison.</p></div>`;
    }

    panel.innerHTML = html;
}

// ══════════════════════════════════════════════
// INITIALIZATION
// ══════════════════════════════════════════════

function init() {
    initTheme();

    // Build vendor list
    const proposals = DATA.proposals || [];
    vendors = proposals.map(p => p.id || p.company_name || p.filename);

    // Build vendor color map
    vendors.forEach((v, i) => { vendorColorMap[v] = VENDOR_COLORS[i % VENDOR_COLORS.length]; });

    // Show/hide rates tab
    const indirect = DATA.indirect_rates || {};
    const rateAnalysis = DATA.rate_analysis || {};
    if ((indirect.has_data) || ((rateAnalysis.items || []).length > 0)) {
        document.getElementById('tab-btn-rates').style.display = '';
    }

    // Render all tabs
    renderExecutive();
    renderComparisonMatrix();
    renderCategories();
    renderScorecard();
    renderRisk();
    renderRates();

    // Handle hash navigation
    const hash = window.location.hash.replace('#', '');
    if (hash && document.getElementById('panel-' + hash)) {
        switchTab(hash);
    }
}

document.addEventListener('DOMContentLoaded', init);
'''


# ──────────────────────────────────────────────────────────
# Convenience: generate + save to file
# ──────────────────────────────────────────────────────────

def export_proposal_compare_html(comparison_data: dict, filepath: str) -> str:
    """Generate HTML and write to file. Returns the filepath."""
    html = generate_proposal_compare_html(comparison_data)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return filepath
