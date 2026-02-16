"""
AEGIS - Document Quality Checkers Module
Version: 3.4.0
Created: February 3, 2026

Provides document structure and element quality validation.
All checkers are 100% offline-capable with no external API dependencies.

Checkers included:
1. NumberedListSequenceChecker - Validates numbered list sequences
2. ProductNameConsistencyChecker - Validates product name capitalization
3. CrossReferenceTargetChecker - Validates cross-reference targets exist
4. CodeFormattingConsistencyChecker - Checks code/UI element formatting

Usage:
    from document_quality_checkers import get_document_quality_checkers
    checkers = get_document_quality_checkers()
"""

import re
import json
from typing import Dict, List, Any, Tuple, Set, Optional
from collections import Counter, defaultdict
from pathlib import Path

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
# CHECKER 1: Numbered List Sequence
# =============================================================================

class NumberedListSequenceChecker(BaseChecker):
    """
    Validates that numbered lists are sequential without gaps.

    Detects:
    - Lists not starting at 1
    - Gaps in numbering (1, 2, 4...)
    - Out-of-order numbers (1, 3, 2...)
    - Duplicate numbers (1, 2, 2, 3...)

    Common issue with PDF extraction and manual editing.
    """

    CHECKER_NAME = "Numbered List Sequence"
    CHECKER_VERSION = "3.4.0"

    # Pattern for numbered list items at start of paragraph
    NUMBERED_ITEM = re.compile(r'^\s*(\d+)([.):])\s+', re.MULTILINE)

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []

        # Track list state
        current_list = []  # [(expected, actual, para_idx, delimiter), ...]
        last_delimiter = None
        last_idx = -2  # Track paragraph indices for list continuity

        for idx, text in paragraphs:
            match = self.NUMBERED_ITEM.match(text)

            if match:
                num = int(match.group(1))
                delimiter = match.group(2)

                # Determine if this is a new list or continuation
                is_new_list = (
                    not current_list or  # No current list
                    idx > last_idx + 2 or  # Gap of more than 1 paragraph
                    (delimiter != last_delimiter and last_delimiter is not None)  # Different delimiter
                )

                if is_new_list:
                    # Start new list
                    if num != 1:
                        issues.append(self.create_issue(
                            severity='Medium',
                            message=f"Numbered list starts at {num}, expected 1",
                            context=text[:60] + ('...' if len(text) > 60 else ''),
                            paragraph_index=idx,
                            suggestion="Start numbered lists at 1",
                            rule_id='LISTSEQ001',
                            flagged_text=str(num)
                        ))
                    current_list = [(1, num, idx, delimiter)]
                else:
                    # Continue existing list
                    expected = current_list[-1][0] + 1
                    prev_num = current_list[-1][1]

                    if num == prev_num:
                        # Duplicate number
                        issues.append(self.create_issue(
                            severity='High',
                            message=f"Duplicate list number: {num} appears twice",
                            context=text[:60] + ('...' if len(text) > 60 else ''),
                            paragraph_index=idx,
                            suggestion=f"This should be {expected}",
                            rule_id='LISTSEQ002',
                            flagged_text=str(num)
                        ))
                    elif num < expected:
                        # Out of order (unless it's 1, which might be new list)
                        if num != 1:
                            issues.append(self.create_issue(
                                severity='Medium',
                                message=f"List number {num} out of sequence (expected {expected})",
                                context=text[:60] + ('...' if len(text) > 60 else ''),
                                paragraph_index=idx,
                                suggestion=f"Change to {expected} or verify list structure",
                                rule_id='LISTSEQ003',
                                flagged_text=str(num)
                            ))
                    elif num > expected:
                        # Gap in numbering
                        if num - expected == 1:
                            pass  # Minor jump, might be intentional
                        else:
                            issues.append(self.create_issue(
                                severity='High',
                                message=f"Gap in numbered list: jumped from {prev_num} to {num}",
                                context=text[:60] + ('...' if len(text) > 60 else ''),
                                paragraph_index=idx,
                                suggestion=f"Missing item(s) {expected} through {num-1}",
                                rule_id='LISTSEQ004',
                                flagged_text=str(num)
                            ))

                    current_list.append((expected, num, idx, delimiter))

                last_delimiter = delimiter
                last_idx = idx
            else:
                # Non-numbered paragraph
                # Only reset if it's substantial text (not just a sub-point)
                if len(text.strip()) > 100 and current_list:
                    current_list = []
                    last_delimiter = None

        return issues


# =============================================================================
# CHECKER 2: Product Name Consistency
# =============================================================================

class ProductNameConsistencyChecker(BaseChecker):
    """
    Validates consistent capitalization of product/technology names.

    Common issues:
    - JavaScript vs Javascript vs JAVASCRIPT
    - Node.js vs NodeJS vs Nodejs
    - macOS vs MacOS vs MACOS
    """

    CHECKER_NAME = "Product Name Consistency"
    CHECKER_VERSION = "3.4.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.product_names = self._load_product_names()

    def _load_product_names(self) -> Dict[str, List[str]]:
        """Load product name database."""
        data_path = Path(__file__).parent / 'data' / 'product_names.json'
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback: common product names
        return {
            # Programming Languages & Frameworks
            "JavaScript": ["Javascript", "JAVASCRIPT", "java script", "Java Script"],
            "TypeScript": ["Typescript", "TYPESCRIPT", "type script"],
            "Node.js": ["NodeJS", "Nodejs", "nodejs", "node.js", "NODEJS", "Node.JS"],
            "React": ["ReactJS", "react", "REACT"],
            "Angular": ["AngularJS", "angular", "ANGULAR"],
            "Vue.js": ["VueJS", "Vuejs", "vue.js", "vuejs"],
            "Python": ["python", "PYTHON"],
            "Ruby": ["ruby", "RUBY"],

            # Platforms & Operating Systems
            "macOS": ["MacOS", "MACOS", "macos", "Mac OS", "MAC OS", "Macos"],
            "iOS": ["IOS", "ios", "Ios", "i-OS"],
            "iPadOS": ["iPados", "IPADOS", "Ipados", "IPadOS"],
            "watchOS": ["WatchOS", "WATCHOS", "Watchos"],
            "tvOS": ["TvOS", "TVOS", "Tvos"],
            "Android": ["android", "ANDROID"],
            "Windows": ["windows", "WINDOWS"],
            "Linux": ["linux", "LINUX"],

            # Version Control & DevOps
            "GitHub": ["Github", "GITHUB", "git hub", "Git Hub", "GITHub"],
            "GitLab": ["Gitlab", "GITLAB", "git lab"],
            "Bitbucket": ["BitBucket", "BITBUCKET", "bitbucket"],
            "Docker": ["docker", "DOCKER"],
            "Kubernetes": ["kubernetes", "KUBERNETES", "K8S", "k8s"],

            # Databases
            "PostgreSQL": ["Postgresql", "POSTGRESQL", "postgres", "Postgres", "postgreSQL"],
            "MySQL": ["MySql", "MYSQL", "mysql", "Mysql", "mySQL"],
            "MongoDB": ["Mongodb", "MONGODB", "mongodb", "MongoDb"],
            "SQLite": ["Sqlite", "SQLITE", "sqlite", "SQlite"],
            "Redis": ["redis", "REDIS"],
            "Elasticsearch": ["ElasticSearch", "ELASTICSEARCH", "elastic search", "Elastic Search"],

            # Cloud Platforms
            "AWS": ["aws", "Aws"],
            "Azure": ["azure", "AZURE"],
            "Google Cloud": ["google cloud", "GOOGLE CLOUD", "GoogleCloud"],

            # Web Technologies
            "GraphQL": ["Graphql", "GRAPHQL", "graphql", "graphQL"],
            "REST": ["rest", "Rest"],
            "OAuth": ["Oauth", "OAUTH", "oauth", "oAuth"],
            "JSON": ["json", "Json"],
            "XML": ["xml", "Xml"],
            "HTML": ["html", "Html"],
            "CSS": ["css", "Css"],

            # Hardware & Connectivity
            "Wi-Fi": ["Wifi", "WIFI", "wifi", "WiFi", "wi-fi", "WI-FI"],
            "Bluetooth": ["BlueTooth", "BLUETOOTH", "bluetooth", "Blue Tooth"],
            "USB": ["usb", "Usb"],
            "HDMI": ["hdmi", "Hdmi"],

            # Companies
            "Microsoft": ["microsoft", "MICROSOFT", "Micro soft"],
            "Google": ["google", "GOOGLE"],
            "Amazon": ["amazon", "AMAZON"],
            "Apple": ["apple", "APPLE"],
            "Facebook": ["facebook", "FACEBOOK"],
            "Netflix": ["netflix", "NETFLIX"],

            # Tools & Software
            "PowerShell": ["Powershell", "POWERSHELL", "powershell", "Power Shell"],
            "VS Code": ["VSCode", "vscode", "VSCODE", "Vscode", "VS code"],
            "IntelliJ": ["Intellij", "INTELLIJ", "intellij"],
            "Xcode": ["XCode", "XCODE", "xcode"],

            # Frameworks & Libraries
            "jQuery": ["JQuery", "Jquery", "JQUERY", "jquery"],
            "NumPy": ["Numpy", "numpy", "NUMPY"],
            "TensorFlow": ["Tensorflow", "tensorflow", "TENSORFLOW"],
            "PyTorch": ["Pytorch", "pytorch", "PYTORCH"],

            # Standards & Protocols
            "HTTP": ["http", "Http"],
            "HTTPS": ["https", "Https"],
            "TCP/IP": ["tcp/ip", "Tcp/Ip", "TCP/ip"],
            "SSH": ["ssh", "Ssh"],
            "SSL": ["ssl", "Ssl"],
            "TLS": ["tls", "Tls"],
        }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        found_variants = set()  # Track found issues to avoid duplicates

        for idx, text in paragraphs:
            for correct, wrongs in self.product_names.items():
                for wrong in wrongs:
                    if wrong in found_variants:
                        continue

                    # Case-sensitive search for wrong version
                    # Use word boundaries
                    pattern = re.compile(r'\b' + re.escape(wrong) + r'\b')
                    match = pattern.search(text)

                    if match:
                        found_variants.add(wrong)

                        # Get context
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 20)
                        context = text[start:end]

                        issues.append(self.create_issue(
                            severity='Low',
                            message=f"Product name '{match.group()}' should be '{correct}'",
                            context=f"...{context}...",
                            paragraph_index=idx,
                            suggestion=f"Use official capitalization: {correct}",
                            rule_id='PRODNAME001',
                            flagged_text=match.group(),
                            replacement_text=correct
                        ))

        return issues


# =============================================================================
# CHECKER 3: Cross-Reference Target Validator
# =============================================================================

class CrossReferenceTargetChecker(BaseChecker):
    """
    Validates that cross-references point to existing targets.

    Checks:
    - Table references: "See Table 5" - does Table 5 exist?
    - Figure references: "Figure 3 shows..." - does Figure 3 exist?
    - Section references: "Section 2.1 describes..." - does Section 2.1 exist?
    """

    CHECKER_NAME = "Cross-Reference Target Validator"
    CHECKER_VERSION = "3.4.0"

    # Cross-reference patterns
    XREF_PATTERNS = [
        # Table references
        (r'\b(?:see|refer\s+to|in|per)\s+(Table\s+(\d+))', 'table', 2),
        (r'\b(Table\s+(\d+))\s+(?:shows|lists|contains|provides|describes|summarizes)', 'table', 2),
        (r'\bas\s+(?:shown|listed|described)\s+in\s+(Table\s+(\d+))', 'table', 2),

        # Figure references
        (r'\b(?:see|refer\s+to|in)\s+(Figure\s+(\d+))', 'figure', 2),
        (r'\b(Figure\s+(\d+))\s+(?:shows|illustrates|depicts|displays|demonstrates)', 'figure', 2),
        (r'\bas\s+(?:shown|illustrated|depicted)\s+in\s+(Figure\s+(\d+))', 'figure', 2),

        # Section references
        (r'\b(?:see|refer\s+to)\s+(Section\s+([\d.]+))', 'section', 2),
        (r'\b(Section\s+([\d.]+))\s+(?:describes|explains|discusses|covers)', 'section', 2),
        (r'\bas\s+(?:described|explained|discussed)\s+in\s+(Section\s+([\d.]+))', 'section', 2),

        # Appendix references
        (r'\b(?:see|refer\s+to)\s+(Appendix\s+([A-Z]))', 'appendix', 2),
        (r'\b(Appendix\s+([A-Z]))\s+(?:contains|provides|lists)', 'appendix', 2),

        # Chapter references
        (r'\b(?:see|refer\s+to)\s+(Chapter\s+(\d+))', 'chapter', 2),
        (r'\b(Chapter\s+(\d+))\s+(?:describes|explains|discusses)', 'chapter', 2),
    ]

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        tables = kwargs.get('tables', [])
        figures = kwargs.get('figures', [])
        headings = kwargs.get('headings', [])

        # Build available targets
        available = self._build_available_targets(tables, figures, headings)

        issues = []
        compiled_patterns = [(re.compile(p, re.IGNORECASE), t, g) for p, t, g in self.XREF_PATTERNS]

        for idx, text in paragraphs:
            for pattern, ref_type, num_group in compiled_patterns:
                for match in pattern.finditer(text):
                    full_ref = match.group(1)  # e.g., "Table 5"
                    ref_num = match.group(num_group)  # e.g., "5"

                    # Check if target exists
                    target_set = available.get(ref_type, set())

                    if target_set and ref_num not in target_set:
                        # Build suggestion
                        if target_set:
                            available_list = sorted(target_set, key=lambda x: (len(x), x))[:5]
                            suggestion = f"Available {ref_type}s: {', '.join(available_list)}"
                        else:
                            suggestion = f"No {ref_type}s detected in document"

                        issues.append(self.create_issue(
                            severity='High',
                            message=f"Reference to '{full_ref}' - target not found",
                            context=match.group(0),
                            paragraph_index=idx,
                            suggestion=suggestion,
                            rule_id=f'XREF{ref_type.upper()[:3]}001',
                            flagged_text=full_ref
                        ))

        return issues

    def _build_available_targets(self, tables, figures, headings) -> Dict[str, Set[str]]:
        """Build sets of available targets from document structure."""
        available = {
            'table': set(),
            'figure': set(),
            'section': set(),
            'appendix': set(),
            'chapter': set(),
        }

        # Add table numbers
        for i, table in enumerate(tables, 1):
            available['table'].add(str(i))
            if isinstance(table, dict) and 'number' in table:
                available['table'].add(str(table['number']))

        # Add figure numbers
        for fig in figures:
            if isinstance(fig, dict) and 'number' in fig:
                available['figure'].add(str(fig['number']))

        # Add section numbers from headings
        for h in headings:
            if isinstance(h, dict):
                # Try to extract section number from heading text
                text = h.get('text', '')
                number_match = re.match(r'^([\d.]+)\s', text)
                if number_match:
                    available['section'].add(number_match.group(1))

                # Check for appendix
                appendix_match = re.match(r'^Appendix\s+([A-Z])', text, re.IGNORECASE)
                if appendix_match:
                    available['appendix'].add(appendix_match.group(1))

                # Check for chapter
                chapter_match = re.match(r'^Chapter\s+(\d+)', text, re.IGNORECASE)
                if chapter_match:
                    available['chapter'].add(chapter_match.group(1))

        return available


# =============================================================================
# CHECKER 4: Code Formatting Consistency
# =============================================================================

class CodeFormattingConsistencyChecker(BaseChecker):
    """
    Checks for consistent formatting of code elements and UI references.

    Flags:
    - Code/commands that should be in monospace
    - Inconsistent formatting of similar elements
    - UI element references that should be formatted
    """

    CHECKER_NAME = "Code/UI Formatting Consistency"
    CHECKER_VERSION = "3.4.0"

    # Patterns that typically should be code-formatted
    CODE_PATTERNS = [
        # Commands
        (r'\bnpm\s+(?:install|run|start|test|build|init|update)\b', 'npm command'),
        (r'\bpip\s+(?:install|uninstall|freeze|list)\b', 'pip command'),
        (r'\bgit\s+(?:clone|pull|push|commit|checkout|branch|merge|status|add|diff)\b', 'git command'),
        (r'\bdocker\s+(?:run|build|pull|push|ps|exec|compose)\b', 'docker command'),
        (r'\bkubectl\s+(?:get|apply|delete|describe|logs)\b', 'kubectl command'),

        # Function/method calls
        (r'\b\w+\(\)(?!\s*[{])', 'function call'),
        (r'\b\w+\.\w+\(\)', 'method call'),

        # CLI flags
        (r'\s--[a-zA-Z][-a-zA-Z0-9]*(?:=[^\s]+)?', 'CLI flag'),
        (r'\s-[a-zA-Z]\b', 'CLI flag'),

        # Variables/environment
        (r'\$[A-Z_][A-Z0-9_]*', 'environment variable'),
        (r'\$\{[A-Z_][A-Z0-9_]*\}', 'environment variable'),

        # File paths
        (r'(?<!\w)/(?:usr|etc|var|home|opt|bin|sbin)/[\w/.-]+', 'file path'),
        (r'[A-Z]:\\[\w\\.-]+', 'file path'),

        # Common literals
        (r'\b(?:true|false|null|undefined|None|nil|NaN)\b', 'literal'),
        (r'\b(?:TRUE|FALSE|NULL)\b', 'literal'),

        # Configuration keys
        (r'\b[a-z]+(?:_[a-z]+)+\s*[:=]', 'config key'),
        (r'\b[a-z]+(?:\.[a-z]+)+\b', 'dotted identifier'),
    ]

    # UI element patterns
    UI_PATTERNS = [
        (r'(?:click(?:ing)?|press|select(?:ing)?|choose)\s+(?:the\s+)?["\']?(\w+(?:\s+\w+)?)["\']?\s+button', 'button'),
        (r'(?:in|from)\s+the\s+["\']?(\w+(?:\s+\w+)?)["\']?\s+(?:menu|dropdown|panel|tab|dialog)', 'UI element'),
        (r'the\s+["\']?(\w+(?:\s+\w+)?)["\']?\s+(?:checkbox|radio\s+button|toggle|switch)', 'control'),
    ]

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        seen_codes = set()
        compiled_code = [(re.compile(p), d) for p, d in self.CODE_PATTERNS]

        for idx, text in paragraphs:
            # Check for unformatted code
            for pattern, desc in compiled_code:
                for match in pattern.finditer(text):
                    code = match.group().strip()

                    # Skip if already seen or very short
                    if code in seen_codes or len(code) < 3:
                        continue

                    # Check if it's in backticks (simple check)
                    # Look for backtick before and after
                    start_idx = match.start()
                    end_idx = match.end()

                    pre = text[max(0, start_idx-1):start_idx]
                    post = text[end_idx:end_idx+1]

                    if pre == '`' or post == '`':
                        continue  # Already formatted

                    seen_codes.add(code)

                    issues.append(self.create_issue(
                        severity='Low',
                        message=f"Unformatted {desc}: '{code}'",
                        context=text[max(0, start_idx-20):end_idx+20],
                        paragraph_index=idx,
                        suggestion=f"Consider code formatting: `{code}`",
                        rule_id='CODEFMT001',
                        flagged_text=code
                    ))

        return issues[:15]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_document_quality_checkers() -> Dict[str, BaseChecker]:
    """
    Returns a dictionary of all document quality checker instances.

    Used by core.py to register checkers in bulk.
    """
    return {
        'numbered_list_sequence': NumberedListSequenceChecker(),
        'product_name_consistency': ProductNameConsistencyChecker(),
        'cross_reference_target': CrossReferenceTargetChecker(),
        'code_formatting_consistency': CodeFormattingConsistencyChecker(),
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    # Demo text with intentional issues
    demo_text = """
    1. First step in the process
    2. Second step
    4. Fourth step (number 3 is missing!)

    The system uses javascript for frontend and Nodejs for backend.
    Configure macOS settings in the MACOS preferences panel.

    See Table 5 for the complete list of parameters. As shown in Figure 10,
    the architecture supports multiple backends.

    Run npm install to install dependencies. Then execute the myFunction()
    to start the process. Set the $HOME variable and use --verbose flag.
    """

    # Mock document structure
    demo_tables = [{'number': 1}, {'number': 2}, {'number': 3}]
    demo_figures = [{'number': 1}, {'number': 2}]
    demo_headings = [{'text': '1.0 Introduction'}, {'text': '2.0 Installation'}]

    paragraphs = [(i, p.strip()) for i, p in enumerate(demo_text.split('\n\n')) if p.strip()]

    print("=== Document Quality Checkers Demo ===\n")

    checkers = get_document_quality_checkers()

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(
            paragraphs,
            full_text=demo_text,
            tables=demo_tables,
            figures=demo_figures,
            headings=demo_headings
        )

        if issues:
            for issue in issues[:4]:
                print(f"  [{issue.get('severity', 'Info')}] {issue.get('message', '')}")
                if issue.get('suggestion'):
                    print(f"    Suggestion: {issue.get('suggestion', '')[:70]}...")
        else:
            print("  No issues found")

    print(f"\n\nTotal checkers: {len(checkers)}")
