#!/usr/bin/env python3
"""
Aerospace Engineering Role Extraction Analysis
===============================================
Test role extraction on aerospace/aviation documents including
NASA standards, FAA documents, and aerospace engineering procedures.
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from role_extractor_v3 import RoleExtractor
from pdf_extractor import PDFExtractor


def extract_text_from_document(filepath: str) -> str:
    """Extract text from PDF or DOCX."""
    if filepath.endswith('.pdf'):
        extractor = PDFExtractor(filepath)
        return extractor.full_text
    elif filepath.endswith('.docx'):
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs]
        return '\n'.join(paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {filepath}")


def scan_document_for_aerospace_roles(filepath: str):
    """Scan a document for aerospace-specific roles using regex patterns."""
    text = extract_text_from_document(filepath)
    text_lower = text.lower()

    # Aerospace-specific role patterns
    role_patterns = [
        # Generic engineering/management roles
        'engineer', 'engineers', 'manager', 'managers', 'director', 'directors',
        'analyst', 'analysts', 'specialist', 'specialists', 'technician', 'technicians',
        'supervisor', 'supervisors', 'coordinator', 'coordinators', 'lead', 'leads',
        'administrator', 'administrators', 'operator', 'operators', 'inspector', 'inspectors',

        # Aerospace-specific roles
        'systems engineer', 'system engineer', 'flight engineer', 'test engineer',
        'design engineer', 'software engineer', 'hardware engineer', 'avionics engineer',
        'propulsion engineer', 'structural engineer', 'thermal engineer',
        'reliability engineer', 'safety engineer', 'quality engineer',
        'manufacturing engineer', 'production engineer', 'integration engineer',
        'verification engineer', 'validation engineer', 'mission assurance',

        # Flight operations
        'pilot', 'pilots', 'pilot in command', 'second in command',
        'flight crew', 'crew member', 'crew members', 'flight attendant',
        'dispatcher', 'dispatchers', 'flight dispatcher', 'load master',
        'ground crew', 'maintenance crew',

        # Management/leadership
        'chief engineer', 'chief pilot', 'program manager', 'project manager',
        'mission director', 'flight director', 'operations director',
        'technical lead', 'team lead', 'discipline lead', 'subsystem lead',
        'principal investigator', 'project scientist',

        # Quality/Safety
        'quality assurance', 'quality control', 'safety officer',
        'designated engineering representative', 'designated airworthiness representative',
        'aviation safety inspector', 'principal operations inspector',
        'principal maintenance inspector', 'principal avionics inspector',

        # Government/Certification
        'contracting officer', 'contracting officer representative',
        'government', 'contractor', 'subcontractor', 'certificate holder',
        'accountable executive', 'authorizing official',

        # Boards and teams
        'configuration control board', 'engineering review board',
        'technical review board', 'safety review board', 'review board',
        'integrated product team', 'test team', 'development team',

        # Generic
        'personnel', 'staff', 'user', 'users', 'customer', 'customers',
        'stakeholder', 'stakeholders', 'vendor', 'vendors', 'supplier', 'suppliers',
        'maintainer', 'maintainers', 'owner', 'owners',
    ]

    found_roles = {}
    for role in role_patterns:
        pattern = rf'\b{re.escape(role)}\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            found_roles[role] = len(matches)

    return found_roles, text, len(text.split())


def run_tool_extraction(text: str, filepath: str):
    """Run the role extractor tool on text."""
    extractor = RoleExtractor()
    roles = extractor.extract_from_text(text, source_location=filepath)
    return roles


def compare_and_report(doc_name: str, manual_roles: dict, tool_roles: dict):
    """Compare manual scan vs tool extraction and report."""
    manual_names = set(k.lower() for k in manual_roles.keys())
    tool_names = set(k.lower() for k in tool_roles.keys())

    # Find matches
    exact_matches = set()
    partial_matches = []

    for m in manual_names:
        if m in tool_names:
            exact_matches.add(m)
        else:
            for t in tool_names:
                if m in t or t in m:
                    partial_matches.append((m, t))
                    break

    matched_manual = exact_matches | set(p[0] for p in partial_matches)
    missed = manual_names - matched_manual

    recall = len(matched_manual) / len(manual_names) * 100 if manual_names else 100

    return {
        'doc_name': doc_name,
        'manual_count': len(manual_names),
        'tool_count': len(tool_names),
        'exact_matches': len(exact_matches),
        'partial_matches': len(partial_matches),
        'total_matched': len(matched_manual),
        'missed': list(missed),
        'recall': recall
    }


def main():
    """Main analysis function."""
    print("=" * 90)
    print("AEROSPACE ENGINEERING ROLE EXTRACTION ANALYSIS")
    print("Testing on NASA, FAA, and aerospace engineering documents")
    print("=" * 90)

    base_path = '/Users/nick/Desktop/Work_Tools/TechWriterReview/test_documents'

    # Aerospace-focused documents
    docs = [
        # NASA Documents
        (f'{base_path}/NASA_Systems_Engineering_Handbook.pdf', 'NASA SE Handbook (Full)'),
        (f'{base_path}/batch_test/NASA_SE_Handbook.pdf', 'NASA SE Handbook (Batch)'),
        (f'{base_path}/NASA_Materials_Processes_Standard.pdf', 'NASA Materials & Processes'),

        # FAA Documents
        (f'{base_path}/FAA_AC_120_92B.pdf', 'FAA AC 120-92B (SMS)'),
        (f'{base_path}/batch_test/FAA_Requirements_Engineering.pdf', 'FAA Requirements Eng'),
        (f'{base_path}/batch_test/FAA_VRTM_Requirements.pdf', 'FAA VRTM Requirements'),

        # KSC (Kennedy Space Center)
        (f'{base_path}/KSC_Specs_Standards.pdf', 'KSC Specs & Standards'),
    ]

    results = []

    for filepath, doc_name in docs:
        if not os.path.exists(filepath):
            print(f"\n[SKIP] File not found: {filepath}")
            continue

        print(f"\n{'=' * 90}")
        print(f"ANALYZING: {doc_name}")
        print(f"File: {os.path.basename(filepath)}")
        print("=" * 90)

        # Scan document for aerospace roles
        print("\n1. Scanning document for aerospace roles...")
        manual_roles, text, word_count = scan_document_for_aerospace_roles(filepath)
        print(f"   Word count: {word_count:,}")
        print(f"   Aerospace roles found by regex: {len(manual_roles)}")

        # Show top roles
        top_roles = sorted(manual_roles.items(), key=lambda x: -x[1])[:20]
        print("\n   Top aerospace roles in document:")
        for role, count in top_roles:
            print(f"      [{count:4d}x] {role}")

        # Run tool extraction
        print("\n2. Running role extractor tool...")
        tool_roles = run_tool_extraction(text, filepath)
        print(f"   Roles extracted by tool: {len(tool_roles)}")

        # Show top tool extractions
        sorted_tool = sorted(tool_roles.items(), key=lambda x: x[1].frequency, reverse=True)[:20]
        print("\n   Top tool extractions:")
        for role_name, role_data in sorted_tool:
            print(f"      [{role_data.frequency:4d}x] {role_name} (conf: {role_data.avg_confidence:.2f})")

        # Compare
        print("\n3. Comparing results...")
        result = compare_and_report(doc_name, manual_roles, tool_roles)
        results.append(result)

        print(f"\n   Exact matches: {result['exact_matches']}")
        print(f"   Partial matches: {result['partial_matches']}")
        print(f"   Total matched: {result['total_matched']} / {result['manual_count']}")
        print(f"   RECALL: {result['recall']:.1f}%")

        if result['missed']:
            print(f"\n   Missed roles ({len(result['missed'])}):")
            for m in sorted(result['missed'])[:15]:
                count = manual_roles.get(m, 0)
                print(f"      - {m} ({count}x in doc)")
            if len(result['missed']) > 15:
                print(f"      ... and {len(result['missed']) - 15} more")

    # Summary
    print("\n" + "=" * 90)
    print("OVERALL AEROSPACE ANALYSIS SUMMARY")
    print("=" * 90)

    print(f"\n{'Document':<35} {'Type':<20} {'Manual':>8} {'Tool':>8} {'Match':>8} {'Recall':>10}")
    print("-" * 95)

    total_recall = 0
    for r in results:
        doc_type = "NASA" if "NASA" in r['doc_name'] else "FAA" if "FAA" in r['doc_name'] else "KSC"
        print(f"{r['doc_name']:<35} {doc_type:<20} {r['manual_count']:>8} {r['tool_count']:>8} "
              f"{r['total_matched']:>8} {r['recall']:>9.1f}%")
        total_recall += r['recall']

    avg_recall = total_recall / len(results) if results else 0
    print("-" * 95)
    print(f"{'AVERAGE':<35} {'':<20} {'-':>8} {'-':>8} {'-':>8} {avg_recall:>9.1f}%")

    # Aerospace-specific missed roles
    all_missed = {}
    for r in results:
        for m in r['missed']:
            all_missed[m] = all_missed.get(m, 0) + 1

    if all_missed:
        print("\n" + "=" * 90)
        print("AEROSPACE ROLES POTENTIALLY NEEDING ATTENTION")
        print("=" * 90)

        # Focus on aerospace-specific roles missed in multiple docs
        aerospace_keywords = ['flight', 'pilot', 'avionics', 'propulsion', 'mission',
                            'spacecraft', 'aircraft', 'aviation', 'airworth', 'certif']

        multi_missed = [(k, v) for k, v in all_missed.items() if v >= 2]
        aerospace_missed = [(k, v) for k, v in all_missed.items()
                          if any(kw in k for kw in aerospace_keywords)]

        if multi_missed:
            print("\nMissed in 2+ documents:")
            for role, count in sorted(multi_missed, key=lambda x: -x[1])[:10]:
                print(f"   - {role} (missed in {count} docs)")

        if aerospace_missed:
            print("\nAerospace-specific roles missed:")
            for role, count in sorted(aerospace_missed, key=lambda x: -x[1])[:10]:
                print(f"   - {role}")
    else:
        print("\n" + "=" * 90)
        print("EXCELLENT: No aerospace roles consistently missed!")
        print("=" * 90)

    # Final verdict
    print("\n" + "=" * 90)
    if avg_recall >= 95:
        print(f"AEROSPACE RESULT: EXCELLENT - Average recall {avg_recall:.1f}%")
    elif avg_recall >= 85:
        print(f"AEROSPACE RESULT: GOOD - Average recall {avg_recall:.1f}%")
    else:
        print(f"AEROSPACE RESULT: NEEDS IMPROVEMENT - Average recall {avg_recall:.1f}%")
    print("=" * 90)


if __name__ == "__main__":
    main()
