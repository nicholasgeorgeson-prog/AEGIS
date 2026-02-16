#!/usr/bin/env python3
"""
Enhancement Integration Tests v1.0.0
====================================
Date: 2026-02-04

Tests all newly integrated enhancements:
- PassivePy passive voice detection
- pymupdf4llm PDF extraction
- py-readability-metrics readability analysis
- STE-100 vocabulary checker
- Expanded acronym database

Author: AEGIS NLP Enhancement Project
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_passivepy():
    """Test PassivePy integration."""
    print("\n" + "=" * 60)
    print("Testing PassivePy Integration")
    print("=" * 60)

    try:
        from passivepy_checker import (
            PassivePyChecker,
            CombinedPassiveChecker,
            check_passive_voice,
            is_passivepy_available
        )

        print(f"  PassivePy available: {is_passivepy_available()}")

        # Test text with passive voice
        test_text = """
        The system was tested by the engineering team.
        The software is being developed for military applications.
        The report was completed on time.
        The engineer completed the analysis quickly.
        """

        detections = check_passive_voice(test_text)
        print(f"  Passive sentences detected: {len(detections)}")

        for d in detections[:3]:
            print(f"    - {d.get('sentence', '')[:50]}...")
            print(f"      Confidence: {d.get('confidence', 0):.2f}")

        print("  [PASS] PassivePy integration working")
        return True

    except Exception as e:
        print(f"  [FAIL] PassivePy test failed: {e}")
        return False


def test_pdf_extractor():
    """Test enhanced PDF extractor."""
    print("\n" + "=" * 60)
    print("Testing Enhanced PDF Extractor")
    print("=" * 60)

    try:
        from pdf_extractor_enhanced import (
            EnhancedPDFExtractor,
            get_available_backends,
            PYMUPDF4LLM_AVAILABLE,
            PDFPLUMBER_AVAILABLE,
            PYMUPDF_AVAILABLE
        )

        print(f"  pymupdf4llm available: {PYMUPDF4LLM_AVAILABLE}")
        print(f"  pdfplumber available: {PDFPLUMBER_AVAILABLE}")
        print(f"  PyMuPDF available: {PYMUPDF_AVAILABLE}")

        backends = get_available_backends()
        print(f"  Available backends: {', '.join(backends)}")

        extractor = EnhancedPDFExtractor()
        print(f"  Extractor initialized: {extractor.VERSION}")

        print("  [PASS] PDF extractor integration working")
        return True

    except Exception as e:
        print(f"  [FAIL] PDF extractor test failed: {e}")
        return False


def test_readability():
    """Test enhanced readability metrics."""
    print("\n" + "=" * 60)
    print("Testing Enhanced Readability Metrics")
    print("=" * 60)

    try:
        from readability_enhanced import (
            EnhancedReadabilityChecker,
            analyze_readability,
            get_readability_recommendations,
            is_py_readability_available
        )

        print(f"  py-readability-metrics available: {is_py_readability_available()}")

        test_text = """
        The software requirements specification document defines the functional
        and non-functional requirements for the flight management system.
        This system shall provide navigation, guidance, and flight planning
        capabilities for commercial aircraft operations. The system interfaces
        with multiple avionics subsystems including the air data computer,
        inertial reference system, and flight control computer.
        """

        results = analyze_readability(test_text)

        print(f"  Analysis source: {results.get('source', 'unknown')}")
        print(f"  Flesch-Kincaid Grade: {results.get('flesch_kincaid_grade', 0):.1f}")
        print(f"  Flesch Reading Ease: {results.get('flesch_reading_ease', 0):.1f}")
        print(f"  Gunning Fog Index: {results.get('gunning_fog', 0):.1f}")
        print(f"  SMOG Index: {results.get('smog_index', 0):.1f}")
        print(f"  Average Grade Level: {results.get('average_grade_level', 0):.1f}")
        print(f"  Recommended Audience: {results.get('recommended_audience', 'unknown')}")
        print(f"  Technical Complexity: {results.get('technical_complexity', 0):.1f}")

        recommendations = get_readability_recommendations(test_text)
        print(f"  Recommendations: {len(recommendations)}")
        for rec in recommendations[:2]:
            print(f"    - {rec[:60]}...")

        print("  [PASS] Readability metrics integration working")
        return True

    except Exception as e:
        print(f"  [FAIL] Readability test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ste100():
    """Test STE-100 vocabulary checker."""
    print("\n" + "=" * 60)
    print("Testing STE-100 Vocabulary Checker")
    print("=" * 60)

    try:
        from ste100_checker import (
            STE100Checker,
            check_ste100_compliance,
            get_ste100_alternatives,
            is_ste100_approved
        )

        checker = STE100Checker()
        print(f"  STE-100 checker version: {checker.VERSION}")
        print(f"  Approved verbs loaded: {len(checker.approved_verbs)}")
        print(f"  Approved nouns loaded: {len(checker.approved_nouns)}")
        print(f"  Unapproved words loaded: {len(checker.unapproved_words)}")

        # Test text with STE-100 violations
        test_text = """
        The technician shall accomplish the verification procedure to ensure
        that the system achieves the specified performance parameters.
        The software modification was implemented to facilitate improved
        data processing capabilities. Proceed to terminate the test sequence
        upon completion of all verification activities.
        """

        results = check_ste100_compliance(test_text)

        print(f"  Compliance Score: {results.get('compliance_score', 0):.1f}%")
        print(f"  Total Violations: {results.get('total_violations', 0)}")
        print(f"  Approved Words: {results.get('approved_words', 0)}")
        print(f"  Unapproved Words: {results.get('unapproved_words', 0)}")

        # Show some violations
        violations = results.get('violations', [])[:3]
        for v in violations:
            print(f"    - {v.get('word', '')}: {v.get('suggestion', '')}")

        # Test word lookup
        alt = get_ste100_alternatives('accomplish')
        print(f"  Alternative for 'accomplish': {alt}")

        print("  [PASS] STE-100 checker integration working")
        return True

    except Exception as e:
        print(f"  [FAIL] STE-100 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_acronym_database():
    """Test expanded acronym database."""
    print("\n" + "=" * 60)
    print("Testing Expanded Acronym Database")
    print("=" * 60)

    try:
        from acronym_database import (
            AerospaceAcronymDatabase,
            get_acronym_database,
            lookup_acronym,
            check_document_acronyms,
            extract_acronyms,
            get_acronym_count
        )

        db = get_acronym_database()
        count = get_acronym_count()
        print(f"  Acronyms loaded: {count}")

        # Test lookups
        test_acronyms = ['GPS', 'FAA', 'NASA', 'ARINC', 'FADEC', 'AHRS']
        print("  Sample lookups:")
        for acr in test_acronyms:
            defn = lookup_acronym(acr)
            if defn:
                print(f"    {acr}: {defn[:50]}...")

        # Test document checking
        test_text = """
        The FMS (Flight Management System) interfaces with the AHRS and GPS.
        The FADEC system controls engine parameters. The API provides data to
        the CDU. The XYZ system is not defined anywhere.
        """

        extracted = extract_acronyms(test_text)
        print(f"  Acronyms extracted from text: {len(extracted)}")
        print(f"    Found: {', '.join(extracted[:10])}")

        issues = check_document_acronyms(test_text)
        print(f"  Document issues found: {len(issues)}")
        for issue in issues[:2]:
            print(f"    - {issue.get('acronym')}: {issue.get('message')}")

        stats = db.get_statistics()
        print(f"  Database categories: {stats.get('categories', {})}")

        print("  [PASS] Acronym database integration working")
        return True

    except Exception as e:
        print(f"  [FAIL] Acronym database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_files():
    """Test that all data files are present."""
    print("\n" + "=" * 60)
    print("Testing Data Files")
    print("=" * 60)

    from pathlib import Path
    script_dir = Path(__file__).parent

    files_to_check = [
        'data/dictionaries/ste100_dictionary.json',
        'data/dictionaries/aerospace_acronyms.json',
    ]

    all_present = True
    for file_path in files_to_check:
        full_path = script_dir / file_path
        exists = full_path.exists()
        size = full_path.stat().st_size if exists else 0
        status = "OK" if exists else "MISSING"
        print(f"  [{status}] {file_path} ({size:,} bytes)")
        if not exists:
            all_present = False

    if all_present:
        print("  [PASS] All data files present")
    else:
        print("  [WARN] Some data files missing")

    return all_present


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("AEGIS Enhancement Integration Tests")
    print("=" * 60)

    results = {
        'Data Files': test_data_files(),
        'PassivePy': test_passivepy(),
        'PDF Extractor': test_pdf_extractor(),
        'Readability': test_readability(),
        'STE-100': test_ste100(),
        'Acronym Database': test_acronym_database(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n  Total: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n  All enhancement integrations working correctly!")
        return 0
    else:
        print(f"\n  {failed} integration(s) need attention.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
