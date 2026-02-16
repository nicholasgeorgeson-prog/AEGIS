# AEGIS v3.4.0 Implementation Plan
## 23 Offline-Capable Enhancement Checkers

**Version:** 3.4.0
**Codename:** Maximum Coverage Suite
**Created:** 2026-02-03
**Target:** 100% Offline Operation (No LLM/API Dependencies)

---

## Executive Summary

This plan details the implementation of 23 new offline-capable checkers to address gaps identified against industry tools (Vale, LanguageTool, Acrolinx, Microsoft/Google style guides). All enhancements use rule-based approaches with pre-packaged data files—no LLMs or external APIs required.

**Architecture Strategy:**
- Group related checkers into 5 new module files
- Use factory functions for bulk registration
- Store large pattern sets in `data/` as JSON/SQLite
- Leverage existing spaCy infrastructure (already offline-capable)
- Provide graceful degradation when optional dependencies unavailable

---

## Module Organization

| Module File | Checkers | Focus Area |
|-------------|----------|------------|
| `style_consistency_checkers.py` | 6 | Heading case, contractions, Oxford comma, formatting |
| `clarity_checkers.py` | 5 | Future tense, Latin abbrev, conjunctions, directional, time-sensitive |
| `acronym_enhanced_checkers.py` | 2 | First-use enforcement, unused definitions |
| `procedural_writing_checkers.py` | 3 | Imperative mood, second person, link text |
| `document_quality_checkers.py` | 4 | List sequences, product names, cross-ref targets, code formatting |
| `compliance_checkers.py` | 3 | MIL-STD-40051, S1000D basics, AS9100 documentation |

**Data Files (New):**
```
data/
├── dale_chall_3000.json          # Full 3,000-word easy word list
├── product_names.json            # Common product name capitalizations
├── latin_abbreviations.json      # i.e., e.g., etc. patterns + contexts
├── mil_std_40051_patterns.json   # MIL-STD-40051 documentation rules
├── s1000d_basic_rules.json       # S1000D tag validation rules
├── as9100_doc_requirements.json  # AS9100 documentation checklist
└── spache_easy_words.json        # Spache formula word list
```

---

## Detailed Implementation Plan

---

### MODULE 1: style_consistency_checkers.py

**Purpose:** Ensure consistent styling throughout documents

---

#### Checker 1: HeadingCaseConsistencyChecker

**Gap Addressed:** #2 - Missing heading case consistency validation

**Rule Logic:**
1. Extract all headings from `kwargs['headings']`
2. Classify each heading's case style:
   - Title Case: "The Quick Brown Fox"
   - Sentence case: "The quick brown fox"
   - ALL CAPS: "THE QUICK BROWN FOX"
   - lowercase: "the quick brown fox"
3. Group headings by level (H1, H2, H3, etc.)
4. Flag inconsistencies within same heading level

**Implementation:**
```python
class HeadingCaseConsistencyChecker(BaseChecker):
    CHECKER_NAME = "Heading Case Consistency"
    CHECKER_VERSION = "3.4.0"

    def check(self, paragraphs, **kwargs):
        headings = kwargs.get('headings', [])
        if not headings:
            return []

        # Group by level
        by_level = defaultdict(list)
        for h in headings:
            level = h.get('level', 1)
            case_style = self._detect_case(h['text'])
            by_level[level].append({
                'text': h['text'],
                'index': h['index'],
                'case': case_style
            })

        issues = []
        for level, items in by_level.items():
            case_counts = Counter(h['case'] for h in items)
            if len(case_counts) > 1:
                # Inconsistency detected
                dominant = case_counts.most_common(1)[0][0]
                for h in items:
                    if h['case'] != dominant:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f"Heading case inconsistent with other H{level} headings",
                            context=h['text'],
                            paragraph_index=h['index'],
                            suggestion=f"Use {dominant} to match other H{level} headings",
                            rule_id='HDCASE001'
                        ))
        return issues

    def _detect_case(self, text):
        words = text.split()
        if not words:
            return 'unknown'

        if text.isupper():
            return 'ALL CAPS'
        if text.islower():
            return 'lowercase'

        # Check title case (major words capitalized)
        title_words = [w for w in words if len(w) > 3 or words.index(w) == 0]
        if all(w[0].isupper() for w in title_words if w[0].isalpha()):
            return 'Title Case'

        # Sentence case (first word capitalized)
        if words[0][0].isupper() and all(w[0].islower() for w in words[1:] if w[0].isalpha() and w.lower() not in ['i']):
            return 'Sentence case'

        return 'Mixed'
```

**Dependencies:** None (uses existing heading extraction)
**Data Files:** None
**Effort:** Low (2-3 hours)

---

#### Checker 2: ContractionConsistencyChecker

**Gap Addressed:** #10 - Inconsistent contraction usage

**Rule Logic:**
1. Build contraction map: `{"don't": "do not", "isn't": "is not", ...}`
2. Scan document for both forms of each pair
3. Flag if both forms appear (e.g., "don't" AND "do not")
4. Suggest standardizing on one form

**Implementation:**
```python
class ContractionConsistencyChecker(BaseChecker):
    CHECKER_NAME = "Contraction Consistency"
    CHECKER_VERSION = "3.4.0"

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
        "it's": "it is",  # Context-sensitive: "it is" vs "it has"
        "that's": "that is",
        "there's": "there is",
        "here's": "here is",
        "what's": "what is",
        "who's": "who is",
        "let's": "let us",
        "I'm": "I am",
        "you're": "you are",
        "we're": "we are",
        "they're": "they are",
        "I've": "I have",
        "you've": "you have",
        "we've": "we have",
        "they've": "they have",
        "I'll": "I will",
        "you'll": "you will",
        "we'll": "we will",
        "they'll": "they will",
        "I'd": "I would",
        "you'd": "you would",
        "we'd": "we would",
        "they'd": "they would",
    }

    def check(self, paragraphs, **kwargs):
        full_text = kwargs.get('full_text', '')
        text_lower = full_text.lower()

        issues = []
        found_pairs = []

        for contraction, expansion in self.CONTRACTION_MAP.items():
            has_contraction = re.search(r'\b' + re.escape(contraction) + r'\b', text_lower)
            has_expansion = re.search(r'\b' + re.escape(expansion) + r'\b', text_lower)

            if has_contraction and has_expansion:
                found_pairs.append((contraction, expansion))

        if found_pairs:
            # Find all occurrences and flag the minority form
            for contraction, expansion in found_pairs:
                c_count = len(re.findall(r'\b' + re.escape(contraction) + r'\b', text_lower))
                e_count = len(re.findall(r'\b' + re.escape(expansion) + r'\b', text_lower))

                # Flag the less common form
                minority = contraction if c_count < e_count else expansion
                majority = expansion if c_count < e_count else contraction

                # Find paragraphs with minority form
                for idx, text in paragraphs:
                    if re.search(r'\b' + re.escape(minority) + r'\b', text, re.IGNORECASE):
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f"Inconsistent contraction usage: '{minority}' vs '{majority}'",
                            context=text[:100],
                            paragraph_index=idx,
                            suggestion=f"Standardize on '{majority}' for consistency",
                            rule_id='CONTR001',
                            flagged_text=minority
                        ))

        return issues
```

**Dependencies:** None
**Data Files:** None (embedded in class)
**Effort:** Low (2-3 hours)

---

#### Checker 3: OxfordCommaConsistencyChecker

**Gap Addressed:** #9 - Verify Oxford comma consistency across document

**Rule Logic:**
1. Find all lists of 3+ items: "A, B, and C" or "A, B and C"
2. Classify each as "with Oxford comma" or "without"
3. Flag inconsistency if both styles present
4. Recommend dominant style

**Implementation:**
```python
class OxfordCommaConsistencyChecker(BaseChecker):
    CHECKER_NAME = "Oxford Comma Consistency"
    CHECKER_VERSION = "3.4.0"

    # Pattern for 3+ item lists ending with "and" or "or"
    WITH_OXFORD = re.compile(
        r'\b\w+(?:\s+\w+)*,\s+\w+(?:\s+\w+)*,\s+(?:and|or)\s+\w+',
        re.IGNORECASE
    )
    WITHOUT_OXFORD = re.compile(
        r'\b\w+(?:\s+\w+)*,\s+\w+(?:\s+\w+)*\s+(?:and|or)\s+\w+',
        re.IGNORECASE
    )

    def check(self, paragraphs, **kwargs):
        full_text = kwargs.get('full_text', '')

        with_matches = list(self.WITH_OXFORD.finditer(full_text))
        without_matches = list(self.WITHOUT_OXFORD.finditer(full_text))

        # Filter false positives from without_matches (some may actually have Oxford)
        true_without = []
        for m in without_matches:
            text = m.group()
            # If it has ", and" or ", or" it's actually WITH Oxford
            if not re.search(r',\s+(?:and|or)\b', text):
                true_without.append(m)

        if with_matches and true_without:
            issues = []
            # Determine minority
            if len(with_matches) < len(true_without):
                minority_matches = with_matches
                style = "with Oxford comma"
                suggestion = "Remove comma before 'and/or' for consistency"
            else:
                minority_matches = true_without
                style = "without Oxford comma"
                suggestion = "Add comma before 'and/or' for consistency"

            # Find paragraph indices for minority matches
            for match in minority_matches[:5]:  # Limit to 5 issues
                # Find which paragraph contains this match
                for idx, text in paragraphs:
                    if match.group() in text:
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f"Inconsistent serial comma: this list is {style}",
                            context=match.group(),
                            paragraph_index=idx,
                            suggestion=suggestion,
                            rule_id='OXFORD001',
                            flagged_text=match.group()
                        ))
                        break

            return issues

        return []
```

**Dependencies:** None
**Data Files:** None
**Effort:** Medium (3-4 hours)

---

#### Checker 4: ARIProminenceChecker

**Gap Addressed:** #1 - ARI readability not prominently surfaced

**Rule Logic:**
1. Calculate ARI for document
2. Compare against target audience thresholds:
   - General audience: Grade 12 (ARI ≤ 12)
   - Technical audience: Grade 16 (ARI ≤ 16)
   - Expert audience: No limit
3. Flag if ARI exceeds threshold with specific recommendations

**Implementation:**
```python
class ARIProminenceChecker(BaseChecker):
    CHECKER_NAME = "ARI Readability Assessment"
    CHECKER_VERSION = "3.4.0"

    # Thresholds by document type
    THRESHOLDS = {
        'general': 12,      # High school senior
        'technical': 14,    # College sophomore
        'expert': 16,       # College senior
        'academic': 18,     # Graduate level
    }

    def check(self, paragraphs, **kwargs):
        full_text = kwargs.get('full_text', '')
        if not full_text or len(full_text) < 100:
            return []

        # Calculate ARI: 4.71*(characters/words) + 0.5*(words/sentences) - 21.43
        words = re.findall(r'\b[a-zA-Z]+\b', full_text)
        sentences = re.split(r'[.!?]+', full_text)
        sentences = [s for s in sentences if s.strip()]

        if not words or not sentences:
            return []

        word_count = len(words)
        sentence_count = len(sentences)
        char_count = sum(len(w) for w in words)

        ari = 4.71 * (char_count / word_count) + 0.5 * (word_count / sentence_count) - 21.43
        ari = round(ari, 1)

        issues = []

        # Determine document type from options or default to 'technical'
        doc_type = kwargs.get('options', {}).get('target_audience', 'technical')
        threshold = self.THRESHOLDS.get(doc_type, 14)

        if ari > threshold:
            excess = ari - threshold
            issues.append(self.create_issue(
                severity='Medium' if excess < 2 else 'High',
                message=f"ARI grade level ({ari}) exceeds {doc_type} audience threshold ({threshold})",
                context=f"Document requires approximately grade {int(ari)} reading level",
                paragraph_index=0,
                suggestion=self._get_ari_suggestions(ari, threshold),
                rule_id='ARI001'
            ))

        # Also flag extremely high complexity sections
        for idx, text in paragraphs:
            if len(text.split()) >= 20:  # Only check substantial paragraphs
                para_ari = self._calculate_ari(text)
                if para_ari and para_ari > threshold + 4:  # 4 grades above threshold
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Paragraph ARI ({para_ari:.1f}) significantly exceeds document threshold",
                        context=text[:100] + '...',
                        paragraph_index=idx,
                        suggestion="Simplify this paragraph: shorter words, shorter sentences",
                        rule_id='ARI002'
                    ))

        return issues[:10]  # Limit to 10 issues

    def _calculate_ari(self, text):
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]

        if not words or not sentences:
            return None

        char_count = sum(len(w) for w in words)
        return 4.71 * (char_count / len(words)) + 0.5 * (len(words) / len(sentences)) - 21.43

    def _get_ari_suggestions(self, current, target):
        diff = current - target
        suggestions = []
        if diff > 3:
            suggestions.append("Use shorter words (target: 4-5 letters average)")
        if diff > 2:
            suggestions.append("Use shorter sentences (target: 15-20 words)")
        if diff > 1:
            suggestions.append("Break complex sentences into simpler ones")
        suggestions.append(f"Target ARI: {target} (current: {current:.1f})")
        return "; ".join(suggestions)
```

**Dependencies:** None
**Data Files:** None
**Effort:** Medium (3-4 hours)

---

#### Checker 5: SpacheReadabilityChecker

**Gap Addressed:** #22 - Missing Spache formula for lower reading levels

**Rule Logic:**
1. Calculate Spache readability (for grades 1-4)
2. Use Spache word list (1,000 easy words)
3. Flag documents targeting training/basic audiences that exceed Spache thresholds

**Implementation:**
```python
class SpacheReadabilityChecker(BaseChecker):
    CHECKER_NAME = "Spache Readability (Basic Audiences)"
    CHECKER_VERSION = "3.4.0"

    # Spache formula: 0.141 * (words/sentence) + 0.086 * (unfamiliar words %) + 0.839

    def __init__(self):
        super().__init__()
        self.easy_words = self._load_easy_words()

    def _load_easy_words(self):
        """Load Spache easy word list (1,000+ words)."""
        try:
            import json
            with open('data/spache_easy_words.json', 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            # Fallback: basic word set
            return {
                'a', 'about', 'after', 'all', 'am', 'an', 'and', 'are', 'as', 'at',
                'be', 'been', 'before', 'big', 'but', 'by', 'call', 'came', 'can',
                'come', 'could', 'day', 'did', 'do', 'down', 'each', 'find', 'first',
                'for', 'from', 'get', 'go', 'good', 'had', 'has', 'have', 'he', 'her',
                'him', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'just',
                'know', 'like', 'little', 'long', 'look', 'made', 'make', 'man', 'many',
                'may', 'me', 'more', 'my', 'new', 'no', 'not', 'now', 'of', 'old',
                'on', 'one', 'only', 'or', 'other', 'our', 'out', 'over', 'people',
                'said', 'see', 'she', 'so', 'some', 'take', 'than', 'that', 'the',
                'their', 'them', 'then', 'there', 'these', 'they', 'this', 'time',
                'to', 'two', 'up', 'us', 'use', 'very', 'was', 'way', 'we', 'well',
                'went', 'were', 'what', 'when', 'where', 'which', 'who', 'will',
                'with', 'would', 'year', 'you', 'your'
            }

    def check(self, paragraphs, **kwargs):
        # Only run if document is tagged for basic audiences
        options = kwargs.get('options', {})
        if not options.get('target_basic_audience', False):
            return []

        full_text = kwargs.get('full_text', '')
        if not full_text:
            return []

        spache_grade = self._calculate_spache(full_text)

        issues = []
        if spache_grade and spache_grade > 4:
            issues.append(self.create_issue(
                severity='High' if spache_grade > 6 else 'Medium',
                message=f"Spache grade level ({spache_grade:.1f}) too high for basic audience (target: 4)",
                context="Document may be too complex for training or entry-level materials",
                paragraph_index=0,
                suggestion="Use simpler words from basic vocabulary; shorter sentences",
                rule_id='SPACHE001'
            ))

        return issues

    def _calculate_spache(self, text):
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        sentences = re.split(r'[.!?]+', text)
        sentences = [s for s in sentences if s.strip()]

        if not words or not sentences:
            return None

        unfamiliar = [w for w in words if w not in self.easy_words]
        unfamiliar_pct = (len(unfamiliar) / len(words)) * 100
        words_per_sentence = len(words) / len(sentences)

        # Spache formula
        grade = 0.141 * words_per_sentence + 0.086 * unfamiliar_pct + 0.839
        return round(grade, 1)
```

**Dependencies:** None
**Data Files:** `data/spache_easy_words.json` (will create with 1,000+ words)
**Effort:** Medium (3-4 hours including data file)

---

#### Checker 6: DaleChallEnhancedChecker

**Gap Addressed:** #21 - Expand Dale-Chall easy word list to full 3,000 words

**Rule Logic:**
1. Use complete Dale-Chall 3,000-word list
2. Provide more accurate Dale-Chall scores
3. Flag difficult words with suggestions

**Implementation:**
```python
class DaleChallEnhancedChecker(BaseChecker):
    CHECKER_NAME = "Dale-Chall Enhanced"
    CHECKER_VERSION = "3.4.0"

    def __init__(self):
        super().__init__()
        self.easy_words = self._load_dale_chall()

    def _load_dale_chall(self):
        """Load full Dale-Chall 3,000-word list."""
        try:
            import json
            with open('data/dale_chall_3000.json', 'r') as f:
                return set(json.load(f))
        except FileNotFoundError:
            return set()  # Will use textstat fallback

    def check(self, paragraphs, **kwargs):
        if not self.easy_words:
            return []  # Data file not available

        full_text = kwargs.get('full_text', '')
        words = re.findall(r'\b[a-zA-Z]+\b', full_text.lower())

        if len(words) < 100:
            return []

        difficult_words = [w for w in words if w not in self.easy_words and len(w) > 2]
        difficult_pct = (len(difficult_words) / len(words)) * 100

        issues = []

        # Flag frequently used difficult words
        difficult_counts = Counter(difficult_words)
        frequent_difficult = difficult_counts.most_common(10)

        if difficult_pct > 10:  # More than 10% difficult words
            issues.append(self.create_issue(
                severity='Medium',
                message=f"High percentage of difficult words: {difficult_pct:.1f}%",
                context=f"Top difficult words: {', '.join(w for w, c in frequent_difficult[:5])}",
                paragraph_index=0,
                suggestion="Consider simpler alternatives for frequently used difficult words",
                rule_id='DALE001'
            ))

        return issues
```

**Dependencies:** None
**Data Files:** `data/dale_chall_3000.json` (will create)
**Effort:** Medium (4-5 hours including sourcing word list)

---

### MODULE 2: clarity_checkers.py

**Purpose:** Improve writing clarity and readability

---

#### Checker 7: FutureTenseChecker

**Gap Addressed:** #6 - Technical docs should use present tense

**Rule Logic:**
1. Detect future tense patterns:
   - "will + verb"
   - "shall + verb" (when not requirement language)
   - "going to + verb"
   - "is going to"
2. Exclude requirement contexts (SHALL for obligations)
3. Suggest present tense alternatives

**Implementation:**
```python
class FutureTenseChecker(BaseChecker):
    CHECKER_NAME = "Future Tense Detector"
    CHECKER_VERSION = "3.4.0"

    FUTURE_PATTERNS = [
        (r'\bwill\s+(be\s+)?\w+(?:ing|ed)\b', 'will'),
        (r'\bwill\s+\w+\b', 'will'),
        (r'\bis\s+going\s+to\s+\w+\b', 'is going to'),
        (r'\bare\s+going\s+to\s+\w+\b', 'are going to'),
        (r'\bgoing\s+to\s+be\s+\w+\b', 'going to be'),
    ]

    # Skip in requirement contexts
    REQUIREMENT_CONTEXT = re.compile(
        r'\b(shall|must|required|mandatory|contractor|government)\b',
        re.IGNORECASE
    )

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            # Skip if paragraph contains requirement language
            if self.REQUIREMENT_CONTEXT.search(text):
                continue

            for pattern, future_word in self.FUTURE_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    # Get context
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    context = text[start:end]

                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Future tense detected: '{match.group()}'",
                        context=f"...{context}...",
                        paragraph_index=idx,
                        suggestion="Consider present tense for documentation (describes current behavior)",
                        rule_id='FUTURE001',
                        flagged_text=match.group()
                    ))

        return issues[:20]  # Limit issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (2-3 hours)

---

#### Checker 8: LatinAbbreviationChecker

**Gap Addressed:** #7 - Warn about i.e., e.g., etc. for global audiences

**Rule Logic:**
1. Detect Latin abbreviations: i.e., e.g., etc., et al., viz., cf., ibid., op. cit.
2. Provide plain English alternatives
3. Consider context (some usages are acceptable in academic/legal)

**Implementation:**
```python
class LatinAbbreviationChecker(BaseChecker):
    CHECKER_NAME = "Latin Abbreviation Warnings"
    CHECKER_VERSION = "3.4.0"

    LATIN_ABBREVIATIONS = {
        'i.e.': ('that is', 'Medium'),
        'e.g.': ('for example', 'Medium'),
        'etc.': ('and so on', 'Low'),  # Common, lower severity
        'et al.': ('and others', 'Low'),
        'viz.': ('namely', 'Medium'),
        'cf.': ('compare', 'Medium'),
        'ibid.': ('in the same source', 'Low'),
        'op. cit.': ('in the work cited', 'Low'),
        'vs.': ('versus', 'Low'),
        'ca.': ('approximately', 'Medium'),
        'N.B.': ('note well', 'Medium'),
        'P.S.': ('postscript', 'Low'),
        'per se': ('by itself', 'Medium'),
        'vice versa': ('the other way around', 'Low'),
        'et cetera': ('and so on', 'Low'),
    }

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            text_check = text  # Preserve case for matching

            for abbrev, (replacement, severity) in self.LATIN_ABBREVIATIONS.items():
                pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b', re.IGNORECASE)
                for match in pattern.finditer(text_check):
                    issues.append(self.create_issue(
                        severity=severity,
                        message=f"Latin abbreviation '{match.group()}' may confuse global audiences",
                        context=text[max(0, match.start()-30):match.end()+30],
                        paragraph_index=idx,
                        suggestion=f"Consider: '{replacement}'",
                        rule_id='LATIN001',
                        flagged_text=match.group(),
                        replacement_text=replacement
                    ))

        return issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (2 hours)

---

#### Checker 9: SentenceInitialConjunctionChecker

**Gap Addressed:** #8 - Flag sentences starting with And, But, So

**Rule Logic:**
1. Detect sentence-initial conjunctions
2. Flag as informal for technical writing
3. Suggest alternatives or restructuring

**Implementation:**
```python
class SentenceInitialConjunctionChecker(BaseChecker):
    CHECKER_NAME = "Sentence-Initial Conjunction"
    CHECKER_VERSION = "3.4.0"

    CONJUNCTIONS = {
        'And': 'Additionally, Furthermore, Moreover',
        'But': 'However, Nevertheless, Yet',
        'So': 'Therefore, Consequently, As a result',
        'Or': 'Alternatively',
        'Yet': 'However, Nevertheless',
        'For': 'Because, Since',
        'Nor': 'Neither... nor (restructure)',
    }

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', text)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Check first word
                first_word = sentence.split()[0] if sentence.split() else ''
                first_word_clean = re.sub(r'[^\w]', '', first_word)

                if first_word_clean in self.CONJUNCTIONS:
                    alternatives = self.CONJUNCTIONS[first_word_clean]
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Sentence begins with conjunction '{first_word_clean}'",
                        context=sentence[:80],
                        paragraph_index=idx,
                        suggestion=f"Consider: {alternatives}, or combine with previous sentence",
                        rule_id='CONJ001',
                        flagged_text=first_word_clean
                    ))

        return issues[:15]  # Limit
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (2 hours)

---

#### Checker 10: DirectionalLanguageChecker

**Gap Addressed:** #12 - "Above", "below", "left", "right" break in responsive content

**Rule Logic:**
1. Detect directional references
2. Flag as problematic for responsive/reflowable content
3. Suggest explicit references (Figure X, Section Y)

**Implementation:**
```python
class DirectionalLanguageChecker(BaseChecker):
    CHECKER_NAME = "Directional Language"
    CHECKER_VERSION = "3.4.0"

    DIRECTIONAL_PATTERNS = [
        (r'\b(see|shown|displayed|illustrated)\s+(above|below)\b', 'vertical reference'),
        (r'\bthe\s+(above|below)\s+(figure|table|diagram|image|section|paragraph)\b', 'vertical reference'),
        (r'\b(above|below)\s+(figure|table|diagram|image)\b', 'vertical reference'),
        (r'\b(to the\s+)?(left|right)\s+(of|side)\b', 'horizontal reference'),
        (r'\bon the\s+(left|right)\b', 'horizontal reference'),
        (r'\b(previous|next|following)\s+page\b', 'page reference'),
        (r'\boverleaf\b', 'page reference'),
    ]

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            for pattern, ref_type in self.DIRECTIONAL_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Directional language ({ref_type}) may not work in all formats",
                        context=text[max(0, match.start()-20):match.end()+20],
                        paragraph_index=idx,
                        suggestion="Use explicit references: 'Figure 3', 'Section 2.1', 'Table 5'",
                        rule_id='DIRECT001',
                        flagged_text=match.group()
                    ))

        return issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (2 hours)

---

#### Checker 11: TimeSensitiveLanguageChecker

**Gap Addressed:** #13 - "Currently", "now", "recently", "soon" make docs stale

**Rule Logic:**
1. Detect time-sensitive words/phrases
2. Flag as maintenance risk
3. Suggest alternatives or adding dates

**Implementation:**
```python
class TimeSensitiveLanguageChecker(BaseChecker):
    CHECKER_NAME = "Time-Sensitive Language"
    CHECKER_VERSION = "3.4.0"

    TIME_SENSITIVE = {
        'currently': 'as of [DATE]',
        'now': 'as of [DATE]',
        'at present': 'as of [DATE]',
        'presently': 'as of [DATE]',
        'recently': 'in [MONTH/YEAR]',
        'lately': 'in [MONTH/YEAR]',
        'soon': 'in [TIMEFRAME]',
        'shortly': 'in [TIMEFRAME]',
        'in the near future': 'by [DATE]',
        'upcoming': 'scheduled for [DATE]',
        'new': 'introduced in [VERSION/DATE]',
        'latest': '[VERSION] (released [DATE])',
        'modern': 'current (as of [DATE])',
        'today': '[ACTUAL DATE]',
        'yesterday': '[ACTUAL DATE]',
        'last week': '[DATE RANGE]',
        'last month': '[MONTH YEAR]',
        'last year': '[YEAR]',
        'this year': '[YEAR]',
        'next year': '[YEAR]',
    }

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            text_lower = text.lower()

            for phrase, suggestion in self.TIME_SENSITIVE.items():
                if phrase in text_lower:
                    # Find actual match with case
                    pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
                    for match in pattern.finditer(text):
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f"Time-sensitive language: '{match.group()}' may become outdated",
                            context=text[max(0, match.start()-30):match.end()+30],
                            paragraph_index=idx,
                            suggestion=f"Consider using specific dates/versions: {suggestion}",
                            rule_id='TIME001',
                            flagged_text=match.group()
                        ))

        return issues[:15]
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (2 hours)

---

### MODULE 3: acronym_enhanced_checkers.py

**Purpose:** Advanced acronym validation beyond basic detection

---

#### Checker 12: AcronymFirstUseChecker

**Gap Addressed:** #3 - Enforce acronym defined on first use

**Rule Logic:**
1. Build map of acronym definitions: "Project Management Office (PMO)"
2. Build map of acronym usages: "PMO"
3. Flag if acronym used before definition
4. Flag if acronym defined but never used afterward
5. Flag if acronym defined multiple times

**Implementation:**
```python
class AcronymFirstUseChecker(BaseChecker):
    CHECKER_NAME = "Acronym First-Use Enforcement"
    CHECKER_VERSION = "3.4.0"

    # Pattern: "Full Name (ACRONYM)"
    DEFINITION_PATTERN = re.compile(
        r'([A-Z][a-zA-Z]+(?:\s+[A-Za-z]+){0,6})\s*\(([A-Z]{2,8})\)',
        re.MULTILINE
    )

    # Pattern: Standalone acronym
    USAGE_PATTERN = re.compile(r'\b([A-Z]{2,8})\b')

    # Common acronyms that don't need definition
    UNIVERSAL_ACRONYMS = {
        'USA', 'UK', 'EU', 'UN', 'NATO', 'CEO', 'CFO', 'CTO', 'COO',
        'PDF', 'HTML', 'XML', 'JSON', 'API', 'URL', 'HTTP', 'HTTPS',
        'RAM', 'ROM', 'CPU', 'GPU', 'SSD', 'HDD', 'USB', 'HDMI',
        'AM', 'PM', 'BC', 'AD', 'MBA', 'PhD', 'MD', 'JD',
        'FAQ', 'DIY', 'ASAP', 'FYI', 'TBD', 'TBA', 'N/A',
    }

    def check(self, paragraphs, **kwargs):
        full_text = kwargs.get('full_text', '')

        # Build definition map: {acronym: (full_name, first_para_idx, char_pos)}
        definitions = {}
        for idx, text in paragraphs:
            for match in self.DEFINITION_PATTERN.finditer(text):
                full_name = match.group(1).strip()
                acronym = match.group(2)
                if acronym not in definitions:
                    definitions[acronym] = (full_name, idx, match.start())

        # Build usage map: {acronym: [(para_idx, char_pos), ...]}
        usages = defaultdict(list)
        for idx, text in paragraphs:
            for match in self.USAGE_PATTERN.finditer(text):
                acronym = match.group(1)
                if acronym not in self.UNIVERSAL_ACRONYMS:
                    usages[acronym].append((idx, match.start()))

        issues = []

        for acronym, usage_list in usages.items():
            if acronym in definitions:
                def_idx, def_pos = definitions[acronym][1], definitions[acronym][2]

                # Check if any usage comes before definition
                for use_idx, use_pos in usage_list:
                    if use_idx < def_idx or (use_idx == def_idx and use_pos < def_pos):
                        # Usage before definition
                        issues.append(self.create_issue(
                            severity='High',
                            message=f"Acronym '{acronym}' used before it is defined",
                            context=paragraphs[use_idx][1][:80] if use_idx < len(paragraphs) else '',
                            paragraph_index=use_idx,
                            suggestion=f"Define '{acronym}' on first use: {definitions[acronym][0]} ({acronym})",
                            rule_id='ACRFIRST001',
                            flagged_text=acronym
                        ))
                        break  # Only flag first violation per acronym
            else:
                # Acronym used but never defined
                if len(usage_list) >= 2:  # Only flag if used multiple times
                    first_use = usage_list[0]
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Acronym '{acronym}' used {len(usage_list)} times but never defined",
                        context=paragraphs[first_use[0]][1][:80] if first_use[0] < len(paragraphs) else '',
                        paragraph_index=first_use[0],
                        suggestion=f"Define '{acronym}' on first use: Full Name ({acronym})",
                        rule_id='ACRFIRST002',
                        flagged_text=acronym
                    ))

        # Check for defined but unused acronyms
        for acronym, (full_name, def_idx, _) in definitions.items():
            if acronym not in usages or len(usages[acronym]) <= 1:
                # Only the definition occurrence
                issues.append(self.create_issue(
                    severity='Low',
                    message=f"Acronym '{acronym}' defined but not used afterward",
                    context=f"Defined as: {full_name} ({acronym})",
                    paragraph_index=def_idx,
                    suggestion="Remove unused acronym definition or use the acronym in text",
                    rule_id='ACRFIRST003',
                    flagged_text=acronym
                ))

        return issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Medium (4-5 hours)

---

#### Checker 13: AcronymMultipleDefinitionChecker

**Gap Addressed:** Extension of #3 - Flag acronyms defined multiple times

**Rule Logic:**
1. Detect multiple definitions of same acronym
2. Flag as redundancy/consistency issue

**Implementation:**
```python
class AcronymMultipleDefinitionChecker(BaseChecker):
    CHECKER_NAME = "Acronym Multiple Definition"
    CHECKER_VERSION = "3.4.0"

    DEFINITION_PATTERN = re.compile(
        r'([A-Z][a-zA-Z]+(?:\s+[A-Za-z]+){0,6})\s*\(([A-Z]{2,8})\)'
    )

    def check(self, paragraphs, **kwargs):
        # Track all definitions: {acronym: [(full_name, para_idx), ...]}
        all_definitions = defaultdict(list)

        for idx, text in paragraphs:
            for match in self.DEFINITION_PATTERN.finditer(text):
                full_name = match.group(1).strip()
                acronym = match.group(2)
                all_definitions[acronym].append((full_name, idx))

        issues = []

        for acronym, defs in all_definitions.items():
            if len(defs) > 1:
                # Multiple definitions
                locations = [f"paragraph {d[1]}" for d in defs]
                issues.append(self.create_issue(
                    severity='Medium',
                    message=f"Acronym '{acronym}' defined {len(defs)} times",
                    context=f"Defined in: {', '.join(locations)}",
                    paragraph_index=defs[1][1],  # Flag second definition
                    suggestion="Define acronym only on first use; remove redundant definitions",
                    rule_id='ACRDUP001',
                    flagged_text=acronym
                ))

        return issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (1-2 hours, leverages previous checker)

---

### MODULE 4: procedural_writing_checkers.py

**Purpose:** Validate procedural/instructional writing quality

---

#### Checker 14: ImperativeMoodChecker

**Gap Addressed:** #4 - Procedural steps should use imperative mood

**Rule Logic:**
1. Detect numbered/bulleted lists (procedure steps)
2. Analyze first verb in each step
3. Flag non-imperative constructions:
   - "You should click..." → "Click..."
   - "The user must enter..." → "Enter..."
   - "Click on the button" (correct)
4. Requires spaCy for POS tagging (graceful fallback)

**Implementation:**
```python
class ImperativeMoodChecker(BaseChecker):
    CHECKER_NAME = "Imperative Mood for Procedures"
    CHECKER_VERSION = "3.4.0"

    # Patterns indicating non-imperative instructions
    NON_IMPERATIVE_PATTERNS = [
        (r'\b(you\s+should\s+)(\w+)', 'you should'),
        (r'\b(you\s+must\s+)(\w+)', 'you must'),
        (r'\b(you\s+need\s+to\s+)(\w+)', 'you need to'),
        (r'\b(you\s+can\s+)(\w+)', 'you can'),
        (r'\b(you\s+will\s+)(\w+)', 'you will'),
        (r'\b(the\s+user\s+should\s+)(\w+)', 'the user should'),
        (r'\b(the\s+user\s+must\s+)(\w+)', 'the user must'),
        (r'\b(users\s+should\s+)(\w+)', 'users should'),
        (r'\b(it\s+is\s+recommended\s+to\s+)(\w+)', 'it is recommended to'),
        (r'\b(make\s+sure\s+to\s+)(\w+)', 'make sure to'),
        (r'\b(be\s+sure\s+to\s+)(\w+)', 'be sure to'),
    ]

    # Detect procedural context
    PROCEDURE_INDICATORS = re.compile(
        r'^\s*(?:\d+[.)]\s*|[•●○◦▪▫-]\s*|step\s+\d+[:.]\s*)',
        re.IGNORECASE | re.MULTILINE
    )

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            # Check if this looks like a procedure step
            if not self.PROCEDURE_INDICATORS.search(text):
                continue

            # Remove the list marker for analysis
            clean_text = self.PROCEDURE_INDICATORS.sub('', text).strip()

            for pattern, description in self.NON_IMPERATIVE_PATTERNS:
                match = re.search(pattern, clean_text, re.IGNORECASE)
                if match:
                    # Extract the verb
                    verb = match.group(2) if match.lastindex >= 2 else ''
                    verb_capitalized = verb.capitalize() if verb else ''

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Non-imperative mood in procedure: '{description}...'",
                        context=clean_text[:80],
                        paragraph_index=idx,
                        suggestion=f"Use imperative mood: '{verb_capitalized}...' instead of '{description}...'",
                        rule_id='IMPER001',
                        flagged_text=match.group(0)
                    ))
                    break  # One issue per paragraph

        return issues
```

**Dependencies:** None (regex-based; spaCy enhancement optional)
**Data Files:** None
**Effort:** Medium (3-4 hours)

---

#### Checker 15: SecondPersonChecker

**Gap Addressed:** #5 - Prefer "you" over "the user" for engagement

**Rule Logic:**
1. Detect "the user", "users", "one should"
2. Suggest "you" alternatives
3. Exclude formal/legal contexts if detected

**Implementation:**
```python
class SecondPersonChecker(BaseChecker):
    CHECKER_NAME = "Second Person Preference"
    CHECKER_VERSION = "3.4.0"

    THIRD_PERSON_PATTERNS = [
        (r'\bthe user\s+(should|must|can|will|needs to|has to)\b', 'the user'),
        (r'\busers\s+(should|must|can|will|need to|have to)\b', 'users'),
        (r'\bone\s+(should|must|can|will)\b', 'one'),
        (r'\bhe or she\s+(should|must|can|will)\b', 'he or she'),
        (r'\bhe/she\s+(should|must|can|will)\b', 'he/she'),
        (r'\bthe customer\s+(should|must|can|will)\b', 'the customer'),
        (r'\bthe reader\s+(should|must|can|will)\b', 'the reader'),
        (r'\bthe administrator\s+(should|must|can|will)\b', 'the administrator'),
    ]

    REPLACEMENTS = {
        'the user should': 'you should',
        'the user must': 'you must',
        'the user can': 'you can',
        'the user will': 'you will',
        'the user needs to': 'you need to',
        'the user has to': 'you have to',
        'users should': 'you should',
        'users must': 'you must',
        'users can': 'you can',
        'users need to': 'you need to',
        'one should': 'you should',
        'one must': 'you must',
    }

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            for pattern, description in self.THIRD_PERSON_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matched_text = match.group(0).lower()
                    replacement = self.REPLACEMENTS.get(matched_text, f"you {match.group(1)}")

                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Third person '{description}' - consider second person 'you'",
                        context=text[max(0, match.start()-20):match.end()+20],
                        paragraph_index=idx,
                        suggestion=f"Use '{replacement}' for more direct, engaging writing",
                        rule_id='SECOND001',
                        flagged_text=match.group(0),
                        replacement_text=replacement
                    ))

        return issues[:15]
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (2-3 hours)

---

#### Checker 16: LinkTextQualityChecker

**Gap Addressed:** #11 - "Click here" is bad link text

**Rule Logic:**
1. Detect poor link text patterns
2. Detect links from document structure if available
3. Flag accessibility issues

**Implementation:**
```python
class LinkTextQualityChecker(BaseChecker):
    CHECKER_NAME = "Link Text Quality"
    CHECKER_VERSION = "3.4.0"

    BAD_LINK_TEXT = [
        (r'\bclick\s+here\b', 'click here', 'Describe the destination'),
        (r'\bhere\b(?=\s*[.)]|\s*$)', 'here', 'Describe what "here" links to'),
        (r'\bread\s+more\b', 'read more', 'Specify what will be read'),
        (r'\blearn\s+more\b', 'learn more', 'Specify what will be learned'),
        (r'\bmore\s+info\b', 'more info', 'Specify what information'),
        (r'\bmore\s+information\b', 'more information', 'Specify the topic'),
        (r'\bthis\s+link\b', 'this link', 'Describe the destination'),
        (r'\bthis\s+page\b', 'this page', 'Name the page'),
        (r'\bgo\s+here\b', 'go here', 'Describe the destination'),
        (r'\bvisit\s+this\b', 'visit this', 'Name what to visit'),
        (r'\blink\b(?=\s*[.)]|\s*$)', 'link', 'Describe the link destination'),
    ]

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            for pattern, bad_text, suggestion in self.BAD_LINK_TEXT:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Vague link text: '{match.group()}'",
                        context=text[max(0, match.start()-30):match.end()+30],
                        paragraph_index=idx,
                        suggestion=f"{suggestion}. Example: 'See the Installation Guide' instead of 'click here'",
                        rule_id='LINK001',
                        flagged_text=match.group()
                    ))

        return issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Low (2 hours)

---

### MODULE 5: document_quality_checkers.py

**Purpose:** Validate document structure and element quality

---

#### Checker 17: NumberedListSequenceChecker

**Gap Addressed:** #16 - Verify numbered lists are sequential

**Rule Logic:**
1. Detect numbered list items
2. Track sequence within each list
3. Flag gaps or restarts

**Implementation:**
```python
class NumberedListSequenceChecker(BaseChecker):
    CHECKER_NAME = "Numbered List Sequence"
    CHECKER_VERSION = "3.4.0"

    # Pattern: "1." "2)" "3:" at start of paragraph
    NUMBERED_ITEM = re.compile(r'^\s*(\d+)[.):]?\s+')

    def check(self, paragraphs, **kwargs):
        issues = []

        current_list = []  # [(expected_num, actual_num, para_idx), ...]

        for idx, text in paragraphs:
            match = self.NUMBERED_ITEM.match(text)

            if match:
                num = int(match.group(1))

                if not current_list:
                    # Start of new list
                    if num != 1:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f"Numbered list starts at {num}, expected 1",
                            context=text[:60],
                            paragraph_index=idx,
                            suggestion="Start numbered lists at 1",
                            rule_id='LISTSEQ001',
                            flagged_text=str(num)
                        ))
                    current_list.append((1, num, idx))
                else:
                    expected = current_list[-1][0] + 1
                    if num != expected:
                        if num < expected:
                            issues.append(self.create_issue(
                                severity='Medium',
                                message=f"List number {num} is out of sequence (expected {expected})",
                                context=text[:60],
                                paragraph_index=idx,
                                suggestion=f"Change to {expected} or verify list structure",
                                rule_id='LISTSEQ002',
                                flagged_text=str(num)
                            ))
                        else:
                            # Gap detected
                            issues.append(self.create_issue(
                                severity='High',
                                message=f"Gap in numbered list: jumped from {current_list[-1][1]} to {num}",
                                context=text[:60],
                                paragraph_index=idx,
                                suggestion=f"Missing list item(s) {expected} through {num-1}",
                                rule_id='LISTSEQ003',
                                flagged_text=str(num)
                            ))
                    current_list.append((expected, num, idx))
            else:
                # Non-numbered paragraph - check if it's end of list
                if current_list and len(text.strip()) > 50:
                    # Substantial text breaks the list
                    current_list = []

        return issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Medium (3 hours)

---

#### Checker 18: ProductNameConsistencyChecker

**Gap Addressed:** #14 - Validate product name capitalization

**Rule Logic:**
1. Load known product names with correct capitalization
2. Detect variations (JavaScript vs Javascript)
3. Suggest correct form

**Implementation:**
```python
class ProductNameConsistencyChecker(BaseChecker):
    CHECKER_NAME = "Product Name Consistency"
    CHECKER_VERSION = "3.4.0"

    def __init__(self):
        super().__init__()
        self.product_names = self._load_product_names()

    def _load_product_names(self):
        """Load product name database."""
        try:
            import json
            with open('data/product_names.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback: common product names
            return {
                # Format: "correct": ["wrong1", "wrong2", ...]
                "JavaScript": ["Javascript", "JAVASCRIPT", "java script"],
                "TypeScript": ["Typescript", "TYPESCRIPT"],
                "Node.js": ["NodeJS", "Nodejs", "node.js", "nodejs"],
                "GitHub": ["Github", "GITHUB", "git hub"],
                "GitLab": ["Gitlab", "GITLAB"],
                "PostgreSQL": ["Postgresql", "POSTGRESQL", "postgres"],
                "MySQL": ["MySql", "MYSQL", "mysql"],
                "MongoDB": ["Mongodb", "MONGODB"],
                "macOS": ["MacOS", "MACOS", "macos", "Mac OS"],
                "iOS": ["IOS", "ios", "Ios"],
                "iPadOS": ["iPados", "IPADOS"],
                "watchOS": ["WatchOS", "WATCHOS"],
                "tvOS": ["TvOS", "TVOS"],
                "Windows": ["WINDOWS", "windows"],
                "Linux": ["LINUX", "linux"],
                "PowerShell": ["Powershell", "POWERSHELL", "powershell"],
                "Docker": ["DOCKER", "docker"],
                "Kubernetes": ["kubernetes", "KUBERNETES"],
                "Redis": ["REDIS", "redis"],
                "Elasticsearch": ["ElasticSearch", "ELASTICSEARCH", "elastic search"],
                "GraphQL": ["Graphql", "GRAPHQL", "graphql"],
                "OAuth": ["Oauth", "OAUTH", "oauth"],
                "Wi-Fi": ["Wifi", "WIFI", "wifi", "WiFi"],
                "Bluetooth": ["BlueTooth", "BLUETOOTH", "bluetooth"],
                "Microsoft": ["MICROSOFT", "microsoft"],
                "Google": ["GOOGLE", "google"],
                "Amazon": ["AMAZON", "amazon"],
                "AWS": ["aws", "Aws"],
            }

    def check(self, paragraphs, **kwargs):
        issues = []

        for idx, text in paragraphs:
            for correct, wrongs in self.product_names.items():
                for wrong in wrongs:
                    # Case-sensitive search for wrong version
                    pattern = re.compile(r'\b' + re.escape(wrong) + r'\b')
                    for match in pattern.finditer(text):
                        issues.append(self.create_issue(
                            severity='Low',
                            message=f"Product name '{match.group()}' should be '{correct}'",
                            context=text[max(0, match.start()-20):match.end()+20],
                            paragraph_index=idx,
                            suggestion=f"Use official name: {correct}",
                            rule_id='PRODNAME001',
                            flagged_text=match.group(),
                            replacement_text=correct
                        ))

        return issues
```

**Dependencies:** None
**Data Files:** `data/product_names.json` (will create with 200+ products)
**Effort:** Medium (3-4 hours including data file)

---

#### Checker 19: CrossReferenceTargetChecker

**Gap Addressed:** #17 - Verify cross-reference targets are appropriate

**Rule Logic:**
1. Extract all cross-references: "See Table 5", "Refer to Section 3.2"
2. Extract all targets: tables, figures, sections
3. Verify reference-target semantic match (Table refs → tables, etc.)

**Implementation:**
```python
class CrossReferenceTargetChecker(BaseChecker):
    CHECKER_NAME = "Cross-Reference Target Validator"
    CHECKER_VERSION = "3.4.0"

    # Cross-reference patterns
    XREF_PATTERNS = [
        (r'\b(?:see|refer\s+to|as\s+shown\s+in)\s+(Table\s+\d+)', 'table'),
        (r'\b(?:see|refer\s+to|as\s+shown\s+in)\s+(Figure\s+\d+)', 'figure'),
        (r'\b(?:see|refer\s+to|as\s+described\s+in)\s+(Section\s+[\d.]+)', 'section'),
        (r'\b(?:see|refer\s+to)\s+(Appendix\s+[A-Z])', 'appendix'),
        (r'\b(?:see|per)\s+(Requirement\s+[\d.]+)', 'requirement'),
        (r'\b(Table\s+\d+)\s+(?:shows|lists|contains|provides)', 'table'),
        (r'\b(Figure\s+\d+)\s+(?:shows|illustrates|depicts)', 'figure'),
    ]

    def check(self, paragraphs, **kwargs):
        tables = kwargs.get('tables', [])
        figures = kwargs.get('figures', [])
        headings = kwargs.get('headings', [])

        issues = []

        # Build available targets
        available_tables = set()
        available_figures = set()
        available_sections = set()

        for i, table in enumerate(tables, 1):
            available_tables.add(f"Table {i}")
            if 'number' in table:
                available_tables.add(f"Table {table['number']}")

        for fig in figures:
            if 'number' in fig:
                available_figures.add(f"Figure {fig['number']}")

        for h in headings:
            if 'number' in h:
                available_sections.add(f"Section {h['number']}")

        # Check references
        for idx, text in paragraphs:
            for pattern, ref_type in self.XREF_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    ref = match.group(1)

                    # Verify target exists
                    if ref_type == 'table' and ref not in available_tables:
                        if available_tables:  # Only flag if we have table data
                            issues.append(self.create_issue(
                                severity='High',
                                message=f"Reference to '{ref}' - target not found",
                                context=match.group(0),
                                paragraph_index=idx,
                                suggestion=f"Available tables: {', '.join(sorted(available_tables)[:5])}",
                                rule_id='XREF001',
                                flagged_text=ref
                            ))

                    elif ref_type == 'figure' and ref not in available_figures:
                        if available_figures:
                            issues.append(self.create_issue(
                                severity='High',
                                message=f"Reference to '{ref}' - target not found",
                                context=match.group(0),
                                paragraph_index=idx,
                                suggestion=f"Available figures: {', '.join(sorted(available_figures)[:5])}",
                                rule_id='XREF002',
                                flagged_text=ref
                            ))

        return issues
```

**Dependencies:** None
**Data Files:** None
**Effort:** Medium (3-4 hours)

---

#### Checker 20: CodeFormattingConsistencyChecker

**Gap Addressed:** #15 - Consistent formatting of code/UI elements

**Rule Logic:**
1. Detect inline code patterns (backticks, monospace indicators)
2. Detect UI element references (button names, menu items)
3. Flag inconsistent formatting

**Implementation:**
```python
class CodeFormattingConsistencyChecker(BaseChecker):
    CHECKER_NAME = "Code/UI Formatting Consistency"
    CHECKER_VERSION = "3.4.0"

    # Common code/command patterns that should be formatted
    CODE_INDICATORS = [
        r'\b(npm\s+\w+)\b',           # npm commands
        r'\b(pip\s+\w+)\b',           # pip commands
        r'\b(git\s+\w+)\b',           # git commands
        r'\b(docker\s+\w+)\b',        # docker commands
        r'\b\w+\(\)\b',               # Function calls: myFunction()
        r'\b\w+\.\w+\(\)\b',          # Method calls: obj.method()
        r'--\w+(?:=\w+)?',            # CLI flags: --verbose, --output=file
        r'-[a-zA-Z]\b',               # Short flags: -v, -f
        r'\$\w+',                     # Variables: $PATH, $HOME
        r'\b(?:true|false|null|undefined|None|TRUE|FALSE|NULL)\b',  # Literals
    ]

    # UI element patterns (often in quotes or special formatting)
    UI_PATTERNS = [
        (r'click(?:ing)?\s+(?:the\s+)?["\']?(\w+(?:\s+\w+)?)["\']?\s+button', 'button'),
        (r'select(?:ing)?\s+(?:the\s+)?["\']?(\w+(?:\s+\w+)*)["\']?\s+(?:from|menu|option)', 'menu'),
        (r'(?:the\s+)?["\']?(\w+(?:\s+\w+)?)["\']?\s+(?:tab|panel|window|dialog)', 'ui_element'),
    ]

    def check(self, paragraphs, **kwargs):
        issues = []

        # Track formatting styles used
        formatted_code = []  # Items in backticks or code tags
        unformatted_code = []  # Matching patterns without formatting

        for idx, text in paragraphs:
            # Check for code that should be formatted
            for pattern in self.CODE_INDICATORS:
                for match in re.finditer(pattern, text):
                    matched = match.group()
                    # Check if it's in backticks
                    # Simple check: is there a backtick before and after?
                    pre = text[:match.start()]
                    post = text[match.end():]

                    in_backticks = (pre.endswith('`') or pre.endswith('`')) and post.startswith('`')

                    if not in_backticks and len(matched) > 2:
                        unformatted_code.append((matched, idx, text))

        # Report unformatted code (limit to avoid spam)
        seen = set()
        for code, idx, text in unformatted_code[:20]:
            if code.lower() not in seen:
                seen.add(code.lower())
                issues.append(self.create_issue(
                    severity='Low',
                    message=f"Code/command '{code}' may need formatting",
                    context=text[max(0, text.find(code)-20):text.find(code)+len(code)+20],
                    paragraph_index=idx,
                    suggestion="Consider using code formatting: `" + code + "`",
                    rule_id='CODEFMT001',
                    flagged_text=code
                ))

        return issues[:10]
```

**Dependencies:** None
**Data Files:** None
**Effort:** Medium (3-4 hours)

---

### MODULE 6: compliance_checkers.py

**Purpose:** Domain-specific compliance validation

---

#### Checker 21: MILStd40051Checker

**Gap Addressed:** #18 - MIL-STD-40051 compliance for technical manuals

**Rule Logic:**
1. Load MIL-STD-40051 documentation rules
2. Check structural requirements
3. Check style requirements
4. Flag violations

**Implementation:**
```python
class MILStd40051Checker(BaseChecker):
    CHECKER_NAME = "MIL-STD-40051 Compliance"
    CHECKER_VERSION = "3.4.0"

    def __init__(self):
        super().__init__()
        self.rules = self._load_rules()

    def _load_rules(self):
        """Load MIL-STD-40051 rule patterns."""
        try:
            import json
            with open('data/mil_std_40051_patterns.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback: core rules
            return {
                'warnings': {
                    # Warning structure
                    'warning_format': {
                        'pattern': r'\bWARNING\b(?!\s*:|\s*-|\s*\n)',
                        'message': "WARNING should be followed by colon or on separate line",
                        'severity': 'Medium'
                    },
                    'caution_format': {
                        'pattern': r'\bCAUTION\b(?!\s*:|\s*-|\s*\n)',
                        'message': "CAUTION should be followed by colon or on separate line",
                        'severity': 'Medium'
                    },
                    'note_format': {
                        'pattern': r'\bNOTE\b(?!\s*:|\s*-|\s*\n)',
                        'message': "NOTE should be followed by colon or on separate line",
                        'severity': 'Low'
                    },
                },
                'style': {
                    # Active voice preference
                    'passive_warning': {
                        'pattern': r'\b(damage|injury|death)\s+(may|can|could)\s+be\s+caused\b',
                        'message': "Use active voice in warnings: 'X can cause injury' not 'injury can be caused'",
                        'severity': 'High'
                    },
                    # Direct address
                    'indirect_instruction': {
                        'pattern': r'\b(the\s+operator|the\s+technician)\s+(should|must)\b',
                        'message': "Use direct address: 'You must...' not 'The operator must...'",
                        'severity': 'Medium'
                    },
                },
                'structure': {
                    # Required elements check (placeholders)
                    'missing_scope': {
                        'pattern': None,  # Structural check
                        'message': "Technical manual should have Scope section",
                        'severity': 'High'
                    },
                }
            }

    def check(self, paragraphs, **kwargs):
        issues = []
        full_text = kwargs.get('full_text', '')

        # Pattern-based checks
        for category, rules in self.rules.items():
            for rule_id, rule in rules.items():
                if rule.get('pattern'):
                    pattern = re.compile(rule['pattern'], re.IGNORECASE)
                    for idx, text in paragraphs:
                        for match in pattern.finditer(text):
                            issues.append(self.create_issue(
                                severity=rule['severity'],
                                message=f"MIL-STD-40051: {rule['message']}",
                                context=text[max(0, match.start()-30):match.end()+30],
                                paragraph_index=idx,
                                suggestion="Refer to MIL-STD-40051 for technical manual requirements",
                                rule_id=f"MIL40051-{rule_id.upper()}"
                            ))

        return issues[:20]
```

**Dependencies:** None
**Data Files:** `data/mil_std_40051_patterns.json` (will create)
**Effort:** High (6-8 hours including research and data file)

---

#### Checker 22: S1000DBasicChecker

**Gap Addressed:** #19 - S1000D/IETM basic validation

**Rule Logic:**
1. Detect S1000D-style content markers
2. Validate basic structural patterns
3. Flag common S1000D issues

**Implementation:**
```python
class S1000DBasicChecker(BaseChecker):
    CHECKER_NAME = "S1000D Basic Validation"
    CHECKER_VERSION = "3.4.0"

    def __init__(self):
        super().__init__()
        self.rules = self._load_rules()

    def _load_rules(self):
        """Load S1000D basic rule patterns."""
        try:
            import json
            with open('data/s1000d_basic_rules.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'data_module_codes': {
                    # DMC format validation
                    'dmc_format': {
                        'pattern': r'\bDMC[-:]\s*[A-Z0-9-]+\b',
                        'valid_pattern': r'^DMC[-:]\s*[A-Z]{2,4}-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+',
                        'message': "Data Module Code format may be incorrect",
                        'severity': 'Medium'
                    },
                },
                'procedural': {
                    # Procedural step format
                    'step_numbering': {
                        'pattern': r'^\s*Step\s+\d+[.:]\s',
                        'message': "S1000D uses numbered paragraphs, not 'Step N' format",
                        'severity': 'Low'
                    },
                },
                'warnings_cautions': {
                    # Warning/Caution placement
                    'warning_before_step': {
                        'pattern': r'(\d+[.)]\s+.+)\s+(WARNING|CAUTION):',
                        'message': "Warnings/Cautions should precede the step, not follow",
                        'severity': 'High'
                    },
                }
            }

    def check(self, paragraphs, **kwargs):
        issues = []

        for category, rules in self.rules.items():
            for rule_id, rule in rules.items():
                if rule.get('pattern'):
                    pattern = re.compile(rule['pattern'], re.IGNORECASE | re.MULTILINE)
                    for idx, text in paragraphs:
                        for match in pattern.finditer(text):
                            issues.append(self.create_issue(
                                severity=rule['severity'],
                                message=f"S1000D: {rule['message']}",
                                context=match.group(0),
                                paragraph_index=idx,
                                suggestion="Refer to S1000D specification for correct format",
                                rule_id=f"S1000D-{rule_id.upper()}"
                            ))

        return issues[:15]
```

**Dependencies:** None
**Data Files:** `data/s1000d_basic_rules.json` (will create)
**Effort:** High (6-8 hours including research)

---

#### Checker 23: AS9100DocChecker

**Gap Addressed:** #20 - AS9100 documentation requirements

**Rule Logic:**
1. Check for AS9100 required documentation elements
2. Validate traceability markers
3. Check revision control indicators

**Implementation:**
```python
class AS9100DocChecker(BaseChecker):
    CHECKER_NAME = "AS9100 Documentation Requirements"
    CHECKER_VERSION = "3.4.0"

    def __init__(self):
        super().__init__()
        self.requirements = self._load_requirements()

    def _load_requirements(self):
        """Load AS9100 documentation requirements."""
        try:
            import json
            with open('data/as9100_doc_requirements.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'document_control': {
                    'revision_marker': {
                        'search_for': ['revision', 'rev.', 'rev:', 'version'],
                        'message': "AS9100 requires revision identification",
                        'required': True,
                        'severity': 'High'
                    },
                    'approval_marker': {
                        'search_for': ['approved by', 'approval', 'authorized'],
                        'message': "AS9100 requires approval identification",
                        'required': True,
                        'severity': 'High'
                    },
                    'date_marker': {
                        'search_for': ['date:', 'effective date', 'issue date'],
                        'message': "AS9100 requires document dating",
                        'required': True,
                        'severity': 'High'
                    },
                },
                'traceability': {
                    'requirement_ids': {
                        'pattern': r'\b(REQ|RQ|SRD|SRS)[-_]?\d+\b',
                        'message': "Requirement traceability detected - verify complete coverage",
                        'severity': 'Info'
                    },
                },
                'records': {
                    'record_retention': {
                        'search_for': ['retain', 'retention', 'record keeping'],
                        'message': "AS9100 requires defined record retention",
                        'required': False,
                        'severity': 'Low'
                    },
                }
            }

    def check(self, paragraphs, **kwargs):
        issues = []
        full_text = kwargs.get('full_text', '').lower()

        # Check for required elements
        for category, requirements in self.requirements.items():
            for req_id, req in requirements.items():
                if 'search_for' in req:
                    found = any(term in full_text for term in req['search_for'])
                    if req.get('required') and not found:
                        issues.append(self.create_issue(
                            severity=req['severity'],
                            message=f"AS9100: {req['message']}",
                            context="Document-level check",
                            paragraph_index=0,
                            suggestion=f"Consider adding: {', '.join(req['search_for'][:3])}",
                            rule_id=f"AS9100-{req_id.upper()}"
                        ))

        return issues
```

**Dependencies:** None
**Data Files:** `data/as9100_doc_requirements.json` (will create)
**Effort:** High (5-6 hours including research)

---

## Data Files to Create

### 1. data/dale_chall_3000.json
**Content:** Array of 3,000 Dale-Chall easy words
**Source:** Public domain Dale-Chall word list
**Size:** ~50KB
**Creation:** Download from academic sources, format as JSON array

### 2. data/spache_easy_words.json
**Content:** Array of 1,000+ Spache easy words
**Source:** Public domain Spache formula word list
**Size:** ~20KB
**Creation:** Download from academic sources, format as JSON array

### 3. data/product_names.json
**Content:** Dictionary of correct product names and their variants
**Format:**
```json
{
  "JavaScript": ["Javascript", "JAVASCRIPT", "java script"],
  "Node.js": ["NodeJS", "Nodejs", "nodejs"],
  ...
}
```
**Size:** ~30KB
**Creation:** Compile from tech documentation standards

### 4. data/latin_abbreviations.json
**Content:** Latin abbreviations with replacements and contexts
**Size:** ~5KB
**Creation:** Compile from style guides

### 5. data/mil_std_40051_patterns.json
**Content:** MIL-STD-40051 compliance rules
**Source:** MIL-STD-40051-2 standard
**Size:** ~20KB
**Creation:** Extract rules from standard document

### 6. data/s1000d_basic_rules.json
**Content:** S1000D structural validation rules
**Source:** S1000D specification
**Size:** ~15KB
**Creation:** Extract core rules from specification

### 7. data/as9100_doc_requirements.json
**Content:** AS9100 documentation checklist
**Source:** AS9100D standard
**Size:** ~10KB
**Creation:** Extract documentation requirements from standard

---

## Integration Plan

### Phase 1: Core Module Creation (Week 1)

1. Create `style_consistency_checkers.py` (Checkers 1-6)
2. Create `clarity_checkers.py` (Checkers 7-11)
3. Create data files: `dale_chall_3000.json`, `spache_easy_words.json`
4. Write unit tests for Phase 1 checkers

### Phase 2: Acronym & Procedural (Week 2)

1. Create `acronym_enhanced_checkers.py` (Checkers 12-13)
2. Create `procedural_writing_checkers.py` (Checkers 14-16)
3. Create data file: `product_names.json`
4. Write unit tests for Phase 2 checkers

### Phase 3: Document Quality (Week 2-3)

1. Create `document_quality_checkers.py` (Checkers 17-20)
2. Test cross-reference validation with real documents
3. Write unit tests for Phase 3 checkers

### Phase 4: Compliance (Week 3-4)

1. Create `compliance_checkers.py` (Checkers 21-23)
2. Create data files: `mil_std_40051_patterns.json`, `s1000d_basic_rules.json`, `as9100_doc_requirements.json`
3. Validate against real compliance documents
4. Write unit tests for Phase 4 checkers

### Phase 5: Integration & Testing (Week 4)

1. Register all checkers in `core.py`
2. Add option mappings
3. Update version to 3.4.0
4. Full regression testing
5. Update documentation

---

## core.py Integration Code

```python
# In _init_checkers() method, add:

# ========== v3.4.0 Maximum Coverage Suite ==========
try:
    from style_consistency_checkers import get_style_consistency_checkers
    v340_style = get_style_consistency_checkers()
    self.checkers.update(v340_style)
    _log(f" Loaded {len(v340_style)} style consistency checkers (v3.4.0)")
except ImportError as e:
    _log(f" Style consistency checkers not available: {e}")

try:
    from clarity_checkers import get_clarity_checkers
    v340_clarity = get_clarity_checkers()
    self.checkers.update(v340_clarity)
    _log(f" Loaded {len(v340_clarity)} clarity checkers (v3.4.0)")
except ImportError as e:
    _log(f" Clarity checkers not available: {e}")

try:
    from acronym_enhanced_checkers import get_acronym_enhanced_checkers
    v340_acronym = get_acronym_enhanced_checkers()
    self.checkers.update(v340_acronym)
    _log(f" Loaded {len(v340_acronym)} enhanced acronym checkers (v3.4.0)")
except ImportError as e:
    _log(f" Enhanced acronym checkers not available: {e}")

try:
    from procedural_writing_checkers import get_procedural_checkers
    v340_proc = get_procedural_checkers()
    self.checkers.update(v340_proc)
    _log(f" Loaded {len(v340_proc)} procedural writing checkers (v3.4.0)")
except ImportError as e:
    _log(f" Procedural writing checkers not available: {e}")

try:
    from document_quality_checkers import get_document_quality_checkers
    v340_quality = get_document_quality_checkers()
    self.checkers.update(v340_quality)
    _log(f" Loaded {len(v340_quality)} document quality checkers (v3.4.0)")
except ImportError as e:
    _log(f" Document quality checkers not available: {e}")

try:
    from compliance_checkers import get_compliance_checkers
    v340_compliance = get_compliance_checkers()
    self.checkers.update(v340_compliance)
    _log(f" Loaded {len(v340_compliance)} compliance checkers (v3.4.0)")
except ImportError as e:
    _log(f" Compliance checkers not available: {e}")
```

---

## Option Mapping Additions

```python
# In review_document() option_mapping, add:

# v3.4.0 Style Consistency
'check_heading_case': 'heading_case_consistency',
'check_contraction_consistency': 'contraction_consistency',
'check_oxford_comma_consistency': 'oxford_comma_consistency',
'check_ari_readability': 'ari_prominence',
'check_spache_readability': 'spache_readability',
'check_dale_chall_enhanced': 'dale_chall_enhanced',

# v3.4.0 Clarity
'check_future_tense': 'future_tense',
'check_latin_abbreviations': 'latin_abbreviations',
'check_sentence_conjunctions': 'sentence_initial_conjunction',
'check_directional_language': 'directional_language',
'check_time_sensitive': 'time_sensitive_language',

# v3.4.0 Acronym Enhanced
'check_acronym_first_use': 'acronym_first_use',
'check_acronym_multiple_def': 'acronym_multiple_definition',

# v3.4.0 Procedural
'check_imperative_mood': 'imperative_mood',
'check_second_person': 'second_person',
'check_link_text': 'link_text_quality',

# v3.4.0 Document Quality
'check_list_sequence': 'numbered_list_sequence',
'check_product_names': 'product_name_consistency',
'check_xref_targets': 'cross_reference_target',
'check_code_formatting': 'code_formatting_consistency',

# v3.4.0 Compliance
'check_mil_std_40051': 'mil_std_40051',
'check_s1000d': 's1000d_basic',
'check_as9100': 'as9100_doc',
```

---

## Summary

| Module | Checkers | Dependencies | Data Files | Total Effort |
|--------|----------|--------------|------------|--------------|
| style_consistency_checkers.py | 6 | None | 2 JSON | 18-22 hours |
| clarity_checkers.py | 5 | None | None | 10-12 hours |
| acronym_enhanced_checkers.py | 2 | None | None | 5-7 hours |
| procedural_writing_checkers.py | 3 | None | 1 JSON | 7-9 hours |
| document_quality_checkers.py | 4 | None | None | 12-15 hours |
| compliance_checkers.py | 3 | None | 3 JSON | 17-22 hours |
| **TOTAL** | **23** | **None** | **6 JSON** | **69-87 hours** |

**All checkers are 100% offline-capable with no LLM dependencies.**

---

## Version Update

```json
{
  "version": "3.4.0",
  "release_date": "2026-02-XX",
  "codename": "Maximum Coverage Suite",
  "changes": [
    "NEW: 23 offline-capable checkers for comprehensive document validation",
    "NEW: style_consistency_checkers.py - Heading case, contractions, Oxford comma, ARI/Spache/Dale-Chall readability",
    "NEW: clarity_checkers.py - Future tense, Latin abbreviations, conjunctions, directional/time-sensitive language",
    "NEW: acronym_enhanced_checkers.py - First-use enforcement, multiple definition detection",
    "NEW: procedural_writing_checkers.py - Imperative mood, second person, link text quality",
    "NEW: document_quality_checkers.py - List sequences, product names, cross-ref targets, code formatting",
    "NEW: compliance_checkers.py - MIL-STD-40051, S1000D, AS9100 documentation requirements",
    "NEW: data/dale_chall_3000.json - Full 3,000-word easy word list",
    "NEW: data/spache_easy_words.json - 1,000+ word Spache formula list",
    "NEW: data/product_names.json - 200+ product name capitalizations",
    "NEW: data/mil_std_40051_patterns.json - Technical manual compliance rules",
    "NEW: data/s1000d_basic_rules.json - IETM structural validation",
    "NEW: data/as9100_doc_requirements.json - Aerospace QMS documentation checklist",
    "TOTAL: 88+ checkers (65 existing + 23 new)",
    "OFFLINE: All features 100% offline-capable for air-gapped deployment"
  ]
}
```
