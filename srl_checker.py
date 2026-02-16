#!/usr/bin/env python3
"""
Semantic Role Labeling Checker v1.0.0
======================================
Uses spaCy dependency parsing to analyze sentence structure in requirements.

Identifies:
- Missing or unclear agents (who is doing the action)
- Missing or unclear objects/targets (what is being acted upon)
- Passive voice that obscures responsibility
- Incomplete semantic roles in requirement statements

Parses requirement sentences to identify:
- Agent: Who is responsible (e.g., "The system", "The contractor")
- Action: What they must do (verb)
- Object: What they act upon
- Constraints: Conditions or limitations

No external libraries required beyond spaCy (which AEGIS already uses).
"""

import re
from typing import Dict, List, Tuple, Optional, NamedTuple

try:
    from base_checker import BaseChecker
except ImportError:
    from .base_checker import BaseChecker

try:
    from nlp_utils import get_spacy_model
except ImportError:
    def get_spacy_model(name='en_core_web_sm'):
        """Fallback if nlp_utils not available."""
        try:
            import spacy
            return spacy.load(name)
        except:
            return None

__version__ = "1.0.0"


class SemanticRole(NamedTuple):
    """Semantic role identified in a sentence."""
    agent: str  # Who
    action: str  # What
    object: str  # Acted upon
    has_agent: bool
    has_action: bool
    has_object: bool
    voice: str  # 'active' or 'passive'


class SemanticRoleAnalysisChecker(BaseChecker):
    """
    Analyzes semantic structure of requirement sentences.

    Validates that requirements have clear semantic roles:
    - Agent (actor/responsible party)
    - Action (verb/obligation)
    - Object (target/what is acted upon)

    Uses spaCy dependency parsing to identify these roles without
    requiring heavy NLP models.
    """

    CHECKER_NAME = "Semantic Role Analysis"
    CHECKER_VERSION = "1.0.0"

    # Requirement indicator patterns
    REQUIREMENT_PATTERN = re.compile(r'\b(shall|must|will|should)\b', re.IGNORECASE)

    # Common subjects/agents in requirements
    VALID_AGENTS = {
        'system', 'software', 'hardware', 'contractor', 'developer',
        'operator', 'user', 'manager', 'team', 'organization',
        'supplier', 'vendor', 'government', 'customer', 'stakeholder',
        'interface', 'module', 'component', 'subsystem',
    }

    # Action verbs commonly used in requirements
    REQUIREMENT_VERBS = {
        'provide', 'deliver', 'ensure', 'maintain', 'verify', 'validate',
        'test', 'perform', 'execute', 'process', 'transmit', 'receive',
        'store', 'retrieve', 'generate', 'create', 'delete', 'update',
        'monitor', 'control', 'manage', 'handle', 'process', 'calculate',
        'determine', 'detect', 'identify', 'recover', 'support', 'enable',
        'prevent', 'allow', 'include', 'exclude', 'implement', 'deploy',
    }

    # Passive voice indicators
    PASSIVE_VOICE_WORDS = {'be', 'been', 'being', 'is', 'are', 'was', 'were'}

    # Weak/unclear object patterns
    WEAK_OBJECTS = {'it', 'this', 'that', 'these', 'those', 'them', 'something', ''}

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.nlp = None
        self.spacy_available = self._init_nlp()

    def _init_nlp(self) -> bool:
        """Initialize spaCy for dependency parsing."""
        try:
            self.nlp = get_spacy_model('en_core_web_sm')
            return self.nlp is not None
        except Exception:
            return False

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        tables: List[Dict] = None,
        full_text: str = "",
        filepath: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Analyze semantic roles in requirement sentences.

        Args:
            paragraphs: List of (index, text) tuples
            tables: Table data (unused)
            full_text: Complete document text (unused)
            filepath: File path (unused)

        Returns:
            List of ReviewIssue dicts
        """
        if not self.enabled:
            return []

        issues = []

        for idx, text in paragraphs:
            if len(text.strip()) < 40:
                continue

            # Skip non-requirement paragraphs
            if not self.REQUIREMENT_PATTERN.search(text):
                continue

            # Analyze semantic roles
            if self.spacy_available:
                issues.extend(self._analyze_with_spacy(text, idx))
            else:
                issues.extend(self._analyze_with_patterns(text, idx))

        return issues[:20]

    def _analyze_with_spacy(self, text: str, paragraph_idx: int) -> List[Dict]:
        """Use spaCy for semantic role analysis."""
        issues = []

        try:
            doc = self.nlp(text)

            # Analyze each sentence
            for sent in doc.sents:
                sent_text = sent.text.strip()

                # Check if this is a requirement sentence
                if not self.REQUIREMENT_PATTERN.search(sent_text):
                    continue

                # Extract semantic roles
                srl = self._extract_semantic_roles(sent)

                # Check for missing or unclear roles
                if not srl.has_agent or srl.agent.lower() in self.WEAK_OBJECTS:
                    issues.append(self.create_issue(
                        severity='High',
                        message='Requirement missing clear agent/actor',
                        context=sent_text[:80],
                        paragraph_index=paragraph_idx,
                        suggestion='Clarify who is responsible: "The system shall...", "The contractor shall...", "The operator shall..."',
                        rule_id='SRL001',
                        flagged_text=srl.agent or '[missing]'
                    ))

                elif not srl.has_action or srl.action.lower() in {'be', 'is', 'are'}:
                    issues.append(self.create_issue(
                        severity='High',
                        message='Requirement missing clear action verb',
                        context=sent_text[:80],
                        paragraph_index=paragraph_idx,
                        suggestion='Use specific action verbs: provide, verify, ensure, deliver, maintain, test, validate',
                        rule_id='SRL002',
                        flagged_text=srl.action or '[missing]'
                    ))

                elif not srl.has_object or srl.object.lower() in self.WEAK_OBJECTS:
                    issues.append(self.create_issue(
                        severity='Medium',
                        message='Requirement missing clear object/target',
                        context=sent_text[:80],
                        paragraph_index=paragraph_idx,
                        suggestion='Specify what the action applies to. Replace pronouns with explicit nouns.',
                        rule_id='SRL003',
                        flagged_text=srl.object or '[missing]'
                    ))

                elif srl.voice == 'passive':
                    issues.append(self.create_issue(
                        severity='Medium',
                        message='Requirement uses passive voice (obscures responsibility)',
                        context=sent_text[:80],
                        paragraph_index=paragraph_idx,
                        suggestion=f'Rewrite in active voice: "{srl.agent} shall {srl.action} {srl.object}"',
                        rule_id='SRL004',
                        flagged_text='[passive voice]'
                    ))

        except Exception:
            return self._analyze_with_patterns(text, paragraph_idx)

        return issues

    def _analyze_with_patterns(self, text: str, paragraph_idx: int) -> List[Dict]:
        """Pattern-based fallback semantic analysis."""
        issues = []

        # Simple pattern: "Agent shall verb object"
        pattern = r'(.*?)\s+(?:shall|must|will|should)\s+(\w+)\s+(.*?)(?:\.|$)'
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            agent = match.group(1).strip()
            action = match.group(2).strip()
            obj = match.group(3).strip()

            # Clean up agent
            agent = re.sub(r'^(?:The|A|An)\s+', '', agent, flags=re.IGNORECASE)
            # Clean up object
            obj = re.sub(r'\s+when.*$', '', obj, flags=re.IGNORECASE)

            # Check for missing/weak components
            if not agent or agent.lower() in self.WEAK_OBJECTS:
                issues.append(self.create_issue(
                    severity='High',
                    message='Requirement missing clear agent/actor',
                    context=text[:80],
                    paragraph_index=paragraph_idx,
                    suggestion='Clarify who is responsible: "The system shall...", "The contractor shall...",etc.',
                    rule_id='SRL005',
                    flagged_text='[missing]'
                ))

            if not action or action.lower() not in self.REQUIREMENT_VERBS:
                issues.append(self.create_issue(
                    severity='Medium',
                    message='Action verb may be weak or unclear',
                    context=text[:80],
                    paragraph_index=paragraph_idx,
                    suggestion='Use strong, specific action verbs: provide, verify, ensure, deliver, maintain',
                    rule_id='SRL006',
                    flagged_text=action or '[missing]'
                ))

            if not obj or obj.lower() in self.WEAK_OBJECTS:
                issues.append(self.create_issue(
                    severity='Low',
                    message='Requirement target/object may be unclear',
                    context=text[:80],
                    paragraph_index=paragraph_idx,
                    suggestion='Specify what the action applies to. Avoid pronouns like "it" or "this".',
                    rule_id='SRL007',
                    flagged_text=obj or '[missing]'
                ))

            # Check for passive voice (indicator: verb ends in -ed or -en)
            if re.search(r'\b(?:is|are|was|were)\s+\w+(?:ed|en)\b', text):
                issues.append(self.create_issue(
                    severity='Low',
                    message='Passive voice detected',
                    context=text[:80],
                    paragraph_index=paragraph_idx,
                    suggestion='Use active voice to clarify responsibility: "Agent shall verb object"',
                    rule_id='SRL008',
                    flagged_text='[passive]'
                ))

        return issues

    def _extract_semantic_roles(self, sent) -> SemanticRole:
        """
        Extract semantic roles from spaCy-parsed sentence.

        Returns: SemanticRole with identified agent, action, object
        """
        agent = ""
        action = ""
        obj = ""
        has_agent = False
        has_action = False
        has_object = False
        voice = "active"

        try:
            # Find the main verb (ROOT or highest level verb)
            verb_token = None
            for token in sent:
                if token.pos_ == 'VERB' or (token.dep_ == 'ROOT' and token.pos_ in ['VERB', 'AUX']):
                    verb_token = token
                    break

            if verb_token:
                action = verb_token.text
                has_action = True

                # Check for passive voice
                if verb_token.lemma_ in self.PASSIVE_VOICE_WORDS:
                    voice = 'passive'

                # Find subject (agent) - look for nsubj or nsubjpass
                for child in verb_token.head.children if verb_token.head else []:
                    if child.dep_ in ['nsubj', 'nsubjpass']:
                        # Get full noun phrase
                        agent = ' '.join([t.text for t in child.subtree])
                        has_agent = True
                        break

                # If no subject found via head, search all tokens
                if not has_agent:
                    for token in sent:
                        if token.dep_ in ['nsubj', 'nsubjpass']:
                            agent = ' '.join([t.text for t in token.subtree])
                            has_agent = True
                            break

                # Find object - look for dobj, pobj, nmod
                for child in verb_token.children:
                    if child.dep_ in ['dobj', 'pobj', 'nmod']:
                        obj = ' '.join([t.text for t in child.subtree])
                        has_object = True
                        break

        except Exception:
            pass

        return SemanticRole(
            agent=agent,
            action=action,
            object=obj,
            has_agent=has_agent,
            has_action=has_action,
            has_object=has_object,
            voice=voice
        )


def get_srl_checkers() -> Dict[str, BaseChecker]:
    """Factory function returning semantic role analysis checker."""
    return {
        'semantic_role_analysis': SemanticRoleAnalysisChecker(),
    }


# Standalone test
if __name__ == '__main__':
    print(f"Semantic Role Labeling Checker v{__version__}")
    print("=" * 50)

    test_paragraphs = [
        (0, "The system shall provide real-time monitoring of all flight parameters."),
        (1, "It shall be maintained to ensure compliance with requirements."),
        (2, "The contractor must deliver monthly status reports."),
        (3, "Shall be implemented within 30 days of contract award."),
        (4, "The operator will verify all inputs and validate outputs."),
    ]

    checker = SemanticRoleAnalysisChecker()
    print(f"spaCy available: {checker.spacy_available}\n")

    issues = checker.check(test_paragraphs)
    print(f"Found {len(issues)} semantic role issues:\n")

    for issue in issues:
        print(f"[{issue['severity']}] {issue['message']}")
        print(f"  Context: {issue['context'][:60]}...")
        print()
