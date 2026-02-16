#!/usr/bin/env python3
"""
Enhancement Analysis Runner v1.0.0
==================================
Date: 2026-02-04

Runs all enhanced checkers on a document and produces detailed analysis
for comparison and validation.

Author: AEGIS NLP Enhancement Project
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Ensure Path is available for relative path resolution
PROJECT_ROOT = Path(__file__).parent

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def extract_text_from_pdf(pdf_path: str, max_pages: int = 5) -> str:
    """Extract text from PDF using enhanced extractor."""
    try:
        from pdf_extractor_enhanced import extract_pdf
        result = extract_pdf(pdf_path)
        return result.text[:50000]  # Limit for analysis
    except Exception as e:
        print(f"Enhanced extractor failed: {e}")
        # Fallback to PyMuPDF
        try:
            import fitz
            doc = fitz.open(pdf_path)
            text_parts = []
            for i, page in enumerate(doc):
                if i >= max_pages:
                    break
                text_parts.append(page.get_text())
            doc.close()
            return '\n'.join(text_parts)
        except Exception as e2:
            print(f"PyMuPDF fallback failed: {e2}")
            return ""


def extract_text_from_docx(docx_path: str) -> str:
    """Extract text from DOCX."""
    try:
        from docx import Document
        doc = Document(docx_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
    except Exception as e:
        print(f"DOCX extraction failed: {e}")
        return ""


def run_passive_voice_analysis(text: str) -> dict:
    """Run passive voice analysis."""
    print("\n" + "=" * 70)
    print("PASSIVE VOICE ANALYSIS")
    print("=" * 70)

    results = {
        'passivepy': [],
        'combined': [],
        'statistics': {}
    }

    try:
        from passivepy_checker import (
            check_passive_voice,
            get_combined_checker,
            is_passivepy_available
        )

        print(f"PassivePy available: {is_passivepy_available()}")

        # Run combined analysis
        detections = check_passive_voice(text, use_combined=True)
        results['combined'] = detections

        print(f"\nPassive sentences detected: {len(detections)}")
        print("-" * 70)

        # Show top examples
        for i, d in enumerate(detections[:10]):
            sentence = d.get('sentence', '')[:80]
            confidence = d.get('confidence', 0)
            source = d.get('source', 'unknown')
            print(f"\n{i+1}. [{confidence:.0%}] ({source})")
            print(f"   \"{sentence}...\"")

        # Statistics
        if detections:
            avg_conf = sum(d.get('confidence', 0) for d in detections) / len(detections)
            agreed = len([d for d in detections if d.get('both_checkers_agree')])
            results['statistics'] = {
                'total_detected': len(detections),
                'average_confidence': avg_conf,
                'both_agreed': agreed
            }
            print(f"\n\nStatistics:")
            print(f"  Average confidence: {avg_conf:.1%}")
            print(f"  Both checkers agreed: {agreed}")

    except Exception as e:
        print(f"Passive voice analysis error: {e}")
        import traceback
        traceback.print_exc()

    return results


def run_readability_analysis(text: str) -> dict:
    """Run readability analysis."""
    print("\n" + "=" * 70)
    print("READABILITY ANALYSIS")
    print("=" * 70)

    results = {}

    try:
        from readability_enhanced import (
            analyze_readability,
            get_readability_recommendations,
            EnhancedReadabilityChecker
        )

        scores = analyze_readability(text)
        results['scores'] = scores

        print(f"\nSource: {scores.get('source', 'unknown')}")
        print("-" * 70)

        print(f"\n{'Metric':<35} {'Value':>10}")
        print("-" * 45)
        print(f"{'Flesch Reading Ease':<35} {scores.get('flesch_reading_ease', 0):>10.1f}")
        print(f"{'Flesch-Kincaid Grade':<35} {scores.get('flesch_kincaid_grade', 0):>10.1f}")
        print(f"{'Gunning Fog Index':<35} {scores.get('gunning_fog', 0):>10.1f}")
        print(f"{'SMOG Index':<35} {scores.get('smog_index', 0):>10.1f}")
        print(f"{'Coleman-Liau Index':<35} {scores.get('coleman_liau', 0):>10.1f}")
        print(f"{'Automated Readability Index':<35} {scores.get('automated_readability_index', 0):>10.1f}")
        print(f"{'Linsear Write':<35} {scores.get('linsear_write', 0):>10.1f}")
        print(f"{'Dale-Chall':<35} {scores.get('dale_chall', 0):>10.1f}")

        print(f"\n{'AVERAGE GRADE LEVEL':<35} {scores.get('average_grade_level', 0):>10.1f}")
        print(f"{'Recommended Audience':<35} {scores.get('recommended_audience', 'N/A'):>10}")

        print(f"\n{'Word Count':<35} {scores.get('word_count', 0):>10}")
        print(f"{'Sentence Count':<35} {scores.get('sentence_count', 0):>10}")
        print(f"{'Avg Words/Sentence':<35} {scores.get('avg_words_per_sentence', 0):>10.1f}")
        print(f"{'Avg Syllables/Word':<35} {scores.get('avg_syllables_per_word', 0):>10.2f}")
        print(f"{'Technical Complexity':<35} {scores.get('technical_complexity', 0):>10.1f}")
        print(f"{'Sentence Variety':<35} {scores.get('sentence_variety', 0):>10.1f}")

        recommendations = get_readability_recommendations(text)
        results['recommendations'] = recommendations

        print("\nRecommendations:")
        for rec in recommendations:
            print(f"  - {rec}")

    except Exception as e:
        print(f"Readability analysis error: {e}")
        import traceback
        traceback.print_exc()

    return results


def run_ste100_analysis(text: str) -> dict:
    """Run STE-100 compliance analysis."""
    print("\n" + "=" * 70)
    print("STE-100 COMPLIANCE ANALYSIS")
    print("=" * 70)

    results = {}

    try:
        from ste100_checker import check_ste100_compliance, STE100Checker

        compliance = check_ste100_compliance(text)
        results = compliance

        print(f"\nCompliance Score: {compliance.get('compliance_score', 0):.1f}%")
        print("-" * 70)

        print(f"\n{'Metric':<35} {'Value':>10}")
        print("-" * 45)
        print(f"{'Total Violations':<35} {compliance.get('total_violations', 0):>10}")
        print(f"{'Approved Words Used':<35} {compliance.get('approved_words', 0):>10}")
        print(f"{'Unapproved Words Used':<35} {compliance.get('unapproved_words', 0):>10}")

        summary = compliance.get('summary', {})
        print(f"\n{'Errors':<35} {summary.get('errors', 0):>10}")
        print(f"{'Warnings':<35} {summary.get('warnings', 0):>10}")
        print(f"{'Info':<35} {summary.get('info', 0):>10}")

        # Sentence stats
        sent_stats = compliance.get('sentence_stats', {})
        print(f"\n{'Sentence Count':<35} {sent_stats.get('count', 0):>10}")
        print(f"{'Avg Sentence Length':<35} {sent_stats.get('avg_length', 0):>10.1f}")
        print(f"{'Max Sentence Length':<35} {sent_stats.get('max_length', 0):>10}")
        print(f"{'Sentences Over Limit':<35} {sent_stats.get('over_limit', 0):>10}")

        # Top violations
        violations = compliance.get('violations', [])
        unapproved = [v for v in violations if v.get('type') == 'unapproved_word']

        if unapproved:
            print("\nTop Unapproved Words:")
            seen = set()
            count = 0
            for v in unapproved:
                word = v.get('word', '')
                if word not in seen:
                    seen.add(word)
                    suggestion = v.get('suggestion', '')
                    print(f"  - '{word}' -> {suggestion}")
                    count += 1
                    if count >= 15:
                        break

        # Other violation types
        by_type = summary.get('by_type', {})
        if by_type:
            print("\nViolations by Type:")
            for vtype, vcount in by_type.items():
                print(f"  - {vtype}: {vcount}")

    except Exception as e:
        print(f"STE-100 analysis error: {e}")
        import traceback
        traceback.print_exc()

    return results


def run_acronym_analysis(text: str) -> dict:
    """Run acronym analysis."""
    print("\n" + "=" * 70)
    print("ACRONYM ANALYSIS")
    print("=" * 70)

    results = {}

    try:
        from acronym_database import (
            get_acronym_database,
            extract_acronyms,
            check_document_acronyms,
            lookup_acronym
        )

        db = get_acronym_database()

        # Extract acronyms
        acronyms = extract_acronyms(text)
        unique_acronyms = list(set(acronyms))
        results['extracted'] = unique_acronyms

        print(f"\nAcronyms Found: {len(unique_acronyms)}")
        print("-" * 70)

        # Categorize
        known = []
        unknown = []

        for acr in unique_acronyms:
            defn = lookup_acronym(acr)
            if defn:
                known.append((acr, defn))
            else:
                unknown.append(acr)

        results['known'] = known
        results['unknown'] = unknown

        print(f"\nKnown acronyms: {len(known)}")
        print(f"Unknown acronyms: {len(unknown)}")

        if known:
            print("\nKnown Acronyms (sample):")
            for acr, defn in known[:15]:
                print(f"  {acr}: {defn[:50]}...")

        if unknown:
            print("\nUnknown Acronyms (need definition):")
            for acr in unknown[:15]:
                print(f"  {acr}")

        # Document issues
        issues = check_document_acronyms(text)
        results['issues'] = issues

        if issues:
            print(f"\nDocument Issues: {len(issues)}")
            for issue in issues[:10]:
                print(f"  - {issue.get('acronym')}: {issue.get('message')}")

    except Exception as e:
        print(f"Acronym analysis error: {e}")
        import traceback
        traceback.print_exc()

    return results


def run_full_analysis(file_path: str) -> dict:
    """Run full analysis on a document."""
    print("\n" + "=" * 70)
    print(f"FULL ENHANCEMENT ANALYSIS")
    print(f"Document: {os.path.basename(file_path)}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Extract text
    print("\nExtracting text...")
    if file_path.lower().endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path.lower().endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        print(f"Unsupported file type: {file_path}")
        return {}

    if not text:
        print("Failed to extract text!")
        return {}

    word_count = len(text.split())
    print(f"Extracted {word_count} words ({len(text)} characters)")

    # Preview
    print("\n--- Text Preview (first 500 chars) ---")
    print(text[:500])
    print("...")

    # Run all analyses
    results = {
        'file': file_path,
        'word_count': word_count,
        'char_count': len(text),
        'timestamp': datetime.now().isoformat()
    }

    results['passive_voice'] = run_passive_voice_analysis(text)
    results['readability'] = run_readability_analysis(text)
    results['ste100'] = run_ste100_analysis(text)
    results['acronyms'] = run_acronym_analysis(text)

    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)

    passive_count = len(results['passive_voice'].get('combined', []))
    readability = results['readability'].get('scores', {})
    ste100 = results['ste100']
    acronyms = results['acronyms']

    print(f"\n{'Metric':<40} {'Value':>15}")
    print("-" * 55)
    print(f"{'Word Count':<40} {word_count:>15,}")
    print(f"{'Passive Voice Sentences':<40} {passive_count:>15}")
    print(f"{'Flesch-Kincaid Grade':<40} {readability.get('flesch_kincaid_grade', 0):>15.1f}")
    print(f"{'Average Grade Level':<40} {readability.get('average_grade_level', 0):>15.1f}")
    print(f"{'STE-100 Compliance Score':<40} {ste100.get('compliance_score', 0):>14.1f}%")
    print(f"{'STE-100 Violations':<40} {ste100.get('total_violations', 0):>15}")
    print(f"{'Acronyms Found':<40} {len(acronyms.get('extracted', [])):>15}")
    print(f"{'Unknown Acronyms':<40} {len(acronyms.get('unknown', [])):>15}")

    return results


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        # Default to a test document
        test_docs = [
            str(PROJECT_ROOT / 'test_documents' / 'NASA_Systems_Engineering_Handbook.pdf'),
            str(PROJECT_ROOT / 'test_documents' / 'FAA_AC_120_92B.pdf'),
        ]

        for doc in test_docs:
            if os.path.exists(doc):
                results = run_full_analysis(doc)
                break
        else:
            print("Usage: python run_enhancement_analysis.py <document_path>")
            print("\nNo test document found. Please provide a document path.")
            return 1
    else:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return 1
        results = run_full_analysis(file_path)

    return 0


if __name__ == '__main__':
    sys.exit(main())
