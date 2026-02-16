#!/usr/bin/env python3
"""
PDF Extraction Capabilities Diagnostic for AEGIS
=================================================
Version: 1.0.0
Date: 2026-02-04

Comprehensive diagnostic script to verify all PDF extraction capabilities
are installed and ready for production deployment.

Run this script before packaging for air-gapped deployment to ensure
all models and dependencies are downloaded and configured.

Usage:
    python check_pdf_capabilities.py
    python check_pdf_capabilities.py --verbose
    python check_pdf_capabilities.py --fix    # Attempt to download missing models

Author: Nick / SAIC Systems Engineering
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

__version__ = "1.0.0"

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def color(text: str, color_code: str) -> str:
    """Apply color to text if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color_code}{text}{Colors.END}"
    return text

def check_mark(passed: bool) -> str:
    """Return colored check mark or X."""
    if passed:
        return color("✓", Colors.GREEN)
    return color("✗", Colors.RED)

def print_header(text: str):
    """Print section header."""
    print(f"\n{color('='*60, Colors.BLUE)}")
    print(f"{color(text, Colors.BOLD)}")
    print(f"{color('='*60, Colors.BLUE)}")

def print_subheader(text: str):
    """Print subsection header."""
    print(f"\n{color(text, Colors.BOLD)}")
    print("-" * 40)


# =============================================================================
# CAPABILITY CHECKS
# =============================================================================

def check_basic_pdf_libraries() -> Dict[str, Any]:
    """Check basic PDF extraction libraries."""
    results = {
        'pymupdf': {'installed': False, 'version': None},
        'pdfplumber': {'installed': False, 'version': None},
        'pypdf': {'installed': False, 'version': None},
        'any_available': False
    }

    # PyMuPDF (fitz)
    try:
        import fitz
        results['pymupdf']['installed'] = True
        results['pymupdf']['version'] = fitz.version[0] if hasattr(fitz, 'version') else 'unknown'
    except ImportError:
        pass

    # pdfplumber
    try:
        import pdfplumber
        results['pdfplumber']['installed'] = True
        results['pdfplumber']['version'] = getattr(pdfplumber, '__version__', 'unknown')
    except ImportError:
        pass

    # pypdf
    try:
        import pypdf
        results['pypdf']['installed'] = True
        results['pypdf']['version'] = getattr(pypdf, '__version__', 'unknown')
    except ImportError:
        pass

    results['any_available'] = any([
        results['pymupdf']['installed'],
        results['pdfplumber']['installed'],
        results['pypdf']['installed']
    ])

    return results


def check_ocr_capabilities() -> Dict[str, Any]:
    """Check OCR extraction capabilities."""
    results = {
        'pytesseract': {'installed': False, 'version': None},
        'tesseract_engine': {'installed': False, 'version': None, 'path': None, 'local': False},
        'pdf2image': {'installed': False, 'version': None},
        'poppler': {'installed': False, 'path': None, 'local': False},
        'pil': {'installed': False, 'version': None},
        'ocr_ready': False
    }

    # Check for local Tesseract installation first (Windows portable)
    script_dir = Path(__file__).parent
    local_tesseract_paths = [
        script_dir / 'tools' / 'tesseract' / 'tesseract.exe',
        script_dir / 'tesseract' / 'tesseract.exe',
        script_dir / 'tesseract_package' / 'tesseract' / 'tesseract.exe',
    ]

    local_tesseract = None
    for path in local_tesseract_paths:
        if path.exists():
            local_tesseract = str(path)
            break

    # Also check TESSERACT_CMD environment variable
    if not local_tesseract:
        env_tesseract = os.environ.get('TESSERACT_CMD')
        if env_tesseract and os.path.exists(env_tesseract):
            local_tesseract = env_tesseract

    # pytesseract Python package
    try:
        import pytesseract
        results['pytesseract']['installed'] = True
        results['pytesseract']['version'] = getattr(pytesseract, '__version__', 'unknown')

        # Configure pytesseract to use local Tesseract if found
        if local_tesseract:
            pytesseract.pytesseract.tesseract_cmd = local_tesseract

        # Check if Tesseract engine is installed
        try:
            version = pytesseract.get_tesseract_version()
            results['tesseract_engine']['installed'] = True
            results['tesseract_engine']['version'] = str(version)
            results['tesseract_engine']['path'] = local_tesseract or shutil.which('tesseract') or pytesseract.pytesseract.tesseract_cmd
            results['tesseract_engine']['local'] = local_tesseract is not None
        except Exception:
            # If local tesseract exists but pytesseract couldn't get version, still note it
            if local_tesseract:
                results['tesseract_engine']['path'] = local_tesseract
                results['tesseract_engine']['local'] = True
    except ImportError:
        pass

    # Check for local Poppler installation (Windows portable)
    local_poppler_paths = [
        script_dir / 'tools' / 'poppler' / 'bin',
        script_dir / 'poppler' / 'bin',
        script_dir / 'tesseract_package' / 'poppler' / 'bin',
    ]

    local_poppler = None
    for path in local_poppler_paths:
        if path.exists() and (path / 'pdftoppm.exe').exists():
            local_poppler = str(path)
            break

    # Also check POPPLER_PATH environment variable
    if not local_poppler:
        env_poppler = os.environ.get('POPPLER_PATH')
        if env_poppler and os.path.exists(env_poppler):
            local_poppler = env_poppler

    if local_poppler:
        results['poppler']['installed'] = True
        results['poppler']['path'] = local_poppler
        results['poppler']['local'] = True
    elif shutil.which('pdftoppm'):
        results['poppler']['installed'] = True
        results['poppler']['path'] = shutil.which('pdftoppm')

    # pdf2image
    try:
        import pdf2image
        results['pdf2image']['installed'] = True
        results['pdf2image']['version'] = getattr(pdf2image, '__version__', 'unknown')
    except ImportError:
        pass

    # PIL/Pillow
    try:
        from PIL import Image
        import PIL
        results['pil']['installed'] = True
        results['pil']['version'] = getattr(PIL, '__version__', 'unknown')
    except ImportError:
        pass

    # OCR is ready if we have pytesseract + tesseract engine + PIL
    results['ocr_ready'] = (
        results['pytesseract']['installed'] and
        results['tesseract_engine']['installed'] and
        results['pil']['installed']
    )

    return results


def check_docling_installation() -> Dict[str, Any]:
    """Check Docling installation and model availability."""
    results = {
        'installed': False,
        'version': None,
        'pytorch': {'installed': False, 'version': None, 'cuda': False},
        'models_path': None,
        'models_downloaded': False,
        'required_models': {},
        'optional_models': {},
        'offline_ready': False,
        'env_vars': {}
    }

    # Check environment variables
    results['env_vars'] = {
        'DOCLING_ARTIFACTS_PATH': os.environ.get('DOCLING_ARTIFACTS_PATH'),
        'DOCLING_SERVE_ARTIFACTS_PATH': os.environ.get('DOCLING_SERVE_ARTIFACTS_PATH'),
        'HF_HUB_OFFLINE': os.environ.get('HF_HUB_OFFLINE'),
        'TRANSFORMERS_OFFLINE': os.environ.get('TRANSFORMERS_OFFLINE'),
    }

    # Check PyTorch
    try:
        import torch
        results['pytorch']['installed'] = True
        results['pytorch']['version'] = torch.__version__
        results['pytorch']['cuda'] = torch.cuda.is_available()
    except ImportError:
        pass

    # Check Docling
    try:
        import docling
        results['installed'] = True
        results['version'] = getattr(docling, '__version__', 'unknown')
    except ImportError:
        return results

    # Find models path
    models_path = (
        os.environ.get('DOCLING_ARTIFACTS_PATH') or
        os.environ.get('DOCLING_SERVE_ARTIFACTS_PATH')
    )

    if not models_path:
        # Check common default locations
        home = os.path.expanduser("~")
        default_paths = [
            os.path.join(home, ".cache", "docling", "models"),
            os.path.join(home, ".cache", "huggingface", "hub"),
        ]
        for path in default_paths:
            if os.path.exists(path):
                models_path = path
                break

    if models_path and os.path.exists(models_path):
        results['models_path'] = models_path

        # Required model directories
        required_dirs = [
            'ds4sd--docling-models',
            'models--ds4sd--docling-models',  # Alternative naming
        ]

        # Check for required models
        for model_dir in required_dirs:
            path = os.path.join(models_path, model_dir)
            exists = os.path.exists(path)
            results['required_models'][model_dir] = exists
            if exists:
                results['models_downloaded'] = True

        # Optional model directories
        optional_dirs = [
            'EasyOcr',
            'ds4sd--CodeFormulaV2',
            'models--ds4sd--CodeFormulaV2',
            'ds4sd--DocumentFigureClassifier',
        ]

        for model_dir in optional_dirs:
            path = os.path.join(models_path, model_dir)
            results['optional_models'][model_dir] = os.path.exists(path)

    # If models not found in expected locations, try to use DoclingManager
    if not results['models_downloaded']:
        try:
            from docling_extractor import DoclingManager
            status = DoclingManager.check_installation()
            results['models_path'] = status.get('models_path')
            results['models_downloaded'] = status.get('models_downloaded', False)
            results['required_models'] = status.get('required_models', {})
            results['optional_models'] = status.get('optional_models', {})
        except Exception:
            pass

    # Determine offline readiness
    results['offline_ready'] = (
        results['installed'] and
        results['pytorch']['installed'] and
        results['models_downloaded']
    )

    return results


def check_aegis_extractors() -> Dict[str, Any]:
    """Check AEGIS-specific extractor modules."""
    results = {
        'pdf_extractor': {'available': False, 'version': None},
        'pdf_extractor_v2': {'available': False, 'version': None},
        'docling_extractor': {'available': False, 'version': None},
        'ocr_extractor': {'available': False, 'version': None},
    }

    # pdf_extractor
    try:
        import pdf_extractor
        results['pdf_extractor']['available'] = True
        results['pdf_extractor']['version'] = getattr(pdf_extractor, '__version__', 'unknown')
        results['pdf_extractor']['library'] = pdf_extractor.get_pdf_library() if hasattr(pdf_extractor, 'get_pdf_library') else 'unknown'
    except ImportError:
        pass

    # pdf_extractor_v2
    try:
        import pdf_extractor_v2
        results['pdf_extractor_v2']['available'] = True
        results['pdf_extractor_v2']['version'] = getattr(pdf_extractor_v2, '__version__', 'unknown')
    except ImportError:
        pass

    # docling_extractor
    try:
        import docling_extractor
        results['docling_extractor']['available'] = True
        results['docling_extractor']['version'] = getattr(docling_extractor, '__version__', 'unknown')
    except ImportError:
        pass

    # ocr_extractor
    try:
        import ocr_extractor
        results['ocr_extractor']['available'] = True
        results['ocr_extractor']['version'] = getattr(ocr_extractor, '__version__', 'unknown')
    except ImportError:
        pass

    return results


def estimate_disk_usage() -> Dict[str, Any]:
    """Estimate disk usage of installed components."""
    results = {
        'models_size_mb': 0,
        'packages_size_mb': 0,
        'details': {}
    }

    # Check common model/cache directories
    home = os.path.expanduser("~")
    cache_dirs = [
        os.path.join(home, ".cache", "docling"),
        os.path.join(home, ".cache", "huggingface"),
        os.path.join(home, ".cache", "torch"),
        os.environ.get('DOCLING_ARTIFACTS_PATH', ''),
    ]

    for cache_dir in cache_dirs:
        if cache_dir and os.path.exists(cache_dir):
            try:
                size = sum(
                    f.stat().st_size
                    for f in Path(cache_dir).rglob('*')
                    if f.is_file()
                )
                size_mb = size / (1024 * 1024)
                results['details'][cache_dir] = f"{size_mb:.1f} MB"
                results['models_size_mb'] += size_mb
            except Exception:
                results['details'][cache_dir] = "Error calculating"

    return results


# =============================================================================
# MAIN DIAGNOSTIC RUNNER
# =============================================================================

def run_diagnostics(verbose: bool = False, fix: bool = False) -> Dict[str, Any]:
    """Run all diagnostic checks."""
    print_header("AEGIS PDF Extraction Capabilities Diagnostic")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")

    all_results = {}
    issues = []
    recommendations = []

    # 1. Basic PDF Libraries
    print_subheader("1. Basic PDF Libraries")
    pdf_results = check_basic_pdf_libraries()
    all_results['basic_pdf'] = pdf_results

    for lib in ['pymupdf', 'pdfplumber', 'pypdf']:
        info = pdf_results[lib]
        status = check_mark(info['installed'])
        version = f"v{info['version']}" if info['version'] else ""
        print(f"  {status} {lib}: {version if info['installed'] else 'Not installed'}")

    if not pdf_results['any_available']:
        issues.append("No PDF library installed")
        recommendations.append("Install pymupdf: pip install pymupdf")

    # 2. OCR Capabilities
    print_subheader("2. OCR Capabilities (Scanned PDFs)")
    ocr_results = check_ocr_capabilities()
    all_results['ocr'] = ocr_results

    print(f"  {check_mark(ocr_results['pytesseract']['installed'])} pytesseract: {ocr_results['pytesseract']['version'] or 'Not installed'}")

    tess_status = ocr_results['tesseract_engine']['version'] or 'Not installed'
    if ocr_results['tesseract_engine'].get('local'):
        tess_status += " (local/portable)"
    print(f"  {check_mark(ocr_results['tesseract_engine']['installed'])} Tesseract engine: {tess_status}")
    if ocr_results['tesseract_engine']['path']:
        print(f"      Path: {ocr_results['tesseract_engine']['path']}")

    print(f"  {check_mark(ocr_results['pdf2image']['installed'])} pdf2image: {ocr_results['pdf2image']['version'] or 'Not installed'}")

    poppler_status = 'Not installed'
    if ocr_results['poppler']['installed']:
        poppler_status = 'Installed'
        if ocr_results['poppler'].get('local'):
            poppler_status += " (local/portable)"
    print(f"  {check_mark(ocr_results['poppler']['installed'])} Poppler (pdf2image): {poppler_status}")
    if ocr_results['poppler']['path']:
        print(f"      Path: {ocr_results['poppler']['path']}")

    print(f"  {check_mark(ocr_results['pil']['installed'])} PIL/Pillow: {ocr_results['pil']['version'] or 'Not installed'}")
    print(f"\n  {check_mark(ocr_results['ocr_ready'])} OCR Ready: {'Yes' if ocr_results['ocr_ready'] else 'No'}")

    if not ocr_results['ocr_ready']:
        if not ocr_results['tesseract_engine']['installed']:
            issues.append("Tesseract OCR engine not installed")
            recommendations.append("Run setup.bat to install local Tesseract, or install system-wide")
        if not ocr_results['poppler']['installed']:
            issues.append("Poppler not installed (needed for PDF-to-image OCR)")
            recommendations.append("Run setup.bat to install local Poppler, or install system-wide")

    # 3. Docling (Advanced AI-Powered Extraction)
    print_subheader("3. Docling (AI-Powered Document Parsing)")
    docling_results = check_docling_installation()
    all_results['docling'] = docling_results

    print(f"  {check_mark(docling_results['installed'])} Docling package: {docling_results['version'] or 'Not installed'}")
    print(f"  {check_mark(docling_results['pytorch']['installed'])} PyTorch: {docling_results['pytorch']['version'] or 'Not installed'}")
    if docling_results['pytorch']['installed']:
        print(f"      CUDA available: {docling_results['pytorch']['cuda']}")

    print(f"\n  Models Path: {docling_results['models_path'] or 'Not found'}")
    print(f"  {check_mark(docling_results['models_downloaded'])} Models downloaded: {'Yes' if docling_results['models_downloaded'] else 'No'}")

    if docling_results['required_models']:
        print("\n  Required Models:")
        for model, exists in docling_results['required_models'].items():
            print(f"    {check_mark(exists)} {model}")

    if verbose and docling_results['optional_models']:
        print("\n  Optional Models:")
        for model, exists in docling_results['optional_models'].items():
            print(f"    {check_mark(exists)} {model}")

    print(f"\n  Environment Variables:")
    for var, value in docling_results['env_vars'].items():
        status = check_mark(value is not None)
        print(f"    {status} {var}: {value or 'Not set'}")

    print(f"\n  {check_mark(docling_results['offline_ready'])} {color('OFFLINE READY:', Colors.BOLD)} {'Yes' if docling_results['offline_ready'] else 'No'}")

    if docling_results['installed'] and not docling_results['models_downloaded']:
        issues.append("Docling models not downloaded")
        recommendations.append("Run: python -c \"from docling_extractor import DoclingManager; DoclingManager.download_models()\"")

    if docling_results['installed'] and not docling_results['env_vars'].get('DOCLING_ARTIFACTS_PATH'):
        recommendations.append("Set DOCLING_ARTIFACTS_PATH environment variable for production deployment")

    # 4. AEGIS Extractor Modules
    print_subheader("4. AEGIS Extractor Modules")
    aegis_results = check_aegis_extractors()
    all_results['aegis_modules'] = aegis_results

    for module, info in aegis_results.items():
        status = check_mark(info['available'])
        version = f"v{info['version']}" if info.get('version') else ""
        extra = f" (using {info['library']})" if info.get('library') else ""
        print(f"  {status} {module}: {version}{extra if info['available'] else 'Not available'}")

    # 5. Disk Usage
    if verbose:
        print_subheader("5. Disk Usage")
        disk_results = estimate_disk_usage()
        all_results['disk'] = disk_results

        for path, size in disk_results['details'].items():
            print(f"  {path}: {size}")
        print(f"\n  Total models/cache: {disk_results['models_size_mb']:.1f} MB")

    # Summary
    print_header("Summary")

    # Determine overall status
    basic_ok = pdf_results['any_available']
    ocr_ok = ocr_results['ocr_ready']
    docling_ok = docling_results['offline_ready']
    aegis_ok = all(m['available'] for m in aegis_results.values())

    production_ready = basic_ok and aegis_ok and (ocr_ok or docling_ok)

    print(f"\n  {check_mark(basic_ok)} Basic PDF extraction: {'Ready' if basic_ok else 'NOT READY'}")
    print(f"  {check_mark(ocr_ok)} OCR extraction: {'Ready' if ocr_ok else 'NOT READY'}")
    print(f"  {check_mark(docling_ok)} Docling AI extraction: {'Ready (OFFLINE)' if docling_ok else 'NOT READY'}")
    print(f"  {check_mark(aegis_ok)} AEGIS modules: {'All available' if aegis_ok else 'Some missing'}")

    print(f"\n  {'='*40}")
    if production_ready:
        print(f"  {color('✓ PRODUCTION READY', Colors.GREEN + Colors.BOLD)}")
        print(f"  All essential PDF extraction capabilities are installed.")
        if docling_ok:
            print(f"  {color('✓ Air-gapped deployment ready', Colors.GREEN)}")
    else:
        print(f"  {color('✗ NOT READY FOR PRODUCTION', Colors.RED + Colors.BOLD)}")

    if issues:
        print(f"\n{color('Issues Found:', Colors.RED)}")
        for issue in issues:
            print(f"  • {issue}")

    if recommendations:
        print(f"\n{color('Recommendations:', Colors.YELLOW)}")
        for rec in recommendations:
            print(f"  → {rec}")

    # Fix mode
    if fix and not docling_results['models_downloaded'] and docling_results['installed']:
        print_subheader("Attempting to Download Docling Models...")
        try:
            from docling_extractor import DoclingManager
            result = DoclingManager.download_models()
            if result.get('success'):
                print(f"  {color('✓ Models downloaded successfully', Colors.GREEN)}")
            else:
                print(f"  {color('✗ Download failed', Colors.RED)}")
                for error in result.get('errors', []):
                    print(f"    {error}")
        except Exception as e:
            print(f"  {color(f'✗ Error: {e}', Colors.RED)}")

    all_results['summary'] = {
        'basic_pdf_ready': basic_ok,
        'ocr_ready': ocr_ok,
        'docling_ready': docling_ok,
        'aegis_modules_ready': aegis_ok,
        'production_ready': production_ready,
        'issues': issues,
        'recommendations': recommendations
    }

    return all_results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='AEGIS PDF Extraction Capabilities Diagnostic',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed information including disk usage')
    parser.add_argument('--fix', action='store_true',
                       help='Attempt to download missing models')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    parser.add_argument('--output', '-o', type=str,
                       help='Save results to file')

    args = parser.parse_args()

    results = run_diagnostics(verbose=args.verbose, fix=args.fix)

    if args.json:
        # Clean up results for JSON serialization
        def clean_for_json(obj):
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [clean_for_json(i) for i in obj]
            elif obj is None or isinstance(obj, (bool, int, float, str)):
                return obj
            else:
                return str(obj)

        json_output = json.dumps(clean_for_json(results), indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"\nResults saved to: {args.output}")
        else:
            print("\n" + json_output)
    elif args.output:
        # Save text summary
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(f"AEGIS PDF Extraction Diagnostic\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Production Ready: {results['summary']['production_ready']}\n")
            f.write(f"\nIssues:\n")
            for issue in results['summary']['issues']:
                f.write(f"  - {issue}\n")
        print(f"\nResults saved to: {args.output}")

    # Exit with appropriate code
    sys.exit(0 if results['summary']['production_ready'] else 1)


if __name__ == "__main__":
    main()
