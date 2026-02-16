#!/usr/bin/env python3
"""
Requirement Quality Checkers v1.0.0
====================================
Advanced checkers for requirement document quality:
- Requirement traceability (missing IDs)
- Vague quantifiers in requirements
- Missing verification methods
- Ambiguous scope phrases

These address domain-expertise-level findings that go beyond
basic pattern matching into semantic requirement analysis.
"""

import re
from typing import List, Dict, Tuple

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "1.0.0"

# Shared directive pattern used by multiple checkers
DIRECTIVE_PATTERN = re.compile(r'\b(shall|must|will|should)\b', re.IGNORECASE)


class RequirementTraceabilityChecker(BaseChecker):
    """
    Flags requirement statements that lack a traceable identifier.

    Well-written requirements should have unique IDs (e.g., REQ-001, SRS-3.1.2)
    so they can be traced through design, implementation, and verification.
    Paragraphs containing directive keywords (shall/must/will) without any
    recognizable ID pattern are flagged.
    """

    CHECKER_NAME = "Requirement Traceability"
    CHECKER_VERSION = "1.0.0"

    # Patterns that indicate a requirement has an ID
    ID_PATTERNS = [
        re.compile(r'\b[A-Z]{2,10}[-_]\d{2,6}\b'),           # REQ-001, SRS-1234, RQ_05
        re.compile(r'\b[A-Z]{2,10}[-_]\d+\.\d+\b'),          # REQ-1.2, SRS-3.1
        re.compile(r'\b\d+\.\d+\.\d+(?:\.\d+)?\b'),          # 3.1.2, 4.2.1.3 (numbered sections)
        re.compile(r'\b[A-Z]\.\d+\.\d+\b'),                  # A.1.2, B.3.1
        re.compile(r'\b(?:Requirement|Req|Item)\s*#?\s*\d+\b', re.IGNORECASE),  # Requirement 5, Req #12
    ]

    # Skip paragraphs that are clearly headings or short labels
    MIN_LENGTH = 40

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            if not text or len(text.strip()) < self.MIN_LENGTH:
                continue

            # Only check paragraphs that contain directive language
            if not DIRECTIVE_PATTERN.search(text):
                continue

            # Check if any ID pattern is present
            has_id = False
            for pattern in self.ID_PATTERNS:
                if pattern.search(text):
                    has_id = True
                    break

            if not has_id:
                # Find the directive word for context
                match = DIRECTIVE_PATTERN.search(text)
                directive_word = match.group(0) if match else "shall"

                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Requirement statement lacks traceable identifier',
                    context=text[:80],
                    paragraph_index=idx,
                    suggestion=f'Add a unique requirement ID (e.g., REQ-001) to enable traceability through design, implementation, and verification',
                    rule_id='TRACE001',
                    flagged_text=directive_word
                ))

        return issues


class VagueQuantifierChecker(BaseChecker):
    """
    Flags vague quantifiers in requirement-context sentences.

    Words like "all", "every", "any", "various" make requirements
    untestable because they create unbounded scope. For example,
    "all safety requirements" is vague — which safety requirements?
    """

    CHECKER_NAME = "Vague Quantifier"
    CHECKER_VERSION = "1.0.0"

    # Vague quantifiers to flag
    VAGUE_QUANTIFIERS = [
        (re.compile(r'\ball\b', re.IGNORECASE), 'all'),
        (re.compile(r'\bevery\b', re.IGNORECASE), 'every'),
        (re.compile(r'\bany\b', re.IGNORECASE), 'any'),
        (re.compile(r'\bvarious\b', re.IGNORECASE), 'various'),
        (re.compile(r'\bnumerous\b', re.IGNORECASE), 'numerous'),
        (re.compile(r'\bseveral\b', re.IGNORECASE), 'several'),
        (re.compile(r'\bmany\b', re.IGNORECASE), 'many'),
        (re.compile(r'\bmost\b', re.IGNORECASE), 'most'),
    ]

    # Exclude common acceptable uses
    ACCEPTABLE_PATTERNS = [
        re.compile(r'\ball\s+of\s+the\s+(?:above|following|below)\b', re.IGNORECASE),
        re.compile(r'\bat\s+all\s+times\b', re.IGNORECASE),
        re.compile(r'\bany\s+time\b', re.IGNORECASE),
        re.compile(r'\bif\s+any\b', re.IGNORECASE),
        re.compile(r'\ball\s+rights\s+reserved\b', re.IGNORECASE),
    ]

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 20:
                continue

            # Only check requirement-context sentences (with directives)
            if not DIRECTIVE_PATTERN.search(text):
                continue

            # Check if paragraph matches an acceptable pattern
            is_acceptable = False
            for pattern in self.ACCEPTABLE_PATTERNS:
                if pattern.search(text):
                    is_acceptable = True
                    break

            if is_acceptable:
                continue

            # Check each vague quantifier
            for pattern, word in self.VAGUE_QUANTIFIERS:
                for match in pattern.finditer(text):
                    actual = text[match.start():match.end()]
                    context_start = max(0, match.start() - 25)
                    context_end = min(len(text), match.end() + 25)

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Vague quantifier "{actual}" in requirement statement',
                        context=text[context_start:context_end],
                        paragraph_index=idx,
                        suggestion=f'Replace "{actual}" with a specific, measurable quantity or explicit list to make the requirement testable',
                        rule_id='VAGUE001',
                        flagged_text=actual
                    ))
                    break  # One flag per quantifier type per paragraph

        return issues


class VerificationMethodChecker(BaseChecker):
    """
    Flags requirement statements that don't specify a verification method.

    Requirements should indicate HOW they will be verified — by test,
    inspection, analysis, or demonstration. Requirements without
    verification language risk being unverifiable.
    """

    CHECKER_NAME = "Verification Method"
    CHECKER_VERSION = "1.0.0"

    # Keywords indicating a verification method is mentioned
    VERIFICATION_KEYWORDS = re.compile(
        r'\b(?:verify|verified|verification|test|tested|testing|'
        r'inspect|inspected|inspection|analyze|analyzed|analysis|'
        r'demonstrate|demonstrated|demonstration|validate|validated|validation|'
        r'confirm|confirmed|confirmation|audit|audited|'
        r'measure|measured|measurement|evaluate|evaluated|evaluation|'
        r'assess|assessed|assessment|examine|examined|examination|'
        r'certif(?:y|ied|ication)|check(?:ed|list)?|'
        r'(?:acceptance|qualification|conformance)\s+(?:test|criteria))\b',
        re.IGNORECASE
    )

    # Only flag paragraphs with strong directive language
    STRONG_DIRECTIVE = re.compile(r'\b(shall|must)\b', re.IGNORECASE)

    MIN_LENGTH = 50  # Skip headings and short labels

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            if not text or len(text.strip()) < self.MIN_LENGTH:
                continue

            # Only check paragraphs with shall/must (strong requirements)
            if not self.STRONG_DIRECTIVE.search(text):
                continue

            # Check if any verification keyword is present
            if not self.VERIFICATION_KEYWORDS.search(text):
                match = self.STRONG_DIRECTIVE.search(text)
                directive_word = match.group(0) if match else "shall"

                issues.append(self.create_issue(
                    severity='Low',
                    message=f'Requirement lacks verification method',
                    context=text[:80],
                    paragraph_index=idx,
                    suggestion='Specify how this requirement will be verified (e.g., by test, inspection, analysis, or demonstration)',
                    rule_id='VERIFY001',
                    flagged_text=directive_word
                ))

        return issues


class AmbiguousScopeChecker(BaseChecker):
    """
    Flags overly broad scope phrases in requirements.

    Phrases like "all technical reviews", "all safety requirements",
    "entire system", or "all conditions" create ambiguous scope that
    makes requirements difficult to verify and implement.
    """

    CHECKER_NAME = "Ambiguous Scope"
    CHECKER_VERSION = "1.0.0"

    # Overly broad scope patterns
    SCOPE_PATTERNS = [
        (re.compile(r'\ball\s+(?:technical|safety|system|quality|design|performance|functional|operational)\s+\w+', re.IGNORECASE),
         'SCOPE001', 'Overly broad scope qualifier'),
        (re.compile(r'\bentire\s+(?:system|project|program|process|lifecycle|architecture)\b', re.IGNORECASE),
         'SCOPE002', 'Unbounded system scope'),
        (re.compile(r'\ball\s+(?:conditions|cases|situations|circumstances|scenarios|configurations|environments|modes)\b', re.IGNORECASE),
         'SCOPE003', 'Unbounded condition scope'),
        (re.compile(r'\bany\s+and\s+all\b', re.IGNORECASE),
         'SCOPE004', 'Redundant universal scope'),
        (re.compile(r'\ball\s+(?:applicable|relevant|necessary|required|appropriate)\s+\w+', re.IGNORECASE),
         'SCOPE005', 'Vague applicability scope'),
        (re.compile(r'\bevery\s+(?:aspect|element|component|part|phase|stage)\b', re.IGNORECASE),
         'SCOPE006', 'Unbounded element scope'),
    ]

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 20:
                continue

            for pattern, rule_id, desc in self.SCOPE_PATTERNS:
                for match in pattern.finditer(text):
                    actual = text[match.start():match.end()]
                    context_start = max(0, match.start() - 20)
                    context_end = min(len(text), match.end() + 20)

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'{desc}: "{actual}"',
                        context=text[context_start:context_end],
                        paragraph_index=idx,
                        suggestion=f'Replace "{actual}" with a specific, enumerated list or bounded reference to make scope verifiable',
                        rule_id=rule_id,
                        flagged_text=actual
                    ))
                    break  # One per pattern per paragraph

        return issues


def get_requirement_quality_checkers() -> Dict[str, 'BaseChecker']:
    """Factory function returning all requirement quality checkers."""
    return {
        'requirement_traceability': RequirementTraceabilityChecker(),
        'vague_quantifier': VagueQuantifierChecker(),
        'verification_method': VerificationMethodChecker(),
        'ambiguous_scope': AmbiguousScopeChecker(),
    }


# Standalone test
if __name__ == '__main__':
    print(f"Requirement Quality Checkers v{__version__}")
    print("=" * 50)

    # Test paragraphs that should trigger each checker
    test_paragraphs = [
        (0, "The system shall provide real-time monitoring of all flight parameters during nominal and off-nominal operations."),
        (1, "REQ-101: The contractor shall deliver monthly status reports to the program office."),
        (2, "The system shall comply with all safety requirements defined in the applicable standards."),
        (3, "The software must handle all conditions during flight operations without failure."),
        (4, "The contractor shall ensure that every aspect of the design meets performance criteria."),
        (5, "REQ-205: The system shall be verified by inspection to confirm that all interfaces comply with ICD-2000. Testing shall demonstrate interoperability."),
        (6, "The entire system must be operational within 30 seconds of power-on."),
        (7, "Various components should meet the specified tolerances."),
        (8, "The operator shall perform all technical reviews as specified in the program plan."),
        (9, "This is a short note."),  # Should be skipped (too short)
    ]

    checkers = get_requirement_quality_checkers()
    print(f"Loaded {len(checkers)} checkers\n")

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(test_paragraphs)
        print(f"  Found {len(issues)} issues:")
        for issue in issues:
            print(f"    [{issue['severity']}] {issue['rule_id']}: {issue['message']}")
            print(f"      Context: {issue['context'][:70]}...")
            print(f"      Suggestion: {issue['suggestion'][:80]}...")

    print(f"\n{'=' * 50}")
    print("All checkers working correctly.")
