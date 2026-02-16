"""
AEGIS Hierarchy Export - Interactive HTML Generator

Generates a standalone interactive HTML file for visualizing role hierarchies,
organizational structure, and role relationships. Supports Dashboard, Tree View,
Graph View, and Table View with filtering, search, and dark/light mode.

Usage:
    from hierarchy_export import generate_hierarchy_html
    html = generate_hierarchy_html(roles, relationships, hierarchy, filters, metadata)
"""

import json
import html as html_module
from datetime import datetime, timezone
from typing import List, Dict, Optional
import socket


def generate_hierarchy_html(
    roles: List[Dict],
    relationships: List[Dict],
    hierarchy: Dict,
    filters: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> str:
    """
    Generate a standalone interactive HTML file for role hierarchy visualization.

    Args:
        roles: List of role dicts from db.get_role_dictionary(include_inactive=True).
        relationships: List of relationship dicts from db.get_role_relationships().
        hierarchy: Dict from db.get_role_hierarchy() with nodes, edges, roots, etc.
        filters: Optional dict with org_groups, dispositions, role_types, etc.
        metadata: Optional dict with app_version, export_date, filters_applied.

    Returns:
        Complete HTML string (standalone, no external dependencies).
    """
    if metadata is None:
        metadata = {}
    if filters is None:
        filters = {}

    # Apply filters to data before embedding
    filtered_roles, filtered_relationships = _apply_filters(roles, relationships, filters)

    version = metadata.get('app_version', '4.1.0')
    export_date = metadata.get('export_date', datetime.now(timezone.utc).isoformat())
    hostname = metadata.get('hostname', socket.gethostname())
    filters_applied = metadata.get('filters_applied', filters)

    # Compute stats for embedding
    function_tag_groups = {}
    dispositions = {'Sanctioned': 0, 'To Be Retired': 0, 'TBD': 0}
    role_types = {}
    tools_count = 0
    baselined_count = 0
    with_desc_count = 0
    total = len(filtered_roles)

    for r in filtered_roles:
        ftags = r.get('function_tags') or []
        if ftags:
            for ft in ftags:
                code = ft.get('code', '') if isinstance(ft, dict) else str(ft)
                if code:
                    function_tag_groups[code] = function_tag_groups.get(code, 0) + 1
        else:
            function_tag_groups['Untagged'] = function_tag_groups.get('Untagged', 0) + 1

        disp = r.get('role_disposition') or 'TBD'
        if disp in dispositions:
            dispositions[disp] += 1
        else:
            dispositions['TBD'] += 1

        rt = r.get('role_type') or 'Unknown'
        role_types[rt] = role_types.get(rt, 0) + 1

        rn = r.get('role_name') or ''
        if (rt and ('tool' in rt.lower() or 'software' in rt.lower())) or rn.startswith('[S]'):
            tools_count += 1

        if r.get('baselined'):
            baselined_count += 1

        if r.get('description'):
            with_desc_count += 1

    # Sanitize data for JSON embedding
    safe_roles = json.dumps(filtered_roles, default=str)
    safe_relationships = json.dumps(filtered_relationships, default=str)
    safe_hierarchy = json.dumps(hierarchy, default=str)
    safe_metadata = json.dumps({
        'aegis_version': version,
        'exported_at': export_date,
        'exported_by': hostname,
        'total_roles': total,
        'total_relationships': len(filtered_relationships),
        'filters_applied': filters_applied,
        'stats': {
            'function_tag_groups': function_tag_groups,
            'dispositions': dispositions,
            'role_types': role_types,
            'tools_count': tools_count,
            'baselined_count': baselined_count,
            'with_desc_count': with_desc_count
        }
    }, default=str)

    display_date = export_date[:10] if len(export_date) >= 10 else export_date

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS Role Inheritance Map</title>
    <style>
{_get_css()}
    </style>
</head>
<body>
    <div class="app" id="app">
        <!-- Header -->
        <header class="header">
            <div class="header-left">
                <div class="aegis-logo">
                    <svg width="32" height="32" viewBox="0 0 100 100">
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
                <div>
                    <h1>AEGIS Role Inheritance Map</h1>
                    <p class="subtitle">Exported {html_module.escape(display_date)}</p>
                </div>
            </div>
            <div class="header-right">
                <div class="filter-summary" id="filter-summary"></div>
                <button class="export-changes-btn" id="export-changes-btn" onclick="showChangesModal()" title="Export changes as JSON">
                    &#9998; Export Changes <span class="changes-badge" id="changes-count">0</span>
                </button>
                <button class="btn btn-icon" id="btn-theme" onclick="toggleTheme()" title="Toggle dark/light mode">
                    <svg id="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="5"/>
                        <line x1="12" y1="1" x2="12" y2="3"/>
                        <line x1="12" y1="21" x2="12" y2="23"/>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                        <line x1="1" y1="12" x2="3" y2="12"/>
                        <line x1="21" y1="12" x2="23" y2="12"/>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                    </svg>
                    <svg id="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" stroke-width="2" style="display:none">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                    </svg>
                </button>
            </div>
        </header>

        <!-- Tab Bar -->
        <div class="tab-bar">
            <div class="tab-buttons">
                <button class="tab-btn active" data-tab="dashboard" onclick="switchTab('dashboard')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                    </svg>
                    Dashboard
                </button>
                <button class="tab-btn" data-tab="tree" onclick="switchTab('tree')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 3v18M3 9h18M3 15h18"/>
                    </svg>
                    Tree View
                </button>
                <button class="tab-btn" data-tab="graph" onclick="switchTab('graph')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/>
                        <circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>
                        <line x1="8.5" y1="7.5" x2="15.5" y2="16.5"/>
                        <line x1="15.5" y1="7.5" x2="8.5" y2="16.5"/>
                    </svg>
                    Graph View
                </button>
                <button class="tab-btn" data-tab="table" onclick="switchTab('table')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <line x1="3" y1="9" x2="21" y2="9"/>
                        <line x1="3" y1="15" x2="21" y2="15"/>
                        <line x1="9" y1="3" x2="9" y2="21"/>
                    </svg>
                    Table View
                </button>
            </div>
            <div class="filter-bar">
                <input type="text" id="search-input" class="search-input"
                       placeholder="Search roles..." oninput="handleSearch(this.value)">
                <div class="filter-controls">
                    <div class="filter-dropdown" id="ftag-filter">
                        <button class="filter-btn" onclick="toggleFilterDropdown('ftag-filter')">
                            Function Tag <span class="filter-arrow">&#9662;</span>
                        </button>
                        <div class="filter-dropdown-menu" id="ftag-filter-menu"></div>
                    </div>
                    <div class="filter-dropdown" id="disp-filter">
                        <button class="filter-btn" onclick="toggleFilterDropdown('disp-filter')">
                            Disposition <span class="filter-arrow">&#9662;</span>
                        </button>
                        <div class="filter-dropdown-menu" id="disp-filter-menu"></div>
                    </div>
                    <div class="filter-dropdown" id="type-filter">
                        <button class="filter-btn" onclick="toggleFilterDropdown('type-filter')">
                            Role Type <span class="filter-arrow">&#9662;</span>
                        </button>
                        <div class="filter-dropdown-menu" id="type-filter-menu"></div>
                    </div>
                    <div class="filter-dropdown" id="base-filter">
                        <button class="filter-btn" onclick="toggleFilterDropdown('base-filter')">
                            Baselined <span class="filter-arrow">&#9662;</span>
                        </button>
                        <div class="filter-dropdown-menu" id="base-filter-menu"></div>
                    </div>
                </div>
                <span class="filter-count" id="filter-count"></span>
            </div>
            <div class="active-filters" id="active-filters"></div>
        </div>

        <!-- Tab Content -->
        <div class="tab-content" id="tab-dashboard">
            <div class="dashboard" id="dashboard-content"></div>
        </div>
        <div class="tab-content" id="tab-tree" style="display:none">
            <div class="tree-toolbar">
                <button class="btn btn-secondary" onclick="expandAllTree()">Expand All</button>
                <button class="btn btn-secondary" onclick="collapseAllTree()">Collapse All</button>
            </div>
            <div class="tree-container" id="tree-container"></div>
        </div>
        <div class="tab-content" id="tab-graph" style="display:none">
            <div class="graph-container" id="graph-container" style="display:flex;flex-direction:column;">
                <div id="drill-breadcrumb" class="drill-breadcrumb"></div>
                <div id="drill-content" style="flex:1;overflow:hidden;position:relative;"></div>
            </div>
        </div>
        <div class="tab-content" id="tab-table" style="display:none">
            <div class="table-toolbar">
                <button class="btn btn-secondary" onclick="exportCSV()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    Export CSV
                </button>
            </div>
            <div class="table-wrapper">
                <table class="data-table" id="data-table">
                    <thead id="table-head"></thead>
                    <tbody id="table-body"></tbody>
                </table>
            </div>
        </div>

        <!-- Detail Panel (slide-in sidebar) -->
        <div class="detail-overlay" id="detail-overlay" style="display:none" onclick="closeDetailPanel()"></div>
        <div class="detail-panel" id="detail-panel">
            <div class="detail-header" id="detail-header"></div>
            <div class="detail-body" id="detail-body"></div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="footer-left">
                <span class="footer-brand">Generated by AEGIS v{html_module.escape(version)}</span>
                <span class="footer-sep">&middot;</span>
                <span>{html_module.escape(display_date)}</span>
            </div>
            <div class="footer-right">
                <button class="btn btn-secondary btn-sm" onclick="exportFilteredJSON()">Export Filtered JSON</button>
            </div>
        </footer>
    </div>

    <script id="hierarchy-data" type="application/json">
    {{
        "roles": {safe_roles},
        "relationships": {safe_relationships},
        "hierarchy": {safe_hierarchy},
        "metadata": {safe_metadata}
    }}
    </script>

    <script>
{_get_js()}
    </script>
</body>
</html>'''

    return html


def _apply_filters(roles: List[Dict], relationships: List[Dict],
                   filters: Dict) -> tuple:
    """Apply filter params to data before embedding."""
    if not filters:
        return roles, relationships

    filtered_roles = list(roles)

    org_groups = filters.get('org_groups')
    if org_groups:
        filtered_roles = [r for r in filtered_roles
                          if (r.get('org_group') or 'Unassigned') in org_groups]

    # v4.7.1: Filter by function tags
    functions = filters.get('functions')
    if functions:
        func_set = set(functions)
        filtered_roles = [r for r in filtered_roles
                          if any(ft.get('code') in func_set
                                 for ft in r.get('function_tags', []))]

    dispositions = filters.get('dispositions')
    if dispositions:
        filtered_roles = [r for r in filtered_roles
                          if (r.get('role_disposition') or 'TBD') in dispositions]

    role_types = filters.get('role_types')
    if role_types:
        filtered_roles = [r for r in filtered_roles
                          if (r.get('role_type') or 'Unknown') in role_types]

    baselined_only = filters.get('baselined_only', False)
    if baselined_only:
        filtered_roles = [r for r in filtered_roles if r.get('baselined')]

    include_tools = filters.get('include_tools', True)
    if not include_tools:
        filtered_roles = [r for r in filtered_roles
                          if not (r.get('role_type') or '').lower().startswith('tool')]

    # Filter relationships to only include filtered roles
    role_ids = {r.get('id') for r in filtered_roles}
    filtered_rels = [rel for rel in relationships
                     if rel.get('source_role_id') in role_ids
                     and rel.get('target_role_id') in role_ids]

    return filtered_roles, filtered_rels


def _get_css() -> str:
    """Return all CSS for the standalone HTML including dark mode, responsive, print."""
    return '''
        /* ===== CSS Variables (Light Mode) ===== */
        :root {
            --bg-app: #f0f2f5;
            --bg-surface: #ffffff;
            --bg-secondary: #f8f9fb;
            --bg-elevated: #ffffff;
            --bg-hover: rgba(0,0,0,0.04);
            --text-primary: #1a1a2e;
            --text-secondary: #555770;
            --text-muted: #8b8da3;
            --border-default: #e2e4e9;
            --border-subtle: #eef0f3;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.08);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.1);
            --shadow-lg: 0 8px 32px rgba(0,0,0,0.15);
            --accent: #D6A84A;
            --accent-dark: #B8743A;
            --accent-hover: #c49a3e;
            --accent-subtle: rgba(214,168,74,0.12);
            --accent-gradient: linear-gradient(135deg, #D6A84A, #B8743A);
            --success: #22c55e;
            --success-bg: rgba(34,197,94,0.1);
            --info: #3b82f6;
            --info-bg: rgba(59,130,246,0.1);
            --error: #ef4444;
            --error-bg: rgba(239,68,68,0.1);
            --warning: #f59e0b;
            --warning-bg: rgba(245,158,11,0.1);
            --sanctioned: #22c55e;
            --sanctioned-bg: rgba(34,197,94,0.08);
            --retire: #f59e0b;
            --retire-bg: rgba(245,158,11,0.08);
            --tbd: #8b8da3;
            --tbd-bg: rgba(139,141,163,0.08);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-xl: 18px;
            --detail-width: 420px;
        }

        /* ===== Dark Mode ===== */
        [data-theme="dark"] {
            --bg-app: #0f1117;
            --bg-surface: #1a1c25;
            --bg-secondary: #12141b;
            --bg-elevated: #22242e;
            --bg-hover: rgba(255,255,255,0.06);
            --text-primary: #e8e9ed;
            --text-secondary: #a0a3b5;
            --text-muted: #6b6e82;
            --border-default: #2a2d3a;
            --border-subtle: #1f2230;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
            --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
        }

        /* ===== Reset ===== */
        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-app);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
        }

        .app { max-width: 1600px; margin: 0 auto; padding: 16px 24px; }

        /* ===== Header ===== */
        .header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 14px 24px; margin-bottom: 12px;
            background: var(--bg-surface); border-radius: var(--radius-xl);
            border: 1px solid var(--border-default); box-shadow: var(--shadow-sm);
        }
        .header-left { display: flex; align-items: center; gap: 14px; }
        .header-right { display: flex; align-items: center; gap: 12px; }
        .aegis-logo { flex-shrink: 0; }
        h1 { font-size: 1.35rem; font-weight: 700; color: var(--text-primary); }
        .subtitle { font-size: 0.8rem; color: var(--text-muted); }
        .filter-summary { font-size: 0.75rem; color: var(--text-muted); }

        /* ===== Tab Bar ===== */
        .tab-bar {
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); margin-bottom: 12px;
            padding: 12px 16px;
        }
        .tab-buttons { display: flex; gap: 4px; margin-bottom: 10px; }
        .tab-btn {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 8px 16px; border-radius: var(--radius-sm); border: none;
            background: transparent; color: var(--text-secondary); font-size: 13px;
            font-weight: 500; cursor: pointer; transition: all 0.2s;
        }
        .tab-btn:hover { background: var(--bg-hover); color: var(--text-primary); }
        .tab-btn.active {
            background: var(--accent-subtle); color: var(--accent);
            font-weight: 600; border: 1px solid var(--accent);
        }

        /* ===== Filter Bar ===== */
        .filter-bar {
            display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        }
        .search-input {
            padding: 7px 14px; border-radius: var(--radius-md);
            border: 1px solid var(--border-default); background: var(--bg-secondary);
            color: var(--text-primary); font-size: 13px; width: 220px;
            outline: none; transition: border-color 0.2s;
        }
        .search-input:focus { border-color: var(--accent); }
        .filter-controls { display: flex; gap: 6px; }
        .filter-dropdown { position: relative; }
        .filter-btn {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 6px 12px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-default); background: var(--bg-secondary);
            color: var(--text-secondary); font-size: 12px; cursor: pointer;
            transition: all 0.2s;
        }
        .filter-btn:hover { border-color: var(--accent); color: var(--text-primary); }
        .filter-btn.has-filter { border-color: var(--accent); background: var(--accent-subtle); color: var(--accent); }
        .filter-arrow { font-size: 10px; }
        .filter-dropdown-menu {
            display: none; position: absolute; top: 100%; left: 0; z-index: 100;
            min-width: 200px; max-height: 280px; overflow-y: auto;
            background: var(--bg-surface); border: 1px solid var(--border-default);
            border-radius: var(--radius-md); box-shadow: var(--shadow-lg);
            padding: 6px; margin-top: 4px;
        }
        .filter-dropdown-menu.show { display: block; }
        .filter-option {
            display: flex; align-items: center; gap: 8px;
            padding: 6px 10px; border-radius: var(--radius-sm); cursor: pointer;
            font-size: 12px; transition: background 0.15s;
        }
        .filter-option:hover { background: var(--bg-hover); }
        .filter-option input[type="checkbox"] { accent-color: var(--accent); }
        .filter-count { font-size: 12px; color: var(--text-muted); white-space: nowrap; }
        .active-filters {
            display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
        }
        .active-filters:empty { margin-top: 0; }
        .filter-pill {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 3px 10px; border-radius: 16px; font-size: 11px;
            background: var(--accent-subtle); color: var(--accent);
            border: 1px solid rgba(214,168,74,0.3); cursor: default;
        }
        .filter-pill-remove {
            cursor: pointer; font-size: 14px; line-height: 1; opacity: 0.7;
            margin-left: 2px;
        }
        .filter-pill-remove:hover { opacity: 1; }

        /* ===== Buttons ===== */
        .btn {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 7px 14px; border-radius: var(--radius-sm); border: none;
            font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;
        }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-primary { background: var(--accent); color: #fff; }
        .btn-primary:hover:not(:disabled) { background: var(--accent-hover); transform: translateY(-1px); }
        .btn-secondary {
            background: var(--bg-secondary); color: var(--text-primary);
            border: 1px solid var(--border-default);
        }
        .btn-secondary:hover:not(:disabled) { background: var(--bg-hover); }
        .btn-icon {
            background: none; border: none; color: var(--text-secondary);
            padding: 6px; border-radius: var(--radius-sm); cursor: pointer;
        }
        .btn-icon:hover { background: var(--bg-hover); }
        .btn-sm { padding: 5px 10px; font-size: 12px; }

        /* ===== Tab Content ===== */
        .tab-content { min-height: 500px; }

        /* ===== Dashboard ===== */
        .dashboard { display: flex; flex-direction: column; gap: 16px; }
        .dash-hero {
            background: var(--accent-gradient); border-radius: var(--radius-xl);
            padding: 32px 40px; color: #fff; position: relative; overflow: hidden;
        }
        .dash-hero::after {
            content: ''; position: absolute; top: -50%; right: -10%;
            width: 300px; height: 300px; border-radius: 50%;
            background: rgba(255,255,255,0.06);
        }
        .dash-hero-title { font-size: 1.6rem; font-weight: 700; margin-bottom: 4px; }
        .dash-hero-sub { font-size: 0.9rem; opacity: 0.85; }

        .dash-stats {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
        }
        .stat-card {
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); padding: 20px;
            text-align: center; box-shadow: var(--shadow-sm);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .stat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
        .stat-icon { font-size: 24px; margin-bottom: 8px; }
        .stat-number {
            font-size: 2rem; font-weight: 700; line-height: 1.2;
            background: var(--accent-gradient); -webkit-background-clip: text;
            -webkit-text-fill-color: transparent; background-clip: text;
        }
        .stat-label {
            font-size: 0.78rem; color: var(--text-muted); text-transform: uppercase;
            letter-spacing: 0.5px; margin-top: 4px;
        }

        .dash-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
        .dash-card {
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); padding: 20px;
            box-shadow: var(--shadow-sm);
        }
        .dash-card-title {
            font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);
            text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px;
        }

        /* SVG Donut */
        .donut-container { display: flex; justify-content: center; align-items: center; position: relative; }
        .donut-legend {
            display: flex; flex-direction: column; gap: 6px; margin-left: 24px;
        }
        .donut-legend-item {
            display: flex; align-items: center; gap: 8px; font-size: 12px;
        }
        .donut-legend-dot {
            width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
        }
        .donut-legend-label { color: var(--text-secondary); }
        .donut-legend-count { font-weight: 600; color: var(--text-primary); margin-left: auto; }

        /* Disposition Bars */
        .disp-bar-row {
            display: flex; align-items: center; gap: 12px; margin-bottom: 10px;
        }
        .disp-bar-label {
            font-size: 12px; color: var(--text-secondary); width: 100px;
            text-align: right; flex-shrink: 0;
        }
        .disp-bar-track {
            flex: 1; height: 24px; border-radius: 12px; background: var(--bg-secondary);
            overflow: hidden; border: 1px solid var(--border-subtle);
        }
        .disp-bar-fill {
            height: 100%; border-radius: 12px; transition: width 1s ease;
            display: flex; align-items: center; padding-left: 10px;
            font-size: 11px; font-weight: 600; color: #fff; min-width: 30px;
        }
        .disp-bar-fill.sanctioned { background: var(--sanctioned); }
        .disp-bar-fill.retire { background: var(--retire); }
        .disp-bar-fill.tbd { background: var(--tbd); }

        /* Health Metrics */
        .health-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
        .health-item {
            background: var(--bg-secondary); border-radius: var(--radius-md);
            padding: 14px; text-align: center;
        }
        .health-pct {
            font-size: 1.8rem; font-weight: 700;
        }
        .health-label {
            font-size: 0.75rem; color: var(--text-muted); margin-top: 2px;
        }
        .health-bar {
            height: 6px; border-radius: 3px; background: var(--border-subtle);
            margin-top: 8px; overflow: hidden;
        }
        .health-bar-fill {
            height: 100%; border-radius: 3px; transition: width 1s ease;
        }

        /* ===== Tree View ===== */
        .tree-toolbar {
            display: flex; gap: 8px; margin-bottom: 12px;
        }
        .tree-container {
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); padding: 20px;
            min-height: 400px; overflow: auto; max-height: calc(100vh - 300px);
        }
        .tree-node {
            margin-left: 24px; position: relative;
        }
        .tree-node::before {
            content: ''; position: absolute; left: -16px; top: 0;
            width: 1px; height: 100%; background: var(--border-default);
        }
        .tree-node::after {
            content: ''; position: absolute; left: -16px; top: 18px;
            width: 12px; height: 1px; background: var(--border-default);
        }
        .tree-node:last-child::before { height: 18px; }
        .tree-root { margin-left: 0; }
        .tree-root::before, .tree-root::after { display: none; }
        .tree-item {
            display: flex; align-items: center; gap: 8px;
            padding: 6px 12px; margin: 2px 0; border-radius: var(--radius-sm);
            cursor: pointer; transition: all 0.15s; border: 1px solid transparent;
            position: relative;
        }
        .tree-item:hover { background: var(--bg-hover); }
        .tree-item.highlight {
            animation: treePulse 1.5s ease infinite;
            border-color: var(--accent);
        }
        @keyframes treePulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(214,168,74,0.3); }
            50% { box-shadow: 0 0 0 6px rgba(214,168,74,0); }
        }
        .tree-toggle {
            width: 20px; height: 20px; border-radius: 4px; border: none;
            background: var(--bg-secondary); color: var(--text-secondary);
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            font-size: 12px; flex-shrink: 0; transition: all 0.15s;
        }
        .tree-toggle:hover { background: var(--accent-subtle); color: var(--accent); }
        .tree-toggle.collapsed { transform: rotate(-90deg); }
        .tree-spacer { width: 20px; flex-shrink: 0; }
        .tree-name { font-size: 13px; font-weight: 500; color: var(--text-primary); }
        .tree-name.retired { text-decoration: line-through; opacity: 0.6; }
        .tree-badge {
            display: inline-flex; align-items: center; gap: 3px;
            padding: 1px 8px; border-radius: 10px; font-size: 10px; font-weight: 500;
        }
        .tree-badge-org { background: var(--info-bg); color: var(--info); }
        .tree-badge-sanctioned { background: var(--sanctioned-bg); color: var(--sanctioned); }
        .tree-badge-retire { background: var(--retire-bg); color: var(--retire); }
        .tree-badge-tbd { background: var(--tbd-bg); color: var(--tbd); }
        .tree-baselined {
            color: var(--sanctioned); font-size: 12px; font-weight: 700;
        }
        .tree-icon { font-size: 11px; }

        /* Tree disposition borders */
        .tree-item.disp-sanctioned { border-color: var(--sanctioned); border-style: solid; border-width: 1px; }
        .tree-item.disp-retire { border-color: var(--retire); border-style: dashed; border-width: 1px; opacity: 0.75; }
        .tree-item.disp-tbd { border-color: var(--tbd); border-style: dotted; border-width: 1px; }

        .tree-children { overflow: hidden; transition: max-height 0.3s ease; }
        .tree-children.collapsed { max-height: 0 !important; overflow: hidden; }

        /* ===== Graph View ===== */
        .graph-container {
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); height: calc(100vh - 300px);
            min-height: 500px; overflow: hidden; position: relative;
        }
        #graph-svg { width: 100%; height: 100%; }
        .graph-tooltip {
            position: absolute; padding: 10px 14px; border-radius: var(--radius-md);
            background: var(--bg-elevated); border: 1px solid var(--border-default);
            box-shadow: var(--shadow-lg); font-size: 12px; pointer-events: none;
            z-index: 50; max-width: 250px; display: none;
        }
        .graph-tooltip-name { font-weight: 600; margin-bottom: 4px; color: var(--text-primary); }
        .graph-tooltip-meta { color: var(--text-secondary); }
        .graph-legend {
            position: absolute; bottom: 12px; left: 12px; padding: 10px 14px;
            background: var(--bg-surface); border: 1px solid var(--border-default);
            border-radius: var(--radius-md); box-shadow: var(--shadow-sm);
            font-size: 11px; display: flex; flex-direction: column; gap: 4px;
        }
        .graph-legend-title { font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
        .graph-legend-item { display: flex; align-items: center; gap: 6px; color: var(--text-secondary); }
        .graph-legend-line {
            width: 24px; height: 0; border-top: 2px; display: inline-block;
        }
        .graph-controls {
            position: absolute; top: 12px; right: 12px;
            display: flex; flex-direction: column; gap: 8px; align-items: flex-end; z-index: 20;
        }
        .graph-ctrl-row { display: flex; gap: 4px; }
        .graph-ctrl-btn {
            width: 32px; height: 32px; border-radius: var(--radius-sm);
            background: var(--bg-surface); border: 1px solid var(--border-default);
            color: var(--text-primary); font-size: 18px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            box-shadow: var(--shadow-sm); transition: background 0.15s;
            line-height: 1;
        }
        .graph-ctrl-btn:hover { background: var(--bg-hover); }
        .graph-ctrl-select {
            padding: 4px 8px; border-radius: var(--radius-sm); font-size: 11px;
            background: var(--bg-surface); border: 1px solid var(--border-default);
            color: var(--text-primary); cursor: pointer; box-shadow: var(--shadow-sm);
        }
        .graph-ctrl-label {
            font-size: 11px; color: var(--text-secondary); display: flex;
            align-items: center; gap: 4px; background: var(--bg-surface);
            padding: 4px 8px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-default); box-shadow: var(--shadow-sm);
            cursor: pointer;
        }
        .graph-ctrl-info {
            font-size: 10px; color: var(--text-muted); background: var(--bg-surface);
            padding: 3px 8px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-default); box-shadow: var(--shadow-sm);
        }

        /* ===== Drill-Down Navigation ===== */
        .drill-breadcrumb {
            display: flex; align-items: center; gap: 6px; padding: 10px 16px;
            background: var(--bg-secondary); border-bottom: 1px solid var(--border-default);
            font-size: 13px; color: var(--text-secondary); flex-shrink: 0;
        }
        .drill-breadcrumb-item {
            color: var(--accent); cursor: pointer; font-weight: 500;
            transition: opacity 0.15s;
        }
        .drill-breadcrumb-item:hover { opacity: 0.7; }
        .drill-breadcrumb-item.current {
            color: var(--text-primary); cursor: default; font-weight: 600;
        }
        .drill-breadcrumb-item.current:hover { opacity: 1; }
        .drill-breadcrumb-sep { color: var(--text-muted); font-size: 11px; }
        .drill-back-btn {
            width: 28px; height: 28px; border-radius: var(--radius-sm);
            background: var(--bg-surface); border: 1px solid var(--border-default);
            color: var(--text-primary); font-size: 16px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            margin-right: 6px; transition: background 0.15s;
        }
        .drill-back-btn:hover { background: var(--bg-hover); }

        .drill-cluster-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 16px; padding: 20px; overflow-y: auto; max-height: calc(100% - 44px);
        }
        .drill-cluster-card {
            background: var(--bg-surface); border: 1px solid var(--border-default);
            border-radius: var(--radius-lg); padding: 18px; cursor: pointer;
            transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
            display: flex; flex-direction: column; gap: 10px;
        }
        .drill-cluster-card:hover {
            transform: translateY(-4px) scale(1); box-shadow: var(--shadow-lg);
            border-color: var(--accent);
        }
        .drill-cluster-header {
            display: flex; justify-content: space-between; align-items: center;
        }
        .drill-cluster-title { font-weight: 700; font-size: 15px; color: var(--text-primary); }
        .drill-cluster-count {
            font-size: 12px; color: var(--text-muted); background: var(--bg-secondary);
            padding: 2px 8px; border-radius: 10px;
        }
        .drill-cluster-roles {
            font-size: 12px; color: var(--text-secondary); line-height: 1.5;
        }
        .drill-cluster-roles span { display: block; }
        .drill-mini-bar {
            display: flex; height: 6px; border-radius: 3px; overflow: hidden;
            background: var(--bg-secondary);
        }
        .drill-mini-bar-seg { height: 100%; transition: width 0.3s; }
        .drill-cluster-stats {
            display: flex; gap: 12px; font-size: 11px; color: var(--text-muted);
        }

        .drill-svg-wrap {
            flex: 1; overflow: hidden; position: relative;
        }
        .drill-node { cursor: pointer; }
        .drill-node:hover .drill-node-circle,
        .drill-node:hover .drill-node-rect { filter: brightness(1.15); }
        .drill-info-panel {
            position: absolute; bottom: 12px; left: 12px; right: 12px;
            background: var(--bg-surface); border: 1px solid var(--border-default);
            border-radius: var(--radius-md); padding: 10px 14px;
            font-size: 11px; color: var(--text-muted); text-align: center;
            box-shadow: var(--shadow-sm);
        }
        .drill-legend {
            position: absolute; bottom: 12px; left: 12px; padding: 10px 14px;
            background: var(--bg-surface); border: 1px solid var(--border-default);
            border-radius: var(--radius-md); box-shadow: var(--shadow-sm);
            font-size: 11px; display: flex; flex-direction: column; gap: 4px;
        }

        /* ===== Table View ===== */
        .table-toolbar { display: flex; justify-content: flex-end; margin-bottom: 10px; }
        .table-wrapper {
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); overflow: auto;
            max-height: calc(100vh - 320px);
        }
        .data-table {
            width: 100%; border-collapse: collapse; font-size: 13px;
        }
        .data-table th {
            position: sticky; top: 0; z-index: 10;
            background: var(--bg-secondary); padding: 10px 14px;
            text-align: left; font-weight: 600; font-size: 0.78rem;
            text-transform: uppercase; letter-spacing: 0.5px;
            color: var(--text-secondary); border-bottom: 2px solid var(--border-default);
            cursor: pointer; user-select: none; transition: color 0.15s;
            white-space: nowrap;
        }
        .data-table th:hover { color: var(--accent); }
        .data-table th.sorted { color: var(--accent); }
        .sort-arrow { font-size: 10px; margin-left: 4px; }
        .data-table td {
            padding: 10px 14px; border-bottom: 1px solid var(--border-subtle);
            color: var(--text-primary); vertical-align: middle;
        }
        .data-table tr:hover td { background: var(--bg-hover); }
        .data-table tr:nth-child(even) td { background: var(--bg-secondary); }
        .data-table tr:nth-child(even):hover td { background: var(--bg-hover); }
        .data-table tr { cursor: pointer; transition: background 0.15s; }
        .table-badge {
            display: inline-flex; align-items: center; padding: 2px 8px;
            border-radius: 10px; font-size: 11px; font-weight: 500;
        }
        .table-badge-sanctioned { background: var(--sanctioned-bg); color: var(--sanctioned); }
        .table-badge-retire { background: var(--retire-bg); color: var(--retire); }
        .table-badge-tbd { background: var(--tbd-bg); color: var(--tbd); }
        .table-ftag-badge {
            display: inline-flex; align-items: center; padding: 1px 6px;
            border-radius: 8px; font-size: 10px; font-weight: 600; margin: 1px 2px;
        }
        .table-desc {
            max-width: 250px; overflow: hidden; text-overflow: ellipsis;
            white-space: nowrap; color: var(--text-secondary); font-size: 12px;
        }
        .nimbus-link-list {
            list-style: none; margin: 0; padding: 0; font-size: 11px;
        }
        .nimbus-link-list li { padding: 1px 0; white-space: nowrap; }
        .nimbus-link-list .nimbus-link {
            color: var(--accent); text-decoration: none; font-weight: 500;
        }
        .nimbus-link-list .nimbus-link:hover { text-decoration: underline; }

        /* ===== Detail Panel ===== */
        .detail-overlay {
            position: fixed; inset: 0; background: rgba(0,0,0,0.3);
            z-index: 900; backdrop-filter: blur(2px);
        }
        .detail-panel {
            position: fixed; top: 0; right: -440px; width: var(--detail-width);
            height: 100vh; background: var(--bg-surface);
            border-left: 1px solid var(--border-default);
            box-shadow: var(--shadow-lg); z-index: 1000;
            transition: right 0.3s ease; overflow-y: auto;
        }
        .detail-panel.open { right: 0; }
        .detail-header {
            padding: 20px 24px; border-bottom: 1px solid var(--border-subtle);
            position: sticky; top: 0; background: var(--bg-surface); z-index: 2;
        }
        .detail-header-bar {
            height: 4px; border-radius: 2px; margin-bottom: 12px;
        }
        .detail-header-bar.sanctioned { background: var(--sanctioned); }
        .detail-header-bar.retire { background: var(--retire); }
        .detail-header-bar.tbd { background: var(--tbd); }
        .detail-title-row {
            display: flex; justify-content: space-between; align-items: flex-start;
        }
        .detail-title {
            font-size: 1.15rem; font-weight: 700; color: var(--text-primary);
        }
        .detail-title.retired { text-decoration: line-through; }
        .detail-close {
            background: none; border: none; color: var(--text-secondary);
            cursor: pointer; padding: 4px; border-radius: 4px; font-size: 20px;
        }
        .detail-close:hover { background: var(--bg-hover); }
        .detail-disp-label {
            display: inline-flex; align-items: center; gap: 4px;
            font-size: 11px; font-weight: 500; margin-top: 6px;
            padding: 3px 10px; border-radius: 12px;
        }
        .detail-disp-label.sanctioned { background: var(--sanctioned-bg); color: var(--sanctioned); }
        .detail-disp-label.retire { background: var(--retire-bg); color: var(--retire); }
        .detail-disp-label.tbd { background: var(--tbd-bg); color: var(--tbd); }
        .detail-body { padding: 16px 24px 32px; }
        .detail-section { margin-bottom: 18px; }
        .detail-section-title {
            font-size: 0.72rem; font-weight: 600; color: var(--text-muted);
            text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;
        }
        .detail-section-content { font-size: 13px; color: var(--text-primary); }
        .detail-badge {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: 500;
            background: var(--bg-secondary); color: var(--text-secondary);
            border: 1px solid var(--border-subtle);
        }
        .detail-badge-gold { background: var(--accent-subtle); color: var(--accent); border-color: rgba(214,168,74,0.3); }
        .detail-link-list { list-style: none; padding: 0; }
        .detail-link-item {
            padding: 5px 10px; border-radius: var(--radius-sm); cursor: pointer;
            font-size: 13px; color: var(--accent); transition: background 0.15s;
            display: flex; align-items: center; gap: 6px;
        }
        .detail-link-item:hover { background: var(--accent-subtle); }
        .detail-tag-list { display: flex; flex-wrap: wrap; gap: 4px; }
        .detail-tag {
            padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 500;
        }

        /* ===== Footer ===== */
        .footer {
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px 20px; margin-top: 12px;
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); font-size: 12px;
            color: var(--text-muted);
        }
        .footer-left { display: flex; align-items: center; gap: 8px; }
        .footer-right { display: flex; align-items: center; gap: 8px; }
        .footer-brand { color: var(--accent); font-weight: 600; }
        .footer-sep { opacity: 0.3; }

        /* ===== Toast ===== */
        .toast {
            position: fixed; bottom: 20px; right: 20px; z-index: 2000;
            padding: 12px 20px; border-radius: var(--radius-md);
            background: var(--bg-elevated); border: 1px solid var(--border-default);
            box-shadow: var(--shadow-lg); font-size: 13px; color: var(--text-primary);
            animation: slideUp 0.3s ease;
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* ===== Animations ===== */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes countUp {
            from { opacity: 0; transform: scale(0.5); }
            to { opacity: 1; transform: scale(1); }
        }
        .animate-in { animation: fadeIn 0.4s ease forwards; }
        .stat-number { animation: countUp 0.6s ease forwards; }

        /* Graph view animations */
        @keyframes cardSlideUp {
            from { opacity: 0; transform: translateY(24px) scale(0.97); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes nodePopIn {
            0% { opacity: 0; transform: scale(0); }
            70% { transform: scale(1.08); }
            100% { opacity: 1; transform: scale(1); }
        }
        @keyframes lineDraw {
            from { stroke-dashoffset: 200; }
            to { stroke-dashoffset: 0; }
        }
        @keyframes centerPulse {
            0% { opacity: 0; transform: scale(0); }
            60% { transform: scale(1.12); }
            80% { transform: scale(0.95); }
            100% { opacity: 1; transform: scale(1); }
        }
        @keyframes badgePop {
            0% { opacity: 0; transform: scale(0); }
            80% { transform: scale(1.15); }
            100% { opacity: 1; transform: scale(1); }
        }
        @keyframes labelFadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes miniBarGrow {
            from { transform: scaleX(0); }
            to { transform: scaleX(1); }
        }
        .drill-cluster-card {
            opacity: 0;
            animation: cardSlideUp 0.35s ease forwards;
        }
        .drill-mini-bar { transform-origin: left center; animation: miniBarGrow 0.6s ease forwards; animation-delay: 0.25s; }
        .drill-node { animation: nodePopIn 0.4s ease forwards; opacity: 0; }
        .drill-node-circle { transition: fill-opacity 0.2s, r 0.2s; }
        .drill-node:hover .drill-node-circle { fill-opacity: 0.4; }
        .drill-center-circle { transform-origin: center; }
        .drill-arrow-line { stroke-dasharray: 200; stroke-dashoffset: 200; animation: lineDraw 0.5s ease forwards; }
        .drill-svg-wrap { animation: fadeIn 0.3s ease forwards; }

        /* ===== Responsive ===== */
        @media (max-width: 1200px) {
            .dash-stats { grid-template-columns: repeat(2, 1fr); }
            .dash-row { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
            .app { padding: 10px 12px; }
            .header { flex-direction: column; gap: 10px; padding: 12px 16px; }
            .tab-buttons { flex-wrap: wrap; }
            .filter-bar { flex-direction: column; align-items: stretch; }
            .search-input { width: 100%; }
            .filter-controls { flex-wrap: wrap; }
            .dash-stats { grid-template-columns: 1fr; }
            .detail-panel { width: 100vw; --detail-width: 100vw; }
            .data-table { font-size: 11px; }
        }

        /* ===== Edit Mode ===== */
        .detail-edit-toggle {
            cursor: pointer; padding: 4px 10px; border-radius: 6px;
            background: var(--bg-secondary); border: 1px solid var(--border-default);
            color: var(--text-secondary); font-size: 12px; font-weight: 500;
            transition: all 0.15s;
        }
        .detail-edit-toggle:hover { background: var(--accent); color: white; border-color: var(--accent); }
        .detail-edit-toggle.active { background: var(--accent); color: white; border-color: var(--accent); }
        .edit-status-group { display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
        .edit-status-btn {
            padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border-default);
            cursor: pointer; font-size: 13px; background: var(--bg-surface); color: var(--text-primary);
            transition: all 0.15s;
        }
        .edit-status-btn:hover { border-color: var(--text-secondary); }
        .edit-status-btn.selected { font-weight: 600; }
        .edit-status-btn.s-confirmed.selected { background: #16a34a15; color: #16a34a; border-color: #16a34a; }
        .edit-status-btn.s-deliverable.selected { background: #D6A84A15; color: #D6A84A; border-color: #D6A84A; }
        .edit-status-btn.s-rejected.selected { background: #dc262615; color: #dc2626; border-color: #dc2626; }
        .edit-section-header {
            font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
            color: var(--accent); margin: 16px 0 8px 0; padding-bottom: 4px;
            border-bottom: 1px solid var(--border-default);
        }
        .edit-section-header:first-child { margin-top: 0; }
        .edit-field { margin-bottom: 12px; }
        .edit-field label { font-size: 12px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; display: block; }
        .edit-hint { font-weight: 400; color: var(--text-muted); font-size: 11px; }
        .edit-field textarea, .edit-field input[type="text"] {
            width: 100%; padding: 8px; border: 1px solid var(--border-default);
            border-radius: 6px; background: var(--bg-surface); color: var(--text-primary);
            font-size: 13px; font-family: inherit; box-sizing: border-box;
        }
        .edit-field textarea:focus, .edit-field input[type="text"]:focus {
            outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-bg);
        }
        .edit-field textarea { min-height: 60px; resize: vertical; }
        .edit-field-row { display: flex; gap: 10px; }
        .edit-field-half { flex: 1; min-width: 0; }
        .edit-checkbox-label {
            display: flex; align-items: center; gap: 8px; cursor: pointer;
            font-size: 13px; color: var(--text-primary);
        }
        .edit-checkbox-label input[type="checkbox"] {
            width: 16px; height: 16px; cursor: pointer; accent-color: var(--accent);
        }
        .edit-disp-btn {
            padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border-default);
            cursor: pointer; font-size: 13px; background: var(--bg-surface); color: var(--text-primary);
            transition: all 0.15s;
        }
        .edit-disp-btn:hover { border-color: var(--text-secondary); }
        .edit-disp-btn.selected { font-weight: 600; }
        .edit-disp-btn.d-sanctioned.selected { background: #16a34a15; color: #16a34a; border-color: #16a34a; }
        .edit-disp-btn.d-retire.selected { background: #f9731615; color: #f97316; border-color: #f97316; }
        .edit-disp-btn.d-tbd.selected { background: #6b728015; color: #6b7280; border-color: #6b7280; }
        .edit-actions { display: flex; gap: 8px; margin-top: 14px; }
        .edit-save-btn {
            background: var(--accent); color: white; padding: 7px 18px;
            border-radius: 6px; border: none; cursor: pointer; font-weight: 600; font-size: 13px;
        }
        .edit-save-btn:hover { filter: brightness(1.1); }
        .edit-cancel-btn {
            background: var(--bg-secondary); color: var(--text-primary); padding: 7px 18px;
            border-radius: 6px; border: 1px solid var(--border-default); cursor: pointer; font-size: 13px;
        }
        .edit-cancel-btn:hover { background: var(--bg-tertiary); }
        .change-diff-item { display: block; padding: 2px 0; }

        /* Change indicators */
        .role-modified-dot {
            width: 7px; height: 7px; border-radius: 50%; background: #f59e0b;
            display: inline-block; margin-left: 5px; vertical-align: middle;
        }
        tr.row-modified { border-left: 3px solid #f59e0b !important; }
        .drill-cluster-card.card-modified { border-color: #f59e0b; box-shadow: 0 0 8px #f59e0b30; }
        .detail-modified-badge {
            display: inline-flex; align-items: center; padding: 2px 8px;
            border-radius: 10px; font-size: 11px; font-weight: 600;
            background: #f59e0b20; color: #f59e0b; margin-left: 8px;
        }

        /* Export Changes button */
        .export-changes-btn {
            display: none; padding: 6px 14px; border-radius: 6px;
            background: #f59e0b; color: white; border: none; cursor: pointer;
            font-weight: 600; font-size: 13px; align-items: center; gap: 6px;
        }
        .export-changes-btn.visible { display: inline-flex; }
        .export-changes-btn:hover { filter: brightness(1.1); }
        .changes-badge {
            background: white; color: #f59e0b; font-size: 11px; font-weight: 700;
            padding: 1px 6px; border-radius: 8px; margin-left: 4px;
        }

        /* Changes summary modal */
        .changes-modal-overlay {
            position: fixed; inset: 0; background: rgba(0,0,0,0.5);
            display: flex; align-items: center; justify-content: center; z-index: 1000;
        }
        .changes-modal {
            background: var(--bg-surface); border-radius: 12px;
            max-width: 620px; width: 90%; max-height: 80vh; overflow: auto;
            padding: 24px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .changes-modal h3 { margin: 0 0 16px 0; font-size: 18px; color: var(--text-primary); }
        .changes-list-item {
            padding: 10px 0; border-bottom: 1px solid var(--border-default);
            font-size: 13px; color: var(--text-primary);
        }
        .changes-list-item:last-child { border-bottom: none; }
        .change-role-name { font-weight: 600; }
        .change-diff { color: var(--text-secondary); font-size: 12px; margin-top: 4px; }
        .change-diff span { margin-right: 12px; }
        .changes-modal-actions { display: flex; gap: 8px; margin-top: 18px; justify-content: flex-end; }

        /* Import instructions */
        .import-instructions {
            margin: 16px 0; padding: 12px; background: var(--bg-secondary);
            border-radius: 8px; border: 1px solid var(--border-default);
        }
        .import-instructions-title {
            font-size: 11px; font-weight: 700; text-transform: uppercase;
            letter-spacing: 0.5px; color: var(--accent); margin-bottom: 8px;
        }
        .import-instructions-item {
            font-size: 12px; color: var(--text-secondary); margin-bottom: 6px; line-height: 1.5;
        }
        .import-instructions-item:last-child { margin-bottom: 0; }
        .import-instructions code {
            background: var(--bg-tertiary); padding: 1px 5px; border-radius: 3px; font-size: 11px;
        }

        /* ===== Print ===== */
        @media print {
            body { background: #fff; }
            .header, .tab-bar, .footer, .tree-toolbar, .table-toolbar,
            .detail-overlay, .detail-panel, .toast, .graph-legend { display: none !important; }
            .tab-content { display: block !important; page-break-inside: avoid; }
            .tab-content#tab-dashboard { display: block !important; }
            .tab-content#tab-table { display: block !important; }
            .tab-content#tab-tree { display: none !important; }
            .tab-content#tab-graph { display: none !important; }
            .app { max-width: 100%; padding: 0; }
            .dash-hero { color: #333; background: #f5f5f5 !important; }
            .stat-number { color: #333 !important; -webkit-text-fill-color: #333 !important; }
        }
    '''


def _get_js() -> str:
    """Return all JavaScript for views, filtering, detail panel, graph physics, tree rendering."""
    return '''
    // ===== Parse embedded data =====
    const RAW_DATA = JSON.parse(document.getElementById('hierarchy-data').textContent);
    const ALL_ROLES = RAW_DATA.roles;
    const ALL_RELATIONSHIPS = RAW_DATA.relationships;
    const HIERARCHY = RAW_DATA.hierarchy;
    const META = RAW_DATA.metadata;

    // ===== State =====
    let currentTab = 'dashboard';
    let searchText = '';
    let isDark = localStorage.getItem('aegis-hierarchy-theme') === 'dark' ||
                 (!localStorage.getItem('aegis-hierarchy-theme') &&
                  window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    let graphInitialized = false;
    let sortColumn = 'role_name';
    let sortDirection = 'asc';

    // Filter state
    const activeFilters = {
        function_tags: new Set(),
        dispositions: new Set(),
        role_types: new Set(),
        baselined: null // null = all, true = yes, false = no
    };

    // Function tag color map (built from embedded tag data)
    const ftColorMap = {};
    (function buildFtColorMap() {
        const FALLBACK_COLORS = [
            '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6',
            '#06b6d4', '#ec4899', '#f97316', '#14b8a6', '#6366f1',
            '#84cc16', '#e11d48', '#0ea5e9', '#a855f7', '#d946ef'
        ];
        let idx = 0;
        ALL_ROLES.forEach(r => {
            (r.function_tags || []).forEach(ft => {
                const code = ft.code || ft.name || ft;
                if (code && !ftColorMap[code]) {
                    ftColorMap[code] = ft.color || FALLBACK_COLORS[idx % FALLBACK_COLORS.length];
                    idx++;
                }
            });
        });
        ftColorMap['Untagged'] = '#9ca3af';
    })();

    // ===== Edit/Change Tracking =====
    const INITIAL_STATES = new Map();
    ALL_ROLES.forEach(r => INITIAL_STATES.set(r.role_name, {
        status: r.is_active === false || r.is_active === 0 ? 'rejected' : (r.is_deliverable ? 'deliverable' : 'confirmed'),
        role_name: r.role_name || '',
        role_type: r.role_type || '',
        role_disposition: r.role_disposition || 'TBD',
        category: r.category || '',
        description: r.description || '',
        notes: r.notes || '',
        org_group: r.org_group || '',
        hierarchy_level: r.hierarchy_level || '',
        baselined: r.baselined ? true : false,
        aliases: (typeof r.aliases === 'string' ? r.aliases : (Array.isArray(r.aliases) ? r.aliases.join(', ') : ''))
    }));
    const editChanges = new Map();
    const editHistory = [];
    let editHistoryPos = -1;
    let editModeRole = null; // currently editing role name

    function trackEdit(roleName) {
        const role = ALL_ROLES.find(r => r.role_name === roleName);
        if (!role) return;
        // Use the original name to look up initial state (before any rename)
        const initialKey = role._originalName || roleName;
        const initial = INITIAL_STATES.get(initialKey);
        if (!initial) return;
        const curStatus = (role.is_active === false || role.is_active === 0) ? 'rejected' : (role.is_deliverable ? 'deliverable' : 'confirmed');
        const curAliases = typeof role.aliases === 'string' ? role.aliases : (Array.isArray(role.aliases) ? role.aliases.join(', ') : '');
        const current = {
            status: curStatus,
            role_name: role.role_name || '',
            role_type: role.role_type || '',
            role_disposition: role.role_disposition || 'TBD',
            category: role.category || '',
            description: role.description || '',
            notes: role.notes || '',
            org_group: role.org_group || '',
            hierarchy_level: role.hierarchy_level || '',
            baselined: role.baselined ? true : false,
            aliases: curAliases
        };
        // Compare all tracked fields
        const changed = current.status !== initial.status ||
            current.role_name !== initial.role_name ||
            current.role_type !== initial.role_type ||
            current.role_disposition !== initial.role_disposition ||
            current.category !== initial.category ||
            current.description !== initial.description ||
            current.notes !== initial.notes ||
            current.org_group !== initial.org_group ||
            current.hierarchy_level !== initial.hierarchy_level ||
            current.baselined !== initial.baselined ||
            current.aliases !== initial.aliases;
        if (changed) {
            const change = {
                role_name: initial.role_name,
                action: current.status,
                category: current.category,
                description: current.description,
                notes: current.notes,
                role_type: current.role_type,
                role_disposition: current.role_disposition,
                org_group: current.org_group,
                hierarchy_level: current.hierarchy_level,
                baselined: current.baselined,
                aliases: current.aliases
            };
            if (current.role_name !== initial.role_name) {
                change.new_role_name = current.role_name;
            }
            editChanges.set(initialKey, change);
        } else {
            editChanges.delete(initialKey);
        }
        updateChangesBadge();
    }

    function updateChangesBadge() {
        const btn = document.getElementById('export-changes-btn');
        const badge = document.getElementById('changes-count');
        if (btn) {
            btn.classList.toggle('visible', editChanges.size > 0);
        }
        if (badge) {
            badge.textContent = editChanges.size;
        }
    }

    function pushEditHistory(action) {
        editHistory.splice(editHistoryPos + 1);
        editHistory.push(action);
        editHistoryPos = editHistory.length - 1;
    }

    // ===== Init =====
    document.addEventListener('DOMContentLoaded', () => {
        if (isDark) document.documentElement.setAttribute('data-theme', 'dark');
        updateThemeIcon();
        buildFilterMenus();
        renderDashboard();
        updateFilterCount();

        // Close dropdowns on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.filter-dropdown')) {
                document.querySelectorAll('.filter-dropdown-menu').forEach(m => m.classList.remove('show'));
            }
        });

        // Keyboard: Escape closes detail panel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeDetailPanel();
        });
    });

    // ===== Filtering =====
    function getFilteredRoles() {
        let result = ALL_ROLES;
        if (searchText) {
            const q = searchText.toLowerCase();
            result = result.filter(r =>
                (r.role_name || '').toLowerCase().includes(q) ||
                (r.category || '').toLowerCase().includes(q) ||
                ((r.function_tags || []).map(ft => (ft.code || ft.name || '')).join(' ')).toLowerCase().includes(q) ||
                (r.description || '').toLowerCase().includes(q) ||
                (r.aliases || '').toLowerCase().includes(q)
            );
        }
        if (activeFilters.function_tags.size > 0) {
            result = result.filter(r => {
                const codes = (r.function_tags || []).map(ft => ft.code || ft.name || ft);
                if (codes.length === 0) return activeFilters.function_tags.has('Untagged');
                return codes.some(c => activeFilters.function_tags.has(c));
            });
        }
        if (activeFilters.dispositions.size > 0) {
            result = result.filter(r => activeFilters.dispositions.has(r.role_disposition || 'TBD'));
        }
        if (activeFilters.role_types.size > 0) {
            result = result.filter(r => activeFilters.role_types.has(r.role_type || 'Unknown'));
        }
        if (activeFilters.baselined === true) {
            result = result.filter(r => r.baselined);
        } else if (activeFilters.baselined === false) {
            result = result.filter(r => !r.baselined);
        }
        return result;
    }

    function getFilteredRelationships() {
        const roleIds = new Set(getFilteredRoles().map(r => r.id));
        return ALL_RELATIONSHIPS.filter(rel =>
            roleIds.has(rel.source_role_id) && roleIds.has(rel.target_role_id)
        );
    }

    function handleSearch(value) {
        searchText = value;
        updateFilterCount();
        refreshCurrentTab();
    }

    function buildFilterMenus() {
        // Function tags
        const allTagCodes = new Set();
        ALL_ROLES.forEach(r => {
            const tags = r.function_tags || [];
            if (tags.length === 0) allTagCodes.add('Untagged');
            else tags.forEach(ft => allTagCodes.add(ft.code || ft.name || ft));
        });
        const tagCodes = [...allTagCodes].sort();
        const ftagMenu = document.getElementById('ftag-filter-menu');
        ftagMenu.innerHTML = tagCodes.map(code =>
            '<div class="filter-option" onclick="toggleFilter(\\x27function_tags\\x27, \\x27' + escAttr(code) + '\\x27)">' +
            '<input type="checkbox" ' + (activeFilters.function_tags.has(code) ? 'checked' : '') + '> ' +
            '<span style="color:' + (ftColorMap[code] || '#666') + '">' + escHtml(code) + '</span></div>'
        ).join('');

        // Dispositions
        const disps = ['Sanctioned', 'To Be Retired', 'TBD'];
        const dispMenu = document.getElementById('disp-filter-menu');
        dispMenu.innerHTML = disps.map(d =>
            '<div class="filter-option" onclick="toggleFilter(\\x27dispositions\\x27, \\x27' + escAttr(d) + '\\x27)">' +
            '<input type="checkbox" ' + (activeFilters.dispositions.has(d) ? 'checked' : '') + '> ' + escHtml(d) + '</div>'
        ).join('');

        // Role types
        const types = [...new Set(ALL_ROLES.map(r => r.role_type || 'Unknown'))].sort();
        const typeMenu = document.getElementById('type-filter-menu');
        typeMenu.innerHTML = types.map(t =>
            '<div class="filter-option" onclick="toggleFilter(\\x27role_types\\x27, \\x27' + escAttr(t) + '\\x27)">' +
            '<input type="checkbox" ' + (activeFilters.role_types.has(t) ? 'checked' : '') + '> ' + escHtml(t) + '</div>'
        ).join('');

        // Baselined
        const baseMenu = document.getElementById('base-filter-menu');
        baseMenu.innerHTML =
            '<div class="filter-option" onclick="setBaselinedFilter(null)"><input type="radio" name="baselined" ' + (activeFilters.baselined === null ? 'checked' : '') + '> All</div>' +
            '<div class="filter-option" onclick="setBaselinedFilter(true)"><input type="radio" name="baselined" ' + (activeFilters.baselined === true ? 'checked' : '') + '> Yes</div>' +
            '<div class="filter-option" onclick="setBaselinedFilter(false)"><input type="radio" name="baselined" ' + (activeFilters.baselined === false ? 'checked' : '') + '> No</div>';
    }

    function toggleFilterDropdown(id) {
        const menu = document.getElementById(id + '-menu');
        const wasOpen = menu.classList.contains('show');
        document.querySelectorAll('.filter-dropdown-menu').forEach(m => m.classList.remove('show'));
        if (!wasOpen) menu.classList.add('show');
    }

    function toggleFilter(type, value) {
        if (activeFilters[type].has(value)) {
            activeFilters[type].delete(value);
        } else {
            activeFilters[type].add(value);
        }
        buildFilterMenus();
        updateFilterPills();
        updateFilterCount();
        updateFilterBtnStates();
        refreshCurrentTab();
    }

    function setBaselinedFilter(val) {
        activeFilters.baselined = val;
        buildFilterMenus();
        updateFilterPills();
        updateFilterCount();
        refreshCurrentTab();
    }

    function removeFilter(type, value) {
        if (type === 'baselined') {
            activeFilters.baselined = null;
        } else {
            activeFilters[type].delete(value);
        }
        buildFilterMenus();
        updateFilterPills();
        updateFilterCount();
        updateFilterBtnStates();
        refreshCurrentTab();
    }

    function updateFilterPills() {
        const container = document.getElementById('active-filters');
        let html = '';
        activeFilters.function_tags.forEach(code => {
            html += '<span class="filter-pill" style="color:' + (ftColorMap[code] || '#666') + '">' + escHtml(code) +
                    ' <span class="filter-pill-remove" onclick="removeFilter(\\x27function_tags\\x27,\\x27' + escAttr(code) + '\\x27)">&times;</span></span>';
        });
        activeFilters.dispositions.forEach(d => {
            html += '<span class="filter-pill">' + escHtml(d) +
                    ' <span class="filter-pill-remove" onclick="removeFilter(\\x27dispositions\\x27,\\x27' + escAttr(d) + '\\x27)">&times;</span></span>';
        });
        activeFilters.role_types.forEach(t => {
            html += '<span class="filter-pill">' + escHtml(t) +
                    ' <span class="filter-pill-remove" onclick="removeFilter(\\x27role_types\\x27,\\x27' + escAttr(t) + '\\x27)">&times;</span></span>';
        });
        if (activeFilters.baselined !== null) {
            html += '<span class="filter-pill">Baselined: ' + (activeFilters.baselined ? 'Yes' : 'No') +
                    ' <span class="filter-pill-remove" onclick="removeFilter(\\x27baselined\\x27,null)">&times;</span></span>';
        }
        container.innerHTML = html;
    }

    function updateFilterCount() {
        const filtered = getFilteredRoles();
        const el = document.getElementById('filter-count');
        if (el) {
            el.textContent = 'Showing ' + filtered.length + ' of ' + ALL_ROLES.length + ' roles';
        }
    }

    function updateFilterBtnStates() {
        const ftagBtn = document.querySelector('#ftag-filter .filter-btn');
        const dispBtn = document.querySelector('#disp-filter .filter-btn');
        const typeBtn = document.querySelector('#type-filter .filter-btn');
        const baseBtn = document.querySelector('#base-filter .filter-btn');
        if (ftagBtn) ftagBtn.classList.toggle('has-filter', activeFilters.function_tags.size > 0);
        if (dispBtn) dispBtn.classList.toggle('has-filter', activeFilters.dispositions.size > 0);
        if (typeBtn) typeBtn.classList.toggle('has-filter', activeFilters.role_types.size > 0);
        if (baseBtn) baseBtn.classList.toggle('has-filter', activeFilters.baselined !== null);
    }

    // ===== Tab Switching =====
    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.tab === tab);
        });
        document.querySelectorAll('.tab-content').forEach(c => {
            c.style.display = c.id === 'tab-' + tab ? 'block' : 'none';
        });
        refreshCurrentTab();
    }

    function refreshCurrentTab() {
        switch (currentTab) {
            case 'dashboard': renderDashboard(); break;
            case 'tree': renderTree(); break;
            case 'graph': renderGraph(); break;
            case 'table': renderTable(); break;
        }
    }

    // ===== Dashboard =====
    function renderDashboard() {
        const roles = getFilteredRoles();
        const rels = getFilteredRelationships();
        const total = roles.length;

        // Compute stats
        const ftGroups = {};
        const disps = { 'Sanctioned': 0, 'To Be Retired': 0, 'TBD': 0 };
        let tools = 0, baselined = 0, withDesc = 0;

        roles.forEach(r => {
            const tags = r.function_tags || [];
            if (tags.length === 0) {
                ftGroups['Untagged'] = (ftGroups['Untagged'] || 0) + 1;
            } else {
                tags.forEach(ft => {
                    const code = ft.code || ft.name || ft;
                    ftGroups[code] = (ftGroups[code] || 0) + 1;
                });
            }
            const d = r.role_disposition || 'TBD';
            if (d in disps) disps[d]++;
            else disps['TBD']++;
            if (/tool|software/i.test(r.role_type || '') || (r.role_name || '').startsWith('[S]')) tools++;
            if (r.baselined) baselined++;
            if (r.description) withDesc++;
        });

        const descPct = total > 0 ? Math.round(withDesc / total * 100) : 0;
        const basePct = total > 0 ? Math.round(baselined / total * 100) : 0;
        const ftEntries = Object.entries(ftGroups).sort((a, b) => b[1] - a[1]);
        const uniqueFtags = ftEntries.length;

        // Build donut SVG
        const donutSvg = buildDonutSVG(ftEntries, total);

        // Build disposition bars
        const maxDisp = Math.max(disps['Sanctioned'], disps['To Be Retired'], disps['TBD'], 1);
        const dispBarsHtml =
            buildDispBar('Sanctioned', disps['Sanctioned'], total, 'sanctioned') +
            buildDispBar('To Be Retired', disps['To Be Retired'], total, 'retire') +
            buildDispBar('TBD', disps['TBD'], total, 'tbd');

        const container = document.getElementById('dashboard-content');
        container.innerHTML =
            '<div class="dash-hero animate-in">' +
                '<div class="dash-hero-title">Role Inheritance Overview</div>' +
                '<div class="dash-hero-sub">' + total + ' roles across ' + uniqueFtags + ' function tags with ' + rels.length + ' relationships</div>' +
            '</div>' +
            '<div class="dash-stats">' +
                buildStatCard('Total Roles', total, '&#x1f465;') +
                buildStatCard('Tools', tools, '&#x1f527;') +
                buildStatCard('Function Tags', uniqueFtags, '&#x1f3f7;') +
                buildStatCard('Relationships', rels.length, '&#x1f517;') +
            '</div>' +
            '<div class="dash-row">' +
                '<div class="dash-card animate-in">' +
                    '<div class="dash-card-title">Function Tag Distribution</div>' +
                    '<div class="donut-container">' + donutSvg +
                        '<div class="donut-legend">' +
                            ftEntries.slice(0, 8).map(([code, count]) =>
                                '<div class="donut-legend-item">' +
                                    '<span class="donut-legend-dot" style="background:' + (ftColorMap[code] || '#666') + '"></span>' +
                                    '<span class="donut-legend-label">' + escHtml(code) + '</span>' +
                                    '<span class="donut-legend-count">' + count + '</span>' +
                                '</div>'
                            ).join('') +
                            (ftEntries.length > 8 ? '<div class="donut-legend-item"><span class="donut-legend-label" style="color:var(--text-muted)">+' + (ftEntries.length - 8) + ' more</span></div>' : '') +
                        '</div>' +
                    '</div>' +
                '</div>' +
                '<div class="dash-card animate-in">' +
                    '<div class="dash-card-title">Role Disposition Breakdown</div>' +
                    dispBarsHtml +
                '</div>' +
            '</div>' +
            '<div class="dash-row">' +
                '<div class="dash-card animate-in">' +
                    '<div class="dash-card-title">Health Metrics</div>' +
                    '<div class="health-grid">' +
                        buildHealthMetric('Descriptions', descPct, descPct >= 70 ? 'var(--sanctioned)' : descPct >= 40 ? 'var(--warning)' : 'var(--error)') +
                        buildHealthMetric('Baselined', basePct, basePct >= 70 ? 'var(--sanctioned)' : basePct >= 40 ? 'var(--warning)' : 'var(--error)') +
                    '</div>' +
                '</div>' +
                '<div class="dash-card animate-in">' +
                    '<div class="dash-card-title">Role Types</div>' +
                    '<div>' + buildRoleTypeBars(roles) + '</div>' +
                '</div>' +
            '</div>';

        // Animate stat numbers
        setTimeout(() => animateCounters(), 100);
    }

    function buildStatCard(label, value, icon) {
        return '<div class="stat-card animate-in">' +
            '<div class="stat-icon">' + icon + '</div>' +
            '<div class="stat-number" data-target="' + value + '">0</div>' +
            '<div class="stat-label">' + escHtml(label) + '</div>' +
        '</div>';
    }

    function buildDonutSVG(entries, total) {
        if (total === 0 || entries.length === 0) {
            return '<svg width="160" height="160" viewBox="0 0 160 160"><circle cx="80" cy="80" r="60" fill="none" stroke="var(--border-default)" stroke-width="20"/><text x="80" y="84" text-anchor="middle" fill="var(--text-muted)" font-size="14">No data</text></svg>';
        }
        const cx = 80, cy = 80, r = 60;
        const circumference = 2 * Math.PI * r;
        let offset = 0;
        let paths = '';

        entries.forEach(([code, count]) => {
            const pct = count / total;
            const dashLen = pct * circumference;
            const color = ftColorMap[code] || '#666';
            paths += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" ' +
                     'stroke="' + color + '" stroke-width="20" ' +
                     'stroke-dasharray="' + dashLen + ' ' + (circumference - dashLen) + '" ' +
                     'stroke-dashoffset="' + (-offset) + '" ' +
                     'transform="rotate(-90 ' + cx + ' ' + cy + ')" ' +
                     'style="transition: stroke-dasharray 1s ease"/>';
            offset += dashLen;
        });

        return '<svg width="160" height="160" viewBox="0 0 160 160">' +
               '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="var(--border-subtle)" stroke-width="20"/>' +
               paths +
               '<text x="' + cx + '" y="' + (cy - 4) + '" text-anchor="middle" fill="var(--text-primary)" font-size="22" font-weight="700">' + total + '</text>' +
               '<text x="' + cx + '" y="' + (cy + 14) + '" text-anchor="middle" fill="var(--text-muted)" font-size="10">ROLES</text>' +
               '</svg>';
    }

    function buildDispBar(label, count, total, cls) {
        const pct = total > 0 ? Math.round(count / total * 100) : 0;
        return '<div class="disp-bar-row">' +
            '<span class="disp-bar-label">' + escHtml(label) + '</span>' +
            '<div class="disp-bar-track"><div class="disp-bar-fill ' + cls + '" style="width:' + pct + '%">' + count + '</div></div>' +
        '</div>';
    }

    function buildHealthMetric(label, pct, color) {
        return '<div class="health-item">' +
            '<div class="health-pct" style="color:' + color + '">' + pct + '%</div>' +
            '<div class="health-label">' + escHtml(label) + '</div>' +
            '<div class="health-bar"><div class="health-bar-fill" style="width:' + pct + '%;background:' + color + '"></div></div>' +
        '</div>';
    }

    function buildRoleTypeBars(roles) {
        const typeCounts = {};
        roles.forEach(r => {
            const t = r.role_type || 'Unknown';
            typeCounts[t] = (typeCounts[t] || 0) + 1;
        });
        const entries = Object.entries(typeCounts).sort((a, b) => b[1] - a[1]);
        const max = entries.length > 0 ? entries[0][1] : 1;
        return entries.map(([type, count]) => {
            const pct = Math.round(count / max * 100);
            return '<div class="disp-bar-row">' +
                '<span class="disp-bar-label" style="width:140px">' + escHtml(type) + '</span>' +
                '<div class="disp-bar-track"><div class="disp-bar-fill" style="width:' + pct + '%;background:var(--accent)">' + count + '</div></div>' +
            '</div>';
        }).join('');
    }

    function animateCounters() {
        document.querySelectorAll('.stat-number[data-target]').forEach(el => {
            const target = parseInt(el.dataset.target) || 0;
            const duration = 800;
            const start = performance.now();
            function step(now) {
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(eased * target);
                if (progress < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        });
    }

    // ===== Tree View =====
    function renderTree() {
        const roles = getFilteredRoles();
        const rels = getFilteredRelationships();
        const container = document.getElementById('tree-container');

        // Build parent-child map from relationships
        const childrenMap = {}; // parentId -> [childId, ...]
        const parentMap = {};   // childId -> parentId
        const roleById = {};

        roles.forEach(r => { roleById[r.id] = r; });

        // v4.7.2: Check if we have directional relationships or only shared-function
        const hasDirectional = rels.some(rel =>
            rel.relationship_type === 'inherits-from' ||
            rel.relationship_type === 'supervises' ||
            rel.relationship_type === 'reports_to'
        );

        rels.forEach(rel => {
            if (rel.relationship_type === 'inherits-from' || rel.relationship_type === 'supervises' || rel.relationship_type === 'reports_to') {
                let parentId, childId;
                if (rel.relationship_type === 'inherits-from') {
                    parentId = rel.target_role_id;
                    childId = rel.source_role_id;
                } else if (rel.relationship_type === 'supervises') {
                    parentId = rel.source_role_id;
                    childId = rel.target_role_id;
                } else {
                    parentId = rel.target_role_id;
                    childId = rel.source_role_id;
                }
                if (roleById[parentId] && roleById[childId]) {
                    if (!childrenMap[parentId]) childrenMap[parentId] = [];
                    childrenMap[parentId].push(childId);
                    parentMap[childId] = parentId;
                }
            }
        });

        let roots;
        if (!hasDirectional && roles.length > 0) {
            // v4.7.2: For shared-function only, group by function tags
            const ftGroups = {};
            const assigned = new Set();
            roles.forEach(r => {
                const tags = r.function_tags || [];
                if (tags.length > 0) {
                    const primaryTag = tags[0].name || tags[0].code || 'Untagged';
                    if (!ftGroups[primaryTag]) ftGroups[primaryTag] = { id: 'ftg_' + primaryTag, role_name: primaryTag, category: 'Function Group', function_tags: tags, _isGroup: true, _children: [] };
                    ftGroups[primaryTag]._children.push(r.id);
                    assigned.add(r.id);
                }
            });
            // Build virtual parent-child for function tag groups
            Object.values(ftGroups).forEach(g => {
                roleById[g.id] = g;
                childrenMap[g.id] = g._children;
                g._children.forEach(cid => { parentMap[cid] = g.id; });
            });
            const unassigned = roles.filter(r => !assigned.has(r.id));
            roots = [...Object.values(ftGroups), ...unassigned];
        } else {
            // Find roots (roles with no parent)
            roots = roles.filter(r => !parentMap[r.id]);
        }

        if (roots.length === 0) {
            container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted)">No hierarchy data available for the current filter selection.</div>';
            return;
        }

        function buildNode(role, isRoot) {
            const children = (childrenMap[role.id] || []).map(id => roleById[id]).filter(Boolean);
            const hasChildren = children.length > 0;
            const disp = role.role_disposition || 'TBD';
            const dispClass = disp === 'Sanctioned' ? 'disp-sanctioned' : disp === 'To Be Retired' ? 'disp-retire' : 'disp-tbd';
            const dispBadgeClass = disp === 'Sanctioned' ? 'tree-badge-sanctioned' : disp === 'To Be Retired' ? 'tree-badge-retire' : 'tree-badge-tbd';
            const dispIcon = disp === 'Sanctioned' ? '&#10003;' : disp === 'To Be Retired' ? '&#9888;' : '?';
            const nameClass = disp === 'To Be Retired' ? 'tree-name retired' : 'tree-name';
            const isTool = /tool|software/i.test(role.role_type || '') || (role.role_name || '').startsWith('[S]');
            const roleFtags = role.function_tags || [];
            const nodeId = 'tree-node-' + role.id;
            const childrenId = 'tree-children-' + role.id;

            let html = '<div class="tree-node' + (isRoot ? ' tree-root' : '') + '" id="' + nodeId + '">';
            html += '<div class="tree-item ' + dispClass + '" data-role-id="' + role.id + '" onclick="openDetailFromTree(event, ' + role.id + ')">';

            if (hasChildren) {
                html += '<button class="tree-toggle" onclick="toggleTreeNode(event, \\x27' + childrenId + '\\x27)" title="Toggle children">&#9660;</button>';
            } else {
                html += '<span class="tree-spacer"></span>';
            }

            html += '<span class="tree-icon">' + (isTool ? '&#9632;' : dispIcon) + '</span>';
            html += '<span class="' + nameClass + '" data-role-name="' + escAttr(role.role_name) + '">' + escHtml(role.role_name) + '</span>';
            if (editChanges.has(role.role_name)) {
                html += '<span class="role-modified-dot" title="Modified"></span>';
            }

            roleFtags.forEach(ft => {
                const ftCode = ft.code || ft.name || ft;
                const ftColor = ftColorMap[ftCode] || '#666';
                html += '<span class="tree-badge tree-badge-ftag" style="background:' + ftColor + '15;color:' + ftColor + '">' + escHtml(ftCode) + '</span>';
            });
            html += '<span class="tree-badge ' + dispBadgeClass + '">' + escHtml(disp) + '</span>';
            if (role.baselined) {
                html += '<span class="tree-baselined" title="Baselined">&#10003;</span>';
            }

            html += '</div>'; // end tree-item

            if (hasChildren) {
                html += '<div class="tree-children" id="' + childrenId + '">';
                children.sort((a, b) => (a.role_name || '').localeCompare(b.role_name || ''));
                children.forEach(child => { html += buildNode(child, false); });
                html += '</div>';
            }

            html += '</div>'; // end tree-node
            return html;
        }

        roots.sort((a, b) => (a.role_name || '').localeCompare(b.role_name || ''));
        container.innerHTML = roots.map(r => buildNode(r, true)).join('');

        // Highlight search matches
        if (searchText) {
            highlightTreeSearch(searchText);
        }
    }

    function toggleTreeNode(event, childrenId) {
        event.stopPropagation();
        const el = document.getElementById(childrenId);
        const btn = event.currentTarget;
        if (!el) return;
        if (el.classList.contains('collapsed')) {
            el.classList.remove('collapsed');
            el.style.maxHeight = el.scrollHeight + 'px';
            btn.classList.remove('collapsed');
            // After transition, set maxHeight to none so nested children can expand freely
            const onEnd = function() {
                el.removeEventListener('transitionend', onEnd);
                el.style.maxHeight = 'none';
            };
            el.addEventListener('transitionend', onEnd);
            // Also ensure all ancestor .tree-children have maxHeight:none
            let ancestor = el.parentElement;
            while (ancestor) {
                if (ancestor.classList && ancestor.classList.contains('tree-children') && !ancestor.classList.contains('collapsed')) {
                    ancestor.style.maxHeight = 'none';
                }
                ancestor = ancestor.parentElement;
            }
        } else {
            el.style.maxHeight = el.scrollHeight + 'px';
            requestAnimationFrame(() => {
                el.classList.add('collapsed');
                el.style.maxHeight = '0px';
                btn.classList.add('collapsed');
            });
        }
    }

    function expandAllTree() {
        document.querySelectorAll('.tree-children').forEach(el => {
            el.classList.remove('collapsed');
            el.style.maxHeight = 'none';
        });
        document.querySelectorAll('.tree-toggle').forEach(btn => {
            btn.classList.remove('collapsed');
        });
    }

    function collapseAllTree() {
        document.querySelectorAll('.tree-children').forEach(el => {
            el.classList.add('collapsed');
            el.style.maxHeight = '0px';
        });
        document.querySelectorAll('.tree-toggle').forEach(btn => {
            btn.classList.add('collapsed');
        });
    }

    function highlightTreeSearch(query) {
        const q = query.toLowerCase();
        document.querySelectorAll('.tree-item').forEach(item => {
            const nameEl = item.querySelector('.tree-name');
            if (nameEl) {
                const name = (nameEl.dataset.roleName || '').toLowerCase();
                item.classList.toggle('highlight', name.includes(q));
                // Expand parents of matching items
                if (name.includes(q)) {
                    let parent = item.parentElement;
                    while (parent) {
                        if (parent.classList && parent.classList.contains('tree-children')) {
                            parent.classList.remove('collapsed');
                            parent.style.maxHeight = 'none';
                            const toggle = parent.previousElementSibling?.querySelector('.tree-toggle');
                            if (toggle) toggle.classList.remove('collapsed');
                        }
                        parent = parent.parentElement;
                    }
                }
            }
        });
    }

    function openDetailFromTree(event, roleId) {
        if (event.target.closest('.tree-toggle')) return;
        const role = ALL_ROLES.find(r => r.id === roleId);
        if (role) openDetailPanel(role);
    }

    // ===== Graph View — Drill-Down Navigation =====
    let graphNodes = [];
    let graphEdges = [];
    let graphClusters = [];
    let graphClusterNames = [];
    let drillState = {
        layer: 0,          // 0=clusters overview, 1=cluster roots, 2=node neighborhood
        clusterId: -1,
        focusNodeId: null
    };

    function renderGraph() {
        const roles = getFilteredRoles();
        const rels = getFilteredRelationships();
        const container = document.getElementById('graph-container');
        const content = document.getElementById('drill-content');
        const breadcrumb = document.getElementById('drill-breadcrumb');

        if (roles.length === 0) {
            breadcrumb.innerHTML = '';
            content.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:14px;">No roles to display</div>';
            return;
        }

        const roleById = {};
        roles.forEach(r => { roleById[r.id] = r; });

        // Build connected nodes only
        const connectedIds = new Set();
        rels.forEach(rel => {
            if (roleById[rel.source_role_id] && roleById[rel.target_role_id]) {
                connectedIds.add(rel.source_role_id);
                connectedIds.add(rel.target_role_id);
            }
        });

        const connectedRoles = roles.filter(r => connectedIds.has(r.id));

        graphNodes = connectedRoles.map(r => ({
            id: r.id, role: r,
            color: ((r.function_tags || [])[0] ? ftColorMap[(r.function_tags[0].code || r.function_tags[0].name)] : null) || '#666'
        }));

        const nodeMap = {};
        graphNodes.forEach(n => { nodeMap[n.id] = n; });

        graphEdges = rels.filter(rel => nodeMap[rel.source_role_id] && nodeMap[rel.target_role_id]).map(rel => ({
            source: nodeMap[rel.source_role_id],
            target: nodeMap[rel.target_role_id],
            type: rel.relationship_type
        }));

        graphClusters = findClusters(graphNodes, graphEdges);

        // Name each cluster after its most-connected hub node
        graphClusterNames = graphClusters.map(cluster => {
            const connCount = {};
            graphEdges.forEach(e => {
                if (cluster.some(n => n.id === e.source.id) && cluster.some(n => n.id === e.target.id)) {
                    connCount[e.source.id] = (connCount[e.source.id] || 0) + 1;
                    connCount[e.target.id] = (connCount[e.target.id] || 0) + 1;
                }
            });
            const hub = cluster.reduce((best, n) => (connCount[n.id] || 0) > (connCount[best.id] || 0) ? n : best, cluster[0]);
            return hub.role.role_name;
        });

        // Validate drillState against current data
        if (drillState.layer === 1 && (drillState.clusterId < 0 || drillState.clusterId >= graphClusters.length)) {
            drillState = { layer: 0, clusterId: -1, focusNodeId: null };
        }
        if (drillState.layer === 2 && !nodeMap[drillState.focusNodeId]) {
            drillState = { layer: 0, clusterId: -1, focusNodeId: null };
        }

        // Render breadcrumb
        renderDrillBreadcrumb(breadcrumb);

        // Render current layer
        switch (drillState.layer) {
            case 0: renderClusterOverview(content, roles.length); break;
            case 1: renderClusterRoots(content); break;
            case 2: renderNodeNeighborhood(content); break;
        }
    }

    function renderDrillBreadcrumb(el) {
        let html = '';
        if (drillState.layer > 0) {
            html += '<button class="drill-back-btn" onclick="drillBack()">&#8592;</button>';
        }
        html += '<span class="drill-breadcrumb-item' + (drillState.layer === 0 ? ' current' : '') + '" onclick="drillTo(0)">' +
            'All Clusters (' + graphClusters.length + ')' + '</span>';

        if (drillState.layer >= 1 && drillState.clusterId >= 0) {
            const cluster = graphClusters[drillState.clusterId];
            const cName = graphClusterNames[drillState.clusterId] || ('Cluster ' + (drillState.clusterId + 1));
            html += '<span class="drill-breadcrumb-sep">&#9656;</span>';
            html += '<span class="drill-breadcrumb-item' + (drillState.layer === 1 ? ' current' : '') + '" ' +
                'onclick="drillTo(1, ' + drillState.clusterId + ')">' +
                escHtml(cName) + ' Group (' + cluster.length + ')</span>';
        }

        if (drillState.layer === 2 && drillState.focusNodeId !== null) {
            const node = graphNodes.find(n => n.id === drillState.focusNodeId);
            if (node) {
                html += '<span class="drill-breadcrumb-sep">&#9656;</span>';
                html += '<span class="drill-breadcrumb-item current">' + escHtml(node.role.role_name) + '</span>';
            }
        }

        el.innerHTML = html;
    }

    // ---- Layer 0: Cluster Overview ----
    function renderClusterOverview(content, totalRoles) {
        const unconnected = totalRoles - graphNodes.length;
        let html = '<div class="drill-cluster-grid">';

        graphClusters.forEach((cluster, ci) => {
            const sanctioned = cluster.filter(n => n.role.role_disposition === 'Sanctioned').length;
            const retire = cluster.filter(n => n.role.role_disposition === 'To Be Retired').length;
            const tbd = cluster.length - sanctioned - retire;
            const total = cluster.length;

            // Top role names (sorted by connection count)
            const connCount = {};
            graphEdges.forEach(e => {
                if (cluster.some(n => n.id === e.source.id) && cluster.some(n => n.id === e.target.id)) {
                    connCount[e.source.id] = (connCount[e.source.id] || 0) + 1;
                    connCount[e.target.id] = (connCount[e.target.id] || 0) + 1;
                }
            });
            const sorted = [...cluster].sort((a, b) => (connCount[b.id] || 0) - (connCount[a.id] || 0));
            const topNames = sorted.slice(0, 4);
            const remaining = total - topNames.length;

            // Edge count for this cluster
            const clusterEdgeCount = graphEdges.filter(e =>
                cluster.some(n => n.id === e.source.id) && cluster.some(n => n.id === e.target.id)
            ).length;

            const clusterName = graphClusterNames[ci] || ('Cluster ' + (ci + 1));
            html += '<div class="drill-cluster-card" style="animation-delay:' + (ci * 0.04) + 's;" onclick="drillTo(1, ' + ci + ')">' +
                '<div class="drill-cluster-header">' +
                    '<span class="drill-cluster-title">' + escHtml(clusterName) + ' Group</span>' +
                    '<span class="drill-cluster-count">' + total + ' role' + (total !== 1 ? 's' : '') + '</span>' +
                '</div>' +
                '<div class="drill-cluster-roles">';

            // Show other top roles (excluding the hub name already in title)
            const otherNames = topNames.filter(n => n.role.role_name !== clusterName);
            otherNames.slice(0, 4).forEach(n => {
                html += '<span>' + escHtml(n.role.role_name) + '</span>';
            });
            const othersRemaining = total - otherNames.slice(0, 4).length - 1; // -1 for the hub
            if (othersRemaining > 0) {
                html += '<span style="color:var(--text-muted);">+' + othersRemaining + ' more</span>';
            }

            html += '</div>' +
                '<div class="drill-mini-bar">';
            if (sanctioned > 0) html += '<div class="drill-mini-bar-seg" style="width:' + (sanctioned / total * 100) + '%;background:var(--sanctioned);"></div>';
            if (retire > 0) html += '<div class="drill-mini-bar-seg" style="width:' + (retire / total * 100) + '%;background:var(--retire);"></div>';
            if (tbd > 0) html += '<div class="drill-mini-bar-seg" style="width:' + (tbd / total * 100) + '%;background:var(--tbd);"></div>';
            html += '</div>' +
                '<div class="drill-cluster-stats">' +
                    '<span>' + clusterEdgeCount + ' relationship' + (clusterEdgeCount !== 1 ? 's' : '') + '</span>' +
                    '<span>' + sanctioned + ' sanctioned</span>' +
                '</div>' +
            '</div>';
        });

        if (unconnected > 0) {
            html += '<div class="drill-cluster-card" style="opacity:0.6;cursor:default;border-style:dashed;">' +
                '<div class="drill-cluster-header">' +
                    '<span class="drill-cluster-title" style="color:var(--text-muted);">Unconnected Roles</span>' +
                    '<span class="drill-cluster-count">' + unconnected + '</span>' +
                '</div>' +
                '<div class="drill-cluster-roles"><span style="color:var(--text-muted);">Roles with no relationships are not shown in the graph view.</span></div>' +
            '</div>';
        }

        html += '</div>';
        content.innerHTML = html;
    }

    // ---- Layer 1: Cluster Root Nodes ----
    function renderClusterRoots(content) {
        const cluster = graphClusters[drillState.clusterId];
        if (!cluster) return;

        const clusterIds = new Set(cluster.map(n => n.id));
        const clusterEdges = graphEdges.filter(e => clusterIds.has(e.source.id) && clusterIds.has(e.target.id));

        // Find root nodes: nodes that are NOT a child (no edge points TO them as child)
        // For inherits-from: source inherits from target, so source is child, target is parent
        // For supervises: source supervises target, so target is child
        // For shared-function: no direction, so pick most-connected as hubs
        const hasDirectional = clusterEdges.some(e => e.type === 'inherits-from' || e.type === 'supervises' || e.type === 'reports_to');
        const childIds = new Set();
        if (hasDirectional) {
            clusterEdges.forEach(e => {
                if (e.type === 'inherits-from') childIds.add(e.source.id);
                else if (e.type === 'supervises') childIds.add(e.target.id);
                else if (e.type === 'reports_to') childIds.add(e.source.id);
            });
        }

        let rootNodes;
        if (hasDirectional) {
            rootNodes = cluster.filter(n => !childIds.has(n.id));
            if (rootNodes.length === 0) rootNodes = [...cluster];
        } else {
            // For shared-function only: pick top hub nodes by connection count
            const connCount = {};
            clusterEdges.forEach(e => {
                connCount[e.source.id] = (connCount[e.source.id] || 0) + 1;
                connCount[e.target.id] = (connCount[e.target.id] || 0) + 1;
            });
            rootNodes = [...cluster].sort((a, b) => (connCount[b.id] || 0) - (connCount[a.id] || 0));
            rootNodes = rootNodes.slice(0, Math.min(8, Math.ceil(cluster.length * 0.3)));
        }

        // Count children/connections for each root
        const childCount = {};
        const descendantCount = {};
        cluster.forEach(n => {
            // Direct children (or direct connections for shared-function)
            const children = clusterEdges.filter(e =>
                (e.type === 'inherits-from' && e.target.id === n.id) ||
                (e.type === 'supervises' && e.source.id === n.id) ||
                (e.type === 'shared-function' && (e.source.id === n.id || e.target.id === n.id))
            ).length;
            childCount[n.id] = children;
        });

        // Count all descendants (BFS)
        cluster.forEach(n => {
            const visited = new Set([n.id]);
            let frontier = [n.id];
            let count = 0;
            while (frontier.length > 0) {
                const next = [];
                frontier.forEach(nid => {
                    clusterEdges.forEach(e => {
                        let childId = null;
                        if (e.type === 'inherits-from' && e.target.id === nid) childId = e.source.id;
                        else if (e.type === 'supervises' && e.source.id === nid) childId = e.target.id;
                        else if (e.type === 'shared-function') {
                            if (e.source.id === nid) childId = e.target.id;
                            else if (e.target.id === nid) childId = e.source.id;
                        }
                        if (childId && !visited.has(childId)) {
                            visited.add(childId);
                            next.push(childId);
                            count++;
                        }
                    });
                });
                frontier = next;
            }
            descendantCount[n.id] = count;
        });

        // Sort roots: most descendants first
        rootNodes.sort((a, b) => (descendantCount[b.id] || 0) - (descendantCount[a.id] || 0));

        // CSS grid of root node cards (scrollable, like Layer 0)
        let html = '<div style="padding:12px 20px 0;color:var(--text-muted);font-size:12px;font-weight:600;letter-spacing:0.5px;text-transform:uppercase;">' +
            rootNodes.length + ' Root Role' + (rootNodes.length !== 1 ? 's' : '') + ' in ' + escHtml(graphClusterNames[drillState.clusterId] || 'Cluster') + ' Group' +
            '</div>';
        html += '<div class="drill-cluster-grid" style="max-height:calc(100% - 40px);">';

        rootNodes.forEach((node, ri) => {
            const disp = node.role.role_disposition || 'TBD';
            const borderColor = disp === 'Sanctioned' ? 'var(--sanctioned)' : disp === 'To Be Retired' ? 'var(--retire)' : 'var(--tbd)';
            const children = childCount[node.id] || 0;
            const desc = descendantCount[node.id] || 0;

            // Find direct children/connected names
            const directChildNames = [];
            clusterEdges.forEach(e => {
                let childNode = null;
                if (e.type === 'inherits-from' && e.target.id === node.id) childNode = e.source;
                else if (e.type === 'supervises' && e.source.id === node.id) childNode = e.target;
                else if (e.type === 'shared-function') {
                    if (e.source.id === node.id) childNode = e.target;
                    else if (e.target.id === node.id) childNode = e.source;
                }
                if (childNode) directChildNames.push(childNode.role.role_name);
            });

            html += '<div class="drill-cluster-card" style="animation-delay:' + (ri * 0.04) + 's;border-left:3px solid ' + borderColor + ';" ' +
                'onclick="drillRootClick(' + node.id + ', ' + children + ')">' +
                '<div class="drill-cluster-header">' +
                    '<span class="drill-cluster-title" style="font-size:14px;">' + escHtml(node.role.role_name) + '</span>' +
                    (desc > 0 ? '<span class="drill-cluster-count" style="background:var(--accent);color:var(--bg-surface);font-weight:600;">+' + desc + ' desc.</span>' : '') +
                '</div>';

            // Show disposition and type
            html += '<div style="font-size:11px;color:var(--text-muted);">' + escHtml(disp);
            if (node.role.role_type) html += ' &middot; ' + escHtml(node.role.role_type);
            html += '</div>';

            // Show direct children if any
            if (directChildNames.length > 0) {
                html += '<div class="drill-cluster-roles">';
                directChildNames.slice(0, 3).forEach(name => {
                    html += '<span style="font-size:11px;">&#8627; ' + escHtml(name) + '</span>';
                });
                if (directChildNames.length > 3) {
                    html += '<span style="color:var(--text-muted);font-size:11px;">+' + (directChildNames.length - 3) + ' more children</span>';
                }
                html += '</div>';
            } else {
                html += '<div style="font-size:11px;color:var(--text-muted);font-style:italic;">Leaf node (no children)</div>';
            }

            html += '</div>';
        });

        html += '</div>';
        content.innerHTML = html;
    }

    function drillRootClick(nodeId, childrenCount) {
        if (childrenCount > 0) {
            drillTo(2, drillState.clusterId, nodeId);
        } else {
            const node = graphNodes.find(n => n.id === nodeId);
            if (node) openDetailPanel(node.role);
        }
    }

    // ---- Layer 2: Node Neighborhood ----
    function renderNodeNeighborhood(content) {
        const focusNode = graphNodes.find(n => n.id === drillState.focusNodeId);
        if (!focusNode) return;

        // Find direct parents, children, and peers
        const parents = [];
        const children = [];
        const peers = [];
        graphEdges.forEach(e => {
            if (e.type === 'inherits-from' && e.source.id === focusNode.id) {
                parents.push(e.target);
            } else if (e.type === 'inherits-from' && e.target.id === focusNode.id) {
                children.push(e.source);
            } else if (e.type === 'supervises' && e.source.id === focusNode.id) {
                children.push(e.target);
            } else if (e.type === 'supervises' && e.target.id === focusNode.id) {
                parents.push(e.source);
            } else if (e.type === 'reports_to' && e.source.id === focusNode.id) {
                parents.push(e.target);
            } else if (e.type === 'reports_to' && e.target.id === focusNode.id) {
                children.push(e.source);
            } else if (e.type === 'shared-function') {
                if (e.source.id === focusNode.id) peers.push(e.target);
                else if (e.target.id === focusNode.id) peers.push(e.source);
            } else if (e.type === 'uses_tool' || e.type === 'uses-tool') {
                if (e.source.id === focusNode.id) children.push(e.target);
                else if (e.target.id === focusNode.id) parents.push(e.source);
            } else if (e.type === 'alias_of' || e.type === 'alias-of') {
                if (e.source.id === focusNode.id) children.push(e.target);
                else if (e.target.id === focusNode.id) children.push(e.source);
            }
        });
        // For shared-function only graphs, treat peers as children for layout
        if (parents.length === 0 && children.length === 0 && peers.length > 0) {
            peers.forEach(p => children.push(p));
        }

        // De-duplicate
        const seen = new Set();
        const dedupe = (arr) => {
            const result = [];
            arr.forEach(n => { if (!seen.has(n.id) && n.id !== focusNode.id) { seen.add(n.id); result.push(n); } });
            return result;
        };
        const uniqueParents = dedupe(parents);
        seen.clear(); seen.add(focusNode.id); uniqueParents.forEach(n => seen.add(n.id));
        const uniqueChildren = dedupe(children);

        const wrap = document.createElement('div');
        wrap.className = 'drill-svg-wrap';
        wrap.innerHTML = '<svg id="drill-svg" width="100%" height="100%" style="display:block;"></svg>';
        content.innerHTML = '';
        content.appendChild(wrap);

        const svg = wrap.querySelector('svg');
        const w = wrap.clientWidth || 900;
        const h = wrap.clientHeight || 600;

        const centerX = w / 2;
        const centerR = 36;
        const neighborR = 20;
        const nodeSlotW = 110; // width per child node slot
        const nodeSlotH = 80;  // height per child row

        // Calculate how many nodes fit per row
        const maxPerRow = Math.max(1, Math.floor((w - 60) / nodeSlotW));

        // Layout: parents at top, center in middle, children below
        // Calculate vertical positions based on counts
        const parentRows = uniqueParents.length > 0 ? Math.ceil(uniqueParents.length / maxPerRow) : 0;
        const childRows = uniqueChildren.length > 0 ? Math.ceil(uniqueChildren.length / maxPerRow) : 0;

        const parentSectionH = parentRows > 0 ? 40 + parentRows * nodeSlotH : 0;
        const centerSectionH = 120;
        const childSectionH = childRows > 0 ? 30 + childRows * nodeSlotH : 0;
        const totalH = Math.max(h, parentSectionH + centerSectionH + childSectionH + 80);

        // Set SVG height to accommodate content
        svg.setAttribute('height', totalH);
        wrap.style.overflowY = 'auto';

        let curY = 30;
        let svgContent = '<defs><marker id="drill-arrowhead" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="8" markerHeight="6" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="var(--text-muted)" opacity="0.5"/></marker></defs>';

        // Parents section
        if (uniqueParents.length > 0) {
            svgContent += '<text x="' + centerX + '" y="' + curY + '" text-anchor="middle" fill="var(--text-muted)" font-size="11" font-weight="600" letter-spacing="0.5">INHERITS FROM</text>';
            curY += 20;

            const pPerRow = Math.min(uniqueParents.length, maxPerRow);
            uniqueParents.forEach((pn, i) => {
                const row = Math.floor(i / pPerRow);
                const col = i % pPerRow;
                const rowCount = Math.min(pPerRow, uniqueParents.length - row * pPerRow);
                const rowStartX = centerX - (rowCount - 1) * nodeSlotW / 2;
                const px = rowStartX + col * nodeSlotW;
                const py = curY + row * nodeSlotH + neighborR + 10;
                pn._cx = px; pn._cy = py;
                svgContent += buildDrillNode(pn, px, py, neighborR, nodeSlotW - 10, i);
            });
            curY += parentRows * nodeSlotH + 10;
        }

        // Center node
        const centerY = curY + centerR + 10;
        curY = centerY;

        // Arrows from parents to center
        uniqueParents.forEach((pn, ai) => {
            const angle = Math.atan2(centerY - pn._cy, centerX - pn._cx);
            const sx = pn._cx + Math.cos(angle) * (neighborR + 2);
            const sy = pn._cy + Math.sin(angle) * (neighborR + 2);
            const ex = centerX - Math.cos(angle) * (centerR + 6);
            const ey = centerY - Math.sin(angle) * (centerR + 6);
            svgContent += '<line x1="' + sx + '" y1="' + sy + '" x2="' + ex + '" y2="' + ey + '" class="drill-arrow-line" style="animation-delay:' + (ai * 0.06 + 0.2) + 's;"/>';
        });

        const disp = focusNode.role.role_disposition || 'TBD';
        const strokeColor = disp === 'Sanctioned' ? 'var(--sanctioned)' : disp === 'To Be Retired' ? 'var(--retire)' : 'var(--tbd)';
        const strokeDash = disp === 'To Be Retired' ? '3,2' : disp === 'TBD' ? '2,2' : '';
        svgContent += '<circle cx="' + centerX + '" cy="' + centerY + '" r="' + centerR + '" ' +
            'fill="' + focusNode.color + '" fill-opacity="0.25" stroke="' + strokeColor + '" stroke-width="3"' +
            (strokeDash ? ' stroke-dasharray="' + strokeDash + '"' : '') + ' style="cursor:pointer;animation:centerPulse 0.5s ease forwards;transform-origin:' + centerX + 'px ' + centerY + 'px;" class="drill-center-circle"/>';

        // Center label (inside circle)
        const centerName = focusNode.role.role_name;
        const centerLines = wrapText(centerName, 200, 14);
        centerLines.forEach((line, li) => {
            svgContent += '<text x="' + centerX + '" y="' + (centerY + centerR + 18 + li * 17) + '" ' +
                'text-anchor="middle" fill="var(--text-primary)" font-size="14" font-weight="700" pointer-events="none">' +
                escHtml(line) + '</text>';
        });

        // Center metadata
        const metaY = centerY + centerR + 18 + centerLines.length * 17 + 4;
        svgContent += '<text x="' + centerX + '" y="' + metaY + '" text-anchor="middle" fill="var(--text-muted)" font-size="11" pointer-events="none">' +
            escHtml(disp) +
            (focusNode.role.role_type ? ' \\u00B7 ' + escHtml(focusNode.role.role_type) : '') +
            ((focusNode.role.function_tags || []).length > 0 ? ' \\u00B7 ' + escHtml((focusNode.role.function_tags[0].code || focusNode.role.function_tags[0].name)) : '') +
            '</text>';

        curY += centerR + 20 + centerLines.length * 17 + 20;

        // Children section (multi-row grid)
        if (uniqueChildren.length > 0) {
            svgContent += '<text x="' + centerX + '" y="' + curY + '" text-anchor="middle" fill="var(--text-muted)" font-size="11" font-weight="600" letter-spacing="0.5">INHERITED BY (' + uniqueChildren.length + ')</text>';
            curY += 20;

            const cPerRow = Math.min(uniqueChildren.length, maxPerRow);
            uniqueChildren.forEach((cn, i) => {
                const row = Math.floor(i / cPerRow);
                const col = i % cPerRow;
                const rowCount = Math.min(cPerRow, uniqueChildren.length - row * cPerRow);
                const rowStartX = centerX - (rowCount - 1) * nodeSlotW / 2;
                const cx2 = rowStartX + col * nodeSlotW;
                const cy2 = curY + row * nodeSlotH + neighborR + 10;
                cn._cx = cx2; cn._cy = cy2;

                // Arrow from center to first row only (to avoid visual clutter)
                if (row === 0) {
                    const angle = Math.atan2(cy2 - centerY, cx2 - centerX);
                    const sx = centerX + Math.cos(angle) * (centerR + 2);
                    const sy = centerY + Math.sin(angle) * (centerR + 2);
                    const ex = cx2 - Math.cos(angle) * (neighborR + 6);
                    const ey = cy2 - Math.sin(angle) * (neighborR + 6);
                    svgContent += '<line x1="' + sx + '" y1="' + sy + '" x2="' + ex + '" y2="' + ey + '" class="drill-arrow-line" style="animation-delay:' + (i * 0.04 + 0.3) + 's;"/>';
                }

                svgContent += buildDrillNode(cn, cx2, cy2, neighborR, nodeSlotW - 10, i + uniqueParents.length);
            });
        }

        svg.innerHTML = svgContent;

        // Click handler
        svg.addEventListener('click', (e) => {
            // Check center circle click
            if (e.target.classList && e.target.classList.contains('drill-center-circle')) {
                openDetailPanel(focusNode.role);
                return;
            }

            const nodeEl = e.target.closest('.drill-node');
            if (!nodeEl) return;
            const nodeId = parseInt(nodeEl.dataset.nodeId);
            const node = graphNodes.find(n => n.id === nodeId);
            if (!node) return;

            // Check if this node has its own children/parents to drill into
            const hasNeighbors = graphEdges.some(e =>
                e.source.id === nodeId || e.target.id === nodeId
            );
            if (hasNeighbors) {
                drillTo(2, drillState.clusterId, nodeId);
            } else {
                openDetailPanel(node.role);
            }
        });

        // Info
        const info = document.createElement('div');
        info.className = 'drill-info-panel';
        info.innerHTML = (uniqueParents.length + uniqueChildren.length) + ' direct connection' + ((uniqueParents.length + uniqueChildren.length) !== 1 ? 's' : '') +
            ' &middot; Click a neighbor to drill deeper &middot; Click center node to view details';
        content.appendChild(info);
    }

    function buildDrillNode(node, x, y, r, maxLabelW, animIdx) {
        const disp = node.role.role_disposition || 'TBD';
        const strokeColor = disp === 'Sanctioned' ? 'var(--sanctioned)' : disp === 'To Be Retired' ? 'var(--retire)' : 'var(--tbd)';
        const strokeDash = disp === 'To Be Retired' ? '3,2' : disp === 'TBD' ? '2,2' : '';

        // Count this node\'s own connections for badge
        const ownChildren = graphEdges.filter(e =>
            (e.type === 'inherits-from' && e.target.id === node.id) ||
            (e.type === 'supervises' && e.source.id === node.id)
        ).length;

        const delay = (animIdx || 0) * 0.05 + 0.15;
        let svg = '<g class="drill-node" data-node-id="' + node.id + '" style="cursor:pointer;animation-delay:' + delay + 's;">' +
            '<circle class="drill-node-circle" cx="' + x + '" cy="' + y + '" r="' + r + '" ' +
                'fill="' + node.color + '" fill-opacity="0.2" stroke="' + strokeColor + '" stroke-width="2"' +
                (strokeDash ? ' stroke-dasharray="' + strokeDash + '"' : '') + '/>';

        // Label
        const name = node.role.role_name;
        const lines = wrapText(name, maxLabelW || 140, 11);
        lines.forEach((line, li) => {
            svg += '<text x="' + x + '" y="' + (y + r + 14 + li * 13) + '" ' +
                'text-anchor="middle" fill="var(--text-primary)" font-size="11" font-weight="500" pointer-events="none">' +
                escHtml(line) + '</text>';
        });

        // Child count badge
        if (ownChildren > 0) {
            const badgeText = '+' + ownChildren;
            const badgeW = badgeText.length * 7 + 10;
            svg += '<rect x="' + (x + r * 0.5) + '" y="' + (y - r - 6) + '" width="' + badgeW + '" height="16" rx="8" fill="var(--accent)" opacity="0.85"/>' +
                '<text x="' + (x + r * 0.5 + badgeW / 2) + '" y="' + (y - r + 6) + '" text-anchor="middle" fill="var(--bg-surface)" font-size="10" font-weight="600" pointer-events="none">' + badgeText + '</text>';
        }

        svg += '</g>';
        return svg;
    }

    // Text wrapping helper
    function wrapText(text, maxW, fontSize) {
        const charW = fontSize * 0.58;
        const maxChars = Math.floor(maxW / charW);
        if (text.length <= maxChars) return [text];
        const words = text.split(/\\s+/);
        const lines = [];
        let line = '';
        words.forEach(word => {
            if ((line + ' ' + word).trim().length > maxChars && line.length > 0) {
                lines.push(line.trim());
                line = word;
            } else {
                line = (line + ' ' + word).trim();
            }
        });
        if (line) lines.push(line);
        return lines.slice(0, 3); // Max 3 lines
    }

    // ---- Navigation Functions ----
    function drillTo(layer, clusterId, focusNodeId) {
        drillState.layer = layer;
        if (clusterId !== undefined) drillState.clusterId = clusterId;
        if (focusNodeId !== undefined) drillState.focusNodeId = focusNodeId;
        if (layer === 0) { drillState.clusterId = -1; drillState.focusNodeId = null; }
        renderGraph();
    }

    function drillBack() {
        if (drillState.layer === 2) {
            drillTo(1, drillState.clusterId);
        } else if (drillState.layer === 1) {
            drillTo(0);
        }
    }

    function findClusters(nodes, edges) {
        const parent = {};
        nodes.forEach(n => { parent[n.id] = n.id; });
        function find(x) { return parent[x] === x ? x : (parent[x] = find(parent[x])); }
        function union(a, b) { parent[find(a)] = find(b); }
        edges.forEach(e => { union(e.source.id, e.target.id); });

        const groups = {};
        nodes.forEach(n => {
            const root = find(n.id);
            if (!groups[root]) groups[root] = [];
            groups[root].push(n);
        });
        return Object.values(groups).sort((a, b) => b.length - a.length);
    }

    function subCountForNode(nodeId) {
        return graphEdges.filter(e =>
            (e.type === 'inherits-from' && e.target.id === nodeId) ||
            (e.type === 'supervises' && e.source.id === nodeId) ||
            (e.type === 'shared-function' && (e.source.id === nodeId || e.target.id === nodeId))
        ).length;
    }
    function parentCountForNode(nodeId) {
        return graphEdges.filter(e =>
            (e.type === 'inherits-from' && e.source.id === nodeId) ||
            (e.type === 'supervises' && e.target.id === nodeId) ||
            (e.type === 'shared-function' && (e.source.id === nodeId || e.target.id === nodeId))
        ).length;
    }

    // ===== Table View =====
    function renderTable() {
        const roles = getFilteredRoles();
        const rels = getFilteredRelationships();

        // Build relationship maps
        const reportsTo = {};
        const directReports = {};
        rels.forEach(rel => {
            if (rel.relationship_type === 'inherits-from') {
                reportsTo[rel.source_role_id] = rel.target_role_name;
                if (!directReports[rel.target_role_id]) directReports[rel.target_role_id] = [];
                directReports[rel.target_role_id].push(rel.source_role_name);
            } else if (rel.relationship_type === 'supervises') {
                reportsTo[rel.target_role_id] = rel.source_role_name;
                if (!directReports[rel.source_role_id]) directReports[rel.source_role_id] = [];
                directReports[rel.source_role_id].push(rel.target_role_name);
            } else if (rel.relationship_type === 'reports_to') {
                reportsTo[rel.source_role_id] = rel.target_role_name;
                if (!directReports[rel.target_role_id]) directReports[rel.target_role_id] = [];
                directReports[rel.target_role_id].push(rel.source_role_name);
            }
        });

        // Sort
        const sorted = [...roles].sort((a, b) => {
            let va, vb;
            switch (sortColumn) {
                case 'role_name': va = a.role_name || ''; vb = b.role_name || ''; break;
                case 'function_tags': va = ((a.function_tags || [])[0] || {}).code || ''; vb = ((b.function_tags || [])[0] || {}).code || ''; break;
                case 'role_type': va = a.role_type || ''; vb = b.role_type || ''; break;
                case 'disposition': va = a.role_disposition || ''; vb = b.role_disposition || ''; break;
                case 'baselined': va = a.baselined ? '1' : '0'; vb = b.baselined ? '1' : '0'; break;
                case 'reports_to': va = reportsTo[a.id] || ''; vb = reportsTo[b.id] || ''; break;
                case 'direct_reports':
                    va = (directReports[a.id] || []).length;
                    vb = (directReports[b.id] || []).length;
                    return sortDirection === 'asc' ? va - vb : vb - va;
                case 'nimbus': va = (a.tracings || []).length; vb = (b.tracings || []).length; return sortDirection === 'asc' ? va - vb : vb - va;
                case 'description': va = a.description || ''; vb = b.description || ''; break;
                default: va = a.role_name || ''; vb = b.role_name || '';
            }
            if (typeof va === 'string') {
                const cmp = va.localeCompare(vb);
                return sortDirection === 'asc' ? cmp : -cmp;
            }
            return sortDirection === 'asc' ? va - vb : vb - va;
        });

        const columns = [
            { key: 'role_name', label: 'Role Name' },
            { key: 'function_tags', label: 'Function Tags' },
            { key: 'role_type', label: 'Role Type' },
            { key: 'disposition', label: 'Disposition' },
            { key: 'baselined', label: 'Baselined' },
            { key: 'reports_to', label: 'Inherits From' },
            { key: 'direct_reports', label: 'Inherited By' },
            { key: 'nimbus', label: 'Nimbus' },
            { key: 'description', label: 'Description' }
        ];

        // Header
        const thead = document.getElementById('table-head');
        thead.innerHTML = '<tr>' + columns.map(col => {
            const isSorted = sortColumn === col.key;
            const arrow = isSorted ? (sortDirection === 'asc' ? ' &#9650;' : ' &#9660;') : '';
            return '<th class="' + (isSorted ? 'sorted' : '') + '" onclick="sortTable(\\x27' + col.key + '\\x27)">' +
                   col.label + '<span class="sort-arrow">' + arrow + '</span></th>';
        }).join('') + '</tr>';

        // Body
        const tbody = document.getElementById('table-body');
        tbody.innerHTML = sorted.map(r => {
            const disp = r.role_disposition || 'TBD';
            const dispClass = disp === 'Sanctioned' ? 'table-badge-sanctioned' : disp === 'To Be Retired' ? 'table-badge-retire' : 'table-badge-tbd';
            const drCount = (directReports[r.id] || []).length;
            const rt = reportsTo[r.id] || '-';
            return '<tr class="' + (editChanges.has(r.role_name) ? 'row-modified' : '') + '" onclick="openDetailPanel(ALL_ROLES.find(x => x.id === ' + r.id + '))">' +
                '<td><strong>' + escHtml(r.role_name) + '</strong></td>' +
                '<td>' + ((r.function_tags || []).length > 0 ? (r.function_tags || []).map(ft => { const c = ft.code || ft.name || ft; const clr = ftColorMap[c] || '#666'; return '<span class="table-ftag-badge" style="background:' + clr + '15;color:' + clr + '">' + escHtml(c) + '</span>'; }).join(' ') : '<span style="color:var(--text-muted)">-</span>') + '</td>' +
                '<td>' + escHtml(r.role_type || '-') + '</td>' +
                '<td><span class="table-badge ' + dispClass + '">' + escHtml(disp) + '</span></td>' +
                '<td>' + (r.baselined ? '<span style="color:var(--sanctioned);font-weight:700">&#10003;</span>' : '-') + '</td>' +
                '<td>' + escHtml(rt) + '</td>' +
                '<td>' + drCount + '</td>' +
                '<td>' + ((r.tracings || []).length > 0 ? '<ul class="nimbus-link-list">' + (r.tracings || []).map(function(t) { return '<li><a href="' + (t.url || '#') + '" target="_blank" rel="noopener" onclick="event.stopPropagation()" class="nimbus-link" title="Open in Nimbus">&#128279; ' + escHtml(t.title || 'Nimbus') + '</a></li>'; }).join('') + '</ul>' : '<span style="color:var(--text-muted)">-</span>') + '</td>' +
                '<td><span class="table-desc">' + escHtml(r.description || '-') + '</span></td>' +
            '</tr>';
        }).join('');
    }

    function sortTable(column) {
        if (sortColumn === column) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            sortColumn = column;
            sortDirection = 'asc';
        }
        renderTable();
    }

    function exportCSV() {
        const roles = getFilteredRoles();
        const rels = getFilteredRelationships();
        const reportsTo = {};
        const directReports = {};
        rels.forEach(rel => {
            if (rel.relationship_type === 'inherits-from') {
                reportsTo[rel.source_role_id] = rel.target_role_name;
                if (!directReports[rel.target_role_id]) directReports[rel.target_role_id] = [];
                directReports[rel.target_role_id].push(rel.source_role_name);
            } else if (rel.relationship_type === 'supervises') {
                reportsTo[rel.target_role_id] = rel.source_role_name;
                if (!directReports[rel.source_role_id]) directReports[rel.source_role_id] = [];
                directReports[rel.source_role_id].push(rel.target_role_name);
            }
        });

        const headers = ['Role Name', 'Function Tags', 'Role Type', 'Disposition', 'Baselined', 'Inherits From', 'Inherited By', 'Nimbus Links', 'Description'];
        const rows = roles.map(r => [
            '"' + (r.role_name || '').replace(/"/g, '""') + '"',
            '"' + ((r.function_tags || []).map(ft => ft.code || ft.name || ft).join(', ')).replace(/"/g, '""') + '"',
            '"' + (r.role_type || '').replace(/"/g, '""') + '"',
            '"' + (r.role_disposition || 'TBD').replace(/"/g, '""') + '"',
            r.baselined ? 'Yes' : 'No',
            '"' + (reportsTo[r.id] || '').replace(/"/g, '""') + '"',
            (directReports[r.id] || []).length,
            '"' + ((r.tracings || []).map(t => (t.title || 'Nimbus') + ': ' + (t.url || '')).join(' | ')).replace(/"/g, '""') + '"',
            '"' + (r.description || '').replace(/"/g, '""') + '"'
        ]);

        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'aegis_hierarchy_' + new Date().toISOString().slice(0, 10) + '.csv';
        a.click();
        URL.revokeObjectURL(a.href);
        showToast('CSV exported successfully');
    }

    // ===== Detail Panel =====
    function openDetailPanel(role) {
        if (!role) return;
        const panel = document.getElementById('detail-panel');
        const overlay = document.getElementById('detail-overlay');
        const header = document.getElementById('detail-header');
        const body = document.getElementById('detail-body');

        const disp = role.role_disposition || 'TBD';
        const dispClass = disp === 'Sanctioned' ? 'sanctioned' : disp === 'To Be Retired' ? 'retire' : 'tbd';
        const dispLabel = disp === 'Sanctioned' ? '&#x1f6e1; Owner Approved' : disp === 'To Be Retired' ? '&#9888; Pending Replacement' : '? Pending Disposition';
        const titleClass = disp === 'To Be Retired' ? 'detail-title retired' : 'detail-title';

        const isModified = editChanges.has(role.role_name);
        header.innerHTML =
            '<div class="detail-header-bar ' + dispClass + '"></div>' +
            '<div class="detail-title-row">' +
                '<div class="' + titleClass + '">' + escHtml(role.role_name) +
                    (isModified ? '<span class="detail-modified-badge">Modified</span>' : '') +
                '</div>' +
                '<div style="display:flex;gap:6px;align-items:center">' +
                    '<button class="detail-edit-toggle" onclick="toggleEditMode(\\x27' + escAttr(role.role_name).replace(/\\\\/g, '\\\\\\\\') + '\\x27)" title="Edit this role">&#9998; Edit</button>' +
                    '<button class="detail-close" onclick="closeDetailPanel()">&times;</button>' +
                '</div>' +
            '</div>' +
            '<div class="detail-disp-label ' + dispClass + '">' + dispLabel + '</div>';

        // Build body sections
        let bodyHtml = '';

        // Description
        if (role.description) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Description</div>' +
                '<div class="detail-section-content">' + escHtml(role.description) + '</div></div>';
        }

        // Role Type
        bodyHtml += '<div class="detail-section">' +
            '<div class="detail-section-title">Role Type</div>' +
            '<div><span class="detail-badge detail-badge-gold">' + escHtml(role.role_type || 'Unknown') + '</span></div></div>';

        // Hierarchy Level
        if (role.hierarchy_level !== undefined && role.hierarchy_level !== null) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Hierarchy Level</div>' +
                '<div class="detail-section-content">Level ' + role.hierarchy_level + '</div></div>';
        }

        // Tags
        const tags = [];
        if (role.baselined) tags.push('<span class="detail-badge" style="background:var(--sanctioned-bg);color:var(--sanctioned)">&#10003; Baselined</span>');
        if (role.is_active === false || role.is_active === 0) tags.push('<span class="detail-badge" style="background:var(--error-bg);color:var(--error)">Inactive</span>');
        if (role.is_deliverable) tags.push('<span class="detail-badge" style="background:var(--info-bg);color:var(--info)">&#9733; Deliverable</span>');
        if (role.category) tags.push('<span class="detail-badge">' + escHtml(role.category) + '</span>');
        if (tags.length > 0) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Tags</div>' +
                '<div class="detail-tag-list">' + tags.join(' ') + '</div></div>';
        }

        // Function Tags
        if (role.function_tags && role.function_tags.length > 0) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Function Tags</div>' +
                '<div class="detail-tag-list">' +
                role.function_tags.map(ft => {
                    const color = ft.color || '#6b7280';
                    return '<span class="detail-tag" style="background:' + color + '20;color:' + color + ';border:1px solid ' + color + '40">' +
                           escHtml(ft.code || ft.name || ft) + '</span>';
                }).join('') +
                '</div></div>';
        }

        // v4.7.3: Nimbus Tracings (hyperlinks to source model)
        if (role.tracings && role.tracings.length > 0) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Nimbus Model Locations (' + role.tracings.length + ')</div>' +
                '<ul class="detail-link-list">' +
                role.tracings.map(t => {
                    const title = t.title || 'Nimbus Location';
                    const url = t.url || '#';
                    return '<li class="detail-link-item"><a href="' + url + '" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;display:flex;align-items:center;gap:6px;">' +
                        '<span>&#128279;</span>' +
                        escHtml(title) +
                        '</a></li>';
                }).join('') +
                '</ul></div>';
        }

        // Inherits From (parents)
        const parents = ALL_RELATIONSHIPS.filter(rel =>
            (rel.relationship_type === 'inherits-from' && rel.source_role_id === role.id) ||
            (rel.relationship_type === 'supervises' && rel.target_role_id === role.id) ||
            (rel.relationship_type === 'reports_to' && rel.source_role_id === role.id)
        );
        if (parents.length > 0) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Inherits From</div>' +
                '<ul class="detail-link-list">' +
                parents.map(rel => {
                    let parentName, parentId;
                    if (rel.relationship_type === 'inherits-from') {
                        parentName = rel.target_role_name;
                        parentId = rel.target_role_id;
                    } else if (rel.relationship_type === 'supervises') {
                        parentName = rel.source_role_name;
                        parentId = rel.source_role_id;
                    } else {
                        parentName = rel.target_role_name;
                        parentId = rel.target_role_id;
                    }
                    return '<li class="detail-link-item" onclick="navigateToRole(' + parentId + ')">&#8593; ' + escHtml(parentName) + '</li>';
                }).join('') +
                '</ul></div>';
        }

        // Inherited By (children)
        const children = ALL_RELATIONSHIPS.filter(rel =>
            (rel.relationship_type === 'inherits-from' && rel.target_role_id === role.id) ||
            (rel.relationship_type === 'supervises' && rel.source_role_id === role.id) ||
            (rel.relationship_type === 'reports_to' && rel.target_role_id === role.id)
        );
        if (children.length > 0) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Inherited By (' + children.length + ')</div>' +
                '<ul class="detail-link-list">' +
                children.map(rel => {
                    let childName, childId;
                    if (rel.relationship_type === 'inherits-from') {
                        childName = rel.source_role_name;
                        childId = rel.source_role_id;
                    } else if (rel.relationship_type === 'supervises') {
                        childName = rel.target_role_name;
                        childId = rel.target_role_id;
                    } else {
                        childName = rel.source_role_name;
                        childId = rel.source_role_id;
                    }
                    return '<li class="detail-link-item" onclick="navigateToRole(' + childId + ')">&#8595; ' + escHtml(childName) + '</li>';
                }).join('') +
                '</ul></div>';
        }

        // Connected Tools
        const toolRels = ALL_RELATIONSHIPS.filter(rel =>
            (rel.relationship_type === 'uses_tool' || rel.relationship_type === 'uses-tool') &&
            (rel.source_role_id === role.id || rel.target_role_id === role.id)
        );
        if (toolRels.length > 0) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Connected Tools</div>' +
                '<ul class="detail-link-list">' +
                toolRels.map(rel => {
                    const toolName = rel.source_role_id === role.id ? rel.target_role_name : rel.source_role_name;
                    const toolId = rel.source_role_id === role.id ? rel.target_role_id : rel.source_role_id;
                    return '<li class="detail-link-item" onclick="navigateToRole(' + toolId + ')">&#9632; ' + escHtml(toolName) + '</li>';
                }).join('') +
                '</ul></div>';
        }

        // v4.7.2: Shared Function Connections
        const sharedFnRels = ALL_RELATIONSHIPS.filter(rel =>
            rel.relationship_type === 'shared-function' &&
            (rel.source_role_id === role.id || rel.target_role_id === role.id)
        );
        if (sharedFnRels.length > 0) {
            // Sort by weight (most shared functions first), limit to top 20
            const sorted = [...sharedFnRels].sort((a, b) => (b.weight || 0) - (a.weight || 0)).slice(0, 20);
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Related Roles (' + sharedFnRels.length + ')</div>' +
                '<ul class="detail-link-list">' +
                sorted.map(rel => {
                    const peerName = rel.source_role_id === role.id ? rel.target_name : rel.source_name;
                    const peerId = rel.source_role_id === role.id ? rel.target_role_id : rel.source_role_id;
                    const weight = rel.weight || 1;
                    const fns = (rel.shared_functions || []).join(', ');
                    return '<li class="detail-link-item" onclick="navigateToRole(' + peerId + ')" title="Shared: ' + escHtml(fns) + '">&#8596; ' + escHtml(peerName) + ' <span style="color:var(--text-muted);font-size:11px;">(' + weight + ' shared)</span></li>';
                }).join('') +
                (sharedFnRels.length > 20 ? '<li style="color:var(--text-muted);font-size:12px;">+' + (sharedFnRels.length - 20) + ' more connections</li>' : '') +
                '</ul></div>';
        }

        // Aliases
        if (role.aliases) {
            const aliasList = typeof role.aliases === 'string' ? role.aliases.split(',').map(a => a.trim()).filter(Boolean) : role.aliases;
            if (aliasList.length > 0) {
                bodyHtml += '<div class="detail-section">' +
                    '<div class="detail-section-title">Aliases</div>' +
                    '<div class="detail-tag-list">' +
                    aliasList.map(a => '<span class="detail-badge">' + escHtml(a) + '</span>').join('') +
                    '</div></div>';
            }
        }

        // Notes
        if (role.notes) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Notes</div>' +
                '<div class="detail-section-content" style="font-style:italic;color:var(--text-secondary)">' + escHtml(role.notes) + '</div></div>';
        }

        // Source
        if (role.source) {
            bodyHtml += '<div class="detail-section">' +
                '<div class="detail-section-title">Source</div>' +
                '<div class="detail-section-content" style="font-size:11px;color:var(--text-muted)">' + escHtml(role.source) + '</div></div>';
        }

        body.innerHTML = bodyHtml;

        overlay.style.display = 'block';
        requestAnimationFrame(() => { panel.classList.add('open'); });
    }

    function closeDetailPanel() {
        const panel = document.getElementById('detail-panel');
        const overlay = document.getElementById('detail-overlay');
        panel.classList.remove('open');
        setTimeout(() => { overlay.style.display = 'none'; }, 300);
    }

    function navigateToRole(roleId) {
        const role = ALL_ROLES.find(r => r.id === roleId);
        if (role) openDetailPanel(role);
    }

    function toggleEditMode(roleName) {
        const role = ALL_ROLES.find(r => r.role_name === roleName);
        if (!role) return;
        editModeRole = roleName;
        const body = document.getElementById('detail-body');

        // Current status
        const curStatus = (role.is_active === false || role.is_active === 0) ? 'rejected' : (role.is_deliverable ? 'deliverable' : 'confirmed');
        const curDisp = role.role_disposition || 'TBD';

        // Available categories and role types for datalists
        const cats = [...new Set(ALL_ROLES.map(r => r.category).filter(Boolean))].sort();
        const catOptions = cats.map(c => '<option value="' + escAttr(c) + '">').join('');
        const rtypes = [...new Set(ALL_ROLES.map(r => r.role_type).filter(Boolean))].sort();
        const rtypeOptions = rtypes.map(t => '<option value="' + escAttr(t) + '">').join('');
        const orgGroups = [...new Set(ALL_ROLES.map(r => r.org_group).filter(Boolean))].sort();
        const orgOptions = orgGroups.map(g => '<option value="' + escAttr(g) + '">').join('');

        // Aliases as comma-separated string
        const aliasStr = typeof role.aliases === 'string' ? role.aliases : (Array.isArray(role.aliases) ? role.aliases.join(', ') : '');

        body.innerHTML =
            '<div class="edit-section-header">Identity</div>' +
            '<div class="edit-field">' +
                '<label>Role Name</label>' +
                '<input type="text" id="edit-role-name" value="' + escAttr(role.role_name || '') + '" placeholder="Role name">' +
            '</div>' +
            '<div class="edit-field-row">' +
                '<div class="edit-field edit-field-half">' +
                    '<label>Role Type</label>' +
                    '<input type="text" id="edit-role-type" list="edit-rtype-list" value="' + escAttr(role.role_type || '') + '" placeholder="e.g. Person, Document, Software">' +
                    '<datalist id="edit-rtype-list">' + rtypeOptions + '</datalist>' +
                '</div>' +
                '<div class="edit-field edit-field-half">' +
                    '<label>Org Group</label>' +
                    '<input type="text" id="edit-org-group" list="edit-org-list" value="' + escAttr(role.org_group || '') + '" placeholder="e.g. Engineering">' +
                    '<datalist id="edit-org-list">' + orgOptions + '</datalist>' +
                '</div>' +
            '</div>' +
            '<div class="edit-field">' +
                '<label>Aliases <span class="edit-hint">(comma-separated)</span></label>' +
                '<input type="text" id="edit-aliases" value="' + escAttr(aliasStr) + '" placeholder="e.g. QA Lead, Quality Assurance Lead">' +
            '</div>' +
            '<div class="edit-section-header">Classification</div>' +
            '<div class="edit-field">' +
                '<label>Adjudication Status</label>' +
                '<div class="edit-status-group">' +
                    '<button class="edit-status-btn s-confirmed' + (curStatus === 'confirmed' ? ' selected' : '') + '" onclick="selectEditStatus(\\x27confirmed\\x27)">&#10003; Confirmed</button>' +
                    '<button class="edit-status-btn s-deliverable' + (curStatus === 'deliverable' ? ' selected' : '') + '" onclick="selectEditStatus(\\x27deliverable\\x27)">&#9733; Deliverable</button>' +
                    '<button class="edit-status-btn s-rejected' + (curStatus === 'rejected' ? ' selected' : '') + '" onclick="selectEditStatus(\\x27rejected\\x27)">&#10007; Rejected</button>' +
                '</div>' +
            '</div>' +
            '<div class="edit-field">' +
                '<label>Disposition</label>' +
                '<div class="edit-status-group">' +
                    '<button class="edit-disp-btn d-sanctioned' + (curDisp === 'Sanctioned' ? ' selected' : '') + '" onclick="selectEditDisp(\\x27Sanctioned\\x27)">&#x1f6e1; Sanctioned</button>' +
                    '<button class="edit-disp-btn d-retire' + (curDisp === 'To Be Retired' ? ' selected' : '') + '" onclick="selectEditDisp(\\x27To Be Retired\\x27)">&#9888; To Be Retired</button>' +
                    '<button class="edit-disp-btn d-tbd' + (curDisp === 'TBD' ? ' selected' : '') + '" onclick="selectEditDisp(\\x27TBD\\x27)">? TBD</button>' +
                '</div>' +
            '</div>' +
            '<div class="edit-field-row">' +
                '<div class="edit-field edit-field-half">' +
                    '<label>Category</label>' +
                    '<input type="text" id="edit-category" list="edit-cat-list" value="' + escAttr(role.category || '') + '" placeholder="e.g. Engineering">' +
                    '<datalist id="edit-cat-list">' + catOptions + '</datalist>' +
                '</div>' +
                '<div class="edit-field edit-field-half">' +
                    '<label>Hierarchy Level</label>' +
                    '<input type="text" id="edit-hierarchy-level" value="' + escAttr(role.hierarchy_level || '') + '" placeholder="e.g. Level 2">' +
                '</div>' +
            '</div>' +
            '<div class="edit-field">' +
                '<label class="edit-checkbox-label">' +
                    '<input type="checkbox" id="edit-baselined"' + (role.baselined ? ' checked' : '') + '>' +
                    ' <span>Baselined</span>' +
                '</label>' +
            '</div>' +
            '<div class="edit-section-header">Details</div>' +
            '<div class="edit-field">' +
                '<label>Description</label>' +
                '<textarea id="edit-description" placeholder="Role description...">' + escHtml(role.description || '') + '</textarea>' +
            '</div>' +
            '<div class="edit-field">' +
                '<label>Notes</label>' +
                '<textarea id="edit-notes" placeholder="Review notes...">' + escHtml(role.notes || '') + '</textarea>' +
            '</div>' +
            '<div class="edit-actions">' +
                '<button class="edit-save-btn" onclick="saveEdit()">&#10003; Save Changes</button>' +
                '<button class="edit-cancel-btn" onclick="cancelEdit()">Cancel</button>' +
            '</div>';

        // Store selected status and disposition
        body.dataset.editStatus = curStatus;
        body.dataset.editDisp = curDisp;

        // Mark edit button active
        const editBtn = document.querySelector('.detail-edit-toggle');
        if (editBtn) editBtn.classList.add('active');
    }

    function selectEditStatus(status) {
        const body = document.getElementById('detail-body');
        body.dataset.editStatus = status;
        body.querySelectorAll('.edit-status-btn').forEach(btn => {
            btn.classList.toggle('selected', btn.classList.contains('s-' + status));
        });
    }

    function selectEditDisp(disp) {
        const body = document.getElementById('detail-body');
        body.dataset.editDisp = disp;
        const dispKey = disp === 'Sanctioned' ? 'sanctioned' : disp === 'To Be Retired' ? 'retire' : 'tbd';
        body.querySelectorAll('.edit-disp-btn').forEach(btn => {
            btn.classList.toggle('selected', btn.classList.contains('d-' + dispKey));
        });
    }

    function saveEdit() {
        const roleName = editModeRole;
        if (!roleName) return;
        const role = ALL_ROLES.find(r => r.role_name === roleName);
        if (!role) return;

        const body = document.getElementById('detail-body');
        const newStatus = body.dataset.editStatus || 'confirmed';
        const newDisp = body.dataset.editDisp || 'TBD';
        const newRoleName = (document.getElementById('edit-role-name') || {}).value || roleName;
        const newRoleType = (document.getElementById('edit-role-type') || {}).value || '';
        const newOrgGroup = (document.getElementById('edit-org-group') || {}).value || '';
        const newCategory = (document.getElementById('edit-category') || {}).value || '';
        const newHierarchyLevel = (document.getElementById('edit-hierarchy-level') || {}).value || '';
        const newBaselined = document.getElementById('edit-baselined') ? document.getElementById('edit-baselined').checked : false;
        const newAliases = (document.getElementById('edit-aliases') || {}).value || '';
        const newDescription = (document.getElementById('edit-description') || {}).value || '';
        const newNotes = (document.getElementById('edit-notes') || {}).value || '';

        // Save old values for undo
        const oldState = {
            role_name: role.role_name,
            is_active: role.is_active,
            is_deliverable: role.is_deliverable,
            role_type: role.role_type,
            role_disposition: role.role_disposition,
            org_group: role.org_group,
            category: role.category,
            hierarchy_level: role.hierarchy_level,
            baselined: role.baselined,
            aliases: role.aliases,
            description: role.description,
            notes: role.notes
        };

        // Apply all fields
        if (newStatus === 'rejected') {
            role.is_active = 0; role.is_deliverable = 0;
        } else if (newStatus === 'deliverable') {
            role.is_active = 1; role.is_deliverable = 1;
        } else {
            role.is_active = 1; role.is_deliverable = 0;
        }
        // Track original name for change tracking (before rename)
        if (!role._originalName) role._originalName = roleName;
        role.role_name = newRoleName;
        role.role_type = newRoleType;
        role.role_disposition = newDisp;
        role.org_group = newOrgGroup;
        role.category = newCategory;
        role.hierarchy_level = newHierarchyLevel;
        role.baselined = newBaselined;
        role.aliases = newAliases;
        role.description = newDescription;
        role.notes = newNotes;

        // Push undo
        pushEditHistory({
            role_name: role._originalName || roleName,
            old: oldState,
            new: {
                role_name: newRoleName, is_active: role.is_active, is_deliverable: role.is_deliverable,
                role_type: newRoleType, role_disposition: newDisp, org_group: newOrgGroup,
                category: newCategory, hierarchy_level: newHierarchyLevel, baselined: newBaselined,
                aliases: newAliases, description: newDescription, notes: newNotes
            }
        });

        trackEdit(role._originalName || roleName);
        editModeRole = null;
        openDetailPanel(role);
        refreshCurrentTab();
        showToast('Changes saved for ' + newRoleName);
    }

    function cancelEdit() {
        const roleName = editModeRole;
        editModeRole = null;
        // Re-open in read mode
        if (roleName) {
            const role = ALL_ROLES.find(r => r.role_name === roleName || r._originalName === roleName);
            if (role) { openDetailPanel(role); return; }
        }
        // Fallback: try title text
        const titleEl = document.querySelector('.detail-title');
        if (titleEl) {
            const name = titleEl.textContent.replace('Modified', '').trim();
            const role = ALL_ROLES.find(r => r.role_name === name);
            if (role) { openDetailPanel(role); return; }
        }
        closeDetailPanel();
    }

    // ===== Changes Modal =====
    function showChangesModal() {
        if (editChanges.size === 0) return;

        let listHtml = '';
        editChanges.forEach((change, roleName) => {
            const initial = INITIAL_STATES.get(roleName);
            let diffs = [];
            if (change.new_role_name && change.new_role_name !== initial.role_name) {
                diffs.push('<span class="change-diff-item">Name: ' + escHtml(initial.role_name) + ' &#8594; <strong>' + escHtml(change.new_role_name) + '</strong></span>');
            }
            if (change.action !== initial.status) {
                diffs.push('<span class="change-diff-item">Status: ' + escHtml(initial.status) + ' &#8594; <strong>' + escHtml(change.action) + '</strong></span>');
            }
            if (change.role_disposition !== initial.role_disposition) {
                diffs.push('<span class="change-diff-item">Disposition: ' + escHtml(initial.role_disposition || 'TBD') + ' &#8594; <strong>' + escHtml(change.role_disposition || 'TBD') + '</strong></span>');
            }
            if (change.role_type !== initial.role_type) {
                diffs.push('<span class="change-diff-item">Type: ' + escHtml(initial.role_type || '(none)') + ' &#8594; <strong>' + escHtml(change.role_type || '(none)') + '</strong></span>');
            }
            if (change.category !== initial.category) {
                diffs.push('<span class="change-diff-item">Category: ' + escHtml(initial.category || '(none)') + ' &#8594; <strong>' + escHtml(change.category || '(none)') + '</strong></span>');
            }
            if (change.org_group !== initial.org_group) {
                diffs.push('<span class="change-diff-item">Org Group: ' + escHtml(initial.org_group || '(none)') + ' &#8594; <strong>' + escHtml(change.org_group || '(none)') + '</strong></span>');
            }
            if (change.hierarchy_level !== initial.hierarchy_level) {
                diffs.push('<span class="change-diff-item">Level: ' + escHtml(initial.hierarchy_level || '(none)') + ' &#8594; <strong>' + escHtml(change.hierarchy_level || '(none)') + '</strong></span>');
            }
            if (change.baselined !== initial.baselined) {
                diffs.push('<span class="change-diff-item">Baselined: ' + (initial.baselined ? 'Yes' : 'No') + ' &#8594; <strong>' + (change.baselined ? 'Yes' : 'No') + '</strong></span>');
            }
            if (change.aliases !== initial.aliases) {
                diffs.push('<span class="change-diff-item">Aliases updated</span>');
            }
            if (change.description !== initial.description) {
                diffs.push('<span class="change-diff-item">Description updated</span>');
            }
            if (change.notes !== initial.notes) {
                diffs.push('<span class="change-diff-item">Notes updated</span>');
            }
            const displayName = change.new_role_name || roleName;
            listHtml += '<div class="changes-list-item">' +
                '<div class="change-role-name">' + escHtml(displayName) + '</div>' +
                '<div class="change-diff">' + diffs.join('') + '</div>' +
            '</div>';
        });

        const modalHtml =
            '<div class="changes-modal-overlay" id="changes-modal" onclick="if(event.target===this)this.remove()">' +
                '<div class="changes-modal">' +
                    '<h3>&#9998; ' + editChanges.size + ' Role' + (editChanges.size !== 1 ? 's' : '') + ' Modified</h3>' +
                    '<div>' + listHtml + '</div>' +
                    '<div class="import-instructions">' +
                        '<div class="import-instructions-title">How to import back into AEGIS</div>' +
                        '<div class="import-instructions-item"><strong>Option A (Easiest):</strong> Copy the downloaded JSON file into the AEGIS <code>updates/</code> folder, then go to Settings &#8594; Check for Updates &#8594; click Update.</div>' +
                        '<div class="import-instructions-item"><strong>Option B:</strong> Open AEGIS &#8594; Roles Studio &#8594; Adjudication tab &#8594; Export menu &#8594; Import Decisions &#8594; select this file.</div>' +
                    '</div>' +
                    '<div class="changes-modal-actions">' +
                        '<button class="edit-cancel-btn" onclick="document.getElementById(\\x27changes-modal\\x27).remove()">Cancel</button>' +
                        '<button class="edit-save-btn" onclick="downloadChangesJSON()">&#x2B07; Download JSON</button>' +
                    '</div>' +
                '</div>' +
            '</div>';

        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    function downloadChangesJSON() {
        const decisions = Array.from(editChanges.values());
        const summary = { total: decisions.length, confirmed: 0, deliverable: 0, rejected: 0, fields_changed: {} };
        decisions.forEach(d => {
            if (d.action in summary) summary[d.action]++;
            const initial = INITIAL_STATES.get(d.role_name);
            if (initial) {
                ['action', 'role_type', 'role_disposition', 'category', 'description', 'notes', 'org_group', 'hierarchy_level', 'baselined', 'aliases'].forEach(f => {
                    const initVal = f === 'action' ? initial.status : initial[f];
                    if (d[f] !== initVal) summary.fields_changed[f] = (summary.fields_changed[f] || 0) + 1;
                });
                if (d.new_role_name) summary.fields_changed.role_name = (summary.fields_changed.role_name || 0) + 1;
            }
        });

        const exportData = {
            aegis_version: META.aegis_version || META.app_version || '4.1.0',
            export_type: 'adjudication_decisions',
            exported_at: new Date().toISOString(),
            exported_by: 'hierarchy_export_' + (META.exported_by || 'offline'),
            source: 'hierarchy_review',
            decisions: decisions,
            summary: summary
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'aegis_hierarchy_changes_' + new Date().toISOString().slice(0, 10) + '.json';
        a.click();
        URL.revokeObjectURL(a.href);

        const modal = document.getElementById('changes-modal');
        if (modal) modal.remove();
        showToast('Changes exported (' + decisions.length + ' roles)');
    }

    // ===== Theme =====
    function toggleTheme() {
        isDark = !isDark;
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('aegis-hierarchy-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('aegis-hierarchy-theme', 'light');
        }
        updateThemeIcon();
        // Re-render graph if on graph tab (colors change)
        if (currentTab === 'graph') renderGraph();
    }

    function updateThemeIcon() {
        const sun = document.getElementById('icon-sun');
        const moon = document.getElementById('icon-moon');
        if (sun) sun.style.display = isDark ? 'none' : 'block';
        if (moon) moon.style.display = isDark ? 'block' : 'none';
    }

    // ===== Export Filtered JSON =====
    function exportFilteredJSON() {
        const data = {
            aegis_version: META.aegis_version,
            export_type: 'hierarchy_filtered',
            exported_at: new Date().toISOString(),
            roles: getFilteredRoles(),
            relationships: getFilteredRelationships(),
            filters_applied: {
                search: searchText || null,
                function_tags: [...activeFilters.function_tags],
                dispositions: [...activeFilters.dispositions],
                role_types: [...activeFilters.role_types],
                baselined: activeFilters.baselined
            }
        };
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'aegis_hierarchy_filtered_' + new Date().toISOString().slice(0, 10) + '.json';
        a.click();
        URL.revokeObjectURL(a.href);
        showToast('Filtered JSON exported');
    }

    // ===== Toast =====
    function showToast(message) {
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // ===== Utilities =====
    function escHtml(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function escAttr(str) {
        if (!str) return '';
        return String(str).replace(/'/g, '&#x27;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
    '''
