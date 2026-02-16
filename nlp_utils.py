"""
NLP Utilities for AEGIS
===================================
Version: 1.1.0
Date: 2026-02-03

Enhancement ENH-008: Integrate NLP models (spaCy) to improve:
- Role extraction accuracy
- Deliverables identification
- Acronym detection
- Grammar/style checking

v1.1.0 (2026-02-03):
- Enhanced spaCy POS tagging for role pattern detection
- Improved noun phrase extraction using spaCy's noun_chunks
- Added compound noun detection for multi-word roles
- Better passive voice subject detection for roles
- Enhanced context window using sentence boundaries
- Added role verb associations (approve, review, coordinate, etc.)
- Improved filtering with spaCy entity types

This module provides NLP-powered analysis using spaCy for:
- Named Entity Recognition (NER)
- Dependency parsing for role-action relationships
- Noun phrase extraction for deliverables
- Better sentence boundary detection

Usage:
    from nlp_utils import NLPProcessor
    processor = NLPProcessor()
    roles = processor.extract_roles(text)
    deliverables = processor.extract_deliverables(text)
"""

import re
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict

# Structured logging support
try:
    from config_logging import get_logger
    _logger = get_logger('nlp_utils')
except ImportError:
    _logger = None

def _log(message: str, level: str = 'info', **kwargs):
    """Internal logging helper with fallback."""
    if _logger:
        getattr(_logger, level)(message, **kwargs)
    elif level in ('warning', 'error', 'critical'):
        print(f"[NLPUtils] {level.upper()}: {message}")


# Try to import spaCy - it's optional
_spacy_available = False
_nlp = None

try:
    import spacy
    _spacy_available = True
    _log("spaCy import successful", level='debug')
except ImportError:
    _log("spaCy not available - NLP features disabled", level='warning')


@dataclass
class NLPRole:
    """Role extracted using NLP analysis."""
    name: str
    normalized_name: str
    confidence: float
    source: str  # 'ner', 'dependency', 'pattern', 'shall_statement'
    context: str
    start_char: int
    end_char: int
    modifiers: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'normalized_name': self.normalized_name,
            'confidence': self.confidence,
            'source': self.source,
            'context': self.context,
            'start_char': self.start_char,
            'end_char': self.end_char,
            'modifiers': self.modifiers
        }


@dataclass
class NLPDeliverable:
    """Deliverable extracted using NLP analysis."""
    name: str
    normalized_name: str
    confidence: float
    source: str  # 'noun_phrase', 'pattern', 'shall_statement'
    context: str
    deliverable_type: str  # 'document', 'artifact', 'report', 'plan', etc.

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'normalized_name': self.normalized_name,
            'confidence': self.confidence,
            'source': self.source,
            'context': self.context,
            'deliverable_type': self.deliverable_type
        }


@dataclass
class NLPAcronym:
    """Acronym detected using NLP analysis."""
    acronym: str
    expansion: Optional[str]
    confidence: float
    is_defined: bool
    definition_location: Optional[int]  # Character offset of definition
    usage_locations: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'acronym': self.acronym,
            'expansion': self.expansion,
            'confidence': self.confidence,
            'is_defined': self.is_defined,
            'definition_location': self.definition_location,
            'usage_count': len(self.usage_locations)
        }


class NLPProcessor:
    """
    NLP-powered text analysis for technical documents.
    Uses spaCy for advanced linguistic analysis when available,
    falls back to pattern matching otherwise.

    v1.1.0: Enhanced spaCy integration for better role detection:
    - Uses POS tagging to validate role candidates
    - Leverages dependency parsing for role-action relationships
    - Better noun phrase extraction using spaCy's noun_chunks
    - Filters using entity types and compound nouns
    """

    VERSION = '1.1.0'

    # Role-related patterns - expanded for aerospace/defense
    ROLE_SUFFIXES = {
        'engineer', 'manager', 'lead', 'director', 'officer', 'specialist',
        'analyst', 'coordinator', 'administrator', 'authority', 'chief',
        'supervisor', 'inspector', 'auditor', 'reviewer', 'approver',
        'representative', 'owner', 'custodian', 'architect', 'integrator',
        'technician', 'scientist', 'investigator', 'controller', 'planner',
        # v1.1.0: Additional aerospace/defense roles
        'contractor', 'subcontractor', 'vendor', 'supplier', 'customer',
        'sponsor', 'stakeholder', 'user', 'operator', 'maintainer',
        'assembler', 'fabricator', 'developer', 'designer', 'tester',
        'verifier', 'validator', 'certifier', 'assessor', 'evaluator',
        'liaison', 'delegate', 'agent', 'monitor', 'watchdog'
    }

    ROLE_MODIFIERS = {
        'project', 'program', 'systems', 'system', 'lead', 'chief', 'senior',
        'deputy', 'assistant', 'associate', 'principal', 'technical', 'quality',
        'safety', 'mission', 'flight', 'ground', 'test', 'integration',
        'software', 'hardware', 'mechanical', 'electrical', 'structural',
        'configuration', 'data', 'risk', 'requirements', 'interface',
        # v1.1.0: Additional modifiers for aerospace/defense
        'acquisition', 'logistics', 'supply', 'operations', 'maintenance',
        'production', 'manufacturing', 'design', 'development', 'research',
        'security', 'compliance', 'regulatory', 'contract', 'procurement',
        'sustainment', 'training', 'support', 'field', 'depot',
        'prime', 'sub', 'government', 'military', 'civilian'
    }

    # v1.1.0: Verbs that typically precede or follow role references
    ROLE_ACTION_VERBS = {
        'approve', 'review', 'coordinate', 'manage', 'supervise', 'oversee',
        'authorize', 'certify', 'validate', 'verify', 'inspect', 'audit',
        'assess', 'evaluate', 'monitor', 'control', 'direct', 'administer',
        'assign', 'delegate', 'designate', 'appoint', 'notify', 'inform',
        'consult', 'advise', 'support', 'assist', 'facilitate', 'enable'
    }

    # v1.1.0: Organizational unit indicators
    ORG_INDICATORS = {
        'team', 'group', 'board', 'committee', 'panel', 'council',
        'personnel', 'staff', 'department', 'office', 'division',
        'branch', 'section', 'unit', 'organization', 'agency',
        'directorate', 'center', 'lab', 'laboratory', 'facility'
    }

    # Deliverable-related patterns
    DELIVERABLE_TYPES = {
        'document': ['document', 'doc', 'documentation', 'manual', 'guide', 'handbook'],
        'report': ['report', 'summary', 'assessment', 'analysis', 'review', 'audit'],
        'plan': ['plan', 'schedule', 'roadmap', 'strategy', 'approach'],
        'specification': ['specification', 'spec', 'requirement', 'standard', 'baseline'],
        'design': ['design', 'architecture', 'drawing', 'schematic', 'diagram'],
        'procedure': ['procedure', 'process', 'instruction', 'protocol', 'method'],
        'artifact': ['artifact', 'deliverable', 'product', 'output', 'work product'],
        'list': ['list', 'inventory', 'catalog', 'register', 'log', 'matrix'],
        'data': ['data', 'dataset', 'package', 'file', 'database']
    }

    # Shall statement patterns for requirements
    SHALL_PATTERNS = [
        r'\b(?:shall|will|must)\s+(?:be\s+)?(?:responsible\s+(?:for|to)|provide|deliver|submit|prepare|develop|create|maintain|ensure|verify|validate|review|approve|coordinate|support)',
        r'\b(?:is|are)\s+responsible\s+(?:for|to)',
        r'\brequired\s+to\b',
        r'\bresponsibility\s+(?:of|for|to)\b'
    ]

    def __init__(self, model_name: str = 'en_core_web_md', load_model: bool = True):
        """
        Initialize the NLP processor.

        Args:
            model_name: spaCy model to load (default: en_core_web_md)
            load_model: Whether to load the spaCy model immediately
        """
        global _nlp

        self.model_name = model_name
        self.nlp = None
        self.is_nlp_available = False

        if load_model and _spacy_available:
            self._load_model()

    def _load_model(self) -> bool:
        """Load the spaCy model."""
        global _nlp

        if not _spacy_available:
            _log("spaCy not installed - using pattern matching only", level='warning')
            return False

        # Use cached model if already loaded
        if _nlp is not None:
            self.nlp = _nlp
            self.is_nlp_available = True
            _log("Using cached spaCy model", level='debug')
            return True

        try:
            _log(f"Loading spaCy model: {self.model_name}", level='info')
            self.nlp = spacy.load(self.model_name)
            _nlp = self.nlp  # Cache globally
            self.is_nlp_available = True
            _log(f"spaCy model loaded successfully: {self.nlp.meta['name']}", level='info')
            return True
        except OSError as e:
            _log(f"Could not load spaCy model '{self.model_name}': {e}", level='warning')
            # Try smaller model as fallback
            try:
                _log("Trying fallback model: en_core_web_sm", level='info')
                self.nlp = spacy.load('en_core_web_sm')
                _nlp = self.nlp
                self.is_nlp_available = True
                _log("Fallback model loaded successfully", level='info')
                return True
            except OSError:
                _log("No spaCy models available - using pattern matching only", level='warning')
                return False
        except Exception as e:
            _log(f"Error loading spaCy: {e}", level='error')
            return False

    def process_text(self, text: str) -> Optional[Any]:
        """
        Process text with spaCy if available.

        Args:
            text: Text to process

        Returns:
            spaCy Doc object or None if NLP not available
        """
        if not self.is_nlp_available or self.nlp is None:
            return None

        # Limit text length for performance
        max_length = 100000
        if len(text) > max_length:
            _log(f"Text truncated from {len(text)} to {max_length} chars", level='debug')
            text = text[:max_length]

        try:
            return self.nlp(text)
        except Exception as e:
            _log(f"Error processing text: {e}", level='error')
            return None

    def extract_roles(self, text: str) -> List[NLPRole]:
        """
        Extract roles from text using NLP and pattern matching.

        Args:
            text: Document text to analyze

        Returns:
            List of NLPRole objects
        """
        roles = []

        # Try NLP-based extraction first
        if self.is_nlp_available:
            roles.extend(self._extract_roles_nlp(text))

        # Add pattern-based extraction
        roles.extend(self._extract_roles_patterns(text))

        # Deduplicate and merge
        return self._deduplicate_roles(roles)

    def _extract_roles_nlp(self, text: str) -> List[NLPRole]:
        """
        Extract roles using spaCy NER and dependency parsing.

        v1.1.0: Enhanced with:
        - Better noun chunk analysis
        - Compound noun detection
        - Passive voice subject extraction
        - Role-verb association detection
        - Improved confidence scoring based on POS tags
        """
        roles = []
        doc = self.process_text(text)

        if doc is None:
            return roles

        # Track what we've already found to avoid duplicates
        seen_spans = set()

        # 1. NER-based extraction (PERSON, ORG entities that look like roles)
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG', 'NORP']:
                # v1.1.1: Skip excessively long entities
                if len(ent.text) > 60:
                    continue
                # Check if it looks like a role (not a named person)
                ent_lower = ent.text.lower()
                if self._is_role_pattern_nlp(ent, doc):
                    span_key = (ent.start_char, ent.end_char)
                    if span_key not in seen_spans:
                        seen_spans.add(span_key)
                        roles.append(NLPRole(
                            name=ent.text,
                            normalized_name=self._normalize_role(ent.text),
                            confidence=0.8,
                            source='ner',
                            context=self._get_sentence_context(doc, ent.start_char, ent.end_char),
                            start_char=ent.start_char,
                            end_char=ent.end_char
                        ))

        # 2. v1.1.0: Noun chunk analysis - check all noun phrases
        for chunk in doc.noun_chunks:
            chunk_lower = chunk.text.lower().strip()
            # Skip very short or very long chunks
            if len(chunk_lower) < 4 or len(chunk_lower) > 60:
                continue

            # Check if this noun chunk looks like a role
            if self._is_role_pattern_nlp(chunk, doc):
                span_key = (chunk.start_char, chunk.end_char)
                if span_key not in seen_spans:
                    seen_spans.add(span_key)
                    # Calculate confidence based on POS tags
                    confidence = self._calculate_role_confidence(chunk, doc)
                    if confidence >= 0.5:
                        roles.append(NLPRole(
                            name=chunk.text,
                            normalized_name=self._normalize_role(chunk.text),
                            confidence=confidence,
                            source='noun_chunk',
                            context=self._get_sentence_context(doc, chunk.start_char, chunk.end_char),
                            start_char=chunk.start_char,
                            end_char=chunk.end_char,
                            modifiers=self._extract_modifiers(chunk)
                        ))

        # 3. Dependency-based extraction (subjects of "shall" statements)
        for token in doc:
            # Find subjects of shall/will/must verbs
            if token.dep_ in ['nsubj', 'nsubjpass'] and token.head.lemma_ in ['shall', 'will', 'must', 'be']:
                # Get the full noun phrase
                np = self._get_noun_phrase(token)
                if np and self._is_role_pattern(np.lower()):
                    # Find start/end char positions
                    start_char = token.idx
                    end_char = token.idx + len(token.text)
                    for child in token.subtree:
                        start_char = min(start_char, child.idx)
                        end_char = max(end_char, child.idx + len(child.text))

                    span_key = (start_char, end_char)
                    if span_key not in seen_spans:
                        seen_spans.add(span_key)
                        roles.append(NLPRole(
                            name=np,
                            normalized_name=self._normalize_role(np),
                            confidence=0.85,
                            source='dependency',
                            context=self._get_sentence_context(doc, start_char, end_char),
                            start_char=start_char,
                            end_char=end_char
                        ))

            # v1.1.0: Find roles that are objects of role-action verbs
            if token.lemma_ in self.ROLE_ACTION_VERBS:
                for child in token.children:
                    if child.dep_ in ['dobj', 'pobj', 'nsubj', 'agent']:
                        np = self._get_noun_phrase(child)
                        if np and self._is_role_pattern(np.lower()):
                            start_char = child.idx
                            end_char = child.idx + len(child.text)
                            for c in child.subtree:
                                start_char = min(start_char, c.idx)
                                end_char = max(end_char, c.idx + len(c.text))

                            span_key = (start_char, end_char)
                            if span_key not in seen_spans:
                                seen_spans.add(span_key)
                                roles.append(NLPRole(
                                    name=np,
                                    normalized_name=self._normalize_role(np),
                                    confidence=0.8,
                                    source='verb_association',
                                    context=self._get_sentence_context(doc, start_char, end_char),
                                    start_char=start_char,
                                    end_char=end_char
                                ))

            # Find roles in "responsible for" patterns
            if token.lemma_ == 'responsible' and token.head.dep_ in ['nsubj', 'attr', 'ROOT', 'acomp']:
                subj = None
                # Check direct children first
                for child in token.head.children:
                    if child.dep_ == 'nsubj':
                        subj = child
                        break
                # If not found, check parent's children
                if not subj and token.head.head:
                    for child in token.head.head.children:
                        if child.dep_ == 'nsubj':
                            subj = child
                            break

                if subj:
                    np = self._get_noun_phrase(subj)
                    if np and self._is_role_pattern(np.lower()):
                        start_char = subj.idx
                        end_char = subj.idx + len(subj.text)
                        for c in subj.subtree:
                            start_char = min(start_char, c.idx)
                            end_char = max(end_char, c.idx + len(c.text))

                        span_key = (start_char, end_char)
                        if span_key not in seen_spans:
                            seen_spans.add(span_key)
                            roles.append(NLPRole(
                                name=np,
                                normalized_name=self._normalize_role(np),
                                confidence=0.9,
                                source='responsibility',
                                context=self._get_sentence_context(doc, start_char, end_char),
                                start_char=start_char,
                                end_char=end_char
                            ))

        # 4. v1.1.0: Check for passive voice subjects (often roles)
        for token in doc:
            if token.dep_ == 'nsubjpass':
                np = self._get_noun_phrase(token)
                if np and self._is_role_pattern(np.lower()):
                    start_char = token.idx
                    end_char = token.idx + len(token.text)
                    for c in token.subtree:
                        start_char = min(start_char, c.idx)
                        end_char = max(end_char, c.idx + len(c.text))

                    span_key = (start_char, end_char)
                    if span_key not in seen_spans:
                        seen_spans.add(span_key)
                        roles.append(NLPRole(
                            name=np,
                            normalized_name=self._normalize_role(np),
                            confidence=0.75,
                            source='passive_subject',
                            context=self._get_sentence_context(doc, start_char, end_char),
                            start_char=start_char,
                            end_char=end_char
                        ))

        return roles

    def _is_role_pattern_nlp(self, span, doc) -> bool:
        """
        v1.1.0: Check if a spaCy span matches role patterns using linguistic analysis.
        v1.1.1: Added length validation.

        Uses POS tagging and token analysis for more accurate detection.
        """
        text = span.text.strip()
        text_lower = text.lower()

        # v1.1.1: Reject excessively long candidates (>60 chars)
        if len(text) > 60:
            return False

        # Quick check with existing pattern method
        if self._is_role_pattern(text_lower):
            return True

        # v1.1.0: Check using spaCy token analysis
        tokens = list(span) if hasattr(span, '__iter__') else [span]

        # Look for proper nouns followed by common nouns (typical role pattern)
        has_proper_noun = any(t.pos_ == 'PROPN' for t in tokens)
        has_noun = any(t.pos_ in ['NOUN', 'PROPN'] for t in tokens)

        if has_noun:
            # Check if last token (head of noun phrase) ends with role suffix
            last_token = tokens[-1] if tokens else None
            if last_token:
                lemma = last_token.lemma_.lower()
                if lemma in self.ROLE_SUFFIXES or lemma.rstrip('s') in self.ROLE_SUFFIXES:
                    return True

                # Check for org indicators
                if lemma in self.ORG_INDICATORS or lemma.rstrip('s') in self.ORG_INDICATORS:
                    return True

        return False

    def _calculate_role_confidence(self, span, doc) -> float:
        """
        v1.1.0: Calculate confidence score for a potential role based on linguistic features.

        Factors:
        - POS tag patterns (higher for PROPN + NOUN combinations)
        - Presence of role suffixes
        - Position in sentence (subjects score higher)
        - Association with role-related verbs
        """
        confidence = 0.5  # Base confidence
        tokens = list(span) if hasattr(span, '__iter__') else [span]

        if not tokens:
            return 0.0

        # Check for role suffixes (+0.2)
        last_lemma = tokens[-1].lemma_.lower()
        if last_lemma in self.ROLE_SUFFIXES or last_lemma.rstrip('s') in self.ROLE_SUFFIXES:
            confidence += 0.2

        # Check for role modifiers (+0.1)
        for t in tokens[:-1]:  # All but last
            if t.lemma_.lower() in self.ROLE_MODIFIERS:
                confidence += 0.1
                break  # Only count once

        # Check POS pattern (+0.1 for PROPN, +0.05 for NOUN)
        if any(t.pos_ == 'PROPN' for t in tokens):
            confidence += 0.1
        elif any(t.pos_ == 'NOUN' for t in tokens):
            confidence += 0.05

        # Check if it's a subject (+0.1)
        root = span.root if hasattr(span, 'root') else tokens[0]
        if root.dep_ in ['nsubj', 'nsubjpass']:
            confidence += 0.1

        # Check if associated with role-action verb (+0.1)
        if root.head and root.head.lemma_ in self.ROLE_ACTION_VERBS:
            confidence += 0.1

        # Penalize if it looks like a named person (-0.2)
        # (e.g., "John Smith" vs "Project Manager")
        if len(tokens) == 2 and all(t.pos_ == 'PROPN' for t in tokens):
            # Likely a person name
            if not any(t.lemma_.lower() in self.ROLE_SUFFIXES for t in tokens):
                confidence -= 0.2

        return min(0.95, max(0.0, confidence))

    def _extract_modifiers(self, span) -> List[str]:
        """v1.1.0: Extract modifier words from a role span."""
        modifiers = []
        tokens = list(span) if hasattr(span, '__iter__') else [span]

        for t in tokens[:-1]:  # All but the head noun
            if t.dep_ in ['amod', 'compound', 'nmod'] or t.pos_ == 'ADJ':
                modifiers.append(t.text)
            elif t.lemma_.lower() in self.ROLE_MODIFIERS:
                modifiers.append(t.text)

        return modifiers

    def _get_sentence_context(self, doc, start_char: int, end_char: int) -> str:
        """
        v1.1.0: Get context using sentence boundaries for cleaner excerpts.

        Uses spaCy's sentence segmentation when available.
        """
        # Find the sentence containing the span
        for sent in doc.sents:
            if sent.start_char <= start_char and sent.end_char >= end_char:
                return sent.text.strip()

        # Fallback to window-based context
        return self._get_context(doc.text, start_char, end_char)

    def _extract_roles_patterns(self, text: str) -> List[NLPRole]:
        """Extract roles using regex pattern matching."""
        roles = []

        # Pattern 1: [Modifier] + Role Suffix
        modifier_pattern = '|'.join(re.escape(m) for m in self.ROLE_MODIFIERS)
        suffix_pattern = '|'.join(re.escape(s) for s in self.ROLE_SUFFIXES)

        role_pattern = rf'\b((?:(?:{modifier_pattern})\s+)*(?:{suffix_pattern})(?:s)?)\b'

        for match in re.finditer(role_pattern, text, re.IGNORECASE):
            role_text = match.group(1)
            # v1.1.1: Added max length check (60 chars)
            if len(role_text) > 3 and len(role_text) <= 60:
                roles.append(NLPRole(
                    name=role_text,
                    normalized_name=self._normalize_role(role_text),
                    confidence=0.7,
                    source='pattern',
                    context=self._get_context(text, match.start(), match.end()),
                    start_char=match.start(),
                    end_char=match.end()
                ))

        # Pattern 2: Shall statement subjects
        for pattern in self.SHALL_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Look backwards for the subject
                before_text = text[max(0, match.start() - 100):match.start()]
                # Find the last capitalized phrase
                subj_match = re.search(r'(?:The\s+)?([A-Z][a-zA-Z\s]+?)(?:\s+shall|\s+will|\s+must|\s+is|\s+are)\s*$', before_text)
                if subj_match:
                    role_text = subj_match.group(1).strip()
                    # v1.1.1: Added max length check (60 chars)
                    if len(role_text) <= 60 and self._is_role_pattern(role_text.lower()):
                        start = match.start() - len(before_text) + subj_match.start()
                        roles.append(NLPRole(
                            name=role_text,
                            normalized_name=self._normalize_role(role_text),
                            confidence=0.75,
                            source='shall_statement',
                            context=self._get_context(text, start, match.end()),
                            start_char=start,
                            end_char=match.end()
                        ))

        return roles

    def _is_role_pattern(self, text: str) -> bool:
        """
        Check if text matches role patterns.

        v1.1.0: Enhanced to check more indicators and handle plurals better.
        v1.1.1: Added phone number and numeric filtering.
        """
        text_lower = text.lower().strip()

        # Skip very short text
        if len(text_lower) < 3:
            return False

        # v1.1.1: Filter out phone numbers and numeric patterns
        # Skip if starts with digit
        if text and text[0].isdigit():
            return False

        # Skip if contains phone patterns (###-####, (###), etc.)
        if re.search(r'\d{3}[-.\s]?\d{4}', text):
            return False
        if re.search(r'\(\d{3}\)', text):
            return False

        # Skip if high numeric content (>30%)
        digit_count = sum(1 for c in text if c.isdigit())
        if len(text) > 0 and digit_count / len(text) > 0.3:
            return False

        # Skip if contains ZIP code pattern
        if re.search(r'\b\d{5}(?:-\d{4})?\b', text):
            return False

        # v1.1.2: Skip run-together words (PDF extraction artifacts)
        if len(text) > 10 and ' ' not in text:
            # Check for camelCase or run-together patterns
            if re.search(r'[a-z][A-Z]', text):
                return False
            # Check for common run-together prefixes
            run_together_prefixes = ['bythe', 'bya', 'tothe', 'forthe', 'ofthe',
                                     'thepersonnel', 'thedifference', 'theaccountable']
            if any(text_lower.startswith(p) for p in run_together_prefixes):
                return False

        # v1.1.2: Skip section headers
        if re.match(r'^[A-Z0-9]+\.\s', text):
            return False

        # v1.1.2: Skip "Other X" patterns
        if text_lower.startswith('other '):
            return False

        # Check for role suffixes
        words = text_lower.split()
        if words:
            last_word = words[-1].rstrip('s')  # Remove plural
            if last_word in self.ROLE_SUFFIXES or last_word + 's' in self.ROLE_SUFFIXES:
                return True

            # v1.1.0: Also check second-to-last word for compound roles
            # e.g., "Program Manager Office" -> check "Manager"
            if len(words) >= 2:
                second_last = words[-2].rstrip('s')
                if second_last in self.ROLE_SUFFIXES:
                    return True

        # v1.1.0: Check for org unit indicators (use the class attribute)
        for indicator in self.ORG_INDICATORS:
            if indicator in text_lower:
                return True

        # v1.1.0: Check for role modifiers + generic role terms
        for modifier in self.ROLE_MODIFIERS:
            if modifier in text_lower:
                # If it has a modifier and looks like an org phrase, it's likely a role
                if any(word in text_lower for word in ['authority', 'function', 'activity', 'element']):
                    return True

        return False

    def _normalize_role(self, role: str) -> str:
        """Normalize a role name for comparison."""
        # v1.1.1: Strip inline acronyms like "(PM)" from role names
        normalized = re.sub(r'\s*\([A-Z][A-Z&/]{1,7}\)\s*', ' ', role).strip()

        # Convert to title case
        normalized = normalized.strip().title()

        # Handle common variations
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        normalized = re.sub(r"'S\b", "'s", normalized)  # Fix possessives

        return normalized

    def _get_noun_phrase(self, token) -> Optional[str]:
        """Get the full noun phrase for a token."""
        if token is None:
            return None

        # Collect all tokens in the subtree
        tokens = sorted(list(token.subtree), key=lambda t: t.i)

        # Filter to get the noun phrase
        np_tokens = []
        for t in tokens:
            if t.dep_ in ['compound', 'amod', 'det', 'nsubj', 'nmod', 'poss'] or t == token:
                np_tokens.append(t)

        if not np_tokens:
            return token.text

        # Sort by position and join
        np_tokens.sort(key=lambda t: t.i)

        # Build the phrase, handling whitespace
        phrase_parts = []
        for i, t in enumerate(np_tokens):
            if i > 0 and np_tokens[i-1].i + 1 == t.i:
                phrase_parts.append(t.text)
            elif i > 0:
                phrase_parts.append(' ' + t.text)
            else:
                phrase_parts.append(t.text)

        return ''.join(phrase_parts)

    def _get_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Get context around a match."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)

        context = text[ctx_start:ctx_end]

        # Clean up context
        if ctx_start > 0:
            context = '...' + context
        if ctx_end < len(text):
            context = context + '...'

        return context.replace('\n', ' ').strip()

    def _deduplicate_roles(self, roles: List[NLPRole]) -> List[NLPRole]:
        """Deduplicate and merge similar roles."""
        if not roles:
            return []

        # Group by normalized name
        groups: Dict[str, List[NLPRole]] = defaultdict(list)
        for role in roles:
            key = role.normalized_name.lower()
            groups[key].append(role)

        # Merge each group
        merged = []
        for normalized, group in groups.items():
            # Take the highest confidence one
            best = max(group, key=lambda r: r.confidence)
            # Boost confidence if found by multiple methods
            sources = set(r.source for r in group)
            if len(sources) > 1:
                best.confidence = min(0.95, best.confidence + 0.1 * (len(sources) - 1))
            merged.append(best)

        return sorted(merged, key=lambda r: -r.confidence)

    def extract_deliverables(self, text: str) -> List[NLPDeliverable]:
        """
        Extract deliverables from text.

        Args:
            text: Document text to analyze

        Returns:
            List of NLPDeliverable objects
        """
        deliverables = []

        # NLP-based extraction
        if self.is_nlp_available:
            deliverables.extend(self._extract_deliverables_nlp(text))

        # Pattern-based extraction
        deliverables.extend(self._extract_deliverables_patterns(text))

        return self._deduplicate_deliverables(deliverables)

    def _extract_deliverables_nlp(self, text: str) -> List[NLPDeliverable]:
        """Extract deliverables using spaCy noun phrase extraction."""
        deliverables = []
        doc = self.process_text(text)

        if doc is None:
            return deliverables

        # Look for noun phrases that are objects of delivery verbs
        delivery_verbs = {'deliver', 'provide', 'submit', 'prepare', 'develop', 'create', 'produce', 'generate'}

        for token in doc:
            if token.lemma_ in delivery_verbs:
                # Find direct objects
                for child in token.children:
                    if child.dep_ in ['dobj', 'pobj']:
                        np = self._get_noun_phrase(child)
                        if np:
                            deliv_type = self._classify_deliverable(np)
                            if deliv_type:
                                deliverables.append(NLPDeliverable(
                                    name=np,
                                    normalized_name=self._normalize_deliverable(np),
                                    confidence=0.8,
                                    source='noun_phrase',
                                    context=self._get_context(text, child.idx, child.idx + len(child.text)),
                                    deliverable_type=deliv_type
                                ))

        # Also check noun chunks for deliverable patterns
        for chunk in doc.noun_chunks:
            deliv_type = self._classify_deliverable(chunk.text)
            if deliv_type:
                deliverables.append(NLPDeliverable(
                    name=chunk.text,
                    normalized_name=self._normalize_deliverable(chunk.text),
                    confidence=0.6,
                    source='noun_phrase',
                    context=self._get_context(text, chunk.start_char, chunk.end_char),
                    deliverable_type=deliv_type
                ))

        return deliverables

    def _extract_deliverables_patterns(self, text: str) -> List[NLPDeliverable]:
        """Extract deliverables using regex patterns."""
        deliverables = []

        # Pattern: shall deliver/provide/submit [deliverable]
        delivery_pattern = r'\b(?:shall|will|must)\s+(?:deliver|provide|submit|prepare|develop|create)\s+(?:the\s+)?([A-Za-z][A-Za-z\s]+?(?:document|report|plan|specification|design|procedure|list|data|package|matrix)s?)\b'

        for match in re.finditer(delivery_pattern, text, re.IGNORECASE):
            name = match.group(1).strip()
            deliv_type = self._classify_deliverable(name)
            if deliv_type:
                deliverables.append(NLPDeliverable(
                    name=name,
                    normalized_name=self._normalize_deliverable(name),
                    confidence=0.75,
                    source='pattern',
                    context=self._get_context(text, match.start(), match.end()),
                    deliverable_type=deliv_type
                ))

        # Pattern: CDRL/DID references
        cdrl_pattern = r'\b((?:CDRL|DID|DI-)[\s-]?[A-Z0-9-]+)\b'
        for match in re.finditer(cdrl_pattern, text):
            deliverables.append(NLPDeliverable(
                name=match.group(1),
                normalized_name=match.group(1).upper(),
                confidence=0.95,
                source='pattern',
                context=self._get_context(text, match.start(), match.end()),
                deliverable_type='artifact'
            ))

        return deliverables

    def _classify_deliverable(self, text: str) -> Optional[str]:
        """Classify a deliverable by type."""
        text_lower = text.lower()

        for deliv_type, keywords in self.DELIVERABLE_TYPES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return deliv_type

        return None

    def _normalize_deliverable(self, name: str) -> str:
        """Normalize a deliverable name."""
        normalized = name.strip().title()
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def _deduplicate_deliverables(self, deliverables: List[NLPDeliverable]) -> List[NLPDeliverable]:
        """Deduplicate deliverables."""
        if not deliverables:
            return []

        seen = set()
        unique = []
        for d in deliverables:
            key = d.normalized_name.lower()
            if key not in seen:
                seen.add(key)
                unique.append(d)

        return sorted(unique, key=lambda d: -d.confidence)

    def extract_acronyms(self, text: str) -> List[NLPAcronym]:
        """
        Extract and analyze acronyms in text.

        Args:
            text: Document text to analyze

        Returns:
            List of NLPAcronym objects
        """
        acronyms = []

        # Pattern 1: Defined acronyms - "Full Name (ACRONYM)"
        defined_pattern = r'([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z]?[a-z]+)*)\s*\(([A-Z]{2,6})\)'

        defined_acronyms = {}
        for match in re.finditer(defined_pattern, text):
            expansion = match.group(1).strip()
            acronym = match.group(2)
            defined_acronyms[acronym] = {
                'expansion': expansion,
                'location': match.start()
            }

        # Pattern 2: All uppercase words (potential acronyms)
        acronym_pattern = r'\b([A-Z]{2,6})\b'

        usage_locations: Dict[str, List[int]] = defaultdict(list)
        for match in re.finditer(acronym_pattern, text):
            acronym = match.group(1)
            # Skip common words that are all caps
            if acronym not in {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT'}:
                usage_locations[acronym].append(match.start())

        # Build acronym list
        for acronym, locations in usage_locations.items():
            if acronym in defined_acronyms:
                info = defined_acronyms[acronym]
                acronyms.append(NLPAcronym(
                    acronym=acronym,
                    expansion=info['expansion'],
                    confidence=0.95,
                    is_defined=True,
                    definition_location=info['location'],
                    usage_locations=locations
                ))
            else:
                # Check if first use is before any potential definition
                first_use = min(locations)
                acronyms.append(NLPAcronym(
                    acronym=acronym,
                    expansion=None,
                    confidence=0.7,
                    is_defined=False,
                    definition_location=None,
                    usage_locations=locations
                ))

        return sorted(acronyms, key=lambda a: (-len(a.usage_locations), a.acronym))

    def get_sentence_boundaries(self, text: str) -> List[Tuple[int, int]]:
        """
        Get sentence boundaries using NLP.

        Args:
            text: Document text

        Returns:
            List of (start, end) tuples for each sentence
        """
        doc = self.process_text(text)

        if doc is None:
            # Fallback to simple pattern matching
            boundaries = []
            for match in re.finditer(r'[^.!?]+[.!?]+', text):
                boundaries.append((match.start(), match.end()))
            return boundaries

        return [(sent.start_char, sent.end_char) for sent in doc.sents]

    def analyze_requirements(self, text: str) -> Dict[str, Any]:
        """
        Analyze requirements in text for quality issues.

        Args:
            text: Document text

        Returns:
            Dict with analysis results
        """
        results = {
            'shall_statements': [],
            'passive_voice': [],
            'ambiguous_terms': [],
            'incomplete_requirements': []
        }

        doc = self.process_text(text)

        if doc is None:
            return results

        # Find shall statements
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if re.search(r'\bshall\b', sent_text, re.IGNORECASE):
                results['shall_statements'].append({
                    'text': sent_text,
                    'start': sent.start_char,
                    'end': sent.end_char
                })

        # Find ambiguous terms
        ambiguous_words = {'appropriate', 'adequate', 'sufficient', 'reasonable', 'timely',
                          'as required', 'if necessary', 'as needed', 'etc', 'and/or'}
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            for word in ambiguous_words:
                if word in sent_lower:
                    results['ambiguous_terms'].append({
                        'term': word,
                        'sentence': sent.text.strip(),
                        'start': sent.start_char
                    })

        # Find incomplete requirements (TBD, TBR, TBS)
        tbd_pattern = r'\b(TBD|TBR|TBS|TO BE DETERMINED|TO BE RESOLVED|TO BE SUPPLIED)\b'
        for match in re.finditer(tbd_pattern, text, re.IGNORECASE):
            results['incomplete_requirements'].append({
                'marker': match.group(1),
                'location': match.start(),
                'context': self._get_context(text, match.start(), match.end(), 50)
            })

        return results


# Module-level cache for spaCy models to prevent multiple loads
_SPACY_MODEL_CACHE = {}


def get_spacy_model(model_name: str):
    """
    Get or load a spaCy model with caching.

    Prevents multiple checkers from each loading the model separately,
    which is expensive and can cause memory issues.

    Args:
        model_name: Name of the spaCy model (e.g., 'en_core_web_sm')

    Returns:
        The loaded spaCy model
    """
    global _SPACY_MODEL_CACHE

    if model_name not in _SPACY_MODEL_CACHE:
        import spacy
        _SPACY_MODEL_CACHE[model_name] = spacy.load(model_name)

    return _SPACY_MODEL_CACHE[model_name]


# Convenience function for quick access
def get_nlp_processor() -> NLPProcessor:
    """Get a shared NLP processor instance."""
    global _nlp_processor
    if _nlp_processor is None:
        _nlp_processor = NLPProcessor()
    return _nlp_processor

_nlp_processor = None


# Export main classes
__all__ = [
    'NLPProcessor',
    'NLPRole',
    'NLPDeliverable',
    'NLPAcronym',
    'get_nlp_processor'
]
