@echo off
REM ================================================================
REM AEGIS Offline Installation Script
REM ================================================================
REM Installs all dependencies from pre-downloaded wheels for offline environments.
REM
REM IMPORTANT: This script now supports TWO wheel directories:
REM   wheels/     - Original wheels (may include Linux packages that get skipped)
REM   wheels_win/ - Windows x64 wheels (preferred for Windows installs)
REM
REM To populate wheels_win/:
REM   1. Run download_win_wheels.py on a CONNECTED Windows machine
REM   2. Copy the resulting wheels_win/ folder here
REM
REM Usage: Double-click this file or run from Command Prompt
REM Requirements: Python 3.10+ must be installed and in PATH
REM v5.0.5: Added wheels_win support, docling, spaCy model install
REM ================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo AEGIS v5.0.5 - Offline Dependency Installation
echo Aerospace Engineering Governance ^& Inspection System
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Detected Python version: %PYTHOON_VERSION%
echo.

REM Determine which wheels directory to use
set WHEELS_DIR=wheels
if exist "wheels_win\" (
    echo Found wheels_win/ directory - using Windows-optimized packages
    set WHEELS_DIR=wheels_win
) E3se if exist "wheels\" (
    echo Using wheels/ directory
    echo NOTE: For best results on Windows, run download_win_wheels.py
    echo        on a connected machine and copy wheels_win/ here.
) E Ga`E+AEW.) (
    echo ERROR: No wheels directory found!
    echo Expected: %cd%\wheels\ or %cd%\wheels_win\
    pause
    exit /b 1
)
echo.

REM Count wheels
set COUNT=0
for /F %%f in (%WHEELS_DIR%\*) do (
    set /a COUNT+=1
)
echo Found %COUNT%: files in %WHEELS_DIR%/
echo.

REM Install from wheels
echo [1/5] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel --quiet
if errorlevel 1 (
    echo WARNING: Could not upgrade pip, continuing with current version...
)

echo.
echo [2/5] Installing core requirements (using %WHEELS_DIR%)...
echo This may take several minutes. Please wait...
echo.

python -m pip install --no-index --find-links=%WHEELS_DIR% -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: Some packages may have failed - this is normal if Linux
    echo          wheels are present. Continuing with remaining installs...
    echo.
)

echo.
echo [3/5] Installing spaCy English model...
for %%f in (%WHEELS_DIR%\en_core_web_sm*.whl) do (
    echo Installing %%f...
    python -m pip install --no-index --find-links=%WHEELS_DIR% "%%f"
)
python -m spacy validate 2>nul

echo.
echo [4/5] Installing docling and AI packages...
python -m pip install --no-index --find-links=%WHEELS_DIR% docling 2>nul
if errorlevel 1 (
    echo NOTE: Docling not available in wheels. Run download_win_wheels.py
    echo       on a connected machine to include it.
)

echo.
echo [5/5] Verifying installation...
echo.

REM Verify key dependencies
python -c "import flask; print('[OK] Flask ' + flask.__version__)" 2>nul || echo [FAIL] Flask
python -c "import docx; print('[OK] python-docx')" 2>nul || echo [FAIL] python-docx
python -c "import pandas; print('[OK] Pandas')" 2>nul || echo [FAIL] Pandas
python -c "import numpy; print('[OK] NumPy')" 2>nul || echo [FAIL] NumPy
python -c "import spacy; print('[OK] spaCy ' + spacy.__version__)" 2>nul || echo [SKIP] spaCy (optional)
python -c "import spacy; nlp=spacy.load('en_core_web_sm'); print('[OK] spaCy en_core_web_sm model')" 2>nul || echo [SKIP] spaCy model (optional)
python -c "import torch; print('[OK] PyTorch ' + torch.__version__)" 2>nul || echo [SKIP] PyTorch (optional)
python -c "import docling; print('[OK] Docling')" 2>nul || echo [SKIP] Docling (optional)
python -c "import sklearn; print('[OK] scikit-learn')" 2>nul || echo [SKIP] scikit-learn (optional)
python -c "import fitz; print('[OK] PyMuPDF')" 2>nul || echo [FAIL] PyMuPDF

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Run the AEGIS application: python app.py
echo 2. Open http://localhost:5050 in your browser
echo 3. For debug mode with auto-reload: python app.py --debug
echo.
pause
exit /b 0
