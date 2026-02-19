@echo off
title AEGIS v5.9.28 Update Puller
echo.
echo  ============================================
echo    AEGIS v5.9.28 Update Puller
echo  ============================================
echo.

:: Try to find Python
set "PYTHON_EXE="

:: 1. Check if AEGIS embedded Python exists (same directory)
if exist "%~dp0python\python.exe" (
    set "PYTHON_EXE=%~dp0python\python.exe"
    echo  Found AEGIS Python: %~dp0python\python.exe
    goto :found_python
)

:: 2. Check parent directory (if script is inside AEGIS folder)
if exist "%~dp0..\python\python.exe" (
    set "PYTHON_EXE=%~dp0..\python\python.exe"
    echo  Found AEGIS Python: %~dp0..\python\python.exe
    goto :found_python
)

:: 3. Check system Python
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    echo  Found system Python
    goto :found_python
)

where python3 >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python3"
    echo  Found system Python3
    goto :found_python
)

:: 4. Common install locations
if exist "C:\Python310\python.exe" (
    set "PYTHON_EXE=C:\Python310\python.exe"
    echo  Found Python at C:\Python310
    goto :found_python
)
if exist "C:\Python39\python.exe" (
    set "PYTHON_EXE=C:\Python39\python.exe"
    echo  Found Python at C:\Python39
    goto :found_python
)

echo  [ERROR] Could not find Python!
echo.
echo  Please place this file in your AEGIS installation directory
echo  (where the "python" folder is), or install Python and add
echo  it to your PATH.
echo.
pause
exit /b 1

:found_python
echo.

:: Run the pull script inline (no separate .py file needed)
"%PYTHON_EXE%" -c "
import urllib.request, ssl, json, os, sys

REPO = 'nicholasgeorgeson-prog/AEGIS'
BRANCH = 'main'
OUTPUT_DIR = 'updates_v5.9.28'

FILES = [
    'version.json', 'static/version.json', 'core.py', 'config_logging.py',
    'report_generator.py', 'graph_export_html.py', 'adjudication_export.py',
    'routes/roles_routes.py', 'routes/data_routes.py', 'routes/config_routes.py',
    'routes/review_routes.py', 'nlp/spelling/checker.py', 'dictionaries/defense.txt',
    'templates/index.html', 'static/js/app.js', 'static/js/roles-tabs-fix.js',
    'static/js/help-docs.js', 'static/js/features/hyperlink-validator.js',
    'static/js/features/hyperlink-validator-state.js', 'static/js/features/landing-page.js',
    'static/js/features/document-viewer.js', 'static/js/features/scan-progress-dashboard.js',
    'static/css/features/sow-generator.css', 'static/css/features/landing-page.css',
    'static/css/features/metrics-analytics.css', 'static/css/features/scan-progress-dashboard.css',
]

def get_ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError: pass
    try:
        ctx = ssl.create_default_context()
        urllib.request.urlopen(urllib.request.Request('https://github.com'), context=ctx, timeout=5)
        return ctx
    except Exception: pass
    print('  [WARN] SSL certs unavailable - using unverified HTTPS')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

print(f'AEGIS v5.9.28 Update Puller')
print('=' * 50)
print(f'Repo:   {REPO}')
print(f'Branch: {BRANCH}')
print(f'Output: {OUTPUT_DIR}/')
print(f'Files:  {len(FILES)}')
print()
print('Setting up SSL...')
ssl_ctx = get_ssl_ctx()
print()
os.makedirs(OUTPUT_DIR, exist_ok=True)
print('Downloading files...')
ok = fail = 0
for fp in FILES:
    url = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/{fp}'
    dest = os.path.join(OUTPUT_DIR, fp)
    dd = os.path.dirname(dest)
    if dd: os.makedirs(dd, exist_ok=True)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            data = resp.read()
        with open(dest, 'wb') as f: f.write(data)
        print(f'  OK  {fp} ({len(data)/1024:.1f} KB)')
        ok += 1
    except Exception as e:
        print(f'  FAIL {fp} -- {e}')
        fail += 1
print()
print('=' * 50)
print(f'Complete: {ok} downloaded, {fail} failed')
print()
if fail == 0:
    print('All files downloaded successfully!')
    print()
    print('NEXT STEPS:')
    print(f'  1. Stop AEGIS (Ctrl+C or close terminal)')
    print(f'  2. Copy all files from {OUTPUT_DIR}/ into your AEGIS install directory')
    print(f'     (overwrite existing files, preserve folder structure)')
    print(f'  3. Restart AEGIS with Start_AEGIS.bat')
else:
    print(f'WARNING: {fail} file(s) failed. Check internet and retry.')
sys.exit(0 if fail == 0 else 1)
"

echo.
if errorlevel 1 (
    echo  [ERROR] Download had failures. See above for details.
) else (
    echo  Done! Your updates are in the updates_v5.9.28 folder.
)
echo.
pause
