#!/usr/bin/env python3
"""
AEGIS SIPOC Parser Module
================================================
Parses Nimbus SIPOC (Supplier-Input-Process-Output-Customer) Excel exports
to extract organizational role hierarchies for import into AEGIS.

Nimbus is a business process mapping tool that exports process models as
SIPOC-format Excel spreadsheets. Each row in the export represents an
activity node from the process model, with columns capturing the SIPOC
dimensions plus metadata such as Map Path, Diagram Statements, and
Activity Statements.

This parser supports two modes based on the Map Path column:

**Hierarchy Mode** (when "Roles Hierarchy" map path is found):
  - Resources (Column I) = role inheritance chain. First role inherits
    FROM the 2nd+ roles (inheritance, not supervisory)
  - Suppliers/Customers columns are IGNORED (false positives on hierarchy maps)
  - Column L Org (Diagram Statements) maps to existing function category codes
  - Column M Org (Activity Statements) creates grandchild function tags

**Process Mode** (fallback when no "Roles Hierarchy" map path):
  - All rows processed; multiple resources = co-performers
  - Suppliers = upstream roles, Customers = downstream roles

The parser deduplicates roles across all rows, merges metadata from
multiple occurrences, and produces a structured dict suitable for import
into the AEGIS role dictionary.

Version: 1.0.0 (AEGIS v4.1.0)
"""

import os
import re
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Column indices (0-based) in the SIPOC Excel export
COL_LEVEL = 0               # A - Level (e.g., "1.1.3.2 Draft Copy")
COL_DIAGRAM_TITLE = 1       # B - Diagram Title (org group name)
COL_ACTIVITY_TEXT = 6        # G - Activity Text
COL_RESOURCES = 8            # I - Resources (semicolon-separated role names)
COL_COMMENTARY = 9           # J - Activity Commentary (description text)
COL_DIAGRAM_STATEMENTS = 11  # L - Diagram Statements (newline "Key - Value")
COL_ACTIVITY_STATEMENTS = 12 # M - Activity Statements (newline "Key - Value")
COL_DRILL_DOWN = 14          # O - Contains Drill Down
COL_TASK_TYPE = 15           # P - Task Type
COL_GUID = 16                # Q - GUID (unique identifier for Nimbus diagram node)
COL_MAP_PATH = 17            # R - Map Path (filter key)
COL_SUPPLIERS = 18           # S - Suppliers (semicolon-separated parent names)
COL_CUSTOMERS = 19           # T - Customers (semicolon-separated child names)

# Nimbus web base URL for constructing hyperlinks from GUIDs
# Format: BASE_URL + "." + NODE_GUID
# The root map GUID (ED910D9C5F0C4F8491F8FD10A0C5695B) is the static path for the model.
# Each node GUID is appended after a period to link directly to that diagram.
NIMBUS_BASE_URL = "https://nimbusweb.as.northgrum.com/Nimbus/CtrlWebIsapi.dll/app/diagram/0:ED910D9C5F0C4F8491F8FD10A0C5695B."

# Filter value for Roles Hierarchy rows
ROLES_HIERARCHY_FILTER = "Roles Hierarchy"

# Tool prefix in resource names
TOOL_PREFIX = "[S] "

# Suffix to strip from Level values
LEVEL_SUFFIX_PATTERN = re.compile(r'\s+Draft\s+Copy$', re.IGNORECASE)

# -------------------------------------------------------------------------
# Col L Org → existing function category code mapping
# Maps the descriptive org names from SIPOC Column L (Diagram Statements)
# to the codes already in the function_categories table.
# -------------------------------------------------------------------------
COL_L_ORG_TO_CODE = {
    'T&E':                       'TE',
    'T&E-Flight Test':           'TE-FT',
    'T&E-Instrumentation':       'TE-INST',
    'T&E-Lab Design':            'TE-LD',
    'T&E-Lab Ops':               'TE-LO',
    'T&E-Specialty Test (ST)':   'TE-ST',
    'T&E-System Test Eng':       'TE-STE',
    'T&E-Eng Asset Mgmt (EAM)': 'TE-EAM',
}

# Col M Org values that appear WITHOUT a Col L parent and map to
# existing function category codes (not new grandchildren).
COL_M_ORG_TO_CODE = {
    'Facilities-Planning':       'FAC-PLAN',
    'VE-Controls':               'VE-CTRL',
}


# =============================================================================
# CELL PARSING HELPERS
# =============================================================================

def _clean_cell(value):
    """Return a cleaned string from a cell value, or empty string if None."""
    if value is None:
        return ''
    return str(value).strip()


def _clean_level(raw_level):
    """Strip ' Draft Copy' suffix from level strings like '1.1.3.2 Draft Copy'."""
    level = _clean_cell(raw_level)
    if not level:
        return ''
    return LEVEL_SUFFIX_PATTERN.sub('', level).strip()


def _split_semicolons(value):
    """Split a semicolon-separated cell into a list of stripped, non-empty names."""
    text = _clean_cell(value)
    if not text:
        return []
    return [name.strip() for name in text.split(';') if name.strip()]


def _parse_key_value_pairs(text):
    """Parse newline-separated 'Key - Value' pairs from a cell.

    Returns a list of (key, value) tuples. Lines that do not contain
    ' - ' are skipped.
    """
    raw = _clean_cell(text)
    if not raw:
        return []
    pairs = []
    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Split on first occurrence of ' - '
        sep_idx = line.find(' - ')
        if sep_idx < 0:
            continue
        key = line[:sep_idx].strip()
        val = line[sep_idx + 3:].strip()
        if key:
            pairs.append((key, val))
    return pairs


def _is_tool_name(name):
    """Check if a resource name represents a tool (starts with '[S] ')."""
    return name.startswith(TOOL_PREFIX)


def _strip_tool_prefix(name):
    """Remove the '[S] ' prefix from a tool name."""
    if name.startswith(TOOL_PREFIX):
        return name[len(TOOL_PREFIX):]
    return name


def _normalize_name(name):
    """Lowercase name for case-insensitive dedup lookup."""
    return name.strip().lower()


def _is_truthy(value):
    """Check if a cell value represents a boolean True / 'Yes'."""
    text = _clean_cell(value).lower()
    return text in ('yes', 'true', '1', 'y')


# =============================================================================
# DIAGRAM STATEMENTS (COLUMN L) PARSER
# =============================================================================

def _parse_diagram_statements(cell_value):
    """Parse Column L (Diagram Statements) for org and baselined flags.

    Returns:
        dict with keys: 'org' (str or None), 'baselined' (bool)
    """
    result = {'org': None, 'baselined': False}
    pairs = _parse_key_value_pairs(cell_value)
    for key, val in pairs:
        key_lower = key.lower()
        if key_lower == 'org':
            result['org'] = val
        # Handle both the typo "Baslined" and the correct "Baselined"
        elif key_lower in ('baslined', 'baselined'):
            result['baselined'] = val.lower() in ('yes', 'true', '1', 'y')
    return result


# =============================================================================
# ACTIVITY STATEMENTS (COLUMN M) PARSER
# =============================================================================

def _parse_activity_statements(cell_value):
    """Parse Column M (Activity Statements) for role metadata.

    Returns:
        dict with keys: 'role_type', 'role_disposition', 'orgs' (list), 'urls' (list)
    """
    result = {
        'role_type': None,
        'role_disposition': None,
        'orgs': [],
        'urls': [],
    }
    pairs = _parse_key_value_pairs(cell_value)
    for key, val in pairs:
        key_lower = key.lower().rstrip("'")  # Handle "Org'" apostrophe variant
        if key_lower == 'role type':
            if result['role_type'] is None:
                result['role_type'] = val
        elif key_lower == 'role disposition':
            if result['role_disposition'] is None:
                result['role_disposition'] = val
        elif key_lower == 'org':
            if val and val not in result['orgs']:
                result['orgs'].append(val)
        elif key_lower == 'url':
            if val and val not in result['urls']:
                result['urls'].append(val)
    return result


# =============================================================================
# MAIN PARSER
# =============================================================================

def parse_sipoc_file(filepath):
    """Parse a Nimbus SIPOC Excel file and extract role hierarchy data.

    Filters to rows where Column R (Map Path) contains "Roles Hierarchy",
    then extracts unique roles with hierarchy relationships, metadata,
    and org groupings.

    Args:
        filepath: Path to the .xlsx file.

    Returns:
        dict with keys: 'roles', 'relationships', 'grouping_rows', 'stats'

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid .xlsx or cannot be parsed.
    """
    # Validate file exists
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"SIPOC file not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    if ext != '.xlsx':
        raise ValueError(f"Expected .xlsx file, got '{ext}'")

    try:
        import openpyxl
    except ImportError:
        raise ImportError(
            "openpyxl is required for SIPOC parsing. "
            "Install it with: pip install openpyxl"
        )

    logger.info("Opening SIPOC file: %s", filepath)

    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError(f"Failed to open Excel file: {exc}")

    ws = wb.active
    if ws is None:
        wb.close()
        raise ValueError("Workbook has no active sheet")

    # ------------------------------------------------------------------
    # Pass 1: Collect all rows, auto-detect Roles Hierarchy map path
    # ------------------------------------------------------------------
    total_rows = 0
    all_rows = []
    hierarchy_rows = []

    for row in ws.iter_rows(min_row=2, values_only=True):  # skip header row
        total_rows += 1
        # Ensure row has enough columns
        if len(row) <= COL_MAP_PATH:
            continue
        all_rows.append(row)

    wb.close()

    # Check if "Roles Hierarchy" map path exists in any row
    has_hierarchy_filter = any(
        ROLES_HIERARCHY_FILTER in _clean_cell(row[COL_MAP_PATH])
        for row in all_rows
    )

    # Apply filter or include all rows (auto-fallback)
    if has_hierarchy_filter:
        map_path_used = ROLES_HIERARCHY_FILTER
        for row in all_rows:
            map_path = _clean_cell(row[COL_MAP_PATH])
            if ROLES_HIERARCHY_FILTER in map_path:
                hierarchy_rows.append(row)
    else:
        map_path_used = 'All'
        hierarchy_rows = list(all_rows)

    # Parsing mode: hierarchy uses resource-based inheritance;
    # process mode uses suppliers/customers relationships
    is_hierarchy_mode = has_hierarchy_filter

    logger.info(
        "Read %d total rows, %d match filter (map_path_found=%s, map_path_used=%s, mode=%s)",
        total_rows, len(hierarchy_rows), has_hierarchy_filter, map_path_used,
        'hierarchy' if is_hierarchy_mode else 'process'
    )

    # ------------------------------------------------------------------
    # Pass 2: Categorize rows into role rows vs grouping rows
    # ------------------------------------------------------------------
    role_rows = []
    grouping_rows = []

    for row in hierarchy_rows:
        resources = _clean_cell(row[COL_RESOURCES] if len(row) > COL_RESOURCES else None)
        if resources:
            role_rows.append(row)
        else:
            level = _clean_level(row[COL_LEVEL] if len(row) > COL_LEVEL else None)
            diagram_title = _clean_cell(row[COL_DIAGRAM_TITLE] if len(row) > COL_DIAGRAM_TITLE else None)
            activity_text = _clean_cell(row[COL_ACTIVITY_TEXT] if len(row) > COL_ACTIVITY_TEXT else None)
            grouping_rows.append({
                'level': level,
                'diagram_title': diagram_title,
                'activity_text': activity_text,
            })

    logger.info(
        "Categorized: %d role rows, %d grouping rows",
        len(role_rows), len(grouping_rows)
    )

    # ------------------------------------------------------------------
    # Pass 3: Build deduplicated role registry and relationships
    # ------------------------------------------------------------------
    # roles_map: normalized_name -> role dict
    roles_map = OrderedDict()
    # relationships: list of dicts (deduplicated at end)
    raw_relationships = []

    def _safe_col(row, idx):
        """Safely access a column value from a row tuple."""
        if idx < len(row):
            return row[idx]
        return None

    def _ensure_role(name, is_tool=False):
        """Ensure a role entry exists in the registry. Returns the canonical name.
        Names are stored verbatim (including [S] prefix for tools)."""
        norm = _normalize_name(name)
        if norm not in roles_map:
            roles_map[norm] = {
                'role_name': name,
                'is_tool': is_tool,
                'category': 'Tools & Systems' if is_tool else 'Role',
                'description': '',
                'org_group': '',
                'hierarchy_level': '',
                'role_type': None,
                'role_disposition': None,
                'baselined': False,
                'tracings': [],
                'tags': {
                    'org': [],
                    'urls': [],
                },
                # Function tag hierarchy: Col L = parent, Col M = grandchild under parent
                'function_tags': [],  # list of {'parent': col_l_org, 'child': col_m_org}
                'parents': [],
                'children': [],
                'aliases': [],
                'drill_down': False,
            }
        return roles_map[norm]['role_name']

    for row in role_rows:
        level = _clean_level(_safe_col(row, COL_LEVEL))
        diagram_title = _clean_cell(_safe_col(row, COL_DIAGRAM_TITLE))
        activity_text = _clean_cell(_safe_col(row, COL_ACTIVITY_TEXT))
        resources_raw = _split_semicolons(_safe_col(row, COL_RESOURCES))
        commentary = _clean_cell(_safe_col(row, COL_COMMENTARY))
        drill_down = _is_truthy(_safe_col(row, COL_DRILL_DOWN))
        guid = _clean_cell(_safe_col(row, COL_GUID))
        # Only read Suppliers/Customers in process mode — ignored in hierarchy mode
        if not is_hierarchy_mode:
            suppliers = _split_semicolons(_safe_col(row, COL_SUPPLIERS))
            customers = _split_semicolons(_safe_col(row, COL_CUSTOMERS))
        else:
            suppliers = []
            customers = []

        # Parse statement columns
        diag_stmts = _parse_diagram_statements(_safe_col(row, COL_DIAGRAM_STATEMENTS))
        act_stmts = _parse_activity_statements(_safe_col(row, COL_ACTIVITY_STATEMENTS))

        if not resources_raw:
            continue

        # First resource is primary; others are aliases
        primary_name_raw = resources_raw[0]
        primary_is_tool = _is_tool_name(primary_name_raw)
        primary_name = primary_name_raw  # Keep verbatim (including [S] prefix)

        _ensure_role(primary_name, is_tool=primary_is_tool)
        primary_norm = _normalize_name(primary_name)
        role = roles_map[primary_norm]

        # Merge metadata into the primary role
        if not role['description'] and commentary:
            role['description'] = commentary

        # diagram_title is the Nimbus page name (may be a person's name or role name)
        # Keep as org_group context only — do NOT use as category
        if not role['org_group'] and diagram_title:
            role['org_group'] = diagram_title

        if not role['hierarchy_level'] and level:
            role['hierarchy_level'] = level

        if not role['role_type'] and act_stmts['role_type']:
            role['role_type'] = act_stmts['role_type']

        if not role['role_disposition'] and act_stmts['role_disposition']:
            role['role_disposition'] = act_stmts['role_disposition']

        if diag_stmts['baselined']:
            role['baselined'] = True

        if drill_down:
            role['drill_down'] = True

        # v4.7.3: Build Nimbus tracing hyperlink from Column Q GUID
        # Each row a role appears in has its own GUID → link to that location in the model
        if guid:
            # Level text (Column A) is the clean display title for the link
            link_title = level if level else (activity_text[:60] if activity_text else 'Nimbus Location')
            nimbus_url = NIMBUS_BASE_URL + guid
            tracing_entry = {
                'title': link_title,
                'url': nimbus_url,
                'guid': guid,
            }
            # Avoid duplicate GUIDs for the same role
            existing_guids = {t.get('guid') for t in role['tracings']}
            if guid not in existing_guids:
                role['tracings'].append(tracing_entry)

        # Build function tag hierarchy from Col L (parent) and Col M (grandchild)
        # Col L Org = maps to an existing function category (e.g. "T&E-Flight Test" -> TE-FT)
        # Col M Org = grandchild under the Col L parent (e.g. "Flight Operations (Flt Ops)")
        col_l_org_raw = diag_stmts.get('org')  # single value or None
        col_m_orgs_raw = act_stmts.get('orgs', [])  # list of values

        # Resolve Col L to existing function code
        col_l_code = COL_L_ORG_TO_CODE.get(col_l_org_raw, '') if col_l_org_raw else ''

        if col_l_org_raw or col_m_orgs_raw:
            if col_m_orgs_raw:
                for m_org in col_m_orgs_raw:
                    # Check if Col M maps to an existing code directly
                    m_code = COL_M_ORG_TO_CODE.get(m_org, '')
                    tag_entry = {
                        'parent_name': col_l_org_raw or '',
                        'parent_code': col_l_code,
                        'child_name': m_org,
                        'child_code': m_code,  # empty if needs to be created as grandchild
                    }
                    if tag_entry not in role['function_tags']:
                        role['function_tags'].append(tag_entry)
            elif col_l_org_raw:
                # Col L only, no Col M — assign the parent tag directly
                tag_entry = {
                    'parent_name': col_l_org_raw,
                    'parent_code': col_l_code,
                    'child_name': '',
                    'child_code': '',
                }
                if tag_entry not in role['function_tags']:
                    role['function_tags'].append(tag_entry)

        # Legacy org list (kept for backward compat, but function_tags is authoritative)
        if col_l_org_raw and col_l_org_raw not in role['tags']['org']:
            role['tags']['org'].append(col_l_org_raw)
        for org_val in col_m_orgs_raw:
            if org_val not in role['tags']['org']:
                role['tags']['org'].append(org_val)

        # Merge URLs
        for url_val in act_stmts['urls']:
            if url_val not in role['tags']['urls']:
                role['tags']['urls'].append(url_val)

        # Process secondary resources (positions 1+) — mode-dependent
        if is_hierarchy_mode:
            # MODE A: Roles Hierarchy — resource-based inheritance
            # Primary role (pos 1) INHERITS FROM secondary roles (pos 2+)
            for secondary_raw in resources_raw[1:]:
                secondary_is_tool = _is_tool_name(secondary_raw)
                secondary_name = secondary_raw  # Keep verbatim

                _ensure_role(secondary_name, is_tool=secondary_is_tool)

                if secondary_is_tool:
                    # Tool used by the primary role
                    raw_relationships.append({
                        'source': primary_name,
                        'target': secondary_name,
                        'type': 'uses-tool',
                        'context': activity_text,
                    })
                else:
                    # Primary inherits FROM secondary
                    raw_relationships.append({
                        'source': primary_name,
                        'target': secondary_name,
                        'type': 'inherits-from',
                        'context': activity_text,
                    })
                    # primary's parents = roles it inherits from
                    if secondary_name not in role['parents']:
                        role['parents'].append(secondary_name)
                    # secondary's children = roles that inherit from it
                    secondary_role = roles_map[_normalize_name(secondary_name)]
                    if primary_name not in secondary_role['children']:
                        secondary_role['children'].append(primary_name)
            # Suppliers/Customers IGNORED in hierarchy mode
        else:
            # MODE B: Process maps — co-performers + supplier/customer
            # Multiple roles on an activity = people needed for that step
            for co_raw in resources_raw[1:]:
                co_is_tool = _is_tool_name(co_raw)
                co_name = co_raw  # Keep verbatim

                _ensure_role(co_name, is_tool=co_is_tool)

                if co_is_tool:
                    raw_relationships.append({
                        'source': primary_name,
                        'target': co_name,
                        'type': 'uses-tool',
                        'context': activity_text,
                    })
                else:
                    raw_relationships.append({
                        'source': primary_name,
                        'target': co_name,
                        'type': 'co-performs',
                        'context': activity_text,
                    })

            # Process Suppliers (upstream roles providing inputs)
            for supplier_raw in suppliers:
                supplier_is_tool = _is_tool_name(supplier_raw)
                supplier_name = supplier_raw  # Keep verbatim
                _ensure_role(supplier_name, is_tool=supplier_is_tool)
                raw_relationships.append({
                    'source': supplier_name,
                    'target': primary_name,
                    'type': 'supplies-to',
                    'context': activity_text,
                })

            # Process Customers (downstream roles receiving outputs)
            for customer_raw in customers:
                customer_is_tool = _is_tool_name(customer_raw)
                customer_name = customer_raw  # Keep verbatim
                _ensure_role(customer_name, is_tool=customer_is_tool)
                raw_relationships.append({
                    'source': primary_name,
                    'target': customer_name,
                    'type': 'receives-from',
                    'context': activity_text,
                })

    # ------------------------------------------------------------------
    # Deduplicate relationships
    # ------------------------------------------------------------------
    seen_rels = set()
    relationships = []
    for rel in raw_relationships:
        key = (rel['source'], rel['target'], rel['type'])
        if key not in seen_rels:
            seen_rels.add(key)
            relationships.append(rel)

    # ------------------------------------------------------------------
    # Build final roles list
    # ------------------------------------------------------------------
    roles_list = list(roles_map.values())

    # Compute stats
    unique_tools = sum(1 for r in roles_list if r['is_tool'])
    unique_roles = len(roles_list) - unique_tools
    org_groups = len(set(
        r['org_group'] for r in roles_list
        if r['org_group'] and not r['is_tool']
    ))

    # Collect unique function tag parent→child pairs
    all_tag_pairs = set()
    all_parent_tags = set()
    all_child_tags = set()
    resolved_parent_codes = set()
    resolved_child_codes = set()
    unresolved_children = set()  # Col M values that need new grandchild codes
    for r in roles_list:
        for ft in r.get('function_tags', []):
            p_name = ft.get('parent_name', '')
            p_code = ft.get('parent_code', '')
            c_name = ft.get('child_name', '')
            c_code = ft.get('child_code', '')
            if p_name:
                all_parent_tags.add(p_name)
            if p_code:
                resolved_parent_codes.add(p_code)
            if c_name:
                all_child_tags.add(c_name)
            if c_code:
                resolved_child_codes.add(c_code)
            elif c_name:
                unresolved_children.add((c_name, p_code or p_name))
            all_tag_pairs.add((p_name, c_name))

    roles_with_tags = sum(1 for r in roles_list if r.get('function_tags'))
    roles_with_tracings = sum(1 for r in roles_list if r.get('tracings'))
    total_tracings = sum(len(r.get('tracings', [])) for r in roles_list)

    stats = {
        'total_rows_in_file': total_rows,
        'hierarchy_rows': len(hierarchy_rows),
        'role_rows': len(role_rows),
        'grouping_rows': len(grouping_rows),
        'unique_roles': unique_roles,
        'unique_tools': unique_tools,
        'total_relationships': len(relationships),
        'org_groups': org_groups,
        'unique_parent_tags': len(all_parent_tags),
        'unique_child_tags': len(all_child_tags),
        'unique_tag_pairs': len(all_tag_pairs),
        'roles_with_tags': roles_with_tags,
        'resolved_parent_codes': sorted(resolved_parent_codes),
        'resolved_child_codes': sorted(resolved_child_codes),
        'unresolved_children': sorted([(n, p) for n, p in unresolved_children]),
        'map_path_found': has_hierarchy_filter,
        'map_path_used': map_path_used,
        'parsing_mode': 'hierarchy' if is_hierarchy_mode else 'process',
        'roles_with_tracings': roles_with_tracings,
        'total_tracings': total_tracings,
    }

    logger.info(
        "Parse complete: %d unique roles, %d tools, %d relationships, %d org groups",
        stats['unique_roles'], stats['unique_tools'],
        stats['total_relationships'], stats['org_groups']
    )

    return {
        'roles': roles_list,
        'relationships': relationships,
        'grouping_rows': grouping_rows,
        'stats': stats,
    }


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    import sys
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )

    import tempfile
    test_path = os.path.join(tempfile.gettempdir(), 'Roles-SIPOC.xlsx')
    if len(sys.argv) > 1:
        test_path = sys.argv[1]

    print(f"Parsing SIPOC file: {test_path}")
    print("=" * 60)

    try:
        result = parse_sipoc_file(test_path)
    except (FileNotFoundError, ValueError, ImportError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    stats = result['stats']
    print(f"\n{'STATISTICS':^60}")
    print("-" * 60)
    print(f"  Parsing mode:             {'hierarchy' if stats.get('parsing_mode') == 'hierarchy' else 'process'}")
    print(f"  Map path found:           {stats.get('map_path_found', False)}")
    print(f"  Map path used:            {stats.get('map_path_used', '-')}")
    print(f"  Total rows in file:       {stats['total_rows_in_file']:>6}")
    print(f"  Roles Hierarchy rows:     {stats['hierarchy_rows']:>6}")
    print(f"  Role rows (with data):    {stats['role_rows']:>6}")
    print(f"  Grouping rows (no data):  {stats['grouping_rows']:>6}")
    print(f"  Unique roles:             {stats['unique_roles']:>6}")
    print(f"  Unique tools:             {stats['unique_tools']:>6}")
    print(f"  Total relationships:      {stats['total_relationships']:>6}")
    print(f"  Org groups:               {stats['org_groups']:>6}")
    print(f"  Roles with func tags:     {stats['roles_with_tags']:>6}")
    print(f"  Unique parent tags:       {stats['unique_parent_tags']:>6}")
    print(f"  Unique child tags:        {stats['unique_child_tags']:>6}")

    # Show resolved code mappings
    if stats.get('resolved_parent_codes'):
        print(f"\n{'FUNCTION TAG RESOLUTION':^60}")
        print("-" * 60)
        print("  Col L (Parent) -> Existing Code:")
        for name, code in COL_L_ORG_TO_CODE.items():
            if code in stats['resolved_parent_codes']:
                print(f"    {name:35s} -> {code}")
        if stats.get('resolved_child_codes'):
            print("  Col M (Child) -> Existing Code:")
            for name, code in COL_M_ORG_TO_CODE.items():
                if code in stats['resolved_child_codes']:
                    print(f"    {name:35s} -> {code}")
        if stats.get('unresolved_children'):
            print("  Col M (Child) -> NEW grandchild (to create under parent):")
            for child_name, parent_ref in stats['unresolved_children']:
                print(f"    {child_name:35s} under {parent_ref}")

    print(f"\n{'ROLES':^60}")
    print("-" * 60)
    for r in result['roles']:
        kind = "TOOL" if r['is_tool'] else "ROLE"
        parents = ', '.join(r['parents']) if r['parents'] else '-'
        children = ', '.join(r['children']) if r['children'] else '-'
        print(f"  [{kind}] {r['role_name']}")
        print(f"         Category:    {r['category']}")
        print(f"         Org Group:   {r['org_group'] or '-'}")
        print(f"         Level:       {r['hierarchy_level'] or '-'}")
        print(f"         Role Type:   {r['role_type'] or '-'}")
        print(f"         Disposition: {r['role_disposition'] or '-'}")
        print(f"         Baselined:   {r['baselined']}")
        print(f"         Drill Down:  {r['drill_down']}")
        if r.get('function_tags'):
            for ft in r['function_tags']:
                p_disp = ft.get('parent_code') or ft.get('parent_name') or '?'
                c_disp = ft.get('child_code') or ft.get('child_name') or ''
                if c_disp:
                    print(f"         Func Tag:    {p_disp} > {c_disp}")
                else:
                    print(f"         Func Tag:    {p_disp}")
        if r['tags']['org']:
            print(f"         Org Tags:    {', '.join(r['tags']['org'])}")
        if r['tags']['urls']:
            print(f"         URLs:        {', '.join(r['tags']['urls'])}")
        if r['aliases']:
            print(f"         Aliases:     {', '.join(r['aliases'])}")
        print(f"         Parents:     {parents}")
        print(f"         Children:    {children}")
        if r['description']:
            desc_preview = r['description'][:80]
            if len(r['description']) > 80:
                desc_preview += '...'
            print(f"         Description: {desc_preview}")
        print()

    print(f"{'RELATIONSHIPS':^60}")
    print("-" * 60)
    for rel in result['relationships']:
        ctx = f" ({rel['context'][:40]}...)" if len(rel['context']) > 40 else (f" ({rel['context']})" if rel['context'] else '')
        print(f"  {rel['source']} --[{rel['type']}]--> {rel['target']}{ctx}")

    if result['grouping_rows']:
        print(f"\n{'GROUPING ROWS':^60}")
        print("-" * 60)
        for g in result['grouping_rows']:
            print(f"  [{g['level']}] {g['diagram_title']} - {g['activity_text']}")

    print("\n" + "=" * 60)
    print("Parse complete.")
