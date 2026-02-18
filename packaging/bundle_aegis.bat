@echo off
setlocal enabledelayedexpansion
title AEGIS Network Bundler v5.0.0
color 0B

REM ============================================================
REM  AEGIS - Network Distribution Bundler
REM  Creates a self-contained folder for network sharing
REM  No GitHub access required - everything bundled locally
REM  Created by Nicholas Georgeson
REM ============================================================

echo.
echo   ================================================================
echo.
echo          AEGIS v5.0.0 - Network Distribution Bundler
echo          Creates a shareable package for network deployment
echo.
echo   ================================================================
echo.

REM --- Determine project root (one level up from packaging/) ---
set "PROJECT_ROOT=%~dp0.."
pushd "%PROJECT_ROOT%"
set "PROJECT_ROOT=%CD%"
popd

echo   Project root: %PROJECT_ROOT%
echo.

REM --- Choose output location ---
set "DEFAULT_OUTPUT=%PROJECT_ROOT%\dist"
echo   Default output: %DEFAULT_OUTPUT%\AEGIS_Package
echo.
set /p "CUSTOM_OUTPUT=  Output location [press Enter for default]: "
if "%CUSTOM_OUTPUT%"=="" (
    set "OUTPUT_DIR=%DEFAULT_OUTPUT%\AEGIS_Package"
) else (
    set "OUTPUT_DIR=%CUSTOM_OUTPUT%\AEGIS_Package"
)

REM Remove trailing backslash
if "%OUTPUT_DIR:~-1%"=="\" set "OUTPUT_DIR=%OUTPUT_DIR:~0,-1%"

echo.
echo   Bundle will be created at:
echo     %OUTPUT_DIR%
echo.
set /p "CONFIRM=  Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    if /i not "%CONFIRM%"=="yes" (
        echo   Bundling cancelled.
        pause
        exit /b 0
    )
)

echo.
echo   ================================================================
echo   Building AEGIS distribution package...
echo   ================================================================
echo.

REM --- Clean previous bundle ---
if exist "%OUTPUT_DIR%" (
    echo   [1/8] Cleaning previous bundle...
    rd /s /q "%OUTPUT_DIR%" 2>nul
)
mkdir "%OUTPUT_DIR%"

REM --- Copy installer and runtime ---
echo   [2/8] Copying installer and Python runtime...
copy "%~dp0install_aegis.bat" "%OUTPUT_DIR%\install_aegis.bat" >nul
copy "%~dp0python-3.10.11-embed-amd64.zip" "%OUTPUT_DIR%\python-3.10.11-embed-amd64.zip" >nul
copy "%~dp0get-pip.py" "%OUTPUT_DIR%\get-pip.py" >nul
echo          [OK] Installer and Python runtime copied.

REM --- Copy wheel packages ---
echo   [3/8] Copying dependency wheels...
if exist "%~dp0wheels" (
    mkdir "%OUTPUT_DIR%\wheels" 2>nul
    robocopy "%~dp0wheels" "%OUTPUT_DIR%\wheels" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
    echo          [OK] Wheels copied.
) else (
    echo          [WARNING] No wheels directory found - users will need internet for deps.
)

REM --- Copy AEGIS application files ---
echo   [4/8] Copying AEGIS application files...
mkdir "%OUTPUT_DIR%\app" 2>nul

REM Copy all application files, excluding dev/build artifacts
robocopy "%PROJECT_ROOT%" "%OUTPUT_DIR%\app" /E ^
    /XD packaging __pycache__ .git .claude node_modules logs temp dist build backups updates .mypy_cache .pytest_cache venv .venv ^
    /XF "*.pyc" "*.pyo" "*.db" "*.db-shm" "*.db-wal" ".DS_Store" "*.log" ".secret_key" ".env" ".env.local" ^
    /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
echo          [OK] Application files copied.

REM --- Copy NLTK data if bundled ---
echo   [5/8] Copying NLP model data...
if exist "%~dp0..\nltk_data" (
    mkdir "%OUTPUT_DIR%\nltk_data" 2>nul
    robocopy "%~dp0..\nltk_data" "%OUTPUT_DIR%\nltk_data" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
    echo          [OK] NLTK data bundled.
) else if exist "%~dp0nltk_data" (
    mkdir "%OUTPUT_DIR%\nltk_data" 2>nul
    robocopy "%~dp0nltk_data" "%OUTPUT_DIR%\nltk_data" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
    echo          [OK] NLTK data bundled.
) else (
    echo          [INFO] No NLTK data found - will use defaults.
)

REM --- Copy sentence-transformers model if bundled ---
if exist "%~dp0..\models\sentence_transformers" (
    mkdir "%OUTPUT_DIR%\models\sentence_transformers" 2>nul
    robocopy "%~dp0..\models\sentence_transformers" "%OUTPUT_DIR%\models\sentence_transformers" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
    echo          [OK] Sentence-Transformers model bundled.
) else if exist "%~dp0models\sentence_transformers" (
    mkdir "%OUTPUT_DIR%\models\sentence_transformers" 2>nul
    robocopy "%~dp0models\sentence_transformers" "%OUTPUT_DIR%\models\sentence_transformers" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
    echo          [OK] Sentence-Transformers model bundled.
) else (
    echo          [INFO] No sentence-transformers model found - will download on first use.
)

REM --- Create Quick Install script for the recipient ---
echo   [6/8] Creating quick-install script...
(
    echo @echo off
    echo setlocal enabledelayedexpansion
    echo title AEGIS Quick Install
    echo color 0B
    echo echo.
    echo echo   ================================================================
    echo echo.
    echo echo          AEGIS v5.0.0 - Quick Install
    echo echo          From network share / USB / local copy
    echo echo.
    echo echo   ================================================================
    echo echo.
    echo echo   This will install AEGIS from this local package.
    echo echo   No internet connection required.
    echo echo.
    echo cd /d "%%~dp0"
    echo call install_aegis.bat
) > "%OUTPUT_DIR%\INSTALL.bat"
echo          [OK] Quick-install script created.

REM --- Create README for the package ---
echo   [7/8] Creating package README...
(
    echo ================================================================
    echo  AEGIS v5.0.0 - Distribution Package
    echo  Aerospace Engineering Governance ^& Inspection System
    echo  Created by Nicholas Georgeson
    echo ================================================================
    echo.
    echo  INSTALLATION:
    echo  1. Copy this entire folder to the target computer
    echo     ^(or access it from a network share / USB drive^)
    echo  2. Double-click INSTALL.bat
    echo  3. Follow the on-screen prompts
    echo.
    echo  REQUIREMENTS:
    echo  - Windows 10 or later
    echo  - No administrator privileges needed
    echo  - No internet connection needed
    echo.
    echo  INSTALL LOCATIONS:
    echo  - Default: %%LOCALAPPDATA%%\AEGIS
    echo  - You can also install to OneDrive or any writable folder
    echo  - The installer will ask you to choose a location
    echo.
    echo  CONTENTS:
    echo  - install_aegis.bat      : Installer script
    echo  - INSTALL.bat            : Quick-install launcher
    echo  - python-3.10.11-*.zip   : Embedded Python runtime
    echo  - get-pip.py             : pip installer
    echo  - wheels\                : All Python dependencies ^(offline^)
    echo  - app\                   : AEGIS application files
    echo  - nltk_data\             : NLP language data ^(if bundled^)
    echo  - models\                : ML models ^(if bundled^)
    echo.
    echo  AFTER INSTALLATION:
    echo  - Desktop shortcut "AEGIS" will be created
    echo  - Or run AEGIS.bat from the install directory
    echo  - Opens browser to http://localhost:5050
    echo.
    echo  UPDATES:
    echo  - Place update files in the 'updates' folder inside your
    echo    AEGIS install directory, then use the in-app updater
    echo.
    echo  UNINSTALL:
    echo  - Run Uninstall-AEGIS.bat from the install directory
    echo.
) > "%OUTPUT_DIR%\README.txt"
echo          [OK] README created.

REM --- Calculate package size ---
echo   [8/8] Calculating package size...
set "SIZE=0"
for /f "usebackq tokens=3" %%a in (`dir "%OUTPUT_DIR%" /s 2^>nul ^| findstr "File(s)"`) do set "SIZE=%%a"
echo.
echo   ================================================================
echo.
echo          AEGIS Distribution Package Ready!
echo.
echo   ================================================================
echo.
echo   Package location: %OUTPUT_DIR%
echo   Package size: %SIZE% bytes
echo.
echo   TO SHARE:
echo   - Copy the entire AEGIS_Package folder to a network share
echo   - Or copy to a USB drive
echo   - Recipients run INSTALL.bat to install locally
echo.
echo   No GitHub access or internet connection required!
echo.
echo   ================================================================
echo.
pause
