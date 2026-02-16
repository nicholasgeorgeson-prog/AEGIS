"""
LanguageTool Client for AEGIS
========================================
Wraps language_tool_python library for grammar checking.

Features:
- Singleton pattern (one server per process)
- Rule filtering to avoid overlap with existing checkers
- Technical whitelist for aerospace/defense terms
- Severity mapping from LanguageTool categories
- Auto-correction support

Requires: pip install language-tool-python
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import threading

from ..base import NLPIntegrationBase


@dataclass
class GrammarMatch:
    """Represents a grammar issue found by LanguageTool."""
    message: str
    context: str
    offset: int
    length: int
    replacements: List[str]
    rule_id: str
    category: str
    severity: str
    sentence: str = ""


class LanguageToolClient(NLPIntegrationBase):
    """
    LanguageTool integration for comprehensive grammar checking.

    Runs local Java server - no internet required after installation.
    Uses singleton pattern to avoid multiple server instances.
    """

    INTEGRATION_NAME = "LanguageTool"
    INTEGRATION_VERSION = "1.0.0"

    # Severity mapping from LanguageTool categories
    SEVERITY_MAP = {
        'GRAMMAR': 'High',
        'TYPOS': 'High',
        'PUNCTUATION': 'Medium',
        'STYLE': 'Low',
        'TYPOGRAPHY': 'Low',
        'CASING': 'Medium',
        'COLLOCATIONS': 'Low',
        'REDUNDANCY': 'Low',
        'SEMANTICS': 'Medium',
        'MISC': 'Low',
    }

    # Rules to skip (overlap with existing AEGIS checkers)
    SKIP_RULES: Set[str] = {
        # Passive voice - we have our own checker
        'PASSIVE_VOICE',
        'BE_PASSIVE_VOICE',
        # Whitespace - handled by document formatting
        'WHITESPACE_RULE',
        'DOUBLE_WHITESPACE',
        # Spelling - we'll have enhanced spelling checker
        # 'MORFOLOGIK_RULE_EN_US',  # Keep this one for now
        # Contractions - often intentional in technical writing
        'CONTRACTION_SPELLING',
    }

    # Technical terms whitelist (aerospace/defense/software)
    TECHNICAL_WHITELIST: Set[str] = {
        # Aerospace
        'avionics', 'fuselage', 'airframe', 'aileron', 'altimeter',
        'autopilot', 'empennage', 'nacelle', 'pitot', 'yaw',
        # Defense
        'countermeasure', 'datalink', 'hardpoint', 'stealth',
        'radar', 'lidar', 'sonar', 'munition', 'ordnance',
        # Software
        'api', 'sdk', 'gui', 'cli', 'backend', 'frontend',
        'microservice', 'kubernetes', 'docker', 'devops',
        'readme', 'changelog', 'npm', 'yaml', 'json',
        # Acronyms
        'CONOPS', 'SDD', 'ICD', 'SRS', 'TRD', 'CDR', 'PDR',
        'FMEA', 'FMECA', 'FTA', 'HAZOP', 'V&V', 'IV&V',
    }

    # Singleton implementation
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern - only one LanguageTool server."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, language: str = 'en-US'):
        """
        Initialize LanguageTool client.

        Args:
            language: Language code (default: 'en-US')
        """
        if self._initialized:
            return

        super().__init__()
        self.language = language
        self._tool = None
        self._init_tool()
        self._initialized = True

    def _init_tool(self):
        """Initialize LanguageTool (starts local Java server)."""
        try:
            import language_tool_python
            self._lt_module = language_tool_python

            # Use local server mode - no internet needed
            self._tool = language_tool_python.LanguageTool(
                self.language,
                config={'cacheSize': 1000, 'pipelineCaching': True}
            )
            self._available = True

        except ImportError as e:
            self._error = f"language-tool-python not installed: {e}"
            self._available = False

        except Exception as e:
            self._error = f"LanguageTool initialization failed: {e}"
            self._available = False

    @property
    def is_available(self) -> bool:
        """Check if LanguageTool is available."""
        return self._available and self._tool is not None

    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the LanguageTool integration."""
        status = {
            'available': self.is_available,
            'language': self.language if self.is_available else None,
            'error': self._error,
        }

        if self.is_available:
            try:
                # Get server info
                status['version'] = getattr(self._tool, '_server_version', 'unknown')
                status['rules_count'] = len(self._tool.get_all_rules()) if hasattr(self._tool, 'get_all_rules') else 'unknown'
            except Exception:
                status['version'] = 'unknown'
                status['rules_count'] = 'unknown'

        return status

    def check(self, text: str) -> List[GrammarMatch]:
        """
        Check text for grammar issues.

        Args:
            text: Text to check

        Returns:
            List of GrammarMatch objects
        """
        if not self.is_available:
            return []

        try:
            matches = self._tool.check(text)
        except Exception as e:
            self._error = f"Check failed: {e}"
            return []

        issues = []
        for match in matches:
            # Skip rules that overlap with existing checkers
            if match.ruleId in self.SKIP_RULES:
                continue

            # Skip technical terms (check if the error is about a whitelisted word)
            if self._is_whitelisted_term(match, text):
                continue

            # Map category to severity
            category = match.category if hasattr(match, 'category') else 'MISC'
            severity = self.SEVERITY_MAP.get(category, 'Low')

            # Get replacements
            replacements = list(match.replacements) if match.replacements else []

            issues.append(GrammarMatch(
                message=match.message,
                context=match.context,
                offset=match.offset,
                length=match.errorLength,
                replacements=replacements[:5],  # Limit to 5 suggestions
                rule_id=match.ruleId,
                category=category,
                severity=severity,
                sentence=match.sentence if hasattr(match, 'sentence') else ''
            ))

        return issues

    def _is_whitelisted_term(self, match, text: str) -> bool:
        """Check if the match involves a whitelisted technical term."""
        try:
            # Extract the problematic text
            error_text = text[match.offset:match.offset + match.errorLength].lower()

            # Check against whitelist
            if error_text in self.TECHNICAL_WHITELIST:
                return True

            # Check if any whitelist term is in the error
            for term in self.TECHNICAL_WHITELIST:
                if term in error_text or error_text in term:
                    return True

        except Exception:
            pass

        return False

    def correct(self, text: str) -> str:
        """
        Auto-correct text using LanguageTool suggestions.

        Args:
            text: Text to correct

        Returns:
            Corrected text
        """
        if not self.is_available:
            return text

        try:
            return self._lt_module.utils.correct(text, self._tool.check(text))
        except Exception:
            return text

    def disable_rule(self, rule_id: str):
        """Disable a specific rule."""
        self.SKIP_RULES.add(rule_id)

    def enable_rule(self, rule_id: str):
        """Enable a previously disabled rule."""
        self.SKIP_RULES.discard(rule_id)

    def add_to_whitelist(self, term: str):
        """Add a term to the technical whitelist."""
        self.TECHNICAL_WHITELIST.add(term.lower())

    def close(self):
        """Shut down the LanguageTool server."""
        if self._tool:
            try:
                self._tool.close()
            except Exception:
                pass
            self._tool = None
            self._available = False

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
