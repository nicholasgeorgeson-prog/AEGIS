#!/usr/bin/env python3
"""
AEGIS - NLP Model Installer
=======================================
Downloads and installs all NLP models required for full AEGIS functionality.
Can run online (downloads from internet) or offline (uses bundled data).

Prerequisites:
1. Python 3.10+ installed
2. spaCy, NLTK already installed (via pip/wheels)
3. Internet connection (for online mode)

Usage:
    python install_nlp.py           # Online: downloads everything
    python install_nlp.py --verify  # Just verify what's installed
    python install_nlp.py --offline # Use bundled nltk_data/ if available

This script installs:
1. spaCy English model (en_core_web_sm)
2. NLTK data: punkt, punkt_tab, averaged_perceptron_tagger,
   averaged_perceptron_tagger_eng, stopwords, wordnet, omw-1.4, cmudict

v6.1.9: NLTK data packages are bundled as ZIP files in the project's
nltk_data/ directory (8 packages, ~57MB total). The --offline flag now
defaults to this directory. app.py sets NLTK_DATA env var to point here
on startup, so no nltk.download() calls are needed at runtime.
"""

import os
import sys
import subprocess
import ssl
import zipfile
from pathlib import Path


# ============================================================
# Required NLP models — must match health check in core_routes.py
# ============================================================
REQUIRED_NLTK_DATA = [
    # Tokenizers
    ('punkt', 'tokenizers/punkt'),
    ('punkt_tab', 'tokenizers/punkt_tab'),
    # Taggers
    ('averaged_perceptron_tagger', 'taggers/averaged_perceptron_tagger'),
    ('averaged_perceptron_tagger_eng', 'taggers/averaged_perceptron_tagger_eng'),
    # Corpora
    ('stopwords', 'corpora/stopwords'),
    ('wordnet', 'corpora/wordnet'),
    ('omw-1.4', 'corpora/omw-1.4'),
    ('cmudict', 'corpora/cmudict'),
]

SPACY_MODEL = 'en_core_web_sm'


def print_header(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def print_step(msg):
    print(f"[*] {msg}")


def print_success(msg):
    print(f"[OK] {msg}")


def print_warn(msg):
    print(f"[WARN] {msg}")


def print_error(msg):
    print(f"[ERROR] {msg}")


def install_spacy_model():
    """Download spaCy English model (en_core_web_sm)."""
    print_step(f"Checking spaCy model: {SPACY_MODEL}...")

    # Check if already installed
    try:
        import spacy
        nlp = spacy.load(SPACY_MODEL)
        print_success(f"spaCy {SPACY_MODEL} already installed (v{nlp.meta.get('version', '?')})")
        return True
    except (ImportError, OSError):
        pass

    print_step(f"Downloading spaCy model: {SPACY_MODEL}...")
    print_step("This may take a minute...")

    cmd = [sys.executable, "-m", "spacy", "download", SPACY_MODEL]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # Try en_core_web_md as fallback
            print_warn(f"{SPACY_MODEL} download failed, trying en_core_web_md...")
            cmd2 = [sys.executable, "-m", "spacy", "download", "en_core_web_md"]
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=300)
            if result2.returncode != 0:
                print_error(f"spaCy model download failed:\n{result2.stderr[-500:]}")
                return False
            print_success("spaCy en_core_web_md downloaded (fallback)")
            return True
        print_success(f"spaCy {SPACY_MODEL} downloaded")
        return True
    except subprocess.TimeoutExpired:
        print_error("spaCy model download timed out (5 min limit)")
        return False
    except Exception as e:
        print_error(f"Failed to download model: {e}")
        return False


def install_nltk_data(offline_dir=None):
    """Download all required NLTK data packages.

    v6.1.9: The project bundles all 8 NLTK data ZIP packages in nltk_data/
    directory (organized by category: tokenizers/, taggers/, corpora/).
    When --offline is passed, checks both the specified dir AND the project's
    bundled nltk_data/ directory. The bundled ZIPs are the primary offline source.
    """
    print_step("Setting up NLTK data...")

    # Handle SSL certificate issues (common on macOS)
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    try:
        import nltk
    except ImportError:
        print_error("NLTK is not installed. Run: pip install nltk")
        return False

    # v6.1.9: Ensure the project's bundled nltk_data/ is on the NLTK search path
    project_nltk_dir = Path(__file__).parent / 'nltk_data'
    if project_nltk_dir.is_dir():
        os.environ['NLTK_DATA'] = str(project_nltk_dir)
        if str(project_nltk_dir) not in nltk.data.path:
            nltk.data.path.insert(0, str(project_nltk_dir))
        print_step(f"Using bundled nltk_data/ at: {project_nltk_dir}")

    success_count = 0
    fail_count = 0

    for name, find_path in REQUIRED_NLTK_DATA:
        # Check if already installed
        try:
            nltk.data.find(find_path)
            print_success(f"  {name} - already installed")
            success_count += 1
            continue
        except LookupError:
            pass

        # v6.1.9: Try extracting from project's bundled nltk_data/ ZIPs
        if project_nltk_dir.is_dir():
            parts = find_path.split('/')
            if len(parts) == 2:
                bundled_zip = project_nltk_dir / parts[0] / f"{name}.zip"
                extract_dir = project_nltk_dir / parts[0] / name
                if bundled_zip.exists() and not extract_dir.is_dir():
                    try:
                        with zipfile.ZipFile(str(bundled_zip), 'r') as zf:
                            zf.extractall(str(project_nltk_dir / parts[0]))
                        if extract_dir.is_dir():
                            print_success(f"  {name} - extracted from bundled ZIP")
                            success_count += 1
                            continue
                    except Exception as e:
                        print_warn(f"  {name} - bundled ZIP extraction failed: {e}")

        # Try offline first if directory provided
        if offline_dir:
            offline_path = Path(offline_dir)
            # Check for zip file
            zip_file = offline_path / f"{name}.zip"
            if zip_file.exists():
                try:
                    _install_nltk_from_zip(name, zip_file, find_path)
                    print_success(f"  {name} - installed from offline package")
                    success_count += 1
                    continue
                except Exception as e:
                    print_warn(f"  {name} - offline install failed: {e}")

        # Download online
        print_step(f"  Downloading {name}...")
        try:
            nltk.download(name, quiet=True)
            # Verify it actually installed
            try:
                nltk.data.find(find_path)
                print_success(f"  {name} - downloaded")
                success_count += 1
            except LookupError:
                # Download succeeded but data not found — may need extraction
                _fix_nltk_zip(name, find_path)
                try:
                    nltk.data.find(find_path)
                    print_success(f"  {name} - downloaded and extracted")
                    success_count += 1
                except LookupError:
                    print_warn(f"  {name} - downloaded but not found at {find_path}")
                    fail_count += 1
        except Exception as e:
            print_error(f"  {name} - download failed: {e}")
            fail_count += 1

    print()
    if fail_count == 0:
        print_success(f"All {success_count} NLTK data packages ready")
        return True
    else:
        print_warn(f"{success_count} installed, {fail_count} failed")
        return fail_count == 0


def _fix_nltk_zip(name, find_path):
    """Fix NLTK data that was downloaded as zip but not extracted."""
    import nltk
    # Determine the expected directory
    for search_path in nltk.data.path:
        search_dir = Path(search_path)
        # find_path is like 'corpora/wordnet' — split to get category and name
        parts = find_path.split('/')
        if len(parts) == 2:
            category_dir = search_dir / parts[0]
            data_dir = category_dir / parts[1]
            zip_file = category_dir / f"{name}.zip"

            if zip_file.exists() and not data_dir.exists():
                try:
                    with zipfile.ZipFile(str(zip_file), 'r') as zf:
                        zf.extractall(str(category_dir))
                    return True
                except Exception:
                    pass
    return False


def _install_nltk_from_zip(name, zip_path, find_path):
    """Install NLTK data from an offline zip file."""
    import nltk
    # Use first writable nltk data path
    target_dir = None
    for p in nltk.data.path:
        if os.path.isdir(p) and os.access(p, os.W_OK):
            target_dir = Path(p)
            break
    if not target_dir:
        target_dir = Path.home() / 'nltk_data'
        target_dir.mkdir(parents=True, exist_ok=True)

    parts = find_path.split('/')
    if len(parts) == 2:
        category_dir = target_dir / parts[0]
        category_dir.mkdir(parents=True, exist_ok=True)

        # Copy zip
        import shutil
        dest_zip = category_dir / f"{name}.zip"
        shutil.copy2(str(zip_path), str(dest_zip))

        # Extract
        with zipfile.ZipFile(str(dest_zip), 'r') as zf:
            zf.extractall(str(category_dir))


def verify_installation():
    """Verify all NLP models are working."""
    print_header("Verifying NLP Installation")

    errors = []
    total = 0

    # Test spaCy
    total += 1
    print_step("Testing spaCy model...")
    try:
        import spacy
        # Try en_core_web_sm first, then fallbacks
        nlp = None
        for model in [SPACY_MODEL, 'en_core_web_md', 'en_core_web_lg']:
            try:
                nlp = spacy.load(model)
                doc = nlp("This is a test sentence.")
                print_success(f"spaCy working (model: {model}, v{nlp.meta.get('version', '?')})")
                break
            except OSError:
                continue
        if nlp is None:
            print_error("No spaCy English model found")
            errors.append("spaCy model")
    except ImportError:
        print_error("spaCy not installed")
        errors.append("spaCy")

    # Test each NLTK dataset
    try:
        import nltk
        for name, find_path in REQUIRED_NLTK_DATA:
            total += 1
            try:
                nltk.data.find(find_path)
                print_success(f"NLTK {name}")
            except LookupError:
                print_error(f"NLTK {name} - MISSING")
                errors.append(f"nltk/{name}")
    except ImportError:
        print_error("NLTK not installed")
        errors.append("NLTK")

    # Test NLTK WordNet actually works
    total += 1
    print_step("Testing NLTK WordNet lookup...")
    try:
        from nltk.corpus import wordnet
        synsets = wordnet.synsets("test")
        print_success(f"NLTK WordNet working ({len(synsets)} synsets for 'test')")
    except Exception as e:
        print_error(f"NLTK WordNet lookup failed: {e}")
        errors.append("WordNet lookup")

    # Test SymSpell
    total += 1
    try:
        from symspellpy import SymSpell
        print_success("SymSpell available")
    except Exception:
        print_warn("SymSpell not available (optional)")

    # Test textstat
    total += 1
    try:
        import textstat
        score = textstat.flesch_reading_ease("This is a test.")
        print_success(f"textstat working (Flesch score: {score})")
    except Exception:
        print_warn("textstat not available (optional)")

    print()
    ok = len(errors) == 0
    if ok:
        print_success(f"All NLP components verified ({total} checks passed)")
    else:
        print_error(f"{len(errors)} component(s) failed: {', '.join(errors)}")

    return ok


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AEGIS NLP Model Installer')
    parser.add_argument('--verify', action='store_true', help='Only verify installation')
    parser.add_argument('--offline', type=str, nargs='?', const='nltk_data',
                        help='Use offline NLTK data from specified directory')
    args = parser.parse_args()

    print_header("AEGIS - NLP Model Installer v5.9.25")
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print()

    if args.verify:
        ok = verify_installation()
        sys.exit(0 if ok else 1)

    # Install spaCy model
    print_header("Step 1: spaCy English Model")
    spacy_ok = install_spacy_model()

    # Install NLTK data
    print_header("Step 2: NLTK Data Packages")
    nltk_ok = install_nltk_data(offline_dir=args.offline)

    # Verify
    print_header("Step 3: Verification")
    all_ok = verify_installation()

    if all_ok:
        print_header("Installation Complete!")
        print("All NLP components installed successfully.")
        print("AEGIS health check should now show 7/7 models available.")
    else:
        print_header("Installation Completed with Warnings")
        print("Some components may not be working correctly.")
        print("Check the errors above for details.")
        if not spacy_ok:
            print(f"\nTo install spaCy model manually:")
            print(f"  python -m spacy download {SPACY_MODEL}")
        if not nltk_ok:
            print("\nTo install NLTK data manually:")
            print('  python -c "import nltk; nltk.download(\'punkt\'); nltk.download(\'punkt_tab\'); '
                  'nltk.download(\'averaged_perceptron_tagger\'); nltk.download(\'averaged_perceptron_tagger_eng\'); '
                  'nltk.download(\'stopwords\'); nltk.download(\'wordnet\')"')

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
