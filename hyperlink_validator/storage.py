"""
Hyperlink Validator Storage Module
==================================
Persistent storage for hyperlink validation exclusions and scan history.

Uses SQLite database (shared with scan_history.db) for persistence.
"""

import sqlite3
import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict


@contextmanager
def db_connection(db_path):
    """Context manager for SQLite operations."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()
    try:
        yield (conn, cursor)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class StoredExclusion:
    """Persistent exclusion rule."""
    id: Optional[int] = None
    pattern: str = ""
    match_type: str = "contains"  # exact, prefix, suffix, contains, regex
    reason: str = ""
    treat_as_valid: bool = True
    created_at: str = ""
    created_by: str = "user"
    is_active: bool = True
    hit_count: int = 0  # How many times this exclusion matched
    last_hit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'pattern': self.pattern,
            'match_type': self.match_type,
            'reason': self.reason,
            'treat_as_valid': self.treat_as_valid,
            'created_at': self.created_at,
            'created_by': self.created_by,
            'is_active': self.is_active,
            'hit_count': self.hit_count,
            'last_hit': self.last_hit
        }

    @classmethod
    def from_row(cls, row: tuple) -> 'StoredExclusion':
        return cls(
            id=row[0],
            pattern=row[1],
            match_type=row[2],
            reason=row[3],
            treat_as_valid=bool(row[4]),
            created_at=row[5],
            created_by=row[6],
            is_active=bool(row[7]),
            hit_count=row[8],
            last_hit=row[9]
        )


@dataclass
class LinkScanRecord:
    """Record of a hyperlink validation scan."""
    id: Optional[int] = None
    scan_time: str = ""
    source_type: str = "paste"  # paste, file, docx, excel
    source_name: str = ""
    total_urls: int = 0
    working: int = 0
    broken: int = 0
    redirect: int = 0
    timeout: int = 0
    blocked: int = 0
    unknown: int = 0
    excluded: int = 0
    validation_mode: str = "validator"
    scan_depth: str = "standard"
    duration_ms: int = 0
    results_json: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'scan_time': self.scan_time,
            'source_type': self.source_type,
            'source_name': self.source_name,
            'total_urls': self.total_urls,
            'working': self.working,
            'broken': self.broken,
            'redirect': self.redirect,
            'timeout': self.timeout,
            'blocked': self.blocked,
            'unknown': self.unknown,
            'excluded': self.excluded,
            'validation_mode': self.validation_mode,
            'scan_depth': self.scan_depth,
            'duration_ms': self.duration_ms
        }

    @classmethod
    def from_row(cls, row: tuple) -> 'LinkScanRecord':
        return cls(
            id=row[0],
            scan_time=row[1],
            source_type=row[2],
            source_name=row[3],
            total_urls=row[4],
            working=row[5],
            broken=row[6],
            redirect=row[7],
            timeout=row[8],
            blocked=row[9],
            unknown=row[10],
            excluded=row[11],
            validation_mode=row[12],
            scan_depth=row[13],
            duration_ms=row[14],
            results_json=row[15] if len(row) > 15 else ""
        )


# =============================================================================
# STORAGE CLASS
# =============================================================================

class HyperlinkValidatorStorage:
    """
    Persistent storage for hyperlink validator data.

    Stores:
    - URL exclusion rules
    - Scan history with results
    - Statistics
    """

    def __init__(self, db_path: str = None):
        """Initialize storage with database path."""
        if db_path is None:
            # Default to app directory
            app_dir = Path(__file__).parent.parent
            db_path = str(app_dir / "scan_history.db")

        self.db_path = db_path
        self._init_tables()

    def connection(self):
        """Get database connection context manager."""
        return db_connection(self.db_path)

    def _init_tables(self):
        """Initialize hyperlink validator tables."""
        with self.connection() as (conn, cursor):
            # Exclusions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hyperlink_exclusions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    match_type TEXT DEFAULT 'contains',
                    reason TEXT,
                    treat_as_valid INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT DEFAULT 'user',
                    is_active INTEGER DEFAULT 1,
                    hit_count INTEGER DEFAULT 0,
                    last_hit TIMESTAMP,
                    UNIQUE(pattern, match_type)
                )
            ''')

            # Create index for faster pattern lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_exclusion_pattern
                ON hyperlink_exclusions(pattern)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_exclusion_active
                ON hyperlink_exclusions(is_active)
            ''')

            # Link scan history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS link_scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_type TEXT DEFAULT 'paste',
                    source_name TEXT,
                    total_urls INTEGER DEFAULT 0,
                    working INTEGER DEFAULT 0,
                    broken INTEGER DEFAULT 0,
                    redirect INTEGER DEFAULT 0,
                    timeout INTEGER DEFAULT 0,
                    blocked INTEGER DEFAULT 0,
                    unknown INTEGER DEFAULT 0,
                    excluded INTEGER DEFAULT 0,
                    validation_mode TEXT DEFAULT 'validator',
                    scan_depth TEXT DEFAULT 'standard',
                    duration_ms INTEGER DEFAULT 0,
                    results_json TEXT
                )
            ''')

            # Create index for time-based queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_link_scan_time
                ON link_scan_history(scan_time DESC)
            ''')

    # =========================================================================
    # EXCLUSION METHODS
    # =========================================================================

    def add_exclusion(
        self,
        pattern: str,
        match_type: str = "contains",
        reason: str = "",
        treat_as_valid: bool = True,
        created_by: str = "user"
    ) -> Optional[int]:
        """
        Add a new exclusion rule.

        Returns the exclusion ID if successful, None if duplicate.
        """
        try:
            with self.connection() as (conn, cursor):
                cursor.execute('''
                    INSERT INTO hyperlink_exclusions
                    (pattern, match_type, reason, treat_as_valid, created_by)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pattern, match_type, reason, int(treat_as_valid), created_by))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate pattern/match_type combination
            return None

    def update_exclusion(
        self,
        exclusion_id: int,
        pattern: str = None,
        match_type: str = None,
        reason: str = None,
        treat_as_valid: bool = None,
        is_active: bool = None
    ) -> bool:
        """Update an existing exclusion rule."""
        updates = []
        params = []

        if pattern is not None:
            updates.append("pattern = ?")
            params.append(pattern)
        if match_type is not None:
            updates.append("match_type = ?")
            params.append(match_type)
        if reason is not None:
            updates.append("reason = ?")
            params.append(reason)
        if treat_as_valid is not None:
            updates.append("treat_as_valid = ?")
            params.append(int(treat_as_valid))
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(int(is_active))

        if not updates:
            return False

        params.append(exclusion_id)

        with self.connection() as (conn, cursor):
            cursor.execute(f'''
                UPDATE hyperlink_exclusions
                SET {", ".join(updates)}
                WHERE id = ?
            ''', params)
            success = cursor.rowcount > 0
        return success

    def delete_exclusion(self, exclusion_id: int) -> bool:
        """Delete an exclusion rule."""
        with self.connection() as (conn, cursor):
            cursor.execute('DELETE FROM hyperlink_exclusions WHERE id = ?', (exclusion_id,))
            success = cursor.rowcount > 0
        return success

    def get_exclusion(self, exclusion_id: int) -> Optional[StoredExclusion]:
        """Get a single exclusion by ID."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT id, pattern, match_type, reason, treat_as_valid,
                       created_at, created_by, is_active, hit_count, last_hit
                FROM hyperlink_exclusions
                WHERE id = ?
            ''', (exclusion_id,))
            row = cursor.fetchone()
        if row:
            return StoredExclusion.from_row(row)
        return None

    def get_all_exclusions(self, active_only: bool = True) -> List[StoredExclusion]:
        """Get all exclusion rules."""
        with self.connection() as (conn, cursor):
            if active_only:
                cursor.execute('''
                    SELECT id, pattern, match_type, reason, treat_as_valid,
                           created_at, created_by, is_active, hit_count, last_hit
                    FROM hyperlink_exclusions
                    WHERE is_active = 1
                    ORDER BY created_at DESC
                ''')
            else:
                cursor.execute('''
                    SELECT id, pattern, match_type, reason, treat_as_valid,
                           created_at, created_by, is_active, hit_count, last_hit
                    FROM hyperlink_exclusions
                    ORDER BY created_at DESC
                ''')
            rows = cursor.fetchall()
        return [StoredExclusion.from_row(row) for row in rows]

    def increment_exclusion_hit(self, exclusion_id: int):
        """Increment hit count for an exclusion."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                UPDATE hyperlink_exclusions
                SET hit_count = hit_count + 1,
                    last_hit = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (exclusion_id,))

    def find_matching_exclusion(self, url: str) -> Optional[StoredExclusion]:
        """Find the first exclusion that matches a URL."""
        exclusions = self.get_all_exclusions(active_only=True)

        for exc in exclusions:
            if self._matches_pattern(url, exc.pattern, exc.match_type):
                return exc
        return None

    def _matches_pattern(self, url: str, pattern: str, match_type: str) -> bool:
        """Check if URL matches an exclusion pattern."""
        import re

        if match_type == 'exact':
            return url == pattern
        elif match_type == 'prefix':
            return url.startswith(pattern)
        elif match_type == 'suffix':
            return url.endswith(pattern) or pattern in url
        elif match_type == 'contains':
            return pattern in url
        elif match_type == 'regex':
            try:
                return bool(re.search(pattern, url, re.IGNORECASE))
            except:
                return False
        return False

    def get_exclusion_stats(self) -> Dict[str, Any]:
        """Get exclusion statistics."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                    SUM(hit_count) as total_hits,
                    MAX(last_hit) as last_hit
                FROM hyperlink_exclusions
            ''')
            row = cursor.fetchone()
        return {
            'total_exclusions': row[0] or 0,
            'active_exclusions': row[1] or 0,
            'total_hits': row[2] or 0,
            'last_hit': row[3]
        }

    # =========================================================================
    # SCAN HISTORY METHODS
    # =========================================================================

    def record_scan(
        self,
        source_type: str,
        source_name: str,
        total_urls: int,
        summary: Dict[str, int],
        validation_mode: str = "validator",
        scan_depth: str = "standard",
        duration_ms: int = 0,
        results: List[Dict] = None
    ) -> int:
        """
        Record a link validation scan.

        Returns the scan ID.
        """
        results_json = json.dumps(results) if results else ""

        with self.connection() as (conn, cursor):
            cursor.execute('''
                INSERT INTO link_scan_history
                (source_type, source_name, total_urls, working, broken, redirect,
                 timeout, blocked, unknown, excluded, validation_mode, scan_depth,
                 duration_ms, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source_type,
                source_name,
                total_urls,
                summary.get('working', 0),
                summary.get('broken', 0),
                summary.get('redirect', 0),
                summary.get('timeout', 0),
                summary.get('blocked', 0),
                summary.get('unknown', 0),
                summary.get('excluded', 0),
                validation_mode,
                scan_depth,
                duration_ms,
                results_json
            ))
            scan_id = cursor.lastrowid
        return scan_id

    def get_scan(self, scan_id: int) -> Optional[LinkScanRecord]:
        """Get a single scan record by ID."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT id, scan_time, source_type, source_name, total_urls,
                       working, broken, redirect, timeout, blocked, unknown,
                       excluded, validation_mode, scan_depth, duration_ms, results_json
                FROM link_scan_history
                WHERE id = ?
            ''', (scan_id,))
            row = cursor.fetchone()
        if row:
            return LinkScanRecord.from_row(row)
        return None

    def get_scan_results(self, scan_id: int) -> List[Dict]:
        """Get detailed results for a scan."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT results_json FROM link_scan_history WHERE id = ?
            ''', (scan_id,))
            row = cursor.fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except:
                return []
        return []

    def get_recent_scans(self, limit: int = 20) -> List[LinkScanRecord]:
        """Get recent scan history."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT id, scan_time, source_type, source_name, total_urls,
                       working, broken, redirect, timeout, blocked, unknown,
                       excluded, validation_mode, scan_depth, duration_ms
                FROM link_scan_history
                ORDER BY scan_time DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
        return [LinkScanRecord.from_row(row) for row in rows]

    def get_scans_by_date_range(
        self,
        start_date: str,
        end_date: str = None
    ) -> List[LinkScanRecord]:
        """Get scans within a date range."""
        with self.connection() as (conn, cursor):
            if end_date:
                cursor.execute('''
                    SELECT id, scan_time, source_type, source_name, total_urls,
                           working, broken, redirect, timeout, blocked, unknown,
                           excluded, validation_mode, scan_depth, duration_ms
                    FROM link_scan_history
                    WHERE scan_time >= ? AND scan_time <= ?
                    ORDER BY scan_time DESC
                ''', (start_date, end_date))
            else:
                cursor.execute('''
                    SELECT id, scan_time, source_type, source_name, total_urls,
                           working, broken, redirect, timeout, blocked, unknown,
                           excluded, validation_mode, scan_depth, duration_ms
                    FROM link_scan_history
                    WHERE scan_time >= ?
                    ORDER BY scan_time DESC
                ''', (start_date,))
            rows = cursor.fetchall()
        return [LinkScanRecord.from_row(row) for row in rows]

    def delete_scan(self, scan_id: int) -> bool:
        """Delete a scan record."""
        with self.connection() as (conn, cursor):
            cursor.execute('DELETE FROM link_scan_history WHERE id = ?', (scan_id,))
            success = cursor.rowcount > 0
        return success

    def get_scan_stats(self) -> Dict[str, Any]:
        """Get overall scan statistics."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                SELECT
                    COUNT(*) as total_scans,
                    SUM(total_urls) as total_urls_scanned,
                    SUM(working) as total_working,
                    SUM(broken) as total_broken,
                    AVG(working * 100.0 / NULLIF(total_urls, 0)) as avg_success_rate,
                    MAX(scan_time) as last_scan
                FROM link_scan_history
            ''')
            row = cursor.fetchone()

            # Get source type breakdown
            cursor.execute('''
                SELECT source_type, COUNT(*) as count
                FROM link_scan_history
                GROUP BY source_type
            ''')
            source_breakdown = {r[0]: r[1] for r in cursor.fetchall()}
        return {
            'total_scans': row[0] or 0,
            'total_urls_scanned': row[1] or 0,
            'total_working': row[2] or 0,
            'total_broken': row[3] or 0,
            'avg_success_rate': round(row[4], 1) if row[4] else 0,
            'last_scan': row[5],
            'by_source': source_breakdown
        }

    def clear_old_scans(self, days_to_keep: int = 90) -> int:
        """Clear scan history older than specified days."""
        with self.connection() as (conn, cursor):
            cursor.execute('''
                DELETE FROM link_scan_history
                WHERE scan_time < datetime('now', ? || ' days')
            ''', (f'-{days_to_keep}',))
            deleted = cursor.rowcount
        return deleted


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_storage_instance: Optional[HyperlinkValidatorStorage] = None


def get_storage() -> HyperlinkValidatorStorage:
    """Get or create the singleton storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = HyperlinkValidatorStorage()
    return _storage_instance
