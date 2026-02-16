"""
AEGIS - Enhanced Analyzers Integration Module
Version: 1.0.0
Created: February 3, 2026

Provides BaseChecker-compatible wrappers for the v3.2.4 analysis modules:
- SemanticAnalyzerChecker - Semantic similarity and duplicate detection
- EnhancedAcronymChecker - Schwartz-Hearst algorithm for acronyms
- ProseLinterChecker - Vale-style prose quality checking
- StructureAnalyzerChecker - Document structure validation
- TextStatisticsChecker - Comprehensive text metrics

These checkers integrate with AEGIS's checker framework and can be
enabled/disabled via the standard options system.

Usage:
    # In core.py _init_checkers():
    from enhanced_analyzers import get_enhanced_analyzers
    enhanced = get_enhanced_analyzers()
    self.checkers.update(enhanced)
"""

import os
from typing import List, Dict, Any, Optional, Tuple

# Import base checker
try:
    from base_checker import BaseChecker
except ImportError:
    # Fallback for standalone testing
    class BaseChecker:
        CHECKER_NAME = "Base"
        CHECKER_VERSION = "1.0.0"
        def __init__(self, enabled=True):
            self.enabled = enabled
            self._errors = []
        def check(self, **kwargs): return []
        def safe_check(self, **kwargs):
            try: return self.check(**kwargs)
            except Exception as e:
                self._errors.append(str(e))
                return []
        def create_issue(self, severity, message, **kwargs):
            return {
                'category': self.CHECKER_NAME,
                'severity': severity,
                'message': message,
                **kwargs
            }


# =============================================================================
# SEMANTIC ANALYZER CHECKER
# =============================================================================

class SemanticAnalyzerChecker(BaseChecker):
    """
    Checker that uses Sentence-Transformers for semantic analysis.

    Detects:
    - Duplicate/near-duplicate content
    - Semantically similar but differently worded statements
    - Content that may need consolidation
    """

    CHECKER_NAME = "Semantic Analysis"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True, similarity_threshold: float = 0.85):
        super().__init__(enabled)
        self.similarity_threshold = similarity_threshold
        self._analyzer = None
        self._available = False
        self._init_analyzer()

    def _init_analyzer(self):
        """Initialize the semantic analyzer (deferred model loading for fast startup)."""
        try:
            from semantic_analyzer import SemanticAnalyzer
            self._analyzer = SemanticAnalyzer(load_model=False)  # v5.0.2: Defer model load to first use
            self._available = True
        except ImportError as e:
            self._errors.append(f"Semantic analyzer not available: {e}")
        except Exception as e:
            self._errors.append(f"Failed to initialize semantic analyzer: {e}")

    def is_available(self) -> bool:
        """Check if semantic analysis is available."""
        return self._available and self._analyzer is not None

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        full_text: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Check for semantic duplicates and similar content.

        Returns issues for:
        - Near-duplicate paragraphs (similarity > threshold)
        - Potentially redundant content
        """
        if not self.is_available():
            return []

        issues = []

        # Filter to substantial paragraphs only
        substantial = [(idx, text) for idx, text in paragraphs
                      if len(text.split()) >= 10]

        if len(substantial) < 2:
            return []

        try:
            # Extract just the text for analysis
            texts = [text for _, text in substantial]
            indices = [idx for idx, _ in substantial]

            # Find duplicates
            duplicates = self._analyzer.find_duplicates(
                texts,
                threshold=self.similarity_threshold
            )

            for dup in duplicates.get('duplicates', []):
                idx1 = dup.get('index1', 0)
                idx2 = dup.get('index2', 0)
                similarity = dup.get('similarity', 0)

                if idx1 < len(indices) and idx2 < len(indices):
                    para_idx1 = indices[idx1]
                    para_idx2 = indices[idx2]
                    text1 = texts[idx1][:100] + '...' if len(texts[idx1]) > 100 else texts[idx1]

                    issues.append(self.create_issue(
                        severity='Medium',
                        message=f'Potentially duplicate content detected ({similarity:.0%} similar to paragraph {para_idx2})',
                        context=text1,
                        paragraph_index=para_idx1,
                        suggestion='Review for redundancy and consider consolidating',
                        rule_id='SEMANTIC_DUP_001',
                        flagged_text=text1
                    ))

        except Exception as e:
            self._errors.append(f"Semantic analysis error: {e}")

        return issues

    def get_metrics(self) -> Dict[str, Any]:
        """Get semantic analysis metrics."""
        return {
            'available': self._available,
            'model': self._analyzer.model_name if self._analyzer else None,
            'threshold': self.similarity_threshold
        }

    def find_similar(self, paragraphs: List[str], query: str, top_k: int = 5) -> List[Dict]:
        """Find paragraphs similar to a query (utility method)."""
        if not self.is_available():
            return []
        return self._analyzer.find_similar(paragraphs, query, top_k)


# =============================================================================
# ENHANCED ACRONYM CHECKER
# =============================================================================

class EnhancedAcronymChecker(BaseChecker):
    """
    Enhanced acronym checker using Schwartz-Hearst algorithm.

    Improvements over basic checker:
    - Better acronym-definition pair extraction
    - Consistency checking across document
    - Detection of undefined acronyms
    - 100+ standard aerospace/defense acronyms
    """

    CHECKER_NAME = "Enhanced Acronyms"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._extractor = None
        self._available = False
        self._init_extractor()

    def _init_extractor(self):
        """Initialize the acronym extractor."""
        try:
            from acronym_extractor import AcronymExtractor
            self._extractor = AcronymExtractor()
            self._available = True
        except ImportError as e:
            self._errors.append(f"Acronym extractor not available: {e}")
        except Exception as e:
            self._errors.append(f"Failed to initialize acronym extractor: {e}")

    def is_available(self) -> bool:
        """Check if enhanced acronym extraction is available."""
        return self._available and self._extractor is not None

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        full_text: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Check for acronym issues.

        Returns issues for:
        - Undefined acronyms (used without definition)
        - Inconsistent definitions
        - First use without definition
        """
        if not self.is_available():
            return []

        issues = []

        try:
            # Extract acronyms from full text
            extraction_result = self._extractor.extract_acronyms(full_text)

            # Check for undefined acronyms
            undefined = self._extractor.find_undefined_acronyms(full_text)

            for acronym_info in undefined.get('undefined', []):
                acronym = acronym_info.get('acronym', '')
                first_use = acronym_info.get('first_occurrence', 0)

                # Find which paragraph contains this
                para_idx = 0
                char_count = 0
                for idx, text in paragraphs:
                    if char_count + len(text) > first_use:
                        para_idx = idx
                        break
                    char_count += len(text) + 1

                issues.append(self.create_issue(
                    severity='Medium',
                    message=f'Acronym "{acronym}" used without definition',
                    context=acronym,
                    paragraph_index=para_idx,
                    suggestion=f'Define "{acronym}" on first use, e.g., "Full Name ({acronym})"',
                    rule_id='ACRONYM_UNDEF_001',
                    flagged_text=acronym
                ))

            # Check for consistency issues
            consistency = self._extractor.check_consistency(full_text)

            for issue in consistency.get('issues', []):
                acronym = issue.get('acronym', '')
                definitions = issue.get('definitions', [])

                issues.append(self.create_issue(
                    severity='High',
                    message=f'Acronym "{acronym}" has inconsistent definitions: {", ".join(definitions)}',
                    context=acronym,
                    paragraph_index=0,
                    suggestion='Use a consistent definition throughout the document',
                    rule_id='ACRONYM_INCONSIST_001',
                    flagged_text=acronym
                ))

        except Exception as e:
            self._errors.append(f"Acronym extraction error: {e}")

        return issues

    def get_metrics(self) -> Dict[str, Any]:
        """Get acronym extraction metrics."""
        return {
            'available': self._available,
            'standard_acronyms_count': len(self._extractor.STANDARD_ACRONYMS) if self._extractor else 0
        }

    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extract all acronyms with definitions (utility method)."""
        if not self.is_available():
            return {'acronyms': [], 'error': 'Extractor not available'}
        return self._extractor.extract_acronyms(text)


# =============================================================================
# PROSE LINTER CHECKER
# =============================================================================

class ProseLinterChecker(BaseChecker):
    """
    Prose quality checker implementing Vale-style rules.

    Checks for:
    - Passive voice overuse
    - Nominalizations (hidden verbs)
    - Wordy phrases
    - Government/legal jargon
    - Weasel words
    - Sentence length issues
    """

    CHECKER_NAME = "Prose Quality"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True, style: str = 'technical'):
        super().__init__(enabled)
        self.style = style
        self._linter = None
        self._available = False
        self._init_linter()

    def _init_linter(self):
        """Initialize the prose linter."""
        try:
            from prose_linter import ProseLinter
            self._linter = ProseLinter(style=self.style)
            self._available = True
        except ImportError as e:
            self._errors.append(f"Prose linter not available: {e}")
        except Exception as e:
            self._errors.append(f"Failed to initialize prose linter: {e}")

    def is_available(self) -> bool:
        """Check if prose linting is available."""
        return self._available and self._linter is not None

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        full_text: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Check prose quality.

        Returns issues for style violations, wordiness, jargon, etc.
        """
        if not self.is_available():
            return []

        issues = []

        try:
            # Run linting on full text
            lint_results = self._linter.lint_text(full_text)

            # Map severity levels
            severity_map = {
                'error': 'High',
                'warning': 'Medium',
                'suggestion': 'Low',
                'info': 'Info'
            }

            for lint_issue in lint_results.get('issues', []):
                severity = severity_map.get(lint_issue.get('severity', 'info'), 'Info')

                # Find paragraph index from position
                position = lint_issue.get('position', 0)
                para_idx = 0
                char_count = 0
                for idx, text in paragraphs:
                    if char_count + len(text) > position:
                        para_idx = idx
                        break
                    char_count += len(text) + 1

                issues.append(self.create_issue(
                    severity=severity,
                    message=lint_issue.get('message', 'Prose quality issue'),
                    context=lint_issue.get('text', '')[:100],
                    paragraph_index=para_idx,
                    suggestion=lint_issue.get('suggestion', ''),
                    rule_id=lint_issue.get('rule_id', 'PROSE_001'),
                    flagged_text=lint_issue.get('text', '')
                ))

        except Exception as e:
            self._errors.append(f"Prose linting error: {e}")

        return issues

    def get_metrics(self) -> Dict[str, Any]:
        """Get prose linting metrics."""
        if not self.is_available():
            return {'available': False}

        rules = self._linter.export_rules()
        return {
            'available': self._available,
            'style': self.style,
            'rules_count': sum(rules.values())
        }


# =============================================================================
# STRUCTURE ANALYZER CHECKER
# =============================================================================

class StructureAnalyzerChecker(BaseChecker):
    """
    Document structure analyzer.

    Checks for:
    - Heading hierarchy issues (skipped levels)
    - Broken cross-references
    - TOC mismatches
    - Unreferenced figures/tables
    - Inconsistent numbering
    """

    CHECKER_NAME = "Document Structure"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._analyzer = None
        self._available = False
        self._init_analyzer()

    def _init_analyzer(self):
        """Initialize the structure analyzer."""
        try:
            from structure_analyzer import StructureAnalyzer
            self._analyzer = StructureAnalyzer()
            self._available = True
        except ImportError as e:
            self._errors.append(f"Structure analyzer not available: {e}")
        except Exception as e:
            self._errors.append(f"Failed to initialize structure analyzer: {e}")

    def is_available(self) -> bool:
        """Check if structure analysis is available."""
        return self._available and self._analyzer is not None

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        filepath: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Check document structure.

        Note: Requires filepath to analyze DOCX structure directly.
        """
        if not self.is_available():
            return []

        if not filepath or not filepath.lower().endswith('.docx'):
            return []  # Can only analyze DOCX files

        issues = []

        try:
            # Analyze document structure
            analysis = self._analyzer.analyze_docx(filepath)

            if 'error' in analysis:
                self._errors.append(analysis['error'])
                return []

            # Map structure issues to checker issues
            severity_map = {
                'error': 'High',
                'warning': 'Medium',
                'info': 'Info'
            }

            for struct_issue in analysis.get('issues', []):
                severity = severity_map.get(struct_issue.get('severity', 'warning'), 'Medium')

                issues.append(self.create_issue(
                    severity=severity,
                    message=struct_issue.get('message', 'Structure issue'),
                    context=struct_issue.get('location', ''),
                    paragraph_index=0,
                    suggestion=struct_issue.get('suggestion', ''),
                    rule_id=f"STRUCT_{struct_issue.get('issue_type', 'UNKNOWN').upper()}",
                    flagged_text=struct_issue.get('location', '')
                ))

            # Store analysis results for later retrieval
            self._last_analysis = analysis

        except Exception as e:
            self._errors.append(f"Structure analysis error: {e}")

        return issues

    def get_metrics(self) -> Dict[str, Any]:
        """Get structure analysis metrics."""
        if hasattr(self, '_last_analysis') and self._last_analysis:
            return {
                'available': self._available,
                'heading_count': self._last_analysis.get('heading_count', 0),
                'figure_count': self._last_analysis.get('figure_count', 0),
                'table_count': self._last_analysis.get('table_count', 0),
                'cross_reference_count': self._last_analysis.get('cross_reference_count', 0),
                'broken_references': self._last_analysis.get('broken_references', 0)
            }
        return {'available': self._available}

    def get_outline(self) -> str:
        """Get document outline (utility method)."""
        if hasattr(self, '_last_analysis') and self._last_analysis:
            return self._last_analysis.get('outline', '')
        return ''


# =============================================================================
# TEXT STATISTICS CHECKER
# =============================================================================

class TextStatisticsChecker(BaseChecker):
    """
    Comprehensive text statistics analyzer.

    Provides:
    - Extended readability metrics
    - Vocabulary richness analysis
    - Keyword extraction
    - Technical writing metrics

    Note: This checker doesn't produce issues - it provides metrics.
    Use get_metrics() to retrieve analysis results.
    """

    CHECKER_NAME = "Text Statistics"
    CHECKER_VERSION = "1.0.0"

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self._stats = None
        self._available = False
        self._last_analysis = None
        self._init_stats()

    def _init_stats(self):
        """Initialize the text statistics analyzer."""
        try:
            from text_statistics import TextStatistics
            self._stats = TextStatistics()
            self._available = True
        except ImportError as e:
            self._errors.append(f"Text statistics not available: {e}")
        except Exception as e:
            self._errors.append(f"Failed to initialize text statistics: {e}")

    def is_available(self) -> bool:
        """Check if text statistics is available."""
        return self._available and self._stats is not None

    def check(
        self,
        paragraphs: List[Tuple[int, str]],
        full_text: str = "",
        **kwargs
    ) -> List[Dict]:
        """
        Analyze text statistics.

        This checker doesn't produce issues - it stores metrics.
        Use get_metrics() or get_analysis() to retrieve results.
        """
        if not self.is_available():
            return []

        issues = []

        try:
            # Run full analysis
            self._last_analysis = self._stats.analyze(full_text)

            # Generate issues for extreme values
            readability = self._last_analysis.get('readability', {})
            technical = self._last_analysis.get('technical', {})

            # Flag very low readability
            flesch = readability.get('flesch_reading_ease', 50)
            if flesch < 30:
                issues.append(self.create_issue(
                    severity='Info',
                    message=f'Document has low readability score ({flesch:.1f}). Consider simplifying.',
                    context='Document-level metric',
                    paragraph_index=0,
                    suggestion='Use shorter sentences and simpler words to improve readability',
                    rule_id='STATS_READABILITY_001'
                ))

            # Flag high passive voice
            passive_pct = technical.get('passive_voice_percentage', 0)
            if passive_pct > 40:
                issues.append(self.create_issue(
                    severity='Info',
                    message=f'High passive voice usage ({passive_pct:.1f}%). Consider using more active voice.',
                    context='Document-level metric',
                    paragraph_index=0,
                    suggestion='Rewrite passive constructions in active voice for clarity',
                    rule_id='STATS_PASSIVE_001'
                ))

            # Flag high jargon
            jargon_pct = technical.get('jargon_percentage', 0)
            if jargon_pct > 15:
                issues.append(self.create_issue(
                    severity='Info',
                    message=f'High jargon density ({jargon_pct:.1f}%). Document may be difficult to read.',
                    context='Document-level metric',
                    paragraph_index=0,
                    suggestion='Consider defining technical terms or using simpler alternatives',
                    rule_id='STATS_JARGON_001'
                ))

        except Exception as e:
            self._errors.append(f"Text statistics error: {e}")

        return issues

    def get_metrics(self) -> Dict[str, Any]:
        """Get text statistics metrics."""
        if not self._last_analysis:
            return {'available': self._available}

        return {
            'available': self._available,
            'basic': self._last_analysis.get('basic', {}),
            'readability': self._last_analysis.get('readability', {}),
            'vocabulary': self._last_analysis.get('vocabulary', {}),
            'technical': self._last_analysis.get('technical', {}),
            'summary': self._last_analysis.get('summary', {})
        }

    def get_analysis(self) -> Dict[str, Any]:
        """Get full analysis results (utility method)."""
        return self._last_analysis or {}

    def get_keywords(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """Get extracted keywords (utility method)."""
        if not self._last_analysis:
            return []
        keywords = self._last_analysis.get('keywords', {})
        return keywords.get('combined_top', [])[:top_n]


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def get_enhanced_analyzers() -> Dict[str, BaseChecker]:
    """
    Get all enhanced analyzers as a dictionary.

    Use this to integrate with AEGISEngine:

        from enhanced_analyzers import get_enhanced_analyzers
        enhanced = get_enhanced_analyzers()
        self.checkers.update(enhanced)

    Returns:
        Dictionary mapping checker names to checker instances
    """
    analyzers = {}

    # Semantic analyzer
    try:
        analyzers['semantic_analysis'] = SemanticAnalyzerChecker()
    except Exception as e:
        print(f"Warning: Could not load SemanticAnalyzerChecker: {e}")

    # Enhanced acronym checker
    try:
        analyzers['enhanced_acronyms'] = EnhancedAcronymChecker()
    except Exception as e:
        print(f"Warning: Could not load EnhancedAcronymChecker: {e}")

    # Prose linter
    try:
        analyzers['prose_linting'] = ProseLinterChecker()
    except Exception as e:
        print(f"Warning: Could not load ProseLinterChecker: {e}")

    # Structure analyzer
    try:
        analyzers['structure_analysis'] = StructureAnalyzerChecker()
    except Exception as e:
        print(f"Warning: Could not load StructureAnalyzerChecker: {e}")

    # Text statistics
    try:
        analyzers['text_statistics'] = TextStatisticsChecker()
    except Exception as e:
        print(f"Warning: Could not load TextStatisticsChecker: {e}")

    return analyzers


def get_analyzer_status() -> Dict[str, bool]:
    """
    Check availability of all enhanced analyzers.

    Returns:
        Dictionary mapping analyzer names to availability status
    """
    analyzers = get_enhanced_analyzers()
    return {
        name: checker.is_available()
        for name, checker in analyzers.items()
    }


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    print("Enhanced Analyzers Integration Module")
    print("=" * 50)

    # Check availability
    status = get_analyzer_status()

    print("\nAnalyzer Availability:")
    for name, available in status.items():
        status_str = "✓ Available" if available else "✗ Not available"
        print(f"  {name}: {status_str}")

    # Get all analyzers
    analyzers = get_enhanced_analyzers()
    print(f"\nLoaded {len(analyzers)} analyzers")

    # Quick test with sample text
    sample_text = """
    The Project Manager (PM) shall coordinate with the Systems Engineer (SE)
    to ensure requirements are properly documented. The utilization of passive
    voice should be minimized in order to improve clarity. In the event that
    issues are identified, the PM will facilitate resolution.

    The contractor shall provide deliverables in accordance with the SOW.
    All CDRLs must be submitted per the CDRL schedule. The PM is responsible
    for ensuring compliance with all applicable regulations.
    """

    sample_paragraphs = [(i, p.strip()) for i, p in enumerate(sample_text.split('\n\n')) if p.strip()]

    print("\nRunning checks on sample text...")

    for name, checker in analyzers.items():
        if checker.is_available():
            issues = checker.safe_check(
                paragraphs=sample_paragraphs,
                full_text=sample_text
            )
            print(f"\n{name}: {len(issues)} issues found")
            for issue in issues[:3]:  # Show first 3
                print(f"  - [{issue.get('severity')}] {issue.get('message')[:60]}...")
