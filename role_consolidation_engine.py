"""
Role Consolidation Engine v1.0
Intelligent duplicate/similar role detection with detailed reporting

DESIGN: Modular component that can be:
1. Imported into other tools (like Document Review Tool)
2. Run standalone for role standardization projects

ACCURACY FOCUS:
- Multiple similarity algorithms (not just string matching)
- Confidence scoring with explanations
- Human-in-the-loop review process
- Detailed audit trail

Author: Nick / SAIC Systems Engineering
"""

import os
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from difflib import SequenceMatcher
import math

# For standalone operation, try to import from sibling modules
try:
    from role_management_studio_v3 import (
        RoleDatabase, StandardRole, RoleResponsibility, 
        SourceDocument, StudioSettings
    )
except ImportError:
    # Will be provided when integrated into another tool
    pass


# =============================================================================
# SIMILARITY ALGORITHMS
# =============================================================================

class SimilarityEngine:
    """
    Multi-algorithm similarity detection for role names and responsibilities.
    Uses multiple approaches to ensure accuracy.
    """
    
    # Common role name variations
    EQUIVALENT_TERMS = {
        'engineer': ['engr', 'eng'],
        'manager': ['mgr', 'mngr'],
        'director': ['dir'],
        'coordinator': ['coord'],
        'specialist': ['spec'],
        'technician': ['tech'],
        'supervisor': ['supv', 'supvr'],
        'administrator': ['admin'],
        'representative': ['rep'],
        'analyst': ['anlyst'],
        'associate': ['assoc'],
        'assistant': ['asst'],
        'senior': ['sr', 'snr'],
        'junior': ['jr', 'jnr'],
        'principal': ['prin'],
        'chief': ['chf'],
        'lead': ['ld'],
        'quality': ['qa', 'qc'],
        'systems': ['sys', 'system'],
        'software': ['sw'],
        'hardware': ['hw'],
        'manufacturing': ['mfg'],
        'configuration': ['config', 'cm'],
        'requirements': ['reqts', 'reqs'],
        'verification': ['verif'],
        'validation': ['valid'],
        'integration': ['integ', 'int'],
        'development': ['dev'],
        'production': ['prod'],
        'operations': ['ops'],
        'maintenance': ['maint'],
        'logistics': ['log'],
        'procurement': ['proc'],
        'subcontract': ['subk'],
        'program': ['pgm'],
        'project': ['proj'],
    }
    
    # Words to ignore in comparison
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'of', 'for', 'to', 'in', 'on', 'at',
        'by', 'with', 'from', 'as', 'is', 'are', 'was', 'were', 'be', 'been'
    }
    
    @classmethod
    def normalize_role_name(cls, name: str) -> str:
        """Normalize a role name for comparison."""
        # Lowercase
        normalized = name.lower().strip()
        
        # Expand abbreviations
        for full, abbrevs in cls.EQUIVALENT_TERMS.items():
            for abbrev in abbrevs:
                # Match as whole word
                normalized = re.sub(rf'\b{abbrev}\b', full, normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """Tokenize text into meaningful words."""
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return [w for w in words if w not in cls.STOP_WORDS and len(w) > 1]
    
    @classmethod
    def string_similarity(cls, s1: str, s2: str) -> float:
        """Basic string similarity using SequenceMatcher."""
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
    
    @classmethod
    def normalized_similarity(cls, s1: str, s2: str) -> float:
        """Similarity after normalization (expands abbreviations)."""
        n1 = cls.normalize_role_name(s1)
        n2 = cls.normalize_role_name(s2)
        return SequenceMatcher(None, n1, n2).ratio()
    
    @classmethod
    def token_similarity(cls, s1: str, s2: str) -> float:
        """Jaccard similarity of tokens."""
        tokens1 = set(cls.tokenize(s1))
        tokens2 = set(cls.tokenize(s2))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union) if union else 0.0
    
    @classmethod
    def semantic_similarity(cls, s1: str, s2: str) -> float:
        """
        Semantic similarity based on role structure patterns.
        Considers prefix (adjective) + core role + suffix (specialization)
        """
        n1 = cls.normalize_role_name(s1)
        n2 = cls.normalize_role_name(s2)
        
        # Extract core role (usually the noun at the end)
        core_roles = ['engineer', 'manager', 'director', 'coordinator', 'specialist',
                     'technician', 'supervisor', 'analyst', 'lead', 'chief', 
                     'inspector', 'auditor', 'planner', 'controller', 'officer']
        
        core1 = None
        core2 = None
        
        for core in core_roles:
            if core in n1:
                core1 = core
            if core in n2:
                core2 = core
        
        # If same core role, they're likely related
        if core1 and core2 and core1 == core2:
            # Check for similar modifiers
            mods1 = n1.replace(core1, '').strip()
            mods2 = n2.replace(core2, '').strip()
            
            if mods1 == mods2:
                return 1.0  # Exact match after normalization
            
            # Partial modifier match
            mod_sim = cls.token_similarity(mods1, mods2)
            return 0.7 + (0.3 * mod_sim)  # High base similarity + modifier bonus
        
        return 0.0
    
    @classmethod
    def compute_overall_similarity(cls, s1: str, s2: str) -> Tuple[float, Dict[str, float]]:
        """
        Compute overall similarity using multiple algorithms.
        Returns (overall_score, breakdown_dict)
        """
        scores = {
            'string': cls.string_similarity(s1, s2),
            'normalized': cls.normalized_similarity(s1, s2),
            'token': cls.token_similarity(s1, s2),
            'semantic': cls.semantic_similarity(s1, s2)
        }
        
        # Weighted combination (semantic and normalized weighted higher for accuracy)
        weights = {
            'string': 0.15,
            'normalized': 0.35,
            'token': 0.20,
            'semantic': 0.30
        }
        
        overall = sum(scores[k] * weights[k] for k in scores)
        
        return overall, scores
    
    @classmethod
    def explain_similarity(cls, s1: str, s2: str, scores: Dict[str, float]) -> List[str]:
        """Generate human-readable explanations for similarity scores."""
        explanations = []
        
        n1 = cls.normalize_role_name(s1)
        n2 = cls.normalize_role_name(s2)
        
        # Check for exact match after normalization
        if n1 == n2:
            explanations.append(f"✓ Exact match after normalizing abbreviations")
            explanations.append(f"  '{s1}' → '{n1}'")
            if s1.lower() != n1:
                explanations.append(f"  '{s2}' → '{n2}'")
            return explanations
        
        # Explain string similarity
        if scores['string'] > 0.8:
            explanations.append(f"✓ Very similar spelling ({scores['string']:.0%} match)")
        elif scores['string'] > 0.6:
            explanations.append(f"○ Moderately similar spelling ({scores['string']:.0%} match)")
        
        # Explain normalization impact
        if scores['normalized'] > scores['string'] + 0.1:
            explanations.append(f"✓ Abbreviation expansion increases match")
            explanations.append(f"  '{s1}' → '{n1}'")
            explanations.append(f"  '{s2}' → '{n2}'")
        
        # Explain token overlap
        tokens1 = set(cls.tokenize(s1))
        tokens2 = set(cls.tokenize(s2))
        common = tokens1 & tokens2
        
        if common:
            explanations.append(f"✓ Shared terms: {', '.join(sorted(common))}")
        
        only1 = tokens1 - tokens2
        only2 = tokens2 - tokens1
        
        if only1:
            explanations.append(f"  Only in '{s1}': {', '.join(sorted(only1))}")
        if only2:
            explanations.append(f"  Only in '{s2}': {', '.join(sorted(only2))}")
        
        # Explain semantic match
        if scores['semantic'] > 0.7:
            explanations.append(f"✓ Same core role type with similar qualifiers")
        
        return explanations


# =============================================================================
# CONSOLIDATION CANDIDATE
# =============================================================================

@dataclass
class ConsolidationCandidate:
    """A potential consolidation of similar roles."""
    
    id: str
    primary_role_id: str
    primary_role_name: str
    secondary_role_ids: List[str]
    secondary_role_names: List[str]
    
    # Similarity analysis
    overall_similarity: float
    similarity_breakdown: Dict[str, float]
    explanations: List[str]
    
    # Impact analysis
    documents_affected: int
    responsibilities_to_merge: int
    
    # Recommendation
    recommendation: str  # "merge", "review", "keep_separate"
    confidence: float
    
    # Status
    status: str  # "pending", "approved", "rejected", "completed"
    reviewed_by: str
    review_date: str
    review_notes: str
    
    # Suggested merge result
    suggested_canonical_name: str
    suggested_aliases: List[str]
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConsolidationCandidate':
        return cls(**data)


# =============================================================================
# CONSOLIDATION ENGINE
# =============================================================================

class RoleConsolidationEngine:
    """
    Detects and manages role consolidation candidates.
    
    Usage:
        engine = RoleConsolidationEngine(database)
        candidates = engine.find_consolidation_candidates()
        report = engine.generate_consolidation_report(candidates)
    """
    
    # Thresholds (tuned for accuracy over recall)
    MERGE_THRESHOLD = 0.85  # High confidence merge
    REVIEW_THRESHOLD = 0.65  # Needs human review
    
    def __init__(self, database=None, roles: List[StandardRole] = None):
        """
        Initialize with either a database or a list of roles.
        This allows use within the studio or standalone.
        """
        self.database = database
        
        if roles:
            self._roles = {r.id: r for r in roles}
        elif database:
            self._roles = {r.id: r for r in database.get_all_roles()}
        else:
            self._roles = {}
        
        self._candidates: List[ConsolidationCandidate] = []
    
    def find_consolidation_candidates(self, 
                                      min_similarity: float = None) -> List[ConsolidationCandidate]:
        """
        Analyze all roles and find potential consolidation candidates.
        
        Returns list of ConsolidationCandidate objects sorted by similarity (highest first).
        """
        if min_similarity is None:
            min_similarity = self.REVIEW_THRESHOLD
        
        candidates = []
        roles = list(self._roles.values())
        processed_pairs = set()
        
        for i, role1 in enumerate(roles):
            for role2 in roles[i+1:]:
                # Skip if already processed
                pair_key = tuple(sorted([role1.id, role2.id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                # Calculate similarity
                overall, breakdown = SimilarityEngine.compute_overall_similarity(
                    role1.canonical_name, role2.canonical_name
                )
                
                if overall >= min_similarity:
                    # Generate explanations
                    explanations = SimilarityEngine.explain_similarity(
                        role1.canonical_name, role2.canonical_name, breakdown
                    )
                    
                    # Determine primary role (higher usage wins)
                    if role1.usage_count >= role2.usage_count:
                        primary, secondary = role1, role2
                    else:
                        primary, secondary = role2, role1
                    
                    # Calculate impact
                    docs_affected = len(set(primary.source_document_ids) | 
                                       set(secondary.source_document_ids))
                    
                    resps_to_merge = 0
                    if self.database:
                        resps1 = self.database.get_responsibilities_for_role(primary.id, active_only=False)
                        resps2 = self.database.get_responsibilities_for_role(secondary.id, active_only=False)
                        resps_to_merge = len(resps1) + len(resps2)
                    
                    # Determine recommendation
                    if overall >= self.MERGE_THRESHOLD:
                        recommendation = "merge"
                        confidence = min(1.0, overall + 0.1)
                    else:
                        recommendation = "review"
                        confidence = overall
                    
                    # Suggest canonical name and aliases
                    suggested_name = primary.canonical_name
                    suggested_aliases = list(set(
                        [secondary.canonical_name] + 
                        primary.aliases + 
                        secondary.aliases
                    ))
                    
                    candidate = ConsolidationCandidate(
                        id=hashlib.md5(f"{primary.id}{secondary.id}".encode()).hexdigest()[:12],
                        primary_role_id=primary.id,
                        primary_role_name=primary.canonical_name,
                        secondary_role_ids=[secondary.id],
                        secondary_role_names=[secondary.canonical_name],
                        overall_similarity=overall,
                        similarity_breakdown=breakdown,
                        explanations=explanations,
                        documents_affected=docs_affected,
                        responsibilities_to_merge=resps_to_merge,
                        recommendation=recommendation,
                        confidence=confidence,
                        status="pending",
                        reviewed_by="",
                        review_date="",
                        review_notes="",
                        suggested_canonical_name=suggested_name,
                        suggested_aliases=suggested_aliases
                    )
                    
                    candidates.append(candidate)
        
        # Sort by similarity (highest first)
        candidates.sort(key=lambda c: -c.overall_similarity)
        
        # Group related candidates (A≈B and B≈C means A,B,C should merge)
        candidates = self._group_related_candidates(candidates)
        
        self._candidates = candidates
        return candidates
    
    def _group_related_candidates(self, 
                                  candidates: List[ConsolidationCandidate]) -> List[ConsolidationCandidate]:
        """
        Group related candidates together.
        If A≈B and B≈C, create a single candidate for A,B,C.
        """
        if not candidates:
            return candidates
        
        # Build a graph of similar roles
        role_groups = {}  # role_id -> group_id
        groups = {}  # group_id -> set of role_ids
        
        for candidate in candidates:
            if candidate.recommendation != "merge":
                continue
            
            all_ids = [candidate.primary_role_id] + candidate.secondary_role_ids
            
            # Find existing groups for these roles
            existing_groups = set()
            for role_id in all_ids:
                if role_id in role_groups:
                    existing_groups.add(role_groups[role_id])
            
            if not existing_groups:
                # Create new group
                group_id = candidate.id
                groups[group_id] = set(all_ids)
                for role_id in all_ids:
                    role_groups[role_id] = group_id
            else:
                # Merge into first existing group
                target_group = min(existing_groups)
                for group_id in existing_groups:
                    if group_id != target_group:
                        groups[target_group].update(groups[group_id])
                        del groups[group_id]
                
                groups[target_group].update(all_ids)
                for role_id in groups[target_group]:
                    role_groups[role_id] = target_group
        
        # Create consolidated candidates from groups
        consolidated = []
        processed_groups = set()
        
        for candidate in candidates:
            all_ids = set([candidate.primary_role_id] + candidate.secondary_role_ids)
            
            # Check if this is part of a larger group
            if candidate.primary_role_id in role_groups:
                group_id = role_groups[candidate.primary_role_id]
                
                if group_id in processed_groups:
                    continue
                processed_groups.add(group_id)
                
                group_role_ids = groups[group_id]
                
                if len(group_role_ids) > 2:
                    # Create a multi-role consolidation candidate
                    group_roles = [self._roles[rid] for rid in group_role_ids if rid in self._roles]
                    
                    # Sort by usage count to find primary
                    group_roles.sort(key=lambda r: -r.usage_count)
                    
                    primary = group_roles[0]
                    secondaries = group_roles[1:]
                    
                    # Recalculate metrics
                    docs = set()
                    for r in group_roles:
                        docs.update(r.source_document_ids)
                    
                    new_candidate = ConsolidationCandidate(
                        id=group_id,
                        primary_role_id=primary.id,
                        primary_role_name=primary.canonical_name,
                        secondary_role_ids=[r.id for r in secondaries],
                        secondary_role_names=[r.canonical_name for r in secondaries],
                        overall_similarity=candidate.overall_similarity,
                        similarity_breakdown=candidate.similarity_breakdown,
                        explanations=candidate.explanations + [
                            f"✓ Part of larger group: {len(group_roles)} related roles detected"
                        ],
                        documents_affected=len(docs),
                        responsibilities_to_merge=candidate.responsibilities_to_merge,
                        recommendation="merge",
                        confidence=candidate.confidence,
                        status="pending",
                        reviewed_by="",
                        review_date="",
                        review_notes="",
                        suggested_canonical_name=primary.canonical_name,
                        suggested_aliases=list(set(
                            [r.canonical_name for r in secondaries] +
                            sum([r.aliases for r in group_roles], [])
                        ))
                    )
                    consolidated.append(new_candidate)
                    continue
            
            consolidated.append(candidate)
        
        return consolidated
    
    def generate_consolidation_report(self, 
                                      candidates: List[ConsolidationCandidate] = None,
                                      format: str = "text") -> str:
        """
        Generate a detailed consolidation report.
        
        Args:
            candidates: List of candidates (uses cached if None)
            format: "text", "markdown", or "html"
        
        Returns:
            Formatted report string
        """
        if candidates is None:
            candidates = self._candidates
        
        if format == "markdown":
            return self._generate_markdown_report(candidates)
        elif format == "html":
            return self._generate_html_report(candidates)
        else:
            return self._generate_text_report(candidates)
    
    def _generate_text_report(self, candidates: List[ConsolidationCandidate]) -> str:
        """Generate plain text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("ROLE CONSOLIDATION ANALYSIS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")
        
        # Summary
        merge_count = sum(1 for c in candidates if c.recommendation == "merge")
        review_count = sum(1 for c in candidates if c.recommendation == "review")
        
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 40)
        lines.append(f"Total potential consolidations: {len(candidates)}")
        lines.append(f"  Recommended for merge: {merge_count}")
        lines.append(f"  Requires review: {review_count}")
        lines.append("")
        
        if not candidates:
            lines.append("No consolidation candidates found.")
            lines.append("All roles appear to be sufficiently distinct.")
            return "\n".join(lines)
        
        # High confidence merges
        merges = [c for c in candidates if c.recommendation == "merge"]
        if merges:
            lines.append("")
            lines.append("HIGH CONFIDENCE MERGE RECOMMENDATIONS")
            lines.append("=" * 60)
            lines.append("")
            
            for i, candidate in enumerate(merges, 1):
                lines.append(f"Recommendation #{i}")
                lines.append("-" * 40)
                lines.append(f"Similarity: {candidate.overall_similarity:.1%} ({candidate.confidence:.1%} confidence)")
                lines.append("")
                lines.append("Roles to Merge:")
                lines.append(f"  PRIMARY:   {candidate.primary_role_name}")
                for name in candidate.secondary_role_names:
                    lines.append(f"  SECONDARY: {name}")
                lines.append("")
                lines.append("Why these should be merged:")
                for exp in candidate.explanations:
                    lines.append(f"  {exp}")
                lines.append("")
                lines.append(f"Impact: {candidate.documents_affected} documents, {candidate.responsibilities_to_merge} responsibilities")
                lines.append("")
                lines.append("Suggested Result:")
                lines.append(f"  Canonical Name: {candidate.suggested_canonical_name}")
                lines.append(f"  Aliases: {', '.join(candidate.suggested_aliases)}")
                lines.append("")
                lines.append("")
        
        # Review candidates
        reviews = [c for c in candidates if c.recommendation == "review"]
        if reviews:
            lines.append("")
            lines.append("REQUIRES HUMAN REVIEW")
            lines.append("=" * 60)
            lines.append("")
            
            for i, candidate in enumerate(reviews, 1):
                lines.append(f"Review Item #{i}")
                lines.append("-" * 40)
                lines.append(f"Similarity: {candidate.overall_similarity:.1%}")
                lines.append("")
                lines.append("Potentially Similar Roles:")
                lines.append(f"  1. {candidate.primary_role_name}")
                for j, name in enumerate(candidate.secondary_role_names, 2):
                    lines.append(f"  {j}. {name}")
                lines.append("")
                lines.append("Analysis:")
                for exp in candidate.explanations:
                    lines.append(f"  {exp}")
                lines.append("")
                lines.append("Please review and determine if these represent the same role.")
                lines.append("")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_markdown_report(self, candidates: List[ConsolidationCandidate]) -> str:
        """Generate markdown report."""
        lines = []
        lines.append("# Role Consolidation Analysis Report")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        
        # Summary
        merge_count = sum(1 for c in candidates if c.recommendation == "merge")
        review_count = sum(1 for c in candidates if c.recommendation == "review")
        
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Candidates | {len(candidates)} |")
        lines.append(f"| Recommended Merges | {merge_count} |")
        lines.append(f"| Requires Review | {review_count} |")
        lines.append("")
        
        if not candidates:
            lines.append("**No consolidation candidates found.** All roles appear to be sufficiently distinct.")
            return "\n".join(lines)
        
        # Merges
        merges = [c for c in candidates if c.recommendation == "merge"]
        if merges:
            lines.append("## High Confidence Merge Recommendations")
            lines.append("")
            
            for i, c in enumerate(merges, 1):
                lines.append(f"### {i}. Merge: {c.primary_role_name}")
                lines.append("")
                lines.append(f"**Similarity:** {c.overall_similarity:.1%} | **Confidence:** {c.confidence:.1%}")
                lines.append("")
                lines.append("**Roles to Consolidate:**")
                lines.append(f"- ✅ **{c.primary_role_name}** (primary)")
                for name in c.secondary_role_names:
                    lines.append(f"- ➡️ {name}")
                lines.append("")
                lines.append("**Why Merge:**")
                for exp in c.explanations:
                    lines.append(f"- {exp}")
                lines.append("")
                lines.append(f"**Impact:** {c.documents_affected} documents, {c.responsibilities_to_merge} responsibilities")
                lines.append("")
                lines.append("**Suggested Result:**")
                lines.append(f"- Canonical: `{c.suggested_canonical_name}`")
                lines.append(f"- Aliases: {', '.join(f'`{a}`' for a in c.suggested_aliases)}")
                lines.append("")
                lines.append("---")
                lines.append("")
        
        # Reviews
        reviews = [c for c in candidates if c.recommendation == "review"]
        if reviews:
            lines.append("## Requires Human Review")
            lines.append("")
            
            for i, c in enumerate(reviews, 1):
                lines.append(f"### Review {i}: {c.primary_role_name} ↔ {c.secondary_role_names[0]}")
                lines.append("")
                lines.append(f"**Similarity:** {c.overall_similarity:.1%}")
                lines.append("")
                lines.append("**Potentially Similar:**")
                lines.append(f"1. {c.primary_role_name}")
                for j, name in enumerate(c.secondary_role_names, 2):
                    lines.append(f"{j}. {name}")
                lines.append("")
                lines.append("**Analysis:**")
                for exp in c.explanations:
                    lines.append(f"- {exp}")
                lines.append("")
                lines.append("⚠️ *Please review and determine if these represent the same role.*")
                lines.append("")
                lines.append("---")
                lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_report(self, candidates: List[ConsolidationCandidate]) -> str:
        """Generate HTML report."""
        merge_count = sum(1 for c in candidates if c.recommendation == "merge")
        review_count = sum(1 for c in candidates if c.recommendation == "review")
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Role Consolidation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #0f172a; margin-bottom: 0.5rem; }}
        .timestamp {{ color: #64748b; margin-bottom: 2rem; }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .summary-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-value {{ font-size: 2rem; font-weight: 700; color: #2563eb; }}
        .summary-label {{ color: #64748b; font-size: 0.875rem; }}
        
        .section {{ margin-bottom: 2rem; }}
        .section-title {{
            font-size: 1.25rem;
            color: #0f172a;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 1rem;
        }}
        
        .card {{
            background: white;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1.5rem;
            margin-bottom: 1rem;
        }}
        .card.merge {{ border-left: 4px solid #10b981; }}
        .card.review {{ border-left: 4px solid #f59e0b; }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        .card-title {{ font-weight: 600; font-size: 1.1rem; }}
        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        .badge-merge {{ background: #d1fae5; color: #065f46; }}
        .badge-review {{ background: #fef3c7; color: #92400e; }}
        
        .similarity-bar {{
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }}
        .similarity-fill {{
            height: 100%;
            background: linear-gradient(90deg, #10b981, #2563eb);
            border-radius: 4px;
        }}
        
        .role-list {{ margin: 1rem 0; }}
        .role-item {{
            padding: 0.5rem 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        .role-item:last-child {{ border-bottom: none; }}
        .role-primary {{ font-weight: 600; color: #10b981; }}
        .role-secondary {{ color: #64748b; }}
        
        .explanations {{
            background: #f8fafc;
            padding: 1rem;
            border-radius: 0.375rem;
            margin: 1rem 0;
        }}
        .explanation {{ padding: 0.25rem 0; font-size: 0.875rem; }}
        
        .result-box {{
            background: #eff6ff;
            padding: 1rem;
            border-radius: 0.375rem;
            margin-top: 1rem;
        }}
        .result-label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; }}
        .result-value {{ font-weight: 500; }}
        
        .impact {{
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            font-size: 0.875rem;
            color: #64748b;
        }}
        
        .no-candidates {{
            text-align: center;
            padding: 3rem;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Role Consolidation Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-value">{len(candidates)}</div>
                <div class="summary-label">Total Candidates</div>
            </div>
            <div class="summary-card">
                <div class="summary-value" style="color: #10b981;">{merge_count}</div>
                <div class="summary-label">Recommended Merges</div>
            </div>
            <div class="summary-card">
                <div class="summary-value" style="color: #f59e0b;">{review_count}</div>
                <div class="summary-label">Requires Review</div>
            </div>
        </div>
'''
        
        if not candidates:
            html += '''
        <div class="no-candidates">
            <h2>✅ No Consolidation Candidates Found</h2>
            <p>All roles appear to be sufficiently distinct.</p>
        </div>
'''
        else:
            merges = [c for c in candidates if c.recommendation == "merge"]
            if merges:
                html += '''
        <div class="section">
            <h2 class="section-title">✅ High Confidence Merge Recommendations</h2>
'''
                for c in merges:
                    explanations_html = "".join(
                        f'<div class="explanation">{exp}</div>' 
                        for exp in c.explanations
                    )
                    aliases_html = ", ".join(f"<code>{a}</code>" for a in c.suggested_aliases[:5])
                    
                    html += f'''
            <div class="card merge">
                <div class="card-header">
                    <span class="card-title">Merge: {c.primary_role_name}</span>
                    <span class="badge badge-merge">{c.overall_similarity:.0%} Match</span>
                </div>
                
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: {c.overall_similarity*100}%"></div>
                </div>
                
                <div class="role-list">
                    <div class="role-item role-primary">✓ {c.primary_role_name} (primary)</div>
                    {"".join(f'<div class="role-item role-secondary">→ {name}</div>' for name in c.secondary_role_names)}
                </div>
                
                <div class="explanations">
                    <strong>Why merge these roles:</strong>
                    {explanations_html}
                </div>
                
                <div class="impact">
                    <span>📄 {c.documents_affected} documents affected</span>
                    <span>📋 {c.responsibilities_to_merge} responsibilities to merge</span>
                </div>
                
                <div class="result-box">
                    <div class="result-label">Suggested Result</div>
                    <div class="result-value">Canonical: <strong>{c.suggested_canonical_name}</strong></div>
                    <div style="font-size: 0.875rem; color: #64748b;">Aliases: {aliases_html}</div>
                </div>
            </div>
'''
                html += '        </div>\n'
            
            reviews = [c for c in candidates if c.recommendation == "review"]
            if reviews:
                html += '''
        <div class="section">
            <h2 class="section-title">⚠️ Requires Human Review</h2>
'''
                for c in reviews:
                    explanations_html = "".join(
                        f'<div class="explanation">{exp}</div>' 
                        for exp in c.explanations
                    )
                    
                    html += f'''
            <div class="card review">
                <div class="card-header">
                    <span class="card-title">{c.primary_role_name} ↔ {c.secondary_role_names[0]}</span>
                    <span class="badge badge-review">{c.overall_similarity:.0%} Similar</span>
                </div>
                
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: {c.overall_similarity*100}%"></div>
                </div>
                
                <div class="role-list">
                    <div class="role-item">1. {c.primary_role_name}</div>
                    {"".join(f'<div class="role-item">2. {name}</div>' for name in c.secondary_role_names)}
                </div>
                
                <div class="explanations">
                    <strong>Analysis:</strong>
                    {explanations_html}
                </div>
                
                <p style="margin-top: 1rem; color: #92400e; font-size: 0.875rem;">
                    ⚠️ Please review and determine if these represent the same role.
                </p>
            </div>
'''
                html += '        </div>\n'
        
        html += '''
    </div>
</body>
</html>'''
        
        return html
    
    def approve_consolidation(self, candidate_id: str, 
                             reviewer: str, 
                             notes: str = "") -> bool:
        """Mark a consolidation as approved."""
        for candidate in self._candidates:
            if candidate.id == candidate_id:
                candidate.status = "approved"
                candidate.reviewed_by = reviewer
                candidate.review_date = datetime.now().isoformat()
                candidate.review_notes = notes
                return True
        return False
    
    def reject_consolidation(self, candidate_id: str,
                            reviewer: str,
                            notes: str = "") -> bool:
        """Mark a consolidation as rejected."""
        for candidate in self._candidates:
            if candidate.id == candidate_id:
                candidate.status = "rejected"
                candidate.reviewed_by = reviewer
                candidate.review_date = datetime.now().isoformat()
                candidate.review_notes = notes
                return True
        return False
    
    def execute_approved_consolidations(self) -> dict:
        """
        Execute all approved consolidations.
        
        Returns summary of actions taken.
        """
        if not self.database:
            return {"error": "No database connected"}
        
        results = {
            "consolidations_executed": 0,
            "roles_merged": 0,
            "responsibilities_updated": 0,
            "errors": []
        }
        
        approved = [c for c in self._candidates if c.status == "approved"]
        
        for candidate in approved:
            try:
                # Get roles
                primary = self.database.get_role(candidate.primary_role_id)
                if not primary:
                    results["errors"].append(f"Primary role not found: {candidate.primary_role_id}")
                    continue
                
                for secondary_id in candidate.secondary_role_ids:
                    secondary = self.database.get_role(secondary_id)
                    if not secondary:
                        continue
                    
                    # Merge aliases
                    primary.aliases = list(set(
                        primary.aliases + 
                        [secondary.canonical_name] + 
                        secondary.aliases
                    ))
                    
                    # Merge responsibilities
                    primary.typical_responsibilities = list(set(
                        primary.typical_responsibilities + 
                        secondary.typical_responsibilities
                    ))[:15]
                    
                    # Merge actions
                    primary.typical_actions = list(set(
                        primary.typical_actions + 
                        secondary.typical_actions
                    ))[:10]
                    
                    # Merge document references
                    primary.source_document_ids = list(set(
                        primary.source_document_ids + 
                        secondary.source_document_ids
                    ))
                    
                    # Update usage count
                    primary.usage_count += secondary.usage_count
                    
                    # Update confidence
                    primary.confidence_avg = (primary.confidence_avg + secondary.confidence_avg) / 2
                    
                    # Update responsibilities to point to primary
                    for resp_data in self.database._data["responsibilities"].values():
                        if resp_data.get("role_id") == secondary_id:
                            resp_data["role_id"] = primary.id
                            results["responsibilities_updated"] += 1
                    
                    # Delete secondary role
                    self.database.delete_role(secondary_id)
                    results["roles_merged"] += 1
                
                # Save primary with merged data
                primary.notes += f"\n[{datetime.now().strftime('%Y-%m-%d')}] Consolidated from: {', '.join(candidate.secondary_role_names)}"
                self.database.add_role(primary)
                
                candidate.status = "completed"
                results["consolidations_executed"] += 1
                
            except Exception as e:
                results["errors"].append(f"Error processing {candidate.id}: {str(e)}")
        
        return results


# =============================================================================
# CONVENIENCE FUNCTIONS FOR INTEGRATION
# =============================================================================

def analyze_roles_for_consolidation(roles: List[StandardRole], 
                                    min_similarity: float = 0.65) -> List[ConsolidationCandidate]:
    """
    Convenience function for integration with other tools.
    
    Args:
        roles: List of StandardRole objects
        min_similarity: Minimum similarity threshold
    
    Returns:
        List of consolidation candidates
    """
    engine = RoleConsolidationEngine(roles=roles)
    return engine.find_consolidation_candidates(min_similarity)


def generate_consolidation_report(roles: List[StandardRole],
                                  format: str = "html",
                                  min_similarity: float = 0.65) -> str:
    """
    Convenience function to analyze roles and generate report.
    
    Args:
        roles: List of StandardRole objects
        format: "text", "markdown", or "html"
        min_similarity: Minimum similarity threshold
    
    Returns:
        Formatted report string
    """
    engine = RoleConsolidationEngine(roles=roles)
    candidates = engine.find_consolidation_candidates(min_similarity)
    return engine.generate_consolidation_report(candidates, format)


def check_role_similarity(role_name1: str, role_name2: str) -> dict:
    """
    Quick check if two role names might be duplicates.
    
    Returns:
        {
            "are_similar": bool,
            "overall_similarity": float,
            "breakdown": {...},
            "explanations": [...]
        }
    """
    overall, breakdown = SimilarityEngine.compute_overall_similarity(role_name1, role_name2)
    explanations = SimilarityEngine.explain_similarity(role_name1, role_name2, breakdown)
    
    return {
        "are_similar": overall >= 0.65,
        "should_merge": overall >= 0.85,
        "overall_similarity": overall,
        "breakdown": breakdown,
        "explanations": explanations
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Role Consolidation Engine')
    parser.add_argument('--database', type=str, help='Path to role database JSON')
    parser.add_argument('--report', type=str, choices=['text', 'markdown', 'html'], 
                       default='text', help='Report format')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--min-similarity', type=float, default=0.65,
                       help='Minimum similarity threshold')
    parser.add_argument('--check', nargs=2, metavar=('ROLE1', 'ROLE2'),
                       help='Quick similarity check between two role names')
    
    args = parser.parse_args()
    
    if args.check:
        result = check_role_similarity(args.check[0], args.check[1])
        print(f"\nSimilarity Check: '{args.check[0]}' vs '{args.check[1]}'")
        print("=" * 60)
        print(f"Overall Similarity: {result['overall_similarity']:.1%}")
        print(f"Should Merge: {'Yes' if result['should_merge'] else 'No'}")
        print(f"Are Similar: {'Yes' if result['are_similar'] else 'No'}")
        print("\nBreakdown:")
        for algo, score in result['breakdown'].items():
            print(f"  {algo}: {score:.1%}")
        print("\nExplanations:")
        for exp in result['explanations']:
            print(f"  {exp}")
        return
    
    if args.database:
        # Load database
        settings = StudioSettings()
        settings.database_path = args.database
        database = RoleDatabase(settings)
        
        engine = RoleConsolidationEngine(database)
        candidates = engine.find_consolidation_candidates(args.min_similarity)
        report = engine.generate_consolidation_report(candidates, args.report)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to: {args.output}")
        else:
            print(report)
    else:
        # Demo mode
        print("Role Consolidation Engine - Demo Mode")
        print("=" * 60)
        
        test_pairs = [
            ("Systems Engineer", "System Engr"),
            ("Quality Manager", "QA Manager"),
            ("Configuration Manager", "Config Mgr"),
            ("Software Engineer", "SW Engineer"),
            ("Program Manager", "Project Manager"),
            ("Test Engineer", "Verification Engineer"),
            ("Safety Engineer", "System Safety Engineer"),
        ]
        
        for role1, role2 in test_pairs:
            result = check_role_similarity(role1, role2)
            status = "✓ MERGE" if result['should_merge'] else "? REVIEW" if result['are_similar'] else "✗ DISTINCT"
            print(f"\n{status} ({result['overall_similarity']:.0%})")
            print(f"  '{role1}' vs '{role2}'")


if __name__ == "__main__":
    main()
