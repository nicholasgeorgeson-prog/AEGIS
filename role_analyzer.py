#!/usr/bin/env python3
"""
AEGIS Role Relationship Analyzer
============================================
Analyzes relationships between roles for network visualization.

Features:
- Extracts role co-occurrences
- Identifies interaction patterns
- Builds relationship graph
- Generates D3.js-compatible network data

Created by Nicholas Georgeson
"""

import re
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict
from dataclasses import dataclass, field
import json


@dataclass
class RoleNode:
    """Represents a role node in the network."""
    id: str
    label: str
    count: int = 1
    category: str = "entity"
    responsibilities: List[str] = field(default_factory=list)
    action_types: Dict[str, int] = field(default_factory=dict)
    color: str = "#4A90D9"
    size: int = 20


@dataclass 
class RoleEdge:
    """Represents an edge between roles."""
    source: str
    target: str
    relationship_type: str = "interacts_with"
    weight: float = 1.0
    context: str = ""
    bidirectional: bool = False


class RoleRelationshipAnalyzer:
    """Analyzes relationships between roles in documents."""
    
    # Relationship patterns
    RELATIONSHIP_PATTERNS = {
        'delegates_to': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?delegate[sd]?\s+(?:to\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?assign[s]?\s+(?:to\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
        'reports_to': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?report[s]?\s+to\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?submit[s]?\s+(?:to\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
        'coordinates_with': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?coordinate[s]?\s+with\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?collaborate[s]?\s+with\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?work[s]?\s+with\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
        'approves': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?approve[s]?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?authorize[s]?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
        'reviews': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?review[s]?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?evaluate[s]?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?assess(?:es)?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
        'provides_to': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?provide[s]?\s+(?:\w+\s+)?to\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?deliver[s]?\s+(?:\w+\s+)?to\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?supply(?:ies)?\s+(?:\w+\s+)?to\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
        'supports': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?support[s]?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?assist[s]?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
        'notifies': [
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?notify(?:ies)?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?inform[s]?\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
            r'(\w+(?:\s+\w+)?)\s+(?:shall\s+)?communicate[s]?\s+(?:with\s+)?(?:the\s+)?(\w+(?:\s+\w+)?)',
        ],
    }
    
    # Known organizational roles
    KNOWN_ROLES = {
        'organization', 'contractor', 'customer', 'supplier', 'vendor',
        'program manager', 'project manager', 'systems engineer', 
        'quality manager', 'quality engineer', 'test engineer',
        'design engineer', 'manufacturing engineer', 'production manager',
        'procurement', 'purchasing', 'configuration manager',
        'safety engineer', 'reliability engineer', 'logistics',
        'subcontractor', 'prime contractor', 'government',
        'user', 'operator', 'maintainer', 'inspector',
        'review board', 'material review board', 'mrb',
        'engineering', 'management', 'team', 'personnel',
    }
    
    # Role categories for coloring
    ROLE_CATEGORIES = {
        'management': ['program manager', 'project manager', 'management', 'director'],
        'engineering': ['engineer', 'engineering', 'design', 'systems'],
        'quality': ['quality', 'inspector', 'review board', 'mrb'],
        'supplier': ['supplier', 'vendor', 'subcontractor', 'contractor'],
        'customer': ['customer', 'government', 'user', 'operator'],
        'production': ['production', 'manufacturing', 'procurement'],
    }
    
    CATEGORY_COLORS = {
        'management': '#E74C3C',
        'engineering': '#3498DB', 
        'quality': '#9B59B6',
        'supplier': '#F39C12',
        'customer': '#27AE60',
        'production': '#1ABC9C',
        'entity': '#7F8C8D',
    }
    
    def __init__(self, extracted_roles: Dict = None):
        """Initialize analyzer with optional pre-extracted roles."""
        self.roles: Dict[str, RoleNode] = {}
        self.edges: List[RoleEdge] = []
        self.co_occurrences: Dict[Tuple[str, str], int] = defaultdict(int)
        
        if extracted_roles:
            self._load_extracted_roles(extracted_roles)
    
    def _load_extracted_roles(self, roles: Dict):
        """Load roles from extraction results."""
        for role_name, role_data in roles.items():
            if isinstance(role_data, dict):
                node = RoleNode(
                    id=self._normalize_role_name(role_name),
                    label=role_data.get('canonical_name', role_name),
                    count=role_data.get('count', 1),
                    responsibilities=role_data.get('responsibilities', [])[:10],
                    action_types=dict(role_data.get('action_types', {})),
                )
                node.category = self._categorize_role(node.label)
                node.color = self.CATEGORY_COLORS.get(node.category, '#7F8C8D')
                node.size = min(50, max(15, 15 + node.count * 2))
                
                self.roles[node.id] = node
    
    def _normalize_role_name(self, name: str) -> str:
        """Normalize role name for comparison."""
        return name.lower().strip().replace('_', ' ')
    
    def _categorize_role(self, role_name: str) -> str:
        """Categorize a role for coloring."""
        role_lower = role_name.lower()
        for category, keywords in self.ROLE_CATEGORIES.items():
            if any(kw in role_lower for kw in keywords):
                return category
        return 'entity'
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze text for role relationships."""
        # Find direct relationships from patterns
        for rel_type, patterns in self.RELATIONSHIP_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    source = self._normalize_role_name(match.group(1))
                    target = self._normalize_role_name(match.group(2))
                    
                    # Only consider known roles or already extracted roles
                    if self._is_valid_role(source) and self._is_valid_role(target):
                        self._add_edge(source, target, rel_type, match.group(0))
        
        # Analyze co-occurrences in sentences
        self._analyze_co_occurrences(text)
        
        return self.get_network_data()
    
    def _is_valid_role(self, role: str) -> bool:
        """Check if a string represents a valid role."""
        role_lower = role.lower()
        
        # Check if it's a known role
        if role_lower in self.KNOWN_ROLES:
            return True
        
        # Check if it matches an extracted role
        if role_lower in self.roles:
            return True
        
        # Check partial matches with known roles
        for known in self.KNOWN_ROLES:
            if known in role_lower or role_lower in known:
                return True
        
        # Check if it looks like a role (capitalized, reasonable length)
        if len(role) > 2 and len(role) < 50:
            words = role.split()
            if len(words) <= 4:
                return True
        
        return False
    
    def _add_edge(self, source: str, target: str, rel_type: str, context: str = ""):
        """Add an edge between roles."""
        # Ensure both nodes exist
        if source not in self.roles:
            self.roles[source] = RoleNode(
                id=source,
                label=source.title(),
                category=self._categorize_role(source),
                color=self.CATEGORY_COLORS.get(self._categorize_role(source), '#7F8C8D')
            )
        
        if target not in self.roles:
            self.roles[target] = RoleNode(
                id=target,
                label=target.title(),
                category=self._categorize_role(target),
                color=self.CATEGORY_COLORS.get(self._categorize_role(target), '#7F8C8D')
            )
        
        # Check if edge already exists
        existing = next(
            (e for e in self.edges if e.source == source and e.target == target),
            None
        )
        
        if existing:
            existing.weight += 1
        else:
            self.edges.append(RoleEdge(
                source=source,
                target=target,
                relationship_type=rel_type,
                context=context[:200] if context else ""
            ))
    
    def _analyze_co_occurrences(self, text: str):
        """Analyze role co-occurrences within sentences."""
        sentences = re.split(r'[.!?]+', text)
        
        role_names = set(self.roles.keys())
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            found_roles = []
            
            for role in role_names:
                if role in sentence_lower:
                    found_roles.append(role)
            
            # Record co-occurrences
            if len(found_roles) >= 2:
                for i, role1 in enumerate(found_roles):
                    for role2 in found_roles[i+1:]:
                        key = tuple(sorted([role1, role2]))
                        self.co_occurrences[key] += 1
        
        # Add co-occurrence edges for frequent pairs
        for (role1, role2), count in self.co_occurrences.items():
            if count >= 2:  # Minimum threshold
                existing = next(
                    (e for e in self.edges 
                     if (e.source == role1 and e.target == role2) or 
                        (e.source == role2 and e.target == role1)),
                    None
                )
                
                if not existing:
                    self.edges.append(RoleEdge(
                        source=role1,
                        target=role2,
                        relationship_type='co_occurs_with',
                        weight=count * 0.5,
                        bidirectional=True
                    ))
    
    def get_network_data(self) -> Dict:
        """Get network data for D3.js visualization."""
        # Prepare nodes
        nodes = []
        for role_id, role in self.roles.items():
            nodes.append({
                'id': role.id,
                'label': role.label,
                'count': role.count,
                'category': role.category,
                'color': role.color,
                'size': role.size,
                'responsibilities': role.responsibilities[:5],
                'action_types': role.action_types
            })
        
        # Prepare edges (links)
        links = []
        for edge in self.edges:
            links.append({
                'source': edge.source,
                'target': edge.target,
                'type': edge.relationship_type,
                'weight': edge.weight,
                'context': edge.context,
                'bidirectional': edge.bidirectional
            })
        
        # Calculate statistics
        stats = {
            'total_roles': len(nodes),
            'total_relationships': len(links),
            'categories': defaultdict(int),
            'relationship_types': defaultdict(int),
        }
        
        for node in nodes:
            stats['categories'][node['category']] += 1
        for link in links:
            stats['relationship_types'][link['type']] += 1
        
        stats['categories'] = dict(stats['categories'])
        stats['relationship_types'] = dict(stats['relationship_types'])
        
        return {
            'nodes': nodes,
            'links': links,
            'stats': stats
        }
    
    def get_adjacency_matrix(self) -> Dict:
        """Get adjacency matrix representation."""
        role_ids = list(self.roles.keys())
        n = len(role_ids)
        
        # Initialize matrix
        matrix = [[0] * n for _ in range(n)]
        
        # Fill matrix
        for edge in self.edges:
            if edge.source in role_ids and edge.target in role_ids:
                i = role_ids.index(edge.source)
                j = role_ids.index(edge.target)
                matrix[i][j] = edge.weight
                if edge.bidirectional:
                    matrix[j][i] = edge.weight
        
        return {
            'labels': [self.roles[rid].label for rid in role_ids],
            'matrix': matrix
        }
    
    def get_hierarchy(self) -> Dict:
        """Attempt to infer organizational hierarchy."""
        hierarchy = {
            'root': None,
            'children': {}
        }
        
        # Find potential root (most connections, reports_to target)
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        
        for edge in self.edges:
            if edge.relationship_type in ['reports_to', 'delegates_to']:
                in_degree[edge.target] += 1
                out_degree[edge.source] += 1
        
        # Root is the one with most incoming reports_to but few outgoing
        candidates = []
        for role_id in self.roles:
            score = in_degree[role_id] - out_degree[role_id]
            candidates.append((role_id, score))
        
        if candidates:
            candidates.sort(key=lambda x: -x[1])
            hierarchy['root'] = candidates[0][0]
        
        return hierarchy
    
    def to_json(self) -> str:
        """Export network data as JSON."""
        return json.dumps(self.get_network_data(), indent=2)
    
    def get_role_summary(self) -> List[Dict]:
        """Get summary of all roles with relationship counts."""
        summaries = []
        
        for role_id, role in self.roles.items():
            # Count relationships
            outgoing = sum(1 for e in self.edges if e.source == role_id)
            incoming = sum(1 for e in self.edges if e.target == role_id)
            
            summaries.append({
                'id': role_id,
                'label': role.label,
                'count': role.count,
                'category': role.category,
                'color': role.color,
                'outgoing_relationships': outgoing,
                'incoming_relationships': incoming,
                'total_relationships': outgoing + incoming,
                'responsibilities': role.responsibilities[:3],
                'top_actions': sorted(
                    role.action_types.items(), 
                    key=lambda x: -x[1]
                )[:3] if role.action_types else []
            })
        
        # Sort by total relationships
        summaries.sort(key=lambda x: -x['total_relationships'])
        
        return summaries


def analyze_document_roles(text: str, extracted_roles: Dict = None) -> Dict:
    """
    Convenience function to analyze document roles.
    
    Args:
        text: Document text
        extracted_roles: Pre-extracted roles from RoleExtractor
        
    Returns:
        Network data for visualization
    """
    analyzer = RoleRelationshipAnalyzer(extracted_roles)
    return analyzer.analyze_text(text)


def generate_role_report(text: str, extracted_roles: Dict = None) -> Dict:
    """
    Generate comprehensive role analysis report.
    
    Returns:
        Dict with network data, summaries, and statistics
    """
    analyzer = RoleRelationshipAnalyzer(extracted_roles)
    analyzer.analyze_text(text)
    
    return {
        'network': analyzer.get_network_data(),
        'summary': analyzer.get_role_summary(),
        'adjacency': analyzer.get_adjacency_matrix(),
        'hierarchy': analyzer.get_hierarchy()
    }
