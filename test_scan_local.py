#!/usr/bin/env python3
"""
AEGIS Local Scan Test Script v5.5.0
====================================
Tests single file scanning (5 different files) and batch folder scanning.

Usage:
    python3 test_scan_local.py                     # Run all tests
    python3 test_scan_local.py --single            # Run single file tests only
    python3 test_scan_local.py --batch             # Run batch folder test only
    python3 test_scan_local.py --folder /path/to/docs  # Scan custom folder

Requirements:
    - AEGIS server running on localhost:5050
    - Test documents in test_documents/ directory
"""

import argparse
import json
import os
import sys
import time
import requests
from pathlib import Path

# ── Configuration ──
BASE_URL = 'http://localhost:5050'
TEST_DOCS_DIR = Path(__file__).parent / 'test_documents'
BATCH_TEST_DIR = TEST_DOCS_DIR / 'batch_test'

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


def get_csrf_token(session):
    """Fetch a fresh CSRF token from the server."""
    resp = session.get(f'{BASE_URL}/api/version')
    csrf = resp.headers.get('X-CSRF-Token', '')
    if not csrf:
        # Try from meta tag
        resp2 = session.get(BASE_URL)
        import re
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', resp2.text)
        if match:
            csrf = match.group(1)
    return csrf


def print_header(title):
    print(f'\n{BOLD}{CYAN}{"=" * 70}')
    print(f'  {title}')
    print(f'{"=" * 70}{RESET}\n')


def print_result(label, value, color=GREEN):
    print(f'  {color}{label}{RESET}: {value}')


def print_separator():
    print(f'  {"-" * 50}')


def test_server_connection(session):
    """Verify the AEGIS server is reachable."""
    print_header('AEGIS Server Check')
    try:
        resp = session.get(f'{BASE_URL}/api/version', timeout=5)
        if resp.ok:
            data = resp.json()
            version = data.get('version', 'unknown')
            print_result('Server Status', f'Online (v{version})')
            return True
        else:
            print_result('Server Status', f'Error: HTTP {resp.status_code}', RED)
            return False
    except requests.ConnectionError:
        print_result('Server Status', 'OFFLINE - Start server first: python3 app.py --debug', RED)
        return False
    except Exception as e:
        print_result('Server Status', f'Error: {e}', RED)
        return False


def pick_test_files():
    """Select 5 files of different types and complexity levels."""
    candidates = []

    # 1. Small DOCX (simple SOP template)
    for name in ['Stanford_SOP_Template.docx', 'Brown_SOP_Template.docx', 'USC_SOP_Template.docx']:
        path = TEST_DOCS_DIR / name
        if not path.exists():
            path = BATCH_TEST_DIR / name
        if path.exists():
            candidates.append({'path': path, 'label': 'Small DOCX (SOP Template)', 'complexity': 'Low'})
            break

    # 2. Medium DOCX (engineering content)
    for name in ['Stanford_Engineering_Robotics_SOP.docx', 'Rowan_SOP_Guideline.docx', 'UConn_Lab_SOP_Template.docx']:
        path = TEST_DOCS_DIR / name
        if path.exists():
            candidates.append({'path': path, 'label': 'Medium DOCX (Engineering)', 'complexity': 'Medium'})
            break

    # 3. Small PDF (focused requirements)
    for name in ['DO-178C_VV_Plan_FlightControl.pdf', 'EPA_SOP_Guidance.pdf', 'PMBOK_Guide_Summary.pdf']:
        path = TEST_DOCS_DIR / name
        if path.exists():
            candidates.append({'path': path, 'label': 'Small PDF (Requirements)', 'complexity': 'Low'})
            break

    # 4. Medium PDF (standards document)
    for name in ['FAA_AC_120_92B.pdf', 'KSC_Specs_Standards.pdf', 'NIST_Cybersecurity_Framework.pdf']:
        path = TEST_DOCS_DIR / name
        if path.exists():
            candidates.append({'path': path, 'label': 'Medium PDF (Standards)', 'complexity': 'Medium'})
            break

    # 5. Large PDF (comprehensive handbook)
    for name in ['NASA_Systems_Engineering_Handbook.pdf', 'NIST_SP_800_53_Security_Controls.pdf', 'MIL-STD-40051-2A.pdf']:
        path = TEST_DOCS_DIR / name
        if not path.exists():
            path = BATCH_TEST_DIR / name
        if path.exists():
            candidates.append({'path': path, 'label': 'Large PDF (Handbook)', 'complexity': 'High'})
            break

    # Fallback: if we didn't get 5, add whatever's available
    if len(candidates) < 5:
        for f in sorted(TEST_DOCS_DIR.glob('*.*')):
            if f.suffix.lower() in ('.docx', '.pdf', '.doc') and f.stat().st_size > 0:
                already = {c['path'] for c in candidates}
                if f not in already and len(candidates) < 5:
                    candidates.append({
                        'path': f,
                        'label': f'Fallback ({f.suffix})',
                        'complexity': 'Unknown'
                    })

    return candidates


def run_single_file_tests(session, csrf_token):
    """Run 5 single file scans with different file types."""
    print_header('Single File Scan Tests (5 Files)')

    test_files = pick_test_files()
    if not test_files:
        print_result('Error', 'No test documents found!', RED)
        return False

    print(f'  Selected {len(test_files)} test files:\n')
    for i, tf in enumerate(test_files, 1):
        size_kb = tf['path'].stat().st_size / 1024
        print(f'  {i}. {tf["label"]}')
        print(f'     File: {tf["path"].name} ({size_kb:.0f} KB)')
        print(f'     Complexity: {tf["complexity"]}')
        print()

    results = []
    all_passed = True

    for i, tf in enumerate(test_files, 1):
        print_separator()
        print(f'\n  {BOLD}Test {i}/5: {tf["label"]}{RESET}')
        print(f'  File: {tf["path"].name}')

        start_time = time.time()
        try:
            # Step 1: Upload
            with open(tf['path'], 'rb') as f:
                upload_resp = session.post(
                    f'{BASE_URL}/api/upload',
                    files={'file': (tf['path'].name, f)},
                    headers={'X-CSRF-Token': csrf_token}
                )

            if not upload_resp.ok:
                print_result('Upload', f'FAILED (HTTP {upload_resp.status_code})', RED)
                all_passed = False
                results.append({'file': tf['path'].name, 'status': 'upload_failed'})
                continue

            upload_data = upload_resp.json()
            if not upload_data.get('success'):
                print_result('Upload', f'FAILED: {upload_data.get("error", {}).get("message", "Unknown")}', RED)
                all_passed = False
                results.append({'file': tf['path'].name, 'status': 'upload_failed'})
                continue

            doc_info = upload_data.get('data', {})
            print_result('Upload', f'OK — {doc_info.get("word_count", 0):,} words, {doc_info.get("paragraph_count", 0)} paragraphs')

            # Step 2: Review (async start)
            review_resp = session.post(
                f'{BASE_URL}/api/review/start',
                json={'options': {}},
                headers={'X-CSRF-Token': csrf_token, 'Content-Type': 'application/json'}
            )

            if not review_resp.ok:
                # Try sync review as fallback
                review_resp = session.post(
                    f'{BASE_URL}/api/review',
                    json={'options': {}},
                    headers={'X-CSRF-Token': csrf_token, 'Content-Type': 'application/json'}
                )
                if review_resp.ok:
                    review_data = review_resp.json().get('data', {})
                    elapsed = time.time() - start_time
                    issues = review_data.get('issues', [])
                    score = review_data.get('score', 0)
                    grade = review_data.get('grade', 'N/A')
                    print_result('Review', f'OK (sync) — {len(issues)} issues, Score: {score}, Grade: {grade}')
                    print_result('Time', f'{elapsed:.1f}s')
                    results.append({
                        'file': tf['path'].name,
                        'status': 'success',
                        'issues': len(issues),
                        'score': score,
                        'grade': grade,
                        'time': round(elapsed, 1)
                    })
                    continue

            review_json = review_resp.json()
            job_id = review_json.get('job_id')

            if not job_id:
                print_result('Review', 'FAILED: No job_id returned', RED)
                all_passed = False
                continue

            print_result('Review', f'Started (job: {job_id[:8]}...)')

            # Step 3: Poll for completion
            poll_url = f'{BASE_URL}/api/job/{job_id}'
            max_wait = 300  # 5 minutes
            poll_start = time.time()

            while time.time() - poll_start < max_wait:
                time.sleep(2)
                poll_resp = session.get(poll_url)
                if poll_resp.ok:
                    job_data = poll_resp.json().get('data', poll_resp.json())
                    status = job_data.get('status', '')
                    phase = job_data.get('current_phase', '')
                    message = job_data.get('phase_message', '')

                    if status == 'complete':
                        # Get results
                        result_resp = session.get(f'{BASE_URL}/api/review/result/{job_id}')
                        if result_resp.ok:
                            review_data = result_resp.json().get('data', {})
                            elapsed = time.time() - start_time
                            issues = review_data.get('issues', [])
                            score = review_data.get('score', 0)
                            grade = review_data.get('grade', 'N/A')
                            print_result('Review', f'COMPLETE — {len(issues)} issues, Score: {score}, Grade: {grade}')
                            print_result('Time', f'{elapsed:.1f}s')

                            # Issue breakdown
                            sev_counts = {}
                            for iss in issues:
                                s = iss.get('severity', 'Unknown')
                                sev_counts[s] = sev_counts.get(s, 0) + 1
                            if sev_counts:
                                breakdown = ', '.join(f'{k}: {v}' for k, v in sorted(sev_counts.items()))
                                print_result('Issues', breakdown)

                            results.append({
                                'file': tf['path'].name,
                                'status': 'success',
                                'issues': len(issues),
                                'score': score,
                                'grade': grade,
                                'time': round(elapsed, 1)
                            })
                        break

                    elif status == 'failed':
                        error = job_data.get('error', 'Unknown error')
                        print_result('Review', f'FAILED: {error}', RED)
                        all_passed = False
                        results.append({'file': tf['path'].name, 'status': 'failed', 'error': error})
                        break

                    else:
                        # Still processing
                        if message:
                            sys.stdout.write(f'\r  Processing: {message[:60]}...')
                            sys.stdout.flush()
                else:
                    time.sleep(3)

            else:
                print_result('Review', 'TIMEOUT after 5 minutes', RED)
                all_passed = False
                results.append({'file': tf['path'].name, 'status': 'timeout'})

        except Exception as e:
            print_result('Error', str(e), RED)
            all_passed = False
            results.append({'file': tf['path'].name, 'status': 'error', 'error': str(e)})

    # Summary
    print_header('Single File Test Summary')
    for r in results:
        status_icon = '✓' if r['status'] == 'success' else '✗'
        status_color = GREEN if r['status'] == 'success' else RED
        detail = ''
        if r['status'] == 'success':
            detail = f"  Score: {r.get('score', 'N/A')}, Grade: {r.get('grade', 'N/A')}, Issues: {r.get('issues', 0)}, Time: {r.get('time', '?')}s"
        else:
            detail = f"  {r.get('error', r['status'])}"
        print(f'  {status_color}{status_icon}{RESET} {r["file"]}{detail}')

    print()
    passed = sum(1 for r in results if r['status'] == 'success')
    print(f'  {BOLD}Result: {passed}/{len(results)} tests passed{RESET}')

    return all_passed


def run_batch_folder_test(session, csrf_token, folder_path=None):
    """Test batch folder scanning on a document repository."""
    print_header('Batch Folder Scan Test')

    # Determine folder to scan
    if folder_path:
        scan_dir = Path(folder_path)
    else:
        # Default: use test_documents directory (includes subdirectories)
        scan_dir = TEST_DOCS_DIR

    if not scan_dir.exists():
        print_result('Error', f'Folder not found: {scan_dir}', RED)
        return False

    print_result('Target Folder', str(scan_dir))
    print()

    # Step 1: Discovery (dry run)
    print(f'  {BOLD}Phase 1: Discovery{RESET}')
    start = time.time()
    discover_resp = session.post(
        f'{BASE_URL}/api/review/folder-discover',
        json={'folder_path': str(scan_dir)},
        headers={'X-CSRF-Token': csrf_token, 'Content-Type': 'application/json'}
    )

    if not discover_resp.ok:
        print_result('Discovery', f'FAILED (HTTP {discover_resp.status_code})', RED)
        try:
            err = discover_resp.json()
            print_result('Error', err.get('error', {}).get('message', 'Unknown'), RED)
        except Exception:
            pass
        return False

    disc_data = discover_resp.json().get('data', {})
    disc_time = time.time() - start
    print_result('Files Found', f'{disc_data.get("total_files", 0)} documents')
    print_result('Total Size', disc_data.get('total_size_human', '0 B'))
    print_result('Discovery Time', f'{disc_time:.1f}s')

    types = disc_data.get('type_breakdown', {})
    if types:
        type_str = ', '.join(f'{ext}: {count}' for ext, count in sorted(types.items()))
        print_result('Types', type_str)

    # Show file list
    files = disc_data.get('files', [])
    if files:
        print(f'\n  Files to scan:')
        for f in files[:20]:
            size_str = f.get('size_human', '')
            print(f'    {f["relative_path"]} ({size_str})')
        if len(files) > 20:
            print(f'    ... and {len(files) - 20} more')

    if not files:
        print_result('Result', 'No documents found in folder', YELLOW)
        return True

    # Step 2: Full scan
    print(f'\n  {BOLD}Phase 2: Full Scan{RESET}')
    print(f'  Scanning {len(files)} documents (this may take a while)...\n')

    start = time.time()
    scan_resp = session.post(
        f'{BASE_URL}/api/review/folder-scan',
        json={'folder_path': str(scan_dir)},
        headers={'X-CSRF-Token': csrf_token, 'Content-Type': 'application/json'},
        timeout=1800  # 30 minute timeout for large repos
    )

    scan_time = time.time() - start

    if not scan_resp.ok:
        print_result('Scan', f'FAILED (HTTP {scan_resp.status_code})', RED)
        try:
            err = scan_resp.json()
            print_result('Error', err.get('error', {}).get('message', 'Unknown'), RED)
        except Exception:
            pass
        return False

    scan_data = scan_resp.json().get('data', {})
    review = scan_data.get('review', {})
    summary = review.get('summary', {})

    print_result('Processing Time', f'{review.get("processing_time_seconds", 0):.1f}s (network: {scan_time:.1f}s)')
    print_result('Documents Processed', f'{summary.get("processed", 0)}')
    print_result('Errors', f'{summary.get("errors", 0)}', RED if summary.get('errors', 0) > 0 else GREEN)
    print_result('Total Issues', f'{summary.get("total_issues", 0):,}')
    print_result('Total Words', f'{summary.get("total_words", 0):,}')

    # Severity breakdown
    sev = summary.get('issues_by_severity', {})
    if sev:
        sev_str = ', '.join(f'{k}: {v}' for k, v in sorted(sev.items()) if v > 0)
        print_result('By Severity', sev_str)

    # Grade distribution
    grades = summary.get('grade_distribution', {})
    if grades:
        grade_str = ', '.join(f'{k}: {v}' for k, v in sorted(grades.items()))
        print_result('Grades', grade_str)

    # Top categories
    cats = summary.get('issues_by_category', {})
    if cats:
        top_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, count in top_cats:
            print(f'    {cat}: {count}')

    # Per-document results
    docs = review.get('documents', [])
    if docs:
        print(f'\n  {BOLD}Per-Document Results:{RESET}')
        for doc in docs:
            status = doc.get('status', 'unknown')
            if status == 'success':
                icon = f'{GREEN}✓{RESET}'
                detail = f'Score: {doc.get("score", "N/A")}, Grade: {doc.get("grade", "N/A")}, Issues: {doc.get("issue_count", 0)}, Words: {(doc.get("word_count", 0)):,}'
            else:
                icon = f'{RED}✗{RESET}'
                detail = doc.get('error', 'Unknown error')
            print(f'    {icon} {doc.get("relative_path", doc.get("filename", "?"))}')
            print(f'      {detail}')

    # Roles found
    roles = review.get('roles_found', {})
    if roles:
        print(f'\n  {BOLD}Roles Discovered: {len(roles)}{RESET}')
        top_roles = sorted(roles.items(), key=lambda x: x[1].get('total_mentions', 0), reverse=True)[:10]
        for role_name, role_data in top_roles:
            docs_count = len(role_data.get('documents', []))
            mentions = role_data.get('total_mentions', 0)
            print(f'    {role_name}: {mentions} mentions across {docs_count} docs')

    print_separator()
    success = summary.get('processed', 0) > 0
    print(f'\n  {BOLD}{"PASS" if success else "FAIL"}: Batch folder scan {"completed" if success else "failed"}{RESET}')

    return success


def main():
    parser = argparse.ArgumentParser(description='AEGIS Local Scan Test Script')
    parser.add_argument('--single', action='store_true', help='Run single file tests only')
    parser.add_argument('--batch', action='store_true', help='Run batch folder test only')
    parser.add_argument('--folder', type=str, help='Custom folder path for batch test')
    args = parser.parse_args()

    # Default: run both
    run_single = args.single or (not args.single and not args.batch)
    run_batch = args.batch or (not args.single and not args.batch)

    print(f'\n{BOLD}{CYAN}╔══════════════════════════════════════════════════╗')
    print(f'║     AEGIS Scan Test Script v5.5.0                ║')
    print(f'║     Testing single file + batch folder scanning  ║')
    print(f'╚══════════════════════════════════════════════════╝{RESET}\n')

    session = requests.Session()

    # Check server
    if not test_server_connection(session):
        print(f'\n{RED}Cannot continue — AEGIS server is not running.{RESET}')
        print(f'Start the server first: {BOLD}python3 app.py --debug{RESET}')
        sys.exit(1)

    # Get CSRF token
    csrf_token = get_csrf_token(session)
    if not csrf_token:
        print(f'\n{YELLOW}Warning: Could not get CSRF token. Some requests may fail.{RESET}')

    results = {}

    if run_single:
        results['single'] = run_single_file_tests(session, csrf_token)

    if run_batch:
        results['batch'] = run_batch_folder_test(session, csrf_token, args.folder)

    # Final summary
    print_header('Final Summary')
    all_passed = True
    for test_name, passed in results.items():
        icon = f'{GREEN}PASS{RESET}' if passed else f'{RED}FAIL{RESET}'
        print(f'  {test_name}: {icon}')
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print(f'  {BOLD}{GREEN}All tests passed!{RESET}')
    else:
        print(f'  {BOLD}{RED}Some tests failed — check output above.{RESET}')

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
