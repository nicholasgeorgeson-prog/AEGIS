"""
AEGIS - Enhanced Acronym Checkers Module
Version: 3.4.0
Created: February 3, 2026

Provides advanced acronym validation beyond basic detection.
All checkers are 100% offline-capable with no external API dependencies.

Checkers included:
1. AcronymFirstUseChecker - Enforces acronym defined on first use
2. AcronymMultipleDefinitionChecker - Flags acronyms defined multiple times

Usage:
    from acronym_enhanced_checkers import get_acronym_enhanced_checkers
    checkers = get_acronym_enhanced_checkers()
"""

import re
from typing import Dict, List, Any, Tuple, Set
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
# SHARED: Universal Acronyms (don't need definition)
# =============================================================================

UNIVERSAL_ACRONYMS = {
    # Countries/Regions
    'USA', 'US', 'UK', 'EU', 'UN', 'NATO', 'UAE', 'USSR',

    # Common titles
    'CEO', 'CFO', 'CTO', 'COO', 'CIO', 'CSO', 'CMO',
    'VP', 'SVP', 'EVP', 'MD', 'PhD', 'MBA', 'JD', 'RN', 'LPN',

    # Technology (universally known)
    'PDF', 'HTML', 'XML', 'JSON', 'API', 'URL', 'HTTP', 'HTTPS', 'FTP',
    'RAM', 'ROM', 'CPU', 'GPU', 'SSD', 'HDD', 'USB', 'HDMI', 'VGA', 'DVI',
    'LAN', 'WAN', 'WiFi', 'GPS', 'SMS', 'MMS',
    'GUI', 'CLI', 'SDK', 'IDE', 'OS',

    # File formats
    'JPG', 'JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'SVG',
    'DOC', 'DOCX', 'XLS', 'XLSX', 'PPT', 'PPTX', 'CSV', 'TXT',
    'MP3', 'MP4', 'AVI', 'MOV', 'WAV', 'FLAC',
    'ZIP', 'RAR', 'TAR', 'GZ',

    # Time/Calendar
    'AM', 'PM', 'BC', 'AD', 'BCE', 'CE',

    # Common abbreviations
    'FAQ', 'DIY', 'ASAP', 'FYI', 'TBD', 'TBA', 'NA', 'N/A',
    'ETA', 'ETD', 'EOD', 'COB', 'WIP',
    'ID', 'PIN', 'ATM', 'TV', 'DVD', 'CD', 'PC', 'MAC',

    # Measurements (when standalone)
    'AC', 'DC', 'Hz', 'MHz', 'GHz', 'KB', 'MB', 'GB', 'TB',

    # Government/Military (widely known)
    'FBI', 'CIA', 'NSA', 'DoD', 'DOD', 'NASA', 'NOAA',
    'IRS', 'FDA', 'EPA', 'OSHA', 'FAA', 'FCC', 'SEC',

    # Organizations
    'IEEE', 'ISO', 'ANSI', 'NIST', 'SAE', 'ASTM',
}


# =============================================================================
# CHECKER 1: Acronym First-Use Enforcement
# =============================================================================

class AcronymFirstUseChecker(BaseChecker):
    """
    Enforces that acronyms are defined on first use.

    Detects:
    - Acronyms used before they are defined
    - Acronyms used multiple times but never defined
    - Acronyms defined but never used afterward

    Definition pattern: "Full Name (ACRONYM)"
    """

    CHECKER_NAME = "Acronym First-Use Enforcement"
    CHECKER_VERSION = "3.4.0"

    # Pattern: "Full Name (ACRONYM)" - captures full name and acronym
    DEFINITION_PATTERN = re.compile(
        r'([A-Z][a-zA-Z]+(?:[\s-]+[A-Za-z]+){0,7})\s*\(([A-Z][A-Z0-9&/-]{1,10})\)',
        re.MULTILINE
    )

    # Pattern: Standalone acronym (2-10 uppercase letters/numbers)
    USAGE_PATTERN = re.compile(r'\b([A-Z][A-Z0-9&/-]{1,9})\b')

    # Skip patterns (not acronyms)
    SKIP_PATTERNS = {
        re.compile(r'^[IVXLCDM]+$'),  # Roman numerals
        re.compile(r'^\d+[A-Z]+$'),    # Numbers with units like 5GB
        re.compile(r'^[A-Z]\d+$'),     # Letter+number like A1, B2
    }

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.universal = UNIVERSAL_ACRONYMS

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        # Build definition map: {acronym: (full_name, para_idx, char_pos)}
        definitions = {}
        # Build usage map: {acronym: [(para_idx, char_pos), ...]}
        usages = defaultdict(list)

        # First pass: find all definitions and usages
        for idx, text in paragraphs:
            # Find definitions
            for match in self.DEFINITION_PATTERN.finditer(text):
                full_name = match.group(1).strip()
                acronym = match.group(2).upper()

                if acronym not in definitions:
                    definitions[acronym] = (full_name, idx, match.start())

            # Find usages
            for match in self.USAGE_PATTERN.finditer(text):
                acronym = match.group(1).upper()

                # Skip if not a valid acronym
                if self._should_skip(acronym):
                    continue

                usages[acronym].append((idx, match.start(), match.group()))

        issues = []

        # Check for issues
        for acronym, usage_list in usages.items():
            if acronym in definitions:
                def_info = definitions[acronym]
                def_idx, def_pos = def_info[1], def_info[2]

                # Check if any usage comes before definition
                for use_idx, use_pos, original_text in usage_list:
                    if use_idx < def_idx or (use_idx == def_idx and use_pos < def_pos):
                        # Usage before definition
                        para_text = paragraphs[use_idx][1] if use_idx < len(paragraphs) else ''
                        context = para_text[:80] if para_text else ''

                        issues.append(self.create_issue(
                            severity='High',
                            message=f"Acronym '{original_text}' used before definition",
                            context=context,
                            paragraph_index=use_idx,
                            suggestion=f"Define on first use: '{def_info[0]} ({acronym})'",
                            rule_id='ACRFIRST001',
                            flagged_text=original_text
                        ))
                        break  # Only flag first violation per acronym

            else:
                # Acronym used but never defined
                # Only flag if used multiple times (single use might be intentional)
                if len(usage_list) >= 2:
                    first_use = usage_list[0]
                    para_text = paragraphs[first_use[0]][1] if first_use[0] < len(paragraphs) else ''
                    context = para_text[:80] if para_text else ''

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f"Acronym '{first_use[2]}' used {len(usage_list)} times but never defined",
                        context=context,
                        paragraph_index=first_use[0],
                        suggestion=f"Define on first use: 'Full Name ({acronym})'",
                        rule_id='ACRFIRST002',
                        flagged_text=first_use[2]
                    ))

        # Check for defined but unused acronyms
        for acronym, (full_name, def_idx, def_pos) in definitions.items():
            usage_count = len(usages.get(acronym, []))

            # The definition itself counts as one "usage" in our detection
            # So if total usages <= 1, acronym is defined but not used elsewhere
            if usage_count <= 1:
                issues.append(self.create_issue(
                    severity='Low',
                    message=f"Acronym '{acronym}' defined but not used afterward",
                    context=f"Defined as: {full_name} ({acronym})",
                    paragraph_index=def_idx,
                    suggestion="Remove unused definition or use the acronym in text",
                    rule_id='ACRFIRST003',
                    flagged_text=acronym
                ))

        return issues

    def _should_skip(self, acronym: str) -> bool:
        """Check if an acronym should be skipped."""
        # Skip universal acronyms
        if acronym in self.universal:
            return True

        # Skip based on patterns
        for pattern in self.SKIP_PATTERNS:
            if pattern.match(acronym):
                return True

        # Skip very short (likely not acronyms)
        if len(acronym) < 2:
            return True

        # Skip if all digits
        if acronym.isdigit():
            return True

        return False


# =============================================================================
# CHECKER 2: Acronym Multiple Definition
# =============================================================================

class AcronymMultipleDefinitionChecker(BaseChecker):
    """
    Flags acronyms that are defined multiple times in a document.

    Multiple definitions can confuse readers and indicate inconsistent writing.
    Acronyms should be defined once on first use.
    """

    CHECKER_NAME = "Acronym Multiple Definition"
    CHECKER_VERSION = "3.4.0"

    # Pattern: "Full Name (ACRONYM)"
    DEFINITION_PATTERN = re.compile(
        r'([A-Z][a-zA-Z]+(?:[\s-]+[A-Za-z]+){0,7})\s*\(([A-Z][A-Z0-9&/-]{1,10})\)',
        re.MULTILINE
    )

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        # Track all definitions: {acronym: [(full_name, para_idx, char_pos), ...]}
        all_definitions = defaultdict(list)

        for idx, text in paragraphs:
            for match in self.DEFINITION_PATTERN.finditer(text):
                full_name = match.group(1).strip()
                acronym = match.group(2).upper()
                all_definitions[acronym].append((full_name, idx, match.start()))

        issues = []

        for acronym, defs in all_definitions.items():
            if len(defs) > 1:
                # Multiple definitions found
                locations = [f"paragraph {d[1]+1}" for d in defs]

                # Check if definitions are consistent
                full_names = set(d[0] for d in defs)
                if len(full_names) > 1:
                    # Different definitions - more serious
                    severity = 'High'
                    message = f"Acronym '{acronym}' defined differently {len(defs)} times"
                    names_list = ', '.join(f"'{n}'" for n in full_names)
                    suggestion = f"Use one consistent definition. Found: {names_list}"
                else:
                    # Same definition repeated - less serious
                    severity = 'Medium'
                    message = f"Acronym '{acronym}' defined {len(defs)} times"
                    suggestion = "Define acronym only on first use; remove redundant definitions"

                # Flag the second and subsequent definitions
                for full_name, def_idx, _ in defs[1:]:
                    issues.append(self.create_issue(
                        severity=severity,
                        message=message,
                        context=f"'{full_name} ({acronym})' - also defined in: {', '.join(locations)}",
                        paragraph_index=def_idx,
                        suggestion=suggestion,
                        rule_id='ACRDUP001',
                        flagged_text=f"{full_name} ({acronym})"
                    ))

        return issues


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_acronym_enhanced_checkers() -> Dict[str, BaseChecker]:
    """
    Returns a dictionary of all enhanced acronym checker instances.

    Used by core.py to register checkers in bulk.
    """
    return {
        'acronym_first_use': AcronymFirstUseChecker(),
        'acronym_multiple_definition': AcronymMultipleDefinitionChecker(),
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    # Demo text with intentional issues
    demo_text = """
    The SRS must be reviewed by the quality team. The Software Requirements
    Specification (SRS) defines all system requirements.

    The PMO coordinates with the Project Management Office (PMO) weekly.
    Each team reports to the Project Management Office (PMO) for status updates.

    The API endpoint returns JSON data. Users can also use the REST interface.
    The REST interface was designed by the development team.

    The Configuration Management Plan (CMP) is maintained by the CM team.
    """

    paragraphs = [(i, p.strip()) for i, p in enumerate(demo_text.split('\n\n')) if p.strip()]

    print("=== Enhanced Acronym Checkers Demo ===\n")

    checkers = get_acronym_enhanced_checkers()

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(paragraphs, full_text=demo_text)

        if issues:
            for issue in issues:
                print(f"  [{issue.get('severity', 'Info')}] {issue.get('message', '')}")
                if issue.get('suggestion'):
                    print(f"    Suggestion: {issue.get('suggestion', '')[:80]}...")
        else:
            print("  No issues found")

    print(f"\n\nTotal checkers: {len(checkers)}")
