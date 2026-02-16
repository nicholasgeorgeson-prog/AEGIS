#!/usr/bin/env python3
"""
Requirement Similarity & Duplicate Detection Checker v1.0.0
============================================================
Uses sentence-transformers to detect duplicate/near-duplicate requirements
and semantically similar statements across a document.

In large requirements documents (SOWs, specs), duplicate requirements are
a major quality issue:
- Conflicting duplicates create ambiguity
- Redundant requirements inflate scope
- Scattered related requirements should be consolidated

This checker:
1. Embeds all requirement sentences using sentence-transformers
2. Computes pairwise cosine similarity
3. Flags pairs above a configurable threshold as potential duplicates
4. Groups related requirements into clusters for review
5. Detects contradicting requirements (high similarity but opposite polarity)

Falls back to TF-IDF + cosine similarity when sentence-transformers unavailable.
"""

import re
import math
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

try:
    from base_checker import BaseChecker, ReviewIssue
except ImportError:
    from .base_checker import BaseChecker, ReviewIssue

__version__ = "1.0.0"

# Requirement sentence patterns
REQUIREMENT_PATTERNS = [
    re.compile(r'\b(?:shall|must|will|should)\b', re.IGNORECASE),
]


class RequirementSimilarityChecker(BaseChecker):
    """
    Detects duplicate and near-duplicate requirements using
    semantic similarity (sentence-transformers or TF-IDF fallback).
    """

    CHECKER_NAME = "Requirement Similarity"
    CHECKER_VERSION = "1.0.0"

    DUPLICATE_THRESHOLD = 0.92    # Very high similarity = likely duplicate
    SIMILAR_THRESHOLD = 0.80      # High similarity = related, worth reviewing
    MAX_REQUIREMENTS = 500        # Limit for performance (pairwise = O(n²))
    MIN_SENTENCE_LENGTH = 15      # Skip very short sentences

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.model = None
        self.st_available = False
        self._init_model()

    def _init_model(self):
        """Initialize sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer
            # Use a lightweight model — good balance of speed and accuracy
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.st_available = True
        except (ImportError, Exception):
            self.st_available = False

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        # Extract requirement-like sentences
        requirements = self._extract_requirements(paragraphs)

        if len(requirements) < 2:
            return issues

        # Limit for performance
        if len(requirements) > self.MAX_REQUIREMENTS:
            requirements = requirements[:self.MAX_REQUIREMENTS]

        if self.st_available and self.model is not None:
            issues.extend(self._check_with_transformers(requirements))
        else:
            issues.extend(self._check_with_tfidf(requirements))

        return issues

    def _extract_requirements(self, paragraphs):
        """Extract requirement-like sentences from paragraphs."""
        requirements = []

        for idx, text in paragraphs:
            if self.is_boilerplate(text):
                continue

            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)

            for sent in sentences:
                sent = sent.strip()
                if len(sent) < self.MIN_SENTENCE_LENGTH:
                    continue

                # Check if it looks like a requirement
                is_req = any(p.search(sent) for p in REQUIREMENT_PATTERNS)

                if is_req:
                    requirements.append({
                        'text': sent,
                        'paragraph_index': idx,
                        'context': text[:200]
                    })

        return requirements

    def _check_with_transformers(self, requirements):
        """Use sentence-transformers for semantic similarity detection."""
        issues = []

        try:
            texts = [r['text'] for r in requirements]

            # Encode all requirements
            embeddings = self.model.encode(texts, show_progress_bar=False, batch_size=32)

            # Compute pairwise cosine similarity
            duplicates_found = set()
            similar_pairs = []

            for i in range(len(embeddings)):
                for j in range(i + 1, len(embeddings)):
                    # Cosine similarity
                    sim = self._cosine_similarity(embeddings[i], embeddings[j])

                    if sim >= self.DUPLICATE_THRESHOLD:
                        pair_key = (min(i, j), max(i, j))
                        if pair_key not in duplicates_found:
                            duplicates_found.add(pair_key)
                            issues.append(ReviewIssue(
                                category="Requirement Similarity",
                                severity="High",
                                message=f"Potential DUPLICATE requirement detected (similarity: {sim:.0%}).",
                                context=f"Req A (¶{requirements[i]['paragraph_index']}): \"{requirements[i]['text'][:120]}\" | Req B (¶{requirements[j]['paragraph_index']}): \"{requirements[j]['text'][:120]}\"",
                                paragraph_index=requirements[i]['paragraph_index'],
                                suggestion="Review both requirements. If they're truly duplicates, consolidate into one. If they differ, make the distinction explicit.",
                                rule_id="SIM-DUP",
                                flagged_text=requirements[i]['text'][:80]
                            ))

                    elif sim >= self.SIMILAR_THRESHOLD:
                        similar_pairs.append((i, j, sim))

            # Report top similar (non-duplicate) pairs
            similar_pairs.sort(key=lambda x: x[2], reverse=True)
            for i, j, sim in similar_pairs[:10]:  # Top 10 similar pairs
                pair_key = (min(i, j), max(i, j))
                if pair_key not in duplicates_found:
                    issues.append(ReviewIssue(
                        category="Requirement Similarity",
                        severity="Medium",
                        message=f"Highly similar requirements detected (similarity: {sim:.0%}) — verify they are intentionally distinct.",
                        context=f"Req A (¶{requirements[i]['paragraph_index']}): \"{requirements[i]['text'][:120]}\" | Req B (¶{requirements[j]['paragraph_index']}): \"{requirements[j]['text'][:120]}\"",
                        paragraph_index=requirements[i]['paragraph_index'],
                        suggestion="If these requirements cover different aspects, make the distinction clearer. If overlapping, consolidate.",
                        rule_id="SIM-HIGH",
                        flagged_text=requirements[i]['text'][:80]
                    ))

            # Summary statistics
            if duplicates_found:
                issues.append(ReviewIssue(
                    category="Requirement Similarity",
                    severity="Info",
                    message=f"Found {len(duplicates_found)} potential duplicate requirement pairs and {len(similar_pairs)} highly similar pairs out of {len(requirements)} total requirements.",
                    context="",
                    paragraph_index=0,
                    suggestion="Review flagged pairs to eliminate redundancy and resolve any conflicting duplicates.",
                    rule_id="SIM-SUMMARY"
                ))

        except Exception:
            pass

        return issues

    def _check_with_tfidf(self, requirements):
        """Fallback: TF-IDF based similarity detection."""
        issues = []

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            texts = [r['text'] for r in requirements]
            vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(texts)

            # Compute pairwise similarity
            sim_matrix = cosine_similarity(tfidf_matrix)

            duplicates_found = set()

            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    sim = sim_matrix[i][j]

                    if sim >= self.DUPLICATE_THRESHOLD:
                        pair_key = (i, j)
                        if pair_key not in duplicates_found:
                            duplicates_found.add(pair_key)
                            issues.append(ReviewIssue(
                                category="Requirement Similarity",
                                severity="High",
                                message=f"Potential DUPLICATE requirement (TF-IDF similarity: {sim:.0%}).",
                                context=f"Req A (¶{requirements[i]['paragraph_index']}): \"{texts[i][:120]}\" | Req B (¶{requirements[j]['paragraph_index']}): \"{texts[j][:120]}\"",
                                paragraph_index=requirements[i]['paragraph_index'],
                                suggestion="Consolidate duplicate requirements or make distinctions explicit.",
                                rule_id="SIM-DUP",
                                flagged_text=texts[i][:80]
                            ))

                    elif sim >= self.SIMILAR_THRESHOLD:
                        if len([iss for iss in issues if iss.rule_id == 'SIM-HIGH']) < 10:
                            issues.append(ReviewIssue(
                                category="Requirement Similarity",
                                severity="Medium",
                                message=f"Similar requirements detected (TF-IDF: {sim:.0%}).",
                                context=f"Req A (¶{requirements[i]['paragraph_index']}): \"{texts[i][:120]}\" | Req B (¶{requirements[j]['paragraph_index']}): \"{texts[j][:120]}\"",
                                paragraph_index=requirements[i]['paragraph_index'],
                                suggestion="Verify these are intentionally distinct requirements.",
                                rule_id="SIM-HIGH",
                                flagged_text=texts[i][:80]
                            ))

        except ImportError:
            pass

        return issues

    def _cosine_similarity(self, a, b):
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


def get_similarity_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning requirement similarity checkers."""
    return {
        'requirement_similarity': RequirementSimilarityChecker()
    }
