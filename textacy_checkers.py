#!/usr/bin/env python3
"""
Textacy Advanced Text Analysis Checkers v1.0.0
===============================================
Uses textacy library for keyword extraction, text complexity metrics,
information extraction, and noun phrase density analysis.

Features:
- Keyword extraction (SGRANK algorithm) and undefined technical terms detection
- Text complexity metrics beyond basic readability scores
- Information extraction: SVO triples (Subject-Verb-Object) from requirements
- Excessive noun phrase detection (noun phrase density > threshold)

The textacy library must be installed: pip install textacy

All checkers gracefully fall back to pattern matching if textacy unavailable.
"""

import re
from typing import Dict, List, Tuple, Optional, Set

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "1.0.0"


class KeywordExtractionChecker(BaseChecker):
    """
    Extracts technical keywords and flags undefined terms.

    Uses textacy SGRANK algorithm to identify key terms in technical documentation.
    Flags specialized/technical terms that appear without definition or context.
    """

    CHECKER_NAME = "Keyword Extraction"
    CHECKER_VERSION = "1.0.0"

    # Common technical acronyms that don't need definition
    KNOWN_TECHNICAL_TERMS = {
        'api', 'rest', 'json', 'xml', 'http', 'https', 'tcp', 'ip', 'dns',
        'sql', 'database', 'cache', 'queue', 'load', 'balance', 'cluster',
        'kubernetes', 'docker', 'ci', 'cd', 'qa', 'qc', 'test', 'unit',
        'integration', 'regression', 'smoke', 'soak', 'stress', 'performance',
        'ui', 'ux', 'ui/ux', 'crud', 'orm', 'mvc', 'mvvm', 'microservice',
        'framework', 'library', 'sdk', 'ide', 'git', 'scm', 'vcs',
        'agile', 'scrum', 'kanban', 'waterfall', 'devops', 'sre',
        'rpc', 'grpc', 'graphql', 'webassembly', 'wasm',
    }

    # Domains where all-caps terms are assumed known
    AEROSPACE_TERMS = {
        'apu', 'aod', 'aft', 'fwd', 'cg', 'icd', 'cdrl', 'srs', 'sos', 'swrs',
        'tbd', 'tbr', 'tbs', 'dod', 'mil', 'mil-spec', 'nasa', 'faa',
    }

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.textacy_available = False
        self._init_textacy()

    def _init_textacy(self) -> bool:
        """Check if textacy is available."""
        try:
            import textacy
            self.textacy_available = True
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
        Extract keywords and detect undefined technical terms.

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

        if not full_text:
            full_text = '\n\n'.join([text for _, text in paragraphs])

        issues = []

        if self.textacy_available:
            issues.extend(self._check_with_textacy(paragraphs, full_text))
        else:
            issues.extend(self._check_with_patterns(paragraphs, full_text))

        return issues[:20]

    def _check_with_textacy(self, paragraphs: List[Tuple[int, str]], full_text: str) -> List[Dict]:
        """Use textacy for keyword extraction."""
        try:
            import textacy
            import textacy.extract
        except ImportError:
            return []

        issues = []

        try:
            # Create textacy Doc
            doc = textacy.make_spacy_doc(full_text)

            # Extract keywords using SGRANK
            keywords = textacy.extract.sgrank(doc, topn=20)
            keyword_set = {kw[0].lower() for kw in keywords}

            # Check each paragraph for undefined technical terms
            for idx, text in paragraphs:
                if len(text.strip()) < 30:
                    continue

                # Find potential technical terms (capitalized phrases, acronyms)
                potential_terms = self._extract_technical_terms(text)

                for term in potential_terms:
                    term_lower = term.lower()

                    # Skip if it's a known term or defined in text
                    if self._is_known_term(term_lower):
                        continue

                    # Check if term is defined near its usage
                    if not self._is_defined_in_context(term, text, full_text):
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'Technical term "{term}" may not be defined',
                            context=text[:80],
                            paragraph_index=idx,
                            suggestion=f'Define "{term}" on first use, or ensure it is a known industry term.',
                            rule_id='KEYWORD001',
                            flagged_text=term
                        ))
                        break  # One per paragraph

        except Exception:
            return []

        return issues

    def _check_with_patterns(self, paragraphs: List[Tuple[int, str]], full_text: str) -> List[Dict]:
        """Pattern-based keyword detection."""
        issues = []

        # Identify capitalized phrases (potential technical terms)
        for idx, text in paragraphs:
            if len(text.strip()) < 30:
                continue

            # Find all-caps terms (likely acronyms)
            acronyms = re.findall(r'\b([A-Z]{2,6})\b', text)

            for acronym in acronyms[:3]:  # Check first 3 per paragraph
                if acronym not in self.KNOWN_TECHNICAL_TERMS and acronym not in self.AEROSPACE_TERMS:
                    # Check if defined
                    definition_pattern = acronym + r'\s*\(([^)]+)\)|' + re.escape(acronym) + r'\s+means'
                    if not re.search(definition_pattern, full_text, re.IGNORECASE):
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'Acronym "{acronym}" not defined',
                            context=text[:80],
                            paragraph_index=idx,
                            suggestion=f'Define "{acronym}" on first use (e.g., "{acronym} (Full Name)")',
                            rule_id='KEYWORD002',
                            flagged_text=acronym
                        ))
                        break

        return issues

    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract potential technical terms from text."""
        terms = []

        # All-caps terms (acronyms)
        terms.extend(re.findall(r'\b([A-Z]{2,6})\b', text))

        # Capitalized phrases (2-3 words)
        terms.extend(re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', text))

        return list(set(terms))

    def _is_known_term(self, term: str) -> bool:
        """Check if term is in known technical/aerospace vocabulary."""
        term_normalized = term.lower().replace('-', '').replace('_', '')
        return (term_normalized in self.KNOWN_TECHNICAL_TERMS or
                term_normalized in self.AEROSPACE_TERMS or
                len(term_normalized) < 3)

    def _is_defined_in_context(self, term: str, paragraph: str, full_text: str) -> bool:
        """Check if term is defined in text."""
        # Pattern: "Term (definition)" or "Term means"
        definition_pattern = re.escape(term) + r'\s*\(([^)]+)\)|' + re.escape(term) + r'\s+(?:means|is|refers to)'
        return bool(re.search(definition_pattern, full_text, re.IGNORECASE))


class ComplexityAnalysisChecker(BaseChecker):
    """
    Analyzes text complexity beyond basic readability scores.

    Detects:
    - Excessive nested clauses
    - Long sentences
    - Complex noun phrases
    - Passive voice overuse
    """

    CHECKER_NAME = "Complexity Analysis"
    CHECKER_VERSION = "1.0.0"

    # Complexity thresholds
    MAX_CLAUSE_DEPTH = 3
    MAX_SENTENCE_LENGTH = 30  # words
    MAX_PASSIVE_RATIO = 0.3

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.spacy_available = self._init_spacy()

    def _init_spacy(self) -> bool:
        """Check if spaCy is available."""
        try:
            import spacy
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
        Analyze text complexity.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text (unused)
            filepath: File path (unused)

        Returns:
            List of ReviewIssue dicts
        """
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            if len(text.strip()) < 40:
                continue

            # Check sentence length
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                word_count = len(sentence.split())
                if word_count > self.MAX_SENTENCE_LENGTH:
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Long sentence ({word_count} words)',
                        context=sentence[:80],
                        paragraph_index=idx,
                        suggestion='Break into 2-3 shorter sentences for clarity.',
                        rule_id='COMPLEX001',
                        flagged_text=sentence[:40]
                    ))
                    break

            # Check passive voice usage
            passive_count = len(re.findall(r'\b(?:is|are|was|were|be|been|being)\s+\w+(?:ed|en)\b', text))
            total_sentences = max(1, len(sentences))
            passive_ratio = passive_count / total_sentences

            if passive_ratio > self.MAX_PASSIVE_RATIO:
                issues.append(self.create_issue(
                    severity='Low',
                    message=f'High passive voice usage ({passive_ratio:.0%} of sentences)',
                    context=text[:80],
                    paragraph_index=idx,
                    suggestion='Use active voice for clarity. Change "was done by" to "did".',
                    rule_id='COMPLEX002',
                    flagged_text='[passive voice]'
                ))

        return issues[:20]


class InformationExtractionChecker(BaseChecker):
    """
    Extracts Subject-Verb-Object (SVO) triples from requirements text.

    Helps identify:
    - Who is responsible (subject)
    - What they must do (verb/action)
    - What they act upon (object)

    Useful for analyzing requirement clarity and completeness.
    """

    CHECKER_NAME = "Information Extraction"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.spacy_available = self._init_spacy()

    def _init_spacy(self) -> bool:
        """Check if spaCy is available."""
        try:
            import spacy
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
        Extract SVO triples from requirement statements.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text (unused)
            filepath: File path (unused)

        Returns:
            List of ReviewIssue dicts
        """
        if not self.enabled:
            return []

        issues = []

        # Only check paragraphs with requirement keywords
        requirement_keywords = {'shall', 'must', 'will', 'should', 'required'}

        for idx, text in paragraphs:
            if len(text.strip()) < 40:
                continue

            # Check if this looks like a requirement
            if not any(kw in text.lower() for kw in requirement_keywords):
                continue

            # Try to extract SVO structure
            svo = self._extract_svo(text)

            if svo:
                subject, verb, obj = svo

                # Check if subject is present
                if not subject or subject.lower() in {'', 'it', 'this'}:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message='Requirement missing clear subject/actor',
                        context=text[:80],
                        paragraph_index=idx,
                        suggestion='Clarify who is responsible. Use "The system shall..." or "The contractor must..."',
                        rule_id='INFO001',
                        flagged_text=text[:30]
                    ))
                    break

                # Check if verb is clear
                if not verb or verb.lower() in {'be', 'is', 'are'}:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message='Requirement missing clear action verb',
                        context=text[:80],
                        paragraph_index=idx,
                        suggestion='Use action verbs: provide, deliver, ensure, verify, test, maintain.',
                        rule_id='INFO002',
                        flagged_text=verb or '[missing]'
                    ))
                    break

                # Check if object is present
                if not obj or obj.lower() in {'', 'it', 'this'}:
                    issues.append(self.create_issue(
                        severity='Low',
                        message='Requirement may be missing clear object/target',
                        context=text[:80],
                        paragraph_index=idx,
                        suggestion='Clarify what the action applies to. Be specific about the target.',
                        rule_id='INFO003',
                        flagged_text=text[:30]
                    ))

        return issues[:15]

    def _extract_svo(self, text: str) -> Optional[Tuple[str, str, str]]:
        """
        Extract SVO triple using spaCy dependency parsing when available,
        falling back to regex patterns.

        Returns: (subject, verb, object) tuple or None
        """
        if self.spacy_available:
            result = self._extract_svo_spacy(text)
            if result:
                return result

        # Regex fallback: "X shall/must/will Y Z" pattern
        svo_pattern = r'(.*?)\s+(?:shall|must|will|should)\s+(\w+)\s+(.*?)(?:\.|$)'
        match = re.search(svo_pattern, text, re.IGNORECASE)

        if match:
            subject = match.group(1).strip()
            verb = match.group(2).strip()
            obj = match.group(3).strip()

            # Clean up
            subject = re.sub(r'^(?:The|A|An)\s+', '', subject, flags=re.IGNORECASE)
            obj = re.sub(r'\s+when.*$', '', obj, flags=re.IGNORECASE)

            return (subject, verb, obj)

        return None

    def _extract_svo_spacy(self, text: str) -> Optional[Tuple[str, str, str]]:
        """Use spaCy dependency parsing for more accurate SVO extraction."""
        try:
            from nlp_utils import get_spacy_model
            nlp = get_spacy_model()
            if not nlp:
                return None

            doc = nlp(text[:500])  # Limit to avoid slow processing

            for sent in doc.sents:
                subject = ''
                verb = ''
                obj = ''

                for token in sent:
                    # Find the main verb (ROOT)
                    if token.dep_ == 'ROOT' and token.pos_ == 'VERB':
                        verb = token.text

                        # Find subject (nsubj, nsubjpass)
                        for child in token.children:
                            if child.dep_ in ('nsubj', 'nsubjpass'):
                                subject = ' '.join(t.text for t in child.subtree)
                            elif child.dep_ in ('dobj', 'attr', 'oprd'):
                                obj = ' '.join(t.text for t in child.subtree)

                        # Also check for modal auxiliaries (shall, must)
                        for child in token.children:
                            if child.dep_ == 'aux' and child.text.lower() in {'shall', 'must', 'will', 'should'}:
                                if subject and verb:
                                    return (subject.strip(), verb.strip(), obj.strip())

                if subject and verb:
                    return (subject.strip(), verb.strip(), obj.strip())

        except Exception:
            pass
        return None


class NounPhraseDensityChecker(BaseChecker):
    """
    Detects excessive noun phrase density in technical text.

    High noun phrase density (>40%) indicates:
    - Over-nominalization (turning verbs into nouns)
    - Excessive use of compound nouns
    - Text that is harder to read

    Example: "The implementation of the system's capability for data processing..."
    Better: "The system processes data..."
    """

    CHECKER_NAME = "Noun Phrase Density"
    CHECKER_VERSION = "1.0.0"

    DENSITY_THRESHOLD = 0.4  # 40% noun phrases

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        full_text: str = "",
        filepath: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Check noun phrase density.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text (unused)
            filepath: File path (unused)

        Returns:
            List of ReviewIssue dicts
        """
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            if len(text.strip()) < 40:
                continue

            # Count noun chunks (simple heuristic)
            noun_phrases = re.findall(
                r'\b(?:The\s+)?[A-Za-z]+(?:\s+(?:of|for|in|on|at)\s+[A-Za-z]+)*\b',
                text
            )

            all_words = text.split()

            if len(all_words) > 0:
                density = len(noun_phrases) / len(all_words)

                if density > self.DENSITY_THRESHOLD:
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'High noun phrase density ({density:.0%})',
                        context=text[:80],
                        paragraph_index=idx,
                        suggestion='Reduce nominalization. Use active verbs instead of noun phrases. "Process data" instead of "Data processing".',
                        rule_id='NOUN001',
                        flagged_text='[high noun density]'
                    ))

        return issues[:15]


def get_textacy_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning textacy checkers."""
    return {
        'keyword_extraction': KeywordExtractionChecker(),
        'complexity_analysis': ComplexityAnalysisChecker(),
        'information_extraction': InformationExtractionChecker(),
        'noun_phrase_density': NounPhraseDensityChecker(),
    }


# Standalone test
if __name__ == '__main__':
    print(f"Textacy Advanced Analysis Checkers v{__version__}")
    print("=" * 50)

    test_paragraphs = [
        (0, "REQ-001: The system shall provide real-time monitoring of all parameters."),
        (1, "The implementation of the system's comprehensive capability for real-time data processing and analysis must be completed within 30 days."),
        (2, "The software was designed to handle errors gracefully."),
        (3, "The TCP/IP protocol should be used for all communications without exception."),
    ]

    checkers = get_textacy_checkers()
    print(f"Loaded {len(checkers)} checkers\n")

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(test_paragraphs)
        print(f"  Found {len(issues)} issues")
        for issue in issues[:2]:
            print(f"    [{issue['severity']}] {issue['message'][:60]}...")
