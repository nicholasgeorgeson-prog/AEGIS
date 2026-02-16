#!/usr/bin/env python3
"""
Summarization and Verbosity Checker v1.0.0
===========================================
Uses sumy library to detect verbose, low-information-density, and repetitive sections.

Detects:
- Paragraphs with low information density (filler/padding)
- Repetitive sections (saying same thing multiple ways)
- Overly verbose documentation (when compared to summary)
- Redundant explanations

The sumy library must be installed: pip install sumy

For documents with >20 paragraphs, generates a 5-sentence extractive summary
and identifies paragraphs with significantly lower information density.
"""

import re
from typing import Dict, List, Tuple, Optional, Set

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "1.0.0"


class VerbosityDetectionChecker(BaseChecker):
    """
    Detects verbose, redundant, and low-information-density paragraphs.

    Uses lexical analysis and simple heuristics to identify:
    - Filler/padding content
    - Repetitive phrases and concepts
    - Overly wordy explanations
    - Information that could be condensed

    Works with or without sumy library (uses heuristic fallback).
    """

    CHECKER_NAME = "Verbosity Detection"
    CHECKER_VERSION = "1.0.0"

    # Common filler phrases and padding
    FILLER_PHRASES = {
        'it is important to note that',
        'it is worth noting that',
        'it should be mentioned that',
        'it is clear that',
        'it is obvious that',
        'as we have seen',
        'as mentioned above',
        'as previously stated',
        'as we discussed',
        'in fact',
        'in reality',
        'in conclusion',
        'to summarize',
        'in summary',
        'in a nutshell',
        'it goes without saying that',
        'needless to say',
        'generally speaking',
        'more or less',
        'to some extent',
        'all in all',
        'by and large',
        'for the most part',
        'on the whole',
    }

    # Weak/filler words
    WEAK_WORDS = {
        'very', 'quite', 'rather', 'somewhat', 'really', 'basically',
        'basically', 'essentially', 'actually', 'apparently', 'supposedly',
        'arguably', 'virtually', 'apparently', 'allegedly',
    }

    MIN_DOC_PARAGRAPHS = 10  # Only check docs with >10 paragraphs

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.sumy_available = False
        self._init_sumy()

    def _init_sumy(self) -> bool:
        """Check if sumy is available."""
        try:
            from sumy.summarizers.text_rank import TextRankSummarizer
            from sumy.nlp.tokenizer import Tokenizer
            self.sumy_available = True
            return True
        except ImportError:
            return False

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        full_text: str = "",
        filepath: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Check for verbose and redundant paragraphs.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text
            filepath: File path (unused)

        Returns:
            List of ReviewIssue dicts
        """
        if not self.enabled:
            return []

        # Skip small documents
        if len(paragraphs) < self.MIN_DOC_PARAGRAPHS:
            return []

        issues = []

        # Get full text
        if not full_text:
            full_text = '\n\n'.join([text for _, text in paragraphs])

        # Check for verbosity and filler
        issues.extend(self._check_filler_content(paragraphs))

        # Check for repetition
        issues.extend(self._check_repetition(paragraphs, full_text))

        # If sumy available, do deeper analysis
        if self.sumy_available:
            issues.extend(self._check_with_summary(paragraphs, full_text))

        return issues[:25]  # Limit issues

    def _check_filler_content(self, paragraphs: List[Tuple[int, str]]) -> List[Dict]:
        """Detect filler phrases and weak language."""
        issues = []

        for idx, text in paragraphs:
            if len(text.strip()) < 30:
                continue

            text_lower = text.lower()

            # Count filler phrases in this paragraph
            filler_count = 0
            for phrase in self.FILLER_PHRASES:
                if phrase in text_lower:
                    filler_count += 1

            if filler_count >= 2:
                # Paragraph is heavily padded
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Paragraph contains {filler_count} filler phrases',
                    context=text[:80],
                    paragraph_index=idx,
                    suggestion='Remove filler phrases and state content directly. Be concise.',
                    rule_id='VERB001',
                    flagged_text='[multiple filler phrases]'
                ))
            elif filler_count == 1:
                # Find and report the specific phrase
                for phrase in self.FILLER_PHRASES:
                    if phrase in text_lower:
                        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                        match = pattern.search(text)
                        if match:
                            issues.append(self.create_issue(
                                severity='Low',
                                message=f'Filler phrase: "{match.group()}"',
                                context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                                paragraph_index=idx,
                                suggestion='Remove this phrase and state content directly.',
                                rule_id='VERB002',
                                flagged_text=match.group()
                            ))
                        break

            # Count weak words (general verbosity indicator)
            weak_word_count = 0
            for word in self.WEAK_WORDS:
                if re.search(r'\b' + word + r'\b', text_lower):
                    weak_word_count += 1

            if weak_word_count >= 3:
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Paragraph uses {weak_word_count} weak/filler words',
                    context=text[:80],
                    paragraph_index=idx,
                    suggestion='Replace weak words with stronger, more specific language.',
                    rule_id='VERB003',
                    flagged_text='[weak words]'
                ))

        return issues

    def _check_repetition(self, paragraphs: List[Tuple[int, str]], full_text: str) -> List[Dict]:
        """Detect repeated concepts and phrases."""
        issues = []

        # Extract key phrases from each paragraph
        phrase_map: Dict[str, List[int]] = {}

        for idx, text in paragraphs:
            if len(text.strip()) < 40:
                continue

            # Extract 2-3 word phrases (simple noun phrases)
            phrases = self._extract_key_phrases(text)

            for phrase in phrases:
                if phrase not in phrase_map:
                    phrase_map[phrase] = []
                phrase_map[phrase].append(idx)

        # Find phrases repeated across multiple paragraphs
        for phrase, indices in phrase_map.items():
            if len(indices) >= 3:
                # This phrase appears in 3+ paragraphs
                para_text = paragraphs[indices[0]][1][:80]
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Concept "{phrase}" repeated in {len(indices)} paragraphs',
                    context=para_text,
                    paragraph_index=indices[0],
                    suggestion='Consolidate repeated concept into a single explanation or define once and reference.',
                    rule_id='VERB004',
                    flagged_text=phrase
                ))
                break  # Report one repetition per check pass

        return issues

    def _check_with_summary(self, paragraphs: List[Tuple[int, str]], full_text: str) -> List[Dict]:
        """Use sumy to generate summary and detect low-density paragraphs."""
        try:
            from sumy.summarizers.text_rank import TextRankSummarizer
            from sumy.nlp.tokenizer import Tokenizer
            from sumy.nlp.stemmer import Stemmer
            from sumy.utils import get_stop_words
        except ImportError:
            return []

        issues = []

        try:
            # Create summarizer
            language = 'english'
            stemmer = Stemmer(language)
            summarizer = TextRankSummarizer(stemmer)

            # Generate summary (5 sentences)
            from sumy.parser.plaintext import PlaintextParser
            parser = PlaintextParser.from_string(full_text, Tokenizer(language))
            summary_sentences = summarizer(parser.document, sentences_count=5)

            # Get key terms from summary
            summary_text = ' '.join([str(s) for s in summary_sentences])
            summary_terms = self._extract_key_phrases(summary_text, min_length=3)
            summary_set = set(summary_terms)

            # Score each paragraph by coverage of summary terms
            for idx, text in paragraphs:
                if len(text.strip()) < 50:
                    continue

                para_terms = set(self._extract_key_phrases(text, min_length=3))
                coverage = len(para_terms & summary_set) / (len(para_terms) + 1)

                # Low coverage = low information density
                if coverage < 0.15 and len(para_terms) > 5:
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Paragraph has low information density ({coverage:.0%} coverage)',
                        context=text[:80],
                        paragraph_index=idx,
                        suggestion='This paragraph adds little information. Consider removing or consolidating with adjacent sections.',
                        rule_id='VERB005',
                        flagged_text='[low density]'
                    ))
                    break  # Report one low-density per check pass

        except Exception:
            # If sumy processing fails, continue
            pass

        return issues

    def _extract_key_phrases(self, text: str, min_length: int = 2) -> List[str]:
        """
        Extract key phrases (multi-word terms) from text.

        Simple approach: noun phrase approximation using word patterns.
        """
        phrases = []

        # Simple n-gram approach (2-3 word phrases)
        words = re.findall(r'\b[a-z]+\b', text.lower())

        for i in range(len(words) - min_length + 1):
            phrase = ' '.join(words[i:i + min_length])
            # Skip if contains stop words
            if not self._is_stop_phrase(phrase):
                phrases.append(phrase)

        return phrases

    def _is_stop_phrase(self, phrase: str) -> bool:
        """Check if phrase contains only stop words."""
        stop_words = {'a', 'the', 'and', 'or', 'but', 'in', 'is', 'to', 'of', 'that',
                     'this', 'be', 'as', 'for', 'on', 'with', 'by', 'are', 'was'}
        words = phrase.split()
        return all(w in stop_words for w in words)


class DocumentSummarizationChecker(BaseChecker):
    """
    Generates summaries of long documents to assess content coverage.

    For documents with >20 paragraphs, generates a 5-sentence extractive summary
    and reports it as an Info-level finding for manual review.
    """

    CHECKER_NAME = "Document Summarization"
    CHECKER_VERSION = "1.0.0"

    MIN_DOC_PARAGRAPHS = 20
    SUMMARY_SENTENCES = 5

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.sumy_available = False
        self._init_sumy()

    def _init_sumy(self) -> bool:
        """Check if sumy is available."""
        try:
            from sumy.summarizers.text_rank import TextRankSummarizer
            from sumy.nlp.tokenizer import Tokenizer
            self.sumy_available = True
            return True
        except ImportError:
            return False

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        full_text: str = "",
        filepath: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Generate summary for long documents.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text
            filepath: File path (unused)

        Returns:
            List with single Info-level summary issue (if applicable)
        """
        if not self.enabled or not self.sumy_available:
            return []

        # Only process long documents
        if len(paragraphs) < self.MIN_DOC_PARAGRAPHS:
            return []

        if not full_text:
            full_text = '\n\n'.join([text for _, text in paragraphs])

        try:
            from sumy.summarizers.text_rank import TextRankSummarizer
            from sumy.nlp.tokenizer import Tokenizer
            from sumy.nlp.stemmer import Stemmer
            from sumy.parser.plaintext import PlaintextParser

            language = 'english'
            stemmer = Stemmer(language)
            summarizer = TextRankSummarizer(stemmer)

            parser = PlaintextParser.from_string(full_text, Tokenizer(language))
            summary_sentences = summarizer(parser.document, sentences_count=self.SUMMARY_SENTENCES)

            summary_text = ' '.join([str(s) for s in summary_sentences])

            return [self.create_issue(
                severity='Info',
                message=f'Document summary ({len(paragraphs)} paragraphs)',
                context=summary_text[:150],
                paragraph_index=0,
                suggestion='Review this summary to ensure main points are covered. If key information is missing, consider reorganizing.',
                rule_id='SUMM001',
                flagged_text=summary_text
            )]

        except Exception:
            return []


def get_summarization_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning summarization checkers."""
    return {
        'verbosity_detection': VerbosityDetectionChecker(),
        'document_summarization': DocumentSummarizationChecker(),
    }


# Standalone test
if __name__ == '__main__':
    print(f"Summarization & Verbosity Checker v{__version__}")
    print("=" * 50)

    test_paragraphs = [
        (0, "As mentioned above, it is important to note that the system processes data efficiently."),
        (1, "It is worth noting that data processing is a critical function."),
        (2, "Processing of data should be done carefully. Data must be validated."),
        (3, "The system handles errors gracefully through comprehensive error handling mechanisms."),
        (4, "Error handling is also important for system reliability."),
    ] + [(i, f"Paragraph {i}: Additional content for testing.") for i in range(5, 25)]

    checker = VerbosityDetectionChecker()
    print(f"Sumy available: {checker.sumy_available}\n")

    issues = checker.check(test_paragraphs)
    print(f"Found {len(issues)} verbosity issues:")
    for issue in issues[:5]:
        print(f"  [{issue['severity']}] {issue['message']}")
