"""
AEGIS Hyperlink Validator Learner — learns from user corrections to link statuses.

Tracks patterns from:
1. Status overrides — when users mark AUTH_REQUIRED links as actually WORKING
2. Domain trust — domains users consistently mark as trustworthy
3. Exclusion patterns — domains/paths users frequently exclude
4. False positive domains — domains where bot protection always triggers but links work

All data stays in hv_patterns.json on disk, never uploaded.

Author: AEGIS v5.9.50
"""

import json
import os
import re
import logging
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

PATTERNS_FILE = os.path.join(os.path.dirname(__file__), 'hv_patterns.json')

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
    """Load learned HV patterns from local JSON file."""
    if os.path.exists(PATTERNS_FILE):
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and '_meta' in data:
                    return data
        except Exception as e:
            logger.warning(f'[AEGIS HVLearner] Failed to load {PATTERNS_FILE}: {e}')
    return _empty_patterns()


def save_patterns(patterns: dict):
    """Save learned patterns to local JSON file (atomic write)."""
    try:
        patterns['_meta']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        tmp_path = PATTERNS_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, PATTERNS_FILE)
        logger.info(f'[AEGIS HVLearner] Saved {_count_patterns(patterns)} patterns')
    except Exception as e:
        logger.error(f'[AEGIS HVLearner] Failed to save patterns: {e}')
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

def learn_status_override(url: str, original_status: str, user_status: str):
    """Learn when a user overrides a link's detected status.

    Common case: user marks AUTH_REQUIRED as WORKING (they know it works behind SSO).

    Args:
        url: The URL that was overridden
        original_status: Status from validator (e.g., AUTH_REQUIRED, BLOCKED, SSLERROR)
        user_status: Status the user set (e.g., WORKING, EXCLUDED)
    """
    if not url or original_status == user_status or not _is_learning_enabled():
        return

    patterns = load_patterns()
    domain = _extract_domain(url)

    if not domain:
        return

    # Learn domain-level override pattern
    override_key = f"{domain}:{original_status}→{user_status}"
    _add_or_increment(patterns, 'status_overrides',
                      'override_key', override_key,
                      {'domain': domain, 'original_status': original_status,
                       'user_status': user_status, 'sample_url': url[:200]})

    # Learn domain trust if user says it's WORKING
    if user_status.upper() in ('WORKING', 'OK'):
        _add_or_increment(patterns, 'trusted_domains',
                          'domain', domain,
                          {'original_status': original_status,
                           'sample_url': url[:200]})

    save_patterns(patterns)
    reload_learned_patterns()


def learn_from_exclusion(url: str, reason: str = ''):
    """Learn when a user excludes a URL.

    Tracks the domain so similar URLs can be auto-suggested for exclusion.

    Args:
        url: The excluded URL
        reason: User's reason for exclusion
    """
    if not url or not _is_learning_enabled():
        return

    patterns = load_patterns()
    domain = _extract_domain(url)
    path_pattern = _extract_path_pattern(url)

    if domain:
        _add_or_increment(patterns, 'exclusion_domains',
                          'domain', domain,
                          {'reason': reason, 'path_pattern': path_pattern,
                           'sample_url': url[:200]})

    save_patterns(patterns)
    reload_learned_patterns()


def learn_from_rescan_results(results: list):
    """Learn from Deep Validate (headless rescan) results.

    When headless browser recovers a URL that standard validation couldn't reach,
    learn that the domain likely needs headless validation.

    Args:
        results: List of rescan result dicts with url, status, original_status
    """
    if not results or not _is_learning_enabled():
        return

    patterns = load_patterns()
    learned = 0

    for result in results:
        url = result.get('url', '')
        new_status = result.get('status', '')
        original_status = result.get('original_status', '')
        domain = _extract_domain(url)

        if not domain:
            continue

        # If headless recovered it (was blocked/auth_required, now working)
        if new_status.upper() in ('WORKING', 'OK') and \
           original_status.upper() in ('BLOCKED', 'AUTH_REQUIRED', 'SSLERROR', 'TIMEOUT'):
            _add_or_increment(patterns, 'headless_required_domains',
                              'domain', domain,
                              {'original_status': original_status,
                               'sample_url': url[:200]})
            learned += 1

    if learned > 0:
        save_patterns(patterns)
        reload_learned_patterns()
        logger.info(f'[AEGIS HVLearner] Learned {learned} headless-required domain patterns')


# ──────────────────────────────────────────────
# Application functions — called during validation
# ──────────────────────────────────────────────

def get_trusted_domains() -> set:
    """Get domains the user has marked as trustworthy (count >= 2).

    URLs on these domains that fail validation should be downgraded
    to INFO instead of being flagged as errors.
    """
    patterns = get_learned_patterns()
    trusted = set()

    for entry in patterns.get('trusted_domains', []):
        if entry.get('count', 0) >= 2:
            trusted.add(entry.get('domain', '').lower())

    return trusted


def get_status_override(url: str, detected_status: str) -> str:
    """Get learned status override for a URL based on domain patterns.

    Returns override status if pattern count >= 2, else empty string.
    """
    patterns = get_learned_patterns()
    domain = _extract_domain(url)
    if not domain:
        return ''

    for entry in patterns.get('status_overrides', []):
        if entry.get('count', 0) < 2:
            continue
        if entry.get('domain', '').lower() == domain.lower() and \
           entry.get('original_status', '').upper() == detected_status.upper():
            return entry.get('user_status', '')

    return ''


def should_prioritize_headless(domain: str) -> bool:
    """Check if a domain should be prioritized for headless validation.

    Returns True if count >= 2 headless recoveries for this domain.
    """
    patterns = get_learned_patterns()

    for entry in patterns.get('headless_required_domains', []):
        if entry.get('count', 0) >= 2 and \
           entry.get('domain', '').lower() == domain.lower():
            return True

    return False


def get_auto_exclude_suggestions(urls: list) -> list:
    """Get URLs that should be suggested for auto-exclusion based on learned patterns.

    Returns list of URLs whose domains have been excluded >= 3 times.
    Higher threshold (3) since auto-exclusion skips validation entirely.
    """
    patterns = get_learned_patterns()
    excluded_domains = set()

    for entry in patterns.get('exclusion_domains', []):
        if entry.get('count', 0) >= 3:
            excluded_domains.add(entry.get('domain', '').lower())

    if not excluded_domains:
        return []

    suggestions = []
    for url in urls:
        domain = _extract_domain(url)
        if domain and domain.lower() in excluded_domains:
            suggestions.append(url)

    return suggestions


def get_pattern_stats() -> dict:
    """Return summary stats for UI display."""
    patterns = load_patterns()
    return {
        'status_overrides': len(patterns.get('status_overrides', [])),
        'trusted_domains': len(patterns.get('trusted_domains', [])),
        'exclusion_domains': len(patterns.get('exclusion_domains', [])),
        'headless_required_domains': len(patterns.get('headless_required_domains', [])),
        'total': _count_patterns(patterns),
        'last_updated': patterns.get('_meta', {}).get('last_updated', ''),
    }


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    """Extract domain from URL, handling edge cases."""
    try:
        parsed = urlparse(url)
        return parsed.hostname or ''
    except Exception:
        return ''


def _extract_path_pattern(url: str) -> str:
    """Extract a generalized path pattern from URL (for exclusion matching)."""
    try:
        parsed = urlparse(url)
        path = parsed.path or '/'
        # Generalize: replace specific IDs/numbers with wildcards
        pattern = re.sub(r'/\d+', '/*', path)
        # Truncate to first 3 segments
        parts = [p for p in pattern.split('/') if p][:3]
        return '/' + '/'.join(parts) if parts else '/'
    except Exception:
        return '/'


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
            'tool': 'AEGIS HV Learner',
            'last_updated': '',
            'total_corrections': 0,
        },
        'status_overrides': [],
        'trusted_domains': [],
        'exclusion_domains': [],
        'headless_required_domains': [],
    }
