#!/usr/bin/env python3
"""
AEGIS Repair Tool - Diagnose & Fix Missing Dependencies
Run via Repair_AEGIS.bat or directly: python repair_aegis.py

Phases:
  1. Environment check (._pth, sys.path)
  2. Diagnose all imports (shows actual errors)
  3. Repair failed packages
  4. NLTK data check
  5. Final verification
"""

import subprocess
import sys
import os
import importlib
import traceback

# ANSI colors (colorama not guaranteed available yet)
try:
    os.system('')  # Enable ANSI on Windows 10+
except:
    pass

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def ok(msg):
    print(f'  {GREEN}[OK]{RESET} {msg}')

def fail(msg):
    print(f'  {RED}[FAIL]{RESET} {msg}')

def warn(msg):
    print(f'  {YELLOW}[WARN]{RESET} {msg}')

def skip(msg):
    print(f'  {YELLOW}[SKIP]{RESET} {msg}')

def info(msg):
    print(f'  {CYAN}[INFO]{RESET} {msg}')

def header(msg):
    print(f'\n  {BOLD}{msg}{RESET}')
    print(f'  {"-" * 51}')


# ============================================================
# Package definitions
# ============================================================
CRITICAL_PACKAGES = [
    # (import_name, pip_name, description)
    ('flask', 'flask', 'Core Web Framework'),
    ('waitress', 'waitress', 'Production Server'),
    ('docx', 'python-docx', 'Word Document Processing'),
    ('mammoth', 'mammoth', 'DOCX-to-HTML Conversion'),
    ('lxml', 'lxml', 'XML Processing'),
    ('openpyxl', 'openpyxl', 'Excel Processing'),
    ('fitz', 'PyMuPDF', 'PDF Text Extraction'),
    ('pdfplumber', 'pdfplumber', 'PDF Table Extraction'),
    ('colorama', 'colorama', 'Terminal Colors (Windows)'),
    ('typer', 'typer', 'CLI Framework (spaCy dep)'),
    ('cymem', 'cymem', 'spaCy: Memory Management'),
    ('murmurhash', 'murmurhash', 'spaCy: Hash Functions'),
    ('preshed', 'preshed', 'spaCy: Pre-hashed Data'),
    ('blis', 'blis', 'spaCy: Linear Algebra'),
    ('srsly', 'srsly', 'spaCy: Serialization'),
    ('thinc', 'thinc', 'spaCy: ML Framework'),
    ('spacy', 'spacy', 'NLP Engine'),
    ('sklearn', 'scikit-learn', 'ML/Clustering'),
    ('nltk', 'nltk', 'Text Processing'),
    ('textstat', 'textstat', 'Readability Metrics'),
    ('textblob', 'textblob', 'Sentiment Analysis'),
    ('rapidfuzz', 'rapidfuzz', 'Fuzzy Matching'),
    ('symspellpy', 'symspellpy', 'Spell Checking'),
    ('pandas', 'pandas', 'Data Analysis'),
    ('numpy', 'numpy', 'Numerical Computing'),
    ('requests', 'requests', 'HTTP Client'),
    ('reportlab', 'reportlab', 'PDF Report Generation'),
]

OPTIONAL_PACKAGES = [
    ('torch', 'torch', 'AI/Deep Learning'),
    ('docling', 'docling', 'AI Document Extraction'),
    ('requests_negotiate_sspi', 'requests-negotiate-sspi', 'Windows SSO'),
    ('requests_ntlm', 'requests-ntlm', 'Windows Domain Auth'),
]

SPACY_CHAIN = ['colorama', 'typer', 'cymem', 'murmurhash', 'preshed', 'blis', 'srsly',
               'thinc', 'wasabi', 'weasel', 'catalogue', 'confection', 'spacy']


def find_install_dir():
    """Find the AEGIS installation directory."""
    # Check script's own directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, 'app.py')):
        return script_dir

    # Check common locations
    home = os.path.expanduser('~')
    candidates = [
        r'C:\AEGIS',
        os.path.join(home, 'Desktop', 'AEGIS'),
        os.path.join(home, 'Desktop', 'Doc Review', 'AEGIS'),
        os.path.join(home, 'OneDrive', 'Desktop', 'AEGIS'),
        os.path.join(home, 'OneDrive', 'Desktop', 'Doc Review', 'AEGIS'),
        os.path.join(home, 'OneDrive - NGC', 'Desktop', 'AEGIS'),
        os.path.join(home, 'OneDrive - NGC', 'Desktop', 'Doc Review', 'AEGIS'),
    ]
    for d in candidates:
        if os.path.exists(os.path.join(d, 'app.py')):
            return d

    return script_dir  # fallback


def find_wheels_dir(install_dir):
    """Find the wheels directory."""
    for sub in ['packaging/wheels', 'wheels']:
        path = os.path.join(install_dir, sub)
        if os.path.isdir(path):
            return path
    return None


def pip_install(packages, wheels_dir=None, force=False):
    """Install packages via pip. Offline-first with online fallback."""
    if isinstance(packages, str):
        packages = [packages]

    cmd = [sys.executable, '-m', 'pip', 'install', '--no-warn-script-location']
    if force:
        cmd.append('--force-reinstall')

    # Try offline first
    if wheels_dir:
        offline_cmd = cmd + ['--no-index', '--find-links', wheels_dir] + packages
        result = subprocess.run(offline_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, 'offline'

        # Try with online fallback (still use wheels as extra source)
        hybrid_cmd = cmd + ['--find-links', wheels_dir] + packages
        result = subprocess.run(hybrid_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, 'hybrid'

    # Try pure online
    online_cmd = cmd + packages
    result = subprocess.run(online_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return True, 'online'

    return False, result.stderr[-500:] if result.stderr else 'Unknown error'


def check_import(module_name):
    """Try importing a module. Returns (success, error_message)."""
    try:
        # Force reimport in case it was fixed during this run
        if module_name in sys.modules:
            del sys.modules[module_name]
        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        return False, str(e)


def check_spacy_model():
    """Check if en_core_web_sm loads."""
    try:
        if 'spacy' in sys.modules:
            del sys.modules['spacy']
        import spacy
        nlp = spacy.load('en_core_web_sm')
        return True, nlp.meta.get('version', '?')
    except Exception as e:
        return False, str(e)


def main():
    print()
    print(f'  {"=" * 56}')
    print()
    print(f'      {BOLD}AEGIS Repair Tool v5.9.26{RESET}')
    print(f'      Diagnose & Fix Missing Dependencies')
    print()
    print(f'  {"=" * 56}')

    install_dir = find_install_dir()
    wheels_dir = find_wheels_dir(install_dir)

    # ============================================================
    # PHASE 1: Environment
    # ============================================================
    header('[Phase 1] Environment Check')
    print()
    info(f'Python: {sys.version}')
    info(f'Executable: {sys.executable}')
    info(f'Install dir: {install_dir}')

    # Check site-packages on path
    sp = [p for p in sys.path if 'site-packages' in p]
    if sp:
        ok(f'site-packages on path: {sp[0]}')
    else:
        fail('site-packages NOT on sys.path!')
        warn('This means pip-installed packages cannot be found.')
        warn('Check python310._pth file has "import site" uncommented.')

    if wheels_dir:
        ok(f'Wheels directory: {wheels_dir}')
    else:
        warn('No wheels directory found. Will try online install only.')

    # ============================================================
    # PHASE 2: Diagnose
    # ============================================================
    header('[Phase 2] Diagnosing package imports')
    print()

    failed = []  # list of (pip_name, error_msg)
    passed = 0

    # Group display
    groups = {
        'Core Framework': [('flask',), ('waitress',)],
        'Document Processing': [('docx',), ('mammoth',), ('lxml',), ('openpyxl',)],
        'PDF Processing': [('fitz',), ('pdfplumber',)],
        'Platform Dependencies': [('colorama',), ('typer',)],
        'spaCy Dependency Chain': [('cymem',), ('murmurhash',), ('preshed',),
                                    ('blis',), ('srsly',), ('thinc',), ('spacy',)],
        'NLP Libraries': [('sklearn',), ('nltk',), ('textstat',), ('textblob',),
                          ('rapidfuzz',), ('symspellpy',)],
        'Data Libraries': [('pandas',), ('numpy',), ('requests',), ('reportlab',)],
    }

    pkg_lookup = {p[0]: p for p in CRITICAL_PACKAGES}

    for group_name, group_imports in groups.items():
        print(f'  --- {group_name} ---')
        for (imp_name,) in group_imports:
            pkg = pkg_lookup[imp_name]
            imp, pip_name, desc = pkg
            success, err = check_import(imp)
            if success:
                ok(desc)
                passed += 1
            else:
                fail(f'{desc} ({pip_name})')
                print(f'         {RED}Error: {err}{RESET}')
                failed.append((pip_name, err))
        print()

    # spaCy model
    print('  --- spaCy Model ---')
    model_ok, model_info = check_spacy_model()
    if model_ok:
        ok(f'en_core_web_sm ({model_info})')
        passed += 1
    else:
        fail('en_core_web_sm - spaCy English model')
        print(f'         {RED}Error: {model_info}{RESET}')
        failed.append(('en_core_web_sm', model_info))
    print()

    # Optional
    print('  --- Optional Packages ---')
    for imp, pip_name, desc in OPTIONAL_PACKAGES:
        success, err = check_import(imp)
        if success:
            ok(f'{desc}')
            passed += 1
        else:
            skip(f'{desc} (optional)')
    print()

    print(f'  Results: {GREEN}{passed} passed{RESET}, {RED}{len(failed)} failed{RESET}')
    print()

    if not failed:
        print(f'  {GREEN}{BOLD}All packages are working! No repairs needed.{RESET}')
        check_nltk_data()
        final_summary(0)
        return

    # ============================================================
    # PHASE 3: Repair
    # ============================================================
    header(f'[Phase 3] Repairing {len(failed)} failed package(s)')
    print()

    failed_names = [name for name, _ in failed]
    print(f'  Failed: {", ".join(failed_names)}')
    print()

    repaired = 0

    # Step 3a: Install colorama first (needed by spaCy and Flask)
    if 'colorama' in failed_names:
        info('Installing colorama first (required by spaCy/Flask on Windows)...')
        success, method = pip_install('colorama', wheels_dir)
        if success:
            ok(f'colorama installed ({method})')
            repaired += 1
        else:
            fail(f'colorama install failed: {method}')
        print()

    # Step 3b: If spaCy or any C dep failed, reinstall whole chain
    spacy_deps_failed = [n for n in failed_names if n.lower() in
                         ['spacy', 'typer', 'cymem', 'murmurhash', 'preshed', 'blis', 'srsly', 'thinc']]
    if spacy_deps_failed:
        info('Reinstalling spaCy + ALL C dependencies together...')
        info('(This ensures version compatibility across the chain)')
        success, method = pip_install(SPACY_CHAIN, wheels_dir, force=True)
        if success:
            ok(f'spaCy chain installed ({method})')
            repaired += 1
        else:
            fail(f'spaCy chain install failed')
            print(f'         {RED}{method}{RESET}')
        print()

    # Step 3c: Repair remaining packages individually
    skip_names = {'colorama', 'typer', 'spacy', 'cymem', 'murmurhash', 'preshed',
                  'blis', 'srsly', 'thinc', 'en_core_web_sm'}
    for pip_name, _ in failed:
        if pip_name.lower() in skip_names:
            continue
        info(f'Reinstalling {pip_name}...')
        success, method = pip_install(pip_name, wheels_dir, force=True)
        if success:
            ok(f'{pip_name} installed ({method})')
            repaired += 1
        else:
            fail(f'{pip_name} install failed: {method}')
        print()

    # Step 3d: en_core_web_sm
    if 'en_core_web_sm' in failed_names:
        info('Reinstalling spaCy English model...')
        # Try wheel first
        sm_installed = False
        if wheels_dir:
            import glob
            sm_wheels = glob.glob(os.path.join(wheels_dir, 'en_core_web_sm*.whl'))
            for whl in sm_wheels:
                info(f'Installing from wheel: {os.path.basename(whl)}')
                success, method = pip_install(whl, wheels_dir, force=True)
                if success:
                    ok('en_core_web_sm installed from wheel')
                    sm_installed = True
                    repaired += 1
                    break

        if not sm_installed:
            info('Downloading en_core_web_sm from internet...')
            result = subprocess.run(
                [sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                ok('en_core_web_sm downloaded')
                repaired += 1
            else:
                fail('en_core_web_sm download failed')
                if result.stderr:
                    print(f'         {RED}{result.stderr[-300:]}{RESET}')
        print()

    # ============================================================
    # PHASE 4: NLTK Data
    # ============================================================
    check_nltk_data()

    # ============================================================
    # PHASE 5: Final Verification
    # ============================================================
    header('[Phase 5] Final Verification')
    print()

    final_pass = 0
    final_fail = 0

    for imp, pip_name, desc in CRITICAL_PACKAGES:
        success, err = check_import(imp)
        if success:
            ok(desc)
            final_pass += 1
        else:
            fail(f'{desc} - STILL BROKEN')
            print(f'         {RED}Error: {err}{RESET}')
            final_fail += 1

    # spaCy model
    model_ok, model_info = check_spacy_model()
    if model_ok:
        ok(f'spaCy en_core_web_sm model ({model_info})')
        final_pass += 1
    else:
        fail('spaCy en_core_web_sm model')
        print(f'         {RED}Error: {model_info}{RESET}')
        final_fail += 1

    print()
    print('  --- Optional ---')
    for imp, pip_name, desc in OPTIONAL_PACKAGES:
        success, _ = check_import(imp)
        if success:
            ok(f'{desc} (optional)')
            final_pass += 1
        else:
            skip(f'{desc} (optional)')

    final_summary(final_fail)


def check_nltk_data():
    """Check and fix NLTK data."""
    header('[Phase 4] Checking NLTK data')
    print()

    try:
        import nltk
    except ImportError:
        warn('NLTK not available, skipping data check')
        return

    datasets = [
        ('corpora/wordnet', 'wordnet'),
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords'),
        ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng'),
        ('corpora/omw-1.4', 'omw-1.4'),
    ]

    for path, name in datasets:
        try:
            nltk.data.find(path)
            ok(name)
        except LookupError:
            warn(f'{name} missing - downloading...')
            try:
                import ssl
                ssl._create_default_https_context = ssl._create_unverified_context
            except:
                pass
            nltk.download(name, quiet=True)

    # Fix wordnet zip extraction bug
    try:
        import zipfile
        nltk_dir = os.path.join(os.path.expanduser('~'), 'nltk_data', 'corpora')
        zip_path = os.path.join(nltk_dir, 'wordnet.zip')
        dir_path = os.path.join(nltk_dir, 'wordnet')
        if os.path.exists(zip_path) and not os.path.isdir(dir_path):
            zipfile.ZipFile(zip_path).extractall(nltk_dir)
            ok('Extracted wordnet.zip')
    except:
        pass


def final_summary(fail_count):
    """Print final summary."""
    print()
    print(f'  {"=" * 56}')
    print()
    print(f'      {BOLD}Repair Complete{RESET}')
    print()
    if fail_count > 0:
        print(f'      {RED}FAILED: {fail_count} package(s) still broken{RESET}')
        print()
        print(f'      The error messages above show exactly why.')
        print(f'      Common fixes:')
        print()
        print(f'      1. Missing wheel: Download the .whl file and')
        print(f'         place it in the wheels folder, re-run.')
        print(f'      2. DLL error: Install Visual C++ Redistributable.')
        print(f'      3. Corrupted: Delete python\\Lib\\site-packages')
        print(f'         and re-run the full OneClick installer.')
    else:
        print(f'      {GREEN}{BOLD}All packages are working!{RESET}')
    print()
    print(f'  {"=" * 56}')
    print()
    input('  Press Enter to exit...')


if __name__ == '__main__':
    main()
