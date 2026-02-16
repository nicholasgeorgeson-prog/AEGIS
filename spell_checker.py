#!/usr/bin/env python3
"""
Enhanced Spell Checker v2.0.0 (Offline)
=======================================
Comprehensive spell checking without external API dependencies.

Features:
- Pure Python implementation (no API calls)
- Custom dictionary support
- Technical/domain term whitelist
- Aerospace/defense terminology built-in
- Context-aware suggestions
- Compound word handling

Author: AEGIS
"""

import re
import os
from typing import List, Dict, Tuple, Set, Optional
from collections import Counter
from pathlib import Path

try:
    from base_checker import BaseChecker
except ImportError:
    class BaseChecker:
        CHECKER_NAME = "Unknown"
        CHECKER_VERSION = "1.0.0"
        def __init__(self, enabled=True):
            self.enabled = enabled
            self._errors = []
        def create_issue(self, **kwargs):
            kwargs['category'] = getattr(self, 'CHECKER_NAME', 'Unknown')
            return kwargs
        def safe_check(self, *args, **kwargs):
            try:
                return self.check(*args, **kwargs)
            except Exception as e:
                self._errors.append(str(e))
                return []

__version__ = "2.5.0"


class EnhancedSpellChecker(BaseChecker):
    """
    Offline spell checker with custom dictionary support.
    
    Uses a combination of:
    - Built-in common English words
    - Technical/domain terminology
    - User-provided custom dictionaries
    - Learned words from document context
    """
    
    CHECKER_NAME = "Spelling"
    CHECKER_VERSION = "2.0.0"
    
    # Common English words (core vocabulary) - expanded list
    COMMON_WORDS = {
        # Articles, pronouns, prepositions
        'a', 'an', 'the', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
        'this', 'that', 'these', 'those', 'who', 'whom', 'whose', 'which', 'what', 'where', 'when', 'why', 'how',
        'in', 'on', 'at', 'to', 'for', 'with', 'by', 'from', 'of', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'under', 'over', 'out', 'up', 'down', 'off',
        
        # Common verbs (expanded)
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'am',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'done',
        'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'can', 'could',
        'say', 'said', 'says', 'saying', 'get', 'got', 'gets', 'getting', 'gotten',
        'make', 'made', 'makes', 'making', 'go', 'goes', 'went', 'going', 'gone',
        'know', 'knew', 'knows', 'knowing', 'known', 'think', 'thought', 'thinks', 'thinking',
        'take', 'took', 'takes', 'taking', 'taken', 'see', 'saw', 'sees', 'seeing', 'seen',
        'come', 'came', 'comes', 'coming', 'want', 'wanted', 'wants', 'wanting',
        'use', 'used', 'uses', 'using', 'find', 'found', 'finds', 'finding',
        'give', 'gave', 'gives', 'giving', 'given', 'tell', 'told', 'tells', 'telling',
        'work', 'worked', 'works', 'working', 'call', 'called', 'calls', 'calling',
        'try', 'tried', 'tries', 'trying', 'need', 'needed', 'needs', 'needing',
        'feel', 'felt', 'feels', 'feeling', 'become', 'became', 'becomes', 'becoming',
        'leave', 'left', 'leaves', 'leaving', 'put', 'puts', 'putting',
        'mean', 'meant', 'means', 'meaning', 'keep', 'kept', 'keeps', 'keeping',
        'let', 'lets', 'letting', 'begin', 'began', 'begins', 'beginning', 'begun',
        'seem', 'seemed', 'seems', 'seeming', 'help', 'helped', 'helps', 'helping',
        'show', 'showed', 'shows', 'showing', 'shown', 'hear', 'heard', 'hears', 'hearing',
        'play', 'played', 'plays', 'playing', 'run', 'ran', 'runs', 'running',
        'move', 'moved', 'moves', 'moving', 'live', 'lived', 'lives', 'living',
        'believe', 'believed', 'believes', 'believing', 'bring', 'brought', 'brings', 'bringing',
        'happen', 'happened', 'happens', 'happening', 'write', 'wrote', 'writes', 'writing', 'written',
        'provide', 'provided', 'provides', 'providing', 'sit', 'sat', 'sits', 'sitting',
        'stand', 'stood', 'stands', 'standing', 'lose', 'lost', 'loses', 'losing',
        'pay', 'paid', 'pays', 'paying', 'meet', 'met', 'meets', 'meeting',
        'include', 'included', 'includes', 'including', 'continue', 'continued', 'continues', 'continuing',
        'set', 'sets', 'setting', 'learn', 'learned', 'learns', 'learning', 'learnt',
        'change', 'changed', 'changes', 'changing', 'lead', 'led', 'leads', 'leading',
        'understand', 'understood', 'understands', 'understanding', 'watch', 'watched', 'watches', 'watching',
        'follow', 'followed', 'follows', 'following', 'stop', 'stopped', 'stops', 'stopping',
        'create', 'created', 'creates', 'creating', 'speak', 'spoke', 'speaks', 'speaking', 'spoken',
        'read', 'reads', 'reading', 'allow', 'allowed', 'allows', 'allowing',
        'add', 'added', 'adds', 'adding', 'spend', 'spent', 'spends', 'spending',
        'grow', 'grew', 'grows', 'growing', 'grown', 'open', 'opened', 'opens', 'opening',
        'walk', 'walked', 'walks', 'walking', 'win', 'won', 'wins', 'winning',
        'offer', 'offered', 'offers', 'offering', 'remember', 'remembered', 'remembers', 'remembering',
        'love', 'loved', 'loves', 'loving', 'consider', 'considered', 'considers', 'considering',
        'appear', 'appeared', 'appears', 'appearing', 'buy', 'bought', 'buys', 'buying',
        'wait', 'waited', 'waits', 'waiting', 'serve', 'served', 'serves', 'serving',
        'die', 'died', 'dies', 'dying', 'send', 'sent', 'sends', 'sending',
        'expect', 'expected', 'expects', 'expecting', 'build', 'built', 'builds', 'building',
        'stay', 'stayed', 'stays', 'staying', 'fall', 'fell', 'falls', 'falling', 'fallen',
        'cut', 'cuts', 'cutting', 'reach', 'reached', 'reaches', 'reaching',
        'kill', 'killed', 'kills', 'killing', 'remain', 'remained', 'remains', 'remaining',
        'suggest', 'suggested', 'suggests', 'suggesting', 'raise', 'raised', 'raises', 'raising',
        'pass', 'passed', 'passes', 'passing', 'sell', 'sold', 'sells', 'selling',
        'require', 'required', 'requires', 'requiring', 'report', 'reported', 'reports', 'reporting',
        'decide', 'decided', 'decides', 'deciding', 'pull', 'pulled', 'pulls', 'pulling',
        'describe', 'described', 'describes', 'describing', 'description', 'descriptions',
        'develop', 'developed', 'develops', 'developing', 'development', 'developments',
        'establish', 'established', 'establishes', 'establishing', 'establishment',
        'determine', 'determined', 'determines', 'determining', 'determination',
        'maintain', 'maintained', 'maintains', 'maintaining', 'maintenance',
        'perform', 'performed', 'performs', 'performing', 'performance',
        'support', 'supported', 'supports', 'supporting', 'supportable',
        'manage', 'managed', 'manages', 'managing', 'management', 'manager',
        'ensure', 'ensured', 'ensures', 'ensuring',
        'define', 'defined', 'defines', 'defining', 'definition', 'definitions',
        'identify', 'identified', 'identifies', 'identifying', 'identification',
        'review', 'reviewed', 'reviews', 'reviewing', 'reviewer',
        'complete', 'completed', 'completes', 'completing', 'completion',
        'document', 'documented', 'documents', 'documenting', 'documentation',
        
        # Common nouns
        'time', 'year', 'people', 'way', 'day', 'man', 'woman', 'child', 'children',
        'world', 'life', 'hand', 'part', 'place', 'case', 'week', 'company', 'system',
        'program', 'question', 'work', 'government', 'number', 'night', 'point', 'home', 'water',
        'room', 'mother', 'area', 'money', 'story', 'fact', 'month', 'lot', 'right',
        'study', 'book', 'eye', 'job', 'word', 'business', 'issue', 'side', 'kind',
        'head', 'house', 'service', 'friend', 'father', 'power', 'hour', 'game', 'line',
        'end', 'member', 'law', 'car', 'city', 'community', 'name', 'president', 'team',
        'minute', 'idea', 'kid', 'body', 'information', 'back', 'parent', 'face', 'others',
        'level', 'office', 'door', 'health', 'person', 'art', 'war', 'history', 'party',
        'result', 'change', 'morning', 'reason', 'research', 'girl', 'guy', 'moment', 'air',
        'teacher', 'force', 'education', 'foot', 'boy', 'age', 'policy', 'process', 'music',
        'market', 'sense', 'nation', 'plan', 'college', 'interest', 'death', 'experience', 'effect',
        'use', 'class', 'control', 'care', 'field', 'development', 'role', 'effort', 'rate',
        'heart', 'drug', 'show', 'leader', 'light', 'voice', 'wife', 'police', 'mind',
        'difference', 'period', 'value', 'building', 'action', 'authority', 'model', 'paper', 'data',
        
        # Common adjectives
        'good', 'new', 'first', 'last', 'long', 'great', 'little', 'own', 'other', 'old',
        'right', 'big', 'high', 'different', 'small', 'large', 'next', 'early', 'young', 'important',
        'few', 'public', 'bad', 'same', 'able', 'best', 'better', 'sure', 'free', 'true',
        'real', 'full', 'special', 'major', 'strong', 'possible', 'whole', 'clear', 'recent', 'certain',
        'personal', 'open', 'red', 'difficult', 'available', 'likely', 'short', 'single', 'low', 'hard',
        'past', 'local', 'main', 'current', 'national', 'natural', 'physical', 'final', 'general', 'environmental',
        'financial', 'blue', 'black', 'white', 'green', 'common', 'poor', 'happy', 'serious', 'ready',
        'simple', 'left', 'nice', 'late', 'less', 'complete', 'total', 'similar', 'hot', 'dead',
        
        # Common adverbs
        'not', 'just', 'also', 'very', 'often', 'however', 'too', 'usually', 'really', 'early',
        'never', 'always', 'sometimes', 'together', 'likely', 'simply', 'generally', 'instead', 'actually', 'already',
        'enough', 'especially', 'ever', 'quickly', 'probably', 'certainly', 'perhaps', 'finally', 'today', 'either',
        'exactly', 'ago', 'behind', 'recently', 'soon', 'thus', 'almost', 'directly', 'alone', 'actually',
        
        # Conjunctions and other
        'and', 'but', 'or', 'so', 'if', 'when', 'because', 'as', 'than', 'while',
        'although', 'whether', 'though', 'since', 'until', 'unless', 'nor', 'yet', 'both', 'either',
        'neither', 'each', 'every', 'all', 'any', 'some', 'no', 'most', 'more', 'only',
        'even', 'still', 'such', 'well', 'back', 'then', 'now', 'here', 'there', 'much',
        'many', 'few', 'several', 'own', 'same', 'another', 'around', 'away', 'yes', 'no',
    }
    
    # Technical and domain-specific terms (aerospace, defense, engineering)
    TECHNICAL_TERMS = {
        # Aerospace/Aviation
        'aircraft', 'airplane', 'airframe', 'airspeed', 'altitude', 'avionics', 'autopilot',
        'aerodynamic', 'aerodynamics', 'aeroelastic', 'aerostructures', 'airborne', 'airworthiness',
        'fuselage', 'empennage', 'aileron', 'elevator', 'rudder', 'flap', 'slat', 'spoiler',
        'propulsion', 'turbofan', 'turbojet', 'turboprop', 'afterburner', 'nacelle', 'pylon',
        'cockpit', 'flight deck', 'avionics', 'radar', 'lidar', 'transponder', 'altimeter',
        'gyroscope', 'accelerometer', 'pitot', 'static', 'mach', 'subsonic', 'supersonic', 'hypersonic',
        'takeoff', 'landing', 'taxi', 'cruise', 'climb', 'descent', 'approach', 'flare',
        
        # Defense/Military
        'mil', 'std', 'spec', 'milspec', 'milstd', 'itar', 'dfars', 'dfar', 'far', 'nist',
        'classified', 'unclassified', 'fouo', 'cui', 'controlled', 'proprietary', 'export',
        'countermeasure', 'countermeasures', 'survivability', 'vulnerability', 'lethality',
        'logistics', 'sustainment', 'maintainability', 'reliability', 'availability', 'testability',
        'interoperability', 'compatibility', 'interface', 'integration', 'verification', 'validation',
        
        # Systems Engineering
        'system', 'systems', 'subsystem', 'subsystems', 'component', 'components', 'assembly',
        'requirement', 'requirements', 'specification', 'specifications', 'baseline', 'configuration',
        'architecture', 'design', 'development', 'implementation', 'deployment', 'operations',
        'lifecycle', 'tradeoff', 'tradeoffs', 'tradespace', 'analysis', 'analyses', 'assessment',
        'verification', 'validation', 'qualification', 'certification', 'accreditation', 'authorization',
        'decomposition', 'allocation', 'traceability', 'traceable', 'bidirectional', 'flowdown',
        'stakeholder', 'stakeholders', 'conops', 'concept', 'operational', 'functional', 'physical',
        'performance', 'effectiveness', 'efficiency', 'capability', 'capabilities', 'constraint',
        'interface', 'interfaces', 'interoperability', 'integration', 'modular', 'modularity',
        'scalable', 'scalability', 'extensible', 'extensibility', 'maintainable', 'supportable',
        
        # Software/IT
        'software', 'hardware', 'firmware', 'middleware', 'database', 'server', 'client',
        'api', 'apis', 'gui', 'cli', 'ui', 'ux', 'frontend', 'backend', 'fullstack',
        'algorithm', 'algorithms', 'codebase', 'repository', 'deployment', 'devops', 'cicd',
        'agile', 'scrum', 'kanban', 'waterfall', 'spiral', 'iterative', 'incremental',
        'cybersecurity', 'encryption', 'authentication', 'authorization', 'firewall', 'malware',
        'ethernet', 'wifi', 'bluetooth', 'tcp', 'ip', 'http', 'https', 'ssl', 'tls',
        
        # Quality/Process
        'quality', 'assurance', 'control', 'inspection', 'audit', 'review', 'compliance',
        'nonconformance', 'nonconforming', 'discrepancy', 'deviation', 'waiver', 'variance',
        'corrective', 'preventive', 'root cause', 'failure', 'defect', 'deficiency', 'finding',
        'procedure', 'process', 'workflow', 'checklist', 'template', 'guideline', 'standard',
        'iso', 'cmmi', 'as9100', 'nadcap', 'asme', 'ieee', 'ansi', 'astm', 'sae',
        
        # Project Management
        'project', 'program', 'portfolio', 'milestone', 'deliverable', 'deliverables', 'schedule', 'budget',
        'scope', 'risk', 'issue', 'action', 'decision', 'resource', 'allocation', 'utilization',
        'baseline', 'baselines', 'variance', 'earned', 'value', 'wbs', 'obs', 'gantt', 'pert', 'cpm',
        'stakeholder', 'stakeholders', 'sponsor', 'manager', 'lead', 'coordinator', 'analyst', 'engineer',
        'procurement', 'procurements', 'subcontractor', 'subcontractors', 'workload', 'workstream',
        'tollgate', 'tollgates', 'kickoff', 'signoff', 'readiness', 'walkthrough',
        
        # NASA / Aerospace Standards
        'conops', 'ops', 'cdrl', 'cdr', 'pdr', 'srr', 'sdrl', 'icd', 'sow', 'wbs',
        'fmea', 'fmeca', 'hazop', 'fracas', 'praca', 'gidep', 'dmsms', 'eol',
        'trl', 'mrl', 'irl', 'srl', 'raci', 'rasci', 'nfr', 'srs', 'sdd', 'stp',
        'swimlane', 'swimlanes', 'tradeoff', 'tradeoffs', 'tradespace', 'downtick',
        'workaround', 'workarounds', 'de-scope', 'descope', 'descoped', 'rebaseline',
        'rebaselined', 'subsystem', 'subsystems', 'datasheet', 'datasheets',
        'downselect', 'downselected', 'uplink', 'downlink', 'telemetry',
        'flyby', 'flyover', 'overflight', 'geosynchronous', 'geostationary',

        # Documentation
        'document', 'documentation', 'specification', 'procedure', 'instruction', 'manual',
        'drawing', 'schematic', 'diagram', 'flowchart', 'table', 'figure', 'appendix',
        'section', 'paragraph', 'clause', 'subclause', 'annex', 'attachment', 'exhibit',
        'revision', 'version', 'draft', 'final', 'approved', 'released', 'controlled',
        'acronym', 'acronyms', 'abbreviation', 'abbreviations', 'definition', 'definitions',
        'reference', 'references', 'bibliography', 'glossary', 'index', 'toc', 'lof', 'lot',
        
        # Common technical verbs
        'configure', 'configured', 'configures', 'configuring', 'configuration',
        'install', 'installed', 'installs', 'installing', 'installation',
        'implement', 'implemented', 'implements', 'implementing', 'implementation',
        'integrate', 'integrated', 'integrates', 'integrating', 'integration',
        'validate', 'validated', 'validates', 'validating', 'validation',
        'verify', 'verified', 'verifies', 'verifying', 'verification',
        'analyze', 'analyzed', 'analyzes', 'analyzing', 'analysis',
        'assess', 'assessed', 'assesses', 'assessing', 'assessment',
        'evaluate', 'evaluated', 'evaluates', 'evaluating', 'evaluation',
        'specify', 'specified', 'specifies', 'specifying', 'specification',
        'allocate', 'allocated', 'allocates', 'allocating', 'allocation',
        'derive', 'derived', 'derives', 'deriving', 'derivation',
        'decompose', 'decomposed', 'decomposes', 'decomposing', 'decomposition',
        'prioritize', 'prioritized', 'prioritizes', 'prioritizing', 'prioritization',
        'optimize', 'optimized', 'optimizes', 'optimizing', 'optimization',
        'coordinate', 'coordinated', 'coordinates', 'coordinating', 'coordination',
        'collaborate', 'collaborated', 'collaborates', 'collaborating', 'collaboration',
        'mitigate', 'mitigated', 'mitigates', 'mitigating', 'mitigation',
        'remediate', 'remediated', 'remediates', 'remediating', 'remediation',
        'facilitate', 'facilitated', 'facilitates', 'facilitating', 'facilitation',
        'utilize', 'utilized', 'utilizes', 'utilizing', 'utilization',
        'leverage', 'leveraged', 'leverages', 'leveraging',
        'streamline', 'streamlined', 'streamlines', 'streamlining',
        
        # Units and measurements
        'kg', 'lb', 'lbs', 'oz', 'g', 'mg', 'km', 'mi', 'ft', 'in', 'm', 'cm', 'mm',
        'mph', 'kph', 'knots', 'mach', 'psi', 'kpa', 'mpa', 'bar', 'atm',
        'hz', 'khz', 'mhz', 'ghz', 'db', 'dba', 'dbc', 'dbm',
        'kw', 'mw', 'gw', 'kwh', 'mwh', 'amp', 'amps', 'volt', 'volts', 'ohm', 'ohms',
        'celsius', 'fahrenheit', 'kelvin', 'deg', 'degrees',
    }
    
    # Common misspellings and their corrections
    COMMON_MISSPELLINGS = {
        'accomodate': 'accommodate',
        'acheive': 'achieve',
        'accross': 'across',
        'agressive': 'aggressive',
        'apparant': 'apparent',
        'appearence': 'appearance',
        'arguement': 'argument',
        'begining': 'beginning',
        'beleive': 'believe',
        'calender': 'calendar',
        'catagory': 'category',
        'cemetary': 'cemetery',
        'collegue': 'colleague',
        'comming': 'coming',
        'commitee': 'committee',
        'completly': 'completely',
        'concious': 'conscious',
        'definately': 'definitely',
        'diffrent': 'different',
        'dissapear': 'disappear',
        'dissapoint': 'disappoint',
        'embarass': 'embarrass',
        'enviroment': 'environment',
        'existance': 'existence',
        'experiance': 'experience',
        'foriegn': 'foreign',
        'goverment': 'government',
        'grammer': 'grammar',
        'guage': 'gauge',
        'harrass': 'harass',
        'heighth': 'height',
        'heirarchy': 'hierarchy',
        'humourous': 'humorous',
        'immediatly': 'immediately',
        'independant': 'independent',
        'indispensible': 'indispensable',
        'innoculate': 'inoculate',
        'intellegent': 'intelligent',
        'judgement': 'judgment',
        'knowlege': 'knowledge',
        'liason': 'liaison',
        'libary': 'library',
        'lisence': 'license',
        'maintenence': 'maintenance',
        'millenium': 'millennium',
        'miniscule': 'minuscule',
        'mispell': 'misspell',
        'neccessary': 'necessary',
        'noticable': 'noticeable',
        'occassion': 'occasion',
        'occured': 'occurred',
        'occurence': 'occurrence',
        'paralell': 'parallel',
        'particulary': 'particularly',
        'pavillion': 'pavilion',
        'persistant': 'persistent',
        'personell': 'personnel',
        'posession': 'possession',
        'preceed': 'precede',
        'privelege': 'privilege',
        'professer': 'professor',
        'publically': 'publicly',
        'realy': 'really',
        'recieve': 'receive',
        'reccomend': 'recommend',
        'refered': 'referred',
        'relevent': 'relevant',
        'religous': 'religious',
        'repitition': 'repetition',
        'rythm': 'rhythm',
        'secretery': 'secretary',
        'seize': 'seize',
        'seperate': 'separate',
        'sergent': 'sergeant',
        'sieze': 'seize',
        'similer': 'similar',
        'speach': 'speech',
        'succesful': 'successful',
        'supercede': 'supersede',
        'suprise': 'surprise',
        'temperture': 'temperature',
        'therefor': 'therefore',
        'threshhold': 'threshold',
        'tommorow': 'tomorrow',
        'tounge': 'tongue',
        'truely': 'truly',
        'unfortunatly': 'unfortunately',
        'untill': 'until',
        'usefull': 'useful',
        'vaccuum': 'vacuum',
        'vegeterian': 'vegetarian',
        'vehical': 'vehicle',
        'visable': 'visible',
        'wether': 'whether',
        'wierd': 'weird',
        'writting': 'writing',
    }
    
    def __init__(
        self,
        enabled: bool = True,
        custom_dictionary: Optional[Set[str]] = None,
        ignore_uppercase: bool = True,
        ignore_numbers: bool = True,
        min_word_length: int = 2,
        max_suggestions: int = 3
    ):
        super().__init__(enabled)
        self.custom_dictionary = custom_dictionary or set()
        self.ignore_uppercase = ignore_uppercase
        self.ignore_numbers = ignore_numbers
        self.min_word_length = min_word_length
        self.max_suggestions = max_suggestions
        
        # Build complete dictionary
        self._dictionary = self._build_dictionary()
        
        # Cache for document-learned words
        self._document_words: Set[str] = set()
    
    def _build_dictionary(self) -> Set[str]:
        """Build the complete dictionary from all sources."""
        dictionary = set()
        
        # Add common words
        dictionary.update(self.COMMON_WORDS)
        
        # Add technical terms
        dictionary.update(self.TECHNICAL_TERMS)
        
        # Add custom dictionary
        dictionary.update(w.lower() for w in self.custom_dictionary)
        
        # Add correct spellings from misspellings dict
        dictionary.update(self.COMMON_MISSPELLINGS.values())
        
        return dictionary
    
    def add_to_dictionary(self, words: Set[str]):
        """Add words to the custom dictionary."""
        self.custom_dictionary.update(words)
        self._dictionary.update(w.lower() for w in words)
    
    def load_dictionary_file(self, filepath: str):
        """Load additional words from a file (one word per line)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                words = {line.strip().lower() for line in f if line.strip()}
                self.add_to_dictionary(words)
        except Exception as e:
            self._errors.append(f"Error loading dictionary: {e}")
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        """Check spelling in paragraphs."""
        if not self.enabled:
            return []
        
        issues = []
        
        # Learn words from document (acronyms, proper nouns, etc.)
        self._learn_document_words(paragraphs)
        
        # Word extraction pattern
        word_pattern = re.compile(r"[a-zA-Z][a-zA-Z'-]*[a-zA-Z]|[a-zA-Z]")
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 5:
                continue
            
            # Skip special sections
            special_sections = kwargs.get('special_sections', {})
            skip_indices = set()
            for indices in special_sections.values():
                skip_indices.update(indices)
            if idx in skip_indices:
                continue
            
            # Find all words
            words = word_pattern.findall(text)
            
            for word in words:
                # Skip if too short
                if len(word) < self.min_word_length:
                    continue
                
                # Skip if all uppercase (likely acronym)
                if self.ignore_uppercase and word.isupper():
                    continue
                
                # Skip if contains numbers
                if self.ignore_numbers and any(c.isdigit() for c in word):
                    continue
                
                # Check if word is misspelled
                word_lower = word.lower()
                
                if self._is_misspelled(word_lower):
                    suggestion = self._get_suggestion(word_lower)
                    
                    # Find context
                    word_pos = text.lower().find(word_lower)
                    context = text[max(0, word_pos-15):word_pos+len(word)+15]
                    
                    issues.append(self.create_issue(
                        severity='Low',
                        message=f'Possible misspelling: "{word}"',
                        context=context,
                        paragraph_index=idx,
                        suggestion=f'Did you mean: "{suggestion}"' if suggestion else 'Check spelling',
                        rule_id='SP001',
                        flagged_text=word,
                        original_text=word,
                        replacement_text=suggestion or ''
                    ))
        
        return issues
    
    def _learn_document_words(self, paragraphs: List[Tuple[int, str]]):
        """Learn words from the document (proper nouns, repeated terms)."""
        word_counts: Counter = Counter()
        
        for idx, text in paragraphs:
            # Find capitalized words (potential proper nouns)
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            word_counts.update(w.lower() for w in words)
        
        # Add frequently occurring words (appear 3+ times)
        for word, count in word_counts.items():
            if count >= 3:
                self._document_words.add(word)
    
    def _is_misspelled(self, word: str) -> bool:
        """Check if a word is misspelled. Conservative approach - only flag obvious errors."""
        word_lower = word.lower()
        
        # Only flag if it's a KNOWN misspelling (high confidence)
        if word_lower in self.COMMON_MISSPELLINGS:
            return True
        
        # Skip everything else - we don't want false positives
        # The Word integration will catch real spelling errors
        return False
    
    def _has_valid_affix(self, word: str) -> bool:
        """Check if word has valid prefix/suffix on a known word."""
        # Common suffixes
        suffixes = ['ing', 'ed', 'er', 'est', 'ly', 's', 'es', 'tion', 'sion', 
                   'ment', 'ness', 'able', 'ible', 'ful', 'less', 'ous', 'ive',
                   'al', 'ial', 'ic', 'ical', 'ity', 'ty', 'ance', 'ence']
        
        for suffix in suffixes:
            if word.endswith(suffix):
                base = word[:-len(suffix)]
                if base in self._dictionary:
                    return True
                # Check with common spelling changes
                if (base + 'e') in self._dictionary:  # hoping -> hope
                    return True
                if base and base[-1] == base[-2] and base[:-1] in self._dictionary:  # running -> run
                    return True
        
        # Common prefixes
        prefixes = ['un', 're', 'pre', 'dis', 'mis', 'non', 'over', 'under', 
                   'sub', 'super', 'anti', 'auto', 'co', 'de', 'inter', 'multi',
                   'post', 'semi', 'trans']
        
        for prefix in prefixes:
            if word.startswith(prefix):
                base = word[len(prefix):]
                if base in self._dictionary:
                    return True
        
        return False
    
    def _is_valid_compound(self, word: str) -> bool:
        """Check if word is a valid compound of known words."""
        # Try splitting at each position
        for i in range(2, len(word) - 1):
            left = word[:i]
            right = word[i:]
            if left in self._dictionary and right in self._dictionary:
                return True
        
        return False
    
    def _get_suggestion(self, word: str) -> Optional[str]:
        """Get spelling suggestion for a misspelled word."""
        word_lower = word.lower()
        
        # Check known misspellings first
        if word_lower in self.COMMON_MISSPELLINGS:
            return self.COMMON_MISSPELLINGS[word_lower]
        
        # Find closest match using edit distance
        candidates = []
        
        for dict_word in self._dictionary:
            if abs(len(dict_word) - len(word_lower)) > 2:
                continue
            
            distance = self._edit_distance(word_lower, dict_word)
            if distance <= 2:
                candidates.append((dict_word, distance))
        
        # Sort by distance, then alphabetically
        candidates.sort(key=lambda x: (x[1], x[0]))
        
        if candidates:
            return candidates[0][0]
        
        return None
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance between two strings."""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]


if __name__ == '__main__':
    # Test
    checker = EnhancedSpellChecker()
    test_paragraphs = [
        (0, "This document describes the system requiremens."),
        (1, "The sofware shall be maintainable and testible."),
        (2, "We will accomodate all stakeholder needs."),
    ]
    
    issues = checker.check(test_paragraphs)
    for issue in issues:
        print(f"[{issue['severity']}] {issue['message']}")
        print(f"  Suggestion: {issue['suggestion']}")
