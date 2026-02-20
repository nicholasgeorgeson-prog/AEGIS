"""
AEGIS Proposal Comparison Engine — Aligns and compares financial data across proposals.

Pure extraction/comparison — NO AI/LLM. Compares only what was extracted.

Key features:
- Aligns line items across proposals by description similarity
- Builds side-by-side comparison matrix
- Highlights price differences and missing items
- Calculates cost variances and percentages
- Exports to HTML table and PDF
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from difflib import SequenceMatcher

from .parser import ProposalData, LineItem

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Data classes for comparison results
# ──────────────────────────────────────────────

@dataclass
class AlignedItem:
    """A single row in the comparison matrix — one line item aligned across proposals."""
    description: str = ''          # Canonical description (from first proposal with this item)
    category: str = ''
    amounts: Dict[str, Optional[float]] = field(default_factory=dict)  # proposal_id → amount
    amounts_raw: Dict[str, str] = field(default_factory=dict)          # proposal_id → raw string
    quantities: Dict[str, Optional[float]] = field(default_factory=dict)
    unit_prices: Dict[str, Optional[float]] = field(default_factory=dict)

    # Comparison metrics
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    avg_amount: Optional[float] = None
    variance_pct: Optional[float] = None  # (max - min) / min * 100
    lowest_bidder: str = ''                # Proposal ID with lowest amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            'description': self.description,
            'category': self.category,
            'amounts': self.amounts,
            'amounts_raw': self.amounts_raw,
            'quantities': self.quantities,
            'unit_prices': self.unit_prices,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'avg_amount': self.avg_amount,
            'variance_pct': self.variance_pct,
            'lowest_bidder': self.lowest_bidder,
        }


@dataclass
class CategorySummary:
    """Summary of costs by category across proposals."""
    category: str = ''
    totals: Dict[str, float] = field(default_factory=dict)  # proposal_id → category total
    item_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'category': self.category,
            'totals': self.totals,
            'item_count': self.item_count,
        }


@dataclass
class ComparisonResult:
    """Complete comparison of multiple proposals."""
    proposals: List[Dict[str, Any]] = field(default_factory=list)
    aligned_items: List[AlignedItem] = field(default_factory=list)
    category_summaries: List[CategorySummary] = field(default_factory=list)
    unmatched_items: Dict[str, List[Dict]] = field(default_factory=dict)
    totals: Dict[str, Optional[float]] = field(default_factory=dict)
    totals_raw: Dict[str, str] = field(default_factory=dict)

    # Overall comparison metrics
    lowest_total_proposal: str = ''
    highest_total_proposal: str = ''
    total_variance_pct: Optional[float] = None

    # Advanced analytics
    red_flags: Dict[str, List[Dict]] = field(default_factory=dict)
    heatmap: Dict[str, Any] = field(default_factory=dict)
    rate_analysis: Dict[str, Any] = field(default_factory=dict)
    cost_breakdown: Dict[str, Any] = field(default_factory=dict)
    vendor_scores: Dict[str, Dict] = field(default_factory=dict)
    executive_summary: Dict[str, Any] = field(default_factory=dict)

    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposals': self.proposals,
            'aligned_items': [ai.to_dict() for ai in self.aligned_items],
            'category_summaries': [cs.to_dict() for cs in self.category_summaries],
            'unmatched_items': self.unmatched_items,
            'totals': self.totals,
            'totals_raw': self.totals_raw,
            'lowest_total_proposal': self.lowest_total_proposal,
            'highest_total_proposal': self.highest_total_proposal,
            'total_variance_pct': self.total_variance_pct,
            'red_flags': self.red_flags,
            'heatmap': self.heatmap,
            'rate_analysis': self.rate_analysis,
            'cost_breakdown': self.cost_breakdown,
            'vendor_scores': self.vendor_scores,
            'executive_summary': self.executive_summary,
            'notes': self.notes,
        }


# ──────────────────────────────────────────────
# Text similarity for line item alignment
# ──────────────────────────────────────────────

def _normalize_description(desc: str) -> str:
    """Normalize a description for comparison."""
    desc = desc.lower().strip()
    # Remove common noise words
    desc = re.sub(r'\b(the|a|an|of|for|and|or|in|to|with|per)\b', ' ', desc)
    # Remove extra whitespace
    desc = re.sub(r'\s+', ' ', desc).strip()
    # Remove trailing numbers/IDs
    desc = re.sub(r'\s*#?\d+\s*$', '', desc)
    return desc


def _description_similarity(desc1: str, desc2: str) -> float:
    """Calculate similarity between two line item descriptions (0.0 to 1.0)."""
    norm1 = _normalize_description(desc1)
    norm2 = _normalize_description(desc2)

    if not norm1 or not norm2:
        return 0.0

    # Exact match after normalization
    if norm1 == norm2:
        return 1.0

    # SequenceMatcher ratio
    ratio = SequenceMatcher(None, norm1, norm2).ratio()

    # Boost if one contains the other
    if norm1 in norm2 or norm2 in norm1:
        ratio = max(ratio, 0.85)

    # Word overlap bonus
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    if words1 and words2:
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        jaccard = overlap / union
        ratio = max(ratio, jaccard * 0.9)

    return ratio


# ──────────────────────────────────────────────
# Core comparison logic
# ──────────────────────────────────────────────

MATCH_THRESHOLD = 0.55  # Minimum similarity to consider a match


def align_line_items(proposals: List[ProposalData]) -> Tuple[List[AlignedItem], Dict[str, List[Dict]]]:
    """Align line items across multiple proposals by description similarity.

    Returns:
        aligned: List of AlignedItem objects with amounts from each proposal
        unmatched: Dict of proposal_id → list of unmatched items
    """
    if not proposals:
        return [], {}

    # Create proposal IDs
    prop_ids = []
    for p in proposals:
        pid = p.company_name or p.filename
        # Ensure unique IDs
        counter = 1
        base_pid = pid
        while pid in prop_ids:
            pid = f'{base_pid} ({counter})'
            counter += 1
        prop_ids.append(pid)

    # Build the alignment using the first proposal as anchor
    # Then merge in items from subsequent proposals
    aligned: List[AlignedItem] = []
    unmatched: Dict[str, List[Dict]] = {pid: [] for pid in prop_ids}

    # Start with all items from first proposal
    first_items = proposals[0].line_items
    for item in first_items:
        ai = AlignedItem(
            description=item.description,
            category=item.category,
            amounts={prop_ids[0]: item.amount},
            amounts_raw={prop_ids[0]: item.amount_raw},
            quantities={prop_ids[0]: item.quantity},
            unit_prices={prop_ids[0]: item.unit_price},
        )
        aligned.append(ai)

    # For each subsequent proposal, try to match items to existing aligned items
    for p_idx in range(1, len(proposals)):
        pid = prop_ids[p_idx]
        prop_items = proposals[p_idx].line_items
        matched_aligned_indices = set()

        for item in prop_items:
            best_match_idx = -1
            best_score = 0.0

            for ai_idx, ai in enumerate(aligned):
                if ai_idx in matched_aligned_indices:
                    continue  # Already matched by another item from this proposal

                # Also check category match as a signal
                score = _description_similarity(item.description, ai.description)

                # Category match bonus
                if item.category == ai.category and item.category != 'Other':
                    score += 0.1

                if score > best_score and score >= MATCH_THRESHOLD:
                    best_score = score
                    best_match_idx = ai_idx

            if best_match_idx >= 0:
                # Matched — add this proposal's data to the aligned item
                ai = aligned[best_match_idx]
                ai.amounts[pid] = item.amount
                ai.amounts_raw[pid] = item.amount_raw
                ai.quantities[pid] = item.quantity
                ai.unit_prices[pid] = item.unit_price
                matched_aligned_indices.add(best_match_idx)
            else:
                # No match — add as new aligned item (this proposal only)
                ai = AlignedItem(
                    description=item.description,
                    category=item.category,
                    amounts={pid: item.amount},
                    amounts_raw={pid: item.amount_raw},
                    quantities={pid: item.quantity},
                    unit_prices={pid: item.unit_price},
                )
                aligned.append(ai)

    # Calculate comparison metrics for each aligned item
    for ai in aligned:
        valid_amounts = [a for a in ai.amounts.values() if a is not None and a > 0]
        if valid_amounts:
            ai.min_amount = min(valid_amounts)
            ai.max_amount = max(valid_amounts)
            ai.avg_amount = sum(valid_amounts) / len(valid_amounts)

            if ai.min_amount > 0:
                ai.variance_pct = round((ai.max_amount - ai.min_amount) / ai.min_amount * 100, 1)

            # Find lowest bidder
            for pid, amount in ai.amounts.items():
                if amount == ai.min_amount:
                    ai.lowest_bidder = pid
                    break

    return aligned, unmatched


def build_category_summaries(
    aligned_items: List[AlignedItem],
    prop_ids: List[str]
) -> List[CategorySummary]:
    """Build category-level cost summaries from aligned items."""
    category_data: Dict[str, Dict[str, float]] = {}

    for ai in aligned_items:
        cat = ai.category or 'Other'
        if cat not in category_data:
            category_data[cat] = {pid: 0.0 for pid in prop_ids}

        for pid, amount in ai.amounts.items():
            if amount is not None:
                category_data[cat][pid] = category_data[cat].get(pid, 0.0) + amount

    summaries = []
    for cat, totals in sorted(category_data.items()):
        item_count = sum(1 for ai in aligned_items if (ai.category or 'Other') == cat)
        summaries.append(CategorySummary(
            category=cat,
            totals=totals,
            item_count=item_count,
        ))

    return summaries


def compare_proposals(proposals: List[ProposalData]) -> ComparisonResult:
    """Compare multiple proposals and produce a comprehensive comparison result.

    This is the main entry point for the comparison engine.
    """
    result = ComparisonResult()

    if len(proposals) < 2:
        result.notes.append('Need at least 2 proposals to compare')
        return result

    # Create proposal IDs
    prop_ids = []
    for p in proposals:
        pid = p.company_name or p.filename
        counter = 1
        base_pid = pid
        while pid in prop_ids:
            pid = f'{base_pid} ({counter})'
            counter += 1
        prop_ids.append(pid)

    # Build proposal summaries
    for i, (p, pid) in enumerate(zip(proposals, prop_ids)):
        result.proposals.append({
            'id': pid,
            'filename': p.filename,
            'company_name': p.company_name,
            'proposal_title': p.proposal_title,
            'date': p.date,
            'file_type': p.file_type,
            'total_amount': p.total_amount,
            'total_raw': p.total_raw,
            'line_item_count': len(p.line_items),
            'table_count': len(p.tables),
            'extraction_notes': p.extraction_notes,
        })

    # Align line items
    result.aligned_items, result.unmatched_items = align_line_items(proposals)

    # Category summaries
    result.category_summaries = build_category_summaries(result.aligned_items, prop_ids)

    # Grand totals
    for i, (p, pid) in enumerate(zip(proposals, prop_ids)):
        result.totals[pid] = p.total_amount
        result.totals_raw[pid] = p.total_raw

    # Overall metrics
    valid_totals = {pid: t for pid, t in result.totals.items() if t is not None and t > 0}
    if valid_totals:
        min_pid = min(valid_totals, key=valid_totals.get)
        max_pid = max(valid_totals, key=valid_totals.get)
        result.lowest_total_proposal = min_pid
        result.highest_total_proposal = max_pid

        min_total = valid_totals[min_pid]
        max_total = valid_totals[max_pid]
        if min_total > 0:
            result.total_variance_pct = round((max_total - min_total) / min_total * 100, 1)

    # ── Advanced Analytics ──

    # Red flags
    result.red_flags = detect_red_flags(proposals, prop_ids, result.aligned_items, result.totals)

    # Heatmap data (variance by line item × vendor)
    result.heatmap = build_heatmap_data(result.aligned_items, prop_ids)

    # Rate analysis
    result.rate_analysis = build_rate_analysis(proposals, prop_ids)

    # Cost element breakdown (waterfall chart data)
    result.cost_breakdown = build_cost_breakdown(result.category_summaries, prop_ids, result.totals)

    # Vendor scoring
    result.vendor_scores = compute_vendor_scores(
        proposals, prop_ids, result.aligned_items,
        result.red_flags, result.totals
    )

    # Executive summary
    result.executive_summary = build_executive_summary(
        proposals, prop_ids, result
    )

    # Summary notes
    result.notes.append(f'Compared {len(proposals)} proposals')
    result.notes.append(f'{len(result.aligned_items)} line items aligned')
    if result.lowest_total_proposal:
        result.notes.append(
            f'Lowest total: {result.lowest_total_proposal} '
            f'({result.totals_raw.get(result.lowest_total_proposal, "N/A")})'
        )
    if result.total_variance_pct is not None:
        result.notes.append(f'Total cost variance: {result.total_variance_pct}%')
    if result.red_flags:
        total_flags = sum(len(flags) for flags in result.red_flags.values())
        result.notes.append(f'{total_flags} red flags detected across all proposals')

    return result


# ──────────────────────────────────────────────
# Red Flag Detection Engine
# ──────────────────────────────────────────────

RED_FLAG_SEVERITY = {
    'critical': 3,
    'warning': 2,
    'info': 1,
}


def detect_red_flags(
    proposals: List[ProposalData],
    prop_ids: List[str],
    aligned_items: List[AlignedItem],
    totals: Dict[str, Optional[float]]
) -> Dict[str, List[Dict]]:
    """Detect financial red flags in each proposal."""
    flags: Dict[str, List[Dict]] = {pid: [] for pid in prop_ids}

    for p_idx, (proposal, pid) in enumerate(zip(proposals, prop_ids)):
        # ── 1. Unbalanced Pricing (buy-in risk) ──
        for ai in aligned_items:
            if pid not in ai.amounts or ai.amounts[pid] is None:
                continue
            amt = ai.amounts[pid]
            other_amounts = [a for k, a in ai.amounts.items()
                            if k != pid and a is not None and a > 0]
            if other_amounts and amt > 0:
                avg_others = sum(other_amounts) / len(other_amounts)
                if avg_others > 0 and amt < avg_others * 0.5:
                    flags[pid].append({
                        'type': 'unbalanced_pricing',
                        'severity': 'critical',
                        'title': 'Potential Buy-In Pricing',
                        'detail': f'"{ai.description}" at ${amt:,.0f} is {((avg_others - amt) / avg_others * 100):.0f}% below competitors\' average (${avg_others:,.0f})',
                        'line_item': ai.description,
                    })

        # ── 2. Round Number Syndrome ──
        round_count = 0
        for li in proposal.line_items:
            if li.amount and li.amount >= 1000 and li.amount % 1000 == 0:
                round_count += 1
        if round_count > 0 and len(proposal.line_items) > 0:
            pct = round_count / len(proposal.line_items) * 100
            if pct > 50:
                flags[pid].append({
                    'type': 'round_numbers',
                    'severity': 'warning',
                    'title': 'Round Number Pricing',
                    'detail': f'{round_count} of {len(proposal.line_items)} line items ({pct:.0f}%) are round numbers — may indicate estimates rather than bottoms-up pricing',
                })

        # ── 3. Missing Line Items (scope gap) ──
        total_aligned = len(aligned_items)
        priced_by_vendor = sum(1 for ai in aligned_items
                               if pid in ai.amounts and ai.amounts[pid] is not None)
        missing = total_aligned - priced_by_vendor
        if missing > 0 and total_aligned > 0:
            flags[pid].append({
                'type': 'missing_items',
                'severity': 'critical' if missing > total_aligned * 0.3 else 'warning',
                'title': f'{missing} Missing Line Items',
                'detail': f'Vendor did not price {missing} of {total_aligned} line items — possible scope gap',
            })

        # ── 4. Fee/Profit Rate Check ──
        fee_items = [li for li in proposal.line_items
                     if li.category in ('Fee', 'Overhead')]
        if fee_items and proposal.total_amount and proposal.total_amount > 0:
            fee_total = sum(li.amount for li in fee_items if li.amount)
            fee_pct = fee_total / proposal.total_amount * 100
            if fee_pct > 20:
                flags[pid].append({
                    'type': 'high_fee',
                    'severity': 'warning',
                    'title': f'High Fee/Overhead Rate ({fee_pct:.1f}%)',
                    'detail': f'Fee and overhead items total ${fee_total:,.0f} ({fee_pct:.1f}% of total) — industry norm is 8-15%',
                })

        # ── 5. Extreme Variance on Individual Items ──
        for ai in aligned_items:
            if pid not in ai.amounts or ai.amounts[pid] is None:
                continue
            if ai.variance_pct is not None and ai.variance_pct > 100:
                amt = ai.amounts[pid]
                if amt == ai.max_amount:
                    flags[pid].append({
                        'type': 'extreme_variance',
                        'severity': 'warning',
                        'title': f'Extreme Price Variance on "{ai.description}"',
                        'detail': f'${amt:,.0f} is {ai.variance_pct:.0f}% above the lowest bid — significant cost risk',
                        'line_item': ai.description,
                    })

        # ── 6. Low Line Item Count (sparse proposal) ──
        if len(proposal.line_items) < 3 and len(proposal.tables) > 0:
            flags[pid].append({
                'type': 'sparse_data',
                'severity': 'info',
                'title': 'Limited Financial Detail',
                'detail': f'Only {len(proposal.line_items)} line items extracted — proposal may lack detailed cost breakdown',
            })

        # ── 7. No Total Found (incomplete data) ──
        if proposal.total_amount is None or proposal.total_amount == 0:
            flags[pid].append({
                'type': 'no_total',
                'severity': 'warning',
                'title': 'No Grand Total Detected',
                'detail': 'Could not find an explicit total/grand total in the proposal — amounts may be incomplete',
            })

    # ── Cross-vendor flags (need all vendors processed) ──

    # 8. Identical Pricing (possible collusion indicator)
    if len(prop_ids) >= 2:
        for i in range(len(prop_ids)):
            for j in range(i + 1, len(prop_ids)):
                pid_a, pid_b = prop_ids[i], prop_ids[j]
                matching_items = 0
                total_comparable = 0
                for ai in aligned_items:
                    amt_a = ai.amounts.get(pid_a)
                    amt_b = ai.amounts.get(pid_b)
                    if amt_a is not None and amt_b is not None and amt_a > 0 and amt_b > 0:
                        total_comparable += 1
                        if abs(amt_a - amt_b) < 0.01:
                            matching_items += 1
                if total_comparable >= 3 and matching_items / total_comparable > 0.6:
                    detail = f'{matching_items} of {total_comparable} comparable line items have identical pricing between {pid_a} and {pid_b}'
                    flags[pid_a].append({
                        'type': 'identical_pricing',
                        'severity': 'warning',
                        'title': f'Identical Pricing with {pid_b}',
                        'detail': detail,
                    })
                    flags[pid_b].append({
                        'type': 'identical_pricing',
                        'severity': 'warning',
                        'title': f'Identical Pricing with {pid_a}',
                        'detail': detail,
                    })

    # 9. Missing Categories (scope gap across vendors)
    all_categories = set()
    vendor_categories: Dict[str, set] = {pid: set() for pid in prop_ids}
    for ai in aligned_items:
        cat = ai.category or 'Uncategorized'
        all_categories.add(cat)
        for pid in prop_ids:
            if pid in ai.amounts and ai.amounts[pid] is not None:
                vendor_categories[pid].add(cat)

    if len(all_categories) >= 2:
        for pid in prop_ids:
            missing_cats = all_categories - vendor_categories[pid]
            if missing_cats and len(missing_cats) < len(all_categories):
                flags[pid].append({
                    'type': 'missing_categories',
                    'severity': 'warning' if len(missing_cats) >= 2 else 'info',
                    'title': f'Missing {len(missing_cats)} Cost {"Categories" if len(missing_cats) > 1 else "Category"}',
                    'detail': f'No pricing in: {", ".join(sorted(missing_cats))} — other vendors include these categories',
                })

    # 10. Price Reasonableness (FAR 15.404 inspired — statistical outlier detection)
    import statistics
    for ai in aligned_items:
        valid_amounts = [a for a in ai.amounts.values() if a is not None and a > 0]
        if len(valid_amounts) < 3:
            continue
        mean = statistics.mean(valid_amounts)
        stdev = statistics.stdev(valid_amounts)
        if stdev == 0:
            continue
        for pid in prop_ids:
            amt = ai.amounts.get(pid)
            if amt is None or amt <= 0:
                continue
            z_score = (amt - mean) / stdev
            if abs(z_score) > 2.0:
                direction = 'above' if z_score > 0 else 'below'
                flags[pid].append({
                    'type': 'price_reasonableness',
                    'severity': 'warning',
                    'title': f'Price Outlier on "{ai.description}"',
                    'detail': f'${amt:,.0f} is {abs(z_score):.1f} standard deviations {direction} the mean (${mean:,.0f}) — requires justification per FAR 15.404',
                    'line_item': ai.description,
                })

    return flags


# ──────────────────────────────────────────────
# Heatmap Data Builder
# ──────────────────────────────────────────────

def build_heatmap_data(
    aligned_items: List[AlignedItem],
    prop_ids: List[str]
) -> Dict[str, Any]:
    """Build heatmap data showing deviation from average per line item × vendor.

    Returns:
        {
            'rows': [
                {
                    'description': 'Software Dev',
                    'category': 'Labor',
                    'cells': {
                        'Vendor A': {'amount': 250000, 'deviation_pct': -5.2, 'level': 'low'},
                        'Vendor B': {'amount': 275000, 'deviation_pct': 4.8, 'level': 'mid'},
                    }
                }
            ],
            'prop_ids': ['Vendor A', 'Vendor B']
        }
    """
    rows = []
    for ai in aligned_items:
        valid_amounts = [a for a in ai.amounts.values() if a is not None and a > 0]
        if not valid_amounts:
            continue
        avg = sum(valid_amounts) / len(valid_amounts)
        if avg == 0:
            continue

        cells = {}
        for pid in prop_ids:
            amt = ai.amounts.get(pid)
            if amt is not None and amt > 0:
                dev = (amt - avg) / avg * 100
                # Categorize deviation level for coloring
                if abs(dev) < 5:
                    level = 'neutral'
                elif dev < -15:
                    level = 'very_low'
                elif dev < -5:
                    level = 'low'
                elif dev > 15:
                    level = 'very_high'
                else:
                    level = 'high'
                cells[pid] = {
                    'amount': amt,
                    'deviation_pct': round(dev, 1),
                    'level': level,
                }
            else:
                cells[pid] = {'amount': None, 'deviation_pct': None, 'level': 'missing'}

        rows.append({
            'description': ai.description,
            'category': ai.category,
            'avg': round(avg, 2),
            'cells': cells,
        })

    return {'rows': rows, 'prop_ids': prop_ids}


# ──────────────────────────────────────────────
# Rate Analysis
# ──────────────────────────────────────────────

def build_rate_analysis(
    proposals: List[ProposalData],
    prop_ids: List[str]
) -> Dict[str, Any]:
    """Analyze unit prices/rates across proposals.

    Extracts hourly rates, per-unit prices and compares them.
    """
    # Build rate table: description → {vendor: rate}
    rate_items: Dict[str, Dict[str, Dict]] = {}

    for p_idx, (proposal, pid) in enumerate(zip(proposals, prop_ids)):
        for li in proposal.line_items:
            if li.unit_price is not None and li.unit_price > 0:
                key = _normalize_description(li.description)
                if key not in rate_items:
                    rate_items[key] = {
                        'description': li.description,
                        'category': li.category,
                        'rates': {},
                    }
                rate_items[key]['rates'][pid] = {
                    'rate': li.unit_price,
                    'quantity': li.quantity,
                    'total': li.amount,
                }

    # Calculate stats for each rate item
    results = []
    for key, item in rate_items.items():
        rates = item['rates']
        rate_values = [r['rate'] for r in rates.values() if r['rate'] > 0]
        if not rate_values:
            continue

        min_rate = min(rate_values)
        max_rate = max(rate_values)
        avg_rate = sum(rate_values) / len(rate_values)
        variance = round((max_rate - min_rate) / min_rate * 100, 1) if min_rate > 0 else 0

        # Find lowest rate vendor
        lowest_vendor = ''
        for pid, r in rates.items():
            if r['rate'] == min_rate:
                lowest_vendor = pid
                break

        results.append({
            'description': item['description'],
            'category': item['category'],
            'rates': {pid: r['rate'] for pid, r in rates.items()},
            'quantities': {pid: r['quantity'] for pid, r in rates.items()},
            'min_rate': min_rate,
            'max_rate': max_rate,
            'avg_rate': round(avg_rate, 2),
            'variance_pct': variance,
            'lowest_vendor': lowest_vendor,
            'vendor_count': len(rates),
        })

    # Sort by variance (most contentious first)
    results.sort(key=lambda x: x['variance_pct'], reverse=True)

    return {
        'items': results,
        'summary': {
            'total_rate_items': len(results),
            'items_with_variance_over_20': sum(1 for r in results if r['variance_pct'] > 20),
            'avg_rate_variance': round(
                sum(r['variance_pct'] for r in results) / len(results), 1
            ) if results else 0,
        }
    }


# ──────────────────────────────────────────────
# Cost Element Breakdown (Waterfall Chart Data)
# ──────────────────────────────────────────────

def build_cost_breakdown(
    category_summaries: List[CategorySummary],
    prop_ids: List[str],
    totals: Dict[str, Optional[float]]
) -> Dict[str, Any]:
    """Build stacked cost breakdown data for waterfall/stacked bar charts."""
    categories = []
    for cs in category_summaries:
        cat_data = {
            'category': cs.category,
            'amounts': {},
            'percentages': {},
        }
        for pid in prop_ids:
            amount = cs.totals.get(pid, 0)
            total = totals.get(pid, 0) or 1  # prevent div/0
            cat_data['amounts'][pid] = amount
            cat_data['percentages'][pid] = round(amount / total * 100, 1) if total > 0 else 0
        categories.append(cat_data)

    return {
        'categories': categories,
        'prop_ids': prop_ids,
        'totals': {pid: totals.get(pid, 0) for pid in prop_ids},
    }


# ──────────────────────────────────────────────
# Vendor Scoring
# ──────────────────────────────────────────────

def compute_vendor_scores(
    proposals: List[ProposalData],
    prop_ids: List[str],
    aligned_items: List[AlignedItem],
    red_flags: Dict[str, List[Dict]],
    totals: Dict[str, Optional[float]]
) -> Dict[str, Dict]:
    """Compute a multi-factor score for each vendor.

    Scoring factors (all automated, no manual input):
    - Price competitiveness (40%) — lower total = higher score
    - Completeness (25%) — more line items priced = higher score
    - Risk profile (25%) — fewer red flags = higher score
    - Data quality (10%) — higher extraction confidence = higher score
    """
    scores: Dict[str, Dict] = {}
    valid_totals = {pid: t for pid, t in totals.items() if t is not None and t > 0}

    for p_idx, (proposal, pid) in enumerate(zip(proposals, prop_ids)):
        # Price Score (0-100) — lowest gets 100, scaled linearly
        price_score = 50  # default
        if valid_totals and pid in valid_totals:
            min_total = min(valid_totals.values())
            max_total = max(valid_totals.values())
            if max_total > min_total:
                price_score = round(100 - (valid_totals[pid] - min_total) / (max_total - min_total) * 80)
            elif len(valid_totals) > 1:
                price_score = 100  # all equal

        # Completeness Score (0-100)
        total_items = len(aligned_items)
        priced = sum(1 for ai in aligned_items
                     if pid in ai.amounts and ai.amounts[pid] is not None)
        completeness_score = round(priced / total_items * 100) if total_items > 0 else 0

        # Risk Score (0-100) — fewer flags = higher score
        vendor_flags = red_flags.get(pid, [])
        severity_points = sum(
            RED_FLAG_SEVERITY.get(f.get('severity', 'info'), 1)
            for f in vendor_flags
        )
        risk_score = max(0, 100 - severity_points * 12)

        # Data Quality Score (0-100)
        avg_confidence = 1.0
        if proposal.line_items:
            avg_confidence = sum(li.confidence for li in proposal.line_items) / len(proposal.line_items)
        has_total = 1 if proposal.total_amount and proposal.total_amount > 0 else 0
        has_company = 1 if proposal.company_name else 0
        data_quality = round(avg_confidence * 60 + has_total * 25 + has_company * 15)

        # Weighted total
        overall = round(
            price_score * 0.40 +
            completeness_score * 0.25 +
            risk_score * 0.25 +
            data_quality * 0.10
        )

        # Letter grade
        if overall >= 90:
            grade = 'A'
        elif overall >= 80:
            grade = 'B'
        elif overall >= 70:
            grade = 'C'
        elif overall >= 60:
            grade = 'D'
        else:
            grade = 'F'

        scores[pid] = {
            'overall': overall,
            'grade': grade,
            'price_score': price_score,
            'completeness_score': completeness_score,
            'risk_score': risk_score,
            'data_quality_score': data_quality,
            'red_flag_count': len(vendor_flags),
            'critical_flags': sum(1 for f in vendor_flags if f.get('severity') == 'critical'),
        }

    return scores


# ──────────────────────────────────────────────
# Executive Summary Generator
# ──────────────────────────────────────────────

def build_executive_summary(
    proposals: List[ProposalData],
    prop_ids: List[str],
    result  # ComparisonResult — avoid circular type hint
) -> Dict[str, Any]:
    """Generate a structured executive summary from the comparison data.

    Template-based — no AI. Just structured data presentation.
    """
    summary = {
        'proposal_count': len(proposals),
        'total_line_items': len(result.aligned_items),
    }

    # Winner determination
    valid_totals = {pid: t for pid, t in result.totals.items() if t is not None and t > 0}
    if valid_totals:
        sorted_by_price = sorted(valid_totals.items(), key=lambda x: x[1])
        summary['price_ranking'] = [
            {
                'rank': i + 1,
                'vendor': pid,
                'total': total,
                'total_formatted': f'${total:,.2f}',
                'delta_from_lowest': round(total - sorted_by_price[0][1], 2),
                'delta_pct': round((total - sorted_by_price[0][1]) / sorted_by_price[0][1] * 100, 1) if sorted_by_price[0][1] > 0 else 0,
            }
            for i, (pid, total) in enumerate(sorted_by_price)
        ]

    # Score ranking
    if result.vendor_scores:
        sorted_by_score = sorted(
            result.vendor_scores.items(),
            key=lambda x: x[1]['overall'],
            reverse=True
        )
        summary['score_ranking'] = [
            {
                'rank': i + 1,
                'vendor': pid,
                'overall_score': scores['overall'],
                'grade': scores['grade'],
            }
            for i, (pid, scores) in enumerate(sorted_by_score)
        ]

    # Key findings
    findings = []

    # Price spread
    if result.total_variance_pct is not None:
        findings.append({
            'type': 'price_spread',
            'text': f'Total price spread of {result.total_variance_pct}% between lowest and highest bidders',
            'severity': 'info' if result.total_variance_pct < 20 else 'warning',
        })

    # Best value indicator
    if result.vendor_scores:
        best_score = max(result.vendor_scores.items(), key=lambda x: x[1]['overall'])
        lowest_price = result.lowest_total_proposal
        if best_score[0] != lowest_price:
            findings.append({
                'type': 'best_value_split',
                'text': f'Lowest price ({lowest_price}) differs from highest-scored vendor ({best_score[0]}) — best value analysis recommended',
                'severity': 'info',
            })

    # Red flag summary
    for pid in prop_ids:
        critical = sum(1 for f in result.red_flags.get(pid, [])
                       if f.get('severity') == 'critical')
        if critical > 0:
            findings.append({
                'type': 'critical_flags',
                'text': f'{pid} has {critical} critical red flag{"s" if critical > 1 else ""}',
                'severity': 'critical',
            })

    # Rate variance highlight
    if result.rate_analysis and result.rate_analysis.get('summary', {}).get('items_with_variance_over_20', 0) > 0:
        count = result.rate_analysis['summary']['items_with_variance_over_20']
        findings.append({
            'type': 'rate_variance',
            'text': f'{count} labor/rate categories have >20% variance — negotiation opportunities',
            'severity': 'info',
        })

    summary['key_findings'] = findings

    # Negotiation opportunities (items with highest variance where vendor is highest)
    negotiation_items = []
    for ai in result.aligned_items:
        if ai.variance_pct and ai.variance_pct > 15:
            for pid, amt in ai.amounts.items():
                if amt == ai.max_amount and ai.avg_amount:
                    savings = amt - ai.avg_amount
                    negotiation_items.append({
                        'vendor': pid,
                        'line_item': ai.description,
                        'current_amount': amt,
                        'avg_amount': ai.avg_amount,
                        'potential_savings': round(savings, 2),
                        'savings_formatted': f'${savings:,.0f}',
                        'variance_pct': ai.variance_pct,
                    })

    negotiation_items.sort(key=lambda x: x['potential_savings'], reverse=True)
    summary['negotiation_opportunities'] = negotiation_items[:10]  # Top 10

    # Total potential savings
    if negotiation_items:
        total_savings = sum(n['potential_savings'] for n in negotiation_items)
        summary['total_potential_savings'] = round(total_savings, 2)
        summary['total_potential_savings_formatted'] = f'${total_savings:,.0f}'

    return summary
