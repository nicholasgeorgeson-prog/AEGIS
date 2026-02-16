"""
Comprehensive Grammar Checker for AEGIS
==================================================
NLP checker wrapper for LanguageTool integration.

Provides 3000+ grammar rules beyond basic regex patterns.
Inherits from NLPCheckerBase for consistent interface.
"""

from typing import List, Tuple, Optional

from ..base import NLPCheckerBase, NLPIssue
from .client import LanguageToolClient, GrammarMatch


class ComprehensiveGrammarChecker(NLPCheckerBase):
    """
    Comprehensive grammar checking using LanguageTool.

    Provides 3000+ grammar rules beyond basic regex patterns.
    Handles initialization, paragraph processing, and issue conversion.
    """

    CHECKER_NAME = "Grammar (Comprehensive)"
    CHECKER_VERSION = "1.0.0"

    # Categories to include/exclude
    INCLUDE_CATEGORIES = {
        'GRAMMAR', 'TYPOS', 'PUNCTUATION', 'STYLE',
        'CASING', 'COLLOCATIONS', 'REDUNDANCY', 'SEMANTICS'
    }

    def __init__(self, enabled: bool = True):
        """
        Initialize the grammar checker.

        Args:
            enabled: Whether the checker is enabled
        """
        super().__init__(enabled)
        self._client: Optional[LanguageToolClient] = None

    def _initialize(self) -> bool:
        """Initialize the LanguageTool client."""
        try:
            self._client = LanguageToolClient()
            if not self._client.is_available:
                self._init_error = self._client.error
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
        Check for grammar issues in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected issues
        """
        issues = []

        for para_idx, text in paragraphs:
            if not text.strip():
                continue

            matches = self._client.check(text)

            for match in matches:
                # Skip categories we don't want
                if match.category not in self.INCLUDE_CATEGORIES:
                    continue

                issue = self._convert_match_to_issue(match, para_idx, text)
                issues.append(issue)

        return issues

    def _convert_match_to_issue(
        self,
        match: GrammarMatch,
        para_idx: int,
        full_text: str
    ) -> NLPIssue:
        """
        Convert a LanguageTool match to an NLPIssue.

        Args:
            match: GrammarMatch from LanguageTool
            para_idx: Paragraph index
            full_text: Full paragraph text

        Returns:
            NLPIssue object
        """
        # Extract the original text that has the error
        try:
            original = full_text[match.offset:match.offset + match.length]
        except (IndexError, TypeError):
            original = ""

        # Get the best replacement if available
        replacement = match.replacements[0] if match.replacements else ""

        # Build suggestion text
        if match.replacements:
            if len(match.replacements) == 1:
                suggestion = f"Consider: '{match.replacements[0]}'"
            else:
                suggestions = "', '".join(match.replacements[:3])
                suggestion = f"Consider: '{suggestions}'"
                if len(match.replacements) > 3:
                    suggestion += f" (and {len(match.replacements) - 3} more)"
        else:
            suggestion = "Review this text for potential issues."

        # Use sentence context if available, otherwise use match context
        context = match.sentence if match.sentence else match.context

        return self.create_issue(
            severity=match.severity,
            message=match.message,
            paragraph_index=para_idx,
            context=context,
            suggestion=suggestion,
            rule_id=match.rule_id,
            category=f"Grammar/{match.category}",
            original_text=original,
            replacement_text=replacement,
            confidence=0.9  # LanguageTool is generally reliable
        )

    def get_corrected_text(self, text: str) -> str:
        """
        Get auto-corrected version of text.

        Args:
            text: Text to correct

        Returns:
            Corrected text
        """
        if not self._initialized or not self._client:
            return text
        return self._client.correct(text)

    def disable_rule(self, rule_id: str):
        """
        Disable a specific LanguageTool rule.

        Args:
            rule_id: Rule ID to disable
        """
        if self._client:
            self._client.disable_rule(rule_id)

    def enable_rule(self, rule_id: str):
        """
        Enable a previously disabled rule.

        Args:
            rule_id: Rule ID to enable
        """
        if self._client:
            self._client.enable_rule(rule_id)

    def add_to_whitelist(self, term: str):
        """
        Add a term to the technical whitelist.

        Args:
            term: Technical term to whitelist
        """
        if self._client:
            self._client.add_to_whitelist(term)
