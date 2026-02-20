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
    proposals: List[Dict[str, Any]] = field(default_factory=list)  # List of proposal summaries
    aligned_items: List[AlignedItem] = field(default_factory=list)
    category_summaries: List[CategorySummary] = field(default_factory=list)
    unmatched_items: Dict[str, List[Dict]] = field(default_factory=dict)  # proposal_id → items
    totals: Dict[str, Optional[float]] = field(default_factory=dict)  # proposal_id → grand total
    totals_raw: Dict[str, str] = field(default_factory=dict)

    # Overall comparison metrics
    lowest_total_proposal: str = ''
    highest_total_proposal: str = ''
    total_variance_pct: Optional[float] = None

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

    return result
