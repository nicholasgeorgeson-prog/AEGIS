"""
Acronym Extractor for AEGIS
======================================
Version: 1.0.0
Date: 2026-02-03

Advanced acronym extraction using the Schwartz-Hearst algorithm
and additional pattern-based detection for technical documents.

Features:
- Schwartz-Hearst algorithm for acronym-definition extraction
- Pattern-based detection for standard formats
- Aerospace/defense acronym dictionary integration
- Undefined acronym detection
- Acronym consistency checking

Usage:
    from acronym_extractor import AcronymExtractor
    extractor = AcronymExtractor()

    # Extract all acronyms with definitions
    results = extractor.extract_acronyms(text)

    # Find undefined acronyms
    undefined = extractor.find_undefined_acronyms(text)

    # Check consistency
    issues = extractor.check_consistency(text)
"""

import re
from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

# Structured logging
try:
    from config_logging import get_logger
    _logger = get_logger('acronym_extractor')
except ImportError:
    _logger = None

def _log(message: str, level: str = 'info', **kwargs):
    """Internal logging helper."""
    if _logger:
        getattr(_logger, level)(message, **kwargs)
    elif level in ('warning', 'error', 'critical'):
        print(f"[AcronymExtractor] {level.upper()}: {message}")


class AcronymStatus(Enum):
    """Status of an acronym in the document."""
    DEFINED = "defined"           # Has definition in document
    UNDEFINED = "undefined"       # Used but not defined
    KNOWN = "known"               # In standard dictionary
    INCONSISTENT = "inconsistent" # Multiple definitions


@dataclass
class AcronymEntry:
    """Represents an extracted acronym."""
    acronym: str
    expansion: Optional[str]
    status: AcronymStatus
    definition_location: Optional[int]  # Character offset where defined
    usage_locations: List[int] = field(default_factory=list)
    confidence: float = 1.0
    source: str = "pattern"  # 'schwartz_hearst', 'pattern', 'dictionary'
    alternatives: List[str] = field(default_factory=list)  # Alternative expansions found

    def to_dict(self) -> dict:
        return {
            'acronym': self.acronym,
            'expansion': self.expansion,
            'status': self.status.value,
            'definition_location': self.definition_location,
            'usage_count': len(self.usage_locations),
            'confidence': round(self.confidence, 2),
            'source': self.source,
            'alternatives': self.alternatives,
            'first_use': min(self.usage_locations) if self.usage_locations else None,
            'defined_before_use': (
                self.definition_location is not None and
                self.usage_locations and
                self.definition_location <= min(self.usage_locations)
            )
        }


@dataclass
class ConsistencyIssue:
    """Represents an acronym consistency issue."""
    acronym: str
    issue_type: str  # 'undefined', 'used_before_defined', 'multiple_definitions', 'inconsistent_case'
    message: str
    locations: List[int]
    severity: str  # 'error', 'warning', 'info'

    def to_dict(self) -> dict:
        return {
            'acronym': self.acronym,
            'issue_type': self.issue_type,
            'message': self.message,
            'locations': self.locations,
            'severity': self.severity
        }


class AcronymExtractor:
    """
    Advanced acronym extraction for technical documents.

    Implements Schwartz-Hearst algorithm plus pattern-based detection.
    """

    VERSION = '1.0.0'

    # Common acronyms that shouldn't be flagged (all-caps words that aren't acronyms)
    COMMON_WORDS_SKIP = {
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD',
        'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'HAS', 'HIS', 'HOW', 'ITS', 'MAY',
        'NEW', 'NOW', 'OLD', 'SEE', 'WAY', 'WHO', 'BOY', 'DID', 'GET', 'HIM',
        'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE', 'DAY', 'END', 'FAR', 'GOT',
        'YET', 'YES', 'SET', 'RUN', 'TOP', 'ANY', 'ASK', 'BIG', 'FEW', 'OWN',
        'ALSO', 'BACK', 'BEEN', 'CALL', 'COME', 'COULD', 'EACH', 'EVEN', 'FIND',
        'FIRST', 'FROM', 'GIVE', 'GOOD', 'HAVE', 'HERE', 'HIGH', 'INTO', 'JUST',
        'KNOW', 'LAST', 'LIKE', 'LINE', 'LONG', 'LOOK', 'MADE', 'MAKE', 'MANY',
        'MORE', 'MOST', 'MUCH', 'MUST', 'NAME', 'NEED', 'NEXT', 'ONLY', 'OVER',
        'PART', 'SAME', 'SHOW', 'SIDE', 'SOME', 'SUCH', 'TAKE', 'THAN', 'THAT',
        'THEM', 'THEN', 'THERE', 'THESE', 'THEY', 'THIS', 'TIME', 'UNDER', 'VERY',
        'WANT', 'WELL', 'WERE', 'WHAT', 'WHEN', 'WHERE', 'WHICH', 'WHILE', 'WITH',
        'WORK', 'WOULD', 'YEAR', 'YOUR', 'ABOUT', 'AFTER', 'AGAIN', 'BEING',
        'BELOW', 'BETWEEN', 'BOTH', 'BEFORE', 'COULD', 'DURING', 'EACH', 'EVERY',
        'SHALL', 'SHOULD', 'WILL', 'WOULD', 'WILL', 'NOTE', 'NOTES', 'TABLE',
        'FIGURE', 'SECTION', 'CHAPTER', 'APPENDIX', 'REFERENCE', 'ITEM', 'ITEMS'
    }

    # Standard aerospace/defense acronym dictionary
    STANDARD_ACRONYMS = {
        # Program/Project Management
        'PM': 'Program Manager',
        'PMP': 'Program Management Plan',
        'WBS': 'Work Breakdown Structure',
        'SOW': 'Statement of Work',
        'PWS': 'Performance Work Statement',
        'CDRL': 'Contract Data Requirements List',
        'DID': 'Data Item Description',
        'CDR': 'Critical Design Review',
        'PDR': 'Preliminary Design Review',
        'SRR': 'System Requirements Review',
        'TRR': 'Test Readiness Review',
        'PRR': 'Production Readiness Review',
        'FCA': 'Functional Configuration Audit',
        'PCA': 'Physical Configuration Audit',
        'IMP': 'Integrated Master Plan',
        'IMS': 'Integrated Master Schedule',

        # Systems Engineering
        'SE': 'Systems Engineer',
        'SEMP': 'Systems Engineering Management Plan',
        'SRS': 'Software Requirements Specification',
        'IRS': 'Interface Requirements Specification',
        'ICD': 'Interface Control Document',
        'SDD': 'Software Design Description',
        'STP': 'Software Test Plan',
        'STR': 'Software Test Report',
        'CONOPS': 'Concept of Operations',
        'OPSCON': 'Operational Concept',
        'TPM': 'Technical Performance Measure',
        'MOE': 'Measure of Effectiveness',
        'MOP': 'Measure of Performance',

        # Quality & Safety
        'QA': 'Quality Assurance',
        'QC': 'Quality Control',
        'FMEA': 'Failure Mode and Effects Analysis',
        'FMECA': 'Failure Mode Effects and Criticality Analysis',
        'FTA': 'Fault Tree Analysis',
        'HAZOP': 'Hazard and Operability Study',
        'PHA': 'Preliminary Hazard Analysis',
        'SHA': 'System Hazard Analysis',
        'SSHA': 'Subsystem Hazard Analysis',
        'MA': 'Mission Assurance',
        'SMA': 'Safety and Mission Assurance',
        'NCR': 'Nonconformance Report',
        'CAR': 'Corrective Action Report',
        'RCA': 'Root Cause Analysis',

        # Configuration Management
        'CM': 'Configuration Management',
        'CMP': 'Configuration Management Plan',
        'CCB': 'Configuration Control Board',
        'ECR': 'Engineering Change Request',
        'ECP': 'Engineering Change Proposal',
        'ECN': 'Engineering Change Notice',
        'DCN': 'Document Change Notice',
        'CI': 'Configuration Item',
        'CSCI': 'Computer Software Configuration Item',
        'HWCI': 'Hardware Configuration Item',

        # Testing
        'ATP': 'Acceptance Test Procedure',
        'DT': 'Developmental Test',
        'OT': 'Operational Test',
        'IV&V': 'Independent Verification and Validation',
        'VDD': 'Version Description Document',
        'RTM': 'Requirements Traceability Matrix',
        'TBD': 'To Be Determined',
        'TBR': 'To Be Resolved',
        'TBS': 'To Be Supplied',

        # Government/Contracting
        'COR': 'Contracting Officer Representative',
        'CO': 'Contracting Officer',
        'COTR': "Contracting Officer's Technical Representative",
        'GTR': 'Government Technical Representative',
        'PCO': 'Procuring Contracting Officer',
        'ACO': 'Administrative Contracting Officer',
        'DCMA': 'Defense Contract Management Agency',
        'DCAA': 'Defense Contract Audit Agency',
        'FAR': 'Federal Acquisition Regulation',
        'DFARS': 'Defense Federal Acquisition Regulation Supplement',
        'NDA': 'Non-Disclosure Agreement',
        'ITAR': 'International Traffic in Arms Regulations',
        'EAR': 'Export Administration Regulations',

        # NASA-Specific
        'NPR': 'NASA Procedural Requirement',
        'NPD': 'NASA Policy Directive',
        'GSFC': 'Goddard Space Flight Center',
        'JPL': 'Jet Propulsion Laboratory',
        'KSC': 'Kennedy Space Center',
        'JSC': 'Johnson Space Center',
        'MSFC': 'Marshall Space Flight Center',

        # DoD-Specific
        'DOD': 'Department of Defense',
        'JCIDS': 'Joint Capabilities Integration and Development System',
        'PPBE': 'Planning, Programming, Budgeting, and Execution',
        'ACAT': 'Acquisition Category',
        'MDA': 'Milestone Decision Authority',
        'DAU': 'Defense Acquisition University',

        # Technical Standards
        'MIL-STD': 'Military Standard',
        'MIL-HDBK': 'Military Handbook',
        'IEEE': 'Institute of Electrical and Electronics Engineers',
        'ISO': 'International Organization for Standardization',
        'ANSI': 'American National Standards Institute',
        'SAE': 'Society of Automotive Engineers',
        'ASTM': 'American Society for Testing and Materials',
    }

    def __init__(self, custom_dictionary: Dict[str, str] = None,
                 case_sensitive: bool = False):
        """
        Initialize the acronym extractor.

        Args:
            custom_dictionary: Additional acronym-expansion mappings
            case_sensitive: Whether to treat acronyms case-sensitively
        """
        self.case_sensitive = case_sensitive

        # Build dictionary
        self.dictionary = dict(self.STANDARD_ACRONYMS)
        if custom_dictionary:
            self.dictionary.update(custom_dictionary)

        # Compile patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for acronym detection."""
        # Pattern: "Full Name (ACRONYM)"
        self.pattern_definition = re.compile(
            r'([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Za-z]+){0,8})\s*\(([A-Z][A-Z0-9&/-]{1,12})\)',
            re.UNICODE
        )

        # Pattern: "ACRONYM (Full Name)"
        self.pattern_definition_reverse = re.compile(
            r'\b([A-Z][A-Z0-9&/-]{1,12})\s*\(([A-Z][a-z]+(?:\s+[A-Za-z]+){0,8})\)',
            re.UNICODE
        )

        # Pattern: "ACRONYM - Full Name" or "ACRONYM: Full Name"
        self.pattern_definition_dash = re.compile(
            r'\b([A-Z][A-Z0-9&/-]{1,12})\s*[-:]\s*([A-Z][a-z]+(?:\s+[A-Za-z]+){0,8})\b',
            re.UNICODE
        )

        # Pattern: Standalone acronym (2-12 uppercase letters/numbers)
        self.pattern_acronym = re.compile(
            r'(?<![a-zA-Z])([A-Z][A-Z0-9]{1,11})(?![a-zA-Z])',
            re.UNICODE
        )

        # Pattern: Mixed case acronyms (like "GHz", "MHz")
        self.pattern_mixed = re.compile(
            r'\b([A-Z][a-z]?[A-Z][a-zA-Z0-9]*)\b',
            re.UNICODE
        )

    def extract_acronyms(self, text: str) -> Dict[str, AcronymEntry]:
        """
        Extract all acronyms from text with their definitions.

        Args:
            text: Document text

        Returns:
            Dictionary mapping acronyms to AcronymEntry objects
        """
        results: Dict[str, AcronymEntry] = {}

        # Step 1: Extract definitions using patterns
        self._extract_pattern_definitions(text, results)

        # Step 2: Apply Schwartz-Hearst algorithm
        self._extract_schwartz_hearst(text, results)

        # Step 3: Find all acronym usages
        self._find_all_usages(text, results)

        # Step 4: Match against dictionary for unknowns
        self._match_dictionary(results)

        # Step 5: Determine status
        self._determine_status(results)

        return results

    def _extract_pattern_definitions(self, text: str, results: Dict[str, AcronymEntry]):
        """Extract acronym definitions using regex patterns."""

        # Pattern: "Full Name (ACRONYM)"
        for match in self.pattern_definition.finditer(text):
            expansion = match.group(1).strip()
            acronym = match.group(2).upper()

            if self._is_valid_acronym(acronym):
                if acronym not in results:
                    results[acronym] = AcronymEntry(
                        acronym=acronym,
                        expansion=expansion,
                        status=AcronymStatus.DEFINED,
                        definition_location=match.start(),
                        confidence=0.95,
                        source='pattern'
                    )
                elif results[acronym].expansion != expansion:
                    results[acronym].alternatives.append(expansion)

        # Pattern: "ACRONYM (Full Name)"
        for match in self.pattern_definition_reverse.finditer(text):
            acronym = match.group(1).upper()
            expansion = match.group(2).strip()

            if self._is_valid_acronym(acronym):
                if acronym not in results:
                    results[acronym] = AcronymEntry(
                        acronym=acronym,
                        expansion=expansion,
                        status=AcronymStatus.DEFINED,
                        definition_location=match.start(),
                        confidence=0.90,
                        source='pattern'
                    )

        # Pattern: "ACRONYM - Full Name"
        for match in self.pattern_definition_dash.finditer(text):
            acronym = match.group(1).upper()
            expansion = match.group(2).strip()

            if self._is_valid_acronym(acronym):
                if acronym not in results:
                    results[acronym] = AcronymEntry(
                        acronym=acronym,
                        expansion=expansion,
                        status=AcronymStatus.DEFINED,
                        definition_location=match.start(),
                        confidence=0.85,
                        source='pattern'
                    )

    def _extract_schwartz_hearst(self, text: str, results: Dict[str, AcronymEntry]):
        """
        Apply Schwartz-Hearst algorithm for acronym extraction.

        The algorithm identifies short forms (acronyms) and their
        corresponding long forms (expansions) based on character matching.
        """
        # Find all potential short forms in parentheses
        paren_pattern = re.compile(r'\(([^()]+)\)')

        for match in paren_pattern.finditer(text):
            short_form = match.group(1).strip()

            # Check if this could be an acronym (mostly uppercase)
            if not self._is_valid_acronym(short_form):
                continue

            short_form_upper = short_form.upper()

            # Skip if already found with high confidence
            if short_form_upper in results and results[short_form_upper].confidence >= 0.95:
                continue

            # Get text before parenthesis (potential long form)
            start = max(0, match.start() - 200)
            before_text = text[start:match.start()].strip()

            # Try to find long form using Schwartz-Hearst
            long_form = self._find_long_form(short_form, before_text)

            if long_form:
                if short_form_upper not in results:
                    results[short_form_upper] = AcronymEntry(
                        acronym=short_form_upper,
                        expansion=long_form,
                        status=AcronymStatus.DEFINED,
                        definition_location=match.start() - len(long_form),
                        confidence=0.92,
                        source='schwartz_hearst'
                    )
                elif results[short_form_upper].expansion != long_form:
                    results[short_form_upper].alternatives.append(long_form)

    def _find_long_form(self, short_form: str, text: str) -> Optional[str]:
        """
        Find the long form for a short form using Schwartz-Hearst algorithm.

        Args:
            short_form: The acronym/abbreviation
            text: Text to search for the long form

        Returns:
            The long form if found, None otherwise
        """
        short_form = short_form.upper()
        short_len = len(short_form)

        # Maximum length of long form
        max_long_len = min(short_len + 5 + short_len * 2, len(text))

        # Get candidate text
        candidate = text[-max_long_len:].strip() if len(text) > max_long_len else text.strip()

        # Remove trailing punctuation/whitespace
        candidate = re.sub(r'[\s.,;:]+$', '', candidate)

        # Try to match short form characters with long form words
        words = candidate.split()

        if not words:
            return None

        # Work backwards through short form characters
        short_idx = short_len - 1
        long_start = len(words) - 1

        for word_idx in range(len(words) - 1, -1, -1):
            if short_idx < 0:
                break

            word = words[word_idx]
            if not word:
                continue

            # Check if word starts with the short form character
            if word[0].upper() == short_form[short_idx]:
                short_idx -= 1
                long_start = word_idx

        # If we matched all characters
        if short_idx < 0:
            long_form = ' '.join(words[long_start:])

            # Validate: long form should be longer than short form
            if len(long_form) > len(short_form):
                return long_form

        return None

    def _find_all_usages(self, text: str, results: Dict[str, AcronymEntry]):
        """Find all usages of acronyms in the text."""
        for match in self.pattern_acronym.finditer(text):
            acronym = match.group(1).upper()

            if not self._is_valid_acronym(acronym):
                continue

            if acronym in results:
                results[acronym].usage_locations.append(match.start())
            else:
                # Unknown acronym
                results[acronym] = AcronymEntry(
                    acronym=acronym,
                    expansion=None,
                    status=AcronymStatus.UNDEFINED,
                    definition_location=None,
                    usage_locations=[match.start()],
                    confidence=0.0,
                    source='usage'
                )

    def _match_dictionary(self, results: Dict[str, AcronymEntry]):
        """Match undefined acronyms against the standard dictionary."""
        for acronym, entry in results.items():
            if entry.expansion is None and acronym in self.dictionary:
                entry.expansion = self.dictionary[acronym]
                entry.status = AcronymStatus.KNOWN
                entry.confidence = 0.80
                entry.source = 'dictionary'

    def _determine_status(self, results: Dict[str, AcronymEntry]):
        """Determine final status for each acronym."""
        for acronym, entry in results.items():
            if entry.alternatives:
                entry.status = AcronymStatus.INCONSISTENT
            elif entry.expansion is not None:
                if entry.source == 'dictionary':
                    entry.status = AcronymStatus.KNOWN
                else:
                    entry.status = AcronymStatus.DEFINED
            else:
                entry.status = AcronymStatus.UNDEFINED

    def _is_valid_acronym(self, text: str) -> bool:
        """Check if text is a valid acronym."""
        text_upper = text.upper().strip()

        # Must be 2-12 characters
        if len(text_upper) < 2 or len(text_upper) > 12:
            return False

        # Must start with a letter
        if not text_upper[0].isalpha():
            return False

        # Skip common words
        if text_upper in self.COMMON_WORDS_SKIP:
            return False

        # Must be mostly uppercase letters/numbers
        alpha_count = sum(1 for c in text_upper if c.isalpha())
        if alpha_count < len(text_upper) * 0.5:
            return False

        return True

    def find_undefined_acronyms(self, text: str) -> List[AcronymEntry]:
        """
        Find acronyms that are used but not defined.

        Args:
            text: Document text

        Returns:
            List of undefined acronym entries
        """
        results = self.extract_acronyms(text)
        return [
            entry for entry in results.values()
            if entry.status == AcronymStatus.UNDEFINED
        ]

    def check_consistency(self, text: str) -> List[ConsistencyIssue]:
        """
        Check for acronym consistency issues.

        Args:
            text: Document text

        Returns:
            List of consistency issues found
        """
        results = self.extract_acronyms(text)
        issues = []

        for acronym, entry in results.items():
            # Undefined acronyms
            if entry.status == AcronymStatus.UNDEFINED:
                issues.append(ConsistencyIssue(
                    acronym=acronym,
                    issue_type='undefined',
                    message=f"Acronym '{acronym}' is used but not defined",
                    locations=entry.usage_locations[:5],  # First 5 locations
                    severity='error'
                ))

            # Used before defined
            elif entry.definition_location is not None and entry.usage_locations:
                first_use = min(entry.usage_locations)
                if first_use < entry.definition_location:
                    issues.append(ConsistencyIssue(
                        acronym=acronym,
                        issue_type='used_before_defined',
                        message=f"Acronym '{acronym}' is used at position {first_use} before being defined at position {entry.definition_location}",
                        locations=[first_use, entry.definition_location],
                        severity='warning'
                    ))

            # Multiple definitions
            if entry.alternatives:
                issues.append(ConsistencyIssue(
                    acronym=acronym,
                    issue_type='multiple_definitions',
                    message=f"Acronym '{acronym}' has multiple definitions: '{entry.expansion}' and {entry.alternatives}",
                    locations=entry.usage_locations[:3],
                    severity='warning'
                ))

        return sorted(issues, key=lambda i: (
            0 if i.severity == 'error' else 1,
            i.acronym
        ))

    def get_acronym_table(self, text: str) -> List[Dict[str, Any]]:
        """
        Generate an acronym table for the document.

        Args:
            text: Document text

        Returns:
            List of dictionaries suitable for table display
        """
        results = self.extract_acronyms(text)

        table = []
        for acronym in sorted(results.keys()):
            entry = results[acronym]
            table.append({
                'acronym': acronym,
                'expansion': entry.expansion or '(undefined)',
                'status': entry.status.value,
                'usage_count': len(entry.usage_locations),
                'defined': entry.definition_location is not None,
                'source': entry.source
            })

        return table


# Convenience function
def get_acronym_extractor(custom_dictionary: Dict[str, str] = None) -> AcronymExtractor:
    """Get an AcronymExtractor instance."""
    return AcronymExtractor(custom_dictionary=custom_dictionary)


# Export
__all__ = [
    'AcronymExtractor',
    'AcronymEntry',
    'AcronymStatus',
    'ConsistencyIssue',
    'get_acronym_extractor'
]
