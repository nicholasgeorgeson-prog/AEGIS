"""
AEGIS - Advanced HTML Report Generator
v2.0.0 - Rich, interactive HTML reports with cross-functional analysis

Features:
- Cross-functional role reference detection and visualization
- Interactive charts and graphs (Chart.js)
- Heatmaps for role frequency
- Executive summary with key metrics
- Role selection / filtering
- Drill-down capability
- Print-optimized layouts
- Dark mode support
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from html import escape


def _abbreviate_code(code: str, max_len: int = 4) -> str:
    """
    Abbreviate a function code for badge display.
    - Short codes (<=max_len): return as-is
    - Hyphenated codes: use initials from each part (FS-AERO -> FSA)
    - Long codes: truncate
    """
    if not code:
        return '?'
    if len(code) <= max_len:
        return code

    # Handle hyphenated codes like FS-AERO, FS-AD
    if '-' in code:
        parts = code.split('-')
        # Take first part fully if short, plus first letter of remaining parts
        if len(parts[0]) <= 2:
            abbrev = parts[0] + ''.join(p[0] for p in parts[1:] if p)
            return abbrev[:max_len]
        else:
            # Just use initials
            return ''.join(p[0] for p in parts if p)[:max_len]

    # No hyphen, just truncate
    return code[:max_len]


def generate_comprehensive_roles_report(
    functions: List[Dict],
    cross_references: List[Dict],
    role_stats: Dict,
    document_stats: Dict,
    report_title: str = "Roles by Function Report"
) -> str:
    """
    Generate a comprehensive, data-rich HTML report for roles by function.

    Args:
        functions: List of function data with roles
        cross_references: List of cross-functional role references
        role_stats: Aggregate statistics about roles
        document_stats: Aggregate statistics about documents
        report_title: Title for the report

    Returns:
        Complete HTML document as string
    """

    # Calculate summary statistics
    total_functions = len(functions)
    total_role_assignments = sum(len(f.get('roles', [])) for f in functions)
    total_documents = document_stats.get('total_documents', 0)
    total_cross_refs = len(cross_references)

    # Deduplicate roles across functions for a unique count
    unique_role_names = set()
    for func in functions:
        for role in func.get('roles', []):
            unique_role_names.add(role.get('name', ''))
    total_unique_roles = len(unique_role_names)

    # Group cross-references by source function
    cross_ref_by_source = {}
    cross_ref_by_target = {}
    for ref in cross_references:
        source = ref.get('source_function', 'Unknown')
        target = ref.get('target_function', 'Unknown')
        if source not in cross_ref_by_source:
            cross_ref_by_source[source] = []
        cross_ref_by_source[source].append(ref)
        if target not in cross_ref_by_target:
            cross_ref_by_target[target] = []
        cross_ref_by_target[target].append(ref)

    # Prepare chart data
    function_role_counts = [
        {'name': f.get('name', f.get('code', 'Unknown')), 'code': f.get('code', ''), 'count': len(f.get('roles', [])), 'color': f.get('color', '#3b82f6')}
        for f in functions if f.get('roles')
    ]
    function_role_counts.sort(key=lambda x: x['count'], reverse=True)

    # Build cross-reference matrix data
    cross_ref_matrix = []
    for ref in cross_references:
        cross_ref_matrix.append({
            'source': ref.get('source_function'),
            'target': ref.get('target_function'),
            'role': ref.get('role_name'),
            'document': ref.get('document_name')
        })

    # Build the complete deduplicated role list for the filter and details table
    role_map = {}
    for func in functions:
        for role in func.get('roles', []):
            rname = role.get('name', '')
            if rname not in role_map:
                role_cross_refs = [r for r in cross_references if r.get('role_name') == rname]
                role_map[rname] = {
                    'name': rname,
                    'functions': [],
                    'doc_count': len(role.get('documents', [])),
                    'action_count': len(role.get('required_actions', [])),
                    'cross_refs': len(role_cross_refs)
                }
            else:
                role_map[rname]['doc_count'] += len(role.get('documents', []))
                role_map[rname]['action_count'] += len(role.get('required_actions', []))
            role_map[rname]['functions'].append({
                'name': func.get('name'),
                'code': func.get('code'),
                'color': func.get('color', '#3b82f6')
            })

    all_roles_sorted = sorted(role_map.values(), key=lambda x: x['name'])
    # JSON-safe list for the filter dropdown
    all_role_names_json = json.dumps(sorted(unique_role_names))

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS - {escape(report_title)}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary: #3b82f6;
            --primary-dark: #1d4ed8;
            --secondary: #6366f1;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --border: #e2e8f0;
            --shadow: rgba(0, 0, 0, 0.1);
            --gradient-primary: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            --gradient-success: linear-gradient(135deg, #059669 0%, #10b981 100%);
            --gradient-warning: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
            --gradient-danger: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --text-primary: #f1f5f9;
                --text-secondary: #94a3b8;
                --text-muted: #64748b;
                --bg-primary: #0f172a;
                --bg-secondary: #1e293b;
                --bg-tertiary: #334155;
                --border: #475569;
                --shadow: rgba(0, 0, 0, 0.3);
            }}
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.6;
            font-size: 14px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }}

        /* Header */
        .report-header {{
            background: var(--gradient-primary);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }}

        .report-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }}

        .report-header::after {{
            content: '';
            position: absolute;
            bottom: -30%;
            left: 10%;
            width: 200px;
            height: 200px;
            background: rgba(255,255,255,0.05);
            border-radius: 50%;
        }}

        .header-content {{
            position: relative;
            z-index: 1;
        }}

        .report-title {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .report-subtitle {{
            font-size: 16px;
            opacity: 0.9;
            max-width: 600px;
        }}

        .report-meta {{
            display: flex;
            gap: 24px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            opacity: 0.85;
        }}

        /* Role Filter Bar */
        .filter-bar {{
            background: var(--bg-primary);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px var(--shadow);
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}

        .filter-bar label {{
            font-weight: 600;
            font-size: 13px;
            color: var(--text-secondary);
            white-space: nowrap;
        }}

        .filter-search {{
            flex: 1;
            min-width: 200px;
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 13px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            outline: none;
        }}

        .filter-search:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
        }}

        .filter-tags {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            max-height: 120px;
            overflow-y: auto;
        }}

        .filter-tag {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            background: var(--primary);
            color: white;
            border-radius: 16px;
            font-size: 11px;
            cursor: pointer;
            white-space: nowrap;
        }}

        .filter-tag:hover {{
            background: var(--primary-dark);
        }}

        .filter-tag .remove {{
            font-size: 14px;
            line-height: 1;
            opacity: 0.8;
        }}

        .filter-dropdown {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 8px 24px var(--shadow);
            max-height: 250px;
            overflow-y: auto;
            z-index: 100;
            display: none;
        }}

        .filter-dropdown.visible {{
            display: block;
        }}

        .filter-option {{
            padding: 8px 12px;
            cursor: pointer;
            font-size: 13px;
            color: var(--text-primary);
            border-bottom: 1px solid var(--border);
        }}

        .filter-option:hover {{
            background: var(--bg-tertiary);
        }}

        .filter-option:last-child {{
            border-bottom: none;
        }}

        .filter-option.selected {{
            background: rgba(59, 130, 246, 0.1);
            color: var(--primary);
            font-weight: 600;
        }}

        .filter-count {{
            font-size: 12px;
            color: var(--text-muted);
            margin-left: 8px;
        }}

        .filter-actions {{
            display: flex;
            gap: 8px;
        }}

        .filter-btn {{
            padding: 6px 14px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            font-size: 12px;
            cursor: pointer;
            white-space: nowrap;
        }}

        .filter-btn:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}

        .filter-btn.primary {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}

        .filter-btn.primary:hover {{
            background: var(--primary-dark);
        }}

        /* Navigation Tabs */
        .tab-nav {{
            display: flex;
            gap: 4px;
            background: var(--bg-primary);
            padding: 8px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px var(--shadow);
            overflow-x: auto;
        }}

        .tab-btn {{
            padding: 12px 20px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .tab-btn:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}

        .tab-btn.active {{
            background: var(--primary);
            color: white;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* Stats Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .stat-card {{
            background: var(--bg-primary);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary);
        }}

        .stat-card.success::before {{ background: var(--success); }}
        .stat-card.warning::before {{ background: var(--warning); }}
        .stat-card.danger::before {{ background: var(--danger); }}
        .stat-card.info::before {{ background: var(--info); }}
        .stat-card.secondary::before {{ background: var(--secondary); }}

        .stat-value {{
            font-size: 36px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
        }}

        .stat-label {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        .stat-change {{
            position: absolute;
            top: 16px;
            right: 16px;
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 12px;
            font-weight: 500;
        }}

        .stat-change.positive {{
            background: rgba(34, 197, 94, 0.1);
            color: var(--success);
        }}

        .stat-change.negative {{
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }}

        /* Charts Section */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }}

        .chart-card {{
            background: var(--bg-primary);
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
            padding: 24px;
        }}

        .chart-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .chart-container {{
            position: relative;
            height: 300px;
        }}

        /* Cross-Reference Section */
        .cross-ref-section {{
            background: var(--bg-primary);
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
            margin-bottom: 24px;
            overflow: hidden;
        }}

        .section-header {{
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .section-title {{
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-badge {{
            background: var(--warning);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .cross-ref-list {{
            padding: 16px 24px;
        }}

        .cross-ref-item {{
            display: grid;
            grid-template-columns: 1fr auto 1fr auto;
            gap: 16px;
            align-items: center;
            padding: 16px;
            background: var(--bg-secondary);
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 4px solid var(--warning);
        }}

        .cross-ref-function {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .func-badge {{
            min-width: 32px;
            height: 28px;
            padding: 4px 8px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 11px;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
            max-width: 80px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        }}

        .func-badge-sm {{
            min-width: 28px;
            height: 24px;
            padding: 3px 6px;
            border-radius: 5px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 10px;
            white-space: nowrap;
            max-width: 70px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        }}

        .func-badge-lg {{
            min-width: 40px;
            height: 36px;
            padding: 6px 12px;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 12px;
            white-space: nowrap;
            max-width: 100px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }}

        .func-info {{
            display: flex;
            flex-direction: column;
        }}

        .func-name {{
            font-weight: 600;
            color: var(--text-primary);
        }}

        .func-role {{
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .cross-ref-arrow {{
            font-size: 24px;
            color: var(--warning);
        }}

        .cross-ref-context {{
            font-size: 13px;
            color: var(--text-secondary);
            text-align: right;
        }}

        /* Function Cards */
        .function-card {{
            background: var(--bg-primary);
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
            margin-bottom: 20px;
            overflow: hidden;
        }}

        .function-header {{
            padding: 20px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s;
        }}

        .function-header:hover {{
            background: var(--bg-secondary);
        }}

        .function-badge {{
            min-width: 40px;
            height: 40px;
            padding: 6px 10px;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 11px;
            flex-shrink: 0;
            white-space: nowrap;
            max-width: 90px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            letter-spacing: -0.5px;
        }}

        .function-info {{
            flex: 1;
        }}

        .function-name {{
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .function-meta {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 2px;
        }}

        .function-stats {{
            display: flex;
            gap: 16px;
        }}

        .mini-stat {{
            text-align: center;
            padding: 8px 16px;
            background: var(--bg-tertiary);
            border-radius: 8px;
        }}

        .mini-stat-value {{
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .mini-stat-label {{
            font-size: 11px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .function-toggle {{
            font-size: 20px;
            color: var(--text-muted);
            transition: transform 0.2s;
        }}

        .function-card.expanded .function-toggle {{
            transform: rotate(180deg);
        }}

        .function-body {{
            display: none;
            padding: 24px;
            border-top: 1px solid var(--border);
        }}

        .function-card.expanded .function-body {{
            display: block;
        }}

        /* Role Items */
        .role-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 16px;
        }}

        .role-item {{
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 16px;
            border: 1px solid var(--border);
            transition: all 0.2s;
        }}

        .role-item:hover {{
            border-color: var(--primary);
            box-shadow: 0 4px 12px var(--shadow);
        }}

        .role-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}

        .role-name {{
            font-weight: 600;
            color: var(--text-primary);
            font-size: 15px;
        }}

        .role-count {{
            background: var(--primary);
            color: white;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}

        .role-docs {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }}

        .doc-tag {{
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            max-width: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .doc-tag.cross-ref {{
            background: rgba(245, 158, 11, 0.15);
            color: var(--warning);
            border: 1px dashed var(--warning);
        }}

        .role-actions {{
            border-top: 1px dashed var(--border);
            padding-top: 12px;
            margin-top: 8px;
        }}

        .action-item {{
            font-size: 13px;
            color: var(--text-secondary);
            padding: 6px 0;
            padding-left: 20px;
            position: relative;
            line-height: 1.4;
        }}

        .action-item::before {{
            content: '→';
            position: absolute;
            left: 0;
            color: var(--primary);
        }}

        /* Heatmap */
        .heatmap-grid {{
            display: grid;
            gap: 10px;
            padding: 8px;
        }}

        .heatmap-cell {{
            border-radius: 10px;
            padding: 16px 12px;
            text-align: center;
            cursor: default;
            transition: transform 0.15s;
        }}

        .heatmap-cell:hover {{
            transform: scale(1.04);
        }}

        .heatmap-value {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .heatmap-code {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.85;
        }}

        .heatmap-name {{
            font-size: 11px;
            margin-top: 2px;
            opacity: 0.7;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* Legend */
        .legend {{
            display: flex;
            gap: 16px;
            margin-top: 16px;
            flex-wrap: wrap;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
        }}

        /* Table */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        .data-table th,
        .data-table td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        .data-table th {{
            background: var(--bg-tertiary);
            font-weight: 600;
            color: var(--text-primary);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
        }}

        .data-table tr:hover td {{
            background: var(--bg-secondary);
        }}

        .data-table tr.hidden-role {{
            display: none;
        }}

        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 24px;
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 24px;
        }}

        .report-footer a {{
            color: var(--primary);
            text-decoration: none;
        }}

        /* Print Styles */
        @media print {{
            body {{
                background: white;
                font-size: 12px;
            }}

            .tab-nav, .function-toggle, .filter-bar {{
                display: none;
            }}

            .tab-content {{
                display: block !important;
            }}

            .function-body {{
                display: block !important;
            }}

            .container {{
                max-width: 100%;
                padding: 0;
            }}

            .report-header {{
                background: #1e40af !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}

            .function-card, .chart-card, .cross-ref-section {{
                break-inside: avoid;
                box-shadow: none;
                border: 1px solid #ddd;
            }}

            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .fade-in {{
            animation: fadeIn 0.3s ease-out forwards;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 16px;
            }}

            .report-header {{
                padding: 24px;
            }}

            .report-title {{
                font-size: 24px;
            }}

            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .charts-grid {{
                grid-template-columns: 1fr;
            }}

            .cross-ref-item {{
                grid-template-columns: 1fr;
                text-align: center;
            }}

            .cross-ref-arrow {{
                transform: rotate(90deg);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="report-header">
            <div class="header-content">
                <h1 class="report-title">
                    <span>📊</span> {escape(report_title)}
                </h1>
                <p class="report-subtitle">
                    Comprehensive analysis of organizational roles, functions, and cross-functional references
                </p>
                <div class="report-meta">
                    <div class="meta-item">
                        <span>📅</span>
                        <span>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</span>
                    </div>
                    <div class="meta-item">
                        <span>🏢</span>
                        <span>{total_functions} Functions</span>
                    </div>
                    <div class="meta-item">
                        <span>👤</span>
                        <span>{total_unique_roles} Unique Roles</span>
                    </div>
                    <div class="meta-item">
                        <span>📄</span>
                        <span>{total_documents} Documents</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Role Filter Bar -->
        <div class="filter-bar" id="filterBar">
            <label>Filter Roles:</label>
            <div style="position: relative; flex: 1; min-width: 200px;">
                <input type="text" class="filter-search" id="roleSearchInput" placeholder="Search and select roles to include..." autocomplete="off">
                <div class="filter-dropdown" id="roleDropdown"></div>
            </div>
            <div class="filter-actions">
                <span class="filter-count" id="filterCount">Showing all {total_unique_roles} roles</span>
                <button class="filter-btn" id="clearFilterBtn" onclick="clearRoleFilter()">Clear</button>
                <button class="filter-btn primary" id="selectAllBtn" onclick="selectAllRoles()">Select All</button>
            </div>
        </div>
        <div class="filter-tags" id="filterTags"></div>

        <!-- Navigation Tabs -->
        <div class="tab-nav" id="tabNav">
            <button class="tab-btn active" onclick="showTab('overview', this)">📈 Overview</button>
            <button class="tab-btn" onclick="showTab('cross-refs', this)">🔀 Cross-References ({total_cross_refs})</button>
            <button class="tab-btn" onclick="showTab('functions', this)">🏢 By Function</button>
            <button class="tab-btn" onclick="showTab('matrix', this)">📊 Matrix View</button>
            <button class="tab-btn" onclick="showTab('details', this)">📋 Detailed List</button>
        </div>

        <!-- Tab: Overview -->
        <div id="tab-overview" class="tab-content active">
            <!-- Stats Cards -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_functions}</div>
                    <div class="stat-label">Active Functions</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-value" id="statUniqueRoles">{total_unique_roles}</div>
                    <div class="stat-label">Unique Roles</div>
                </div>
                <div class="stat-card secondary">
                    <div class="stat-value">{total_role_assignments}</div>
                    <div class="stat-label">Role Assignments</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-value">{total_documents}</div>
                    <div class="stat-label">Documents Analyzed</div>
                </div>
                <div class="stat-card {"warning" if total_cross_refs > 0 else ""}">
                    <div class="stat-value">{total_cross_refs}</div>
                    <div class="stat-label">Cross-Functional Refs</div>
                    {f'<span class="stat-change negative">Requires Review</span>' if total_cross_refs > 0 else ''}
                </div>
            </div>

            <!-- Charts -->
            <div class="charts-grid">
                <div class="chart-card">
                    <div class="chart-title">
                        <span>📊</span> Roles by Function (Top 10)
                    </div>
                    <div class="chart-container">
                        <canvas id="rolesByFunctionChart"></canvas>
                    </div>
                </div>

                <div class="chart-card">
                    <div class="chart-title">
                        <span>🥧</span> Role Distribution
                    </div>
                    <div class="chart-container">
                        <canvas id="roleDistributionChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Top Functions Table -->
            <div class="chart-card">
                <div class="chart-title">
                    <span>🏆</span> Top 10 Functions by Role Count
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Function</th>
                            <th>Code</th>
                            <th>Roles</th>
                            <th>Cross-Refs</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    # Add top 10 functions
    for i, func in enumerate(function_role_counts[:10]):
        cross_count = len(cross_ref_by_source.get(func['code'], [])) + len(cross_ref_by_target.get(func['code'], []))
        html += f'''
                        <tr>
                            <td><strong>#{i+1}</strong></td>
                            <td>
                                <span class="func-badge" style="background: {func['color']}; margin-right: 8px; vertical-align: middle;">{escape(func.get('code', '?'))}</span>
                                {escape(func['name'])}
                            </td>
                            <td><code>{escape(func['code'])}</code></td>
                            <td><strong>{func['count']}</strong></td>
                            <td>{f'<span style="color: var(--warning)">⚠️ {cross_count}</span>' if cross_count > 0 else '-'}</td>
                        </tr>
'''

    html += '''
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Tab: Cross-References -->
        <div id="tab-cross-refs" class="tab-content">
'''

    if cross_references:
        html += f'''
            <div class="cross-ref-section">
                <div class="section-header">
                    <div class="section-title">
                        <span>🔀</span> Cross-Functional Role References
                        <span class="section-badge">{len(cross_references)} Found</span>
                    </div>
                </div>
                <div style="padding: 16px 24px; background: var(--bg-secondary); border-bottom: 1px solid var(--border);">
                    <p style="color: var(--text-secondary); font-size: 14px;">
                        ⚠️ These are roles that appear in documents owned by one function but are assigned to a different function.
                        This may indicate cross-functional dependencies that should be reviewed.
                    </p>
                </div>
                <div class="cross-ref-list">
'''

        for ref in cross_references:
            source_color = ref.get('source_color', '#6b7280')
            target_color = ref.get('target_color', '#6b7280')
            html += f'''
                    <div class="cross-ref-item" data-role-name="{escape(ref.get('role_name', ''))}">
                        <div class="cross-ref-function">
                            <span class="func-badge-sm" style="background: {source_color};">{escape(ref.get('source_function', '?'))}</span>
                            <div class="func-info">
                                <div class="func-name">{escape(ref.get('source_function_name', ref.get('source_function', 'Unknown')))}</div>
                                <div class="func-role">Document Owner</div>
                            </div>
                        </div>
                        <div class="cross-ref-arrow">→</div>
                        <div class="cross-ref-function">
                            <span class="func-badge-sm" style="background: {target_color};">{escape(ref.get('target_function', '?'))}</span>
                            <div class="func-info">
                                <div class="func-name">{escape(ref.get('target_function_name', ref.get('target_function', 'Unknown')))}</div>
                                <div class="func-role">Role Owner: <strong>{escape(ref.get('role_name', 'Unknown'))}</strong></div>
                            </div>
                        </div>
                        <div class="cross-ref-context">
                            📄 {escape(ref.get('document_name', 'Unknown Document')[:40])}
                        </div>
                    </div>
'''

        html += '''
                </div>
            </div>

            <!-- Cross-Reference Flow Chart -->
            <div class="chart-card">
                <div class="chart-title">
                    <span>📊</span> Cross-Reference Flow
                </div>
                <div class="chart-container" style="height: 400px;">
                    <canvas id="crossRefFlowChart"></canvas>
                </div>
            </div>
'''
    else:
        html += '''
            <div class="chart-card" style="text-align: center; padding: 60px;">
                <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
                <h3 style="color: var(--success); margin-bottom: 8px;">No Cross-Functional References Found</h3>
                <p style="color: var(--text-secondary);">All roles are properly contained within their assigned functions.</p>
            </div>
'''

    html += '''
        </div>

        <!-- Tab: Functions -->
        <div id="tab-functions" class="tab-content">
'''

    for func in functions:
        roles = func.get('roles', [])
        func_cross_refs = [r for r in cross_references if r.get('source_function') == func.get('code') or r.get('target_function') == func.get('code')]

        html += f'''
            <div class="function-card" onclick="toggleFunction(this)">
                <div class="function-header">
                    <div class="function-badge" style="background: {func.get('color', '#3b82f6')}" title="{escape(func.get('code', ''))}">{escape(func.get('code', '?'))}</div>
                    <div class="function-info">
                        <div class="function-name">{escape(func.get('name', 'Unknown'))}</div>
                        <div class="function-meta">{escape(func.get('description', ''))}</div>
                    </div>
                    <div class="function-stats">
                        <div class="mini-stat">
                            <div class="mini-stat-value">{len(roles)}</div>
                            <div class="mini-stat-label">Roles</div>
                        </div>
                        {f'<div class="mini-stat" style="background: rgba(245, 158, 11, 0.1);"><div class="mini-stat-value" style="color: var(--warning)">{len(func_cross_refs)}</div><div class="mini-stat-label">Cross-Refs</div></div>' if func_cross_refs else ''}
                    </div>
                    <div class="function-toggle">▼</div>
                </div>
                <div class="function-body">
'''

        if roles:
            html += '<div class="role-grid">'
            for role in roles:
                docs = role.get('documents', [])
                actions = role.get('required_actions', [])

                # Check if any documents are cross-functional
                role_cross_refs = [r for r in cross_references if r.get('role_name') == role.get('name')]

                html += f'''
                    <div class="role-item" data-role-name="{escape(role.get('name', ''))}">
                        <div class="role-header">
                            <div class="role-name">{escape(role.get('name', 'Unknown'))}</div>
                            <div class="role-count">{len(docs)} docs</div>
                        </div>
                        <div class="role-docs">
'''
                for doc in docs[:6]:
                    is_cross_ref = any(r.get('document_name') == doc.get('filename') for r in role_cross_refs)
                    html += f'<span class="doc-tag {" cross-ref" if is_cross_ref else ""}" title="{escape(doc.get("filename", ""))}">{escape(doc.get("filename", "")[:20])}</span>'

                if len(docs) > 6:
                    html += f'<span class="doc-tag">+{len(docs) - 6} more</span>'

                html += '</div>'

                if actions:
                    html += '<div class="role-actions">'
                    for action in actions[:3]:
                        stmt = action.get('statement', '')[:100]
                        if len(action.get('statement', '')) > 100:
                            stmt += '...'
                        html += f'<div class="action-item">{escape(stmt)}</div>'
                    if len(actions) > 3:
                        html += f'<div class="action-item" style="color: var(--primary)">+{len(actions) - 3} more actions</div>'
                    html += '</div>'

                html += '</div>'
            html += '</div>'
        else:
            html += '<p style="color: var(--text-muted); text-align: center; padding: 40px;">No roles assigned to this function</p>'

        html += '''
                </div>
            </div>
'''

    html += '''
        </div>

        <!-- Tab: Matrix -->
        <div id="tab-matrix" class="tab-content">
            <div class="chart-card">
                <div class="chart-title">
                    <span>📊</span> Function-Role Density Matrix
                </div>
                <p style="color: var(--text-secondary); margin-bottom: 16px;">
                    Heatmap showing role density across functions. Darker colors indicate more roles assigned.
                </p>
                <div id="heatmapContainer"></div>
                <div class="legend" style="margin-top: 20px;">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #dbeafe;"></div>
                        <span>Low (1-5 roles)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #60a5fa;"></div>
                        <span>Medium (6-15 roles)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #2563eb;"></div>
                        <span>High (16-30 roles)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #1e3a8a;"></div>
                        <span>Very High (30+ roles)</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tab: Details -->
        <div id="tab-details" class="tab-content">
            <div class="chart-card">
                <div class="chart-title">
                    <span>📋</span> Complete Role Registry
                    <span class="filter-count" id="detailsCount"></span>
                </div>
                <div style="max-height: 600px; overflow-y: auto;">
                <table class="data-table" id="roleRegistryTable">
                    <thead>
                        <tr>
                            <th>Role Name</th>
                            <th>Function(s)</th>
                            <th>Documents</th>
                            <th>Actions</th>
                            <th>Cross-Refs</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    for role in all_roles_sorted:
        func_badges = ' '.join(
            f'<span class="func-badge-sm" style="background: {f.get("color", "#6b7280")}; margin-right: 4px; vertical-align: middle;">{escape(f.get("code", "?"))}</span>'
            for f in role['functions']
        )
        func_names = ', '.join(escape(f['name']) for f in role['functions'])
        html += f'''
                        <tr data-role-name="{escape(role['name'])}">
                            <td><strong>{escape(role['name'])}</strong></td>
                            <td>
                                {func_badges}
                                <span style="margin-left: 2px;">{func_names}</span>
                            </td>
                            <td>{role['doc_count']}</td>
                            <td>{role['action_count']}</td>
                            <td>{f'<span style="color: var(--warning)">⚠️ {role["cross_refs"]}</span>' if role['cross_refs'] > 0 else '-'}</td>
                        </tr>
'''

    html += f'''
                    </tbody>
                </table>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="report-footer">
            <p>Generated by <strong>AEGIS</strong> - Aerospace Engineering Governance & Inspection System</p>
            <p style="margin-top: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | v2.0.0</p>
        </div>
    </div>

    <script>
        // =====================================================
        // TAB SWITCHING
        // =====================================================
        function showTab(tabId, btn) {{
            document.querySelectorAll('.tab-content').forEach(function(t) {{ t.classList.remove('active'); }});
            document.querySelectorAll('.tab-btn').forEach(function(b) {{ b.classList.remove('active'); }});
            var tab = document.getElementById('tab-' + tabId);
            if (tab) tab.classList.add('active');
            if (btn) btn.classList.add('active');
        }}

        // =====================================================
        // FUNCTION CARD TOGGLE
        // =====================================================
        function toggleFunction(card) {{
            card.classList.toggle('expanded');
        }}

        // =====================================================
        // ROLE FILTER SYSTEM
        // =====================================================
        var allRoleNames = {all_role_names_json};
        var selectedRoles = new Set();  // empty = show all
        var roleSearchInput = document.getElementById('roleSearchInput');
        var roleDropdown = document.getElementById('roleDropdown');
        var filterTags = document.getElementById('filterTags');
        var filterCount = document.getElementById('filterCount');

        function buildDropdown(filter) {{
            var search = (filter || '').toLowerCase();
            var html = '';
            var matches = allRoleNames.filter(function(r) {{
                return !search || r.toLowerCase().indexOf(search) !== -1;
            }});
            if (matches.length === 0) {{
                html = '<div class="filter-option" style="color: var(--text-muted);">No roles match</div>';
            }} else {{
                matches.slice(0, 50).forEach(function(name) {{
                    var sel = selectedRoles.has(name) ? ' selected' : '';
                    html += '<div class="filter-option' + sel + '" onclick="toggleRoleSelection(\\'' + name.replace(/'/g, "\\\\'") + '\\')">' + name + '</div>';
                }});
                if (matches.length > 50) {{
                    html += '<div class="filter-option" style="color: var(--text-muted); cursor: default;">...and ' + (matches.length - 50) + ' more (type to narrow)</div>';
                }}
            }}
            roleDropdown.innerHTML = html;
        }}

        function toggleRoleSelection(name) {{
            if (selectedRoles.has(name)) {{
                selectedRoles.delete(name);
            }} else {{
                selectedRoles.add(name);
            }}
            applyRoleFilter();
            buildDropdown(roleSearchInput.value);
        }}

        function clearRoleFilter() {{
            selectedRoles.clear();
            roleSearchInput.value = '';
            applyRoleFilter();
            roleDropdown.classList.remove('visible');
        }}

        function selectAllRoles() {{
            allRoleNames.forEach(function(r) {{ selectedRoles.add(r); }});
            applyRoleFilter();
            buildDropdown(roleSearchInput.value);
        }}

        function applyRoleFilter() {{
            var showAll = selectedRoles.size === 0;
            var count = 0;

            // Update filter tags
            var tagsHtml = '';
            selectedRoles.forEach(function(name) {{
                tagsHtml += '<span class="filter-tag" onclick="toggleRoleSelection(\\'' + name.replace(/'/g, "\\\\'") + '\\')">' + name + ' <span class="remove">×</span></span>';
            }});
            filterTags.innerHTML = tagsHtml;
            if (selectedRoles.size > 0) {{
                filterTags.style.marginBottom = '12px';
            }} else {{
                filterTags.style.marginBottom = '0';
            }}

            // Filter the Details table
            var rows = document.querySelectorAll('#roleRegistryTable tbody tr[data-role-name]');
            rows.forEach(function(row) {{
                var rname = row.getAttribute('data-role-name');
                if (showAll || selectedRoles.has(rname)) {{
                    row.classList.remove('hidden-role');
                    count++;
                }} else {{
                    row.classList.add('hidden-role');
                }}
            }});

            // Filter role items in By Function tab
            document.querySelectorAll('.role-item[data-role-name]').forEach(function(item) {{
                var rname = item.getAttribute('data-role-name');
                if (showAll || selectedRoles.has(rname)) {{
                    item.style.display = '';
                }} else {{
                    item.style.display = 'none';
                }}
            }});

            // Filter cross-reference items
            document.querySelectorAll('.cross-ref-item[data-role-name]').forEach(function(item) {{
                var rname = item.getAttribute('data-role-name');
                if (showAll || selectedRoles.has(rname)) {{
                    item.style.display = '';
                }} else {{
                    item.style.display = 'none';
                }}
            }});

            // Update count display
            if (showAll) {{
                filterCount.textContent = 'Showing all ' + allRoleNames.length + ' roles';
                count = allRoleNames.length;
            }} else {{
                filterCount.textContent = 'Showing ' + selectedRoles.size + ' of ' + allRoleNames.length + ' roles';
            }}

            var detailsCount = document.getElementById('detailsCount');
            if (detailsCount) {{
                detailsCount.textContent = showAll ? '' : '(' + selectedRoles.size + ' selected)';
            }}
        }}

        // Search input events
        roleSearchInput.addEventListener('focus', function() {{
            buildDropdown(this.value);
            roleDropdown.classList.add('visible');
        }});

        roleSearchInput.addEventListener('input', function() {{
            buildDropdown(this.value);
            roleDropdown.classList.add('visible');
        }});

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {{
            if (!e.target.closest('.filter-bar') && !e.target.closest('.filter-dropdown')) {{
                roleDropdown.classList.remove('visible');
            }}
        }});

        // =====================================================
        // CHARTS (Chart.js)
        // =====================================================
        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                var chartColors = {json.dumps([f['color'] for f in function_role_counts[:10]])};
                var chartLabels = {json.dumps([f['name'][:20] for f in function_role_counts[:10]])};
                var chartData = {json.dumps([f['count'] for f in function_role_counts[:10]])};

                // Bar chart - Roles by Function
                var barCanvas = document.getElementById('rolesByFunctionChart');
                if (barCanvas && chartData.length > 0) {{
                    new Chart(barCanvas, {{
                        type: 'bar',
                        data: {{
                            labels: chartLabels,
                            datasets: [{{
                                label: 'Roles',
                                data: chartData,
                                backgroundColor: chartColors,
                                borderRadius: 6,
                                borderSkipped: false
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{ display: false }},
                                tooltip: {{
                                    callbacks: {{
                                        label: function(ctx) {{ return ctx.parsed.y + ' roles'; }}
                                    }}
                                }}
                            }},
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    grid: {{ color: 'rgba(0,0,0,0.05)' }},
                                    ticks: {{ precision: 0 }}
                                }},
                                x: {{
                                    grid: {{ display: false }},
                                    ticks: {{ maxRotation: 45, minRotation: 0 }}
                                }}
                            }}
                        }}
                    }});
                }}

                // Doughnut chart - Distribution
                var doughnutCanvas = document.getElementById('roleDistributionChart');
                if (doughnutCanvas && chartData.length > 0) {{
                    new Chart(doughnutCanvas, {{
                        type: 'doughnut',
                        data: {{
                            labels: chartLabels,
                            datasets: [{{
                                data: chartData,
                                backgroundColor: chartColors,
                                borderWidth: 0,
                                hoverOffset: 10
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            maintainAspectRatio: false,
                            cutout: '60%',
                            plugins: {{
                                legend: {{
                                    position: 'right',
                                    labels: {{
                                        boxWidth: 12,
                                        padding: 12,
                                        font: {{ size: 11 }}
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}

                // Heatmap - Function-Role Density Matrix (HTML-based)
                var heatmapContainer = document.getElementById('heatmapContainer');
                if (heatmapContainer) {{
                    var heatmapData = {json.dumps(function_role_counts)};
                    if (heatmapData.length > 0) {{
                        var maxCount = Math.max.apply(null, heatmapData.map(function(d) {{ return d.count; }}));
                        var cols = Math.min(heatmapData.length, 6);
                        var gridHtml = '<div class="heatmap-grid" style="grid-template-columns: repeat(' + cols + ', 1fr);">';
                        heatmapData.forEach(function(item) {{
                            var ratio = maxCount > 0 ? item.count / maxCount : 0;
                            var bg, fg;
                            if (item.count <= 5) {{ bg = '#dbeafe'; fg = '#1e3a8a'; }}
                            else if (item.count <= 15) {{ bg = '#60a5fa'; fg = '#1e3a8a'; }}
                            else if (item.count <= 30) {{ bg = '#2563eb'; fg = '#ffffff'; }}
                            else {{ bg = '#1e3a8a'; fg = '#ffffff'; }}
                            gridHtml += '<div class="heatmap-cell" style="background:' + bg + '; color:' + fg + ';">'
                                + '<div class="heatmap-value">' + item.count + '</div>'
                                + '<div class="heatmap-code">' + item.code + '</div>'
                                + '<div class="heatmap-name">' + item.name.substring(0, 25) + '</div>'
                                + '</div>';
                        }});
                        gridHtml += '</div>';
                        heatmapContainer.innerHTML = gridHtml;
                    }} else {{
                        heatmapContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">No function data available for heatmap</p>';
                    }}
                }}

                // Cross-reference flow chart
                var crossRefCanvas = document.getElementById('crossRefFlowChart');
                if (crossRefCanvas) {{
                    var crossRefData = {json.dumps(cross_ref_matrix)};

                    // Count cross-refs between each function pair
                    var pairCounts = {{}};
                    crossRefData.forEach(function(ref) {{
                        var key = ref.source + ' → ' + ref.target;
                        pairCounts[key] = (pairCounts[key] || 0) + 1;
                    }});

                    var flowLabels = Object.keys(pairCounts);
                    var flowValues = Object.values(pairCounts);

                    if (flowLabels.length > 0) {{
                        new Chart(crossRefCanvas, {{
                            type: 'bar',
                            data: {{
                                labels: flowLabels,
                                datasets: [{{
                                    label: 'Cross-References',
                                    data: flowValues,
                                    backgroundColor: '#f59e0b',
                                    borderRadius: 6
                                }}]
                            }},
                            options: {{
                                indexAxis: 'y',
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {{
                                    legend: {{ display: false }},
                                    tooltip: {{
                                        callbacks: {{
                                            label: function(ctx) {{ return ctx.parsed.x + ' cross-references'; }}
                                        }}
                                    }}
                                }},
                                scales: {{
                                    x: {{
                                        beginAtZero: true,
                                        grid: {{ color: 'rgba(0,0,0,0.05)' }},
                                        ticks: {{ precision: 0 }}
                                    }},
                                    y: {{
                                        grid: {{ display: false }}
                                    }}
                                }}
                            }}
                        }});
                    }} else {{
                        crossRefCanvas.parentElement.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 40px;">No cross-references to chart</p>';
                    }}
                }}
            }} catch (err) {{
                console.error('AEGIS Report: Chart initialization error:', err);
            }}
        }});
    </script>
</body>
</html>
'''

    return html


def generate_comprehensive_documents_report(
    functions: List[Dict],
    cross_references: List[Dict],
    document_stats: Dict,
    role_stats: Dict,
    report_title: str = "Documents by Function Report"
) -> str:
    """
    Generate a comprehensive, data-rich HTML report for documents grouped by function,
    showing which roles appear in each document.

    Args:
        functions: List of function groups, each with 'documents' containing roles
        cross_references: List of cross-functional role references
        document_stats: Aggregate statistics about documents
        role_stats: Aggregate statistics about roles
        report_title: Title for the report

    Returns:
        Complete HTML document as string
    """
    # Calculate summary statistics
    total_functions = len(functions)
    all_documents = []
    for func in functions:
        all_documents.extend(func.get('documents', []))
    total_documents = len(all_documents)
    total_roles_found = sum(d.get('role_count') or 0 for d in all_documents)
    unique_roles = set()
    for doc in all_documents:
        for role in doc.get('roles', []):
            rn = role.get('name') or ''
            if rn:
                unique_roles.add(rn)
    total_unique_roles = len(unique_roles)
    total_cross_refs = len(cross_references)

    # Docs with most roles
    docs_by_role_count = sorted(all_documents, key=lambda d: d.get('role_count') or 0, reverse=True)

    # Docs per function for charts
    func_doc_counts = [
        {
            'name': str(f.get('function_name') or f.get('function_code') or '?'),
            'code': str(f.get('function_code') or '?'),
            'count': len(f.get('documents', [])),
            'color': f.get('function_color') or '#3b82f6'
        }
        for f in functions if f.get('documents')
    ]
    func_doc_counts.sort(key=lambda x: x['count'], reverse=True)

    # Role frequency across all documents
    role_frequency = {}
    for doc in all_documents:
        for role in doc.get('roles', []):
            rname = role.get('name', '')
            if rname:
                if rname not in role_frequency:
                    role_frequency[rname] = {'name': rname, 'doc_count': 0, 'total_mentions': 0}
                role_frequency[rname]['doc_count'] += 1
                role_frequency[rname]['total_mentions'] += role.get('count', 0) or 0
    top_roles = sorted(role_frequency.values(), key=lambda r: r['doc_count'], reverse=True)[:15]

    # Owner stats
    owner_counts = {}
    for doc in all_documents:
        owner = doc.get('document_owner', 'Unknown') or 'Unknown'
        owner_counts[owner] = owner_counts.get(owner, 0) + 1

    # JSON data for charts
    all_role_names_json = json.dumps(sorted(unique_roles))

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGIS - {escape(report_title)}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --primary: #3b82f6;
            --primary-dark: #1d4ed8;
            --secondary: #6366f1;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #06b6d4;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --text-muted: #94a3b8;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --border: #e2e8f0;
            --shadow: rgba(0, 0, 0, 0.1);
            --gradient-primary: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --text-primary: #f1f5f9;
                --text-secondary: #94a3b8;
                --text-muted: #64748b;
                --bg-primary: #0f172a;
                --bg-secondary: #1e293b;
                --bg-tertiary: #334155;
                --border: #475569;
                --shadow: rgba(0, 0, 0, 0.3);
            }}
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.6;
            font-size: 14px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
        }}

        .report-header {{
            background: var(--gradient-primary);
            color: white;
            padding: 40px;
            border-radius: 16px;
            margin-bottom: 24px;
            position: relative;
            overflow: hidden;
        }}

        .report-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: rgba(255,255,255,0.1);
            border-radius: 50%;
        }}

        .header-content {{
            position: relative;
            z-index: 1;
        }}

        .report-title {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .report-subtitle {{
            font-size: 16px;
            opacity: 0.9;
            max-width: 600px;
        }}

        .report-meta {{
            display: flex;
            gap: 24px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            opacity: 0.85;
        }}

        /* Tabs */
        .tab-nav {{
            display: flex;
            gap: 4px;
            background: var(--bg-primary);
            padding: 8px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px var(--shadow);
            overflow-x: auto;
        }}

        .tab-btn {{
            padding: 12px 20px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .tab-btn:hover {{ background: var(--bg-tertiary); color: var(--text-primary); }}
        .tab-btn.active {{ background: var(--primary); color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        /* Stats */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}

        .stat-card {{
            background: var(--bg-primary);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: var(--primary);
        }}

        .stat-card.success::before {{ background: var(--success); }}
        .stat-card.warning::before {{ background: var(--warning); }}
        .stat-card.info::before {{ background: var(--info); }}
        .stat-card.secondary::before {{ background: var(--secondary); }}

        .stat-value {{
            font-size: 36px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1;
        }}

        .stat-label {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        /* Charts */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }}

        .chart-card {{
            background: var(--bg-primary);
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
            padding: 24px;
        }}

        .chart-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .chart-container {{
            position: relative;
            height: 300px;
        }}

        /* Function sections */
        .function-section {{
            background: var(--bg-primary);
            border-radius: 12px;
            box-shadow: 0 2px 8px var(--shadow);
            margin-bottom: 20px;
            overflow: hidden;
        }}

        .function-header {{
            padding: 20px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s;
        }}

        .function-header:hover {{ background: var(--bg-secondary); }}

        .function-badge {{
            min-width: 40px;
            height: 40px;
            padding: 6px 10px;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 11px;
            flex-shrink: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        .function-info {{ flex: 1; }}

        .function-name {{
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .function-meta {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 2px;
        }}

        .function-toggle {{
            font-size: 20px;
            color: var(--text-muted);
            transition: transform 0.2s;
        }}

        .function-section.expanded .function-toggle {{
            transform: rotate(180deg);
        }}

        .function-body {{
            display: none;
            padding: 20px 24px;
        }}

        .function-section.expanded .function-body {{
            display: block;
        }}

        /* Document cards */
        .doc-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
            transition: all 0.2s;
        }}

        .doc-card:hover {{
            border-color: var(--primary);
            box-shadow: 0 4px 12px var(--shadow);
        }}

        .doc-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}

        .doc-name {{
            font-weight: 600;
            font-size: 15px;
            color: var(--text-primary);
        }}

        .doc-number {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }}

        .doc-owner {{
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
        }}

        .role-badge-count {{
            background: var(--primary);
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
        }}

        .doc-roles {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }}

        .role-chip {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 5px 12px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 12px;
            color: var(--text-primary);
            transition: all 0.15s;
        }}

        .role-chip:hover {{
            border-color: var(--primary);
            background: rgba(59, 130, 246, 0.08);
        }}

        .role-chip .mention-count {{
            background: var(--primary);
            color: white;
            padding: 1px 6px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
            min-width: 18px;
            text-align: center;
        }}

        .role-chip.cross-ref {{
            border-color: var(--warning);
            background: rgba(245, 158, 11, 0.08);
        }}

        .role-chip.cross-ref .mention-count {{
            background: var(--warning);
        }}

        .responsibilities-list {{
            margin-top: 8px;
            padding-left: 16px;
        }}

        .responsibility {{
            font-size: 12px;
            color: var(--text-secondary);
            padding: 2px 0;
            line-height: 1.4;
        }}

        .responsibility::before {{
            content: '→ ';
            color: var(--primary);
        }}

        .doc-expand-btn {{
            display: inline-block;
            padding: 4px 10px;
            font-size: 11px;
            color: var(--primary);
            background: none;
            border: 1px solid var(--primary);
            border-radius: 6px;
            cursor: pointer;
            margin-top: 8px;
        }}

        .doc-expand-btn:hover {{
            background: rgba(59, 130, 246, 0.08);
        }}

        .doc-details {{
            display: none;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dashed var(--border);
        }}

        .doc-details.visible {{
            display: block;
        }}

        /* Tables */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        .data-table th, .data-table td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        .data-table th {{
            background: var(--bg-tertiary);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
        }}

        .data-table tr:hover td {{ background: var(--bg-secondary); }}

        .func-badge-sm {{
            min-width: 28px; height: 24px; padding: 3px 6px;
            border-radius: 5px; display: inline-flex; align-items: center;
            justify-content: center; color: white; font-weight: 600;
            font-size: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        }}

        .bar-bg {{
            background: var(--bg-tertiary);
            border-radius: 4px;
            height: 8px;
            width: 100%;
            overflow: hidden;
        }}

        .bar-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s;
        }}

        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 24px;
            color: var(--text-muted);
            font-size: 13px;
            margin-top: 24px;
        }}

        @media print {{
            .tab-nav, .function-toggle, .doc-expand-btn {{ display: none; }}
            .tab-content {{ display: block !important; }}
            .function-body {{ display: block !important; }}
            .doc-details {{ display: block !important; }}
            .container {{ max-width: 100%; padding: 0; }}
            .report-header {{ background: #0f766e !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .function-section, .chart-card {{ break-inside: avoid; box-shadow: none; border: 1px solid #ddd; }}
        }}

        @media (max-width: 768px) {{
            .container {{ padding: 16px; }}
            .report-header {{ padding: 24px; }}
            .report-title {{ font-size: 24px; }}
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .charts-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="report-header">
            <div class="header-content">
                <h1 class="report-title">
                    <span>📄</span> {escape(report_title)}
                </h1>
                <p class="report-subtitle">
                    Document inventory by function with role extraction analysis
                </p>
                <div class="report-meta">
                    <div class="meta-item"><span>📅</span> <span>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</span></div>
                    <div class="meta-item"><span>🏢</span> <span>{total_functions} Functions</span></div>
                    <div class="meta-item"><span>📄</span> <span>{total_documents} Documents</span></div>
                    <div class="meta-item"><span>👤</span> <span>{total_unique_roles} Unique Roles Found</span></div>
                </div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="tab-nav">
            <button class="tab-btn active" onclick="showTab('overview', this)">📈 Overview</button>
            <button class="tab-btn" onclick="showTab('documents', this)">📄 By Function</button>
            <button class="tab-btn" onclick="showTab('roles', this)">👤 Role Analysis</button>
            <button class="tab-btn" onclick="showTab('all-docs', this)">📋 All Documents</button>
        </div>

        <!-- Tab: Overview -->
        <div id="tab-overview" class="tab-content active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_functions}</div>
                    <div class="stat-label">Functions</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-value">{total_documents}</div>
                    <div class="stat-label">Documents</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-value">{total_unique_roles}</div>
                    <div class="stat-label">Unique Roles Found</div>
                </div>
                <div class="stat-card secondary">
                    <div class="stat-value">{total_roles_found}</div>
                    <div class="stat-label">Total Role References</div>
                </div>
                <div class="stat-card {"warning" if total_cross_refs > 0 else ""}">
                    <div class="stat-value">{total_cross_refs}</div>
                    <div class="stat-label">Cross-Function Refs</div>
                </div>
            </div>

            <div class="charts-grid">
                <div class="chart-card">
                    <div class="chart-title"><span>📊</span> Documents per Function</div>
                    <div class="chart-container">
                        <canvas id="docsPerFunctionChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <div class="chart-title"><span>🥧</span> Document Distribution</div>
                    <div class="chart-container">
                        <canvas id="docDistributionChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- Top Documents by Role Count -->
            <div class="chart-card">
                <div class="chart-title"><span>🏆</span> Documents with Most Roles</div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Document</th>
                            <th>Function</th>
                            <th>Owner</th>
                            <th>Roles</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    for i, doc in enumerate(docs_by_role_count[:15]):
        fc = doc.get('function_code') or '?'
        color = doc.get('function_color') or '#6b7280'
        html += f'''
                        <tr>
                            <td><strong>#{i+1}</strong></td>
                            <td><strong>{escape(str(doc.get('document_name') or '?')[:50])}</strong></td>
                            <td><span class="func-badge-sm" style="background: {color}">{escape(str(fc))}</span> {escape(str(doc.get('function_name') or ''))}</td>
                            <td>{escape(str(doc.get('document_owner') or '-'))}</td>
                            <td><strong>{doc.get('role_count', 0)}</strong></td>
                        </tr>
'''

    html += '''
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Tab: By Function -->
        <div id="tab-documents" class="tab-content">
'''

    for func in functions:
        docs = func.get('documents', [])
        fc = func.get('function_code') or '?'
        fname = func.get('function_name') or fc
        fcolor = func.get('function_color') or '#6b7280'
        total_func_roles = sum(d.get('role_count', 0) for d in docs)

        html += f'''
            <div class="function-section" onclick="toggleSection(this)">
                <div class="function-header">
                    <div class="function-badge" style="background: {fcolor}">{escape(str(fc))}</div>
                    <div class="function-info">
                        <div class="function-name">{escape(str(fname))}</div>
                        <div class="function-meta">{len(docs)} documents · {total_func_roles} role references</div>
                    </div>
                    <div class="function-toggle">▼</div>
                </div>
                <div class="function-body">
'''

        for doc in sorted(docs, key=lambda d: d.get('role_count', 0) or 0, reverse=True):
            dname = str(doc.get('document_name') or '?')
            dnumber = str(doc.get('doc_number') or '')
            downer = str(doc.get('document_owner') or '')
            droles = doc.get('roles', [])
            doc_id = doc.get('document_id') or 0

            html += f'''
                    <div class="doc-card">
                        <div class="doc-card-header">
                            <div>
                                <div class="doc-name">{escape(dname[:60])}</div>
                                {f'<div class="doc-number">#{escape(dnumber)}</div>' if dnumber else ''}
                                {f'<div class="doc-owner">Owner: {escape(downer)}</div>' if downer else ''}
                            </div>
                            <span class="role-badge-count">{len(droles)} role{"s" if len(droles) != 1 else ""}</span>
                        </div>
'''
            if droles:
                html += '<div class="doc-roles">'
                for role in sorted(droles, key=lambda r: r.get('count', 0) or 0, reverse=True):
                    rname = str(role.get('name') or '?')
                    rcount = role.get('count') or 0
                    is_cross = any(
                        cr.get('role_name') == rname and cr.get('document_name') == dname
                        for cr in cross_references
                    )
                    css_class = 'role-chip cross-ref' if is_cross else 'role-chip'
                    html += f'<span class="{css_class}">{escape(rname)} <span class="mention-count">{rcount}</span></span>'
                html += '</div>'

                # Expandable responsibilities section
                has_responsibilities = any(role.get('responsibilities') for role in droles)
                if has_responsibilities:
                    html += f'''
                        <button class="doc-expand-btn" onclick="event.stopPropagation(); toggleDetails('details-{doc_id}', this)">Show responsibilities</button>
                        <div class="doc-details" id="details-{doc_id}">
'''
                    for role in droles:
                        resps = role.get('responsibilities', [])
                        if resps:
                            html += f'<div style="margin-bottom: 8px;"><strong style="font-size: 12px;">{escape(role.get("name", "?"))}</strong></div>'
                            html += '<div class="responsibilities-list">'
                            for resp in resps[:5]:
                                html += f'<div class="responsibility">{escape(str(resp)[:120])}</div>'
                            html += '</div>'
                    html += '</div>'
            else:
                html += '<div style="color: var(--text-muted); font-size: 13px; margin-top: 6px;">No roles extracted</div>'

            html += '</div>'  # doc-card

        html += '''
                </div>
            </div>
'''

    html += '''
        </div>

        <!-- Tab: Role Analysis -->
        <div id="tab-roles" class="tab-content">
            <div class="chart-card">
                <div class="chart-title"><span>👤</span> Most Referenced Roles Across Documents</div>
                <div class="chart-container" style="height: 400px;">
                    <canvas id="topRolesChart"></canvas>
                </div>
            </div>

            <div class="chart-card" style="margin-top: 24px;">
                <div class="chart-title"><span>📊</span> Role Frequency Table</div>
                <div style="max-height: 500px; overflow-y: auto;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Role</th>
                            <th>Documents</th>
                            <th>Total Mentions</th>
                            <th>Frequency</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    max_doc_count = top_roles[0]['doc_count'] if top_roles else 1
    for role in top_roles:
        pct = (role['doc_count'] / max_doc_count * 100) if max_doc_count > 0 else 0
        html += f'''
                        <tr>
                            <td><strong>{escape(role['name'])}</strong></td>
                            <td>{role['doc_count']}</td>
                            <td>{role['total_mentions']}</td>
                            <td style="width: 200px;">
                                <div class="bar-bg"><div class="bar-fill" style="width: {pct:.0f}%; background: var(--primary);"></div></div>
                            </td>
                        </tr>
'''

    html += '''
                    </tbody>
                </table>
                </div>
            </div>
        </div>

        <!-- Tab: All Documents -->
        <div id="tab-all-docs" class="tab-content">
            <div class="chart-card">
                <div class="chart-title"><span>📋</span> Complete Document Inventory</div>
                <div style="max-height: 600px; overflow-y: auto;">
                <table class="data-table" id="allDocsTable">
                    <thead>
                        <tr>
                            <th>Document</th>
                            <th>Function</th>
                            <th>Owner</th>
                            <th>Roles</th>
                            <th>Top Roles</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    for doc in sorted(all_documents, key=lambda d: str(d.get('document_name') or '')):
        fc = str(doc.get('function_code') or '?')
        color = doc.get('function_color') or '#6b7280'
        droles = doc.get('roles', [])
        top_3 = sorted(droles, key=lambda r: r.get('count', 0) or 0, reverse=True)[:3]
        role_chips = ' '.join(
            f'<span style="display:inline-block;padding:2px 8px;background:var(--bg-tertiary);border-radius:12px;font-size:11px;margin:1px 2px;">{escape(str(r.get("name") or "?")[:20])}</span>'
            for r in top_3
        )
        if len(droles) > 3:
            role_chips += f' <span style="font-size:11px;color:var(--text-muted);">+{len(droles)-3}</span>'
        html += f'''
                        <tr>
                            <td><strong>{escape(str(doc.get('document_name') or '?')[:45])}</strong></td>
                            <td><span class="func-badge-sm" style="background:{color}">{escape(fc)}</span></td>
                            <td>{escape(str(doc.get('document_owner') or '-'))}</td>
                            <td><strong>{doc.get('role_count', 0)}</strong></td>
                            <td>{role_chips or '<span style="color:var(--text-muted)">—</span>'}</td>
                        </tr>
'''

    html += f'''
                    </tbody>
                </table>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="report-footer">
            <p>Generated by <strong>AEGIS</strong> - Aerospace Engineering Governance & Inspection System</p>
            <p style="margin-top: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | v2.0.0</p>
        </div>
    </div>

    <script>
        function showTab(tabId, btn) {{
            document.querySelectorAll('.tab-content').forEach(function(t) {{ t.classList.remove('active'); }});
            document.querySelectorAll('.tab-btn').forEach(function(b) {{ b.classList.remove('active'); }});
            var tab = document.getElementById('tab-' + tabId);
            if (tab) tab.classList.add('active');
            if (btn) btn.classList.add('active');
        }}

        function toggleSection(el) {{
            el.classList.toggle('expanded');
        }}

        function toggleDetails(id, btn) {{
            var el = document.getElementById(id);
            if (el) {{
                el.classList.toggle('visible');
                btn.textContent = el.classList.contains('visible') ? 'Hide responsibilities' : 'Show responsibilities';
            }}
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                var funcColors = {json.dumps([f['color'] for f in func_doc_counts[:10]])};
                var funcLabels = {json.dumps([f['name'][:20] for f in func_doc_counts[:10]])};
                var funcData = {json.dumps([f['count'] for f in func_doc_counts[:10]])};

                // Bar chart
                var barCanvas = document.getElementById('docsPerFunctionChart');
                if (barCanvas && funcData.length > 0) {{
                    new Chart(barCanvas, {{
                        type: 'bar',
                        data: {{
                            labels: funcLabels,
                            datasets: [{{ label: 'Documents', data: funcData, backgroundColor: funcColors, borderRadius: 6, borderSkipped: false }}]
                        }},
                        options: {{
                            responsive: true, maintainAspectRatio: false,
                            plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: function(ctx) {{ return ctx.parsed.y + ' documents'; }} }} }} }},
                            scales: {{ y: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ precision: 0 }} }}, x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 45 }} }} }}
                        }}
                    }});
                }}

                // Doughnut
                var doughnutCanvas = document.getElementById('docDistributionChart');
                if (doughnutCanvas && funcData.length > 0) {{
                    new Chart(doughnutCanvas, {{
                        type: 'doughnut',
                        data: {{
                            labels: funcLabels,
                            datasets: [{{ data: funcData, backgroundColor: funcColors, borderWidth: 0, hoverOffset: 10 }}]
                        }},
                        options: {{
                            responsive: true, maintainAspectRatio: false, cutout: '60%',
                            plugins: {{ legend: {{ position: 'right', labels: {{ boxWidth: 12, padding: 12, font: {{ size: 11 }} }} }} }}
                        }}
                    }});
                }}

                // Top roles horizontal bar
                var topRolesCanvas = document.getElementById('topRolesChart');
                if (topRolesCanvas) {{
                    var roleLabels = {json.dumps([r['name'][:25] for r in top_roles])};
                    var roleDocCounts = {json.dumps([r['doc_count'] for r in top_roles])};
                    if (roleLabels.length > 0) {{
                        new Chart(topRolesCanvas, {{
                            type: 'bar',
                            data: {{
                                labels: roleLabels,
                                datasets: [{{ label: 'Documents', data: roleDocCounts, backgroundColor: '#14b8a6', borderRadius: 6 }}]
                            }},
                            options: {{
                                indexAxis: 'y',
                                responsive: true, maintainAspectRatio: false,
                                plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{ label: function(ctx) {{ return 'Found in ' + ctx.parsed.x + ' documents'; }} }} }} }},
                                scales: {{ x: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ precision: 0 }} }}, y: {{ grid: {{ display: false }} }} }}
                            }}
                        }});
                    }}
                }}
            }} catch (err) {{
                console.error('AEGIS Report: Chart error:', err);
            }}
        }});
    </script>
</body>
</html>
'''

    return html


def detect_cross_functional_references(
    functions: List[Dict],
    document_categories: List[Dict],
    role_documents: Dict[str, List[Dict]]
) -> List[Dict]:
    """
    Detect roles that are referenced in documents owned by different functions.

    Args:
        functions: List of function definitions with their assigned roles
        document_categories: List of document category assignments (document -> function)
        role_documents: Mapping of role names to documents they appear in

    Returns:
        List of cross-functional reference records
    """
    cross_refs = []

    # Build lookup: document -> owning function
    doc_to_function = {}
    for cat in document_categories:
        doc_name = cat.get('document_name')
        func_code = cat.get('function_code')
        if doc_name and func_code:
            doc_to_function[doc_name] = {
                'function_code': func_code,
                'function_name': cat.get('function_name', func_code),
                'function_color': cat.get('function_color', '#6b7280')
            }

    # Build lookup: role -> assigned function
    role_to_function = {}
    func_lookup = {}
    for func in functions:
        func_code = func.get('code')
        func_lookup[func_code] = func
        for role in func.get('roles', []):
            role_name = role.get('name') if isinstance(role, dict) else role
            role_to_function[role_name] = {
                'function_code': func_code,
                'function_name': func.get('name', func_code),
                'function_color': func.get('color', '#6b7280')
            }

    # Find cross-references
    for role_name, docs in role_documents.items():
        role_func = role_to_function.get(role_name)
        if not role_func:
            continue

        for doc in docs:
            doc_name = doc.get('filename') if isinstance(doc, dict) else doc
            doc_func = doc_to_function.get(doc_name)

            if doc_func and doc_func['function_code'] != role_func['function_code']:
                cross_refs.append({
                    'role_name': role_name,
                    'document_name': doc_name,
                    'source_function': doc_func['function_code'],
                    'source_function_name': doc_func['function_name'],
                    'source_color': doc_func['function_color'],
                    'target_function': role_func['function_code'],
                    'target_function_name': role_func['function_name'],
                    'target_color': role_func['function_color']
                })

    return cross_refs
