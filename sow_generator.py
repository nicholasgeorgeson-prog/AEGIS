"""
AEGIS SOW Generator - Statement of Work HTML Generator
=======================================================
Generates a standalone, print-friendly HTML Statement of Work document
by aggregating data from AEGIS's extracted statements, adjudicated roles,
function categories, and document metadata.

Usage:
    from sow_generator import generate_sow_html
    html = generate_sow_html(config, roles, statements, documents, function_categories, relationships)

v1.0.0 (v4.6.1): Initial implementation
Author: AEGIS
"""

import json
import html as html_module
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import socket


def generate_sow_html(
    config: Dict[str, Any],
    roles: List[Dict],
    statements: List[Dict],
    documents: List[Dict],
    function_categories: List[Dict],
    relationships: List[Dict],
    metadata: Optional[Dict] = None
) -> str:
    """
    Generate a standalone HTML Statement of Work document.

    Args:
        config: SOW configuration with keys:
            - title: Project/SOW title
            - doc_number: Document number
            - version: Version string
            - date: Effective date
            - prepared_by: Author name
            - organization: Organization name
            - sections: Dict of section toggles (intro, scope, documents, requirements, wbs, roles, acceptance, standards)
            - intro_text: Custom introduction text
            - scope_text: Custom scope description
            - assumptions_text: Custom assumptions text
        roles: List of role dicts from role_dictionary
        statements: List of statement dicts from scan_statements
        documents: List of document metadata dicts
        function_categories: List of function category dicts
        relationships: List of role relationship dicts
        metadata: Optional dict with version, export_date, etc.

    Returns:
        Complete HTML string (standalone, no external dependencies)
    """
    if metadata is None:
        metadata = {}

    version = metadata.get('version', '4.6.1')
    export_date = metadata.get('export_date', datetime.now(timezone.utc).isoformat())
    hostname = metadata.get('hostname', socket.gethostname())

    # Extract config
    title = config.get('title', 'Statement of Work')
    doc_number = config.get('doc_number', '')
    doc_version = config.get('version', '1.0')
    effective_date = config.get('date', datetime.now().strftime('%Y-%m-%d'))
    prepared_by = config.get('prepared_by', '')
    organization = config.get('organization', '')
    sections = config.get('sections', {})
    intro_text = config.get('intro_text', '')
    scope_text = config.get('scope_text', '')
    assumptions_text = config.get('assumptions_text', '')

    # Default all sections to enabled
    show = {
        'intro': sections.get('intro', True),
        'scope': sections.get('scope', True),
        'documents': sections.get('documents', True),
        'requirements': sections.get('requirements', True),
        'wbs': sections.get('wbs', True),
        'roles': sections.get('roles', True),
        'acceptance': sections.get('acceptance', True),
        'standards': sections.get('standards', True),
        'assumptions': sections.get('assumptions', True),
    }

    # ── Data Processing ───────────────────────────────────────

    # Group statements by directive
    stmt_by_directive = {'shall': [], 'must': [], 'will': [], 'should': [], 'may': [], 'other': []}
    for s in statements:
        d = (s.get('directive') or '').lower().strip()
        if d in stmt_by_directive:
            stmt_by_directive[d].append(s)
        else:
            stmt_by_directive['other'].append(s)

    # Group statements by section
    stmt_by_section = {}
    for s in statements:
        sec = s.get('section') or s.get('source_section_title') or 'General'
        if sec not in stmt_by_section:
            stmt_by_section[sec] = []
        stmt_by_section[sec].append(s)

    # Group statements by role
    stmt_by_role = {}
    for s in statements:
        role = s.get('role') or 'Unassigned'
        if role not in stmt_by_role:
            stmt_by_role[role] = []
        stmt_by_role[role].append(s)

    # Active roles only
    active_roles = [r for r in roles if r.get('is_active', True)]
    deliverable_roles = [r for r in active_roles if r.get('is_deliverable', False)]

    # Function category lookup
    fc_lookup = {fc.get('code', ''): fc for fc in function_categories}

    # Build WBS from function categories (hierarchical)
    wbs_tree = _build_wbs_tree(function_categories, active_roles, statements)

    # Collect standards/references from statements
    standards_refs = _extract_standards(statements, documents)

    # Acceptance criteria from testable "shall" statements
    acceptance_stmts = [s for s in stmt_by_directive.get('shall', [])
                        if s.get('description', '')]

    # ── Generate Section HTML ─────────────────────────────────

    section_num = 0
    sections_html = ''

    # 1. Introduction
    if show['intro']:
        section_num += 1
        default_intro = f'This Statement of Work (SOW) defines the technical requirements, deliverables, and responsibilities for the work to be performed. It has been generated from analysis of {len(documents)} source document(s) containing {len(statements)} extracted requirement statement(s) and {len(active_roles)} identified role(s).'
        intro_content = html_module.escape(intro_text) if intro_text else default_intro
        sections_html += f'''
        <div class="sow-section" id="sec-intro">
            <h2>{section_num}. Introduction</h2>
            <p>{intro_content}</p>
        </div>'''

    # 2. Scope
    if show['scope']:
        section_num += 1
        scope_content = ''
        if scope_text:
            scope_content = f'<p>{html_module.escape(scope_text)}</p>'
        else:
            # Auto-generate scope from directive distribution
            shall_count = len(stmt_by_directive.get('shall', []))
            must_count = len(stmt_by_directive.get('must', []))
            will_count = len(stmt_by_directive.get('will', []))
            scope_content = f'''
            <p>This SOW encompasses the following scope of work derived from source document analysis:</p>
            <ul class="sow-list">
                <li><strong>{shall_count}</strong> binding requirement(s) (shall)</li>
                <li><strong>{must_count}</strong> mandatory obligation(s) (must)</li>
                <li><strong>{will_count}</strong> declarative statement(s) (will)</li>
                <li><strong>{len(active_roles)}</strong> identified role(s) / responsible parties</li>
                <li><strong>{len(deliverable_roles)}</strong> deliverable-critical role(s)</li>
            </ul>'''

        # Add section breakdown
        if stmt_by_section:
            scope_content += '<h3>Coverage Areas</h3><ul class="sow-list">'
            for sec_name, sec_stmts in sorted(stmt_by_section.items()):
                scope_content += f'<li><strong>{html_module.escape(str(sec_name))}</strong> — {len(sec_stmts)} statement(s)</li>'
            scope_content += '</ul>'

        sections_html += f'''
        <div class="sow-section" id="sec-scope">
            <h2>{section_num}. Scope</h2>
            {scope_content}
        </div>'''

    # 3. Applicable Documents
    if show['documents'] and documents:
        section_num += 1
        docs_rows = ''
        for i, doc in enumerate(documents, 1):
            fname = html_module.escape(doc.get('filename', 'Unknown'))
            word_count = doc.get('word_count', 0) or 0
            scan_count = doc.get('scan_count', 0) or 0
            score = doc.get('latest_score', doc.get('score', '—'))
            grade = doc.get('latest_grade', doc.get('grade', '—'))
            docs_rows += f'''
            <tr>
                <td>{i}</td>
                <td>{fname}</td>
                <td class="num">{word_count:,}</td>
                <td class="num">{scan_count}</td>
                <td class="num">{score}</td>
                <td>{grade}</td>
            </tr>'''

        sections_html += f'''
        <div class="sow-section" id="sec-documents">
            <h2>{section_num}. Applicable Documents</h2>
            <p>The following documents were analyzed to derive this Statement of Work:</p>
            <table class="sow-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Document</th>
                        <th>Words</th>
                        <th>Scans</th>
                        <th>Score</th>
                        <th>Grade</th>
                    </tr>
                </thead>
                <tbody>
                    {docs_rows}
                </tbody>
            </table>
        </div>'''

    # 4. Requirements / Deliverables
    if show['requirements'] and statements:
        section_num += 1
        req_content = ''

        # Group by directive priority: shall > must > will > should > may
        for directive in ['shall', 'must', 'will', 'should', 'may']:
            stmts = stmt_by_directive.get(directive, [])
            if not stmts:
                continue

            directive_label = directive.upper()
            req_content += f'<h3>{section_num}.{["shall","must","will","should","may"].index(directive)+1} {directive_label} Requirements ({len(stmts)})</h3>'
            req_content += '<table class="sow-table sow-req-table">'
            req_content += '<thead><tr><th>#</th><th>Requirement</th><th>Role</th><th>Source</th></tr></thead><tbody>'

            for i, s in enumerate(stmts, 1):
                desc = html_module.escape(s.get('description', '') or '')
                role = html_module.escape(s.get('role', '') or '—')
                source_doc = s.get('source_document', '') or ''
                source_section = s.get('source_section_title', s.get('section', '')) or ''
                source = html_module.escape(f'{source_doc} {source_section}'.strip()) if source_doc or source_section else '—'
                stmt_num = s.get('statement_number', s.get('number', '')) or ''

                req_content += f'''
                <tr>
                    <td class="num">{stmt_num or i}</td>
                    <td class="req-desc">{desc}</td>
                    <td class="role-cell">{role}</td>
                    <td class="source-cell">{source}</td>
                </tr>'''

            req_content += '</tbody></table>'

        sections_html += f'''
        <div class="sow-section" id="sec-requirements">
            <h2>{section_num}. Requirements and Deliverables</h2>
            <p>Requirements extracted from source documents, organized by directive type. Each requirement includes the responsible role and source traceability.</p>
            {req_content}
        </div>'''

    # 5. Work Breakdown Structure
    if show['wbs'] and wbs_tree:
        section_num += 1
        wbs_html = _render_wbs_tree(wbs_tree, section_num)
        sections_html += f'''
        <div class="sow-section" id="sec-wbs">
            <h2>{section_num}. Work Breakdown Structure</h2>
            <p>Hierarchical breakdown of work areas organized by AEGIS function categories.</p>
            {wbs_html}
        </div>'''

    # 6. Roles & Responsibilities
    if show['roles'] and active_roles:
        section_num += 1
        roles_html = ''

        for role in sorted(active_roles, key=lambda r: r.get('role_name', '')):
            rname = html_module.escape(role.get('role_name', ''))
            rdesc = html_module.escape(role.get('description', '') or '')
            rtype = html_module.escape(role.get('role_type', '') or '')
            rorg = html_module.escape(role.get('org_group', '') or '')
            is_del = role.get('is_deliverable', False)
            func_tags = role.get('function_tags', [])

            # Badge HTML
            badges = ''
            if is_del:
                badges += '<span class="sow-badge sow-badge-deliverable">Deliverable</span>'
            if rtype:
                badges += f'<span class="sow-badge sow-badge-type">{rtype}</span>'
            if rorg:
                badges += f'<span class="sow-badge sow-badge-org">{rorg}</span>'

            # Function tags
            tags_html = ''
            if func_tags:
                tags_html = '<div class="sow-role-tags">'
                for tag in func_tags:
                    if isinstance(tag, dict):
                        tname = html_module.escape(tag.get('name', tag.get('code', '')))
                        tcolor = tag.get('color', '#3b82f6')
                    else:
                        tname = html_module.escape(str(tag))
                        tcolor = '#3b82f6'
                    tags_html += f'<span class="sow-func-tag" style="--tag-color:{tcolor}">{tname}</span>'
                tags_html += '</div>'

            # Statements for this role
            role_stmts = stmt_by_role.get(role.get('role_name', ''), [])
            stmts_html = ''
            if role_stmts:
                stmts_html = f'<div class="sow-role-stmts"><strong>{len(role_stmts)} assigned statement(s):</strong><ul>'
                for rs in role_stmts[:10]:  # Limit to 10
                    d = html_module.escape(rs.get('description', '')[:120])
                    directive = (rs.get('directive', '') or '').upper()
                    stmts_html += f'<li><span class="sow-directive sow-d-{directive.lower()}">{directive}</span> {d}</li>'
                if len(role_stmts) > 10:
                    stmts_html += f'<li class="sow-more">...and {len(role_stmts) - 10} more</li>'
                stmts_html += '</ul></div>'

            # Relationships
            role_rels = [r for r in relationships
                         if r.get('source_role_name', '').lower() == role.get('role_name', '').lower()
                         or r.get('target_role_name', '').lower() == role.get('role_name', '').lower()]
            rels_html = ''
            if role_rels:
                rels_html = '<div class="sow-role-rels"><strong>Relationships:</strong><ul>'
                for rel in role_rels[:8]:
                    src = html_module.escape(rel.get('source_role_name', ''))
                    tgt = html_module.escape(rel.get('target_role_name', ''))
                    rtype_rel = html_module.escape(rel.get('relationship_type', ''))
                    rels_html += f'<li>{src} <em>{rtype_rel}</em> {tgt}</li>'
                rels_html += '</ul></div>'

            roles_html += f'''
            <div class="sow-role-card">
                <div class="sow-role-header">
                    <h4>{rname}</h4>
                    {badges}
                </div>
                {f'<p class="sow-role-desc">{rdesc}</p>' if rdesc else ''}
                {tags_html}
                {stmts_html}
                {rels_html}
            </div>'''

        sections_html += f'''
        <div class="sow-section" id="sec-roles">
            <h2>{section_num}. Roles and Responsibilities</h2>
            <p>{len(active_roles)} identified role(s), {len(deliverable_roles)} designated as deliverable-critical.</p>
            {roles_html}
        </div>'''

    # 7. Acceptance Criteria
    if show['acceptance'] and acceptance_stmts:
        section_num += 1
        acc_rows = ''
        for i, s in enumerate(acceptance_stmts[:50], 1):
            desc = html_module.escape(s.get('description', '')[:200])
            role = html_module.escape(s.get('role', '') or '—')
            source = html_module.escape(s.get('source_document', '') or '—')
            acc_rows += f'''
            <tr>
                <td class="num">{i}</td>
                <td class="req-desc">{desc}</td>
                <td class="role-cell">{role}</td>
                <td class="source-cell">{source}</td>
            </tr>'''

        sections_html += f'''
        <div class="sow-section" id="sec-acceptance">
            <h2>{section_num}. Acceptance Criteria</h2>
            <p>The following binding requirements (SHALL statements) serve as acceptance criteria for deliverables:</p>
            <table class="sow-table">
                <thead>
                    <tr><th>#</th><th>Acceptance Criterion</th><th>Responsible</th><th>Source</th></tr>
                </thead>
                <tbody>{acc_rows}</tbody>
            </table>
            {f'<p class="sow-note">Showing {min(50, len(acceptance_stmts))} of {len(acceptance_stmts)} acceptance criteria.</p>' if len(acceptance_stmts) > 50 else ''}
        </div>'''

    # 8. Standards & Compliance
    if show['standards'] and standards_refs:
        section_num += 1
        std_rows = ''
        for i, ref in enumerate(sorted(standards_refs), 1):
            std_rows += f'<tr><td class="num">{i}</td><td>{html_module.escape(ref)}</td></tr>'

        sections_html += f'''
        <div class="sow-section" id="sec-standards">
            <h2>{section_num}. Applicable Standards and References</h2>
            <p>The following standards, specifications, and references were identified in the source documents:</p>
            <table class="sow-table">
                <thead><tr><th>#</th><th>Standard / Reference</th></tr></thead>
                <tbody>{std_rows}</tbody>
            </table>
        </div>'''

    # 9. Assumptions & Constraints
    if show['assumptions']:
        section_num += 1
        assumptions_content = ''
        if assumptions_text:
            assumptions_content = f'<p>{html_module.escape(assumptions_text)}</p>'
        else:
            assumptions_content = '''
            <p>The following assumptions and constraints apply to this Statement of Work:</p>
            <ul class="sow-list">
                <li>All requirements are derived from the analyzed source documents and may require additional validation.</li>
                <li>Role assignments are based on automated extraction and adjudication; organizational confirmation is recommended.</li>
                <li>This SOW does not constitute a binding contract unless formally approved and executed by authorized parties.</li>
                <li>Schedule milestones and budget allocations should be added during the formal SOW review process.</li>
            </ul>'''

        sections_html += f'''
        <div class="sow-section" id="sec-assumptions">
            <h2>{section_num}. Assumptions and Constraints</h2>
            {assumptions_content}
        </div>'''

    # ── Build Table of Contents ───────────────────────────────
    toc_html = _build_toc(show, section_num)

    # ── Assemble Full HTML ────────────────────────────────────
    safe_config = json.dumps(config, default=str)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="AEGIS SOW Generator v{version}">
    <title>{html_module.escape(title)}</title>
    {_get_styles()}
</head>
<body>
    <div class="sow-container">
        <!-- Cover / Title Block -->
        <header class="sow-cover">
            <div class="sow-cover-brand">
                <svg class="sow-logo" viewBox="0 0 40 40" width="40" height="40">
                    <polygon points="20,4 36,36 4,36" fill="none" stroke="#D6A84A" stroke-width="2.5"/>
                    <circle cx="20" cy="24" r="6" fill="none" stroke="#D6A84A" stroke-width="2"/>
                    <line x1="20" y1="14" x2="20" y2="18" stroke="#D6A84A" stroke-width="2"/>
                </svg>
                <span class="sow-brand-text">AEGIS</span>
            </div>
            <h1 class="sow-title">{html_module.escape(title)}</h1>
            <div class="sow-meta-grid">
                {f'<div class="sow-meta-item"><span class="sow-meta-label">Document No.</span><span class="sow-meta-value">{html_module.escape(doc_number)}</span></div>' if doc_number else ''}
                <div class="sow-meta-item"><span class="sow-meta-label">Version</span><span class="sow-meta-value">{html_module.escape(str(doc_version))}</span></div>
                <div class="sow-meta-item"><span class="sow-meta-label">Effective Date</span><span class="sow-meta-value">{html_module.escape(effective_date)}</span></div>
                {f'<div class="sow-meta-item"><span class="sow-meta-label">Prepared By</span><span class="sow-meta-value">{html_module.escape(prepared_by)}</span></div>' if prepared_by else ''}
                {f'<div class="sow-meta-item"><span class="sow-meta-label">Organization</span><span class="sow-meta-value">{html_module.escape(organization)}</span></div>' if organization else ''}
            </div>
            <div class="sow-summary-bar">
                <div class="sow-sum-item"><span class="sow-sum-num">{len(documents)}</span><span class="sow-sum-label">Source Documents</span></div>
                <div class="sow-sum-item"><span class="sow-sum-num">{len(statements)}</span><span class="sow-sum-label">Statements</span></div>
                <div class="sow-sum-item"><span class="sow-sum-num">{len(active_roles)}</span><span class="sow-sum-label">Roles</span></div>
                <div class="sow-sum-item"><span class="sow-sum-num">{len(deliverable_roles)}</span><span class="sow-sum-label">Deliverables</span></div>
            </div>
        </header>

        <!-- Table of Contents -->
        <nav class="sow-toc">
            <h2>Table of Contents</h2>
            {toc_html}
        </nav>

        <!-- Sections -->
        {sections_html}

        <!-- Footer -->
        <footer class="sow-footer">
            <div class="sow-footer-left">
                Generated by AEGIS v{version} on {datetime.now().strftime('%B %d, %Y at %H:%M')}
            </div>
            <div class="sow-footer-right">
                {html_module.escape(title)} {f'| {html_module.escape(doc_number)}' if doc_number else ''} | v{html_module.escape(str(doc_version))}
            </div>
        </footer>
    </div>

    <script>
    // SOW config for reference
    window.SOW_CONFIG = {safe_config};
    window.SOW_META = {{
        aegis_version: '{version}',
        exported_at: '{export_date}',
        exported_by: '{html_module.escape(hostname)}'
    }};

    // Print button
    document.addEventListener('DOMContentLoaded', () => {{
        const printBtn = document.createElement('button');
        printBtn.className = 'sow-print-btn';
        printBtn.innerHTML = '&#x1F5B6; Print / Save PDF';
        printBtn.onclick = () => window.print();
        document.body.appendChild(printBtn);
    }});
    </script>
</body>
</html>'''

    return html


# ── Helper Functions ──────────────────────────────────────────

def _build_toc(show: Dict[str, bool], total_sections: int) -> str:
    """Build HTML table of contents."""
    section_names = []
    if show.get('intro'): section_names.append(('sec-intro', 'Introduction'))
    if show.get('scope'): section_names.append(('sec-scope', 'Scope'))
    if show.get('documents'): section_names.append(('sec-documents', 'Applicable Documents'))
    if show.get('requirements'): section_names.append(('sec-requirements', 'Requirements and Deliverables'))
    if show.get('wbs'): section_names.append(('sec-wbs', 'Work Breakdown Structure'))
    if show.get('roles'): section_names.append(('sec-roles', 'Roles and Responsibilities'))
    if show.get('acceptance'): section_names.append(('sec-acceptance', 'Acceptance Criteria'))
    if show.get('standards'): section_names.append(('sec-standards', 'Applicable Standards and References'))
    if show.get('assumptions'): section_names.append(('sec-assumptions', 'Assumptions and Constraints'))

    items = ''
    for i, (anchor, name) in enumerate(section_names, 1):
        items += f'<li><a href="#{anchor}">{i}. {name}</a></li>'

    return f'<ol class="sow-toc-list">{items}</ol>'


def _build_wbs_tree(function_categories: List[Dict], roles: List[Dict], statements: List[Dict]) -> List[Dict]:
    """Build a WBS tree from function categories with role and statement counts."""
    if not function_categories:
        return []

    # Build parent-child structure
    nodes = {}
    for fc in function_categories:
        code = fc.get('code', '')
        if not code:
            continue
        nodes[code] = {
            'code': code,
            'name': fc.get('name', code),
            'description': fc.get('description', ''),
            'color': fc.get('color', '#3b82f6'),
            'parent': fc.get('parent_code', ''),
            'children': [],
            'roles': [],
            'stmt_count': 0
        }

    # Assign children
    roots = []
    for code, node in nodes.items():
        parent = node['parent']
        if parent and parent in nodes:
            nodes[parent]['children'].append(node)
        else:
            roots.append(node)

    # Count roles per function category
    for role in roles:
        tags = role.get('function_tags', [])
        for tag in tags:
            tag_code = tag.get('code', tag) if isinstance(tag, dict) else str(tag)
            if tag_code in nodes:
                nodes[tag_code]['roles'].append(role.get('role_name', ''))

    return roots


def _render_wbs_tree(nodes: List[Dict], section_num: int) -> str:
    """Render WBS tree as nested HTML."""
    if not nodes:
        return '<p class="sow-note">No function categories defined.</p>'

    html = '<div class="sow-wbs">'
    for i, node in enumerate(nodes, 1):
        html += _render_wbs_node(node, f'{section_num}.{i}')
    html += '</div>'
    return html


def _render_wbs_node(node: Dict, prefix: str) -> str:
    """Render a single WBS node and its children."""
    name = html_module.escape(node.get('name', ''))
    desc = html_module.escape(node.get('description', ''))
    color = node.get('color', '#3b82f6')
    roles = node.get('roles', [])
    children = node.get('children', [])

    roles_badge = f'<span class="sow-wbs-badge">{len(roles)} role(s)</span>' if roles else ''

    html = f'''
    <div class="sow-wbs-item">
        <div class="sow-wbs-header" style="--wbs-color: {color}">
            <span class="sow-wbs-num">{prefix}</span>
            <span class="sow-wbs-name">{name}</span>
            {roles_badge}
        </div>
        {f'<p class="sow-wbs-desc">{desc}</p>' if desc else ''}
    </div>'''

    if children:
        for j, child in enumerate(children, 1):
            html += _render_wbs_node(child, f'{prefix}.{j}')

    return html


def _extract_standards(statements: List[Dict], documents: List[Dict]) -> set:
    """Extract standards and references from statement text."""
    import re
    standards = set()

    # Common patterns for standards references
    patterns = [
        r'\b(MIL-(?:STD|HDBK|PRF|DTL|SPEC)-[\w-]+)',
        r'\b(DO-\d+\w?)',
        r'\b(SAE\s*(?:AS|ARP|AMS|J)\d+\w?)',
        r'\b(ISO\s*\d+(?:[-:]\d+)*)',
        r'\b(AS\d{4}\w?)',
        r'\b(ANSI[/-]\w+[-.\w]*)',
        r'\b(IEEE\s*\d+(?:\.\d+)*)',
        r'\b(NIST\s*SP\s*\d+-\d+)',
        r'\b(FAR\s*\d+\.\d+)',
        r'\b(DFARS\s*\d+\.\d+)',
        r'\b(NASA-(?:STD|HDBK)-\d+\w?)',
    ]

    combined = '|'.join(patterns)

    for s in statements:
        desc = s.get('description', '') or ''
        matches = re.findall(combined, desc, re.IGNORECASE)
        for m in matches:
            if isinstance(m, tuple):
                for part in m:
                    if part:
                        standards.add(part.strip())
            elif m:
                standards.add(m.strip())

    return standards


def _get_styles() -> str:
    """Return embedded CSS styles for the SOW document."""
    return '''<style>
    :root {
        --aegis-gold: #D6A84A;
        --aegis-amber: #B8743A;
        --text-primary: #1a1a2e;
        --text-secondary: #4a4a68;
        --text-muted: #8888a0;
        --bg-primary: #ffffff;
        --bg-surface: #f8f9fc;
        --bg-elevated: #f0f2f8;
        --border-default: #e2e4eb;
        --accent: #3b82f6;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 11pt;
        line-height: 1.6;
        color: var(--text-primary);
        background: #eef0f4;
    }

    .sow-container {
        max-width: 850px;
        margin: 2rem auto;
        background: var(--bg-primary);
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        border-radius: 4px;
    }

    /* ── Cover ──────────────────────────────── */
    .sow-cover {
        padding: 3rem 3rem 2rem;
        border-bottom: 3px solid var(--aegis-gold);
        text-align: center;
    }

    .sow-cover-brand {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }

    .sow-brand-text {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--aegis-gold);
        letter-spacing: 0.15em;
    }

    .sow-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1.5rem;
        line-height: 1.2;
    }

    .sow-meta-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .sow-meta-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .sow-meta-label {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        margin-bottom: 0.125rem;
    }

    .sow-meta-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .sow-summary-bar {
        display: flex;
        justify-content: center;
        gap: 2rem;
        padding: 1rem 0 0;
        border-top: 1px solid var(--border-default);
        margin-top: 1rem;
    }

    .sow-sum-item {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .sow-sum-num {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--aegis-gold);
    }

    .sow-sum-label {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
    }

    /* ── TOC ───────────────────────────────── */
    .sow-toc {
        padding: 2rem 3rem;
        border-bottom: 1px solid var(--border-default);
        background: var(--bg-surface);
    }

    .sow-toc h2 {
        font-size: 1.125rem;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
    }

    .sow-toc-list {
        list-style: none;
        counter-reset: toc;
    }

    .sow-toc-list li {
        padding: 0.375rem 0;
        border-bottom: 1px dotted var(--border-default);
    }

    .sow-toc-list a {
        color: var(--accent);
        text-decoration: none;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.9rem;
    }

    .sow-toc-list a:hover {
        text-decoration: underline;
    }

    /* ── Sections ──────────────────────────── */
    .sow-section {
        padding: 2rem 3rem;
        border-bottom: 1px solid var(--border-default);
        page-break-inside: avoid;
    }

    .sow-section h2 {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--aegis-gold);
    }

    .sow-section h3 {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin: 1.5rem 0 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .sow-section p {
        margin-bottom: 0.75rem;
    }

    .sow-list {
        margin: 0.75rem 0 0.75rem 1.5rem;
    }

    .sow-list li {
        margin-bottom: 0.375rem;
    }

    .sow-note {
        font-size: 0.85rem;
        color: var(--text-muted);
        font-style: italic;
        margin-top: 0.5rem;
    }

    .sow-more {
        font-style: italic;
        color: var(--text-muted);
    }

    /* ── Tables ────────────────────────────── */
    .sow-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.85rem;
    }

    .sow-table thead {
        background: var(--bg-elevated);
    }

    .sow-table th {
        padding: 0.625rem 0.75rem;
        text-align: left;
        font-weight: 600;
        color: var(--text-secondary);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 2px solid var(--border-default);
    }

    .sow-table td {
        padding: 0.5rem 0.75rem;
        border-bottom: 1px solid var(--border-default);
        vertical-align: top;
    }

    .sow-table tr:hover td {
        background: rgba(59, 130, 246, 0.03);
    }

    .sow-table .num {
        text-align: center;
        color: var(--text-muted);
        width: 40px;
    }

    .sow-table .role-cell {
        font-weight: 500;
        color: var(--aegis-amber);
        white-space: nowrap;
    }

    .sow-table .source-cell {
        font-size: 0.8rem;
        color: var(--text-muted);
        max-width: 150px;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .sow-table .req-desc {
        line-height: 1.5;
    }

    /* ── Directive Badges ──────────────────── */
    .sow-directive {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.125rem 0.375rem;
        border-radius: 3px;
        margin-right: 0.25rem;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }

    .sow-d-shall { background: rgba(239, 68, 68, 0.1); color: #b91c1c; }
    .sow-d-must { background: rgba(234, 88, 12, 0.1); color: #c2410c; }
    .sow-d-will { background: rgba(59, 130, 246, 0.1); color: #1d4ed8; }
    .sow-d-should { background: rgba(34, 197, 94, 0.1); color: #15803d; }
    .sow-d-may { background: rgba(139, 92, 246, 0.1); color: #6d28d9; }

    /* ── Role Cards ───────────────────────── */
    .sow-role-card {
        padding: 1.25rem;
        margin: 1rem 0;
        border: 1px solid var(--border-default);
        border-radius: 6px;
        border-left: 4px solid var(--aegis-gold);
        background: var(--bg-primary);
    }

    .sow-role-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-bottom: 0.5rem;
    }

    .sow-role-header h4 {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .sow-badge {
        display: inline-block;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.125rem 0.5rem;
        border-radius: 10px;
    }

    .sow-badge-deliverable {
        background: rgba(214, 168, 74, 0.15);
        color: var(--aegis-amber);
    }

    .sow-badge-type {
        background: rgba(59, 130, 246, 0.1);
        color: #2563eb;
    }

    .sow-badge-org {
        background: rgba(139, 92, 246, 0.1);
        color: #7c3aed;
    }

    .sow-role-desc {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
    }

    .sow-role-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.375rem;
        margin: 0.5rem 0;
    }

    .sow-func-tag {
        display: inline-block;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.7rem;
        font-weight: 500;
        padding: 0.125rem 0.5rem;
        border-radius: 4px;
        background: color-mix(in srgb, var(--tag-color, #3b82f6) 12%, transparent);
        color: var(--tag-color, #3b82f6);
        border: 1px solid color-mix(in srgb, var(--tag-color, #3b82f6) 25%, transparent);
    }

    .sow-role-stmts, .sow-role-rels {
        margin-top: 0.75rem;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.85rem;
    }

    .sow-role-stmts ul, .sow-role-rels ul {
        margin: 0.375rem 0 0 1.25rem;
    }

    .sow-role-stmts li, .sow-role-rels li {
        margin-bottom: 0.25rem;
        line-height: 1.4;
    }

    .sow-role-rels em {
        color: var(--text-muted);
        font-size: 0.8rem;
    }

    /* ── WBS ──────────────────────────────── */
    .sow-wbs {
        margin: 1rem 0;
    }

    .sow-wbs-item {
        margin-left: 1.5rem;
        margin-bottom: 0.5rem;
    }

    .sow-wbs-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0;
    }

    .sow-wbs-num {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--wbs-color, var(--accent));
        min-width: 3rem;
    }

    .sow-wbs-name {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .sow-wbs-badge {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.7rem;
        color: var(--text-muted);
        background: var(--bg-elevated);
        padding: 0.125rem 0.5rem;
        border-radius: 10px;
    }

    .sow-wbs-desc {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin: 0.125rem 0 0 3.5rem;
    }

    /* ── Footer ───────────────────────────── */
    .sow-footer {
        display: flex;
        justify-content: space-between;
        padding: 1.5rem 3rem;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.75rem;
        color: var(--text-muted);
        border-top: 2px solid var(--aegis-gold);
    }

    /* ── Print Button ─────────────────────── */
    .sow-print-btn {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        padding: 0.75rem 1.25rem;
        background: var(--aegis-gold);
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.875rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(214, 168, 74, 0.4);
        z-index: 1000;
    }

    .sow-print-btn:hover {
        background: var(--aegis-amber);
    }

    /* ── Print Styles ─────────────────────── */
    @media print {
        body { background: white; }
        .sow-container { box-shadow: none; margin: 0; max-width: 100%; }
        .sow-print-btn { display: none; }
        .sow-section { page-break-inside: avoid; }
        .sow-cover { page-break-after: always; }
        .sow-table { font-size: 8pt; }
        .sow-role-card { page-break-inside: avoid; }
    }

    @media (max-width: 900px) {
        .sow-container { margin: 0; border-radius: 0; }
        .sow-cover, .sow-toc, .sow-section, .sow-footer { padding-left: 1.5rem; padding-right: 1.5rem; }
        .sow-title { font-size: 1.5rem; }
        .sow-meta-grid { gap: 1rem; }
    }
    </style>'''
