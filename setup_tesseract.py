#!/usr/bin/env python3
"""
Tesseract OCR Setup Script for AEGIS
====================================
Version: 1.0.0
Date: 2026-02-04

This script helps set up Tesseract OCR for AEGIS, including:
- Checking if Tesseract is installed
- Providing installation instructions
- Downloading language data for offline packaging
- Verifying the installation

For air-gapped deployment, Tesseract binaries and language data
must be packaged with the application.

Author: Nick / SAIC Systems Engineering
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List

__version__ = "1.0.0"

# Tesseract language data URLs (tessdata_fast - smaller, good quality)
TESSDATA_BASE_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/main"
DEFAULT_LANGUAGES = ['eng']  # English by default
ADDITIONAL_LANGUAGES = ['osd']  # Orientation and script detection

# Common Tesseract installation paths
TESSERACT_PATHS = {
    'Darwin': [  # macOS
        '/opt/homebrew/bin/tesseract',
        '/usr/local/bin/tesseract',
        '/usr/bin/tesseract',
    ],
    'Linux': [
        '/usr/bin/tesseract',
        '/usr/local/bin/tesseract',
    ],
    'Windows': [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
}


class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def color(text: str, color_code: str) -> str:
    if sys.stdout.isatty():
        return f"{color_code}{text}{Colors.END}"
    return text


def find_tesseract() -> Optional[str]:
    """Find Tesseract executable."""
    # First check if it's in PATH
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        return tesseract_path

    # Check common installation paths
    system = platform.system()
    paths = TESSERACT_PATHS.get(system, [])

    for path in paths:
        if os.path.exists(path):
            return path

    return None


def get_tesseract_version(tesseract_path: str) -> Optional[str]:
    """Get Tesseract version."""
    try:
        result = subprocess.run(
            [tesseract_path, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Version is typically on first line: "tesseract 5.3.0"
        first_line = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
        return first_line.strip()
    except Exception:
        return None


def get_tessdata_path(tesseract_path: str) -> Optional[str]:
    """Get the tessdata directory path."""
    try:
        result = subprocess.run(
            [tesseract_path, '--print-parameters'],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Look for tessdata_dir in output
        for line in result.stdout.split('\n'):
            if 'tessdata_dir' in line.lower():
                # Format: "tessdata_dir	/path/to/tessdata"
                parts = line.split('\t')
                if len(parts) >= 2:
                    return parts[-1].strip()
    except Exception:
        pass

    # Try common locations relative to tesseract path
    tesseract_dir = os.path.dirname(tesseract_path)
    common_tessdata = [
        os.path.join(tesseract_dir, '..', 'share', 'tessdata'),
        os.path.join(tesseract_dir, '..', 'share', 'tesseract-ocr', 'tessdata'),
        os.path.join(tesseract_dir, 'tessdata'),
        '/usr/share/tesseract-ocr/4.00/tessdata',
        '/usr/share/tesseract-ocr/5/tessdata',
        '/usr/local/share/tessdata',
        '/opt/homebrew/share/tessdata',
    ]

    for path in common_tessdata:
        normalized = os.path.normpath(path)
        if os.path.exists(normalized):
            return normalized

    return None


def get_installed_languages(tessdata_path: str) -> List[str]:
    """Get list of installed language files."""
    languages = []
    if tessdata_path and os.path.exists(tessdata_path):
        for file in os.listdir(tessdata_path):
            if file.endswith('.traineddata'):
                lang = file.replace('.traineddata', '')
                languages.append(lang)
    return sorted(languages)


def download_language_data(lang: str, output_dir: str) -> bool:
    """Download language data file."""
    url = f"{TESSDATA_BASE_URL}/{lang}.traineddata"
    output_path = os.path.join(output_dir, f"{lang}.traineddata")

    try:
        print(f"  Downloading {lang}.traineddata...", end=' ')
        urllib.request.urlretrieve(url, output_path)
        print(color("✓", Colors.GREEN))
        return True
    except Exception as e:
        print(color(f"✗ ({e})", Colors.RED))
        return False


def check_tesseract_status() -> Dict[str, Any]:
    """Check complete Tesseract status."""
    status = {
        'installed': False,
        'path': None,
        'version': None,
        'tessdata_path': None,
        'languages': [],
        'pytesseract_available': False,
        'ocr_ready': False
    }

    # Find Tesseract
    tesseract_path = find_tesseract()
    if tesseract_path:
        status['installed'] = True
        status['path'] = tesseract_path
        status['version'] = get_tesseract_version(tesseract_path)
        status['tessdata_path'] = get_tessdata_path(tesseract_path)
        if status['tessdata_path']:
            status['languages'] = get_installed_languages(status['tessdata_path'])

    # Check pytesseract
    try:
        import pytesseract
        status['pytesseract_available'] = True

        # Configure pytesseract with found path
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    except ImportError:
        pass

    # OCR is ready if we have tesseract + pytesseract + eng language
    status['ocr_ready'] = (
        status['installed'] and
        status['pytesseract_available'] and
        'eng' in status['languages']
    )

    return status


def print_installation_instructions():
    """Print platform-specific installation instructions."""
    system = platform.system()

    print(f"\n{color('Installation Instructions:', Colors.BOLD)}")
    print("=" * 50)

    if system == 'Darwin':  # macOS
        print("""
macOS Installation Options:

Option 1: Homebrew (Recommended)
  $ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  $ brew install tesseract

Option 2: MacPorts
  $ sudo port install tesseract

Option 3: Download Binary
  Visit: https://github.com/UB-Mannheim/tesseract/wiki
  Download and install the macOS package

After installation, verify with:
  $ tesseract --version
""")

    elif system == 'Linux':
        print("""
Linux Installation:

Ubuntu/Debian:
  $ sudo apt update
  $ sudo apt install tesseract-ocr tesseract-ocr-eng

CentOS/RHEL:
  $ sudo yum install tesseract

Fedora:
  $ sudo dnf install tesseract tesseract-langpack-eng

After installation, verify with:
  $ tesseract --version
""")

    elif system == 'Windows':
        print("""
Windows Installation:

Option 1: Download Installer (Recommended)
  1. Visit: https://github.com/UB-Mannheim/tesseract/wiki
  2. Download the latest installer (tesseract-ocr-w64-setup-*.exe)
  3. Run the installer
  4. During installation, select additional languages if needed
  5. Add Tesseract to PATH:
     - Default path: C:\\Program Files\\Tesseract-OCR
     - Add to system PATH environment variable

Option 2: Chocolatey
  $ choco install tesseract

After installation, verify with:
  $ tesseract --version
""")


def setup_for_packaging(output_dir: str, languages: List[str] = None) -> Dict[str, Any]:
    """
    Set up Tesseract components for packaging.

    This downloads language data that can be bundled with the application
    for air-gapped deployment.
    """
    if languages is None:
        languages = DEFAULT_LANGUAGES + ADDITIONAL_LANGUAGES

    result = {
        'success': False,
        'output_dir': output_dir,
        'languages_downloaded': [],
        'errors': []
    }

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    tessdata_dir = os.path.join(output_dir, 'tessdata')
    os.makedirs(tessdata_dir, exist_ok=True)

    print(f"\nDownloading language data to: {tessdata_dir}")
    print("-" * 50)

    for lang in languages:
        if download_language_data(lang, tessdata_dir):
            result['languages_downloaded'].append(lang)
        else:
            result['errors'].append(f"Failed to download {lang}")

    result['success'] = len(result['errors']) == 0 and len(result['languages_downloaded']) > 0

    # Create a README for the package
    readme_path = os.path.join(output_dir, 'TESSERACT_PACKAGING_README.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("""TESSERACT OCR PACKAGING GUIDE FOR AEGIS
========================================

This directory contains Tesseract language data files for air-gapped deployment.

CONTENTS:
- tessdata/: Language training data files (.traineddata)

FOR DEPLOYMENT:

1. Install Tesseract on the target system:
   - Windows: Use the installer from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: apt install tesseract-ocr (or equivalent)
   - macOS: brew install tesseract

2. Copy the tessdata files:
   - Copy the contents of tessdata/ to the system's tessdata directory
   - Common locations:
     * Windows: C:\\Program Files\\Tesseract-OCR\\tessdata
     * Linux: /usr/share/tesseract-ocr/4.00/tessdata
     * macOS: /opt/homebrew/share/tessdata or /usr/local/share/tessdata

3. Set environment variable (optional):
   - TESSDATA_PREFIX=/path/to/tessdata

4. Verify installation:
   - Run: python check_pdf_capabilities.py
   - All OCR checks should pass

LANGUAGES INCLUDED:
""")
        for lang in result['languages_downloaded']:
            f.write(f"- {lang}\n")

    print(f"\nPackaging README created: {readme_path}")

    return result


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Tesseract OCR Setup for AEGIS',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--check', action='store_true',
                       help='Check Tesseract installation status')
    parser.add_argument('--install-instructions', action='store_true',
                       help='Show installation instructions')
    parser.add_argument('--package', type=str, metavar='OUTPUT_DIR',
                       help='Download language data for packaging')
    parser.add_argument('--languages', type=str, nargs='+', default=['eng', 'osd'],
                       help='Languages to download (default: eng osd)')

    args = parser.parse_args()

    # Default action is to check status
    if not any([args.check, args.install_instructions, args.package]):
        args.check = True

    print("=" * 60)
    print(color("AEGIS Tesseract OCR Setup", Colors.BOLD))
    print("=" * 60)

    if args.check or args.package:
        print(f"\n{color('Current Status:', Colors.BOLD)}")
        print("-" * 40)

        status = check_tesseract_status()

        def check_mark(passed: bool) -> str:
            if passed:
                return color("✓", Colors.GREEN)
            return color("✗", Colors.RED)

        print(f"  {check_mark(status['installed'])} Tesseract installed: {status['version'] or 'No'}")
        if status['path']:
            print(f"      Path: {status['path']}")
        if status['tessdata_path']:
            print(f"      Tessdata: {status['tessdata_path']}")
        if status['languages']:
            print(f"      Languages: {', '.join(status['languages'][:10])}")
            if len(status['languages']) > 10:
                print(f"                 ... and {len(status['languages']) - 10} more")

        print(f"  {check_mark(status['pytesseract_available'])} pytesseract package: {'Yes' if status['pytesseract_available'] else 'No'}")
        print(f"\n  {check_mark(status['ocr_ready'])} {color('OCR Ready:', Colors.BOLD)} {'Yes' if status['ocr_ready'] else 'No'}")

        if not status['installed']:
            print_installation_instructions()

    if args.install_instructions:
        print_installation_instructions()

    if args.package:
        result = setup_for_packaging(args.package, args.languages)

        print(f"\n{color('Packaging Summary:', Colors.BOLD)}")
        print("-" * 40)

        if result['success']:
            print(f"  {color('✓ Language data downloaded successfully', Colors.GREEN)}")
            print(f"  Languages: {', '.join(result['languages_downloaded'])}")
            print(f"  Output: {result['output_dir']}")
        else:
            print(f"  {color('✗ Some downloads failed', Colors.RED)}")
            for error in result['errors']:
                print(f"    - {error}")

        # Final status check
        print(f"\n{color('Next Steps:', Colors.BOLD)}")
        print("  1. Install Tesseract on the target system")
        print("  2. Copy tessdata files to the system's tessdata directory")
        print("  3. Run 'python check_pdf_capabilities.py' to verify")


if __name__ == "__main__":
    main()
