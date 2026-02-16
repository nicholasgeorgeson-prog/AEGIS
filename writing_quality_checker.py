#!/usr/bin/env python3
"""
Writing Quality Checker v2.0.0
==============================
Checks for writing quality issues:
- Weak/vague language
- Wordy phrases
- Nominalization (noun forms of verbs)
- Jargon and complex words
- Gender-neutral language
"""

import re
from typing import List, Dict, Tuple, Optional

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

__version__ = "2.6.0"


class WeakLanguageChecker(BaseChecker):
    """Detects weak and vague language."""
    
    CHECKER_NAME = "Weak Language"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    # Phrases that should NOT be flagged even though they contain weak words
    # These are common business/technical terms where the weak word is part of a proper noun or title
    EXCLUDED_PHRASES = [
        'long range strategic plan',
        'long range plan',
        'long-range',
        'low-rate initial production',
        'low rate initial production', 
        'low-rate',
        'short range',
        'short-range',
        'short term',
        'short-term',
        'long term',
        'long-term',
        'high level',
        'high-level',
        'low level',
        'low-level',
    ]
    
    WEAK_WORDS = {
        'should': ('Medium', 'Use "shall" for requirements, "will" for statements of fact'),
        'could': ('Medium', 'Be more specific about capability'),
        'might': ('High', 'Avoid uncertainty - state definitively or specify conditions'),
        'may': ('Medium', 'Clarify if permission or possibility'),
        'approximately': ('Low', 'Specify exact value or tolerance range'),
        'adequate': ('High', 'Define specific acceptance criteria'),
        'sufficient': ('High', 'Define specific criteria'),
        'reasonable': ('High', 'Define measurable criteria'),
        'significant': ('High', 'Quantify the significance'),
        'appropriate': ('Medium', 'Define what is appropriate'),
        'as needed': ('Medium', 'Specify the conditions'),
        'as required': ('Medium', 'Reference the specific requirement'),
        'as necessary': ('Medium', 'Define necessity criteria'),
        'soon': ('High', 'Specify exact timeframe'),
        'later': ('Medium', 'Specify when'),
        'periodically': ('High', 'Specify exact period (daily, weekly, etc.)'),
        'regularly': ('High', 'Specify frequency'),
        'etc': ('High', 'List all items explicitly'),
        'etc.': ('High', 'List all items explicitly'),
        'and so on': ('High', 'List all items explicitly'),
        'and/or': ('Medium', 'Use "and" or "or" - not both'),
        'fairly': ('Medium', 'Quantify instead'),
        'normally': ('Medium', 'State exceptions explicitly'),
        'typically': ('Medium', 'State exceptions explicitly'),
        'usually': ('Medium', 'State exceptions explicitly'),
        'generally': ('Medium', 'Be specific'),
        'some': ('Low', 'Specify quantity when possible'),
        'several': ('Low', 'Specify exact number'),
        'many': ('Low', 'Specify quantity'),
        'few': ('Low', 'Specify quantity'),
        'various': ('Low', 'List the specific items'),
        'mostly': ('Medium', 'State what/when exceptions occur'),
        'often': ('Medium', 'Specify frequency'),
        'sometimes': ('Medium', 'Specify conditions when this occurs'),
        'almost': ('Medium', 'Be precise'),
        'nearly': ('Medium', 'Be precise'),
        'about': ('Low', 'Be more specific when referring to quantities'),
        'roughly': ('Medium', 'Specify exact value or range'),
        'relatively': ('Medium', 'Compared to what?'),
        'quite': ('Low', 'Be more specific'),
        'rather': ('Low', 'Be more specific'),
        'somewhat': ('Medium', 'Be more specific'),
        'particular': ('Low', 'Specify which'),
        'certain': ('Medium', 'Specify which'),
        'proper': ('Medium', 'Define what is proper'),
        'suitable': ('Medium', 'Define suitability criteria'),
        'acceptable': ('Medium', 'Define acceptance criteria'),
        'satisfactory': ('Medium', 'Define what satisfies'),
        'good': ('Medium', 'Define criteria'),
        'bad': ('Medium', 'Define criteria'),
        'best': ('Medium', 'Define criteria or provide comparison'),
        'better': ('Low', 'Better than what?'),
        'easy': ('Low', 'For whom? Under what conditions?'),
        'difficult': ('Low', 'Define difficulty criteria'),
        'simple': ('Low', 'Define simplicity'),
        'complex': ('Low', 'Explain the complexity'),
        'large': ('Low', 'Specify size'),
        'small': ('Low', 'Specify size'),
        'long': ('Low', 'Specify length/duration'),
        'short': ('Low', 'Specify length/duration'),
        'high': ('Low', 'Specify level'),
        'low': ('Low', 'Specify level'),
        'fast': ('Low', 'Specify speed'),
        'slow': ('Low', 'Specify speed'),
        'quickly': ('Low', 'Specify timeframe'),
        'timely': ('Medium', 'Specify timeframe'),
        'prompt': ('Medium', 'Specify timeframe'),
        'efficient': ('Medium', 'Define efficiency metrics'),
        'effective': ('Medium', 'Define effectiveness criteria'),
        'optimal': ('Medium', 'Define optimization criteria'),
    }
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        # Get special sections to skip
        special_sections = kwargs.get('special_sections', {})
        skip_indices = set()
        for section_type, indices in special_sections.items():
            skip_indices.update(indices)
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue
            
            # Skip if in special section (acronyms, definitions, references)
            if idx in skip_indices:
                continue
            
            # Skip if this looks like an acronym definition line
            # e.g., "LRSP - Long Range Strategic Plan" or "AOP    Annual Operating Plan"
            if re.match(r'^\s*[A-Z]{2,}[\s\-–—:]+[A-Z]', text):
                continue
            
            # Skip boilerplate lines
            text_upper = text.upper().strip()
            if any(bp in text_upper for bp in ['EFFECTIVE DATE', 'REVIEW DATE', 'DOCUMENT NO', 'PAGE', 'SUPERSEDES']):
                continue
            
            # Skip if this is part of an acronym table (multiple acronyms on adjacent lines)
            # Check if line starts with acronym pattern and has definition
            if re.match(r'^[A-Z]{2,}\s{2,}[A-Z]', text.strip()):
                continue
            
            text_lower = text.lower()
            
            for word, (severity, suggestion) in self.WEAK_WORDS.items():
                pattern = r'\b' + re.escape(word) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    actual_word = text[match.start():match.end()]
                    
                    # Get surrounding context to check if in acronym definition or excluded phrase
                    start = max(0, match.start() - 40)
                    end = min(len(text), match.end() + 40)
                    context = text[start:end]
                    context_lower = context.lower()
                    
                    # Skip if this word is part of an excluded phrase
                    skip = False
                    for excluded in self.EXCLUDED_PHRASES:
                        if excluded in context_lower:
                            skip = True
                            break
                    if skip:
                        continue
                    
                    # Skip if the match is within an acronym definition pattern
                    # Look for pattern like "XXXX - ... word ..." or "XXXX    word..."
                    if re.search(r'[A-Z]{2,}\s*[-–—:]\s*[^-]*\b' + re.escape(actual_word), context, re.IGNORECASE):
                        continue
                    if re.search(r'^[A-Z]{2,}\s{2,}.*\b' + re.escape(actual_word), context, re.IGNORECASE):
                        continue
                    
                    # Use provenance tracking to validate match exists in original
                    issue = self.create_validated_issue(
                        severity=severity,
                        message=f'Weak/vague word: "{actual_word}"',
                        paragraph_index=idx,
                        original_paragraph=text,        # Original text from document
                        normalized_paragraph=text_lower, # Normalized (lowercased) text
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0, match.start()-20):match.end()+20],
                        suggestion=suggestion,
                        rule_id='WL001'
                    )
                    if issue:  # Only add if validated against original
                        issues.append(issue)
        
        return issues


class WordyPhrasesChecker(BaseChecker):
    """Detects wordy phrases that can be simplified."""
    
    CHECKER_NAME = "Wordy Phrases"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    WORDY_PHRASES = {
        'in order to': ('to', 'Low'),
        'in order for': ('for', 'Low'),
        'at this point in time': ('now', 'Medium'),
        'at the present time': ('now', 'Medium'),
        'at this time': ('now', 'Low'),
        'due to the fact that': ('because', 'Medium'),
        'owing to the fact that': ('because', 'Medium'),
        'in light of the fact that': ('because', 'Medium'),
        'on account of the fact that': ('because', 'Medium'),
        'in the event that': ('if', 'Medium'),
        'in the event of': ('if', 'Low'),
        'for the purpose of': ('to', 'Medium'),
        'with the purpose of': ('to', 'Medium'),
        'with regard to': ('about', 'Low'),
        'with regards to': ('about', 'Low'),
        'in regard to': ('about', 'Low'),
        'with respect to': ('about', 'Low'),
        'in reference to': ('about', 'Low'),
        'in relation to': ('about', 'Low'),
        'pertaining to': ('about', 'Low'),
        'in accordance with': ('per', 'Low'),
        'in compliance with': ('per', 'Low'),
        'prior to': ('before', 'Low'),
        'previous to': ('before', 'Low'),
        'in advance of': ('before', 'Low'),
        'subsequent to': ('after', 'Low'),
        'at a later date': ('later', 'Low'),
        'a large number of': ('many', 'Low'),
        'a small number of': ('few', 'Low'),
        'a majority of': ('most', 'Low'),
        'a sufficient number of': ('enough', 'Low'),
        'in the near future': ('soon', 'Low'),
        'it is important to note that': ('importantly,', 'Medium'),
        'it should be noted that': ('note that', 'Medium'),
        'it is worth noting that': ('note that', 'Medium'),
        'needless to say': ('(delete)', 'Medium'),
        'it goes without saying': ('(delete)', 'Medium'),
        'as a matter of fact': ('in fact', 'Low'),
        'the fact that': ('that', 'Low'),
        'despite the fact that': ('although', 'Low'),
        'until such time as': ('until', 'Medium'),
        'during the course of': ('during', 'Low'),
        'during the time that': ('while', 'Low'),
        'in the process of': ('(delete or use verb)', 'Medium'),
        'is able to': ('can', 'Low'),
        'is unable to': ('cannot', 'Low'),
        'has the ability to': ('can', 'Medium'),
        'has the capability to': ('can', 'Medium'),
        'is capable of': ('can', 'Low'),
        'make a decision': ('decide', 'Low'),
        'make a determination': ('determine', 'Low'),
        'make an assumption': ('assume', 'Low'),
        'reach a conclusion': ('conclude', 'Low'),
        'come to a conclusion': ('conclude', 'Low'),
        'conduct an investigation': ('investigate', 'Medium'),
        'conduct an analysis': ('analyze', 'Medium'),
        'perform an analysis': ('analyze', 'Medium'),
        'conduct a review': ('review', 'Medium'),
        'perform a review': ('review', 'Medium'),
        'give consideration to': ('consider', 'Medium'),
        'take into consideration': ('consider', 'Medium'),
        'provide assistance': ('assist', 'Low'),
        'provide support': ('support', 'Low'),
        'make use of': ('use', 'Low'),
        'utilize': ('use', 'Low'),
        'on a daily basis': ('daily', 'Low'),
        'on a weekly basis': ('weekly', 'Low'),
        'on a monthly basis': ('monthly', 'Low'),
        'on a regular basis': ('regularly', 'Low'),
        'whether or not': ('whether', 'Low'),
        'each and every': ('each', 'Low'),
        'any and all': ('all', 'Low'),
        'first and foremost': ('first', 'Low'),
        'full and complete': ('complete', 'Low'),
        'by means of': ('by', 'Low'),
        'in spite of': ('despite', 'Low'),
        'in case of': ('if', 'Low'),
        'in terms of': ('(rephrase)', 'Low'),
        'in the amount of': ('for', 'Low'),
        'in the vicinity of': ('near', 'Low'),
        'in close proximity to': ('near', 'Medium'),
        'take action': ('act', 'Low'),
        'take steps': ('act', 'Low'),
        'make changes': ('change', 'Low'),
        'make improvements': ('improve', 'Low'),
    }
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue
            
            text_lower = text.lower()
            
            for phrase, (replacement, severity) in self.WORDY_PHRASES.items():
                pattern = r'\b' + re.escape(phrase) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    actual_phrase = text[match.start():match.end()]
                    
                    # Use provenance tracking to validate match exists in original
                    issue = self.create_validated_issue(
                        severity=severity,
                        message=f'Wordy phrase: "{actual_phrase}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15],
                        suggestion=f'Replace with: "{replacement}"',
                        rule_id='WP001',
                        original_text=actual_phrase,
                        replacement_text=replacement if replacement != '(delete)' and replacement != '(rephrase)' else ''
                    )
                    if issue:
                        issues.append(issue)
        
        return issues


class NominalizationChecker(BaseChecker):
    """Detects nominalizations (noun forms of verbs that weaken writing)."""
    
    CHECKER_NAME = "Nominalization"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    NOMINALIZATIONS = {
        'decision': 'decide',
        'conclusion': 'conclude',
        'recommendation': 'recommend',
        'suggestion': 'suggest',
        'assumption': 'assume',
        'determination': 'determine',
        'evaluation': 'evaluate',
        'investigation': 'investigate',
        'examination': 'examine',
        'consideration': 'consider',
        'implementation': 'implement',
        'utilization': 'use',
        'authorization': 'authorize',
        'modification': 'modify',
        'verification': 'verify',
        'validation': 'validate',
        'notification': 'notify',
        'calculation': 'calculate',
        'estimation': 'estimate',
        'explanation': 'explain',
        'indication': 'indicate',
        'preparation': 'prepare',
        'establishment': 'establish',
        'development': 'develop',
        'assessment': 'assess',
        'measurement': 'measure',
        'improvement': 'improve',
        'enhancement': 'enhance',
        'allocation': 'allocate',
        'identification': 'identify',
        'specification': 'specify',
        'clarification': 'clarify',
        'completion': 'complete',
        'approval': 'approve',
        'submission': 'submit',
        'execution': 'execute',
        'achievement': 'achieve',
        'agreement': 'agree',
        'requirement': 'require',
        'replacement': 'replace',
        'arrangement': 'arrange',
        'management': 'manage',
        'commitment': 'commit',
        'adjustment': 'adjust',
        'announcement': 'announce',
        'statement': 'state',
    }
    
    # Verbose patterns that indicate nominalization is being used weakly
    VERBOSE_PATTERNS = [
        r'make\s+(?:a|an|the)\s+',
        r'made\s+(?:a|an|the)\s+',
        r'conduct\s+(?:a|an|the)\s+',
        r'conducted\s+(?:a|an|the)\s+',
        r'perform\s+(?:a|an|the)\s+',
        r'performed\s+(?:a|an|the)\s+',
        r'carry\s+out\s+(?:a|an|the)\s+',
        r'give\s+(?:a|an)\s+',
        r'gave\s+(?:a|an)\s+',
        r'take\s+(?:a|an|the)\s+',
        r'took\s+(?:a|an|the)\s+',
        r'provide\s+(?:a|an)\s+',
        r'reach\s+(?:a|an|the)\s+',
        r'come\s+to\s+(?:a|an|the)\s+',
        r'arrive\s+at\s+(?:a|an|the)\s+',
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
            
            text_lower = text.lower()
            
            for noun, verb in self.NOMINALIZATIONS.items():
                for verbose_pattern in self.VERBOSE_PATTERNS:
                    full_pattern = verbose_pattern + re.escape(noun) + r'\b'
                    for match in re.finditer(full_pattern, text_lower):
                        actual_text = text[match.start():match.end()]
                        
                        # Use provenance tracking
                        issue = self.create_validated_issue(
                            severity='Medium',
                            message=f'Verbose nominalization: "{actual_text}"',
                            paragraph_index=idx,
                            original_paragraph=text,
                            normalized_paragraph=text_lower,
                            match_text=match.group(),
                            match_start=match.start(),
                            match_end=match.end(),
                            context=text[max(0, match.start()-10):match.end()+10],
                            suggestion=f'Consider using the verb form: "{verb}"',
                            rule_id='NOM001'
                        )
                        if issue:
                            issues.append(issue)
        
        return issues


class JargonChecker(BaseChecker):
    """Detects jargon and overly complex words with simpler alternatives."""
    
    CHECKER_NAME = "Jargon"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    JARGON_WORDS = {
        # NOTE: Removed common business/technical terms that are standard in corporate documents
        # 'interface', 'deliverable', 'scalable', 'robust' are industry-standard terms
        'utilize': ('use', 'Low'),
        'utilization': ('use', 'Low'),
        'facilitate': ('help', 'Info'),  # Downgraded - common in government docs
        'facilitation': ('help', 'Info'),
        'synergy': ('cooperation', 'Medium'),
        'synergize': ('cooperate', 'Medium'),
        'paradigm': ('model', 'Medium'),
        'incentivize': ('encourage', 'Medium'),
        'actualize': ('achieve', 'Medium'),
        'conceptualize': ('imagine', 'Medium'),
        'operationalize': ('put into practice', 'Medium'),
        'strategize': ('plan', 'Medium'),
        'ideate': ('think of ideas', 'High'),
        'liaise': ('coordinate with', 'Info'),  # Downgraded - common term
        'touchpoint': ('contact', 'Medium'),
        'bandwidth': ('capacity/time', 'Medium'),
        'learnings': ('lessons', 'Medium'),
        'actionable': ('practical', 'Medium'),
        'impactful': ('effective', 'Medium'),
        'best-in-class': ('leading', 'Medium'),
        'cutting-edge': ('advanced', 'Medium'),
        'state-of-the-art': ('latest', 'Medium'),
        'mission-critical': ('essential', 'Info'),  # Downgraded - valid aerospace term
        'value-added': ('beneficial', 'Medium'),
        'win-win': ('mutually beneficial', 'Medium'),
        'low-hanging fruit': ('easy wins', 'Medium'),
        'circle back': ('follow up', 'Medium'),
        'drill down': ('examine in detail', 'Medium'),
        'deep dive': ('detailed analysis', 'Info'),  # Downgraded - common term
        'pain point': ('problem', 'Medium'),
        'value proposition': ('benefit', 'Medium'),
        'wheelhouse': ('expertise', 'Medium'),
        'disambiguate': ('clarify', 'Medium'),
        'heretofore': ('until now', 'Medium'),
        'hereinafter': ('from now on', 'Medium'),
        'herewith': ('with this', 'Medium'),
        'irregardless': ('regardless', 'High'),
    }
    
    # Terms that look like jargon but are actually standard in technical/government documents
    SKIP_JARGON = frozenset({
        'interface', 'interfaces', 'interfacing',  # Standard technical term
        'deliverable', 'deliverables',  # Standard contract term
        'leverage', 'leveraging',  # Often valid (leveraging resources)
        'methodology', 'methodologies',  # Valid technical term
        'functionality',  # Valid software/systems term
        'scalable', 'scalability',  # Valid technical term
        'robust', 'robustness',  # Valid engineering term
        'proactive', 'proactively',  # Common professional term
        'streamline', 'streamlined',  # Common process term
        'finalize', 'finalizing', 'finalized',  # Standard term
        'initialize', 'initializing', 'initialized',  # Valid programming term
        'remediate', 'remediation',  # Valid technical term
        'notwithstanding',  # Valid legal/contract term
        'holistic',  # Valid systems engineering term
        'granular', 'granularity',  # Valid technical term
        'ecosystem',  # Valid in technical contexts
        'pivot',  # Valid term
        'cadence',  # Valid schedule term
        'takeaways',  # Common meeting/presentation term
        'dialogue',  # Valid term
        'aforementioned',  # Valid legal/technical reference
    })
    
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
    
    def check(self, paragraphs: List[Tuple[int, str]], **kwargs) -> List[Dict]:
        if not self.enabled:
            return []
        
        issues = []
        
        # Get special sections to skip
        special_sections = kwargs.get('special_sections', {})
        skip_indices = set()
        for section_type, indices in special_sections.items():
            skip_indices.update(indices)
        
        for idx, text in paragraphs:
            if not text or len(text.strip()) < 10:
                continue
            
            # Skip if in special section (acronyms, definitions, references)
            if idx in skip_indices:
                continue
            
            # Skip if this looks like an acronym definition line
            if re.match(r'^\s*[A-Z]{2,}\s*[-–—:]\s*', text):
                continue
            
            text_lower = text.lower()
            
            for jargon, (replacement, severity) in self.JARGON_WORDS.items():
                # Skip terms that are standard in technical/government documents
                if jargon in self.SKIP_JARGON:
                    continue
                    
                pattern = r'\b' + re.escape(jargon) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    actual_word = text[match.start():match.end()]
                    
                    # Use provenance tracking
                    issue = self.create_validated_issue(
                        severity=severity,
                        message=f'Jargon/complex word: "{actual_word}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15],
                        suggestion=f'Consider simpler alternative: "{replacement}"',
                        rule_id='JAR001',
                        original_text=actual_word,
                        replacement_text=replacement
                    )
                    if issue:
                        issues.append(issue)
        
        return issues


class GenderLanguageChecker(BaseChecker):
    """Detects non-gender-neutral language."""
    
    CHECKER_NAME = "Gender-Neutral"
    CHECKER_VERSION = "2.1.0"  # v2.1.0: Added provenance tracking
    
    GENDERED_TERMS = {
        'he/she': ('they', 'Low'),
        'she/he': ('they', 'Low'),
        'his/her': ('their', 'Low'),
        'her/his': ('their', 'Low'),
        'him/her': ('them', 'Low'),
        'her/him': ('them', 'Low'),
        's/he': ('they', 'Low'),
        'manpower': ('workforce', 'Low'),
        'man-hours': ('person-hours', 'Low'),
        'manhours': ('person-hours', 'Low'),
        'manmade': ('manufactured', 'Low'),
        'man-made': ('manufactured', 'Low'),
        'mankind': ('humanity', 'Low'),
        'manned': ('staffed', 'Low'),
        'unmanned': ('uncrewed', 'Low'),
        'chairman': ('chair', 'Low'),
        'chairwoman': ('chair', 'Low'),
        'fireman': ('firefighter', 'Low'),
        'policeman': ('police officer', 'Low'),
        'policewoman': ('police officer', 'Low'),
        'mailman': ('mail carrier', 'Low'),
        'salesman': ('salesperson', 'Low'),
        'saleswoman': ('salesperson', 'Low'),
        'businessman': ('businessperson', 'Low'),
        'businesswoman': ('businessperson', 'Low'),
        'foreman': ('supervisor', 'Low'),
        'workman': ('worker', 'Low'),
        'freshman': ('first-year student', 'Low'),
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
            
            for term, (replacement, severity) in self.GENDERED_TERMS.items():
                pattern = r'\b' + re.escape(term) + r'\b'
                for match in re.finditer(pattern, text_lower):
                    actual_term = text[match.start():match.end()]
                    
                    # Use provenance tracking
                    issue = self.create_validated_issue(
                        severity=severity,
                        message=f'Non-gender-neutral term: "{actual_term}"',
                        paragraph_index=idx,
                        original_paragraph=text,
                        normalized_paragraph=text_lower,
                        match_text=match.group(),
                        match_start=match.start(),
                        match_end=match.end(),
                        context=text[max(0, match.start()-15):match.end()+15],
                        suggestion=f'Consider using: "{replacement}"',
                        rule_id='GEN001',
                        original_text=actual_term,
                        replacement_text=replacement
                    )
                    if issue:
                        issues.append(issue)
        
        return issues
