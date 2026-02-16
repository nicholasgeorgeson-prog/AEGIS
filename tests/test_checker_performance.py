#!/usr/bin/env python3
"""
Performance Test Suite for AEGIS Checkers
=====================================================
Tests the performance of all 84 checkers on documents of varying sizes.

Run with: pytest tests/test_checker_performance.py -v -s

Created: 2026-02-03
Version: 3.4.0
"""

import os
import sys
import time
import pytest
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import AEGISEngine


@dataclass
class PerformanceResult:
    """Stores performance test results."""
    document_name: str
    document_size_kb: float
    word_count: int
    total_time_ms: float
    checker_count: int
    issue_count: int
    avg_time_per_checker_ms: float
    issues_per_second: float


class TestCheckerPerformance:
    """Performance tests for document checkers."""

    # Test documents directory
    TEST_DOCS_DIR = Path(__file__).parent.parent / 'test_documents'

    # Performance thresholds
    MAX_TIME_PER_1K_WORDS_MS = 500  # Max 500ms per 1000 words
    MAX_TOTAL_TIME_SMALL_DOC_MS = 5000  # Max 5 seconds for small docs
    MAX_TOTAL_TIME_LARGE_DOC_MS = 60000  # Max 60 seconds for large docs

    @pytest.fixture
    def checker(self):
        """Create a AEGISEngine instance."""
        return AEGISEngine()

    def get_test_documents(self) -> List[Path]:
        """Get available test documents."""
        docs = []
        if self.TEST_DOCS_DIR.exists():
            for pattern in ['*.docx', '*.pdf']:
                docs.extend(self.TEST_DOCS_DIR.glob(pattern))
        return sorted(docs, key=lambda p: p.stat().st_size)

    def run_checker_benchmark(self, checker: AEGISEngine, doc_path: Path) -> PerformanceResult:
        """Run all checkers on a document and measure performance."""
        # Read document
        with open(doc_path, 'rb') as f:
            content = f.read()

        doc_size_kb = len(content) / 1024

        # Enable all checkers
        options = {
            'check_spelling': True,
            'check_grammar': True,
            'check_acronyms': True,
            'check_passive_voice': True,
            'check_weak_language': True,
            'check_wordy_phrases': True,
            'check_nominalization': True,
            'check_jargon': True,
            'check_ambiguous_pronouns': True,
            'check_requirements_language': True,
            'check_gender_language': True,
            'check_punctuation': True,
            'check_sentence_length': True,
            'check_repeated_words': True,
            'check_capitalization': True,
            'check_contractions': True,
            'check_references': True,
            'review_document_structure': True,
            'check_tables_figures': True,
            'check_track_changes': True,
            'check_consistency': True,
            'check_lists': True,
            'check_tbd': True,
            'check_testability': True,
            'check_atomicity': True,
            'check_escape_clauses': True,
            'check_hyperlinks': True,
            'check_orphan_headings': True,
            'check_empty_sections': True,
            # v3.2.4 Enhanced Analyzers
            'check_semantic_analysis': True,
            'check_enhanced_acronyms': True,
            'check_prose_linting': True,
            'check_structure_analysis': True,
            'check_text_statistics': True,
            # v3.3.0 NLP Suite
            'check_enhanced_passive': True,
            'check_fragments_v2': True,
            'check_requirements_analysis': True,
            'check_terminology_consistency': True,
            'check_cross_references': True,
            'check_technical_dictionary': True,
            # v3.4.0 Maximum Coverage Suite
            'check_heading_case': True,
            'check_contraction_consistency': True,
            'check_oxford_comma': True,
            'check_ari': True,
            'check_spache': True,
            'check_dale_chall': True,
            'check_future_tense': True,
            'check_latin_abbreviations': True,
            'check_sentence_initial_conjunction': True,
            'check_directional_language': True,
            'check_time_sensitive_language': True,
            'check_acronym_first_use': True,
            'check_acronym_multiple_definition': True,
            'check_imperative_mood': True,
            'check_second_person': True,
            'check_link_text_quality': True,
            'check_numbered_list_sequence': True,
            'check_product_name_consistency': True,
            'check_cross_reference_targets': True,
            'check_code_formatting': True,
            'check_mil_std_40051': True,
            'check_s1000d': True,
            'check_as9100': True,
        }

        # Run benchmark
        start_time = time.perf_counter()

        result = checker.review_document(
            filepath=str(doc_path),
            options=options
        )

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000

        # Extract metrics
        word_count = result.get('statistics', {}).get('words', 0)
        issue_count = len(result.get('issues', []))
        checker_count = len(checker.checkers)

        avg_time = total_time_ms / max(checker_count, 1)
        issues_per_sec = issue_count / max(total_time_ms / 1000, 0.001)

        return PerformanceResult(
            document_name=doc_path.name,
            document_size_kb=doc_size_kb,
            word_count=word_count,
            total_time_ms=total_time_ms,
            checker_count=checker_count,
            issue_count=issue_count,
            avg_time_per_checker_ms=avg_time,
            issues_per_second=issues_per_sec
        )

    def test_checker_count(self, checker):
        """Verify we have approximately 84 checkers registered."""
        count = len(checker.checkers)
        print(f"\n[PERF] Registered checkers: {count}")

        # We expect around 84 checkers (may vary slightly)
        assert count >= 70, f"Expected at least 70 checkers, got {count}"
        assert count <= 100, f"Unexpectedly high checker count: {count}"

    def test_small_document_performance(self, checker):
        """Test performance on small documents (< 100KB)."""
        docs = [d for d in self.get_test_documents() if d.stat().st_size < 100 * 1024]

        if not docs:
            pytest.skip("No small test documents available")

        doc = docs[0]
        print(f"\n[PERF] Testing small document: {doc.name}")

        result = self.run_checker_benchmark(checker, doc)

        print(f"  Size: {result.document_size_kb:.1f} KB")
        print(f"  Words: {result.word_count:,}")
        print(f"  Time: {result.total_time_ms:.0f} ms")
        print(f"  Checkers: {result.checker_count}")
        print(f"  Issues: {result.issue_count}")
        print(f"  Avg per checker: {result.avg_time_per_checker_ms:.1f} ms")

        assert result.total_time_ms < self.MAX_TOTAL_TIME_SMALL_DOC_MS, \
            f"Small doc took {result.total_time_ms:.0f}ms, max is {self.MAX_TOTAL_TIME_SMALL_DOC_MS}ms"

    def test_medium_document_performance(self, checker):
        """Test performance on medium documents (100KB - 1MB)."""
        docs = [d for d in self.get_test_documents()
                if 100 * 1024 <= d.stat().st_size < 1024 * 1024]

        if not docs:
            pytest.skip("No medium test documents available")

        doc = docs[len(docs) // 2]  # Pick middle-sized doc
        print(f"\n[PERF] Testing medium document: {doc.name}")

        result = self.run_checker_benchmark(checker, doc)

        print(f"  Size: {result.document_size_kb:.1f} KB")
        print(f"  Words: {result.word_count:,}")
        print(f"  Time: {result.total_time_ms:.0f} ms")
        print(f"  Checkers: {result.checker_count}")
        print(f"  Issues: {result.issue_count}")
        print(f"  Avg per checker: {result.avg_time_per_checker_ms:.1f} ms")

        # Check time scales reasonably with document size
        if result.word_count > 0:
            time_per_1k = (result.total_time_ms / result.word_count) * 1000
            print(f"  Time per 1K words: {time_per_1k:.0f} ms")
            assert time_per_1k < self.MAX_TIME_PER_1K_WORDS_MS, \
                f"Too slow: {time_per_1k:.0f}ms per 1K words"

    def test_large_document_performance(self, checker):
        """Test performance on large documents (> 1MB)."""
        docs = [d for d in self.get_test_documents() if d.stat().st_size >= 1024 * 1024]

        if not docs:
            pytest.skip("No large test documents available")

        doc = docs[0]
        print(f"\n[PERF] Testing large document: {doc.name}")

        result = self.run_checker_benchmark(checker, doc)

        print(f"  Size: {result.document_size_kb:.1f} KB ({result.document_size_kb/1024:.1f} MB)")
        print(f"  Words: {result.word_count:,}")
        print(f"  Time: {result.total_time_ms:.0f} ms ({result.total_time_ms/1000:.1f} s)")
        print(f"  Checkers: {result.checker_count}")
        print(f"  Issues: {result.issue_count}")
        print(f"  Avg per checker: {result.avg_time_per_checker_ms:.1f} ms")
        print(f"  Issues per second: {result.issues_per_second:.0f}")

        assert result.total_time_ms < self.MAX_TOTAL_TIME_LARGE_DOC_MS, \
            f"Large doc took {result.total_time_ms:.0f}ms, max is {self.MAX_TOTAL_TIME_LARGE_DOC_MS}ms"

    def test_all_documents_benchmark(self, checker):
        """Run benchmark on all available test documents."""
        docs = self.get_test_documents()

        if not docs:
            pytest.skip("No test documents available")

        print("\n" + "=" * 80)
        print("FULL PERFORMANCE BENCHMARK")
        print("=" * 80)

        results = []
        for doc in docs[:5]:  # Limit to first 5 for speed
            try:
                result = self.run_checker_benchmark(checker, doc)
                results.append(result)
            except Exception as e:
                print(f"  [SKIP] {doc.name}: {e}")

        if results:
            print("\n" + "-" * 80)
            print(f"{'Document':<40} {'Size':>10} {'Words':>10} {'Time':>10} {'Issues':>8}")
            print("-" * 80)

            for r in results:
                print(f"{r.document_name[:39]:<40} {r.document_size_kb:>8.0f}KB {r.word_count:>10,} {r.total_time_ms:>8.0f}ms {r.issue_count:>8}")

            print("-" * 80)

            # Summary statistics
            total_words = sum(r.word_count for r in results)
            total_time = sum(r.total_time_ms for r in results)
            total_issues = sum(r.issue_count for r in results)

            print(f"{'TOTAL':<40} {'':<10} {total_words:>10,} {total_time:>8.0f}ms {total_issues:>8}")

            if total_words > 0:
                print(f"\nOverall performance: {(total_time / total_words) * 1000:.1f} ms per 1000 words")

            print("=" * 80)


class TestIndividualCheckerPerformance:
    """Test performance of individual checker categories."""

    @pytest.fixture
    def checker(self):
        """Create a AEGISEngine instance."""
        return AEGISEngine()

    @pytest.fixture
    def sample_text(self):
        """Generate sample text for testing."""
        # Create a moderate-sized sample (about 5000 words)
        paragraphs = []
        for i in range(50):
            paragraphs.append(
                f"The system shall provide functionality for requirement {i+1}. "
                f"This requirement is essential for the operation of the NASA spacecraft. "
                f"The engineer must ensure that the specification is met. "
                f"All documents (e.g., SOPs, TBDs) should be reviewed. "
                f"The contractor will deliver the deliverable per MIL-STD-498. "
                f"Testing shall verify that the requirement is satisfied. "
                f"NOTE: This section describes the basic implementation approach. "
                f"The PM and SE are responsible for oversight. "
                f"See Section 3.{i+1} for additional details."
            )
        return "\n\n".join(paragraphs)

    def test_acronym_checkers_performance(self, checker, sample_text):
        """Test acronym checker performance."""
        print("\n[PERF] Acronym Checkers")

        # Time the acronym-related checkers
        acronym_checkers = ['acronyms', 'enhanced_acronyms', 'acronym_first_use', 'acronym_multiple_definition']

        for name in acronym_checkers:
            if name in checker.checkers:
                start = time.perf_counter()
                issues = checker.checkers[name].safe_check(
                    text=sample_text,
                    paragraphs=sample_text.split('\n\n'),
                    sentences=[s.strip() for p in sample_text.split('\n\n') for s in p.split('. ') if s.strip()],
                    filename='test.docx'
                )
                elapsed = (time.perf_counter() - start) * 1000
                print(f"  {name}: {elapsed:.1f}ms ({len(issues)} issues)")

    def test_style_checkers_performance(self, checker, sample_text):
        """Test style checker performance."""
        print("\n[PERF] Style Checkers")

        style_checkers = ['passive_voice', 'weak_language', 'wordy_phrases', 'nominalization']

        for name in style_checkers:
            if name in checker.checkers:
                start = time.perf_counter()
                issues = checker.checkers[name].safe_check(
                    text=sample_text,
                    paragraphs=sample_text.split('\n\n'),
                    sentences=[s.strip() for p in sample_text.split('\n\n') for s in p.split('. ') if s.strip()],
                    filename='test.docx'
                )
                elapsed = (time.perf_counter() - start) * 1000
                print(f"  {name}: {elapsed:.1f}ms ({len(issues)} issues)")

    def test_compliance_checkers_performance(self, checker, sample_text):
        """Test compliance checker performance."""
        print("\n[PERF] Compliance Checkers")

        compliance_checkers = ['mil_std', 'mil_std_40051', 'do178', 's1000d', 'as9100']

        for name in compliance_checkers:
            if name in checker.checkers:
                start = time.perf_counter()
                issues = checker.checkers[name].safe_check(
                    text=sample_text,
                    paragraphs=sample_text.split('\n\n'),
                    sentences=[s.strip() for p in sample_text.split('\n\n') for s in p.split('. ') if s.strip()],
                    filename='test.docx'
                )
                elapsed = (time.perf_counter() - start) * 1000
                print(f"  {name}: {elapsed:.1f}ms ({len(issues)} issues)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
