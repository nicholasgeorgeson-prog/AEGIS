#!/usr/bin/env python3
"""
AEGIS Proposal Structure Tool — Desktop Edition
=================================================
Double-click this script from ANYWHERE. It will:
  1. Find your AEGIS install automatically
  2. Open a file picker — select one or more proposal files
  3. Analyze them (privacy-safe — no $ amounts, names, or text)
  4. Upload the JSON result directly to GitHub

The JSON appears at:
  https://github.com/nicholasgeorgeson-prog/AEGIS/tree/main/structure_reports/

No server needed. No browser. Just run it.

First run: creates aegis_github_token.txt — paste your GitHub token once.
After that, just double-click and pick files.
"""

import os
import sys
import json
import re
import logging
import base64
import urllib.request
import urllib.error
import ssl
from datetime import datetime
from typing import List, Dict, Optional, Any

VERSION = "2.0.0"

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger('proposal_structure_tool')

# GitHub config
GITHUB_REPO = "nicholasgeorgeson-prog/AEGIS"
GITHUB_BRANCH = "main"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_REPORT_DIR = "structure_reports"
TOKEN_FILENAME = "aegis_github_token.txt"

_github_token = None  # loaded at runtime


# ═══════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════

def print_banner():
    print()
    print("=" * 62)
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║  AEGIS Proposal Structure Tool                  ║")
    print("  ║  Desktop Edition  v{}                       ║".format(VERSION))
    print("  ║  Analyze → Upload to GitHub automatically       ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print("=" * 62)
    print()


# ═══════════════════════════════════════════════
# GITHUB TOKEN
# ═══════════════════════════════════════════════

def find_token():
    """Find the GitHub PAT from aegis_github_token.txt.

    Searches:
      1. Next to this script
      2. In the AEGIS install directory
      3. User's home directory
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")

    search_paths = [
        os.path.join(script_dir, TOKEN_FILENAME),
        os.path.join(home, "Desktop", TOKEN_FILENAME),
        os.path.join(home, TOKEN_FILENAME),
        os.path.join(home, "Desktop", "Doc Review", "AEGIS", TOKEN_FILENAME),
        os.path.join(home, "OneDrive - NGC", "Desktop", "Doc Review", "AEGIS", TOKEN_FILENAME),
        os.path.join(home, "Desktop", "Work_Tools", "TechWriterReview", TOKEN_FILENAME),
    ]

    for path in search_paths:
        if os.path.isfile(path):
            try:
                with open(path, 'r') as f:
                    token = f.read().strip()
                if token and token.startswith('ghp_'):
                    return token
            except Exception:
                pass

    return None


def setup_token():
    """Create the token file on first run."""
    print("  ┌─────────────────────────────────────────────┐")
    print("  │  First-time setup: GitHub token needed       │")
    print("  └─────────────────────────────────────────────┘")
    print()
    print("  This lets the tool upload results to GitHub.")
    print("  You only need to do this once.")
    print()
    print("  Paste your GitHub Personal Access Token below.")
    print("  (It starts with ghp_ ...)")
    print()

    token = input("  Token: ").strip()

    if not token:
        print("  No token entered. Results will be saved locally only.")
        return None

    if not token.startswith('ghp_'):
        print("  WARNING: Token doesn't start with 'ghp_' — may not work.")

    # Save next to the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(script_dir, TOKEN_FILENAME)

    try:
        with open(token_path, 'w') as f:
            f.write(token)
        print(f"  ✓ Token saved to: {token_path}")
        print("    (You won't be asked again)")
        print()
        return token
    except Exception as e:
        print(f"  Could not save token file: {e}")
        print("  Token will be used this session only.")
        return token


def load_token():
    """Load or create the GitHub token."""
    global _github_token

    token = find_token()
    if token:
        _github_token = token
        return True

    # First run — ask for token
    token = setup_token()
    if token:
        _github_token = token
        return True

    return False


# ═══════════════════════════════════════════════
# FIND AEGIS INSTALL
# ═══════════════════════════════════════════════

def find_aegis_install():
    """Search common locations for the AEGIS install directory."""
    candidates = []

    home = os.path.expanduser("~")

    # Windows paths
    candidates += [
        os.path.join(home, "Desktop", "Doc Review", "AEGIS"),
        os.path.join(home, "Desktop", "AEGIS"),
        os.path.join(home, "Documents", "AEGIS"),
        os.path.join(home, "OneDrive - NGC", "Desktop", "Doc Review", "AEGIS"),
        os.path.join(home, "OneDrive", "Desktop", "Doc Review", "AEGIS"),
        os.path.join(home, "OneDrive - NGC", "Desktop", "AEGIS"),
        "C:\\AEGIS",
        "C:\\AEGIS\\app",
    ]

    # Mac paths
    candidates += [
        os.path.join(home, "Desktop", "Work_Tools", "TechWriterReview"),
        os.path.join(home, "Desktop", "TechWriterReview"),
    ]

    # Script's own directory and parent
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.insert(0, script_dir)
    candidates.insert(1, os.path.dirname(script_dir))

    for path in candidates:
        if os.path.isdir(path):
            parser_path = os.path.join(path, "proposal_compare", "parser.py")
            if os.path.isfile(parser_path):
                return path

    return None


def load_aegis_modules(aegis_dir):
    """Import parser and structure analyzer from the AEGIS install."""
    if aegis_dir not in sys.path:
        sys.path.insert(0, aegis_dir)

    try:
        from proposal_compare.parser import (
            parse_proposal, CATEGORY_PATTERNS, SUPPORTED_EXTENSIONS,
        )
        from proposal_compare.structure_analyzer import (
            analyze_proposal_structure,
            analyze_batch_structure,
        )
        return {
            'available': True,
            'analyze_proposal_structure': analyze_proposal_structure,
            'analyze_batch_structure': analyze_batch_structure,
            'SUPPORTED_EXTENSIONS': SUPPORTED_EXTENSIONS,
        }
    except ImportError as e:
        return {'available': False, 'error': str(e)}


# ═══════════════════════════════════════════════
# FILE PICKER
# ═══════════════════════════════════════════════

def open_file_picker():
    """Open a native file picker. Returns list of file paths."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

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
        return list(files) if files else []

    except Exception as e:
        print(f"  File picker error: {e}")
        print("  Enter file paths manually (blank line to finish):")
        files = []
        while True:
            path = input("  Path: ").strip().strip('"').strip("'")
            if not path:
                break
            if os.path.isfile(path):
                files.append(path)
                print(f"    ✓ {os.path.basename(path)}")
            else:
                print(f"    ✗ Not found")
        return files


# ═══════════════════════════════════════════════
# GITHUB UPLOAD
# ═══════════════════════════════════════════════

def _github_request(endpoint, method="GET", data=None):
    """Make a GitHub API request using the loaded token."""
    url = f"{GITHUB_API}/{endpoint}" if not endpoint.startswith("http") else endpoint

    headers = {
        "Authorization": f"token {_github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AEGIS-StructureTool",
    }

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    ctx = ssl.create_default_context()
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    except ssl.SSLError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)

    return json.loads(resp.read().decode("utf-8"))


def upload_to_github(json_content, filename):
    """Upload a JSON file to the structure_reports/ folder on GitHub."""
    path = f"{GITHUB_REPORT_DIR}/{filename}"

    # Check if file already exists
    existing_sha = None
    try:
        existing = _github_request(f"contents/{path}?ref={GITHUB_BRANCH}")
        existing_sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    content_b64 = base64.b64encode(json_content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Structure analysis: {filename}",
        "content": content_b64,
        "branch": GITHUB_BRANCH,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    result = _github_request(f"contents/{path}", method="PUT", data=payload)

    return result.get("content", {}).get(
        "html_url",
        f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"
    )


# ═══════════════════════════════════════════════
# ANALYSIS
# ═══════════════════════════════════════════════

def run_analysis(files, modules):
    """Run structure analysis on selected files."""
    analyze_single = modules['analyze_proposal_structure']
    analyze_batch = modules['analyze_batch_structure']
    count = len(files)

    print(f"  Analyzing {count} file{'s' if count != 1 else ''}...")
    print()

    if count == 1:
        filepath = files[0]
        filename = os.path.basename(filepath)
        print(f"    Processing: {filename}...", end=" ", flush=True)

        try:
            result = analyze_single(filepath)
            result['file_info']['original_filename'] = filename
            result['_meta']['tool'] = 'AEGIS Structure Tool (Desktop)'
            result['_meta']['standalone_version'] = VERSION
            base = os.path.splitext(filename)[0]
            safe_base = re.sub(r'[^\w\-.]', '_', base)
            output_name = f"{safe_base}_structure.json"
            print("done")
            return result, output_name
        except Exception as e:
            print(f"ERROR: {e}")
            return None, None
    else:
        file_tuples = [(f, os.path.basename(f)) for f in files]

        for i, (fp, fn) in enumerate(file_tuples, 1):
            print(f"    [{i}/{count}] {fn}")

        print()
        print("  Running batch analysis...", end=" ", flush=True)

        try:
            result = analyze_batch(file_tuples)
            result['_meta']['tool'] = 'AEGIS Batch Structure Tool (Desktop)'
            result['_meta']['standalone_version'] = VERSION

            succeeded = result['_meta']['files_succeeded']
            failed = result['_meta']['files_failed']

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_name = f"batch_{count}files_{timestamp}.json"

            print(f"done — {succeeded} succeeded, {failed} failed")
            return result, output_name
        except Exception as e:
            print(f"ERROR: {e}")
            return None, None


def print_summary(result, github_url, local_path):
    """Print results summary."""
    print()
    print("=" * 62)
    print("  RESULTS")
    print("-" * 62)

    meta = result.get('_meta', {})
    file_count = meta.get('file_count', 1)

    if file_count and file_count > 1:
        cross = result.get('cross_file_summary', {})
        print(f"  Files:            {meta.get('files_succeeded', 0)} OK, {meta.get('files_failed', 0)} failed")
        print(f"  Tables found:     {cross.get('total_tables_found', 0)} ({cross.get('total_financial_tables', 0)} financial)")
        print(f"  Line items:       {cross.get('total_line_items', 0)}")
        print(f"  Avg completeness: {cross.get('avg_extraction_completeness', 0)}%")
    else:
        assessment = result.get('overall_assessment', {})
        completeness = assessment.get('extraction_completeness', {})
        print(f"  Tables found:     {assessment.get('total_tables_found', 0)} ({assessment.get('financial_tables', 0)} financial)")
        print(f"  Line items:       {assessment.get('total_line_items', 0)}")
        print(f"  Completeness:     {completeness.get('overall', 0)}%")

        suggestions = assessment.get('parser_suggestions', [])
        if suggestions:
            print()
            print("  Parser notes:")
            for s in suggestions[:5]:
                print(f"    - {s}")

    print()
    print("-" * 62)
    print(f"  Saved locally:  {local_path}")
    if github_url and not github_url.startswith("("):
        print(f"  On GitHub:      {github_url}")
    else:
        print(f"  GitHub:         {github_url}")
    print()
    print("  Done! This JSON is privacy-safe — no dollar amounts,")
    print("  company names, or descriptions are included.")
    print("=" * 62)
    print()


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

def main():
    print_banner()

    # Step 1: Find AEGIS
    print("  Looking for AEGIS install...", end=" ", flush=True)
    aegis_dir = find_aegis_install()

    if not aegis_dir:
        print("NOT FOUND")
        print()
        print("  Could not find AEGIS automatically.")
        print("  Enter the path to your AEGIS folder:")
        aegis_dir = input("  AEGIS path: ").strip().strip('"').strip("'")
        if not aegis_dir or not os.path.isdir(aegis_dir):
            print("  Invalid path. Exiting.")
            input("\n  Press Enter to close...")
            sys.exit(1)
        parser_check = os.path.join(aegis_dir, "proposal_compare", "parser.py")
        if not os.path.isfile(parser_check):
            print(f"  proposal_compare/parser.py not found in {aegis_dir}")
            input("\n  Press Enter to close...")
            sys.exit(1)

    print(f"found!")
    print(f"    {aegis_dir}")
    print()

    # Step 2: Load modules
    print("  Loading parser...", end=" ", flush=True)
    modules = load_aegis_modules(aegis_dir)
    if not modules['available']:
        print("FAILED")
        print(f"  Error: {modules.get('error', 'unknown')}")
        print()
        print("  You may need: pip install openpyxl python-docx pdfplumber")
        input("\n  Press Enter to close...")
        sys.exit(1)
    print("OK")
    print()

    # Step 3: Load GitHub token
    has_token = load_token()
    if has_token:
        print("  GitHub upload: enabled")
    else:
        print("  GitHub upload: disabled (no token)")
        print("  Results will be saved locally only.")
    print()

    # Step 4: Pick files
    print("  Opening file picker — select your proposal files...")
    print()
    files = open_file_picker()

    if not files:
        print("  No files selected.")
        input("\n  Press Enter to close...")
        sys.exit(0)

    # Filter to supported types
    supported = modules.get('SUPPORTED_EXTENSIONS', {'.xlsx', '.xls', '.docx', '.pdf'})
    valid_files = []
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in supported:
            valid_files.append(f)
        else:
            print(f"  Skipping: {os.path.basename(f)} (unsupported type)")

    if not valid_files:
        print("  No supported files selected.")
        input("\n  Press Enter to close...")
        sys.exit(0)

    print(f"  Selected {len(valid_files)} file(s):")
    for f in valid_files:
        print(f"    - {os.path.basename(f)}")
    print()

    # Step 5: Analyze
    result, output_name = run_analysis(valid_files, modules)

    if result is None:
        print("  Analysis failed.")
        input("\n  Press Enter to close...")
        sys.exit(1)

    # Step 6: Save local copy (next to the script)
    json_str = json.dumps(result, indent=2, ensure_ascii=False)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(script_dir, output_name)
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(json_str)

    # Step 7: Upload to GitHub (if token available)
    github_url = "(no token — saved locally only)"
    if _github_token:
        print()
        print("  Uploading to GitHub...", end=" ", flush=True)
        try:
            github_url = upload_to_github(json_str, output_name)
            print("done!")
        except Exception as e:
            print(f"failed: {e}")
            github_url = f"(upload failed: {e})"

    # Step 8: Summary
    print_summary(result, github_url, local_path)

    input("  Press Enter to close...")


if __name__ == '__main__':
    main()
