#!/usr/bin/env python3
"""
Acronym Checker v4.0.0 (Complete Rewrite)
=========================================
Detects undefined acronyms in documents.

v4.0.0 COMPLETE REWRITE:
- FIXED: Acronyms in acronym section were being flagged
- NEW: Better acronym section detection using paragraph clustering
- NEW: Don't flag ANY acronym that appears in the acronym section
- NEW: Recognizes acronym section by density of CAPS patterns
- NEW: Better document number exclusion

The key insight: If a paragraph contains "ACRONYM - Description" or 
"ACRONYM: Description" patterns, and there are multiple such paragraphs
in a cluster, that's an acronym list section.

Logic:
1. Find acronym section by looking for clusters of definition-style paragraphs
2. Extract all defined acronyms from that section
3. Also extract from inline definitions like "Full Name (ACRONYM)"
4. Flag acronyms that are used BUT not defined AND not in skip lists
"""

import re
import zipfile
from typing import List, Dict, Tuple, Set, Optional, Any
from dataclasses import dataclass
import os
from datetime import datetime

# Import from core contracts
try:
    from base_checker import BaseChecker, ReviewIssue
except ImportError:
    try:
        from .base_checker import BaseChecker, ReviewIssue
    except ImportError:
        # Minimal fallback
        class BaseChecker:
            CHECKER_NAME = "Unknown"
            def __init__(self, enabled=True):
                self.enabled = enabled
                self._errors = []
            def create_issue(self, **kwargs):
                kwargs['category'] = getattr(self, 'CHECKER_NAME', 'Unknown')
                return kwargs
            def clear_errors(self):
                self._errors = []
        class ReviewIssue:
            pass

# Import version from centralized config
try:
    from config_logging import VERSION, get_logger
    __version__ = VERSION
    _structured_logger = get_logger('acronym_checker')
except ImportError:
    __version__ = "2.5.0"
    _structured_logger = None

# v4.6.0: Load external acronym database
_EXTERNAL_ACRONYMS = None

def _load_external_acronym_database() -> set:
    """Load acronyms from the universal_acronyms.json database.

    This provides 1700+ well-known acronyms from:
    - UK Ministry of Justice
    - DOD Dictionary of Military Terms
    - FDA Acronyms and Abbreviations
    - IEEE/ISO/ANSI Standards
    - Common Technical Writing
    """
    global _EXTERNAL_ACRONYMS

    if _EXTERNAL_ACRONYMS is not None:
        return _EXTERNAL_ACRONYMS

    _EXTERNAL_ACRONYMS = set()

    try:
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'universal_acronyms.json')
        if os.path.exists(db_path):
            import json
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _EXTERNAL_ACRONYMS = set(data.get('acronyms', {}).keys())
                if _structured_logger:
                    _structured_logger.info(f"Loaded {len(_EXTERNAL_ACRONYMS)} external acronyms from database")
    except Exception as e:
        if _structured_logger:
            _structured_logger.warning(f"Failed to load external acronym database: {e}")

    return _EXTERNAL_ACRONYMS

# Debug settings - now controlled by logger level
DEBUG = False  # Disabled by default in production


def _log(msg: str, level: str = 'debug'):
    """Debug logging using structured logger."""
    if _structured_logger:
        getattr(_structured_logger, level)(msg)
    elif DEBUG:
        print(f"[AcronymChecker] {msg}")


@dataclass
class AcronymInfo:
    """Track information about an acronym."""
    acronym: str
    usage_count: int = 0
    first_para_idx: int = -1
    is_defined: bool = False
    definition_source: str = ""


class AcronymChecker(BaseChecker):
    """
    Detects undefined acronyms in documents.
    
    v2.9.3 B12: Added more title words to COMMON_CAPS_SKIP to reduce false positives
    """
    
    CHECKER_NAME = "Acronyms"
    CHECKER_VERSION = "4.7.0"  # v4.7.0: Added NEVER_FLAG list for truly universal terms

    # v4.7.0: Truly universal acronyms that are NEVER flagged, even in strict mode
    # These are so universally understood that requiring definition is pedantic
    NEVER_FLAG = frozenset({
        # File formats - everyone knows these
        'PDF', 'HTML', 'XML', 'JSON', 'CSV', 'TXT', 'DOC', 'DOCX', 'XLS', 'XLSX',
        'JPG', 'JPEG', 'PNG', 'GIF', 'BMP', 'TIFF', 'SVG', 'MP3', 'MP4', 'AVI',
        'ZIP', 'RAR', 'TAR', 'GZ', 'ISO',
        # Basic computing - universally understood
        'PC', 'CPU', 'RAM', 'USB', 'URL', 'HTTP', 'HTTPS', 'WWW',
        # Common abbreviations that aren't really acronyms
        'ID', 'OK', 'VS', 'AM', 'PM', 'AC', 'DC', 'TV',
        # Standard measurements
        'PSI', 'RPM', 'MPH', 'KPH', 'HP',
        # Standard placeholders
        'TBD', 'TBA', 'TBC', 'NA', 'N/A',
    })

    # Universal skip list - skipped in non-strict mode
    UNIVERSAL_SKIP = frozenset({
        # Common abbreviations
        'ID', 'OK', 'PC', 'TV', 'AM', 'PM', 'AC', 'DC', 'VS', 'NA', 'TBD', 'TBR', 'TBC',
        # Countries/regions
        'US', 'USA', 'UK', 'EU', 'UN',
        # US State abbreviations
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC', 'PR', 'VI', 'GU', 'AS',
        # Business titles
        'CEO', 'CFO', 'CTO', 'COO', 'CIO', 'VP', 'SVP', 'EVP',
        'HR', 'IT', 'PR', 'QA', 'QC', 'RD', 'LLC', 'INC', 'CORP',
        # Tech
        'PDF', 'HTML', 'XML', 'JSON', 'API', 'URL', 'HTTP', 'HTTPS',
        'CPU', 'GPU', 'RAM', 'ROM', 'SSD', 'HDD', 'USB', 'LED', 'LCD',
        'IP', 'TCP', 'UDP', 'DNS', 'VPN', 'LAN', 'WAN', 'WIFI',
        # Government agencies
        'NASA', 'FBI', 'CIA', 'NSA', 'IRS', 'FDA', 'EPA', 'DOD', 'DOE',
        'OSHA', 'FEMA', 'SEC', 'FCC', 'FAA', 'DOT',
        # v4.5.2: Additional well-known regulatory/safety organizations
        'NIOSH', 'CDC', 'NIH', 'DHHS', 'HHS', 'DHS', 'USDA', 'DOL', 'EEOC',
        'NRC', 'DOJ', 'ATF', 'DEA', 'ICE', 'CBP', 'TSA', 'USCG', 'USACE',
        # Education
        'MBA', 'PhD', 'MD', 'JD', 'BA', 'BS', 'MA', 'MS',
        # Standards bodies and organizations
        'ISO', 'IEEE', 'ANSI', 'NIST', 'MIL', 'STD',
        'SAE', 'ASTM', 'ASME', 'AIAA', 'AIA', 'NAS', 'AMS', 'ARP',
        'IPC', 'JEDEC', 'EIA', 'TIA', 'GEIA', 'GIDEP', 'NAVSO',
        # Common document terms
        'REV', 'REVISION', 'VER', 'VERSION', 'ED', 'EDITION',
        # Business terms
        'NDA', 'SLA', 'KPI', 'ROI', 'PO', 'RFP', 'RFI', 'RFQ', 'SOW', 'POC',
        # v4.5.2: Laboratory/Safety acronyms (universally understood)
        'PPE', 'SDS', 'MSDS', 'GHS', 'HMIS', 'NFPA', 'CAS', 'DOT', 'UN',
        'EHS', 'HSE', 'OHS', 'SOP', 'LOTO', 'JSA', 'JHA', 'PHA', 'HAZOP',
        'PI', 'RA', 'TA', 'GA', 'PA',  # Common academic/research titles
        # v4.5.2: Engineering/Process acronyms
        'PID', 'PLC', 'HMI', 'SCADA', 'DCS', 'RTU', 'I/O', 'PFD', 'BFD',
        'PHA', 'FMEA', 'FMECA', 'FTA', 'ETA', 'LOPA', 'SIL', 'SIS', 'SIF',
        'MOC', 'PSM', 'RMP', 'PSI', 'PSSR', 'PSR', 'PHR', 'RCA', 'RCFA',
        # v4.5.2: Well-known places/entities
        'JFK', 'LAX', 'NYC', 'LA', 'SF', 'DC', 'GPO', 'GAO', 'CBO', 'OMB',
        # Defense/aerospace companies
        'NG', 'NGC', 'NORTHROP', 'GRUMMAN',
        'LM', 'LOCKHEED', 'MARTIN',
        'BA', 'BOEING',
        'RTX', 'RAYTHEON',
        'GD', 'GENERAL', 'DYNAMICS',
        # Document number prefixes (common in aerospace/defense)
        'N0', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9',
        'F0', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9',
        'NO',  # Common document number prefix
    })
    
    # Common words that appear in caps but aren't acronyms
    # v2.9.3 B12: Added EXAMPLES, CHECKLIST and other common title words
    # v4.5.1: Added section reference codes, template markers, and domain-specific words
    COMMON_CAPS_SKIP = frozenset({
        # Section reference codes (A1, B2, C3, etc.) - common in SOPs
        'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9',
        'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9',
        'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9',
        'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9',
        'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9',
        'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9',
        'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9',
        'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9',
        # Template/instruction markers (often in brackets)
        'GREEN', 'RED', 'YELLOW', 'BLUE', 'ORANGE', 'TEXT', 'INSERT', 'ENTER',
        'PLACEHOLDER', 'BLANK', 'FILL', 'REPLACE', 'DELETE', 'REMOVE', 'ADD',
        'YOUR', 'HERE', 'NAME', 'TITLE', 'DATE', 'NUMBER', 'SPECIFY', 'SELECT',
        # Domain-specific words that aren't acronyms - Laboratory/Science
        'ROBOTICS', 'ROBOTS', 'ROBOT', 'LASER', 'LASERS', 'DRONES', 'DRONE',
        'SENSORS', 'SENSOR', 'ACTUATOR', 'ACTUATORS', 'MOTORS', 'MOTOR',
        'MACHINING', 'WELDING', 'SOLDERING', 'PRINTING', 'MILLING', 'CUTTING',
        # Computing/Tech words
        'REST', 'RESTFUL', 'SOAP', 'AJAX', 'JSON', 'YAML', 'CRUD', 'ASYNC',
        'SYNC', 'BATCH', 'QUEUE', 'STACK', 'HEAP', 'CACHE', 'BUFFER',
        # Medical/Health terms
        'COVID', 'SARS', 'MERS', 'FLU', 'VACCINE', 'VACCINES', 'VIRUS', 'VIRAL',
        'PANDEMIC', 'EPIDEMIC', 'ISOLATION', 'QUARANTINE',
        # v4.5.2: Common words that appear in ALL CAPS instructions/headers
        'HARD', 'SOFT', 'ELECTRONIC', 'DIGITAL', 'PHYSICAL', 'COPY', 'COPIES',
        'MUST', 'SHALL', 'SHOULD', 'WILL', 'MAY', 'CAN', 'COULD', 'WOULD',
        'READILY', 'EASILY', 'QUICKLY', 'IMMEDIATELY', 'ALWAYS', 'NEVER',
        'AVAILABLE', 'UNAVAILABLE', 'ACCESSIBLE', 'INACCESSIBLE',
        'LAB', 'LABS', 'LABORATORY', 'LABORATORIES', 'OFFICE', 'OFFICES',
        'PERSONNEL', 'STAFF', 'EMPLOYEE', 'EMPLOYEES', 'WORKER', 'WORKERS',
        'INVESTIGATOR', 'INVESTIGATORS', 'RESEARCHER', 'RESEARCHERS',
        'APPROVAL', 'APPROVALS', 'SIGNATURE', 'SIGNATURES', 'SIGN', 'SIGNED',
        'REQUIRED', 'OPTIONAL', 'MANDATORY', 'RECOMMENDED', 'SUGGESTED',
        'TRAINING', 'TRAINED', 'CERTIFIED', 'QUALIFIED', 'AUTHORIZED',
        'COMPLETE', 'COMPLETED', 'INCOMPLETE', 'PENDING', 'SUBMITTED',
        'ANNUAL', 'MONTHLY', 'WEEKLY', 'DAILY', 'QUARTERLY', 'BIANNUAL',
        'REGULAR', 'PERIODIC', 'ROUTINE', 'SCHEDULED', 'UNSCHEDULED',
        # Document labels (including common PDF kerning artifacts like "OTE" from "N OTE")
        'NOTE', 'NOTES', 'WARNING', 'CAUTION', 'IMPORTANT', 'TIP', 'EXAMPLE',
        'OTE', 'ARNING', 'AUTION',  # PDF kerning artifacts from NOTE, WARNING, CAUTION
        'ATTACHMENT', 'APPENDIX', 'SECTION', 'CHAPTER', 'TABLE', 'FIGURE',
        'PART', 'PAGE', 'DOCUMENT', 'DOCUMENTS', 'TITLE', 'INDEX', 'CONTENTS',
        'SUMMARY', 'OVERVIEW', 'INTRODUCTION', 'CONCLUSION', 'REFERENCE',
        'REFERENCES', 'CONTINUED', 'CONT', 'TRADE', 'STUDY',
        # v2.9.3 B12: Common section title words causing false positives
        'EXAMPLES', 'CHECKLIST', 'CHECKLISTS', 'GLOSSARY', 'PREFACE', 'ABSTRACT',
        'RECOMMENDATIONS', 'BACKGROUND', 'OBJECTIVES', 'PROCEDURES', 'DEFINITIONS',
        'ABBREVIATIONS', 'RELATED', 'ADDITIONAL', 'HISTORY', 'APPROVAL',
        'DISTRIBUTION', 'ATTENTION', 'EXHIBIT', 'ANNEX', 'ENCLOSURE', 'ENCLOSURES',
        # Status words
        'DRAFT', 'FINAL', 'APPROVED', 'REJECTED', 'PENDING', 'OPEN', 'CLOSED',
        'YES', 'NO', 'TOTAL', 'SUBTOTAL', 'NEW', 'OLD', 'END', 'USE', 'KEY',
        'ACTIVE', 'INACTIVE', 'CURRENT', 'OBSOLETE', 'ARCHIVED',
        # Common headers
        'SUBJECT', 'DATE', 'NAME', 'STATUS', 'ACTION', 'ITEM', 'OWNER',
        'DESCRIPTION', 'PURPOSE', 'SCOPE', 'PROCESS', 'PROCEDURE',
        'REQUIREMENTS', 'REQUIREMENT', 'REVISION', 'VERSION', 'CATEGORY',
        # Short common words
        'AND', 'THE', 'FOR', 'FROM', 'WITH', 'THIS', 'THAT', 'ALL', 'ANY',
        'NOT', 'BUT', 'ARE', 'WAS', 'HAS', 'ONLY', 'ALSO', 'EACH', 'EVERY',
        'OTHER', 'OTHERS', 'BOTH', 'EITHER', 'NEITHER', 'NONE', 'SOME',
        # Disclaimer/header words (common in corporate docs)
        'AUTHORIZED', 'PUBLISHED', 'ONLINE', 'VERIFY', 'VERIFIED', 'COPY',
        'AGAINST', 'BEFORE', 'AFTER', 'PRIOR', 'FOLLOWING',
        'CONFIDENTIAL', 'PROPRIETARY', 'RESTRICTED', 'INTERNAL', 'EXTERNAL',
        'PUBLIC', 'PRIVATE', 'SENSITIVE', 'CLASSIFIED', 'UNCLASSIFIED',
        # Business/document words that appear in headers/titles
        'EFFECTIVE', 'REVIEW', 'FACILITIES', 'PLANNING', 'TYPE', 
        'GUIDANCE', 'CAPTURE', 'VALIDATION', 'MANAGEMENT', 'PROGRAM',
        'PROJECT', 'SYSTEM', 'SYSTEMS', 'ENGINEERING', 'TECHNICAL',
        'ACQUISITION', 'PROCUREMENT', 'CONTRACT', 'PROPOSAL', 'BUDGET',
        'SCHEDULE', 'RISK', 'ISSUE', 'ISSUES', 'CHANGE', 'CHANGES',
        'CONTROL', 'CONFIGURATION', 'DATA', 'INFORMATION', 'REPORT',
        # Additional variations and plurals (v2.8.7 patch for title false positives)
        'REVIEWS', 'FACILITY', 'PROGRAMS', 'PROJECTS', 'CONTRACTS', 'PROPOSALS',
        'SCHEDULES', 'RISKS', 'BUDGETS', 'CONTROLS', 'REPORTS', 'TYPES',
        'EFFECTIVENESS', 'REVIEWER', 'REVIEWERS', 'PLANNED', 'PLANNER',
        'FACILITY', 'GUIDELINES', 'GUIDELINE', 'MANAGES', 'MANAGED', 'MANAGING',
        'REPORTS', 'PLAN', 'PLANS', 'POLICY', 'POLICIES', 'STANDARD',
        'STANDARDS', 'SPECIFICATION', 'SPECIFICATIONS', 'PERFORMANCE',
        'OBJECTIVE', 'OBJECTIVES', 'GOAL', 'GOALS', 'MISSION', 'VISION',
        'STRATEGY', 'STRATEGIC', 'TACTICAL', 'OPERATIONAL', 'EXECUTIVE',
        'DELIVERABLE', 'DELIVERABLES', 'MILESTONE', 'MILESTONES',
        'BASELINE', 'PHASE', 'PHASES', 'TASK', 'TASKS', 'WORK',
        'COST', 'COSTS', 'PRICE', 'PRICING', 'ESTIMATE', 'ESTIMATES',
        'TERM', 'TERMS', 'CONDITION', 'CONDITIONS', 'CLAUSE', 'CLAUSES',
        'METHOD', 'METHODS', 'APPROACH', 'SOLUTION', 'SOLUTIONS',
        'INPUT', 'INPUTS', 'OUTPUT', 'OUTPUTS', 'RESULT', 'RESULTS',
        'METRIC', 'METRICS', 'MEASURE', 'MEASURES', 'CRITERIA',
        'FUNCTION', 'FUNCTIONS', 'FEATURE', 'FEATURES', 'CAPABILITY',
        'INTERFACE', 'INTERFACES', 'MODULE', 'MODULES', 'COMPONENT',
        'PRIORITY', 'IMPACT', 'ANALYSIS', 'ASSESSMENT', 'EVALUATION',
        # Additional common corporate words
        'APPLICABLE', 'APPLY', 'APPLIES', 'RESPONSIBLE', 'RESPONSIBILITY',
        'AUTHORITY', 'APPROVAL', 'COMPLIANCE', 'COMPLIANT', 'ACCORDANCE',
        'DEFINITION', 'DEFINITIONS', 'ACRONYM', 'ACRONYMS', 'ABBREVIATION',
        'GENERAL', 'SPECIFIC', 'DETAIL', 'DETAILS', 'LEVEL', 'LEVELS',
        # Added - corporate and organizational terms
        'CORPORATE', 'CORPORATION', 'COMPANY', 'ENTERPRISE', 'BUSINESS',
        'DIVISION', 'DEPARTMENT', 'OFFICE', 'CENTER', 'BRANCH', 'UNIT',
        'GROUP', 'TEAM', 'STAFF', 'PERSONNEL', 'EMPLOYEE', 'EMPLOYEES',
        'DIRECTOR', 'MANAGER', 'LEAD', 'CHIEF', 'HEAD', 'SENIOR', 'JUNIOR',
        'PRINCIPAL', 'ASSOCIATE', 'ASSISTANT', 'DEPUTY', 'ACTING',
        # Aerospace/Defense/Engineering common terms (v2.8.5 patch)
        'TAILORING', 'GUIDELINES', 'TESTABILITY', 'RANGES', 'TESTING',
        'HARDWARE', 'SOFTWARE', 'FIRMWARE', 'VERIFICATION', 'VALIDATION',
        'QUALIFICATION', 'CERTIFICATION', 'PRODUCTION', 'MANUFACTURING',
        'ASSEMBLY', 'INTEGRATION', 'INSPECTION', 'QUALITY', 'ASSURANCE',
        'RELIABILITY', 'MAINTAINABILITY', 'AVAILABILITY', 'SUPPORTABILITY',
        'SUSTAINMENT', 'LOGISTICS', 'DEPOT', 'FIELD', 'SUPPORT',
        'DESIGN', 'DEVELOPMENT', 'PROTOTYPE', 'DEMONSTRATION', 'TRANSITION',
        'DEPLOYMENT', 'OPERATIONS', 'MAINTENANCE', 'DISPOSAL', 'DECOMMISSION',
        'REVIEW', 'AUDIT', 'SURVEILLANCE', 'MONITORING', 'TRACKING',
        'INTERFACE', 'INTEGRATION', 'INTEROPERABILITY', 'COMPATIBILITY',
        'TRACEABILITY', 'ALLOCATION', 'FLOWDOWN', 'DECOMPOSITION',
        'ANALYSIS', 'SYNTHESIS', 'MODELING', 'SIMULATION', 'EMULATION',
        'ENVIRONMENT', 'ENVIRONMENTAL', 'THERMAL', 'STRUCTURAL', 'ELECTRICAL',
        'MECHANICAL', 'ELECTROMAGNETIC', 'OPTICAL', 'ACOUSTIC', 'VIBRATION',
        'SHOCK', 'ACCELERATION', 'PRESSURE', 'TEMPERATURE', 'HUMIDITY',
        'ALTITUDE', 'SPEED', 'VELOCITY', 'RANGE', 'AZIMUTH', 'ELEVATION',
        'FREQUENCY', 'BANDWIDTH', 'POWER', 'VOLTAGE', 'CURRENT', 'RESISTANCE',
        'MEMORY', 'STORAGE', 'PROCESSING', 'THROUGHPUT', 'LATENCY',
        'SAFETY', 'HAZARD', 'MISHAP', 'ACCIDENT', 'INCIDENT', 'FAILURE',
        'FAULT', 'ERROR', 'DEFECT', 'ANOMALY', 'DISCREPANCY', 'DEVIATION',
        'WAIVER', 'DEVIATION', 'EXCEPTION', 'VARIANCE', 'MODIFICATION',
        'CONFIGURATION', 'BASELINE', 'VERSION', 'REVISION', 'RELEASE',
        'DOCUMENT', 'DRAWING', 'SPECIFICATION', 'PROCEDURE', 'INSTRUCTION',
        'MANUAL', 'HANDBOOK', 'GUIDE', 'STANDARD', 'POLICY', 'DIRECTIVE',
        'REGULATION', 'STATUTE', 'LAW', 'CODE', 'RULE', 'REQUIREMENT',
        'STATEMENT', 'OBJECTIVE', 'THRESHOLD', 'GOAL', 'TARGET', 'METRIC',
        'MEASURE', 'INDICATOR', 'CRITERIA', 'CRITERION', 'PARAMETER',
        'ATTRIBUTE', 'CHARACTERISTIC', 'PROPERTY', 'FEATURE', 'FUNCTION',
        'CAPABILITY', 'CAPACITY', 'PERFORMANCE', 'EFFECTIVENESS', 'EFFICIENCY',
        'SUITABILITY', 'SURVIVABILITY', 'VULNERABILITY', 'LETHALITY',
        'ACCURACY', 'PRECISION', 'RESOLUTION', 'SENSITIVITY', 'SELECTIVITY',
        'PROBABILITY', 'CONFIDENCE', 'UNCERTAINTY', 'TOLERANCE', 'MARGIN',
        'BUDGET', 'ALLOCATION', 'RESERVE', 'CONTINGENCY', 'OVERHEAD',
        'MATURITY', 'READINESS', 'AVAILABILITY', 'OPERABILITY', 'USABILITY',
        # v2.9.1 Batch 7 A6: Military branch proper nouns (not acronyms)
        'MARINE', 'MARINES', 'CORPS', 'ARMY', 'NAVY', 'FORCE', 'GUARD', 'COAST',
        'NATIONAL', 'RESERVE', 'RESERVES', 'AIR', 'SPACE', 'SPECIAL', 'FORCES',
        # v2.9.1 Batch 7 A7: Document ID prefixes
        'C0', 'D0', 'Q0', 'A0', 'B0', 'E0', 'P0', 'R0', 'S0', 'T0',
        # v3.0.92: Common words appearing in document titles/headers causing false positives
        'OMNIBUS', 'SERVICES', 'SERVICE', 'APPLIED', 'TECHNOLOGY', 'TECHNOLOGIES',
        'DIRECTORATE', 'DIRECTORATES', 'MEASUREMENT', 'MEASUREMENTS',
        'STATEMENTS', 'STATEMENT', 'PRELIMINARY', 'MAJOR', 'SMALL', 'LARGE',
        'CENTER', 'CENTERS', 'OFFICE', 'OFFICES', 'FLIGHT', 'FLIGHTS',
        'ATTACHMENT', 'ATTACHMENTS', 'DATED', 'GODDARD', 'MULTIDISCIPLINE',
        'ENGINEERING', 'ENGINEERS', 'HANDBOOK', 'HANDBOOK', 'INTRODUCTION',
        'CONTRACTOR', 'CONTRACTORS', 'GOVERNMENT', 'FEDERAL', 'AGENCY',
        'ACTIVITIES', 'ACTIVITY', 'SERVICES', 'SUPPORT', 'SUPPORTS',
        'RESEARCH', 'DEVELOPMENT', 'ADMINISTRATION', 'ADMINISTRATIVE',
        'TECHNICAL', 'SPECIFICATIONS', 'SPECIFICATION', 'DOCUMENTATION',
        'IMPLEMENTATION', 'IMPLEMENTATIONS', 'FORMULATION', 'FABRICATION',
        'ASSEMBLY', 'TESTING', 'VERIFICATION', 'VALIDATION', 'INTEGRATION',
        'OPERATIONS', 'OPERATION', 'MAINTENANCE', 'SUSTAINING', 'MISSION',
        'MISSIONS', 'FUNCTION', 'FUNCTIONS', 'TASKS', 'TASK', 'SCOPE',
        'INSTRUMENTS', 'INSTRUMENT', 'SPACECRAFT', 'SATELLITE', 'SATELLITES',
        'PROPULSION', 'GUIDANCE', 'NAVIGATION', 'CONTROL', 'CONTROLS',
        'ANALYSES', 'ANALYTICAL', 'SUBSYSTEM', 'SUBSYSTEMS', 'SYSTEMS',
        'RESPONSIBILITIES', 'RESPONSIBILITY', 'PERFORMANCE', 'DELIVERABLES',
        'REQUIREMENTS', 'SPECIFICATION', 'APPLICABLE', 'DOCUMENTS',
        # Common short words that appear in all caps in titles
        'OF', 'FOR', 'AND', 'THE', 'TO', 'IN', 'ON', 'AT', 'BY', 'WITH',
        'AN', 'AS', 'OR', 'IS', 'BE', 'IT', 'IF', 'SO', 'UP', 'NO',
        # v3.0.105: BUG-003 FIX - REMOVED government/organization acronyms from here.
        # These ARE real acronyms and should be handled by the strict/permissive mode logic
        # in UNIVERSAL_SKIP, not unconditionally skipped here.
        # v3.0.93: Additional common words that appear in ALL CAPS in document titles/headers
        'ARCHITECTURE', 'ILLUSTRATING', 'ORGANIZATION', 'ORGANIZATIONS',
        'INSTRUCTIONS', 'INSTRUCTION', 'OBLIGATIONS', 'OBLIGATION',
        'FOREWORD', 'PREFACE', 'ABSTRACT', 'SUMMARY', 'APPENDIX', 'APPENDICES',
        'FORMAT', 'FORMATS', 'FORMATTING', 'MAIN', 'BLANK', 'NOTICE', 'NOTICES',
        'CHAPTER', 'CHAPTERS', 'SECTION', 'SECTIONS', 'PART', 'PARTS',
        'INTRODUCTION', 'CONCLUSION', 'CONCLUSIONS', 'DISCUSSION', 'RESULTS',
        'METHODOLOGY', 'METHODS', 'APPROACH', 'APPROACHES', 'PROCEDURE', 'PROCEDURES',
        'BACKGROUND', 'OVERVIEW', 'PURPOSE', 'OBJECTIVES', 'OBJECTIVE',
        'REFERENCE', 'REFERENCES', 'BIBLIOGRAPHY', 'GLOSSARY', 'INDEX',
        'FIGURE', 'FIGURES', 'TABLE', 'TABLES', 'EXHIBIT', 'EXHIBITS',
        'ATTACHMENT', 'ATTACHMENTS', 'ENCLOSURE', 'ENCLOSURES',
        'DRAFT', 'FINAL', 'REVISION', 'REVISIONS', 'VERSION', 'RELEASE',
        'APPROVED', 'PENDING', 'REVIEW', 'REVIEWS', 'COMMENT', 'COMMENTS',
        'NOTE', 'NOTES', 'WARNING', 'WARNINGS', 'CAUTION', 'CAUTIONS',
        # Government/agency common terms
        'FEDERAL', 'STATE', 'LOCAL', 'NATIONAL', 'REGIONAL', 'INTERNATIONAL',
        'DEPARTMENT', 'AGENCY', 'OFFICE', 'BUREAU', 'DIVISION', 'BRANCH',
        'PROGRAM', 'PROGRAMS', 'PROJECT', 'PROJECTS', 'INITIATIVE', 'INITIATIVES',
        'POLICY', 'POLICIES', 'STANDARD', 'STANDARDS', 'GUIDELINE', 'GUIDELINES',
        'REGULATION', 'REGULATIONS', 'COMPLIANCE', 'COMPLIANT',
        # Transportation/ITS terms
        'HIGHWAY', 'TRANSIT', 'TRANSPORTATION', 'TRAFFIC', 'VEHICLE', 'VEHICLES',
        'CORRIDOR', 'CORRIDORS', 'INFRASTRUCTURE', 'MOBILITY',
        # Common project document terms
        'PLAN', 'PLANS', 'REPORT', 'REPORTS', 'DOCUMENT', 'DOCUMENTATION',
        'SPECIFICATION', 'SPECIFICATIONS', 'MANUAL', 'MANUALS', 'GUIDE', 'GUIDES',
        'HANDBOOK', 'HANDBOOKS', 'TEMPLATE', 'TEMPLATES', 'CHECKLIST', 'CHECKLISTS',
        # v3.0.93: Missing common document/writing words
        'HEADING', 'HEADINGS', 'WRITING', 'WRITTEN', 'PARAGRAPH', 'PARAGRAPHS',
        'CONTENT', 'CONTENTS', 'TEXT', 'EXAMPLE', 'EXAMPLES', 'SAMPLE', 'SAMPLES',
        # v3.0.93: US State abbreviations (never need definition in documents)
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC',
        # v3.0.93: Country/region codes
        'US', 'USA', 'UK', 'EU', 'UAE', 'AU', 'CA', 'JP', 'CN', 'DE', 'FR', 'IT', 'ES',
        # v3.0.93: Well-known organizations (don't need definitions)
        'IET', 'ACM', 'ASME', 'ASCE', 'AIA', 'ACI', 'ASHRAE', 'AWWA', 'APHA',
        # v3.0.93: Extremely common universal acronyms (no definition needed)
        'TBD', 'TBA', 'TBC', 'NA', 'N/A',  # To Be Determined/Announced/Confirmed, Not Applicable
        'FAQ', 'FAQS',  # Frequently Asked Questions
        'UI', 'UX', 'GUI',  # User Interface/Experience, Graphical UI
        'IBM', 'HP', 'AMD', 'ARM',  # Well-known tech companies
        'PII',  # Personally Identifiable Information (universal privacy term)
        'USDOT', 'FHWA', 'FTA', 'NHTSA',  # US transportation agencies
        'V2I', 'V2V', 'V2X', 'C2C',  # Vehicle/car communications (ITS standard terms)
        'O&M', 'R&D',  # Operations & Maintenance, Research & Development
        'COTS', 'GOTS',  # Commercial/Government Off-The-Shelf
        'ROI', 'KPI', 'SLA',  # Return on Investment, Key Performance Indicator, Service Level Agreement
        'B2B', 'B2C', 'B2G',  # Business to Business/Consumer/Government
        'QA', 'QC',  # Quality Assurance/Control
        'PM', 'SE', 'QE',  # Project Manager, Systems Engineer, Quality Engineer
        # v3.0.93: Common long ALL CAPS words (11-12 chars) in technical documents
        'ILLUSTRATING', 'ILLUSTRATION', 'ILLUSTRATIONS', 'DEMONSTRATED', 'DEMONSTRATES',
        'COORDINATING', 'COORDINATION', 'COMMUNICATING', 'COMMUNICATION', 'COMMUNICATIONS',
        'RELATIONSHIP', 'RELATIONSHIPS', 'ABBREVIATION', 'ABBREVIATIONS',
        'STAKEHOLDER', 'STAKEHOLDERS', 'MEASUREMENT', 'MEASUREMENTS',
        'DISTRIBUTION', 'DISTRIBUTIONS', 'DEVELOPMENT', 'DEVELOPMENTS',
        'DESCRIPTION', 'DESCRIPTIONS', 'ENVIRONMENT', 'ENVIRONMENTS', 'ENVIRONMENTAL',
        'APPLICATION', 'APPLICATIONS', 'ENGINEERING', 'OPERATIONAL', 'OPERATIONS',
        'INFORMATION', 'NOTIFICATION', 'NOTIFICATIONS', 'CERTIFICATION', 'CERTIFICATIONS',
        'PREPARATION', 'PRESENTATION', 'PRESENTATIONS', 'INSTALLATION', 'INSTALLATIONS',
        'REQUIREMENTS', 'REQUIREMENT', 'DELIVERABLE', 'DELIVERABLES', 'ACHIEVEMENT', 'ACHIEVEMENTS',
        'PROCUREMENT', 'PROCUREMENTS', 'MANUFACTURE', 'MANUFACTURER', 'MANUFACTURERS',
        'DOCUMENTATION', 'INSPECTION', 'INSPECTIONS', 'EVALUATION', 'EVALUATIONS',
        'AUTHORIZATION', 'AUTHORIZATIONS', 'MODIFICATION', 'MODIFICATIONS',
        'RESPONSIBILITIES', 'RESPONSIBILITY', 'ACCOUNTABILITY',
        # v3.0.93: Less common but valid document terms
        'SUBCONTRACTOR', 'SUBCONTRACTORS', 'CONFIGURATION', 'CONFIGURATIONS',
        'AUTHORIZATION', 'AUTHORIZATIONS', 'DETERMINATION', 'DETERMINATIONS',
        'CONSIDERATION', 'CONSIDERATIONS', 'RECOMMENDATION', 'RECOMMENDATIONS',
        'IMPLEMENTATION', 'IMPLEMENTATIONS', 'SPECIFICATION', 'SPECIFICATIONS',
        'IDENTIFICATION', 'IDENTIFICATIONS', 'QUALIFICATION', 'QUALIFICATIONS',
        'DEMONSTRATION', 'DEMONSTRATIONS', 'INVESTIGATION', 'INVESTIGATIONS',
        'PARTICIPATION', 'PARTICIPATIONS', 'COLLABORATION', 'COLLABORATIONS',
        # v3.0.93: Common words that appear ALL CAPS in NIST/security documents
        'PUBLICATION', 'PUBLICATIONS', 'PERSPECTIVE', 'PERSPECTIVES',
        'UNAUTHORIZED', 'AUTHORIZED', 'SECURITY', 'INCLUDES', 'INCLUDED',
        'UPDATES', 'UPDATED', 'UPDATES', 'SEE', 'EXCEPTION', 'EXCEPTIONS',
        'ACCESS', 'CONTROL', 'CONTROLS', 'CONTROLLED', 'CATEGORY', 'CATEGORIES',
        'BASELINE', 'BASELINES', 'MODERATE', 'HIGH', 'LOW', 'CRITICAL',
        'ASSESSMENT', 'ASSESSMENTS', 'PROTECTION', 'PROTECTIONS',
        'PRIVACY', 'INTEGRITY', 'AVAILABILITY', 'CONFIDENTIALITY',
        'MANAGEMENT', 'MANAGER', 'MANAGERS', 'SYSTEM', 'SYSTEMS',
        'COMPONENT', 'COMPONENTS', 'ORGANIZATION', 'ORGANIZATIONAL',
        # Additional security/compliance terms
        'MONITORING', 'PLANNING', 'AWARENESS', 'TRAINING', 'PERSONNEL',
        'PHYSICAL', 'CONTINGENCY', 'MAINTENANCE', 'MEDIA', 'AUDIT', 'AUDITS',
        'INCIDENT', 'INCIDENTS', 'RESPONSE', 'RISK', 'RISKS', 'SUPPLY', 'CHAIN',
        'ACQUISITION', 'ACQUISITIONS', 'PROGRAM', 'PROGRAMS', 'TRANSMITTED',
        # Common verbs/adjectives appearing in ALL CAPS
        'ENHANCED', 'WITHDRAWAL', 'WITHDRAWN', 'SELECTED', 'SELECTION',
        'ADDITIONAL', 'RELATED', 'DISCUSSED', 'DISCUSSION', 'SUPPLEMENTAL',
        # v3.0.93: More common words from NIST/security documents
        'DESTRUCTION', 'ALTERNATIVE', 'ALTERNATIVES', 'CONNECTIONS', 'CONNECTION',
        'INDIVIDUALS', 'INDIVIDUAL', 'HISTORICAL', 'PERSONNEL', 'TRANSMISSION',
        'ESTABLISHING', 'ESTABLISHED', 'DISPOSITION', 'DISPOSITIONS',
        'COMPROMISE', 'COMPROMISED', 'TERMINATION', 'TERMINATED', 'TERMINATE',
        'SUSPENSION', 'SUSPENDED', 'REVOCATION', 'REVOKED', 'REVOKE',
        'ACTIVATION', 'ACTIVATED', 'DEACTIVATION', 'DEACTIVATED',
        'GENERATION', 'GENERATED', 'REGENERATION', 'REGENERATED',
        'ENCRYPTION', 'ENCRYPTED', 'DECRYPTION', 'DECRYPTED',
        'AUTHENTICATION', 'AUTHENTICATED', 'AUTHORIZATION', 'AUTHORIZATIONS',
        'NOTIFICATION', 'NOTIFICATIONS', 'NOTIFICATION', 'NOTIFIED',
        'REGISTRATION', 'REGISTERED', 'UNREGISTERED', 'DEREGISTRATION',
        'SEGREGATION', 'SEGREGATED', 'SEPARATION', 'SEPARATED',
        'RESTRICTION', 'RESTRICTED', 'UNRESTRICTED', 'LIMITATIONS', 'LIMITATION',
        'PROHIBITION', 'PROHIBITED', 'PROHIBITION', 'PROHIBITIONS',
        'PRESERVATION', 'PRESERVED', 'RETENTION', 'RETAINED', 'RETAINS',
        'ALLOCATION', 'ALLOCATED', 'DEALLOCATION', 'DEALLOCATED',
        'COLLECTION', 'COLLECTED', 'PROCESSING', 'PROCESSED', 'PROCESSOR',
        'DISCLOSURE', 'DISCLOSED', 'REDACTION', 'REDACTED', 'MINIMIZATION',
        'VALIDATION', 'VALIDATED', 'VERIFICATION', 'VERIFIED', 'VERIFIES',
        'PENETRATION', 'VULNERABILITY', 'VULNERABILITIES', 'EXPLOITATION',
        'REMEDIATION', 'REMEDIATED', 'MITIGATION', 'MITIGATED', 'MITIGATIONS',
        'RESOLUTION', 'RESOLVED', 'ESCALATION', 'ESCALATED', 'CORRELATION',
        'AGGREGATION', 'AGGREGATED', 'CONSOLIDATION', 'CONSOLIDATED',
        'DISSEMINATION', 'DISSEMINATED', 'DISTRIBUTION', 'DISTRIBUTED',
        'DUPLICATION', 'DUPLICATED', 'REPLICATION', 'REPLICATED',
        'RESTORATION', 'RESTORED', 'RECONSTITUTION', 'RECONSTITUTED',
        'RECONSTRUCTION', 'RECONSTRUCTED', 'SANITIZATION', 'SANITIZED',
        # Common adjective/status words
        'SENSITIVE', 'CLASSIFIED', 'UNCLASSIFIED', 'CONFIDENTIAL', 'SECRET',
        'PRIVILEGED', 'UNPRIVILEGED', 'ELEVATED', 'STANDARD', 'NONSTANDARD',
        'AUTOMATIC', 'AUTOMATED', 'MANUAL', 'DYNAMIC', 'STATIC', 'PASSIVE', 'ACTIVE',
        'EXTERNAL', 'INTERNAL', 'REMOVABLE', 'PORTABLE', 'MOBILE', 'WIRELESS',
        'TEMPORARY', 'PERMANENT', 'PERIODIC', 'CONTINUOUS', 'INTERMITTENT',
        # v3.0.93: Final batch from NIST testing
        'CYBERSPACE', 'NETWORKING', 'REQUIRING', 'REQUIRED', 'REQUIRES',
        'PROCESSES', 'PROCESSED', 'PROCESSOR', 'PROCESSORS', 'PROCESSING',
        'OPERATING', 'OPERATOR', 'OPERATORS', 'OPERATION', 'OPERATIONS',
        'SUPPORTING', 'SUPPORTED', 'SUPPORTS', 'SUPPORT', 'SUPPORTER',
        'PROVIDING', 'PROVIDED', 'PROVIDES', 'PROVIDER', 'PROVIDERS',
        'RECEIVING', 'RECEIVED', 'RECEIVES', 'RECEIVER', 'RECEIVERS',
        'DETECTING', 'DETECTED', 'DETECTS', 'DETECTOR', 'DETECTORS', 'DETECTION',
        'REPORTING', 'REPORTED', 'REPORTS', 'REPORTER', 'REPORTERS',
        'RECORDING', 'RECORDED', 'RECORDS', 'RECORDER', 'RECORDERS',
        'ANALYZING', 'ANALYZED', 'ANALYZES', 'ANALYZER', 'ANALYZERS', 'ANALYSIS',
        'REVIEWING', 'REVIEWED', 'REVIEWS', 'REVIEWER', 'REVIEWERS',
        'APPROVING', 'APPROVED', 'APPROVES', 'APPROVER', 'APPROVERS', 'APPROVAL',
        'EXECUTING', 'EXECUTED', 'EXECUTES', 'EXECUTOR', 'EXECUTORS', 'EXECUTION',
        'EMPLOYING', 'EMPLOYED', 'EMPLOYS', 'EMPLOYER', 'EMPLOYERS', 'EMPLOYMENT',
        # More common words
        'STRUCTURE', 'STRUCTURES', 'STRUCTURED', 'STRUCTURING',
        'FRAMEWORK', 'FRAMEWORKS', 'BOUNDARY', 'BOUNDARIES',
        'ATTRIBUTE', 'ATTRIBUTES', 'PROPERTY', 'PROPERTIES',
        'PARAMETER', 'PARAMETERS', 'VARIABLE', 'VARIABLES', 'CONSTANT', 'CONSTANTS',
        'MECHANISM', 'MECHANISMS', 'TECHNIQUE', 'TECHNIQUES', 'STRATEGY', 'STRATEGIES',
        'PRINCIPLE', 'PRINCIPLES', 'CRITERION', 'CRITERIA', 'FACTOR', 'FACTORS',
        # Short common verbs that might appear as ALL CAPS
        'REV', 'VER', 'VOL', 'NO', 'PG', 'PP', 'FIG', 'CH', 'SEC', 'PT', 'APP',
        # v3.0.93: More common words found in NASA/DOT/government documents
        'ASSIGN', 'ASSIGNED', 'ASSIGNS', 'ASSURE', 'ASSURED', 'ASSURES', 'ASSURANCE',
        'BASED', 'CROSS', 'CROSSED', 'CROSSES', 'CROSSING',
        'DESCRIBE', 'DESCRIBED', 'DESCRIBES', 'DESCRIBING',
        'EARTH', 'LUNAR', 'SOLAR', 'ORBITAL', 'PLANETARY',
        'GO', 'GOES', 'GOING', 'GONE',
        'DO', 'DOES', 'DOING', 'DONE',
        'HOURS', 'HOUR', 'DAYS', 'DAY', 'WEEKS', 'WEEK', 'MONTHS', 'MONTH', 'YEARS', 'YEAR',
        'LESS', 'MORE', 'MOST', 'LEAST', 'MUCH', 'MANY', 'FEW', 'SOME', 'ALL', 'NONE',
        'OUTLINE', 'OUTLINED', 'OUTLINES', 'OUTLINING',
        'ELEMENT', 'ELEMENTS', 'ITEM', 'ITEMS', 'UNIT', 'UNITS', 'PIECE', 'PIECES',
        'INERTIAL', 'THERMAL', 'MECHANICAL', 'ELECTRICAL', 'OPTICAL', 'CHEMICAL',
        'LABORATORY', 'LABORATORIES', 'FACILITY', 'FACILITIES', 'STATION', 'STATIONS',
        'SIMULATION', 'SIMULATED', 'SIMULATES', 'SIMULATOR', 'SIMULATORS',
        'FINISHING', 'FINISHED', 'FINISHES', 'FINISH',
        'CHAIRMAN', 'CHAIRWOMAN', 'CHAIRPERSON', 'COMMITTEE', 'COMMITTEES',
        'ACCEPTANCE', 'ACCEPTED', 'ACCEPTS', 'ACCEPTING', 'ACCEPTABLE',
        'ADAPTIVE', 'ADAPTED', 'ADAPTS', 'ADAPTING', 'ADAPTATION',
        'DIAGRAM', 'DIAGRAMS', 'DIAGRAMMED', 'CHART', 'CHARTS', 'CHARTED', 'CHARTING',
        'CONCEPT', 'CONCEPTS', 'CONCEPTUAL', 'CONOPS', 'GROUPS', 'GROUP', 'GROUPED',
        'ABILITY', 'ABILITIES', 'CAPABLE', 'CAPABILITY', 'CAPABILITIES',
        # Additional action verbs
        'ACCEPT', 'ACCESS', 'ACCESSED', 'ACCESSES', 'ACCESSING',
        'MAINTAIN', 'MAINTAINED', 'MAINTAINS', 'MAINTAINING',
        'INSTALL', 'INSTALLED', 'INSTALLS', 'INSTALLING', 'INSTALLER',
        'DISPOSE', 'DISPOSED', 'DISPOSES', 'DISPOSING', 'DISPOSAL',
        'PROCURE', 'PROCURED', 'PROCURES', 'PROCURING',
        # v3.0.93: More common words from NASA/government documents
        'PERFORMED', 'PERFORMING', 'PERFORMS', 'PERFORM', 'PERFORMER',
        'SCIENCES', 'SCIENCE', 'SCIENTIFIC', 'SCIENTIFICALLY',
        'SHIFT', 'SHIFTS', 'SHIFTED', 'SHIFTING',
        'SUBMISSION', 'SUBMISSIONS', 'SUBMIT', 'SUBMITS', 'SUBMITTED', 'SUBMITTING',
        'USED', 'USE', 'USES', 'USING', 'USER', 'USERS', 'USAGE',
        'REQUIRED', 'REQUIRE', 'REQUIRES', 'REQUIRING', 'REQUISITE', 'REQUISITION',
        'PROVIDED', 'PROVIDE', 'PROVIDES', 'PROVIDING', 'PROVIDER', 'PROVIDERS',
        'INCLUDED', 'INCLUDE', 'INCLUDES', 'INCLUDING', 'INCLUSION',
        'COMPLETED', 'COMPLETE', 'COMPLETES', 'COMPLETING', 'COMPLETION',
        'DEVELOPED', 'DEVELOP', 'DEVELOPS', 'DEVELOPING', 'DEVELOPER', 'DEVELOPERS',
        'DETERMINED', 'DETERMINE', 'DETERMINES', 'DETERMINING', 'DETERMINISTIC',
        'ESTABLISHED', 'ESTABLISH', 'ESTABLISHES', 'ESTABLISHING', 'ESTABLISHMENT',
        'IDENTIFIED', 'IDENTIFY', 'IDENTIFIES', 'IDENTIFYING', 'IDENTIFIER',
        'IMPLEMENTED', 'IMPLEMENT', 'IMPLEMENTS', 'IMPLEMENTING', 'IMPLEMENTER',
        'SPECIFIED', 'SPECIFY', 'SPECIFIES', 'SPECIFYING', 'SPECIFIER',
        'EVALUATED', 'EVALUATE', 'EVALUATES', 'EVALUATING', 'EVALUATOR',
        'VERIFIED', 'VERIFY', 'VERIFIES', 'VERIFYING', 'VERIFIER',
        'VALIDATED', 'VALIDATE', 'VALIDATES', 'VALIDATING', 'VALIDATOR',
        'APPROVED', 'APPROVE', 'APPROVES', 'APPROVING', 'APPROVER',
    })
    
    def __init__(self, enabled: bool = True, ignore_common_acronyms: bool = None):
        super().__init__(enabled)
        self._defined: Set[str] = set()
        self._acronym_section_paras: Set[int] = set()  # Paragraph indices in acronym section
        self._errors: List[str] = []
        
        # v3.0.33: Strict mode configuration
        # Load from config if not explicitly provided
        if ignore_common_acronyms is None:
            self._ignore_common_acronyms = self._load_config_setting()
        else:
            self._ignore_common_acronyms = ignore_common_acronyms
        
        # v3.0.33: Transparency metrics
        self._metrics = {
            'total_acronyms_found': 0,
            'defined_count': 0,
            'suppressed_by_allowlist_count': 0,
            'flagged_count': 0,
            'strict_mode': not self._ignore_common_acronyms,
            'allowlist_matches': []  # Track which acronyms were suppressed
        }
    
    def _load_config_setting(self) -> bool:
        """Load ignore_common_acronyms from config.json."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = __import__('json').load(f)
                    return config.get('acronym_settings', {}).get('ignore_common_acronyms', False)
        except Exception as e:
            _log(f"Config load error: {e}", level='warning')
        return False  # Default to strict mode
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return transparency metrics from last check."""
        return self._metrics.copy()
    
    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        full_text: str = "",
        filepath: str = "",
        **kwargs
    ) -> List['ReviewIssue']:
        """Check for undefined acronyms.
        
        v3.0.33: Added strict mode and transparency metrics.
        - When ignore_common_acronyms=False (strict mode): ALL acronyms must be defined
        - When ignore_common_acronyms=True: Common acronyms (NASA, FBI, etc.) are suppressed
        - Metrics are always available via get_metrics()
        """
        
        if not self.enabled:
            return []
        
        self._defined = set()
        self._acronym_section_paras = set()
        self._errors = []
        issues = []
        
        # Reset metrics for this check
        self._metrics = {
            'total_acronyms_found': 0,
            'defined_count': 0,
            'suppressed_by_allowlist_count': 0,
            'flagged_count': 0,
            'strict_mode': not self._ignore_common_acronyms,
            'allowlist_matches': []
        }
        
        _log(f"Starting check: {len(paragraphs)} paragraphs, filepath={bool(filepath)}, strict_mode={not self._ignore_common_acronyms}")
        
        try:
            # Step 1: Find acronym section and extract definitions
            self._find_acronym_section(paragraphs)
            _log(f"After section detection: {len(self._defined)} defined, section paras: {len(self._acronym_section_paras)}")
            
            # Step 2: Extract from XML (tables that python-docx can't read)
            if filepath:
                self._extract_from_xml(filepath)
                _log(f"After XML extraction: {len(self._defined)} defined")
            
            # Step 3: Extract inline definitions from full text
            if full_text:
                self._extract_inline_definitions(full_text)
                _log(f"After inline extraction: {len(self._defined)} defined")
            
            # Step 4: Find all acronym usage
            acronym_usage = self._find_usage(paragraphs, filepath)
            _log(f"Found {len(acronym_usage)} unique acronyms in document")
            
            # Track total unique acronyms found
            self._metrics['total_acronyms_found'] = len(acronym_usage)
            
            # Step 5: Generate issues for undefined acronyms with metrics tracking
            for acronym, info in acronym_usage.items():
                # Check if defined in document
                if info.is_defined or acronym in self._defined:
                    self._metrics['defined_count'] += 1
                    _log(f"OK (defined): {acronym}")
                    continue

                # v4.7.0: NEVER_FLAG list - always skip these regardless of strict mode
                # These are truly universal terms like PDF, HTML, USB that never need definition
                if acronym in self.NEVER_FLAG:
                    self._metrics['suppressed_by_allowlist_count'] += 1
                    self._metrics['allowlist_matches'].append(acronym)
                    _log(f"NEVER_FLAG (universal): {acronym}")
                    continue

                # Check if suppressed by allowlist (only in non-strict mode)
                if self._ignore_common_acronyms:
                    if acronym in self.UNIVERSAL_SKIP:
                        self._metrics['suppressed_by_allowlist_count'] += 1
                        self._metrics['allowlist_matches'].append(acronym)
                        _log(f"SUPPRESSED (allowlist): {acronym}")
                        continue

                    # v4.6.0: Check external acronym database
                    external_acronyms = _load_external_acronym_database()
                    if acronym in external_acronyms:
                        self._metrics['suppressed_by_allowlist_count'] += 1
                        self._metrics['allowlist_matches'].append(acronym)
                        _log(f"SUPPRESSED (external db): {acronym}")
                        continue
                
                # Check other skip conditions (not affected by strict mode)
                if self._should_flag_with_metrics(acronym, info):
                    issues.append(self.create_issue(
                        severity='High',
                        message=f'"{acronym}" used {info.usage_count}x but never defined',
                        context=acronym,
                        paragraph_index=info.first_para_idx,
                        suggestion=f'Define "{acronym}" on first use or add to acronym list',
                        rule_id='ACR001'
                    ))
                    self._metrics['flagged_count'] += 1
                    _log(f"FLAGGED: {acronym} (para {info.first_para_idx}, {info.usage_count}x)")
        
        except Exception as e:
            self._errors.append(f"Acronym check error: {e}")
            _log(f"ERROR: {e}")
        
        _log(f"Check complete: {len(issues)} issues, metrics={self._metrics}")
        return issues
    
    def _find_acronym_section(self, paragraphs: List[Tuple[int, str]]):
        """
        Find the acronym/abbreviation section by looking for clusters of
        definition-style paragraphs OR table-style acronym lists.
        
        Handles two formats:
        1. Paragraph format: "ABC - Some Definition" or "ABC: Some Definition"
        2. Table format: Paragraph N = "ABC", Paragraph N+1 = "Some Definition"
        """
        
        # Pattern for definition-style paragraph
        definition_pattern = re.compile(
            r'^([A-Z][A-Z0-9&/]{0,9})\s*[-–—:]\s*[A-Z]',
            re.MULTILINE
        )
        
        # Pattern for standalone acronym (table cell style)
        standalone_acronym_pattern = re.compile(r'^[A-Z][A-Z0-9&/]{1,9}$')
        
        # Pattern for definition text (starts with capital, has lowercase)
        definition_text_pattern = re.compile(r'^[A-Z][a-z]')
        
        # Find all paragraphs that look like definitions
        definition_paras = []
        
        # Also track potential table-style definitions
        # (acronym in one para, definition in next)
        table_style_acronyms = []
        
        for i, (idx, text) in enumerate(paragraphs):
            if not text or len(text) < 2:
                continue
            
            text_stripped = text.strip()
            
            # Check for paragraph-style definition "ABC - Definition"
            match = definition_pattern.match(text_stripped)
            if match:
                acronym = match.group(1)
                if len(acronym) >= 2 and acronym not in self.COMMON_CAPS_SKIP:
                    definition_paras.append((idx, acronym, text_stripped[:50]))
                    _log(f"Definition para {idx}: {acronym}")
                continue
            
            # Check for table-style: standalone acronym followed by definition
            if standalone_acronym_pattern.match(text_stripped):
                acronym = text_stripped
                if (len(acronym) >= 2 and 
                    acronym not in self.COMMON_CAPS_SKIP and
                    acronym not in self.UNIVERSAL_SKIP):
                    
                    # Look at next paragraph - is it a definition?
                    if i + 1 < len(paragraphs):
                        next_idx, next_text = paragraphs[i + 1]
                        if next_text and definition_text_pattern.match(next_text.strip()):
                            # This looks like table-style: ACRONYM / Definition
                            table_style_acronyms.append((idx, acronym, next_text[:50]))
                            _log(f"Table-style para {idx}: {acronym} -> {next_text[:30]}...")
        
        _log(f"Found {len(definition_paras)} definition-style, {len(table_style_acronyms)} table-style paragraphs")
        
        # Combine both types
        all_definitions = definition_paras + table_style_acronyms
        
        if len(all_definitions) < 3:
            # Not enough to form a section, but still mark any we found
            for idx, acronym, _ in all_definitions:
                self._mark_defined(acronym, 'sparse_def')
            return
        
        # Sort by paragraph index
        all_definitions.sort(key=lambda x: x[0])
        
        # Find clusters of definition paragraphs (allowing gaps)
        clusters = []
        current_cluster = [all_definitions[0]]
        
        for i in range(1, len(all_definitions)):
            prev_idx = all_definitions[i-1][0]
            curr_idx = all_definitions[i][0]
            gap = curr_idx - prev_idx
            
            # Allow larger gaps (up to 15) to handle skipped items and spacing
            if gap <= 15:
                current_cluster.append(all_definitions[i])
            else:
                if len(current_cluster) >= 3:
                    clusters.append(current_cluster)
                current_cluster = [all_definitions[i]]
        
        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)
        
        _log(f"Found {len(clusters)} definition clusters")
        
        # Process clusters - mark all acronyms as defined
        for cluster in clusters:
            start_idx = cluster[0][0]
            end_idx = cluster[-1][0]
            
            _log(f"Acronym section: paragraphs {start_idx} to {end_idx} ({len(cluster)} definitions)")
            
            # Only mark the actual definition paragraphs as "in acronym section"
            # (not the entire range, to avoid skipping usage in other content)
            for idx, acronym, text_preview in cluster:
                # Add the acronym paragraph and the next one (definition)
                self._acronym_section_paras.add(idx)
                self._acronym_section_paras.add(idx + 1)
            
            # Mark all acronyms in the cluster as defined
            for idx, acronym, text_preview in cluster:
                self._mark_defined(acronym, 'section')
    
    def _extract_from_xml(self, filepath: str):
        """
        Extract acronyms from document XML.
        
        This is CRITICAL for documents where acronyms are in tables,
        which python-docx often can't read properly.
        
        Looks for patterns like:
        - Table cells: ACRONYM | Definition
        - Inline: "Full Name (ACRONYM)"
        """
        if not filepath or not os.path.exists(filepath):
            return
        
        # Skip PDF files - they're not zip files
        if filepath.lower().endswith('.pdf'):
            return
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                if 'word/document.xml' not in zf.namelist():
                    return
                
                xml_content = zf.read('word/document.xml').decode('utf-8')
                
                # Extract all text runs to find acronym patterns
                # Pattern: Find all <w:t> text content
                text_pattern = re.compile(r'<w:t[^>]*>([^<]+)</w:t>')
                all_texts = text_pattern.findall(xml_content)
                
                # Join consecutive texts and look for acronym definitions
                full_text = ' '.join(all_texts)
                
                # Pattern 1: "ACRONYM - Definition" or "ACRONYM: Definition"
                # MUST have explicit delimiter to avoid false positives like "FMEA Analysis"
                # v3.0.8: Fixed to require - or : delimiter (was matching any whitespace)
                definition_pattern = re.compile(
                    r'\b([A-Z][A-Z0-9&/]{1,9})\s*[-:]\s*([A-Z][a-z][a-zA-Z\s,&-]{5,80})'
                )
                
                for match in definition_pattern.finditer(full_text):
                    acronym = match.group(1)
                    definition = match.group(2).strip()
                    
                    # Validate it looks like a real definition
                    # (starts with capital, has lowercase, reasonable length)
                    if (len(acronym) >= 2 and 
                        len(definition) >= 5 and
                        acronym not in self.COMMON_CAPS_SKIP and
                        not acronym[0].isdigit()):
                        
                        self._mark_defined(acronym, 'xml_table')
                        _log(f"XML defined: {acronym} = {definition[:30]}...")
                
                # Pattern 2: Look for table rows with acronym patterns
                # Tables have <w:tr> rows with <w:tc> cells
                row_pattern = re.compile(r'<w:tr[^>]*>(.*?)</w:tr>', re.DOTALL)
                cell_pattern = re.compile(r'<w:tc[^>]*>(.*?)</w:tc>', re.DOTALL)
                
                for row_match in row_pattern.finditer(xml_content):
                    row_content = row_match.group(1)
                    cells = cell_pattern.findall(row_content)
                    
                    if len(cells) >= 2:
                        # Extract text from first two cells
                        cell1_texts = text_pattern.findall(cells[0])
                        cell2_texts = text_pattern.findall(cells[1])
                        
                        cell1 = ''.join(cell1_texts).strip()
                        cell2 = ''.join(cell2_texts).strip()
                        
                        # Check if cell1 looks like an acronym and cell2 looks like definition
                        if (re.match(r'^[A-Z][A-Z0-9&/]{1,9}$', cell1) and
                            len(cell2) >= 3 and
                            cell1 not in self.COMMON_CAPS_SKIP):
                            
                            self._mark_defined(cell1, 'table_cell')
                            _log(f"Table cell defined: {cell1}")
                
                # Pattern 3: Inline definitions "Full Name (ACRONYM)"
                inline_pattern = re.compile(
                    r'([A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+){1,5})\s*\(([A-Z][A-Z0-9&/]{1,9})\)'
                )
                
                for match in inline_pattern.finditer(full_text):
                    full_name = match.group(1)
                    acronym = match.group(2)
                    
                    if (len(acronym) >= 2 and 
                        acronym not in self.COMMON_CAPS_SKIP):
                        self._mark_defined(acronym, 'inline_xml')
                        _log(f"Inline defined: {acronym} = {full_name}")
                
                # Pattern 4: Look for "Acronyms" section header and extract content
                # v3.0.8: Added more stop headers and length cap to prevent swallowing entire doc
                acronym_section = re.search(
                    r'Acronyms.*?(?=Overview|Definitions|Purpose|Scope|Process|Procedure|'
                    r'Introduction|Background|References|Appendix|Requirements|'
                    r'Section\s+\d|^\d+\.\s+[A-Z]|\Z)',
                    full_text[:5000],  # Cap at 5000 chars to avoid matching entire document
                    re.DOTALL | re.IGNORECASE | re.MULTILINE
                )
                
                if acronym_section:
                    section_text = acronym_section.group(0)
                    # Additional safety: cap section to 3000 chars max
                    section_text = section_text[:3000]
                    # Find all uppercase sequences that look like acronyms
                    potential_acronyms = re.findall(r'\b([A-Z][A-Z0-9&/]{1,9})\b', section_text)
                    
                    for acronym in potential_acronyms:
                        if (len(acronym) >= 2 and 
                            acronym not in self.COMMON_CAPS_SKIP and
                            acronym not in self.UNIVERSAL_SKIP):
                            self._mark_defined(acronym, 'acronym_section')
                            _log(f"Section defined: {acronym}")
        
        except Exception as e:
            _log(f"XML extraction error: {e}")
            import traceback
            _log(traceback.format_exc())
    
    def _extract_inline_definitions(self, text: str):
        """Find inline definitions like 'Full Name (ACRONYM)'."""
        if not text:
            return
        
        # Pattern: "Full Name (ACRONYM)"
        pattern = re.compile(
            r'([A-Z][a-zA-Z]*(?:\s+(?:and|of|the|for|in|on|to|[A-Za-z]+))*)\s*'
            r'\(([A-Z][A-Z0-9&/-]{1,9})\)'
        )
        
        for match in pattern.finditer(text):
            acronym = match.group(2)
            if len(acronym) >= 2 and acronym not in self.COMMON_CAPS_SKIP:
                self._mark_defined(acronym, 'inline')
    
    def _mark_defined(self, acronym: str, source: str):
        """Mark an acronym as defined, including variants."""
        self._defined.add(acronym)
        
        # Handle special characters - ESH&M should also define ESH and ESHM
        if '&' in acronym or '/' in acronym:
            # Without special char
            clean = re.sub(r'[&/-]', '', acronym)
            if len(clean) >= 2:
                self._defined.add(clean)
            
            # Parts before special char
            for sep in ['&', '/', '-']:
                if sep in acronym:
                    parts = acronym.split(sep)
                    for part in parts:
                        part = part.strip()
                        if len(part) >= 2:
                            self._defined.add(part)
    
    def _is_section_heading(self, text: str) -> bool:
        """
        Detect if text is a section heading rather than content with acronyms.
        Section headings like "5. ROLES AND RESPONSIBILITIES" should not have
        their uppercase words flagged as undefined acronyms.
        """
        if not text:
            return False
        
        text = text.strip()
        
        # Pattern 1: Numbered section headers (1., 1.1, 2.3.4, etc.)
        # "5. ROLES AND RESPONSIBILITIES", "4.1 Functional Requirements"
        # Also handles definition sections: "2.2.1 AFFORDABILITY"
        if re.match(r'^\d+(\.\d+)*[\.\s]', text):
            # Check if this starts with a numbered section followed by all-caps term
            # This handles definition headers like "2.2.1 AFFORDABILITY" or "2.2.15 KEY PART"
            definition_match = re.match(r'^\d+(\.\d+)+\s+([A-Z][A-Z\s/()]+)(\s|$)', text)
            if definition_match:
                return True
            
            # Check if most of it is uppercase words (heading style)
            words = text.split()
            if len(words) <= 8:  # Short enough to be a heading
                # Skip the number prefix
                text_words = [w for w in words if not re.match(r'^\d+(\.\d+)*\.?$', w)]
                if text_words:
                    upper_count = sum(1 for w in text_words if w.isupper() or w[0].isupper())
                    if upper_count / len(text_words) >= 0.5:
                        return True
        
        # Pattern 2: All-caps short phrases (common headers)
        # "NOTES", "END OF DOCUMENT", "APPENDIX A"
        if text.isupper() and len(text.split()) <= 5 and len(text) <= 50:
            return True
        
        # Pattern 3: Definition-style headers in the middle of text
        # e.g., text contains "2.2.5 CRITICAL CHARACTERISTIC" as a definition
        definition_inline = re.match(r'^(\d+\.\d+(?:\.\d+)?)\s+([A-Z][A-Z\s]+)\s', text)
        if definition_inline:
            term = definition_inline.group(2).strip()
            # If the all-caps term is followed by definition text, it's a header
            if len(term.split()) <= 5:
                return True
        
        # Pattern 4: Common section header patterns
        header_patterns = [
            r'^(APPENDIX|ANNEX|SECTION|CHAPTER|PART)\s+[A-Z0-9]',
            r'^(TABLE OF CONTENTS|REVISION HISTORY|DOCUMENT CONTROL)',
            r'^(END OF|BEGINNING OF)\s+',
            r'^[A-Z]\.\s+[A-Z]',  # "A. INTRODUCTION"
            r'^(RATIONALE|DEFINITIONS|REFERENCES|OBJECTIVES|SCOPE)\s*$',
        ]
        for pattern in header_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def _is_all_caps_instruction(self, text: str) -> bool:
        """
        Detect if text is an ALL CAPS instruction/header that should be skipped entirely.

        v4.5.2: Handles instructional text like:
        "A HARD OR ELECTRONIC COPY OF THE LSOP MUST BE READILY AVAILABLE IN THE LAB"

        Returns True if:
        - Text has 4+ words
        - More than 70% of words are ALL CAPS
        - Contains common instruction patterns
        """
        if not text or len(text) < 10:
            return False

        text = text.strip()
        words = text.split()

        # Need at least 4 words to be considered an ALL CAPS instruction
        if len(words) < 4:
            return False

        # Count uppercase words (words that are all caps, excluding single-letter words)
        upper_words = sum(1 for w in words if len(w) > 1 and w.isupper())

        # If more than 70% of words are ALL CAPS, this is likely instructional text
        if upper_words / len(words) >= 0.7:
            return True

        return False

    def _find_usage(self, paragraphs: List[Tuple[int, str]], filepath: str = "") -> Dict[str, AcronymInfo]:
        """Find all acronym usage in the document."""

        usage: Dict[str, AcronymInfo] = {}

        # Get hyperlinked text to exclude (document numbers)
        hyperlinked = self._get_hyperlinked_text(filepath) if filepath else set()

        # Pattern for potential acronyms
        acronym_pattern = re.compile(r'\b([A-Z][A-Z0-9&/-]{1,11})\b')

        # Pattern for template/instruction text in brackets - skip these entirely
        # Matches: [GREEN TEXT], [INSERT NAME], [ENTER DATE], etc.
        template_bracket_pattern = re.compile(r'\[[A-Z][A-Z\s]+\]')
        
        # Patterns for document numbers/references to SKIP
        # These match things like: N0-0202_00, F-FAC1-006, FAC1-001-DI, CTM N201
        # v2.9.1 Batch 7 A7: Enhanced document ID patterns
        doc_number_patterns = [
            re.compile(r'^[A-Z]{1,2}\d-'),           # N0-, F1-, C0-, D0- etc
            re.compile(r'^[A-Z]-[A-Z]{2,4}\d'),      # F-FAC1, F-FAC2
            re.compile(r'^[A-Z]{2,4}\d-\d'),         # FAC1-001, FAC2-001
            re.compile(r'^[A-Z]{2,4}-\d'),           # CTM-123, etc
            re.compile(r'^\d{1,2}-[A-Z]'),           # 01-A, etc (numbered items)
            re.compile(r'^[A-Z]{2}\s*N\d'),          # CO N101, CTM N201
            re.compile(r'^MIL-STD-\d'),              # MIL-STD-498, MIL-STD-882E
            re.compile(r'^MIL-[A-Z]+-\d'),           # MIL-HDBK-217, etc
            re.compile(r'^DO-\d'),                   # DO-178C, DO-254
            re.compile(r'^IEEE\s*\d'),               # IEEE 830, IEEE 1233
            re.compile(r'^ISO\s*\d'),                # ISO 9001, ISO 26262
            re.compile(r'^SAE\s*[A-Z]*\d'),          # SAE AS6500, SAE J1939
            # v2.9.1 Batch 7 A7: Additional Northrop Grumman doc patterns
            re.compile(r'^[A-Z]\d-\d{4}'),           # C0-0920, D0-5400, etc.
            re.compile(r'^[A-Z]\d-\d{4}_\d'),        # C0-0920_00, C0-0912_01
            re.compile(r'^[A-Z]{2,3}\d{3,5}'),       # DI12345, SRS1234
        ]
        
        for idx, text in paragraphs:
            if not text:
                continue
            
            # Skip paragraphs in the acronym section entirely
            if idx in self._acronym_section_paras:
                continue
            
            # Skip section headings (numbered titles like "5. ROLES AND RESPONSIBILITIES")
            # These are NOT acronyms but section headers
            text_stripped = text.strip()
            if self._is_section_heading(text_stripped):
                continue

            # v4.5.1: Remove template/instruction text in brackets before scanning
            # This prevents [GREEN TEXT], [INSERT NAME], etc. from being flagged
            text_for_scan = template_bracket_pattern.sub(' ', text)

            # v4.5.2: Detect ALL CAPS sentences/phrases and skip them entirely
            # These are instructional text like "A HARD OR ELECTRONIC COPY MUST BE AVAILABLE"
            # If more than 70% of a sentence is uppercase words, skip the whole thing
            if self._is_all_caps_instruction(text_for_scan):
                _log(f"Skipping ALL CAPS instruction text: {text_for_scan[:50]}...")
                continue

            for match in acronym_pattern.finditer(text_for_scan):
                acronym = match.group(1).rstrip('&/-')
                
                if not acronym or len(acronym) < 2:
                    continue
                
                # Skip common caps words early (performance + clarity)
                # These are NEVER real acronyms (NOTE, SECTION, TABLE, etc.)
                if acronym in self.COMMON_CAPS_SKIP:
                    continue
                
                # v3.0.33: DON'T skip UNIVERSAL_SKIP here anymore
                # Let the check() method handle it based on strict mode setting
                # This enables proper metrics tracking
                
                # Skip if in hyperlinked text
                if acronym in hyperlinked:
                    continue
                
                # Skip if matches any document number pattern
                is_doc_number = False
                for pattern in doc_number_patterns:
                    if pattern.match(acronym):
                        _log(f"Skipping doc number pattern: {acronym}")
                        is_doc_number = True
                        break
                if is_doc_number:
                    continue
                
                # Check context - is this followed by digits/dashes suggesting doc reference?
                end_pos = match.end()
                if end_pos < len(text_for_scan):
                    following = text_for_scan[end_pos:end_pos+10]
                    # Skip if followed by: -digits, _digits, space+N+digits
                    if re.match(r'^[-_]\d', following) or re.match(r'^\s+N\d', following):
                        _log(f"Skipping doc ref context: {acronym}{following[:5]}")
                        continue

                # v4.5.1: Skip section reference codes (single letter + 1-2 digits)
                # Matches: A1, B12, C3, D99, etc. - common in SOPs and procedures
                if re.match(r'^[A-Z]\d{1,2}$', acronym):
                    _log(f"Skipping section reference code: {acronym}")
                    continue
                
                # v3.0.9: Removed parentheses skip - it was too aggressive
                # Acronyms like "(FMEA)" should still be counted as usage.
                # The inline definition detection (_extract_inline_definitions) 
                # already handles "Full Name (ACRONYM)" patterns properly.
                
                # Track usage
                if acronym not in usage:
                    usage[acronym] = AcronymInfo(
                        acronym=acronym,
                        first_para_idx=idx,
                        is_defined=acronym in self._defined
                    )
                
                usage[acronym].usage_count += 1
        
        return usage
    
    def _get_hyperlinked_text(self, filepath: str) -> Set[str]:
        """Extract text that is hyperlinked (document numbers, etc.)."""
        hyperlinked = set()
        
        if not filepath or not os.path.exists(filepath):
            return hyperlinked
        
        # Skip PDF files
        if filepath.lower().endswith('.pdf'):
            return hyperlinked
        
        try:
            with zipfile.ZipFile(filepath, 'r') as zf:
                if 'word/document.xml' not in zf.namelist():
                    return hyperlinked
                
                xml_content = zf.read('word/document.xml').decode('utf-8')
                
                # Find hyperlink content
                hyperlink_pattern = re.compile(
                    r'<w:hyperlink[^>]*>(.+?)</w:hyperlink>',
                    re.DOTALL
                )
                
                for match in hyperlink_pattern.finditer(xml_content):
                    content = match.group(1)
                    # Extract text from this hyperlink
                    text_matches = re.findall(r'<w:t[^>]*>([^<]+)</w:t>', content)
                    full_text = ''.join(text_matches).strip()
                    if full_text:
                        hyperlinked.add(full_text)
                        # Also add individual words
                        for word in full_text.split():
                            hyperlinked.add(word)
        
        except Exception as e:
            _log(f"Hyperlink extraction error: {e}")
        
        return hyperlinked
    
    def _should_flag(self, acronym: str, info: AcronymInfo) -> bool:
        """Determine if this acronym should be flagged as undefined."""
        
        # No usage - don't flag
        if info.usage_count == 0:
            return False
        
        # Universal skip
        if acronym in self.UNIVERSAL_SKIP:
            return False
        
        # Common caps words
        if acronym in self.COMMON_CAPS_SKIP:
            return False
        
        # Already defined
        if info.is_defined or acronym in self._defined:
            return False
        
        # Check if this is a compound acronym where all parts are defined
        # e.g., "LRSP/AOP" should be OK if both LRSP and AOP are defined
        if '/' in acronym:
            parts = acronym.split('/')
            all_parts_defined = all(
                part in self._defined or part in self.UNIVERSAL_SKIP
                for part in parts if len(part) >= 2
            )
            if all_parts_defined:
                _log(f"Compound OK: {acronym} (all parts defined)")
                return False
        
        # Check if part of a compound defined acronym
        for defined in self._defined:
            if len(defined) > len(acronym) and acronym in defined:
                return False
        
        # Roman numerals
        if re.match(r'^[IVXLCDM]+$', acronym):
            return False
        
        # Mostly numbers (like F-123)
        digits = sum(1 for c in acronym if c.isdigit())
        if digits > len(acronym) / 2:
            return False
        
        return True
    
    def _should_flag_with_metrics(self, acronym: str, info: AcronymInfo) -> bool:
        """Determine if this acronym should be flagged, respecting strict mode.
        
        v3.0.33: This version handles UNIVERSAL_SKIP separately based on strict mode.
        The UNIVERSAL_SKIP check is done in the main check() method to enable metrics.
        """
        
        # No usage - don't flag
        if info.usage_count == 0:
            return False
        
        # Common caps words - these are NEVER acronyms (SECTION, NOTE, etc.)
        # This is NOT affected by strict mode
        if acronym in self.COMMON_CAPS_SKIP:
            return False
        
        # v3.0.93: Skip document identifiers (reference numbers, not acronyms)
        # Patterns: FHWA-JPO-21, NASA-STD8719, ISO/IEC/IEEE, EEE-INST-002, GSFC/S312-P
        if self._is_document_identifier(acronym):
            return False
        
        # NOTE: UNIVERSAL_SKIP is handled in check() method based on strict mode
        # If we got here, either:
        # - strict mode is ON (ignore_common_acronyms=False), or
        # - the acronym wasn't in UNIVERSAL_SKIP
        
        # Already defined in document
        if info.is_defined or acronym in self._defined:
            return False
        
        # Check if this is a compound acronym where all parts are defined
        # e.g., "LRSP/AOP" should be OK if both LRSP and AOP are defined
        if '/' in acronym:
            parts = acronym.split('/')
            all_parts_defined = all(
                part in self._defined or (self._ignore_common_acronyms and part in self.UNIVERSAL_SKIP)
                for part in parts if len(part) >= 2
            )
            if all_parts_defined:
                _log(f"Compound OK: {acronym} (all parts defined)")
                return False
        
        # Check if part of a compound defined acronym
        for defined in self._defined:
            if len(defined) > len(acronym) and acronym in defined:
                return False
        
        # Roman numerals
        if re.match(r'^[IVXLCDM]+$', acronym):
            return False
        
        # Mostly numbers (like F-123)
        digits = sum(1 for c in acronym if c.isdigit())
        if digits > len(acronym) / 2:
            return False
        
        return True
    
    def _is_document_identifier(self, text: str) -> bool:
        """Check if text is a document identifier (not an acronym needing definition).
        
        v3.0.93: Document identifiers are reference numbers like:
        - FHWA-JPO-21 (agency-office-number)
        - NASA-STD8719, MIL-STD-498 (standards)
        - ISO/IEC/IEEE (standards org combinations)
        - EEE-INST-002 (specification numbers)
        - GSFC/S312-P (center/document codes)
        - NPR 7123.1A (procedural requirements)
        - CONOPS-FINAL, REPORT-DRAFT (document status suffixes)
        - IEST-STD, NASA-STD (standards prefixes/suffixes)
        """
        # Pattern: Contains hyphen with numbers (FHWA-JPO-21, EEE-INST-002)
        if '-' in text and re.search(r'\d', text):
            return True
        
        # Pattern: Standards notation (STD, INST, SPEC followed by or preceded by hyphen)
        if re.search(r'[-/](STD|INST|SPEC|REV|VER)(?:[-/]|$)', text, re.IGNORECASE):
            return True
        if re.search(r'^(STD|INST|SPEC)[-/]', text, re.IGNORECASE):
            return True
        if re.search(r'(STD|INST|SPEC|REV|VER)\d', text, re.IGNORECASE):
            return True
        
        # Pattern: Document status suffixes (CONOPS-FINAL, REPORT-DRAFT, etc.)
        status_suffixes = {'FINAL', 'DRAFT', 'APPROVED', 'PENDING', 'REVIEW', 
                          'PRELIMINARY', 'INTERIM', 'REVISED', 'UPDATED', 'CURRENT'}
        if '-' in text:
            parts = text.split('-')
            if parts[-1] in status_suffixes or parts[0] in status_suffixes:
                return True
            # Compound document identifiers (SCC-B-CVE, STN-CTN, CVE-TPI, etc.)
            if len(parts) >= 3:
                return True
            # Two-part compound identifiers where both parts are acronym-like (3+ chars)
            if len(parts) == 2 and all(len(p) >= 3 and p.isupper() for p in parts):
                return True
            # Policy terms like ALLOW-BY, DENY-BY, etc.
            policy_words = {'ALLOW', 'DENY', 'BASED', 'ONLY', 'ALL', 'ANY', 'DEFAULT'}
            if len(parts) == 2 and (parts[0] in policy_words or parts[1] in policy_words):
                return True
        
        # Pattern: Standards org combination (ISO/IEC, ISO/IEC/IEEE)
        if '/' in text:
            parts = text.split('/')
            # If all parts are known standards orgs or short codes
            standards_orgs = {'ISO', 'IEC', 'IEEE', 'ANSI', 'SAE', 'ASTM', 'MIL', 'NASA', 'ESA', 'GSFC'}
            if all(p in standards_orgs or len(p) <= 4 for p in parts):
                return True
            # If contains document-like codes (letters followed by numbers)
            if any(re.match(r'^[A-Z]+\d+', p) for p in parts):
                return True
            # If has many parts (FEMAP/TCON, MMTPA/CPA)
            if len(parts) >= 2 and all(len(p) >= 2 for p in parts):
                return True
        
        # Pattern: Agency document codes with slashes (GSFC/S312-P)
        if re.match(r'^[A-Z]+/[A-Z]*\d+', text):
            return True
        
        # Pattern: Version/revision suffix (ends with -A, -B, etc. or .1, .2)
        if re.match(r'^[A-Z]+-[A-Z]$', text) or re.search(r'\.\d+[A-Z]?$', text):
            return True
        
        # Pattern: Very long ALL CAPS (>10 chars) without digits - likely product names or regular words
        # e.g., SIDEWALKSIM (11), ARCHITECTURE (12) - these should be in COMMON_CAPS_SKIP or are product names
        if len(text) > 10 and text.isupper() and not any(c.isdigit() for c in text) and '-' not in text and '/' not in text:
            return True
        
        # v3.0.93: Detect word fragments from PDF extraction artifacts
        # These are partial words that were broken due to PDF formatting (e.g., "ORGANIZA TION" -> "ORGANIZA")
        # Common fragment patterns:
        # - Ends in unusual consonant clusters that wouldn't be valid acronyms (LABORA, PENDIC)
        # - Very short fragments that look like word endings (NTIFY, TION, TORY)
        fragment_endings = (
            'IZA', 'ORA', 'DIC', 'MEN', 'TIF', 'ULA', 'ILA', 'OPE',
            'ARA', 'ORI', 'ULA', 'ANI', 'IFI', 'ABI', 'IBI', 'UBI',
            'ERA', 'ORA', 'URA', 'ARA', 'IRA',
        )
        fragment_starts = (
            'NTIF', 'TION', 'TORY', 'MENT', 'NESS', 'IBLE', 'ABLE',
            'IZED', 'IZED', 'ATED', 'LING', 'MING', 'NING', 'RING',
            'TEME', 'EMEN',  # fragments from STATEMENT, etc.
        )
        if len(text) >= 3 and len(text) <= 6:
            # Short fragments
            if text.endswith(fragment_endings) or text.startswith(fragment_starts):
                return True
        if len(text) >= 5 and len(text) <= 8:
            # Medium fragments - check if looks like partial word
            if text.endswith(('IZA', 'ORA', 'ULA', 'MEN', 'DIC', 'ABI', 'IBI')):
                return True
        
        return False
    
    def safe_check(self, *args, **kwargs) -> List['ReviewIssue']:
        """Safely run check with exception handling."""
        try:
            return self.check(*args, **kwargs)
        except Exception as e:
            self._errors.append(f"Safe check error: {e}")
            return []
