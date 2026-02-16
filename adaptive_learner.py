"""
Adaptive Learning System v1.0.0
===============================
A unified learning system for AEGIS that tracks user decisions
across all checkers and improves accuracy over time.

This system learns from:
- Role extraction adjudications (accept/reject/edit)
- Acronym decisions (accept/reject/expand)
- Grammar/style decisions (accept/reject)
- Spelling decisions (accept/add to dictionary)
- Custom patterns (user-defined rules)

All learning is 100% offline - uses SQLite for persistence.

Integration Points:
- role_extractor_v3.py: Role confidence boosting
- acronym_checker.py: Acronym pattern learning
- extended_checkers.py: Grammar/style learning
- spell_checker.py: Custom dictionary integration
- technical_dictionary.py: Term validation

Author: AEGIS NLP Enhancement Project
Date: 2026-02-03
"""

import sqlite3
import threading
import logging
import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple, NamedTuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Version
VERSION = '1.0.0'


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class LearningDecision:
    """Represents a single learning decision."""
    decision_type: str  # 'role', 'acronym', 'grammar', 'spelling', 'custom'
    pattern_key: str    # Unique identifier for the pattern
    decision: str       # 'accepted', 'rejected', 'edited', 'added_to_dict'
    original_value: str
    corrected_value: Optional[str] = None
    context: Optional[str] = None
    document_id: Optional[str] = None
    confidence_boost: float = 0.0
    timestamp: Optional[str] = None
    metadata: Optional[Dict] = None


@dataclass
class PatternStats:
    """Statistics for a learned pattern."""
    pattern_key: str
    pattern_type: str
    accept_count: int
    reject_count: int
    edit_count: int
    total_count: int
    confidence: float
    predicted_action: Optional[str]
    last_seen: str
    first_seen: str
    contexts: List[str]


@dataclass
class LearnerStats:
    """Overall learner statistics."""
    total_decisions: int
    role_decisions: int
    acronym_decisions: int
    grammar_decisions: int
    spelling_decisions: int
    custom_decisions: int
    unique_patterns: int
    predictable_patterns: int
    high_confidence_patterns: int
    dictionary_size: int
    learning_rate: float  # Decisions per day
    oldest_decision: Optional[str]
    newest_decision: Optional[str]


# ============================================================
# PATTERN KEY GENERATORS
# ============================================================

def make_role_pattern_key(role_name: str, source: str = '') -> str:
    """
    Create pattern key for role learning.

    Format: "role:{normalized_name}:{source_type}"
    Example: "role:project_manager:table"
    """
    normalized = role_name.lower().strip()
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', '_', normalized)
    source_type = source.lower() if source else 'unknown'
    return f"role:{normalized}:{source_type}"


def make_acronym_pattern_key(acronym: str, expansion: str = '') -> str:
    """
    Create pattern key for acronym learning.

    Format: "acronym:{ACRONYM}:{expansion_hash}"
    """
    acronym_upper = acronym.upper().strip()
    expansion_lower = expansion.lower().strip() if expansion else ''
    expansion_hash = expansion_lower[:20].replace(' ', '_') if expansion_lower else 'noexp'
    return f"acronym:{acronym_upper}:{expansion_hash}"


def make_grammar_pattern_key(category: str, flagged: str, suggestion: str) -> str:
    """
    Create pattern key for grammar/style learning.

    Format: "grammar:{category}:{flagged}:{suggestion}"
    """
    category = category.lower().strip()
    flagged = flagged.lower().strip()[:30]
    suggestion = suggestion.lower().strip()[:30] if suggestion else 'none'
    return f"grammar:{category}:{flagged}->{suggestion}"


def make_spelling_pattern_key(misspelled: str, correction: str) -> str:
    """
    Create pattern key for spelling learning.

    Format: "spelling:{misspelled}:{correction}"
    """
    misspelled = misspelled.lower().strip()
    correction = correction.lower().strip() if correction else 'none'
    return f"spelling:{misspelled}->{correction}"


def make_custom_pattern_key(pattern_type: str, pattern: str) -> str:
    """
    Create pattern key for custom rules.

    Format: "custom:{type}:{pattern_hash}"
    """
    pattern_hash = pattern.lower().strip()[:40].replace(' ', '_')
    return f"custom:{pattern_type}:{pattern_hash}"


# ============================================================
# ADAPTIVE LEARNER CLASS
# ============================================================

class AdaptiveLearner:
    """
    Unified learning system that tracks user decisions and predicts preferences.

    Features:
    - Multi-domain learning (roles, acronyms, grammar, spelling)
    - Confidence boosting based on user feedback
    - Context-aware predictions
    - Export/import for team sharing
    - Automatic cleanup of stale patterns
    - Thread-safe SQLite operations
    """

    # Confidence thresholds
    ACCEPT_THRESHOLD = 0.70  # 70%+ accept -> auto-accept
    REJECT_THRESHOLD = 0.30  # 30%- accept -> auto-reject
    MIN_DECISIONS = 2        # Minimum decisions before prediction
    HIGH_CONFIDENCE = 0.85   # Threshold for "high confidence" patterns

    # Confidence boost values for role extraction
    ROLE_CONFIDENCE_BOOST = {
        'accepted': 0.15,    # Boost confidence by 15% when accepted
        'rejected': -0.20,   # Reduce confidence by 20% when rejected
        'edited': 0.10       # Slight boost for edited (still valid role)
    }

    # Default database path
    DEFAULT_DB_PATH = 'data/adaptive_learning.db'

    def __init__(self, db_path: str = None):
        """
        Initialize the Adaptive Learner.

        Args:
            db_path: Path to SQLite database (default: data/adaptive_learning.db)
        """
        if db_path is None:
            # Use default path relative to this file
            app_dir = Path(__file__).parent
            data_dir = app_dir / 'data'
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / 'adaptive_learning.db')

        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.RLock()
        self._cache = {}
        self._cache_ttl = 300  # 5 minute cache
        self._cache_time = {}

        self._init_database()
        logger.info(f"[AdaptiveLearner] Initialized v{VERSION} with database: {db_path}")

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
            logger.error(f"[AdaptiveLearner] Database error: {e}")
            raise
        finally:
            cursor.close()

    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with self._lock:
            with self._db_cursor() as cursor:
                # Enable WAL mode for better concurrency
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.execute('PRAGMA busy_timeout=5000')
                cursor.execute('PRAGMA synchronous=NORMAL')

                # Main decisions table - stores every decision
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        decision_type TEXT NOT NULL,
                        pattern_key TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        original_value TEXT,
                        corrected_value TEXT,
                        context TEXT,
                        document_id TEXT,
                        confidence_boost REAL DEFAULT 0.0,
                        metadata_json TEXT
                    )
                ''')

                # Aggregated patterns table - statistics for each pattern
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS patterns (
                        pattern_key TEXT PRIMARY KEY,
                        pattern_type TEXT NOT NULL,
                        original_value TEXT,
                        accept_count INTEGER DEFAULT 0,
                        reject_count INTEGER DEFAULT 0,
                        edit_count INTEGER DEFAULT 0,
                        total_count INTEGER DEFAULT 0,
                        confidence REAL DEFAULT 0.5,
                        predicted_action TEXT,
                        first_seen DATETIME,
                        last_seen DATETIME,
                        contexts_json TEXT,
                        metadata_json TEXT
                    )
                ''')

                # Role-specific learning table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS role_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        role_name TEXT NOT NULL,
                        normalized_name TEXT NOT NULL,
                        source_type TEXT,
                        accept_count INTEGER DEFAULT 0,
                        reject_count INTEGER DEFAULT 0,
                        confidence_adjustment REAL DEFAULT 0.0,
                        is_known_valid INTEGER DEFAULT 0,
                        is_known_invalid INTEGER DEFAULT 0,
                        first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        sample_contexts_json TEXT,
                        UNIQUE(normalized_name, source_type)
                    )
                ''')

                # Acronym-specific learning table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS acronym_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        acronym TEXT NOT NULL,
                        expansion TEXT,
                        domain TEXT,
                        accept_count INTEGER DEFAULT 0,
                        reject_count INTEGER DEFAULT 0,
                        is_standard INTEGER DEFAULT 0,
                        is_custom INTEGER DEFAULT 0,
                        first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(acronym, expansion)
                    )
                ''')

                # Context patterns - learns which contexts produce valid/invalid results
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS context_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_type TEXT NOT NULL,
                        context_signature TEXT NOT NULL,
                        valid_count INTEGER DEFAULT 0,
                        invalid_count INTEGER DEFAULT 0,
                        confidence_modifier REAL DEFAULT 0.0,
                        sample_text TEXT,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(pattern_type, context_signature)
                    )
                ''')

                # User preferences and settings
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Custom dictionary - terms user has marked as valid
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS custom_dictionary (
                        term TEXT PRIMARY KEY,
                        term_type TEXT DEFAULT 'word',
                        category TEXT DEFAULT 'custom',
                        added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        source TEXT,
                        notes TEXT
                    )
                ''')

                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_pattern ON decisions(pattern_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_type ON decisions(decision_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_predicted ON patterns(predicted_action)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_role_patterns_name ON role_patterns(normalized_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_acronym_patterns_acr ON acronym_patterns(acronym)')

                logger.info("[AdaptiveLearner] Database tables initialized")

    # ============================================================
    # CORE LEARNING METHODS
    # ============================================================

    def record_decision(self, decision: LearningDecision) -> bool:
        """
        Record a user decision for learning.

        Args:
            decision: LearningDecision object with all decision data

        Returns:
            True if recorded successfully
        """
        if not decision.pattern_key:
            logger.warning("[AdaptiveLearner] Cannot record decision with empty pattern_key")
            return False

        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    # Record individual decision
                    cursor.execute('''
                        INSERT INTO decisions
                        (decision_type, pattern_key, decision, original_value,
                         corrected_value, context, document_id, confidence_boost, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        decision.decision_type,
                        decision.pattern_key,
                        decision.decision,
                        decision.original_value,
                        decision.corrected_value,
                        decision.context,
                        decision.document_id,
                        decision.confidence_boost,
                        json.dumps(decision.metadata) if decision.metadata else None
                    ))

                    # Update aggregated pattern statistics
                    self._update_pattern_stats(cursor, decision)

                    # Update type-specific tables
                    if decision.decision_type == 'role':
                        self._update_role_pattern(cursor, decision)
                    elif decision.decision_type == 'acronym':
                        self._update_acronym_pattern(cursor, decision)

                    # Update context patterns
                    if decision.context:
                        self._update_context_pattern(cursor, decision)

            # Invalidate cache
            self._invalidate_cache(decision.pattern_key)

            logger.info(f"[AdaptiveLearner] Recorded {decision.decision} for {decision.decision_type}: {decision.pattern_key}")
            return True

        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Failed to record decision: {e}")
            return False

    def _update_pattern_stats(self, cursor, decision: LearningDecision) -> None:
        """Update aggregated pattern statistics."""
        now = datetime.now().isoformat()

        # Get existing pattern
        cursor.execute('SELECT * FROM patterns WHERE pattern_key = ?', (decision.pattern_key,))
        existing = cursor.fetchone()

        if existing:
            accept_count = existing['accept_count'] + (1 if decision.decision == 'accepted' else 0)
            reject_count = existing['reject_count'] + (1 if decision.decision == 'rejected' else 0)
            edit_count = existing['edit_count'] + (1 if decision.decision == 'edited' else 0)
            total_count = accept_count + reject_count + edit_count

            # Merge contexts
            contexts = json.loads(existing['contexts_json']) if existing['contexts_json'] else []
            if decision.context and decision.context not in contexts:
                contexts.append(decision.context)
                contexts = contexts[-10:]  # Keep last 10 contexts

            cursor.execute('''
                UPDATE patterns
                SET accept_count = ?, reject_count = ?, edit_count = ?, total_count = ?,
                    last_seen = ?, contexts_json = ?
                WHERE pattern_key = ?
            ''', (accept_count, reject_count, edit_count, total_count, now,
                  json.dumps(contexts), decision.pattern_key))
        else:
            accept_count = 1 if decision.decision == 'accepted' else 0
            reject_count = 1 if decision.decision == 'rejected' else 0
            edit_count = 1 if decision.decision == 'edited' else 0
            total_count = 1
            contexts = [decision.context] if decision.context else []

            cursor.execute('''
                INSERT INTO patterns
                (pattern_key, pattern_type, original_value, accept_count, reject_count,
                 edit_count, total_count, first_seen, last_seen, contexts_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (decision.pattern_key, decision.decision_type, decision.original_value,
                  accept_count, reject_count, edit_count, total_count, now, now,
                  json.dumps(contexts)))

        # Update prediction
        self._update_prediction(cursor, decision.pattern_key, accept_count, reject_count, edit_count)

    def _update_prediction(self, cursor, pattern_key: str,
                          accept_count: int, reject_count: int, edit_count: int) -> None:
        """Update predicted action and confidence for a pattern."""
        total = accept_count + reject_count + edit_count

        if total < self.MIN_DECISIONS:
            predicted_action = None
            confidence = 0.5
        else:
            # Edits count as partial accepts (the role/correction was valid, just needed adjustment)
            effective_accepts = accept_count + (edit_count * 0.5)
            accept_ratio = effective_accepts / total

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

    def _update_role_pattern(self, cursor, decision: LearningDecision) -> None:
        """Update role-specific learning table."""
        # Extract role info from decision
        original = decision.original_value or ''
        normalized = original.lower().strip()
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)

        # Extract source type from pattern key
        parts = decision.pattern_key.split(':')
        source_type = parts[2] if len(parts) > 2 else 'unknown'

        # Get existing
        cursor.execute('''
            SELECT * FROM role_patterns
            WHERE normalized_name = ? AND source_type = ?
        ''', (normalized, source_type))
        existing = cursor.fetchone()

        # Calculate confidence adjustment
        boost = self.ROLE_CONFIDENCE_BOOST.get(decision.decision, 0.0)

        if existing:
            accept_count = existing['accept_count'] + (1 if decision.decision == 'accepted' else 0)
            reject_count = existing['reject_count'] + (1 if decision.decision == 'rejected' else 0)
            conf_adj = existing['confidence_adjustment'] + boost

            # Update known valid/invalid status
            is_known_valid = 1 if accept_count >= 3 and reject_count == 0 else existing['is_known_valid']
            is_known_invalid = 1 if reject_count >= 3 and accept_count == 0 else existing['is_known_invalid']

            # Merge sample contexts
            contexts = json.loads(existing['sample_contexts_json']) if existing['sample_contexts_json'] else []
            if decision.context and decision.context not in contexts:
                contexts.append(decision.context)
                contexts = contexts[-5:]

            cursor.execute('''
                UPDATE role_patterns
                SET accept_count = ?, reject_count = ?, confidence_adjustment = ?,
                    is_known_valid = ?, is_known_invalid = ?, last_seen = ?,
                    sample_contexts_json = ?
                WHERE normalized_name = ? AND source_type = ?
            ''', (accept_count, reject_count, conf_adj, is_known_valid, is_known_invalid,
                  datetime.now().isoformat(), json.dumps(contexts), normalized, source_type))
        else:
            cursor.execute('''
                INSERT INTO role_patterns
                (role_name, normalized_name, source_type, accept_count, reject_count,
                 confidence_adjustment, sample_contexts_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (original, normalized, source_type,
                  1 if decision.decision == 'accepted' else 0,
                  1 if decision.decision == 'rejected' else 0,
                  boost, json.dumps([decision.context]) if decision.context else '[]'))

    def _update_acronym_pattern(self, cursor, decision: LearningDecision) -> None:
        """Update acronym-specific learning table."""
        # Extract acronym and expansion from decision
        original = decision.original_value or ''
        acronym = original.upper().strip()
        expansion = decision.corrected_value or ''

        cursor.execute('''
            SELECT * FROM acronym_patterns
            WHERE acronym = ? AND expansion = ?
        ''', (acronym, expansion))
        existing = cursor.fetchone()

        if existing:
            accept_count = existing['accept_count'] + (1 if decision.decision == 'accepted' else 0)
            reject_count = existing['reject_count'] + (1 if decision.decision == 'rejected' else 0)

            cursor.execute('''
                UPDATE acronym_patterns
                SET accept_count = ?, reject_count = ?, last_seen = ?
                WHERE acronym = ? AND expansion = ?
            ''', (accept_count, reject_count, datetime.now().isoformat(), acronym, expansion))
        else:
            cursor.execute('''
                INSERT INTO acronym_patterns
                (acronym, expansion, accept_count, reject_count)
                VALUES (?, ?, ?, ?)
            ''', (acronym, expansion,
                  1 if decision.decision == 'accepted' else 0,
                  1 if decision.decision == 'rejected' else 0))

    def _update_context_pattern(self, cursor, decision: LearningDecision) -> None:
        """Update context-based learning."""
        # Create a context signature (simplified version of context)
        context = decision.context or ''
        # Create signature from first 50 chars, removing specific values
        signature = re.sub(r'\d+', 'N', context[:50].lower())
        signature = re.sub(r'[^a-z\s]', '', signature).strip()[:30]

        if not signature:
            return

        cursor.execute('''
            SELECT * FROM context_patterns
            WHERE pattern_type = ? AND context_signature = ?
        ''', (decision.decision_type, signature))
        existing = cursor.fetchone()

        is_valid = decision.decision in ('accepted', 'edited')

        if existing:
            valid_count = existing['valid_count'] + (1 if is_valid else 0)
            invalid_count = existing['invalid_count'] + (0 if is_valid else 1)
            total = valid_count + invalid_count

            # Calculate confidence modifier (-0.2 to +0.2)
            if total >= 3:
                ratio = valid_count / total
                conf_mod = (ratio - 0.5) * 0.4  # Scale to -0.2 to +0.2
            else:
                conf_mod = 0.0

            cursor.execute('''
                UPDATE context_patterns
                SET valid_count = ?, invalid_count = ?, confidence_modifier = ?,
                    last_updated = ?
                WHERE pattern_type = ? AND context_signature = ?
            ''', (valid_count, invalid_count, conf_mod, datetime.now().isoformat(),
                  decision.decision_type, signature))
        else:
            cursor.execute('''
                INSERT INTO context_patterns
                (pattern_type, context_signature, valid_count, invalid_count, sample_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (decision.decision_type, signature,
                  1 if is_valid else 0, 0 if is_valid else 1, context[:100]))

    # ============================================================
    # PREDICTION METHODS
    # ============================================================

    def get_prediction(self, pattern_key: str) -> Dict[str, Any]:
        """
        Get prediction for a pattern based on learned data.

        Args:
            pattern_key: The pattern key to look up

        Returns:
            Dict with prediction, confidence, reason, and history
        """
        # Check cache first
        cache_key = f"pred:{pattern_key}"
        if cache_key in self._cache:
            cache_time = self._cache_time.get(cache_key, 0)
            if datetime.now().timestamp() - cache_time < self._cache_ttl:
                return self._cache[cache_key]

        try:
            with self._db_cursor() as cursor:
                cursor.execute('SELECT * FROM patterns WHERE pattern_key = ?', (pattern_key,))
                pattern = cursor.fetchone()

                if not pattern:
                    result = {
                        'prediction': None,
                        'confidence': 0.0,
                        'reason': 'No history for this pattern',
                        'history': None,
                        'pattern_key': pattern_key
                    }
                else:
                    accept_count = pattern['accept_count']
                    reject_count = pattern['reject_count']
                    edit_count = pattern['edit_count']
                    total = pattern['total_count']

                    history = {
                        'accepted': accept_count,
                        'rejected': reject_count,
                        'edited': edit_count,
                        'total': total
                    }

                    if total < self.MIN_DECISIONS:
                        result = {
                            'prediction': None,
                            'confidence': 0.0,
                            'reason': f'Not enough history (need {self.MIN_DECISIONS}+ decisions)',
                            'history': history,
                            'pattern_key': pattern_key
                        }
                    else:
                        predicted = pattern['predicted_action']
                        confidence = pattern['confidence']

                        if predicted == 'accept':
                            reason = f"You accepted this {accept_count} of {total} times"
                        elif predicted == 'reject':
                            reason = f"You rejected this {reject_count} of {total} times"
                        else:
                            reason = f"Mixed history ({accept_count} accepted, {reject_count} rejected, {edit_count} edited)"

                        result = {
                            'prediction': predicted,
                            'confidence': round(confidence, 2),
                            'reason': reason,
                            'history': history,
                            'pattern_key': pattern_key
                        }

                # Cache result
                self._cache[cache_key] = result
                self._cache_time[cache_key] = datetime.now().timestamp()

                return result

        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Prediction error: {e}")
            return {
                'prediction': None,
                'confidence': 0.0,
                'reason': 'Database error',
                'history': None,
                'pattern_key': pattern_key
            }

    def get_role_confidence_boost(self, role_name: str, source_type: str = 'unknown') -> float:
        """
        Get confidence boost for a role based on learning history.

        Args:
            role_name: The role name to check
            source_type: Where the role was found (table, sentence, etc.)

        Returns:
            Float confidence adjustment (-0.2 to +0.2)
        """
        normalized = role_name.lower().strip()
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)

        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT confidence_adjustment, is_known_valid, is_known_invalid
                    FROM role_patterns
                    WHERE normalized_name = ? AND source_type = ?
                ''', (normalized, source_type))
                result = cursor.fetchone()

                if result:
                    if result['is_known_valid']:
                        return 0.20  # Strong boost for known valid
                    elif result['is_known_invalid']:
                        return -0.30  # Strong penalty for known invalid
                    else:
                        # Return learned adjustment, clamped to range
                        return max(-0.20, min(0.20, result['confidence_adjustment']))

                return 0.0

        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Role confidence boost error: {e}")
            return 0.0

    def is_known_valid_role(self, role_name: str) -> bool:
        """Check if a role is known to be valid from learning."""
        normalized = role_name.lower().strip()
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)

        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT 1 FROM role_patterns
                    WHERE normalized_name = ? AND is_known_valid = 1
                ''', (normalized,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def is_known_invalid_role(self, role_name: str) -> bool:
        """Check if a role is known to be invalid from learning."""
        normalized = role_name.lower().strip()
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        normalized = re.sub(r'\s+', '_', normalized)

        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT 1 FROM role_patterns
                    WHERE normalized_name = ? AND is_known_invalid = 1
                ''', (normalized,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def get_context_modifier(self, pattern_type: str, context: str) -> float:
        """
        Get confidence modifier based on context patterns.

        Returns a value between -0.2 and +0.2 based on how well
        this type of context has predicted valid results.
        """
        # Create context signature
        signature = re.sub(r'\d+', 'N', context[:50].lower())
        signature = re.sub(r'[^a-z\s]', '', signature).strip()[:30]

        if not signature:
            return 0.0

        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT confidence_modifier FROM context_patterns
                    WHERE pattern_type = ? AND context_signature = ?
                ''', (pattern_type, signature))
                result = cursor.fetchone()

                if result:
                    return result['confidence_modifier']
                return 0.0

        except sqlite3.Error:
            return 0.0

    # ============================================================
    # CUSTOM DICTIONARY METHODS
    # ============================================================

    def add_to_dictionary(self, term: str, term_type: str = 'word',
                         category: str = 'custom', notes: str = '') -> bool:
        """Add a term to the custom dictionary."""
        if not term or not term.strip():
            return False

        term = term.strip()

        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    cursor.execute('''
                        INSERT OR REPLACE INTO custom_dictionary
                        (term, term_type, category, notes, added_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (term, term_type, category, notes, datetime.now().isoformat()))
            logger.info(f"[AdaptiveLearner] Added to dictionary: {term}")
            return True
        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Add to dictionary error: {e}")
            return False

    def remove_from_dictionary(self, term: str) -> bool:
        """Remove a term from the custom dictionary."""
        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    cursor.execute('DELETE FROM custom_dictionary WHERE term = ?', (term,))
                    if cursor.rowcount > 0:
                        logger.info(f"[AdaptiveLearner] Removed from dictionary: {term}")
                        return True
                    return False
        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Remove from dictionary error: {e}")
            return False

    def is_in_dictionary(self, term: str) -> bool:
        """Check if a term is in the custom dictionary (case-insensitive)."""
        if not term:
            return False
        try:
            with self._db_cursor() as cursor:
                cursor.execute(
                    'SELECT 1 FROM custom_dictionary WHERE LOWER(term) = LOWER(?)',
                    (term.strip(),)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def get_dictionary(self) -> List[Dict[str, Any]]:
        """Get all custom dictionary terms."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('SELECT * FROM custom_dictionary ORDER BY term')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Get dictionary error: {e}")
            return []

    # ============================================================
    # STATISTICS AND REPORTING
    # ============================================================

    def get_statistics(self) -> LearnerStats:
        """Get overall learning statistics."""
        try:
            with self._db_cursor() as cursor:
                # Total decisions
                cursor.execute('SELECT COUNT(*) FROM decisions')
                total_decisions = cursor.fetchone()[0]

                # Decisions by type
                cursor.execute('''
                    SELECT decision_type, COUNT(*) as count
                    FROM decisions GROUP BY decision_type
                ''')
                by_type = {row['decision_type']: row['count'] for row in cursor.fetchall()}

                # Unique patterns
                cursor.execute('SELECT COUNT(*) FROM patterns')
                unique_patterns = cursor.fetchone()[0]

                # Predictable patterns
                cursor.execute('SELECT COUNT(*) FROM patterns WHERE predicted_action IS NOT NULL')
                predictable = cursor.fetchone()[0]

                # High confidence patterns
                cursor.execute(f'SELECT COUNT(*) FROM patterns WHERE confidence >= {self.HIGH_CONFIDENCE}')
                high_conf = cursor.fetchone()[0]

                # Dictionary size
                cursor.execute('SELECT COUNT(*) FROM custom_dictionary')
                dict_size = cursor.fetchone()[0]

                # Date range
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM decisions')
                date_range = cursor.fetchone()
                oldest = date_range[0]
                newest = date_range[1]

                # Learning rate (decisions per day)
                if oldest and newest and total_decisions > 0:
                    try:
                        oldest_dt = datetime.fromisoformat(oldest)
                        newest_dt = datetime.fromisoformat(newest)
                        days = max(1, (newest_dt - oldest_dt).days)
                        learning_rate = total_decisions / days
                    except:
                        learning_rate = 0.0
                else:
                    learning_rate = 0.0

                return LearnerStats(
                    total_decisions=total_decisions,
                    role_decisions=by_type.get('role', 0),
                    acronym_decisions=by_type.get('acronym', 0),
                    grammar_decisions=by_type.get('grammar', 0),
                    spelling_decisions=by_type.get('spelling', 0),
                    custom_decisions=by_type.get('custom', 0),
                    unique_patterns=unique_patterns,
                    predictable_patterns=predictable,
                    high_confidence_patterns=high_conf,
                    dictionary_size=dict_size,
                    learning_rate=round(learning_rate, 2),
                    oldest_decision=oldest,
                    newest_decision=newest
                )

        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Statistics error: {e}")
            return LearnerStats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, None, None)

    def get_patterns_by_type(self, pattern_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get learned patterns of a specific type."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT * FROM patterns
                    WHERE pattern_type = ?
                    ORDER BY total_count DESC, last_seen DESC
                    LIMIT ?
                ''', (pattern_type, limit))
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Get patterns error: {e}")
            return []

    def get_high_confidence_patterns(self, pattern_type: str = None) -> List[Dict[str, Any]]:
        """Get patterns with high confidence predictions."""
        try:
            with self._db_cursor() as cursor:
                if pattern_type:
                    cursor.execute(f'''
                        SELECT * FROM patterns
                        WHERE pattern_type = ? AND confidence >= {self.HIGH_CONFIDENCE}
                        ORDER BY confidence DESC
                    ''', (pattern_type,))
                else:
                    cursor.execute(f'''
                        SELECT * FROM patterns
                        WHERE confidence >= {self.HIGH_CONFIDENCE}
                        ORDER BY confidence DESC
                    ''')
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Get high confidence patterns error: {e}")
            return []

    def get_known_valid_roles(self) -> List[str]:
        """Get list of all known valid roles."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT DISTINCT role_name FROM role_patterns
                    WHERE is_known_valid = 1
                    ORDER BY role_name
                ''')
                return [row['role_name'] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_known_invalid_roles(self) -> List[str]:
        """Get list of all known invalid roles (false positives)."""
        try:
            with self._db_cursor() as cursor:
                cursor.execute('''
                    SELECT DISTINCT role_name FROM role_patterns
                    WHERE is_known_invalid = 1
                    ORDER BY role_name
                ''')
                return [row['role_name'] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    # ============================================================
    # EXPORT/IMPORT FOR TEAM SHARING
    # ============================================================

    def export_data(self, include_decisions: bool = False) -> Dict[str, Any]:
        """
        Export learning data for backup or team sharing.

        Args:
            include_decisions: Whether to include individual decisions (can be large)

        Returns:
            Dict with all exportable data
        """
        try:
            with self._db_cursor() as cursor:
                # Export patterns
                cursor.execute('SELECT * FROM patterns')
                patterns = [dict(row) for row in cursor.fetchall()]

                # Export role patterns
                cursor.execute('SELECT * FROM role_patterns')
                role_patterns = [dict(row) for row in cursor.fetchall()]

                # Export acronym patterns
                cursor.execute('SELECT * FROM acronym_patterns')
                acronym_patterns = [dict(row) for row in cursor.fetchall()]

                # Export context patterns
                cursor.execute('SELECT * FROM context_patterns')
                context_patterns = [dict(row) for row in cursor.fetchall()]

                # Export dictionary
                cursor.execute('SELECT * FROM custom_dictionary')
                dictionary = [dict(row) for row in cursor.fetchall()]

                # Export preferences
                cursor.execute('SELECT * FROM user_preferences')
                preferences = {row['key']: row['value'] for row in cursor.fetchall()}

                export_data = {
                    'version': VERSION,
                    'format': 'twr_adaptive_learning',
                    'exported_at': datetime.now().isoformat(),
                    'patterns': patterns,
                    'role_patterns': role_patterns,
                    'acronym_patterns': acronym_patterns,
                    'context_patterns': context_patterns,
                    'dictionary': dictionary,
                    'preferences': preferences,
                    'statistics': asdict(self.get_statistics())
                }

                # Optionally include decisions
                if include_decisions:
                    cursor.execute('SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 5000')
                    export_data['decisions'] = [dict(row) for row in cursor.fetchall()]

                return export_data

        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Export error: {e}")
            return {}

    def import_data(self, data: Dict[str, Any], merge: bool = True) -> Dict[str, Any]:
        """
        Import learning data from backup or team export.

        Args:
            data: Exported data dict
            merge: If True, merge with existing data. If False, replace.

        Returns:
            Dict with import results
        """
        if not data or data.get('format') != 'twr_adaptive_learning':
            return {'success': False, 'error': 'Invalid import data format'}

        imported = {'patterns': 0, 'role_patterns': 0, 'acronym_patterns': 0,
                   'dictionary': 0, 'context_patterns': 0}

        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    if not merge:
                        # Clear existing data
                        cursor.execute('DELETE FROM patterns')
                        cursor.execute('DELETE FROM role_patterns')
                        cursor.execute('DELETE FROM acronym_patterns')
                        cursor.execute('DELETE FROM context_patterns')
                        cursor.execute('DELETE FROM custom_dictionary')

                    # Import patterns
                    for p in data.get('patterns', []):
                        cursor.execute('''
                            INSERT OR REPLACE INTO patterns
                            (pattern_key, pattern_type, original_value, accept_count, reject_count,
                             edit_count, total_count, confidence, predicted_action, first_seen,
                             last_seen, contexts_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (p['pattern_key'], p['pattern_type'], p.get('original_value'),
                              p.get('accept_count', 0), p.get('reject_count', 0),
                              p.get('edit_count', 0), p.get('total_count', 0),
                              p.get('confidence', 0.5), p.get('predicted_action'),
                              p.get('first_seen'), p.get('last_seen'),
                              p.get('contexts_json')))
                        imported['patterns'] += 1

                    # Import role patterns
                    for r in data.get('role_patterns', []):
                        cursor.execute('''
                            INSERT OR REPLACE INTO role_patterns
                            (role_name, normalized_name, source_type, accept_count, reject_count,
                             confidence_adjustment, is_known_valid, is_known_invalid,
                             first_seen, last_seen, sample_contexts_json)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (r['role_name'], r['normalized_name'], r.get('source_type'),
                              r.get('accept_count', 0), r.get('reject_count', 0),
                              r.get('confidence_adjustment', 0.0),
                              r.get('is_known_valid', 0), r.get('is_known_invalid', 0),
                              r.get('first_seen'), r.get('last_seen'),
                              r.get('sample_contexts_json')))
                        imported['role_patterns'] += 1

                    # Import acronym patterns
                    for a in data.get('acronym_patterns', []):
                        cursor.execute('''
                            INSERT OR REPLACE INTO acronym_patterns
                            (acronym, expansion, domain, accept_count, reject_count,
                             is_standard, is_custom, first_seen, last_seen)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (a['acronym'], a.get('expansion'), a.get('domain'),
                              a.get('accept_count', 0), a.get('reject_count', 0),
                              a.get('is_standard', 0), a.get('is_custom', 0),
                              a.get('first_seen'), a.get('last_seen')))
                        imported['acronym_patterns'] += 1

                    # Import context patterns
                    for c in data.get('context_patterns', []):
                        cursor.execute('''
                            INSERT OR REPLACE INTO context_patterns
                            (pattern_type, context_signature, valid_count, invalid_count,
                             confidence_modifier, sample_text)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (c['pattern_type'], c['context_signature'],
                              c.get('valid_count', 0), c.get('invalid_count', 0),
                              c.get('confidence_modifier', 0.0), c.get('sample_text')))
                        imported['context_patterns'] += 1

                    # Import dictionary
                    for d in data.get('dictionary', []):
                        cursor.execute('''
                            INSERT OR REPLACE INTO custom_dictionary
                            (term, term_type, category, notes)
                            VALUES (?, ?, ?, ?)
                        ''', (d['term'], d.get('term_type', 'word'),
                              d.get('category', 'custom'), d.get('notes', '')))
                        imported['dictionary'] += 1

            # Clear cache
            self._cache.clear()
            self._cache_time.clear()

            logger.info(f"[AdaptiveLearner] Imported: {imported}")
            return {'success': True, 'imported': imported}

        except (sqlite3.Error, KeyError) as e:
            logger.error(f"[AdaptiveLearner] Import error: {e}")
            return {'success': False, 'error': str(e)}

    # ============================================================
    # MAINTENANCE METHODS
    # ============================================================

    def cleanup_stale_patterns(self, days: int = 180) -> int:
        """
        Remove patterns that haven't been seen in a while.

        Args:
            days: Remove patterns older than this many days

        Returns:
            Number of patterns removed
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    cursor.execute('''
                        DELETE FROM patterns
                        WHERE last_seen < ? AND total_count < 5
                    ''', (cutoff,))
                    removed = cursor.rowcount

                    logger.info(f"[AdaptiveLearner] Cleaned up {removed} stale patterns")
                    return removed
        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Cleanup error: {e}")
            return 0

    def reset_learning(self, pattern_types: List[str] = None) -> bool:
        """
        Reset learning data.

        Args:
            pattern_types: List of types to reset (None = all)

        Returns:
            True if successful
        """
        try:
            with self._lock:
                with self._db_cursor() as cursor:
                    if pattern_types:
                        for pt in pattern_types:
                            cursor.execute('DELETE FROM decisions WHERE decision_type = ?', (pt,))
                            cursor.execute('DELETE FROM patterns WHERE pattern_type = ?', (pt,))
                            if pt == 'role':
                                cursor.execute('DELETE FROM role_patterns')
                            elif pt == 'acronym':
                                cursor.execute('DELETE FROM acronym_patterns')
                        logger.info(f"[AdaptiveLearner] Reset learning for: {pattern_types}")
                    else:
                        cursor.execute('DELETE FROM decisions')
                        cursor.execute('DELETE FROM patterns')
                        cursor.execute('DELETE FROM role_patterns')
                        cursor.execute('DELETE FROM acronym_patterns')
                        cursor.execute('DELETE FROM context_patterns')
                        logger.info("[AdaptiveLearner] Reset all learning data")

            self._cache.clear()
            self._cache_time.clear()
            return True

        except sqlite3.Error as e:
            logger.error(f"[AdaptiveLearner] Reset error: {e}")
            return False

    def _invalidate_cache(self, pattern_key: str = None) -> None:
        """Invalidate cache entries."""
        if pattern_key:
            cache_key = f"pred:{pattern_key}"
            self._cache.pop(cache_key, None)
            self._cache_time.pop(cache_key, None)
        else:
            self._cache.clear()
            self._cache_time.clear()


# ============================================================
# SINGLETON INSTANCE
# ============================================================

_learner_instance: Optional[AdaptiveLearner] = None


def get_adaptive_learner(db_path: str = None) -> AdaptiveLearner:
    """Get or create the singleton AdaptiveLearner instance."""
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = AdaptiveLearner(db_path)
    return _learner_instance


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

def record_role_decision(role_name: str, decision: str, source: str = '',
                        context: str = '', document_id: str = None) -> bool:
    """
    Convenience function to record a role adjudication decision.

    Args:
        role_name: The role that was adjudicated
        decision: 'accepted', 'rejected', or 'edited'
        source: Where the role was found (table, sentence, etc.)
        context: The text context where role was found
        document_id: Optional document identifier

    Returns:
        True if recorded successfully
    """
    learner = get_adaptive_learner()
    pattern_key = make_role_pattern_key(role_name, source)

    learning_decision = LearningDecision(
        decision_type='role',
        pattern_key=pattern_key,
        decision=decision,
        original_value=role_name,
        context=context,
        document_id=document_id,
        confidence_boost=AdaptiveLearner.ROLE_CONFIDENCE_BOOST.get(decision, 0.0)
    )

    return learner.record_decision(learning_decision)


def record_acronym_decision(acronym: str, expansion: str, decision: str,
                           context: str = '', document_id: str = None) -> bool:
    """
    Convenience function to record an acronym decision.

    Args:
        acronym: The acronym that was checked
        expansion: The expansion that was suggested
        decision: 'accepted' or 'rejected'
        context: The text context
        document_id: Optional document identifier

    Returns:
        True if recorded successfully
    """
    learner = get_adaptive_learner()
    pattern_key = make_acronym_pattern_key(acronym, expansion)

    learning_decision = LearningDecision(
        decision_type='acronym',
        pattern_key=pattern_key,
        decision=decision,
        original_value=acronym,
        corrected_value=expansion,
        context=context,
        document_id=document_id
    )

    return learner.record_decision(learning_decision)


def record_grammar_decision(category: str, flagged: str, suggestion: str,
                           decision: str, context: str = '') -> bool:
    """
    Convenience function to record a grammar/style decision.

    Args:
        category: The checker category (e.g., 'Passive Voice')
        flagged: The flagged text
        suggestion: The suggested correction
        decision: 'accepted' or 'rejected'
        context: The text context

    Returns:
        True if recorded successfully
    """
    learner = get_adaptive_learner()
    pattern_key = make_grammar_pattern_key(category, flagged, suggestion)

    learning_decision = LearningDecision(
        decision_type='grammar',
        pattern_key=pattern_key,
        decision=decision,
        original_value=flagged,
        corrected_value=suggestion,
        context=context
    )

    return learner.record_decision(learning_decision)


def get_role_boost(role_name: str, source: str = 'unknown') -> float:
    """Get confidence boost for a role based on learning history."""
    learner = get_adaptive_learner()
    return learner.get_role_confidence_boost(role_name, source)


def is_learned_valid_role(role_name: str) -> bool:
    """Check if a role has been learned as valid."""
    learner = get_adaptive_learner()
    return learner.is_known_valid_role(role_name)


def is_learned_invalid_role(role_name: str) -> bool:
    """Check if a role has been learned as invalid (false positive)."""
    learner = get_adaptive_learner()
    return learner.is_known_invalid_role(role_name)
