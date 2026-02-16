#!/usr/bin/env python3
"""
Passive Voice Checker v2.0.0
============================
Detects passive voice constructions.
"""

import re
from typing import List, Dict, Tuple

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "2.6.0"


class PassiveVoiceChecker(BaseChecker):
    """Detects passive voice constructions."""
    
    CHECKER_NAME = "Passive Voice"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    # BUG-C01 FIX: Significantly expanded false positives list to reduce over-matching
    # Words that are often false positives (adjectives/past participles used as adjectives)
    FALSE_POSITIVES = {
        # Common predicate adjectives ending in -ed
        'concerned', 'interested', 'required', 'needed', 'used', 'based',
        'related', 'associated', 'located', 'designed', 'intended',
        'supposed', 'expected', 'allowed', 'permitted', 'written',
        'tired', 'bored', 'excited', 'pleased', 'satisfied', 'disappointed',
        'surprised', 'amazed', 'confused', 'frustrated', 'married',
        'retired', 'qualified', 'experienced', 'skilled', 'trained',
        'dedicated', 'committed', 'motivated', 'determined', 'organized',
        'advanced', 'detailed', 'complicated', 'sophisticated', 'automated',
        'defined', 'specified', 'described', 'listed', 'outlined', 'noted',
        # Technical/Systems engineering terms (BUG-C01 fix)
        'aligned', 'allocated', 'applied', 'approved', 'assigned', 'attached',
        'calibrated', 'certified', 'classified', 'cleared', 'closed', 'coded',
        'completed', 'configured', 'connected', 'contained', 'controlled',
        'coordinated', 'coupled', 'covered', 'created', 'customized',
        'deployed', 'derived', 'developed', 'directed', 'distributed', 'documented',
        'embedded', 'enabled', 'enclosed', 'engaged', 'enhanced', 'equipped',
        'established', 'evaluated', 'executed', 'expanded', 'exposed', 'extended',
        'filed', 'filled', 'filtered', 'finalized', 'fixed', 'focused', 'formatted',
        'generated', 'grounded', 'grouped', 'guided',
        'handled', 'highlighted', 'hosted',
        'identified', 'illustrated', 'implemented', 'improved', 'included',
        'incorporated', 'indexed', 'indicated', 'initialized', 'installed',
        'integrated', 'involved', 'isolated',
        'justified', 'labeled', 'layered', 'leveraged', 'limited', 'linked', 'loaded',
        'maintained', 'managed', 'mapped', 'marked', 'matched', 'measured', 'merged',
        'modified', 'monitored', 'mounted', 'named', 'nested', 'normalized', 'numbered',
        'obtained', 'occupied', 'offered', 'opened', 'operated', 'optimized', 'ordered',
        'oriented', 'owned',
        'paired', 'partitioned', 'passed', 'performed', 'placed', 'planned', 'populated',
        'positioned', 'powered', 'prepared', 'presented', 'prioritized', 'processed',
        'produced', 'programmed', 'protected', 'provided', 'published', 'purchased',
        'rated', 'realized', 'received', 'recognized', 'recorded', 'referenced',
        'registered', 'regulated', 'released', 'removed', 'repeated', 'replaced',
        'reported', 'represented', 'reserved', 'resolved', 'restricted', 'resulted',
        'routed', 'ruled',
        'saved', 'scaled', 'scheduled', 'scoped', 'secured', 'selected', 'separated',
        'sequenced', 'serialized', 'served', 'shaped', 'shared', 'signed', 'simplified',
        'simulated', 'situated', 'sized', 'sorted', 'sourced', 'specialized', 'stated',
        'stored', 'structured', 'submitted', 'summarized', 'supported', 'suspended',
        'synchronized', 'targeted', 'tasked', 'terminated', 'tested', 'tracked',
        'transferred', 'transformed', 'triggered', 'tuned', 'typed',
        'unified', 'updated', 'upgraded', 'utilized', 'validated', 'valued', 'varied',
        'verified', 'versioned', 'viewed', 'weighted', 'wrapped', 'zipped',
        # Irregular past participles ending in -en (adjectives)
        'given', 'taken', 'known', 'shown', 'proven', 'chosen',
        'broken', 'frozen', 'hidden', 'driven', 'risen', 'fallen',
        'spoken', 'stolen', 'sunken', 'swollen', 'woven', 'worn',
        'beaten', 'bitten', 'eaten', 'forgotten', 'gotten', 'mistaken',
        'shaken', 'awoken', 'undertaken', 'overtaken', 'withdrawn',
        'ridden', 'striven', 'thriven', 'written', 'overwritten',
        'forbidden', 'forgiven', 'trodden', 'stricken', 'smitten',
        # Emotional/psychological states
        'alarmed', 'annoyed', 'astonished', 'attached', 'attracted',
        'bewildered', 'blessed', 'bothered', 'challenged', 'charmed',
        'convinced', 'delighted', 'depressed', 'devoted', 'disgusted',
        'distressed', 'disturbed', 'embarrassed', 'encouraged', 'enlightened',
        'entertained', 'fascinated', 'flattered', 'frightened', 'gratified',
        'honored', 'humiliated', 'impressed', 'informed', 'inspired',
        'intrigued', 'irritated', 'moved', 'offended', 'overwhelmed',
        'perplexed', 'puzzled', 'relieved', 'shocked', 'stressed',
        'stunned', 'terrified', 'thrilled', 'touched', 'troubled', 'worried',
        # Physical/positional states
        'bent', 'buried', 'centered', 'cluttered', 'collapsed', 'combined',
        'compressed', 'concentrated', 'cracked', 'crowded', 'curved', 'damaged',
        'drained', 'dried', 'elevated', 'enclosed', 'exhausted', 'exposed',
        'faded', 'fitted', 'flattened', 'folded', 'gathered', 'heated',
        'jammed', 'leaned', 'locked', 'loosened', 'lowered', 'mixed',
        'packed', 'painted', 'piled', 'pointed', 'polished', 'pressed',
        'raised', 'relaxed', 'renewed', 'rested', 'scattered', 'sealed',
        'seated', 'settled', 'sheltered', 'shifted', 'shut', 'split', 'spread',
        'stacked', 'stretched', 'stuck', 'stuffed', 'tightened', 'tilted',
        'torn', 'trapped', 'twisted', 'united', 'worn', 'wounded', 'wrecked',
        # v2.6.1: Additional SOP/procedure language - these are standard requirements language
        'prohibited', 'contacted', 'notified', 'informed', 'consulted', 'escorted',
        'accompanied', 'supervised', 'authorized', 'granted', 'denied', 'revoked',
        'suspended', 'terminated', 'permitted', 'restricted', 'limited', 'forbidden',
        'obligated', 'mandated', 'stipulated', 'dictated', 'enforced', 'prescribed',
        'recommended', 'suggested', 'advised', 'warned', 'cautioned', 'alerted',
        'reminded', 'instructed', 'directed', 'guided', 'led', 'mentored', 'coached',
        # Equipment and safety states
        'grounded', 'isolated', 'locked', 'tagged', 'energized', 'de-energized',
        'pressurized', 'depressurized', 'ventilated', 'evacuated', 'secured',
        'shielded', 'insulated', 'bonded', 'charged', 'discharged', 'activated',
        'deactivated', 'armed', 'disarmed', 'engaged', 'disengaged',
        # v2.6.2: Regulatory/requirements language - common in SOPs and standards
        'reviewed', 'conducted', 'issued', 'addressed', 'corrected', 'affected',
        'analyzed', 'fabricated', 'interconnected', 'enacted', 'reproduced',
        'introduced', 'established', 'implemented', 'maintained', 'documented',
        'inspected', 'audited', 'evaluated', 'assessed', 'investigated',
        'communicated', 'coordinated', 'resolved', 'disposed', 'cleaned',
        'labeled', 'marked', 'posted', 'filed', 'archived', 'retained',
        # Process/engineering terms
        'welded', 'bolted', 'piped', 'vented', 'drained', 'filtered', 'pumped',
        'heated', 'cooled', 'mixed', 'separated', 'distilled', 'purified',
        # Administrative/procedural
        'scheduled', 'planned', 'assigned', 'delegated', 'distributed',
        'submitted', 'approved', 'rejected', 'signed', 'witnessed', 'dated',
        'numbered', 'stamped', 'sealed', 'certified', 'accredited', 'licensed',
        # v2.6.2: Words that look like past participles but aren't (false positive fixes)
        'need', 'feed', 'seed', 'deed', 'breed', 'bleed', 'speed', 'creed',
        'indeed', 'agreed', 'freed', 'treed',  # Words ending in -eed
        'led', 'fled', 'sled', 'shed', 'red', 'bed', 'wed',  # Short words
    }
    
    PASSIVE_PATTERNS = [
        (r'\b(is|are|was|were|be|been|being)\s+(\w+ed)\b', 'be + past participle'),
        (r'\b(is|are|was|were|be|been|being)\s+(\w+en)\b', 'be + past participle'),
        (r'\b(has|have|had)\s+been\s+(\w+ed)\b', 'has/have been + past participle'),
        (r'\b(has|have|had)\s+been\s+(\w+en)\b', 'has/have been + past participle'),
        (r'\b(will|shall|can|could|may|might|must|should|would)\s+be\s+(\w+ed)\b', 'modal + be + past participle'),
        (r'\b(will|shall|can|could|may|might|must|should|would)\s+be\s+(\w+en)\b', 'modal + be + past participle'),
        (r'\b(is|are|was|were)\s+being\s+(\w+ed)\b', 'continuous passive'),
    ]
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 15:
                continue
            
            for pattern, pattern_name in self.PASSIVE_PATTERNS:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matched_text = match.group()
                    
                    # Extract the past participle
                    words = matched_text.lower().split()
                    past_participle = words[-1] if words else ''
                    
                    # Skip likely false positives
                    if past_participle in self.FALSE_POSITIVES:
                        continue
                    
                    # Use provenance tracking - note: searching case-insensitive on original text
                    issue = self.create_validated_issue(
                        severity='Low',
                        message=f'Passive voice detected: "{matched_text}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text,  # Not lowercased, using IGNORECASE in regex
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15],
                        suggestion='Consider rewriting in active voice for clarity',
                        rule_id='PAS001'
                    )
                    if issue:
                        issues.append(issue)
        
        return issues


class ContractionsChecker(BaseChecker):
    """Detects contractions (inappropriate for formal technical writing)."""
    
    CHECKER_NAME = "Contractions"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    CONTRACTIONS = {
        "don't": "do not",
        "doesn't": "does not",
        "didn't": "did not",
        "won't": "will not",
        "wouldn't": "would not",
        "couldn't": "could not",
        "shouldn't": "should not",
        "can't": "cannot",
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
        "where's": "where is",
        "we're": "we are",
        "they're": "they are",
        "you're": "you are",
        "I'm": "I am",
        "he's": "he is",
        "she's": "she is",
        "let's": "let us",
        "we've": "we have",
        "they've": "they have",
        "you've": "you have",
        "I've": "I have",
        "we'll": "we will",
        "they'll": "they will",
        "you'll": "you will",
        "I'll": "I will",
        "he'll": "he will",
        "she'll": "she will",
        "it'll": "it will",
        "we'd": "we would",
        "they'd": "they would",
        "you'd": "you would",
        "I'd": "I would",
        "he'd": "he would",
        "ain't": "is not / am not",
        "gonna": "going to",
        "wanna": "want to",
        "gotta": "got to",
    }
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        for idx, text in paragraphs:
            if not text:
                continue
            
            text_lower = text.lower()
            
            for contraction, expansion in self.CONTRACTIONS.items():
                pattern = r'\b' + re.escape(contraction) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    actual = text[match.start():match.end()]
                    
                    # Use provenance tracking
                    issue = self.create_validated_issue(
                        severity='Low',
                        message=f'Contraction found: "{actual}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15],
                        suggestion=f'Replace with: "{expansion}"',
                        rule_id='CON001',
                        original_text=actual,
                        replacement_text=expansion
                    )
                    if issue:
                        issues.append(issue)
        
        return issues


class RepeatedWordsChecker(BaseChecker):
    """Detects repeated adjacent words (e.g., 'the the')."""
    
    CHECKER_NAME = "Repeated Words"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    # Words that can legitimately be repeated
    ALLOWED_REPEATS = {'that', 'had', 'very', 'really'}
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        pattern = r'\b(\w+)\s+\1\b'
        
        for idx, text in paragraphs:
            if not text:
                continue
            
            for match in re.finditer(pattern, text, re.IGNORECASE):
                repeated_word = match.group(1)
                
                # Skip allowed repetitions
                if repeated_word.lower() in self.ALLOWED_REPEATS:
                    continue
                
                # Use provenance tracking
                issue = self.create_validated_issue(
                    severity='Medium',
                    message=f'Repeated word: "{match.group()}"',
                    paragraph_index=idx,
                    original_paragraph=text,
                    normalized_paragraph=text,  # Not normalized, using IGNORECASE
                    match_text=match.group(),
                    match_start=match.start(),
                    match_end=match.end(),
                    context=text[max(0, match.start()-10):match.end()+10],
                    suggestion=f'Remove duplicate "{repeated_word}"',
                    rule_id='REP001',
                    original_text=match.group(),
                    replacement_text=repeated_word
                )
                if issue:
                    issues.append(issue)
        
        return issues


class CapitalizationChecker(BaseChecker):
    """Checks for capitalization issues."""
    
    CHECKER_NAME = "Capitalization"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking for consistency
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        for idx, text in paragraphs:
            if not text:
                continue
            
            stripped = text.strip()
            
            # Check if paragraph starts with lowercase (excluding lists)
            if stripped and stripped[0].islower():
                # Check it's not a list continuation
                if not re.match(r'^(?:[a-z]\)|[ivx]+\)|[-•*])', stripped):
                    issues.append(self.create_issue(
                        severity='Medium',
                        message='Paragraph does not start with capital letter',
                        context=stripped[:30],
                        paragraph_index=idx,
                        suggestion='Capitalize first letter',
                        rule_id='CAP001',
                        flagged_text=stripped[:20]
                    ))
        
        return issues
