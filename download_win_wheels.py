#!/usr/bin/env python3
"""
AEGIS Offline Wheel Downloader for Windows x64
================================================
Run this script on a CONNECTED Windows machine to download all required
wheels for offline installation on an air-gapped production system.

Usage:
    python download_win_wheels.py

This will create a 'wheels_win/' directory with all Windows x64 wheels.
Copy that entire folder to the production machine, then run:
    pip install --no-index --find-links wheels_win/ -r requirements_offline.txt

v5.0.5: Added docling, spaCy model, and all Windows platform wheels.
"""

import subprocess
import sys
import os
from pathlib import Path

# Target directory
WHEELS_DIR = Path(__file__).parent / "wheels_win"
PYTHON_VERSION = "310"  # cp310 = Python 3.10
PLATFORM = "win_amd64"

# ═══════════════════════════════════════════════════════════════════
# PACKAGE GROUPS - organized by function
# ═══════════════════════════════════════════════════════════════════

# Core Flask & web framework
CORE_PACKAGES = [
    "flask==2.3.3",
    "waitress",
    "werkzeug",
    "jinja2",
    "markupsafe",
    "itsdangerous",
    "blinker",
    "click",
    "requests",
    "urllib3",
    "certifi",
    "charset-normalizer",
    "idna",
    "cryptography",
    "cffi",
    "pycparser",
]

# Document processing
DOC_PACKAGES = [
    "python-docx",
    "mammoth",              # DOCX to HTML
    "openpyxl",             # Excel
    "reportlab",            # PDF generation
    "pypdf",
    "pypdf2",
    "pdfplumber",
    "pdfminer.six",
    "pymupdf",              # PyMuPDF / fitz
    "pymupdf4llm",
    "pypdfium2",
    "pdf2image",
    "camelot-py",
    "tabula-py",
    "lxml",
    "pillow",
    "pytesseract",
]

# NLP & text analysis
NLP_PACKAGES = [
    "spacy>=3.8",
    "nltk",
    "textblob",
    "textstat",
    "rapidfuzz",
    "py-readability-metrics",
    "pyphen",
    "language-tool-python",
    "regex",
]

# spaCy model (downloaded separately)
SPACY_MODEL_URL = "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"

# AI/ML - docling + transformers stack
AI_PACKAGES = [
    "docling",              # AI-powered PDF layout analysis
    "transformers",
    "sentence-transformers",
    "tokenizers",
    "torch",                # CPU-only is fine for inference
    "safetensors",
    "huggingface-hub",
    "accelerate",
    "scikit-learn",
    "scipy",
    "numpy",
    "pandas",
]

# Data & visualization
DATA_PACKAGES = [
    "bokeh",
    "matplotlib",
    "contourpy",
    "opencv-python-headless",
]

# System & utilities
UTIL_PACKAGES = [
    "psutil",
    "pyyaml",
    "toml",
    "jsonschema",
    "pydantic",
    "tqdm",
    "rich",
    "tabulate",
    "diff-match-patch",
    "chardet",
    "six",
    "python-dateutil",
    "pytz",
    "packaging",
    "typing-extensions",
    "annotated-types",
    "filelock",
    "fsspec",
    "setuptools",
    "wrapt",
]

ALL_PACKAGES = CORE_PACKAGES + DOC_PACKAGES + NLP_PACKAGES + AI_PACKAGES + DATA_PACKAGES + UTIL_PACKAGES


def download_wheels():
    """Download all Windows x64 wheels."""
    WHEELS_DIR.mkdir(exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  AEGIS Offline Wheel Downloader")
    print(f"  Target: Python {PYTHON_VERSION} / {PLATFORM}")
    print(f"  Output: {WHEELS_DIR}")
    print(f"{'='*60}\n")

    # Download main packages
    print(f"[1/3] Downloading {len(ALL_PACKAGES)} packages + dependencies...\n")
    cmd = [
        sys.executable, "-m", "pip", "download",
        "--platform", PLATFORM,
        "--python-version", PYTHON_VERSION,
        "--only-binary=:all:",
        "-d", str(WHEELS_DIR),
    ] + ALL_PACKAGES

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("\n[WARNING] Some packages may have failed. Continuing...")

    # Download spaCy English model
    print(f"\n[2/3] Downloading spaCy English model...\n")
    cmd_model = [
        sys.executable, "-m", "pip", "download",
        "--no-deps",
        "-d", str(WHEELS_DIR),
        SPACY_MODEL_URL,
    ]
    subprocess.run(cmd_model, capture_output=False)

    # Summary
    print(f"\n[3/3] Summary\n")
    wheels = list(WHEELS_DIR.glob("*.whl")) + list(WHEELS_DIR.glob("*.tar.gz"))
    total_size = sum(f.stat().st_size for f in wheels)
    print(f"  Downloaded: {len(wheels)} files")
    print(f"  Total size: {total_size / (1024*1024):.1f} MB")
    print(f"  Location:   {WHEELS_DIR.resolve()}")

    # Count platform-specific vs pure Python
    win_wheels = [f for f in wheels if "win_amd64" in f.name or "win32" in f.name]
    pure_wheels = [f for f in wheels if "none-any" in f.name]
    print(f"\n  Windows-specific wheels: {len(win_wheels)}")
    print(f"  Pure Python wheels:     {len(pure_wheels)}")

    print(f"\n{'='*60}")
    print(f"  NEXT STEPS:")
    print(f"  1. Copy the entire '{WHEELS_DIR.name}/' folder to the")
    print(f"     air-gapped production machine")
    print(f"  2. On the production machine, run:")
    print(f"     pip install --no-index --find-links wheels_win/ docling spacy")
    print(f"     python -m spacy validate")
    print(f"     pip install --no-index --find-links wheels_win/ en_core_web_sm-3.8.0-py3-none-any.whl")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    download_wheels()
