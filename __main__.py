#!/usr/bin/env python3
"""
AEGIS CLI
====================
Command-line interface for AEGIS document analysis.

Usage:
    python -m AEGIS document.docx
    python -m AEGIS document.pdf --preset microsoft
    python -m AEGIS *.docx --batch --output results.json
    twr document.docx --preset google --format xlsx

Examples:
    # Basic analysis
    python -m AEGIS report.docx

    # Use Microsoft style preset
    python -m AEGIS report.docx --preset microsoft

    # JSON output for CI/CD integration
    python -m AEGIS report.docx --format json --output results.json

    # Batch processing
    python -m AEGIS docs/*.docx --batch --format xlsx

    # List available presets
    python -m AEGIS --list-presets
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import glob

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config_logging import VERSION, get_logger
    _logger = get_logger('twr_cli')
except ImportError:
    VERSION = "3.4.0"
    import logging
    _logger = logging.getLogger('twr_cli')
    logging.basicConfig(level=logging.INFO)


def print_banner():
    """Print CLI banner."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  AEGIS v{VERSION:10}                              ║
║  Enterprise Document Analysis Tool                           ║
║  84 Quality Checkers | Offline-Capable | Air-Gap Ready       ║
╚══════════════════════════════════════════════════════════════╝
""")


def list_presets():
    """List available style presets."""
    try:
        from style_presets import list_presets as get_presets
        presets = get_presets()

        print("\nAvailable Style Presets:")
        print("=" * 60)
        for preset in presets:
            print(f"\n  {preset['display_name']} (--preset {preset['name']})")
            print(f"    {preset['description']}")
            print(f"    Target: {preset['target_audience']}")
            print(f"    Checkers: {preset['checker_count']} enabled")
        print()
    except ImportError:
        print("Error: style_presets module not found")
        sys.exit(1)


def analyze_document(
    filepath: str,
    preset: Optional[str] = None,
    options: Optional[Dict] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Analyze a single document.

    Args:
        filepath: Path to document (DOCX or PDF)
        preset: Style preset name
        options: Custom checker options
        verbose: Print verbose output

    Returns:
        Analysis results dictionary
    """
    from core import AEGISEngine

    # Build options
    review_options = {}

    # Apply preset if specified
    if preset:
        try:
            from style_presets import apply_preset
            review_options = apply_preset(preset)
            if verbose:
                print(f"  Applied preset: {preset}")
        except ImportError:
            print(f"Warning: Could not load preset '{preset}'")

    # Override with custom options
    if options:
        review_options.update(options)

    # Create reviewer
    reviewer = AEGISEngine()

    if verbose:
        print(f"  Loaded {len(reviewer.checkers)} checkers")

    # Run analysis
    try:
        results = reviewer.review_document(filepath, review_options)
        return results
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'filepath': filepath
        }


def format_issue(issue: Dict, index: int) -> str:
    """Format a single issue for display."""
    severity = issue.get('severity', 'info').upper()
    category = issue.get('category', 'General')
    message = issue.get('message', 'No message')
    context = issue.get('context', '')[:60]

    severity_colors = {
        'ERROR': '\033[91m',    # Red
        'WARNING': '\033[93m',  # Yellow
        'INFO': '\033[94m',     # Blue
    }
    reset = '\033[0m'
    color = severity_colors.get(severity, '')

    line = f"{index:3}. [{color}{severity:7}{reset}] {category}: {message}"
    if context:
        line += f"\n      Context: \"{context}...\""
    return line


def print_summary(results: Dict, filepath: str):
    """Print analysis summary to console."""
    if not results.get('success', False):
        print(f"\n  ERROR: {results.get('error', 'Unknown error')}")
        return

    issues = results.get('issues', [])
    metrics = results.get('readability', {})

    # Count by severity
    errors = sum(1 for i in issues if i.get('severity') == 'error')
    warnings = sum(1 for i in issues if i.get('severity') == 'warning')
    info = sum(1 for i in issues if i.get('severity') == 'info')

    print(f"\n  File: {filepath}")
    print(f"  Issues Found: {len(issues)} total")
    print(f"    \033[91mErrors:   {errors}\033[0m")
    print(f"    \033[93mWarnings: {warnings}\033[0m")
    print(f"    \033[94mInfo:     {info}\033[0m")

    if metrics:
        print(f"\n  Readability:")
        print(f"    Word Count: {metrics.get('word_count', 'N/A')}")
        print(f"    Flesch Reading Ease: {metrics.get('flesch_reading_ease', 'N/A'):.1f}")
        print(f"    Flesch-Kincaid Grade: {metrics.get('flesch_kincaid_grade', 'N/A'):.1f}")


def print_issues(results: Dict, limit: int = 50):
    """Print issues to console."""
    issues = results.get('issues', [])

    if not issues:
        print("\n  No issues found!")
        return

    # Group by category
    categories = {}
    for issue in issues:
        cat = issue.get('category', 'Other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(issue)

    print(f"\n  Issues by Category:")
    print("  " + "=" * 58)

    displayed = 0
    for category, cat_issues in sorted(categories.items()):
        if displayed >= limit:
            break
        print(f"\n  {category} ({len(cat_issues)} issues):")
        for issue in cat_issues[:5]:  # Show max 5 per category
            if displayed >= limit:
                break
            print(f"    - {issue.get('message', 'No message')[:70]}")
            displayed += 1

    if len(issues) > limit:
        print(f"\n  ... and {len(issues) - limit} more issues (use --all to see all)")


def export_results(
    results: Dict,
    output_path: str,
    format_type: str,
    filepath: str
) -> bool:
    """
    Export results to file.

    Args:
        results: Analysis results
        output_path: Output file path
        format_type: Output format (json, csv, xlsx)
        filepath: Original document path

    Returns:
        True if export successful
    """
    try:
        if format_type == 'json':
            # Add metadata
            export_data = {
                'metadata': {
                    'tool': 'AEGIS',
                    'version': VERSION,
                    'timestamp': datetime.now().isoformat(),
                    'source_file': filepath
                },
                'results': results
            }
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            return True

        elif format_type == 'csv':
            import csv
            issues = results.get('issues', [])
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if issues:
                    writer = csv.DictWriter(f, fieldnames=issues[0].keys())
                    writer.writeheader()
                    writer.writerows(issues)
            return True

        elif format_type == 'xlsx':
            try:
                from export_module import export_xlsx_enhanced
                export_xlsx_enhanced(results, output_path)
                return True
            except ImportError:
                # Fallback to basic CSV
                print("Warning: xlsx export not available, falling back to CSV")
                csv_path = output_path.replace('.xlsx', '.csv')
                return export_results(results, csv_path, 'csv', filepath)

        else:
            print(f"Unknown format: {format_type}")
            return False

    except Exception as e:
        print(f"Export error: {e}")
        return False


def process_batch(
    file_patterns: List[str],
    preset: Optional[str],
    output_dir: str,
    format_type: str,
    verbose: bool
) -> Dict[str, Any]:
    """
    Process multiple files in batch.

    Args:
        file_patterns: List of file paths or glob patterns
        preset: Style preset name
        output_dir: Output directory
        format_type: Output format
        verbose: Verbose output

    Returns:
        Batch results summary
    """
    # Expand glob patterns
    files = []
    for pattern in file_patterns:
        expanded = glob.glob(pattern)
        if expanded:
            files.extend(expanded)
        elif os.path.exists(pattern):
            files.append(pattern)

    # Filter to supported formats
    supported = ['.docx', '.pdf']
    files = [f for f in files if Path(f).suffix.lower() in supported]

    if not files:
        print("No supported files found (.docx, .pdf)")
        return {'success': False, 'processed': 0}

    print(f"\nProcessing {len(files)} files...")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    results_summary = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'total_issues': 0,
        'files': []
    }

    for i, filepath in enumerate(files, 1):
        filename = Path(filepath).name
        print(f"  [{i}/{len(files)}] {filename}...", end=' ', flush=True)

        results = analyze_document(filepath, preset, verbose=False)

        if results.get('success', False):
            issue_count = len(results.get('issues', []))
            print(f"{issue_count} issues")
            results_summary['successful'] += 1
            results_summary['total_issues'] += issue_count

            # Export individual results
            output_name = Path(filepath).stem + f'_results.{format_type}'
            output_path = os.path.join(output_dir, output_name)
            export_results(results, output_path, format_type, filepath)
        else:
            print(f"FAILED: {results.get('error', 'Unknown')}")
            results_summary['failed'] += 1

        results_summary['files'].append({
            'filepath': filepath,
            'success': results.get('success', False),
            'issues': len(results.get('issues', [])) if results.get('success') else 0
        })
        results_summary['processed'] += 1

    # Write batch summary
    summary_path = os.path.join(output_dir, 'batch_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2)

    print(f"\nBatch Complete:")
    print(f"  Processed: {results_summary['processed']}")
    print(f"  Successful: {results_summary['successful']}")
    print(f"  Failed: {results_summary['failed']}")
    print(f"  Total Issues: {results_summary['total_issues']}")
    print(f"  Results saved to: {output_dir}/")

    return results_summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='twr',
        description='AEGIS - Enterprise Document Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s report.docx                    Basic analysis
  %(prog)s report.docx --preset microsoft Use Microsoft style
  %(prog)s report.docx -o results.json    Export to JSON
  %(prog)s docs/*.docx --batch            Batch processing
  %(prog)s --list-presets                 Show available presets
        """
    )

    # Positional arguments
    parser.add_argument(
        'files',
        nargs='*',
        help='Document file(s) to analyze (.docx, .pdf)'
    )

    # Preset selection
    parser.add_argument(
        '-p', '--preset',
        choices=['microsoft', 'google', 'plain_language', 'asd_ste100',
                 'government', 'aerospace', 'all_checks', 'minimal'],
        help='Style guide preset to use'
    )

    # Output options
    parser.add_argument(
        '-o', '--output',
        help='Output file path'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'csv', 'xlsx', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    # Batch processing
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process multiple files in batch mode'
    )
    parser.add_argument(
        '--output-dir',
        default='twr_results',
        help='Output directory for batch results (default: twr_results)'
    )

    # Display options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - minimal output'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all issues (no limit)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum issues to display (default: 50)'
    )

    # Info options
    parser.add_argument(
        '--list-presets',
        action='store_true',
        help='List available style presets'
    )
    parser.add_argument(
        '--list-checkers',
        action='store_true',
        help='List all available checkers'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'AEGIS v{VERSION}'
    )

    # Checker toggles
    parser.add_argument(
        '--enable',
        nargs='+',
        help='Enable specific checkers (space-separated)'
    )
    parser.add_argument(
        '--disable',
        nargs='+',
        help='Disable specific checkers (space-separated)'
    )

    args = parser.parse_args()

    # Handle info commands
    if args.list_presets:
        print_banner()
        list_presets()
        return 0

    if args.list_checkers:
        print_banner()
        try:
            from core import AEGISEngine
            reviewer = AEGISEngine()
            print("\nAvailable Checkers:")
            print("=" * 60)
            for name, checker in sorted(reviewer.checkers.items()):
                desc = getattr(checker, 'description', 'No description')
                print(f"  {name:30} {desc[:40]}")
            print(f"\nTotal: {len(reviewer.checkers)} checkers")
        except Exception as e:
            print(f"Error loading checkers: {e}")
        return 0

    # Require files for analysis
    if not args.files:
        parser.print_help()
        return 1

    if not args.quiet:
        print_banner()

    # Build custom options from --enable/--disable
    custom_options = {}
    if args.enable:
        for checker in args.enable:
            custom_options[f'check_{checker}'] = True
    if args.disable:
        for checker in args.disable:
            custom_options[f'check_{checker}'] = False

    # Batch processing
    if args.batch:
        results = process_batch(
            args.files,
            args.preset,
            args.output_dir,
            args.format if args.format != 'text' else 'json',
            args.verbose
        )
        return 0 if results['failed'] == 0 else 1

    # Single file processing
    filepath = args.files[0]

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return 1

    print(f"Analyzing: {filepath}")
    if args.preset:
        print(f"Preset: {args.preset}")

    # Run analysis
    results = analyze_document(
        filepath,
        args.preset,
        custom_options if custom_options else None,
        args.verbose
    )

    # Handle output
    if args.output or args.format != 'text':
        output_path = args.output or f"{Path(filepath).stem}_results.{args.format}"
        if export_results(results, output_path, args.format, filepath):
            print(f"\nResults exported to: {output_path}")
        else:
            print("\nExport failed")
            return 1

    # Print results to console
    if not args.quiet:
        print_summary(results, filepath)

        if not args.output:  # Only print issues if not exporting
            limit = None if args.all else args.limit
            print_issues(results, limit or 9999)

    # Return exit code based on errors
    if results.get('success', False):
        errors = sum(1 for i in results.get('issues', [])
                    if i.get('severity') == 'error')
        return 1 if errors > 0 else 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
