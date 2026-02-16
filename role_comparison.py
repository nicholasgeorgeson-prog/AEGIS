"""
Role Comparison Module
======================
ENH-004: Multi-document comparison for side-by-side role analysis.

Compares roles extracted from multiple documents to identify:
- Common roles across documents
- Roles unique to specific documents
- Role responsibility variations
- Consistency analysis

Version: 1.0.0
Date: 2026-02-02
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json
import difflib

# Structured logging support
try:
    from config_logging import get_logger
    logger = get_logger('role_comparison')
except ImportError:
    import logging
    logger = logging.getLogger('role_comparison')


@dataclass
class RolePresence:
    """Tracks a role's presence across documents."""
    role_name: str
    documents: List[str] = field(default_factory=list)
    frequencies: Dict[str, int] = field(default_factory=dict)
    responsibilities: Dict[str, List[str]] = field(default_factory=dict)
    variants: Dict[str, Set[str]] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    @property
    def document_count(self) -> int:
        return len(self.documents)

    @property
    def total_frequency(self) -> int:
        return sum(self.frequencies.values())

    @property
    def avg_confidence(self) -> float:
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores.values()) / len(self.confidence_scores)

    def to_dict(self) -> dict:
        return {
            'role_name': self.role_name,
            'documents': self.documents,
            'document_count': self.document_count,
            'frequencies': self.frequencies,
            'total_frequency': self.total_frequency,
            'responsibilities': {k: list(v) for k, v in self.responsibilities.items()},
            'variants': {k: list(v) for k, v in self.variants.items()},
            'confidence_scores': self.confidence_scores,
            'avg_confidence': self.avg_confidence
        }


@dataclass
class ResponsibilityDiff:
    """Represents a difference in responsibilities for a role across documents."""
    role_name: str
    doc1_name: str
    doc2_name: str
    doc1_only: List[str]  # Responsibilities only in doc1
    doc2_only: List[str]  # Responsibilities only in doc2
    common: List[str]     # Responsibilities in both

    def to_dict(self) -> dict:
        return {
            'role_name': self.role_name,
            'doc1_name': self.doc1_name,
            'doc2_name': self.doc2_name,
            'doc1_only': self.doc1_only,
            'doc2_only': self.doc2_only,
            'common': self.common,
            'total_doc1': len(self.doc1_only) + len(self.common),
            'total_doc2': len(self.doc2_only) + len(self.common),
            'similarity_score': self._similarity_score()
        }

    def _similarity_score(self) -> float:
        """Calculate similarity between responsibility sets."""
        total = len(self.doc1_only) + len(self.doc2_only) + len(self.common)
        if total == 0:
            return 1.0
        return len(self.common) / total


@dataclass
class ComparisonResult:
    """Complete comparison result across multiple documents."""
    documents: List[str]
    common_roles: List[RolePresence]      # Roles in ALL documents
    partial_roles: List[RolePresence]     # Roles in SOME documents
    unique_roles: Dict[str, List[str]]    # Roles unique to each document
    responsibility_diffs: List[ResponsibilityDiff]
    summary: Dict[str, Any]

    def to_dict(self) -> dict:
        return {
            'documents': self.documents,
            'common_roles': [r.to_dict() for r in self.common_roles],
            'partial_roles': [r.to_dict() for r in self.partial_roles],
            'unique_roles': self.unique_roles,
            'responsibility_diffs': [d.to_dict() for d in self.responsibility_diffs],
            'summary': self.summary
        }


class RoleComparator:
    """
    Compares roles extracted from multiple documents.

    Provides side-by-side analysis of:
    - Role presence across documents
    - Responsibility variations
    - Consistency metrics
    """

    def __init__(self, similarity_threshold: float = 0.8):
        """
        Initialize the comparator.

        Args:
            similarity_threshold: Minimum similarity to consider roles as matching (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
        self._role_aliases: Dict[str, str] = {}  # Maps variations to canonical names

    def compare(
        self,
        documents: Dict[str, Dict[str, Any]]
    ) -> ComparisonResult:
        """
        Compare roles across multiple documents.

        Args:
            documents: Dict mapping document names to role extraction results.
                       Each result should have 'roles' key with Dict[str, ExtractedRole.to_dict()]

        Returns:
            ComparisonResult with full analysis
        """
        logger.info(f"Comparing roles across {len(documents)} documents")

        doc_names = list(documents.keys())

        # Build role presence map
        role_presence = self._build_role_presence_map(documents)

        # Categorize roles
        common_roles = []
        partial_roles = []
        unique_roles = defaultdict(list)

        for role_name, presence in role_presence.items():
            if presence.document_count == len(doc_names):
                common_roles.append(presence)
            elif presence.document_count == 1:
                doc = presence.documents[0]
                unique_roles[doc].append(role_name)
            else:
                partial_roles.append(presence)

        # Sort by frequency/confidence
        common_roles.sort(key=lambda r: (-r.total_frequency, -r.avg_confidence))
        partial_roles.sort(key=lambda r: (-r.document_count, -r.total_frequency))

        # Compute responsibility diffs for common roles
        responsibility_diffs = []
        if len(doc_names) >= 2:
            for presence in common_roles:
                diff = self._compute_responsibility_diff(
                    presence.role_name,
                    doc_names[0], presence.responsibilities.get(doc_names[0], []),
                    doc_names[1], presence.responsibilities.get(doc_names[1], [])
                )
                if diff.doc1_only or diff.doc2_only:
                    responsibility_diffs.append(diff)

        # Build summary statistics
        summary = self._build_summary(
            doc_names, role_presence, common_roles, partial_roles, unique_roles
        )

        logger.info(f"Comparison complete: {len(common_roles)} common, "
                   f"{len(partial_roles)} partial, {sum(len(v) for v in unique_roles.values())} unique")

        return ComparisonResult(
            documents=doc_names,
            common_roles=common_roles,
            partial_roles=partial_roles,
            unique_roles=dict(unique_roles),
            responsibility_diffs=responsibility_diffs,
            summary=summary
        )

    def _build_role_presence_map(
        self,
        documents: Dict[str, Dict[str, Any]]
    ) -> Dict[str, RolePresence]:
        """Build a map of role names to their presence across documents."""
        role_map: Dict[str, RolePresence] = {}

        for doc_name, doc_data in documents.items():
            roles = doc_data.get('roles', {})

            for role_name, role_data in roles.items():
                # Normalize role name
                canonical = self._normalize_role_name(role_name)

                if canonical not in role_map:
                    role_map[canonical] = RolePresence(role_name=canonical)

                presence = role_map[canonical]

                # Add document if not already present
                if doc_name not in presence.documents:
                    presence.documents.append(doc_name)

                # Add frequency
                freq = role_data.get('frequency', 1)
                presence.frequencies[doc_name] = freq

                # Add responsibilities
                responsibilities = role_data.get('responsibilities', [])
                if doc_name not in presence.responsibilities:
                    presence.responsibilities[doc_name] = []
                presence.responsibilities[doc_name].extend(responsibilities)

                # Add variants
                variants = role_data.get('variants', [])
                if doc_name not in presence.variants:
                    presence.variants[doc_name] = set()
                presence.variants[doc_name].update(variants)

                # Add confidence
                confidence = role_data.get('avg_confidence', 0.8)
                presence.confidence_scores[doc_name] = confidence

        return role_map

    def _normalize_role_name(self, role_name: str) -> str:
        """Normalize a role name for comparison."""
        # Check if we already have a canonical mapping
        if role_name.lower() in self._role_aliases:
            return self._role_aliases[role_name.lower()]

        # Basic normalization
        normalized = role_name.strip().title()

        # Handle common variations
        normalized = normalized.replace('  ', ' ')

        # Remove common suffixes that don't change meaning
        for suffix in ['(s)', 's']:
            if normalized.endswith(suffix) and len(normalized) > len(suffix) + 3:
                normalized = normalized[:-len(suffix)]

        return normalized

    def _compute_responsibility_diff(
        self,
        role_name: str,
        doc1_name: str,
        doc1_responsibilities: List[str],
        doc2_name: str,
        doc2_responsibilities: List[str]
    ) -> ResponsibilityDiff:
        """Compute the difference in responsibilities between two documents."""
        # Normalize responsibilities for comparison
        doc1_set = set(r.lower().strip() for r in doc1_responsibilities if r.strip())
        doc2_set = set(r.lower().strip() for r in doc2_responsibilities if r.strip())

        # Find common, doc1-only, doc2-only
        common = doc1_set & doc2_set
        doc1_only = doc1_set - doc2_set
        doc2_only = doc2_set - doc1_set

        return ResponsibilityDiff(
            role_name=role_name,
            doc1_name=doc1_name,
            doc2_name=doc2_name,
            doc1_only=list(doc1_only),
            doc2_only=list(doc2_only),
            common=list(common)
        )

    def _build_summary(
        self,
        doc_names: List[str],
        role_presence: Dict[str, RolePresence],
        common_roles: List[RolePresence],
        partial_roles: List[RolePresence],
        unique_roles: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Build summary statistics for the comparison."""
        total_roles = len(role_presence)

        # Roles per document
        roles_per_doc = {}
        for doc_name in doc_names:
            count = sum(1 for p in role_presence.values() if doc_name in p.documents)
            roles_per_doc[doc_name] = count

        # Consistency score (% of roles that are common)
        consistency_score = len(common_roles) / total_roles if total_roles > 0 else 1.0

        # Most frequent common roles
        top_common = [r.role_name for r in common_roles[:5]]

        return {
            'total_documents': len(doc_names),
            'total_unique_roles': total_roles,
            'common_role_count': len(common_roles),
            'partial_role_count': len(partial_roles),
            'unique_role_count': sum(len(v) for v in unique_roles.values()),
            'roles_per_document': roles_per_doc,
            'consistency_score': round(consistency_score, 3),
            'top_common_roles': top_common,
            'document_names': doc_names
        }

    def find_similar_roles(
        self,
        roles: List[str],
        threshold: float = None
    ) -> List[Tuple[str, str, float]]:
        """
        Find similar role names that might be variations of each other.

        Args:
            roles: List of role names
            threshold: Similarity threshold (uses self.similarity_threshold if None)

        Returns:
            List of (role1, role2, similarity_score) tuples
        """
        if threshold is None:
            threshold = self.similarity_threshold

        similar_pairs = []
        roles_lower = [r.lower() for r in roles]

        for i, role1 in enumerate(roles):
            for j, role2 in enumerate(roles):
                if i >= j:
                    continue

                # Compute similarity
                similarity = difflib.SequenceMatcher(
                    None, roles_lower[i], roles_lower[j]
                ).ratio()

                if similarity >= threshold and similarity < 1.0:
                    similar_pairs.append((role1, role2, round(similarity, 3)))

        # Sort by similarity (highest first)
        similar_pairs.sort(key=lambda x: -x[2])

        return similar_pairs

    def generate_comparison_report(
        self,
        result: ComparisonResult,
        format: str = 'text'
    ) -> str:
        """
        Generate a human-readable comparison report.

        Args:
            result: ComparisonResult to format
            format: Output format ('text', 'markdown', 'html')

        Returns:
            Formatted report string
        """
        if format == 'markdown':
            return self._generate_markdown_report(result)
        elif format == 'html':
            return self._generate_html_report(result)
        else:
            return self._generate_text_report(result)

    def _generate_text_report(self, result: ComparisonResult) -> str:
        """Generate plain text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("ROLE COMPARISON REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Documents compared: {', '.join(result.documents)}")
        lines.append(f"Total unique roles: {result.summary['total_unique_roles']}")
        lines.append(f"Common roles (in all documents): {result.summary['common_role_count']}")
        lines.append(f"Partial roles (in some documents): {result.summary['partial_role_count']}")
        lines.append(f"Unique roles (in one document only): {result.summary['unique_role_count']}")
        lines.append(f"Consistency score: {result.summary['consistency_score']:.1%}")
        lines.append("")

        # Roles per document
        lines.append("ROLES PER DOCUMENT")
        lines.append("-" * 40)
        for doc, count in result.summary['roles_per_document'].items():
            lines.append(f"  {doc}: {count} roles")
        lines.append("")

        # Common roles
        if result.common_roles:
            lines.append("COMMON ROLES (found in all documents)")
            lines.append("-" * 40)
            for presence in result.common_roles[:10]:
                lines.append(f"  ■ {presence.role_name}")
                lines.append(f"    Total occurrences: {presence.total_frequency}")
                for doc in presence.documents:
                    freq = presence.frequencies.get(doc, 0)
                    lines.append(f"      - {doc}: {freq} times")
            if len(result.common_roles) > 10:
                lines.append(f"  ... and {len(result.common_roles) - 10} more")
            lines.append("")

        # Partial roles
        if result.partial_roles:
            lines.append("PARTIAL ROLES (found in some documents)")
            lines.append("-" * 40)
            for presence in result.partial_roles[:10]:
                docs_str = ", ".join(presence.documents)
                lines.append(f"  ■ {presence.role_name}")
                lines.append(f"    Found in: {docs_str}")
            if len(result.partial_roles) > 10:
                lines.append(f"  ... and {len(result.partial_roles) - 10} more")
            lines.append("")

        # Unique roles
        if any(result.unique_roles.values()):
            lines.append("UNIQUE ROLES (found in only one document)")
            lines.append("-" * 40)
            for doc, roles in result.unique_roles.items():
                if roles:
                    lines.append(f"  {doc}:")
                    for role in roles[:5]:
                        lines.append(f"    - {role}")
                    if len(roles) > 5:
                        lines.append(f"    ... and {len(roles) - 5} more")
            lines.append("")

        # Responsibility differences
        if result.responsibility_diffs:
            lines.append("RESPONSIBILITY DIFFERENCES")
            lines.append("-" * 40)
            for diff in result.responsibility_diffs[:5]:
                lines.append(f"  ■ {diff.role_name}")
                if diff.doc1_only:
                    lines.append(f"    Only in {diff.doc1_name}: {len(diff.doc1_only)} responsibilities")
                if diff.doc2_only:
                    lines.append(f"    Only in {diff.doc2_name}: {len(diff.doc2_only)} responsibilities")
                lines.append(f"    Common responsibilities: {len(diff.common)}")
            if len(result.responsibility_diffs) > 5:
                lines.append(f"  ... and {len(result.responsibility_diffs) - 5} more")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_markdown_report(self, result: ComparisonResult) -> str:
        """Generate Markdown report."""
        lines = []
        lines.append("# Role Comparison Report")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Documents compared:** {', '.join(result.documents)}")
        lines.append(f"- **Total unique roles:** {result.summary['total_unique_roles']}")
        lines.append(f"- **Consistency score:** {result.summary['consistency_score']:.1%}")
        lines.append("")

        # Common roles table
        if result.common_roles:
            lines.append("## Common Roles")
            lines.append("")
            lines.append("| Role | Total Occurrences | " + " | ".join(result.documents) + " |")
            lines.append("|------|------------------|" + "|".join(["---"] * len(result.documents)) + "|")
            for presence in result.common_roles[:15]:
                freq_cells = [str(presence.frequencies.get(d, 0)) for d in result.documents]
                lines.append(f"| {presence.role_name} | {presence.total_frequency} | {' | '.join(freq_cells)} |")
            lines.append("")

        # Unique roles
        if any(result.unique_roles.values()):
            lines.append("## Unique Roles")
            lines.append("")
            for doc, roles in result.unique_roles.items():
                if roles:
                    lines.append(f"### {doc}")
                    lines.append("")
                    for role in roles:
                        lines.append(f"- {role}")
                    lines.append("")

        return "\n".join(lines)

    def _generate_html_report(self, result: ComparisonResult) -> str:
        """Generate HTML report."""
        html = ['<div class="role-comparison-report">']
        html.append('<h2>Role Comparison Report</h2>')

        # Summary
        html.append('<div class="summary">')
        html.append(f'<p><strong>Documents:</strong> {", ".join(result.documents)}</p>')
        html.append(f'<p><strong>Consistency:</strong> {result.summary["consistency_score"]:.1%}</p>')
        html.append('</div>')

        # Common roles table
        if result.common_roles:
            html.append('<h3>Common Roles</h3>')
            html.append('<table class="role-table">')
            html.append('<thead><tr><th>Role</th><th>Total</th>')
            for doc in result.documents:
                html.append(f'<th>{doc}</th>')
            html.append('</tr></thead><tbody>')
            for presence in result.common_roles[:15]:
                html.append(f'<tr><td>{presence.role_name}</td>')
                html.append(f'<td>{presence.total_frequency}</td>')
                for doc in result.documents:
                    html.append(f'<td>{presence.frequencies.get(doc, 0)}</td>')
                html.append('</tr>')
            html.append('</tbody></table>')

        html.append('</div>')

        return '\n'.join(html)


# Convenience function
def compare_documents(
    documents: Dict[str, Dict[str, Any]],
    **kwargs
) -> ComparisonResult:
    """
    Compare roles across multiple documents.

    Args:
        documents: Dict mapping document names to role extraction results
        **kwargs: Additional arguments for RoleComparator

    Returns:
        ComparisonResult
    """
    comparator = RoleComparator(**kwargs)
    return comparator.compare(documents)


# Export main classes
__all__ = [
    'RoleComparator',
    'RolePresence',
    'ResponsibilityDiff',
    'ComparisonResult',
    'compare_documents'
]
