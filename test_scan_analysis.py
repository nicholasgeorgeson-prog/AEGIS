#!/usr/bin/env python3
"""
Test Scan Analysis Script
Runs scans on test documents and analyzes results for improvement opportunities.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from collections import defaultdict

# Configuration
BASE_URL = "http://localhost:5050"
TEST_DOCS_DIR = Path("/Users/nick/Desktop/Work_Tools/AEGIS/test_documents")
OUTPUT_DIR = Path("/Users/nick/Desktop/Work_Tools/AEGIS/test_results")

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)

def scan_document(filepath: str) -> dict:
    """Submit a document for review and return results."""
    filename = os.path.basename(filepath)
    print(f"\n{'='*60}")
    print(f"Scanning: {filename}")
    print(f"{'='*60}")

    try:
        with open(filepath, 'rb') as f:
            files = {'document': (filename, f)}
            data = {
                'check_spelling': 'false',  # Skip spelling for speed
                'check_grammar': 'true',
                'check_acronyms': 'true',
                'check_passive_voice': 'true',
                'check_weak_language': 'true',
                'check_wordy_phrases': 'true',
                'check_nominalization': 'true',
                'check_requirements_language': 'true',
                'check_sentence_length': 'true',
                'check_hyperlinks': 'false',  # Skip for offline docs
                # Enhanced analyzers
                'check_semantic_analysis': 'true',
                'check_enhanced_acronyms': 'true',
                'check_prose_linting': 'true',
                'check_structure_analysis': 'true',
                'check_text_statistics': 'true',
            }

            response = requests.post(
                f"{BASE_URL}/api/review",
                files=files,
                data=data,
                timeout=300
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result
                else:
                    print(f"  Error: {result.get('error', 'Unknown error')}")
                    return None
            else:
                print(f"  HTTP Error: {response.status_code}")
                return None

    except Exception as e:
        print(f"  Exception: {e}")
        return None

def extract_roles(filepath: str, full_text: str) -> dict:
    """Extract roles from document using the roles API."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/roles/extract",
            json={
                'filepath': filepath,
                'full_text': full_text[:50000],  # Limit text size
                'store_in_database': False
            },
            timeout=120
        )

        if response.status_code == 200:
            return response.json().get('data', {})
        return {}
    except Exception as e:
        print(f"  Role extraction error: {e}")
        return {}

def analyze_results(results: dict, filename: str) -> dict:
    """Analyze scan results and identify patterns."""
    analysis = {
        'filename': filename,
        'success': results.get('success', False),
        'word_count': results.get('word_count', 0),
        'paragraph_count': results.get('paragraph_count', 0),
        'issue_count': results.get('issue_count', 0),
        'score': results.get('score', 0),
        'grade': results.get('grade', 'N/A'),
    }

    # Readability
    readability = results.get('readability', {})
    analysis['readability'] = {
        'flesch_reading_ease': readability.get('flesch_reading_ease', 0),
        'flesch_kincaid_grade': readability.get('flesch_kincaid_grade', 0),
        'gunning_fog_index': readability.get('gunning_fog_index', 0),
    }

    # Issues by severity
    by_severity = results.get('by_severity', {})
    analysis['issues_by_severity'] = by_severity

    # Issues by category
    by_category = results.get('by_category', {})
    analysis['issues_by_category'] = by_category

    # Enhanced analyzer metrics
    enhanced_metrics = results.get('enhanced_analyzer_metrics', {})
    analysis['enhanced_analyzer_metrics'] = enhanced_metrics

    # Roles data
    roles = results.get('roles', {})
    if roles and roles.get('success'):
        role_list = roles.get('roles', [])
        analysis['roles'] = {
            'count': len(role_list),
            'top_roles': [r.get('name', '') for r in role_list[:10]],
            'avg_confidence': sum(r.get('confidence', 0) for r in role_list) / max(len(role_list), 1)
        }
    else:
        analysis['roles'] = {'count': 0, 'top_roles': [], 'avg_confidence': 0}

    # Acronym metrics
    acronym_metrics = results.get('acronym_metrics', {})
    analysis['acronyms'] = acronym_metrics

    return analysis

def print_analysis(analysis: dict):
    """Print analysis results in a readable format."""
    print(f"\n--- Results for: {analysis['filename']} ---")
    print(f"Words: {analysis['word_count']:,} | Paragraphs: {analysis['paragraph_count']}")
    print(f"Score: {analysis['score']}/100 | Grade: {analysis['grade']}")
    print(f"Total Issues: {analysis['issue_count']}")

    print(f"\nReadability:")
    r = analysis['readability']
    print(f"  Flesch Reading Ease: {r.get('flesch_reading_ease', 0):.1f}")
    print(f"  Flesch-Kincaid Grade: {r.get('flesch_kincaid_grade', 0):.1f}")
    print(f"  Gunning Fog Index: {r.get('gunning_fog_index', 0):.1f}")

    print(f"\nIssues by Severity:")
    for sev, count in sorted(analysis['issues_by_severity'].items()):
        print(f"  {sev}: {count}")

    print(f"\nTop Issue Categories:")
    sorted_cats = sorted(analysis['issues_by_category'].items(), key=lambda x: x[1], reverse=True)[:10]
    for cat, count in sorted_cats:
        print(f"  {cat}: {count}")

    print(f"\nRoles Extracted:")
    roles = analysis['roles']
    print(f"  Count: {roles['count']}")
    print(f"  Avg Confidence: {roles['avg_confidence']:.2f}")
    if roles['top_roles']:
        print(f"  Top Roles: {', '.join(roles['top_roles'][:5])}")

    if analysis.get('acronyms'):
        print(f"\nAcronyms:")
        acr = analysis['acronyms']
        print(f"  Found: {acr.get('total_found', 0)}")
        print(f"  Defined: {acr.get('defined_count', 0)}")
        print(f"  Undefined: {acr.get('undefined_count', 0)}")

def identify_improvement_opportunities(all_analyses: list) -> dict:
    """Identify areas where the tool could be improved."""
    opportunities = {
        'role_extraction': [],
        'acronym_detection': [],
        'checker_coverage': [],
        'false_positives': [],
        'missing_detections': [],
    }

    # Aggregate statistics
    total_roles = sum(a['roles']['count'] for a in all_analyses)
    total_issues = sum(a['issue_count'] for a in all_analyses)

    # Analyze category distribution
    category_totals = defaultdict(int)
    for a in all_analyses:
        for cat, count in a['issues_by_category'].items():
            category_totals[cat] += count

    print("\n" + "="*60)
    print("AGGREGATE ANALYSIS")
    print("="*60)

    print(f"\nDocuments Scanned: {len(all_analyses)}")
    print(f"Total Issues Found: {total_issues}")
    print(f"Total Roles Extracted: {total_roles}")

    print(f"\nCategory Distribution (All Documents):")
    for cat, count in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = count / max(total_issues, 1) * 100
        print(f"  {cat}: {count} ({pct:.1f}%)")

    # Check for potential improvements
    print("\n" + "="*60)
    print("IMPROVEMENT OPPORTUNITIES")
    print("="*60)

    # Role extraction analysis
    low_confidence_docs = [a for a in all_analyses if a['roles']['avg_confidence'] < 0.7 and a['roles']['count'] > 0]
    if low_confidence_docs:
        print(f"\n1. ROLE EXTRACTION - Low Confidence Documents ({len(low_confidence_docs)}):")
        for doc in low_confidence_docs:
            print(f"   - {doc['filename']}: avg confidence {doc['roles']['avg_confidence']:.2f}")
        opportunities['role_extraction'].append("Consider tuning confidence thresholds or adding more role patterns")

    no_role_docs = [a for a in all_analyses if a['roles']['count'] == 0]
    if no_role_docs:
        print(f"\n2. ROLE EXTRACTION - No Roles Found ({len(no_role_docs)}):")
        for doc in no_role_docs:
            print(f"   - {doc['filename']}")
        opportunities['role_extraction'].append("Some documents may need different extraction patterns")

    # Checker balance
    dominant_cats = [(cat, count) for cat, count in category_totals.items() if count / max(total_issues, 1) > 0.2]
    if dominant_cats:
        print(f"\n3. CHECKER BALANCE - Dominant Categories:")
        for cat, count in dominant_cats:
            print(f"   - {cat}: {count} issues ({count/max(total_issues,1)*100:.1f}%)")
        opportunities['checker_coverage'].append("Some categories dominate - may need tuning or user filtering")

    # Enhanced analyzer usage
    print(f"\n4. ENHANCED ANALYZER COVERAGE:")
    for a in all_analyses:
        metrics = a.get('enhanced_analyzer_metrics', {})
        if metrics:
            for analyzer, data in metrics.items():
                if data.get('available'):
                    print(f"   ✓ {analyzer} active on {a['filename']}")

    return opportunities

def main():
    """Main function to run scans and analyze results."""
    print("AEGIS - Comprehensive Test Scan")
    print("="*60)

    # Get list of test documents
    docs = list(TEST_DOCS_DIR.glob("*.pdf")) + list(TEST_DOCS_DIR.glob("*.docx")) + list(TEST_DOCS_DIR.glob("*.doc"))

    print(f"Found {len(docs)} documents to scan")

    # Select a subset for testing (to save time)
    selected_docs = [
        "NASA_Systems_Engineering_Handbook.pdf",
        "NIST_Cybersecurity_Framework.pdf",
        "FAA_AC_120_92B.pdf",
        "OSHA_Process_Safety_Management.pdf",
        "Stanford_Engineering_Robotics_SOP.docx",
    ]

    docs_to_scan = []
    for doc_name in selected_docs:
        doc_path = TEST_DOCS_DIR / doc_name
        if doc_path.exists():
            docs_to_scan.append(doc_path)
        else:
            print(f"Warning: {doc_name} not found")

    if not docs_to_scan:
        print("No documents found to scan!")
        return

    print(f"\nScanning {len(docs_to_scan)} selected documents...")

    all_analyses = []
    all_results = []

    for doc_path in docs_to_scan:
        result = scan_document(str(doc_path))

        if result:
            all_results.append(result)
            analysis = analyze_results(result, doc_path.name)
            all_analyses.append(analysis)
            print_analysis(analysis)

            # Save individual result
            output_file = OUTPUT_DIR / f"{doc_path.stem}_results.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n  Results saved to: {output_file}")

        time.sleep(1)  # Brief pause between scans

    # Aggregate analysis
    if all_analyses:
        opportunities = identify_improvement_opportunities(all_analyses)

        # Save aggregate analysis
        aggregate_file = OUTPUT_DIR / "aggregate_analysis.json"
        with open(aggregate_file, 'w') as f:
            json.dump({
                'analyses': all_analyses,
                'opportunities': opportunities
            }, f, indent=2, default=str)
        print(f"\nAggregate analysis saved to: {aggregate_file}")

    print("\n" + "="*60)
    print("SCAN COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
