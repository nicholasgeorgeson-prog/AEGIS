"""
AEGIS - Compliance Checkers Module
Version: 3.4.0
Created: February 3, 2026

Provides domain-specific compliance validation for aerospace/defense documentation.
All checkers are 100% offline-capable with no external API dependencies.

Checkers included:
1. MILStd40051Checker - MIL-STD-40051 technical manual compliance
2. S1000DBasicChecker - S1000D/IETM basic structural validation
3. AS9100DocChecker - AS9100 documentation requirements

Usage:
    from compliance_checkers import get_compliance_checkers
    checkers = get_compliance_checkers()
"""

import re
import json
from typing import Dict, List, Any, Tuple, Set, Optional
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
# CHECKER 1: MIL-STD-40051 Compliance
# =============================================================================

class MILStd40051Checker(BaseChecker):
    """
    Validates compliance with MIL-STD-40051 for technical manual preparation.

    MIL-STD-40051 (Preparation of Digital Technical Information for Interactive
    Electronic Technical Manuals) provides requirements for:
    - Warning/Caution/Note formatting and placement
    - Procedural step structure
    - Active voice in warnings
    - Direct address of personnel
    """

    CHECKER_NAME = "MIL-STD-40051 Compliance"
    CHECKER_VERSION = "3.4.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """Load MIL-STD-40051 compliance rules."""
        data_path = Path(__file__).parent / 'data' / 'mil_std_40051_patterns.json'
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback: embedded rules based on MIL-STD-40051
        return {
            'warnings_cautions': {
                # Warning format requirements
                'warning_format': {
                    'pattern': r'\bWARNING[.!]?\s+(?![:\-\n])',
                    'message': "WARNING should be followed by colon, dash, or newline",
                    'severity': 'Medium',
                    'suggestion': "Format as 'WARNING:' or 'WARNING -' followed by the hazard"
                },
                'caution_format': {
                    'pattern': r'\bCAUTION[.!]?\s+(?![:\-\n])',
                    'message': "CAUTION should be followed by colon, dash, or newline",
                    'severity': 'Medium',
                    'suggestion': "Format as 'CAUTION:' or 'CAUTION -' followed by the hazard"
                },
                'note_format': {
                    'pattern': r'\bNOTE[.!]?\s+(?![:\-\n])',
                    'message': "NOTE should be followed by colon, dash, or newline",
                    'severity': 'Low',
                    'suggestion': "Format as 'NOTE:' or 'NOTE -' followed by the information"
                },
                # Warning content requirements
                'passive_in_warning': {
                    'pattern': r'\b(?:WARNING|CAUTION)\b[:\-]?\s*.{0,50}\b(?:injury|damage|death)\s+(?:may|can|could|will)\s+be\s+(?:caused|resulted?)\b',
                    'message': "Use active voice in warnings: state what causes the hazard",
                    'severity': 'High',
                    'suggestion': "Rewrite as 'X can cause injury' not 'injury can be caused by X'"
                },
                # Warning placement
                'warning_after_step': {
                    'pattern': r'^\s*\d+[.)]\s+.{10,100}(?:WARNING|CAUTION)\s*[:\-]',
                    'message': "Warnings/Cautions should precede the step, not be embedded in it",
                    'severity': 'High',
                    'suggestion': "Place WARNING/CAUTION on separate line before the procedural step"
                },
            },
            'procedural': {
                # Direct address
                'indirect_instruction': {
                    'pattern': r'\b(?:the\s+(?:operator|technician|maintainer|personnel))\s+(?:should|must|shall|will)\b',
                    'message': "Use direct address in procedures: 'You must...' not 'The operator must...'",
                    'severity': 'Medium',
                    'suggestion': "Rewrite using second person: 'You must...' or imperative: 'Do X'"
                },
                # Vague step references
                'vague_step_ref': {
                    'pattern': r'\b(?:do|perform|complete|execute)\s+(?:the\s+)?(?:above|previous|preceding)\s+(?:step|procedure|action)s?\b',
                    'message': "Use specific step numbers instead of 'the above step'",
                    'severity': 'Medium',
                    'suggestion': "Reference by step number: 'Repeat step 3' not 'repeat the above step'"
                },
                # Action verb at start
                'no_action_verb': {
                    'pattern': r'^\s*\d+[.)]\s+(?:The|This|It|A|An)\s',
                    'message': "Procedural steps should begin with an action verb",
                    'severity': 'Medium',
                    'suggestion': "Start with imperative verb: 'Remove...', 'Install...', 'Verify...'"
                },
            },
            'terminology': {
                # Shall/will usage in procedures
                'shall_in_procedure': {
                    'pattern': r'^\s*\d+[.)]\s+.{0,10}\bshall\b',
                    'message': "'Shall' is for requirements, use imperative mood for procedures",
                    'severity': 'Low',
                    'suggestion': "In procedures, use direct commands: 'Remove the cover' not 'The cover shall be removed'"
                },
                # Avoid certain words
                'avoid_easy': {
                    'pattern': r'\b(?:simply|just|easily|obviously|clearly)\s+\w+',
                    'message': "Avoid dismissive words in technical procedures",
                    'severity': 'Low',
                    'suggestion': "Remove 'simply/just/easily' - what's easy for experts may not be for all users"
                },
            },
            'structure': {
                # Tool/equipment listing
                'missing_tool_warning': {
                    'pattern': r'\busing\s+(?:a|the)\s+\w+(?:\s+\w+)?\s+tool\b',
                    'message': "Tools should be listed in equipment section, not introduced in procedures",
                    'severity': 'Low',
                    'suggestion': "List required tools/equipment before procedural steps begin"
                },
            }
        }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []
        full_text = kwargs.get('full_text', '')

        # Handle prohibited_patterns from JSON (list format)
        prohibited = self.rules.get('prohibited_patterns', {})
        if isinstance(prohibited, dict):
            patterns_list = prohibited.get('patterns', [])
        elif isinstance(prohibited, list):
            patterns_list = prohibited
        else:
            patterns_list = []

        for rule in patterns_list:
            if isinstance(rule, dict):
                pattern_str = rule.get('pattern')
                if not pattern_str:
                    continue

                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE)
                    for idx, text in paragraphs:
                        for match in pattern.finditer(text):
                            issues.append(self.create_issue(
                                severity=rule.get('severity', 'Medium'),
                                message=f"MIL-STD-40051: {rule.get('message', 'Compliance issue')}",
                                context=text[max(0, match.start()-20):match.end()+30],
                                paragraph_index=idx,
                                suggestion=rule.get('suggestion', 'See MIL-STD-40051 for requirements'),
                                rule_id=rule.get('rule_id', 'MIL40051'),
                                flagged_text=match.group()
                            ))
                except re.error:
                    continue

        # Handle embedded fallback rules (dict of dicts format)
        for category, rules in self.rules.items():
            if category in ('metadata', 'prohibited_patterns', 'warning_requirements',
                           'procedural_step_requirements', 'terminology_requirements',
                           'illustration_requirements', 'table_requirements',
                           'safety_criticality_levels'):
                continue  # Skip JSON-structured sections

            if not isinstance(rules, dict):
                continue

            for rule_id, rule in rules.items():
                if not isinstance(rule, dict):
                    continue

                pattern_str = rule.get('pattern')
                if not pattern_str:
                    continue

                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                    for idx, text in paragraphs:
                        for match in pattern.finditer(text):
                            issues.append(self.create_issue(
                                severity=rule.get('severity', 'Medium'),
                                message=f"MIL-STD-40051: {rule.get('message', 'Compliance issue')}",
                                context=text[max(0, match.start()-20):match.end()+30],
                                paragraph_index=idx,
                                suggestion=rule.get('suggestion', 'See MIL-STD-40051 for requirements'),
                                rule_id=f"MIL40051-{rule_id.upper()}",
                                flagged_text=match.group()
                            ))
                except re.error:
                    continue

        return issues[:25]  # Limit


# =============================================================================
# CHECKER 2: S1000D Basic Validation
# =============================================================================

class S1000DBasicChecker(BaseChecker):
    """
    Provides basic S1000D/IETM structural validation.

    S1000D is an international specification for technical publications using
    a common source database. This checker validates:
    - Data module code format
    - Warning/Caution structure
    - Procedural step formatting
    - Common structural issues
    """

    CHECKER_NAME = "S1000D Basic Validation"
    CHECKER_VERSION = "3.4.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        """Load S1000D basic validation rules."""
        data_path = Path(__file__).parent / 'data' / 's1000d_basic_rules.json'
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback: embedded rules based on S1000D
        return {
            'data_modules': {
                # DMC format hints
                'dmc_reference': {
                    'pattern': r'\bDMC[-:\s]+([A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+)',
                    'message': "Data Module Code detected - verify format per S1000D",
                    'severity': 'Info',
                    'suggestion': "DMC should follow: ModelIdentCode-SystemDiffCode-SystemCode-SubSystemCode..."
                },
                'invalid_dmc_chars': {
                    'pattern': r'\bDMC[-:\s]+[A-Z0-9]*[^A-Z0-9\-\s][A-Z0-9\-]*',
                    'message': "DMC contains invalid characters",
                    'severity': 'Medium',
                    'suggestion': "DMC should only contain uppercase letters, digits, and hyphens"
                },
            },
            'warnings_cautions': {
                # S1000D Warning structure
                'warning_structure': {
                    'pattern': r'\bWARNING\b(?!\s*[-:]?\s*\n?\s*[A-Z])',
                    'message': "S1000D warnings should be followed by warning text starting with capital letter",
                    'severity': 'Medium',
                    'suggestion': "Format: WARNING: [warning type if applicable] followed by warning text"
                },
                # Warning after step number
                'embedded_warning': {
                    'pattern': r'^\s*\d+\.\s+.{5,}\s+WARNING\b',
                    'message': "S1000D: Warnings must precede the step, not be embedded",
                    'severity': 'High',
                    'suggestion': "Place warning element before the procedural step element"
                },
            },
            'procedures': {
                # Step numbering style
                'non_standard_numbering': {
                    'pattern': r'^\s*Step\s+\d+[:.]\s',
                    'message': "S1000D uses structured numbering, not 'Step N' format",
                    'severity': 'Low',
                    'suggestion': "Use structured procedural steps per S1000D schema"
                },
                # Nested steps
                'flat_substeps': {
                    'pattern': r'^\s*\d+[a-z]\.\s+',
                    'message': "Substeps should use proper S1000D nesting structure",
                    'severity': 'Low',
                    'suggestion': "Use nested proceduralStep elements rather than flat numbering"
                },
            },
            'cross_references': {
                # Internal references
                'hotspot_reference': {
                    'pattern': r'\b(?:hotspot|callout)\s+(?:\d+|[A-Z])\b',
                    'message': "Hotspot/callout reference detected - verify ICN reference",
                    'severity': 'Info',
                    'suggestion': "Hotspot references should link to ICN (Illustration Control Number)"
                },
            },
            'content': {
                # Tables in procedures
                'table_in_procedure': {
                    'pattern': r'^\s*\d+[.)]\s+.{0,50}\bsee\s+(?:the\s+)?(?:following\s+)?table\b',
                    'message': "Tables referenced within steps should be properly linked",
                    'severity': 'Low',
                    'suggestion': "Use internalRef to link to table data module"
                },
            }
        }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        issues = []

        # Handle JSON format where rules may be in different sections
        for category, rules in self.rules.items():
            if category == 'metadata':
                continue

            # Handle list of rules (JSON format)
            if isinstance(rules, dict) and 'rules' in rules:
                rule_list = rules.get('rules', [])
                for rule in rule_list:
                    if isinstance(rule, dict) and 'pattern' in rule:
                        self._check_pattern(paragraphs, rule, issues, 'S1000D')
                continue

            # Handle dict of rules (fallback format)
            if not isinstance(rules, dict):
                continue

            for rule_id, rule in rules.items():
                if not isinstance(rule, dict):
                    continue

                pattern_str = rule.get('pattern')
                if not pattern_str:
                    continue

                try:
                    pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                    for idx, text in paragraphs:
                        for match in pattern.finditer(text):
                            issues.append(self.create_issue(
                                severity=rule.get('severity', 'Medium'),
                                message=f"S1000D: {rule.get('message', 'Validation issue')}",
                                context=match.group(0)[:80],
                                paragraph_index=idx,
                                suggestion=rule.get('suggestion', 'See S1000D specification'),
                                rule_id=f"S1000D-{rule_id.upper()}",
                                flagged_text=match.group()
                            ))
                except re.error:
                    continue

        return issues[:20]

    def _check_pattern(self, paragraphs, rule, issues, prefix):
        """Helper to check a single pattern rule."""
        pattern_str = rule.get('pattern')
        if not pattern_str:
            return

        try:
            pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
            for idx, text in paragraphs:
                for match in pattern.finditer(text):
                    issues.append(self.create_issue(
                        severity=rule.get('severity', 'Medium'),
                        message=f"{prefix}: {rule.get('message', rule.get('rule', 'Validation issue'))}",
                        context=match.group(0)[:80],
                        paragraph_index=idx,
                        suggestion=rule.get('suggestion', f'See {prefix} specification'),
                        rule_id=rule.get('id', f'{prefix}-RULE'),
                        flagged_text=match.group()
                    ))
        except re.error:
            pass


# =============================================================================
# CHECKER 3: AS9100 Documentation Requirements
# =============================================================================

class AS9100DocChecker(BaseChecker):
    """
    Validates AS9100 documentation requirements.

    AS9100 is the Quality Management System standard for aerospace. This checker
    validates documentation requirements including:
    - Document control elements (revision, approval, date)
    - Traceability markers
    - Required sections
    - Record retention language
    """

    CHECKER_NAME = "AS9100 Documentation Requirements"
    CHECKER_VERSION = "3.4.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.requirements = self._load_requirements()

    def _load_requirements(self) -> Dict:
        """Load AS9100 documentation requirements."""
        data_path = Path(__file__).parent / 'data' / 'as9100_doc_requirements.json'
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback: embedded requirements based on AS9100D
        return {
            'document_control': {
                'revision_marker': {
                    'search_terms': ['revision', 'rev.', 'rev:', 'version', 'issue'],
                    'required': True,
                    'severity': 'High',
                    'message': "AS9100 7.5.3: Document control requires revision identification",
                    'suggestion': "Include revision number/letter (e.g., 'Revision 3' or 'Rev. C')"
                },
                'approval_marker': {
                    'search_terms': ['approved by', 'approval', 'authorized by', 'approved:'],
                    'required': True,
                    'severity': 'High',
                    'message': "AS9100 7.5.3: Documents require approval identification",
                    'suggestion': "Include approval authority (e.g., 'Approved by: [Name/Title]')"
                },
                'effective_date': {
                    'search_terms': ['effective date', 'issue date', 'date:', 'dated:'],
                    'required': True,
                    'severity': 'High',
                    'message': "AS9100 7.5.3: Documents require effective/issue date",
                    'suggestion': "Include date of issue or effective date"
                },
                'document_number': {
                    'search_terms': ['document number', 'doc no', 'document id', 'doc #'],
                    'required': False,
                    'severity': 'Medium',
                    'message': "AS9100: Consider adding unique document identifier",
                    'suggestion': "Include document number for configuration management"
                },
            },
            'traceability': {
                'requirement_refs': {
                    'pattern': r'\b(?:per|ref|reference|see)\s+(?:requirement|req\.?|RQ)[-\s]?\d+',
                    'severity': 'Info',
                    'message': "Requirement reference detected - verify traceability",
                    'suggestion': "Ensure requirement references are traceable to source"
                },
                'change_tracking': {
                    'search_terms': ['change history', 'revision history', 'change log', 'revision log'],
                    'required': False,
                    'severity': 'Medium',
                    'message': "AS9100 7.5.3.2: Consider including change history",
                    'suggestion': "Add revision history table tracking changes and approvals"
                },
            },
            'configuration': {
                'baseline_ref': {
                    'search_terms': ['baseline', 'configuration', 'config. item', 'ci '],
                    'required': False,
                    'severity': 'Info',
                    'message': "Configuration item reference detected",
                    'suggestion': "Verify configuration management per AS9100 8.1.2"
                },
            },
            'records': {
                'retention_statement': {
                    'search_terms': ['retain', 'retention', 'record keeping', 'preserve', 'archived'],
                    'required': False,
                    'severity': 'Low',
                    'message': "AS9100 7.5.3.1: Consider defining retention requirements",
                    'suggestion': "Specify record retention period if applicable"
                },
                'quality_records': {
                    'pattern': r'\bquality\s+record',
                    'severity': 'Info',
                    'message': "Quality record reference - verify retention per AS9100 7.5.3.1",
                    'suggestion': "Quality records must be retained per documented retention periods"
                },
            },
            'risk': {
                'risk_reference': {
                    'pattern': r'\brisk\s+(?:assessment|analysis|mitigation|management)',
                    'severity': 'Info',
                    'message': "Risk reference detected - verify per AS9100 6.1",
                    'suggestion': "Risk documentation should address actions to address risks per AS9100 6.1"
                },
            }
        }

    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []

        full_text = kwargs.get('full_text', '')
        if not full_text:
            full_text = ' '.join(text for _, text in paragraphs)

        full_text_lower = full_text.lower()
        issues = []

        # Check required elements
        for category, requirements in self.requirements.items():
            for req_id, req in requirements.items():
                # Search term-based checks
                if 'search_terms' in req:
                    found = any(term.lower() in full_text_lower for term in req['search_terms'])

                    if req.get('required') and not found:
                        issues.append(self.create_issue(
                            severity=req.get('severity', 'Medium'),
                            message=req.get('message', 'AS9100 requirement not met'),
                            context="Document-level check",
                            paragraph_index=0,
                            suggestion=req.get('suggestion', 'See AS9100D requirements'),
                            rule_id=f"AS9100-{req_id.upper()}"
                        ))

                # Pattern-based checks
                if 'pattern' in req:
                    pattern = re.compile(req['pattern'], re.IGNORECASE)
                    for idx, text in paragraphs:
                        for match in pattern.finditer(text):
                            issues.append(self.create_issue(
                                severity=req.get('severity', 'Info'),
                                message=req.get('message', 'AS9100 reference detected'),
                                context=match.group(0),
                                paragraph_index=idx,
                                suggestion=req.get('suggestion', 'Verify AS9100 compliance'),
                                rule_id=f"AS9100-{req_id.upper()}"
                            ))

        return issues


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_compliance_checkers() -> Dict[str, BaseChecker]:
    """
    Returns a dictionary of all compliance checker instances.

    Used by core.py to register checkers in bulk.
    """
    return {
        'mil_std_40051': MILStd40051Checker(),
        's1000d_basic': S1000DBasicChecker(),
        'as9100_doc': AS9100DocChecker(),
    }


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == '__main__':
    # Demo text with intentional issues
    demo_text = """
    Document: System Maintenance Procedures

    WARNING Failure to follow these procedures may result in injury.

    1. The technician should verify power is disconnected.
    2. Simply remove the access panel using a Phillips screwdriver.
    3. WARNING: High voltage present. Check voltage levels.

    See DMC-ACME-A-00-00-00-00A-040A-A for additional information.

    Step 5: The operator must replace the filter element.

    This procedure should be performed per the above steps.

    Quality records shall be retained as specified.
    Risk assessment must be documented per company procedures.
    """

    paragraphs = [(i, p.strip()) for i, p in enumerate(demo_text.split('\n\n')) if p.strip()]

    print("=== Compliance Checkers Demo ===\n")

    checkers = get_compliance_checkers()

    for name, checker in checkers.items():
        print(f"\n--- {checker.CHECKER_NAME} ---")
        issues = checker.check(paragraphs, full_text=demo_text)

        if issues:
            for issue in issues[:5]:
                print(f"  [{issue.get('severity', 'Info')}] {issue.get('message', '')}")
                if issue.get('suggestion'):
                    print(f"    Suggestion: {issue.get('suggestion', '')[:70]}...")
        else:
            print("  No issues found")

    print(f"\n\nTotal checkers: {len(checkers)}")
