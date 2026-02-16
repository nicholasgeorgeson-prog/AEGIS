"""
Cross-Reference Validator v1.0.0
================================
Date: 2026-02-03

Validates cross-references in technical documents.
Detects broken, missing, and inconsistent references.

Features:
- Section reference validation (Section 1.1, etc.)
- Table/Figure reference validation
- Requirement ID validation (REQ-001, etc.)
- Unreferenced item detection
- Reference format consistency checking
- Bidirectional reference validation

Author: AEGIS NLP Enhancement Project
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERSION = '1.0.0'


@dataclass
class ReferenceIssue:
    """Represents a cross-reference issue."""
    reference_text: str
    reference_type: str  # 'section', 'table', 'figure', 'requirement', 'appendix', 'document'
    issue_type: str  # 'broken', 'unreferenced', 'format_inconsistent', 'ambiguous'
    location: int
    confidence: float
    suggestion: str
    context: str


@dataclass
class Reference:
    """Represents a detected reference."""
    text: str
    ref_type: str
    ref_id: str
    location: int
    context: str


@dataclass
class ReferencedItem:
    """Represents an item that can be referenced."""
    item_type: str  # 'section', 'table', 'figure', 'requirement', 'appendix'
    item_id: str
    title: Optional[str]
    location: int
    is_referenced: bool = False
    reference_count: int = 0


# ============================================================
# REFERENCE PATTERNS
# ============================================================

# Section reference patterns
SECTION_REFERENCE_PATTERNS = [
    r'\bSection\s+(\d+(?:\.\d+)*)\b',
    r'\bsection\s+(\d+(?:\.\d+)*)\b',
    r'\b\u00A7\s*(\d+(?:\.\d+)*)\b',  # Section symbol
    r'(?:see|See|per|Per|refer to|Refer to)\s+(?:Section\s+)?(\d+(?:\.\d+)+)\b',
    r'\bparagraph\s+(\d+(?:\.\d+)*)\b',
    r'\bParagraph\s+(\d+(?:\.\d+)*)\b',
    r'\bclause\s+(\d+(?:\.\d+)*)\b',
    r'\bClause\s+(\d+(?:\.\d+)*)\b',
]

# Section definition patterns
SECTION_DEFINITION_PATTERNS = [
    r'^(\d+(?:\.\d+)*)\s+[A-Z]',  # 1.1 Title
    r'^(\d+(?:\.\d+)*)\s+\w',     # 1.1.1 title
    r'^\s*(\d+(?:\.\d+)*)\.\s+',  # 1.1. with trailing period
]

# Table reference patterns
TABLE_REFERENCE_PATTERNS = [
    r'\bTable\s+(\d+(?:[\-\.]\d+)?)\b',
    r'\btable\s+(\d+(?:[\-\.]\d+)?)\b',
    r'(?:see|See|per|Per)\s+Table\s+(\d+(?:[\-\.]\d+)?)\b',
    r'\bTbl\.?\s+(\d+(?:[\-\.]\d+)?)\b',
]

# Table definition patterns
TABLE_DEFINITION_PATTERNS = [
    r'\bTable\s+(\d+(?:[\-\.]\d+)?)[:\.]?\s',
    r'\bTABLE\s+(\d+(?:[\-\.]\d+)?)[:\.]?\s',
]

# Figure reference patterns
FIGURE_REFERENCE_PATTERNS = [
    r'\bFigure\s+(\d+(?:[\-\.]\d+)?)\b',
    r'\bfigure\s+(\d+(?:[\-\.]\d+)?)\b',
    r'(?:see|See|per|Per)\s+Figure\s+(\d+(?:[\-\.]\d+)?)\b',
    r'\bFig\.?\s+(\d+(?:[\-\.]\d+)?)\b',
]

# Figure definition patterns
FIGURE_DEFINITION_PATTERNS = [
    r'\bFigure\s+(\d+(?:[\-\.]\d+)?)[:\.]?\s',
    r'\bFIGURE\s+(\d+(?:[\-\.]\d+)?)[:\.]?\s',
]

# Requirement ID patterns
REQUIREMENT_REFERENCE_PATTERNS = [
    r'\b([A-Z]{2,5}[-_]\d{3,6})\b',           # ABC-1234
    r'\b(REQ[-_]\d{3,6})\b',                   # REQ-1234
    r'\b(SYS[-_]\d{3,6})\b',                   # SYS-1234
    r'\b(SW[-_]\d{3,6})\b',                    # SW-1234
    r'\b(HW[-_]\d{3,6})\b',                    # HW-1234
    r'\b(IF[-_]\d{3,6})\b',                    # IF-1234 (interface)
    r'\b(TC[-_]\d{3,6})\b',                    # TC-1234 (test case)
    r'\[([A-Z]{2,5}[-_]\d{3,6})\]',           # [ABC-1234]
]

# Appendix reference patterns
APPENDIX_REFERENCE_PATTERNS = [
    r'\bAppendix\s+([A-Z])\b',
    r'\bappendix\s+([A-Z])\b',
    r'\bAnnex\s+([A-Z])\b',
    r'\bannex\s+([A-Z])\b',
    r'(?:see|See|per|Per)\s+Appendix\s+([A-Z])\b',
]

# Appendix definition patterns
APPENDIX_DEFINITION_PATTERNS = [
    r'\bAppendix\s+([A-Z])[:\.]?\s',
    r'\bAPPENDIX\s+([A-Z])[:\.]?\s',
    r'\bAnnex\s+([A-Z])[:\.]?\s',
    r'\bANNEX\s+([A-Z])[:\.]?\s',
]

# Document reference patterns
DOCUMENT_REFERENCE_PATTERNS = [
    r'\b([A-Z]{2,5}[-_]\d{4,8}[-_][A-Z0-9]+)\b',  # DOC-12345-ABC
    r'\b(MIL[-_]STD[-_]\d+[A-Z]?)\b',              # MIL-STD-1553
    r'\b(IEEE\s+\d+(?:\.\d+)?)\b',                  # IEEE 802.11
    r'\b(ISO\s+\d+(?:[-:]\d+)?)\b',                 # ISO 9001
    r'\b(AS\d{4}[A-Z]?)\b',                         # AS9100D
    r'\b(SAE\s+[A-Z]+\d+)\b',                       # SAE J1939
]


class CrossReferenceValidator:
    """
    Validates cross-references in technical documents.

    Features:
    - Detects references to sections, tables, figures, requirements
    - Validates that referenced items exist
    - Finds unreferenced items
    - Checks reference format consistency
    """

    VERSION = VERSION

    def __init__(self):
        """Initialize the cross-reference validator."""
        pass

    def validate_text(self, text: str) -> Tuple[List[ReferenceIssue], Dict[str, Any]]:
        """
        Validate cross-references in text.

        Args:
            text: Document text to validate

        Returns:
            Tuple of (issues list, statistics dict)
        """
        # Extract all references
        references = self._extract_references(text)

        # Extract all defined items
        defined_items = self._extract_defined_items(text)

        # Validate references
        issues = self._validate_references(references, defined_items, text)

        # Find unreferenced items
        unreferenced_issues = self._find_unreferenced_items(references, defined_items, text)
        issues.extend(unreferenced_issues)

        # Check format consistency
        format_issues = self._check_format_consistency(references)
        issues.extend(format_issues)

        # Calculate statistics
        statistics = self._calculate_statistics(references, defined_items, issues)

        return issues, statistics

    def _extract_references(self, text: str) -> List[Reference]:
        """Extract all references from text."""
        references = []

        # Section references
        for pattern in SECTION_REFERENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                references.append(Reference(
                    text=match.group(0),
                    ref_type='section',
                    ref_id=match.group(1),
                    location=match.start(),
                    context=context
                ))

        # Table references
        for pattern in TABLE_REFERENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                references.append(Reference(
                    text=match.group(0),
                    ref_type='table',
                    ref_id=match.group(1),
                    location=match.start(),
                    context=context
                ))

        # Figure references
        for pattern in FIGURE_REFERENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                references.append(Reference(
                    text=match.group(0),
                    ref_type='figure',
                    ref_id=match.group(1),
                    location=match.start(),
                    context=context
                ))

        # Requirement references
        for pattern in REQUIREMENT_REFERENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                references.append(Reference(
                    text=match.group(0),
                    ref_type='requirement',
                    ref_id=match.group(1),
                    location=match.start(),
                    context=context
                ))

        # Appendix references
        for pattern in APPENDIX_REFERENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                context = text[max(0, match.start()-30):min(len(text), match.end()+30)]
                references.append(Reference(
                    text=match.group(0),
                    ref_type='appendix',
                    ref_id=match.group(1),
                    location=match.start(),
                    context=context
                ))

        return references

    def _extract_defined_items(self, text: str) -> Dict[str, List[ReferencedItem]]:
        """Extract all defined items (sections, tables, figures, etc.)."""
        items: Dict[str, List[ReferencedItem]] = defaultdict(list)

        # Split into lines for section detection
        lines = text.split('\n')
        char_offset = 0

        for line in lines:
            # Section definitions
            for pattern in SECTION_DEFINITION_PATTERNS:
                match = re.match(pattern, line)
                if match:
                    items['section'].append(ReferencedItem(
                        item_type='section',
                        item_id=match.group(1),
                        title=line.strip(),
                        location=char_offset
                    ))
                    break

            char_offset += len(line) + 1  # +1 for newline

        # Table definitions
        for pattern in TABLE_DEFINITION_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                items['table'].append(ReferencedItem(
                    item_type='table',
                    item_id=match.group(1),
                    title=text[match.start():min(len(text), match.end()+50)].split('\n')[0],
                    location=match.start()
                ))

        # Figure definitions
        for pattern in FIGURE_DEFINITION_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                items['figure'].append(ReferencedItem(
                    item_type='figure',
                    item_id=match.group(1),
                    title=text[match.start():min(len(text), match.end()+50)].split('\n')[0],
                    location=match.start()
                ))

        # Appendix definitions
        for pattern in APPENDIX_DEFINITION_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                items['appendix'].append(ReferencedItem(
                    item_type='appendix',
                    item_id=match.group(1),
                    title=text[match.start():min(len(text), match.end()+50)].split('\n')[0],
                    location=match.start()
                ))

        # Requirements are usually defined inline, track unique IDs
        req_ids_seen: Set[str] = set()
        for pattern in REQUIREMENT_REFERENCE_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                req_id = match.group(1)
                if req_id not in req_ids_seen:
                    req_ids_seen.add(req_id)
                    # Check if it's a definition (followed by colon or at line start)
                    if match.start() == 0 or text[match.start()-1] in '\n[':
                        items['requirement'].append(ReferencedItem(
                            item_type='requirement',
                            item_id=req_id,
                            title=None,
                            location=match.start()
                        ))

        return items

    def _validate_references(self, references: List[Reference],
                           defined_items: Dict[str, List[ReferencedItem]],
                           text: str) -> List[ReferenceIssue]:
        """Validate that all references point to defined items."""
        issues = []

        # Build sets of defined IDs for each type
        defined_ids: Dict[str, Set[str]] = {}
        for item_type, items in defined_items.items():
            defined_ids[item_type] = {item.item_id for item in items}

        for ref in references:
            # Skip requirement references (often defined in other docs)
            if ref.ref_type == 'requirement':
                continue

            # Check if referenced item exists
            type_items = defined_ids.get(ref.ref_type, set())

            if ref.ref_id not in type_items:
                issues.append(ReferenceIssue(
                    reference_text=ref.text,
                    reference_type=ref.ref_type,
                    issue_type='broken',
                    location=ref.location,
                    confidence=0.90,
                    suggestion=f"Referenced {ref.ref_type} '{ref.ref_id}' not found in document",
                    context=ref.context
                ))

        return issues

    def _find_unreferenced_items(self, references: List[Reference],
                                defined_items: Dict[str, List[ReferencedItem]],
                                text: str) -> List[ReferenceIssue]:
        """Find defined items that are never referenced."""
        issues = []

        # Count references to each ID
        ref_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for ref in references:
            ref_counts[ref.ref_type][ref.ref_id] += 1

        # Check each defined item
        for item_type, items in defined_items.items():
            # Skip checking requirements (often cross-doc)
            if item_type == 'requirement':
                continue

            for item in items:
                count = ref_counts[item_type].get(item.item_id, 0)
                item.reference_count = count
                item.is_referenced = count > 0

                if not item.is_referenced:
                    # Tables and Figures should generally be referenced
                    if item_type in ['table', 'figure']:
                        issues.append(ReferenceIssue(
                            reference_text=f"{item_type.title()} {item.item_id}",
                            reference_type=item_type,
                            issue_type='unreferenced',
                            location=item.location,
                            confidence=0.75,
                            suggestion=f"This {item_type} is never referenced in the text",
                            context=item.title or ''
                        ))

        return issues

    def _check_format_consistency(self, references: List[Reference]) -> List[ReferenceIssue]:
        """Check for inconsistent reference formats."""
        issues = []

        # Group references by type
        by_type: Dict[str, List[Reference]] = defaultdict(list)
        for ref in references:
            by_type[ref.ref_type].append(ref)

        # Check each type for format consistency
        for ref_type, refs in by_type.items():
            if len(refs) < 2:
                continue

            # Extract format patterns
            formats = defaultdict(list)
            for ref in refs:
                # Normalize format (remove ID)
                format_key = re.sub(r'\d+(?:\.\d+)*', 'N', ref.text)
                format_key = re.sub(r'[A-Z]{2,5}[-_]\d+', 'ID', format_key)
                formats[format_key].append(ref)

            if len(formats) > 1:
                # Multiple formats used
                most_common = max(formats.keys(), key=lambda k: len(formats[k]))
                for format_key, format_refs in formats.items():
                    if format_key != most_common and len(format_refs) < len(refs) / 2:
                        for ref in format_refs[:3]:  # Report first 3 examples
                            issues.append(ReferenceIssue(
                                reference_text=ref.text,
                                reference_type=ref.ref_type,
                                issue_type='format_inconsistent',
                                location=ref.location,
                                confidence=0.70,
                                suggestion=f"Inconsistent format. Most common format is: {most_common}",
                                context=ref.context
                            ))

        return issues

    def _calculate_statistics(self, references: List[Reference],
                            defined_items: Dict[str, List[ReferencedItem]],
                            issues: List[ReferenceIssue]) -> Dict[str, Any]:
        """Calculate validation statistics."""
        # Count references by type
        refs_by_type = defaultdict(int)
        for ref in references:
            refs_by_type[ref.ref_type] += 1

        # Count defined items by type
        items_by_type = {k: len(v) for k, v in defined_items.items()}

        # Count issues by type
        issues_by_type = defaultdict(int)
        for issue in issues:
            issues_by_type[issue.issue_type] += 1

        return {
            'total_references': len(references),
            'references_by_type': dict(refs_by_type),
            'total_defined_items': sum(items_by_type.values()),
            'defined_items_by_type': items_by_type,
            'total_issues': len(issues),
            'issues_by_type': dict(issues_by_type),
            'broken_references': issues_by_type.get('broken', 0),
            'unreferenced_items': issues_by_type.get('unreferenced', 0),
            'format_inconsistencies': issues_by_type.get('format_inconsistent', 0)
        }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

_validator_instance: Optional[CrossReferenceValidator] = None


def get_cross_reference_validator() -> CrossReferenceValidator:
    """Get or create singleton validator."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = CrossReferenceValidator()
    return _validator_instance


def validate_cross_references(text: str) -> Dict[str, Any]:
    """
    Convenience function to validate cross-references.

    Args:
        text: Document text to validate

    Returns:
        Dict with issues and statistics
    """
    validator = get_cross_reference_validator()
    issues, statistics = validator.validate_text(text)

    return {
        'issues': [{
            'reference_text': i.reference_text,
            'reference_type': i.reference_type,
            'issue_type': i.issue_type,
            'location': i.location,
            'confidence': i.confidence,
            'suggestion': i.suggestion,
            'context': i.context
        } for i in issues],
        'statistics': statistics
    }


__all__ = [
    'CrossReferenceValidator',
    'ReferenceIssue',
    'Reference',
    'ReferencedItem',
    'get_cross_reference_validator',
    'validate_cross_references',
    'VERSION'
]
