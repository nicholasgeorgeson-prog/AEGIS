#!/usr/bin/env python3
"""
AEGIS Repair Tool v5.9.27 - Single-Script Diagnose & Fix
=========================================================
Usage:
  python\python.exe repair_aegis.py

No .bat wrapper needed. This script handles everything:
  0. Pre-flight: fix setuptools v82 (removed pkg_resources) via subprocess
  1. Environment check
  2. Diagnose all imports (shows actual errors)
  3. Repair failed packages
  4. NLTK data check
  5. Final verification
"""

import subprocess
import sys
import os
import importlib
import glob

# Enable ANSI colors on Windows 10+
try:
    os.system('')
except Exception:
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
    print(f'  {"-" * 55}')


# ============================================================
# Package definitions
# ============================================================
CRITICAL_PACKAGES = [
    # (import_name, pip_name, description)
    ('pkg_resources', 'setuptools', 'Package Resources (setuptools)'),
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

SPACY_CHAIN = ['colorama', 'typer', 'cymem', 'murmurhash', 'preshed', 'blis',
               'srsly', 'thinc', 'wasabi', 'weasel', 'catalogue', 'confection',
               'spacy']

DIAGNOSTIC_GROUPS = {
    'Core Framework': [('flask',), ('waitress',)],
    'Document Processing': [('docx',), ('mammoth',), ('lxml',), ('openpyxl',)],
    'PDF Processing': [('fitz',), ('pdfplumber',)],
    'Platform Dependencies': [('pkg_resources',), ('colorama',), ('typer',)],
    'spaCy Dependency Chain': [('cymem',), ('murmurhash',), ('preshed',),
                                ('blis',), ('srsly',), ('thinc',), ('spacy',)],
    'NLP Libraries': [('sklearn',), ('nltk',), ('textstat',), ('textblob',),
                      ('rapidfuzz',), ('symspellpy',)],
    'Data Libraries': [('pandas',), ('numpy',), ('requests',), ('reportlab',)],
}


# ============================================================
# Utility functions
# ============================================================

def find_install_dir():
    """Find the AEGIS installation directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, 'app.py')):
        return script_dir

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

    return script_dir


def find_wheels_dirs(install_dir):
    """Find ALL wheels directories (there may be more than one)."""
    dirs = []
    for sub in ['wheels', 'packaging/wheels', 'packaging']:
        path = os.path.join(install_dir, sub)
        if os.path.isdir(path):
            dirs.append(path)
    return dirs


def pip_install(packages, wheels_dirs=None, force=False):
    """Install packages via pip. Offline-first with online fallback.

    wheels_dirs can be a single path string or a list of paths.
    All directories are passed as --find-links so pip searches all of them.
    """
    if isinstance(packages, str):
        packages = [packages]
    if isinstance(wheels_dirs, str):
        wheels_dirs = [wheels_dirs]

    cmd = [sys.executable, '-m', 'pip', 'install', '--no-warn-script-location']
    if force:
        cmd.append('--force-reinstall')

    # Build --find-links flags for all wheel directories
    find_links = []
    if wheels_dirs:
        for d in wheels_dirs:
            find_links.extend(['--find-links', d])

    # Try offline first (all wheel dirs)
    if find_links:
        offline_cmd = cmd + ['--no-index'] + find_links + packages
        result = subprocess.run(offline_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return True, 'offline'

        # Try hybrid (wheels + online)
        hybrid_cmd = cmd + find_links + packages
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
    """Try importing a module. Returns (success, error_message).

    Uses subprocess for packages known to have reimport issues
    (torch, requests_negotiate_sspi) to avoid false failures.
    """
    # Packages that break when reimported in-process
    SUBPROCESS_CHECK = {'torch', 'requests_negotiate_sspi'}
    if module_name in SUBPROCESS_CHECK:
        result = subprocess.run(
            [sys.executable, '-c', f'import {module_name}'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return True, None
        err = result.stderr.strip().split('\n')[-1] if result.stderr else 'import failed'
        return False, err

    try:
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


# ============================================================
# PHASE 0: Pre-flight setuptools fix (runs BEFORE anything imports)
# ============================================================

def preflight_setuptools(wheels_dirs):
    """Fix setuptools v82+ which removed pkg_resources.

    This runs as a subprocess so it takes effect for THIS process
    when we later try to import pkg_resources.

    setuptools v82.0 (Feb 2026) completely removed pkg_resources.
    spaCy model loading requires pkg_resources. The fix is to
    force-downgrade to setuptools<81 which still has it.

    wheels_dirs: list of paths to search for wheel files.
    """
    header('[Phase 0] Pre-flight: setuptools / pkg_resources')
    print()

    # Test if pkg_resources works
    result = subprocess.run(
        [sys.executable, '-c', 'import pkg_resources'],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        ok('pkg_resources available')
        return

    # It's broken - check what version of setuptools is installed
    ver_result = subprocess.run(
        [sys.executable, '-c',
         'try:\n import setuptools; print(setuptools.__version__)\nexcept: print("none")'],
        capture_output=True, text=True
    )
    st_ver = ver_result.stdout.strip() if ver_result.returncode == 0 else 'unknown'
    warn(f'pkg_resources missing! setuptools version: {st_ver}')

    if st_ver != 'none' and st_ver != 'unknown':
        try:
            major = int(st_ver.split('.')[0])
            if major >= 81:
                info(f'setuptools {st_ver} removed pkg_resources (v82+ breaking change)')
                info('Downgrading to setuptools<81 which still includes it...')
        except ValueError:
            pass

    # Build --find-links for all wheel directories
    find_links = []
    if wheels_dirs:
        for d in wheels_dirs:
            find_links.extend(['--find-links', d])

    # Method 1: Force-reinstall setuptools<81 from wheels
    if find_links:
        info(f'Trying offline install from {len(wheels_dirs)} wheel dir(s)...')
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--force-reinstall',
             '--no-index'] + find_links +
            ['--no-warn-script-location', 'setuptools<81'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            # Verify it worked
            verify = subprocess.run(
                [sys.executable, '-c', 'import pkg_resources; print("OK")'],
                capture_output=True, text=True
            )
            if verify.returncode == 0:
                ok('setuptools downgraded - pkg_resources now available')
                return
            else:
                warn('pip said success but pkg_resources still fails')

        # Method 2: Try installing the wheel file directly
        for wd in (wheels_dirs or []):
            for whl in sorted(glob.glob(os.path.join(wd, 'setuptools-[0-7]*.whl')),
                             reverse=True):
                info(f'Trying direct wheel: {os.path.basename(whl)}')
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--force-reinstall',
                     '--no-warn-script-location', whl],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    verify = subprocess.run(
                        [sys.executable, '-c', 'import pkg_resources; print("OK")'],
                        capture_output=True, text=True
                    )
                    if verify.returncode == 0:
                        ok('setuptools installed from wheel - pkg_resources available')
                        return

    # Method 3: Online fallback
    info('Trying online install: setuptools<81...')
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--force-reinstall',
         '--no-warn-script-location', 'setuptools<81'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        verify = subprocess.run(
            [sys.executable, '-c', 'import pkg_resources; print("OK")'],
            capture_output=True, text=True
        )
        if verify.returncode == 0:
            ok('setuptools installed online - pkg_resources available')
            return

    # All methods failed
    fail('Could not fix pkg_resources!')
    warn('spaCy model loading will fail. You may need to manually run:')
    warn(f'  {sys.executable} -m pip install "setuptools<81"')
    print()


# ============================================================
# Main repair flow
# ============================================================

def main():
    print()
    print(f'  {"=" * 56}')
    print()
    print(f'      {BOLD}AEGIS Repair Tool v5.9.27{RESET}')
    print(f'      Single-Script Diagnose & Fix')
    print()
    print(f'  {"=" * 56}')

    install_dir = find_install_dir()
    wheels_dirs = find_wheels_dirs(install_dir)

    # ============================================================
    # PHASE 0: Pre-flight setuptools fix (BEFORE any imports)
    # ============================================================
    preflight_setuptools(wheels_dirs)

    # ============================================================
    # PHASE 1: Environment
    # ============================================================
    header('[Phase 1] Environment Check')
    print()
    info(f'Python: {sys.version}')
    info(f'Executable: {sys.executable}')
    info(f'Install dir: {install_dir}')

    sp = [p for p in sys.path if 'site-packages' in p]
    if sp:
        ok(f'site-packages on path: {sp[0]}')
    else:
        fail('site-packages NOT on sys.path!')
        warn('Check python310._pth file has "import site" uncommented.')

    if wheels_dirs:
        for wd in wheels_dirs:
            ok(f'Wheels directory: {wd}')
    else:
        warn('No wheels directory found. Will try online install only.')

    # ============================================================
    # PHASE 2: Diagnose
    # ============================================================
    header('[Phase 2] Diagnosing package imports')
    print()

    failed = []  # list of (pip_name, error_msg)
    passed = 0
    pkg_lookup = {p[0]: p for p in CRITICAL_PACKAGES}

    for group_name, group_imports in DIAGNOSTIC_GROUPS.items():
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
    optional_failed = []  # track separately
    print('  --- Optional Packages ---')
    for imp, pip_name, desc in OPTIONAL_PACKAGES:
        success, err = check_import(imp)
        if success:
            ok(desc)
            passed += 1
        else:
            fail(f'{desc} ({pip_name}) — optional but recommended')
            print(f'         {RED}Error: {err}{RESET}')
            optional_failed.append((pip_name, err))
    print()

    print(f'  Results: {GREEN}{passed} passed{RESET}, {RED}{len(failed)} failed{RESET}')
    print()

    if not failed and not optional_failed:
        print(f'  {GREEN}{BOLD}All packages are working! No repairs needed.{RESET}')
        check_nltk_data()
        final_summary(0)
        return

    # ============================================================
    # PHASE 3: Repair
    # ============================================================
    total_to_fix = len(failed) + len(optional_failed)
    header(f'[Phase 3] Repairing {total_to_fix} failed package(s)')
    print()

    failed_names = [name for name, _ in failed]
    optional_names = [name for name, _ in optional_failed]
    all_names = failed_names + optional_names
    print(f'  Critical: {", ".join(failed_names) if failed_names else "none"}')
    print(f'  Optional: {", ".join(optional_names) if optional_names else "none"}')
    print()

    repaired = 0

    # Step 3a: Fix setuptools if still broken after pre-flight
    if 'setuptools' in failed_names:
        info('setuptools v82+ removed pkg_resources — downgrading to v80...')
        success, method = pip_install(['setuptools<81'], wheels_dirs, force=True)
        if success:
            ok(f'setuptools downgraded ({method})')
            repaired += 1
        else:
            fail(f'setuptools downgrade failed: {method}')
        print()

    # Step 3b: Install colorama/typer if needed
    other_priority = []
    if 'colorama' in failed_names:
        other_priority.append('colorama')
    if 'typer' in failed_names:
        other_priority.append('typer')
    if other_priority:
        info(f'Installing: {", ".join(other_priority)}...')
        success, method = pip_install(other_priority, wheels_dirs)
        if success:
            ok(f'Installed ({method})')
            repaired += len(other_priority)
        else:
            fail(f'Install failed: {method}')
        print()

    # Step 3c: If spaCy or any C dep failed, reinstall whole chain
    spacy_deps_failed = [n for n in failed_names if n.lower() in
                         ['spacy', 'typer', 'cymem', 'murmurhash', 'preshed',
                          'blis', 'srsly', 'thinc']]
    if spacy_deps_failed:
        info('Reinstalling spaCy + ALL C dependencies together...')
        success, method = pip_install(SPACY_CHAIN, wheels_dirs, force=True)
        if success:
            ok(f'spaCy chain installed ({method})')
            repaired += 1
        else:
            fail(f'spaCy chain install failed')
            print(f'         {RED}{method}{RESET}')
        print()

    # Step 3d: Repair remaining packages individually
    skip_names = {'setuptools', 'colorama', 'typer', 'spacy', 'cymem',
                  'murmurhash', 'preshed', 'blis', 'srsly', 'thinc',
                  'en_core_web_sm'}
    for pip_name, _ in failed:
        if pip_name.lower() in skip_names:
            continue
        info(f'Reinstalling {pip_name}...')
        success, method = pip_install(pip_name, wheels_dirs, force=True)
        if success:
            ok(f'{pip_name} installed ({method})')
            repaired += 1
        else:
            fail(f'{pip_name} install failed: {method}')
        print()

    # Step 3e: en_core_web_sm model
    if 'en_core_web_sm' in failed_names:
        info('Reinstalling spaCy English model...')
        sm_installed = False
        if wheels_dirs:
            for wd in wheels_dirs:
                sm_wheels = glob.glob(os.path.join(wd, 'en_core_web_sm*.whl'))
                for whl in sm_wheels:
                    info(f'Installing from wheel: {os.path.basename(whl)}')
                    success, method = pip_install(whl, wheels_dirs, force=True)
                    if success:
                        ok('en_core_web_sm installed from wheel')
                        sm_installed = True
                        repaired += 1
                        break
                if sm_installed:
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

    # Step 3f: Optional packages
    if optional_failed:
        print('  --- Optional Packages ---')
        optional_names_set = {name for name, _ in optional_failed}

        # Install sspilib first if Windows auth packages need it
        if 'requests-ntlm' in optional_names_set or 'requests-negotiate-sspi' in optional_names_set:
            info('Installing sspilib (required by pyspnego/requests-ntlm on Windows)...')
            success, method = pip_install('sspilib', wheels_dirs)
            if success:
                ok(f'sspilib installed ({method})')
            else:
                warn(f'sspilib not available — Windows auth packages may fail')
            print()

        for pip_name, _ in optional_failed:
            info(f'Installing {pip_name}...')
            success, method = pip_install(pip_name, wheels_dirs, force=True)
            if success:
                ok(f'{pip_name} installed ({method})')
                repaired += 1
            else:
                warn(f'{pip_name} not available ({method})')
                warn(f'  This is optional — AEGIS will work without it.')
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

    # spaCy model — test via subprocess to get clean import state
    info('Testing spaCy model in clean subprocess...')
    model_result = subprocess.run(
        [sys.executable, '-c',
         'import spacy; nlp=spacy.load("en_core_web_sm"); '
         'print("OK:" + nlp.meta.get("version", "?"))'],
        capture_output=True, text=True
    )
    if model_result.returncode == 0 and model_result.stdout.strip().startswith('OK:'):
        ver = model_result.stdout.strip().split(':')[1]
        ok(f'spaCy en_core_web_sm model ({ver})')
        final_pass += 1
    else:
        err_msg = model_result.stderr.strip().split('\n')[-1] if model_result.stderr else 'unknown'
        fail(f'spaCy en_core_web_sm model')
        print(f'         {RED}Error: {err_msg}{RESET}')
        final_fail += 1

    print()
    print('  --- Optional ---')
    optional_still_broken = 0
    for imp, pip_name, desc in OPTIONAL_PACKAGES:
        success, err = check_import(imp)
        if success:
            ok(f'{desc}')
            final_pass += 1
        else:
            warn(f'{desc} — not available')
            optional_still_broken += 1

    final_summary(final_fail, optional_still_broken)


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
            except Exception:
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
    except Exception:
        pass


def final_summary(fail_count, optional_missing=0):
    """Print final summary."""
    print()
    print(f'  {"=" * 56}')
    print()
    print(f'      {BOLD}Repair Complete{RESET}')
    print()
    if fail_count > 0:
        print(f'      {RED}FAILED: {fail_count} critical package(s) still broken{RESET}')
        if optional_missing > 0:
            print(f'      {YELLOW}OPTIONAL: {optional_missing} optional package(s) not available{RESET}')
        print()
        print(f'      The error messages above show exactly why.')
        print(f'      Common fixes:')
        print()
        print(f'      1. Missing wheel: Download the .whl file and')
        print(f'         place it in the wheels folder, re-run.')
        print(f'      2. DLL error: Install Visual C++ Redistributable.')
        print(f'      3. Corrupted: Delete python\\Lib\\site-packages')
        print(f'         and re-run the full OneClick installer.')
    elif optional_missing > 0:
        print(f'      {GREEN}{BOLD}All critical packages are working!{RESET}')
        print()
        print(f'      {YELLOW}{optional_missing} optional package(s) not available.{RESET}')
        print(f'      AEGIS works fine without these. To install them,')
        print(f'      download their .whl files into the wheels folder')
        print(f'      and re-run this tool.')
    else:
        print(f'      {GREEN}{BOLD}All packages are working!{RESET}')
    print()
    print(f'  {"=" * 56}')
    print()
    input('  Press Enter to exit...')


if __name__ == '__main__':
    main()
