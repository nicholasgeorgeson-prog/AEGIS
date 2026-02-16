#!/usr/bin/env python3
"""
AEGIS - Online NLP Installer
=======================================
Installs NLP dependencies from the internet.

Prerequisites:
1. Python 3.10+ installed
2. Internet connection

Usage:
    python install_nlp.py

This script will:
1. Install Python packages via pip
2. Download spaCy English model
3. Download NLTK data (WordNet, etc.)
"""

import os
import sys
import subprocess
import ssl


def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def print_step(msg):
    print(f"[*] {msg}")


def print_success(msg):
    print(f"[OK] {msg}")


def print_error(msg):
    print(f"[ERROR] {msg}")


def run_pip_install(packages):
    """Install packages via pip."""
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    print_step(f"Running: pip install {' '.join(packages)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print_error(f"pip install failed:\n{result.stderr}")
            return False
        return True
    except Exception as e:
        print_error(f"Failed to run pip: {e}")
        return False


def install_packages():
    """Install core NLP packages."""
    packages = [
        "spacy>=3.7.0,<3.8.0",
        "symspellpy",
        "textstat",
        "proselint",
        "nltk",
    ]

    print_step("Installing NLP packages...")
    if run_pip_install(packages):
        print_success("Core packages installed")
        return True
    return False


def install_spacy_model():
    """Download spaCy English model."""
    print_step("Downloading spaCy English model (en_core_web_md)...")
    print_step("This may take a few minutes...")

    cmd = [sys.executable, "-m", "spacy", "download", "en_core_web_md"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print_error(f"spaCy model download failed:\n{result.stderr}")
            return False
        print_success("spaCy model downloaded")
        return True
    except Exception as e:
        print_error(f"Failed to download model: {e}")
        return False


def install_nltk_data():
    """Download NLTK data."""
    print_step("Downloading NLTK data...")

    # Handle SSL certificate issues
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    try:
        import nltk

        datasets = ['wordnet', 'omw-1.4', 'cmudict']
        for dataset in datasets:
            print_step(f"  Downloading {dataset}...")
            nltk.download(dataset, quiet=True)

        print_success("NLTK data downloaded")
        return True
    except Exception as e:
        print_error(f"NLTK download failed: {e}")
        return False


def verify_installation():
    """Verify the installation works."""
    print_header("Verifying Installation")

    errors = []

    # Test spaCy
    print_step("Testing spaCy...")
    try:
        import spacy
        nlp = spacy.load("en_core_web_md")
        doc = nlp("This is a test sentence.")
        print_success(f"spaCy working (model: en_core_web_md)")
    except Exception as e:
        print_error(f"spaCy failed: {e}")
        errors.append("spaCy")

    # Test NLTK/WordNet
    print_step("Testing NLTK WordNet...")
    try:
        from nltk.corpus import wordnet
        synsets = wordnet.synsets("test")
        print_success(f"NLTK WordNet working ({len(synsets)} synsets for 'test')")
    except Exception as e:
        print_error(f"NLTK WordNet failed: {e}")
        errors.append("NLTK WordNet")

    # Test symspellpy
    print_step("Testing SymSpell...")
    try:
        from symspellpy import SymSpell
        print_success("SymSpell available")
    except Exception as e:
        print_error(f"SymSpell failed: {e}")
        errors.append("SymSpell")

    # Test textstat
    print_step("Testing textstat...")
    try:
        import textstat
        score = textstat.flesch_reading_ease("This is a test.")
        print_success(f"textstat working (Flesch score: {score})")
    except Exception as e:
        print_error(f"textstat failed: {e}")
        errors.append("textstat")

    # Test proselint
    print_step("Testing proselint...")
    try:
        import proselint
        print_success("proselint available")
    except Exception as e:
        print_error(f"proselint failed: {e}")
        errors.append("proselint")

    return len(errors) == 0


def main():
    print_header("AEGIS - Online NLP Installer")

    print(f"Python version: {sys.version}")
    print()

    # Install packages
    print_header("Installing Python Packages")
    if not install_packages():
        print_error("Package installation failed")
        print("\nTry running manually:")
        print("  pip install spacy symspellpy textstat proselint nltk")
        sys.exit(1)

    # Install spaCy model
    print_header("Installing spaCy Model")
    if not install_spacy_model():
        print_error("spaCy model installation failed")
        print("\nTry running manually:")
        print("  python -m spacy download en_core_web_md")
        sys.exit(1)

    # Install NLTK data
    print_header("Installing NLTK Data")
    if not install_nltk_data():
        print_error("NLTK data installation failed")
        print("\nTry running manually:")
        print("  python -c \"import nltk; nltk.download('wordnet')\"")
        sys.exit(1)

    # Verify
    if verify_installation():
        print_header("Installation Complete!")
        print("All NLP components installed successfully.")
        print("\nYou can now use AEGIS with full NLP capabilities.")
    else:
        print_header("Installation Completed with Warnings")
        print("Some components may not be working correctly.")
        print("Check the errors above for details.")


if __name__ == "__main__":
    main()
