"""
AEGIS Review Learner — learns from user behavior during document reviews.

Tracks patterns from:
1. Issue dismissals — when users repeatedly ignore specific issue types/categories
2. Fix Assistant corrections — when users consistently apply the same fix patterns
3. Severity overrides — when users treat certain categories as less/more important
4. Document-type preferences — category suppression by document type

All data stays in review_patterns.json on disk, never uploaded.

Author: AEGIS v5.9.50
"""

import json
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PATTERNS_FILE = os.path.join(os.path.dirname(__file__), 'review_patterns.json')

# Module-level cache for fast access during review
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
    """Load learned review patterns from local JSON file."""
    if os.path.exists(PATTERNS_FILE):
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and '_meta' in data:
                    return data
        except Exception as e:
            logger.warning(f'[AEGIS ReviewLearner] Failed to load {PATTERNS_FILE}: {e}')
    return _empty_patterns()


def save_patterns(patterns: dict):
    """Save learned patterns to local JSON file (atomic write)."""
    try:
        patterns['_meta']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        tmp_path = PATTERNS_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, PATTERNS_FILE)
        logger.info(f'[AEGIS ReviewLearner] Saved {_count_patterns(patterns)} patterns')
    except Exception as e:
        logger.error(f'[AEGIS ReviewLearner] Failed to save patterns: {e}')
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
# Learning functions — called after user actions
# ──────────────────────────────────────────────

def learn_dismissed_issues(dismissed_issues: list, doc_type: str = ''):
    """Learn from issues the user dismissed/ignored during review.

    Args:
        dismissed_issues: List of issue dicts that were not acted on
        doc_type: Detected document type (e.g., 'requirements', 'work_instruction', 'general')
    """
    if not dismissed_issues or not _is_learning_enabled():
        return

    patterns = load_patterns()
    learned = 0

    for issue in dismissed_issues:
        category = issue.get('category', '').strip()
        rule_id = issue.get('rule_id', '').strip()
        severity = issue.get('severity', '').strip()

        if not category:
            continue

        # Track category dismissal frequency
        key = category.lower()
        if doc_type:
            key = f"{doc_type}:{key}"

        _add_or_increment(patterns, 'dismissed_categories',
                          'category_key', key,
                          {'category': category, 'doc_type': doc_type,
                           'severity': severity, 'rule_id': rule_id})
        learned += 1

    if learned > 0:
        save_patterns(patterns)
        reload_learned_patterns()
        logger.info(f'[AEGIS ReviewLearner] Learned {learned} dismissed issue patterns')


def learn_fix_patterns(fix_decisions: list):
    """Learn from Fix Assistant correction patterns.

    Args:
        fix_decisions: List of dicts with original_text, replacement_text, category, rule_id
    """
    if not fix_decisions or not _is_learning_enabled():
        return

    patterns = load_patterns()
    learned = 0

    for fix in fix_decisions:
        original = fix.get('original_text', '').strip()
        replacement = fix.get('replacement_text', '').strip()
        category = fix.get('category', '')

        if not original or not replacement or original == replacement:
            continue

        # Only learn short, specific replacements (not full paragraph rewrites)
        if len(original) > 100 or len(replacement) > 100:
            continue

        _add_or_increment(patterns, 'fix_patterns',
                          'original', original.lower(),
                          {'replacement': replacement, 'category': category})
        learned += 1

    if learned > 0:
        save_patterns(patterns)
        reload_learned_patterns()
        logger.info(f'[AEGIS ReviewLearner] Learned {learned} fix patterns')


def learn_severity_preference(category: str, original_severity: str,
                              preferred_severity: str, doc_type: str = ''):
    """Learn when a user consistently treats a category at a different severity.

    Args:
        category: Issue category name
        original_severity: Severity assigned by checker
        preferred_severity: Severity the user wants (e.g., 'Info' instead of 'Warning')
        doc_type: Optional document type for context
    """
    if not category or original_severity == preferred_severity or not _is_learning_enabled():
        return

    patterns = load_patterns()
    key = category.lower()
    if doc_type:
        key = f"{doc_type}:{key}"

    _add_or_increment(patterns, 'severity_overrides',
                      'category_key', key,
                      {'category': category, 'original_severity': original_severity,
                       'preferred_severity': preferred_severity, 'doc_type': doc_type})

    save_patterns(patterns)
    reload_learned_patterns()


# ──────────────────────────────────────────────
# Application functions — called during review
# ──────────────────────────────────────────────

def get_suppressed_categories(doc_type: str = '') -> set:
    """Get categories that should be suppressed (downgraded to Info) based on learned patterns.

    Only returns categories dismissed >= 2 times (safety threshold).
    """
    patterns = get_learned_patterns()
    suppressed = set()

    for entry in patterns.get('dismissed_categories', []):
        if entry.get('count', 0) < 2:
            continue

        cat_key = entry.get('category_key', '')
        category = entry.get('category', '')

        # Check doc_type-specific dismissals
        if doc_type and cat_key.startswith(f"{doc_type}:"):
            suppressed.add(category.lower())
        # Check universal dismissals (no doc_type prefix)
        elif ':' not in cat_key:
            suppressed.add(category.lower())

    return suppressed


def get_severity_override(category: str, doc_type: str = '') -> str:
    """Get learned severity override for a category, or empty string if none.

    Only returns overrides seen >= 2 times (safety threshold).
    """
    patterns = get_learned_patterns()

    for entry in patterns.get('severity_overrides', []):
        if entry.get('count', 0) < 2:
            continue

        cat_key = entry.get('category_key', '')
        # Check doc_type-specific first
        if doc_type and cat_key == f"{doc_type}:{category.lower()}":
            return entry.get('preferred_severity', '')
        # Then universal
        if cat_key == category.lower():
            return entry.get('preferred_severity', '')

    return ''


def get_learned_fixes() -> dict:
    """Get learned fix patterns as {original_lower: replacement} dict.

    Only returns fixes seen >= 2 times (safety threshold).
    """
    patterns = get_learned_patterns()
    fixes = {}
    for entry in patterns.get('fix_patterns', []):
        if entry.get('count', 0) >= 2:
            fixes[entry['original']] = entry.get('replacement', '')
    return fixes


def get_pattern_stats() -> dict:
    """Return summary stats for UI display."""
    patterns = load_patterns()
    return {
        'dismissed_categories': len(patterns.get('dismissed_categories', [])),
        'fix_patterns': len(patterns.get('fix_patterns', [])),
        'severity_overrides': len(patterns.get('severity_overrides', [])),
        'total': _count_patterns(patterns),
        'last_updated': patterns.get('_meta', {}).get('last_updated', ''),
    }


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

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
        'source': 'user_behavior',
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
            'tool': 'AEGIS Review Learner',
            'last_updated': '',
            'total_corrections': 0,
        },
        'dismissed_categories': [],
        'fix_patterns': [],
        'severity_overrides': [],
    }
