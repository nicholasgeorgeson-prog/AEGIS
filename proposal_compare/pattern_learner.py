"""
AEGIS Local Pattern Learning — learns from user corrections during Proposal Compare.

Computes diffs between original parser output and user-edited data,
stores learned patterns in parser_patterns.json. ALL data stays on disk,
never uploaded anywhere.

Learning types:
1. Category overrides — when user changes a line item's category
2. Company name patterns — when user corrects the detected company name
3. Financial table headers — when tables with user-verified data have specific headers
4. Column mappings — header signatures linked to known financial tables
"""

import json
import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

PATTERNS_FILE = os.path.join(os.path.dirname(__file__), 'parser_patterns.json')


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
    """Load learned patterns from local JSON file.

    Returns empty pattern structure if file doesn't exist or is corrupt.
    """
    if os.path.exists(PATTERNS_FILE):
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Validate structure
                if isinstance(data, dict) and '_meta' in data:
                    return data
        except Exception as e:
            logger.warning(f'[AEGIS PatternLearner] Failed to load {PATTERNS_FILE}: {e}')
    return _empty_patterns()


def save_patterns(patterns: dict):
    """Save learned patterns to local JSON file."""
    try:
        patterns['_meta']['last_updated'] = datetime.utcnow().isoformat() + 'Z'
        # Write to temp file first, then rename (atomic on most filesystems)
        tmp_path = PATTERNS_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        # Rename atomically
        if os.path.exists(PATTERNS_FILE):
            os.replace(tmp_path, PATTERNS_FILE)
        else:
            os.rename(tmp_path, PATTERNS_FILE)
        logger.info(f'[AEGIS PatternLearner] Saved {_count_patterns(patterns)} patterns to {PATTERNS_FILE}')
    except Exception as e:
        logger.error(f'[AEGIS PatternLearner] Failed to save patterns: {e}')
        # Clean up temp file if it exists
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def learn_from_corrections(proposals_with_originals: list):
    """Compare original parser extraction to user-edited data, learn patterns.

    Called automatically after each comparison. Each proposal dict should have
    an '_original_extraction' key containing the parser's original output.
    If no corrections were made, nothing is learned.
    """
    if not _is_learning_enabled():
        return
    patterns = load_patterns()
    corrections_found = 0

    for proposal in proposals_with_originals:
        original = proposal.get('_original_extraction')
        if not original:
            continue

        # Learn category corrections
        corrections_found += _learn_categories(original, proposal, patterns)
        # Learn company name corrections
        corrections_found += _learn_company(original, proposal, patterns)
        # Learn financial table header signatures
        corrections_found += _learn_table_signatures(proposal, patterns)

    if corrections_found > 0:
        patterns['_meta']['total_corrections'] = (
            len(patterns.get('category_overrides', [])) +
            len(patterns.get('company_patterns', [])) +
            len(patterns.get('column_mappings', [])) +
            len(patterns.get('financial_table_headers', []))
        )
        save_patterns(patterns)
        logger.info(f'[AEGIS PatternLearner] Learned {corrections_found} new corrections')
    else:
        logger.debug('[AEGIS PatternLearner] No corrections detected — nothing to learn')


def get_pattern_stats() -> dict:
    """Return summary stats about learned patterns (for UI display)."""
    patterns = load_patterns()
    return {
        'total_corrections': patterns.get('_meta', {}).get('total_corrections', 0),
        'category_overrides': len(patterns.get('category_overrides', [])),
        'company_patterns': len(patterns.get('company_patterns', [])),
        'column_mappings': len(patterns.get('column_mappings', [])),
        'financial_table_headers': len(patterns.get('financial_table_headers', [])),
        'last_updated': patterns.get('_meta', {}).get('last_updated', ''),
    }


# ──────────────────────────────────────────────
# Internal learning functions
# ──────────────────────────────────────────────

# Common filler words to exclude from keyword extraction
_FILLER_WORDS = frozenset([
    'with', 'from', 'that', 'this', 'each', 'year', 'unit', 'item',
    'line', 'total', 'price', 'cost', 'amount', 'description', 'note',
    'none', 'other', 'misc', 'various', 'general', 'includes', 'included',
    'based', 'plus', 'additional', 'option', 'optional',
])


def _learn_categories(original: dict, edited: dict, patterns: dict) -> int:
    """Detect category changes and learn new keyword→category mappings.

    Returns number of new corrections learned.
    """
    orig_items = original.get('line_items', [])
    edit_items = edited.get('line_items', [])
    corrections = 0

    for oi, ei in zip(orig_items, edit_items):
        orig_cat = oi.get('category', '')
        edit_cat = ei.get('category', '')
        desc = ei.get('description', '').strip().lower()

        if orig_cat != edit_cat and edit_cat and edit_cat != 'Other' and desc:
            # User changed the category — extract significant keywords
            words = [w for w in re.findall(r'\b\w{4,}\b', desc)
                     if w.lower() not in _FILLER_WORDS]
            keyword = ' '.join(words[:4])  # First 4 significant words

            if keyword and len(keyword) >= 6:
                _add_or_increment(patterns, 'category_overrides',
                                  'keyword', keyword,
                                  {'category': edit_cat, 'original_category': orig_cat})
                corrections += 1

    return corrections


def _learn_company(original: dict, edited: dict, patterns: dict) -> int:
    """Learn company name patterns when user corrects extraction.

    Returns 1 if a correction was learned, 0 otherwise.
    """
    orig_name = original.get('company_name', '').strip()
    edit_name = edited.get('company_name', '').strip()
    filename = edited.get('filename', '')

    if orig_name != edit_name and edit_name and len(edit_name) >= 3:
        filename_hint = ''
        if filename:
            # Extract meaningful part of filename (no extension, no timestamp prefix)
            base = os.path.splitext(filename)[0].lower()
            # Remove common timestamp prefixes (e.g., "1740123456_")
            base = re.sub(r'^\d{8,}_', '', base)
            filename_hint = base[:40]

        _add_or_increment(patterns, 'company_patterns',
                          'pattern', edit_name,
                          {'filename_hint': filename_hint, 'original_name': orig_name})
        return 1
    return 0


def _learn_table_signatures(proposal: dict, patterns: dict) -> int:
    """Learn financial table header signatures from tables with verified line items.

    When a proposal has user-verified line items with amounts, record
    the header signatures of its financial tables so similar tables
    are auto-detected in future parses.

    Returns number of new signatures learned.
    """
    items = proposal.get('line_items', [])
    if not items or not any(i.get('amount') for i in items):
        return 0

    learned = 0
    for table in proposal.get('tables', []):
        headers = table.get('headers', [])
        if not headers or len(headers) < 2:
            continue

        # Build normalized header signature
        sig = '|'.join(h.lower().strip()[:20] for h in headers if h)
        if not sig or len(sig) < 3:
            continue

        # Check if we already have this signature
        existing = any(
            m.get('header_signature', '').lower() == sig.lower()
            for m in patterns.get('financial_table_headers', [])
        )
        if not existing:
            _add_or_increment(patterns, 'financial_table_headers',
                              'header_signature', sig,
                              {'is_financial': table.get('has_financial_data', True)})
            learned += 1

    return learned


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _add_or_increment(patterns: dict, section: str, key_field: str,
                      key_value: str, extra_data: dict):
    """Add a new pattern entry or increment its count if it already exists."""
    if section not in patterns:
        patterns[section] = []

    # Check for existing entry (case-insensitive match)
    for item in patterns[section]:
        if item.get(key_field, '').lower() == key_value.lower():
            item['count'] = item.get('count', 1) + 1
            item['last_seen'] = datetime.utcnow().strftime('%Y-%m-%d')
            return

    # New entry
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
    """Count total number of pattern entries across all sections."""
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
            'tool': 'AEGIS Pattern Learner',
            'last_updated': '',
            'total_corrections': 0,
        },
        'category_overrides': [],
        'company_patterns': [],
        'column_mappings': [],
        'financial_table_headers': [],
    }
