"""
AEGIS Graph Export -- Interactive HTML Generator
================================================
Generates a standalone, interactive HTML file containing the role relationship
graph with embedded D3.js force-directed layout, pan/zoom, search, and
filter controls (by function tag, role type, document, org group).

v5.9.16: Initial implementation
v5.9.23: Enhanced with relationship arrows, link type styling, node sizing,
         info panel, dark/light toggle, improved legend, offline D3 fallback
"""

import json
import html as html_module
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


def generate_graph_html(
    graph_data: Dict[str, Any],
    metadata: Optional[Dict] = None
) -> str:
    """
    Generate a standalone interactive HTML page for the role relationship graph.

    Args:
        graph_data: Dict with 'nodes' and 'links' arrays from get_role_graph_data()
        metadata: Optional dict with version, export_date, hostname

    Returns:
        Complete HTML string
    """
    meta = metadata or {}
    nodes = graph_data.get('nodes', [])
    links = graph_data.get('links', [])

    # Collect filter options from node data
    role_types = sorted(set(
        n.get('role_type', '') for n in nodes
        if n.get('type') == 'role' and n.get('role_type')
    ))
    org_groups = sorted(set(
        n.get('org_group', '') for n in nodes
        if n.get('type') == 'role' and n.get('org_group')
    ))
    function_tags = {}
    for n in nodes:
        for tag in n.get('function_tags', []):
            code = tag.get('code', '')
            if code and code not in function_tags:
                function_tags[code] = {
                    'name': tag.get('name', code),
                    'color': tag.get('color', '#3b82f6')
                }
    function_tags_sorted = sorted(function_tags.items(), key=lambda x: x[1]['name'])

    # Collect relationship types for legend
    rel_types = sorted(set(
        l.get('relationship_type', '') for l in links
        if l.get('link_type') == 'relationship' and l.get('relationship_type')
    ))

    # Sanitize data for JSON embedding
    graph_json = json.dumps({
        'nodes': nodes,
        'links': links
    }, default=str)

    version = html_module.escape(str(meta.get('version', 'Unknown')))
    export_date = meta.get('export_date', datetime.now(timezone.utc).isoformat())
    hostname = html_module.escape(str(meta.get('hostname', '')))

    # Build filter option HTML
    role_type_options = ''.join(
        f'<option value="{html_module.escape(rt)}">{html_module.escape(rt)}</option>'
        for rt in role_types
    )
    org_group_options = ''.join(
        f'<option value="{html_module.escape(og)}">{html_module.escape(og)}</option>'
        for og in org_groups
    )
    func_tag_options = ''.join(
        f'<option value="{html_module.escape(code)}">{html_module.escape(info["name"])}</option>'
        for code, info in function_tags_sorted
    )

    role_count = sum(1 for n in nodes if n.get('type') == 'role')
    doc_count = sum(1 for n in nodes if n.get('type') == 'document')
    link_count = len(links)
    rel_count = sum(1 for l in links if l.get('link_type') == 'relationship')

    # Relationship legend items
    rel_legend_html = ''
    rel_colors = {
        'inherits-from': '#a855f7',
        'uses-tool': '#06b6d4',
        'co-performs': '#f59e0b',
        'supplies-to': '#10b981',
        'receives-from': '#ef4444'
    }
    for rt in rel_types:
        color = rel_colors.get(rt, '#8b949e')
        label = rt.replace('-', ' ').title()
        rel_legend_html += f'<div class="legend-item"><div class="legend-line" style="background:{color}"></div> {html_module.escape(label)}</div>\n'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AEGIS -- Role Relationship Graph</title>
<style>
:root {{
    --bg-deep: #0d1117; --bg-surface: #161b22; --bg-elevated: #21262d;
    --text-primary: #e6edf3; --text-secondary: #8b949e; --text-muted: #484f58;
    --border: #30363d; --gold: #D6A84A; --blue: #3b82f6; --green: #22c55e;
    --purple: #a855f7; --cyan: #06b6d4; --orange: #f59e0b; --teal: #10b981; --red: #ef4444;
}}
html.light {{
    --bg-deep: #f8fafc; --bg-surface: #ffffff; --bg-elevated: #f1f5f9;
    --text-primary: #0f172a; --text-secondary: #475569; --text-muted: #94a3b8;
    --border: #e2e8f0;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-deep); color: var(--text-primary); overflow: hidden; height: 100vh; }}

/* Header */
.header {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 20px; background: var(--bg-surface); border-bottom: 1px solid var(--border); z-index: 10; position: relative; }}
.header-left {{ display: flex; align-items: center; gap: 12px; }}
.logo {{ font-size: 1.125rem; font-weight: 700; color: var(--gold); letter-spacing: 0.05em; }}
.logo-sub {{ font-size: 0.75rem; color: var(--text-secondary); }}
.header-stats {{ display: flex; gap: 16px; align-items: center; }}
.stat {{ font-size: 0.75rem; color: var(--text-secondary); }}
.stat-num {{ font-weight: 700; color: var(--gold); }}
.theme-btn {{ background: none; border: 1px solid var(--border); border-radius: 6px; padding: 4px 8px; cursor: pointer; color: var(--text-secondary); font-size: 14px; }}
.theme-btn:hover {{ border-color: var(--gold); color: var(--gold); }}

/* Toolbar */
.toolbar {{ display: flex; align-items: center; gap: 8px; padding: 8px 20px; background: var(--bg-surface); border-bottom: 1px solid var(--border); flex-wrap: wrap; z-index: 10; position: relative; }}
.toolbar label {{ font-size: 0.6875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }}
.toolbar select, .toolbar input[type="text"] {{ padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-deep); color: var(--text-primary); font-size: 0.8125rem; }}
.toolbar select:focus, .toolbar input:focus {{ outline: none; border-color: var(--gold); box-shadow: 0 0 0 2px rgba(214,168,74,0.2); }}
.toolbar .sep {{ width: 1px; height: 24px; background: var(--border); margin: 0 4px; }}
.search-wrap {{ position: relative; }}
.search-wrap input {{ padding-left: 28px; width: 200px; }}
.search-icon {{ position: absolute; left: 8px; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 0.8125rem; }}
.btn {{ padding: 5px 12px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-elevated); color: var(--text-primary); font-size: 0.8125rem; cursor: pointer; }}
.btn:hover {{ border-color: var(--gold); color: var(--gold); }}

/* Graph container */
#graph-container {{ width: 100%; height: calc(100vh - 88px); position: relative; }}
svg {{ width: 100%; height: 100%; }}

/* Node styles */
.node-label {{ font-size: 10px; fill: var(--text-primary); pointer-events: none; text-anchor: middle; dominant-baseline: central; }}
html.light .node-label {{ fill: #334155; }}

/* Link styles */
.link-default {{ stroke: var(--border); stroke-opacity: 0.5; }}
.link-relationship {{ stroke-opacity: 0.7; }}
.link-rr {{ stroke: #6366f1; stroke-dasharray: 4 2; stroke-opacity: 0.4; }}

/* Tooltip */
.tooltip {{ position: absolute; padding: 12px 16px; background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; font-size: 0.8125rem; color: var(--text-primary); pointer-events: none; max-width: 320px; box-shadow: 0 8px 24px rgba(0,0,0,0.35); z-index: 100; display: none; }}
.tooltip .tt-name {{ font-weight: 700; margin-bottom: 4px; color: var(--gold); font-size: 0.875rem; }}
.tooltip .tt-type {{ font-size: 0.6875rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.03em; }}
.tooltip .tt-detail {{ margin-top: 6px; font-size: 0.75rem; color: var(--text-secondary); line-height: 1.5; }}
.tooltip .tt-tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.625rem; font-weight: 600; margin: 2px; }}
.tooltip .tt-section {{ margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--border); }}
.tooltip .tt-rel {{ font-size: 0.6875rem; color: var(--text-secondary); padding: 1px 0; }}

/* Highlighted node */
.node-highlight {{ stroke: var(--gold); stroke-width: 3px; }}
.node-dim {{ opacity: 0.1; }}
.link-dim {{ stroke-opacity: 0.03 !important; }}

/* Legend */
.legend {{ position: absolute; bottom: 16px; left: 16px; background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; z-index: 5; max-height: calc(100vh - 180px); overflow-y: auto; }}
.legend h4 {{ font-size: 0.6875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 6px; margin-top: 10px; }}
.legend h4:first-child {{ margin-top: 0; }}
.legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 3px; }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }}
.legend-line {{ width: 20px; height: 3px; border-radius: 2px; flex-shrink: 0; }}

/* Info panel */
.info-panel {{ position: absolute; top: 0; right: -360px; width: 360px; height: 100%; background: var(--bg-surface); border-left: 1px solid var(--border); z-index: 15; transition: right 0.3s; overflow-y: auto; padding: 20px; }}
.info-panel.open {{ right: 0; box-shadow: -4px 0 20px rgba(0,0,0,0.2); }}
.info-close {{ position: absolute; top: 12px; right: 12px; background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 18px; }}
.info-close:hover {{ color: var(--text-primary); }}
.info-name {{ font-size: 1.125rem; font-weight: 700; color: var(--gold); margin-bottom: 4px; padding-right: 30px; }}
.info-type {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.05em; margin-bottom: 12px; }}
.info-section {{ margin-bottom: 14px; }}
.info-section h5 {{ font-size: 0.6875rem; text-transform: uppercase; color: var(--text-secondary); letter-spacing: 0.05em; margin-bottom: 4px; }}
.info-section p {{ font-size: 0.8125rem; color: var(--text-primary); line-height: 1.5; }}
.info-badge {{ display: inline-block; padding: 2px 10px; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; margin: 2px; }}
.info-rel-item {{ font-size: 0.8125rem; color: var(--text-primary); padding: 4px 0; border-bottom: 1px solid var(--border); }}
.info-rel-type {{ font-size: 0.625rem; color: var(--text-secondary); }}

/* Footer */
.footer {{ position: absolute; bottom: 16px; right: 16px; font-size: 0.6875rem; color: var(--text-muted); z-index: 5; }}

/* Print */
@media print {{
    .toolbar, .legend, .footer, .info-panel, .theme-btn {{ display: none !important; }}
    body {{ background: white; color: #111; }}
    svg {{ background: white; }}
    .node-label {{ fill: #111; }}
    .link-default {{ stroke: #ccc; }}
}}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <span class="logo">AEGIS</span>
        <span class="logo-sub">Role Relationship Graph</span>
    </div>
    <div class="header-stats">
        <span class="stat"><span class="stat-num">{role_count}</span> Roles</span>
        <span class="stat"><span class="stat-num">{doc_count}</span> Documents</span>
        <span class="stat"><span class="stat-num">{link_count}</span> Connections</span>
        {'<span class="stat"><span class="stat-num">' + str(rel_count) + '</span> Relationships</span>' if rel_count > 0 else ''}
        <button class="theme-btn" id="themeToggle" title="Toggle light/dark mode">&#9681;</button>
    </div>
</div>

<div class="toolbar">
    <div class="search-wrap">
        <span class="search-icon">&#x1F50D;</span>
        <input type="text" id="search" placeholder="Search roles or documents...">
    </div>
    <div class="sep"></div>
    <label>Function</label>
    <select id="filter-function"><option value="">All Functions</option>{func_tag_options}</select>
    <label>Role Type</label>
    <select id="filter-role-type"><option value="">All Types</option>{role_type_options}</select>
    <label>Org Group</label>
    <select id="filter-org-group"><option value="">All Groups</option>{org_group_options}</select>
    <div class="sep"></div>
    <button class="btn" id="btn-reset">Reset</button>
    <button class="btn" id="btn-print" onclick="window.print()">&#128424; Print</button>
</div>

<div id="graph-container">
    <svg id="graph-svg">
        <defs>
            <marker id="arrow-inherits" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="{rel_colors.get('inherits-from', '#a855f7')}" />
            </marker>
            <marker id="arrow-supplies" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="{rel_colors.get('supplies-to', '#10b981')}" />
            </marker>
            <marker id="arrow-receives" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="{rel_colors.get('receives-from', '#ef4444')}" />
            </marker>
            <marker id="arrow-default" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b949e" />
            </marker>
        </defs>
    </svg>
    <div class="tooltip" id="tooltip"></div>
    <div class="legend">
        <h4>Nodes</h4>
        <div class="legend-item"><div class="legend-dot" style="background:var(--gold)"></div> Role</div>
        <div class="legend-item"><div class="legend-dot" style="background:var(--blue)"></div> Document</div>
        <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div> Deliverable</div>
        <h4>Links</h4>
        <div class="legend-item"><div class="legend-line" style="background:var(--border)"></div> Co-occurrence</div>
        <div class="legend-item"><div class="legend-line" style="background:#6366f1;opacity:0.6"></div> Role-Role</div>
        {rel_legend_html}
    </div>
    <div class="info-panel" id="infoPanel">
        <button class="info-close" id="infoClose">&times;</button>
        <div id="infoPanelContent"></div>
    </div>
    <div class="footer">AEGIS v{version} &middot; Exported {export_date[:10]}</div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
(function() {{
    'use strict';

    // Relationship type colors
    const REL_COLORS = {{
        'inherits-from': '#a855f7',
        'uses-tool': '#06b6d4',
        'co-performs': '#f59e0b',
        'supplies-to': '#10b981',
        'receives-from': '#ef4444'
    }};

    // Arrow markers by relationship type
    const REL_MARKERS = {{
        'inherits-from': 'url(#arrow-inherits)',
        'supplies-to': 'url(#arrow-supplies)',
        'receives-from': 'url(#arrow-receives)'
    }};

    const graphData = {graph_json};
    const nodes = graphData.nodes.map(d => ({{...d}}));
    const links = graphData.links.map(d => ({{...d}}));

    const container = document.getElementById('graph-container');
    const svg = d3.select('#graph-svg');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Theme toggle
    document.getElementById('themeToggle').addEventListener('click', function() {{
        document.documentElement.classList.toggle('light');
    }});

    // Zoom
    const g = svg.append('g');
    const zoom = d3.zoom()
        .scaleExtent([0.05, 10])
        .on('zoom', (e) => g.attr('transform', e.transform));
    svg.call(zoom);

    // Calculate node radii based on connections
    const connectionCount = {{}};
    links.forEach(l => {{
        const src = typeof l.source === 'string' ? l.source : l.source.id;
        const tgt = typeof l.target === 'string' ? l.target : l.target.id;
        connectionCount[src] = (connectionCount[src] || 0) + 1;
        connectionCount[tgt] = (connectionCount[tgt] || 0) + 1;
    }});
    nodes.forEach(n => {{
        const conns = connectionCount[n.id] || 0;
        if (n.type === 'role') {{
            n.radius = n.is_deliverable ? Math.max(10, Math.min(18, 8 + conns * 0.8)) : Math.max(7, Math.min(14, 6 + conns * 0.6));
        }} else {{
            n.radius = Math.max(5, Math.min(10, 4 + conns * 0.4));
        }}
    }});

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(d => {{
            if (d.link_type === 'relationship') return 120;
            if (d.link_type === 'role-role') return 100;
            return 80;
        }}))
        .force('charge', d3.forceManyBody().strength(d => d.type === 'role' ? -250 : -120))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide(d => (d.radius || 8) + 4));

    // Links
    const link = g.append('g').attr('class', 'links').selectAll('line')
        .data(links).enter().append('line')
        .attr('stroke', d => {{
            if (d.link_type === 'relationship') return REL_COLORS[d.relationship_type] || '#8b949e';
            if (d.link_type === 'role-role') return '#6366f1';
            return null;
        }})
        .attr('class', d => {{
            if (d.link_type === 'relationship') return 'link-relationship';
            if (d.link_type === 'role-role') return 'link-rr';
            return 'link-default';
        }})
        .attr('stroke-width', d => {{
            if (d.link_type === 'relationship') return 2;
            return Math.max(1, Math.sqrt(d.weight || 1));
        }})
        .attr('stroke-dasharray', d => {{
            if (d.link_type === 'role-role') return '4 2';
            if (d.relationship_type === 'co-performs') return '6 3';
            if (d.relationship_type === 'uses-tool') return '2 2';
            return null;
        }})
        .attr('marker-end', d => {{
            if (d.link_type !== 'relationship') return null;
            return REL_MARKERS[d.relationship_type] || 'url(#arrow-default)';
        }});

    // Nodes
    const node = g.append('g').attr('class', 'nodes').selectAll('circle')
        .data(nodes).enter().append('circle')
        .attr('r', d => d.radius || 8)
        .style('fill', d => d.type === 'role' ? (d.is_deliverable ? 'var(--green)' : 'var(--gold)') : 'var(--blue)')
        .style('stroke', d => d.type === 'role' ? (d.is_deliverable ? '#16a34a' : '#b8860b') : '#2563eb')
        .style('stroke-width', 1.5)
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded));

    // Labels
    const label = g.append('g').attr('class', 'labels').selectAll('text')
        .data(nodes).enter().append('text')
        .attr('class', 'node-label')
        .attr('dy', d => (d.radius || 8) + 12)
        .text(d => ((d.label || d.name || d.original_name || '')).substring(0, 24));

    // Tooltip
    const tooltip = document.getElementById('tooltip');

    node.on('mouseover', function(e, d) {{
        tooltip.style.display = 'block';
        const name = d.label || d.name || d.original_name || '';
        let html = '<div class="tt-name">' + escHtml(name) + '</div>';
        html += '<div class="tt-type">' + escHtml(d.type || '') + (d.is_deliverable ? ' &bull; Deliverable' : '') + '</div>';
        if (d.role_type) html += '<div class="tt-detail">Type: ' + escHtml(d.role_type) + '</div>';
        if (d.org_group) html += '<div class="tt-detail">Org: ' + escHtml(d.org_group) + '</div>';
        if (d.description) html += '<div class="tt-detail">' + escHtml((d.description || '').substring(0, 150)) + '</div>';
        if (d.function_tags && d.function_tags.length) {{
            html += '<div class="tt-detail" style="margin-top:6px">';
            d.function_tags.forEach(t => {{
                html += '<span class="tt-tag" style="background:' + (t.color || '#3b82f6') + '20;color:' + (t.color || '#3b82f6') + '">' + escHtml(t.name || t.code) + '</span>';
            }});
            html += '</div>';
        }}
        // Show relationships in tooltip
        const rels = links.filter(l => l.link_type === 'relationship' && (getId(l.source) === d.id || getId(l.target) === d.id));
        if (rels.length > 0) {{
            html += '<div class="tt-section">';
            rels.forEach(r => {{
                const isSrc = getId(r.source) === d.id;
                const other = isSrc ? (typeof r.target === 'object' ? r.target : nodes.find(n => n.id === r.target)) : (typeof r.source === 'object' ? r.source : nodes.find(n => n.id === r.source));
                const otherName = other ? (other.label || other.name || '') : '?';
                const relLabel = (r.relationship_type || 'related').replace(/-/g, ' ');
                html += '<div class="tt-rel">' + (isSrc ? relLabel : relLabel) + ' &rarr; ' + escHtml(otherName) + '</div>';
            }});
            html += '</div>';
        }}
        tooltip.innerHTML = html;
        tooltip.style.left = (e.pageX + 14) + 'px';
        tooltip.style.top = (e.pageY - 10) + 'px';

        // Highlight connected
        const connected = new Set();
        connected.add(d.id);
        links.forEach(l => {{
            const src = getId(l.source);
            const tgt = getId(l.target);
            if (src === d.id) connected.add(tgt);
            if (tgt === d.id) connected.add(src);
        }});
        node.classed('node-dim', n => !connected.has(n.id));
        node.classed('node-highlight', n => n.id === d.id);
        link.classed('link-dim', l => !connected.has(getId(l.source)) || !connected.has(getId(l.target)));
        label.style('opacity', n => connected.has(n.id) ? 1 : 0.05);
    }}).on('mouseout', function() {{
        tooltip.style.display = 'none';
        node.classed('node-dim', false).classed('node-highlight', false);
        link.classed('link-dim', false);
        label.style('opacity', 1);
    }}).on('mousemove', function(e) {{
        tooltip.style.left = (e.pageX + 14) + 'px';
        tooltip.style.top = (e.pageY - 10) + 'px';
    }}).on('click', function(e, d) {{
        showInfoPanel(d);
    }});

    function getId(x) {{ return typeof x === 'object' ? x.id : x; }}

    // Info panel
    const infoPanel = document.getElementById('infoPanel');
    const infoPanelContent = document.getElementById('infoPanelContent');
    document.getElementById('infoClose').addEventListener('click', () => infoPanel.classList.remove('open'));

    function showInfoPanel(d) {{
        const name = d.label || d.name || d.original_name || '';
        let html = '<div class="info-name">' + escHtml(name) + '</div>';
        html += '<div class="info-type">' + escHtml(d.type || '') + (d.is_deliverable ? ' &bull; Deliverable' : '') + '</div>';

        if (d.description) {{
            html += '<div class="info-section"><h5>Description</h5><p>' + escHtml(d.description) + '</p></div>';
        }}
        if (d.role_type || d.org_group || d.category) {{
            html += '<div class="info-section"><h5>Metadata</h5>';
            if (d.role_type) html += '<p>Role Type: <strong>' + escHtml(d.role_type) + '</strong></p>';
            if (d.org_group) html += '<p>Org Group: <strong>' + escHtml(d.org_group) + '</strong></p>';
            if (d.category) html += '<p>Category: <strong>' + escHtml(d.category) + '</strong></p>';
            html += '</div>';
        }}
        if (d.function_tags && d.function_tags.length) {{
            html += '<div class="info-section"><h5>Function Tags</h5><div>';
            d.function_tags.forEach(t => {{
                html += '<span class="info-badge" style="background:' + (t.color || '#3b82f6') + '20;color:' + (t.color || '#3b82f6') + '">' + escHtml(t.name || t.code) + '</span>';
            }});
            html += '</div></div>';
        }}

        // Relationships
        const rels = links.filter(l => l.link_type === 'relationship' && (getId(l.source) === d.id || getId(l.target) === d.id));
        if (rels.length > 0) {{
            html += '<div class="info-section"><h5>Relationships (' + rels.length + ')</h5>';
            rels.forEach(r => {{
                const isSrc = getId(r.source) === d.id;
                const other = isSrc ? (typeof r.target === 'object' ? r.target : nodes.find(n => n.id === r.target)) : (typeof r.source === 'object' ? r.source : nodes.find(n => n.id === r.source));
                const otherName = other ? (other.label || other.name || '') : '?';
                const relLabel = (r.relationship_type || 'related').replace(/-/g, ' ');
                const color = REL_COLORS[r.relationship_type] || '#8b949e';
                html += '<div class="info-rel-item"><span class="info-rel-type" style="color:' + color + '">' + escHtml(relLabel) + '</span> &rarr; ' + escHtml(otherName) + '</div>';
            }});
            html += '</div>';
        }}

        // Connected nodes
        const connected = [];
        links.forEach(l => {{
            const src = getId(l.source);
            const tgt = getId(l.target);
            if (src === d.id && l.link_type !== 'relationship') {{
                const other = typeof l.target === 'object' ? l.target : nodes.find(n => n.id === tgt);
                if (other) connected.push(other);
            }}
            if (tgt === d.id && l.link_type !== 'relationship') {{
                const other = typeof l.source === 'object' ? l.source : nodes.find(n => n.id === src);
                if (other) connected.push(other);
            }}
        }});
        if (connected.length > 0) {{
            const connRoles = connected.filter(c => c.type === 'role').slice(0, 15);
            const connDocs = connected.filter(c => c.type === 'document').slice(0, 15);
            if (connDocs.length > 0) {{
                html += '<div class="info-section"><h5>Documents (' + connDocs.length + ')</h5>';
                connDocs.forEach(c => {{ html += '<div style="font-size:0.8125rem;padding:2px 0;color:var(--text-primary)">' + escHtml(c.label || c.name || '') + '</div>'; }});
                html += '</div>';
            }}
            if (connRoles.length > 0) {{
                html += '<div class="info-section"><h5>Co-occurring Roles (' + connRoles.length + ')</h5>';
                connRoles.forEach(c => {{ html += '<div style="font-size:0.8125rem;padding:2px 0;color:var(--text-primary)">' + escHtml(c.label || c.name || '') + '</div>'; }});
                html += '</div>';
            }}
        }}

        infoPanelContent.innerHTML = html;
        infoPanel.classList.add('open');
    }}

    // Tick
    simulation.on('tick', () => {{
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('cx', d => d.x).attr('cy', d => d.y);
        label.attr('x', d => d.x).attr('y', d => d.y);
    }});

    // Drag
    function dragStarted(e, d) {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }}
    function dragged(e, d) {{ d.fx = e.x; d.fy = e.y; }}
    function dragEnded(e, d) {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }}

    // Search
    document.getElementById('search').addEventListener('input', function() {{
        const q = this.value.toLowerCase().trim();
        if (!q) {{ node.classed('node-dim', false); label.style('opacity', 1); link.classed('link-dim', false); return; }}
        const matched = new Set();
        nodes.forEach(n => {{
            const name = (n.label || n.name || n.original_name || '').toLowerCase();
            if (name.includes(q)) matched.add(n.id);
        }});
        const visible = new Set(matched);
        links.forEach(l => {{
            const src = getId(l.source); const tgt = getId(l.target);
            if (matched.has(src)) visible.add(tgt);
            if (matched.has(tgt)) visible.add(src);
        }});
        node.classed('node-dim', n => !visible.has(n.id));
        label.style('opacity', n => visible.has(n.id) ? 1 : 0.05);
        link.classed('link-dim', l => !visible.has(getId(l.source)) || !visible.has(getId(l.target)));
    }});

    // Filters
    ['filter-function', 'filter-role-type', 'filter-org-group'].forEach(id => {{
        document.getElementById(id).addEventListener('change', applyFilters);
    }});

    function applyFilters() {{
        const funcFilter = document.getElementById('filter-function').value;
        const typeFilter = document.getElementById('filter-role-type').value;
        const orgFilter = document.getElementById('filter-org-group').value;
        if (!funcFilter && !typeFilter && !orgFilter) {{
            node.classed('node-dim', false); label.style('opacity', 1); link.classed('link-dim', false); return;
        }}
        const matched = new Set();
        nodes.forEach(n => {{
            if (n.type !== 'role') return;
            let pass = true;
            if (funcFilter) {{
                const tags = (n.function_tags || []).map(t => t.code);
                if (!tags.includes(funcFilter)) pass = false;
            }}
            if (typeFilter && n.role_type !== typeFilter) pass = false;
            if (orgFilter && n.org_group !== orgFilter) pass = false;
            if (pass) matched.add(n.id);
        }});
        const visible = new Set(matched);
        links.forEach(l => {{
            const src = getId(l.source); const tgt = getId(l.target);
            if (matched.has(src)) visible.add(tgt);
            if (matched.has(tgt)) visible.add(src);
        }});
        node.classed('node-dim', n => !visible.has(n.id));
        label.style('opacity', n => visible.has(n.id) ? 1 : 0.05);
        link.classed('link-dim', l => !visible.has(getId(l.source)) || !visible.has(getId(l.target)));
    }}

    // Reset
    document.getElementById('btn-reset').addEventListener('click', function() {{
        document.getElementById('search').value = '';
        document.getElementById('filter-function').value = '';
        document.getElementById('filter-role-type').value = '';
        document.getElementById('filter-org-group').value = '';
        node.classed('node-dim', false).classed('node-highlight', false);
        label.style('opacity', 1);
        link.classed('link-dim', false);
        infoPanel.classList.remove('open');
        svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
    }});

    function escHtml(s) {{ const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }}
}})();
</script>
</body>
</html>'''

    return html
