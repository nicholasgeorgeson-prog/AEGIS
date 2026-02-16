# v3.0.97: Fix Assistant v2 - Rule-Based Learning System
# WP7: Pattern tracking and prediction (NO AI/ML)
"""
Decision Learner - tracks user decisions and predicts preferences.
Uses SQLite for storage. Works completely offline.

This is a rule-based system that:
- Tracks accept/reject decisions for each fix pattern
- Predicts user preferences based on historical frequency
- Maintains a custom dictionary for terms to auto-skip
- Requires NO external API calls or ML models
"""

import sqlite3
import threading
import logging
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_pattern_key(fix: Dict[str, Any]) -> str:
    """
    Create consistent pattern key for matching.
    
    Format: "{category}:{original_lower}→{suggestion_lower}"
    Example: "Spelling:recieve→receive"
    """
    category = fix.get('category', 'Other')
    original = (fix.get('flagged_text') or '').lower().strip()
    suggestion = (fix.get('suggestion') or '').lower().strip()
    return f"{category}:{original}→{suggestion}"


class DecisionLearner:
    """
    Rule-based learning from user decisions.
    Tracks patterns and predicts user preferences.
    Thread-safe SQLite operations.
    """
    
    # Confidence thresholds
    ACCEPT_THRESHOLD = 0.75
    REJECT_THRESHOLD = 0.25
    MIN_DECISIONS = 2
    
    def __init__(self, db_path: str = 'data/decision_patterns.db'):
        """
        Initialize with SQLite database.
        Creates tables if they don't exist.
        """
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_database()
        logger.info(f"[DecisionLearner] Initialized with database: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection
    
    @contextmanager
    def _db_cursor(self):
        """Thread-safe cursor context manager."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"[DecisionLearner] Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def _init_database(self) -> None:
        """Create tables if they don't exist."""
        with self._lock:
            with self._db_cursor() as cursor:
                # v3.0.100: Enable WAL mode for better concurrency (ISSUE-002)
                # WAL provides better concurrent read/write performance
                cursor.execute('PRAGMA journal_mode=WAL')
                # Set busy timeout to 5 seconds to handle concurrent access
                cursor.execute('PRAGMA busy_timeout=5000')
                # Optimize synchronous mode for WAL
                cursor.execute('PRAGMA synchronous=NORMAL')
                logger.info("[DecisionLearner] Database pragmas set: WAL mode, 5s busy timeout")
                
                # User decisions history
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        pattern_key TEXT NOT NULL,
                        category TEXT,
                        original_text TEXT,
                        suggestion_text TEXT,
                        decision TEXT NOT NULL,
                        reviewer_note TEXT,
                        document_id TEXT
                    )
                ''')
                
                # Aggregated patterns
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS patterns (
                        pattern_key TEXT PRIMARY KEY,
                        category TEXT,
                        original_text TEXT,
                        suggestion_text TEXT,
                        accept_count INTEGER DEFAULT 0,
                        reject_count INTEGER DEFAULT 0,
                        last_seen DATETIME,
                        predicted_action TEXT,
                        confidence REAL DEFAULT 0.0
                    )
                ''')
                
                # User's custom dictionary
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_dictionary (
                        term TEXT PRIMARY KEY,
                        category TEXT DEFAULT 'custom',
                        added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                ''')
                
                # Indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_pattern ON decisions(pattern_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_category ON patterns(category)')
                
                logger.info("[DecisionLearner] Database tables initialized")
    
    def record_decision(
        self,
        fix: Dict[str, Any],
        decision: str,
        note: str = '',
        document_id: str = None
    ) -> bool:
        """
        Record a user decision for learning.
        
        Args:
            fix: Dict with flagged_text, suggestion, category, context
            decision: 'accepted' or 'rejected'
            note: Optional reviewer note
            document_id: Optional document identifier
            
        Returns:
            True if recorded successfully
        """
        if decision not in ('accepted', 'rejected'):
            logger.warning(f"[DecisionLearner] Invalid decision: {decision}")
            return False
        
        pattern_key = make_pattern_key(fix)
        category = fix.get('category', 'Other')
        original = fix.get('flagged_text', '')
        suggestion = fix.get('suggestion', '')
        
        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    # Record individual decision
                    cursor.execute('''
                        INSERT INTO decisions 
                        (pattern_key, category, original_text, suggestion_text, decision, reviewer_note, document_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (pattern_key, category, original, suggestion, decision, note, document_id))
                    
                    # Update aggregated pattern
                    cursor.execute('SELECT * FROM patterns WHERE pattern_key = ?', (pattern_key,))
                    existing = cursor.fetchone()
                    
                    now = datetime.now().isoformat()
                    
                    if existing:
                        accept_count = existing['accept_count'] + (1 if decision == 'accepted' else 0)
                        reject_count = existing['reject_count'] + (1 if decision == 'rejected' else 0)
                        
                        cursor.execute('''
                            UPDATE patterns 
                            SET accept_count = ?, reject_count = ?, last_seen = ?
                            WHERE pattern_key = ?
                        ''', (accept_count, reject_count, now, pattern_key))
                    else:
                        accept_count = 1 if decision == 'accepted' else 0
                        reject_count = 1 if decision == 'rejected' else 0
                        
                        cursor.execute('''
                            INSERT INTO patterns 
                            (pattern_key, category, original_text, suggestion_text, accept_count, reject_count, last_seen)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (pattern_key, category, original, suggestion, accept_count, reject_count, now))
                    
                    # Update prediction
                    self._update_prediction(cursor, pattern_key, accept_count, reject_count)
                    
            logger.info(f"[DecisionLearner] Recorded {decision} for pattern: {pattern_key}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Failed to record decision: {e}")
            return False
    
    def _update_prediction(self, cursor, pattern_key: str, accept_count: int, reject_count: int) -> None:
        """Update the predicted action and confidence for a pattern."""
        total = accept_count + reject_count
        
        if total < self.MIN_DECISIONS:
            predicted_action = None
            confidence = 0.0
        else:
            accept_ratio = accept_count / total
            if accept_ratio >= self.ACCEPT_THRESHOLD:
                predicted_action = 'accept'
                confidence = accept_ratio
            elif accept_ratio <= self.REJECT_THRESHOLD:
                predicted_action = 'reject'
                confidence = 1 - accept_ratio
            else:
                predicted_action = None
                confidence = 0.5
        
        cursor.execute('''
            UPDATE patterns SET predicted_action = ?, confidence = ?
            WHERE pattern_key = ?
        ''', (predicted_action, confidence, pattern_key))
    
    def get_prediction(self, fix: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get prediction for a fix based on learned patterns.
        
        Returns:
            Dict with prediction, confidence, reason, and history
        """
        flagged_text = fix.get('flagged_text', '')
        
        # Check custom dictionary first
        if self.is_in_dictionary(flagged_text):
            return {
                'prediction': 'reject',
                'confidence': 1.0,
                'reason': 'Term is in your custom dictionary',
                'history': None
            }
        
        pattern_key = make_pattern_key(fix)
        
        try:
            with self._db_cursor() as cursor:
                cursor.execute('SELECT * FROM patterns WHERE pattern_key = ?', (pattern_key,))
                pattern = cursor.fetchone()
                
                if not pattern:
                    return {
                        'prediction': None,
                        'confidence': 0.0,
                        'reason': 'No history for this pattern',
                        'history': None
                    }
                
                accept_count = pattern['accept_count']
                reject_count = pattern['reject_count']
                total = accept_count + reject_count
                
                history = {
                    'accepted': accept_count,
                    'rejected': reject_count,
                    'total': total
                }
                
                if total < self.MIN_DECISIONS:
                    return {
                        'prediction': None,
                        'confidence': 0.0,
                        'reason': f'Not enough history (need {self.MIN_DECISIONS}+ decisions)',
                        'history': history
                    }
                
                accept_ratio = accept_count / total
                
                if accept_ratio >= self.ACCEPT_THRESHOLD:
                    return {
                        'prediction': 'accept',
                        'confidence': round(accept_ratio, 2),
                        'reason': f"You accepted this {accept_count} of {total} times",
                        'history': history
                    }
                elif accept_ratio <= self.REJECT_THRESHOLD:
                    return {
                        'prediction': 'reject',
                        'confidence': round(1 - accept_ratio, 2),
                        'reason': f"You rejected this {reject_count} of {total} times",
                        'history': history
                    }
                else:
                    return {
                        'prediction': None,
                        'confidence': 0.5,
                        'reason': f"Mixed history ({accept_count} accepted, {reject_count} rejected)",
                        'history': history
                    }
                    
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Prediction error: {e}")
            return {
                'prediction': None,
                'confidence': 0.0,
                'reason': 'Database error',
                'history': None
            }
    
    def get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all learned patterns with statistics."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM patterns 
                    ORDER BY (accept_count + reject_count) DESC, last_seen DESC
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Get patterns error: {e}")
            return []
    
    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get patterns for a specific category."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM patterns WHERE category = ?
                    ORDER BY (accept_count + reject_count) DESC
                ''', (category,))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Get patterns by category error: {e}")
            return []
    
    def add_to_dictionary(self, term: str, category: str = 'custom', notes: str = '') -> bool:
        """Add term to user's custom dictionary."""
        if not term or not term.strip():
            return False
        
        term = term.strip()
        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    cursor.execute('''
                        INSERT OR REPLACE INTO user_dictionary (term, category, notes)
                        VALUES (?, ?, ?)
                    ''', (term, category, notes))
            logger.info(f"[DecisionLearner] Added to dictionary: {term}")
            return True
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Add to dictionary error: {e}")
            return False
    
    def remove_from_dictionary(self, term: str) -> bool:
        """Remove term from custom dictionary."""
        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    cursor.execute('DELETE FROM user_dictionary WHERE term = ?', (term,))
                    if cursor.rowcount > 0:
                        logger.info(f"[DecisionLearner] Removed from dictionary: {term}")
                        return True
                    return False
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Remove from dictionary error: {e}")
            return False
    
    def get_dictionary(self) -> List[Dict[str, Any]]:
        """Get all custom dictionary terms."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('SELECT * FROM user_dictionary ORDER BY term')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Get dictionary error: {e}")
            return []
    
    def is_in_dictionary(self, term: str) -> bool:
        """Check if term is in custom dictionary (case-insensitive)."""
        if not term:
            return False
        try:
            with self._db_cursor() as cursor:
                cursor.execute(
                    'SELECT 1 FROM user_dictionary WHERE LOWER(term) = LOWER(?)',
                    (term.strip(),)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Dictionary check error: {e}")
            return False
    
    def clear_patterns(self) -> bool:
        """Reset all learned patterns (keep dictionary)."""
        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    cursor.execute('DELETE FROM decisions')
                    cursor.execute('DELETE FROM patterns')
            logger.info("[DecisionLearner] All patterns cleared")
            return True
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Clear patterns error: {e}")
            return False
    
    def export_data(self) -> Dict[str, Any]:
        """Export all learning data for backup."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('SELECT * FROM patterns')
                patterns = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('SELECT * FROM user_dictionary')
                dictionary = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 1000')
                recent_decisions = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'version': '3.0.97',
                    'exported_at': datetime.now().isoformat(),
                    'patterns': patterns,
                    'dictionary': dictionary,
                    'recent_decisions': recent_decisions
                }
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Export error: {e}")
            return {}
    
    def import_data(self, data: Dict[str, Any]) -> bool:
        """Import learning data from backup."""
        if not data or 'patterns' not in data:
            logger.warning("[DecisionLearner] Invalid import data")
            return False
        
        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    # Import patterns
                    for p in data.get('patterns', []):
                        cursor.execute('''
                            INSERT OR REPLACE INTO patterns 
                            (pattern_key, category, original_text, suggestion_text, 
                             accept_count, reject_count, last_seen, predicted_action, confidence)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            p['pattern_key'], p.get('category'), p.get('original_text'),
                            p.get('suggestion_text'), p.get('accept_count', 0),
                            p.get('reject_count', 0), p.get('last_seen'),
                            p.get('predicted_action'), p.get('confidence', 0.0)
                        ))
                    
                    # Import dictionary
                    for d in data.get('dictionary', []):
                        cursor.execute('''
                            INSERT OR REPLACE INTO user_dictionary (term, category, notes)
                            VALUES (?, ?, ?)
                        ''', (d['term'], d.get('category', 'custom'), d.get('notes', '')))
            
            logger.info(f"[DecisionLearner] Imported {len(data.get('patterns', []))} patterns, "
                       f"{len(data.get('dictionary', []))} dictionary terms")
            return True
            
        except (sqlite3.Error, KeyError) as e:
            logger.error(f"[DecisionLearner] Import error: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall learning statistics."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('SELECT COUNT(*) as count FROM decisions')
                total_decisions = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM patterns')
                total_patterns = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM patterns WHERE predicted_action IS NOT NULL')
                predictable = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM user_dictionary')
                dict_size = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT category, COUNT(*) as count FROM patterns 
                    GROUP BY category ORDER BY count DESC
                ''')
                by_category = {row['category']: row['count'] for row in cursor.fetchall()}
                
                return {
                    'total_decisions': total_decisions,
                    'unique_patterns': total_patterns,
                    'predictable_patterns': predictable,
                    'dictionary_size': dict_size,
                    'patterns_by_category': by_category
                }
        except sqlite3.Error as e:
            logger.error(f"[DecisionLearner] Statistics error: {e}")
            return {}


# Singleton instance for Flask app
_learner_instance: Optional[DecisionLearner] = None


def get_learner(db_path: str = 'data/decision_patterns.db') -> DecisionLearner:
    """Get or create the singleton DecisionLearner instance."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = DecisionLearner(db_path)
    return _learner_instance
