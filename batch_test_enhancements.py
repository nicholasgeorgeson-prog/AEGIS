#!/usr/bin/env python3
"""
Batch Enhancement Testing
=========================
Run enhancement analysis on multiple documents to validate accuracy.
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import enhancement modules
from passivepy_checker import check_passive_voice, is_passivepy_available
from ste100_checker import check_ste100_compliance
from readability_enhanced import analyze_readability
from acronym_database import check_document_acronyms, extract_acronyms
from pdf_extractor_enhanced import EnhancedPDFExtractor

# Document paths
TEST_DOCS_DIR = Path(__file__).parent / 'test_documents'

# Documents to test
DOCUMENTS = [
    'NASA_Systems_Engineering_Handbook.pdf',
    'FAA_AC_120_92B.pdf',
    'NIST_Cybersecurity_Framework.pdf',
    'OSHA_Process_Safety_Management.pdf',
    'EPA_SOP_Guidance.pdf',
    'KSC_Specs_Standards.pdf',
    'PMBOK_Guide_Summary.pdf',
    'Stanford_Engineering_Robotics_SOP.docx',
    'Rowan_SOP_Guideline.docx',
]


def extract_text(filepath: Path, max_chars: int = 50000) -> str:
    """Extract text from document."""
    if filepath.suffix.lower() == '.pdf':
        extractor = EnhancedPDFExtractor()
        result = extractor.extract(str(filepath))
        text = result.text if hasattr(result, 'text') else str(result)
    elif filepath.suffix.lower() in ['.docx', '.doc']:
        try:
            from docx import Document
            doc = Document(str(filepath))
            text = '\n'.join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"    Error reading DOCX: {e}")
            return ""
    else:
        return ""

    # Limit text size
    if len(text) > max_chars:
        text = text[:max_chars]

    return text


def analyze_document(filepath: Path) -> dict:
    """Analyze a single document with all enhancement modules."""
    results = {
        'filename': filepath.name,
        'status': 'success',
        'errors': [],
        'metrics': {}
    }

    # Extract text
    text = extract_text(filepath)
    if not text:
        results['status'] = 'error'
        results['errors'].append('Failed to extract text')
        return results

    word_count = len(text.split())
    results['metrics']['word_count'] = word_count

    # Passive voice analysis
    try:
        passive_results = check_passive_voice(text)
        results['metrics']['passive_sentences'] = len(passive_results)
        results['metrics']['passive_source'] = passive_results[0]['source'] if passive_results else 'none'
    except Exception as e:
        results['errors'].append(f'Passive: {e}')
        results['metrics']['passive_sentences'] = -1

    # STE-100 analysis
    try:
        ste_results = check_ste100_compliance(text)
        unapproved = [v for v in ste_results['violations'] if v['type'] == 'unapproved_word']
        long_sent = [v for v in ste_results['violations'] if v['type'] == 'sentence_length']
        results['metrics']['ste100_unapproved'] = len(unapproved)
        results['metrics']['ste100_long_sentences'] = len(long_sent)
        results['metrics']['ste100_compliance'] = ste_results['compliance_score']
    except Exception as e:
        results['errors'].append(f'STE-100: {e}')
        results['metrics']['ste100_unapproved'] = -1

    # Readability analysis
    try:
        read_results = analyze_readability(text)
        results['metrics']['flesch_kincaid_grade'] = read_results.get('flesch_kincaid_grade', 0)
        results['metrics']['flesch_reading_ease'] = read_results.get('flesch_reading_ease', 0)
        results['metrics']['gunning_fog'] = read_results.get('gunning_fog', 0)
    except Exception as e:
        results['errors'].append(f'Readability: {e}')
        results['metrics']['flesch_kincaid_grade'] = -1

    # Acronym analysis
    try:
        acronyms = extract_acronyms(text)
        issues = check_document_acronyms(text)
        results['metrics']['acronyms_found'] = len(acronyms)
        results['metrics']['acronym_issues'] = len(issues)
    except Exception as e:
        results['errors'].append(f'Acronyms: {e}')
        results['metrics']['acronyms_found'] = -1

    return results


def main():
    print("\n" + "=" * 80)
    print("BATCH ENHANCEMENT TESTING")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    print(f"\nPassivePy available: {is_passivepy_available()}")
    print(f"Documents to test: {len(DOCUMENTS)}")
    print("-" * 80)

    all_results = []

    for doc_name in DOCUMENTS:
        filepath = TEST_DOCS_DIR / doc_name

        if not filepath.exists():
            print(f"\n[SKIP] {doc_name} - File not found")
            continue

        print(f"\n[TEST] {doc_name}")
        print(f"       Size: {filepath.stat().st_size / 1024:.1f} KB")

        results = analyze_document(filepath)
        all_results.append(results)

        if results['status'] == 'success':
            m = results['metrics']
            print(f"       Words: {m.get('word_count', 0):,}")
            print(f"       Passive sentences: {m.get('passive_sentences', 0)}")
            print(f"       STE-100 unapproved: {m.get('ste100_unapproved', 0)}")
            print(f"       STE-100 long sentences: {m.get('ste100_long_sentences', 0)}")
            print(f"       Flesch-Kincaid Grade: {m.get('flesch_kincaid_grade', 0):.1f}")
            print(f"       Acronyms found: {m.get('acronyms_found', 0)}")
            print(f"       [OK] All analyses completed")
        else:
            print(f"       [ERROR] {results['errors']}")

    # Summary table
    print("\n" + "=" * 80)
    print("BATCH TEST SUMMARY")
    print("=" * 80)

    print(f"\n{'Document':<40} {'Words':>8} {'Passive':>8} {'STE-100':>8} {'F-K':>6} {'Acro':>6}")
    print("-" * 80)

    successful = 0
    failed = 0

    for r in all_results:
        if r['status'] == 'success':
            successful += 1
            m = r['metrics']
            print(f"{r['filename'][:39]:<40} {m.get('word_count', 0):>8,} "
                  f"{m.get('passive_sentences', 0):>8} {m.get('ste100_unapproved', 0):>8} "
                  f"{m.get('flesch_kincaid_grade', 0):>6.1f} {m.get('acronyms_found', 0):>6}")
        else:
            failed += 1
            print(f"{r['filename'][:39]:<40} {'ERROR':>8} {'-':>8} {'-':>8} {'-':>6} {'-':>6}")

    print("-" * 80)
    print(f"\nTotal: {successful} successful, {failed} failed out of {len(all_results)} documents")

    # Validation checks
    print("\n" + "=" * 80)
    print("VALIDATION CHECKS")
    print("=" * 80)

    checks_passed = 0
    checks_failed = 0

    for r in all_results:
        if r['status'] != 'success':
            continue

        m = r['metrics']
        doc = r['filename']

        # Check 1: Passive detection should find some passives in technical docs
        if m.get('word_count', 0) > 1000 and m.get('passive_sentences', 0) == 0:
            print(f"  [WARN] {doc}: No passive sentences detected (suspicious)")
            checks_failed += 1
        else:
            checks_passed += 1

        # Check 2: STE-100 should find some violations in technical docs
        if m.get('word_count', 0) > 1000 and m.get('ste100_unapproved', 0) == 0:
            print(f"  [WARN] {doc}: No STE-100 violations (suspicious)")
            checks_failed += 1
        else:
            checks_passed += 1

        # Check 3: Readability should be reasonable (grade 8-20 for technical docs)
        fkg = m.get('flesch_kincaid_grade', 0)
        if fkg < 8 or fkg > 25:
            print(f"  [WARN] {doc}: Unusual readability grade ({fkg:.1f})")
            checks_failed += 1
        else:
            checks_passed += 1

        # Check 4: Should find acronyms in technical docs
        if m.get('word_count', 0) > 1000 and m.get('acronyms_found', 0) == 0:
            print(f"  [WARN] {doc}: No acronyms found (suspicious)")
            checks_failed += 1
        else:
            checks_passed += 1

    print(f"\n  Validation: {checks_passed} passed, {checks_failed} warnings")

    # Final status
    print("\n" + "=" * 80)
    if failed == 0 and checks_failed == 0:
        print("BATCH TEST RESULT: ALL PASSED ✓")
    elif failed == 0:
        print(f"BATCH TEST RESULT: PASSED with {checks_failed} warnings")
    else:
        print(f"BATCH TEST RESULT: {failed} FAILURES")
    print("=" * 80)


if __name__ == '__main__':
    main()
