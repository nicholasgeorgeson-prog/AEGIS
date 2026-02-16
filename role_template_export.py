"""
AEGIS Role Import Template - Interactive HTML Generator

Generates a standalone interactive HTML file (no external dependencies) that users
download and open in their browser to manually populate roles. They can add roles
one-by-one or bulk-paste from any format (Excel, CSV, plain text). Then export a
JSON file to import back into AEGIS.

Usage:
    from role_template_export import generate_role_template_html
    html = generate_role_template_html(function_categories, metadata)
"""

import json
import html as html_module
from datetime import datetime, timezone
from typing import List, Dict, Optional
import socket


def generate_role_template_html(
    function_categories: Optional[List[Dict]] = None,
    metadata: Optional[Dict] = None
) -> str:
    """Generate an interactive standalone HTML template for manual role entry.

    Args:
        function_categories: List of dicts with 'code', 'name', 'color', 'description'
                           for the tag picker. Can be None/empty.
        metadata: Dict with 'aegis_version', 'exported_at', 'exported_by'.

    Returns:
        str: Complete HTML string.
    """
    if function_categories is None:
        function_categories = []
    if metadata is None:
        metadata = {}

    version = metadata.get('aegis_version', '4.1.0')
    export_date = metadata.get('exported_at', datetime.now(timezone.utc).isoformat())
    hostname = metadata.get('exported_by', socket.gethostname())

    # Sanitize data for JSON embedding
    safe_categories = json.dumps(function_categories, default=str)
    safe_metadata = json.dumps({
        'aegis_version': version,
        'exported_at': export_date,
        'exported_by': hostname,
    }, default=str)

    display_date = export_date[:10] if len(export_date) >= 10 else export_date

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS Role Import Template</title>
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
                    <h1>AEGIS Role Import Template</h1>
                    <p class="subtitle">Add roles below, then export as JSON to import into AEGIS</p>
                </div>
            </div>
            <div class="header-right">
                <span class="version-badge">v{html_module.escape(version)}</span>
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

        <!-- Stat Cards -->
        <div class="stat-cards" id="stat-cards">
            <div class="stat-card">
                <span class="stat-count" id="stat-total">0</span>
                <span class="stat-label">Total Roles</span>
            </div>
            <div class="stat-card stat-deliverable">
                <span class="stat-count" id="stat-deliverables">0</span>
                <span class="stat-label">Deliverables</span>
            </div>
            <div class="stat-card stat-tags">
                <span class="stat-count" id="stat-with-tags">0</span>
                <span class="stat-label">With Tags</span>
            </div>
            <div class="stat-card stat-desc">
                <span class="stat-count" id="stat-with-desc">0</span>
                <span class="stat-label">With Description</span>
            </div>
        </div>

        <!-- Role Entry Form -->
        <div class="form-section" id="form-section">
            <div class="form-header" onclick="toggleFormSection()">
                <h2>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    </svg>
                    Add Role
                </h2>
                <svg class="form-toggle-icon" id="form-toggle-icon" width="20" height="20" viewBox="0 0 24 24"
                     fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            </div>
            <div class="form-body" id="form-body">
                <div class="form-grid">
                    <div class="form-group">
                        <label for="inp-role-name">Role Name <span class="required">*</span></label>
                        <input type="text" id="inp-role-name" class="form-input" placeholder="e.g., Systems Engineer"
                               required>
                    </div>
                    <div class="form-group">
                        <label for="inp-category">Category</label>
                        <select id="inp-category" class="form-select">
                            <option value="Role">Role</option>
                            <option value="Management">Management</option>
                            <option value="Technical">Technical</option>
                            <option value="Deliverable">Deliverable</option>
                            <option value="Tools & Systems">Tools &amp; Systems</option>
                            <option value="Custom">Custom</option>
                        </select>
                    </div>
                    <div class="form-group form-group-wide">
                        <label for="inp-description">Description</label>
                        <textarea id="inp-description" class="form-input" rows="2"
                                  placeholder="Brief description of the role..."></textarea>
                    </div>
                    <div class="form-group">
                        <label for="inp-aliases">Aliases</label>
                        <input type="text" id="inp-aliases" class="form-input"
                               placeholder="Comma-separated aliases">
                    </div>
                    <div class="form-group">
                        <label for="inp-role-type">Role Type</label>
                        <select id="inp-role-type" class="form-select">
                            <option value="">(none)</option>
                            <option value="Singular-Specific">Singular-Specific</option>
                            <option value="Singular-Aggregate">Singular-Aggregate</option>
                            <option value="Group-Specific">Group-Specific</option>
                            <option value="Group-Aggregate">Group-Aggregate</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="inp-disposition">Disposition</label>
                        <select id="inp-disposition" class="form-select">
                            <option value="">(none)</option>
                            <option value="Sanctioned">Sanctioned</option>
                            <option value="To Be Retired">To Be Retired</option>
                            <option value="TBD">TBD</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="inp-org-group">Org Group</label>
                        <input type="text" id="inp-org-group" class="form-input"
                               placeholder="e.g., Engineering">
                    </div>
                    <div class="form-group form-group-checks">
                        <label class="checkbox-label">
                            <input type="checkbox" id="inp-deliverable">
                            <span>Mark as deliverable</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" id="inp-baselined">
                            <span>Baselined in process model</span>
                        </label>
                    </div>
                    <div class="form-group form-group-wide">
                        <label>Function Tags</label>
                        <div class="tag-picker" id="tag-picker">
                            <div class="tag-pills" id="tag-pills"></div>
                            <div class="tag-input-wrap">
                                <input type="text" id="inp-tag-search" class="form-input tag-search-input"
                                       placeholder="Search or type a tag and press Enter"
                                       oninput="handleTagSearch(this.value)"
                                       onkeydown="handleTagKeydown(event)">
                                <div class="tag-dropdown" id="tag-dropdown" style="display:none"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="form-actions">
                    <button class="btn btn-primary" id="btn-add-role" onclick="addOrUpdateRole()">Add Role</button>
                    <button class="btn btn-secondary" onclick="clearForm()">Clear Form</button>
                </div>
            </div>
        </div>

        <!-- Toolbar -->
        <div class="toolbar">
            <div class="toolbar-left">
                <input type="text" id="search-input" class="search-input" placeholder="Search roles..."
                       oninput="handleSearch(this.value)">
                <span class="role-count" id="role-count">0 roles</span>
            </div>
            <div class="toolbar-right">
                <button class="btn btn-secondary" onclick="openBulkModal()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="8" y1="8" x2="16" y2="8"/>
                        <line x1="8" y1="12" x2="16" y2="12"/><line x1="8" y1="16" x2="12" y2="16"/>
                    </svg>
                    Bulk Add
                </button>
                <button class="btn btn-primary" onclick="exportJSON()">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    Export JSON
                </button>
                <button class="btn btn-danger-outline" onclick="clearAllRoles()">Clear All</button>
            </div>
        </div>

        <!-- Role Table -->
        <div class="table-wrap" id="table-wrap">
            <table class="role-table" id="role-table">
                <thead>
                    <tr>
                        <th class="th-check"><input type="checkbox" id="select-all" onchange="toggleSelectAll(this.checked)"></th>
                        <th class="th-num" onclick="sortTable('index')">#</th>
                        <th onclick="sortTable('role_name')">Role Name <span class="sort-arrow" id="sort-role_name"></span></th>
                        <th onclick="sortTable('category')">Category <span class="sort-arrow" id="sort-category"></span></th>
                        <th onclick="sortTable('org_group')">Org Group <span class="sort-arrow" id="sort-org_group"></span></th>
                        <th onclick="sortTable('role_type')">Type <span class="sort-arrow" id="sort-role_type"></span></th>
                        <th onclick="sortTable('role_disposition')">Disposition <span class="sort-arrow" id="sort-role_disposition"></span></th>
                        <th>Deliverable</th>
                        <th>Tags</th>
                        <th class="th-actions">Actions</th>
                    </tr>
                </thead>
                <tbody id="role-tbody"></tbody>
            </table>
            <div class="empty-state" id="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
                </svg>
                <p>No roles added yet.</p>
                <p class="empty-hint">Use the form above or click <strong>Bulk Add</strong> to get started.</p>
            </div>
        </div>

        <!-- Bulk Delete Bar -->
        <div class="bulk-bar" id="bulk-bar" style="display:none">
            <span id="bulk-count">0 selected</span>
            <button class="btn btn-danger-outline btn-sm" onclick="bulkDeleteSelected()">Delete Selected</button>
            <button class="btn btn-secondary btn-sm" onclick="clearSelection()">Clear Selection</button>
        </div>

        <!-- Bulk Paste Modal -->
        <div class="modal-overlay" id="bulk-modal" style="display:none" onclick="closeBulkModal(event)">
            <div class="modal-content modal-large" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3>Bulk Add Roles</h3>
                    <button class="btn btn-icon" onclick="closeBulkModal()">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </div>
                <div class="modal-body">
                    <div id="bulk-input-section">
                        <p class="bulk-instructions">Paste roles from Excel, CSV, or plain text. One role per line,
                        or use tab/comma delimiters for multiple columns.</p>
                        <textarea id="bulk-textarea" class="form-input bulk-textarea" rows="16"
                                  placeholder="Paste roles from Excel, CSV, or plain text...&#10;&#10;Examples:&#10;Systems Engineer&#10;Program Manager, Management, Oversees program activities&#10;Role Name&#9;Category&#9;Description"></textarea>
                        <div class="bulk-format-hint" id="bulk-format-hint">Auto-detecting format...</div>
                        <div class="bulk-actions">
                            <button class="btn btn-primary" onclick="parseBulkInput()">Parse</button>
                            <button class="btn btn-secondary" onclick="closeBulkModal()">Cancel</button>
                        </div>
                    </div>
                    <div id="bulk-preview-section" style="display:none">
                        <div class="bulk-preview-header">
                            <h4>Preview: <span id="bulk-preview-count">0</span> roles detected</h4>
                            <button class="btn btn-secondary btn-sm" onclick="backToBulkInput()">Back to Edit</button>
                        </div>
                        <div class="bulk-preview-table-wrap">
                            <table class="role-table bulk-preview-table">
                                <thead id="bulk-preview-thead"></thead>
                                <tbody id="bulk-preview-tbody"></tbody>
                            </table>
                        </div>
                        <div class="bulk-actions">
                            <button class="btn btn-primary" id="btn-import-bulk" onclick="importBulkRoles()">
                                Import Roles
                            </button>
                            <button class="btn btn-secondary" onclick="closeBulkModal()">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Confirm Dialog -->
        <div class="modal-overlay" id="confirm-modal" style="display:none" onclick="cancelConfirm()">
            <div class="modal-content modal-small" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h3 id="confirm-title">Confirm</h3>
                </div>
                <div class="modal-body">
                    <p id="confirm-message"></p>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="cancelConfirm()">Cancel</button>
                    <button class="btn btn-danger" id="confirm-ok-btn" onclick="doConfirm()">Confirm</button>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="footer">
            <div class="footer-left">
                <span class="footer-brand">Generated by AEGIS v{html_module.escape(version)}</span>
                <span class="footer-sep">&middot;</span>
                <span>{html_module.escape(display_date)}</span>
            </div>
            <div class="footer-right">
                <kbd>Tab</kbd> through fields
                <kbd>Enter</kbd> to add
                <kbd>Ctrl+E</kbd> to export
            </div>
        </footer>
    </div>

    <!-- Toast Container -->
    <div id="toast-container"></div>

    <!-- Embedded Data -->
    <script id="template-categories" type="application/json">
    {safe_categories}
    </script>
    <script id="template-metadata" type="application/json">
    {safe_metadata}
    </script>

    <script>
{_get_js()}
    </script>
</body>
</html>'''

    return html


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
            --bg-input: #ffffff;
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
            --accent-dark: #B8743A;
            --accent-subtle: rgba(214,168,74,0.12);
            --success: #10b981;
            --success-bg: rgba(16,185,129,0.1);
            --info: #3b82f6;
            --info-bg: rgba(59,130,246,0.1);
            --danger: #ef4444;
            --danger-bg: rgba(239,68,68,0.1);
            --warning: #f59e0b;
            --warning-bg: rgba(245,158,11,0.1);
            --radius-sm: 6px;
            --radius-md: 10px;
            --radius-lg: 14px;
        }

        [data-theme="dark"] {
            --bg-app: #0f1117;
            --bg-surface: #1a1c25;
            --bg-secondary: #12141b;
            --bg-elevated: #22242e;
            --bg-hover: rgba(255,255,255,0.06);
            --bg-input: #1e2030;
            --text-primary: #e8e9ed;
            --text-secondary: #a0a3b5;
            --text-muted: #6b6e82;
            --border-default: #2a2d3a;
            --border-subtle: #1f2230;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
            --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
        }

        /* ===== Base ===== */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-app);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
        }

        .app {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        /* ===== Header ===== */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background: var(--bg-surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            margin-bottom: 16px;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .header-left h1 {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .header-left .subtitle {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .version-badge {
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--accent);
            background: var(--accent-subtle);
            padding: 3px 10px;
            border-radius: 20px;
            letter-spacing: 0.3px;
        }

        .aegis-logo {
            flex-shrink: 0;
        }

        /* ===== Buttons ===== */
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border: 1px solid transparent;
            border-radius: var(--radius-sm);
            font-size: 0.85rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s;
            white-space: nowrap;
            font-family: inherit;
        }

        .btn:hover { opacity: 0.88; }

        .btn-primary {
            background: var(--accent);
            color: #fff;
            border-color: var(--accent);
        }
        .btn-primary:hover { background: var(--accent-hover); }

        .btn-secondary {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border-color: var(--border-default);
        }
        .btn-secondary:hover { background: var(--bg-hover); }

        .btn-danger {
            background: var(--danger);
            color: #fff;
            border-color: var(--danger);
        }

        .btn-danger-outline {
            background: transparent;
            color: var(--danger);
            border-color: var(--danger);
        }
        .btn-danger-outline:hover {
            background: var(--danger-bg);
        }

        .btn-icon {
            padding: 6px;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm);
            cursor: pointer;
            transition: all 0.15s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .btn-icon:hover { background: var(--bg-hover); color: var(--text-primary); }

        .btn-sm { padding: 5px 10px; font-size: 0.78rem; }

        /* ===== Stat Cards ===== */
        .stat-cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }

        .stat-card {
            background: var(--bg-surface);
            border-radius: var(--radius-md);
            padding: 16px 18px;
            box-shadow: var(--shadow-sm);
            text-align: center;
            border-left: 3px solid var(--accent);
            transition: transform 0.15s;
        }
        .stat-card:hover { transform: translateY(-2px); }

        .stat-card.stat-deliverable { border-left-color: var(--success); }
        .stat-card.stat-tags { border-left-color: var(--info); }
        .stat-card.stat-desc { border-left-color: var(--warning); }

        .stat-count {
            display: block;
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .stat-label {
            font-size: 0.78rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 2px;
        }

        /* ===== Form Section ===== */
        .form-section {
            background: var(--bg-surface);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            margin-bottom: 16px;
            overflow: hidden;
        }

        .form-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 20px;
            cursor: pointer;
            user-select: none;
            transition: background 0.15s;
        }
        .form-header:hover { background: var(--bg-hover); }

        .form-header h2 {
            font-size: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-primary);
        }

        .form-toggle-icon {
            transition: transform 0.2s;
            color: var(--text-muted);
        }
        .form-section.collapsed .form-toggle-icon {
            transform: rotate(-90deg);
        }
        .form-section.collapsed .form-body {
            display: none;
        }

        .form-body {
            padding: 0 20px 20px;
        }

        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        .form-group-wide {
            grid-column: 1 / -1;
        }

        .form-group-checks {
            display: flex;
            flex-direction: row;
            align-items: center;
            gap: 20px;
            padding-top: 8px;
        }

        .form-group label {
            font-size: 0.82rem;
            font-weight: 500;
            color: var(--text-secondary);
        }

        .required {
            color: var(--danger);
        }

        .form-input, .form-select {
            padding: 8px 12px;
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm);
            background: var(--bg-input);
            color: var(--text-primary);
            font-size: 0.88rem;
            font-family: inherit;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-subtle);
        }
        .form-input.error {
            border-color: var(--danger);
            box-shadow: 0 0 0 3px var(--danger-bg);
        }

        textarea.form-input {
            resize: vertical;
            min-height: 56px;
        }

        .checkbox-label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
            color: var(--text-secondary);
            cursor: pointer;
        }
        .checkbox-label input[type="checkbox"] {
            width: 16px;
            height: 16px;
            accent-color: var(--accent);
        }

        .form-actions {
            display: flex;
            gap: 10px;
            margin-top: 16px;
            padding-top: 14px;
            border-top: 1px solid var(--border-subtle);
        }

        /* ===== Tag Picker ===== */
        .tag-picker {
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm);
            background: var(--bg-input);
            padding: 6px 8px;
            min-height: 42px;
            transition: border-color 0.15s;
        }
        .tag-picker:focus-within {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-subtle);
        }

        .tag-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 4px;
        }
        .tag-pills:empty { margin-bottom: 0; }

        .tag-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 8px;
            border-radius: 20px;
            font-size: 0.76rem;
            font-weight: 500;
            color: #fff;
            background: var(--accent);
        }
        .tag-pill .tag-remove {
            cursor: pointer;
            font-size: 0.9rem;
            line-height: 1;
            opacity: 0.7;
            margin-left: 2px;
        }
        .tag-pill .tag-remove:hover { opacity: 1; }

        .tag-input-wrap {
            position: relative;
        }

        .tag-search-input {
            border: none !important;
            box-shadow: none !important;
            padding: 4px 6px !important;
            font-size: 0.84rem;
            width: 100%;
            background: transparent !important;
        }

        .tag-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            max-height: 200px;
            overflow-y: auto;
            background: var(--bg-surface);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-md);
            z-index: 100;
        }

        .tag-option {
            padding: 6px 10px;
            cursor: pointer;
            font-size: 0.84rem;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: background 0.1s;
        }
        .tag-option:hover { background: var(--bg-hover); }

        .tag-option-color {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .tag-option-code {
            font-weight: 600;
            color: var(--text-primary);
        }

        .tag-option-name {
            color: var(--text-secondary);
        }

        /* ===== Toolbar ===== */
        .toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: var(--bg-surface);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            margin-bottom: 12px;
            gap: 12px;
            flex-wrap: wrap;
        }

        .toolbar-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .toolbar-right {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .search-input {
            padding: 7px 12px;
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm);
            background: var(--bg-input);
            color: var(--text-primary);
            font-size: 0.85rem;
            min-width: 220px;
            font-family: inherit;
            transition: border-color 0.15s;
        }
        .search-input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-subtle);
        }

        .role-count {
            font-size: 0.82rem;
            color: var(--text-muted);
            white-space: nowrap;
        }

        /* ===== Table ===== */
        .table-wrap {
            background: var(--bg-surface);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            overflow-x: auto;
        }

        .role-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }

        .role-table thead th {
            padding: 10px 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.78rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.4px;
            border-bottom: 2px solid var(--border-default);
            white-space: nowrap;
            cursor: pointer;
            user-select: none;
            transition: color 0.15s;
        }
        .role-table thead th:hover { color: var(--text-primary); }

        .th-check, .th-num { width: 40px; text-align: center; }
        .th-actions { width: 80px; text-align: center; cursor: default !important; }

        .role-table tbody tr {
            border-bottom: 1px solid var(--border-subtle);
            transition: background 0.1s;
        }
        .role-table tbody tr:hover { background: var(--bg-hover); }
        .role-table tbody tr:nth-child(even) { background: var(--bg-secondary); }
        .role-table tbody tr:nth-child(even):hover { background: var(--bg-hover); }
        .role-table tbody tr.selected { background: var(--accent-subtle); }

        .role-table tbody td {
            padding: 9px 12px;
            color: var(--text-primary);
            vertical-align: middle;
        }

        .role-table td.td-check,
        .role-table td.td-num { text-align: center; }

        .sort-arrow {
            font-size: 0.7rem;
            margin-left: 3px;
        }

        /* Disposition styling */
        .disp-sanctioned {
            color: var(--success);
            font-weight: 500;
        }
        .disp-retired {
            color: var(--warning);
            text-decoration: line-through;
        }
        .disp-tbd {
            color: var(--text-muted);
            font-style: italic;
        }

        /* Deliverable badge */
        .badge-deliverable {
            display: inline-block;
            padding: 2px 7px;
            font-size: 0.72rem;
            font-weight: 600;
            border-radius: 20px;
            background: var(--success-bg);
            color: var(--success);
        }

        /* Table tags */
        .table-tag {
            display: inline-block;
            padding: 1px 6px;
            font-size: 0.72rem;
            border-radius: 10px;
            color: #fff;
            margin: 1px;
        }

        /* Row actions */
        .row-actions {
            display: flex;
            gap: 4px;
            justify-content: center;
        }
        .row-actions button {
            padding: 4px 6px;
            background: transparent;
            border: none;
            cursor: pointer;
            color: var(--text-muted);
            border-radius: 4px;
            transition: all 0.15s;
        }
        .row-actions button:hover { background: var(--bg-hover); color: var(--text-primary); }
        .row-actions button.btn-row-delete:hover { color: var(--danger); }

        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 48px 20px;
            color: var(--text-muted);
        }
        .empty-state p { margin-top: 12px; font-size: 0.95rem; }
        .empty-state .empty-hint { font-size: 0.84rem; margin-top: 6px; }

        /* ===== Bulk Bar ===== */
        .bulk-bar {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-elevated);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-md);
            padding: 10px 20px;
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 90;
            font-size: 0.85rem;
            color: var(--text-primary);
        }

        /* ===== Modal ===== */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 200;
            padding: 20px;
        }

        .modal-content {
            background: var(--bg-surface);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            width: 100%;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
        }

        .modal-large {
            max-width: 900px;
        }

        .modal-small {
            max-width: 400px;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-default);
        }
        .modal-header h3 {
            font-size: 1.05rem;
            font-weight: 600;
        }

        .modal-body {
            padding: 20px;
        }

        .modal-footer {
            padding: 14px 20px;
            border-top: 1px solid var(--border-default);
            display: flex;
            justify-content: flex-end;
            gap: 8px;
        }

        /* ===== Bulk Modal Specific ===== */
        .bulk-instructions {
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 12px;
        }

        .bulk-textarea {
            width: 100%;
            min-height: 280px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.84rem;
            resize: vertical;
        }

        .bulk-format-hint {
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 8px;
            font-style: italic;
        }

        .bulk-actions {
            display: flex;
            gap: 8px;
            margin-top: 14px;
        }

        .bulk-preview-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .bulk-preview-header h4 {
            font-size: 0.95rem;
            color: var(--text-primary);
        }

        .bulk-preview-table-wrap {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm);
            margin-bottom: 14px;
        }

        .bulk-preview-table {
            font-size: 0.82rem;
        }

        /* ===== Toast ===== */
        #toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 300;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .toast {
            padding: 10px 18px;
            background: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm);
            box-shadow: var(--shadow-md);
            font-size: 0.85rem;
            animation: toastIn 0.3s ease;
            max-width: 360px;
        }
        .toast.toast-success { border-left: 3px solid var(--success); }
        .toast.toast-error { border-left: 3px solid var(--danger); }
        .toast.toast-info { border-left: 3px solid var(--info); }

        @keyframes toastIn {
            from { opacity: 0; transform: translateX(30px); }
            to   { opacity: 1; transform: translateX(0); }
        }

        /* ===== Footer ===== */
        .footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 20px;
            margin-top: 16px;
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .footer-left {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .footer-brand { font-weight: 600; color: var(--accent); }
        .footer-sep { opacity: 0.5; }

        .footer-right {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        kbd {
            display: inline-block;
            padding: 2px 6px;
            font-size: 0.72rem;
            font-family: inherit;
            background: var(--bg-secondary);
            border: 1px solid var(--border-default);
            border-radius: 4px;
            color: var(--text-secondary);
        }

        /* ===== Responsive ===== */
        @media (max-width: 768px) {
            .stat-cards { grid-template-columns: repeat(2, 1fr); }
            .form-grid { grid-template-columns: 1fr; }
            .form-group-checks { flex-direction: column; align-items: flex-start; }
            .header { flex-direction: column; gap: 10px; text-align: center; }
            .header-right { justify-content: center; }
            .toolbar { flex-direction: column; }
            .toolbar-left, .toolbar-right { width: 100%; justify-content: center; }
            .search-input { min-width: unset; flex: 1; }
            .footer { flex-direction: column; gap: 8px; text-align: center; }
            .role-table { font-size: 0.78rem; }
        }

        @media (max-width: 480px) {
            .stat-cards { grid-template-columns: 1fr 1fr; }
            .toolbar-right { flex-wrap: wrap; }
        }

        /* ===== Print ===== */
        @media print {
            .form-section, .toolbar, .bulk-bar, .footer, .header-right,
            .row-actions, .th-check, .td-check, #toast-container { display: none !important; }
            .app { max-width: 100%; padding: 0; }
            .header { box-shadow: none; border-bottom: 2px solid #333; border-radius: 0; margin-bottom: 10px; }
            .stat-cards { box-shadow: none; }
            .stat-card { box-shadow: none; border: 1px solid #ccc; }
            .table-wrap { box-shadow: none; }
            .role-table tbody tr:nth-child(even) { background: #f5f5f5 !important; }
            body { background: #fff; color: #000; }
        }
    '''


def _get_js() -> str:
    """Return all JavaScript for the standalone HTML."""
    return '''
    // ===== State =====
    const CATEGORIES = JSON.parse(document.getElementById('template-categories').textContent || '[]');
    const METADATA = JSON.parse(document.getElementById('template-metadata').textContent || '{}');

    const STATE = {
        roles: [],
        nextId: 1,
        editingId: null,
        search: '',
        sortField: 'index',
        sortAsc: true,
        selectedIds: new Set(),
        formTags: [],
        isDark: false,
    };

    let confirmCallback = null;
    let parsedBulkRoles = [];

    // ===== Init =====
    document.addEventListener('DOMContentLoaded', function() {
        // Restore theme from localStorage
        const savedTheme = localStorage.getItem('aegis-template-theme');
        if (savedTheme === 'dark') {
            STATE.isDark = true;
            document.documentElement.setAttribute('data-theme', 'dark');
        }
        updateThemeIcon();
        updateStats();
        renderTable();

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl+E to export
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                exportJSON();
            }
            // Escape to close modals
            if (e.key === 'Escape') {
                closeBulkModal();
                cancelConfirm();
            }
        });

        // Enter in role name input adds role
        document.getElementById('inp-role-name').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addOrUpdateRole();
            }
        });
    });

    // ===== Theme =====
    function toggleTheme() {
        STATE.isDark = !STATE.isDark;
        if (STATE.isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('aegis-template-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('aegis-template-theme', 'light');
        }
        updateThemeIcon();
    }

    function updateThemeIcon() {
        const sun = document.getElementById('icon-sun');
        const moon = document.getElementById('icon-moon');
        if (sun) sun.style.display = STATE.isDark ? 'none' : 'block';
        if (moon) moon.style.display = STATE.isDark ? 'block' : 'none';
    }

    // ===== Stats =====
    function updateStats() {
        document.getElementById('stat-total').textContent = STATE.roles.length;
        document.getElementById('stat-deliverables').textContent =
            STATE.roles.filter(function(r) { return r.is_deliverable; }).length;
        document.getElementById('stat-with-tags').textContent =
            STATE.roles.filter(function(r) { return r.function_tags && r.function_tags.length > 0; }).length;
        document.getElementById('stat-with-desc').textContent =
            STATE.roles.filter(function(r) { return r.description && r.description.trim() !== ''; }).length;
    }

    // ===== Form =====
    function toggleFormSection() {
        var el = document.getElementById('form-section');
        el.classList.toggle('collapsed');
    }

    function getFormData() {
        return {
            role_name: document.getElementById('inp-role-name').value.trim(),
            category: document.getElementById('inp-category').value,
            description: document.getElementById('inp-description').value.trim(),
            aliases: document.getElementById('inp-aliases').value.trim(),
            role_type: document.getElementById('inp-role-type').value,
            role_disposition: document.getElementById('inp-disposition').value,
            org_group: document.getElementById('inp-org-group').value.trim(),
            is_deliverable: document.getElementById('inp-deliverable').checked,
            baselined: document.getElementById('inp-baselined').checked,
            function_tags: STATE.formTags.slice(),
        };
    }

    function setFormData(role) {
        document.getElementById('inp-role-name').value = role.role_name || '';
        document.getElementById('inp-category').value = role.category || 'Role';
        document.getElementById('inp-description').value = role.description || '';
        document.getElementById('inp-aliases').value =
            Array.isArray(role.aliases) ? role.aliases.join(', ') : (role.aliases || '');
        document.getElementById('inp-role-type').value = role.role_type || '';
        document.getElementById('inp-disposition').value = role.role_disposition || '';
        document.getElementById('inp-org-group').value = role.org_group || '';
        document.getElementById('inp-deliverable').checked = !!role.is_deliverable;
        document.getElementById('inp-baselined').checked = !!role.baselined;
        STATE.formTags = Array.isArray(role.function_tags) ? role.function_tags.slice() : [];
        renderFormTags();
    }

    function clearForm() {
        document.getElementById('inp-role-name').value = '';
        document.getElementById('inp-category').value = 'Role';
        document.getElementById('inp-description').value = '';
        document.getElementById('inp-aliases').value = '';
        document.getElementById('inp-role-type').value = '';
        document.getElementById('inp-disposition').value = '';
        document.getElementById('inp-org-group').value = '';
        document.getElementById('inp-deliverable').checked = false;
        document.getElementById('inp-baselined').checked = false;
        STATE.formTags = [];
        STATE.editingId = null;
        renderFormTags();
        document.getElementById('btn-add-role').textContent = 'Add Role';
        document.getElementById('inp-role-name').classList.remove('error');
    }

    function addOrUpdateRole() {
        var data = getFormData();
        var nameInput = document.getElementById('inp-role-name');

        if (!data.role_name) {
            nameInput.classList.add('error');
            nameInput.focus();
            showToast('Role name is required', 'error');
            return;
        }
        nameInput.classList.remove('error');

        if (STATE.editingId !== null) {
            // Update existing
            var idx = STATE.roles.findIndex(function(r) { return r._id === STATE.editingId; });
            if (idx !== -1) {
                data._id = STATE.editingId;
                STATE.roles[idx] = data;
                showToast('Role updated: ' + data.role_name, 'success');
            }
            STATE.editingId = null;
            document.getElementById('btn-add-role').textContent = 'Add Role';
        } else {
            // Add new
            data._id = STATE.nextId++;
            STATE.roles.push(data);
            showToast('Role added: ' + data.role_name, 'success');
        }

        clearForm();
        updateStats();
        renderTable();
    }

    function editRole(id) {
        var role = STATE.roles.find(function(r) { return r._id === id; });
        if (!role) return;
        STATE.editingId = id;
        setFormData(role);
        document.getElementById('btn-add-role').textContent = 'Update Role';

        // Expand form if collapsed
        var section = document.getElementById('form-section');
        section.classList.remove('collapsed');

        // Scroll to form
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        document.getElementById('inp-role-name').focus();
    }

    function deleteRole(id) {
        var role = STATE.roles.find(function(r) { return r._id === id; });
        if (!role) return;
        showConfirm('Delete Role', 'Are you sure you want to delete "' + escHtml(role.role_name) + '"?', function() {
            STATE.roles = STATE.roles.filter(function(r) { return r._id !== id; });
            STATE.selectedIds.delete(id);
            if (STATE.editingId === id) {
                clearForm();
            }
            updateStats();
            renderTable();
            updateBulkBar();
            showToast('Deleted: ' + role.role_name, 'info');
        });
    }

    // ===== Function Tags =====
    function renderFormTags() {
        var container = document.getElementById('tag-pills');
        container.innerHTML = '';
        STATE.formTags.forEach(function(tag, i) {
            var cat = CATEGORIES.find(function(c) { return c.code === tag; });
            var color = cat ? (cat.color || '#888') : '#888';
            var label = cat ? (tag + ' ' + cat.name) : tag;
            var pill = document.createElement('span');
            pill.className = 'tag-pill';
            pill.style.background = color;
            pill.innerHTML = escHtml(label) + '<span class="tag-remove" onclick="removeFormTag(' + i + ')">&times;</span>';
            container.appendChild(pill);
        });
    }

    function removeFormTag(index) {
        STATE.formTags.splice(index, 1);
        renderFormTags();
    }

    function handleTagSearch(value) {
        var dropdown = document.getElementById('tag-dropdown');
        if (!value.trim()) {
            dropdown.style.display = 'none';
            return;
        }
        var term = value.toLowerCase();
        var matches = CATEGORIES.filter(function(c) {
            return (c.code && c.code.toLowerCase().indexOf(term) !== -1) ||
                   (c.name && c.name.toLowerCase().indexOf(term) !== -1);
        }).filter(function(c) {
            return STATE.formTags.indexOf(c.code) === -1;
        }).slice(0, 10);

        if (matches.length === 0 && CATEGORIES.length > 0) {
            dropdown.style.display = 'none';
            return;
        }

        dropdown.innerHTML = '';
        matches.forEach(function(c) {
            var opt = document.createElement('div');
            opt.className = 'tag-option';
            opt.innerHTML = '<span class="tag-option-color" style="background:' + (c.color || '#888') + '"></span>' +
                '<span class="tag-option-code">' + escHtml(c.code) + '</span>' +
                '<span class="tag-option-name">' + escHtml(c.name) + '</span>';
            opt.addEventListener('click', function() {
                addFormTag(c.code);
                document.getElementById('inp-tag-search').value = '';
                dropdown.style.display = 'none';
            });
            dropdown.appendChild(opt);
        });
        dropdown.style.display = matches.length > 0 ? 'block' : 'none';
    }

    function handleTagKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            var val = e.target.value.trim();
            if (val) {
                // Check if it matches a category code
                var cat = CATEGORIES.find(function(c) { return c.code && c.code.toLowerCase() === val.toLowerCase(); });
                addFormTag(cat ? cat.code : val);
                e.target.value = '';
                document.getElementById('tag-dropdown').style.display = 'none';
            }
        }
    }

    function addFormTag(code) {
        if (STATE.formTags.indexOf(code) === -1) {
            STATE.formTags.push(code);
            renderFormTags();
        }
    }

    // ===== Table =====
    function renderTable() {
        var tbody = document.getElementById('role-tbody');
        var emptyState = document.getElementById('empty-state');
        var filtered = getFilteredRoles();

        if (STATE.roles.length === 0) {
            emptyState.style.display = 'block';
            tbody.innerHTML = '';
            document.getElementById('role-count').textContent = '0 roles';
            return;
        }

        emptyState.style.display = filtered.length === 0 && STATE.search ? 'block' : 'none';
        if (filtered.length === 0 && STATE.search) {
            emptyState.querySelector('p').textContent = 'No roles match "' + STATE.search + '"';
        } else if (STATE.roles.length === 0) {
            emptyState.querySelector('p').textContent = 'No roles added yet.';
        }

        // Sort
        var sorted = filtered.slice();
        var field = STATE.sortField;
        var asc = STATE.sortAsc;
        sorted.sort(function(a, b) {
            var va, vb;
            if (field === 'index') {
                va = STATE.roles.indexOf(a);
                vb = STATE.roles.indexOf(b);
            } else {
                va = (a[field] || '').toString().toLowerCase();
                vb = (b[field] || '').toString().toLowerCase();
            }
            if (va < vb) return asc ? -1 : 1;
            if (va > vb) return asc ? 1 : -1;
            return 0;
        });

        tbody.innerHTML = '';
        sorted.forEach(function(role, idx) {
            var tr = document.createElement('tr');
            if (STATE.selectedIds.has(role._id)) tr.classList.add('selected');
            tr.setAttribute('data-id', role._id);

            // Checkbox
            var tdCheck = document.createElement('td');
            tdCheck.className = 'td-check';
            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.checked = STATE.selectedIds.has(role._id);
            cb.addEventListener('change', function() { toggleSelect(role._id, this.checked); });
            tdCheck.appendChild(cb);
            tr.appendChild(tdCheck);

            // Index
            var tdNum = document.createElement('td');
            tdNum.className = 'td-num';
            tdNum.textContent = idx + 1;
            tr.appendChild(tdNum);

            // Role Name
            var tdName = document.createElement('td');
            tdName.innerHTML = '<strong>' + escHtml(role.role_name) + '</strong>';
            if (role.aliases) {
                var aliasStr = Array.isArray(role.aliases) ? role.aliases.join(', ') : role.aliases;
                if (aliasStr) {
                    tdName.innerHTML += '<br><span style="font-size:0.76rem;color:var(--text-muted)">aka: ' +
                        escHtml(aliasStr) + '</span>';
                }
            }
            tr.appendChild(tdName);

            // Category
            var tdCat = document.createElement('td');
            tdCat.textContent = role.category || 'Role';
            tr.appendChild(tdCat);

            // Org Group
            var tdOrg = document.createElement('td');
            tdOrg.textContent = role.org_group || '';
            tr.appendChild(tdOrg);

            // Type
            var tdType = document.createElement('td');
            tdType.textContent = role.role_type || '';
            tdType.style.fontSize = '0.82rem';
            tr.appendChild(tdType);

            // Disposition
            var tdDisp = document.createElement('td');
            var disp = role.role_disposition || '';
            tdDisp.textContent = disp;
            if (disp === 'Sanctioned') tdDisp.className = 'disp-sanctioned';
            else if (disp === 'To Be Retired') tdDisp.className = 'disp-retired';
            else if (disp === 'TBD') tdDisp.className = 'disp-tbd';
            tr.appendChild(tdDisp);

            // Deliverable
            var tdDel = document.createElement('td');
            if (role.is_deliverable) {
                tdDel.innerHTML = '<span class="badge-deliverable">Yes</span>';
            }
            tr.appendChild(tdDel);

            // Tags
            var tdTags = document.createElement('td');
            if (role.function_tags && role.function_tags.length > 0) {
                role.function_tags.forEach(function(tag) {
                    var cat = CATEGORIES.find(function(c) { return c.code === tag; });
                    var color = cat ? (cat.color || '#888') : '#888';
                    tdTags.innerHTML += '<span class="table-tag" style="background:' + color + '">' +
                        escHtml(tag) + '</span>';
                });
            }
            tr.appendChild(tdTags);

            // Actions
            var tdAct = document.createElement('td');
            tdAct.className = 'th-actions';
            tdAct.innerHTML = '<div class="row-actions">' +
                '<button title="Edit" onclick="editRole(' + role._id + ')">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>' +
                '<path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>' +
                '<button class="btn-row-delete" title="Delete" onclick="deleteRole(' + role._id + ')">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
                '<polyline points="3 6 5 6 21 6"/>' +
                '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>' +
                '</div>';
            tr.appendChild(tdAct);

            tbody.appendChild(tr);
        });

        // Update count
        var countText = STATE.roles.length + ' role' + (STATE.roles.length !== 1 ? 's' : '');
        if (STATE.search && filtered.length !== STATE.roles.length) {
            countText = filtered.length + ' of ' + STATE.roles.length + ' roles';
        }
        document.getElementById('role-count').textContent = countText;

        // Update sort arrows
        document.querySelectorAll('.sort-arrow').forEach(function(el) { el.textContent = ''; });
        var arrow = document.getElementById('sort-' + STATE.sortField);
        if (arrow) arrow.textContent = STATE.sortAsc ? '\\u25B2' : '\\u25BC';

        // Update select-all checkbox
        var selectAll = document.getElementById('select-all');
        if (selectAll) {
            selectAll.checked = filtered.length > 0 && filtered.every(function(r) { return STATE.selectedIds.has(r._id); });
        }
    }

    function getFilteredRoles() {
        if (!STATE.search) return STATE.roles;
        var term = STATE.search.toLowerCase();
        return STATE.roles.filter(function(r) {
            return (r.role_name && r.role_name.toLowerCase().indexOf(term) !== -1) ||
                   (r.category && r.category.toLowerCase().indexOf(term) !== -1) ||
                   (r.org_group && r.org_group.toLowerCase().indexOf(term) !== -1) ||
                   (r.description && r.description.toLowerCase().indexOf(term) !== -1);
        });
    }

    function handleSearch(value) {
        STATE.search = value.trim();
        renderTable();
    }

    function sortTable(field) {
        if (STATE.sortField === field) {
            STATE.sortAsc = !STATE.sortAsc;
        } else {
            STATE.sortField = field;
            STATE.sortAsc = true;
        }
        renderTable();
    }

    // ===== Selection =====
    function toggleSelect(id, checked) {
        if (checked) {
            STATE.selectedIds.add(id);
        } else {
            STATE.selectedIds.delete(id);
        }
        renderTable();
        updateBulkBar();
    }

    function toggleSelectAll(checked) {
        var filtered = getFilteredRoles();
        filtered.forEach(function(r) {
            if (checked) STATE.selectedIds.add(r._id);
            else STATE.selectedIds.delete(r._id);
        });
        renderTable();
        updateBulkBar();
    }

    function clearSelection() {
        STATE.selectedIds.clear();
        renderTable();
        updateBulkBar();
    }

    function updateBulkBar() {
        var bar = document.getElementById('bulk-bar');
        if (STATE.selectedIds.size > 0) {
            bar.style.display = 'flex';
            document.getElementById('bulk-count').textContent = STATE.selectedIds.size + ' selected';
        } else {
            bar.style.display = 'none';
        }
    }

    function bulkDeleteSelected() {
        var count = STATE.selectedIds.size;
        showConfirm('Delete ' + count + ' Role(s)', 'Are you sure you want to delete ' + count + ' selected role(s)?', function() {
            STATE.roles = STATE.roles.filter(function(r) { return !STATE.selectedIds.has(r._id); });
            if (STATE.editingId !== null && STATE.selectedIds.has(STATE.editingId)) {
                clearForm();
            }
            STATE.selectedIds.clear();
            updateStats();
            renderTable();
            updateBulkBar();
            showToast('Deleted ' + count + ' role(s)', 'info');
        });
    }

    // ===== Bulk Paste Modal =====
    function openBulkModal() {
        document.getElementById('bulk-modal').style.display = 'flex';
        document.getElementById('bulk-input-section').style.display = 'block';
        document.getElementById('bulk-preview-section').style.display = 'none';
        document.getElementById('bulk-textarea').value = '';
        document.getElementById('bulk-format-hint').textContent = 'Auto-detecting format...';
        parsedBulkRoles = [];
        document.getElementById('bulk-textarea').focus();
    }

    function closeBulkModal(e) {
        if (e && e.target !== e.currentTarget) return;
        document.getElementById('bulk-modal').style.display = 'none';
    }

    function backToBulkInput() {
        document.getElementById('bulk-input-section').style.display = 'block';
        document.getElementById('bulk-preview-section').style.display = 'none';
    }

    function parseBulkInput() {
        var text = document.getElementById('bulk-textarea').value;
        var lines = text.trim().split('\\n');
        if (lines.length === 0 || (lines.length === 1 && !lines[0].trim())) {
            showToast('No data to parse', 'error');
            return;
        }

        var firstLine = lines[0];
        var delimiter = '\\n'; // default: one per line
        if (firstLine.indexOf('\\t') !== -1) delimiter = '\\t'; // Excel/TSV
        else if (firstLine.split(',').length > 2) delimiter = ','; // CSV
        else if (firstLine.indexOf(';') !== -1) delimiter = ';'; // Semicolons

        // Update format hint
        var fmtNames = { '\\n': 'one role per line', '\\t': 'tab-separated (TSV/Excel)', ',': 'comma-separated (CSV)', ';': 'semicolon-separated' };
        document.getElementById('bulk-format-hint').textContent = 'Detected: ' + (fmtNames[delimiter] || delimiter);

        // Check if first line is a header row
        var headerKeywords = ['role', 'name', 'category', 'description', 'type', 'disposition', 'org'];
        var isHeader = headerKeywords.some(function(kw) { return firstLine.toLowerCase().indexOf(kw) !== -1; });

        var startRow = isHeader ? 1 : 0;
        var results = [];

        if (delimiter === '\\n') {
            // One role per line
            for (var i = startRow; i < lines.length; i++) {
                var name = lines[i].trim();
                if (name) results.push({ role_name: name });
            }
        } else {
            // Delimited data
            var headers = isHeader ? lines[0].split(delimiter).map(function(h) { return h.trim().toLowerCase(); }) : [];
            var fieldMap = {};
            if (isHeader) {
                headers.forEach(function(h, i) {
                    if (h.indexOf('role') !== -1 || h.indexOf('name') !== -1) fieldMap[i] = 'role_name';
                    else if (h.indexOf('categ') !== -1) fieldMap[i] = 'category';
                    else if (h.indexOf('desc') !== -1) fieldMap[i] = 'description';
                    else if (h.indexOf('alias') !== -1) fieldMap[i] = 'aliases';
                    else if (h.indexOf('type') !== -1) fieldMap[i] = 'role_type';
                    else if (h.indexOf('dispo') !== -1) fieldMap[i] = 'role_disposition';
                    else if (h.indexOf('org') !== -1) fieldMap[i] = 'org_group';
                    else if (h.indexOf('deliv') !== -1) fieldMap[i] = 'is_deliverable';
                    else if (h.indexOf('base') !== -1) fieldMap[i] = 'baselined';
                    else if (h.indexOf('tag') !== -1) fieldMap[i] = 'function_tags';
                });
            }

            for (var j = startRow; j < lines.length; j++) {
                var cols = lines[j].split(delimiter).map(function(c) { return c.trim(); });
                if (!cols[0]) continue;

                var role = {};
                if (isHeader && Object.keys(fieldMap).length > 0) {
                    for (var idx in fieldMap) {
                        if (cols[idx]) {
                            var fieldName = fieldMap[idx];
                            if (fieldName === 'is_deliverable' || fieldName === 'baselined') {
                                role[fieldName] = cols[idx].toLowerCase() === 'yes' ||
                                    cols[idx].toLowerCase() === 'true' || cols[idx] === '1';
                            } else if (fieldName === 'function_tags') {
                                role[fieldName] = cols[idx].split(/[,;|]/).map(function(t) { return t.trim(); }).filter(Boolean);
                            } else {
                                role[fieldName] = cols[idx];
                            }
                        }
                    }
                } else {
                    // No header: assume first col = name, second = category, third = description
                    role.role_name = cols[0] || '';
                    if (cols[1]) role.category = cols[1];
                    if (cols[2]) role.description = cols[2];
                }

                if (role.role_name) results.push(role);
            }
        }

        if (results.length === 0) {
            showToast('No valid roles found', 'error');
            return;
        }

        parsedBulkRoles = results;
        showBulkPreview(results, isHeader ? lines[0].split(delimiter).map(function(h) { return h.trim(); }) : null);
    }

    function showBulkPreview(roles, headerRow) {
        document.getElementById('bulk-input-section').style.display = 'none';
        document.getElementById('bulk-preview-section').style.display = 'block';
        document.getElementById('bulk-preview-count').textContent = roles.length;
        document.getElementById('btn-import-bulk').textContent = 'Import ' + roles.length + ' Role' + (roles.length !== 1 ? 's' : '');

        var fields = ['role_name', 'category', 'description', 'org_group', 'role_type', 'role_disposition'];
        var fieldLabels = { role_name: 'Role Name', category: 'Category', description: 'Description',
            org_group: 'Org Group', role_type: 'Type', role_disposition: 'Disposition' };

        // Detect which fields are present
        var activeFields = fields.filter(function(f) {
            return roles.some(function(r) { return r[f] && r[f].toString().trim() !== ''; });
        });

        // Ensure at least role_name
        if (activeFields.indexOf('role_name') === -1) activeFields.unshift('role_name');

        var thead = document.getElementById('bulk-preview-thead');
        thead.innerHTML = '<tr><th>#</th>' + activeFields.map(function(f) {
            return '<th>' + (fieldLabels[f] || f) + '</th>';
        }).join('') + '</tr>';

        var tbody = document.getElementById('bulk-preview-tbody');
        tbody.innerHTML = '';
        roles.forEach(function(role, idx) {
            var tr = document.createElement('tr');
            tr.innerHTML = '<td>' + (idx + 1) + '</td>' + activeFields.map(function(f) {
                return '<td>' + escHtml(role[f] || '') + '</td>';
            }).join('');
            tbody.appendChild(tr);
        });
    }

    function importBulkRoles() {
        var count = parsedBulkRoles.length;
        parsedBulkRoles.forEach(function(role) {
            role._id = STATE.nextId++;
            if (!role.category) role.category = 'Role';
            if (!role.is_deliverable) role.is_deliverable = false;
            if (!role.baselined) role.baselined = false;
            if (!role.function_tags) role.function_tags = [];
            STATE.roles.push(role);
        });
        parsedBulkRoles = [];
        closeBulkModal();
        updateStats();
        renderTable();
        showToast('Imported ' + count + ' role(s)', 'success');
    }

    // ===== Clear All =====
    function clearAllRoles() {
        if (STATE.roles.length === 0) {
            showToast('No roles to clear', 'info');
            return;
        }
        showConfirm('Clear All Roles',
            'This will remove all ' + STATE.roles.length + ' role(s). This cannot be undone. Continue?',
            function() {
                STATE.roles = [];
                STATE.selectedIds.clear();
                STATE.editingId = null;
                STATE.nextId = 1;
                clearForm();
                updateStats();
                renderTable();
                updateBulkBar();
                showToast('All roles cleared', 'info');
            });
    }

    // ===== Export =====
    function exportJSON() {
        if (STATE.roles.length === 0) {
            showToast('No roles to export. Add some roles first.', 'error');
            return;
        }

        var data = {
            aegis_version: METADATA.aegis_version || '4.1.0',
            export_type: 'role_dictionary_import',
            template_generated: true,
            exported_at: new Date().toISOString(),
            roles: STATE.roles.map(function(r) {
                return {
                    role_name: r.role_name,
                    category: r.category || 'Role',
                    description: r.description || '',
                    aliases: r.aliases ? (Array.isArray(r.aliases)
                        ? r.aliases
                        : r.aliases.split(',').map(function(a) { return a.trim(); }).filter(Boolean))
                        : [],
                    is_deliverable: !!r.is_deliverable,
                    function_tags: r.function_tags || [],
                    role_type: r.role_type || '',
                    role_disposition: r.role_disposition || '',
                    org_group: r.org_group || '',
                    baselined: !!r.baselined,
                };
            }),
            summary: {
                total: STATE.roles.length,
                deliverables: STATE.roles.filter(function(r) { return r.is_deliverable; }).length,
                with_tags: STATE.roles.filter(function(r) { return r.function_tags && r.function_tags.length > 0; }).length,
            }
        };

        var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'AEGIS_Role_Import_' + new Date().toISOString().slice(0, 10) + '.json';
        a.click();
        URL.revokeObjectURL(url);
        showToast('Exported ' + STATE.roles.length + ' role(s) to JSON', 'success');
    }

    // ===== Confirm Dialog =====
    function showConfirm(title, message, callback) {
        document.getElementById('confirm-title').textContent = title;
        document.getElementById('confirm-message').textContent = message;
        confirmCallback = callback;
        document.getElementById('confirm-modal').style.display = 'flex';
    }

    function doConfirm() {
        document.getElementById('confirm-modal').style.display = 'none';
        if (confirmCallback) {
            confirmCallback();
            confirmCallback = null;
        }
    }

    function cancelConfirm(e) {
        if (e && e.target !== e.currentTarget) return;
        document.getElementById('confirm-modal').style.display = 'none';
        confirmCallback = null;
    }

    // ===== Toast =====
    function showToast(message, type) {
        var container = document.getElementById('toast-container');
        var toast = document.createElement('div');
        toast.className = 'toast toast-' + (type || 'info');
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(function() {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(function() { toast.remove(); }, 300);
        }, 3000);
    }

    // ===== Utilities =====
    function escHtml(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    '''


if __name__ == '__main__':
    # Generate a sample template file for testing
    sample_categories = [
        {'code': 'ENG', 'name': 'Engineering', 'color': '#3b82f6', 'description': 'Engineering functions'},
        {'code': 'MGT', 'name': 'Management', 'color': '#8b5cf6', 'description': 'Management functions'},
        {'code': 'QA', 'name': 'Quality Assurance', 'color': '#10b981', 'description': 'Quality functions'},
        {'code': 'OPS', 'name': 'Operations', 'color': '#f59e0b', 'description': 'Operations functions'},
        {'code': 'LOG', 'name': 'Logistics', 'color': '#ef4444', 'description': 'Logistics functions'},
        {'code': 'CM', 'name': 'Configuration Management', 'color': '#06b6d4', 'description': 'CM functions'},
    ]

    sample_metadata = {
        'aegis_version': '4.1.0',
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'exported_by': 'test-user',
    }

    html = generate_role_template_html(
        function_categories=sample_categories,
        metadata=sample_metadata,
    )

    output_path = 'AEGIS_Role_Import_Template.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Generated {output_path} ({len(html):,} chars, {html.count(chr(10)):,} lines)')
