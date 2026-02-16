"""
Statement Forge Extractor
=========================
Extraction engine for requirement statements and work instructions from documents.

Ported from StatementForge v10.2 (core.py v5.9.6) to ensure extraction logic
is identical to the standalone tool.

v5.9.6 - Fixed: NOTEs between sub-steps attach to preceding sub-step, not main step
v5.9.5 - Fixed: Notes now included in CSV export description field
v5.9.4 - Fixed: Short non-action fragments (<50 chars) combined with previous statement
v5.9.3 - Fixed: Requirements SECTION_PATTERN allows leading whitespace (PDF support)
v5.9.2 - Removed directive type from requirements document title field (kept count)
v5.9.1 - Fixed: References/Appendix/Attachment content excluded from extraction
v5.9.0 - Fixed: Continuation step NOTES not skipped
v5.8.9 - Fixed: Inline lists after "the following:" split into separate statements
v5.8.8 - Fixed: "See..." references kept with parent statement, not split off
v5.8.7 - Fixed: NOTE content after abbreviations (U.S.) not incorrectly split
v5.8.6 - Fixed: NOTE handling improved - content stays together
v5.8.5 - Fixed: IF/THEN conditional tables combined into single statements
v5.8.4 - Fixed: Letters (a,b,c) used for split content to avoid conflicts with sub-steps

AEGIS Enhancements (preserved from original integration):
- F06: Shared extraction logic with role_extractor_v3
- F08: Expanded from 505 to 1000+ categorized action verbs
- v3.0.109: Multi-word directive phrases, expanded directive words, fallback extraction

Author: AEGIS
"""

import re
from typing import List, Tuple, Optional, Dict, Set
from collections import defaultdict

# v3.0.49: Support both package and flat import layouts
try:
    from statement_forge.models import Statement, DocumentType, DirectiveType
except ImportError:
    from statement_forge__models import Statement, DocumentType, DirectiveType


# =============================================================================
# TEXT CLEANING (ported from standalone core.py)
# =============================================================================

def clean_text(text: str) -> str:
    """Clean text by fixing common encoding issues and special characters."""
    if not text:
        return text

    # Fix common UTF-8 encoding issues (mojibake)
    # Order matters - longer patterns first
    replacements = [
        ('\u00e2\u0080\u0099', "'"),      # Right single quote
        ('\u00e2\u0080\u0098', "'"),      # Left single quote
        ('\u00e2\u0080\u009c', '"'),      # Left double quote
        ('\u00e2\u0080\u009d', '"'),      # Right double quote
        ('\u00e2\u0080\u0094', '-'),      # Em dash
        ('\u00e2\u0080\u0093', '-'),      # En dash
        ('\u00e2\u0080\u00a6', '...'),    # Ellipsis
        ('\u00e2\u0080\u00a2', '-'),      # Bullet
        ('\u00c3\u00a9', '\u00e9'),       # e acute
        ('\u00c3\u00a8', '\u00e8'),       # e grave
        ('\u00c3\u00b1', '\u00f1'),       # n tilde
        ('\u00a0', ' '),   # Non-breaking space
        ('\u2019', "'"),   # Right single quote
        ('\u2018', "'"),   # Left single quote
        ('\u201c', '"'),   # Left double quote
        ('\u201d', '"'),   # Right double quote
        ('\u2013', '-'),   # En dash
        ('\u2014', '-'),   # Em dash
        ('\u2026', '...'), # Ellipsis
        ('\u2022', '-'),   # Bullet
        ('\u00b7', '-'),   # Middle dot
        ('\ufffd', ' '),   # Replacement character
    ]

    for bad, good in replacements:
        text = text.replace(bad, good)

    return text


# =============================================================================
# ACTION VERBS (F08: Expanded to 1000+)
# =============================================================================

# Original 505 verbs (identical to standalone WorkInstructionExtractor.ACTION_VERBS)
ORIGINAL_ACTION_VERBS = {
    'accept', 'accomplish', 'achieve', 'acquire', 'act', 'adapt', 'add', 'address',
    'adjust', 'administer', 'advance', 'advise', 'advocate', 'affirm', 'allocate',
    'allow', 'analyze', 'announce', 'anticipate', 'apply', 'appoint', 'appraise',
    'approve', 'arrange', 'ascertain', 'assemble', 'assess', 'assign', 'assist',
    'assume', 'assure', 'attach', 'attain', 'attend', 'audit', 'authorize', 'avoid',
    'begin', 'brief', 'bring', 'build',
    'calculate', 'calibrate', 'capture', 'categorize', 'certify', 'chair', 'challenge',
    'change', 'check', 'clarify', 'classify', 'close', 'collaborate', 'collect',
    'combine', 'communicate', 'compare', 'compile', 'complete', 'comply', 'compose',
    'compute', 'conclude', 'conduct', 'confirm', 'connect', 'consider', 'consolidate',
    'construct', 'consult', 'contact', 'continue', 'contract', 'contribute', 'control',
    'convene', 'convert', 'coordinate', 'correct', 'correspond', 'counsel', 'create', 'critique',
    'decide', 'declare', 'decrease', 'define', 'delegate', 'delete', 'deliver',
    'demonstrate', 'deploy', 'describe', 'design', 'detail', 'detect', 'determine',
    'develop', 'devise', 'diagnose', 'direct', 'disassemble', 'disclose', 'discover',
    'discuss', 'dispatch', 'display', 'dispose', 'distribute', 'document', 'download', 'draft', 'drive',
    'edit', 'educate', 'effect', 'eliminate', 'emphasize', 'employ', 'enable',
    'encourage', 'end', 'endorse', 'enforce', 'engage', 'engineer', 'enhance',
    'ensure', 'enter', 'escalate', 'establish', 'estimate', 'evaluate', 'examine',
    'exceed', 'exchange', 'execute', 'exercise', 'exhibit', 'expand', 'expedite',
    'explain', 'explore', 'export', 'express', 'extend', 'extract',
    'facilitate', 'find', 'finalize', 'fix', 'focus', 'follow', 'forecast',
    'formalize', 'format', 'formulate', 'forward', 'foster', 'fulfill', 'fund', 'furnish',
    'gain', 'gather', 'generate', 'govern', 'grade', 'grant', 'guide',
    'halt', 'handle', 'head', 'help', 'highlight', 'hire', 'host',
    'identify', 'illustrate', 'implement', 'import', 'improve', 'include',
    'incorporate', 'increase', 'indicate', 'influence', 'inform', 'initiate',
    'innovate', 'input', 'inspect', 'install', 'institute', 'instruct', 'integrate',
    'interact', 'interface', 'interpret', 'intervene', 'interview', 'introduce',
    'inventory', 'investigate', 'invoice', 'involve', 'isolate', 'issue',
    'join', 'judge', 'justify',
    'keep',
    'label', 'launch', 'lead', 'learn', 'leverage', 'liaise', 'license', 'limit',
    'link', 'list', 'listen', 'load', 'locate', 'log',
    'maintain', 'make', 'manage', 'manipulate', 'map', 'market', 'master', 'match',
    'measure', 'mediate', 'meet', 'mentor', 'merge', 'migrate', 'minimize', 'mobilize',
    'model', 'moderate', 'modify', 'monitor', 'motivate', 'move',
    'name', 'navigate', 'negotiate', 'nominate', 'normalize', 'note', 'notify', 'number',
    'observe', 'obtain', 'offer', 'onboard', 'open', 'operate', 'optimize',
    'orchestrate', 'order', 'organize', 'orient', 'originate', 'outline', 'output',
    'outsource', 'overcome', 'oversee', 'own',
    'package', 'participate', 'partner', 'pass', 'pay', 'perceive', 'perform',
    'permit', 'persuade', 'pilot', 'pioneer', 'place', 'plan', 'position', 'post',
    'practice', 'predict', 'prepare', 'prescribe', 'present', 'preserve', 'preside',
    'prevent', 'print', 'prioritize', 'probe', 'process', 'procure', 'produce',
    'program', 'progress', 'project', 'promote', 'prompt', 'propose', 'protect',
    'provide', 'publicize', 'publish', 'purchase', 'pursue',
    'qualify', 'quantify', 'query', 'question',
    'raise', 'rank', 'rate', 'reach', 'read', 'realign', 'realize', 'reason',
    'reassign', 'rebuild', 'recall', 'receive', 'recognize', 'recommend', 'reconcile',
    'record', 'recover', 'recruit', 'rectify', 'redesign', 'reduce', 'reengineer',
    'refer', 'refine', 'reflect', 'refresh', 'register', 'regulate', 'reinforce',
    'reject', 'relate', 'release', 'relocate', 'rely', 'remediate', 'remind',
    'remove', 'render', 'renew', 'reorganize', 'repair', 'repeat', 'replace',
    'replicate', 'report', 'represent', 'reproduce', 'request', 'require', 'research',
    'reserve', 'reset', 'reshape', 'resolve', 'resource', 'respond', 'restore',
    'restructure', 'retain', 'retire', 'retrieve', 'return', 'reveal', 'reverse',
    'review', 'revise', 'revitalize', 'rewrite', 'route', 'run',
    'safeguard', 'sample', 'satisfy', 'save', 'scan', 'schedule', 'scope', 'screen',
    'search', 'secure', 'seek', 'segment', 'select', 'sell', 'send', 'separate',
    'sequence', 'serve', 'service', 'set', 'settle', 'shape', 'share', 'shift',
    'ship', 'show', 'signal', 'simplify', 'simulate', 'sketch', 'solicit', 'solve',
    'sort', 'source', 'speak', 'specify', 'sponsor', 'stabilize', 'staff', 'stage',
    'standardize', 'start', 'state', 'steer', 'stimulate', 'stop', 'store',
    'strategize', 'streamline', 'strengthen', 'structure', 'study', 'submit',
    'substantiate', 'succeed', 'suggest', 'summarize', 'supervise', 'supplement',
    'supply', 'support', 'survey', 'suspend', 'sustain', 'synchronize', 'synthesize', 'systematize',
    'tabulate', 'tailor', 'target', 'teach', 'terminate', 'test', 'track', 'trade',
    'train', 'transact', 'transcribe', 'transfer', 'transform', 'transition',
    'translate', 'transmit', 'transport', 'treat', 'trend', 'trigger', 'troubleshoot', 'turn',
    'uncover', 'undergo', 'understand', 'undertake', 'undo', 'unify', 'unite',
    'update', 'upgrade', 'upload', 'use', 'utilize',
    'validate', 'value', 'verify', 'view', 'visit', 'visualize',
    'waive', 'warn', 'weigh', 'welcome', 'withdraw', 'witness', 'work', 'write',
    'yield'
}

# Categorized action verbs (F08 - AEGIS enhancement)
ACTION_VERB_CATEGORIES = {
    'decisive': {
        'approve', 'authorize', 'decide', 'determine', 'direct', 'mandate', 'require',
        'command', 'decree', 'dictate', 'order', 'rule', 'adjudicate', 'arbitrate',
        'sanction', 'ratify', 'veto', 'overrule', 'countermand', 'commission', 'empower'
    },
    'ownership': {
        'own', 'manage', 'lead', 'oversee', 'control', 'govern', 'administer',
        'supervise', 'direct', 'head', 'chair', 'preside', 'steward', 'captain',
        'helm', 'spearhead', 'champion', 'sponsor', 'patron', 'custodian'
    },
    'creation': {
        'create', 'develop', 'design', 'build', 'establish', 'generate', 'produce',
        'construct', 'fabricate', 'manufacture', 'assemble', 'compose', 'formulate',
        'devise', 'engineer', 'architect', 'craft', 'forge', 'originate', 'innovate',
        'invent', 'conceive', 'pioneer', 'institute', 'found', 'launch', 'initiate'
    },
    'execution': {
        'execute', 'perform', 'implement', 'conduct', 'accomplish', 'achieve', 'complete',
        'fulfill', 'realize', 'deliver', 'effect', 'carry', 'enact', 'administer',
        'discharge', 'prosecute', 'pursue', 'undertake', 'exercise', 'practice',
        'apply', 'employ', 'utilize', 'operate', 'run', 'activate', 'deploy'
    },
    'verification': {
        'verify', 'validate', 'confirm', 'check', 'test', 'inspect', 'audit',
        'examine', 'review', 'assess', 'evaluate', 'appraise', 'scrutinize', 'probe',
        'investigate', 'analyze', 'authenticate', 'certify', 'attest', 'corroborate',
        'substantiate', 'witness', 'observe', 'monitor', 'survey', 'vet', 'screen'
    },
    'coordination': {
        'coordinate', 'collaborate', 'interface', 'liaise', 'integrate', 'synchronize',
        'harmonize', 'align', 'unify', 'consolidate', 'merge', 'combine', 'reconcile',
        'mediate', 'arbitrate', 'negotiate', 'facilitate', 'broker', 'orchestrate',
        'organize', 'arrange', 'schedule', 'plan', 'sequence', 'prioritize'
    },
    'communication': {
        'communicate', 'report', 'inform', 'notify', 'present', 'document', 'record',
        'brief', 'advise', 'counsel', 'consult', 'discuss', 'confer', 'deliberate',
        'correspond', 'convey', 'transmit', 'relay', 'disseminate', 'publish',
        'announce', 'proclaim', 'declare', 'articulate', 'express', 'explain'
    },
    'analysis': {
        'analyze', 'assess', 'evaluate', 'review', 'examine', 'investigate', 'study',
        'research', 'explore', 'survey', 'diagnose', 'interpret', 'deduce', 'infer',
        'conclude', 'determine', 'ascertain', 'calculate', 'compute', 'measure',
        'quantify', 'estimate', 'forecast', 'predict', 'model', 'simulate', 'project'
    },
    'support': {
        'support', 'assist', 'help', 'facilitate', 'enable', 'provide', 'supply',
        'furnish', 'equip', 'resource', 'staff', 'fund', 'finance', 'sponsor',
        'back', 'endorse', 'advocate', 'promote', 'encourage', 'foster', 'nurture',
        'sustain', 'maintain', 'preserve', 'protect', 'safeguard', 'secure'
    },
    'aerospace': {
        'certify', 'qualify', 'baseline', 'accredit', 'commission', 'decommission',
        'launch', 'deploy', 'orbit', 'track', 'telemetry', 'downlink', 'uplink',
        'encrypt', 'decrypt', 'authenticate', 'classify', 'declassify',
        'procure', 'source', 'provision', 'requisition', 'allocate',
        'retrofit', 'upgrade', 'modernize', 'refurbish', 'overhaul', 'recondition',
        'test', 'flight-test', 'ground-test', 'integrate', 'assemble', 'mate',
        'calibrate', 'align', 'boresight', 'checkout', 'acceptance', 'qualification',
        'harden', 'shield', 'isolate', 'attenuate', 'filter', 'condition'
    }
}

# Combined expanded verb set (1000+ verbs)
ACTION_VERBS = ORIGINAL_ACTION_VERBS.copy()
for category_verbs in ACTION_VERB_CATEGORIES.values():
    ACTION_VERBS.update(category_verbs)

# Additional verbs to reach 1000+
ADDITIONAL_VERBS = {
    # General business/technical
    'accelerate', 'accommodate', 'accumulate', 'acknowledge', 'activate', 'actuate',
    'adapt', 'adjoin', 'adjust', 'administer', 'adopt', 'advance', 'advertise',
    'affect', 'affirm', 'aggregate', 'aim', 'alert', 'allocate', 'alter', 'amend',
    'amplify', 'annotate', 'append', 'appreciate', 'archive', 'argue', 'arise',
    'articulate', 'ascend', 'assert', 'assign', 'associate', 'assume', 'attach',
    'attain', 'attempt', 'attract', 'attribute', 'augment', 'automate', 'await',

    # Technical/Engineering
    'backtrack', 'balance', 'benchmark', 'bind', 'block', 'boot', 'branch',
    'bridge', 'broadcast', 'browse', 'buffer', 'bundle', 'bypass', 'cache',
    'calibrate', 'cancel', 'cascade', 'cast', 'catalog', 'centralize', 'certify',
    'characterize', 'checkpoint', 'circulate', 'cite', 'clamp', 'cleanse',
    'clear', 'clone', 'cluster', 'code', 'cohere', 'coincide', 'collate',
    'color', 'commit', 'compact', 'compensate', 'compile', 'complement',
    'compress', 'concatenate', 'concur', 'configure', 'conform', 'conjoin',
    'constrain', 'containerize', 'contextualize', 'converge', 'correlate',
    'couple', 'crash', 'crawl', 'cross-check', 'cross-reference', 'customize',

    # Process/Workflow
    'dampen', 'debug', 'decentralize', 'decompose', 'decouple', 'decrement',
    'dedicate', 'deduplicate', 'default', 'defer', 'degrade', 'delineate',
    'demarcate', 'demote', 'denote', 'depict', 'deprecate', 'derive',
    'descend', 'designate', 'destabilize', 'detach', 'detail', 'deteriorate',
    'deviate', 'differentiate', 'digitize', 'dimension', 'diminish', 'disaggregate',
    'disambiguate', 'discard', 'discontinue', 'discount', 'disengage', 'disentangle',
    'dismantle', 'dispatch', 'disperse', 'displace', 'distinguish', 'diverge',
    'divert', 'dock', 'double', 'downgrade', 'drain', 'draw', 'drift', 'drop',
    'duplicate', 'dwell', 'earmark', 'echo', 'economize', 'edge', 'elevate',
    'elicit', 'elucidate', 'embed', 'embody', 'emerge', 'emit', 'emulate',
    'encapsulate', 'enclose', 'encode', 'encompass', 'encounter', 'endure',
    'energize', 'enlarge', 'enlist', 'enrich', 'entail', 'enumerate', 'envelop',
    'equate', 'eradicate', 'erect', 'err', 'escape', 'escort', 'evade', 'evolve',
    'exacerbate', 'excavate', 'excel', 'exclude', 'exempt', 'exhaust', 'exit',
    'expedite', 'expire', 'explode', 'exploit', 'expose', 'extrapolate', 'extrude',

    # Quality/Safety
    'fail', 'falsify', 'fault', 'feature', 'federate', 'feed', 'fetch',
    'figure', 'file', 'fill', 'filter', 'finesse', 'firm', 'fit', 'flag',
    'flatten', 'flip', 'float', 'flood', 'flow', 'fluctuate', 'flush', 'fold',
    'force', 'forge', 'form', 'formalize', 'fragment', 'frame', 'freeze',
    'fuel', 'function', 'fuse', 'gain', 'gate', 'gauge', 'generalize', 'geotag',
    'globalize', 'glue', 'google', 'govern', 'graft', 'grasp', 'grind', 'ground',
    'group', 'grow', 'guarantee', 'guard', 'guess', 'hack', 'handoff', 'handshake',
    'hang', 'harness', 'hash', 'hasten', 'heal', 'heat', 'heighten', 'hide',
    'hinder', 'hoist', 'hold', 'home', 'hook', 'hop', 'house', 'hover', 'humanize',
    'hunt', 'hurry', 'idle', 'ignite', 'ignore', 'image', 'immerse', 'immunize',
    'impact', 'impair', 'impede', 'implant', 'import', 'impose', 'impress',
    'imprint', 'imprison', 'improvise', 'incite', 'incline', 'include', 'incur',
    'index', 'individualize', 'induce', 'industrialize', 'infect', 'inflate',
    'inflict', 'ingest', 'inhabit', 'inherit', 'inhibit', 'inject', 'innovate',
    'inoculate', 'inquire', 'inscribe', 'insert', 'insist', 'install', 'instantiate',
    'instigate', 'instill', 'institutionalize', 'insulate', 'insure', 'intend',
    'intensify', 'intercede', 'intercept', 'interchange', 'interconnect',
    'interject', 'interleave', 'interlink', 'interlock', 'internalize', 'interoperate',
    'interpolate', 'interpose', 'intersect', 'intersperse', 'intertwine', 'intervene',
    'intrigue', 'introspect', 'invalidate', 'invert', 'invoke', 'ionize', 'irrigate',
    'irritate', 'iterate', 'jeopardize', 'jettison', 'juggle', 'jump', 'juxtapose',

    # More verbs
    'kick', 'kindle', 'knit', 'knock', 'knot', 'know', 'lag', 'laminate', 'land',
    'lapse', 'laser', 'latch', 'layer', 'layout', 'leak', 'lean', 'leap', 'legalize',
    'legislate', 'legitimize', 'lengthen', 'lessen', 'level', 'levy', 'liberate',
    'lift', 'lighten', 'liken', 'line', 'linearize', 'liquidate', 'lithograph',
    'litigate', 'live', 'load', 'loan', 'lobby', 'localize', 'lock', 'lodge',
    'loop', 'loosen', 'lose', 'lower', 'lubricate', 'lure', 'machine', 'magnify',
    'mail', 'majorize', 'malfunction', 'mandate', 'manifest', 'maneuver', 'mark',
    'mask', 'mass', 'massage', 'materialize', 'mature', 'maximize', 'meander',
    'mechanize', 'meld', 'melt', 'memorize', 'mesh', 'message', 'meter', 'micromanage',
    'migrate', 'mill', 'mimic', 'mind', 'mine', 'miniaturize', 'minimize', 'mint',
    'mirror', 'misalign', 'miscalculate', 'misconfigure', 'misinterpret', 'mismanage',
    'misplace', 'miss', 'misspell', 'mistake', 'mitigate', 'mix', 'mock', 'modernize',
    'modulate', 'monetize', 'monopolize', 'morph', 'mortgage', 'mount', 'multiply',
    'mutate', 'mute', 'nail', 'narrow', 'naturalize', 'negate', 'nest', 'network',
    'neutralize', 'nominalize', 'notarize', 'notch', 'nudge', 'nullify', 'nurture',
}

ACTION_VERBS.update(ADDITIONAL_VERBS)


# =============================================================================
# DIRECTIVE DETECTION (AEGIS enhanced - multi-word phrases + expanded words)
# =============================================================================

# v3.0.109: Expanded directive words for better extraction
DIRECTIVE_WORDS = ['shall', 'must', 'will', 'should', 'may', 'ensure', 'verify', 'confirm']

# v3.0.109: Multi-word directive phrases (checked before single words)
DIRECTIVE_PHRASES = [
    ('is responsible for', 'responsible'),
    ('are responsible for', 'responsible'),
    ('is accountable for', 'accountable'),
    ('are accountable for', 'accountable'),
    ('is required to', 'required'),
    ('are required to', 'required'),
    ('needs to', 'should'),
    ('need to', 'should'),
    ('has to', 'must'),
    ('have to', 'must'),
    ('it is the responsibility of', 'responsible'),
]

def detect_directive(text: str) -> str:
    """
    Detect directive word in text.

    v3.0.109: Enhanced to catch more requirement patterns including
    responsibility phrases and action words.

    Returns the directive word if found, empty string otherwise.
    """
    text_lower = text.lower()

    # v3.0.109: Check multi-word phrases first (order matters - longest first)
    for phrase, normalized in DIRECTIVE_PHRASES:
        if phrase in text_lower:
            return normalized

    # Check single-word directives
    for directive in DIRECTIVE_WORDS:
        # Look for word boundaries
        pattern = r'\b' + directive + r'\b'
        if re.search(pattern, text_lower):
            return directive
    return ""


# =============================================================================
# TEXT SPLITTING (shared with role_extractor_v3)
# =============================================================================

def split_on_action_verbs(text: str) -> List[str]:
    """
    Split text into statements based on action verbs.

    This is a key function shared with role_extractor_v3 for
    extracting responsibilities.
    """
    if not text:
        return []

    # Clean text
    text = re.sub(r'\s+', ' ', text).strip()

    # Don't split very short text
    if len(text) < 50:
        return [text] if text else []

    # Build verb pattern for splitting
    # Sort by length (longest first) to match multi-word verbs
    verbs_sorted = sorted(ACTION_VERBS, key=len, reverse=True)

    # Escape special regex characters
    escaped_verbs = [re.escape(v) for v in verbs_sorted[:200]]  # Top 200 for performance
    verb_pattern = r'\b(' + '|'.join(escaped_verbs) + r')(?:s|ed|ing|es)?\b'

    # Find all verb positions
    verb_matches = list(re.finditer(verb_pattern, text, re.IGNORECASE))

    if not verb_matches:
        return [text]

    # Split at verb positions, keeping the verb with the following text
    sentences = []
    last_end = 0

    for match in verb_matches:
        start = match.start()

        # Check if this is at a sentence boundary or after comma/semicolon
        if start > 0:
            prev_char = text[start - 1]
            # Good split points: after period, comma, semicolon, or "and"
            if prev_char in '.;,' or text[max(0, start-4):start].strip().lower() == 'and':
                if last_end < start:
                    prev_text = text[last_end:start].strip()
                    if prev_text and len(prev_text) > 20:
                        sentences.append(prev_text)
                last_end = start

    # Add remaining text
    if last_end < len(text):
        remaining = text[last_end:].strip()
        if remaining:
            sentences.append(remaining)

    # If no good splits found, return original
    if not sentences:
        return [text]

    return sentences


# =============================================================================
# REQUIREMENTS EXTRACTOR (ported from standalone core.py RequirementsExtractor)
# =============================================================================

class RequirementsExtractor:
    """Extracts requirement statements with shall/must/will/should/may."""

    # Directive words in priority order (standalone uses only these 5)
    DIRECTIVES = ['shall', 'must', 'will', 'should', 'may']

    # Section number pattern (e.g., "4.1 Title" or "4.1.2 Title")
    # Allows leading whitespace (common in PDFs)
    SECTION_PATTERN = re.compile(
        r'^\s*(\d+(?:\.\d+)*\.?)\s+([A-Z][A-Za-z\s,\-/&()]+?)(?:\s*$|\s{2,})',
        re.MULTILINE
    )

    # Procedure-style section pattern (e.g., "Section Title\tContent")
    PROCEDURE_SECTION_PATTERN = re.compile(
        r'^([A-Z][A-Za-z\s\-/&()]+?)(?:\s*\(Continued\))?\t(.+)$',
        re.MULTILINE
    )

    def __init__(self):
        self._seen = set()
        self._statement_counter = defaultdict(int)
        self._directive_counter = defaultdict(lambda: defaultdict(int))
        self._section_counter = 0

    def extract(self, text: str, tables: List[Dict], doc_title: str = "") -> List[Statement]:
        """Extract requirement statements from text."""
        self._seen.clear()
        self._statement_counter.clear()
        self._directive_counter.clear()
        self._section_counter = 0

        statements = []

        # Add document title as Level 1
        if doc_title:
            title = doc_title.rsplit('.', 1)[0] if '.' in doc_title else doc_title
            statements.append(Statement(
                number="",
                title=title,
                description="",
                level=1,
                section="",
                is_header=True
            ))

        # First try to extract Scope and Purpose
        scope_purpose = self._extract_scope_purpose(text)
        statements.extend(scope_purpose)

        # Try numbered section pattern first
        sections = self._parse_sections(text)

        if sections:
            for section_num, section_title, content, level in sections:
                adjusted_level = level + 1

                header = Statement(
                    number=section_num.rstrip('.'),
                    title=section_title,
                    description="",
                    level=adjusted_level,
                    section=section_num,
                    is_header=True
                )
                statements.append(header)

                directive_stmts = self._extract_directives(section_num, section_title, content, adjusted_level)
                statements.extend(directive_stmts)
        else:
            # Try procedure-style sections
            proc_statements = self._extract_procedure_style(text)
            statements.extend(proc_statements)

        # v3.0.109 AEGIS enhancement: Fallback - if very few statements extracted,
        # scan the entire document for directive sentences
        directive_count = sum(1 for s in statements if s.directive)
        if directive_count < 3:
            fallback_stmts = self._extract_directives_fallback(text)
            statements.extend(fallback_stmts)

        return statements

    def _extract_scope_purpose(self, text: str) -> List[Statement]:
        """Extract Scope and Purpose from document."""
        statements = []
        directives = ['shall', 'must', 'will', 'should', 'may']

        for line in text.split('\n'):
            line = line.rstrip('\r')

            if line.startswith('Scope\t'):
                parts = line.split('\t', 1)
                if len(parts) > 1 and parts[1].strip():
                    content = parts[1].strip()
                    if any(d in content.lower() for d in directives):
                        statements.append(Statement(
                            number="",
                            title="Scope",
                            description=content,
                            level=2,
                            section="",
                            is_header=False
                        ))
            elif line.startswith('Purpose\t'):
                parts = line.split('\t', 1)
                if len(parts) > 1 and parts[1].strip():
                    content = parts[1].strip()
                    if any(d in content.lower() for d in directives):
                        statements.append(Statement(
                            number="",
                            title="Purpose",
                            description=content,
                            level=2,
                            section="",
                            is_header=False
                        ))

        return statements

    def _extract_procedure_style(self, text: str) -> List[Statement]:
        """Extract sections from Procedure-style documents (Title\\tContent format)."""
        statements = []
        section_numbers = {}
        current_section = ""
        current_section_title = ""

        lines = text.split('\n')

        for line in lines:
            line = line.rstrip('\r')

            # Skip metadata lines
            if any(line.startswith(skip) for skip in ['Scope\t', 'Purpose\t', 'Process Architecture\t',
                                                        'Supersedes\t', 'Document Owner\t', 'Applies To\t',
                                                        'Process Flow\t', 'Definitions\t', 'SUBJECT:\t',
                                                        'Company\t', 'Sector\t', 'Authorized documents']):
                continue

            # Skip empty or whitespace-only lines
            if not line.strip() or line.strip() in ['\u00e2', '\u00e2\u00a2']:
                continue

            # Check if this is a section header line: "Title\tContent"
            if '\t' in line:
                parts = line.split('\t', 1)
                potential_title = parts[0].strip()
                content = parts[1].strip() if len(parts) > 1 else ""

                if (potential_title and
                    potential_title[0].isupper() and
                    len(potential_title.split()) >= 2 and
                    not potential_title.startswith(('PAGE', 'DOCUMENT', 'EFFECTIVE', 'REVIEW', 'NOTE'))):

                    clean_title = re.sub(r'\s*\(Continued\)\s*', '', potential_title).strip()

                    if clean_title not in section_numbers:
                        self._section_counter += 1
                        section_numbers[clean_title] = str(self._section_counter)
                        current_section = section_numbers[clean_title]
                        current_section_title = clean_title

                        statements.append(Statement(
                            number=current_section,
                            title=clean_title,
                            description="",
                            level=2,
                            section=current_section,
                            is_header=True
                        ))
                    else:
                        current_section = section_numbers[clean_title]
                        current_section_title = clean_title

                    if content:
                        directive_stmts = self._extract_directives(current_section, current_section_title, content, 2)
                        statements.extend(directive_stmts)

            elif current_section and line.strip():
                content = line.strip()
                has_directive = any(d in content.lower() for d in self.DIRECTIVES)
                if has_directive:
                    directive_stmts = self._extract_directives(current_section, current_section_title, content, 2)
                    statements.extend(directive_stmts)

        return statements

    def _extract_directives_fallback(self, text: str) -> List[Statement]:
        """
        v3.0.109 AEGIS enhancement: Fallback extraction for documents without
        clear section structure. Scans entire document for directive sentences.
        """
        statements = []

        paragraphs = re.split(r'\n\s*\n', text)

        para_num = 0
        for para in paragraphs:
            para = para.strip()
            if not para or len(para) < 30:
                continue

            sentences = re.split(r'(?<=[.!?])\s+', para)

            for sent in sentences:
                sent = re.sub(r'\s+', ' ', sent).strip()

                if len(sent) < 20:
                    continue

                directive = detect_directive(sent)
                if not directive:
                    continue

                norm = sent.lower()[:100]
                if norm in self._seen:
                    continue
                self._seen.add(norm)

                para_num += 1
                self._statement_counter['fallback'] += 1
                stmt_counter = self._statement_counter['fallback']

                self._directive_counter['fallback'][directive] += 1
                directive_count = self._directive_counter['fallback'][directive]

                stmt_num = f"{stmt_counter}"
                title = f"{directive.capitalize()} Statement {directive_count}"

                statements.append(Statement(
                    number=stmt_num,
                    title=title,
                    description=sent,
                    level=2,
                    section="",
                    directive=directive
                ))

        return statements

    def _parse_sections(self, text: str) -> List[Tuple[str, str, str, int]]:
        """Parse text into sections with hierarchy."""
        sections = []
        matches = list(self.SECTION_PATTERN.finditer(text))

        for i, m in enumerate(matches):
            num = m.group(1).strip()
            title = m.group(2).strip()

            level = min(num.rstrip('.').count('.') + 1, 6)

            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            sections.append((num, title, content, level))

        return sections

    def _extract_directives(self, section_num: str, section_title: str, content: str, level: int) -> List[Statement]:
        """Extract statements with directive words."""
        statements = []

        sentences = re.split(r'(?<=[.!?])\s+', content)

        for sent in sentences:
            sent = re.sub(r'\s+', ' ', sent).strip()

            if len(sent) < 20:
                continue

            directive = self._find_directive(sent)
            if not directive:
                continue

            norm = sent.lower()[:100]
            if norm in self._seen:
                continue
            self._seen.add(norm)

            self._statement_counter[section_num] += 1
            stmt_counter = self._statement_counter[section_num]

            self._directive_counter[section_num][directive] += 1
            directive_count = self._directive_counter[section_num][directive]

            clean_section = section_num.rstrip('.')
            stmt_num = f"{clean_section}.{stmt_counter}"

            directive_cap = directive.capitalize() if directive else "Statement"
            stmt_title = f"{section_title} {directive_cap} {directive_count}"

            statements.append(Statement(
                number=stmt_num,
                title=stmt_title,
                description=sent,
                level=min(level + 1, 6),
                section=clean_section,
                directive=directive
            ))

        return statements

    def _find_directive(self, text: str) -> str:
        """Find directive word in text."""
        lower = text.lower()
        for d in self.DIRECTIVES:
            if re.search(rf'\b{d}\b', lower):
                return d
        return ""


# =============================================================================
# WORK INSTRUCTION EXTRACTOR (ported from standalone core.py v5.9.6)
# =============================================================================

class WorkInstructionExtractor:
    """Extracts process steps from Work Instruction documents."""

    # Diagnostic flag - set to True to see debug output
    DEBUG = False
    DEBUG_SUBSTEPS = False

    # Pattern for section headers - handles both "A.  Title" and "A.\tTitle" formats
    PROCESS_SECTION_PATTERN = re.compile(
        r'^([A-Z])\.[\s\t]+(.+?)(?:\s*\(Continued\))?\s*$',
        re.MULTILINE
    )

    # Common action verbs for Work Instructions (the original 505 - identical to standalone)
    WI_ACTION_VERBS = ORIGINAL_ACTION_VERBS

    def __init__(self):
        self._current_role = ""
        self._current_section = ""
        self._pending_step_content = ""

    def extract(self, text: str, tables: List[Dict], doc_title: str = "") -> List[Statement]:
        """Extract process steps from Work Instruction."""
        statements = []

        # Add document title as Level 1
        if doc_title:
            title = doc_title.rsplit('.', 1)[0] if '.' in doc_title else doc_title
            statements.append(Statement(
                number="",
                title=title,
                description="",
                level=1,
                section="",
                is_header=True
            ))

        # Extract from text (handles both paragraphs and table content)
        text_statements = self._extract_from_text(text)
        statements.extend(text_statements)

        return statements

    def _extract_from_tables(self, tables: List[Dict]) -> List[Statement]:
        """Extract steps from table structures."""
        statements = []

        for table in tables:
            if not table.get('rows'):
                continue

            first_row = table['rows'][0] if table['rows'] else []
            headers = [c.get('text', '').lower() if isinstance(c, dict) else str(c).lower()
                      for c in first_row]

            has_step = any('step' in h for h in headers)
            has_action = any('action' in h for h in headers)
            has_role = any(h in ['responsible party', 'role', 'responsibility'] for h in headers)

            if has_step and has_action:
                tbl_statements = self._parse_step_action_table(table['rows'], has_role)
                statements.extend(tbl_statements)

        return statements

    def _parse_step_action_table(self, rows: List, has_role: bool) -> List[Statement]:
        """Parse a step-action table into statements."""
        statements = []
        current_role = ""
        current_section = ""

        data_rows = rows[1:] if rows else []

        for row in data_rows:
            cells = []
            for c in row:
                if isinstance(c, dict):
                    cells.append(c.get('text', ''))
                else:
                    cells.append(str(c) if c else '')

            if len(cells) < 2:
                continue

            if has_role and len(cells) >= 3:
                role = cells[0].strip()
                step = cells[1].strip()
                action = cells[2].strip()
            else:
                role = ""
                step = cells[0].strip()
                action = cells[1].strip()

            if role:
                role = re.sub(r'\s*\(Continued\)\s*', '', role)
                current_role = role

            if not action:
                continue

            is_continuation = '(Cont' in step
            step_clean = re.sub(r'\s*\(Cont\.?\)\s*', '', step).strip()

            stmt = Statement(
                number=f"{current_section}.{step_clean}" if current_section else step_clean,
                title=self._make_step_title(action),
                description=action,
                level=2 if current_section else 1,
                section=current_section,
                role=current_role,
                step_number=step_clean
            )
            statements.append(stmt)

        return statements

    def _extract_from_text(self, text: str) -> List[Statement]:
        """Extract steps from text content (primary method)."""
        statements = []
        seen_sections = {}
        seen_steps = {}

        self._current_section = ""
        self._current_role = ""

        directives = ['shall', 'must', 'will', 'should', 'may']

        # First, try to find Scope and Purpose
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line_clean = line.rstrip('\r')

            if line_clean.startswith('Scope\t') or line_clean.startswith('Scope '):
                parts = line_clean.split('\t', 1)
                if len(parts) > 1:
                    content = parts[1].strip()
                    if any(d in content.lower() for d in directives):
                        statements.append(Statement(
                            number="",
                            title="Scope",
                            description=content,
                            level=2,
                            section="",
                            is_header=False
                        ))
            elif line_clean.startswith('Purpose\t') or line_clean.startswith('Purpose '):
                parts = line_clean.split('\t', 1)
                if len(parts) > 1:
                    content = parts[1].strip()
                    if any(d in content.lower() for d in directives):
                        statements.append(Statement(
                            number="",
                            title="Purpose",
                            description=content,
                            level=2,
                            section="",
                            is_header=False
                        ))

        # Now process sections and steps
        self._pending_step_content = ""
        content_started = False

        for line in lines:
            line = line.rstrip('\r')
            line_stripped = line.strip()

            # STOP processing when we hit non-process content sections
            if content_started and seen_sections:
                stop_markers = [
                    'ATTACHMENT',
                    'References',
                    'Related Documents',
                    'Company Policies',
                    'Company Manuals',
                    'Company Forms',
                    'Sector Forms',
                    'NG Enterprise Design Guidelines',
                ]

                if line_stripped in stop_markers or line_stripped.startswith('ATTACHMENT'):
                    if self._pending_step_content:
                        stmts = self._parse_step_line(self._pending_step_content, seen_steps)
                        if stmts:
                            statements.extend(stmts)
                        self._pending_step_content = ""
                    break

            # Check for section header: "A.  Title" or "A.\tTitle"
            section_match = re.match(r'^([A-Z])\.[\s\t]+([^(\t]+?)(?:\s*\(Continued\))?(?:\s*NOTE:|\t|$)', line)
            if section_match:
                section_letter = section_match.group(1)
                section_title = section_match.group(2).strip()

                section_title = re.sub(r'\s*\(Continued\)\s*$', '', section_title).strip()

                # Process any pending step content BEFORE changing sections
                if self._pending_step_content:
                    stmts = self._parse_step_line(self._pending_step_content, seen_steps)
                    if stmts:
                        statements.extend(stmts)
                    self._pending_step_content = ""

                if section_letter not in seen_sections:
                    seen_sections[section_letter] = section_title
                    seen_steps[section_letter] = {}
                    statements.append(Statement(
                        number=f"{section_letter}.",
                        title=section_title,
                        description="",
                        level=2,
                        section=section_letter,
                        is_header=True
                    ))

                self._current_section = section_letter
                continue

            # Skip table headers
            if 'Responsible Party' in line and 'Step' in line and 'Action' in line:
                if self._pending_step_content:
                    stmts = self._parse_step_line(self._pending_step_content, seen_steps)
                    if stmts:
                        statements.extend(stmts)
                    self._pending_step_content = ""
                continue

            # Check if this line starts a new step (has step number pattern)
            has_step_num = False
            parts = line.split('\t')
            non_empty = [p.strip() for p in parts if p.strip()]

            for part in non_empty:
                if re.match(r'^\d+(\s*\(Cont\.?\))?$', part) or re.match(r'^\d+\.\d+$', part):
                    has_step_num = True
                    break

            if has_step_num and self._current_section:
                content_started = True

                # Check if this line is a NOTE
                line_content = '\t'.join(non_empty[1:]) if len(non_empty) > 1 else non_empty[0] if non_empty else ''
                is_note_line = line_content.strip().upper().startswith('NOTE')

                if is_note_line:
                    if self._pending_step_content:
                        stmts = self._parse_step_line(self._pending_step_content, seen_steps)
                        if stmts:
                            statements.extend(stmts)
                        self._pending_step_content = ""

                    if statements:
                        note_text = line_content.strip()
                        if note_text.upper().startswith('NOTE:'):
                            pass
                        elif note_text.upper().startswith('NOTE'):
                            note_text = 'NOTE:' + note_text[4:]
                        statements[-1].notes.append(note_text)
                    continue

                # This is a new step - first process any pending content
                if self._pending_step_content:
                    stmts = self._parse_step_line(self._pending_step_content, seen_steps)
                    if stmts:
                        statements.extend(stmts)

                self._pending_step_content = line
            elif self._current_section and self._pending_step_content:
                stripped = line.strip()
                if stripped and not stripped.startswith('NOTE'):
                    self._pending_step_content += '\n' + line

            # Check for NOTE lines
            stripped = line.strip()
            if stripped.startswith('NOTE:') or stripped.startswith('NOTE\t'):
                if self._pending_step_content:
                    stmts = self._parse_step_line(self._pending_step_content, seen_steps)
                    if stmts:
                        statements.extend(stmts)
                    self._pending_step_content = ""

                note_text = stripped.replace('\t', ' ')
                if not note_text.startswith('NOTE:'):
                    note_text = 'NOTE:' + note_text[4:].lstrip(': ')

                if statements:
                    statements[-1].notes.append(note_text)

        # Don't forget the last pending step
        if self._pending_step_content:
            stmts = self._parse_step_line(self._pending_step_content, seen_steps)
            if stmts:
                statements.extend(stmts)
            self._pending_step_content = ""

        # Post-process: restructure when main steps have sub-steps
        statements = self._restructure_with_substeps(statements)

        return statements

    def _restructure_with_substeps(self, statements: List[Statement]) -> List[Statement]:
        """Restructure statements when main steps have sub-steps."""
        if not statements:
            return statements

        # First pass: Handle IF/THEN conditional tables
        statements = self._handle_if_then_conditionals(statements)

        result = []
        i = 0

        while i < len(statements):
            stmt = statements[i]

            main_match = re.match(r'^([A-Z])\.(\d+)$', stmt.number)

            if main_match and stmt.description:
                section = main_match.group(1)
                step_num = main_match.group(2)

                has_substeps = False
                j = i + 1
                while j < len(statements):
                    next_stmt = statements[j]
                    if re.match(rf'^{section}\.{step_num}\.\d+$', next_stmt.number):
                        has_substeps = True
                        break
                    elif re.match(rf'^{section}\.\d+', next_stmt.number) and not next_stmt.number.startswith(f"{section}.{step_num}"):
                        break
                    j += 1

                if has_substeps:
                    parent = Statement(
                        number=stmt.number,
                        title=stmt.number,
                        description="",
                        level=stmt.level,
                        section=stmt.section,
                        role=stmt.role,
                        step_number=stmt.step_number,
                        is_header=False
                    )
                    result.append(parent)

                    action_sentences = self._split_on_action_verbs(stmt.description)

                    if len(action_sentences) > 1:
                        for idx, sentence in enumerate(action_sentences):
                            letter = chr(ord('a') + idx)
                            sub_stmt = Statement(
                                number=f"{stmt.number}.{letter}",
                                title=f"{stmt.number}.{letter}",
                                description=sentence.strip(),
                                level=stmt.level + 1,
                                section=stmt.section,
                                role=stmt.role,
                                step_number=f"{stmt.step_number}.{letter}" if stmt.step_number else letter,
                                notes=stmt.notes.copy() if stmt.notes and idx == 0 else []
                            )
                            result.append(sub_stmt)
                    else:
                        a_stmt = Statement(
                            number=f"{stmt.number}.a",
                            title=f"{stmt.number}.a",
                            description=stmt.description,
                            level=stmt.level + 1,
                            section=stmt.section,
                            role=stmt.role,
                            step_number=f"{stmt.step_number}.a" if stmt.step_number else "a",
                            notes=stmt.notes.copy() if stmt.notes else []
                        )
                        result.append(a_stmt)
                else:
                    action_sentences = self._split_on_action_verbs(stmt.description)

                    if len(action_sentences) > 1:
                        parent = Statement(
                            number=stmt.number,
                            title=stmt.number,
                            description="",
                            level=stmt.level,
                            section=stmt.section,
                            role=stmt.role,
                            step_number=stmt.step_number,
                            is_header=False
                        )
                        result.append(parent)

                        a_stmt = Statement(
                            number=f"{stmt.number}.a",
                            title=f"{stmt.number}.a",
                            description=action_sentences[0],
                            level=stmt.level + 1,
                            section=stmt.section,
                            role=stmt.role,
                            step_number=f"{stmt.step_number}.a" if stmt.step_number else "a"
                        )
                        result.append(a_stmt)

                        for idx, sentence in enumerate(action_sentences[1:], start=1):
                            letter = chr(ord('a') + idx)
                            child = Statement(
                                number=f"{stmt.number}.{letter}",
                                title=f"{stmt.number}.{letter}",
                                description=sentence,
                                level=stmt.level + 1,
                                section=stmt.section,
                                role=stmt.role,
                                step_number=f"{stmt.step_number}.{letter}" if stmt.step_number else letter
                            )
                            result.append(child)
                    else:
                        result.append(stmt)
            else:
                result.append(stmt)

            i += 1

        return result

    def _handle_if_then_conditionals(self, statements: List[Statement]) -> List[Statement]:
        """Handle IF/THEN conditional tables - combine into single statements."""
        result = []
        i = 0

        while i < len(statements):
            stmt = statements[i]

            if stmt.description and self._is_if_then_content(stmt.description):
                combined_statements = self._parse_if_then_content(stmt)
                if combined_statements:
                    result.extend(combined_statements)
                else:
                    result.append(stmt)
            else:
                result.append(stmt)

            i += 1

        return result

    def _is_if_then_content(self, text: str) -> bool:
        """Check if text contains IF/THEN conditional pattern."""
        if not text:
            return False

        text_upper = text.upper()
        has_if = 'IF...' in text_upper or 'IF\u2026' in text_upper or re.search(r'\bIF\s*\.{2,}', text_upper)
        has_then = 'THEN...' in text_upper or 'THEN\u2026' in text_upper or re.search(r'\bTHEN\s*\.{2,}', text_upper)

        return has_if and has_then

    def _parse_if_then_content(self, stmt: Statement) -> List[Statement]:
        """Parse IF/THEN conditional content into combined statements."""
        text = stmt.description
        if not text:
            return []

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        content_lines = []
        for line in lines:
            line_upper = line.upper()
            if line_upper in ('IF...', 'THEN...', 'IF\u2026', 'THEN\u2026') or \
               re.match(r'^IF\s*\.{2,}$', line_upper) or \
               re.match(r'^THEN\s*\.{2,}$', line_upper):
                continue
            content_lines.append(line)

        if not content_lines:
            return []

        conditionals = []
        current_condition = None
        current_actions = []
        notes = []

        for line in content_lines:
            if line.upper().startswith('NOTE'):
                notes.append(line)
                continue

            is_condition = self._is_condition_line(line)

            if is_condition:
                if current_condition and current_actions:
                    conditionals.append((current_condition, current_actions))
                current_condition = line
                current_actions = []
            else:
                if current_condition is not None:
                    current_actions.append(line)

        if current_condition and current_actions:
            conditionals.append((current_condition, current_actions))

        if not conditionals:
            return []

        result = []

        parent = Statement(
            number=stmt.number,
            title=stmt.number,
            description="",
            level=stmt.level,
            section=stmt.section,
            role=stmt.role,
            step_number=stmt.step_number,
            is_header=True
        )
        result.append(parent)

        for idx, (condition, actions) in enumerate(conditionals):
            letter = chr(ord('a') + idx)
            combined_actions = ' '.join(actions)
            description = f"IF {condition} THEN {combined_actions}"

            child = Statement(
                number=f"{stmt.number}.{letter}",
                title=f"{stmt.number}.{letter}",
                description=description,
                level=stmt.level + 1,
                section=stmt.section,
                role=stmt.role,
                step_number=f"{stmt.step_number}.{letter}" if stmt.step_number else letter,
                notes=notes.copy() if idx == len(conditionals) - 1 else []
            )
            result.append(child)

        return result

    def _is_condition_line(self, line: str) -> bool:
        """Determine if a line is a condition (scenario identifier) vs an action."""
        if not line:
            return False

        condition_endings = [
            'project', 'projects', 'request', 'requests',
            'sponsored', 'owned', 'operated', 'based'
        ]

        action_starters = [
            'upon', 'prepare', 'submit', 'provide', 'review', 'ensure',
            'obtain', 'coordinate', 'verify', 'maintain', 'document',
            'initiate', 'complete', 'approve', 'receive', 'conduct',
            'ccfa', 'fsa'
        ]

        line_lower = line.lower().strip()
        first_word = line_lower.split()[0] if line_lower.split() else ''

        if first_word in action_starters:
            return False

        for ending in condition_endings:
            if line_lower.endswith(ending):
                return True

        if len(line) < 60 and first_word not in action_starters:
            if not any(starter in line_lower for starter in ['must be', 'shall be', 'should be']):
                return True

        return False

    def _split_on_action_verbs(self, text: str) -> List[str]:
        """Split text into separate action statements with NOTE handling."""
        if not text:
            return []

        # First, extract any NOTE content and process separately
        note_matches = list(re.finditer(r'NOTE\s*:\s*', text, re.IGNORECASE))

        if not note_matches:
            return self._split_standard(text)

        result = []
        last_end = 0

        for match in note_matches:
            note_start = match.start()

            before_note = text[last_end:note_start].strip()
            if before_note:
                before_parts = self._split_standard(before_note)
                result.extend(before_parts)

            note_content_start = match.end()
            note_end = len(text)

            remaining = text[note_content_start:]

            abbrev_pattern = r'\b(U\.S|i\.e|e\.g|etc|vs|Dr|Mr|Mrs|Ms|No|Inc|Corp|Ltd|Jr|Sr|St)\.'

            abbrevs_found = []
            for abbrev_match in re.finditer(abbrev_pattern, remaining, re.IGNORECASE):
                abbrevs_found.append((abbrev_match.start(), abbrev_match.end(), abbrev_match.group()))

            real_end_match = re.search(r'\.\s+([A-Z][a-z]+(?:s|ed|ing|e)?)\s+', remaining)

            if real_end_match:
                potential_verb = real_end_match.group(1).lower()
                if self._is_action_verb_start(potential_verb):
                    end_pos = real_end_match.start() + 1
                    is_in_abbrev = any(start <= real_end_match.start() < end
                                       for start, end, _ in abbrevs_found)
                    if not is_in_abbrev:
                        note_end = note_content_start + end_pos

            note_text = "NOTE: " + text[note_content_start:note_end].strip()
            note_text = re.sub(r'^NOTE:\s*NOTE:\s*', 'NOTE: ', note_text, flags=re.IGNORECASE)
            result.append(note_text)

            last_end = note_end

        after_notes = text[last_end:].strip()
        if after_notes:
            after_parts = self._split_standard(after_notes)
            result.extend(after_parts)

        return result

    def _split_standard(self, text: str) -> List[str]:
        """Standard splitting on sentence boundaries and bullets (no NOTE handling)."""
        if not text:
            return []

        # Handle bullet points
        text = re.sub(r'\n?\s*[•\-\*]\s+', '\n<<BULLET>>', text)

        # Handle inline lists
        text = self._split_inline_lists(text)

        # Protect abbreviations
        abbrev_pattern = r'\b(U\.S|i\.e|e\.g|etc|vs|Dr|Mr|Mrs|Ms|No|Inc|Corp|Ltd|Jr|Sr|St)\.'
        protected = text
        placeholders = []

        for match in re.finditer(abbrev_pattern, text, re.IGNORECASE):
            placeholder = f'<<ABBREV_{len(placeholders)}>>'
            placeholders.append((placeholder, match.group()))
            protected = protected[:match.start()] + placeholder + protected[match.end():]

        parts = re.split(r'(?<=[.!?])\s+|\n<<BULLET>>', protected)

        result = []
        for part in parts:
            part = part.strip()
            if not part:
                continue

            for placeholder, original in placeholders:
                part = part.replace(placeholder, original)

            # "See..." references kept with parent statement
            if part.lower().startswith('see ') and result:
                result[-1] = result[-1] + ' ' + part
                continue

            # Short non-action fragments combined with previous
            if result and len(part) < 50:
                first_word = part.split()[0].rstrip('.,;:') if part.split() else ''
                if not self._is_action_verb_start(first_word.lower()):
                    result[-1] = result[-1] + ' ' + part
                    continue

            sub_statements = self._split_on_conjunctions(part)
            result.extend(sub_statements)

        return result

    def _split_inline_lists(self, text: str) -> str:
        """Split inline lists that follow patterns like 'the following:'."""
        list_indicators = [
            r'the following:',
            r'as follows:',
            r'following items:',
            r'following actions:',
            r'following steps:',
            r'include:',
            r'including:',
        ]

        for indicator in list_indicators:
            match = re.search(indicator, text, re.IGNORECASE)
            if match:
                after_indicator = text[match.end():]

                action_verb_pattern = r'\s+([A-Z][a-z]+)'

                list_items = []
                for verb_match in re.finditer(action_verb_pattern, after_indicator):
                    word = verb_match.group(1).lower()
                    if self._is_action_verb_start(word):
                        list_items.append(verb_match.start())

                if len(list_items) >= 2:
                    new_after = after_indicator
                    offset = 0
                    for pos in list_items:
                        insert_pos = pos + offset
                        new_after = new_after[:insert_pos] + '\n<<BULLET>>' + new_after[insert_pos:].lstrip()
                        offset += len('\n<<BULLET>>') - 1

                    text = text[:match.end()] + new_after
                    break

        return text

    def _is_action_verb_start(self, word: str) -> bool:
        """Check if a word is likely an action verb that starts a new statement.

        Uses a curated subset that excludes noun-ambiguous words.
        """
        action_starters = {
            'accept', 'accomplish', 'achieve', 'acquire', 'address', 'adjust',
            'advise', 'align', 'allocate', 'analyze', 'apply', 'approve',
            'arrange', 'assess', 'assign', 'assist', 'authorize', 'calculate',
            'capture', 'certify', 'check', 'clarify', 'collaborate', 'collect',
            'communicate', 'compare', 'complete', 'comply', 'conduct', 'configure',
            'confirm', 'consider', 'consolidate', 'contact', 'continue', 'coordinate',
            'correct', 'create', 'define', 'delegate', 'deliver', 'demonstrate',
            'deploy', 'describe', 'determine', 'develop', 'direct', 'distribute',
            'document', 'draft', 'enable', 'engage', 'ensure', 'enter', 'establish',
            'evaluate', 'examine', 'execute', 'facilitate', 'finalize', 'follow',
            'formulate', 'forward', 'gather', 'generate', 'identify', 'implement',
            'improve', 'incorporate', 'inform', 'initiate', 'inspect', 'install',
            'integrate', 'interface', 'interpret', 'introduce', 'issue', 'launch',
            'lead', 'leverage', 'locate', 'log', 'maintain', 'manage', 'measure',
            'modify', 'monitor', 'negotiate', 'notify', 'obtain', 'operate',
            'organize', 'oversee', 'participate', 'perform', 'prepare', 'present',
            'prevent', 'prioritize', 'process', 'procure', 'produce', 'promote',
            'propose', 'protect', 'provide', 'publish', 'purchase', 'pursue',
            'receive', 'recognize', 'recommend', 'record', 'reduce', 'refine',
            'register', 'release', 'remove', 'report', 'represent', 'request',
            'research', 'resolve', 'respond', 'restore', 'retain', 'retrieve',
            'return', 'review', 'revise', 'save', 'scan', 'schedule', 'secure',
            'select', 'send', 'serve', 'share', 'ship', 'sign', 'solicit', 'solve',
            'sort', 'specify', 'standardize', 'store', 'streamline', 'study',
            'submit', 'summarize', 'survey', 'suspend', 'sustain', 'synchronize',
            'synthesize', 'tabulate', 'terminate', 'track', 'train', 'transfer',
            'transform', 'transition', 'translate', 'transmit', 'transport',
            'troubleshoot', 'update', 'upgrade', 'upload', 'utilize', 'validate',
            'verify', 'withdraw', 'write'
        }
        return word.lower() in action_starters

    def _split_on_conjunctions(self, text: str) -> List[str]:
        """Split a single sentence on conjunctions followed by action verbs."""
        if not text:
            return []

        # Only split on action verbs that CLEARLY start new action statements
        # Excludes noun-ambiguous words (design, support, control, test, etc.)
        clear_action_verbs = {
            'accept', 'accomplish', 'achieve', 'acquire', 'address', 'adjust', 'administer',
            'advise', 'align', 'allocate', 'analyze', 'apply', 'approve', 'arrange', 'assess',
            'assign', 'assist', 'assure', 'authorize', 'calculate', 'capture', 'certify',
            'check', 'clarify', 'collaborate', 'collect', 'communicate', 'compare',
            'complete', 'comply', 'conduct', 'configure', 'confirm', 'consider', 'consolidate',
            'contact', 'continue', 'coordinate', 'correct', 'create', 'define',
            'delegate', 'deliver', 'demonstrate', 'deploy', 'describe', 'determine',
            'develop', 'direct', 'distribute', 'document', 'draft', 'enable', 'engage',
            'ensure', 'enter', 'establish', 'evaluate', 'examine', 'execute',
            'facilitate', 'finalize', 'follow', 'formulate', 'forward', 'gather',
            'generate', 'identify', 'implement', 'improve', 'incorporate', 'inform',
            'initiate', 'inspect', 'install', 'integrate', 'interface', 'interpret',
            'introduce', 'issue', 'launch', 'lead', 'leverage', 'locate', 'log', 'maintain',
            'manage', 'measure', 'modify', 'monitor', 'negotiate', 'notify', 'obtain',
            'operate', 'organize', 'oversee', 'participate', 'perform', 'prepare',
            'present', 'prevent', 'prioritize', 'process', 'procure', 'produce',
            'promote', 'propose', 'protect', 'provide', 'publish', 'purchase', 'pursue',
            'reassess', 'receive', 'recognize', 'recommend', 'record', 'reduce',
            'refine', 'register', 'release', 'remove', 'report', 'represent', 'request',
            'research', 'resolve', 'respond', 'restore', 'retain', 'retrieve', 'return',
            'review', 'revise', 'save', 'scan', 'schedule', 'secure', 'select', 'send',
            'serve', 'share', 'ship', 'sign', 'solicit', 'solve', 'sort', 'specify',
            'standardize', 'store', 'streamline', 'study', 'submit', 'summarize',
            'survey', 'suspend', 'sustain', 'synchronize', 'synthesize', 'tabulate',
            'terminate', 'track', 'train', 'transfer', 'transform', 'transition',
            'translate', 'transmit', 'transport', 'troubleshoot', 'update', 'upgrade',
            'upload', 'utilize', 'validate', 'verify', 'withdraw', 'write'
        }

        result = []
        current_start = 0
        i = 0

        while i < len(text):
            # Check for "; " followed by action verb
            if i < len(text) - 2 and text[i:i+2] == '; ':
                next_word = self._get_next_word(text, i+2)
                if next_word.lower() in clear_action_verbs:
                    if current_start < i:
                        result.append(text[current_start:i].strip())
                    current_start = i + 2
                    i += 2
                    continue

            # Check for ", and " followed by action verb
            if i < len(text) - 6 and text[i:i+6].lower() == ', and ':
                next_word = self._get_next_word(text, i + 6)
                if next_word.lower() in clear_action_verbs:
                    current_segment = text[current_start:i].strip()
                    if len(current_segment) > 15:
                        result.append(current_segment)
                        current_start = i + 6
                        i += 6
                        continue

            # Check for " and " followed by action verb
            if i < len(text) - 5 and text[i:i+5].lower() == ' and ':
                next_word = self._get_next_word(text, i + 5)
                if next_word.lower() in clear_action_verbs:
                    current_segment = text[current_start:i].strip()
                    very_clear_verbs = {'ensure', 'verify', 'validate', 'confirm', 'coordinate',
                                       'obtain', 'maintain', 'provide', 'prepare', 'review',
                                       'document', 'identify', 'establish', 'determine'}
                    if len(current_segment) > 20 and next_word.lower() in very_clear_verbs:
                        result.append(current_segment)
                        current_start = i + 5
                        i += 5
                        continue

            i += 1

        remaining = text[current_start:].strip()
        if remaining:
            if result:
                remaining = remaining[0].upper() + remaining[1:] if len(remaining) > 1 else remaining.upper()
            result.append(remaining)

        return result if result else [text]

    def _get_next_word(self, text: str, start: int) -> str:
        """Extract the next word starting at position start."""
        while start < len(text) and text[start].isspace():
            start += 1
        end = start
        while end < len(text) and (text[end].isalnum() or text[end] == '-'):
            end += 1
        return text[start:end]

    def _split_on_bullets_only(self, text: str) -> List[str]:
        """Split text ONLY on bullet points, not on action verbs."""
        if not text:
            return []

        text = re.sub(r'\n?\s*[•\-\*]\s+', '\n<<BULLET>>', text)

        if '<<BULLET>>' in text:
            parts = text.split('<<BULLET>>')
            result = [p.strip() for p in parts if p.strip()]
            return result
        else:
            return [text.strip()] if text.strip() else []

    def _parse_step_line(self, content: str, seen_steps: dict) -> List[Statement]:
        """Parse step content (possibly multi-line), splitting on action verbs and bullets."""
        lines = content.split('\n')
        first_line = lines[0] if lines else ""
        continuation_lines = lines[1:] if len(lines) > 1 else []

        parts = first_line.split('\t')
        non_empty = [(i, p.strip()) for i, p in enumerate(parts) if p.strip()]

        if len(non_empty) < 2:
            return []

        role = ""
        step = ""
        action = ""
        is_substep = False

        # Check if any part is a sub-step number (N.N format)
        substep_idx = -1
        for i, (orig_idx, part) in enumerate(non_empty):
            if re.match(r'^\d+\.\d+$', part):
                substep_idx = i
                break

        if substep_idx >= 0:
            is_substep = True
            step = non_empty[substep_idx][1]

            if substep_idx > 0:
                role = non_empty[substep_idx - 1][1]

            if substep_idx < len(non_empty) - 1:
                action = ' '.join(p[1] for p in non_empty[substep_idx + 1:])
        else:
            step_idx = -1
            for i, (orig_idx, part) in enumerate(non_empty):
                if re.match(r'^\d+(\s*\(Cont\.?\))?$', part):
                    step_idx = i
                    step = part
                    break

            if step_idx == -1:
                return []

            if step_idx > 0:
                role = non_empty[step_idx - 1][1]

            if step_idx < len(non_empty) - 1:
                action_parts = [p[1] for p in non_empty[step_idx + 1:]]
                action = ' '.join(action_parts)

        # Append continuation lines to action
        for cont_line in continuation_lines:
            cont_line = cont_line.strip()
            if cont_line:
                action += '\n' + cont_line

        if not action:
            return []

        # Strip end-of-document content
        end_markers = [
            '\nReferences\n',
            '\nReferences\t',
            '\nCompany\t',
            '\nSector\t',
            '\nOther\t',
            '\nCompany Forms',
            '\nSector Forms',
            '\nNG Enterprise Design Guidelines',
        ]
        for marker in end_markers:
            if marker in action:
                action = action[:action.index(marker)]

        if action.strip().endswith('References'):
            action = action[:action.rfind('References')]

        if not action.strip():
            return []

        if role:
            role = re.sub(r'\s*\(Continued\)\s*', '', role)
            self._current_role = role

        step_clean = re.sub(r'\s*\(Cont\.?\)\s*', '', step).strip()

        # Check for embedded sub-steps
        embedded_substeps = re.findall(r'(\d+\.\d+)\s+([A-Z][^0-9]*?)(?=\d+\.\d+\s+[A-Z]|NOTE:|$)', action, re.DOTALL)
        embedded_substeps = [(num, content) for num, content in embedded_substeps
                            if not content.strip().upper().startswith('NOTE')]

        if embedded_substeps and not is_substep:
            first_substep_match = re.search(r'\d+\.\d+\s+[A-Z]', action)
            if first_substep_match:
                main_content = action[:first_substep_match.start()].strip()

                if self._current_section not in seen_steps:
                    seen_steps[self._current_section] = {}
                section_steps = seen_steps[self._current_section]

                if step_clean not in section_steps:
                    section_steps[step_clean] = 1

                base_num = f"{self._current_section}.{step_clean}"
                statements = []

                statements.append(Statement(
                    number=base_num,
                    title=base_num,
                    description="",
                    level=3,
                    section=self._current_section,
                    role=self._current_role,
                    step_number=step_clean
                ))

                if main_content:
                    statements.append(Statement(
                        number=f"{base_num}.a",
                        title=f"{base_num}.a",
                        description=main_content,
                        level=4,
                        section=self._current_section,
                        role=self._current_role,
                        step_number=f"{step_clean}.a"
                    ))

                for substep_num, substep_content in embedded_substeps:
                    substep_content = substep_content.strip()

                    if substep_content.upper().startswith('NOTE'):
                        if statements:
                            note_text = substep_content
                            if not note_text.startswith('NOTE:'):
                                note_text = 'NOTE: ' + note_text[4:].lstrip(': ')
                            statements[-1].notes.append(note_text)
                        continue

                    if 'NOTE:' in substep_content:
                        substep_content = substep_content[:substep_content.index('NOTE:')].strip()

                    statements.append(Statement(
                        number=f"{self._current_section}.{substep_num}",
                        title=f"{self._current_section}.{substep_num}",
                        description=substep_content,
                        level=4,
                        section=self._current_section,
                        role=self._current_role,
                        step_number=substep_num
                    ))

                return statements

        if self._current_section not in seen_steps:
            seen_steps[self._current_section] = {}

        section_steps = seen_steps[self._current_section]
        statements = []

        if is_substep:
            full_num = f"{self._current_section}.{step_clean}"

            if self._current_section not in seen_steps:
                seen_steps[self._current_section] = {}
            section_steps = seen_steps[self._current_section]

            substep_key = f"substep_{step_clean}"

            if substep_key in section_steps:
                return []
            section_steps[substep_key] = True

            statements.append(Statement(
                number=full_num,
                title=full_num,
                description=action,
                level=4,
                section=self._current_section,
                role=self._current_role,
                step_number=step_clean
            ))
        else:
            is_continuation = '(Cont' in step

            if is_continuation:
                if step_clean in section_steps:
                    section_steps[step_clean] += 1
                    cont_num = section_steps[step_clean]
                    base_num = f"{self._current_section}.{step_clean}.{cont_num}"
                else:
                    section_steps[step_clean] = 1
                    base_num = f"{self._current_section}.{step_clean}.1"
                base_level = 4
            elif step_clean in section_steps:
                section_steps[step_clean] += 1
                suffix = chr(ord('a') + section_steps[step_clean] - 1)
                base_num = f"{self._current_section}.{step_clean}{suffix}"
                base_level = 4
            else:
                section_steps[step_clean] = 1
                base_num = f"{self._current_section}.{step_clean}"
                base_level = 3

            # Split action on bullets ONLY (not action verbs for main steps)
            action_sentences = self._split_on_bullets_only(action)

            if len(action_sentences) <= 1:
                return [Statement(
                    number=base_num,
                    title=base_num,
                    description=action,
                    level=base_level,
                    section=self._current_section,
                    role=self._current_role,
                    step_number=step_clean
                )]

            # Multiple sentences - create parent placeholder + lettered children
            statements.append(Statement(
                number=base_num,
                title=base_num,
                description="",
                level=base_level,
                section=self._current_section,
                role=self._current_role,
                step_number=step_clean,
                is_header=True
            ))

            for i, sent in enumerate(action_sentences):
                letter = chr(ord('a') + i)
                child_num = f"{base_num}.{letter}"

                statements.append(Statement(
                    number=child_num,
                    title=child_num,
                    description=sent,
                    level=base_level + 1,
                    section=self._current_section,
                    role=self._current_role,
                    step_number=f"{step_clean}.{letter}"
                ))

        return statements

    def _make_step_title(self, action: str) -> str:
        """Create a short title from action text."""
        first_sentence = re.split(r'[.!?]', action)[0]

        if len(first_sentence) > 50:
            return first_sentence[:47] + "..."
        return first_sentence


# =============================================================================
# UNIFIED EXTRACTOR (ported from standalone core.py StatementExtractor)
# =============================================================================

class StatementExtractor:
    """Unified extractor that handles both document types."""

    def __init__(self):
        self.requirements_extractor = RequirementsExtractor()
        self.work_instruction_extractor = WorkInstructionExtractor()

    def detect_document_type(self, text: str, tables: List[Dict] = None) -> Tuple[DocumentType, float]:
        """
        Auto-detect document type with confidence score.

        Returns:
            tuple: (DocumentType, confidence 0.0-1.0)
        """
        if tables is None:
            tables = []

        # Count directive words
        directive_count = sum(
            len(re.findall(rf'\b{d}\b', text, re.I))
            for d in ['shall', 'must', 'will']
        )

        # Count step-action indicators
        step_action_count = len(re.findall(r'\bStep\b.*\bAction\b', text, re.I))
        role_count = len(re.findall(r'Responsible\s+Party|Role\s*\t', text, re.I))

        # Check tables for step-action structure
        has_step_action_table = False
        for table in tables:
            if table.get('rows'):
                first_row = [str(c.get('text', '') if isinstance(c, dict) else c).lower()
                            for c in table['rows'][0]]
                if any('step' in h for h in first_row) and any('action' in h for h in first_row):
                    has_step_action_table = True
                    break

        # Calculate scores
        req_score = directive_count / 100
        wi_score = (step_action_count + role_count) / 10 + (1.0 if has_step_action_table else 0)

        if req_score > wi_score:
            confidence = min(req_score / (req_score + wi_score + 0.01), 0.95)
            return DocumentType.PROCEDURES, confidence
        else:
            confidence = min(wi_score / (req_score + wi_score + 0.01), 0.95)
            return DocumentType.WORK_INSTRUCTION, confidence

    def extract(self, text: str, doc_title: str = "",
                doc_type: DocumentType = None,
                tables: List[Dict] = None) -> List[Statement]:
        """
        Extract statements from text.

        Args:
            text: Document text
            doc_title: Document title/filename
            doc_type: Optional document type (auto-detected if not provided)
            tables: Optional list of table structures from document

        Returns:
            List of Statement objects
        """
        if tables is None:
            tables = []

        if not text:
            return []

        # Auto-detect document type
        if doc_type is None:
            doc_type, _ = self.detect_document_type(text, tables)

        if doc_type == DocumentType.REQUIREMENTS or doc_type == DocumentType.PROCEDURES:
            return self.requirements_extractor.extract(text, tables, doc_title)
        else:
            return self.work_instruction_extractor.extract(text, tables, doc_title)

    def validate_extraction(self, statements: List[Statement],
                           doc_type: DocumentType) -> List[str]:
        """Validate extraction results and return warnings."""
        warnings = []

        if not statements:
            warnings.append("No statements were extracted from the document.")
            return warnings

        if doc_type == DocumentType.REQUIREMENTS or doc_type == DocumentType.PROCEDURES:
            directive_count = sum(1 for s in statements if s.directive)
            if directive_count == 0:
                warnings.append(
                    "No requirement statements (shall/must/will) found. "
                    "This may not be a requirements document."
                )
            elif directive_count < 5:
                warnings.append(
                    f"Only {directive_count} requirement statements found. "
                    "Consider checking if this is the correct document type."
                )
        else:
            step_count = sum(1 for s in statements if s.step_number and not s.is_header)
            if step_count == 0:
                warnings.append(
                    "No process steps found. "
                    "This may not be a Work Instruction document."
                )
            elif step_count < 3:
                warnings.append(
                    f"Only {step_count} process steps found. "
                    "Consider checking if this is the correct document type."
                )

        return warnings


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def extract_statements(text: str, doc_title: str = "",
                       doc_type: DocumentType = None,
                       tables: List[Dict] = None) -> List[Statement]:
    """
    Extract statements from document text.

    Convenience function that creates an extractor and calls extract().
    """
    extractor = StatementExtractor()
    return extractor.extract(text, doc_title, doc_type, tables)


def get_verb_category(verb: str) -> Optional[str]:
    """Get the category for an action verb."""
    verb_lower = verb.lower()
    for category, verbs in ACTION_VERB_CATEGORIES.items():
        if verb_lower in verbs:
            return category
    return None


def get_verbs_by_category(category: str) -> Set[str]:
    """Get all verbs in a category."""
    return ACTION_VERB_CATEGORIES.get(category, set())
