"""
AEGIS Proposal Structure Analyzer — Privacy-Safe Structural Analysis

Runs the existing ProposalParser on a document, then produces a REDACTED
structural report that reveals the document's layout, table shapes, column
patterns, category distribution, and extraction diagnostics WITHOUT exposing:
  - Actual dollar amounts or financial figures
  - Company names, vendor identities, or personnel names
  - Proprietary line-item descriptions
  - Dates or contract-specific metadata

Purpose: Allow users to share parsing results with developers for accuracy
refinement without disclosing confidential proposal content.

Output is a JSON structure with:
  - file_info: type, size, page count
  - tables[]: shape (rows × cols), header names, column role inference,
              financial detection result, total row presence, data patterns
  - line_items_summary: count, category distribution, confidence histogram,
                        description length stats, amount range bucket, field coverage
  - extraction_diagnostics: notes, strategy used, warnings
  - column_analysis: per-table column role detection details
"""

import os
import re
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Amount bucketing (hides real values)
# ──────────────────────────────────────────────

def _bucket_amount(amount: Optional[float]) -> str:
    """Convert a dollar amount into a non-revealing bucket label."""
    if amount is None:
        return 'none'
    a = abs(amount)
    if a == 0:
        return '$0'
    elif a < 100:
        return '$1-$99'
    elif a < 1000:
        return '$100-$999'
    elif a < 10000:
        return '$1K-$9.9K'
    elif a < 100000:
        return '$10K-$99K'
    elif a < 1000000:
        return '$100K-$999K'
    elif a < 10000000:
        return '$1M-$9.9M'
    elif a < 100000000:
        return '$10M-$99M'
    else:
        return '$100M+'


def _bucket_count(count: Optional[float]) -> str:
    """Bucket a quantity/count into a range."""
    if count is None:
        return 'none'
    c = abs(count)
    if c == 0:
        return '0'
    elif c < 10:
        return '1-9'
    elif c < 100:
        return '10-99'
    elif c < 1000:
        return '100-999'
    else:
        return '1000+'


# ──────────────────────────────────────────────
# Description pattern analysis (no actual text)
# ──────────────────────────────────────────────

def _analyze_description_pattern(desc: str) -> Dict[str, Any]:
    """Analyze a line item description's structural characteristics without revealing content."""
    if not desc:
        return {'length': 0, 'word_count': 0, 'has_numbers': False, 'pattern': 'empty'}

    words = desc.split()
    word_count = len(words)
    char_count = len(desc)
    has_numbers = bool(re.search(r'\d', desc))
    has_parentheses = '(' in desc and ')' in desc
    has_dash = '-' in desc or '–' in desc
    has_comma = ',' in desc

    # Classify description pattern
    if char_count < 10:
        pattern = 'very_short'
    elif char_count < 30:
        pattern = 'short_label'
    elif char_count < 80:
        pattern = 'medium_description'
    elif char_count < 200:
        pattern = 'long_description'
    else:
        pattern = 'very_long_text'

    return {
        'length': char_count,
        'word_count': word_count,
        'has_numbers': has_numbers,
        'has_parentheses': has_parentheses,
        'has_dash': has_dash,
        'has_comma': has_comma,
        'pattern': pattern,
    }


def _classify_header(header: str) -> str:
    """Classify a column header into a generic role without revealing exact text.

    Returns the header role (e.g., 'description', 'amount', 'quantity') or
    the original header if it's a standard non-proprietary term.
    """
    if not header or not header.strip():
        return '(empty)'

    h = header.strip().lower()

    # Standard financial/table headers — safe to show as-is
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
        'total labor', 'total material', 'total travel', 'total odc',
        'wbs', 'wbs element', 'task number', 'task no',
        'part number', 'part no', 'sku', 'model',
        'manufacturer', 'vendor', 'supplier',
        'sin', 'schedule', 'contract', 'gsa price', 'list price',
        'retail price', 'msrp', 'your price', 'discount',
        'notes', 'remarks', 'comments',
    }

    if h in safe_headers:
        return header.strip()

    # Check if it matches known patterns
    if any(kw in h for kw in ['desc', 'item', 'task', 'service', 'product', 'deliverable', 'scope', 'work']):
        return f'description_variant ({len(header)} chars)'
    if any(kw in h for kw in ['cost', 'price', 'amount', 'total', 'value', 'charge', 'extended']):
        return f'amount_variant ({len(header)} chars)'
    if any(kw in h for kw in ['qty', 'quantity', 'hours', 'units', 'count']):
        return f'quantity_variant ({len(header)} chars)'
    if any(kw in h for kw in ['rate', 'unit price', 'per', 'hourly']):
        return f'rate_variant ({len(header)} chars)'

    # Unknown header — redact but show length and word count
    words = header.strip().split()
    return f'custom_header ({len(words)} words, {len(header)} chars)'


# ──────────────────────────────────────────────
# Cell data pattern analysis
# ──────────────────────────────────────────────

def _analyze_cell_patterns(rows: List[List[str]], max_rows: int = 20) -> List[Dict[str, Any]]:
    """Analyze data patterns in each column without revealing actual values.

    Returns per-column stats:
    - dominant_type: 'dollar', 'numeric', 'text', 'mixed', 'empty'
    - fill_rate: percentage of non-empty cells
    - dollar_pattern_count: cells with $ prefix
    - numeric_count: pure numeric cells
    - text_count: cells with alphabetic content
    - avg_text_length: average character count for text cells
    - sample_lengths: distribution of cell text lengths
    """
    if not rows:
        return []

    num_cols = max(len(r) for r in rows) if rows else 0
    sample = rows[:max_rows]
    total_rows = len(sample)

    col_analyses = []
    for col_idx in range(num_cols):
        stats = {
            'column_index': col_idx,
            'fill_rate': 0.0,
            'dollar_pattern_count': 0,
            'numeric_count': 0,
            'text_count': 0,
            'empty_count': 0,
            'avg_text_length': 0.0,
            'min_text_length': 999999,
            'max_text_length': 0,
            'dominant_type': 'empty',
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

            # Dollar pattern
            if re.search(r'\$\s*[\d,]+', cell):
                stats['dollar_pattern_count'] += 1
            # Numeric (including comma-separated)
            elif re.match(r'^[\d,]+(?:\.\d+)?$', cell.replace(',', '').strip()):
                stats['numeric_count'] += 1
            # Text (has alphabetic chars)
            elif sum(1 for c in cell if c.isalpha()) > 0:
                stats['text_count'] += 1

        if text_lengths:
            stats['avg_text_length'] = round(sum(text_lengths) / len(text_lengths), 1)
            stats['min_text_length'] = min(text_lengths)
            stats['max_text_length'] = max(text_lengths)
        else:
            stats['min_text_length'] = 0

        filled = total_rows - stats['empty_count']
        stats['fill_rate'] = round(filled / total_rows * 100, 1) if total_rows > 0 else 0

        # Determine dominant type
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


# ──────────────────────────────────────────────
# Main structure analysis function
# ──────────────────────────────────────────────

def analyze_proposal_structure(filepath: str) -> Dict[str, Any]:
    """Parse a proposal and return a REDACTED structural analysis.

    Runs the existing parser, then strips all proprietary data while
    preserving structural metadata useful for parser accuracy refinement.

    Returns a JSON-serializable dict with:
    - file_info: type, size, page count, anonymized hash
    - tables: structural shape and column pattern analysis for each table
    - line_items_summary: aggregate statistics (no individual items)
    - extraction_diagnostics: parser notes, strategy, warnings
    - category_analysis: distribution of detected categories
    - overall_assessment: parser confidence metrics and coverage stats
    """
    from .parser import parse_proposal, CATEGORY_PATTERNS

    result = {
        '_meta': {
            'tool': 'AEGIS Proposal Structure Analyzer',
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

    # ── File info (safe metadata) ──
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()
    file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

    # Create anonymous hash so we can track the same file across runs
    file_hash = hashlib.sha256(f'{file_size}_{ext}'.encode()).hexdigest()[:12]

    result['file_info'] = {
        'file_type': ext.lstrip('.'),
        'file_size_bytes': file_size,
        'file_size_label': _format_file_size(file_size),
        'file_hash': file_hash,  # Non-reversible, size+ext based only
    }

    # ── Run the parser ──
    try:
        proposal = parse_proposal(filepath)
    except Exception as e:
        result['extraction_diagnostics'] = {
            'error': str(type(e).__name__),
            'error_message_redacted': _redact_error_message(str(e)),
        }
        return result

    result['file_info']['page_count'] = proposal.page_count

    # ── Table structure analysis ──
    for tbl in proposal.tables:
        table_info = {
            'table_index': tbl.table_index,
            'source': tbl.source,
            'shape': {
                'rows': len(tbl.rows),
                'columns': len(tbl.headers) if tbl.headers else (max(len(r) for r in tbl.rows) if tbl.rows else 0),
            },
            'headers': [_classify_header(h) for h in tbl.headers],
            'headers_are_generic': _check_generic_headers(tbl.headers),
            'has_financial_data': tbl.has_financial_data,
            'has_total_row': tbl.total_row_index is not None,
            'total_row_position': _total_row_position(tbl.total_row_index, len(tbl.rows)),
            'column_data_patterns': _analyze_cell_patterns(tbl.rows),
        }

        # If there are rows, analyze the row patterns
        if tbl.rows:
            row_lengths = [len(r) for r in tbl.rows]
            table_info['row_analysis'] = {
                'min_cells_per_row': min(row_lengths),
                'max_cells_per_row': max(row_lengths),
                'consistent_width': min(row_lengths) == max(row_lengths),
                'empty_row_count': sum(1 for r in tbl.rows if not any(str(c).strip() for c in r)),
            }

        result['tables'].append(table_info)

    # ── Line items summary (aggregate only, no individual items) ──
    items = proposal.line_items
    if items:
        # Category distribution
        cat_dist = {}
        for li in items:
            cat = li.category or 'Uncategorized'
            cat_dist[cat] = cat_dist.get(cat, 0) + 1

        # Confidence distribution
        conf_buckets = {'high (0.9-1.0)': 0, 'medium (0.7-0.89)': 0, 'low (<0.7)': 0}
        for li in items:
            if li.confidence >= 0.9:
                conf_buckets['high (0.9-1.0)'] += 1
            elif li.confidence >= 0.7:
                conf_buckets['medium (0.7-0.89)'] += 1
            else:
                conf_buckets['low (<0.7)'] += 1

        # Amount bucket distribution
        amount_buckets = {}
        for li in items:
            bucket = _bucket_amount(li.amount)
            amount_buckets[bucket] = amount_buckets.get(bucket, 0) + 1

        # Description pattern analysis
        desc_patterns = {}
        desc_lengths = []
        desc_word_counts = []
        for li in items:
            analysis = _analyze_description_pattern(li.description)
            p = analysis['pattern']
            desc_patterns[p] = desc_patterns.get(p, 0) + 1
            desc_lengths.append(analysis['length'])
            desc_word_counts.append(analysis['word_count'])

        # Field coverage (which fields are populated)
        field_coverage = {
            'has_description': sum(1 for li in items if li.description and len(li.description) > 2),
            'has_amount': sum(1 for li in items if li.amount is not None),
            'has_quantity': sum(1 for li in items if li.quantity is not None),
            'has_unit_price': sum(1 for li in items if li.unit_price is not None),
            'has_category': sum(1 for li in items if li.category and li.category != 'Other'),
            'has_source_sheet': sum(1 for li in items if li.source_sheet),
        }

        # Source table distribution
        source_tables = {}
        for li in items:
            key = f'table_{li.table_index}'
            source_tables[key] = source_tables.get(key, 0) + 1

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
                'median': sorted(desc_lengths)[len(desc_lengths) // 2] if desc_lengths else 0,
            },
            'description_word_count_stats': {
                'min': min(desc_word_counts) if desc_word_counts else 0,
                'max': max(desc_word_counts) if desc_word_counts else 0,
                'avg': round(sum(desc_word_counts) / len(desc_word_counts), 1) if desc_word_counts else 0,
            },
            'field_coverage': field_coverage,
            'field_coverage_percentages': {
                k: round(v / len(items) * 100, 1) for k, v in field_coverage.items()
            },
            'source_table_distribution': source_tables,
            'total_amount_bucket': _bucket_amount(proposal.total_amount),
        }
    else:
        result['line_items_summary'] = {
            'total_count': 0,
            'note': 'No line items extracted',
        }

    # ── Category analysis ──
    result['category_analysis'] = {
        'detected_categories': list(set(li.category for li in items)) if items else [],
        'supported_categories': list(CATEGORY_PATTERNS.keys()),
        'uncategorized_count': sum(1 for li in items if li.category == 'Other') if items else 0,
        'uncategorized_percentage': round(
            sum(1 for li in items if li.category == 'Other') / len(items) * 100, 1
        ) if items else 0,
    }

    # ── Extraction diagnostics ──
    result['extraction_diagnostics'] = {
        'notes': proposal.extraction_notes,
        'company_detected': bool(proposal.company_name),
        'company_detection_strategy': _detect_company_strategy(proposal.extraction_notes),
        'date_detected': bool(proposal.date),
        'contract_term_detected': bool(proposal.contract_term),
        'contract_term_value': proposal.contract_term or '(none)',
        'total_detected_via': 'total_row' if any('total' in n.lower() for n in proposal.extraction_notes) else (
            'line_item_sum' if proposal.total_amount else 'none'
        ),
        'text_extraction_available': bool(proposal.extraction_text),
        'text_length': len(proposal.extraction_text) if proposal.extraction_text else 0,
    }

    # ── Column inference details (per financial table) ──
    from .parser import _infer_columns_from_data, _headers_are_generic
    for tbl in proposal.tables:
        if tbl.has_financial_data:
            inferred = _infer_columns_from_data(tbl.headers, tbl.rows)
            result['column_inference_details'].append({
                'table_index': tbl.table_index,
                'source': tbl.source,
                'headers_generic': _headers_are_generic(tbl.headers),
                'inferred_roles': {
                    'description_col': inferred.get('desc_col'),
                    'amount_col': inferred.get('amount_col'),
                    'quantity_col': inferred.get('qty_col'),
                    'unit_price_col': inferred.get('unit_price_col'),
                },
                'header_count': len(tbl.headers),
                'data_row_count': len(tbl.rows),
            })

    # ── Overall assessment ──
    total_tables = len(proposal.tables)
    financial_tables = sum(1 for t in proposal.tables if t.has_financial_data)
    non_financial_tables = total_tables - financial_tables

    result['overall_assessment'] = {
        'total_tables_found': total_tables,
        'financial_tables': financial_tables,
        'non_financial_tables': non_financial_tables,
        'total_line_items': len(items),
        'avg_confidence': round(
            sum(li.confidence for li in items) / len(items), 3
        ) if items else 0,
        'has_total_amount': proposal.total_amount is not None,
        'has_company_name': bool(proposal.company_name),
        'has_date': bool(proposal.date),
        'has_contract_term': bool(proposal.contract_term),
        'extraction_completeness': _compute_completeness_score(proposal),
        'parser_suggestions': _generate_suggestions(proposal, result),
    }

    return result


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────

def _format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.1f} KB'
    else:
        return f'{size_bytes / (1024 * 1024):.1f} MB'


def _check_generic_headers(headers: List[str]) -> bool:
    """Check if headers are generic auto-generated names."""
    if not headers:
        return True
    generic = re.compile(r'^(col\s*\d+|column\s*\d+|\d+|unnamed.*|)$', re.IGNORECASE)
    count = sum(1 for h in headers if generic.match(h.strip()))
    return count > len(headers) * 0.6


def _total_row_position(total_idx: Optional[int], total_rows: int) -> str:
    """Describe where the total row is positioned."""
    if total_idx is None:
        return 'none'
    if total_rows == 0:
        return 'none'
    ratio = total_idx / total_rows
    if ratio > 0.9:
        return 'bottom (last 10%)'
    elif ratio > 0.7:
        return 'near bottom (70-90%)'
    elif ratio > 0.5:
        return 'middle-bottom (50-70%)'
    else:
        return 'upper half (<50%)'


def _detect_company_strategy(notes: List[str]) -> str:
    """Determine which company detection strategy was used from notes."""
    for note in notes:
        if 'Company:' in note:
            return 'text_extraction'
    return 'unknown_or_filename'


def _redact_error_message(msg: str) -> str:
    """Redact file paths and potentially sensitive info from error messages."""
    # Remove file paths
    msg = re.sub(r'[A-Z]:\\[^\s]+', '[PATH]', msg)
    msg = re.sub(r'/[^\s]+/', '[PATH]/', msg)
    # Remove anything that looks like a filename with extension
    msg = re.sub(r'\b\w+\.(xlsx|docx|pdf|xls|doc)\b', '[FILE]', msg, flags=re.IGNORECASE)
    return msg


def _compute_completeness_score(proposal) -> Dict[str, Any]:
    """Compute a completeness score for the extraction."""
    scores = {}

    # Table extraction (0-100)
    if proposal.tables:
        financial = sum(1 for t in proposal.tables if t.has_financial_data)
        scores['table_extraction'] = min(100, financial * 25)  # 4+ financial tables = 100
    else:
        scores['table_extraction'] = 0

    # Line item extraction (0-100)
    if proposal.line_items:
        scores['line_item_extraction'] = min(100, len(proposal.line_items) * 5)  # 20+ items = 100
    else:
        scores['line_item_extraction'] = 0

    # Metadata (0-100)
    meta_score = 0
    if proposal.company_name:
        meta_score += 30
    if proposal.date:
        meta_score += 20
    if proposal.contract_term:
        meta_score += 25
    if proposal.total_amount is not None:
        meta_score += 25
    scores['metadata_extraction'] = meta_score

    # Field coverage (0-100)
    if proposal.line_items:
        items = proposal.line_items
        has_amount = sum(1 for li in items if li.amount is not None) / len(items)
        has_desc = sum(1 for li in items if li.description) / len(items)
        has_cat = sum(1 for li in items if li.category != 'Other') / len(items)
        scores['field_coverage'] = round((has_amount + has_desc + has_cat) / 3 * 100, 1)
    else:
        scores['field_coverage'] = 0

    # Overall
    weights = {'table_extraction': 0.3, 'line_item_extraction': 0.3,
               'metadata_extraction': 0.2, 'field_coverage': 0.2}
    scores['overall'] = round(sum(scores[k] * weights[k] for k in weights), 1)

    return scores


def _generate_suggestions(proposal, analysis: Dict) -> List[str]:
    """Generate parser improvement suggestions based on the structural analysis."""
    suggestions = []

    # No tables found
    if not proposal.tables:
        suggestions.append('CRITICAL: No tables detected — parser may need different extraction strategy for this document format')

    # Tables found but no financial data
    if proposal.tables and not any(t.has_financial_data for t in proposal.tables):
        suggestions.append('Tables found but none flagged as financial — header keywords or data patterns may not match expected financial indicators')

    # No line items despite financial tables
    financial_tables = [t for t in proposal.tables if t.has_financial_data]
    if financial_tables and not proposal.line_items:
        suggestions.append('Financial tables detected but no line items extracted — column role detection may be failing (check column_inference_details)')

    # Low confidence items
    if proposal.line_items:
        low_conf = sum(1 for li in proposal.line_items if li.confidence < 0.7)
        if low_conf > len(proposal.line_items) * 0.3:
            suggestions.append(f'{low_conf} of {len(proposal.line_items)} items have low confidence (<0.7) — column inference may be unreliable')

    # High "Other" category percentage
    if proposal.line_items:
        other_count = sum(1 for li in proposal.line_items if li.category == 'Other')
        if other_count > len(proposal.line_items) * 0.5:
            suggestions.append(f'{other_count} of {len(proposal.line_items)} items categorized as "Other" — description text may not match CATEGORY_PATTERNS')

    # No company name
    if not proposal.company_name:
        suggestions.append('Company name not detected — document may lack standard identification patterns')

    # No total amount
    if proposal.total_amount is None:
        suggestions.append('No total amount found — document may lack a "Total" row or inline total')

    # Generic headers detected in financial tables
    for tbl in proposal.tables:
        if tbl.has_financial_data and _check_generic_headers(tbl.headers):
            suggestions.append(f'Table {tbl.table_index} ({tbl.source}) has generic headers — column roles inferred from data patterns (lower accuracy)')
            break

    # Inconsistent row widths
    for tbl_info in analysis.get('tables', []):
        row_analysis = tbl_info.get('row_analysis', {})
        if not row_analysis.get('consistent_width', True):
            suggestions.append(f'Table {tbl_info["table_index"]} has inconsistent row widths ({row_analysis.get("min_cells_per_row")}-{row_analysis.get("max_cells_per_row")} cols) — merged cells or irregular layout')
            break

    # No contract term
    if not proposal.contract_term:
        suggestions.append('Contract term not detected — document may not contain standard period-of-performance language')

    if not suggestions:
        suggestions.append('Extraction looks complete — no issues detected')

    return suggestions


# ──────────────────────────────────────────────
# Convenience: Analyze and export to JSON file
# ──────────────────────────────────────────────

def analyze_and_export(filepath: str, output_path: str = None) -> str:
    """Analyze a proposal and write the structure report to a JSON file.

    Args:
        filepath: Path to the proposal document (XLSX, DOCX, or PDF)
        output_path: Optional output file path. If None, creates one next to the input file.

    Returns:
        Path to the generated JSON report.
    """
    analysis = analyze_proposal_structure(filepath)

    if output_path is None:
        base = os.path.splitext(filepath)[0]
        output_path = f'{base}_structure_analysis.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    logger.info(f'[AEGIS StructureAnalyzer] Wrote structure report to {output_path}')
    return output_path
