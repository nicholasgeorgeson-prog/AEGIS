"""
Document Differ v2.0.0
======================
Enhanced document comparison engine with:
- Line-level alignment with word-level diff highlighting
- Move/reorder detection (Tier 1 feature)
- Section-aware grouping by headings
- Change classification and statistics

Uses diff-match-patch for accurate word-level comparisons
and difflib.SequenceMatcher for line alignment.

v1.0.0: Initial implementation with line/word diffs
v1.0.1 (v3.0.114): Added comprehensive logging
v2.0.0 (v4.6.1): Move detection, section awareness, change index, unified view support
Author: AEGIS
"""

import re
import html
import difflib
import logging
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass

# Setup logger
try:
    from config_logging import get_logger
    logger = get_logger('document_compare.differ')
except ImportError:
    logger = logging.getLogger('document_compare.differ')

# Try to import diff_match_patch
try:
    import diff_match_patch as dmp_module
    DMP_AVAILABLE = True
    logger.debug("diff-match-patch library loaded successfully")
except ImportError:
    DMP_AVAILABLE = False
    logger.warning("diff-match-patch not available - word-level diff will be limited")

from .models import WordChange, AlignedRow, DiffResult


# =============================================================================
# SECTION DETECTION
# =============================================================================

# Patterns for detecting section headings in technical documents
HEADING_PATTERNS = [
    # Numbered sections: 1.0, 1.1, 2.3.4, etc. (with or without trailing period)
    re.compile(r'^(\d+(?:\.\d+)*\.?)\s+(.+)$'),
    # ALL-CAPS headings (common in aerospace/defense docs)
    re.compile(r'^([A-Z][A-Z\s]{4,})$'),
    # Markdown-style headings
    re.compile(r'^(#{1,6})\s+(.+)$'),
]


def detect_section(line: str) -> Optional[Dict]:
    """Detect if a line is a section heading.

    Returns dict with section info or None.
    """
    stripped = line.strip()
    if not stripped or len(stripped) < 3:
        return None

    for pattern in HEADING_PATTERNS:
        m = pattern.match(stripped)
        if m:
            groups = m.groups()
            if len(groups) == 2:
                return {
                    'number': groups[0].strip(),
                    'title': groups[1].strip(),
                    'full': stripped
                }
            else:
                return {
                    'number': '',
                    'title': stripped,
                    'full': stripped
                }

    return None


def assign_sections(lines: List[str]) -> List[Optional[str]]:
    """Assign section labels to each line based on heading detection.

    Returns a list of section names (same length as lines).
    Lines before any heading get section "".
    """
    sections = []
    current_section = ""

    for line in lines:
        heading = detect_section(line)
        if heading:
            current_section = heading['full']
        sections.append(current_section)

    return sections


# =============================================================================
# MOVE DETECTION
# =============================================================================

def detect_moves(
    old_lines: List[str],
    new_lines: List[str],
    deleted_indices: Set[int],
    added_indices: Set[int],
    similarity_threshold: float = 0.85
) -> List[Dict]:
    """Detect moved/reordered content between old and new text.

    Uses a two-pass approach:
    1. Exact match: Find deleted lines that appear verbatim in added lines
    2. Fuzzy match: Find deleted lines that are similar to added lines (>85%)

    Returns list of move pairs: [{old_idx, new_idx, similarity, old_line, new_line}]
    """
    moves = []
    matched_old = set()
    matched_new = set()

    # Normalize lines for comparison (strip whitespace, lowercase)
    def normalize(line):
        return line.strip().lower()

    # Build lookup for added lines
    added_lookup = {}
    for idx in added_indices:
        if idx < len(new_lines):
            norm = normalize(new_lines[idx])
            if norm and len(norm) > 10:  # Skip very short lines
                if norm not in added_lookup:
                    added_lookup[norm] = []
                added_lookup[norm].append(idx)

    # Pass 1: Exact matches
    for old_idx in deleted_indices:
        if old_idx >= len(old_lines):
            continue
        norm = normalize(old_lines[old_idx])
        if not norm or len(norm) <= 10:
            continue

        if norm in added_lookup:
            for new_idx in added_lookup[norm]:
                if new_idx not in matched_new:
                    moves.append({
                        'old_idx': old_idx,
                        'new_idx': new_idx,
                        'similarity': 1.0,
                        'old_line': old_lines[old_idx],
                        'new_line': new_lines[new_idx]
                    })
                    matched_old.add(old_idx)
                    matched_new.add(new_idx)
                    break

    # Pass 2: Fuzzy matches for remaining unmatched
    remaining_deleted = [i for i in deleted_indices if i not in matched_old and i < len(old_lines)]
    remaining_added = [i for i in added_indices if i not in matched_new and i < len(new_lines)]

    # Only do fuzzy matching for reasonable sizes (O(n*m) complexity)
    if len(remaining_deleted) * len(remaining_added) <= 50000:
        for old_idx in remaining_deleted:
            old_line = old_lines[old_idx]
            if not old_line.strip() or len(old_line.strip()) <= 15:
                continue

            best_ratio = 0
            best_new_idx = -1

            for new_idx in remaining_added:
                if new_idx in matched_new:
                    continue
                new_line = new_lines[new_idx]
                if not new_line.strip() or len(new_line.strip()) <= 15:
                    continue

                ratio = difflib.SequenceMatcher(None, old_line.strip(), new_line.strip()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_new_idx = new_idx

            if best_ratio >= similarity_threshold and best_new_idx >= 0:
                moves.append({
                    'old_idx': old_idx,
                    'new_idx': best_new_idx,
                    'similarity': best_ratio,
                    'old_line': old_lines[old_idx],
                    'new_line': new_lines[best_new_idx]
                })
                matched_old.add(old_idx)
                matched_new.add(best_new_idx)

    return moves


# =============================================================================
# DOCUMENT DIFFER
# =============================================================================

class DocumentDiffer:
    """
    Enhanced document comparison engine with line-level alignment,
    word-level diff highlighting, move detection, and section awareness.
    """

    def __init__(self, similarity_threshold: float = 0.6):
        """
        Initialize the differ.

        Args:
            similarity_threshold: Minimum similarity ratio to consider
                                  lines as modified vs added/deleted (0.0 to 1.0)
        """
        self.similarity_threshold = similarity_threshold
        self._change_counter = 0

        # Initialize diff-match-patch if available
        if DMP_AVAILABLE:
            self.dmp = dmp_module.diff_match_patch()
            self.dmp.Diff_Timeout = 2.0  # Max 2 seconds per diff
            self.dmp.Diff_EditCost = 4
        else:
            self.dmp = None

    def align_and_diff(
        self,
        old_text: str,
        new_text: str,
        old_scan_id: int = 0,
        new_scan_id: int = 0,
        document_id: int = 0,
        old_scan_time: str = "",
        new_scan_time: str = "",
        filename: str = ""
    ) -> DiffResult:
        """
        Perform full document comparison with move detection and section awareness.

        Args:
            old_text: Original document text
            new_text: New document text
            old_scan_id: ID of older scan
            new_scan_id: ID of newer scan
            document_id: Document ID
            old_scan_time: Timestamp of older scan
            new_scan_time: Timestamp of newer scan
            filename: Document filename

        Returns:
            DiffResult with aligned rows, moves, sections, and statistics
        """
        self._change_counter = 0

        logger.info(f"Starting diff: old_scan={old_scan_id}, new_scan={new_scan_id}, doc={document_id}")
        logger.debug(f"Text lengths: old={len(old_text or '')}, new={len(new_text or '')}")

        # Split into lines
        old_lines = self._split_into_lines(old_text)
        new_lines = self._split_into_lines(new_text)
        logger.debug(f"Line counts: old={len(old_lines)}, new={len(new_lines)}")

        # Assign sections
        old_sections = assign_sections(old_lines)
        new_sections = assign_sections(new_lines)

        # Align lines and compute diffs
        try:
            aligned_rows = self._align_lines(old_lines, new_lines)
        except Exception as e:
            logger.error(f"Line alignment failed: {e}", exc_info=True)
            raise

        # Detect moves among deleted/added lines
        deleted_indices = set()
        added_indices = set()
        for row in aligned_rows:
            if row.status == 'deleted':
                # Find the original old line index
                for i, line in enumerate(old_lines):
                    if line == row.old_line and i not in deleted_indices:
                        deleted_indices.add(i)
                        break
            elif row.status == 'added':
                for i, line in enumerate(new_lines):
                    if line == row.new_line and i not in added_indices:
                        added_indices.add(i)
                        break

        moves = detect_moves(old_lines, new_lines, deleted_indices, added_indices)
        logger.info(f"Detected {len(moves)} moved lines")

        # Mark moved rows in aligned_rows
        move_old_lines = {m['old_line'].strip() for m in moves}
        move_new_lines = {m['new_line'].strip() for m in moves}
        move_pairs = {(m['old_line'].strip(), m['new_line'].strip()) for m in moves}

        for row in aligned_rows:
            if row.status == 'deleted' and row.old_line.strip() in move_old_lines:
                row.status = 'moved_from'
                row.is_change = True
                # Find the destination
                for m in moves:
                    if m['old_line'].strip() == row.old_line.strip():
                        row.move_target = m['new_line']
                        break
            elif row.status == 'added' and row.new_line.strip() in move_new_lines:
                row.status = 'moved_to'
                row.is_change = True
                for m in moves:
                    if m['new_line'].strip() == row.new_line.strip():
                        row.move_source = m['old_line']
                        break

        # Assign section info to each row
        old_line_idx = 0
        new_line_idx = 0
        for row in aligned_rows:
            if row.status in ('unchanged', 'modified', 'deleted', 'moved_from'):
                if old_line_idx < len(old_sections):
                    row.section = old_sections[old_line_idx]
                old_line_idx += 1
                if row.status in ('unchanged', 'modified'):
                    new_line_idx += 1
            elif row.status in ('added', 'moved_to'):
                if new_line_idx < len(new_sections):
                    row.section = new_sections[new_line_idx]
                new_line_idx += 1

        # Build change index (list of all changes with context)
        change_index = []
        for row in aligned_rows:
            if row.is_change:
                # Determine change type for frontend display
                change_type = row.status
                if change_type in ('moved_from', 'moved_to'):
                    change_type = 'moved'
                # Preview text: prefer new_line for additions/modifications, old_line for deletions
                preview = ''
                if row.status in ('added', 'moved_to', 'modified'):
                    preview = (row.new_line or '')[:80]
                else:
                    preview = (row.old_line or '')[:80]

                change_entry = {
                    'row_index': row.row_index,
                    'status': row.status,
                    'type': change_type,
                    'section': getattr(row, 'section', ''),
                    'preview': preview,
                    'old_text': (row.old_line or '')[:80],
                    'new_text': (row.new_line or '')[:80],
                }
                change_index.append(change_entry)

        # Collect all changes for navigation
        all_changes = []
        for row in aligned_rows:
            all_changes.extend(row.word_changes)

        # Compute statistics
        stats = {
            'total_rows': len(aligned_rows),
            'unchanged': sum(1 for r in aligned_rows if r.status == 'unchanged'),
            'added': sum(1 for r in aligned_rows if r.status in ('added', 'moved_to')),
            'deleted': sum(1 for r in aligned_rows if r.status in ('deleted', 'moved_from')),
            'modified': sum(1 for r in aligned_rows if r.status == 'modified'),
            'moved': len(moves),
            'total_changes': len(all_changes),
            'sections_changed': len(set(
                getattr(r, 'section', '') for r in aligned_rows
                if r.is_change and getattr(r, 'section', '')
            ))
        }

        logger.info(f"Diff complete: {stats['total_rows']} rows, {stats['total_changes']} changes "
                    f"(+{stats['added']}, -{stats['deleted']}, ~{stats['modified']}, "
                    f"↔{stats['moved']})")

        result = DiffResult(
            old_scan_id=old_scan_id,
            new_scan_id=new_scan_id,
            document_id=document_id,
            old_scan_time=old_scan_time,
            new_scan_time=new_scan_time,
            filename=filename,
            rows=aligned_rows,
            changes=all_changes,
            stats=stats
        )
        result.change_index = change_index
        result.moves = [{'old_line': m['old_line'][:80], 'new_line': m['new_line'][:80],
                         'similarity': round(m['similarity'], 2)} for m in moves]

        return result

    def _split_into_lines(self, text: str) -> List[str]:
        """
        Split text into lines for comparison.

        Splits on newlines, preserving the structure of the document.
        Empty lines are preserved to maintain document structure.

        Args:
            text: Document text

        Returns:
            List of lines (may include empty strings for blank lines)
        """
        if not text:
            return []

        # Split on newlines
        lines = text.split('\n')

        # Strip trailing whitespace from each line but preserve leading
        # (for indentation-sensitive content)
        lines = [line.rstrip() for line in lines]

        return lines

    def _align_lines(
        self,
        old_lines: List[str],
        new_lines: List[str]
    ) -> List[AlignedRow]:
        """
        Align old and new lines using sequence matching.

        Creates aligned rows where:
        - Unchanged lines appear in both panels
        - Added lines have empty placeholder in old panel
        - Deleted lines have empty placeholder in new panel
        - Modified lines show word-level diffs

        Args:
            old_lines: Lines from original document
            new_lines: Lines from new document

        Returns:
            List of AlignedRow objects
        """
        rows = []
        row_index = 0

        # Use difflib for intelligent sequence matching
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged lines
                for idx in range(i2 - i1):
                    old_line = old_lines[i1 + idx]
                    rows.append(AlignedRow(
                        row_index=row_index,
                        status='unchanged',
                        old_line=old_line,
                        new_line=old_line,
                        old_html=self._escape_html(old_line),
                        new_html=self._escape_html(old_line),
                        word_changes=[]
                    ))
                    row_index += 1

            elif tag == 'delete':
                # Lines removed in new version
                for idx in range(i2 - i1):
                    old_line = old_lines[i1 + idx]
                    change = self._create_change(
                        'deleted', old_line, '', row_index
                    )
                    rows.append(AlignedRow(
                        row_index=row_index,
                        status='deleted',
                        old_line=old_line,
                        new_line='',
                        old_html=self._generate_deleted_html(old_line),
                        new_html='',  # Placeholder
                        word_changes=[change]
                    ))
                    row_index += 1

            elif tag == 'insert':
                # Lines added in new version
                for idx in range(j2 - j1):
                    new_line = new_lines[j1 + idx]
                    change = self._create_change(
                        'added', '', new_line, row_index
                    )
                    rows.append(AlignedRow(
                        row_index=row_index,
                        status='added',
                        old_line='',
                        new_line=new_line,
                        old_html='',  # Placeholder
                        new_html=self._generate_added_html(new_line),
                        word_changes=[change]
                    ))
                    row_index += 1

            elif tag == 'replace':
                # Lines modified - need to match them
                old_section = old_lines[i1:i2]
                new_section = new_lines[j1:j2]
                matched_rows = self._match_modified_lines(
                    old_section, new_section, row_index
                )
                rows.extend(matched_rows)
                row_index += len(matched_rows)

        return rows

    def _match_modified_lines(
        self,
        old_section: List[str],
        new_section: List[str],
        start_row_index: int
    ) -> List[AlignedRow]:
        """
        Match modified lines between sections using similarity scoring.

        Args:
            old_section: Lines from old document section
            new_section: Lines from new document section
            start_row_index: Starting row index for this section

        Returns:
            List of AlignedRow objects
        """
        rows = []
        row_index = start_row_index
        matched_new = set()

        # For each old line, find best matching new line
        for old_idx, old_line in enumerate(old_section):
            best_match = None
            best_ratio = 0.0
            best_new_idx = -1

            for new_idx, new_line in enumerate(new_section):
                if new_idx in matched_new:
                    continue

                ratio = difflib.SequenceMatcher(
                    None, old_line, new_line
                ).ratio()

                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = new_line
                    best_new_idx = new_idx

            if best_ratio >= self.similarity_threshold:
                # Found a match - it's a modification
                matched_new.add(best_new_idx)

                # Compute word-level diff
                word_changes, old_html, new_html = self._diff_words(
                    old_line, best_match, row_index
                )

                rows.append(AlignedRow(
                    row_index=row_index,
                    status='modified',
                    old_line=old_line,
                    new_line=best_match,
                    old_html=old_html,
                    new_html=new_html,
                    word_changes=word_changes
                ))
            else:
                # No good match - it's a deletion
                change = self._create_change(
                    'deleted', old_line, '', row_index
                )
                rows.append(AlignedRow(
                    row_index=row_index,
                    status='deleted',
                    old_line=old_line,
                    new_line='',
                    old_html=self._generate_deleted_html(old_line),
                    new_html='',
                    word_changes=[change]
                ))

            row_index += 1

        # Any unmatched new lines are additions
        for new_idx, new_line in enumerate(new_section):
            if new_idx not in matched_new:
                change = self._create_change(
                    'added', '', new_line, row_index
                )
                rows.append(AlignedRow(
                    row_index=row_index,
                    status='added',
                    old_line='',
                    new_line=new_line,
                    old_html='',
                    new_html=self._generate_added_html(new_line),
                    word_changes=[change]
                ))
                row_index += 1

        return rows

    def _diff_words(
        self,
        old_line: str,
        new_line: str,
        row_index: int
    ) -> Tuple[List[WordChange], str, str]:
        """
        Compute word-level diff between two lines.

        Uses diff-match-patch if available, falls back to
        character-based difflib otherwise.

        Args:
            old_line: Original line
            new_line: New line
            row_index: Row index for change tracking

        Returns:
            Tuple of (word_changes, old_html, new_html)
        """
        if self.dmp:
            return self._diff_words_dmp(old_line, new_line, row_index)
        else:
            return self._diff_words_difflib(old_line, new_line, row_index)

    def _diff_words_dmp(
        self,
        old_line: str,
        new_line: str,
        row_index: int
    ) -> Tuple[List[WordChange], str, str]:
        """
        Word-level diff using diff-match-patch.

        Args:
            old_line: Original line
            new_line: New line
            row_index: Row index

        Returns:
            Tuple of (word_changes, old_html, new_html)
        """
        # Compute diff
        diffs = self.dmp.diff_main(old_line, new_line)
        self.dmp.diff_cleanupSemantic(diffs)

        word_changes = []
        old_html_parts = []
        new_html_parts = []

        for op, text in diffs:
            escaped_text = html.escape(text)

            if op == 0:  # Equal
                old_html_parts.append(escaped_text)
                new_html_parts.append(escaped_text)

            elif op == -1:  # Deletion
                old_html_parts.append(
                    f'<span class="dc-word-deleted">{escaped_text}</span>'
                )
                # Create change for navigation
                change = self._create_change(
                    'modified', text, '', row_index
                )
                word_changes.append(change)

            elif op == 1:  # Insertion
                new_html_parts.append(
                    f'<span class="dc-word-added">{escaped_text}</span>'
                )
                # Create change for navigation (if not paired with deletion)
                if not word_changes or word_changes[-1].old_text:
                    change = self._create_change(
                        'modified', '', text, row_index
                    )
                    word_changes.append(change)
                else:
                    # Pair with previous deletion
                    word_changes[-1].new_text = text

        return (
            word_changes,
            ''.join(old_html_parts),
            ''.join(new_html_parts)
        )

    def _diff_words_difflib(
        self,
        old_line: str,
        new_line: str,
        row_index: int
    ) -> Tuple[List[WordChange], str, str]:
        """
        Word-level diff using difflib (fallback).

        Tokenizes into words and compares word sequences.

        Args:
            old_line: Original line
            new_line: New line
            row_index: Row index

        Returns:
            Tuple of (word_changes, old_html, new_html)
        """
        # Tokenize preserving whitespace
        old_tokens = self._tokenize(old_line)
        new_tokens = self._tokenize(new_line)

        word_changes = []
        old_html_parts = []
        new_html_parts = []

        matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                text = ''.join(old_tokens[i1:i2])
                escaped = html.escape(text)
                old_html_parts.append(escaped)
                new_html_parts.append(escaped)

            elif tag == 'delete':
                text = ''.join(old_tokens[i1:i2])
                escaped = html.escape(text)
                old_html_parts.append(
                    f'<span class="dc-word-deleted">{escaped}</span>'
                )
                change = self._create_change('modified', text, '', row_index)
                word_changes.append(change)

            elif tag == 'insert':
                text = ''.join(new_tokens[j1:j2])
                escaped = html.escape(text)
                new_html_parts.append(
                    f'<span class="dc-word-added">{escaped}</span>'
                )
                change = self._create_change('modified', '', text, row_index)
                word_changes.append(change)

            elif tag == 'replace':
                old_text = ''.join(old_tokens[i1:i2])
                new_text = ''.join(new_tokens[j1:j2])
                old_html_parts.append(
                    f'<span class="dc-word-deleted">{html.escape(old_text)}</span>'
                )
                new_html_parts.append(
                    f'<span class="dc-word-added">{html.escape(new_text)}</span>'
                )
                change = self._create_change(
                    'modified', old_text, new_text, row_index
                )
                word_changes.append(change)

        return (
            word_changes,
            ''.join(old_html_parts),
            ''.join(new_html_parts)
        )

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words and whitespace.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens (words and whitespace)
        """
        # Split on word boundaries while preserving separators
        return re.findall(r'\S+|\s+', text)

    def _create_change(
        self,
        change_type: str,
        old_text: str,
        new_text: str,
        row_index: int
    ) -> WordChange:
        """
        Create a WordChange object with unique ID.

        Args:
            change_type: Type of change
            old_text: Original text
            new_text: New text
            row_index: Row index

        Returns:
            WordChange object
        """
        change_id = f"change-{self._change_counter}"
        self._change_counter += 1

        # Extract context (first 30 chars)
        context = old_text or new_text
        context_before = context[:30] if len(context) > 30 else context

        return WordChange(
            id=change_id,
            change_type=change_type,
            old_text=old_text,
            new_text=new_text,
            row_index=row_index,
            context_before=context_before,
            context_after=""
        )

    def _escape_html(self, text: str) -> str:
        """Escape text for safe HTML display."""
        return html.escape(text) if text else ""

    def _generate_added_html(self, text: str) -> str:
        """Generate HTML for an added line."""
        escaped = html.escape(text)
        return f'<span class="dc-line-added">{escaped}</span>'

    def _generate_deleted_html(self, text: str) -> str:
        """Generate HTML for a deleted line."""
        escaped = html.escape(text)
        return f'<span class="dc-line-deleted">{escaped}</span>'

    def _generate_moved_html(self, text: str, direction: str) -> str:
        """Generate HTML for a moved line."""
        escaped = html.escape(text)
        icon = '↑' if direction == 'from' else '↓'
        return f'<span class="dc-line-moved">{icon} {escaped}</span>'


# Convenience function
def compute_diff(
    old_text: str,
    new_text: str,
    **kwargs
) -> DiffResult:
    """
    Compute diff between two texts.

    Args:
        old_text: Original text
        new_text: New text
        **kwargs: Additional arguments passed to DiffResult

    Returns:
        DiffResult with aligned rows
    """
    differ = DocumentDiffer()
    return differ.align_and_diff(old_text, new_text, **kwargs)


if __name__ == '__main__':
    # Demo/test
    print(f"Document Differ v2.0.0 - DMP Available: {DMP_AVAILABLE}")
    print("=" * 50)

    old_text = """1.0 INTRODUCTION
This document describes the system.
The system shall meet all requirements.

2.0 REQUIREMENTS
- Requirement 1
- Requirement 2
- Requirement 3

3.0 CONCLUSION
The system is complete."""

    new_text = """1.0 INTRODUCTION
This document describes the system architecture.
The system shall meet all requirements.

2.0 REQUIREMENTS
- Requirement 1
- Requirement 2 (updated)
- NEW REQUIREMENT
- Requirement 3

3.0 SUMMARY
The system is ready for deployment.

4.0 APPENDIX
The system is complete."""

    differ = DocumentDiffer()
    result = differ.align_and_diff(old_text, new_text)

    print(f"\nStatistics:")
    print(f"  Total rows: {result.stats['total_rows']}")
    print(f"  Unchanged: {result.stats['unchanged']}")
    print(f"  Added: {result.stats['added']}")
    print(f"  Deleted: {result.stats['deleted']}")
    print(f"  Modified: {result.stats['modified']}")
    print(f"  Moved: {result.stats['moved']}")
    print(f"  Total changes: {result.stats['total_changes']}")

    print(f"\nRows:")
    for row in result.rows:
        if row.status != 'unchanged':
            print(f"  [{row.row_index}] {row.status}: "
                  f"'{row.old_line[:30]}...' -> '{row.new_line[:30]}...'")
