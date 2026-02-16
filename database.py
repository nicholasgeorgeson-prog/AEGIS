#!/usr/bin/env python3
"""
AEGIS Database Layer
================================
SQLite-based persistence for:
- Analysis history and trends
- Issue baselines and suppressions
- User configurations
- Role extraction caching

Created by Nicholas Georgeson
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import threading

# Thread-local storage for connections
_local = threading.local()

DATABASE_PATH = Path(__file__).parent / 'data' / 'techwriter.db'
DATABASE_VERSION = 1


def get_connection() -> sqlite3.Connection:
    """Get thread-local database connection."""
    if not hasattr(_local, 'connection') or _local.connection is None:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _local.connection = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
        _local.connection.execute("PRAGMA foreign_keys = ON")
    return _local.connection


@contextmanager
def get_db():
    """Context manager for database operations."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_database():
    """Initialize database schema."""
    with get_db() as conn:
        # Documents table - tracks analyzed documents
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT UNIQUE,
                file_size INTEGER,
                word_count INTEGER,
                paragraph_count INTEGER,
                first_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analysis_count INTEGER DEFAULT 1
            )
        """)
        
        # Analysis history - each analysis run
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                issue_count INTEGER,
                score REAL,
                grade TEXT,
                by_severity TEXT,
                by_category TEXT,
                readability TEXT,
                checkers_used TEXT,
                duration_ms REAL,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Issues - individual issues from analysis
        conn.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                category TEXT,
                severity TEXT,
                message TEXT,
                flagged_text TEXT,
                suggestion TEXT,
                paragraph_index INTEGER,
                start_offset INTEGER,
                end_offset INTEGER,
                FOREIGN KEY (analysis_id) REFERENCES analysis_history(id)
            )
        """)
        
        # Issue baselines - suppressed/accepted issues
        conn.execute("""
            CREATE TABLE IF NOT EXISTS issue_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                issue_hash TEXT UNIQUE,
                category TEXT,
                message TEXT,
                flagged_text TEXT,
                status TEXT DEFAULT 'accepted',
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Roles cache - extracted roles per document
        conn.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                role_name TEXT,
                canonical_name TEXT,
                variants TEXT,
                occurrence_count INTEGER,
                responsibilities TEXT,
                action_types TEXT,
                contexts TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Role relationships - connections between roles
        conn.execute("""
            CREATE TABLE IF NOT EXISTS role_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                source_role TEXT,
                target_role TEXT,
                relationship_type TEXT,
                context TEXT,
                strength REAL DEFAULT 1.0,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # User configurations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Custom word lists (acronyms, forbidden words, etc.)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_type TEXT,
                word TEXT,
                definition TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_hash ON documents(file_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_doc ON analysis_history(document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_issues_analysis ON issues(analysis_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_baseline_doc ON issue_baselines(document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_roles_doc ON roles(document_id)")
        
        # Set version
        conn.execute("INSERT OR REPLACE INTO configurations (key, value) VALUES (?, ?)",
                    ('db_version', str(DATABASE_VERSION)))


def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of file."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def compute_issue_hash(issue: Dict) -> str:
    """Compute hash for issue deduplication."""
    key = f"{issue.get('category', '')}|{issue.get('message', '')}|{issue.get('flagged_text', '')}"
    return hashlib.md5(key.encode()).hexdigest()


class DocumentRepository:
    """Repository for document-related database operations."""
    
    @staticmethod
    def get_or_create(filename: str, filepath: str) -> int:
        """Get existing document or create new one."""
        file_hash = compute_file_hash(filepath)
        file_size = Path(filepath).stat().st_size
        
        with get_db() as conn:
            # Check if exists
            row = conn.execute(
                "SELECT id FROM documents WHERE file_hash = ?", 
                (file_hash,)
            ).fetchone()
            
            if row:
                # Update last analyzed
                conn.execute("""
                    UPDATE documents 
                    SET last_analyzed = CURRENT_TIMESTAMP,
                        analysis_count = analysis_count + 1,
                        filename = ?
                    WHERE id = ?
                """, (filename, row['id']))
                return row['id']
            
            # Create new
            cursor = conn.execute("""
                INSERT INTO documents (filename, file_hash, file_size)
                VALUES (?, ?, ?)
            """, (filename, file_hash, file_size))
            return cursor.lastrowid
    
    @staticmethod
    def update_stats(doc_id: int, word_count: int, paragraph_count: int):
        """Update document statistics."""
        with get_db() as conn:
            conn.execute("""
                UPDATE documents 
                SET word_count = ?, paragraph_count = ?
                WHERE id = ?
            """, (word_count, paragraph_count, doc_id))
    
    @staticmethod
    def get_history(doc_id: int, limit: int = 10) -> List[Dict]:
        """Get analysis history for document."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT id, analyzed_at, issue_count, score, grade,
                       by_severity, by_category, duration_ms
                FROM analysis_history
                WHERE document_id = ?
                ORDER BY analyzed_at DESC
                LIMIT ?
            """, (doc_id, limit)).fetchall()
            
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_all_documents(limit: int = 50) -> List[Dict]:
        """Get all analyzed documents."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT d.*,
                       (SELECT COUNT(*) FROM analysis_history WHERE document_id = d.id) as analyses,
                       (SELECT score FROM analysis_history WHERE document_id = d.id
                        ORDER BY analyzed_at DESC LIMIT 1) as latest_score
                FROM documents d
                ORDER BY last_analyzed DESC
                LIMIT ?
            """, (limit,)).fetchall()

            return [dict(row) for row in rows]

    @staticmethod
    def get_analysis_count(doc_id: int) -> int:
        """Get the number of analyses for a document."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT analysis_count FROM documents WHERE id = ?",
                (doc_id,)
            ).fetchone()
            return row['analysis_count'] if row else 0


class AnalysisRepository:
    """Repository for analysis history operations."""
    
    @staticmethod
    def save_analysis(doc_id: int, results: Dict, duration_ms: float = 0) -> int:
        """Save analysis results."""
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO analysis_history 
                (document_id, issue_count, score, grade, by_severity, 
                 by_category, readability, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                results.get('issue_count', 0),
                results.get('score', 100),
                results.get('grade', 'A'),
                json.dumps(results.get('by_severity', {})),
                json.dumps(results.get('by_category', {})),
                json.dumps(results.get('readability', {})),
                duration_ms
            ))
            analysis_id = cursor.lastrowid
            
            # Save individual issues
            for issue in results.get('issues', []):
                conn.execute("""
                    INSERT INTO issues 
                    (analysis_id, category, severity, message, flagged_text,
                     suggestion, paragraph_index, start_offset, end_offset)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    issue.get('category'),
                    issue.get('severity'),
                    issue.get('message'),
                    issue.get('flagged_text', issue.get('text', '')),
                    issue.get('suggestion'),
                    issue.get('paragraph_index'),
                    issue.get('start_offset'),
                    issue.get('end_offset')
                ))
            
            return analysis_id
    
    @staticmethod
    def get_trends(doc_id: int, days: int = 30) -> Dict:
        """Get trend data for document."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT DATE(analyzed_at) as date, 
                       AVG(score) as avg_score,
                       AVG(issue_count) as avg_issues,
                       COUNT(*) as analysis_count
                FROM analysis_history
                WHERE document_id = ?
                  AND analyzed_at >= datetime('now', ?)
                GROUP BY DATE(analyzed_at)
                ORDER BY date
            """, (doc_id, f'-{days} days')).fetchall()
            
            return {
                'dates': [row['date'] for row in rows],
                'scores': [row['avg_score'] for row in rows],
                'issues': [row['avg_issues'] for row in rows],
                'counts': [row['analysis_count'] for row in rows]
            }
    
    @staticmethod
    def compare_analyses(analysis_id_1: int, analysis_id_2: int) -> Dict:
        """Compare two analyses."""
        with get_db() as conn:
            # Get both analyses
            a1 = conn.execute(
                "SELECT * FROM analysis_history WHERE id = ?", 
                (analysis_id_1,)
            ).fetchone()
            a2 = conn.execute(
                "SELECT * FROM analysis_history WHERE id = ?", 
                (analysis_id_2,)
            ).fetchone()
            
            if not a1 or not a2:
                return {}
            
            # Get issues for both
            issues_1 = set()
            for row in conn.execute(
                "SELECT category, message, flagged_text FROM issues WHERE analysis_id = ?",
                (analysis_id_1,)
            ):
                issues_1.add((row['category'], row['message'], row['flagged_text']))
            
            issues_2 = set()
            for row in conn.execute(
                "SELECT category, message, flagged_text FROM issues WHERE analysis_id = ?",
                (analysis_id_2,)
            ):
                issues_2.add((row['category'], row['message'], row['flagged_text']))
            
            return {
                'analysis_1': dict(a1),
                'analysis_2': dict(a2),
                'new_issues': list(issues_2 - issues_1),
                'resolved_issues': list(issues_1 - issues_2),
                'unchanged_issues': list(issues_1 & issues_2),
                'score_change': (a2['score'] or 0) - (a1['score'] or 0),
                'issue_count_change': (a2['issue_count'] or 0) - (a1['issue_count'] or 0)
            }


class BaselineRepository:
    """Repository for issue baseline/suppression operations."""
    
    @staticmethod
    def add_baseline(doc_id: int, issue: Dict, status: str = 'accepted', 
                     reason: str = '', created_by: str = '') -> bool:
        """Add issue to baseline (suppress it)."""
        issue_hash = compute_issue_hash(issue)
        
        with get_db() as conn:
            try:
                conn.execute("""
                    INSERT INTO issue_baselines 
                    (document_id, issue_hash, category, message, flagged_text,
                     status, reason, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, issue_hash,
                    issue.get('category'),
                    issue.get('message'),
                    issue.get('flagged_text', issue.get('text', '')),
                    status, reason, created_by
                ))
                return True
            except sqlite3.IntegrityError:
                return False
    
    @staticmethod
    def remove_baseline(doc_id: int, issue: Dict) -> bool:
        """Remove issue from baseline."""
        issue_hash = compute_issue_hash(issue)
        
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM issue_baselines WHERE document_id = ? AND issue_hash = ?",
                (doc_id, issue_hash)
            )
            return cursor.rowcount > 0
    
    @staticmethod
    def get_baselines(doc_id: int) -> List[Dict]:
        """Get all baselines for document."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT * FROM issue_baselines WHERE document_id = ?
            """, (doc_id,)).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def is_baselined(doc_id: int, issue: Dict) -> bool:
        """Check if issue is in baseline."""
        issue_hash = compute_issue_hash(issue)
        
        with get_db() as conn:
            row = conn.execute(
                "SELECT 1 FROM issue_baselines WHERE document_id = ? AND issue_hash = ?",
                (doc_id, issue_hash)
            ).fetchone()
            return row is not None
    
    @staticmethod
    def filter_baselined(doc_id: int, issues: List[Dict]) -> List[Dict]:
        """Filter out baselined issues."""
        with get_db() as conn:
            baselined = set()
            for row in conn.execute(
                "SELECT issue_hash FROM issue_baselines WHERE document_id = ?",
                (doc_id,)
            ):
                baselined.add(row['issue_hash'])
            
            return [
                issue for issue in issues 
                if compute_issue_hash(issue) not in baselined
            ]


class RoleRepository:
    """Repository for role extraction data."""
    
    @staticmethod
    def save_roles(doc_id: int, roles: Dict):
        """Save extracted roles."""
        with get_db() as conn:
            # Clear existing roles for this document
            conn.execute("DELETE FROM roles WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM role_relationships WHERE document_id = ?", (doc_id,))
            
            if not roles:
                return
            
            # Save each role
            for role_name, role_data in roles.items():
                if isinstance(role_data, dict):
                    conn.execute("""
                        INSERT INTO roles 
                        (document_id, role_name, canonical_name, variants,
                         occurrence_count, responsibilities, action_types, contexts)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc_id,
                        role_name,
                        role_data.get('canonical_name', role_name),
                        json.dumps(list(role_data.get('variants', []))),
                        role_data.get('count', 1),
                        json.dumps(role_data.get('responsibilities', [])),
                        json.dumps(dict(role_data.get('action_types', {}))),
                        json.dumps(role_data.get('contexts', [])[:10])  # Limit contexts
                    ))
    
    @staticmethod
    def save_relationships(doc_id: int, relationships: List[Dict]):
        """Save role relationships."""
        with get_db() as conn:
            for rel in relationships:
                conn.execute("""
                    INSERT INTO role_relationships
                    (document_id, source_role, target_role, relationship_type, context, strength)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    rel.get('source'),
                    rel.get('target'),
                    rel.get('type', 'interacts_with'),
                    rel.get('context', ''),
                    rel.get('strength', 1.0)
                ))
    
    @staticmethod
    def get_roles(doc_id: int) -> List[Dict]:
        """Get roles for document."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT * FROM roles WHERE document_id = ?
            """, (doc_id,)).fetchall()
            
            results = []
            for row in rows:
                role = dict(row)
                role['variants'] = json.loads(role['variants'] or '[]')
                role['responsibilities'] = json.loads(role['responsibilities'] or '[]')
                role['action_types'] = json.loads(role['action_types'] or '{}')
                role['contexts'] = json.loads(role['contexts'] or '[]')
                results.append(role)
            
            return results
    
    @staticmethod
    def get_relationships(doc_id: int) -> List[Dict]:
        """Get role relationships for document."""
        with get_db() as conn:
            rows = conn.execute("""
                SELECT * FROM role_relationships WHERE document_id = ?
            """, (doc_id,)).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_role_network(doc_id: int) -> Dict:
        """Get role network for visualization."""
        roles = RoleRepository.get_roles(doc_id)
        relationships = RoleRepository.get_relationships(doc_id)
        
        # Build nodes
        nodes = []
        for role in roles:
            nodes.append({
                'id': role['role_name'],
                'label': role['canonical_name'] or role['role_name'],
                'count': role['occurrence_count'],
                'responsibilities': role['responsibilities'][:5],
                'action_types': role['action_types']
            })
        
        # Build edges
        edges = []
        for rel in relationships:
            edges.append({
                'source': rel['source_role'],
                'target': rel['target_role'],
                'type': rel['relationship_type'],
                'strength': rel['strength']
            })
        
        return {'nodes': nodes, 'edges': edges}


class ConfigRepository:
    """Repository for user configurations."""
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get configuration value."""
        with get_db() as conn:
            row = conn.execute(
                "SELECT value FROM configurations WHERE key = ?",
                (key,)
            ).fetchone()
            
            if row:
                try:
                    return json.loads(row['value'])
                except json.JSONDecodeError:
                    return row['value']
            return default
    
    @staticmethod
    def set(key: str, value: Any):
        """Set configuration value."""
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO configurations (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json.dumps(value) if not isinstance(value, str) else value))
    
    @staticmethod
    def get_all() -> Dict:
        """Get all configurations."""
        with get_db() as conn:
            rows = conn.execute("SELECT key, value FROM configurations").fetchall()
            result = {}
            for row in rows:
                try:
                    result[row['key']] = json.loads(row['value'])
                except json.JSONDecodeError:
                    result[row['key']] = row['value']
            return result


class CustomWordRepository:
    """Repository for custom word lists."""
    
    @staticmethod
    def add_word(list_type: str, word: str, definition: str = ''):
        """Add word to custom list."""
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO custom_words (list_type, word, definition)
                VALUES (?, ?, ?)
            """, (list_type, word, definition))
    
    @staticmethod
    def remove_word(list_type: str, word: str):
        """Remove word from custom list."""
        with get_db() as conn:
            conn.execute(
                "DELETE FROM custom_words WHERE list_type = ? AND word = ?",
                (list_type, word)
            )
    
    @staticmethod
    def get_words(list_type: str) -> List[Dict]:
        """Get words from custom list."""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT word, definition FROM custom_words WHERE list_type = ?",
                (list_type,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    @staticmethod
    def get_acronyms() -> Dict[str, str]:
        """Get custom acronyms dictionary."""
        words = CustomWordRepository.get_words('acronym')
        return {w['word']: w['definition'] for w in words}


# Initialize database on import
init_database()
