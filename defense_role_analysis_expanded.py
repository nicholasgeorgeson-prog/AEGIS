#!/usr/bin/env python3
"""
Expanded Defense/Government Sector Role Extraction Analysis
============================================================
Test role extraction on multiple MIL-STD, NASA, NIST, and government documents
with complex structures (tables, bulleted lists).
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


def scan_document_for_roles(filepath: str):
    """Scan a document and find actual roles using regex patterns."""
    text = extract_text_from_document(filepath)
    text_lower = text.lower()

    # Common role patterns to search for
    role_patterns = [
        # Single word roles
        'operator', 'operators', 'maintainer', 'maintainers', 'user', 'users',
        'government', 'contractor', 'contractors', 'subcontractor', 'subcontractors',
        'personnel', 'technician', 'technicians', 'inspector', 'inspectors',
        'engineer', 'engineers', 'manager', 'managers', 'director', 'directors',
        'analyst', 'analysts', 'specialist', 'specialists', 'coordinator', 'coordinators',
        'administrator', 'administrators', 'supervisor', 'supervisors',
        'auditor', 'auditors', 'reviewer', 'reviewers', 'approver', 'approvers',
        'author', 'authors', 'editor', 'editors', 'illustrator', 'illustrators',
        'custodian', 'custodians', 'owner', 'owners', 'stakeholder', 'stakeholders',
        'vendor', 'vendors', 'supplier', 'suppliers', 'customer', 'customers',
        'staff', 'worker', 'workers', 'employee', 'employees', 'employer', 'employers',

        # Multi-word roles
        'program manager', 'project manager', 'systems engineer', 'system engineer',
        'contracting officer', 'contracting officer representative',
        'quality assurance', 'quality control', 'configuration manager',
        'data manager', 'risk manager', 'safety manager', 'test engineer',
        'design engineer', 'software engineer', 'hardware engineer',
        'principal investigator', 'technical lead', 'team lead',
        'subject matter expert', 'technical authority', 'approving authority',
        'preparing activity', 'reviewing activity', 'procuring activity',
        'maintenance personnel', 'operating personnel', 'technical personnel',
        'engineering personnel', 'flight crew', 'crew member', 'crew members',
        'accountable executive', 'senior management', 'executive management',
        'information system security officer', 'isso', 'issm',
        'authorizing official', 'system owner', 'information owner',
    ]

    found_roles = {}
    for role in role_patterns:
        # Use word boundaries for accurate matching
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
            # Check for partial matches
            for t in tool_names:
                if m in t or t in m:
                    partial_matches.append((m, t))
                    break

    matched_manual = exact_matches | set(p[0] for p in partial_matches)
    missed = manual_names - matched_manual

    # Calculate recall
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
    print("EXPANDED DEFENSE/GOVERNMENT SECTOR ROLE EXTRACTION ANALYSIS")
    print("Testing on MIL-STD, NASA, NIST, and government technical documents")
    print("=" * 90)

    # Documents to test
    base_path = '/Users/nick/Desktop/Work_Tools/TechWriterReview/test_documents'
    docs = [
        # MIL-STD documents
        (f'{base_path}/batch_test/MIL-STD-38784B.pdf', 'MIL-STD-38784B (Tech Manuals)'),
        (f'{base_path}/batch_test/MIL-STD-40051-2A.pdf', 'MIL-STD-40051-2A (TM Prep)'),

        # NASA documents (defense-adjacent, complex structure)
        (f'{base_path}/batch_test/NASA_SE_Handbook.pdf', 'NASA SE Handbook'),
        (f'{base_path}/NASA_Systems_Engineering_Handbook.pdf', 'NASA Systems Engineering'),

        # NIST Security documents (government, defense-adjacent)
        (f'{base_path}/NIST_SP_800_53_Security_Controls.pdf', 'NIST SP 800-53 (Security)'),
        (f'{base_path}/batch_test/../NIST_SP_800_171.pdf', 'NIST SP 800-171 (CUI)'),

        # FAA documents (government, aviation)
        (f'{base_path}/batch_test/FAA_Requirements_Engineering.pdf', 'FAA Requirements Eng'),
        (f'{base_path}/batch_test/FAA_VRTM_Requirements.pdf', 'FAA VRTM Requirements'),

        # KSC (Kennedy Space Center - defense/space)
        (f'{base_path}/KSC_Specs_Standards.pdf', 'KSC Specs & Standards'),
    ]

    results = []

    for filepath, doc_name in docs:
        if not os.path.exists(filepath):
            print(f"\n[SKIP] File not found: {filepath}")
            continue

        print(f"\n{'=' * 90}")
        print(f"ANALYZING: {doc_name}")
        print(f"File: {filepath}")
        print("=" * 90)

        # Scan document for roles
        print("\n1. Scanning document for roles (regex)...")
        manual_roles, text, word_count = scan_document_for_roles(filepath)
        print(f"   Word count: {word_count:,}")
        print(f"   Roles found by regex scan: {len(manual_roles)}")

        # Show top roles found
        top_roles = sorted(manual_roles.items(), key=lambda x: -x[1])[:15]
        print("\n   Top roles in document:")
        for role, count in top_roles:
            print(f"      [{count:3d}x] {role}")

        # Run tool extraction
        print("\n2. Running role extractor tool...")
        tool_roles = run_tool_extraction(text, filepath)
        print(f"   Roles extracted by tool: {len(tool_roles)}")

        # Show top tool extractions
        sorted_tool = sorted(tool_roles.items(), key=lambda x: x[1].frequency, reverse=True)[:15]
        print("\n   Top tool extractions:")
        for role_name, role_data in sorted_tool:
            print(f"      [{role_data.frequency:3d}x] {role_name} (conf: {role_data.avg_confidence:.2f})")

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
            for m in sorted(result['missed'])[:10]:
                count = manual_roles.get(m, 0)
                print(f"      - {m} ({count}x in doc)")
            if len(result['missed']) > 10:
                print(f"      ... and {len(result['missed']) - 10} more")

    # Summary
    print("\n" + "=" * 90)
    print("OVERALL SUMMARY")
    print("=" * 90)

    print(f"\n{'Document':<40} {'Manual':>8} {'Tool':>8} {'Match':>8} {'Recall':>10}")
    print("-" * 80)

    total_recall = 0
    for r in results:
        print(f"{r['doc_name']:<40} {r['manual_count']:>8} {r['tool_count']:>8} "
              f"{r['total_matched']:>8} {r['recall']:>9.1f}%")
        total_recall += r['recall']

    avg_recall = total_recall / len(results) if results else 0
    print("-" * 80)
    print(f"{'AVERAGE':<40} {'-':>8} {'-':>8} {'-':>8} {avg_recall:>9.1f}%")

    # List any consistently missed roles
    all_missed = {}
    for r in results:
        for m in r['missed']:
            all_missed[m] = all_missed.get(m, 0) + 1

    if all_missed:
        print("\n" + "=" * 90)
        print("ROLES MISSED IN MULTIPLE DOCUMENTS (may need to be added)")
        print("=" * 90)

        multi_missed = [(k, v) for k, v in all_missed.items() if v >= 2]
        if multi_missed:
            for role, count in sorted(multi_missed, key=lambda x: -x[1]):
                print(f"  - {role} (missed in {count} documents)")
        else:
            print("  No roles missed in multiple documents!")

    # Final verdict
    print("\n" + "=" * 90)
    if avg_recall >= 95:
        print(f"RESULT: EXCELLENT - Average recall {avg_recall:.1f}% (target: 95%+)")
    elif avg_recall >= 85:
        print(f"RESULT: GOOD - Average recall {avg_recall:.1f}% (target: 95%+)")
    else:
        print(f"RESULT: NEEDS IMPROVEMENT - Average recall {avg_recall:.1f}% (target: 95%+)")
    print("=" * 90)


if __name__ == "__main__":
    main()
