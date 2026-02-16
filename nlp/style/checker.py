"""
Style Checker for AEGIS
==================================
NLP checker wrapper for Proselint integration.

Provides professional editorial style checking with
rules from Strunk & White, Garner, Orwell, etc.

Inherits from NLPCheckerBase for consistent interface.
"""

from typing import List, Tuple, Optional

from ..base import NLPCheckerBase, NLPIssue
from .proselint import ProselintWrapper, StyleIssue


class StyleChecker(NLPCheckerBase):
    """
    Professional style checking using Proselint.

    Detects clichés, jargon, redundancy, weasel words, and more.
    """

    CHECKER_NAME = "Style (Professional)"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        """
        Initialize the style checker.

        Args:
            enabled: Whether the checker is enabled
        """
        super().__init__(enabled)
        self._wrapper: Optional[ProselintWrapper] = None

    def _initialize(self) -> bool:
        """Initialize the Proselint wrapper."""
        try:
            self._wrapper = ProselintWrapper()
            if not self._wrapper.is_available:
                self._init_error = self._wrapper.error
                return False
            return True
        except Exception as e:
            self._init_error = str(e)
            return False

    def _check_impl(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> List[NLPIssue]:
        """
        Check for style issues in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected issues
        """
        issues = []

        for para_idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            style_issues = self._wrapper.check(text)

            for si in style_issues:
                issue = self._convert_to_nlp_issue(si, para_idx, text)
                issues.append(issue)

        return issues

    def _convert_to_nlp_issue(
        self,
        style_issue: StyleIssue,
        para_idx: int,
        full_text: str
    ) -> NLPIssue:
        """
        Convert a StyleIssue to NLPIssue.

        Args:
            style_issue: StyleIssue from Proselint
            para_idx: Paragraph index
            full_text: Full paragraph text

        Returns:
            NLPIssue object
        """
        # Extract context around the issue
        context = self._get_context(full_text, style_issue.start, style_issue.end)

        # Get the original problematic text
        try:
            original = full_text[style_issue.start:style_issue.end]
        except (IndexError, TypeError):
            original = ""

        # Build suggestion
        if style_issue.replacement:
            suggestion = f"Consider: '{style_issue.replacement}'"
        else:
            suggestion = "Review this phrasing for style."

        # Get category
        category = self._wrapper.get_category(style_issue.check_name)

        return self.create_issue(
            severity=style_issue.severity,
            message=style_issue.message,
            paragraph_index=para_idx,
            context=context,
            suggestion=suggestion,
            rule_id=style_issue.check_name,
            category=f"Style/{category}",
            original_text=original,
            replacement_text=style_issue.replacement,
            confidence=0.85
        )

    def _get_context(
        self,
        text: str,
        start: int,
        end: int,
        context_chars: int = 40
    ) -> str:
        """Get context around an issue."""
        try:
            ctx_start = max(0, start - context_chars)
            ctx_end = min(len(text), end + context_chars)

            context = text[ctx_start:ctx_end]

            if ctx_start > 0:
                context = '...' + context
            if ctx_end < len(text):
                context = context + '...'

            return context

        except Exception:
            return text[:80] + '...' if len(text) > 80 else text

    def add_skip_check(self, check_name: str):
        """
        Add a check to skip.

        Args:
            check_name: Proselint check name to skip
        """
        if self._wrapper:
            self._wrapper.add_skip_check(check_name)

    def remove_skip_check(self, check_name: str):
        """
        Remove a check from skip list.

        Args:
            check_name: Proselint check name to enable
        """
        if self._wrapper:
            self._wrapper.remove_skip_check(check_name)

    def get_available_checks(self) -> List[str]:
        """Get list of available Proselint checks."""
        if self._wrapper:
            return self._wrapper.get_available_checks()
        return []
