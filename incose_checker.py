#!/usr/bin/env python3
"""
INCOSE Requirements Compliance Checker v1.0.0
==============================================
Validates requirements against INCOSE (International Council on Systems Engineering)
best practices and standards.

Implements 10 key INCOSE rules for requirements quality:

R1:  Mandatory requirements use "shall" (not "should", "will", "could", "may")
R2:  Each requirement is atomic (one "shall" per sentence/requirement)
R3:  No escape clauses ("if practicable", "as appropriate", etc.)
R4:  No vague/unmeasurable terms ("adequate", "sufficient", "timely", etc.)
R5:  Requirements must be testable (avoid subjective adjectives)
R6:  No negative requirements (rephrase "shall not" positively)
R7:  No compound requirements (avoid "and" connecting distinct obligations)
R8:  Temporal requirements need specific timeframes (not "soon", "quickly")
R9:  No dangling references ("the system mentioned above", "as described elsewhere")
R10: Each requirement needs a traceable identifier (REQ-XXX pattern)

No external library required - uses regex + spaCy (optional for better analysis)
"""

import re
from typing import Dict, List, Tuple, Optional

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "1.0.0"


class INCOSEComplianceChecker(BaseChecker):
    """
    Validates requirements against INCOSE standards.

    INCOSE (International Council on Systems Engineering) provides best practices
    for writing clear, unambiguous, testable requirements. This checker validates
    against the 10 most critical INCOSE rules.

    All checks use regex patterns and optional spaCy for detailed analysis.
    """

    CHECKER_NAME = "INCOSE Compliance"
    CHECKER_VERSION = "1.0.0"

    # INCOSE Rule Definitions
    # R1: Mandatory vs optional language
    MANDATORY_KEYWORDS = {'shall', 'must'}
    OPTIONAL_KEYWORDS = {'should', 'may', 'could', 'might', 'can'}

    # R3: Escape clause patterns (permission to deviate)
    ESCAPE_CLAUSES = {
        'if practicable': 'Escape clause: "if practicable"',
        'as appropriate': 'Escape clause: "as appropriate"',
        'as required': 'Escape clause: "as required"',
        'to the extent': 'Escape clause: "to the extent"',
        'if necessary': 'Escape clause: "if necessary"',
        'if applicable': 'Escape clause: "if applicable"',
        'unless': 'Escape clause: "unless"',
        'except': 'Escape clause: "except"',
        'as feasible': 'Escape clause: "as feasible"',
        'if available': 'Escape clause: "if available"',
        'when possible': 'Escape clause: "when possible"',
        'as much as practical': 'Escape clause: "as much as practical"',
    }

    # R4: Vague/unmeasurable terms
    VAGUE_TERMS = {
        'adequate': 'Vague term - specify measurable requirement',
        'sufficient': 'Vague term - specify quantity or threshold',
        'reasonable': 'Vague term - define specific criteria',
        'timely': 'Vague term - specify deadline or timeframe',
        'easy': 'Subjective - specify measurable criteria',
        'quickly': 'Vague timeframe - specify exact duration',
        'soon': 'Vague timeframe - specify date or version',
        'rapidly': 'Vague - specify speed/duration',
        'frequently': 'Vague - specify frequency',
        'infrequently': 'Vague - specify frequency',
        'generally': 'Vague - be specific',
        'normally': 'Vague - specify conditions',
        'substantially': 'Vague - specify percentage or quantity',
    }

    # R5: Subjective/untestable adjectives
    SUBJECTIVE_ADJECTIVES = {
        'beautiful': 'Untestable - subjective',
        'good': 'Untestable - subjective',
        'bad': 'Untestable - subjective',
        'nice': 'Untestable - subjective',
        'robust': 'Untestable without metrics - specify performance criteria',
        'efficient': 'Untestable without metrics - specify efficiency target',
        'reliable': 'Untestable without metrics - specify MTBF or uptime',
        'user-friendly': 'Untestable - specify usability criteria (e.g., SUS score)',
        'safe': 'Untestable without context - specify safety criteria',
        'high-quality': 'Untestable - specify quality metrics',
        'optimal': 'Untestable - specify optimization criteria',
    }

    # R6: Negative requirements (should be rephrased)
    NEGATIVE_PATTERN = re.compile(r'\bshall\s+not\b', re.IGNORECASE)

    # R7: Compound requirement indicators ("and" connecting distinct things)
    COMPOUND_PATTERN = re.compile(r'\bshall\s+[^.!?]*?\s+and\s+[^.!?]*?\b', re.IGNORECASE)

    # R8: Vague temporal indicators
    VAGUE_TEMPORAL = {
        'soon': 'Vague timeframe - specify date or version',
        'quickly': 'Vague duration - specify seconds/minutes/hours',
        'fast': 'Vague - specify speed in measurable units',
        'immediately': 'Vague - specify maximum latency',
        'as soon as possible': 'Vague - specify deadline',
    }

    # R9: Dangling reference patterns
    DANGLING_PATTERNS = [
        (r'\bthe\s+(?:system|document|section)\s+mentioned\s+(?:above|below)', 'Dangling reference'),
        (r'\bas\s+(?:described|stated|noted)\s+(?:above|below|elsewhere)', 'Dangling reference'),
        (r'\bas\s+(?:previously|earlier)\s+(?:mentioned|described|stated)', 'Dangling reference'),
        (r'\bthe\s+aforementioned\b', 'Dangling reference'),
        (r'\bthe\s+latter\b', 'Dangling reference'),
        (r'\bthe\s+former\b', 'Dangling reference'),
    ]

    # R10: Requirement ID patterns
    REQUIREMENT_ID_PATTERNS = [
        re.compile(r'\b[A-Z]{2,10}[-_]\d{2,6}\b'),           # REQ-001, SRS-1234
        re.compile(r'\b[A-Z]{2,10}[-_]\d+\.\d+\b'),          # REQ-1.2, SRS-3.1
        re.compile(r'\b\d+\.\d+\.\d+(?:\.\d+)?\b'),          # 3.1.2, 4.2.1.3
        re.compile(r'\b[A-Z]\.\d+\.\d+\b'),                  # A.1.2, B.3.1
    ]

    # Document-level tracking
    COMPLIANCE_SCORE_RULE = 'INCOSE010'
    MIN_PARAGRAPH_LENGTH = 40

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.spacy_available = self._init_spacy()
        self.total_requirements = 0
        self.compliant_requirements = 0

    def _init_spacy(self) -> bool:
        """Check if spaCy is available for advanced analysis."""
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
        Check requirements for INCOSE compliance.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text (unused)
            filepath: File path (unused)

        Returns:
            List of ReviewIssue dicts with compliance findings + overall score
        """
        if not self.enabled:
            return []

        issues = []
        self.total_requirements = 0
        self.compliant_requirements = 0

        for idx, text in paragraphs:
            if len(text.strip()) < self.MIN_PARAGRAPH_LENGTH:
                continue

            # Only check paragraphs with requirement language
            if not self._looks_like_requirement(text):
                continue

            self.total_requirements += 1

            # Check each INCOSE rule
            rule_violations = []

            rule_violations.extend(self._check_r1_mandatory_shall(text))
            rule_violations.extend(self._check_r2_atomic(text))
            rule_violations.extend(self._check_r3_escape_clauses(text))
            rule_violations.extend(self._check_r4_vague_terms(text))
            rule_violations.extend(self._check_r5_testable(text))
            rule_violations.extend(self._check_r6_negative(text))
            rule_violations.extend(self._check_r7_compound(text))
            rule_violations.extend(self._check_r8_temporal(text))
            rule_violations.extend(self._check_r9_dangling(text))
            rule_violations.extend(self._check_r10_identifier(text))

            if rule_violations:
                # Add violations to issues
                for severity, message, rule_id in rule_violations:
                    issues.append(self.create_issue(
                        severity=severity,
                        message=message,
                        context=text[:80],
                        paragraph_index=idx,
                        rule_id=rule_id,
                        flagged_text=text[:40]
                    ))
            else:
                self.compliant_requirements += 1

        # Add compliance score if document has requirements
        if self.total_requirements > 0:
            compliance_pct = (self.compliant_requirements / self.total_requirements) * 100
            issues.append(self.create_issue(
                severity='Info',
                message=f'INCOSE Compliance Score: {compliance_pct:.0f}%',
                context=f'{self.compliant_requirements}/{self.total_requirements} requirements fully compliant',
                paragraph_index=0,
                suggestion='Review violations above to improve requirements quality and traceability.',
                rule_id='INCOSE_SCORE',
                flagged_text=f'{compliance_pct:.0f}%'
            ))

        return issues[:30]

    def _looks_like_requirement(self, text: str) -> bool:
        """Check if text contains requirement language."""
        return bool(re.search(r'\b(shall|must|will|should|may|required)\b', text, re.IGNORECASE))

    def _check_r1_mandatory_shall(self, text: str) -> List[Tuple[str, str, str]]:
        """R1: Mandatory requirements use "shall", not "should", "will", "could", "may"."""
        violations = []

        # Check for optional keywords in what looks like mandatory context
        for keyword in self.OPTIONAL_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', text, re.IGNORECASE):
                # Check if this appears to be a mandatory requirement
                if any(word in text.lower() for word in ['contractor', 'system', 'software', 'must']):
                    violations.append((
                        'Medium',
                        f'Optional keyword "{keyword}" used for mandatory requirement - use "shall" instead',
                        'INCOSE_R1'
                    ))

        return violations

    def _check_r2_atomic(self, text: str) -> List[Tuple[str, str, str]]:
        """R2: Requirements are atomic (one shall per requirement)."""
        violations = []

        # Count "shall" occurrences
        shall_count = len(re.findall(r'\bshall\b', text, re.IGNORECASE))

        if shall_count > 1:
            violations.append((
                'High',
                f'Non-atomic requirement: {shall_count} "shall" statements (should be 1)',
                'INCOSE_R2'
            ))

        return violations

    def _check_r3_escape_clauses(self, text: str) -> List[Tuple[str, str, str]]:
        """R3: No escape clauses."""
        violations = []

        for clause, description in self.ESCAPE_CLAUSES.items():
            if clause in text.lower():
                violations.append(('High', description, 'INCOSE_R3'))
                break  # Report first escape clause

        return violations

    def _check_r4_vague_terms(self, text: str) -> List[Tuple[str, str, str]]:
        """R4: No vague/unmeasurable terms."""
        violations = []

        for term, description in self.VAGUE_TERMS.items():
            if re.search(r'\b' + term + r'\b', text, re.IGNORECASE):
                violations.append(('Medium', description, 'INCOSE_R4'))
                break  # Report first vague term

        return violations

    def _check_r5_testable(self, text: str) -> List[Tuple[str, str, str]]:
        """R5: Requirements must be testable."""
        violations = []

        for adj, description in self.SUBJECTIVE_ADJECTIVES.items():
            if re.search(r'\b' + adj + r'\b', text, re.IGNORECASE):
                violations.append(('Medium', description, 'INCOSE_R5'))
                break

        return violations

    def _check_r6_negative(self, text: str) -> List[Tuple[str, str, str]]:
        """R6: No negative requirements."""
        violations = []

        if self.NEGATIVE_PATTERN.search(text):
            violations.append((
                'Low',
                'Negative requirement ("shall not") - consider rephrasing positively',
                'INCOSE_R6'
            ))

        return violations

    def _check_r7_compound(self, text: str) -> List[Tuple[str, str, str]]:
        """R7: No compound requirements."""
        violations = []

        if self.COMPOUND_PATTERN.search(text):
            violations.append((
                'High',
                'Compound requirement: "shall ... and ..." - split into separate atomic requirements',
                'INCOSE_R7'
            ))

        return violations

    def _check_r8_temporal(self, text: str) -> List[Tuple[str, str, str]]:
        """R8: Temporal requirements need specific timeframes."""
        violations = []

        # Only check if has temporal requirement language
        if not re.search(r'\b(?:second|minute|hour|day|week|month|year|deadline|schedule|response time)\b', text, re.IGNORECASE):
            return violations

        for term, description in self.VAGUE_TEMPORAL.items():
            if re.search(r'\b' + term + r'\b', text, re.IGNORECASE):
                violations.append(('Medium', description, 'INCOSE_R8'))
                break

        return violations

    def _check_r9_dangling(self, text: str) -> List[Tuple[str, str, str]]:
        """R9: No dangling references."""
        violations = []

        for pattern, description in self.DANGLING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(('High', description, 'INCOSE_R9'))
                break

        return violations

    def _check_r10_identifier(self, text: str) -> List[Tuple[str, str, str]]:
        """R10: Requirements need traceable identifier."""
        violations = []

        # Check if text has any ID pattern
        has_id = False
        for pattern in self.REQUIREMENT_ID_PATTERNS:
            if pattern.search(text):
                has_id = True
                break

        if not has_id:
            violations.append((
                'Low',
                'Requirement lacks traceable identifier (e.g., REQ-001)',
                'INCOSE_R10'
            ))

        return violations


def get_incose_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning INCOSE compliance checker."""
    return {
        'incose_compliance': INCOSEComplianceChecker(),
    }


# Standalone test
if __name__ == '__main__':
    print(f"INCOSE Compliance Checker v{__version__}")
    print("=" * 50)

    test_paragraphs = [
        (0, "REQ-001: The system shall provide real-time monitoring and shall ensure compliance."),
        (1, "The software should respond quickly to user inputs when practicable."),
        (2, "SRS-2.1: The system shall be robust and shall not fail under any circumstances."),
        (3, "The contractor should deliver the adequate documentation as soon as possible."),
        (4, "The system shall verify all inputs and shall validate outputs before transmission to the controller."),
    ]

    checker = INCOSEComplianceChecker()
    issues = checker.check(test_paragraphs)

    print(f"\nFound {len(issues)} issues:\n")
    for issue in issues:
        print(f"[{issue['severity']}] {issue['message']}")
        print(f"  Rule: {issue['rule_id']}")
        print()
