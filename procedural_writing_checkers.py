"""
AEGIS - Procedural Writing Checkers Module
Version: 3.4.0
Created: February 3, 2026

Provides validation for procedural/instructional writing quality.
All checkers are 100% offline-capable with no external API dependencies.

Checkers included:
1. ImperativeMoodChecker - Validates procedural steps use imperative mood
2. SecondPersonChecker - Prefers "you" over "the user"
3. LinkTextQualityChecker - Flags "click here" and vague link text

Usage:
    from procedural_writing_checkers import get_procedural_checkers
    checkers = get_procedural_checkers()
"""

import re
from typing import Dict, List, Any, Tuple

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
# CHECKER 1: Imperative Mood for Procedures
# =============================================================================

class ImperativeMoodChecker(BaseChecker):
    """
    Validates that procedural steps use imperative mood.

    Good: "Click the button", "Enter your password", "Save the file"
    Bad: "You should click the button", "The user must enter..."

    Imperative mood is direct and clearer for instructions.
    """

    CHECKER_NAME = "Imperative Mood for Procedures"
    CHECKER_VERSION = "3.4.0"

    # Patterns indicating non-imperative instructions
    NON_IMPERATIVE_PATTERNS = [
        # "You should/must/can/will/need to"
        (r'\b(you\s+should\s+)(\w+)', 'you should'),
        (r'\b(you\s+must\s+)(\w+)', 'you must'),
        (r'\b(you\s+need\s+to\s+)(\w+)', 'you need to'),
        (r'\b(you\s+can\s+)(\w+)', 'you can'),
        (r'\b(you\s+will\s+)(\w+)', 'you will'),
        (r'\b(you\s+have\s+to\s+)(\w+)', 'you have to'),
        (r'\b(you\s+may\s+)(\w+)', 'you may'),

        # "The user should/must"
        (r'\b(the\s+user\s+should\s+)(\w+)', 'the user should'),
        (r'\b(the\s+user\s+must\s+)(\w+)', 'the user must'),
        (r'\b(the\s+user\s+can\s+)(\w+)', 'the user can'),
        (r'\b(the\s+user\s+will\s+)(\w+)', 'the user will'),
        (r'\b(the\s+user\s+needs\s+to\s+)(\w+)', 'the user needs to'),

        # "Users should/must"
        (r'\b(users\s+should\s+)(\w+)', 'users should'),
        (r'\b(users\s+must\s+)(\w+)', 'users must'),
        (r'\b(users\s+can\s+)(\w+)', 'users can'),
        (r'\b(users\s+need\s+to\s+)(\w+)', 'users need to'),

        # Other indirect forms
        (r'\b(it\s+is\s+recommended\s+to\s+)(\w+)', 'it is recommended to'),
        (r'\b(it\s+is\s+necessary\s+to\s+)(\w+)', 'it is necessary to'),
        (r'\b(make\s+sure\s+to\s+)(\w+)', 'make sure to'),
        (r'\b(be\s+sure\s+to\s+)(\w+)', 'be sure to'),
        (r'\b(remember\s+to\s+)(\w+)', 'remember to'),
        (r'\b(don\'t\s+forget\s+to\s+)(\w+)', "don't forget to"),
    ]

    # Detect procedural context (numbered/bulleted lists)
    PROCEDURE_INDICATORS = re.compile(
        r'^\s*(?:'
        r'\d+[.)]\s*|'                    # 1. or 1)
        r'[•●○◦▪▫►▸‣⁃-]\s*|'             # Bullet points
        r'[a-z][.)]\s*|'                   # a. or a)
        r'[ivxIVX]+[.)]\s*|'              # Roman numerals
        r'step\s+\d+[:.]\s*|'             # Step 1:
        r'task\s+\d+[:.]\s*'              # Task 1:
        r')',
        re.IGNORECASE | re.MULTILINE
    )

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        compiled_patterns = [(re.compile(p, re.IGNORECASE), d) for p, d in self.NON_IMPERATIVE_PATTERNS]

        for idx, text in paragraphs:
            # Check if this looks like a procedure step
            is_procedure = bool(self.PROCEDURE_INDICATORS.search(text))

            # Also check context for procedure-like content
            procedure_keywords = ['click', 'select', 'enter', 'type', 'press', 'choose',
                                 'navigate', 'open', 'close', 'save', 'submit', 'confirm']
            has_procedure_keywords = any(kw in text.lower() for kw in procedure_keywords)

            if not is_procedure and not has_procedure_keywords:
                continue

            # Remove list markers for analysis
            clean_text = self.PROCEDURE_INDICATORS.sub('', text).strip()

            for pattern, description in compiled_patterns:
                match = pattern.search(clean_text)
                if match:
                    # Extract the verb if captured
                    verb = match.group(2) if match.lastindex >= 2 else ''
                    verb_capitalized = verb.capitalize() if verb else '[verb]'

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Non-imperative in procedure: '{description}...'",
                        context=clean_text[:80] + ('...' if len(clean_text) > 80 else ''),
                        paragraph_index=idx,
                        suggestion=f"Use imperative: '{verb_capitalized}...' instead of '{description}...'",
                        rule_id='IMPER001',
                        flagged_text=match.group(0)
                    ))
                    break  # One issue per paragraph

        return issues[:20]


# =============================================================================
# CHECKER 2: Second Person Preference
# =============================================================================

class SecondPersonChecker(BaseChecker):
    """
    Suggests using "you" instead of "the user" for more direct, engaging writing.

    Good: "You can configure the settings"
    Less engaging: "The user can configure the settings"

    Microsoft and Google style guides prefer second person for documentation.
    """

    CHECKER_NAME = "Second Person Preference"
    CHECKER_VERSION = "3.4.0"

    # Third-person patterns and their second-person alternatives
    THIRD_PERSON_PATTERNS = [
        # "The user" patterns
        (r'\bthe\s+user\s+should\b', 'the user should', 'you should'),
        (r'\bthe\s+user\s+must\b', 'the user must', 'you must'),
        (r'\bthe\s+user\s+can\b', 'the user can', 'you can'),
        (r'\bthe\s+user\s+will\b', 'the user will', 'you will'),
        (r'\bthe\s+user\s+needs?\s+to\b', 'the user needs to', 'you need to'),
        (r'\bthe\s+user\s+has\s+to\b', 'the user has to', 'you have to'),
        (r'\bthe\s+user\s+may\b', 'the user may', 'you may'),
        (r'\bthe\s+user\s+is\s+able\s+to\b', 'the user is able to', 'you can'),

        # "Users" patterns
        (r'\busers\s+should\b', 'users should', 'you should'),
        (r'\busers\s+must\b', 'users must', 'you must'),
        (r'\busers\s+can\b', 'users can', 'you can'),
        (r'\busers\s+will\b', 'users will', 'you will'),
        (r'\busers\s+need\s+to\b', 'users need to', 'you need to'),
        (r'\busers\s+may\b', 'users may', 'you may'),

        # "One" patterns
        (r'\bone\s+should\b', 'one should', 'you should'),
        (r'\bone\s+must\b', 'one must', 'you must'),
        (r'\bone\s+can\b', 'one can', 'you can'),
        (r'\bone\s+will\b', 'one will', 'you will'),

        # "He or she" patterns
        (r'\bhe\s+or\s+she\s+(?:should|must|can|will)\b', 'he or she', 'you'),
        (r'\bhe/she\s+(?:should|must|can|will)\b', 'he/she', 'you'),
        (r'\bs/he\s+(?:should|must|can|will)\b', 's/he', 'you'),

        # Role-specific (when in procedural context)
        (r'\bthe\s+administrator\s+(?:should|must|can|will)\b', 'the administrator', 'you (as administrator)'),
        (r'\bthe\s+operator\s+(?:should|must|can|will)\b', 'the operator', 'you'),
        (r'\bthe\s+customer\s+(?:should|must|can|will)\b', 'the customer', 'you'),
        (r'\bthe\s+reader\s+(?:should|must|can|will)\b', 'the reader', 'you'),
    ]

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        compiled_patterns = [(re.compile(p, re.IGNORECASE), d, r) for p, d, r in self.THIRD_PERSON_PATTERNS]
        found_patterns = set()  # Avoid duplicate flagging

        for idx, text in paragraphs:
            for pattern, description, replacement in compiled_patterns:
                if description in found_patterns:
                    continue

                match = pattern.search(text)
                if match:
                    found_patterns.add(description)

                    # Get context
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]

                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Third person '{description}' - consider second person",
                        context=f"...{context}...",
                        paragraph_index=idx,
                        suggestion=f"Use '{replacement}' for more direct, engaging writing",
                        rule_id='SECOND001',
                        flagged_text=match.group(),
                        replacement_text=replacement
                    ))

        return issues[:15]


# =============================================================================
# CHECKER 3: Link Text Quality
# =============================================================================

class LinkTextQualityChecker(BaseChecker):
    """
    Flags vague or unhelpful link text like "click here" or "here".

    Good: "See the Installation Guide", "Download the configuration file"
    Bad: "Click here", "here", "read more"

    Good link text describes the destination, improving accessibility and usability.
    """

    CHECKER_NAME = "Link Text Quality"
    CHECKER_VERSION = "3.4.0"

    # Bad link text patterns
    BAD_LINK_PATTERNS = [
        # "Click here" variants
        (r'\bclick\s+here\b', 'click here', 'Describe the link destination'),
        (r'\bclick\s+on\s+this\s+link\b', 'click on this link', 'Describe the destination'),
        (r'\bclick\s+this\b', 'click this', 'Describe what will be clicked'),

        # Standalone "here"
        (r'\bhere\b(?=\s*[.,;:)]|\s*$|\s+(?:for|to|if))', 'here', 'Name the destination'),

        # "Read more" variants
        (r'\bread\s+more\b', 'read more', 'Specify what will be read'),
        (r'\blearn\s+more\b', 'learn more', 'Specify the topic'),
        (r'\bfind\s+out\s+more\b', 'find out more', 'Specify the topic'),
        (r'\bsee\s+more\b', 'see more', 'Specify the content'),

        # "More info" variants
        (r'\bmore\s+info(?:rmation)?\b', 'more info/information', 'Specify the topic'),
        (r'\badditional\s+info(?:rmation)?\b', 'additional information', 'Specify the topic'),

        # Generic references
        (r'\bthis\s+link\b', 'this link', 'Name the destination'),
        (r'\bthis\s+page\b', 'this page', 'Name the page'),
        (r'\bthis\s+article\b', 'this article', 'Name the article'),
        (r'\bgo\s+here\b', 'go here', 'Describe the destination'),
        (r'\bvisit\s+this\b', 'visit this', 'Name what to visit'),

        # Action-only (no destination)
        (r'\bdownload\b(?=\s*[.,;:)]|\s*$)', 'download', 'Name the file: "Download the User Guide"'),
        (r'\bsubscribe\b(?=\s*[.,;:)]|\s*$)', 'subscribe', 'Specify: "Subscribe to updates"'),
    ]

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        compiled_patterns = [(re.compile(p, re.IGNORECASE), d, s) for p, d, s in self.BAD_LINK_PATTERNS]
        found_patterns = set()

        for idx, text in paragraphs:
            for pattern, description, suggestion in compiled_patterns:
                if description in found_patterns:
                    continue

                for match in pattern.finditer(text):
                    found_patterns.add(description)

                    # Get context
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Vague link text: '{match.group()}'",
                        context=f"...{context}...",
                        paragraph_index=idx,
                        suggestion=f"{suggestion}. Example: 'See the Installation Guide' instead of 'click here'",
                        rule_id='LINK001',
                        flagged_text=match.group()
                    ))
                    break  # One per pattern per paragraph

        return issues


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_procedural_checkers() -> Dict[str, BaseChecker]:
    """
    Returns a dictionary of all procedural writing checker instances.

    Used by core.py to register checkers in bulk.
    """
    return {
        'imperative_mood': ImperativeMoodChecker(),
        'second_person': SecondPersonChecker(),
        'link_text_quality': LinkTextQualityChecker(),
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    # Demo text with intentional issues
    demo_text = """
    1. You should click the Save button to save your work.
    2. The user must enter a valid email address.
    3. Users can configure the settings as needed.

    To learn more, click here. For additional information, read more about
    the configuration options here.

    The administrator should review the logs daily. One must always verify
    the backup before proceeding.

    Step 4: You need to select the appropriate option from the dropdown menu.
    """

    paragraphs = [(i, p.strip()) for i, p in enumerate(demo_text.split('\n\n')) if p.strip()]

    print("=== Procedural Writing Checkers Demo ===\n")

    checkers = get_procedural_checkers()

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(paragraphs, full_text=demo_text)

        if issues:
            for issue in issues[:4]:
                print(f"  [{issue.get('severity', 'Info')}] {issue.get('message', '')}")
                if issue.get('suggestion'):
                    print(f"    Suggestion: {issue.get('suggestion', '')[:70]}...")
        else:
            print("  No issues found")

    print(f"\n\nTotal checkers: {len(checkers)}")
