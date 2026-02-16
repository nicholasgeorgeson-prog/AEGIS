@echo off
REM AEGIS Offline Installation Script
REM Installs all dependencies from pre-downloaded wheels for offline environments
REM Usage: Double-click this file or run from Command Prompt
REM Requirements: Python 3.10+ must be installed and in PATH

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo AEGIS v4.6.2 - Offline Dependency Installation
echo Aerospace Engineering Governance & Inspection System
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
echo Detected Python version: %PYTHON_VERSION%
echo.

REM Check if wheels directory exists
if not exist "wheels\" (
    echo ERROR: wheels directory not found!
    echo Expected: %cd%\wheels\
    echo Please ensure wheels directory exists in the project root.
    pause
    exit /b 1
)

echo Found wheels directory with packages...
echo.

REM Count wheels
setlocal enabledelayedexpansion
set COUNT=0
for %%f in (wheels\*) do (
    set /a COUNT+=1
)
echo Installing %COUNT% packages from wheels...
echo.

REM Install from wheels
echo [1/3] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel --quiet
if errorlevel 1 (
    echo WARNING: Could not upgrade pip, continuing with current version...
)

echo.
echo [2/3] Installing requirements.txt (using wheels)...
echo This may take several minutes. Please wait...
echo.

python -m pip install --no-index --find-links=wheels -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Installation failed!
    echo Some packages may have failed to install.
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying installation...
echo.

REM Verify key dependencies
python -c "import flask; print('[OK] Flask')" 2>nul || (
    echo [FAIL] Flask
    goto verification_failed
)

python -c "import docx; print('[OK] python-docx')" 2>nul || (
    echo [FAIL] python-docx
    goto verification_failed
)

python -c "import pandas; print('[OK] Pandas')" 2>nul || (
    echo [FAIL] Pandas
    goto verification_failed
)

python -c "import spacy; print('[OK] spaCy')" 2>nul || (
    echo [FAIL] spaCy - This is optional but recommended
)

python -c "import torch; print('[OK] PyTorch')" 2>nul || (
    echo [FAIL] PyTorch - This is optional but recommended for enhanced NLP
)

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

:verification_failed
echo.
echo ============================================================
echo Installation verification failed!
echo ============================================================
echo.
echo Some core dependencies could not be verified.
echo Please check the error messages above.
echo.
pause
exit /b 1
