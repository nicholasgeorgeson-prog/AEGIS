"""
AEGIS - Clarity Checkers Module
Version: 3.4.0
Created: February 3, 2026

Provides clarity and readability validation for technical documentation.
All checkers are 100% offline-capable with no external API dependencies.

Checkers included:
1. FutureTenseChecker - Detects future tense in documentation
2. LatinAbbreviationChecker - Warns about i.e., e.g., etc.
3. SentenceInitialConjunctionChecker - Flags sentences starting with And, But, So
4. DirectionalLanguageChecker - Flags "above", "below", "left", "right"
5. TimeSensitiveLanguageChecker - Flags "currently", "now", "recently"

Usage:
    from clarity_checkers import get_clarity_checkers
    checkers = get_clarity_checkers()
"""

import re
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

# Import base checker
try:
    from base_checker import BaseChecker
except ImportError:
    class BaseChecker:
        CHECKER_NAME = "Base"
        CHECKER_VERSION = "1.0.0"
        def __init__(self, enabled=True):
            self.enabled = enabled
        def create_issue(self, **kwargs):
            return {'category': self.CHECKER_NAME, **kwargs}


# =============================================================================
# CHECKER 1: Future Tense Detector
# =============================================================================

class FutureTenseChecker(BaseChecker):
    """
    Detects future tense usage in technical documentation.

    Technical documentation should generally use present tense to describe
    current behavior. Future tense ("will display", "will be shown") can
    make documentation feel tentative and may become inaccurate over time.

    Excludes requirement contexts where "shall" is appropriate.
    """

    CHECKER_NAME = "Future Tense Detector"
    CHECKER_VERSION = "3.4.0"

    # Future tense patterns
    FUTURE_PATTERNS = [
        (r'\bwill\s+be\s+\w+(?:ed|ing)\b', 'will be'),
        (r'\bwill\s+\w+\b', 'will'),
        (r'\bis\s+going\s+to\s+\w+\b', 'is going to'),
        (r'\bare\s+going\s+to\s+\w+\b', 'are going to'),
        (r'\bgoing\s+to\s+be\s+\w+\b', 'going to be'),
        (r'\bshall\s+be\s+\w+(?:ed|ing)\b', 'shall be'),  # Non-requirement context
    ]

    # Context indicators for requirements (skip these)
    REQUIREMENT_CONTEXT = re.compile(
        r'\b(shall|must|required|mandatory|contractor|government|compliance|obligation)\b',
        re.IGNORECASE
    )

    # Skip patterns (legitimate future references)
    SKIP_PATTERNS = [
        r'\bwill\s+not\s+be\s+(?:responsible|liable|covered)\b',  # Legal disclaimers
        r'\bfuture\s+releases?\s+will\b',  # Roadmap language
        r'\bplanned\s+.{0,20}\s+will\b',  # Planned features
    ]

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        skip_compiled = [re.compile(p, re.IGNORECASE) for p in self.SKIP_PATTERNS]

        for idx, text in paragraphs:
            # Skip if paragraph contains requirement language
            if self.REQUIREMENT_CONTEXT.search(text):
                continue

            # Skip certain legitimate patterns
            if any(p.search(text) for p in skip_compiled):
                continue

            for pattern, future_word in self.FUTURE_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Additional context check for "shall"
                    if future_word == 'shall be':
                        # Check if this is requirement language
                        context_start = max(0, match.start() - 50)
                        context = text[context_start:match.start()].lower()
                        if any(w in context for w in ['contractor', 'system', 'software', 'requirement']):
                            continue

                    # Get surrounding context
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]

                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Future tense detected: '{match.group()}'",
                        context=f"...{context}...",
                        paragraph_index=idx,
                        suggestion="Consider present tense: describes current behavior, not future",
                        rule_id='FUTURE001',
                        flagged_text=match.group()
                    ))

        return issues[:20]  # Limit issues


# =============================================================================
# CHECKER 2: Latin Abbreviation Warnings
# =============================================================================

class LatinAbbreviationChecker(BaseChecker):
    """
    Warns about Latin abbreviations that may confuse global audiences.

    Microsoft and Google style guides recommend spelling out Latin abbreviations
    for clarity, especially in technical documentation read by non-native speakers.
    """

    CHECKER_NAME = "Latin Abbreviation Warnings"
    CHECKER_VERSION = "3.4.0"

    # Latin abbreviations with replacements and severity
    # Format: 'abbrev': ('replacement', 'severity')
    LATIN_ABBREVIATIONS = {
        'i.e.': ('that is', 'Medium'),
        'i.e.,': ('that is,', 'Medium'),
        'e.g.': ('for example', 'Medium'),
        'e.g.,': ('for example,', 'Medium'),
        'etc.': ('and so on', 'Low'),
        'et al.': ('and others', 'Low'),
        'viz.': ('namely', 'Medium'),
        'cf.': ('compare', 'Medium'),
        'ibid.': ('in the same source', 'Low'),
        'op. cit.': ('in the work cited', 'Low'),
        'ca.': ('approximately', 'Medium'),
        'n.b.': ('note', 'Medium'),
        'p.s.': ('postscript', 'Low'),
        'per se': ('by itself', 'Low'),
        'vice versa': ('the other way around', 'Low'),
        'et cetera': ('and so on', 'Low'),
        'ad hoc': ('for this purpose', 'Low'),
        'de facto': ('in practice', 'Low'),
        'in situ': ('in place', 'Low'),
        'in vitro': ('in glass/laboratory', 'Low'),
        'in vivo': ('in living organism', 'Low'),
        'pro forma': ('as a formality', 'Low'),
        'quid pro quo': ('something for something', 'Medium'),
        're:': ('regarding', 'Low'),
        'vs.': ('versus', 'Low'),
        'vs': ('versus', 'Low'),
    }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        found_abbrevs = set()  # Avoid duplicate flagging

        for idx, text in paragraphs:
            for abbrev, (replacement, severity) in self.LATIN_ABBREVIATIONS.items():
                if abbrev.lower() in found_abbrevs:
                    continue

                # Build pattern (case-insensitive for most)
                if abbrev in ['i.e.', 'e.g.', 'n.b.']:
                    # These are often lowercase
                    pattern = re.compile(r'\b' + re.escape(abbrev), re.IGNORECASE)
                else:
                    pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b', re.IGNORECASE)

                for match in pattern.finditer(text):
                    found_abbrevs.add(abbrev.lower())

                    # Get context
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]

                    issues.append(self.create_issue(
                        severity=severity,
                        message=f"Latin abbreviation '{match.group()}' may confuse global audiences",
                        context=f"...{context}...",
                        paragraph_index=idx,
                        suggestion=f"Consider: '{replacement}'",
                        rule_id='LATIN001',
                        flagged_text=match.group(),
                        replacement_text=replacement
                    ))
                    break  # One instance per abbreviation per paragraph

        return issues


# =============================================================================
# CHECKER 3: Sentence-Initial Conjunction
# =============================================================================

class SentenceInitialConjunctionChecker(BaseChecker):
    """
    Flags sentences that begin with coordinating conjunctions.

    Starting sentences with "And", "But", "So" is informal and may not be
    appropriate for technical documentation. Suggests alternatives.
    """

    CHECKER_NAME = "Sentence-Initial Conjunction"
    CHECKER_VERSION = "3.4.0"

    # Conjunctions and their alternatives
    CONJUNCTIONS = {
        'and': 'Additionally, Furthermore, Moreover, Also',
        'but': 'However, Nevertheless, Yet, Nonetheless',
        'so': 'Therefore, Consequently, As a result, Thus',
        'or': 'Alternatively, Otherwise',
        'yet': 'However, Nevertheless, Still',
        'for': 'Because, Since, As',
        'nor': 'Neither (restructure sentence)',
    }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence or len(sentence) < 3:
                    continue

                # Get first word
                words = sentence.split()
                if not words:
                    continue

                first_word = words[0]
                # Remove any leading punctuation (quotes, etc.)
                first_word_clean = re.sub(r'^[^\w]+', '', first_word).lower()

                if first_word_clean in self.CONJUNCTIONS:
                    alternatives = self.CONJUNCTIONS[first_word_clean]

                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Sentence begins with conjunction '{first_word}'",
                        context=sentence[:80] + ('...' if len(sentence) > 80 else ''),
                        paragraph_index=idx,
                        suggestion=f"Consider: {alternatives}; or combine with previous sentence",
                        rule_id='CONJ001',
                        flagged_text=first_word
                    ))

        return issues[:15]  # Limit


# =============================================================================
# CHECKER 4: Directional Language
# =============================================================================

class DirectionalLanguageChecker(BaseChecker):
    """
    Flags directional references that may break in responsive/reflowable content.

    References like "see above", "the figure below", "on the left" assume a
    fixed layout that may not exist in all output formats (mobile, PDF reflow, etc.).
    """

    CHECKER_NAME = "Directional Language"
    CHECKER_VERSION = "3.4.0"

    # Directional patterns and their types
    DIRECTIONAL_PATTERNS = [
        # Vertical references
        (r'\b(?:see|shown|displayed|illustrated|described)\s+(?:in\s+the\s+)?(?:section\s+)?(?:above|below)\b', 'vertical'),
        (r'\bthe\s+(?:above|below)\s+(?:figure|table|diagram|image|section|paragraph|example|list)\b', 'vertical'),
        (r'\b(?:above|below)\s+(?:figure|table|diagram|image)\b', 'vertical'),
        (r'\bas\s+(?:shown|described|mentioned|noted)\s+(?:above|below)\b', 'vertical'),
        (r'\b(?:refer|see)\s+(?:above|below)\b', 'vertical'),

        # Horizontal references
        (r'\b(?:to\s+the\s+)?(?:left|right)\s+(?:of|side)\b', 'horizontal'),
        (r'\bon\s+the\s+(?:left|right)(?:\s+side)?\b', 'horizontal'),
        (r'\b(?:left|right)[-\s]hand\s+(?:side|column|panel)\b', 'horizontal'),

        # Page references
        (r'\b(?:on\s+the\s+)?(?:previous|next|following)\s+page\b', 'page'),
        (r'\boverleaf\b', 'page'),
        (r'\bsee\s+(?:the\s+)?(?:facing|opposite)\s+page\b', 'page'),

        # Relative position
        (r'\b(?:the\s+)?(?:preceding|subsequent)\s+(?:section|chapter|paragraph)\b', 'relative'),
    ]

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        compiled_patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in self.DIRECTIONAL_PATTERNS]

        for idx, text in paragraphs:
            for pattern, ref_type in compiled_patterns:
                for match in pattern.finditer(text):
                    # Get context
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end]

                    if ref_type == 'vertical':
                        suggestion = "Use explicit references: 'See Figure 3' or 'Section 2.1 describes...'"
                    elif ref_type == 'horizontal':
                        suggestion = "Use explicit references: 'In the Navigation panel' or 'Column A contains...'"
                    elif ref_type == 'page':
                        suggestion = "Use section/figure numbers: 'See Section 4.2' (page numbers change)"
                    else:
                        suggestion = "Use explicit section numbers or titles"

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Directional reference ({ref_type}) may not work in all formats",
                        context=f"...{context}...",
                        paragraph_index=idx,
                        suggestion=suggestion,
                        rule_id='DIRECT001',
                        flagged_text=match.group()
                    ))

        return issues[:15]


# =============================================================================
# CHECKER 5: Time-Sensitive Language
# =============================================================================

class TimeSensitiveLanguageChecker(BaseChecker):
    """
    Flags time-sensitive language that may cause documentation to become outdated.

    Words like "currently", "now", "recently", "soon", "new" create maintenance
    burden and can make documentation feel stale or inaccurate over time.
    """

    CHECKER_NAME = "Time-Sensitive Language"
    CHECKER_VERSION = "3.4.0"

    # Time-sensitive words/phrases and suggested alternatives
    TIME_SENSITIVE = {
        # Present time references
        'currently': 'as of [VERSION/DATE]',
        'now': 'as of [VERSION/DATE]',
        'at present': 'as of [VERSION/DATE]',
        'presently': 'as of [VERSION/DATE]',
        'at this time': 'as of [VERSION/DATE]',
        'at the moment': 'as of [VERSION/DATE]',
        'as of now': 'as of [SPECIFIC DATE]',

        # Past references
        'recently': 'in [MONTH/YEAR] or [VERSION]',
        'lately': 'in [MONTH/YEAR]',
        'just added': 'added in [VERSION]',
        'newly added': 'added in [VERSION]',

        # Future references
        'soon': 'in [TIMEFRAME] or [VERSION]',
        'shortly': 'in [TIMEFRAME]',
        'in the near future': 'by [DATE] or in [VERSION]',
        'in the future': 'in a future version',
        'upcoming': 'scheduled for [DATE/VERSION]',
        'coming soon': 'planned for [VERSION]',

        # Relative newness
        'new': 'introduced in [VERSION]',
        'latest': '[VERSION] (released [DATE])',
        'newest': '[VERSION]',
        'modern': '[SPECIFY WHAT MAKES IT MODERN]',
        'cutting-edge': '[SPECIFY TECHNOLOGY]',
        'state-of-the-art': '[SPECIFY CAPABILITY]',

        # Calendar references
        'today': '[ACTUAL DATE]',
        'yesterday': '[ACTUAL DATE]',
        'tomorrow': '[ACTUAL DATE]',
        'this week': '[DATE RANGE]',
        'last week': '[DATE RANGE]',
        'next week': '[DATE RANGE]',
        'this month': '[MONTH YEAR]',
        'last month': '[MONTH YEAR]',
        'next month': '[MONTH YEAR]',
        'this year': '[YEAR]',
        'last year': '[YEAR]',
        'next year': '[YEAR]',
    }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        found_phrases = set()  # Avoid duplicate flagging

        for idx, text in paragraphs:
            text_lower = text.lower()

            for phrase, suggestion in self.TIME_SENSITIVE.items():
                if phrase in found_phrases:
                    continue

                if phrase in text_lower:
                    # Find actual match with original case
                    pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
                    match = pattern.search(text)

                    if match:
                        found_phrases.add(phrase)

                        # Get context
                        start = max(0, match.start() - 30)
                        end = min(len(text), match.end() + 30)
                        context = text[start:end]

                        issues.append(self.create_issue(
                            severity='Low',
                            message=f"Time-sensitive: '{match.group()}' may become outdated",
                            context=f"...{context}...",
                            paragraph_index=idx,
                            suggestion=f"Consider specific dates/versions: {suggestion}",
                            rule_id='TIME001',
                            flagged_text=match.group()
                        ))

        return issues[:15]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_clarity_checkers() -> Dict[str, BaseChecker]:
    """
    Returns a dictionary of all clarity checker instances.

    Used by core.py to register checkers in bulk.
    """
    return {
        'future_tense': FutureTenseChecker(),
        'latin_abbreviations': LatinAbbreviationChecker(),
        'sentence_initial_conjunction': SentenceInitialConjunctionChecker(),
        'directional_language': DirectionalLanguageChecker(),
        'time_sensitive_language': TimeSensitiveLanguageChecker(),
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    # Demo text with intentional issues
    demo_text = """
    The system will display a confirmation message. Users can also see the settings
    that are going to be applied.

    For example, e.g., you might want to configure the timeout. I.e., the time
    before the system disconnects. Etc.

    And this is another sentence. But wait, there's more. So we continue here.

    See the figure above for more details. The button on the left side will
    open the menu shown below.

    Currently, the system supports JSON format. This new feature was recently
    added. Soon we will add XML support as well.
    """

    paragraphs = [(i, p.strip()) for i, p in enumerate(demo_text.split('\n\n')) if p.strip()]

    print("=== Clarity Checkers Demo ===\n")

    checkers = get_clarity_checkers()

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(paragraphs, full_text=demo_text)

        if issues:
            for issue in issues[:3]:
                print(f"  [{issue.get('severity', 'Info')}] {issue.get('message', '')}")
                if issue.get('suggestion'):
                    print(f"    Suggestion: {issue.get('suggestion', '')[:70]}...")
        else:
            print("  No issues found")

    print(f"\n\nTotal checkers: {len(checkers)}")
