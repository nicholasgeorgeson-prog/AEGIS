"""
Proselint Wrapper for AEGIS
======================================
Professional writing style rules from world-class writers and editors.

Features:
- Editorial style rules from Strunk & White, Garner, Orwell
- Cliché detection (50+ patterns)
- Jargon patterns
- Redundancy detection
- Weasel word detection
- Sexism/bias detection

Requires: pip install proselint
"""

from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass

from ..base import NLPIntegrationBase


@dataclass
class StyleIssue:
    """A style issue found by Proselint."""
    check_name: str
    message: str
    line: int
    column: int
    start: int
    end: int
    severity: str
    replacement: str = ""


# Module-level flag to prevent duplicate registration
_checks_registered = False


class ProselintWrapper(NLPIntegrationBase):
    """
    Proselint integration for professional writing style.

    Provides rules from Strunk & White, Garner, Orwell, etc.
    """

    INTEGRATION_NAME = "Proselint"
    INTEGRATION_VERSION = "1.0.0"

    # Rules to skip (overlap with existing AEGIS checkers)
    SKIP_CHECKS: Set[str] = {
        # We have our own passive voice checker
        'passive_voice',
        'misc.passive',
        # We have our own contractions checker
        'contractions',
        'misc.contractions',
        # Typography rules might conflict
        'typography.symbols.ellipsis',
        'typography.symbols.multiplication_symbol',
    }

    # Map proselint severity to our severity
    SEVERITY_MAP = {
        'error': 'High',
        'warning': 'Medium',
        'suggestion': 'Low',
    }

    # Category mapping for better organization
    CATEGORY_MAP = {
        'cliches': 'Clichés',
        'hedging': 'Weak Language',
        'redundancy': 'Redundancy',
        'jargon': 'Jargon',
        'weasel_words': 'Weak Language',
        'skunked_terms': 'Usage',
        'lexical_illusions': 'Clarity',
        'mixed_metaphors': 'Style',
        'oxymorons': 'Style',
        'sexism': 'Bias',
        'uncomparables': 'Grammar',
        'corporate_speak': 'Jargon',
        'archaisms': 'Style',
    }

    def __init__(self):
        """Initialize Proselint wrapper."""
        super().__init__()
        self._proselint = None
        self._initialize()

    def _initialize(self):
        """Initialize proselint library."""
        global _checks_registered
        try:
            import proselint
            # Import and register all checks - required for proselint v0.14+
            from proselint.checks import __register__
            from proselint.registry import CheckRegistry
            from proselint.config import DEFAULT

            # Register all checks with the registry (only once)
            if not _checks_registered:
                registry = CheckRegistry()
                registry.register_many(__register__)
                _checks_registered = True

            self._proselint = proselint
            self._default_config = DEFAULT
            self._available = True
        except ImportError as e:
            self._error = f"proselint not installed: {e}"
            self._available = False

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the Proselint integration."""
        status = {
            'available': self.is_available,
            'error': self._error,
            'skip_checks': list(self.SKIP_CHECKS),
        }

        if self.is_available:
            status['checks_available'] = self.get_available_checks()

        return status

    def check(self, text: str) -> List[StyleIssue]:
        """
        Check text for style issues.

        Args:
            text: Text to check

        Returns:
            List of StyleIssue objects
        """
        if not self.is_available:
            return []

        try:
            # New proselint API (v0.14+)
            from proselint.tools import LintFile
            lint_file = LintFile(source='-', content=text)
            suggestions = lint_file.lint(self._default_config)
        except AttributeError:
            # Fallback to old API
            try:
                suggestions = self._proselint.tools.lint(text)
            except Exception as e:
                self._error = f"Check failed: {e}"
                return []
        except Exception as e:
            self._error = f"Check failed: {e}"
            return []

        issues = []
        for sug in suggestions:
            # Handle new LintResult namedtuple format (v0.14+)
            # LintResult(check_result=CheckResult(...), pos=(line, col))
            if hasattr(sug, 'check_result'):
                check_result = sug.check_result
                check_name = check_result.check_path
                message = check_result.message
                line, column = sug.pos
                start = check_result.span[0] if check_result.span else 0
                end = check_result.span[1] if check_result.span else 0
                replacement = check_result.replacements or ''
                severity_str = 'warning'
            elif isinstance(sug, tuple) and len(sug) == 2:
                # Tuple format (CheckResult, (line, column))
                check_result, position = sug
                if hasattr(check_result, 'check_path'):
                    check_name = check_result.check_path
                    message = check_result.message
                    line, column = position
                    start = check_result.span[0] if check_result.span else 0
                    end = check_result.span[1] if check_result.span else 0
                    replacement = check_result.replacements or ''
                    severity_str = 'warning'
                else:
                    continue
            else:
                # Old format (tuple with many elements)
                try:
                    check_name = sug[0]
                    message = sug[1]
                    line = sug[2]
                    column = sug[3]
                    start = sug[4]
                    end = sug[5]
                    severity_str = sug[7] if len(sug) > 7 else 'warning'
                    replacement = sug[8] if len(sug) > 8 else ''
                except (IndexError, TypeError):
                    continue

            # Skip overlapping checks
            if self._should_skip(check_name):
                continue

            severity = self.SEVERITY_MAP.get(severity_str, 'Low')

            issues.append(StyleIssue(
                check_name=check_name,
                message=message,
                line=line,
                column=column,
                start=start,
                end=end,
                severity=severity,
                replacement=replacement if replacement else ''
            ))

        return issues

    def _should_skip(self, check_name: str) -> bool:
        """Check if a rule should be skipped."""
        # Direct match
        if check_name in self.SKIP_CHECKS:
            return True

        # Partial match (e.g., 'misc.passive' matches 'passive')
        for skip in self.SKIP_CHECKS:
            if skip in check_name or check_name in skip:
                return True

        return False

    def get_category(self, check_name: str) -> str:
        """Get category for a check name."""
        # Extract base category from check name (e.g., 'cliches.hell' -> 'cliches')
        parts = check_name.split('.')
        base = parts[0] if parts else check_name

        return self.CATEGORY_MAP.get(base, 'Style')

    def get_available_checks(self) -> List[str]:
        """List all available proselint checks."""
        if not self.is_available:
            return []

        try:
            from proselint import checks
            return [name for name in dir(checks) if not name.startswith('_')]
        except Exception:
            return []

    def add_skip_check(self, check_name: str):
        """Add a check to the skip list."""
        self.SKIP_CHECKS.add(check_name)

    def remove_skip_check(self, check_name: str):
        """Remove a check from the skip list."""
        self.SKIP_CHECKS.discard(check_name)
