"""
AEGIS Graph Export — Interactive HTML Generator
================================================
Generates a standalone, interactive HTML file containing the role relationship
graph with embedded D3.js force-directed layout, pan/zoom, search, and
filter controls (by function tag, role type, document, org group).

v5.9.16: Initial implementation
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

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AEGIS — Role Relationship Graph</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #e6edf3; overflow: hidden; height: 100vh; }}

/* Header */
.header {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; background: #161b22; border-bottom: 1px solid #30363d; z-index: 10; position: relative; }}
.header-left {{ display: flex; align-items: center; gap: 12px; }}
.logo {{ font-size: 1.125rem; font-weight: 700; color: #D6A84A; letter-spacing: 0.05em; }}
.logo-sub {{ font-size: 0.75rem; color: #8b949e; }}
.header-stats {{ display: flex; gap: 16px; }}
.stat {{ font-size: 0.75rem; color: #8b949e; }}
.stat-num {{ font-weight: 700; color: #D6A84A; }}

/* Toolbar */
.toolbar {{ display: flex; align-items: center; gap: 8px; padding: 8px 20px; background: #161b22; border-bottom: 1px solid #30363d; flex-wrap: wrap; z-index: 10; position: relative; }}
.toolbar label {{ font-size: 0.6875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #8b949e; }}
.toolbar select, .toolbar input[type="text"] {{ padding: 4px 8px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #e6edf3; font-size: 0.8125rem; }}
.toolbar select:focus, .toolbar input:focus {{ outline: none; border-color: #D6A84A; box-shadow: 0 0 0 2px rgba(214,168,74,0.2); }}
.toolbar .sep {{ width: 1px; height: 24px; background: #30363d; margin: 0 4px; }}
.search-wrap {{ position: relative; }}
.search-wrap input {{ padding-left: 28px; width: 200px; }}
.search-icon {{ position: absolute; left: 8px; top: 50%; transform: translateY(-50%); color: #484f58; font-size: 0.8125rem; }}
.btn {{ padding: 5px 12px; border: 1px solid #30363d; border-radius: 6px; background: #21262d; color: #c9d1d9; font-size: 0.8125rem; cursor: pointer; }}
.btn:hover {{ border-color: #D6A84A; color: #D6A84A; }}

/* Graph container */
#graph-container {{ width: 100%; height: calc(100vh - 90px); position: relative; }}
svg {{ width: 100%; height: 100%; }}

/* Node styles */
.node-role {{ fill: #D6A84A; }}
.node-document {{ fill: #3b82f6; }}
.node-label {{ font-size: 10px; fill: #c9d1d9; pointer-events: none; text-anchor: middle; dominant-baseline: central; }}
.link {{ stroke: #30363d; stroke-opacity: 0.6; }}
.link:hover {{ stroke: #D6A84A; stroke-opacity: 1; }}

/* Tooltip */
.tooltip {{ position: absolute; padding: 10px 14px; background: #1c2128; border: 1px solid #30363d; border-radius: 8px; font-size: 0.8125rem; color: #e6edf3; pointer-events: none; max-width: 300px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); z-index: 100; display: none; }}
.tooltip .tt-name {{ font-weight: 700; margin-bottom: 4px; color: #D6A84A; }}
.tooltip .tt-type {{ font-size: 0.6875rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.03em; }}
.tooltip .tt-detail {{ margin-top: 6px; font-size: 0.75rem; color: #8b949e; line-height: 1.4; }}
.tooltip .tt-tag {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.625rem; font-weight: 600; margin: 1px; }}

/* Highlighted node */
.node-highlight {{ stroke: #D6A84A; stroke-width: 3px; }}
.node-dim {{ opacity: 0.15; }}
.link-dim {{ stroke-opacity: 0.05; }}

/* Legend */
.legend {{ position: absolute; bottom: 16px; left: 16px; background: rgba(22,27,34,0.9); border: 1px solid #30363d; border-radius: 8px; padding: 10px 14px; z-index: 5; }}
.legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: #8b949e; margin-bottom: 4px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

/* Footer */
.footer {{ position: absolute; bottom: 16px; right: 16px; font-size: 0.6875rem; color: #484f58; z-index: 5; }}

/* Print */
@media print {{ .toolbar, .legend, .footer {{ display: none; }} body {{ background: white; color: #111; }} svg {{ background: white; }} .node-label {{ fill: #111; }} .link {{ stroke: #ccc; }} }}
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
</div>

<div id="graph-container">
    <svg id="graph-svg"></svg>
    <div class="tooltip" id="tooltip"></div>
    <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:#D6A84A"></div> Role</div>
        <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div> Document</div>
        <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div> Deliverable</div>
    </div>
    <div class="footer">AEGIS v{version} &middot; Exported {export_date[:10]}</div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
(function() {{
    'use strict';

    const graphData = {graph_json};
    const nodes = graphData.nodes.map(d => ({{...d}}));
    const links = graphData.links.map(d => ({{...d}}));

    const container = document.getElementById('graph-container');
    const svg = d3.select('#graph-svg');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Zoom
    const g = svg.append('g');
    const zoom = d3.zoom()
        .scaleExtent([0.1, 8])
        .on('zoom', (e) => g.attr('transform', e.transform));
    svg.call(zoom);

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(80))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide(25));

    // Links
    const link = g.append('g').selectAll('line')
        .data(links).enter().append('line')
        .attr('class', 'link')
        .attr('stroke-width', d => Math.sqrt(d.weight || 1));

    // Nodes
    const node = g.append('g').selectAll('circle')
        .data(nodes).enter().append('circle')
        .attr('r', d => d.type === 'role' ? (d.is_deliverable ? 10 : 8) : 6)
        .attr('class', d => d.type === 'role' ? (d.is_deliverable ? 'node-deliverable' : 'node-role') : 'node-document')
        .style('fill', d => d.type === 'role' ? (d.is_deliverable ? '#22c55e' : '#D6A84A') : '#3b82f6')
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragStarted)
            .on('drag', dragged)
            .on('end', dragEnded));

    // Labels
    const label = g.append('g').selectAll('text')
        .data(nodes).enter().append('text')
        .attr('class', 'node-label')
        .attr('dy', d => (d.type === 'role' ? 18 : 14))
        .text(d => (d.name || '').substring(0, 20));

    // Tooltip
    const tooltip = document.getElementById('tooltip');

    node.on('mouseover', function(e, d) {{
        tooltip.style.display = 'block';
        let html = '<div class="tt-name">' + escHtml(d.name || '') + '</div>';
        html += '<div class="tt-type">' + escHtml(d.type || '') + '</div>';
        if (d.role_type) html += '<div class="tt-detail">Type: ' + escHtml(d.role_type) + '</div>';
        if (d.org_group) html += '<div class="tt-detail">Org: ' + escHtml(d.org_group) + '</div>';
        if (d.description) html += '<div class="tt-detail">' + escHtml(d.description.substring(0, 120)) + '</div>';
        if (d.function_tags && d.function_tags.length) {{
            html += '<div class="tt-detail">';
            d.function_tags.forEach(t => {{
                html += '<span class="tt-tag" style="background:' + (t.color || '#3b82f6') + '20;color:' + (t.color || '#3b82f6') + '">' + escHtml(t.name || t.code) + '</span>';
            }});
            html += '</div>';
        }}
        tooltip.innerHTML = html;
        tooltip.style.left = (e.pageX + 12) + 'px';
        tooltip.style.top = (e.pageY - 10) + 'px';

        // Highlight connected
        const connected = new Set();
        connected.add(d.id);
        links.forEach(l => {{
            const src = typeof l.source === 'object' ? l.source.id : l.source;
            const tgt = typeof l.target === 'object' ? l.target.id : l.target;
            if (src === d.id) connected.add(tgt);
            if (tgt === d.id) connected.add(src);
        }});
        node.classed('node-dim', n => !connected.has(n.id));
        node.classed('node-highlight', n => n.id === d.id);
        link.classed('link-dim', l => {{
            const src = typeof l.source === 'object' ? l.source.id : l.source;
            const tgt = typeof l.target === 'object' ? l.target.id : l.target;
            return !connected.has(src) || !connected.has(tgt);
        }});
        label.style('opacity', n => connected.has(n.id) ? 1 : 0.1);
    }}).on('mouseout', function() {{
        tooltip.style.display = 'none';
        node.classed('node-dim', false).classed('node-highlight', false);
        link.classed('link-dim', false);
        label.style('opacity', 1);
    }}).on('mousemove', function(e) {{
        tooltip.style.left = (e.pageX + 12) + 'px';
        tooltip.style.top = (e.pageY - 10) + 'px';
    }});

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
        nodes.forEach(n => {{ if ((n.name || '').toLowerCase().includes(q)) matched.add(n.id); }});
        // Also show connected nodes
        const visible = new Set(matched);
        links.forEach(l => {{
            const src = typeof l.source === 'object' ? l.source.id : l.source;
            const tgt = typeof l.target === 'object' ? l.target.id : l.target;
            if (matched.has(src)) visible.add(tgt);
            if (matched.has(tgt)) visible.add(src);
        }});
        node.classed('node-dim', n => !visible.has(n.id));
        label.style('opacity', n => visible.has(n.id) ? 1 : 0.1);
        link.classed('link-dim', l => {{
            const src = typeof l.source === 'object' ? l.source.id : l.source;
            const tgt = typeof l.target === 'object' ? l.target.id : l.target;
            return !visible.has(src) || !visible.has(tgt);
        }});
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
            node.classed('node-dim', false);
            label.style('opacity', 1);
            link.classed('link-dim', false);
            return;
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

        // Include connected documents
        const visible = new Set(matched);
        links.forEach(l => {{
            const src = typeof l.source === 'object' ? l.source.id : l.source;
            const tgt = typeof l.target === 'object' ? l.target.id : l.target;
            if (matched.has(src)) visible.add(tgt);
            if (matched.has(tgt)) visible.add(src);
        }});

        node.classed('node-dim', n => !visible.has(n.id));
        label.style('opacity', n => visible.has(n.id) ? 1 : 0.1);
        link.classed('link-dim', l => {{
            const src = typeof l.source === 'object' ? l.source.id : l.source;
            const tgt = typeof l.target === 'object' ? l.target.id : l.target;
            return !visible.has(src) || !visible.has(tgt);
        }});
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
        svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
    }});

    function escHtml(s) {{ const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }}
}})();
</script>
</body>
</html>'''

    return html
