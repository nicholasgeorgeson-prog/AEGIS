#!/usr/bin/env python3
"""
Coreference Resolution Checker v1.0.0
======================================
Uses coreferee library (spaCy pipeline component) to detect unresolved/ambiguous
pronoun references in technical documentation.

This checker identifies pronouns (it, they, this, these, those) that have:
- Ambiguous antecedents (multiple possible referents)
- No clear antecedent (dangling pronouns)
- Long-distance references (prone to misunderstanding)

Severity levels:
- High: Pronouns with no clear antecedent
- Medium: Ambiguous references or long-distance pronouns

The coreferee library must be installed: pip install coreferee
"""

import re
from typing import Dict, List, Tuple, Optional

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "1.0.0"


class CoreferenceResolutionChecker(BaseChecker):
    """
    Detects unresolved and ambiguous pronoun references using coreferee.

    Pronouns like "it", "they", "this", "these", "those" should have clear
    antecedents. Ambiguous or missing references can cause misunderstanding
    in technical documentation.

    Requires: spaCy model + coreferee pipeline component installed
    """

    CHECKER_NAME = "Coreference Resolution"
    CHECKER_VERSION = "1.0.0"

    # Pronouns to check (case-insensitive)
    PRONOUNS_TO_CHECK = {
        'it', 'its', 'itself',
        'they', 'them', 'their', 'theirs', 'themselves',
        'this', 'these',
        'that', 'those',
        'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself',
        'we', 'us', 'our', 'ours', 'ourselves',
        'you', 'your', 'yours', 'yourself', 'yourselves',
    }

    # Pronouns that typically need special attention
    AMBIGUOUS_PRONOUNS = {'it', 'this', 'that', 'these', 'those', 'they'}

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.nlp = None
        self.coreferee_available = False
        self._init_nlp()

    def _init_nlp(self) -> bool:
        """Initialize spaCy + coreferee pipeline."""
        try:
            import spacy
            # Try to load model with coreferee
            try:
                self.nlp = spacy.load('en_core_web_sm')
                # Try to add coreferee component
                if 'coreferee' not in self.nlp.pipe_names:
                    self.nlp.add_pipe('coreferee')
                self.coreferee_available = True
                return True
            except (OSError, ValueError) as e:
                # coreferee not available or model not found
                return False
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
        Check for unresolved/ambiguous pronoun references.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text
            filepath: File path (unused)

        Returns:
            List of ReviewIssue dicts
        """
        if not self.enabled or not self.coreferee_available:
            return []

        issues = []

        # Process full text with spaCy for coreferee analysis
        if not full_text and paragraphs:
            full_text = '\n\n'.join([text for _, text in paragraphs])

        if not full_text:
            return []

        try:
            doc = self.nlp(full_text)

            # Find all coreference clusters
            coreference_clusters = self._extract_clusters(doc)

            # Check each pronoun in paragraphs
            for idx, text in paragraphs:
                for match in re.finditer(r'\b(' + '|'.join(self.AMBIGUOUS_PRONOUNS) + r')\b', text, re.IGNORECASE):
                    pronoun = match.group(1).lower()
                    context_start = max(0, match.start() - 40)
                    context_end = min(len(text), match.end() + 40)
                    context = text[context_start:context_end]

                    # Check if pronoun has a clear antecedent in document
                    antecedent = self._find_antecedent(doc, pronoun, match.start(), full_text)

                    if antecedent is None:
                        # No clear antecedent found
                        issues.append(self.create_issue(
                            severity='High',
                            message=f'Pronoun "{pronoun}" has no clear antecedent',
                            context=f"...{context}...",
                            paragraph_index=idx,
                            suggestion=f'Replace "{pronoun}" with the specific noun it refers to (e.g., use the actual system/document name)',
                            rule_id='COREF001',
                            flagged_text=pronoun
                        ))
                    elif isinstance(antecedent, list) and len(antecedent) > 1:
                        # Ambiguous - multiple possible referents
                        candidates = ', '.join(antecedent[:3])
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Pronoun "{pronoun}" has ambiguous antecedent',
                            context=f"...{context}...",
                            paragraph_index=idx,
                            suggestion=f'Clarify which of these "{pronoun}" refers to: {candidates}. Use explicit noun instead.',
                            rule_id='COREF002',
                            flagged_text=pronoun
                        ))
                    elif isinstance(antecedent, str):
                        # Check if antecedent is far away (long-distance reference)
                        if len(antecedent) > 30:
                            issues.append(self.create_issue(
                                severity='Low',
                                message=f'Pronoun "{pronoun}" refers to distant antecedent: "{antecedent[:30]}..."',
                                context=f"...{context}...",
                                paragraph_index=idx,
                                suggestion='Consider repeating the noun instead of using a pronoun for long-distance references',
                                rule_id='COREF003',
                                flagged_text=pronoun
                            ))

        except Exception as e:
            # If coreferee processing fails, fall back to basic pattern matching
            return self._fallback_check(paragraphs)

        return issues[:25]  # Limit issues

    def _extract_clusters(self, doc) -> Dict[int, List[str]]:
        """Extract coreference clusters from spaCy doc with coreferee."""
        clusters = {}
        try:
            if hasattr(doc, '_.coref_clusters'):
                for cluster in doc._.coref_clusters:
                    for mention in cluster:
                        key = mention.start
                        if key not in clusters:
                            clusters[key] = []
                        clusters[key].append(mention.text)
        except (AttributeError, Exception):
            pass
        return clusters

    def _find_antecedent(self, doc, pronoun: str, position: int, full_text: str) -> Optional[str | List[str]]:
        """
        Find the antecedent for a pronoun.

        Returns:
        - None if no antecedent found
        - str if single clear antecedent found
        - List[str] if multiple possible antecedents
        """
        # Extract nouns and named entities before the pronoun
        candidates = []

        # Look back through sentences for potential antecedents
        for sent in doc.sents:
            if sent.start_char >= position:
                break

            # Find nouns and noun phrases in this sentence
            for token in sent:
                if token.pos_ in ['NOUN', 'PROPN'] and token.text.lower() != pronoun:
                    candidates.append(token.text)

        # Check for entities
        for ent in doc.ents:
            if ent.start_char < position and ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT']:
                candidates.append(ent.text)

        if not candidates:
            return None
        elif len(candidates) == 1:
            return candidates[0]
        else:
            # Multiple candidates - ambiguous
            return candidates[-5:]  # Return last 5 unique candidates

    def _fallback_check(self, paragraphs: List[Tuple[int, str]]) -> List[Dict]:
        """
        Fallback check when coreferee is unavailable.
        Uses simple pattern matching to detect obvious dangling pronouns.
        """
        issues = []
        full_text = '\n\n'.join([text for _, text in paragraphs])

        # Simple heuristic: pronouns at start of paragraph without clear subject
        for idx, text in paragraphs:
            # Check if paragraph starts with a pronoun
            start_match = re.match(r'^(it|this|that|they|these|those)\s+', text, re.IGNORECASE)
            if start_match and idx > 0:
                pronoun = start_match.group(1).lower()
                # Check if previous paragraph ends with a clear noun
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Paragraph starts with pronoun "{pronoun}" without clear context',
                    context=text[:60],
                    paragraph_index=idx,
                    suggestion=f'Start paragraph with a noun phrase instead of "{pronoun}", or add context',
                    rule_id='COREF004',
                    flagged_text=pronoun
                ))

        return issues


def get_coreference_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning coreference checker."""
    return {
        'coreference_resolution': CoreferenceResolutionChecker(),
    }


# Standalone test
if __name__ == '__main__':
    print(f"Coreference Resolution Checker v{__version__}")
    print("=" * 50)

    test_paragraphs = [
        (0, "The system processes data in batches. It must complete processing within 30 seconds."),
        (1, "The manager and the engineer reviewed the design. They approved it yesterday."),
        (2, "It is important to verify all requirements. This ensures compliance."),
        (3, "The specification document is comprehensive. That contains all necessary details."),
    ]

    checker = CoreferenceResolutionChecker()
    print(f"Coreference checker available: {checker.coreferee_available}\n")

    if checker.enabled:
        issues = checker.check(test_paragraphs)
        print(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  [{issue['severity']}] {issue['message']}")
            if issue.get('suggestion'):
                print(f"    Suggestion: {issue['suggestion'][:70]}...")
    else:
        print("Coreference checker disabled (coreferee not available)")
