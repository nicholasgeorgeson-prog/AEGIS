"""
AEGIS Proposal Compare — Project Management

Provides persistent project-based proposal storage using SQLite.
Users can create named projects, add proposals incrementally,
and retrieve comparison history.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

DB_NAME = 'proposal_projects.db'


def _get_db_path():
    """Get the database path relative to the project root."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, DB_NAME)


def _get_connection():
    """Get a SQLite connection with WAL mode for concurrency."""
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the proposal projects database schema."""
    conn = _get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pc_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                status TEXT DEFAULT 'active',
                metadata_json TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS pc_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT DEFAULT '',
                company_name TEXT DEFAULT '',
                proposal_title TEXT DEFAULT '',
                date TEXT DEFAULT '',
                total_amount REAL,
                total_raw TEXT DEFAULT '',
                currency TEXT DEFAULT 'USD',
                page_count INTEGER DEFAULT 0,
                line_item_count INTEGER DEFAULT 0,
                table_count INTEGER DEFAULT 0,
                extraction_notes_json TEXT DEFAULT '[]',
                proposal_data_json TEXT NOT NULL,
                added_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES pc_projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pc_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                proposal_ids_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                notes TEXT DEFAULT '',
                FOREIGN KEY (project_id) REFERENCES pc_projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_pc_proposals_project ON pc_proposals(project_id);
            CREATE INDEX IF NOT EXISTS idx_pc_comparisons_project ON pc_comparisons(project_id);
        """)
        conn.commit()
        logger.info("Proposal projects database initialized")
    except Exception as e:
        logger.error(f"Failed to init proposal projects DB: {e}", exc_info=True)
    finally:
        conn.close()


# ──────────────────────────────────────────
# Project CRUD
# ──────────────────────────────────────────

def create_project(name: str, description: str = '') -> Dict[str, Any]:
    """Create a new proposal comparison project."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO pc_projects (name, description) VALUES (?, ?)",
            (name.strip(), description.strip())
        )
        conn.commit()
        project_id = cursor.lastrowid
        return get_project(project_id)
    finally:
        conn.close()


def get_project(project_id: int) -> Optional[Dict[str, Any]]:
    """Get a single project with its proposal count."""
    conn = _get_connection()
    try:
        row = conn.execute("""
            SELECT p.*,
                   COUNT(pp.id) as proposal_count,
                   COALESCE(SUM(pp.line_item_count), 0) as total_line_items
            FROM pc_projects p
            LEFT JOIN pc_proposals pp ON pp.project_id = p.id
            WHERE p.id = ?
            GROUP BY p.id
        """, (project_id,)).fetchone()
        if not row:
            return None
        return _row_to_project(row)
    finally:
        conn.close()


def list_projects(status: str = 'active') -> List[Dict[str, Any]]:
    """List all projects, optionally filtered by status."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT p.*,
                   COUNT(pp.id) as proposal_count,
                   COALESCE(SUM(pp.line_item_count), 0) as total_line_items
            FROM pc_projects p
            LEFT JOIN pc_proposals pp ON pp.project_id = p.id
            WHERE p.status = ? OR ? = 'all'
            GROUP BY p.id
            ORDER BY p.updated_at DESC
        """, (status, status)).fetchall()
        return [_row_to_project(r) for r in rows]
    finally:
        conn.close()


def update_project(project_id: int, name: str = None, description: str = None,
                   status: str = None) -> Optional[Dict[str, Any]]:
    """Update a project's metadata."""
    conn = _get_connection()
    try:
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name.strip())
        if description is not None:
            updates.append("description = ?")
            params.append(description.strip())
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if not updates:
            return get_project(project_id)
        updates.append("updated_at = datetime('now')")
        params.append(project_id)
        conn.execute(
            f"UPDATE pc_projects SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
        return get_project(project_id)
    finally:
        conn.close()


def delete_project(project_id: int) -> bool:
    """Delete a project and all its proposals/comparisons."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM pc_projects WHERE id = ?", (project_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# ──────────────────────────────────────────
# Proposal management within projects
# ──────────────────────────────────────────

def add_proposal_to_project(project_id: int, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add an extracted proposal to a project."""
    conn = _get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO pc_proposals
            (project_id, filename, file_type, company_name, proposal_title,
             date, total_amount, total_raw, currency, page_count,
             line_item_count, table_count, extraction_notes_json, proposal_data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id,
            proposal_data.get('filename', ''),
            proposal_data.get('file_type', ''),
            proposal_data.get('company_name', ''),
            proposal_data.get('proposal_title', ''),
            proposal_data.get('date', ''),
            proposal_data.get('total_amount'),
            proposal_data.get('total_raw', ''),
            proposal_data.get('currency', 'USD'),
            proposal_data.get('page_count', 0),
            len(proposal_data.get('line_items', [])),
            len(proposal_data.get('tables', [])),
            json.dumps(proposal_data.get('extraction_notes', [])),
            json.dumps(proposal_data),
        ))
        conn.execute(
            "UPDATE pc_projects SET updated_at = datetime('now') WHERE id = ?",
            (project_id,)
        )
        conn.commit()
        return {
            'id': cursor.lastrowid,
            'project_id': project_id,
            'filename': proposal_data.get('filename', ''),
            'company_name': proposal_data.get('company_name', ''),
        }
    finally:
        conn.close()


def get_project_proposals(project_id: int) -> List[Dict[str, Any]]:
    """Get all proposals in a project (metadata only, not full data)."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT id, project_id, filename, file_type, company_name,
                   proposal_title, date, total_amount, total_raw, currency,
                   page_count, line_item_count, table_count,
                   extraction_notes_json, added_at
            FROM pc_proposals
            WHERE project_id = ?
            ORDER BY added_at ASC
        """, (project_id,)).fetchall()
        return [_row_to_proposal_summary(r) for r in rows]
    finally:
        conn.close()


def get_proposal_full_data(proposal_id: int) -> Optional[Dict[str, Any]]:
    """Get the full extracted data for a single proposal."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT proposal_data_json FROM pc_proposals WHERE id = ?",
            (proposal_id,)
        ).fetchone()
        if not row:
            return None
        return json.loads(row['proposal_data_json'])
    finally:
        conn.close()


def remove_proposal_from_project(proposal_id: int) -> bool:
    """Remove a proposal from its project."""
    conn = _get_connection()
    try:
        # Get project_id for update
        row = conn.execute(
            "SELECT project_id FROM pc_proposals WHERE id = ?",
            (proposal_id,)
        ).fetchone()
        if not row:
            return False
        project_id = row['project_id']
        conn.execute("DELETE FROM pc_proposals WHERE id = ?", (proposal_id,))
        conn.execute(
            "UPDATE pc_projects SET updated_at = datetime('now') WHERE id = ?",
            (project_id,)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def update_proposal_data(proposal_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a proposal's extracted data after user edits in the review phase.

    Updates both the full proposal_data_json blob and the summary columns
    (company_name, total_amount, line_item_count, etc.) so they stay in sync.
    Also bumps the parent project's updated_at timestamp.
    """
    conn = _get_connection()
    try:
        # Verify proposal exists and get project_id
        row = conn.execute(
            "SELECT id, project_id FROM pc_proposals WHERE id = ?",
            (proposal_id,)
        ).fetchone()
        if not row:
            return None

        project_id = row['project_id']

        # Extract summary fields from updated data
        company_name = updated_data.get('company_name', '')
        proposal_title = updated_data.get('proposal_title', '')
        date = updated_data.get('date', '')
        total_amount = updated_data.get('total_amount')
        total_raw = updated_data.get('total_raw', '')
        currency = updated_data.get('currency', 'USD')
        line_items = updated_data.get('line_items', [])
        tables = updated_data.get('tables', [])

        conn.execute("""
            UPDATE pc_proposals SET
                company_name = ?,
                proposal_title = ?,
                date = ?,
                total_amount = ?,
                total_raw = ?,
                currency = ?,
                line_item_count = ?,
                table_count = ?,
                proposal_data_json = ?
            WHERE id = ?
        """, (
            company_name,
            proposal_title,
            date,
            total_amount,
            total_raw,
            currency,
            len(line_items),
            len(tables),
            json.dumps(updated_data),
            proposal_id,
        ))

        # Bump parent project updated_at
        conn.execute(
            "UPDATE pc_projects SET updated_at = datetime('now') WHERE id = ?",
            (project_id,)
        )
        conn.commit()

        logger.info(f"Updated proposal {proposal_id} in project {project_id}")
        return {
            'id': proposal_id,
            'project_id': project_id,
            'company_name': company_name,
            'line_item_count': len(line_items),
            'total_amount': total_amount,
        }
    except Exception as e:
        logger.error(f"Failed to update proposal {proposal_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()


def move_proposal(proposal_id: int, new_project_id: int) -> Optional[Dict[str, Any]]:
    """Move a proposal from its current project to a different project.

    Updates both the old and new project's updated_at timestamps.
    Returns the updated proposal summary or None if not found.
    """
    conn = _get_connection()
    try:
        # Get current project_id
        row = conn.execute(
            "SELECT id, project_id, filename, company_name FROM pc_proposals WHERE id = ?",
            (proposal_id,)
        ).fetchone()
        if not row:
            return None

        old_project_id = row['project_id']

        # Verify new project exists
        new_project = conn.execute(
            "SELECT id FROM pc_projects WHERE id = ?",
            (new_project_id,)
        ).fetchone()
        if not new_project:
            raise ValueError(f"Target project {new_project_id} not found")

        # Move the proposal
        conn.execute(
            "UPDATE pc_proposals SET project_id = ? WHERE id = ?",
            (new_project_id, proposal_id)
        )

        # Update both projects' timestamps
        conn.execute(
            "UPDATE pc_projects SET updated_at = datetime('now') WHERE id IN (?, ?)",
            (old_project_id, new_project_id)
        )
        conn.commit()

        logger.info(f"Moved proposal {proposal_id} from project {old_project_id} to {new_project_id}")
        return {
            'id': proposal_id,
            'old_project_id': old_project_id,
            'new_project_id': new_project_id,
            'filename': row['filename'],
            'company_name': row['company_name'],
        }
    except Exception as e:
        logger.error(f"Failed to move proposal {proposal_id}: {e}", exc_info=True)
        raise
    finally:
        conn.close()


def list_comparisons_for_project(project_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """List comparisons for a specific project (same format as list_comparisons but filtered)."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT c.id, c.project_id, c.created_at, c.notes,
                   p.name as project_name
            FROM pc_comparisons c
            LEFT JOIN pc_projects p ON p.id = c.project_id
            WHERE c.project_id = ?
            ORDER BY c.created_at DESC
            LIMIT ?
        """, (project_id, limit)).fetchall()

        results = []
        for row in rows:
            try:
                result_json = conn.execute(
                    "SELECT result_json FROM pc_comparisons WHERE id = ?",
                    (row['id'],)
                ).fetchone()
                result_data = json.loads(result_json['result_json']) if result_json else {}
            except (json.JSONDecodeError, TypeError):
                result_data = {}

            proposals = result_data.get('proposals', [])
            vendor_names = [p.get('company_name') or p.get('filename', '') for p in proposals]
            totals = result_data.get('totals', {})
            total_values = [v for v in totals.values() if v is not None and v > 0]

            results.append({
                'id': row['id'],
                'project_id': row['project_id'],
                'project_name': row['project_name'] or 'Ad-hoc',
                'created_at': row['created_at'],
                'notes': row['notes'] or '',
                'vendor_count': len(proposals),
                'vendor_names': vendor_names,
                'total_spread': (
                    '${:,.0f} - ${:,.0f}'.format(min(total_values), max(total_values))
                    if len(total_values) >= 2 else 'N/A'
                ),
            })

        return results
    finally:
        conn.close()


# ──────────────────────────────────────────
# Comparison history
# ──────────────────────────────────────────

def _get_or_create_adhoc_project() -> int:
    """Get or create the default 'Ad-hoc Comparisons' project for comparisons without a project."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM pc_projects WHERE name = 'Ad-hoc Comparisons' AND status = 'active'"
        ).fetchone()
        if row:
            return row['id']
        cursor = conn.execute(
            "INSERT INTO pc_projects (name, description) VALUES ('Ad-hoc Comparisons', 'Auto-created for comparisons without a specific project')"
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def save_comparison(project_id: int, proposal_ids: List[int],
                    result_data: Dict[str, Any], notes: str = '',
                    proposals_json: Dict[str, Any] = None) -> int:
    """Save a comparison result. If project_id is None/0, uses the ad-hoc project."""
    if not project_id:
        project_id = _get_or_create_adhoc_project()

    conn = _get_connection()
    try:
        # Store proposals alongside result for history re-loading
        save_data = result_data
        if proposals_json:
            save_data = dict(result_data)
            save_data['_proposals_input'] = proposals_json

        cursor = conn.execute("""
            INSERT INTO pc_comparisons (project_id, proposal_ids_json, result_json, notes)
            VALUES (?, ?, ?, ?)
        """, (
            project_id,
            json.dumps(proposal_ids),
            json.dumps(save_data),
            notes,
        ))
        conn.execute(
            "UPDATE pc_projects SET updated_at = datetime('now') WHERE id = ?",
            (project_id,)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def list_comparisons(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent comparisons with summary metadata."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT c.id, c.project_id, c.created_at, c.notes,
                   p.name as project_name
            FROM pc_comparisons c
            LEFT JOIN pc_projects p ON p.id = c.project_id
            ORDER BY c.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        results = []
        for row in rows:
            # Extract summary from result_json
            try:
                result_json = conn.execute(
                    "SELECT result_json FROM pc_comparisons WHERE id = ?",
                    (row['id'],)
                ).fetchone()
                result_data = json.loads(result_json['result_json']) if result_json else {}
            except (json.JSONDecodeError, TypeError):
                result_data = {}

            proposals = result_data.get('proposals', [])
            vendor_names = [p.get('company_name') or p.get('filename', '') for p in proposals]
            totals = result_data.get('totals', {})
            total_values = [v for v in totals.values() if v is not None and v > 0]

            results.append({
                'id': row['id'],
                'project_id': row['project_id'],
                'project_name': row['project_name'] or 'Ad-hoc',
                'created_at': row['created_at'],
                'notes': row['notes'] or '',
                'vendor_count': len(proposals),
                'vendor_names': vendor_names,
                'total_spread': (
                    '${:,.0f} - ${:,.0f}'.format(min(total_values), max(total_values))
                    if len(total_values) >= 2 else 'N/A'
                ),
            })

        return results
    finally:
        conn.close()


def get_comparison(comparison_id: int) -> Optional[Dict[str, Any]]:
    """Get full comparison result_json for re-rendering."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id, project_id, result_json, created_at, notes FROM pc_comparisons WHERE id = ?",
            (comparison_id,)
        ).fetchone()
        if not row:
            return None
        try:
            result_data = json.loads(row['result_json'])
        except (json.JSONDecodeError, TypeError):
            result_data = {}
        return {
            'id': row['id'],
            'project_id': row['project_id'],
            'created_at': row['created_at'],
            'notes': row['notes'] or '',
            'result': result_data,
        }
    finally:
        conn.close()


def delete_comparison(comparison_id: int) -> bool:
    """Delete a saved comparison."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM pc_comparisons WHERE id = ?", (comparison_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# ──────────────────────────────────────────
# Metrics / Analytics aggregation
# ──────────────────────────────────────────

def get_proposal_metrics() -> Dict[str, Any]:
    """Get aggregated metrics for the Metrics & Analytics dashboard."""
    conn = _get_connection()
    try:
        # Project stats
        project_stats = conn.execute("""
            SELECT COUNT(*) as total_projects,
                   SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_projects
            FROM pc_projects
        """).fetchone()

        # Proposal stats
        proposal_stats = conn.execute("""
            SELECT COUNT(*) as total_proposals,
                   COUNT(DISTINCT company_name) as unique_vendors,
                   COALESCE(SUM(line_item_count), 0) as total_line_items,
                   COALESCE(AVG(total_amount), 0) as avg_proposal_value,
                   COALESCE(MIN(total_amount), 0) as min_proposal_value,
                   COALESCE(MAX(total_amount), 0) as max_proposal_value,
                   COALESCE(SUM(total_amount), 0) as total_value_analyzed
            FROM pc_proposals
            WHERE total_amount IS NOT NULL AND total_amount > 0
        """).fetchone()

        # Comparison stats
        comparison_stats = conn.execute("""
            SELECT COUNT(*) as total_comparisons
            FROM pc_comparisons
        """).fetchone()

        # File type distribution
        file_types = conn.execute("""
            SELECT file_type, COUNT(*) as count
            FROM pc_proposals
            GROUP BY file_type
            ORDER BY count DESC
        """).fetchall()

        # Category distribution across all proposals
        category_dist = {}
        rows = conn.execute(
            "SELECT proposal_data_json FROM pc_proposals"
        ).fetchall()
        for row in rows:
            try:
                data = json.loads(row['proposal_data_json'])
                for li in data.get('line_items', []):
                    cat = li.get('category', 'Other')
                    category_dist[cat] = category_dist.get(cat, 0) + 1
            except (json.JSONDecodeError, TypeError):
                continue

        # Recent activity
        recent = conn.execute("""
            SELECT pp.filename, pp.company_name, pp.total_raw,
                   pp.added_at, p.name as project_name
            FROM pc_proposals pp
            JOIN pc_projects p ON p.id = pp.project_id
            ORDER BY pp.added_at DESC
            LIMIT 10
        """).fetchall()

        # Vendor frequency
        vendors = conn.execute("""
            SELECT company_name, COUNT(*) as proposal_count,
                   COALESCE(AVG(total_amount), 0) as avg_amount
            FROM pc_proposals
            WHERE company_name != ''
            GROUP BY company_name
            ORDER BY proposal_count DESC
            LIMIT 20
        """).fetchall()

        return {
            'projects': {
                'total': project_stats['total_projects'] or 0,
                'active': project_stats['active_projects'] or 0,
            },
            'proposals': {
                'total': proposal_stats['total_proposals'] or 0,
                'unique_vendors': proposal_stats['unique_vendors'] or 0,
                'total_line_items': proposal_stats['total_line_items'] or 0,
                'avg_value': round(proposal_stats['avg_proposal_value'] or 0, 2),
                'min_value': round(proposal_stats['min_proposal_value'] or 0, 2),
                'max_value': round(proposal_stats['max_proposal_value'] or 0, 2),
                'total_value_analyzed': round(proposal_stats['total_value_analyzed'] or 0, 2),
            },
            'comparisons': {
                'total': comparison_stats['total_comparisons'] or 0,
            },
            'file_types': {r['file_type']: r['count'] for r in file_types},
            'category_distribution': category_dist,
            'recent_activity': [
                {
                    'filename': r['filename'],
                    'company_name': r['company_name'],
                    'total_raw': r['total_raw'],
                    'added_at': r['added_at'],
                    'project_name': r['project_name'],
                }
                for r in recent
            ],
            'vendors': [
                {
                    'name': r['company_name'],
                    'proposal_count': r['proposal_count'],
                    'avg_amount': round(r['avg_amount'], 2),
                }
                for r in vendors
            ],
        }
    finally:
        conn.close()


# ──────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────

def _row_to_project(row) -> Dict[str, Any]:
    """Convert a database row to a project dict."""
    return {
        'id': row['id'],
        'name': row['name'],
        'description': row['description'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'status': row['status'],
        'proposal_count': row['proposal_count'] if 'proposal_count' in row.keys() else 0,
        'total_line_items': row['total_line_items'] if 'total_line_items' in row.keys() else 0,
    }


def _row_to_proposal_summary(row) -> Dict[str, Any]:
    """Convert a database row to a proposal summary dict."""
    return {
        'id': row['id'],
        'project_id': row['project_id'],
        'filename': row['filename'],
        'file_type': row['file_type'],
        'company_name': row['company_name'],
        'proposal_title': row['proposal_title'],
        'date': row['date'],
        'total_amount': row['total_amount'],
        'total_raw': row['total_raw'],
        'line_item_count': row['line_item_count'],
        'table_count': row['table_count'],
        'added_at': row['added_at'],
        'extraction_notes': json.loads(row['extraction_notes_json'] or '[]'),
    }
