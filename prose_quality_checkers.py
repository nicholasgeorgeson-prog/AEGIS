#!/usr/bin/env python3
"""
Prose Quality Checkers v1.0.0
=============================
Uses proselint library for advanced prose quality checking.

Detects:
- Clichés (overused phrases)
- Hedging language (uncertain/tentative)
- Redundancy (repetitive words/phrases)
- Jargon and overly complex language
- Typography issues
- Consistency problems
- Security/legal concerns (corporate speak)

The proselint library must be installed: pip install proselint

Maps proselint issues to severity levels:
- High: Errors affecting clarity or compliance
- Medium: Warnings about style or consistency
- Low: Suggestions for improvement
"""

import re
from typing import Dict, List, Tuple, Optional

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "1.0.0"


class AdvancedProseLintChecker(BaseChecker):
    """
    Advanced prose quality checking using proselint.

    Detects writing issues that affect clarity, consistency, and professionalism
    in technical documentation. Uses the proselint library when available,
    falls back to pattern matching otherwise.
    """

    CHECKER_NAME = "Advanced Prose Lint"
    CHECKER_VERSION = "1.0.0"

    # Clichés commonly found in technical writing
    CLICHES = {
        'at the end of the day': 'In summary',
        'at this point in time': 'now',
        'due to the fact that': 'because',
        'for all intents and purposes': 'essentially',
        'in the event that': 'if',
        'in the final analysis': 'ultimately',
        'in the not too distant future': 'soon',
        'last but not least': 'Finally',
        'no matter what': 'regardless',
        'on a daily basis': 'daily',
        'with respect to': 'regarding',
        'without a doubt': 'certainly',
        'each and every': 'each',
        'never in my entire life': 'never',
    }

    # Hedging language (uncertainty words)
    HEDGING = {
        'arguably': 'state directly instead of hedging',
        'maybe': 'use "might" or be more specific',
        'probably': 'state fact or probability percentage',
        'somewhat': 'quantify with specific term',
        'rather': 'use concrete description',
        'quite': 'be more precise',
        'sort of': 'be direct',
        'kind of': 'be specific',
        'a bit': 'quantify precisely',
    }

    # Redundancy patterns
    REDUNDANCY_PATTERNS = [
        (r'\battempt to try\b', 'attempt to try', 'remove duplicate'),
        (r'\badvance forward\b', 'advance forward', 'use "advance"'),
        (r'\bfinal outcome\b', 'final outcome', 'use "outcome"'),
        (r'\bcompletely finished\b', 'completely finished', 'use "finished"'),
        (r'\btrue fact\b', 'true fact', 'use "fact"'),
        (r'\bnecessary requirement\b', 'necessary requirement', 'use "requirement"'),
        (r'\bfree gift\b', 'free gift', 'use "gift"'),
        (r'\bnew innovation\b', 'new innovation', 'use "innovation"'),
        (r'\bpartially complete\b', 'partially complete', 'use "partially done"'),
        (r'\bcompletely eliminate\b', 'completely eliminate', 'use "eliminate"'),
    ]

    # Jargon and overly complex terms for technical docs
    COMPLEX_JARGON = {
        'utilize': 'use',
        'implement': 'create, deploy, or build (be specific)',
        'paradigm': 'model or framework (be specific)',
        'leverage': 'use or exploit',
        'synergy': 'cooperation or combined benefit',
        'touchpoint': 'contact point',
        'value-add': 'benefit or advantage',
        'at scale': 'in production or at high volume',
        'operationalize': 'put into operation',
        'ideate': 'develop ideas',
    }

    # Typography issues
    TYPOGRAPHY_PATTERNS = [
        (r"'([a-z])", 'curly quote', 'Use proper curly quotes'),
        (r'--(?!-)', 'em dash', 'Use em dash (—) instead of --'),
        (r'\s{2,}', 'multiple spaces', 'Use single spaces'),
        (r'\(\s', 'space after (', 'Remove space after opening parenthesis'),
        (r'\s\)', 'space before )', 'Remove space before closing parenthesis'),
    ]

    # Security/legal concerns (corporate/defensive language)
    DEFENSIVE_LANGUAGE = {
        'not responsible': 'remove disclaimer or state responsibility clearly',
        'use at your own risk': 'clarify safety or support guarantees',
        'as is': 'avoid vague disclaimers',
        'to the extent permitted': 'remove legal hedging',
        'without limitation': 'specify limitations clearly',
    }

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.proselint_available = False
        self._init_proselint()

    def _init_proselint(self) -> bool:
        """Check if proselint is available."""
        try:
            import proselint
            self.proselint_available = True
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
        Check paragraph prose quality.

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

        if self.proselint_available:
            issues.extend(self._check_with_proselint(paragraphs))
        else:
            # Use pattern-based fallback
            issues.extend(self._check_with_patterns(paragraphs))

        return issues[:30]  # Limit issues

    def _check_with_proselint(self, paragraphs: List[Tuple[int, str]]) -> List[Dict]:
        """Use proselint library for checking."""
        try:
            import proselint.tools as proselint_tools
        except ImportError:
            return []

        issues = []
        found_issues = set()  # Avoid duplicates

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            try:
                # Run all proselint checks
                warnings = proselint_tools.checks.run(text)

                for error_type, position, message, replacements in warnings:
                    issue_key = (idx, error_type, position)
                    if issue_key in found_issues:
                        continue
                    found_issues.add(issue_key)

                    # Map error type to severity
                    severity = self._map_severity(error_type)

                    # Extract context
                    start = max(0, position - 30)
                    end = min(len(text), position + 50)
                    context = text[start:end]

                    # Prepare suggestion
                    suggestion = message
                    if replacements:
                        suggestion = f"{message}. Try: {replacements[0]}"

                    issues.append(self.create_issue(
                        severity=severity,
                        message=message,
                        context=f"...{context}...",
                        paragraph_index=idx,
                        suggestion=suggestion,
                        rule_id='PROSE001',
                        flagged_text=text[position:min(len(text), position + 20)]
                    ))

            except Exception:
                # If proselint fails on this paragraph, continue
                pass

        return issues

    def _check_with_patterns(self, paragraphs: List[Tuple[int, str]]) -> List[Dict]:
        """Pattern-based fallback checking."""
        issues = []

        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            # Check clichés
            text_lower = text.lower()
            for cliche, suggestion in self.CLICHES.items():
                if cliche in text_lower:
                    pattern = re.compile(re.escape(cliche), re.IGNORECASE)
                    for match in pattern.finditer(text):
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'Cliché detected: "{match.group()}"',
                            context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                            paragraph_index=idx,
                            suggestion=f'Replace with: "{suggestion}"',
                            rule_id='PROSE002',
                            flagged_text=match.group()
                        ))
                        break  # One per paragraph

            # Check hedging language
            for hedge, suggestion in self.HEDGING.items():
                if re.search(r'\b' + hedge + r'\b', text, re.IGNORECASE):
                    pattern = re.compile(r'\b' + re.escape(hedge) + r'\b', re.IGNORECASE)
                    match = pattern.search(text)
                    if match:
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'Hedging language detected: "{match.group()}"',
                            context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                            paragraph_index=idx,
                            suggestion=f'Be more direct: {suggestion}',
                            rule_id='PROSE003',
                            flagged_text=match.group()
                        ))
                        break

            # Check redundancy
            for pattern, phrase, suggestion in self.REDUNDANCY_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'Redundant phrase: "{phrase}"',
                            context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                            paragraph_index=idx,
                            suggestion=suggestion,
                            rule_id='PROSE004',
                            flagged_text=match.group()
                        ))
                        break

            # Check for jargon
            for jargon, suggestion in self.COMPLEX_JARGON.items():
                if re.search(r'\b' + jargon + r'\b', text, re.IGNORECASE):
                    pattern = re.compile(r'\b' + re.escape(jargon) + r'\b', re.IGNORECASE)
                    match = pattern.search(text)
                    if match:
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f'Complex jargon: "{match.group()}"',
                            context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                            paragraph_index=idx,
                            suggestion=f'Prefer simpler term: "{suggestion}"',
                            rule_id='PROSE005',
                            flagged_text=match.group()
                        ))
                        break

            # Check defensive language
            for phrase, suggestion in self.DEFENSIVE_LANGUAGE.items():
                if re.search(r'\b' + re.escape(phrase) + r'\b', text, re.IGNORECASE):
                    pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
                    match = pattern.search(text)
                    if match:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f'Defensive/legal language: "{match.group()}"',
                            context=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                            paragraph_index=idx,
                            suggestion=suggestion,
                            rule_id='PROSE006',
                            flagged_text=match.group()
                        ))
                        break

        return issues

    def _map_severity(self, error_type: str) -> str:
        """Map proselint error type to severity level."""
        if 'error' in error_type.lower() or 'consistency' in error_type.lower():
            return 'High'
        elif 'warning' in error_type.lower() or 'typography' in error_type.lower():
            return 'Medium'
        else:
            return 'Low'


def get_prose_quality_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning prose quality checker."""
    return {
        'advanced_prose_lint': AdvancedProseLintChecker(),
    }


# Standalone test
if __name__ == '__main__':
    print(f"Prose Quality Checkers v{__version__}")
    print("=" * 50)

    test_paragraphs = [
        (0, "At the end of the day, the system will utilize best practices to leverage core competencies."),
        (1, "This is a somewhat difficult situation. Maybe we should think about it."),
        (2, "The final outcome was completely finished ahead of schedule."),
        (3, "The system is not responsible for security issues. Use at your own risk."),
    ]

    checker = AdvancedProseLintChecker()
    print(f"Proselint available: {checker.proselint_available}\n")

    issues = checker.check(test_paragraphs)
    print(f"Found {len(issues)} issues:")
    for issue in issues[:5]:
        print(f"  [{issue['severity']}] {issue['message']}")
        if issue.get('suggestion'):
            print(f"    Suggestion: {issue['suggestion'][:70]}...")
