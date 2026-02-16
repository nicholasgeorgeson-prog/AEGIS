#!/usr/bin/env python3
"""
Manual Role Extraction Analysis
===============================
Compare manual role identification with tool extraction.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Sample from FAA AC 120-92B (Safety Management Systems)
FAA_SAMPLE = """
The accountable executive is the single person who has ultimate responsibility for
the certificate holder's SMS. The accountable executive is typically a senior
official such as the CEO, President, or General Manager. Regardless of their title,
the accountable executive must have full control of the financial and human resources
required for operations and must have final authority over operations under the
certificate.

The accountable executive is responsible for establishing and promoting the safety
policy, ensuring that the SMS is properly implemented and performing as designed,
and ensuring that the necessary resources are allocated for safety operations.

Management personnel include all individuals who have been designated to carry out
safety management functions. These individuals may include the Director of Safety,
Director of Operations, Director of Maintenance, Chief Pilot, and other personnel
with specific safety roles.

The Director of Safety typically serves as the primary point of contact for SMS
implementation and may also serve as the Safety Manager or SMS Coordinator. This
individual often reports directly to the accountable executive.

Flight crew members, maintenance personnel, dispatchers, and ground handling staff
all have responsibilities under the SMS. These front-line employees are expected to
identify hazards and report safety concerns through appropriate channels.

The Safety Review Board (SRB) is typically composed of senior management representatives
who meet regularly to review safety performance and make risk-based decisions. The
accountable executive usually chairs the SRB or designates a senior representative.
"""

# Sample from OSHA Process Safety Management
OSHA_SAMPLE = """
The employer shall develop a written plan of action regarding the employee participation
required under this standard. The employer shall consult with employees and their
representatives on the conduct and development of process hazard analyses.

The contract employer shall assure that each contract employee is trained in the work
practices necessary to safely perform their job. The contract employer shall assure
that each contract employee follows the safety rules of the host employer.

The operating personnel who operate the process shall be consulted during the
development of the training programs. The training shall include emphasis on the
specific safety and health hazards, emergency operations, and safe work practices.

A process hazard analysis team shall include at least one employee who has experience
and knowledge specific to the process being evaluated. The team leader shall be
qualified to lead the analysis.

Plant managers, supervisors, and engineers shall be designated to handle emergency
shutdown procedures. The emergency coordinator shall be given authority to take
necessary actions during an emergency.

The process safety coordinator is responsible for coordinating all elements of the
process safety management program. This individual typically reports to the plant
manager or director of safety.
"""

# Sample from Stanford Robotics SOP
STANFORD_SAMPLE = """
The Principal Investigator (PI) is responsible for ensuring compliance with all
safety requirements in the laboratory. The PI must approve all high-risk operations
before they can proceed.

Lab supervisors shall ensure that all personnel working in the laboratory have
completed required safety training. The lab supervisor reports to the PI on all
safety matters.

Research staff members are responsible for following established safety procedures.
Graduate students and postdoctoral researchers must complete lab-specific training
before working independently.

The Environmental Health and Safety (EH&S) coordinator provides consultation and
oversight for laboratory safety programs. The EH&S representative shall conduct
periodic inspections of the laboratory.

Equipment operators must be trained and certified before using hazardous equipment.
The equipment manager shall maintain training records for all certified operators.

The department chair has oversight responsibility for all research activities within
the department. The safety committee reviews and approves all new protocols involving
hazardous materials or operations.
"""


def manual_role_extraction(text: str, doc_name: str):
    """Manually identify roles in text."""
    print(f"\n{'=' * 70}")
    print(f"MANUAL ROLE ANALYSIS: {doc_name}")
    print("=" * 70)

    # My manual identification of roles
    # Looking for: job titles, positions, organizational roles
    manual_roles = []

    # Split into sentences for analysis
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

    print(f"\nAnalyzing {len(sentences)} sentences...")
    print("-" * 70)

    return manual_roles


def analyze_faa_roles():
    """Manual analysis of FAA document roles."""
    print("\n" + "=" * 70)
    print("MANUAL ROLE IDENTIFICATION: FAA AC 120-92B")
    print("=" * 70)

    # Roles I manually identify in the FAA sample:
    manual_roles = {
        "accountable executive": {
            "count": 5,
            "contexts": ["ultimate responsibility", "senior official", "full control", "establishing safety policy", "chairs SRB"],
            "is_role": True,
            "reason": "Specific regulatory position with defined responsibilities"
        },
        "CEO": {
            "count": 1,
            "contexts": ["example of accountable executive"],
            "is_role": True,
            "reason": "Corporate officer title"
        },
        "President": {
            "count": 1,
            "contexts": ["example of accountable executive"],
            "is_role": True,
            "reason": "Corporate officer title"
        },
        "General Manager": {
            "count": 1,
            "contexts": ["example of accountable executive"],
            "is_role": True,
            "reason": "Management position"
        },
        "management personnel": {
            "count": 1,
            "contexts": ["carry out safety management functions"],
            "is_role": True,
            "reason": "Collective role designation"
        },
        "Director of Safety": {
            "count": 2,
            "contexts": ["safety management functions", "primary point of contact"],
            "is_role": True,
            "reason": "Specific management position"
        },
        "Director of Operations": {
            "count": 1,
            "contexts": ["safety management functions"],
            "is_role": True,
            "reason": "Specific management position"
        },
        "Director of Maintenance": {
            "count": 1,
            "contexts": ["safety management functions"],
            "is_role": True,
            "reason": "Specific management position"
        },
        "Chief Pilot": {
            "count": 1,
            "contexts": ["safety management functions"],
            "is_role": True,
            "reason": "Specific aviation position"
        },
        "Safety Manager": {
            "count": 1,
            "contexts": ["may serve as"],
            "is_role": True,
            "reason": "Management position"
        },
        "SMS Coordinator": {
            "count": 1,
            "contexts": ["may serve as"],
            "is_role": True,
            "reason": "Specific program coordinator"
        },
        "Flight crew members": {
            "count": 1,
            "contexts": ["have responsibilities under SMS"],
            "is_role": True,
            "reason": "Operational personnel category"
        },
        "maintenance personnel": {
            "count": 1,
            "contexts": ["have responsibilities under SMS"],
            "is_role": True,
            "reason": "Operational personnel category"
        },
        "dispatchers": {
            "count": 1,
            "contexts": ["have responsibilities under SMS"],
            "is_role": True,
            "reason": "Operational position"
        },
        "ground handling staff": {
            "count": 1,
            "contexts": ["have responsibilities under SMS"],
            "is_role": True,
            "reason": "Operational personnel category"
        },
        "front-line employees": {
            "count": 1,
            "contexts": ["identify hazards"],
            "is_role": True,
            "reason": "Collective role designation"
        },
        "Safety Review Board": {
            "count": 1,
            "contexts": ["review safety performance"],
            "is_role": True,
            "reason": "Organizational body with defined responsibilities"
        },
        "certificate holder": {
            "count": 1,
            "contexts": ["SMS ownership"],
            "is_role": True,
            "reason": "Regulatory entity designation"
        },
        "senior management representatives": {
            "count": 1,
            "contexts": ["compose SRB"],
            "is_role": True,
            "reason": "Collective role designation"
        },
        "senior representative": {
            "count": 1,
            "contexts": ["designated by accountable executive"],
            "is_role": True,
            "reason": "Delegate position"
        }
    }

    true_roles = {k: v for k, v in manual_roles.items() if v["is_role"]}

    print(f"\nManual identification of roles:")
    print("-" * 70)
    for role, data in true_roles.items():
        print(f"  [{data['count']}x] {role}")
        print(f"        Context: {data['contexts'][0]}")

    print(f"\n\nMANUAL TOTAL: {len(true_roles)} unique roles")
    return true_roles


def analyze_osha_roles():
    """Manual analysis of OSHA document roles."""
    print("\n" + "=" * 70)
    print("MANUAL ROLE IDENTIFICATION: OSHA Process Safety Management")
    print("=" * 70)

    manual_roles = {
        "employer": {
            "count": 2,
            "contexts": ["develop written plan", "consult with employees"],
            "is_role": True,
            "reason": "Party with regulatory responsibilities"
        },
        "employees": {
            "count": 1,
            "contexts": ["consulted on process hazard analyses"],
            "is_role": True,
            "reason": "Worker category"
        },
        "contract employer": {
            "count": 2,
            "contexts": ["assure training", "assure safety rules followed"],
            "is_role": True,
            "reason": "Specific employer type"
        },
        "contract employee": {
            "count": 2,
            "contexts": ["trained in work practices", "follows safety rules"],
            "is_role": True,
            "reason": "Specific employee type"
        },
        "host employer": {
            "count": 1,
            "contexts": ["safety rules"],
            "is_role": True,
            "reason": "Specific employer type"
        },
        "operating personnel": {
            "count": 1,
            "contexts": ["operate the process", "consulted on training"],
            "is_role": True,
            "reason": "Operational worker category"
        },
        "process hazard analysis team": {
            "count": 1,
            "contexts": ["evaluate process"],
            "is_role": True,
            "reason": "Team designation with defined role"
        },
        "team leader": {
            "count": 1,
            "contexts": ["qualified to lead analysis"],
            "is_role": True,
            "reason": "Leadership position"
        },
        "Plant managers": {
            "count": 2,
            "contexts": ["emergency shutdown", "process safety coordinator reports to"],
            "is_role": True,
            "reason": "Management position"
        },
        "supervisors": {
            "count": 1,
            "contexts": ["emergency shutdown"],
            "is_role": True,
            "reason": "Management position"
        },
        "engineers": {
            "count": 1,
            "contexts": ["emergency shutdown"],
            "is_role": True,
            "reason": "Professional category"
        },
        "emergency coordinator": {
            "count": 1,
            "contexts": ["authority during emergency"],
            "is_role": True,
            "reason": "Specific emergency role"
        },
        "process safety coordinator": {
            "count": 1,
            "contexts": ["coordinating all elements"],
            "is_role": True,
            "reason": "Specific program coordinator"
        },
        "director of safety": {
            "count": 1,
            "contexts": ["reports to"],
            "is_role": True,
            "reason": "Management position"
        }
    }

    true_roles = {k: v for k, v in manual_roles.items() if v["is_role"]}

    print(f"\nManual identification of roles:")
    print("-" * 70)
    for role, data in true_roles.items():
        print(f"  [{data['count']}x] {role}")

    print(f"\n\nMANUAL TOTAL: {len(true_roles)} unique roles")
    return true_roles


def analyze_stanford_roles():
    """Manual analysis of Stanford SOP roles."""
    print("\n" + "=" * 70)
    print("MANUAL ROLE IDENTIFICATION: Stanford Robotics SOP")
    print("=" * 70)

    manual_roles = {
        "Principal Investigator": {
            "count": 2,
            "contexts": ["ensuring compliance", "approve high-risk operations"],
            "is_role": True,
            "reason": "Academic leadership position"
        },
        "PI": {
            "count": 2,
            "contexts": ["approve", "reports to"],
            "is_role": True,
            "reason": "Acronym for Principal Investigator"
        },
        "Lab supervisors": {
            "count": 1,
            "contexts": ["ensure personnel trained"],
            "is_role": True,
            "reason": "Supervisory position"
        },
        "lab supervisor": {
            "count": 1,
            "contexts": ["reports to PI"],
            "is_role": True,
            "reason": "Supervisory position"
        },
        "Research staff members": {
            "count": 1,
            "contexts": ["following safety procedures"],
            "is_role": True,
            "reason": "Personnel category"
        },
        "Graduate students": {
            "count": 1,
            "contexts": ["complete training"],
            "is_role": True,
            "reason": "Student category with responsibilities"
        },
        "postdoctoral researchers": {
            "count": 1,
            "contexts": ["complete training"],
            "is_role": True,
            "reason": "Researcher category"
        },
        "EH&S coordinator": {
            "count": 1,
            "contexts": ["provides consultation"],
            "is_role": True,
            "reason": "Safety coordinator role"
        },
        "EH&S representative": {
            "count": 1,
            "contexts": ["conduct inspections"],
            "is_role": True,
            "reason": "Safety representative role"
        },
        "Equipment operators": {
            "count": 1,
            "contexts": ["trained and certified"],
            "is_role": True,
            "reason": "Operational role"
        },
        "equipment manager": {
            "count": 1,
            "contexts": ["maintain training records"],
            "is_role": True,
            "reason": "Management position"
        },
        "department chair": {
            "count": 1,
            "contexts": ["oversight responsibility"],
            "is_role": True,
            "reason": "Academic leadership"
        },
        "safety committee": {
            "count": 1,
            "contexts": ["reviews and approves protocols"],
            "is_role": True,
            "reason": "Organizational body with defined responsibilities"
        }
    }

    true_roles = {k: v for k, v in manual_roles.items() if v["is_role"]}

    print(f"\nManual identification of roles:")
    print("-" * 70)
    for role, data in true_roles.items():
        print(f"  [{data['count']}x] {role}")

    print(f"\n\nMANUAL TOTAL: {len(true_roles)} unique roles")
    return true_roles


def run_tool_extraction(text: str, doc_name: str):
    """Run tool extraction on text."""
    print(f"\n{'=' * 70}")
    print(f"TOOL EXTRACTION: {doc_name}")
    print("=" * 70)

    from role_extractor_v3 import RoleExtractor
    extractor = RoleExtractor()

    roles = extractor.extract_from_text(text)

    print(f"\nTool extracted {len(roles)} roles:")
    print("-" * 70)
    for role_name, role_data in roles.items():
        print(f"  [{role_data.frequency}x] {role_name} (conf: {role_data.avg_confidence:.2f})")

    return roles


def compare_results(manual_roles: dict, tool_roles: dict, doc_name: str):
    """Compare manual vs tool extraction."""
    print(f"\n{'=' * 70}")
    print(f"COMPARISON: {doc_name}")
    print("=" * 70)

    manual_names = set(k.lower() for k in manual_roles.keys())
    tool_names = set(k.lower() for k in tool_roles.keys())

    # Find matches (exact and partial)
    exact_matches = manual_names & tool_names

    # Find partial matches
    partial_matches = []
    for m in manual_names - exact_matches:
        for t in tool_names - exact_matches:
            if m in t or t in m:
                partial_matches.append((m, t))

    # Unmatched
    manual_only = manual_names - exact_matches - set(p[0] for p in partial_matches)
    tool_only = tool_names - exact_matches - set(p[1] for p in partial_matches)

    print(f"\nExact matches ({len(exact_matches)}):")
    for m in sorted(exact_matches):
        print(f"  ✓ {m}")

    print(f"\nPartial matches ({len(partial_matches)}):")
    for m, t in partial_matches:
        print(f"  ~ Manual: '{m}' <-> Tool: '{t}'")

    print(f"\nManual only ({len(manual_only)}) - Tool missed:")
    for m in sorted(manual_only):
        print(f"  ✗ {m}")

    print(f"\nTool only ({len(tool_only)}) - Tool found extra:")
    for t in sorted(tool_only):
        print(f"  + {t}")

    # Calculate metrics
    total_manual = len(manual_roles)
    total_tool = len(tool_roles)
    matched = len(exact_matches) + len(partial_matches)

    precision = matched / total_tool if total_tool > 0 else 0
    recall = matched / total_manual if total_manual > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\n{'=' * 70}")
    print(f"METRICS:")
    print(f"  Manual roles: {total_manual}")
    print(f"  Tool roles: {total_tool}")
    print(f"  Matched: {matched} (exact: {len(exact_matches)}, partial: {len(partial_matches)})")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall: {recall:.1%}")
    print(f"  F1 Score: {f1:.1%}")

    return {
        "manual": total_manual,
        "tool": total_tool,
        "matched": matched,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


def main():
    print("\n" + "=" * 70)
    print("ROLE EXTRACTION - MANUAL VS TOOL COMPARISON")
    print("=" * 70)

    results = []

    # FAA Analysis
    faa_manual = analyze_faa_roles()
    faa_tool = run_tool_extraction(FAA_SAMPLE, "FAA AC 120-92B")
    faa_comparison = compare_results(faa_manual, faa_tool, "FAA AC 120-92B")
    results.append(("FAA AC 120-92B", faa_comparison))

    # OSHA Analysis
    osha_manual = analyze_osha_roles()
    osha_tool = run_tool_extraction(OSHA_SAMPLE, "OSHA Safety Management")
    osha_comparison = compare_results(osha_manual, osha_tool, "OSHA Safety Management")
    results.append(("OSHA Safety Management", osha_comparison))

    # Stanford Analysis
    stanford_manual = analyze_stanford_roles()
    stanford_tool = run_tool_extraction(STANFORD_SAMPLE, "Stanford Robotics SOP")
    stanford_comparison = compare_results(stanford_manual, stanford_tool, "Stanford Robotics SOP")
    results.append(("Stanford Robotics SOP", stanford_comparison))

    # Summary
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)

    print(f"\n{'Document':<30} {'Manual':>8} {'Tool':>8} {'Match':>8} {'Prec':>8} {'Recall':>8} {'F1':>8}")
    print("-" * 80)

    for doc_name, metrics in results:
        print(f"{doc_name:<30} {metrics['manual']:>8} {metrics['tool']:>8} "
              f"{metrics['matched']:>8} {metrics['precision']:>7.0%} "
              f"{metrics['recall']:>7.0%} {metrics['f1']:>7.0%}")

    # Average metrics
    avg_precision = sum(r[1]['precision'] for r in results) / len(results)
    avg_recall = sum(r[1]['recall'] for r in results) / len(results)
    avg_f1 = sum(r[1]['f1'] for r in results) / len(results)

    print("-" * 80)
    print(f"{'AVERAGE':<30} {'-':>8} {'-':>8} {'-':>8} {avg_precision:>7.0%} {avg_recall:>7.0%} {avg_f1:>7.0%}")


if __name__ == '__main__':
    main()
