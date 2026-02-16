#!/usr/bin/env python3
"""
Defense Sector Role Extraction Analysis
========================================
Analyze role extraction accuracy on MIL-STD and defense sector documents
with complex structures (tables, bulleted lists).
"""

import sys
import os
import re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure Path is available for relative path resolution
PROJECT_ROOT = Path(__file__).parent

from role_extractor_v3 import RoleExtractor
from pdf_extractor import PDFExtractor


def extract_text_from_document(filepath: str) -> str:
    """Extract text from PDF or DOCX."""
    if filepath.endswith('.pdf'):
        extractor = PDFExtractor(filepath)
        return extractor.full_text
    elif filepath.endswith('.docx'):
        # Use python-docx for DOCX files
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs]
        return '\n'.join(paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {filepath}")


def manual_role_analysis_milstd_38784b():
    """
    Manual analysis of MIL-STD-38784B (Standard Practice for Manuals, Technical)
    This is a defense standard for technical manuals preparation.
    Based on ACTUAL content analysis of the document.
    """
    print("\n" + "=" * 80)
    print("MANUAL ROLE IDENTIFICATION: MIL-STD-38784B")
    print("Standard Practice for Manuals, Technical: General Style and Format")
    print("=" * 80)

    # Based on ACTUAL regex scan of document content:
    manual_roles = {
        # Actual roles found in document (verified by regex scan)
        "government": {"count": 21, "is_role": True, "reason": "Contracting party"},
        "contractor": {"count": 11, "is_role": True, "reason": "Performing party"},
        "user": {"count": 16, "is_role": True, "reason": "End user of manual"},
        "engineer": {"count": 7, "is_role": True, "reason": "Technical role"},
        "personnel": {"count": 5, "is_role": True, "reason": "Generic staff"},
        "technician": {"count": 5, "is_role": True, "reason": "Technical worker"},
        "operator": {"count": 1, "is_role": True, "reason": "Equipment operator"},
        "author": {"count": 1, "is_role": True, "reason": "Document author"},
        "writer": {"count": 1, "is_role": True, "reason": "Technical writer"},
        "staff": {"count": 1, "is_role": True, "reason": "Support staff"},
        "preparing activity": {"count": 1, "is_role": True, "reason": "Document originator"},
        "contracting officer": {"count": 2, "is_role": True, "reason": "Contract authority"},
        "copyright owner": {"count": 1, "is_role": True, "reason": "Rights holder"},
        "worker": {"count": 1, "is_role": True, "reason": "Generic worker"},
        "design engineer": {"count": 1, "is_role": True, "reason": "Engineering role"},
        "maintenance technician": {"count": 1, "is_role": True, "reason": "Maintenance role"},
    }

    true_roles = {k: v for k, v in manual_roles.items() if v["is_role"]}

    print(f"\nManual identification of expected roles (based on actual document scan):")
    print("-" * 70)
    for role in sorted(true_roles.keys()):
        print(f"  - {role}")

    print(f"\n\nMANUAL TOTAL: {len(true_roles)} unique roles expected")
    return true_roles


def manual_role_analysis_milstd_40051():
    """
    Manual analysis of MIL-STD-40051-2A (Preparing Activity Technical Manuals)
    Based on ACTUAL content analysis of the document.
    """
    print("\n" + "=" * 80)
    print("MANUAL ROLE IDENTIFICATION: MIL-STD-40051-2A")
    print("Preparing Activity Technical Manual Requirements")
    print("=" * 80)

    # Based on ACTUAL regex scan of document content:
    manual_roles = {
        # High frequency roles (verified by scan)
        "operator": {"count": 134, "is_role": True, "reason": "Equipment operator"},
        "user": {"count": 75, "is_role": True, "reason": "Manual user"},
        "personnel": {"count": 53, "is_role": True, "reason": "Generic staff"},
        "government": {"count": 48, "is_role": True, "reason": "Contracting party"},
        "maintainer": {"count": 28, "is_role": True, "reason": "Maintenance person"},
        "contractor": {"count": 23, "is_role": True, "reason": "Performing contractor"},
        "quality assurance": {"count": 19, "is_role": True, "reason": "QA function"},
        "technician": {"count": 15, "is_role": True, "reason": "Technical worker"},
        "author": {"count": 13, "is_role": True, "reason": "Document author"},
        "engineer": {"count": 7, "is_role": True, "reason": "Technical role"},
        "maintenance personnel": {"count": 5, "is_role": True, "reason": "Maintenance staff"},
        "inspector": {"count": 5, "is_role": True, "reason": "Quality inspector"},
        "staff": {"count": 3, "is_role": True, "reason": "Support staff"},
        "custodian": {"count": 2, "is_role": True, "reason": "Document custodian"},
        "crew member": {"count": 2, "is_role": True, "reason": "Operational crew"},
        "illustrator": {"count": 1, "is_role": True, "reason": "Graphics specialist"},
        "procuring activity": {"count": 1, "is_role": True, "reason": "Acquisition org"},
        "preparing activity": {"count": 1, "is_role": True, "reason": "Document originator"},
    }

    true_roles = {k: v for k, v in manual_roles.items() if v["is_role"]}

    print(f"\nManual identification of expected roles (based on actual document scan):")
    print("-" * 70)
    for role in sorted(true_roles.keys()):
        print(f"  - {role}")

    print(f"\n\nMANUAL TOTAL: {len(true_roles)} unique roles expected")
    return true_roles


def run_tool_extraction(filepath: str, doc_name: str):
    """Run role extraction on a document."""
    print(f"\n{'=' * 80}")
    print(f"TOOL EXTRACTION: {doc_name}")
    print("=" * 80)

    # Extract text
    print(f"\nExtracting text from: {filepath}")
    text = extract_text_from_document(filepath)
    word_count = len(text.split())
    print(f"Extracted {word_count:,} words")

    # Run role extraction
    extractor = RoleExtractor()
    roles = extractor.extract_from_text(text, source_location=filepath)

    print(f"\nTool extracted {len(roles)} unique roles:")
    print("-" * 70)

    # Sort by frequency
    sorted_roles = sorted(roles.items(), key=lambda x: x[1].frequency, reverse=True)
    for role_name, role_data in sorted_roles[:40]:  # Show top 40
        print(f"  [{role_data.frequency:2d}x] {role_name} (conf: {role_data.avg_confidence:.2f})")

    if len(roles) > 40:
        print(f"  ... and {len(roles) - 40} more roles")

    return roles, text


def compare_results(manual_roles: dict, tool_roles: dict, doc_name: str):
    """Compare manual expectations vs tool extraction."""
    print(f"\n{'=' * 80}")
    print(f"COMPARISON: {doc_name}")
    print("=" * 80)

    manual_names = set(k.lower() for k in manual_roles.keys())
    tool_names = set(k.lower() for k in tool_roles.keys())

    # Exact matches
    exact_matches = manual_names & tool_names

    # Partial matches (one contains the other)
    partial_matches = []
    unmatched_manual = manual_names - exact_matches
    unmatched_tool = tool_names - exact_matches

    for m in list(unmatched_manual):
        for t in list(unmatched_tool):
            # Check if one contains the other or they share significant overlap
            if m in t or t in m:
                partial_matches.append((m, t))
                if m in unmatched_manual:
                    unmatched_manual.discard(m)
                if t in unmatched_tool:
                    unmatched_tool.discard(t)

    # Calculate metrics
    matched_count = len(exact_matches) + len(partial_matches)
    precision = matched_count / len(tool_names) * 100 if tool_names else 0
    recall = matched_count / len(manual_names) * 100 if manual_names else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\nExact matches ({len(exact_matches)}):")
    for m in sorted(exact_matches)[:20]:
        print(f"  ✓ {m}")
    if len(exact_matches) > 20:
        print(f"  ... and {len(exact_matches) - 20} more")

    print(f"\nPartial matches ({len(partial_matches)}):")
    for m, t in partial_matches[:10]:
        print(f"  ~ Manual: '{m}' <-> Tool: '{t}'")

    print(f"\nManual only ({len(unmatched_manual)}) - Tool may have missed:")
    for m in sorted(unmatched_manual):
        print(f"  ? {m}")

    print(f"\nTool found additionally ({len(unmatched_tool)}) - Valid roles found:")
    for t in sorted(list(unmatched_tool)[:15]):
        print(f"  + {t}")
    if len(unmatched_tool) > 15:
        print(f"  ... and {len(unmatched_tool) - 15} more")

    print(f"\n{'=' * 80}")
    print("METRICS:")
    print(f"  Expected roles: {len(manual_names)}")
    print(f"  Tool found: {len(tool_names)}")
    print(f"  Matched: {matched_count} (exact: {len(exact_matches)}, partial: {len(partial_matches)})")
    print(f"  Precision: {precision:.1f}%")
    print(f"  Recall: {recall:.1f}%")
    print(f"  F1 Score: {f1:.1f}%")

    return {
        'doc_name': doc_name,
        'manual_count': len(manual_names),
        'tool_count': len(tool_names),
        'matched': matched_count,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'missed': list(unmatched_manual),
        'extra': list(unmatched_tool)
    }


def analyze_text_for_roles(text: str, doc_name: str):
    """
    Perform detailed analysis of actual roles in extracted text.
    This does a more thorough manual analysis based on actual document content.
    """
    print(f"\n{'=' * 80}")
    print(f"DETAILED TEXT ANALYSIS: {doc_name}")
    print("=" * 80)

    # Common defense/technical document role patterns
    role_patterns = [
        # Government roles
        r'\b(contracting\s+officer)\b',
        r'\b(contracting\s+officer\s+representative)\b',
        r'\b(COR)\b',
        r'\b(government)\b',
        r'\b(program\s+manager)\b',
        r'\b(project\s+officer)\b',
        r'\b(technical\s+authority)\b',
        r'\b(procuring\s+activity)\b',
        r'\b(requiring\s+activity)\b',
        r'\b(preparing\s+activity)\b',
        r'\b(reviewing\s+activity)\b',
        r'\b(approving\s+authority)\b',

        # Contractor roles
        r'\b(contractor)\b',
        r'\b(prime\s+contractor)\b',
        r'\b(subcontractor)\b',
        r'\b(vendor)\b',
        r'\b(supplier)\b',

        # Technical roles
        r'\b(technical\s+writer)\b',
        r'\b(illustrator)\b',
        r'\b(editor)\b',
        r'\b(engineer)\b',
        r'\b(systems\s+engineer)\b',
        r'\b(design\s+engineer)\b',
        r'\b(logistics\s+engineer)\b',
        r'\b(subject\s+matter\s+expert)\b',
        r'\b(SME)\b',

        # Quality roles
        r'\b(quality\s+assurance)\b',
        r'\b(quality\s+assurance\s+representative)\b',
        r'\b(configuration\s+manager)\b',
        r'\b(data\s+manager)\b',

        # User roles
        r'\b(operator)\b',
        r'\b(maintainer)\b',
        r'\b(maintenance\s+technician)\b',
        r'\b(maintenance\s+personnel)\b',
        r'\b(crew\s+member)\b',
        r'\b(user)\b',
        r'\b(custodian)\b',

        # Personnel categories
        r'\b(personnel)\b',
        r'\b(staff)\b',
        r'\b(employees?)\b',
    ]

    found_roles = {}
    text_lower = text.lower()

    for pattern in role_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        if matches:
            role_name = matches[0] if isinstance(matches[0], str) else matches[0][0]
            role_name = role_name.strip().lower()
            found_roles[role_name] = len(matches)

    print(f"\nRoles found in actual text (regex scan):")
    print("-" * 70)
    for role, count in sorted(found_roles.items(), key=lambda x: -x[1]):
        print(f"  [{count:3d}x] {role}")

    return found_roles


def main():
    """Main analysis function."""
    print("=" * 80)
    print("DEFENSE SECTOR ROLE EXTRACTION ANALYSIS")
    print("Testing on MIL-STD documents with complex tables and structures")
    print("=" * 80)

    # Document paths
    docs = [
        {
            'path': str(PROJECT_ROOT / 'test_documents' / 'batch_test' / 'MIL-STD-38784B.pdf'),
            'name': 'MIL-STD-38784B',
            'manual_func': manual_role_analysis_milstd_38784b
        },
        {
            'path': str(PROJECT_ROOT / 'test_documents' / 'batch_test' / 'MIL-STD-40051-2A.pdf'),
            'name': 'MIL-STD-40051-2A',
            'manual_func': manual_role_analysis_milstd_40051
        }
    ]

    results = []

    for doc in docs:
        if not os.path.exists(doc['path']):
            print(f"\n[SKIP] File not found: {doc['path']}")
            continue

        # Get manual role expectations
        manual_roles = doc['manual_func']()

        # Run tool extraction
        tool_roles, text = run_tool_extraction(doc['path'], doc['name'])

        # Analyze actual text content
        text_roles = analyze_text_for_roles(text, doc['name'])

        # Compare results
        result = compare_results(manual_roles, tool_roles, doc['name'])
        results.append(result)

    # Print overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    print(f"\n{'Document':<30} {'Expected':>10} {'Found':>10} {'Match':>10} {'Prec':>8} {'Recall':>8} {'F1':>8}")
    print("-" * 94)

    total_precision = 0
    total_recall = 0
    total_f1 = 0

    for r in results:
        print(f"{r['doc_name']:<30} {r['manual_count']:>10} {r['tool_count']:>10} {r['matched']:>10} "
              f"{r['precision']:>7.1f}% {r['recall']:>7.1f}% {r['f1']:>7.1f}%")
        total_precision += r['precision']
        total_recall += r['recall']
        total_f1 += r['f1']

    if results:
        n = len(results)
        print("-" * 94)
        print(f"{'AVERAGE':<30} {'-':>10} {'-':>10} {'-':>10} "
              f"{total_precision/n:>7.1f}% {total_recall/n:>7.1f}% {total_f1/n:>7.1f}%")

    # Print any consistently missed roles
    print("\n" + "=" * 80)
    print("ROLES THAT MAY NEED TO BE ADDED TO KNOWN_ROLES")
    print("=" * 80)

    all_missed = set()
    for r in results:
        all_missed.update(r.get('missed', []))

    if all_missed:
        print("\nPotentially missing roles:")
        for role in sorted(all_missed):
            print(f"  - {role}")
    else:
        print("\nNo consistently missed roles - 100% recall achieved!")


if __name__ == "__main__":
    main()
