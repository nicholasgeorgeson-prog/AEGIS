"""
NLP Base Classes
================
Base classes and utilities for NLP integrations.

Provides common interfaces that all NLP checkers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field
import time

__version__ = "1.0.0"


@dataclass
class NLPIssue:
    """
    Represents an issue found by an NLP checker.

    Compatible with AEGIS's existing issue format.
    """
    severity: str  # 'High', 'Medium', 'Low', 'Info'
    message: str
    paragraph_index: int
    context: str
    suggestion: str = ""
    rule_id: str = ""
    category: str = ""

    # For auto-fix support
    original_text: str = ""
    replacement_text: str = ""

    # Metadata
    checker_name: str = ""
    confidence: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API responses."""
        return {
            'severity': self.severity,
            'message': self.message,
            'paragraph_index': self.paragraph_index,
            'context': self.context,
            'suggestion': self.suggestion,
            'rule_id': self.rule_id,
            'category': self.category,
            'original_text': self.original_text,
            'replacement_text': self.replacement_text,
            'checker_name': self.checker_name,
            'confidence': self.confidence,
        }


@dataclass
class NLPAnalysisResult:
    """Result of NLP analysis on a document."""
    issues: List[NLPIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: float = 0.0
    checker_name: str = ""
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'issues': [i.to_dict() for i in self.issues],
            'metrics': self.metrics,
            'processing_time_ms': self.processing_time_ms,
            'checker_name': self.checker_name,
            'success': self.success,
            'error': self.error,
        }


class NLPCheckerBase(ABC):
    """
    Abstract base class for NLP-enhanced checkers.

    All NLP checkers should inherit from this class.
    """

    CHECKER_NAME: str = "NLP Checker"
    CHECKER_VERSION: str = "1.0.0"

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._initialized = False
        self._init_error: Optional[str] = None

    @abstractmethod
    def _initialize(self) -> bool:
        """
        Initialize the checker (load models, connect to services, etc.).

        Returns True if initialization succeeded.
        Called lazily on first check.
        """
        pass

    @abstractmethod
    def _check_impl(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> List[NLPIssue]:
        """
        Implementation of the check logic.

        Args:
            paragraphs: List of (index, text) tuples
            **kwargs: Additional context (full_text, headings, etc.)

        Returns:
            List of NLPIssue objects
        """
        pass

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        **kwargs
    ) -> NLPAnalysisResult:
        """
        Run the checker on paragraphs.

        Handles initialization, timing, and error handling.
        """
        start_time = time.time()

        result = NLPAnalysisResult(checker_name=self.CHECKER_NAME)

        if not self.enabled:
            result.metrics['skipped'] = 'disabled'
            return result

        # Lazy initialization
        if not self._initialized:
            try:
                self._initialized = self._initialize()
            except Exception as e:
                self._init_error = str(e)
                result.success = False
                result.error = f"Initialization failed: {e}"
                return result

        if not self._initialized:
            result.success = False
            result.error = self._init_error or "Initialization failed"
            return result

        # Run the check
        try:
            issues = self._check_impl(paragraphs, **kwargs)
            result.issues = issues
            result.metrics['issue_count'] = len(issues)
        except Exception as e:
            result.success = False
            result.error = f"Check failed: {e}"

        result.processing_time_ms = (time.time() - start_time) * 1000
        return result

    def create_issue(
        self,
        severity: str,
        message: str,
        paragraph_index: int,
        context: str,
        suggestion: str = "",
        rule_id: str = "",
        category: str = "",
        original_text: str = "",
        replacement_text: str = "",
        confidence: float = 1.0
    ) -> NLPIssue:
        """Helper to create an NLPIssue with checker metadata."""
        return NLPIssue(
            severity=severity,
            message=message,
            paragraph_index=paragraph_index,
            context=context,
            suggestion=suggestion,
            rule_id=rule_id,
            category=category or self.CHECKER_NAME,
            original_text=original_text,
            replacement_text=replacement_text,
            checker_name=self.CHECKER_NAME,
            confidence=confidence
        )


class NLPIntegrationBase(ABC):
    """
    Abstract base class for NLP tool integrations.

    Wraps external NLP libraries (spaCy, LanguageTool, etc.).
    """

    INTEGRATION_NAME: str = "NLP Integration"
    INTEGRATION_VERSION: str = "1.0.0"

    def __init__(self):
        self._available = False
        self._error: Optional[str] = None

    @property
    def is_available(self) -> bool:
        """Check if the integration is available and working."""
        return self._available

    @property
    def error(self) -> Optional[str]:
        """Get initialization error if any."""
        return self._error

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the integration."""
        pass


def convert_to_legacy_issue(nlp_issue: NLPIssue) -> Dict[str, Any]:
    """
    Convert NLPIssue to legacy AEGIS issue format.

    For compatibility with existing code.
    """
    return {
        'severity': nlp_issue.severity,
        'message': nlp_issue.message,
        'paragraph_index': nlp_issue.paragraph_index,
        'context': nlp_issue.context,
        'suggestion': nlp_issue.suggestion,
        'rule_id': nlp_issue.rule_id,
        'category': nlp_issue.category,
        'checker': nlp_issue.checker_name,
        # Auto-fix fields
        'original_text': nlp_issue.original_text,
        'replacement_text': nlp_issue.replacement_text,
    }


def convert_from_legacy_issue(legacy: Dict[str, Any]) -> NLPIssue:
    """
    Convert legacy AEGIS issue to NLPIssue.

    For compatibility with existing code.
    """
    return NLPIssue(
        severity=legacy.get('severity', 'Low'),
        message=legacy.get('message', ''),
        paragraph_index=legacy.get('paragraph_index', 0),
        context=legacy.get('context', ''),
        suggestion=legacy.get('suggestion', ''),
        rule_id=legacy.get('rule_id', ''),
        category=legacy.get('category', ''),
        original_text=legacy.get('original_text', ''),
        replacement_text=legacy.get('replacement_text', ''),
        checker_name=legacy.get('checker', ''),
        confidence=legacy.get('confidence', 1.0),
    )
