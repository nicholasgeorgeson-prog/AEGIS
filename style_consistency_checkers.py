"""
AEGIS - Style Consistency Checkers Module
Version: 3.4.0
Created: February 3, 2026

Provides style consistency validation for technical documentation.
All checkers are 100% offline-capable with no external API dependencies.

Checkers included:
1. HeadingCaseConsistencyChecker - Validates consistent heading capitalization
2. ContractionConsistencyChecker - Detects mixed contraction usage
3. OxfordCommaConsistencyChecker - Validates serial comma consistency
4. ARIProminenceChecker - Automated Readability Index assessment
5. SpacheReadabilityChecker - Spache formula for basic audiences
6. DaleChallEnhancedChecker - Enhanced Dale-Chall with full word list

Usage:
    from style_consistency_checkers import get_style_consistency_checkers
    checkers = get_style_consistency_checkers()
"""

import re
import json
import os
from typing import Dict, List, Any, Tuple, Optional, Set
from collections import Counter, defaultdict
from pathlib import Path

# Import base checker
try:
    from base_checker import BaseChecker
except ImportError:
    # Fallback for standalone testing
    class BaseChecker:
        CHECKER_NAME = "Base"
        CHECKER_VERSION = "1.0.0"
        def __init__(self, enabled=True):
            self.enabled = enabled
        def create_issue(self, **kwargs):
            return {'category': self.CHECKER_NAME, **kwargs}


# =============================================================================
# CHECKER 1: Heading Case Consistency
# =============================================================================

class HeadingCaseConsistencyChecker(BaseChecker):
    """
    Validates that heading capitalization is consistent within each heading level.

    Detects: Title Case, Sentence case, ALL CAPS, lowercase, Mixed
    Flags inconsistencies within H1, H2, H3, etc.
    """

    CHECKER_NAME = "Heading Case Consistency"
    CHECKER_VERSION = "3.4.0"

    # Minor words that are typically lowercase in Title Case
    TITLE_CASE_MINOR = {
        'a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'yet', 'so',
        'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'if', 'per', 'via'
    }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        headings = kwargs.get('headings', [])
        if not headings or len(headings) < 2:
            return []

        issues = []

        # Group headings by level
        by_level = defaultdict(list)
        for h in headings:
            level = h.get('level', h.get('style', '').count('Heading') or 1)
            if isinstance(level, str):
                # Extract number from style name like "Heading 2"
                match = re.search(r'\d+', str(level))
                level = int(match.group()) if match else 1

            case_style = self._detect_case(h.get('text', ''))
            by_level[level].append({
                'text': h.get('text', ''),
                'index': h.get('index', 0),
                'case': case_style
            })

        # Check consistency within each level
        for level, items in by_level.items():
            if len(items) < 2:
                continue

            case_counts = Counter(h['case'] for h in items)

            # Skip if all same or if most are 'Mixed' (hard to standardize)
            if len(case_counts) <= 1:
                continue

            # Find dominant style (excluding 'Mixed')
            dominant_counts = {k: v for k, v in case_counts.items() if k != 'Mixed'}
            if not dominant_counts:
                continue

            dominant = max(dominant_counts, key=dominant_counts.get)

            # Flag non-dominant headings
            for h in items:
                if h['case'] != dominant and h['case'] != 'Mixed':
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Heading case inconsistent: '{h['case']}' (other H{level}s use '{dominant}')",
                        context=h['text'][:80],
                        paragraph_index=h['index'],
                        suggestion=f"Change to {dominant} to match other level-{level} headings",
                        rule_id='HDCASE001',
                        flagged_text=h['text']
                    ))

        return issues

    def _detect_case(self, text: str) -> str:
        """Detect the capitalization style of a heading."""
        text = text.strip()
        if not text:
            return 'Empty'

        words = text.split()
        if not words:
            return 'Empty'

        # Check for ALL CAPS
        alpha_chars = [c for c in text if c.isalpha()]
        if alpha_chars and all(c.isupper() for c in alpha_chars):
            return 'ALL CAPS'

        # Check for all lowercase
        if alpha_chars and all(c.islower() for c in alpha_chars):
            return 'lowercase'

        # Check for Sentence case (first word capitalized, rest lowercase except proper nouns)
        first_word = words[0]
        if len(words) == 1:
            if first_word[0].isupper() and (len(first_word) == 1 or first_word[1:].islower()):
                return 'Sentence case'
            return 'Mixed'

        # Check subsequent words
        lower_count = 0
        upper_count = 0
        for word in words[1:]:
            if not word or not word[0].isalpha():
                continue
            if word[0].isupper():
                upper_count += 1
            else:
                lower_count += 1

        # Title Case: most non-minor words are capitalized
        if upper_count > lower_count:
            return 'Title Case'

        # Sentence case: first word cap, rest lowercase (mostly)
        if first_word[0].isupper() and lower_count >= upper_count:
            return 'Sentence case'

        return 'Mixed'


# =============================================================================
# CHECKER 2: Contraction Consistency
# =============================================================================

class ContractionConsistencyChecker(BaseChecker):
    """
    Detects inconsistent contraction usage (e.g., using both "don't" and "do not").

    Flags documents that mix contracted and expanded forms for the same phrase.
    """

    CHECKER_NAME = "Contraction Consistency"
    CHECKER_VERSION = "3.4.0"

    # Map contractions to their expanded forms
    CONTRACTION_MAP = {
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
        "i'm": "i am",
        "you're": "you are",
        "we're": "we are",
        "they're": "they are",
        "i've": "i have",
        "you've": "you have",
        "we've": "we have",
        "they've": "they have",
        "i'll": "i will",
        "you'll": "you will",
        "we'll": "we will",
        "they'll": "they will",
        "i'd": "i would",
        "you'd": "you would",
        "we'd": "we would",
        "they'd": "they would",
    }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        full_text = kwargs.get('full_text', '')
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs)

        text_lower = full_text.lower()
        issues = []
        inconsistent_pairs = []

        # Check each contraction/expansion pair
        for contraction, expansion in self.CONTRACTION_MAP.items():
            has_contraction = bool(re.search(r'\b' + re.escape(contraction) + r'\b', text_lower))
            has_expansion = bool(re.search(r'\b' + re.escape(expansion) + r'\b', text_lower))

            if has_contraction and has_expansion:
                inconsistent_pairs.append((contraction, expansion))

        if not inconsistent_pairs:
            return []

        # Find occurrences and flag the minority form
        flagged_forms = set()
        for contraction, expansion in inconsistent_pairs:
            c_count = len(re.findall(r'\b' + re.escape(contraction) + r'\b', text_lower))
            e_count = len(re.findall(r'\b' + re.escape(expansion) + r'\b', text_lower))

            # Flag the less common form
            minority = contraction if c_count < e_count else expansion
            majority = expansion if c_count < e_count else contraction

            if minority in flagged_forms:
                continue
            flagged_forms.add(minority)

            # Find paragraphs with minority form
            pattern = re.compile(r'\b' + re.escape(minority) + r'\b', re.IGNORECASE)
            for idx, text in paragraphs:
                match = pattern.search(text)
                if match:
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Inconsistent: '{minority}' and '{majority}' both used",
                        context=text[max(0, match.start()-20):match.end()+40],
                        paragraph_index=idx,
                        suggestion=f"Standardize on '{majority}' for consistency",
                        rule_id='CONTR001',
                        flagged_text=match.group(),
                        replacement_text=majority
                    ))
                    break  # One issue per pair

        return issues


# =============================================================================
# CHECKER 3: Oxford Comma Consistency
# =============================================================================

class OxfordCommaConsistencyChecker(BaseChecker):
    """
    Validates consistent use of the Oxford (serial) comma throughout the document.

    Detects lists of 3+ items and flags inconsistent comma usage before "and/or".
    """

    CHECKER_NAME = "Oxford Comma Consistency"
    CHECKER_VERSION = "3.4.0"

    # Pattern for lists: "X, Y, and Z" (with Oxford) vs "X, Y and Z" (without)
    # These patterns look for the last two items in a list
    WITH_OXFORD = re.compile(
        r'\b\w+(?:\s+\w+)*,\s+\w+(?:\s+\w+)*,\s+(?:and|or)\s+\w+',
        re.IGNORECASE
    )

    WITHOUT_OXFORD = re.compile(
        r'\b\w+(?:\s+\w+)*,\s+\w+(?:\s+\w+)*\s+(?:and|or)\s+\w+(?!\s*,)',
        re.IGNORECASE
    )

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        full_text = kwargs.get('full_text', '')
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs)

        # Find all potential list constructions
        with_oxford = []
        without_oxford = []

        for match in self.WITH_OXFORD.finditer(full_text):
            text = match.group()
            # Verify it has ", and" or ", or" pattern
            if re.search(r',\s+(?:and|or)\b', text):
                with_oxford.append((match.start(), match.end(), text))

        for match in self.WITHOUT_OXFORD.finditer(full_text):
            text = match.group()
            # Exclude if it actually has Oxford comma
            if not re.search(r',\s+(?:and|or)\b', text):
                # Make sure it's a real list (has at least one comma before the and/or)
                if ',' in text.split('and')[0] if 'and' in text.lower() else text.split('or')[0]:
                    without_oxford.append((match.start(), match.end(), text))

        # If we don't have both styles, no inconsistency
        if not with_oxford or not without_oxford:
            return []

        issues = []

        # Determine which is minority
        if len(with_oxford) < len(without_oxford):
            minority_matches = with_oxford
            minority_style = "with Oxford comma"
            suggestion = "Remove comma before 'and/or' for consistency"
        else:
            minority_matches = without_oxford
            minority_style = "without Oxford comma"
            suggestion = "Add comma before 'and/or' for consistency (Oxford comma)"

        # Find paragraph indices for minority matches and flag
        for start, end, text in minority_matches[:5]:  # Limit to 5 issues
            # Find which paragraph contains this
            char_pos = 0
            for idx, para_text in paragraphs:
                if text in para_text:
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Serial comma inconsistency: this list is {minority_style}",
                        context=text[:80],
                        paragraph_index=idx,
                        suggestion=suggestion,
                        rule_id='OXFORD001',
                        flagged_text=text
                    ))
                    break

        return issues


# =============================================================================
# CHECKER 4: ARI Prominence (Automated Readability Index)
# =============================================================================

class ARIProminenceChecker(BaseChecker):
    """
    Evaluates document readability using the Automated Readability Index (ARI).

    ARI was designed for technical documents (U.S. Navy) and uses character count
    rather than syllables, making it more reliable for technical terminology.

    Formula: 4.71*(chars/words) + 0.5*(words/sentences) - 21.43
    """

    CHECKER_NAME = "ARI Readability Assessment"
    CHECKER_VERSION = "3.4.0"

    # Thresholds by target audience
    THRESHOLDS = {
        'general': 12,      # High school senior
        'technical': 14,    # College sophomore
        'expert': 16,       # College senior
        'academic': 18,     # Graduate level
    }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        full_text = kwargs.get('full_text', '')
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs)

        if len(full_text) < 100:
            return []  # Too short to analyze

        # Calculate ARI for full document
        doc_ari = self._calculate_ari(full_text)
        if doc_ari is None:
            return []

        issues = []

        # Get target audience from options or default to 'technical'
        options = kwargs.get('options', {})
        doc_type = options.get('target_audience', 'technical')
        threshold = self.THRESHOLDS.get(doc_type, 14)

        # Flag if document exceeds threshold
        if doc_ari > threshold:
            excess = doc_ari - threshold
            severity = 'High' if excess > 3 else 'Medium' if excess > 1 else 'Low'

            issues.append(self.create_issue(
                severity=severity,
                message=f"ARI grade level ({doc_ari:.1f}) exceeds {doc_type} threshold ({threshold})",
                context=f"Document requires approximately grade {int(doc_ari)} reading level",
                paragraph_index=0,
                suggestion=self._get_suggestions(doc_ari, threshold),
                rule_id='ARI001'
            ))

        # Also flag high-complexity paragraphs
        para_issues = 0
        for idx, text in paragraphs:
            words = text.split()
            if len(words) < 20:
                continue  # Skip short paragraphs

            para_ari = self._calculate_ari(text)
            if para_ari and para_ari > threshold + 4:  # 4+ grades above
                if para_issues < 5:  # Limit paragraph-level issues
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Paragraph ARI ({para_ari:.1f}) significantly exceeds threshold",
                        context=text[:100] + '...' if len(text) > 100 else text,
                        paragraph_index=idx,
                        suggestion="Simplify: use shorter words and shorter sentences",
                        rule_id='ARI002'
                    ))
                    para_issues += 1

        return issues

    def _calculate_ari(self, text: str) -> Optional[float]:
        """Calculate ARI score."""
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not words or not sentences:
            return None

        word_count = len(words)
        sentence_count = len(sentences)
        char_count = sum(len(w) for w in words)

        # ARI formula
        ari = 4.71 * (char_count / word_count) + 0.5 * (word_count / sentence_count) - 21.43
        return round(ari, 1)

    def _get_suggestions(self, current: float, target: int) -> str:
        """Generate improvement suggestions."""
        diff = current - target
        suggestions = []

        if diff > 3:
            suggestions.append("Use shorter words (target: 4-5 letters average)")
        if diff > 2:
            suggestions.append("Use shorter sentences (target: 15-20 words)")
        if diff > 1:
            suggestions.append("Break complex sentences into simpler ones")

        suggestions.append(f"Target ARI: {target} | Current: {current:.1f}")
        return "; ".join(suggestions)


# =============================================================================
# CHECKER 5: Spache Readability (Basic Audiences)
# =============================================================================

class SpacheReadabilityChecker(BaseChecker):
    """
    Evaluates readability using the Spache formula.

    Spache is designed for grades 1-4 and is more accurate than Flesch for
    documents targeting lower reading levels (training materials, entry-level docs).

    v3.5.0: Added configurable thresholds for different audience types:
    - Basic/Training: Grade 4.0 (original Spache target)
    - General Public: Grade 6.0
    - Technical/Engineering: Grade 10.0 (default for AEGIS)

    For engineering documents, a Spache grade of 8-10 is normal and acceptable.

    Formula: 0.141*(words/sentence) + 0.086*(unfamiliar_words_%) + 0.839
    """

    CHECKER_NAME = "Spache Readability"
    CHECKER_VERSION = "3.5.0"  # v3.5.0: Configurable thresholds for audience types

    # v3.5.0: Audience-specific thresholds
    AUDIENCE_THRESHOLDS = {
        'basic': 4.0,       # Training materials, entry-level
        'general': 6.0,     # General public
        'technical': 10.0,  # Engineers, technicians (default)
        'academic': 12.0,   # Academic/research documents
    }

    def __init__(self, enabled: bool = True, target_audience: str = 'technical'):
        super().__init__(enabled)
        self.easy_words = self._load_easy_words()
        self.target_audience = target_audience

    def _load_easy_words(self) -> Set[str]:
        """Load Spache easy word list."""
        # Try to load from data file
        data_path = Path(__file__).parent / 'data' / 'spache_easy_words.json'
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback: core easy words (subset)
        return {
            'a', 'about', 'after', 'again', 'all', 'always', 'am', 'an', 'and',
            'any', 'are', 'around', 'as', 'ask', 'at', 'ate', 'away', 'back',
            'bad', 'be', 'because', 'been', 'before', 'best', 'better', 'big',
            'black', 'blue', 'both', 'bring', 'brown', 'but', 'buy', 'by',
            'call', 'came', 'can', 'carry', 'clean', 'close', 'cold', 'come',
            'could', 'cut', 'day', 'did', 'do', 'does', 'done', 'down', 'draw',
            'drink', 'each', 'eat', 'eight', 'every', 'fall', 'far', 'fast',
            'father', 'find', 'first', 'five', 'fly', 'for', 'found', 'four',
            'from', 'full', 'funny', 'gave', 'get', 'give', 'go', 'goes',
            'going', 'good', 'got', 'green', 'grow', 'had', 'has', 'have',
            'he', 'help', 'her', 'here', 'him', 'his', 'hold', 'hot', 'how',
            'hurt', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'jump', 'just',
            'keep', 'kind', 'know', 'last', 'leave', 'left', 'let', 'light',
            'like', 'little', 'live', 'long', 'look', 'made', 'make', 'man',
            'many', 'may', 'me', 'more', 'most', 'mother', 'much', 'must',
            'my', 'myself', 'name', 'never', 'new', 'next', 'no', 'not', 'now',
            'of', 'off', 'old', 'on', 'once', 'one', 'only', 'open', 'or',
            'other', 'our', 'out', 'over', 'own', 'part', 'people', 'pick',
            'place', 'play', 'please', 'pull', 'put', 'ran', 'read', 'red',
            'ride', 'right', 'round', 'run', 'said', 'same', 'saw', 'say',
            'see', 'seven', 'shall', 'she', 'show', 'sing', 'sit', 'six',
            'sleep', 'small', 'so', 'some', 'soon', 'start', 'stop', 'take',
            'tell', 'ten', 'than', 'thank', 'that', 'the', 'their', 'them',
            'then', 'there', 'these', 'they', 'thing', 'think', 'this',
            'those', 'three', 'through', 'to', 'today', 'together', 'too',
            'try', 'two', 'under', 'up', 'upon', 'us', 'use', 'very', 'walk',
            'want', 'warm', 'was', 'wash', 'water', 'way', 'we', 'well',
            'went', 'were', 'what', 'when', 'where', 'which', 'while', 'white',
            'who', 'why', 'will', 'wish', 'with', 'work', 'would', 'write',
            'year', 'yes', 'yet', 'you', 'your'
        }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        # v3.5.0: Get target audience from options (default: technical for engineering docs)
        options = kwargs.get('options', {})
        target_audience = options.get('spache_target_audience',
                                       options.get('target_audience_type',
                                                    self.target_audience))

        # Get threshold for this audience type
        threshold = self.AUDIENCE_THRESHOLDS.get(target_audience,
                                                   self.AUDIENCE_THRESHOLDS['technical'])

        # Allow explicit override of threshold
        threshold = options.get('spache_threshold', threshold)

        full_text = kwargs.get('full_text', '')
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs)

        if len(full_text) < 100:
            return []

        spache_grade = self._calculate_spache(full_text)
        if spache_grade is None:
            return []

        issues = []

        # v3.5.0: Flag if exceeds audience-appropriate threshold
        if spache_grade > threshold:
            # Severity based on how much it exceeds threshold
            excess = spache_grade - threshold
            severity = 'High' if excess > 3 else 'Medium' if excess > 1.5 else 'Low'

            audience_label = target_audience.replace('_', ' ').title()
            issues.append(self.create_issue(
                severity=severity,
                message=f"Spache grade level ({spache_grade:.1f}) exceeds {audience_label} audience target ({threshold})",
                context=f"Document readability may be above target for {audience_label.lower()} readers",
                paragraph_index=0,
                suggestion="Consider simpler vocabulary or shorter sentences if targeting broader audience",
                rule_id='SPACHE001'
            ))

        return issues

    def _calculate_spache(self, text: str) -> Optional[float]:
        """Calculate Spache readability grade."""
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not words or not sentences:
            return None

        unfamiliar = [w for w in words if w not in self.easy_words]
        unfamiliar_pct = (len(unfamiliar) / len(words)) * 100
        words_per_sentence = len(words) / len(sentences)

        # Spache formula
        grade = 0.141 * words_per_sentence + 0.086 * unfamiliar_pct + 0.839
        return round(grade, 1)


# =============================================================================
# CHECKER 6: Dale-Chall Enhanced
# =============================================================================

class DaleChallEnhancedChecker(BaseChecker):
    """
    Enhanced Dale-Chall readability checker using the full 3,000-word easy word list.

    Dale-Chall is accurate because it's based on familiar words rather than
    syllable counts, which can be misleading for technical terminology.
    """

    CHECKER_NAME = "Dale-Chall Enhanced"
    CHECKER_VERSION = "3.4.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.easy_words = self._load_dale_chall()

    def _load_dale_chall(self) -> Set[str]:
        """Load full Dale-Chall 3,000-word list."""
        data_path = Path(__file__).parent / 'data' / 'dale_chall_3000.json'
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback: basic easy words
        return {
            'a', 'able', 'about', 'above', 'accept', 'across', 'act', 'add',
            'afraid', 'after', 'again', 'against', 'age', 'ago', 'agree', 'air',
            'all', 'allow', 'almost', 'alone', 'along', 'already', 'also',
            'always', 'am', 'among', 'an', 'and', 'angry', 'animal', 'another',
            'answer', 'any', 'anything', 'appear', 'apple', 'are', 'arm',
            'around', 'arrive', 'art', 'as', 'ask', 'at', 'away', 'baby',
            'back', 'bad', 'ball', 'bank', 'be', 'bear', 'beat', 'beautiful',
            'became', 'because', 'become', 'bed', 'been', 'before', 'began',
            'begin', 'behind', 'believe', 'belong', 'below', 'beside', 'best',
            'better', 'between', 'big', 'bird', 'bit', 'black', 'blood', 'blow',
            'blue', 'board', 'boat', 'body', 'book', 'born', 'both', 'bottom',
            'box', 'boy', 'bread', 'break', 'bright', 'bring', 'brother',
            'brought', 'brown', 'build', 'burn', 'business', 'busy', 'but',
            'buy', 'by', 'call', 'came', 'can', 'car', 'care', 'carefully',
            'carry', 'case', 'cat', 'catch', 'caught', 'cause', 'center',
            'certain', 'chair', 'chance', 'change', 'child', 'children', 'city',
            'class', 'clean', 'clear', 'close', 'clothes', 'cloud', 'cold',
            'color', 'come', 'common', 'company', 'compare', 'complete',
            'condition', 'consider', 'contain', 'continue', 'control', 'cook',
            'cool', 'copy', 'corner', 'cost', 'could', 'count', 'country',
            'course', 'cover', 'cow', 'cross', 'crowd', 'cry', 'cup', 'cut',
            'dance', 'danger', 'dark', 'daughter', 'day', 'dead', 'deal',
            'dear', 'death', 'decide', 'deep', 'did', 'die', 'difference',
            'different', 'difficult', 'dinner', 'direction', 'discover', 'do',
            'doctor', 'does', 'dog', 'dollar', 'done', 'door', 'double', 'doubt',
            'down', 'draw', 'dream', 'dress', 'drink', 'drive', 'drop', 'dry',
            'during', 'each', 'ear', 'early', 'earth', 'east', 'easy', 'eat',
            'edge', 'effect', 'egg', 'eight', 'either', 'else', 'end', 'enemy',
            'enjoy', 'enough', 'enter', 'equal', 'even', 'evening', 'ever',
            'every', 'everyone', 'everything', 'example', 'except', 'expect',
            'experience', 'explain', 'eye', 'face', 'fact', 'fair', 'fall',
            'family', 'famous', 'far', 'farm', 'fast', 'fat', 'father', 'favor',
            'fear', 'feel', 'feet', 'fell', 'fellow', 'felt', 'few', 'field',
            'fight', 'figure', 'fill', 'finally', 'find', 'fine', 'finger',
            'finish', 'fire', 'first', 'fish', 'fit', 'five', 'floor', 'flower',
            'fly', 'follow', 'food', 'foot', 'for', 'force', 'foreign', 'forest',
            'forget', 'form', 'forward', 'found', 'four', 'free', 'fresh',
            'friend', 'from', 'front', 'fruit', 'full', 'fun', 'game', 'garden',
            'gate', 'gave', 'general', 'gentle', 'get', 'girl', 'give', 'glad',
            'glass', 'go', 'god', 'gold', 'gone', 'good', 'got', 'government',
            'grass', 'gray', 'great', 'green', 'grew', 'ground', 'group', 'grow',
            'guess', 'gun', 'had', 'hair', 'half', 'hall', 'hand', 'hang',
            'happen', 'happy', 'hard', 'has', 'hat', 'have', 'he', 'head',
            'hear', 'heard', 'heart', 'heat', 'heavy', 'held', 'help', 'her',
            'here', 'herself', 'high', 'hill', 'him', 'himself', 'his', 'history',
            'hit', 'hold', 'hole', 'home', 'hope', 'horse', 'hot', 'hour',
            'house', 'how', 'however', 'human', 'hundred', 'hung', 'hunt',
            'hurry', 'hurt', 'husband', 'i', 'ice', 'idea', 'if', 'imagine',
            'important', 'in', 'include', 'indeed', 'inside', 'instead',
            'interest', 'into', 'iron', 'is', 'island', 'it', 'its', 'itself',
            'job', 'join', 'joy', 'judge', 'jump', 'just', 'keep', 'kept',
            'kill', 'kind', 'king', 'knew', 'know', 'knowledge', 'lady', 'laid',
            'lake', 'land', 'language', 'large', 'last', 'late', 'laugh', 'law',
            'lay', 'lead', 'learn', 'least', 'leave', 'led', 'left', 'leg',
            'less', 'let', 'letter', 'lie', 'life', 'lift', 'light', 'like',
            'line', 'lip', 'list', 'listen', 'little', 'live', 'long', 'look',
            'lose', 'loss', 'lost', 'lot', 'love', 'low', 'made', 'make', 'man',
            'many', 'map', 'mark', 'market', 'master', 'matter', 'may', 'me',
            'mean', 'measure', 'meat', 'meet', 'member', 'men', 'middle', 'might',
            'mile', 'milk', 'million', 'mind', 'minute', 'miss', 'modern',
            'moment', 'money', 'month', 'moon', 'more', 'morning', 'most',
            'mother', 'mountain', 'mouth', 'move', 'much', 'music', 'must', 'my',
            'myself', 'name', 'nation', 'natural', 'nature', 'near', 'nearly',
            'necessary', 'neck', 'need', 'neighbor', 'neither', 'never', 'new',
            'news', 'next', 'nice', 'night', 'nine', 'no', 'nobody', 'none',
            'nor', 'north', 'nose', 'not', 'note', 'nothing', 'notice', 'now',
            'number', 'object', 'observe', 'of', 'off', 'offer', 'office',
            'officer', 'often', 'oh', 'oil', 'old', 'on', 'once', 'one', 'only',
            'open', 'or', 'order', 'other', 'our', 'out', 'outside', 'over',
            'own', 'page', 'paid', 'pain', 'paint', 'pair', 'paper', 'part',
            'party', 'pass', 'past', 'pay', 'peace', 'people', 'perhaps',
            'person', 'pick', 'picture', 'piece', 'place', 'plain', 'plan',
            'plane', 'plant', 'play', 'please', 'pleasure', 'pocket', 'point',
            'police', 'poor', 'popular', 'position', 'possible', 'pound', 'power',
            'practice', 'prepare', 'present', 'president', 'press', 'pretty',
            'price', 'print', 'private', 'probably', 'problem', 'produce',
            'product', 'program', 'promise', 'proper', 'protect', 'prove',
            'provide', 'public', 'pull', 'purpose', 'push', 'put', 'question',
            'quick', 'quiet', 'quite', 'race', 'radio', 'rain', 'raise', 'ran',
            'rather', 'reach', 'read', 'ready', 'real', 'reason', 'receive',
            'record', 'red', 'remain', 'remember', 'report', 'require', 'rest',
            'result', 'return', 'rich', 'ride', 'right', 'ring', 'rise', 'river',
            'road', 'rock', 'roll', 'room', 'rose', 'round', 'rule', 'run',
            'safe', 'said', 'sail', 'sale', 'same', 'sat', 'save', 'saw', 'say',
            'school', 'science', 'sea', 'season', 'seat', 'second', 'secret',
            'see', 'seem', 'seen', 'sell', 'send', 'sense', 'sent', 'sentence',
            'separate', 'serve', 'service', 'set', 'settle', 'seven', 'several',
            'shall', 'shape', 'share', 'she', 'ship', 'shoe', 'shop', 'short',
            'shot', 'should', 'shoulder', 'shout', 'show', 'shut', 'sick', 'side',
            'sight', 'sign', 'silver', 'simple', 'since', 'sing', 'single',
            'sister', 'sit', 'situation', 'six', 'size', 'skin', 'sky', 'sleep',
            'slow', 'small', 'smile', 'smoke', 'snow', 'so', 'social', 'soft',
            'soil', 'sold', 'soldier', 'some', 'somebody', 'someone', 'something',
            'sometimes', 'son', 'song', 'soon', 'sorry', 'sort', 'sound', 'south',
            'space', 'speak', 'special', 'speed', 'spend', 'spirit', 'spot',
            'spread', 'spring', 'square', 'stage', 'stand', 'star', 'start',
            'state', 'station', 'stay', 'step', 'stick', 'still', 'stock',
            'stone', 'stood', 'stop', 'store', 'story', 'straight', 'strange',
            'stream', 'street', 'strike', 'strong', 'student', 'study', 'subject',
            'such', 'sudden', 'suffer', 'sugar', 'suggest', 'suit', 'summer',
            'sun', 'supply', 'support', 'suppose', 'sure', 'surface', 'surprise',
            'sweet', 'swim', 'system', 'table', 'take', 'talk', 'tall', 'taste',
            'teach', 'teacher', 'team', 'tear', 'tell', 'ten', 'term', 'test',
            'than', 'thank', 'that', 'the', 'their', 'them', 'themselves', 'then',
            'there', 'therefore', 'these', 'they', 'thick', 'thin', 'thing',
            'think', 'third', 'this', 'those', 'though', 'thought', 'thousand',
            'three', 'through', 'throw', 'thus', 'tie', 'till', 'time', 'tiny',
            'to', 'today', 'together', 'told', 'tomorrow', 'tone', 'too', 'took',
            'top', 'total', 'touch', 'toward', 'town', 'trade', 'train', 'travel',
            'tree', 'trial', 'trip', 'trouble', 'true', 'trust', 'truth', 'try',
            'turn', 'twelve', 'twenty', 'two', 'type', 'under', 'understand',
            'union', 'unit', 'united', 'until', 'up', 'upon', 'us', 'use',
            'usual', 'valley', 'value', 'various', 'very', 'view', 'village',
            'visit', 'voice', 'wait', 'walk', 'wall', 'want', 'war', 'warm',
            'was', 'wash', 'watch', 'water', 'wave', 'way', 'we', 'wear',
            'weather', 'week', 'weight', 'welcome', 'well', 'went', 'were',
            'west', 'western', 'what', 'whatever', 'wheel', 'when', 'where',
            'whether', 'which', 'while', 'white', 'who', 'whole', 'whom', 'whose',
            'why', 'wide', 'wife', 'wild', 'will', 'win', 'wind', 'window',
            'winter', 'wish', 'with', 'within', 'without', 'woman', 'women',
            'wonder', 'wood', 'word', 'work', 'worker', 'world', 'worry', 'worth',
            'would', 'write', 'wrong', 'yard', 'year', 'yellow', 'yes', 'yesterday',
            'yet', 'you', 'young', 'your', 'yourself', 'youth'
        }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        if not self.easy_words:
            return []  # Data not available

        full_text = kwargs.get('full_text', '')
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs)

        words = re.findall(r'\b[a-zA-Z]+\b', full_text.lower())
        if len(words) < 100:
            return []

        # Find difficult words (not in easy list)
        difficult_words = [w for w in words if w not in self.easy_words and len(w) > 2]
        difficult_pct = (len(difficult_words) / len(words)) * 100

        issues = []

        # Flag high percentage of difficult words
        if difficult_pct > 10:
            # Get most frequent difficult words
            difficult_counts = Counter(difficult_words)
            frequent = difficult_counts.most_common(10)

            issues.append(self.create_issue(
                severity='Medium' if difficult_pct < 15 else 'High',
                message=f"High percentage of difficult words: {difficult_pct:.1f}%",
                context=f"Frequent difficult words: {', '.join(w for w, c in frequent[:5])}",
                paragraph_index=0,
                suggestion="Consider simpler alternatives for frequently used difficult words",
                rule_id='DALE001'
            ))

        return issues


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_style_consistency_checkers() -> Dict[str, BaseChecker]:
    """
    Returns a dictionary of all style consistency checker instances.

    Used by core.py to register checkers in bulk.
    """
    return {
        'heading_case_consistency': HeadingCaseConsistencyChecker(),
        'contraction_consistency': ContractionConsistencyChecker(),
        'oxford_comma_consistency': OxfordCommaConsistencyChecker(),
        'ari_prominence': ARIProminenceChecker(),
        'spache_readability': SpacheReadabilityChecker(target_audience='technical'),  # v3.5.0: Technical default
        'dale_chall_enhanced': DaleChallEnhancedChecker(),
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    import sys

    # Demo text with intentional issues
    demo_text = """
    # Introduction to the System

    This document describes the system requirements. The user should read this carefully.
    Don't forget to check the appendix. The system does not support legacy formats.

    ## System Requirements

    The system requires Python, Node.js, and Java. You will need a computer, monitor
    and keyboard to operate the system.

    ## INSTALLATION STEPS

    1. Download the software
    2. Run the installer
    3. Configure the settings

    The installation won't take long. It will not require administrator access.
    """

    demo_headings = [
        {'text': 'Introduction to the System', 'index': 0, 'level': 1},
        {'text': 'System Requirements', 'index': 2, 'level': 2},
        {'text': 'INSTALLATION STEPS', 'index': 4, 'level': 2},
    ]

    paragraphs = [(i, p.strip()) for i, p in enumerate(demo_text.split('\n\n')) if p.strip()]

    print("=== Style Consistency Checkers Demo ===\n")

    checkers = get_style_consistency_checkers()

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(
            paragraphs,
            full_text=demo_text,
            headings=demo_headings
        )

        if issues:
            for issue in issues[:3]:
                print(f"  [{issue.get('severity', 'Info')}] {issue.get('message', '')}")
                if issue.get('suggestion'):
                    print(f"    Suggestion: {issue.get('suggestion', '')}")
        else:
            print("  No issues found")

    print(f"\n\nTotal checkers: {len(checkers)}")
