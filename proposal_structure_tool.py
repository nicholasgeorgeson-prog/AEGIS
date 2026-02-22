#!/usr/bin/env python3
"""
AEGIS Proposal Structure Analyzer — Standalone Tool
=====================================================
One-time-use diagnostic tool. Analyzes proposal files and produces
a privacy-safe JSON report for sharing with developers.

NO server required. NO browser needed. Just run it.

Usage:
  python proposal_structure_tool.py                    # Opens file picker
  python proposal_structure_tool.py file1.xlsx         # Analyze one file
  python proposal_structure_tool.py *.xlsx *.pdf       # Analyze multiple files
  python proposal_structure_tool.py --dir ./proposals  # Analyze a folder

Output:
  - Single file:   <filename>_structure_analysis.json
  - Multiple files: batch_structure_analysis.json

The JSON is privacy-safe: no dollar amounts, no company names,
no descriptions — only structural patterns and parser diagnostics.
Safe to upload to GitHub.

Requirements (same as AEGIS):
  - openpyxl (for .xlsx)
  - python-docx (for .docx)
  - pdfplumber or PyMuPDF (for .pdf) — optional, skips PDFs if missing
"""

import os
import sys
import json
import glob
import logging
import argparse
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────

VERSION = "1.0.0"
SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.docx', '.pdf'}

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger('proposal_structure_tool')


def print_banner():
    """Print startup banner."""
    print()
    print("=" * 62)
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║  AEGIS Proposal Structure Analyzer              ║")
    print("  ║  Standalone Diagnostic Tool  v{}            ║".format(VERSION))
    print("  ║  Privacy-safe — no $ amounts, names, or text    ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print("=" * 62)
    print()


def check_dependencies():
    """Check which file format libraries are available."""
    deps = {}

    try:
        import openpyxl
        deps['xlsx'] = True
    except ImportError:
        deps['xlsx'] = False

    try:
        from docx import Document
        deps['docx'] = True
    except ImportError:
        deps['docx'] = False

    try:
        import pdfplumber
        deps['pdf_pdfplumber'] = True
    except ImportError:
        deps['pdf_pdfplumber'] = False

    try:
        import fitz
        deps['pdf_pymupdf'] = True
    except ImportError:
        deps['pdf_pymupdf'] = False

    deps['pdf'] = deps['pdf_pdfplumber'] or deps['pdf_pymupdf']

    return deps


def print_dependency_status(deps):
    """Show which formats are supported."""
    print("  Supported formats:")
    print("    ✓ XLSX/XLS" if deps['xlsx'] else "    ✗ XLSX/XLS  (install openpyxl)")
    print("    ✓ DOCX" if deps['docx'] else "    ✗ DOCX      (install python-docx)")
    if deps['pdf']:
        via = "pdfplumber" if deps['pdf_pdfplumber'] else "PyMuPDF"
        print(f"    ✓ PDF       (via {via})")
    else:
        print("    ✗ PDF       (install pdfplumber or PyMuPDF)")
    print()


def find_aegis_modules():
    """Try to find and import the AEGIS proposal_compare modules."""
    # Check if we're in the AEGIS directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Add script directory to path so we can import proposal_compare
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        from proposal_compare.parser import parse_proposal, CATEGORY_PATTERNS
        from proposal_compare.structure_analyzer import (
            analyze_proposal_structure,
            analyze_batch_structure,
        )
        return {
            'parse_proposal': parse_proposal,
            'analyze_proposal_structure': analyze_proposal_structure,
            'analyze_batch_structure': analyze_batch_structure,
            'CATEGORY_PATTERNS': CATEGORY_PATTERNS,
            'available': True,
        }
    except ImportError as e:
        return {'available': False, 'error': str(e)}


def open_file_picker():
    """Open a native file picker dialog. Falls back to manual input."""
    selected = []

    # Try tkinter file dialog
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.attributes('-topmost', True)  # Bring dialog to front

        filetypes = [
            ('Proposal files', '*.xlsx *.xls *.docx *.pdf'),
            ('Excel files', '*.xlsx *.xls'),
            ('Word files', '*.docx'),
            ('PDF files', '*.pdf'),
            ('All files', '*.*'),
        ]

        files = filedialog.askopenfilenames(
            title='Select Proposal Files to Analyze',
            filetypes=filetypes,
        )
        root.destroy()

        if files:
            selected = list(files)
            return selected
        else:
            print("  No files selected.")
            return []

    except Exception:
        pass  # tkinter not available, fall through to manual input

    # Fallback: manual path input
    print("  File picker not available. Enter file paths manually.")
    print("  (Enter each path on its own line, blank line when done)")
    print()
    while True:
        path = input("  File path: ").strip().strip('"').strip("'")
        if not path:
            break
        if os.path.isfile(path):
            selected.append(path)
            print(f"    ✓ Added: {os.path.basename(path)}")
        else:
            print(f"    ✗ Not found: {path}")

    return selected


def collect_files_from_dir(dirpath):
    """Recursively find all supported files in a directory."""
    found = []
    for root, dirs, files in os.walk(dirpath):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                found.append(os.path.join(root, f))
    return found


def filter_by_deps(files, deps):
    """Remove files we can't process due to missing dependencies."""
    filtered = []
    skipped = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in ('.xlsx', '.xls') and not deps['xlsx']:
            skipped.append((f, 'openpyxl not installed'))
        elif ext == '.docx' and not deps['docx']:
            skipped.append((f, 'python-docx not installed'))
        elif ext == '.pdf' and not deps['pdf']:
            skipped.append((f, 'pdfplumber/PyMuPDF not installed'))
        else:
            filtered.append(f)
    return filtered, skipped


def run_analysis(files, modules):
    """Run structure analysis on the file list."""
    analyze_single = modules['analyze_proposal_structure']
    analyze_batch = modules['analyze_batch_structure']

    file_count = len(files)
    print(f"  Analyzing {file_count} file{'s' if file_count != 1 else ''}...")
    print()

    if file_count == 1:
        # Single file — use single analysis
        filepath = files[0]
        filename = os.path.basename(filepath)
        print(f"    Processing: {filename}")

        try:
            result = analyze_single(filepath)
            result['file_info']['original_filename'] = filename
            result['_meta']['tool'] = 'AEGIS Proposal Structure Analyzer (Standalone)'
            result['_meta']['standalone_version'] = VERSION

            # Determine output filename
            base = os.path.splitext(filename)[0]
            output_name = f"{base}_structure_analysis.json"
            print(f"    ✓ Analysis complete")
            return result, output_name

        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None, None

    else:
        # Multiple files — use batch analysis
        file_tuples = [(f, os.path.basename(f)) for f in files]

        for i, (fp, fn) in enumerate(file_tuples, 1):
            print(f"    [{i}/{file_count}] {fn}...", end=" ", flush=True)
            try:
                # Quick test that the file is readable
                with open(fp, 'rb') as test:
                    test.read(4)
                print("queued")
            except Exception as e:
                print(f"ERROR: {e}")

        print()
        print("  Running batch analysis...")

        try:
            result = analyze_batch(file_tuples)
            result['_meta']['tool'] = 'AEGIS Batch Structure Analyzer (Standalone)'
            result['_meta']['standalone_version'] = VERSION

            output_name = "batch_structure_analysis.json"
            succeeded = result['_meta']['files_succeeded']
            failed = result['_meta']['files_failed']

            print(f"    ✓ Batch complete: {succeeded} succeeded, {failed} failed")
            return result, output_name

        except Exception as e:
            print(f"    ✗ Batch error: {e}")
            return None, None


def save_result(result, output_name, output_dir=None):
    """Save the JSON result to disk."""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_name)
    else:
        output_path = output_name

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    size = os.path.getsize(output_path)
    size_label = f"{size / 1024:.1f} KB" if size > 1024 else f"{size} bytes"

    return output_path, size_label


def print_summary(result, output_path, size_label):
    """Print a summary of the analysis results."""
    print()
    print("=" * 62)
    print("  RESULTS")
    print("-" * 62)
    print(f"  Output file: {output_path}")
    print(f"  File size:   {size_label}")
    print()

    meta = result.get('_meta', {})
    file_count = meta.get('file_count', 1)

    if file_count == 1:
        # Single file summary
        assessment = result.get('overall_assessment', {})
        completeness = assessment.get('extraction_completeness', {})
        tables = assessment.get('total_tables_found', 0)
        financial = assessment.get('financial_tables', 0)
        items = assessment.get('total_line_items', 0)
        score = completeness.get('overall', 0)
        suggestions = assessment.get('parser_suggestions', [])

        print(f"  Tables found:     {tables} ({financial} financial)")
        print(f"  Line items:       {items}")
        print(f"  Completeness:     {score}%")
        print(f"  Company detected: {'Yes' if assessment.get('has_company_name') else 'No'}")
        print(f"  Contract term:    {'Yes' if assessment.get('has_contract_term') else 'No'}")

        if suggestions:
            print()
            print("  Parser suggestions:")
            for s in suggestions[:5]:
                print(f"    • {s}")

    else:
        # Batch summary
        cross = result.get('cross_file_summary', {})
        succeeded = meta.get('files_succeeded', 0)
        failed = meta.get('files_failed', 0)

        print(f"  Files analyzed:   {succeeded} succeeded, {failed} failed")
        print(f"  Total tables:     {cross.get('total_tables_found', 0)} ({cross.get('total_financial_tables', 0)} financial)")
        print(f"  Total line items: {cross.get('total_line_items', 0)}")
        print(f"  Avg completeness: {cross.get('avg_extraction_completeness', 0)}%")

        by_type = cross.get('files_by_type', {})
        if by_type:
            print(f"  File types:       {', '.join(f'{v} {k}' for k, v in by_type.items())}")

        common_sug = cross.get('common_parser_suggestions', [])
        if common_sug:
            print()
            print("  Common parser suggestions:")
            for s in common_sug[:5]:
                print(f"    • {s}")

    print()
    print("-" * 62)
    print("  ✅ This JSON is privacy-safe — upload to GitHub for review.")
    print("     No dollar amounts, company names, or descriptions included.")
    print("=" * 62)
    print()


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    print_banner()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='AEGIS Proposal Structure Analyzer — Standalone diagnostic tool',
        epilog='If no files specified, opens a file picker dialog.',
    )
    parser.add_argument(
        'files', nargs='*',
        help='Proposal files to analyze (.xlsx, .xls, .docx, .pdf)',
    )
    parser.add_argument(
        '--dir', '-d',
        help='Directory to scan for proposal files',
    )
    parser.add_argument(
        '--output', '-o',
        help='Output directory for JSON results (default: current directory)',
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Show detailed logging',
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Step 1: Check dependencies
    deps = check_dependencies()
    print_dependency_status(deps)

    if not any([deps['xlsx'], deps['docx'], deps['pdf']]):
        print("  ERROR: No file format libraries installed.")
        print("  Install at least one: pip install openpyxl python-docx pdfplumber")
        sys.exit(1)

    # Step 2: Find AEGIS modules
    print("  Loading AEGIS parser modules...", end=" ", flush=True)
    modules = find_aegis_modules()
    if not modules['available']:
        print("FAILED")
        print()
        print("  ERROR: Could not import proposal_compare modules.")
        print(f"  Detail: {modules.get('error', 'unknown')}")
        print()
        print("  This script must be in the AEGIS install directory")
        print("  (same folder as app.py and the proposal_compare/ folder).")
        print()
        print("  Expected location:")
        print(f"    {os.path.dirname(os.path.abspath(__file__))}/")
        print("    ├── app.py")
        print("    ├── proposal_compare/")
        print("    │   ├── parser.py")
        print("    │   └── structure_analyzer.py")
        print("    └── proposal_structure_tool.py  ← this script")
        sys.exit(1)
    print("OK")
    print()

    # Step 3: Collect files
    files = []

    if args.dir:
        # Scan directory
        dirpath = os.path.abspath(args.dir)
        if not os.path.isdir(dirpath):
            print(f"  ERROR: Directory not found: {dirpath}")
            sys.exit(1)
        print(f"  Scanning directory: {dirpath}")
        files = collect_files_from_dir(dirpath)
        if not files:
            print("  No supported files found in directory.")
            sys.exit(0)
        print(f"  Found {len(files)} files")
        print()

    elif args.files:
        # Files from command line — expand globs on Windows
        for pattern in args.files:
            expanded = glob.glob(pattern)
            if expanded:
                files.extend(expanded)
            elif os.path.isfile(pattern):
                files.append(pattern)
            else:
                print(f"  WARNING: Not found: {pattern}")

    else:
        # No args — open file picker
        print("  No files specified — opening file picker...")
        print()
        files = open_file_picker()

    if not files:
        print("  No files to analyze. Exiting.")
        sys.exit(0)

    # Deduplicate and validate
    seen = set()
    unique_files = []
    for f in files:
        abspath = os.path.abspath(f)
        if abspath not in seen:
            seen.add(abspath)
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                unique_files.append(abspath)
            else:
                print(f"  Skipping unsupported: {os.path.basename(f)}")
    files = unique_files

    # Filter by available dependencies
    files, skipped = filter_by_deps(files, deps)
    for sf, reason in skipped:
        print(f"  Skipping {os.path.basename(sf)}: {reason}")

    if not files:
        print("  No processable files remain. Exiting.")
        sys.exit(0)

    print(f"  Files to analyze: {len(files)}")
    for f in files:
        print(f"    • {os.path.basename(f)}")
    print()

    # Step 4: Run analysis
    result, output_name = run_analysis(files, modules)

    if result is None:
        print("  Analysis failed. Check the error messages above.")
        sys.exit(1)

    # Step 5: Save output
    output_path, size_label = save_result(result, output_name, args.output)

    # Step 6: Print summary
    print_summary(result, output_path, size_label)


if __name__ == '__main__':
    main()
