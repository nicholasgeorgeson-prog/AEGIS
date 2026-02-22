#!/usr/bin/env python3
"""
AEGIS Proposal Structure Tool — Desktop Edition v3
====================================================
Double-click this script from ANYWHERE (Desktop, Downloads, etc).
It will:
  1. Find your AEGIS install automatically
  2. Open a file picker — select one or more proposal files
  3. Analyze them (privacy-safe — no $ amounts, names, or text)
  4. Upload the JSON result directly to GitHub

The JSON appears at:
  https://github.com/nicholasgeorgeson-prog/AEGIS/tree/main/structure_reports/

No server needed. No browser. Just run it.

First run: creates aegis_github_token.txt — paste your GitHub token once.
After that, just double-click and pick files.
"""

import os
import sys
import re
import json
import logging
import base64
import hashlib
import urllib.request
import urllib.error
import ssl
import traceback
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple

VERSION = "3.0.0"

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger('proposal_structure_tool')

# GitHub config
GITHUB_REPO = "nicholasgeorgeson-prog/AEGIS"
GITHUB_BRANCH = "main"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_REPORT_DIR = "structure_reports"
TOKEN_FILENAME = "aegis_github_token.txt"

_github_token = None  # loaded at runtime


# ═══════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════

def print_banner():
    print()
    print("=" * 62)
    print("  AEGIS Proposal Structure Tool")
    print(f"  Desktop Edition  v{VERSION}")
    print("  Analyze → Upload to GitHub automatically")
    print("=" * 62)
    print()


# ═══════════════════════════════════════════════
# GITHUB TOKEN
# ═══════════════════════════════════════════════

def find_token():
    """Find the GitHub PAT from aegis_github_token.txt."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")

    search_paths = [
        os.path.join(script_dir, TOKEN_FILENAME),
        os.path.join(home, "Desktop", TOKEN_FILENAME),
        os.path.join(home, TOKEN_FILENAME),
        os.path.join(home, "Desktop", "Doc Review", "AEGIS", TOKEN_FILENAME),
        os.path.join(home, "OneDrive - NGC", "Desktop", "Doc Review", "AEGIS", TOKEN_FILENAME),
        os.path.join(home, "Desktop", "Work_Tools", "TechWriterReview", TOKEN_FILENAME),
    ]

    for path in search_paths:
        if os.path.isfile(path):
            try:
                with open(path, 'r') as f:
                    token = f.read().strip()
                if token and token.startswith('ghp_'):
                    return token
            except Exception:
                pass
    return None


def setup_token():
    """Create the token file on first run."""
    print("  ┌─────────────────────────────────────────────┐")
    print("  │  First-time setup: GitHub token needed       │")
    print("  └─────────────────────────────────────────────┘")
    print()
    print("  This lets the tool upload results to GitHub.")
    print("  You only need to do this once.")
    print()
    print("  Paste your GitHub Personal Access Token below.")
    print("  (It starts with ghp_ ...)")
    print()

    token = input("  Token: ").strip()

    if not token:
        print("  No token entered. Results will be saved locally only.")
        return None

    if not token.startswith('ghp_'):
        print("  WARNING: Token doesn't start with 'ghp_' — may not work.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, TOKEN_FILENAME)

    try:
        with open(token_path, 'w') as f:
            f.write(token)
        print(f"  Token saved to: {token_path}")
        print("  (You won't be asked again)")
        print()
        return token
    except Exception as e:
        print(f"  Could not save token file: {e}")
        print("  Token will be used this session only.")
        return token


def load_token():
    """Load or create the GitHub token."""
    global _github_token
    token = find_token()
    if token:
        _github_token = token
        return True
    token = setup_token()
    if token:
        _github_token = token
        return True
    return False


# ═══════════════════════════════════════════════
# FIND AEGIS INSTALL
# ═══════════════════════════════════════════════

def find_aegis_install():
    """Search common locations for the AEGIS install directory."""
    candidates = []
    home = os.path.expanduser("~")

    # Windows paths
    candidates += [
        os.path.join(home, "Desktop", "Doc Review", "AEGIS"),
        os.path.join(home, "Desktop", "AEGIS"),
        os.path.join(home, "Documents", "AEGIS"),
        os.path.join(home, "OneDrive - NGC", "Desktop", "Doc Review", "AEGIS"),
        os.path.join(home, "OneDrive", "Desktop", "Doc Review", "AEGIS"),
        os.path.join(home, "OneDrive - NGC", "Desktop", "AEGIS"),
        "C:\\AEGIS",
        "C:\\AEGIS\\app",
    ]

    # Mac paths
    candidates += [
        os.path.join(home, "Desktop", "Work_Tools", "TechWriterReview"),
        os.path.join(home, "Desktop", "TechWriterReview"),
    ]

    # Script's own directory and parent
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.insert(0, script_dir)
    candidates.insert(1, os.path.dirname(script_dir))

    for path in candidates:
        if os.path.isdir(path):
            parser_path = os.path.join(path, "proposal_compare", "parser.py")
            if os.path.isfile(parser_path):
                return path

    return None


def load_parser(aegis_dir):
    """Import ONLY the parser from AEGIS (the part that reads documents).

    The structure analysis logic is embedded in THIS script,
    so we only need the parser for document extraction.
    """
    if aegis_dir not in sys.path:
        sys.path.insert(0, aegis_dir)

    try:
        from proposal_compare.parser import (
            parse_proposal, CATEGORY_PATTERNS, SUPPORTED_EXTENSIONS,
        )
        # Also try to get column inference helpers (optional)
        try:
            from proposal_compare.parser import _infer_columns_from_data, _headers_are_generic
        except ImportError:
            _infer_columns_from_data = None
            _headers_are_generic = None

        return {
            'available': True,
            'parse_proposal': parse_proposal,
            'CATEGORY_PATTERNS': CATEGORY_PATTERNS,
            'SUPPORTED_EXTENSIONS': SUPPORTED_EXTENSIONS,
            '_infer_columns_from_data': _infer_columns_from_data,
            '_headers_are_generic': _headers_are_generic,
        }
    except Exception as e:
        return {
            'available': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }


# ═══════════════════════════════════════════════
# FILE PICKER
# ═══════════════════════════════════════════════

def open_file_picker():
    """Open a native file picker. Returns list of file paths."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        filetypes = [
            ('Proposal files', '*.xlsx *.xls *.docx *.pdf'),
            ('Excel files', '*.xlsx *.xls'),
            ('Word files', '*.docx'),
            ('PDF files', '*.pdf'),
            ('All files', '*.*'),
        ]

        files = filedialog.askopenfilenames(
            title='Select Proposal Files to Analyze',
            filetypes=filetypes,
        )
        root.destroy()
        return list(files) if files else []

    except Exception as e:
        print(f"  File picker error: {e}")
        print("  Enter file paths manually (blank line to finish):")
        files = []
        while True:
            path = input("  Path: ").strip().strip('"').strip("'")
            if not path:
                break
            if os.path.isfile(path):
                files.append(path)
                print(f"    + {os.path.basename(path)}")
            else:
                print(f"    X Not found")
        return files


# ═══════════════════════════════════════════════
# GITHUB UPLOAD
# ═══════════════════════════════════════════════

def _github_request(endpoint, method="GET", data=None):
    """Make a GitHub API request."""
    url = f"{GITHUB_API}/{endpoint}" if not endpoint.startswith("http") else endpoint

    headers = {
        "Authorization": f"token {_github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AEGIS-StructureTool",
    }

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    # Try with default SSL first, fallback to unverified for corporate networks
    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    except ssl.SSLError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)

    return json.loads(resp.read().decode("utf-8"))


def upload_to_github(json_content, filename):
    """Upload a JSON file to the structure_reports/ folder on GitHub."""
    path = f"{GITHUB_REPORT_DIR}/{filename}"

    existing_sha = None
    try:
        existing = _github_request(f"contents/{path}?ref={GITHUB_BRANCH}")
        existing_sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    content_b64 = base64.b64encode(json_content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Structure analysis: {filename}",
        "content": content_b64,
        "branch": GITHUB_BRANCH,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    result = _github_request(f"contents/{path}", method="PUT", data=payload)

    return result.get("content", {}).get(
        "html_url",
        f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"
    )


# ═══════════════════════════════════════════════
# STRUCTURE ANALYSIS (SELF-CONTAINED)
# All analysis logic is here — no imports from
# structure_analyzer.py needed.
# ═══════════════════════════════════════════════

def _bucket_amount(amount):
    """Convert a dollar amount into a non-revealing bucket label."""
    if amount is None:
        return 'none'
    a = abs(amount)
    if a == 0: return '$0'
    elif a < 100: return '$1-$99'
    elif a < 1000: return '$100-$999'
    elif a < 10000: return '$1K-$9.9K'
    elif a < 100000: return '$10K-$99K'
    elif a < 1000000: return '$100K-$999K'
    elif a < 10000000: return '$1M-$9.9M'
    elif a < 100000000: return '$10M-$99M'
    else: return '$100M+'


def _analyze_description_pattern(desc):
    """Analyze description structure without revealing content."""
    if not desc:
        return {'length': 0, 'word_count': 0, 'pattern': 'empty'}
    words = desc.split()
    char_count = len(desc)
    if char_count < 10: pattern = 'very_short'
    elif char_count < 30: pattern = 'short_label'
    elif char_count < 80: pattern = 'medium_description'
    elif char_count < 200: pattern = 'long_description'
    else: pattern = 'very_long_text'
    return {
        'length': char_count,
        'word_count': len(words),
        'has_numbers': bool(re.search(r'\d', desc)),
        'pattern': pattern,
    }


def _classify_header(header):
    """Classify a column header into a generic role."""
    if not header or not header.strip():
        return '(empty)'
    h = header.strip().lower()
    safe_headers = {
        'description', 'task', 'item', 'clin', 'name', 'line item',
        'cost', 'price', 'amount', 'total', 'total cost', 'total price',
        'extended', 'extended price', 'extended cost',
        'unit price', 'unit cost', 'rate', 'hourly rate',
        'quantity', 'qty', 'hours', 'units', 'count', 'each',
        'unit', 'uom', 'category', 'type', 'labor category',
        'subtotal', 'sub-total', 'grand total',
        'overhead', 'g&a', 'fringe', 'fee', 'profit', 'margin',
        'year 1', 'year 2', 'year 3', 'year 4', 'year 5',
        'base year', 'by', 'oy1', 'oy2', 'oy3', 'oy4',
        'option year 1', 'option year 2', 'option year 3',
        'wbs', 'wbs element', 'task number', 'task no',
        'notes', 'remarks', 'comments',
    }
    if h in safe_headers:
        return header.strip()
    if any(kw in h for kw in ['desc', 'item', 'task', 'service', 'product']):
        return f'description_variant ({len(header)} chars)'
    if any(kw in h for kw in ['cost', 'price', 'amount', 'total', 'value']):
        return f'amount_variant ({len(header)} chars)'
    if any(kw in h for kw in ['qty', 'quantity', 'hours', 'units', 'count']):
        return f'quantity_variant ({len(header)} chars)'
    if any(kw in h for kw in ['rate', 'unit price', 'per', 'hourly']):
        return f'rate_variant ({len(header)} chars)'
    words = header.strip().split()
    return f'custom_header ({len(words)} words, {len(header)} chars)'


def _check_generic_headers(headers):
    """Check if headers are generic auto-generated names."""
    if not headers:
        return True
    generic = re.compile(r'^(col\s*\d+|column\s*\d+|\d+|unnamed.*|)$', re.IGNORECASE)
    count = sum(1 for h in headers if generic.match(h.strip()))
    return count > len(headers) * 0.6


def _analyze_cell_patterns(rows, max_rows=20):
    """Analyze data patterns in each column without revealing values."""
    if not rows:
        return []
    num_cols = max(len(r) for r in rows) if rows else 0
    sample = rows[:max_rows]
    total_rows = len(sample)
    col_analyses = []
    for col_idx in range(num_cols):
        stats = {
            'column_index': col_idx, 'fill_rate': 0.0,
            'dollar_pattern_count': 0, 'numeric_count': 0,
            'text_count': 0, 'empty_count': 0,
            'avg_text_length': 0.0, 'dominant_type': 'empty',
        }
        text_lengths = []
        for row in sample:
            if col_idx >= len(row):
                stats['empty_count'] += 1
                continue
            cell = str(row[col_idx]).strip()
            if not cell:
                stats['empty_count'] += 1
                continue
            text_lengths.append(len(cell))
            if re.search(r'\$\s*[\d,]+', cell):
                stats['dollar_pattern_count'] += 1
            elif re.match(r'^[\d,]+(?:\.\d+)?$', cell.replace(',', '').strip()):
                stats['numeric_count'] += 1
            elif sum(1 for c in cell if c.isalpha()) > 0:
                stats['text_count'] += 1
        if text_lengths:
            stats['avg_text_length'] = round(sum(text_lengths) / len(text_lengths), 1)
        filled = total_rows - stats['empty_count']
        stats['fill_rate'] = round(filled / total_rows * 100, 1) if total_rows > 0 else 0
        counts = {
            'dollar': stats['dollar_pattern_count'],
            'numeric': stats['numeric_count'],
            'text': stats['text_count'],
        }
        if filled == 0:
            stats['dominant_type'] = 'empty'
        elif max(counts.values()) > filled * 0.6:
            stats['dominant_type'] = max(counts, key=counts.get)
        else:
            stats['dominant_type'] = 'mixed'
        col_analyses.append(stats)
    return col_analyses


def _format_file_size(size_bytes):
    if size_bytes < 1024: return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024: return f'{size_bytes / 1024:.1f} KB'
    else: return f'{size_bytes / (1024 * 1024):.1f} MB'


def _total_row_position(total_idx, total_rows):
    if total_idx is None: return 'none'
    if total_rows == 0: return 'none'
    ratio = total_idx / total_rows
    if ratio > 0.9: return 'bottom (last 10%)'
    elif ratio > 0.7: return 'near bottom (70-90%)'
    elif ratio > 0.5: return 'middle-bottom (50-70%)'
    else: return 'upper half (<50%)'


def _redact_error_message(msg):
    msg = re.sub(r'[A-Z]:\\[^\s]+', '[PATH]', msg)
    msg = re.sub(r'/[^\s]+/', '[PATH]/', msg)
    msg = re.sub(r'\b\w+\.(xlsx|docx|pdf|xls|doc)\b', '[FILE]', msg, flags=re.IGNORECASE)
    return msg


def _compute_completeness_score(proposal):
    scores = {}
    if proposal.tables:
        financial = sum(1 for t in proposal.tables if t.has_financial_data)
        scores['table_extraction'] = min(100, financial * 25)
    else:
        scores['table_extraction'] = 0
    if proposal.line_items:
        scores['line_item_extraction'] = min(100, len(proposal.line_items) * 5)
    else:
        scores['line_item_extraction'] = 0
    meta_score = 0
    if proposal.company_name: meta_score += 30
    if proposal.date: meta_score += 20
    if proposal.contract_term: meta_score += 25
    if proposal.total_amount is not None: meta_score += 25
    scores['metadata_extraction'] = meta_score
    if proposal.line_items:
        items = proposal.line_items
        has_amount = sum(1 for li in items if li.amount is not None) / len(items)
        has_desc = sum(1 for li in items if li.description) / len(items)
        has_cat = sum(1 for li in items if li.category != 'Other') / len(items)
        scores['field_coverage'] = round((has_amount + has_desc + has_cat) / 3 * 100, 1)
    else:
        scores['field_coverage'] = 0
    weights = {'table_extraction': 0.3, 'line_item_extraction': 0.3,
               'metadata_extraction': 0.2, 'field_coverage': 0.2}
    scores['overall'] = round(sum(scores[k] * weights[k] for k in weights), 1)
    return scores


def _generate_suggestions(proposal, analysis):
    suggestions = []
    if not proposal.tables:
        suggestions.append('CRITICAL: No tables detected')
    if proposal.tables and not any(t.has_financial_data for t in proposal.tables):
        suggestions.append('Tables found but none flagged as financial')
    financial_tables = [t for t in proposal.tables if t.has_financial_data]
    if financial_tables and not proposal.line_items:
        suggestions.append('Financial tables detected but no line items extracted')
    if proposal.line_items:
        low_conf = sum(1 for li in proposal.line_items if li.confidence < 0.7)
        if low_conf > len(proposal.line_items) * 0.3:
            suggestions.append(f'{low_conf} of {len(proposal.line_items)} items have low confidence')
    if proposal.line_items:
        other_count = sum(1 for li in proposal.line_items if li.category == 'Other')
        if other_count > len(proposal.line_items) * 0.5:
            suggestions.append(f'{other_count} of {len(proposal.line_items)} items categorized as Other')
    if not proposal.company_name:
        suggestions.append('Company name not detected')
    if proposal.total_amount is None:
        suggestions.append('No total amount found')
    for tbl in proposal.tables:
        if tbl.has_financial_data and _check_generic_headers(tbl.headers):
            suggestions.append(f'Table {tbl.table_index} has generic headers')
            break
    if not suggestions:
        suggestions.append('Extraction looks complete — no issues detected')
    return suggestions


def analyze_single_file(filepath, parser_modules):
    """Analyze one file and return the structural report dict."""
    parse_proposal = parser_modules['parse_proposal']
    CATEGORY_PATTERNS = parser_modules['CATEGORY_PATTERNS']

    result = {
        '_meta': {
            'tool': 'AEGIS Structure Tool (Desktop)',
            'standalone_version': VERSION,
            'purpose': 'Privacy-safe structural analysis for parser accuracy refinement',
            'note': 'All financial values bucketed, company names removed, descriptions redacted',
        },
        'file_info': {},
        'tables': [],
        'line_items_summary': {},
        'extraction_diagnostics': {},
        'category_analysis': {},
        'column_inference_details': [],
        'overall_assessment': {},
    }

    # File info
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
    file_hash = hashlib.sha256(f'{file_size}_{ext}'.encode()).hexdigest()[:12]

    result['file_info'] = {
        'file_type': ext.lstrip('.'),
        'file_size_bytes': file_size,
        'file_size_label': _format_file_size(file_size),
        'file_hash': file_hash,
    }

    # Parse
    try:
        proposal = parse_proposal(filepath)
    except Exception as e:
        result['extraction_diagnostics'] = {
            'error': type(e).__name__,
            'error_message_redacted': _redact_error_message(str(e)),
        }
        return result

    result['file_info']['page_count'] = proposal.page_count

    # Table structure
    for tbl in proposal.tables:
        table_info = {
            'table_index': tbl.table_index,
            'source': tbl.source,
            'shape': {
                'rows': len(tbl.rows),
                'columns': len(tbl.headers) if tbl.headers else (
                    max(len(r) for r in tbl.rows) if tbl.rows else 0
                ),
            },
            'headers': [_classify_header(h) for h in tbl.headers],
            'headers_are_generic': _check_generic_headers(tbl.headers),
            'has_financial_data': tbl.has_financial_data,
            'has_total_row': tbl.total_row_index is not None,
            'total_row_position': _total_row_position(tbl.total_row_index, len(tbl.rows)),
            'column_data_patterns': _analyze_cell_patterns(tbl.rows),
        }
        if tbl.rows:
            row_lengths = [len(r) for r in tbl.rows]
            table_info['row_analysis'] = {
                'min_cells_per_row': min(row_lengths),
                'max_cells_per_row': max(row_lengths),
                'consistent_width': min(row_lengths) == max(row_lengths),
                'empty_row_count': sum(1 for r in tbl.rows if not any(str(c).strip() for c in r)),
            }
        result['tables'].append(table_info)

    # Line items summary
    items = proposal.line_items
    if items:
        cat_dist = {}
        for li in items:
            cat = li.category or 'Uncategorized'
            cat_dist[cat] = cat_dist.get(cat, 0) + 1

        conf_buckets = {'high (0.9-1.0)': 0, 'medium (0.7-0.89)': 0, 'low (<0.7)': 0}
        for li in items:
            if li.confidence >= 0.9: conf_buckets['high (0.9-1.0)'] += 1
            elif li.confidence >= 0.7: conf_buckets['medium (0.7-0.89)'] += 1
            else: conf_buckets['low (<0.7)'] += 1

        amount_buckets = {}
        for li in items:
            bucket = _bucket_amount(li.amount)
            amount_buckets[bucket] = amount_buckets.get(bucket, 0) + 1

        desc_patterns = {}
        desc_lengths = []
        for li in items:
            analysis = _analyze_description_pattern(li.description)
            desc_patterns[analysis['pattern']] = desc_patterns.get(analysis['pattern'], 0) + 1
            desc_lengths.append(analysis['length'])

        field_coverage = {
            'has_description': sum(1 for li in items if li.description and len(li.description) > 2),
            'has_amount': sum(1 for li in items if li.amount is not None),
            'has_quantity': sum(1 for li in items if li.quantity is not None),
            'has_unit_price': sum(1 for li in items if li.unit_price is not None),
            'has_category': sum(1 for li in items if li.category and li.category != 'Other'),
        }

        result['line_items_summary'] = {
            'total_count': len(items),
            'category_distribution': cat_dist,
            'confidence_distribution': conf_buckets,
            'amount_bucket_distribution': amount_buckets,
            'description_patterns': desc_patterns,
            'description_length_stats': {
                'min': min(desc_lengths) if desc_lengths else 0,
                'max': max(desc_lengths) if desc_lengths else 0,
                'avg': round(sum(desc_lengths) / len(desc_lengths), 1) if desc_lengths else 0,
            },
            'field_coverage': field_coverage,
            'field_coverage_percentages': {
                k: round(v / len(items) * 100, 1) for k, v in field_coverage.items()
            },
            'total_amount_bucket': _bucket_amount(proposal.total_amount),
        }
    else:
        result['line_items_summary'] = {'total_count': 0, 'note': 'No line items extracted'}

    # Category analysis
    result['category_analysis'] = {
        'detected_categories': list(set(li.category for li in items)) if items else [],
        'supported_categories': list(CATEGORY_PATTERNS.keys()),
        'uncategorized_count': sum(1 for li in items if li.category == 'Other') if items else 0,
    }

    # Extraction diagnostics
    result['extraction_diagnostics'] = {
        'notes': proposal.extraction_notes,
        'company_detected': bool(proposal.company_name),
        'date_detected': bool(proposal.date),
        'contract_term_detected': bool(proposal.contract_term),
        'contract_term_value': proposal.contract_term or '(none)',
        'total_detected': proposal.total_amount is not None,
        'text_extraction_available': bool(proposal.extraction_text),
    }

    # Column inference details (if helper available)
    _infer = parser_modules.get('_infer_columns_from_data')
    _generic = parser_modules.get('_headers_are_generic')
    if _infer and _generic:
        for tbl in proposal.tables:
            if tbl.has_financial_data:
                try:
                    inferred = _infer(tbl.headers, tbl.rows)
                    result['column_inference_details'].append({
                        'table_index': tbl.table_index,
                        'source': tbl.source,
                        'headers_generic': _generic(tbl.headers),
                        'inferred_roles': {
                            'description_col': inferred.get('desc_col'),
                            'amount_col': inferred.get('amount_col'),
                            'quantity_col': inferred.get('qty_col'),
                            'unit_price_col': inferred.get('unit_price_col'),
                        },
                    })
                except Exception:
                    pass

    # Overall assessment
    result['overall_assessment'] = {
        'total_tables_found': len(proposal.tables),
        'financial_tables': sum(1 for t in proposal.tables if t.has_financial_data),
        'total_line_items': len(items),
        'avg_confidence': round(sum(li.confidence for li in items) / len(items), 3) if items else 0,
        'has_total_amount': proposal.total_amount is not None,
        'has_company_name': bool(proposal.company_name),
        'has_date': bool(proposal.date),
        'has_contract_term': bool(proposal.contract_term),
        'extraction_completeness': _compute_completeness_score(proposal),
        'parser_suggestions': _generate_suggestions(proposal, result),
    }

    return result


def analyze_batch(files, parser_modules):
    """Analyze multiple files and return combined report."""
    results = []
    errors = []

    for idx, (filepath, original_name) in enumerate(files):
        try:
            analysis = analyze_single_file(filepath, parser_modules)
            analysis['file_index'] = idx
            analysis['file_info']['original_filename'] = original_name
            results.append(analysis)
        except Exception as e:
            results.append({
                'file_index': idx,
                'file_info': {'original_filename': original_name},
                '_error': {'type': type(e).__name__, 'message': _redact_error_message(str(e))},
            })
            errors.append(idx)

    # Cross-file summary
    cross = {
        'total_files': len(files),
        'files_by_type': {},
        'total_tables_found': 0,
        'total_financial_tables': 0,
        'total_line_items': 0,
        'avg_extraction_completeness': 0.0,
        'category_distribution_merged': {},
    }
    completeness_scores = []
    for r in results:
        if '_error' in r:
            continue
        ft = r.get('file_info', {}).get('file_type', 'unknown')
        cross['files_by_type'][ft] = cross['files_by_type'].get(ft, 0) + 1
        assessment = r.get('overall_assessment', {})
        cross['total_tables_found'] += assessment.get('total_tables_found', 0)
        cross['total_financial_tables'] += assessment.get('financial_tables', 0)
        cross['total_line_items'] += assessment.get('total_line_items', 0)
        comp = assessment.get('extraction_completeness', {})
        if 'overall' in comp:
            completeness_scores.append(comp['overall'])
        cat_dist = r.get('line_items_summary', {}).get('category_distribution', {})
        for cat, count in cat_dist.items():
            cross['category_distribution_merged'][cat] = cross['category_distribution_merged'].get(cat, 0) + count
    if completeness_scores:
        cross['avg_extraction_completeness'] = round(sum(completeness_scores) / len(completeness_scores), 1)

    return {
        '_meta': {
            'tool': 'AEGIS Batch Structure Tool (Desktop)',
            'standalone_version': VERSION,
            'purpose': 'Privacy-safe structural analysis for parser accuracy refinement',
            'file_count': len(files),
            'files_succeeded': len(files) - len(errors),
            'files_failed': len(errors),
            'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        },
        'files': results,
        'cross_file_summary': cross,
    }


# ═══════════════════════════════════════════════
# RUN ANALYSIS
# ═══════════════════════════════════════════════

def run_analysis(files, parser_modules):
    """Run structure analysis on selected files."""
    count = len(files)
    print(f"  Analyzing {count} file{'s' if count != 1 else ''}...")
    print()

    if count == 1:
        filepath = files[0]
        filename = os.path.basename(filepath)
        print(f"    Processing: {filename}...", end=" ", flush=True)

        try:
            result = analyze_single_file(filepath, parser_modules)
            base = os.path.splitext(filename)[0]
            safe_base = re.sub(r'[^\w\-.]', '_', base)
            output_name = f"{safe_base}_structure.json"
            print("done")
            return result, output_name
        except Exception as e:
            print(f"ERROR")
            print(f"\n  Error details: {e}")
            traceback.print_exc()
            return None, None
    else:
        file_tuples = [(f, os.path.basename(f)) for f in files]
        for i, (fp, fn) in enumerate(file_tuples, 1):
            print(f"    [{i}/{count}] {fn}")
        print()
        print("  Running batch analysis...", end=" ", flush=True)

        try:
            result = analyze_batch(file_tuples, parser_modules)
            succeeded = result['_meta']['files_succeeded']
            failed = result['_meta']['files_failed']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_name = f"batch_{count}files_{timestamp}.json"
            print(f"done — {succeeded} OK, {failed} failed")
            return result, output_name
        except Exception as e:
            print(f"ERROR")
            print(f"\n  Error details: {e}")
            traceback.print_exc()
            return None, None


def print_summary(result, github_url, local_path):
    """Print results summary."""
    print()
    print("=" * 62)
    print("  RESULTS")
    print("-" * 62)

    meta = result.get('_meta', {})
    file_count = meta.get('file_count', 1)

    if file_count and file_count > 1:
        cross = result.get('cross_file_summary', {})
        print(f"  Files:            {meta.get('files_succeeded', 0)} OK, {meta.get('files_failed', 0)} failed")
        print(f"  Tables found:     {cross.get('total_tables_found', 0)} ({cross.get('total_financial_tables', 0)} financial)")
        print(f"  Line items:       {cross.get('total_line_items', 0)}")
        print(f"  Avg completeness: {cross.get('avg_extraction_completeness', 0)}%")
    else:
        assessment = result.get('overall_assessment', {})
        completeness = assessment.get('extraction_completeness', {})
        print(f"  Tables found:     {assessment.get('total_tables_found', 0)} ({assessment.get('financial_tables', 0)} financial)")
        print(f"  Line items:       {assessment.get('total_line_items', 0)}")
        print(f"  Completeness:     {completeness.get('overall', 0)}%")

        suggestions = assessment.get('parser_suggestions', [])
        if suggestions:
            print()
            print("  Parser notes:")
            for s in suggestions[:5]:
                print(f"    - {s}")

    print()
    print("-" * 62)
    print(f"  Saved locally:  {local_path}")
    if github_url and not github_url.startswith("("):
        print(f"  On GitHub:      {github_url}")
    else:
        print(f"  GitHub:         {github_url}")
    print()
    print("  This JSON is privacy-safe — no dollar amounts,")
    print("  company names, or descriptions are included.")
    print("=" * 62)
    print()


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

def main():
    print_banner()

    # Step 1: Find AEGIS
    print("  [1/5] Looking for AEGIS install...", end=" ", flush=True)
    aegis_dir = find_aegis_install()

    if not aegis_dir:
        print("NOT FOUND")
        print()
        print("  Could not find AEGIS automatically.")
        print("  Enter the path to your AEGIS folder:")
        aegis_dir = input("  AEGIS path: ").strip().strip('"').strip("'")
        if not aegis_dir or not os.path.isdir(aegis_dir):
            print("  Invalid path. Exiting.")
            input("\n  Press Enter to close...")
            sys.exit(1)
        parser_check = os.path.join(aegis_dir, "proposal_compare", "parser.py")
        if not os.path.isfile(parser_check):
            print(f"  proposal_compare/parser.py not found in {aegis_dir}")
            input("\n  Press Enter to close...")
            sys.exit(1)

    print(f"found!")
    print(f"    {aegis_dir}")
    print()

    # Step 2: Load parser only (analysis logic is in this script)
    print("  [2/5] Loading parser...", end=" ", flush=True)
    parser_modules = load_parser(aegis_dir)
    if not parser_modules['available']:
        print("FAILED")
        print()
        print("  Could not load the proposal parser.")
        print()
        print("  ERROR DETAILS:")
        print(f"  {parser_modules.get('error', 'unknown')}")
        print()
        if 'traceback' in parser_modules:
            print("  FULL ERROR:")
            for line in parser_modules['traceback'].split('\n'):
                print(f"    {line}")
        print()
        print("  COMMON FIXES:")
        print("    1. Make sure AEGIS is installed and working")
        print("    2. Try: pip install openpyxl python-docx pdfplumber")
        print()
        input("  Press Enter to close...")
        sys.exit(1)
    print("OK")
    print()

    # Step 3: Load GitHub token
    print("  [3/5] GitHub token...", end=" ", flush=True)
    has_token = load_token()
    if has_token:
        print("ready")
    else:
        print("not found (results saved locally only)")
    print()

    # Step 4: Pick files
    print("  [4/5] Opening file picker...")
    print()
    files = open_file_picker()

    if not files:
        print("  No files selected.")
        input("\n  Press Enter to close...")
        sys.exit(0)

    # Filter to supported types
    supported = parser_modules.get('SUPPORTED_EXTENSIONS', {'.xlsx', '.xls', '.docx', '.pdf'})
    valid_files = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in supported:
            valid_files.append(f)
        else:
            print(f"  Skipping: {os.path.basename(f)} (unsupported type)")

    if not valid_files:
        print("  No supported files selected.")
        input("\n  Press Enter to close...")
        sys.exit(0)

    print(f"  Selected {len(valid_files)} file(s):")
    for f in valid_files:
        print(f"    - {os.path.basename(f)}")
    print()

    # Step 5: Analyze
    print("  [5/5] Analyzing...")
    result, output_name = run_analysis(valid_files, parser_modules)

    if result is None:
        print("  Analysis failed.")
        input("\n  Press Enter to close...")
        sys.exit(1)

    # Save local copy
    json_str = json.dumps(result, indent=2, ensure_ascii=False)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(script_dir, output_name)
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(json_str)

    # Upload to GitHub
    github_url = "(no token — saved locally only)"
    if _github_token:
        print()
        print("  Uploading to GitHub...", end=" ", flush=True)
        try:
            github_url = upload_to_github(json_str, output_name)
            print("done!")
        except Exception as e:
            print(f"failed: {e}")
            github_url = f"(upload failed: {e})"

    print_summary(result, github_url, local_path)
    input("  Press Enter to close...")


if __name__ == '__main__':
    main()
