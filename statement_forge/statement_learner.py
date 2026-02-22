"""
AEGIS Statement Learner — learns from user edits to extracted statements.

Tracks patterns from:
1. Directive corrections — when users change detected directives (should→shall)
2. Role assignments — when users consistently assign roles to certain statement types
3. Description edits — when users correct misidentified statement descriptions
4. Deletion patterns — when users consistently delete certain extraction artifacts

All data stays in statement_patterns.json on disk, never uploaded.

Author: AEGIS v5.9.50
"""

import json
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PATTERNS_FILE = os.path.join(os.path.dirname(__file__), 'statement_patterns.json')

# Module-level cache
_learned_patterns = None


def _is_learning_enabled():
    """Check if learning is enabled via config.json (v5.9.52)."""
    try:
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f).get('learning_enabled', True)
    except Exception:
        pass
    return True


def load_patterns() -> dict:
    """Load learned statement patterns from local JSON file."""
    if os.path.exists(PATTERNS_FILE):
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and '_meta' in data:
                    return data
        except Exception as e:
            logger.warning(f'[AEGIS StatementLearner] Failed to load {PATTERNS_FILE}: {e}')
    return _empty_patterns()


def save_patterns(patterns: dict):
    """Save learned patterns to local JSON file (atomic write)."""
    try:
        patterns['_meta']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        tmp_path = PATTERNS_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, PATTERNS_FILE)
        logger.info(f'[AEGIS StatementLearner] Saved {_count_patterns(patterns)} patterns')
    except Exception as e:
        logger.error(f'[AEGIS StatementLearner] Failed to save patterns: {e}')
        try:
            tmp_path = PATTERNS_FILE + '.tmp'
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def reload_learned_patterns():
    """Clear module-level cache so next access loads fresh from disk."""
    global _learned_patterns
    _learned_patterns = None


def get_learned_patterns() -> dict:
    """Get cached learned patterns (loads from disk on first call)."""
    global _learned_patterns
    if _learned_patterns is None:
        _learned_patterns = load_patterns()
    return _learned_patterns


# ──────────────────────────────────────────────
# Learning functions — called after user edits
# ──────────────────────────────────────────────

def learn_from_statement_edits(original_statements: list, edited_statements: list):
    """Compare original extracted statements to user-edited versions, learn patterns.

    Args:
        original_statements: List of statement dicts from original extraction
        edited_statements: List of statement dicts after user editing
    """
    if not original_statements or not edited_statements or not _is_learning_enabled():
        return

    patterns = load_patterns()
    corrections = 0

    # Build lookup by statement ID
    orig_by_id = {s.get('id', ''): s for s in original_statements if s.get('id')}
    edited_by_id = {s.get('id', ''): s for s in edited_statements if s.get('id')}

    # Find deleted statements (in original but not in edited)
    deleted_ids = set(orig_by_id.keys()) - set(edited_by_id.keys())
    for did in deleted_ids:
        orig = orig_by_id[did]
        desc = orig.get('description', '').strip()
        directive = orig.get('directive', '').strip()
        if desc and len(desc) < 200:
            # Learn deletion patterns — extract first few significant words
            words = re.findall(r'\b\w{4,}\b', desc.lower())
            keyword = ' '.join(words[:5])
            if keyword and len(keyword) >= 8:
                _add_or_increment(patterns, 'deletion_patterns',
                                  'keyword', keyword,
                                  {'directive': directive,
                                   'description_preview': desc[:80]})
                corrections += 1

    # Find edited statements
    for sid, edited in edited_by_id.items():
        orig = orig_by_id.get(sid)
        if not orig:
            continue

        # Learn directive corrections
        orig_directive = orig.get('directive', '').strip().lower()
        edit_directive = edited.get('directive', '').strip().lower()
        if orig_directive and edit_directive and orig_directive != edit_directive:
            # Extract context words from description for pattern matching
            desc = edited.get('description', '').strip()
            context_words = _extract_context_words(desc)

            _add_or_increment(patterns, 'directive_corrections',
                              'correction_key', f"{orig_directive}→{edit_directive}",
                              {'from_directive': orig_directive,
                               'to_directive': edit_directive,
                               'context_words': context_words})
            corrections += 1

        # Learn role assignments
        orig_role = orig.get('role', '').strip()
        edit_role = edited.get('role', '').strip()
        if edit_role and orig_role != edit_role:
            desc = edited.get('description', '').strip()
            context_words = _extract_context_words(desc)

            _add_or_increment(patterns, 'role_assignments',
                              'context_key', context_words,
                              {'role': edit_role, 'directive': edit_directive or orig_directive,
                               'description_preview': desc[:80]})
            corrections += 1

    if corrections > 0:
        save_patterns(patterns)
        reload_learned_patterns()
        logger.info(f'[AEGIS StatementLearner] Learned {corrections} statement corrections')


def learn_from_batch_edit(statement_ids: list, field: str, new_value: str):
    """Learn from batch edit operations (e.g., bulk directive or role change).

    Args:
        statement_ids: List of statement IDs that were batch-edited
        field: Field that was changed ('directive' or 'role')
        new_value: New value applied to all statements
    """
    if not statement_ids or not field or not new_value or not _is_learning_enabled():
        return

    patterns = load_patterns()

    if field == 'directive':
        # Batch directive changes indicate strong preference
        _add_or_increment(patterns, 'batch_preferences',
                          'preference_key', f"batch_directive:{new_value.lower()}",
                          {'field': 'directive', 'value': new_value,
                           'batch_size': len(statement_ids)})
    elif field == 'role':
        _add_or_increment(patterns, 'batch_preferences',
                          'preference_key', f"batch_role:{new_value.lower()}",
                          {'field': 'role', 'value': new_value,
                           'batch_size': len(statement_ids)})

    save_patterns(patterns)
    reload_learned_patterns()


# ──────────────────────────────────────────────
# Application functions — called during extraction
# ──────────────────────────────────────────────

def get_directive_override(original_directive: str, description: str) -> str:
    """Get learned directive override based on correction patterns.

    Returns override directive if pattern count >= 2, else empty string.
    """
    patterns = get_learned_patterns()

    for entry in patterns.get('directive_corrections', []):
        if entry.get('count', 0) < 2:
            continue

        from_dir = entry.get('from_directive', '')
        to_dir = entry.get('to_directive', '')
        context = entry.get('context_words', '')

        if from_dir == original_directive.lower():
            # If context words match, this is a strong signal
            if context and _context_matches(description, context):
                return to_dir
            # Universal correction (no context dependency) needs higher count
            if not context and entry.get('count', 0) >= 3:
                return to_dir

    return ''


def get_role_suggestion(description: str, directive: str = '') -> str:
    """Get learned role suggestion based on description context.

    Returns role name if pattern count >= 2, else empty string.
    """
    patterns = get_learned_patterns()

    for entry in patterns.get('role_assignments', []):
        if entry.get('count', 0) < 2:
            continue

        context = entry.get('context_key', '')
        if context and _context_matches(description, context):
            return entry.get('role', '')

    return ''


def should_skip_extraction(description: str) -> bool:
    """Check if a description matches learned deletion patterns.

    Returns True if users consistently delete statements with this pattern
    (count >= 3, higher threshold since deletion is more destructive).
    """
    patterns = get_learned_patterns()

    for entry in patterns.get('deletion_patterns', []):
        if entry.get('count', 0) < 3:
            continue

        keyword = entry.get('keyword', '')
        if keyword and _context_matches(description, keyword):
            return True

    return False


def get_pattern_stats() -> dict:
    """Return summary stats for UI display."""
    patterns = load_patterns()
    return {
        'directive_corrections': len(patterns.get('directive_corrections', [])),
        'role_assignments': len(patterns.get('role_assignments', [])),
        'deletion_patterns': len(patterns.get('deletion_patterns', [])),
        'batch_preferences': len(patterns.get('batch_preferences', [])),
        'total': _count_patterns(patterns),
        'last_updated': patterns.get('_meta', {}).get('last_updated', ''),
    }


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

_FILLER_WORDS = frozenset([
    'shall', 'should', 'will', 'must', 'may', 'the', 'and', 'for',
    'with', 'from', 'that', 'this', 'each', 'have', 'been', 'being',
    'into', 'such', 'when', 'where', 'which', 'than', 'other',
    'used', 'using', 'include', 'including', 'provide', 'required',
])


def _extract_context_words(text: str) -> str:
    """Extract significant context words from a description for pattern matching."""
    if not text:
        return ''
    words = [w for w in re.findall(r'\b\w{4,}\b', text.lower())
             if w not in _FILLER_WORDS]
    return ' '.join(words[:5])


def _context_matches(text: str, context: str) -> bool:
    """Check if text contains enough of the context words to be a match."""
    if not text or not context:
        return False
    text_lower = text.lower()
    context_words = context.split()
    if not context_words:
        return False
    # Require at least 60% of context words to match
    matches = sum(1 for w in context_words if w in text_lower)
    return matches >= max(1, len(context_words) * 0.6)


def _add_or_increment(patterns: dict, section: str, key_field: str,
                      key_value: str, extra_data: dict):
    """Add a new pattern entry or increment its count if it already exists."""
    if section not in patterns:
        patterns[section] = []

    for item in patterns[section]:
        if item.get(key_field, '').lower() == key_value.lower():
            item['count'] = item.get('count', 1) + 1
            item['last_seen'] = datetime.utcnow().strftime('%Y-%m-%d')
            return

    entry = {
        key_field: key_value,
        'count': 1,
        'added': datetime.utcnow().strftime('%Y-%m-%d'),
        'last_seen': datetime.utcnow().strftime('%Y-%m-%d'),
        'source': 'user_correction',
    }
    entry.update(extra_data)
    patterns[section].append(entry)


def _count_patterns(patterns: dict) -> int:
    """Count total pattern entries across all sections."""
    total = 0
    for key, val in patterns.items():
        if key != '_meta' and isinstance(val, list):
            total += len(val)
    return total


def _empty_patterns() -> dict:
    """Return empty pattern structure."""
    return {
        '_meta': {
            'version': '1.0',
            'tool': 'AEGIS Statement Learner',
            'last_updated': '',
            'total_corrections': 0,
        },
        'directive_corrections': [],
        'role_assignments': [],
        'deletion_patterns': [],
        'batch_preferences': [],
    }
