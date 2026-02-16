#!/usr/bin/env python3
"""
Vocabulary Richness & Lexical Diversity Checker v1.0.0
======================================================
Uses lexical_diversity library to measure vocabulary richness metrics
and detect copy-paste / boilerplate reuse patterns.

Metrics computed:
- MTLD (Measure of Textual Lexical Diversity) — gold standard metric
- HD-D (Hypergeometric Distribution D) — sample-size independent
- TTR (Type-Token Ratio) — basic vocabulary diversity
- MATTR (Moving-Average TTR) — handles document length variation

In technical writing, these metrics help identify:
1. Sections that are copy-pasted from templates (very low diversity)
2. Overly repetitive language that could be consolidated
3. Sections with unusually high diversity (possible inconsistency)
4. Boilerplate that might not match the current document context

Falls back to manual TTR calculation when library unavailable.
"""

import re
from collections import Counter
from typing import Dict, List, Tuple, Optional

try:
    from base_checker import BaseChecker, ReviewIssue
except ImportError:
    from .base_checker import BaseChecker, ReviewIssue

__version__ = "1.0.0"


class LexicalDiversityChecker(BaseChecker):
    """
    Measures vocabulary richness using multiple lexical diversity metrics.
    Flags sections with unusually low or high diversity.
    """

    CHECKER_NAME = "Lexical Diversity"
    CHECKER_VERSION = "1.0.0"

    # Thresholds for document-level MTLD
    MTLD_LOW = 40    # Below this suggests very repetitive/boilerplate text
    MTLD_HIGH = 120  # Above this is unusual for technical writing

    # TTR thresholds for section-level analysis
    TTR_LOW = 0.20   # Very repetitive section
    TTR_HIGH = 0.70  # Unusually diverse for technical writing

    def __init__(self, enabled=True):
        super().__init__(enabled=enabled)
        self.ld_available = False
        try:
            import lexical_diversity as ld
            self.ld = ld
            self.ld_available = True
        except ImportError:
            self.ld = None

    def check(self, paragraphs, tables=None, full_text="", filepath="", **kwargs):
        issues = []

        text = full_text if full_text else "\n".join(t for _, t in paragraphs)
        words = self._tokenize(text)

        if len(words) < 50:
            return issues  # Too short for meaningful analysis

        # Document-level metrics
        if self.ld_available:
            issues.extend(self._check_document_metrics(words))
        else:
            issues.extend(self._check_basic_ttr(words))

        # Section-level analysis: check each paragraph group
        issues.extend(self._check_section_diversity(paragraphs))

        # Repetition detection
        issues.extend(self._check_word_repetition(words, paragraphs))

        return issues

    def _tokenize(self, text):
        """Tokenize text into words for diversity analysis."""
        # Remove numbers, punctuation, keep only alphabetic words
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        # Remove very common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'shall', 'can',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'as', 'into', 'through', 'during', 'before', 'after', 'and',
                      'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
                      'neither', 'each', 'every', 'all', 'any', 'few', 'more',
                      'most', 'other', 'some', 'such', 'no', 'only', 'own',
                      'same', 'than', 'too', 'very', 'just', 'because', 'if',
                      'when', 'where', 'while', 'that', 'this', 'these', 'those',
                      'it', 'its', 'they', 'them', 'their', 'he', 'she', 'his',
                      'her', 'we', 'our', 'you', 'your'}
        return [w for w in words if w not in stop_words]

    def _check_document_metrics(self, words):
        """Compute document-level lexical diversity metrics."""
        issues = []

        try:
            # MTLD — most reliable metric
            mtld = self.ld.mtld(words)
            if mtld < self.MTLD_LOW:
                issues.append(ReviewIssue(
                    category="Lexical Diversity",
                    severity="Medium",
                    message=f"Low lexical diversity (MTLD: {mtld:.1f}) — document uses very repetitive vocabulary. May contain copy-pasted boilerplate.",
                    context="",
                    paragraph_index=0,
                    suggestion="Review for boilerplate text that may not match the current context. Consider varying word choices where appropriate.",
                    rule_id="LD-MTLD-LOW"
                ))
            elif mtld > self.MTLD_HIGH:
                issues.append(ReviewIssue(
                    category="Lexical Diversity",
                    severity="Info",
                    message=f"High lexical diversity (MTLD: {mtld:.1f}) — unusual for technical writing. Verify consistent terminology.",
                    context="",
                    paragraph_index=0,
                    suggestion="High vocabulary diversity in technical docs may indicate inconsistent terminology. Run terminology consistency check.",
                    rule_id="LD-MTLD-HIGH"
                ))

            # HD-D — sample-size independent
            if len(words) >= 42:  # HD-D needs minimum sample
                hdd = self.ld.hdd(words)
                if hdd < 0.5:
                    issues.append(ReviewIssue(
                        category="Lexical Diversity",
                        severity="Low",
                        message=f"Low HD-D score ({hdd:.2f}) — vocabulary is very limited relative to document length.",
                        context="",
                        paragraph_index=0,
                        suggestion="Consider whether the limited vocabulary serves clarity (good) or indicates boilerplate reuse (needs review).",
                        rule_id="LD-HDD"
                    ))

        except Exception:
            pass

        return issues

    def _check_basic_ttr(self, words):
        """Fallback: basic Type-Token Ratio calculation."""
        issues = []

        if len(words) < 20:
            return issues

        # Use a windowed TTR to handle length dependency
        window = min(100, len(words))
        ttrs = []

        for i in range(0, len(words) - window + 1, window // 2):
            chunk = words[i:i + window]
            ttr = len(set(chunk)) / len(chunk) if chunk else 0
            ttrs.append(ttr)

        if ttrs:
            avg_ttr = sum(ttrs) / len(ttrs)

            if avg_ttr < self.TTR_LOW:
                issues.append(ReviewIssue(
                    category="Lexical Diversity",
                    severity="Medium",
                    message=f"Low vocabulary diversity (avg TTR: {avg_ttr:.2f}) — text is very repetitive.",
                    context="",
                    paragraph_index=0,
                    suggestion="Review for unnecessary repetition. Consider consolidating repeated statements.",
                    rule_id="LD-TTR-LOW"
                ))

        return issues

    def _check_section_diversity(self, paragraphs):
        """Check diversity at the section level to find copy-paste blocks."""
        issues = []

        # Group paragraphs into sections of ~10 paragraphs
        section_size = 10
        sections = []
        current_section = []

        for idx, text in paragraphs:
            if self.is_boilerplate(text):
                continue
            current_section.append((idx, text))
            if len(current_section) >= section_size:
                sections.append(current_section)
                current_section = []

        if current_section and len(current_section) >= 3:
            sections.append(current_section)

        for section in sections:
            section_text = " ".join(t for _, t in section)
            words = self._tokenize(section_text)

            if len(words) < 30:
                continue

            ttr = len(set(words)) / len(words)

            if ttr < 0.15:  # Extremely low — likely template/boilerplate
                first_idx = section[0][0]
                issues.append(ReviewIssue(
                    category="Lexical Diversity",
                    severity="Low",
                    message=f"Section starting at paragraph {first_idx} has extremely low vocabulary diversity (TTR: {ttr:.2f}) — possible boilerplate or template text.",
                    context=section[0][1][:150],
                    paragraph_index=first_idx,
                    suggestion="Verify this section is customized for the current document and not unchanged boilerplate.",
                    rule_id="LD-SECT"
                ))

        return issues

    def _check_word_repetition(self, words, paragraphs):
        """Detect excessively repeated words."""
        issues = []

        if len(words) < 100:
            return issues

        word_counts = Counter(words)
        total = len(words)

        for word, count in word_counts.most_common(20):
            frequency = count / total

            # Flag words used more than 3% of all content words (very high)
            if frequency > 0.03 and count >= 10 and len(word) > 4:
                issues.append(ReviewIssue(
                    category="Lexical Diversity",
                    severity="Info",
                    message=f"Word \"{word}\" appears {count} times ({frequency:.1%} of content) — consider if synonyms or pronouns could reduce repetition.",
                    context="",
                    paragraph_index=0,
                    suggestion=f"The word \"{word}\" is used very frequently. Some repetition is expected in technical writing, but verify it's intentional.",
                    rule_id="LD-REP",
                    flagged_text=word
                ))

        return issues


def get_vocabulary_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning vocabulary/lexical diversity checkers."""
    return {
        'lexical_diversity': LexicalDiversityChecker()
    }
