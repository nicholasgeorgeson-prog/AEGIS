#!/usr/bin/env python3
"""
YAKE Keyword Extraction Checker v1.0.0
========================================
Uses YAKE (Yet Another Keyword Extractor) for lightweight, unsupervised,
statistical keyword extraction from technical documents.

Unlike model-based extractors (KeyBERT, textacy), YAKE is:
- Extremely fast (no model loading)
- Works offline with no pre-trained models
- Language-independent
- Produces relevance scores for each keyword

This checker:
1. Extracts document keywords and reports them as Info-level issues
2. Detects key terms that appear only once (potential undefined terms)
3. Identifies keyword clusters that may indicate missing section headers
4. Flags documents where extracted keywords don't match expected domain terminology

Falls back to TF-IDF approach when YAKE unavailable.
"""

import re
import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

try:
    from base_checker import BaseChecker, ReviewIssue
except ImportError:
    from .base_checker import BaseChecker, ReviewIssue

__version__ = "1.0.0"

# Expected domain keywords for aerospace/defense technical documents
DOMAIN_KEYWORDS = {
    'system', 'subsystem', 'component', 'interface', 'requirement',
    'design', 'test', 'verification', 'validation', 'performance',
    'safety', 'reliability', 'maintainability', 'configuration',
    'specification', 'compliance', 'standard', 'procedure',
    'document', 'review', 'baseline', 'deliverable', 'milestone',
    'schedule', 'risk', 'quality', 'inspection', 'analysis',
}


class YakeKeywordChecker(BaseChecker):
    """
    Extracts and analyzes document keywords using YAKE.
    """

    CHECKER_NAME = "Keyword Analysis"
    CHECKER_VERSION = "1.0.0"

    MAX_KEYWORDS = 30
    MAX_NGRAM = 3
    DEDUP_THRESHOLD = 0.7
    WINDOW_SIZE = 2

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.yake_available = False
        try:
            import yake
            self.yake = yake
            self.yake_available = True
        except ImportError:
            self.yake = None

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        text = full_text if full_text else "\n".join(t for _, t in paragraphs)

        if len(text.strip()) < 200:
            return issues

        if self.yake_available:
            issues.extend(self._analyze_with_yake(text, paragraphs))
        else:
            issues.extend(self._analyze_with_tfidf(text, paragraphs))

        # Check for domain keyword coverage
        issues.extend(self._check_domain_coverage(text))

        # Check for key term consistency
        issues.extend(self._check_hapax_legomena(text, paragraphs))

        return issues

    def _analyze_with_yake(self, text, paragraphs):
        """Extract and analyze keywords using YAKE."""
        issues = []

        try:
            # Extract keywords for different ngram sizes
            all_keywords = []

            for ngram in range(1, self.MAX_NGRAM + 1):
                extractor = self.yake.KeywordExtractor(
                    lan="en",
                    n=ngram,
                    dedupLim=self.DEDUP_THRESHOLD,
                    dedupFunc='seqm',
                    windowsSize=self.WINDOW_SIZE,
                    top=self.MAX_KEYWORDS
                )
                keywords = extractor.extract_keywords(text[:50000])
                all_keywords.extend(keywords)

            # Sort by relevance (YAKE: lower score = more relevant)
            all_keywords.sort(key=lambda x: x[1])

            # Top keywords as Info-level summary
            if all_keywords:
                top_kws = all_keywords[:15]
                kw_list = ", ".join(f'"{kw}"' for kw, score in top_kws)
                issues.append(ReviewIssue(
                    category="Keyword Analysis",
                    severity="Info",
                    message=f"Document key terms (by relevance): {kw_list}",
                    context="",
                    paragraph_index=0,
                    suggestion="Verify these key terms align with the document's stated purpose and scope.",
                    rule_id="KW-TOP"
                ))

            # Check for keyword distribution across the document
            issues.extend(self._check_keyword_distribution(all_keywords[:20], paragraphs))

        except Exception:
            pass

        return issues

    def _analyze_with_tfidf(self, text, paragraphs):
        """Fallback: basic TF-IDF keyword extraction."""
        issues = []

        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
                      'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
                      'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see',
                      'way', 'who', 'did', 'get', 'let', 'say', 'she', 'too',
                      'use', 'that', 'this', 'with', 'have', 'from', 'they',
                      'been', 'said', 'each', 'which', 'their', 'will', 'other',
                      'about', 'many', 'then', 'them', 'these', 'some', 'would',
                      'make', 'like', 'into', 'could', 'time', 'very', 'when',
                      'what', 'your', 'shall', 'must', 'should'}

        filtered = [w for w in words if w not in stop_words]
        counts = Counter(filtered)

        if counts:
            top_words = counts.most_common(15)
            kw_list = ", ".join(f'"{w}" ({c}×)' for w, c in top_words)
            issues.append(ReviewIssue(
                category="Keyword Analysis",
                severity="Info",
                message=f"Most frequent content terms: {kw_list}",
                context="",
                paragraph_index=0,
                suggestion="Review whether these terms align with the document's purpose.",
                rule_id="KW-FREQ"
            ))

        return issues

    def _check_keyword_distribution(self, keywords, paragraphs):
        """Check if key terms are distributed throughout the document or clustered."""
        issues = []

        if len(paragraphs) < 10:
            return issues

        para_texts = [(idx, text.lower()) for idx, text in paragraphs if not self.is_boilerplate(text)]
        total_paras = len(para_texts)

        if total_paras < 10:
            return issues

        for kw_text, score in keywords[:10]:
            kw_lower = kw_text.lower()
            # Find which paragraphs contain this keyword
            containing_paras = [i for i, (idx, text) in enumerate(para_texts) if kw_lower in text]

            if len(containing_paras) < 2:
                continue

            # Check if keyword is clustered (appears in one section only)
            first_quarter = total_paras // 4
            last_quarter = total_paras * 3 // 4

            in_first = sum(1 for p in containing_paras if p < first_quarter)
            in_last = sum(1 for p in containing_paras if p > last_quarter)
            total_mentions = len(containing_paras)

            if total_mentions >= 5:
                if in_first / total_mentions > 0.8 or in_last / total_mentions > 0.8:
                    issues.append(ReviewIssue(
                        category="Keyword Analysis",
                        severity="Info",
                        message=f"Key term \"{kw_text}\" is clustered in one section ({total_mentions} mentions). If it's a core concept, it may need to be referenced throughout.",
                        context="",
                        paragraph_index=containing_paras[0],
                        suggestion=f"If \"{kw_text}\" is a central document concept, ensure it's introduced early and referenced consistently.",
                        rule_id="KW-CLUSTER",
                        flagged_text=kw_text
                    ))

        return issues

    def _check_domain_coverage(self, text):
        """Check if document contains expected domain terminology."""
        issues = []
        text_lower = text.lower()

        found_domain = set()
        for kw in DOMAIN_KEYWORDS:
            if kw in text_lower:
                found_domain.add(kw)

        coverage = len(found_domain) / len(DOMAIN_KEYWORDS) if DOMAIN_KEYWORDS else 0

        if coverage < 0.15:  # Less than 15% of expected domain terms
            issues.append(ReviewIssue(
                category="Keyword Analysis",
                severity="Low",
                message=f"Low domain keyword coverage ({coverage:.0%}) — document may be missing standard aerospace/defense terminology.",
                context="",
                paragraph_index=0,
                suggestion="Verify the document uses appropriate domain-specific terminology as defined in applicable standards.",
                rule_id="KW-DOMAIN"
            ))

        return issues

    def _check_hapax_legomena(self, text, paragraphs):
        """Check for technical terms that appear only once (may need definition)."""
        issues = []

        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        counts = Counter(words)

        # Find technical-looking words used only once
        hapax = [w for w, c in counts.items() if c == 1 and len(w) > 7]

        # Filter to likely technical terms (contain specific patterns)
        technical_hapax = [
            w for w in hapax
            if any(pat in w for pat in ['tion', 'ment', 'ance', 'ence', 'ity', 'ous', 'ive', 'ical', 'ized'])
        ]

        if len(technical_hapax) > 20:  # Many unique technical terms
            sample = technical_hapax[:8]
            issues.append(ReviewIssue(
                category="Keyword Analysis",
                severity="Info",
                message=f"Document contains {len(technical_hapax)} technical terms used only once. Examples: {', '.join(sample[:5])}",
                context="",
                paragraph_index=0,
                suggestion="Terms used only once may indicate inconsistent terminology or undefined jargon. Consider adding to glossary.",
                rule_id="KW-HAPAX"
            ))

        return issues


def get_yake_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning YAKE keyword checkers."""
    return {
        'keyword_analysis': YakeKeywordChecker()
    }
