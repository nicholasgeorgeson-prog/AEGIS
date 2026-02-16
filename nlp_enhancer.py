#!/usr/bin/env python3
"""
NLP Enhancement Module for AEGIS
============================================
Version: reads from version.json (module v1.0)
Date: 2026-01-27

Enhances role extraction and text analysis using available NLP libraries.
Uses sklearn (already installed) for classification and clustering.
Optionally uses spaCy if available for even better results.

Author: Nick / SAIC Systems Engineering
"""

import re
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import logging

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

# Check available libraries
SPACY_AVAILABLE = False
SKLEARN_AVAILABLE = False
NLTK_AVAILABLE = False
TEXTSTAT_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    pass

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    pass

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    pass


# ============================================================================
# ENHANCED ROLE PATTERNS
# ============================================================================

# Expanded role indicators with confidence weights
ROLE_INDICATORS = {
    # High confidence - explicit role markers
    'high': [
        (r'\b(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:shall|will|must|is responsible)', 0.95),
        (r'\b(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:reviews?|approves?|authorizes?)', 0.90),
        (r'\bresponsibility\s+of\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 0.95),
        (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:role|position|function)', 0.90),
    ],
    # Medium confidence - common patterns
    'medium': [
        (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:performs?|conducts?|executes?)', 0.75),
        (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:ensures?|verifies?|validates?)', 0.75),
        (r'\bby\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 0.70),
        (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:coordinates?|manages?|leads?)', 0.75),
    ],
    # Lower confidence - contextual
    'low': [
        (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:may|can|should)', 0.55),
        (r'\bnotif(?:y|ies)\s+(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 0.60),
        (r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:department|team|group|office)', 0.65),
    ],
}

# Common organizational role patterns
KNOWN_ROLE_PATTERNS = [
    # Engineering roles
    r'\b(?:Chief|Senior|Lead|Principal|Staff)?\s*(?:Engineer(?:ing)?|Architect|Designer|Developer)\b',
    r'\b(?:Systems?|Software|Hardware|Electrical|Mechanical|Test|Quality)\s+Engineer\b',
    # Management roles  
    r'\b(?:Project|Program|Product|Engineering|Technical|Operations?)\s+Manager\b',
    r'\b(?:Director|VP|Vice President|Chief)\s+(?:of\s+)?[A-Z][a-z]+\b',
    # Technical roles
    r'\b(?:Technical|Tech)\s+(?:Lead|Writer|Specialist|Analyst|Authority)\b',
    r'\b(?:Subject Matter Expert|SME|Domain Expert)\b',
    # Quality/Safety roles
    r'\b(?:Quality|Safety|Reliability|Security)\s+(?:Engineer|Manager|Officer|Analyst)\b',
    r'\bQA(?:\s+Engineer|\s+Manager)?\b',
    # Document roles
    r'\b(?:Document|Configuration|Data)\s+(?:Manager|Controller|Specialist)\b',
    # Review roles
    r'\b(?:Reviewer|Approver|Authorizer|Signatory)\b',
    r'\b(?:Review(?:ing)?\s+)?Authority\b',
]

# Action verbs for Statement Forge enhancement
ACTION_VERBS = {
    'directive': [
        'shall', 'must', 'will', 'require', 'mandate', 'direct', 'instruct',
        'order', 'command', 'dictate', 'prescribe', 'stipulate'
    ],
    'responsibility': [
        'responsible', 'accountable', 'ensure', 'verify', 'validate', 'confirm',
        'certify', 'attest', 'guarantee', 'assure'
    ],
    'action': [
        'perform', 'execute', 'conduct', 'implement', 'accomplish', 'complete',
        'carry out', 'undertake', 'fulfill', 'discharge'
    ],
    'review': [
        'review', 'approve', 'authorize', 'sign', 'endorse', 'accept',
        'concur', 'ratify', 'sanction', 'validate'
    ],
    'create': [
        'create', 'develop', 'design', 'prepare', 'draft', 'write', 'author',
        'produce', 'generate', 'establish', 'formulate'
    ],
    'manage': [
        'manage', 'coordinate', 'oversee', 'supervise', 'control', 'direct',
        'administer', 'lead', 'organize', 'monitor'
    ],
    'communicate': [
        'notify', 'inform', 'report', 'communicate', 'brief', 'advise',
        'alert', 'announce', 'distribute', 'disseminate'
    ],
    'analyze': [
        'analyze', 'assess', 'evaluate', 'examine', 'investigate', 'study',
        'inspect', 'audit', 'review', 'appraise'
    ],
}


@dataclass
class EnhancedEntity:
    """An entity extracted with enhanced NLP analysis."""
    text: str
    entity_type: str  # 'ROLE', 'ORG', 'DELIVERABLE', 'ACTION'
    confidence: float
    context: str
    location: str
    features: Dict[str, Any] = field(default_factory=dict)


class NLPEnhancer:
    """
    Enhances text analysis using available NLP libraries.
    
    Features:
    - Role extraction with pattern matching and ML classification
    - Action verb detection for Statement Forge
    - Text similarity for role deduplication
    - Readability analysis
    """
    
    def __init__(self):
        self._spacy_nlp = None
        self._tfidf = None
        self._load_models()
    
    def _load_models(self):
        """Load available NLP models."""
        # Try to load spaCy
        if SPACY_AVAILABLE:
            try:
                self._spacy_nlp = spacy.load('en_core_web_sm')
                logger.info("spaCy model loaded")
            except OSError:
                logger.debug("spaCy model not downloaded")
        
        # Initialize TF-IDF for similarity
        if SKLEARN_AVAILABLE:
            self._tfidf = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words='english',
                max_features=1000
            )
    
    def extract_roles_enhanced(self, text: str, location: str = "") -> List[EnhancedEntity]:
        """
        Extract roles using multiple methods for maximum accuracy.
        
        Methods used:
        1. Pattern matching with confidence weights
        2. spaCy NER (if available)
        3. Known role pattern matching
        """
        entities = []
        seen_texts = set()
        
        # Method 1: Enhanced pattern matching
        for confidence_level, patterns in ROLE_INDICATORS.items():
            for pattern, base_confidence in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    role_text = match.group(1) if match.groups() else match.group(0)
                    role_text = role_text.strip()
                    
                    if role_text.lower() in seen_texts:
                        continue
                    if len(role_text) < 3 or len(role_text) > 50:
                        continue
                    if self._is_common_word(role_text):
                        continue
                    
                    seen_texts.add(role_text.lower())
                    
                    # Get context
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()
                    
                    entities.append(EnhancedEntity(
                        text=role_text,
                        entity_type='ROLE',
                        confidence=base_confidence,
                        context=context,
                        location=location,
                        features={'method': 'pattern', 'level': confidence_level}
                    ))
        
        # Method 2: Known role patterns
        for pattern in KNOWN_ROLE_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                role_text = match.group(0).strip()
                
                if role_text.lower() in seen_texts:
                    continue
                
                seen_texts.add(role_text.lower())
                
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                entities.append(EnhancedEntity(
                    text=role_text,
                    entity_type='ROLE',
                    confidence=0.90,  # High confidence for known patterns
                    context=context,
                    location=location,
                    features={'method': 'known_pattern'}
                ))
        
        # Method 3: spaCy NER (if available)
        if self._spacy_nlp:
            doc = self._spacy_nlp(text)
            for ent in doc.ents:
                if ent.label_ in ('ORG', 'PERSON', 'GPE'):
                    ent_text = ent.text.strip()
                    
                    if ent_text.lower() in seen_texts:
                        continue
                    if len(ent_text) < 3:
                        continue
                    
                    # Check if this looks like a role
                    if self._looks_like_role(ent_text, ent.sent.text):
                        seen_texts.add(ent_text.lower())
                        
                        entities.append(EnhancedEntity(
                            text=ent_text,
                            entity_type='ROLE' if ent.label_ != 'ORG' else 'ORG',
                            confidence=0.80,
                            context=ent.sent.text,
                            location=location,
                            features={'method': 'spacy_ner', 'label': ent.label_}
                        ))
        
        return entities
    
    def extract_actions(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract action statements for Statement Forge enhancement.
        
        Returns list of dicts with:
        - verb: The action verb
        - category: Type of action (directive, responsibility, etc.)
        - subject: Who performs the action (if detectable)
        - object: What the action is performed on
        - sentence: Full sentence
        """
        actions = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # Find action verbs
            for category, verbs in ACTION_VERBS.items():
                for verb in verbs:
                    pattern = rf'\b{verb}\b'
                    if re.search(pattern, sentence, re.IGNORECASE):
                        # Try to extract subject and object
                        subject, obj = self._extract_subject_object(sentence, verb)
                        
                        actions.append({
                            'verb': verb,
                            'category': category,
                            'subject': subject,
                            'object': obj,
                            'sentence': sentence,
                            'confidence': 0.85 if category == 'directive' else 0.75
                        })
                        break  # One action per sentence
        
        return actions
    
    def calculate_similarity(self, texts: List[str]) -> List[List[float]]:
        """
        Calculate pairwise similarity between texts.
        
        Useful for:
        - Deduplicating similar roles
        - Grouping related statements
        - Finding redundant content
        """
        if not SKLEARN_AVAILABLE or len(texts) < 2:
            return []
        
        try:
            tfidf_matrix = self._tfidf.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            return similarity_matrix.tolist()
        except Exception as e:
            logger.debug(f"Similarity calculation failed: {e}")
            return []
    
    def cluster_roles(self, roles: List[str], threshold: float = 0.7) -> Dict[str, List[str]]:
        """
        Cluster similar roles together.
        
        Returns dict mapping canonical role name to list of variants.
        """
        if not SKLEARN_AVAILABLE or len(roles) < 2:
            return {r: [r] for r in roles}
        
        try:
            tfidf_matrix = self._tfidf.fit_transform(roles)
            similarity = cosine_similarity(tfidf_matrix)
            
            # Use agglomerative clustering
            clustering = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=1 - threshold,
                metric='precomputed',
                linkage='average'
            )
            
            # Convert similarity to distance
            distance_matrix = 1 - similarity
            labels = clustering.fit_predict(distance_matrix)
            
            # Group by cluster
            clusters = defaultdict(list)
            for role, label in zip(roles, labels):
                clusters[label].append(role)
            
            # Pick canonical name (shortest or most common pattern)
            result = {}
            for cluster_roles in clusters.values():
                canonical = min(cluster_roles, key=len)
                result[canonical] = cluster_roles
            
            return result
            
        except Exception as e:
            logger.debug(f"Clustering failed: {e}")
            return {r: [r] for r in roles}
    
    def analyze_readability(self, text: str) -> Dict[str, Any]:
        """
        Analyze text readability using multiple metrics.
        """
        metrics = {}
        
        # Basic stats
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]
        
        metrics['word_count'] = len(words)
        metrics['sentence_count'] = len(sentences)
        metrics['avg_words_per_sentence'] = len(words) / max(len(sentences), 1)
        
        # Use textstat if available
        if TEXTSTAT_AVAILABLE:
            metrics['flesch_reading_ease'] = textstat.flesch_reading_ease(text)
            metrics['flesch_kincaid_grade'] = textstat.flesch_kincaid_grade(text)
            metrics['gunning_fog'] = textstat.gunning_fog(text)
            metrics['smog_index'] = textstat.smog_index(text)
            metrics['automated_readability_index'] = textstat.automated_readability_index(text)
        else:
            # Basic Flesch calculation
            syllables = self._count_syllables(text)
            if len(words) > 0 and len(sentences) > 0:
                metrics['flesch_reading_ease'] = (
                    206.835 
                    - 1.015 * (len(words) / len(sentences))
                    - 84.6 * (syllables / len(words))
                )
                metrics['flesch_kincaid_grade'] = (
                    0.39 * (len(words) / len(sentences))
                    + 11.8 * (syllables / len(words))
                    - 15.59
                )
        
        return metrics
    
    def _is_common_word(self, text: str) -> bool:
        """Check if text is a common word that shouldn't be a role."""
        common = {
            'the', 'a', 'an', 'this', 'that', 'these', 'those',
            'it', 'they', 'we', 'you', 'he', 'she', 'all', 'any',
            'some', 'each', 'every', 'both', 'few', 'many', 'most',
            'other', 'such', 'no', 'nor', 'not', 'only', 'own',
            'same', 'so', 'than', 'too', 'very', 'just', 'also',
            'now', 'here', 'there', 'when', 'where', 'why', 'how',
            'what', 'which', 'who', 'whom', 'whose', 'if', 'then',
            'because', 'although', 'while', 'since', 'until', 'unless',
            'however', 'therefore', 'thus', 'hence', 'accordingly',
            'section', 'paragraph', 'page', 'document', 'figure', 'table',
            'note', 'example', 'step', 'item', 'part', 'chapter',
        }
        return text.lower() in common
    
    def _looks_like_role(self, text: str, context: str) -> bool:
        """Check if text looks like a role based on context."""
        # Check for role-like context
        role_context_patterns = [
            r'\bresponsib',
            r'\bshall\b',
            r'\bmust\b',
            r'\bwill\b',
            r'\bperform',
            r'\breview',
            r'\bapprove',
            r'\bmanag',
            r'\blead',
            r'\bcoordinat',
        ]
        
        context_lower = context.lower()
        for pattern in role_context_patterns:
            if re.search(pattern, context_lower):
                return True
        
        return False
    
    def _extract_subject_object(self, sentence: str, verb: str) -> Tuple[str, str]:
        """Extract subject and object from a sentence."""
        subject = ""
        obj = ""
        
        # Simple pattern: Subject verb object
        pattern = rf'(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+{verb}s?\s+(.+?)(?:\.|$)'
        match = re.search(pattern, sentence, re.IGNORECASE)
        
        if match:
            subject = match.group(1).strip()
            obj = match.group(2).strip()[:100]  # Limit object length
        
        return subject, obj
    
    def _count_syllables(self, text: str) -> int:
        """Count syllables in text (basic method)."""
        text = text.lower()
        count = 0
        vowels = 'aeiouy'
        
        for word in text.split():
            word_count = 0
            prev_vowel = False
            
            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_vowel:
                    word_count += 1
                prev_vowel = is_vowel
            
            # Adjust for silent e
            if word.endswith('e') and word_count > 1:
                word_count -= 1
            
            count += max(word_count, 1)
        
        return count


def get_nlp_capabilities() -> Dict[str, Any]:
    """Report available NLP capabilities."""
    return {
        'spacy': SPACY_AVAILABLE,
        'sklearn': SKLEARN_AVAILABLE,
        'nltk': NLTK_AVAILABLE,
        'textstat': TEXTSTAT_AVAILABLE,
        'features': {
            'enhanced_role_extraction': True,  # Always available via patterns
            'role_clustering': SKLEARN_AVAILABLE,
            'text_similarity': SKLEARN_AVAILABLE,
            'ner': SPACY_AVAILABLE,
            'advanced_readability': TEXTSTAT_AVAILABLE,
        }
    }
