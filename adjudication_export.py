"""
AEGIS Adjudication Export - Interactive HTML Generator

Generates a standalone interactive HTML file replicating the kanban board experience
for offline adjudication. Team members can drag-drop roles between columns, assign
function tags, edit categories, add notes, then generate a JSON import file.

Usage:
    from adjudication_export import generate_adjudication_html
    html = generate_adjudication_html(roles, function_categories, metadata)
"""

import json
import html as html_module
from datetime import datetime, timezone
from typing import List, Dict, Optional
import socket


def generate_adjudication_html(
    roles: List[Dict],
    function_categories: List[Dict],
    metadata: Optional[Dict] = None
) -> str:
    """
    Generate a standalone interactive HTML file for adjudication.

    Args:
        roles: List of role dicts with keys:
            - role_name, status, category, confidence, documents,
              function_tags, total_mentions, notes
        function_categories: List of function category dicts with keys:
            - code, name, description, parent_code, color, is_active
        metadata: Optional dict with version, export_date, etc.

    Returns:
        Complete HTML string (standalone, no external dependencies)
    """
    if metadata is None:
        metadata = {}

    version = metadata.get('version', '4.0.3')
    export_date = metadata.get('export_date', datetime.now(timezone.utc).isoformat())
    hostname = metadata.get('hostname', socket.gethostname())

    # Sanitize data for JSON embedding
    safe_roles = json.dumps(roles, default=str)
    safe_categories = json.dumps(function_categories, default=str)
    safe_metadata = json.dumps({
        'aegis_version': version,
        'exported_at': export_date,
        'exported_by': hostname,
        'total_roles': len(roles)
    }, default=str)

    # Count statuses
    counts = {'pending': 0, 'confirmed': 0, 'deliverable': 0, 'rejected': 0}
    for r in roles:
        s = r.get('status', 'pending').lower()
        if s in counts:
            counts[s] += 1
        else:
            counts['pending'] += 1

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS Role Adjudication Board</title>
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
                        <text x="50" y="62" text-anchor="middle" fill="white" font-size="28" font-weight="bold" font-family="Arial">A</text>
                    </svg>
                </div>
                <div>
                    <h1>AEGIS Role Adjudication</h1>
                    <p class="subtitle">Interactive Board &mdash; Exported {html_module.escape(export_date[:10])}</p>
                </div>
            </div>
            <div class="header-right">
                <div class="stat-cards">
                    <div class="stat-card stat-pending" data-filter="pending" onclick="filterByStatus('pending')">
                        <span class="stat-count" id="count-pending">{counts['pending']}</span>
                        <span class="stat-label">Pending</span>
                    </div>
                    <div class="stat-card stat-confirmed" data-filter="confirmed" onclick="filterByStatus('confirmed')">
                        <span class="stat-count" id="count-confirmed">{counts['confirmed']}</span>
                        <span class="stat-label">Confirmed</span>
                    </div>
                    <div class="stat-card stat-deliverable" data-filter="deliverable" onclick="filterByStatus('deliverable')">
                        <span class="stat-count" id="count-deliverable">{counts['deliverable']}</span>
                        <span class="stat-label">Deliverables</span>
                    </div>
                    <div class="stat-card stat-rejected" data-filter="rejected" onclick="filterByStatus('rejected')">
                        <span class="stat-count" id="count-rejected">{counts['rejected']}</span>
                        <span class="stat-label">Rejected</span>
                    </div>
                </div>
                <button class="btn btn-icon" id="btn-theme" onclick="toggleTheme()" title="Toggle dark/light mode">
                    <svg id="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
                    <svg id="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
                </button>
            </div>
        </header>

        <!-- Toolbar — v5.9.28: added category and function tag filter dropdowns -->
        <div class="toolbar">
            <div class="toolbar-left">
                <input type="text" id="search-input" class="search-input" placeholder="Search roles..." oninput="handleSearch(this.value)">
                <div class="filter-dropdown" id="dd-category">
                    <button class="btn btn-filter" onclick="toggleDropdown('dd-category')">Category <span class="filter-badge" id="badge-category" style="display:none">0</span></button>
                    <div class="dropdown-panel" id="panel-category"></div>
                </div>
                <div class="filter-dropdown" id="dd-tags">
                    <button class="btn btn-filter" onclick="toggleDropdown('dd-tags')">Tags <span class="filter-badge" id="badge-tags" style="display:none">0</span></button>
                    <div class="dropdown-panel" id="panel-tags"></div>
                </div>
                <span class="search-count" id="search-count"></span>
            </div>
            <div class="toolbar-right">
                <div class="changes-badge" id="changes-badge" style="display:none">
                    <span id="changes-count">0</span> changes
                </div>
                <button class="btn btn-primary" id="btn-generate" onclick="generateImportFile()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Generate Import File
                </button>
                <button class="btn btn-secondary" id="btn-undo" onclick="undo()" disabled title="Undo (Ctrl+Z)">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
                </button>
                <button class="btn btn-secondary" id="btn-redo" onclick="redo()" disabled title="Redo (Ctrl+Y)">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.13-9.36L23 10"/></svg>
                </button>
            </div>
        </div>

        <!-- Kanban Board -->
        <div class="kanban-board" id="kanban-board">
            <div class="kanban-column" data-status="pending" ondragover="handleDragOver(event)" ondrop="handleDrop(event, 'pending')">
                <div class="kanban-header">
                    <span class="kanban-dot dot-pending"></span>
                    <span class="kanban-title">Pending</span>
                    <span class="kanban-badge" id="badge-pending">{counts['pending']}</span>
                </div>
                <div class="kanban-cards" id="cards-pending"></div>
            </div>
            <div class="kanban-column" data-status="confirmed" ondragover="handleDragOver(event)" ondrop="handleDrop(event, 'confirmed')">
                <div class="kanban-header">
                    <span class="kanban-dot dot-confirmed"></span>
                    <span class="kanban-title">Confirmed</span>
                    <span class="kanban-badge" id="badge-confirmed">{counts['confirmed']}</span>
                </div>
                <div class="kanban-cards" id="cards-confirmed"></div>
            </div>
            <div class="kanban-column" data-status="deliverable" ondragover="handleDragOver(event)" ondrop="handleDrop(event, 'deliverable')">
                <div class="kanban-header">
                    <span class="kanban-dot dot-deliverable"></span>
                    <span class="kanban-title">Deliverables</span>
                    <span class="kanban-badge" id="badge-deliverable">{counts['deliverable']}</span>
                </div>
                <div class="kanban-cards" id="cards-deliverable"></div>
            </div>
            <div class="kanban-column" data-status="rejected" ondragover="handleDragOver(event)" ondrop="handleDrop(event, 'rejected')">
                <div class="kanban-header">
                    <span class="kanban-dot dot-rejected"></span>
                    <span class="kanban-title">Rejected</span>
                    <span class="kanban-badge" id="badge-rejected">{counts['rejected']}</span>
                </div>
                <div class="kanban-cards" id="cards-rejected"></div>
            </div>
        </div>

        <!-- Expanded Card Modal -->
        <div class="modal-overlay" id="card-modal" style="display:none" onclick="closeModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3 id="modal-role-name"></h3>
                    <button class="btn btn-icon" onclick="closeModal()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="modal-row">
                        <label>Status</label>
                        <div class="modal-status-btns" id="modal-status-btns"></div>
                    </div>
                    <div class="modal-row">
                        <label>Category</label>
                        <select id="modal-category" class="form-select" onchange="handleCategoryChange(this.value)">
                            <option value="Role">Role</option>
                            <option value="Management">Management</option>
                            <option value="Technical">Technical</option>
                            <option value="Organization">Organization</option>
                            <option value="Governance">Governance</option>
                            <option value="Engineering">Engineering</option>
                            <option value="Quality">Quality</option>
                            <option value="Safety">Safety</option>
                            <option value="Operations">Operations</option>
                            <option value="Support">Support</option>
                            <option value="Compliance">Compliance</option>
                            <option value="Procurement">Procurement</option>
                            <option value="Deliverable">Deliverable</option>
                            <option value="__custom__">+ Add Custom...</option>
                        </select>
                        <div id="modal-custom-category" style="display:none; margin-top:6px;">
                            <input type="text" id="modal-custom-category-input" class="form-select"
                                   placeholder="Type custom category name..."
                                   style="border-color:var(--accent);">
                        </div>
                    </div>
                    <div class="modal-row">
                        <label>Function Tags</label>
                        <div class="modal-tags" id="modal-tags"></div>
                        <div class="tag-selector" id="tag-selector">
                            <input type="text" class="tag-search" id="tag-search" placeholder="Search tags..." oninput="filterTags(this.value)">
                            <div class="tag-options" id="tag-options"></div>
                        </div>
                    </div>
                    <div class="modal-row">
                        <label>Notes</label>
                        <textarea id="modal-notes" class="form-textarea" placeholder="Add adjudication notes..." oninput="updateModalNotes(this.value)"></textarea>
                    </div>
                    <div class="modal-row">
                        <label>Source Documents</label>
                        <div class="modal-docs" id="modal-docs"></div>
                    </div>
                    <div class="modal-row">
                        <label>Confidence</label>
                        <div class="modal-confidence" id="modal-confidence"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="footer-left">
                <span class="footer-brand">AEGIS v{html_module.escape(version)}</span>
                <span class="footer-sep">&middot;</span>
                <span>Exported from {html_module.escape(hostname)}</span>
            </div>
            <div class="footer-right">
                <kbd>Drag</kbd> Move between columns
                <kbd>Click</kbd> Edit details
                <kbd>Ctrl+Z</kbd> Undo
                <kbd>Ctrl+Y</kbd> Redo
            </div>
        </footer>
    </div>

    <script>
{_get_js(safe_roles, safe_categories, safe_metadata)}
    </script>
</body>
</html>'''

    return html


def _get_css() -> str:
    """Return embedded CSS for the standalone HTML."""
    return '''
        /* ===== CSS Variables ===== */
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
            --accent-hover: #c49a3e;
            --accent-subtle: rgba(214,168,74,0.12);
            --success: #22c55e;
            --success-bg: rgba(34,197,94,0.1);
            --info: #3b82f6;
            --info-bg: rgba(59,130,246,0.1);
            --error: #ef4444;
            --error-bg: rgba(239,68,68,0.1);
            --warning: #f59e0b;
            --warning-bg: rgba(245,158,11,0.1);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
            --radius-xl: 18px;
        }

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

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-app);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
        }

        .app { max-width: 1600px; margin: 0 auto; padding: 20px 24px; }

        /* ===== Header ===== */
        .header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 16px 24px; margin-bottom: 16px;
            background: var(--bg-surface); border-radius: var(--radius-xl);
            border: 1px solid var(--border-default); box-shadow: var(--shadow-sm);
        }
        .header-left { display: flex; align-items: center; gap: 14px; }
        .header-right { display: flex; align-items: center; gap: 16px; }
        .aegis-logo { flex-shrink: 0; }
        h1 { font-size: 1.4rem; font-weight: 700; color: var(--text-primary); }
        .subtitle { font-size: 0.82rem; color: var(--text-muted); }

        .stat-cards { display: flex; gap: 10px; }
        .stat-card {
            display: flex; flex-direction: column; align-items: center;
            padding: 8px 18px; border-radius: var(--radius-md);
            cursor: pointer; transition: all 0.2s;
            background: var(--bg-secondary); border: 1px solid var(--border-subtle);
        }
        .stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
        .stat-card.active { border-color: var(--accent); background: var(--accent-subtle); }
        .stat-count { font-size: 1.3rem; font-weight: 700; line-height: 1.2; }
        .stat-label { font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
        .stat-pending .stat-count { color: var(--warning); }
        .stat-confirmed .stat-count { color: var(--success); }
        .stat-deliverable .stat-count { color: var(--info); }
        .stat-rejected .stat-count { color: var(--error); }

        /* ===== Toolbar ===== */
        .toolbar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px 16px; margin-bottom: 16px;
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default);
        }
        .toolbar-left { display: flex; align-items: center; gap: 10px; }
        .toolbar-right { display: flex; align-items: center; gap: 8px; }
        .search-input {
            padding: 7px 14px; border-radius: var(--radius-md);
            border: 1px solid var(--border-default); background: var(--bg-secondary);
            color: var(--text-primary); font-size: 13px; width: 260px;
            outline: none; transition: border-color 0.2s;
        }
        .search-input:focus { border-color: var(--accent); }
        .search-count { font-size: 12px; color: var(--text-muted); }
        /* v5.9.28: Filter dropdowns */
        .filter-dropdown { position: relative; }
        .btn-filter { padding: 6px 12px; font-size: 12px; border-radius: var(--radius-md); border: 1px solid var(--border-default); background: var(--bg-secondary); color: var(--text-primary); cursor: pointer; display: flex; align-items: center; gap: 6px; }
        .btn-filter:hover { border-color: var(--accent); }
        .btn-filter.active { border-color: var(--accent); background: rgba(214,168,74,0.1); color: var(--accent); }
        .filter-badge { background: var(--accent); color: #000; font-size: 10px; font-weight: 700; border-radius: 8px; padding: 0 5px; min-width: 16px; text-align: center; }
        .dropdown-panel { display: none; position: absolute; top: 100%; left: 0; margin-top: 4px; background: var(--bg-surface); border: 1px solid var(--border-default); border-radius: var(--radius-md); padding: 8px; min-width: 200px; max-height: 280px; overflow-y: auto; z-index: 100; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
        .dropdown-panel.open { display: block; }
        .dropdown-item { display: flex; align-items: center; gap: 8px; padding: 4px 6px; font-size: 12px; color: var(--text-primary); cursor: pointer; border-radius: 4px; }
        .dropdown-item:hover { background: rgba(255,255,255,0.05); }
        .dropdown-item input[type="checkbox"] { accent-color: var(--accent); }
        .changes-badge {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
            background: var(--accent-subtle); color: var(--accent); border: 1px solid var(--accent);
        }

        /* ===== Buttons ===== */
        .btn {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 7px 14px; border-radius: var(--radius-sm); border: none;
            font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s;
        }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-primary { background: var(--accent); color: #fff; }
        .btn-primary:hover:not(:disabled) { background: var(--accent-hover); transform: translateY(-1px); }
        .btn-secondary { background: var(--bg-secondary); color: var(--text-primary); border: 1px solid var(--border-default); }
        .btn-secondary:hover:not(:disabled) { background: var(--bg-hover); }
        .btn-icon { background: none; border: none; color: var(--text-secondary); padding: 6px; border-radius: var(--radius-sm); cursor: pointer; }
        .btn-icon:hover { background: var(--bg-hover); }
        .btn-success { background: var(--success); color: #fff; }
        .btn-success:hover { filter: brightness(1.1); }
        .btn-info { background: var(--info); color: #fff; }
        .btn-info:hover { filter: brightness(1.1); }
        .btn-danger { background: var(--error); color: #fff; }
        .btn-danger:hover { filter: brightness(1.1); }

        /* ===== Kanban Board ===== */
        .kanban-board {
            display: grid; grid-template-columns: repeat(4, 1fr);
            gap: 16px; min-height: calc(100vh - 280px);
        }
        .kanban-column {
            background: var(--bg-secondary); border-radius: var(--radius-lg);
            border: 1px solid var(--border-subtle); padding: 0;
            display: flex; flex-direction: column; max-height: calc(100vh - 280px);
            transition: all 0.2s;
        }
        .kanban-column.drag-over {
            outline: 2px dashed var(--accent); background: var(--accent-subtle);
            outline-offset: -2px;
        }
        .kanban-header {
            display: flex; align-items: center; gap: 8px;
            padding: 14px 16px; font-weight: 600; font-size: 0.9rem;
            position: sticky; top: 0; z-index: 2;
            background: var(--bg-secondary); border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            border-bottom: 1px solid var(--border-subtle); flex-shrink: 0;
        }
        .kanban-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
        .dot-pending { background: var(--warning); }
        .dot-confirmed { background: var(--success); }
        .dot-deliverable { background: var(--info); }
        .dot-rejected { background: var(--error); }
        .kanban-badge {
            margin-left: auto; padding: 1px 8px; border-radius: 12px;
            font-size: 11px; font-weight: 600; background: var(--bg-hover);
            color: var(--text-secondary);
        }
        .kanban-cards { padding: 8px; overflow-y: auto; flex: 1; }

        /* ===== Role Cards ===== */
        .role-card {
            padding: 12px; margin-bottom: 8px; border-radius: var(--radius-md);
            background: var(--bg-surface); border: 1px solid var(--border-default);
            cursor: grab; transition: all 0.2s; position: relative;
            border-left: 4px solid transparent;
        }
        .role-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
        .role-card:active { cursor: grabbing; }
        .role-card.dragging { opacity: 0.5; }
        .role-card[data-status="pending"] { border-left-color: var(--warning); }
        .role-card[data-status="confirmed"] { border-left-color: var(--success); }
        .role-card[data-status="deliverable"] { border-left-color: var(--info); }
        .role-card[data-status="rejected"] { border-left-color: var(--error); }

        .card-name { font-weight: 600; font-size: 0.88rem; margin-bottom: 6px; color: var(--text-primary); }
        .card-meta { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 6px; }
        .card-badge {
            display: inline-flex; align-items: center; padding: 1px 8px;
            border-radius: 10px; font-size: 10px; font-weight: 500;
        }
        .badge-category { background: var(--bg-hover); color: var(--text-secondary); }
        .badge-confidence-high { background: var(--success-bg); color: var(--success); }
        .badge-confidence-med { background: var(--warning-bg); color: var(--warning); }
        .badge-confidence-low { background: var(--error-bg); color: var(--error); }

        .card-tags { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
        .tag-pill {
            display: inline-flex; align-items: center; padding: 1px 7px;
            border-radius: 8px; font-size: 10px; font-weight: 500;
        }
        .card-docs { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
        .doc-chip {
            display: inline-flex; align-items: center; padding: 1px 6px;
            border-radius: 6px; font-size: 9px; color: var(--text-muted);
            background: var(--bg-secondary); border: 1px solid var(--border-subtle);
            max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }
        .card-changed {
            position: absolute; top: 6px; right: 6px; width: 8px; height: 8px;
            border-radius: 50%; background: var(--accent);
        }

        /* ===== Modal ===== */
        .modal-overlay {
            position: fixed; inset: 0; background: rgba(0,0,0,0.5);
            display: flex; align-items: center; justify-content: center;
            z-index: 1000; backdrop-filter: blur(4px);
        }
        .modal-content {
            background: var(--bg-surface); border-radius: var(--radius-xl);
            border: 1px solid var(--border-default); box-shadow: var(--shadow-lg);
            width: 560px; max-width: 95vw; max-height: 85vh; overflow-y: auto;
        }
        .modal-header {
            display: flex; justify-content: space-between; align-items: center;
            padding: 20px 24px 12px; border-bottom: 1px solid var(--border-subtle);
        }
        .modal-header h3 { font-size: 1.2rem; font-weight: 700; }
        .modal-body { padding: 16px 24px 24px; }
        .modal-row { margin-bottom: 16px; }
        .modal-row label {
            display: block; font-size: 0.78rem; font-weight: 600;
            color: var(--text-secondary); text-transform: uppercase;
            letter-spacing: 0.5px; margin-bottom: 6px;
        }
        .modal-status-btns { display: flex; gap: 8px; }
        .modal-status-btn {
            flex: 1; padding: 8px 12px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-default); background: var(--bg-secondary);
            color: var(--text-primary); font-size: 13px; font-weight: 500;
            cursor: pointer; transition: all 0.2s; text-align: center;
        }
        .modal-status-btn:hover { border-color: var(--accent); }
        .modal-status-btn.active-pending { background: var(--warning-bg); border-color: var(--warning); color: var(--warning); }
        .modal-status-btn.active-confirmed { background: var(--success-bg); border-color: var(--success); color: var(--success); }
        .modal-status-btn.active-deliverable { background: var(--info-bg); border-color: var(--info); color: var(--info); }
        .modal-status-btn.active-rejected { background: var(--error-bg); border-color: var(--error); color: var(--error); }

        .form-select, .form-textarea {
            width: 100%; padding: 8px 12px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-default); background: var(--bg-secondary);
            color: var(--text-primary); font-size: 13px; font-family: inherit;
            outline: none; transition: border-color 0.2s;
        }
        .form-select:focus, .form-textarea:focus { border-color: var(--accent); }
        .form-textarea { min-height: 80px; resize: vertical; }

        .modal-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
        .modal-tag {
            display: inline-flex; align-items: center; gap: 4px;
            padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 500;
            cursor: default;
        }
        .modal-tag .remove-tag {
            cursor: pointer; opacity: 0.6; font-size: 14px; line-height: 1;
            margin-left: 2px;
        }
        .modal-tag .remove-tag:hover { opacity: 1; }

        .tag-selector { margin-top: 4px; }
        .tag-search {
            width: 100%; padding: 6px 10px; border-radius: var(--radius-sm);
            border: 1px solid var(--border-default); background: var(--bg-secondary);
            color: var(--text-primary); font-size: 12px; outline: none;
            margin-bottom: 4px;
        }
        .tag-search:focus { border-color: var(--accent); }
        .tag-options { max-height: 180px; overflow-y: auto; }
        .tag-option {
            display: flex; align-items: center; gap: 8px;
            padding: 6px 10px; cursor: pointer; border-radius: var(--radius-sm);
            font-size: 12px; transition: background 0.15s;
        }
        .tag-option:hover { background: var(--bg-hover); }
        .tag-option.selected { background: var(--accent-subtle); }
        .tag-option-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .tag-option-code { font-weight: 600; color: var(--text-primary); }
        .tag-option-name { color: var(--text-secondary); }
        .tag-option-parent { font-size: 10px; color: var(--text-muted); margin-left: auto; }

        .modal-docs { display: flex; flex-wrap: wrap; gap: 4px; }
        .modal-doc {
            padding: 3px 10px; border-radius: 8px; font-size: 11px;
            background: var(--bg-secondary); border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
        }
        .modal-confidence { display: flex; align-items: center; gap: 10px; }
        .confidence-bar {
            flex: 1; height: 8px; border-radius: 4px; background: var(--bg-secondary);
            overflow: hidden; border: 1px solid var(--border-subtle);
        }
        .confidence-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
        .confidence-value { font-size: 13px; font-weight: 600; min-width: 40px; }

        /* ===== Footer ===== */
        .footer {
            display: flex; justify-content: space-between; align-items: center;
            padding: 14px 20px; margin-top: 16px;
            background: var(--bg-surface); border-radius: var(--radius-lg);
            border: 1px solid var(--border-default); font-size: 12px;
            color: var(--text-muted);
        }
        .footer-left { display: flex; align-items: center; gap: 8px; }
        .footer-right { display: flex; align-items: center; gap: 12px; }
        .footer-brand { color: var(--accent); font-weight: 600; }
        .footer-sep { opacity: 0.3; }
        kbd {
            padding: 2px 6px; border-radius: 4px; font-size: 10px;
            background: var(--bg-secondary); border: 1px solid var(--border-default);
            font-family: inherit; margin-right: 2px;
        }

        /* ===== Animations ===== */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .role-card { animation: fadeIn 0.2s ease; }

        /* ===== Responsive ===== */
        @media (max-width: 1200px) {
            .kanban-board { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 768px) {
            .kanban-board { grid-template-columns: 1fr; }
            .header { flex-direction: column; gap: 12px; }
            .stat-cards { flex-wrap: wrap; }
            .toolbar { flex-direction: column; gap: 8px; }
            .search-input { width: 100%; }
        }

        /* ===== Toast ===== */
        .toast {
            position: fixed; bottom: 20px; right: 20px; z-index: 2000;
            padding: 12px 20px; border-radius: var(--radius-md);
            background: var(--bg-elevated); border: 1px solid var(--border-default);
            box-shadow: var(--shadow-lg); font-size: 13px; color: var(--text-primary);
            animation: slideUp 0.3s ease;
        }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    '''


def _get_js(safe_roles: str, safe_categories: str, safe_metadata: str) -> str:
    """Return embedded JavaScript for the standalone HTML."""
    return f'''
    // ===== Data =====
    const INITIAL_ROLES = {safe_roles};
    const FUNCTION_CATEGORIES = {safe_categories};
    const EXPORT_META = {safe_metadata};

    // ===== State =====
    let roles = JSON.parse(JSON.stringify(INITIAL_ROLES)); // Deep clone
    let searchText = '';
    let statusFilter = null; // null = show all
    let currentModalRole = null;
    let isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Changes tracking
    const changes = new Map(); // role_name -> {{action, category, notes, function_tags}}

    // Undo/Redo
    const history = [];
    let historyPos = -1;

    // ===== Init =====
    document.addEventListener('DOMContentLoaded', () => {{
        if (isDark) document.documentElement.setAttribute('data-theme', 'dark');
        updateThemeIcon();
        initFilterDropdowns();
        renderBoard();

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.ctrlKey && e.key === 'z') {{ e.preventDefault(); undo(); }}
            if (e.ctrlKey && (e.key === 'y' || (e.shiftKey && e.key === 'Z'))) {{ e.preventDefault(); redo(); }}
            if (e.key === 'Escape') closeModal();
        }});
    }});

    // ===== Rendering =====
    function renderBoard() {{
        const filtered = getFilteredRoles();
        const columns = {{ pending: [], confirmed: [], deliverable: [], rejected: [] }};

        filtered.forEach(role => {{
            const status = role.status || 'pending';
            (columns[status] || columns.pending).push(role);
        }});

        Object.entries(columns).forEach(([status, statusRoles]) => {{
            const container = document.getElementById('cards-' + status);
            if (!container) return;
            container.innerHTML = statusRoles.map(r => renderCard(r)).join('');

            // Update badges
            const badge = document.getElementById('badge-' + status);
            if (badge) badge.textContent = statusRoles.length;
        }});

        // Update header stat counts (always show total, not filtered)
        updateStatCounts();
        initDragDrop();
    }}

    function renderCard(role) {{
        const conf = role.confidence || 0;
        const confClass = conf >= 0.85 ? 'badge-confidence-high' : conf >= 0.5 ? 'badge-confidence-med' : 'badge-confidence-low';
        const confPct = Math.round(conf * 100);
        const hasChange = changes.has(role.role_name);

        const tags = (role.function_tags || []).map(code => {{
            const cat = FUNCTION_CATEGORIES.find(c => c.code === code);
            const color = cat ? cat.color : '#6b7280';
            const name = cat ? cat.name : code;
            return `<span class="tag-pill" style="background: ${{color}}20; color: ${{color}}; border: 1px solid ${{color}}40">${{escHtml(name)}}</span>`;
        }}).join('');

        const docs = (role.documents || []).slice(0, 3).map(d => {{
            const short = d.length > 18 ? d.slice(0, 18) + '...' : d;
            return `<span class="doc-chip" title="${{escHtml(d)}}">${{escHtml(short)}}</span>`;
        }}).join('');

        return `
            <div class="role-card" draggable="true" data-role="${{escAttr(role.role_name)}}" data-status="${{role.status || 'pending'}}"
                 onclick="openModal('${{escAttr(role.role_name)}}')" ondragstart="handleDragStart(event)">
                ${{hasChange ? '<div class="card-changed"></div>' : ''}}
                <div class="card-name">${{escHtml(role.role_name)}}</div>
                <div class="card-meta">
                    <span class="card-badge badge-category">${{escHtml(role.category || 'Role')}}</span>
                    <span class="card-badge ${{confClass}}">${{confPct}}%</span>
                </div>
                ${{tags ? `<div class="card-tags">${{tags}}</div>` : ''}}
                ${{docs ? `<div class="card-docs">${{docs}}</div>` : ''}}
            </div>
        `;
    }}

    // v5.9.28: Filter state
    const activeFilters = {{ categories: new Set(), tags: new Set() }};

    function getFilteredRoles() {{
        let result = roles;
        if (searchText) {{
            const q = searchText.toLowerCase();
            result = result.filter(r => {{
                return r.role_name.toLowerCase().includes(q) ||
                       (r.category || '').toLowerCase().includes(q) ||
                       (r.documents || []).join(' ').toLowerCase().includes(q);
            }});
        }}
        if (statusFilter) {{
            result = result.filter(r => (r.status || 'pending') === statusFilter);
        }}
        if (activeFilters.categories.size > 0) {{
            result = result.filter(r => activeFilters.categories.has(r.category || 'Uncategorized'));
        }}
        if (activeFilters.tags.size > 0) {{
            result = result.filter(r => (r.function_tags || []).some(t => activeFilters.tags.has(t)));
        }}
        return result;
    }}

    function updateStatCounts() {{
        const counts = {{ pending: 0, confirmed: 0, deliverable: 0, rejected: 0 }};
        roles.forEach(r => {{ const s = r.status || 'pending'; counts[s] = (counts[s] || 0) + 1; }});
        Object.entries(counts).forEach(([status, count]) => {{
            const el = document.getElementById('count-' + status);
            if (el) el.textContent = count;
        }});
    }}

    // ===== Search & Filter =====
    function handleSearch(value) {{
        searchText = value;
        renderBoard();
        const countEl = document.getElementById('search-count');
        if (countEl) {{
            const filtered = getFilteredRoles();
            countEl.textContent = searchText ? `${{filtered.length}} / ${{roles.length}}` : '';
        }}
    }}

    function filterByStatus(status) {{
        const cards = document.querySelectorAll('.stat-card');
        if (statusFilter === status) {{
            statusFilter = null;
            cards.forEach(c => c.classList.remove('active'));
        }} else {{
            statusFilter = status;
            cards.forEach(c => {{
                c.classList.toggle('active', c.dataset.filter === status);
            }});
        }}
        renderBoard();
    }}

    // ===== v5.9.28: Category & Tag Filter Dropdowns =====
    function initFilterDropdowns() {{
        // Build category options
        const cats = new Set(roles.map(r => r.category || 'Uncategorized'));
        const catPanel = document.getElementById('panel-category');
        if (catPanel) {{
            catPanel.innerHTML = [...cats].sort().map(c =>
                `<label class="dropdown-item"><input type="checkbox" value="${{escHtml(c)}}" onchange="toggleFilter('categories', this.value, this.checked)"> ${{escHtml(c)}}</label>`
            ).join('');
        }}
        // Build tag options (top-level only for simplicity)
        const usedTags = new Set();
        roles.forEach(r => (r.function_tags || []).forEach(t => usedTags.add(t)));
        const tagPanel = document.getElementById('panel-tags');
        if (tagPanel && usedTags.size > 0) {{
            tagPanel.innerHTML = [...usedTags].sort().map(code => {{
                const cat = FUNCTION_CATEGORIES.find(c => c.code === code);
                const name = cat ? cat.name : code;
                const color = cat ? cat.color : '#6b7280';
                return `<label class="dropdown-item"><input type="checkbox" value="${{code}}" onchange="toggleFilter('tags', this.value, this.checked)"> <span style="color:${{color}}">\u25CF</span> ${{escHtml(name)}}</label>`;
            }}).join('');
        }}
    }}

    function toggleDropdown(id) {{
        const panel = document.querySelector('#' + id + ' .dropdown-panel');
        if (!panel) return;
        const wasOpen = panel.classList.contains('open');
        document.querySelectorAll('.dropdown-panel.open').forEach(p => p.classList.remove('open'));
        if (!wasOpen) panel.classList.add('open');
    }}

    function toggleFilter(type, value, checked) {{
        if (checked) activeFilters[type].add(value);
        else activeFilters[type].delete(value);
        // Update badge
        const badge = document.getElementById('badge-' + (type === 'categories' ? 'category' : type));
        const btn = badge?.parentElement;
        if (badge) {{
            badge.textContent = activeFilters[type].size;
            badge.style.display = activeFilters[type].size > 0 ? '' : 'none';
        }}
        if (btn) btn.classList.toggle('active', activeFilters[type].size > 0);
        renderBoard();
        // Update search count
        const countEl = document.getElementById('search-count');
        if (countEl) {{
            const filtered = getFilteredRoles();
            const hasFilter = searchText || statusFilter || activeFilters.categories.size || activeFilters.tags.size;
            countEl.textContent = hasFilter ? `${{filtered.length}} / ${{roles.length}}` : '';
        }}
    }}

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {{
        if (!e.target.closest('.filter-dropdown')) {{
            document.querySelectorAll('.dropdown-panel.open').forEach(p => p.classList.remove('open'));
        }}
    }});

    // ===== Drag & Drop =====
    let draggedRole = null;

    function handleDragStart(e) {{
        draggedRole = e.target.dataset.role;
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', draggedRole);
    }}

    function handleDragOver(e) {{
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        const col = e.currentTarget;
        col.classList.add('drag-over');
    }}

    function handleDrop(e, newStatus) {{
        e.preventDefault();
        const col = e.currentTarget;
        col.classList.remove('drag-over');

        if (!draggedRole) return;
        const role = roles.find(r => r.role_name === draggedRole);
        if (!role) return;

        const oldStatus = role.status || 'pending';
        if (oldStatus === newStatus) return;

        // Record for undo
        pushHistory({{ type: 'status', role_name: role.role_name, old: oldStatus, new: newStatus }});

        // Apply change
        role.status = newStatus;
        trackChange(role.role_name);
        renderBoard();
        showToast(`Moved "${{role.role_name}}" to ${{newStatus}}`);
        draggedRole = null;
    }}

    function initDragDrop() {{
        // Remove drag-over on drag leave
        document.querySelectorAll('.kanban-column').forEach(col => {{
            col.addEventListener('dragleave', (e) => {{
                if (!col.contains(e.relatedTarget)) col.classList.remove('drag-over');
            }});
        }});
        // Remove dragging class on drag end
        document.querySelectorAll('.role-card').forEach(card => {{
            card.addEventListener('dragend', () => card.classList.remove('dragging'));
        }});
    }}

    // ===== Modal =====
    function openModal(roleName) {{
        const role = roles.find(r => r.role_name === roleName);
        if (!role) return;
        currentModalRole = role;

        document.getElementById('modal-role-name').textContent = role.role_name;

        // Status buttons
        const statusBtns = document.getElementById('modal-status-btns');
        statusBtns.innerHTML = ['pending', 'confirmed', 'deliverable', 'rejected'].map(s => {{
            const isActive = (role.status || 'pending') === s;
            const activeClass = isActive ? `active-${{s}}` : '';
            return `<button class="modal-status-btn ${{activeClass}}" onclick="setModalStatus('${{s}}')">${{s.charAt(0).toUpperCase() + s.slice(1)}}</button>`;
        }}).join('');

        // Category - handle custom categories dynamically
        const catSelect = document.getElementById('modal-category');
        const catValue = role.category || 'Role';
        if (!Array.from(catSelect.options).find(o => o.value === catValue)) {{
            const opt = document.createElement('option');
            opt.value = catValue;
            opt.textContent = catValue;
            const customOpt = catSelect.querySelector('option[value="__custom__"]');
            if (customOpt) catSelect.insertBefore(opt, customOpt);
            else catSelect.appendChild(opt);
            customCategories.add(catValue);
        }}
        catSelect.value = catValue;
        document.getElementById('modal-custom-category').style.display = 'none';

        // Function tags
        renderModalTags(role);
        renderTagOptions();

        // Notes
        document.getElementById('modal-notes').value = role.notes || '';

        // Documents
        const docsContainer = document.getElementById('modal-docs');
        docsContainer.innerHTML = (role.documents || []).map(d =>
            `<span class="modal-doc">${{escHtml(d)}}</span>`
        ).join('') || '<span style="color:var(--text-muted);font-size:12px">No documents</span>';

        // Confidence
        const conf = role.confidence || 0;
        const confPct = Math.round(conf * 100);
        const confColor = conf >= 0.85 ? 'var(--success)' : conf >= 0.5 ? 'var(--warning)' : 'var(--error)';
        document.getElementById('modal-confidence').innerHTML = `
            <div class="confidence-bar"><div class="confidence-fill" style="width:${{confPct}}%;background:${{confColor}}"></div></div>
            <span class="confidence-value" style="color:${{confColor}}">${{confPct}}%</span>
        `;

        document.getElementById('card-modal').style.display = 'flex';
    }}

    function closeModal(e) {{
        if (e && e.target !== e.currentTarget && !e) return;
        document.getElementById('card-modal').style.display = 'none';
        currentModalRole = null;
    }}

    function setModalStatus(newStatus) {{
        if (!currentModalRole) return;
        const oldStatus = currentModalRole.status || 'pending';
        if (oldStatus === newStatus) return;

        pushHistory({{ type: 'status', role_name: currentModalRole.role_name, old: oldStatus, new: newStatus }});
        currentModalRole.status = newStatus;
        trackChange(currentModalRole.role_name);

        // Re-render status buttons
        const statusBtns = document.getElementById('modal-status-btns');
        statusBtns.querySelectorAll('.modal-status-btn').forEach(btn => {{
            const s = btn.textContent.toLowerCase();
            btn.className = 'modal-status-btn' + (s === newStatus ? ` active-${{s}}` : '');
        }});
        renderBoard();
    }}

    // Custom categories added by user
    const customCategories = new Set();

    function handleCategoryChange(value) {{
        if (value === '__custom__') {{
            document.getElementById('modal-custom-category').style.display = 'block';
            const input = document.getElementById('modal-custom-category-input');
            input.value = '';
            input.focus();
            input.onkeydown = (e) => {{
                if (e.key === 'Enter' && input.value.trim()) {{
                    applyCustomCategory(input.value.trim());
                }} else if (e.key === 'Escape') {{
                    document.getElementById('modal-custom-category').style.display = 'none';
                    document.getElementById('modal-category').value = currentModalRole?.category || 'Role';
                }}
            }};
            input.onblur = () => {{
                if (input.value.trim()) {{
                    applyCustomCategory(input.value.trim());
                }} else {{
                    document.getElementById('modal-custom-category').style.display = 'none';
                    document.getElementById('modal-category').value = currentModalRole?.category || 'Role';
                }}
            }};
            return;
        }}
        document.getElementById('modal-custom-category').style.display = 'none';
        updateModalCategory(value);
    }}

    function applyCustomCategory(name) {{
        document.getElementById('modal-custom-category').style.display = 'none';
        // Add to dropdown if not already there
        const select = document.getElementById('modal-category');
        const existing = Array.from(select.options).find(o => o.value === name);
        if (!existing) {{
            const opt = document.createElement('option');
            opt.value = name;
            opt.textContent = name;
            // Insert before __custom__
            const customOpt = select.querySelector('option[value="__custom__"]');
            select.insertBefore(opt, customOpt);
            customCategories.add(name);
        }}
        select.value = name;
        updateModalCategory(name);
    }}

    function updateModalCategory(value) {{
        if (!currentModalRole) return;
        const old = currentModalRole.category;
        pushHistory({{ type: 'category', role_name: currentModalRole.role_name, old: old, new: value }});
        currentModalRole.category = value;
        trackChange(currentModalRole.role_name);
        renderBoard();
    }}

    function updateModalNotes(value) {{
        if (!currentModalRole) return;
        currentModalRole.notes = value;
        trackChange(currentModalRole.role_name);
    }}

    function renderModalTags(role) {{
        const container = document.getElementById('modal-tags');
        const tags = role.function_tags || [];
        container.innerHTML = tags.map(code => {{
            const cat = FUNCTION_CATEGORIES.find(c => c.code === code);
            const color = cat ? cat.color : '#6b7280';
            const name = cat ? cat.name : code;
            return `<span class="modal-tag" style="background: ${{color}}20; color: ${{color}}; border: 1px solid ${{color}}40">
                ${{escHtml(name)}}
                <span class="remove-tag" onclick="removeTag('${{escAttr(code)}}')">&times;</span>
            </span>`;
        }}).join('') || '<span style="color:var(--text-muted);font-size:12px">No tags assigned</span>';
    }}

    function renderTagOptions() {{
        const container = document.getElementById('tag-options');
        const currentTags = new Set(currentModalRole ? (currentModalRole.function_tags || []) : []);
        const search = (document.getElementById('tag-search')?.value || '').toLowerCase();

        // Build maps for hierarchy
        const allCats = FUNCTION_CATEGORIES.filter(c => c.is_active !== 0);
        const roots = allCats.filter(c => !c.parent_code);
        const byParent = {{}};
        allCats.forEach(c => {{
            if (c.parent_code) {{
                if (!byParent[c.parent_code]) byParent[c.parent_code] = [];
                byParent[c.parent_code].push(c);
            }}
        }});

        function matchesSearch(cat) {{
            if (!search) return true;
            return cat.name.toLowerCase().includes(search) || cat.code.toLowerCase().includes(search);
        }}

        function hasDescendantMatch(code) {{
            const kids = byParent[code] || [];
            for (const kid of kids) {{
                if (matchesSearch(kid)) return true;
                if (hasDescendantMatch(kid.code)) return true;
            }}
            return false;
        }}

        let html = '';
        roots.forEach(parent => {{
            const showParent = matchesSearch(parent) || hasDescendantMatch(parent.code);
            if (!showParent) return;

            const isSelected = currentTags.has(parent.code);
            html += `<div class="tag-option ${{isSelected ? 'selected' : ''}}" onclick="toggleTag('${{escAttr(parent.code)}}')">
                <span class="tag-option-dot" style="background:${{parent.color || '#6b7280'}}"></span>
                <span class="tag-option-code">${{escHtml(parent.code)}}</span>
                <span class="tag-option-name">${{escHtml(parent.name)}}</span>
            </div>`;

            // Level 2 children
            const children = byParent[parent.code] || [];
            children.forEach(child => {{
                const showChild = matchesSearch(child) || hasDescendantMatch(child.code) || (!search && true);
                if (!showChild && search) return;

                const isChildSelected = currentTags.has(child.code);
                html += `<div class="tag-option ${{isChildSelected ? 'selected' : ''}}" style="padding-left:28px" onclick="toggleTag('${{escAttr(child.code)}}')">
                    <span class="tag-option-dot" style="background:${{child.color || parent.color || '#6b7280'}}; width:6px; height:6px"></span>
                    <span class="tag-option-code">${{escHtml(child.code)}}</span>
                    <span class="tag-option-name">${{escHtml(child.name)}}</span>
                </div>`;

                // Level 3 grandchildren
                const grandchildren = byParent[child.code] || [];
                grandchildren.forEach(gc => {{
                    if (search && !matchesSearch(gc)) return;
                    const isGcSelected = currentTags.has(gc.code);
                    html += `<div class="tag-option ${{isGcSelected ? 'selected' : ''}}" style="padding-left:48px" onclick="toggleTag('${{escAttr(gc.code)}}')">
                        <span class="tag-option-dot" style="background:${{gc.color || child.color || parent.color || '#6b7280'}}; width:5px; height:5px"></span>
                        <span class="tag-option-code">${{escHtml(gc.code)}}</span>
                        <span class="tag-option-name">${{escHtml(gc.name)}}</span>
                        <span class="tag-option-parent">${{escHtml(child.code)}}</span>
                    </div>`;
                }});
            }});
        }});

        container.innerHTML = html || '<div style="padding:8px;color:var(--text-muted);font-size:12px">No matching tags</div>';
    }}

    function filterTags(value) {{ renderTagOptions(); }}

    function toggleTag(code) {{
        if (!currentModalRole) return;
        const tags = currentModalRole.function_tags || [];
        const idx = tags.indexOf(code);

        if (idx >= 0) {{
            pushHistory({{ type: 'tag_remove', role_name: currentModalRole.role_name, tag: code }});
            tags.splice(idx, 1);
        }} else {{
            pushHistory({{ type: 'tag_add', role_name: currentModalRole.role_name, tag: code }});
            tags.push(code);
        }}
        currentModalRole.function_tags = tags;
        trackChange(currentModalRole.role_name);
        renderModalTags(currentModalRole);
        renderTagOptions();
        renderBoard();
    }}

    function removeTag(code) {{
        if (!currentModalRole) return;
        const tags = currentModalRole.function_tags || [];
        const idx = tags.indexOf(code);
        if (idx >= 0) {{
            pushHistory({{ type: 'tag_remove', role_name: currentModalRole.role_name, tag: code }});
            tags.splice(idx, 1);
            currentModalRole.function_tags = tags;
            trackChange(currentModalRole.role_name);
            renderModalTags(currentModalRole);
            renderTagOptions();
            renderBoard();
        }}
    }}

    // ===== Changes Tracking =====
    function trackChange(roleName) {{
        const role = roles.find(r => r.role_name === roleName);
        if (!role) return;
        const original = INITIAL_ROLES.find(r => r.role_name === roleName);

        // Check if actually different from original
        const isDifferent = !original ||
            role.status !== (original.status || 'pending') ||
            role.category !== (original.category || 'Role') ||
            role.notes !== (original.notes || '') ||
            JSON.stringify(role.function_tags || []) !== JSON.stringify(original.function_tags || []);

        if (isDifferent) {{
            changes.set(roleName, {{
                role_name: roleName,
                action: role.status || 'pending',
                category: role.category || 'Role',
                notes: role.notes || '',
                function_tags: role.function_tags || []
            }});
        }} else {{
            changes.delete(roleName);
        }}

        // Update UI
        const badge = document.getElementById('changes-badge');
        const countEl = document.getElementById('changes-count');
        if (badge && countEl) {{
            const n = changes.size;
            badge.style.display = n > 0 ? 'inline-flex' : 'none';
            countEl.textContent = n;
        }}
    }}

    // ===== Undo / Redo =====
    function pushHistory(action) {{
        // Truncate any redo history
        history.length = historyPos + 1;
        history.push(action);
        historyPos = history.length - 1;
        updateUndoRedoBtns();
    }}

    function undo() {{
        if (historyPos < 0) return;
        const action = history[historyPos];
        historyPos--;
        applyReverse(action);
        updateUndoRedoBtns();
        renderBoard();
        if (currentModalRole && currentModalRole.role_name === action.role_name) openModal(action.role_name);
    }}

    function redo() {{
        if (historyPos >= history.length - 1) return;
        historyPos++;
        const action = history[historyPos];
        applyForward(action);
        updateUndoRedoBtns();
        renderBoard();
        if (currentModalRole && currentModalRole.role_name === action.role_name) openModal(action.role_name);
    }}

    function applyReverse(action) {{
        const role = roles.find(r => r.role_name === action.role_name);
        if (!role) return;
        switch (action.type) {{
            case 'status': role.status = action.old; break;
            case 'category': role.category = action.old; break;
            case 'tag_add': {{
                const idx = (role.function_tags || []).indexOf(action.tag);
                if (idx >= 0) role.function_tags.splice(idx, 1);
                break;
            }}
            case 'tag_remove': {{
                if (!role.function_tags) role.function_tags = [];
                role.function_tags.push(action.tag);
                break;
            }}
        }}
        trackChange(role.role_name);
    }}

    function applyForward(action) {{
        const role = roles.find(r => r.role_name === action.role_name);
        if (!role) return;
        switch (action.type) {{
            case 'status': role.status = action.new; break;
            case 'category': role.category = action.new; break;
            case 'tag_add': {{
                if (!role.function_tags) role.function_tags = [];
                role.function_tags.push(action.tag);
                break;
            }}
            case 'tag_remove': {{
                const idx = (role.function_tags || []).indexOf(action.tag);
                if (idx >= 0) role.function_tags.splice(idx, 1);
                break;
            }}
        }}
        trackChange(role.role_name);
    }}

    function updateUndoRedoBtns() {{
        const undoBtn = document.getElementById('btn-undo');
        const redoBtn = document.getElementById('btn-redo');
        if (undoBtn) undoBtn.disabled = historyPos < 0;
        if (redoBtn) redoBtn.disabled = historyPos >= history.length - 1;
    }}

    // ===== Generate Import File =====
    function generateImportFile() {{
        if (changes.size === 0) {{
            showToast('No changes to export');
            return;
        }}

        const decisions = Array.from(changes.values());
        const counts = {{ pending: 0, confirmed: 0, deliverable: 0, rejected: 0 }};
        roles.forEach(r => {{ const s = r.status || 'pending'; counts[s] = (counts[s] || 0) + 1; }});

        const importData = {{
            aegis_version: EXPORT_META.aegis_version,
            export_type: 'adjudication_decisions',
            exported_at: new Date().toISOString(),
            exported_by: EXPORT_META.exported_by,
            decisions: decisions,
            summary: {{
                total: roles.length,
                changed: decisions.length,
                ...counts
            }}
        }};

        const blob = new Blob([JSON.stringify(importData, null, 2)], {{ type: 'application/json' }});
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `adjudication_decisions_${{new Date().toISOString().slice(0, 10)}}.json`;
        a.click();
        URL.revokeObjectURL(a.href);
        showToast(`Exported ${{decisions.length}} decision(s) to JSON`);
    }}

    // ===== Theme =====
    function toggleTheme() {{
        isDark = !isDark;
        if (isDark) {{
            document.documentElement.setAttribute('data-theme', 'dark');
        }} else {{
            document.documentElement.removeAttribute('data-theme');
        }}
        updateThemeIcon();
    }}

    function updateThemeIcon() {{
        const sun = document.getElementById('icon-sun');
        const moon = document.getElementById('icon-moon');
        if (sun) sun.style.display = isDark ? 'none' : 'block';
        if (moon) moon.style.display = isDark ? 'block' : 'none';
    }}

    // ===== Toast =====
    function showToast(message) {{
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }}

    // ===== Utilities =====
    function escHtml(str) {{
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }}
    function escAttr(str) {{
        if (!str) return '';
        return String(str).replace(/'/g, "\\\\'").replace(/"/g, '&quot;');
    }}
    '''
