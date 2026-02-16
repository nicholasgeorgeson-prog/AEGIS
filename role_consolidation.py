"""
Role Consolidation Engine for AEGIS
===============================================
ENH-001: Intelligent merging of similar roles (Engineer/Engineers, abbreviations, etc.)

This module provides enterprise-grade role consolidation capabilities including:
- Fuzzy matching for similar role names
- Automatic plural/singular normalization
- Abbreviation expansion (PM -> Project Manager)
- Confidence scoring for merge suggestions
- User-configurable consolidation rules

Version: 1.0.0
Author: AEGIS
"""

import re
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import difflib

# Structured logging support
try:
    from config_logging import get_logger
    logger = get_logger('role_consolidation')
except ImportError:
    import logging
    logger = logging.getLogger('role_consolidation')


@dataclass
class ConsolidationRule:
    """A rule for consolidating similar roles."""
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    abbreviations: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = more preferred as canonical
    is_builtin: bool = True


@dataclass
class MergeSuggestion:
    """A suggested merge between two roles."""
    role1: str
    role2: str
    confidence: float  # 0.0 to 1.0
    reason: str
    suggested_canonical: str


class RoleConsolidationEngine:
    """
    Enterprise-grade role consolidation engine.

    Features:
    - Built-in knowledge base of common engineering roles
    - Fuzzy matching for similar names (Engineer vs Engineers)
    - Abbreviation recognition (PM, SE, QA, etc.)
    - Confidence-based merge suggestions
    - Custom rule support
    """

    # Comprehensive built-in rules for engineering/defense roles
    BUILTIN_RULES = [
        # Systems Engineering
        ConsolidationRule(
            canonical_name="Systems Engineer",
            aliases=["System Engineer", "Systems Engineers", "System Engineers",
                    "Sys Engineer", "Sys Engineers", "Systems Eng", "System Eng"],
            abbreviations=["SE", "SysE", "SysEng"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Software Engineer",
            aliases=["Software Engineers", "SW Engineer", "SW Engineers",
                    "Software Eng", "Software Developer", "Developer"],
            abbreviations=["SWE", "SwEng"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Hardware Engineer",
            aliases=["Hardware Engineers", "HW Engineer", "HW Engineers",
                    "Hardware Eng", "Electrical Engineer"],
            abbreviations=["HWE", "HwEng", "EE"],
            priority=10
        ),

        # Quality & Testing
        ConsolidationRule(
            canonical_name="Quality Assurance Engineer",
            aliases=["Quality Assurance Engineers", "QA Engineer", "QA Engineers",
                    "Quality Engineer", "Quality Engineers", "Quality Assurance",
                    "Quality Analyst", "QA Analyst"],
            abbreviations=["QA", "QAE", "QE"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Test Engineer",
            aliases=["Test Engineers", "Testing Engineer", "Testing Engineers",
                    "Test Eng", "Tester", "Test Analyst"],
            abbreviations=["TE"],
            priority=9
        ),
        ConsolidationRule(
            canonical_name="Verification Engineer",
            aliases=["Verification Engineers", "V&V Engineer", "V&V Engineers",
                    "Verification", "Verifier"],
            abbreviations=["VE", "V&V"],
            priority=8
        ),
        ConsolidationRule(
            canonical_name="Validation Engineer",
            aliases=["Validation Engineers", "Validation"],
            abbreviations=["ValE"],
            priority=8
        ),

        # Management
        ConsolidationRule(
            canonical_name="Project Manager",
            aliases=["Project Managers", "Proj Manager", "Proj Managers",
                    "Project Mgr", "Project Management"],
            abbreviations=["PM", "PjM"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Program Manager",
            aliases=["Program Managers", "Prog Manager", "Prog Managers",
                    "Programme Manager", "Program Mgr", "Program Management"],
            abbreviations=["PgM", "ProgramMgr"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Technical Lead",
            aliases=["Technical Leads", "Tech Lead", "Tech Leads",
                    "Technical Leader", "Technology Lead"],
            abbreviations=["TL", "TechLead"],
            priority=9
        ),
        ConsolidationRule(
            canonical_name="Chief Engineer",
            aliases=["Chief Engineers", "Chief Eng", "CE"],
            abbreviations=["CE", "ChiefE"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Lead Engineer",
            aliases=["Lead Engineers", "Lead Eng", "Engineering Lead"],
            abbreviations=["LE"],
            priority=9
        ),

        # Specialty Engineering
        ConsolidationRule(
            canonical_name="Safety Engineer",
            aliases=["Safety Engineers", "System Safety Engineer",
                    "Systems Safety Engineer", "Safety Eng"],
            abbreviations=["SafeE", "SSE"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Reliability Engineer",
            aliases=["Reliability Engineers", "Rel Engineer", "R&M Engineer",
                    "Reliability Eng"],
            abbreviations=["RE", "RelE"],
            priority=9
        ),
        ConsolidationRule(
            canonical_name="Integration Engineer",
            aliases=["Integration Engineers", "Integrator", "Integrators",
                    "System Integrator", "Integration Eng"],
            abbreviations=["IE", "IntE"],
            priority=9
        ),
        ConsolidationRule(
            canonical_name="Requirements Engineer",
            aliases=["Requirements Engineers", "Req Engineer", "Requirements Analyst",
                    "Requirements Eng", "Reqs Engineer"],
            abbreviations=["ReqE"],
            priority=9
        ),
        ConsolidationRule(
            canonical_name="Design Engineer",
            aliases=["Design Engineers", "Designer", "Designers"],
            abbreviations=["DE"],
            priority=9
        ),

        # Configuration & Documentation
        ConsolidationRule(
            canonical_name="Configuration Manager",
            aliases=["Configuration Managers", "Configuration Management",
                    "Config Manager", "Config Mgr", "CM Manager"],
            abbreviations=["CM", "ConfigMgr"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Technical Writer",
            aliases=["Technical Writers", "Tech Writer", "Tech Writers",
                    "Documentation Specialist", "Documentation Engineer"],
            abbreviations=["TW", "TechWriter"],
            priority=9
        ),

        # Stakeholders
        ConsolidationRule(
            canonical_name="Subcontractor",
            aliases=["Subcontractors", "Sub-Contractor", "Sub-Contractors",
                    "Sub Contractor", "Subcontract", "Supplier", "Vendor"],
            abbreviations=["Sub", "Subcon"],
            priority=8
        ),
        ConsolidationRule(
            canonical_name="Contractor",
            aliases=["Contractors", "Prime Contractor", "Prime"],
            abbreviations=["Con"],
            priority=9
        ),
        ConsolidationRule(
            canonical_name="Customer",
            aliases=["Customers", "Client", "Clients", "End User", "End Users",
                    "Customer Representative"],
            abbreviations=["Cust"],
            priority=9
        ),
        ConsolidationRule(
            canonical_name="Government",
            aliases=["Government Representative", "Govt", "Government Customer",
                    "Government Rep", "Federal", "DoD", "Agency"],
            abbreviations=["Gov", "Govt"],
            priority=10
        ),
        ConsolidationRule(
            canonical_name="Stakeholder",
            aliases=["Stakeholders", "Key Stakeholder", "Project Stakeholder"],
            abbreviations=[],
            priority=7
        ),
    ]

    def __init__(self, custom_rules: List[ConsolidationRule] = None):
        """
        Initialize the consolidation engine.

        Args:
            custom_rules: Optional list of custom consolidation rules
        """
        self.rules = list(self.BUILTIN_RULES)
        if custom_rules:
            self.rules.extend(custom_rules)

        # Build lookup indexes for fast matching
        self._build_indexes()

    def _build_indexes(self):
        """Build lookup indexes for efficient matching."""
        # Canonical name lookup
        self.canonical_index: Dict[str, ConsolidationRule] = {}
        # Alias lookup (lowercase -> rule)
        self.alias_index: Dict[str, ConsolidationRule] = {}
        # Abbreviation lookup (uppercase -> rule)
        self.abbrev_index: Dict[str, ConsolidationRule] = {}

        for rule in self.rules:
            key = rule.canonical_name.lower()
            self.canonical_index[key] = rule

            for alias in rule.aliases:
                self.alias_index[alias.lower()] = rule

            for abbrev in rule.abbreviations:
                self.abbrev_index[abbrev.upper()] = rule

    def normalize_role(self, role_name: str) -> str:
        """
        Normalize a role name for comparison.
        Handles capitalization, extra spaces, common variations.
        """
        if not role_name:
            return ""

        # Clean and normalize
        normalized = re.sub(r'\s+', ' ', role_name.strip())

        # Title case
        normalized = normalized.title()

        # Fix common patterns
        normalized = re.sub(r"'S\b", "'s", normalized)  # Possessive
        normalized = re.sub(r'\bAnd\b', 'and', normalized)
        normalized = re.sub(r'\bOf\b', 'of', normalized)
        normalized = re.sub(r'\bThe\b', 'the', normalized)

        return normalized

    def get_canonical(self, role_name: str) -> Tuple[str, float]:
        """
        Get the canonical name for a role with confidence score.

        Args:
            role_name: The role name to look up

        Returns:
            Tuple of (canonical_name, confidence)
            Confidence: 1.0 = exact match, 0.0-0.99 = fuzzy match
        """
        if not role_name:
            return role_name, 0.0

        normalized = self.normalize_role(role_name)
        normalized_lower = normalized.lower()

        # Check for exact canonical match
        if normalized_lower in self.canonical_index:
            rule = self.canonical_index[normalized_lower]
            return rule.canonical_name, 1.0

        # Check for alias match
        if normalized_lower in self.alias_index:
            rule = self.alias_index[normalized_lower]
            return rule.canonical_name, 0.95

        # Check for abbreviation match (case sensitive)
        upper = role_name.strip().upper()
        if upper in self.abbrev_index:
            rule = self.abbrev_index[upper]
            return rule.canonical_name, 0.9

        # Fuzzy matching for near matches
        best_match = None
        best_score = 0.0

        for rule in self.rules:
            # Compare with canonical
            score = self._similarity_score(normalized_lower, rule.canonical_name.lower())
            if score > best_score and score >= 0.85:
                best_score = score
                best_match = rule.canonical_name

            # Compare with aliases
            for alias in rule.aliases:
                score = self._similarity_score(normalized_lower, alias.lower())
                if score > best_score and score >= 0.85:
                    best_score = score
                    best_match = rule.canonical_name

        if best_match:
            return best_match, best_score

        # No match found - return original normalized
        return normalized, 0.0

    def _similarity_score(self, s1: str, s2: str) -> float:
        """
        Calculate similarity score between two strings.
        Uses multiple techniques for robust matching.
        """
        # Exact match
        if s1 == s2:
            return 1.0

        # Handle plural/singular
        if self._is_plural_variant(s1, s2):
            return 0.95

        # Use sequence matcher for fuzzy matching
        ratio = difflib.SequenceMatcher(None, s1, s2).ratio()

        # Bonus for word overlap
        words1 = set(s1.split())
        words2 = set(s2.split())
        overlap = len(words1 & words2) / max(len(words1), len(words2), 1)

        # Weighted combination
        return (ratio * 0.7) + (overlap * 0.3)

    def _is_plural_variant(self, s1: str, s2: str) -> bool:
        """Check if two strings are singular/plural variants."""
        # Common patterns
        patterns = [
            (r's$', ''),           # Engineers -> Engineer
            (r'es$', ''),          # Processes -> Process
            (r'ies$', 'y'),        # Responsibilities -> Responsibility
            (r'ers$', 'er'),       # Engineers -> Engineer (more specific)
        ]

        for pattern, replacement in patterns:
            s1_base = re.sub(pattern, replacement, s1)
            s2_base = re.sub(pattern, replacement, s2)
            if s1_base == s2_base:
                return True
            if s1_base == s2 or s1 == s2_base:
                return True

        return False

    def consolidate_roles(
        self,
        roles: Dict[str, Any],
        min_confidence: float = 0.85
    ) -> Dict[str, Any]:
        """
        Consolidate a dictionary of roles, merging similar ones.

        Args:
            roles: Dict mapping role names to role data (any structure)
            min_confidence: Minimum confidence for automatic merging

        Returns:
            New dict with consolidated roles
        """
        consolidated: Dict[str, Any] = {}
        merge_map: Dict[str, str] = {}  # original -> canonical

        for role_name, role_data in roles.items():
            canonical, confidence = self.get_canonical(role_name)

            if confidence >= min_confidence:
                merge_map[role_name] = canonical

                if canonical in consolidated:
                    # Merge data
                    consolidated[canonical] = self._merge_role_data(
                        consolidated[canonical], role_data
                    )
                else:
                    consolidated[canonical] = role_data
            else:
                # No confident match - keep original
                if role_name not in consolidated:
                    consolidated[role_name] = role_data

        logger.info(f"Consolidated {len(roles)} roles into {len(consolidated)} "
                   f"({len(roles) - len(consolidated)} merged)")

        return consolidated

    def _merge_role_data(self, existing: Any, new: Any) -> Any:
        """
        Merge two role data objects intelligently.
        Handles common patterns like ExtractedRole dataclass.
        """
        # If they're both dicts, merge them
        if isinstance(existing, dict) and isinstance(new, dict):
            merged = dict(existing)
            for key, value in new.items():
                if key in merged:
                    # Merge lists
                    if isinstance(merged[key], list) and isinstance(value, list):
                        merged[key] = list(set(merged[key]) | set(value))
                    # Merge sets
                    elif isinstance(merged[key], set) and isinstance(value, set):
                        merged[key] = merged[key] | value
                    # Add counts
                    elif isinstance(merged[key], int) and isinstance(value, int):
                        merged[key] = merged[key] + value
                else:
                    merged[key] = value
            return merged

        # If they have merge() method (like ExtractedRole)
        if hasattr(existing, 'merge'):
            existing.merge(new)
            return existing

        # If they have occurrences attribute
        if hasattr(existing, 'occurrences') and hasattr(new, 'occurrences'):
            existing.occurrences.extend(new.occurrences)
            if hasattr(existing, 'count'):
                existing.count += new.count if hasattr(new, 'count') else 1
            return existing

        # Default: return existing
        return existing

    def get_merge_suggestions(
        self,
        roles: List[str],
        min_confidence: float = 0.7
    ) -> List[MergeSuggestion]:
        """
        Get suggestions for roles that might need merging.

        Args:
            roles: List of role names
            min_confidence: Minimum similarity for suggestions

        Returns:
            List of MergeSuggestion objects
        """
        suggestions = []
        seen_pairs = set()

        for i, role1 in enumerate(roles):
            for role2 in roles[i+1:]:
                # Skip if already checked
                pair = tuple(sorted([role1, role2]))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)

                # Check similarity
                score = self._similarity_score(role1.lower(), role2.lower())

                if score >= min_confidence:
                    # Determine which should be canonical
                    canonical1, conf1 = self.get_canonical(role1)
                    canonical2, conf2 = self.get_canonical(role2)

                    if conf1 >= conf2:
                        suggested = canonical1
                        reason = f"'{role2}' appears to be variant of '{canonical1}'"
                    else:
                        suggested = canonical2
                        reason = f"'{role1}' appears to be variant of '{canonical2}'"

                    suggestions.append(MergeSuggestion(
                        role1=role1,
                        role2=role2,
                        confidence=score,
                        reason=reason,
                        suggested_canonical=suggested
                    ))

        # Sort by confidence descending
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        return suggestions

    def add_custom_rule(self, rule: ConsolidationRule):
        """Add a custom consolidation rule."""
        self.rules.append(rule)
        self._build_indexes()

    def export_rules(self) -> List[Dict]:
        """Export current rules as list of dicts for serialization."""
        return [
            {
                'canonical_name': r.canonical_name,
                'aliases': r.aliases,
                'abbreviations': r.abbreviations,
                'priority': r.priority,
                'is_builtin': r.is_builtin
            }
            for r in self.rules
        ]

    def import_rules(self, rules_data: List[Dict]):
        """Import rules from list of dicts."""
        for data in rules_data:
            if not data.get('is_builtin', True):
                rule = ConsolidationRule(
                    canonical_name=data['canonical_name'],
                    aliases=data.get('aliases', []),
                    abbreviations=data.get('abbreviations', []),
                    priority=data.get('priority', 0),
                    is_builtin=False
                )
                self.rules.append(rule)
        self._build_indexes()


# Singleton instance for easy access
_engine_instance = None

def get_consolidation_engine() -> RoleConsolidationEngine:
    """Get the global consolidation engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RoleConsolidationEngine()
    return _engine_instance


def consolidate_roles(roles: Dict[str, Any], min_confidence: float = 0.85) -> Dict[str, Any]:
    """Convenience function to consolidate roles using the global engine."""
    return get_consolidation_engine().consolidate_roles(roles, min_confidence)


def get_canonical_role(role_name: str) -> Tuple[str, float]:
    """Convenience function to get canonical role name."""
    return get_consolidation_engine().get_canonical(role_name)
