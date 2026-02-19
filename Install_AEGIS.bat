@echo off
setlocal enabledelayedexpansion
title AEGIS Installer v5.9.25
color 0A

:: ============================================================================
:: AEGIS - Aerospace Engineering Governance & Inspection System
:: Windows Installer v5.9.25
:: ============================================================================
:: Double-click this file to install AEGIS
::
:: Requirements:
::   - Windows 10/11 (64-bit)
::   - Python 3.10+ installed and in PATH (3.12+ recommended)
::
:: What this installer does:
::   1. Checks Python 3.10+ is available
::   2. Asks where to install (default: C:\AEGIS)
::   3. Creates directory structure
::   4. Copies application files
::   5. Installs Python dependencies (offline from bundled packages)
::   6. Creates Start/Stop launcher scripts
::   7. Cleans up and finishes
:: ============================================================================

set "DEFAULT_DIR=C:\AEGIS"
set "INSTALLER_DIR=%~dp0"

echo.
echo  ============================================================
echo.
echo      AEGIS - Aerospace Engineering Governance ^& Inspection
echo      Installer v5.9.25
echo.
echo  ============================================================
echo.
echo  This installer will set up AEGIS on your computer.
echo.

:: ============================================================================
:: Step 1: Check Python 3.10+
:: ============================================================================
echo  [Step 1/7] Checking Python installation...
echo.

:: v4.6.2-fix: Accept Python 3.10+ (was 3.12-only). Check major.minor >= 3.10
python --version 2>nul >nul
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH!
    echo.
    echo  Please install Python 3.10 or newer from:
    echo  https://www.python.org/downloads/
    echo.
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2 delims=." %%a in ('python --version 2^>^&1') do set PY_MINOR=%%a
for /f "tokens=1 delims=." %%a in ('python --version 2^>^&1') do (
    for /f "tokens=2 delims= " %%b in ("%%a") do set PY_MAJOR=%%b
)
:: Simple check: look for 3.10, 3.11, 3.12, 3.13, etc.
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
if errorlevel 1 (
    echo  [ERROR] Python 3.10 or newer is required!
    echo.
    echo  Please install Python 3.10+ from:
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo  [OK] Found Python %PYTHON_VER%
echo.

:: ============================================================================
:: Step 2: Choose Install Location
:: ============================================================================
echo  [Step 2/7] Choose installation location...
echo.
echo  Default location: %DEFAULT_DIR%
echo.
set /p INSTALL_DIR="  Install location [%DEFAULT_DIR%]: "
if "%INSTALL_DIR%"=="" set "INSTALL_DIR=%DEFAULT_DIR%"

:: Remove trailing backslash if present
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

set "APP_DIR=%INSTALL_DIR%\app"

echo.
echo  AEGIS will be installed to: %INSTALL_DIR%
echo.
set /p CONFIRM="  Continue? (Y/N): "
if /i "%CONFIRM%" neq "Y" (
    echo  Installation cancelled.
    pause
    exit /b 0
)

:: ============================================================================
:: Step 3: Create Directory Structure
:: ============================================================================
echo.
echo  [Step 3/7] Creating directory structure...
echo.

if exist "%INSTALL_DIR%" (
    echo  [WARNING] Installation directory already exists: %INSTALL_DIR%
    echo.
    set /p OVERWRITE="  Overwrite existing installation? (Y/N): "
    if /i "!OVERWRITE!" neq "Y" (
        echo  Installation cancelled.
        pause
        exit /b 0
    )
    echo  Removing old installation...
    rmdir /s /q "%INSTALL_DIR%" 2>nul
)

mkdir "%INSTALL_DIR%" 2>nul
mkdir "%APP_DIR%" 2>nul
mkdir "%INSTALL_DIR%\updates" 2>nul
mkdir "%INSTALL_DIR%\backups" 2>nul
mkdir "%INSTALL_DIR%\logs" 2>nul

echo  [OK] Created directory structure

:: ============================================================================
:: Step 4: Copy Application Files
:: ============================================================================
echo.
echo  [Step 4/7] Copying application files...
echo.

:: Copy all Python files
xcopy "%INSTALLER_DIR%*.py" "%APP_DIR%\" /Y /Q > nul 2>&1

:: Copy all batch files (except installers)
for %%f in ("%INSTALLER_DIR%*.bat") do (
    if /i not "%%~nxf"=="Install_AEGIS.bat" (
        if /i not "%%~nxf"=="Install_TechWriterReview.bat" (
            copy "%%f" "%APP_DIR%\" /Y > nul 2>&1
        )
    )
)

:: Copy configuration files
xcopy "%INSTALLER_DIR%*.json" "%APP_DIR%\" /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%*.txt" "%APP_DIR%\" /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%*.md" "%APP_DIR%\" /Y /Q > nul 2>&1

:: Copy directories
xcopy "%INSTALLER_DIR%static" "%APP_DIR%\static\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%templates" "%APP_DIR%\templates\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%nlp" "%APP_DIR%\nlp\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%dictionaries" "%APP_DIR%\dictionaries\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%statement_forge" "%APP_DIR%\statement_forge\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%document_compare" "%APP_DIR%\document_compare\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%portfolio" "%APP_DIR%\portfolio\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%hyperlink_validator" "%APP_DIR%\hyperlink_validator\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%images" "%APP_DIR%\images\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%data" "%APP_DIR%\data\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%tools" "%APP_DIR%\tools\" /E /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%docs" "%APP_DIR%\docs\" /E /Y /Q > nul 2>&1

:: Copy nlp_offline folder if present (for offline dependency installation)
if exist "%INSTALLER_DIR%nlp_offline" (
    xcopy "%INSTALLER_DIR%nlp_offline" "%APP_DIR%\nlp_offline\" /E /Y /Q > nul 2>&1
)

:: Copy deployment wheels if present
if exist "%INSTALLER_DIR%deployment" (
    xcopy "%INSTALLER_DIR%deployment" "%APP_DIR%\deployment\" /E /Y /Q > nul 2>&1
)

echo  [OK] Application files copied

:: ============================================================================
:: Step 5: Install Python Dependencies
:: ============================================================================
echo.
echo  [Step 5/7] Installing Python dependencies...
echo  (This may take a few minutes)
echo.

:: Determine where offline packages are located
set "WHEEL_DIR="
if exist "%APP_DIR%\nlp_offline\packages" set "WHEEL_DIR=%APP_DIR%\nlp_offline\packages"
if exist "%APP_DIR%\deployment\wheels" set "WHEEL_DIR=%APP_DIR%\deployment\wheels"

if defined WHEEL_DIR (
    echo  Installing from offline packages...
    echo.

    echo  [5a] Core web framework...
    pip install --no-index --find-links="%WHEEL_DIR%" flask waitress > nul 2>&1

    echo  [5b] Document processing (python-docx, mammoth, lxml, openpyxl)...
    pip install --no-index --find-links="%WHEEL_DIR%" python-docx mammoth lxml openpyxl > nul 2>&1

    echo  [5c] PDF processing (PyMuPDF, pymupdf4llm, pdfplumber)...
    pip install --no-index --find-links="%WHEEL_DIR%" PyMuPDF pymupdf4llm pdfplumber > nul 2>&1

    echo  [5d] NLP packages (spaCy, NLTK, scikit-learn)...
    pip install --no-index --find-links="%WHEEL_DIR%" spacy symspellpy textstat nltk scikit-learn > nul 2>&1

    echo  [5e] Additional packages (reportlab, requests, etc.)...
    pip install --no-index --find-links="%WHEEL_DIR%" reportlab requests pandas numpy diff-match-patch > nul 2>&1

    :: Install spaCy model if present
    for %%m in ("%WHEEL_DIR%\en_core_web_*.tar.gz" "%WHEEL_DIR%\en_core_web_*.whl") do (
        if exist "%%m" (
            echo  [5f] Installing spaCy language model...
            pip install "%%m" > nul 2>&1
        )
    )

    :: Setup NLTK data if present in offline bundle
    if exist "%APP_DIR%\nlp_offline\nltk_data" (
        echo  [5g] Setting up NLTK data from offline bundle...
        set "NLTK_TARGET=%USERPROFILE%\nltk_data\corpora"
        mkdir "!NLTK_TARGET!" 2>nul
        xcopy "%APP_DIR%\nlp_offline\nltk_data\*.zip" "!NLTK_TARGET!\" /Y /Q > nul 2>&1
        cd /d "!NLTK_TARGET!"
        for %%z in (*.zip) do (
            set "FOLDER=%%~nz"
            if not exist "!FOLDER!" (
                powershell -command "Expand-Archive -Path '%%z' -DestinationPath '.' -Force" > nul 2>&1
            )
        )
    ) else (
        echo  [5g] Downloading NLTK data packages...
        pip install nltk > nul 2>&1
        python -c "import ssl; ssl._create_default_https_context = ssl._create_unverified_context; import nltk; [nltk.download(d, quiet=True) for d in ['punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','stopwords','wordnet','omw-1.4','cmudict']]" > nul 2>&1
        if errorlevel 1 (
            echo  [WARN] NLTK data download failed - some NLP features limited
        ) else (
            echo  [OK] NLTK data downloaded
        )
    )

    :: Run full NLP installer if available
    if exist "%APP_DIR%\install_nlp.py" (
        echo  [5h] Running NLP model verification...
        python "%APP_DIR%\install_nlp.py" --verify > nul 2>&1
        if errorlevel 1 (
            echo  [WARN] Some NLP models may need manual installation
            echo         Run: python install_nlp.py
        ) else (
            echo  [OK] All NLP models verified
        )
    )

    echo.
    echo  [OK] Dependencies installed (offline)
) else (
    echo  [INFO] No offline package bundle found.
    echo         Attempting online installation...
    echo.
    pip install -r "%APP_DIR%\requirements.txt" > nul 2>&1
    if errorlevel 1 (
        echo  [WARNING] Some packages may not have installed correctly.
        echo            Check the requirements.txt for missing dependencies.
    ) else (
        echo  [OK] Dependencies installed (online)
    )

    :: Install NLP models online
    echo.
    echo  Installing NLP models...
    if exist "%APP_DIR%\install_nlp.py" (
        python "%APP_DIR%\install_nlp.py"
    ) else (
        python -m spacy download en_core_web_sm > nul 2>&1
        python -c "import ssl; ssl._create_default_https_context = ssl._create_unverified_context; import nltk; [nltk.download(d, quiet=True) for d in ['punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','stopwords','wordnet','omw-1.4','cmudict']]" > nul 2>&1
        echo  [OK] NLP models installed
    )
)

:: ============================================================================
:: Step 6: Create Start/Stop Scripts
:: ============================================================================
echo.
echo  [Step 6/7] Creating launcher scripts...
echo.

:: Create Start_AEGIS.bat at top level
(
echo @echo off
echo title AEGIS
echo color 0A
echo.
echo echo  ============================================================
echo echo.
echo echo      AEGIS - Aerospace Engineering Governance ^& Inspection
echo echo      Starting...
echo echo.
echo echo  ============================================================
echo echo.
echo cd /d "%APP_DIR%"
echo python app.py
echo.
echo echo.
echo echo  AEGIS has stopped.
echo pause
) > "%INSTALL_DIR%\Start_AEGIS.bat"

:: Create Stop_AEGIS.bat at top level
(
echo @echo off
echo title Stop AEGIS
echo color 0C
echo.
echo echo  ============================================================
echo echo      Stopping AEGIS...
echo echo  ============================================================
echo echo.
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq AEGIS*" 2^>nul
echo taskkill /f /fi "WINDOWTITLE eq AEGIS" 2^>nul
echo.
echo :: Also try to kill by port
echo for /f "tokens=5" %%%%a in ('netstat -aon ^| findstr :5050') do (
echo     taskkill /f /pid %%%%a 2^>nul
echo ^)
echo.
echo echo  [OK] AEGIS stopped.
echo timeout /t 3
) > "%INSTALL_DIR%\Stop_AEGIS.bat"

:: Create README for updates folder
(
echo AEGIS - Updates Folder
echo ==================================
echo.
echo To update AEGIS:
echo.
echo 1. Place update files in this folder
echo 2. Start AEGIS
echo 3. Go to Settings ^> Updates
echo 4. Click "Check for Updates"
echo 5. Click "Apply Updates"
echo.
echo The update system will:
echo - Automatically backup current files
echo - Apply the new files
echo - Clean up after itself
) > "%INSTALL_DIR%\updates\README.txt"

echo  [OK] Launcher scripts created

:: ============================================================================
:: Step 7: Cleanup and Finish
:: ============================================================================
echo.
echo  [Step 7/7] Cleaning up...
echo.

:: Remove unnecessary files from app directory
del /q "%APP_DIR%\*.pyc" 2>nul
del /q "%APP_DIR%\*.log" 2>nul
del /q "%APP_DIR%\startup_error.log" 2>nul
rmdir /s /q "%APP_DIR%\__pycache__" 2>nul
rmdir /s /q "%APP_DIR%\.pytest_cache" 2>nul

:: Remove nlp_offline folder after installation (packages are installed)
if exist "%APP_DIR%\nlp_offline" (
    rmdir /s /q "%APP_DIR%\nlp_offline" 2>nul
    echo  [OK] Cleaned up offline packages
)

:: Remove deployment wheels after installation
if exist "%APP_DIR%\deployment\wheels" (
    rmdir /s /q "%APP_DIR%\deployment\wheels" 2>nul
    echo  [OK] Cleaned up deployment wheels
)

:: Remove test files
del /q "%APP_DIR%\test_*.docx" 2>nul
del /q "%APP_DIR%\test_*.xlsx" 2>nul
del /q "%APP_DIR%\hyperlink_test*.docx" 2>nul
del /q "%APP_DIR%\hyperlink_test*.xlsx" 2>nul
del /q "%APP_DIR%\cookies*.txt" 2>nul

:: Remove installer files from app directory (they shouldn't be there)
del /q "%APP_DIR%\Install_AEGIS.bat" 2>nul
del /q "%APP_DIR%\Install_TechWriterReview.bat" 2>nul

echo  [OK] Cleanup complete

:: ============================================================================
:: Installation Complete
:: ============================================================================
echo.
echo  ============================================================
echo.
echo      Installation Complete!
echo.
echo  ============================================================
echo.
echo  AEGIS has been installed to:
echo  %INSTALL_DIR%
echo.
echo  Folder Structure:
echo    %INSTALL_DIR%\
echo      Start_AEGIS.bat             - Double-click to start
echo      Stop_AEGIS.bat              - Double-click to stop
echo      updates\                     - Place update files here
echo      backups\                     - Automatic backups
echo      app\                         - Application files
echo.
echo  To start AEGIS:
echo    Double-click: Start_AEGIS.bat
echo.
echo  Then open your browser to: http://localhost:5050
echo.
echo  To apply updates:
echo    1. Place update files in the 'updates' folder
echo    2. Start AEGIS
echo    3. Go to Settings ^> Updates ^> Apply Updates
echo.
echo  ============================================================
echo.
set /p START_NOW="  Start AEGIS now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    start "" "%INSTALL_DIR%\Start_AEGIS.bat"
)

echo.
echo  Press any key to close this installer...
pause > nul
exit /b 0
