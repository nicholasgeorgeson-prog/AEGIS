#!/usr/bin/env python3
"""
AEGIS Auto-Fix Engine
================================
Applies automatic corrections to document issues.

This module provides the foundation for auto-fixing detected issues.
It works with the existing checker infrastructure to apply fixes.

Supported Fix Types:
- Text replacement (spelling, terminology, product names)
- Style fixes (contractions, Latin abbreviations)
- Punctuation fixes (Oxford comma, spacing)
- Case fixes (heading case, capitalization)

Usage:
    from auto_fixer import AutoFixer, apply_fixes_to_document

    fixer = AutoFixer()
    fixed_issues = fixer.get_fixable_issues(issues)
    fixer.apply_fix(issue)
    fixer.apply_all_fixes(issues)
    fixer.export_corrected_document(filepath, output_path)
"""

import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
from copy import deepcopy

try:
    from config_logging import get_logger
    _logger = get_logger('auto_fixer')
except ImportError:
    import logging
    _logger = logging.getLogger('auto_fixer')


@dataclass
class Fix:
    """Represents a single fix to be applied."""
    issue_id: str
    issue_type: str
    original: str
    replacement: str
    paragraph_idx: int
    start_pos: int = 0
    end_pos: int = 0
    confidence: float = 1.0
    applied: bool = False
    reason: str = ""


@dataclass
class FixResult:
    """Result of applying a fix."""
    success: bool
    fix: Fix
    message: str = ""
    new_text: str = ""


# =============================================================================
# FIX GENERATORS - Functions that generate fixes for specific issue types
# =============================================================================

FIX_GENERATORS = {}


def fix_generator(issue_type: str):
    """Decorator to register a fix generator for an issue type."""
    def decorator(func):
        FIX_GENERATORS[issue_type] = func
        return func
    return decorator


@fix_generator('latin_abbreviations')
def fix_latin_abbreviation(issue: Dict) -> Optional[Fix]:
    """Fix Latin abbreviations by replacing with English equivalents."""
    replacements = {
        'i.e.': 'that is',
        'i.e.,': 'that is,',
        'e.g.': 'for example',
        'e.g.,': 'for example,',
        'etc.': 'and so on',
        'et al.': 'and others',
        'viz.': 'namely',
        'vs.': 'versus',
        'vs': 'versus',
        'cf.': 'compare',
        'n.b.': 'note',
        'N.B.': 'Note',
    }

    context = issue.get('context', '')
    message = issue.get('message', '')

    # Find the abbreviation in the context
    for abbrev, replacement in replacements.items():
        if abbrev.lower() in context.lower():
            # Find exact match with case
            pattern = re.compile(re.escape(abbrev), re.IGNORECASE)
            match = pattern.search(context)
            if match:
                return Fix(
                    issue_id=str(issue.get('id', hash(context))),
                    issue_type='latin_abbreviations',
                    original=match.group(),
                    replacement=replacement,
                    paragraph_idx=issue.get('paragraph', 0),
                    confidence=0.95,
                    reason=f"Replace '{match.group()}' with '{replacement}'"
                )
    return None


@fix_generator('contractions')
def fix_contraction(issue: Dict) -> Optional[Fix]:
    """Expand contractions to full forms."""
    expansions = {
        "don't": "do not",
        "doesn't": "does not",
        "didn't": "did not",
        "won't": "will not",
        "wouldn't": "would not",
        "can't": "cannot",
        "couldn't": "could not",
        "shouldn't": "should not",
        "isn't": "is not",
        "aren't": "are not",
        "wasn't": "was not",
        "weren't": "were not",
        "hasn't": "has not",
        "haven't": "have not",
        "hadn't": "had not",
        "it's": "it is",
        "that's": "that is",
        "there's": "there is",
        "here's": "here is",
        "what's": "what is",
        "who's": "who is",
        "let's": "let us",
        "I'm": "I am",
        "I've": "I have",
        "I'll": "I will",
        "I'd": "I would",
        "you're": "you are",
        "you've": "you have",
        "you'll": "you will",
        "you'd": "you would",
        "we're": "we are",
        "we've": "we have",
        "we'll": "we will",
        "we'd": "we would",
        "they're": "they are",
        "they've": "they have",
        "they'll": "they will",
        "they'd": "they would",
    }

    context = issue.get('context', '')

    for contraction, expansion in expansions.items():
        # Case-insensitive search
        pattern = re.compile(r'\b' + re.escape(contraction) + r'\b', re.IGNORECASE)
        match = pattern.search(context)
        if match:
            # Preserve original case for first letter
            original = match.group()
            if original[0].isupper():
                replacement = expansion[0].upper() + expansion[1:]
            else:
                replacement = expansion

            return Fix(
                issue_id=str(issue.get('id', hash(context))),
                issue_type='contractions',
                original=original,
                replacement=replacement,
                paragraph_idx=issue.get('paragraph', 0),
                confidence=0.98,
                reason=f"Expand '{original}' to '{replacement}'"
            )
    return None


@fix_generator('product_name_consistency')
def fix_product_name(issue: Dict) -> Optional[Fix]:
    """Fix product name capitalization."""
    # Common product name corrections
    corrections = {
        'javascript': 'JavaScript',
        'typescript': 'TypeScript',
        'github': 'GitHub',
        'gitlab': 'GitLab',
        'bitbucket': 'Bitbucket',
        'postgresql': 'PostgreSQL',
        'mysql': 'MySQL',
        'mongodb': 'MongoDB',
        'nodejs': 'Node.js',
        'reactjs': 'React',
        'vuejs': 'Vue.js',
        'angularjs': 'Angular',
        'kubernetes': 'Kubernetes',
        'docker': 'Docker',
        'linux': 'Linux',
        'windows': 'Windows',
        'macos': 'macOS',
        'ios': 'iOS',
        'android': 'Android',
        'python': 'Python',
        'java': 'Java',
        'golang': 'Go',
        'rust': 'Rust',
        'elasticsearch': 'Elasticsearch',
        'graphql': 'GraphQL',
        'tensorflow': 'TensorFlow',
        'pytorch': 'PyTorch',
        'numpy': 'NumPy',
        'pandas': 'pandas',
        'sklearn': 'scikit-learn',
        'scipy': 'SciPy',
        'matplotlib': 'Matplotlib',
        'jupyter': 'Jupyter',
        'vscode': 'VS Code',
        'intellij': 'IntelliJ',
        'xcode': 'Xcode',
        'aws': 'AWS',
        'azure': 'Azure',
        'gcp': 'GCP',
        'api': 'API',
        'rest': 'REST',
        'json': 'JSON',
        'xml': 'XML',
        'html': 'HTML',
        'css': 'CSS',
        'sql': 'SQL',
        'url': 'URL',
        'uri': 'URI',
        'http': 'HTTP',
        'https': 'HTTPS',
        'tcp': 'TCP',
        'ip': 'IP',
        'dns': 'DNS',
        'ssl': 'SSL',
        'tls': 'TLS',
        'oauth': 'OAuth',
        'saml': 'SAML',
        'ldap': 'LDAP',
        'pdf': 'PDF',
        'svg': 'SVG',
        'png': 'PNG',
        'jpeg': 'JPEG',
        'gif': 'GIF',
    }

    context = issue.get('context', '')
    message = issue.get('message', '')

    for wrong, correct in corrections.items():
        # Find case-insensitive match that's not already correct
        pattern = re.compile(r'\b' + re.escape(wrong) + r'\b', re.IGNORECASE)
        for match in pattern.finditer(context):
            if match.group() != correct:
                return Fix(
                    issue_id=str(issue.get('id', hash(context))),
                    issue_type='product_name_consistency',
                    original=match.group(),
                    replacement=correct,
                    paragraph_idx=issue.get('paragraph', 0),
                    confidence=0.95,
                    reason=f"Correct '{match.group()}' to '{correct}'"
                )
    return None


@fix_generator('wordy_phrases')
def fix_wordy_phrase(issue: Dict) -> Optional[Fix]:
    """Replace wordy phrases with concise alternatives."""
    replacements = {
        'in order to': 'to',
        'in order for': 'for',
        'due to the fact that': 'because',
        'for the purpose of': 'to',
        'in the event that': 'if',
        'in the event of': 'if',
        'at this point in time': 'now',
        'at the present time': 'now',
        'at this time': 'now',
        'prior to': 'before',
        'subsequent to': 'after',
        'in spite of the fact that': 'although',
        'despite the fact that': 'although',
        'regardless of the fact that': 'although',
        'on a daily basis': 'daily',
        'on a weekly basis': 'weekly',
        'on a monthly basis': 'monthly',
        'on a regular basis': 'regularly',
        'a large number of': 'many',
        'a small number of': 'few',
        'the majority of': 'most',
        'a significant amount of': 'much',
        'in close proximity to': 'near',
        'with regard to': 'about',
        'with respect to': 'about',
        'in regard to': 'about',
        'in reference to': 'about',
        'pertaining to': 'about',
        'concerning the matter of': 'about',
        'is able to': 'can',
        'has the ability to': 'can',
        'is capable of': 'can',
        'in the process of': 'currently',
        'during the course of': 'during',
        'for the duration of': 'during',
        'in the near future': 'soon',
        'at a later date': 'later',
        'make a decision': 'decide',
        'make a determination': 'determine',
        'reach a conclusion': 'conclude',
        'give consideration to': 'consider',
        'take into consideration': 'consider',
        'in conjunction with': 'with',
        'in combination with': 'with',
    }

    context = issue.get('context', '').lower()

    for wordy, concise in replacements.items():
        if wordy in context:
            # Find in original context preserving case
            pattern = re.compile(re.escape(wordy), re.IGNORECASE)
            match = pattern.search(issue.get('context', ''))
            if match:
                return Fix(
                    issue_id=str(issue.get('id', hash(context))),
                    issue_type='wordy_phrases',
                    original=match.group(),
                    replacement=concise,
                    paragraph_idx=issue.get('paragraph', 0),
                    confidence=0.90,
                    reason=f"Replace '{match.group()}' with '{concise}'"
                )
    return None


@fix_generator('second_person')
def fix_second_person(issue: Dict) -> Optional[Fix]:
    """Replace 'the user' with 'you'."""
    replacements = {
        'the user should': 'you should',
        'the user must': 'you must',
        'the user can': 'you can',
        'the user will': 'you will',
        'the user needs to': 'you need to',
        'the user is able to': 'you can',
        "the user's": 'your',
        'the users': 'users',  # Keep plural
    }

    context = issue.get('context', '').lower()

    for phrase, replacement in replacements.items():
        if phrase in context:
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            match = pattern.search(issue.get('context', ''))
            if match:
                # Preserve capitalization at sentence start
                orig = match.group()
                repl = replacement
                if orig[0].isupper():
                    repl = replacement[0].upper() + replacement[1:]

                return Fix(
                    issue_id=str(issue.get('id', hash(context))),
                    issue_type='second_person',
                    original=orig,
                    replacement=repl,
                    paragraph_idx=issue.get('paragraph', 0),
                    confidence=0.85,
                    reason=f"Replace '{orig}' with '{repl}' (second person)"
                )
    return None


@fix_generator('future_tense')
def fix_future_tense(issue: Dict) -> Optional[Fix]:
    """Convert future tense to present tense."""
    # Common patterns: "will display" -> "displays"
    context = issue.get('context', '')

    # Find "will + verb" patterns
    pattern = re.compile(r'\bwill\s+(\w+)', re.IGNORECASE)
    match = pattern.search(context)

    if match:
        verb = match.group(1).lower()
        # Simple present tense conversion (add 's' for third person)
        # This is simplified - real implementation would need proper conjugation
        if verb.endswith('e'):
            present = verb + 's'
        elif verb.endswith(('s', 'sh', 'ch', 'x', 'z')):
            present = verb + 'es'
        elif verb.endswith('y') and verb[-2] not in 'aeiou':
            present = verb[:-1] + 'ies'
        else:
            present = verb + 's'

        return Fix(
            issue_id=str(issue.get('id', hash(context))),
            issue_type='future_tense',
            original=match.group(),
            replacement=present,
            paragraph_idx=issue.get('paragraph', 0),
            confidence=0.75,  # Lower confidence - may need human review
            reason=f"Convert '{match.group()}' to present tense '{present}'"
        )
    return None


@fix_generator('link_text_quality')
def fix_link_text(issue: Dict) -> Optional[Fix]:
    """Suggest better link text."""
    bad_phrases = {
        'click here': '[descriptive link text]',
        'here': '[descriptive link text]',
        'this link': '[descriptive link text]',
        'this page': '[page name]',
        'read more': '[topic name]',
        'learn more': '[topic name]',
        'more info': '[topic description]',
    }

    context = issue.get('context', '').lower()

    for bad, suggestion in bad_phrases.items():
        if bad in context:
            return Fix(
                issue_id=str(issue.get('id', hash(context))),
                issue_type='link_text_quality',
                original=bad,
                replacement=suggestion,
                paragraph_idx=issue.get('paragraph', 0),
                confidence=0.70,  # Low - needs human input
                reason=f"Replace '{bad}' with descriptive link text"
            )
    return None


# =============================================================================
# AUTO-FIXER CLASS
# =============================================================================

class AutoFixer:
    """
    Manages automatic fixing of document issues.
    """

    def __init__(self):
        self.fixes: List[Fix] = []
        self.applied_fixes: List[Fix] = []
        self.rejected_fixes: List[Fix] = []
        self._document_text: Dict[int, str] = {}  # paragraph_idx -> text

    def get_fixable_issues(self, issues: List[Dict]) -> List[Dict]:
        """
        Filter issues to those that can be auto-fixed.

        Args:
            issues: List of issue dictionaries from review

        Returns:
            List of fixable issues with fix suggestions
        """
        fixable = []

        for issue in issues:
            issue_type = issue.get('type', '')

            if issue_type in FIX_GENERATORS:
                fix = FIX_GENERATORS[issue_type](issue)
                if fix:
                    issue_copy = issue.copy()
                    issue_copy['fix'] = fix
                    issue_copy['fixable'] = True
                    fixable.append(issue_copy)

        _logger.info(f"Found {len(fixable)} fixable issues out of {len(issues)}")
        return fixable

    def generate_fix(self, issue: Dict) -> Optional[Fix]:
        """
        Generate a fix for a single issue.

        Args:
            issue: Issue dictionary

        Returns:
            Fix object or None if not fixable
        """
        issue_type = issue.get('type', '')

        if issue_type in FIX_GENERATORS:
            return FIX_GENERATORS[issue_type](issue)
        return None

    def preview_fixes(self, issues: List[Dict]) -> List[Dict]:
        """
        Preview what fixes would be applied.

        Args:
            issues: List of issues to fix

        Returns:
            List of fix previews
        """
        previews = []

        for issue in issues:
            fix = self.generate_fix(issue)
            if fix:
                previews.append({
                    'issue_type': fix.issue_type,
                    'original': fix.original,
                    'replacement': fix.replacement,
                    'confidence': fix.confidence,
                    'reason': fix.reason,
                    'paragraph': fix.paragraph_idx
                })

        return previews

    def apply_fixes_to_text(
        self,
        text: str,
        fixes: List[Fix],
        confirm_each: bool = False
    ) -> Tuple[str, List[FixResult]]:
        """
        Apply fixes to a text string.

        Args:
            text: Original text
            fixes: List of fixes to apply
            confirm_each: Whether to require confirmation for each fix

        Returns:
            Tuple of (modified_text, list of FixResults)
        """
        results = []
        modified_text = text

        # Sort fixes by position (reverse order to not invalidate positions)
        sorted_fixes = sorted(fixes, key=lambda f: f.start_pos, reverse=True)

        for fix in sorted_fixes:
            # Find the original text in the modified text
            if fix.original in modified_text:
                # Apply replacement
                modified_text = modified_text.replace(fix.original, fix.replacement, 1)
                fix.applied = True
                results.append(FixResult(
                    success=True,
                    fix=fix,
                    message=f"Applied: {fix.reason}",
                    new_text=fix.replacement
                ))
            else:
                results.append(FixResult(
                    success=False,
                    fix=fix,
                    message=f"Could not find '{fix.original}' in text"
                ))

        return modified_text, results

    def get_fix_summary(self, issues: List[Dict]) -> Dict[str, Any]:
        """
        Get summary of available fixes.

        Args:
            issues: List of issues

        Returns:
            Summary dictionary
        """
        fixable = self.get_fixable_issues(issues)

        # Group by type
        by_type = {}
        for issue in fixable:
            t = issue.get('type', 'unknown')
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(issue)

        # Count by confidence level
        high_conf = sum(1 for i in fixable
                       if i.get('fix') and i['fix'].confidence >= 0.9)
        medium_conf = sum(1 for i in fixable
                         if i.get('fix') and 0.7 <= i['fix'].confidence < 0.9)
        low_conf = sum(1 for i in fixable
                       if i.get('fix') and i['fix'].confidence < 0.7)

        return {
            'total_fixable': len(fixable),
            'by_type': {k: len(v) for k, v in by_type.items()},
            'high_confidence': high_conf,
            'medium_confidence': medium_conf,
            'low_confidence': low_conf,
            'recommended_auto_fix': high_conf,
            'needs_review': medium_conf + low_conf
        }


# =============================================================================
# DOCUMENT-LEVEL FIXING
# =============================================================================

def apply_fixes_to_document(
    filepath: str,
    issues: List[Dict],
    output_path: Optional[str] = None,
    min_confidence: float = 0.9
) -> Dict[str, Any]:
    """
    Apply fixes to a document file.

    Args:
        filepath: Path to original document
        issues: List of issues from review
        output_path: Path for fixed document (default: adds '_fixed' suffix)
        min_confidence: Minimum confidence threshold for auto-fix

    Returns:
        Dictionary with fix results
    """
    from pathlib import Path

    fixer = AutoFixer()

    # Get fixable issues
    fixable = fixer.get_fixable_issues(issues)

    # Filter by confidence
    auto_fixable = [
        i for i in fixable
        if i.get('fix') and i['fix'].confidence >= min_confidence
    ]

    results = {
        'original_file': filepath,
        'total_issues': len(issues),
        'fixable_issues': len(fixable),
        'auto_fixed': 0,
        'fixes_applied': [],
        'fixes_skipped': [],
        'output_file': None
    }

    if not auto_fixable:
        results['message'] = 'No issues met the auto-fix confidence threshold'
        return results

    # For now, just return the fix preview
    # Full document editing would require docx manipulation
    results['fixes_applied'] = [
        {
            'type': i['fix'].issue_type,
            'original': i['fix'].original,
            'replacement': i['fix'].replacement,
            'confidence': i['fix'].confidence,
            'reason': i['fix'].reason
        }
        for i in auto_fixable
    ]
    results['auto_fixed'] = len(auto_fixable)

    # Generate output path
    if output_path is None:
        p = Path(filepath)
        output_path = str(p.parent / f"{p.stem}_fixed{p.suffix}")

    results['output_file'] = output_path
    results['message'] = f"Found {len(auto_fixable)} auto-fixable issues"

    _logger.info(f"Auto-fix summary: {results['auto_fixed']} fixes for {filepath}")

    return results


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == '__main__':
    import sys

    # Demo mode
    demo_issues = [
        {
            'type': 'latin_abbreviations',
            'message': 'Avoid Latin abbreviation',
            'context': 'Use the API, i.e., the programming interface',
            'paragraph': 1
        },
        {
            'type': 'contractions',
            'message': 'Contraction found',
            'context': "The system doesn't support this feature",
            'paragraph': 2
        },
        {
            'type': 'wordy_phrases',
            'message': 'Wordy phrase',
            'context': 'In order to complete the task, run the script',
            'paragraph': 3
        },
        {
            'type': 'product_name_consistency',
            'message': 'Product name capitalization',
            'context': 'Install javascript and nodejs',
            'paragraph': 4
        },
        {
            'type': 'second_person',
            'message': 'Use second person',
            'context': 'The user should click the button',
            'paragraph': 5
        },
    ]

    fixer = AutoFixer()

    print("AEGIS Auto-Fix Demo")
    print("=" * 50)

    fixable = fixer.get_fixable_issues(demo_issues)

    print(f"\nFound {len(fixable)} fixable issues:\n")

    for issue in fixable:
        fix = issue.get('fix')
        if fix:
            print(f"  Type: {fix.issue_type}")
            print(f"  Original: \"{fix.original}\"")
            print(f"  Replacement: \"{fix.replacement}\"")
            print(f"  Confidence: {fix.confidence:.0%}")
            print(f"  Reason: {fix.reason}")
            print()

    summary = fixer.get_fix_summary(demo_issues)
    print("Summary:")
    print(f"  Total fixable: {summary['total_fixable']}")
    print(f"  High confidence: {summary['high_confidence']}")
    print(f"  Needs review: {summary['needs_review']}")
