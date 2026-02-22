"""
AEGIS Roles Learner — learns from adjudication decisions and role management.

Tracks patterns from:
1. Category assignments — when users consistently categorize similar roles
2. Deliverable patterns — keywords that predict deliverable vs non-deliverable
3. Disposition patterns — role name patterns that predict confirmed/rejected
4. Role type patterns — keywords that predict role types (person, tool, process, etc.)

All data stays in roles_patterns.json on disk, never uploaded.

Author: AEGIS v5.9.50
"""

import json
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PATTERNS_FILE = os.path.join(os.path.dirname(__file__), 'roles_patterns.json')

# Module-level cache
_learned_patterns = None


def _is_learning_enabled():
    """Check if learning is enabled via config.json (v5.9.52)."""
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f).get('learning_enabled', True)
    except Exception:
        pass
    return True


def load_patterns() -> dict:
    """Load learned role patterns from local JSON file."""
    if os.path.exists(PATTERNS_FILE):
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and '_meta' in data:
                    return data
        except Exception as e:
            logger.warning(f'[AEGIS RolesLearner] Failed to load {PATTERNS_FILE}: {e}')
    return _empty_patterns()


def save_patterns(patterns: dict):
    """Save learned patterns to local JSON file (atomic write)."""
    try:
        patterns['_meta']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        tmp_path = PATTERNS_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, PATTERNS_FILE)
        logger.info(f'[AEGIS RolesLearner] Saved {_count_patterns(patterns)} patterns')
    except Exception as e:
        logger.error(f'[AEGIS RolesLearner] Failed to save patterns: {e}')
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
# Learning functions — called after adjudication
# ──────────────────────────────────────────────

def learn_from_adjudication(decisions: list):
    """Learn from batch adjudication decisions.

    Args:
        decisions: List of decision dicts with role_name, action, category,
                   role_type, is_deliverable, etc.
    """
    if not decisions or not _is_learning_enabled():
        return

    patterns = load_patterns()
    learned = 0

    for decision in decisions:
        role_name = decision.get('role_name', '').strip()
        action = decision.get('action', '')
        category = decision.get('category', '')
        role_type = decision.get('role_type', '')
        is_deliverable = decision.get('is_deliverable', False)

        if not role_name:
            continue

        # Extract significant keywords from role name
        keywords = _extract_role_keywords(role_name)

        # Learn category assignments
        if category and keywords:
            _add_or_increment(patterns, 'category_patterns',
                              'keyword', keywords,
                              {'category': category, 'role_name': role_name})
            learned += 1

        # Learn deliverable patterns
        if keywords:
            _add_or_increment(patterns, 'deliverable_patterns',
                              'keyword', keywords,
                              {'is_deliverable': bool(is_deliverable),
                               'role_name': role_name})
            learned += 1

        # Learn disposition patterns (confirmed vs rejected)
        if action in ('confirmed', 'rejected', 'deliverable') and keywords:
            _add_or_increment(patterns, 'disposition_patterns',
                              'keyword', keywords,
                              {'disposition': action, 'role_name': role_name})
            learned += 1

        # Learn role type patterns
        if role_type and keywords:
            _add_or_increment(patterns, 'role_type_patterns',
                              'keyword', keywords,
                              {'role_type': role_type, 'role_name': role_name})
            learned += 1

    if learned > 0:
        save_patterns(patterns)
        reload_learned_patterns()
        logger.info(f'[AEGIS RolesLearner] Learned {learned} adjudication patterns')


def learn_single_adjudication(role_name: str, action: str, category: str = '',
                               role_type: str = '', is_deliverable: bool = False):
    """Learn from a single role adjudication (convenience wrapper)."""
    learn_from_adjudication([{
        'role_name': role_name,
        'action': action,
        'category': category,
        'role_type': role_type,
        'is_deliverable': is_deliverable,
    }])


# ──────────────────────────────────────────────
# Application functions — called during role processing
# ──────────────────────────────────────────────

def suggest_category(role_name: str) -> str:
    """Suggest a category for a role based on learned patterns.

    Returns category name if pattern count >= 2, else empty string.
    """
    patterns = get_learned_patterns()
    keywords = _extract_role_keywords(role_name)
    if not keywords:
        return ''

    best_match = ''
    best_count = 0

    for entry in patterns.get('category_patterns', []):
        if entry.get('count', 0) < 2:
            continue
        if _keywords_match(keywords, entry.get('keyword', '')):
            if entry['count'] > best_count:
                best_count = entry['count']
                best_match = entry.get('category', '')

    return best_match


def suggest_deliverable(role_name: str) -> bool:
    """Suggest whether a role is deliverable based on learned patterns.

    Returns True/False if pattern count >= 2, else None (no suggestion).
    """
    patterns = get_learned_patterns()
    keywords = _extract_role_keywords(role_name)
    if not keywords:
        return None

    for entry in patterns.get('deliverable_patterns', []):
        if entry.get('count', 0) < 2:
            continue
        if _keywords_match(keywords, entry.get('keyword', '')):
            return entry.get('is_deliverable', False)

    return None


def suggest_disposition(role_name: str) -> str:
    """Suggest disposition (confirmed/rejected/deliverable) based on learned patterns.

    Returns disposition string if pattern count >= 2, else empty string.
    """
    patterns = get_learned_patterns()
    keywords = _extract_role_keywords(role_name)
    if not keywords:
        return ''

    best_match = ''
    best_count = 0

    for entry in patterns.get('disposition_patterns', []):
        if entry.get('count', 0) < 2:
            continue
        if _keywords_match(keywords, entry.get('keyword', '')):
            if entry['count'] > best_count:
                best_count = entry['count']
                best_match = entry.get('disposition', '')

    return best_match


def suggest_role_type(role_name: str) -> str:
    """Suggest role type based on learned patterns.

    Returns role_type string if pattern count >= 2, else empty string.
    """
    patterns = get_learned_patterns()
    keywords = _extract_role_keywords(role_name)
    if not keywords:
        return ''

    best_match = ''
    best_count = 0

    for entry in patterns.get('role_type_patterns', []):
        if entry.get('count', 0) < 2:
            continue
        if _keywords_match(keywords, entry.get('keyword', '')):
            if entry['count'] > best_count:
                best_count = entry['count']
                best_match = entry.get('role_type', '')

    return best_match


def get_pattern_stats() -> dict:
    """Return summary stats for UI display."""
    patterns = load_patterns()
    return {
        'category_patterns': len(patterns.get('category_patterns', [])),
        'deliverable_patterns': len(patterns.get('deliverable_patterns', [])),
        'disposition_patterns': len(patterns.get('disposition_patterns', [])),
        'role_type_patterns': len(patterns.get('role_type_patterns', [])),
        'total': _count_patterns(patterns),
        'last_updated': patterns.get('_meta', {}).get('last_updated', ''),
    }


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

_FILLER_WORDS = frozenset([
    'the', 'and', 'for', 'with', 'from', 'that', 'this',
    'manager', 'lead', 'senior', 'junior', 'chief', 'deputy',
    'assistant', 'associate', 'team', 'group', 'division',
])


def _extract_role_keywords(role_name: str) -> str:
    """Extract significant keywords from a role name for pattern matching."""
    if not role_name:
        return ''
    words = [w for w in re.findall(r'\b\w{3,}\b', role_name.lower())
             if w not in _FILLER_WORDS]
    return ' '.join(words[:4])


def _keywords_match(keywords1: str, keywords2: str) -> bool:
    """Check if two keyword strings share enough words to be considered a match."""
    if not keywords1 or not keywords2:
        return False
    words1 = set(keywords1.split())
    words2 = set(keywords2.split())
    if not words1 or not words2:
        return False
    # Require at least 50% overlap
    intersection = words1 & words2
    min_len = min(len(words1), len(words2))
    return len(intersection) >= max(1, min_len * 0.5)


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
        'source': 'user_adjudication',
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
            'tool': 'AEGIS Roles Learner',
            'last_updated': '',
            'total_corrections': 0,
        },
        'category_patterns': [],
        'deliverable_patterns': [],
        'disposition_patterns': [],
        'role_type_patterns': [],
    }
