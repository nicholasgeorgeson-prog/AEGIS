#!/usr/bin/env python3
"""
AEGIS - Offline NLP Installer
========================================
Installs NLP dependencies from bundled packages (no internet required).

Prerequisites:
1. Python 3.10 installed
2. nlp_offline folder extracted (from nlp_offline_windows.zip)

Usage:
    python install_nlp_offline.py

This script will:
1. Install Python packages from nlp_offline/packages/
2. Install spaCy model from nlp_offline/spacy_model/
3. Set up NLTK data from nlp_offline/nltk_data/
"""

import os
import sys
import subprocess
import shutil
import zipfile
from pathlib import Path


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


def check_python_version():
    """Check that Python 3.12 is being used."""
    version = sys.version_info
    if version.major != 3 or version.minor != 12:
        print_error(f"Python 3.12 required, but you have {version.major}.{version.minor}")
        print("Please install Python 3.12 and run this script with it.")
        return False
    print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def find_nlp_offline_folder():
    """Find the nlp_offline folder."""
    script_dir = Path(__file__).parent
    nlp_offline = script_dir / "nlp_offline"

    if nlp_offline.exists():
        return nlp_offline

    # Check if it's in current directory
    cwd_offline = Path.cwd() / "nlp_offline"
    if cwd_offline.exists():
        return cwd_offline

    return None


def install_packages(nlp_offline: Path):
    """Install Python packages from wheels."""
    packages_dir = nlp_offline / "packages"

    if not packages_dir.exists():
        print_error(f"Packages directory not found: {packages_dir}")
        return False

    wheels = list(packages_dir.glob("*.whl"))
    if not wheels:
        print_error("No .whl files found in packages directory")
        return False

    print_step(f"Found {len(wheels)} packages to install")

    # Install all wheels
    cmd = [sys.executable, "-m", "pip", "install", "--no-index", "--find-links",
           str(packages_dir)] + [str(w) for w in wheels]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print_error(f"pip install failed:\n{result.stderr}")
            return False
        print_success("All packages installed")
        return True
    except Exception as e:
        print_error(f"Failed to run pip: {e}")
        return False


def install_spacy_model(nlp_offline: Path):
    """Install spaCy model from tarball."""
    model_dir = nlp_offline / "spacy_model"
    model_tarball = model_dir / "en_core_web_md-3.7.1.tar.gz"

    if not model_tarball.exists():
        print_error(f"spaCy model not found: {model_tarball}")
        return False

    print_step("Installing spaCy model...")

    cmd = [sys.executable, "-m", "pip", "install", str(model_tarball)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print_error(f"Model install failed:\n{result.stderr}")
            return False
        print_success("spaCy model installed")
        return True
    except Exception as e:
        print_error(f"Failed to install model: {e}")
        return False


def setup_nltk_data(nlp_offline: Path):
    """Set up NLTK data."""
    nltk_source = nlp_offline / "nltk_data"

    if not nltk_source.exists():
        print_error(f"NLTK data not found: {nltk_source}")
        return False

    # Determine NLTK data directory
    if sys.platform == "win32":
        nltk_target = Path.home() / "nltk_data" / "corpora"
    else:
        nltk_target = Path.home() / "nltk_data" / "corpora"

    nltk_target.mkdir(parents=True, exist_ok=True)

    print_step(f"Copying NLTK data to {nltk_target}")

    # Copy zip files and extract them
    for zip_file in nltk_source.glob("*.zip"):
        target_zip = nltk_target / zip_file.name

        # Copy the zip file
        shutil.copy2(zip_file, target_zip)

        # Extract it
        folder_name = zip_file.stem  # wordnet, omw-1.4, cmudict
        extract_dir = nltk_target / folder_name

        if not extract_dir.exists():
            print_step(f"  Extracting {zip_file.name}...")
            with zipfile.ZipFile(target_zip, 'r') as zf:
                zf.extractall(nltk_target)

    print_success("NLTK data installed")
    return True


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
    print_header("AEGIS - Offline NLP Installer")

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Find nlp_offline folder
    nlp_offline = find_nlp_offline_folder()
    if not nlp_offline:
        print_error("nlp_offline folder not found!")
        print("\nPlease ensure you have:")
        print("1. Downloaded nlp_offline_windows.zip from GitHub Releases")
        print("2. Extracted it to the AEGIS folder")
        print("\nExpected location: AEGIS/nlp_offline/")
        sys.exit(1)

    print_success(f"Found nlp_offline at: {nlp_offline}")

    # Install packages
    print_header("Installing Python Packages")
    if not install_packages(nlp_offline):
        print_error("Package installation failed")
        sys.exit(1)

    # Install spaCy model
    print_header("Installing spaCy Model")
    if not install_spacy_model(nlp_offline):
        print_error("spaCy model installation failed")
        sys.exit(1)

    # Setup NLTK data
    print_header("Setting Up NLTK Data")
    if not setup_nltk_data(nlp_offline):
        print_error("NLTK data setup failed")
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
