"""
Enhanced Spelling Checker for AEGIS
==============================================
Combines SymSpell and domain dictionaries for comprehensive spell checking.

Features:
- 500K+ word dictionary via SymSpell
- Domain-specific term awareness
- Technical abbreviation handling
- Configurable skip patterns

Inherits from NLPCheckerBase for consistent interface.
"""

import re
from typing import List, Tuple, Set, Optional

from ..base import NLPCheckerBase, NLPIssue
from .symspell import SymSpellChecker
from .enchant import DomainDictionaryManager


class EnhancedSpellingChecker(NLPCheckerBase):
    """
    Comprehensive spelling checker using SymSpell and domain dictionaries.

    Replaces basic 100-word dictionary with 500K+ words.
    """

    CHECKER_NAME = "Spelling (Enhanced)"
    CHECKER_VERSION = "1.0.0"

    # Words to never flag (technical terms, proper nouns, etc.)
    SKIP_WORDS: Set[str] = {
        # Common technical abbreviations
        'api', 'apis', 'sdk', 'sdks', 'gui', 'guis', 'cli', 'url', 'urls',
        'html', 'css', 'json', 'yaml', 'xml', 'sql', 'nosql',
        'http', 'https', 'ftp', 'ssh', 'tcp', 'udp', 'ip',
        'cpu', 'gpu', 'ram', 'rom', 'ssd', 'hdd',
        'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg',
        'npm', 'pip', 'git', 'svn', 'hg',
        'aws', 'gcp', 'azure', 'saas', 'paas', 'iaas',
        'ci', 'cd', 'devops', 'mlops', 'aiops',
        'todo', 'todos', 'fixme', 'hack', 'xxx',
        # Common proper nouns in tech
        'github', 'gitlab', 'bitbucket', 'jira', 'confluence',
        'linux', 'unix', 'macos', 'ios', 'android', 'windows',
        'python', 'javascript', 'typescript', 'golang', 'rust',
        'kubernetes', 'docker', 'nginx', 'apache',
        'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
        # v5.9.28: Defense contractor abbreviations
        'ng', 'ngc', 'ngis', 'ngas', 'bae', 'gd', 'saic', 'gdit', 'leidos',
    }

    # Patterns to skip (regex)
    SKIP_PATTERNS = [
        r'^[A-Z]{2,}$',        # All caps (acronyms)
        r'^[A-Z][a-z]+[A-Z]',  # CamelCase
        r'^\d+[a-zA-Z]+$',     # Numbers followed by letters
        r'^[a-zA-Z]+\d+$',     # Letters followed by numbers
        r'^v\d+',              # Version numbers
    ]

    def __init__(
        self,
        enabled: bool = True,
        use_domain_dicts: bool = True,
        min_word_length: int = 2
    ):
        """
        Initialize the spelling checker.

        Args:
            enabled: Whether the checker is enabled
            use_domain_dicts: Whether to use domain dictionaries
            min_word_length: Minimum word length to check
        """
        super().__init__(enabled)
        self._symspell: Optional[SymSpellChecker] = None
        self._domain: Optional[DomainDictionaryManager] = None
        self.use_domain_dicts = use_domain_dicts
        self.min_word_length = min_word_length

        # Compile skip patterns
        self._skip_patterns = [re.compile(p) for p in self.SKIP_PATTERNS]

    def _initialize(self) -> bool:
        """Initialize spelling components."""
        try:
            self._symspell = SymSpellChecker()
            if not self._symspell.is_available:
                self._init_error = self._symspell.error
                return False

            if self.use_domain_dicts:
                try:
                    self._domain = DomainDictionaryManager()
                except Exception:
                    pass  # Domain dicts are optional

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
        Check for spelling errors in paragraphs.

        Args:
            paragraphs: List of (index, text) tuples

        Returns:
            List of NLPIssue objects for detected misspellings
        """
        issues = []

        for para_idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue

            misspellings = self._symspell.check_text(text)

            for ms in misspellings:
                word = ms.word

                # Skip if in skip list
                if self._should_skip(word):
                    continue

                # Skip if domain term
                if self._domain and self._domain.is_domain_term(word):
                    continue

                # Get suggestions
                suggestions = [s.suggestion for s in ms.suggestions[:3]]

                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Possible misspelling: "{word}"',
                    paragraph_index=para_idx,
                    context=self._get_word_context(text, word),
                    suggestion=f'Did you mean: {", ".join(suggestions)}?' if suggestions else 'Check spelling',
                    rule_id='SPELL001',
                    category='Spelling',
                    original_text=word,
                    replacement_text=ms.best_suggestion,
                    confidence=self._calculate_confidence(ms)
                ))

        return issues

    def _should_skip(self, word: str) -> bool:
        """Check if a word should be skipped."""
        # Check length
        if len(word) < self.min_word_length:
            return True

        # Check skip list
        if word.lower() in self.SKIP_WORDS:
            return True

        # Check patterns
        for pattern in self._skip_patterns:
            if pattern.match(word):
                return True

        return False

    def _get_word_context(self, text: str, word: str, context_chars: int = 40) -> str:
        """Get context around a word in text."""
        try:
            # Find word position (case insensitive)
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            match = pattern.search(text)

            if match:
                start = max(0, match.start() - context_chars)
                end = min(len(text), match.end() + context_chars)

                context = text[start:end]
                if start > 0:
                    context = '...' + context
                if end < len(text):
                    context = context + '...'

                return context

        except Exception:
            pass

        return text[:80] + '...' if len(text) > 80 else text

    def _calculate_confidence(self, misspelling) -> float:
        """Calculate confidence score for a misspelling."""
        if not misspelling.suggestions:
            return 0.5

        # Higher confidence if edit distance is small
        distance = misspelling.suggestions[0].distance
        if distance == 1:
            return 0.95
        elif distance == 2:
            return 0.85
        else:
            return 0.7

    def add_skip_word(self, word: str):
        """Add a word to the skip list."""
        self.SKIP_WORDS.add(word.lower())

    def add_to_dictionary(self, word: str):
        """Add a word to the SymSpell dictionary."""
        if self._symspell:
            self._symspell.add_word(word)

    def add_domain_term(self, word: str, domain: str = None):
        """Add a word to domain dictionary."""
        if self._domain:
            self._domain.add_word(word, domain)
