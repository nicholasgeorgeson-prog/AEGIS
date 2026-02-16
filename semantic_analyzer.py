"""
Semantic Analyzer for AEGIS
======================================
Version: 1.0.0
Date: 2026-02-03

Provides semantic similarity analysis using Sentence-Transformers.
Works completely offline with downloaded models.

Features:
- Find semantically similar sections across documents
- Detect redundant/duplicate content
- Cluster related requirements
- Semantic role matching
- Find related responsibilities

Air-gap compatible: Models are downloaded once and cached locally.

Usage:
    from semantic_analyzer import SemanticAnalyzer
    analyzer = SemanticAnalyzer()

    # Find similar sentences
    similar = analyzer.find_similar(query, sentences, top_k=5)

    # Detect duplicates
    duplicates = analyzer.find_duplicates(sentences, threshold=0.85)

    # Cluster requirements
    clusters = analyzer.cluster_sentences(sentences, n_clusters=5)
"""

import os
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np

# Structured logging
try:
    from config_logging import get_logger
    _logger = get_logger('semantic_analyzer')
except ImportError:
    _logger = None

def _log(message: str, level: str = 'info', **kwargs):
    """Internal logging helper."""
    if _logger:
        getattr(_logger, level)(message, **kwargs)
    elif level in ('warning', 'error', 'critical'):
        print(f"[SemanticAnalyzer] {level.upper()}: {message}")


# Try to import sentence-transformers
_sbert_available = False
_model = None

try:
    from sentence_transformers import SentenceTransformer, util
    _sbert_available = True
    _log("sentence-transformers available", level='debug')
except ImportError:
    _log("sentence-transformers not installed - semantic features disabled", level='warning')


@dataclass
class SimilarityResult:
    """Result of a similarity search."""
    text: str
    score: float
    index: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'text': self.text,
            'score': round(self.score, 4),
            'index': self.index,
            'metadata': self.metadata
        }


@dataclass
class DuplicateGroup:
    """Group of duplicate/near-duplicate sentences."""
    sentences: List[str]
    indices: List[int]
    similarity_score: float
    representative: str  # Most central sentence in the group

    def to_dict(self) -> dict:
        return {
            'sentences': self.sentences,
            'indices': self.indices,
            'similarity_score': round(self.similarity_score, 4),
            'representative': self.representative,
            'count': len(self.sentences)
        }


@dataclass
class SemanticCluster:
    """Cluster of semantically related sentences."""
    sentences: List[str]
    indices: List[int]
    centroid_text: str  # Most representative sentence
    keywords: List[str]
    cluster_id: int

    def to_dict(self) -> dict:
        return {
            'cluster_id': self.cluster_id,
            'sentences': self.sentences,
            'indices': self.indices,
            'centroid_text': self.centroid_text,
            'keywords': self.keywords,
            'size': len(self.sentences)
        }


class SemanticAnalyzer:
    """
    Semantic analysis using Sentence-Transformers.

    Uses pre-trained models for:
    - Semantic similarity search
    - Duplicate detection
    - Sentence clustering
    - Cross-document analysis

    All processing is local/offline after initial model download.
    """

    VERSION = '1.0.0'

    # Recommended models for different use cases
    # all-MiniLM-L6-v2: Fast, good quality, ~80MB
    # all-mpnet-base-v2: Best quality, slower, ~420MB
    # paraphrase-MiniLM-L6-v2: Good for paraphrase detection
    DEFAULT_MODEL = 'all-MiniLM-L6-v2'

    # Model cache directory for air-gapped deployment
    MODEL_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'models', 'sentence_transformers')

    def __init__(self, model_name: str = None, load_model: bool = True):
        """
        Initialize the semantic analyzer.

        Args:
            model_name: Name of the sentence-transformers model to use
            load_model: Whether to load the model immediately
        """
        global _model

        self.model_name = model_name or self.DEFAULT_MODEL
        self.model = None
        self.is_available = False
        self._embeddings_cache: Dict[str, np.ndarray] = {}

        if load_model and _sbert_available:
            self._load_model()

    def _ensure_model(self) -> bool:
        """v5.0.2: Lazy-load model on first use for faster startup."""
        if self.model is not None:
            return True
        if _sbert_available:
            return self._load_model()
        return False

    def _load_model(self) -> bool:
        """Load the sentence-transformers model."""
        global _model

        if not _sbert_available:
            _log("sentence-transformers not installed", level='warning')
            return False

        # Use cached model if available
        if _model is not None:
            self.model = _model
            self.is_available = True
            _log("Using cached sentence-transformers model", level='debug')
            return True

        try:
            # Create cache directory if it doesn't exist
            os.makedirs(self.MODEL_CACHE_DIR, exist_ok=True)

            _log(f"Loading sentence-transformers model: {self.model_name}", level='info')

            # Try to load from local cache first (for air-gapped networks)
            local_path = os.path.join(self.MODEL_CACHE_DIR, self.model_name.replace('/', '_'))

            if os.path.exists(local_path):
                self.model = SentenceTransformer(local_path)
                _log(f"Loaded model from local cache: {local_path}", level='info')
            else:
                # v5.0.0: Set short timeout for download attempts to avoid 160s+ hangs
                # on air-gapped or corporate networks that block huggingface.co
                os.environ.setdefault('HF_HUB_DOWNLOAD_TIMEOUT', '10')
                try:
                    self.model = SentenceTransformer(self.model_name)
                    # Save for future offline use
                    try:
                        self.model.save(local_path)
                        _log(f"Model cached to: {local_path}", level='info')
                    except Exception as e:
                        _log(f"Could not cache model: {e}", level='warning')
                except Exception as dl_err:
                    _log(f"Could not download model (network may be restricted): {dl_err}", level='warning')
                    _log("Semantic analysis will be disabled. To enable offline, place the model in: " + local_path, level='info')
                    return False

            _model = self.model  # Cache globally
            self.is_available = True
            _log(f"Model loaded successfully: {self.model_name}", level='info')
            return True

        except Exception as e:
            _log(f"Failed to load model: {e}", level='error')
            return False

    def encode(self, texts: List[str], show_progress: bool = False) -> Optional[np.ndarray]:
        """
        Encode texts to embeddings.

        Args:
            texts: List of texts to encode
            show_progress: Show progress bar during encoding

        Returns:
            numpy array of embeddings or None if not available
        """
        if not self.is_available:
            self._ensure_model()  # v5.0.2: Lazy load
        if not self.is_available:
            return None

        try:
            # Check cache for already computed embeddings
            uncached_texts = []
            uncached_indices = []

            for i, text in enumerate(texts):
                if text not in self._embeddings_cache:
                    uncached_texts.append(text)
                    uncached_indices.append(i)

            # Encode uncached texts
            if uncached_texts:
                new_embeddings = self.model.encode(
                    uncached_texts,
                    convert_to_numpy=True,
                    show_progress_bar=show_progress
                )

                # Cache the new embeddings
                for i, text in enumerate(uncached_texts):
                    self._embeddings_cache[text] = new_embeddings[i]

            # Build result array
            embeddings = np.array([self._embeddings_cache[text] for text in texts])
            return embeddings

        except Exception as e:
            _log(f"Encoding error: {e}", level='error')
            return None

    def find_similar(self, query: str, corpus: List[str],
                     top_k: int = 5, threshold: float = 0.0,
                     metadata: List[Dict] = None) -> List[SimilarityResult]:
        """
        Find the most similar sentences to a query.

        Args:
            query: The query text
            corpus: List of sentences to search
            top_k: Number of results to return
            threshold: Minimum similarity threshold (0-1)
            metadata: Optional metadata for each corpus sentence

        Returns:
            List of SimilarityResult objects
        """
        if not self.is_available or not corpus:
            return []

        try:
            # Encode query and corpus
            query_embedding = self.encode([query])[0]
            corpus_embeddings = self.encode(corpus)

            if corpus_embeddings is None:
                return []

            # Compute similarities
            similarities = util.cos_sim(query_embedding, corpus_embeddings)[0]

            # Get top results
            top_results = []
            scores_indices = [(float(similarities[i]), i) for i in range(len(corpus))]
            scores_indices.sort(reverse=True)

            for score, idx in scores_indices[:top_k]:
                if score >= threshold:
                    meta = metadata[idx] if metadata and idx < len(metadata) else {}
                    top_results.append(SimilarityResult(
                        text=corpus[idx],
                        score=score,
                        index=idx,
                        metadata=meta
                    ))

            return top_results

        except Exception as e:
            _log(f"Similarity search error: {e}", level='error')
            return []

    def find_duplicates(self, sentences: List[str],
                        threshold: float = 0.85,
                        min_length: int = 10) -> List[DuplicateGroup]:
        """
        Find groups of duplicate or near-duplicate sentences.

        Args:
            sentences: List of sentences to analyze
            threshold: Similarity threshold for duplicates (0-1)
            min_length: Minimum sentence length to consider

        Returns:
            List of DuplicateGroup objects
        """
        if not sentences:
            return []
        # v5.0.2: Lazy-load model on first use
        if not self.is_available:
            self._ensure_model()
        if not self.is_available:
            return []

        try:
            # Filter short sentences
            valid_sentences = [(i, s) for i, s in enumerate(sentences) if len(s) >= min_length]

            if not valid_sentences:
                return []

            indices, texts = zip(*valid_sentences)
            indices = list(indices)
            texts = list(texts)

            # Encode all sentences
            embeddings = self.encode(texts)
            if embeddings is None:
                return []

            # Compute pairwise similarities
            sim_matrix = util.cos_sim(embeddings, embeddings)

            # Find duplicate groups using union-find approach
            n = len(texts)
            visited = set()
            groups = []

            for i in range(n):
                if i in visited:
                    continue

                # Find all sentences similar to sentence i
                group_indices = [i]
                group_texts = [texts[i]]

                for j in range(i + 1, n):
                    if j not in visited and float(sim_matrix[i][j]) >= threshold:
                        group_indices.append(j)
                        group_texts.append(texts[j])
                        visited.add(j)

                if len(group_indices) > 1:
                    # Calculate average similarity within group
                    total_sim = 0
                    count = 0
                    for gi in range(len(group_indices)):
                        for gj in range(gi + 1, len(group_indices)):
                            total_sim += float(sim_matrix[group_indices[gi]][group_indices[gj]])
                            count += 1
                    avg_sim = total_sim / count if count > 0 else threshold

                    # Find most central sentence (highest avg similarity to others)
                    best_central = 0
                    best_central_score = 0
                    for gi, idx in enumerate(group_indices):
                        score = sum(float(sim_matrix[idx][group_indices[gj]])
                                   for gj in range(len(group_indices)) if gj != gi)
                        if score > best_central_score:
                            best_central_score = score
                            best_central = gi

                    groups.append(DuplicateGroup(
                        sentences=group_texts,
                        indices=[indices[gi] for gi in group_indices],
                        similarity_score=avg_sim,
                        representative=group_texts[best_central]
                    ))

                visited.add(i)

            return sorted(groups, key=lambda g: len(g.sentences), reverse=True)

        except Exception as e:
            _log(f"Duplicate detection error: {e}", level='error')
            return []

    def cluster_sentences(self, sentences: List[str],
                          n_clusters: int = 5,
                          min_cluster_size: int = 2) -> List[SemanticCluster]:
        """
        Cluster sentences by semantic similarity.

        Args:
            sentences: List of sentences to cluster
            n_clusters: Number of clusters to create
            min_cluster_size: Minimum sentences per cluster

        Returns:
            List of SemanticCluster objects
        """
        if not self.is_available or len(sentences) < n_clusters:
            return []

        try:
            from sklearn.cluster import KMeans
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Encode sentences
            embeddings = self.encode(sentences)
            if embeddings is None:
                return []

            # Cluster using K-means
            n_clusters = min(n_clusters, len(sentences))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)

            # Group sentences by cluster
            clusters_dict: Dict[int, List[Tuple[int, str]]] = defaultdict(list)
            for idx, (label, sentence) in enumerate(zip(labels, sentences)):
                clusters_dict[label].append((idx, sentence))

            # Build cluster objects
            clusters = []

            # Use TF-IDF for keyword extraction
            vectorizer = TfidfVectorizer(max_features=5, stop_words='english')

            for cluster_id, members in clusters_dict.items():
                if len(members) < min_cluster_size:
                    continue

                indices = [m[0] for m in members]
                texts = [m[1] for m in members]

                # Find centroid sentence (closest to cluster center)
                cluster_embeddings = embeddings[indices]
                centroid = kmeans.cluster_centers_[cluster_id]
                distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
                centroid_idx = np.argmin(distances)
                centroid_text = texts[centroid_idx]

                # Extract keywords
                try:
                    tfidf_matrix = vectorizer.fit_transform(texts)
                    feature_names = vectorizer.get_feature_names_out()
                    keywords = list(feature_names)
                except:
                    keywords = []

                clusters.append(SemanticCluster(
                    sentences=texts,
                    indices=indices,
                    centroid_text=centroid_text,
                    keywords=keywords,
                    cluster_id=cluster_id
                ))

            return sorted(clusters, key=lambda c: len(c.sentences), reverse=True)

        except Exception as e:
            _log(f"Clustering error: {e}", level='error')
            return []

    def compute_document_similarity(self, doc1_sentences: List[str],
                                    doc2_sentences: List[str]) -> Dict[str, Any]:
        """
        Compute similarity between two documents.

        Args:
            doc1_sentences: Sentences from first document
            doc2_sentences: Sentences from second document

        Returns:
            Dictionary with similarity metrics
        """
        if not self.is_available:
            return {'error': 'Semantic analyzer not available'}

        try:
            # Encode both documents
            emb1 = self.encode(doc1_sentences)
            emb2 = self.encode(doc2_sentences)

            if emb1 is None or emb2 is None:
                return {'error': 'Encoding failed'}

            # Document-level embeddings (mean of sentence embeddings)
            doc1_emb = np.mean(emb1, axis=0)
            doc2_emb = np.mean(emb2, axis=0)

            # Overall document similarity
            doc_similarity = float(util.cos_sim(doc1_emb, doc2_emb)[0][0])

            # Find matching sentences between documents
            cross_sim = util.cos_sim(emb1, emb2)

            matching_pairs = []
            for i in range(len(doc1_sentences)):
                for j in range(len(doc2_sentences)):
                    sim = float(cross_sim[i][j])
                    if sim > 0.8:  # High similarity threshold
                        matching_pairs.append({
                            'doc1_sentence': doc1_sentences[i],
                            'doc2_sentence': doc2_sentences[j],
                            'similarity': round(sim, 4)
                        })

            # Sort by similarity
            matching_pairs.sort(key=lambda x: x['similarity'], reverse=True)

            return {
                'document_similarity': round(doc_similarity, 4),
                'doc1_sentence_count': len(doc1_sentences),
                'doc2_sentence_count': len(doc2_sentences),
                'matching_pairs': matching_pairs[:20],  # Top 20
                'total_matches': len(matching_pairs)
            }

        except Exception as e:
            _log(f"Document similarity error: {e}", level='error')
            return {'error': str(e)}

    def find_related_roles(self, role_name: str,
                           role_descriptions: Dict[str, str],
                           top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find roles related to a given role based on their descriptions.

        Args:
            role_name: Name of the role to find related roles for
            role_descriptions: Dict mapping role names to their descriptions
            top_k: Number of related roles to return

        Returns:
            List of related roles with similarity scores
        """
        if not self.is_available or role_name not in role_descriptions:
            return []

        try:
            query_desc = role_descriptions[role_name]
            other_roles = [(name, desc) for name, desc in role_descriptions.items()
                          if name != role_name]

            if not other_roles:
                return []

            names, descs = zip(*other_roles)

            results = self.find_similar(
                query_desc,
                list(descs),
                top_k=top_k,
                threshold=0.3
            )

            return [
                {
                    'role_name': names[r.index],
                    'description': r.text,
                    'similarity': r.score
                }
                for r in results
            ]

        except Exception as e:
            _log(f"Related roles error: {e}", level='error')
            return []

    def clear_cache(self):
        """Clear the embeddings cache."""
        self._embeddings_cache.clear()
        _log("Embeddings cache cleared", level='debug')


# Convenience function
def get_semantic_analyzer() -> SemanticAnalyzer:
    """Get a shared SemanticAnalyzer instance."""
    global _semantic_analyzer
    if '_semantic_analyzer' not in globals() or _semantic_analyzer is None:
        _semantic_analyzer = SemanticAnalyzer()
    return _semantic_analyzer

_semantic_analyzer = None


# Export
__all__ = [
    'SemanticAnalyzer',
    'SimilarityResult',
    'DuplicateGroup',
    'SemanticCluster',
    'get_semantic_analyzer'
]
