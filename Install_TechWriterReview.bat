@echo off
setlocal enabledelayedexpansion
title TechWriterReview Installer v3.1.0
color 0A

:: ============================================================================
:: TechWriterReview - Windows Installer v3.1.0
:: ============================================================================
:: Double-click this file to install TechWriterReview
::
:: Requirements:
::   - Windows 10/11 (64-bit)
::   - Python 3.12 installed and in PATH
::
:: What this installer does:
::   1. Creates C:\TechWriterReview folder structure
::   2. Copies all application files
::   3. Installs Python dependencies (offline from bundled packages)
::   4. Installs NLP components (offline)
::   5. Creates Start/Stop shortcuts
::   6. Cleans up installation files
:: ============================================================================

set "INSTALL_DIR=C:\TechWriterReview"
set "APP_DIR=%INSTALL_DIR%\app"
set "INSTALLER_DIR=%~dp0"

echo.
echo  ============================================================
echo      TechWriterReview Installer v3.1.0
echo  ============================================================
echo.
echo  This will install TechWriterReview to: %INSTALL_DIR%
echo.
echo  Press any key to continue or Ctrl+C to cancel...
pause > nul

:: ============================================================================
:: Step 1: Check Python 3.12
:: ============================================================================
echo.
echo  [Step 1/7] Checking Python installation...
echo.

python --version 2>nul | findstr /C:"3.12" > nul
if errorlevel 1 (
    echo  [ERROR] Python 3.12 is required but not found!
    echo.
    echo  Please install Python 3.12 from:
    echo  https://www.python.org/downloads/release/python-3120/
    echo.
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo  [OK] Found Python %PYTHON_VER%

:: ============================================================================
:: Step 2: Create Directory Structure
:: ============================================================================
echo.
echo  [Step 2/7] Creating directory structure...
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
:: Step 3: Copy Application Files
:: ============================================================================
echo.
echo  [Step 3/7] Copying application files...
echo.

:: Copy all Python files
xcopy "%INSTALLER_DIR%*.py" "%APP_DIR%\" /Y /Q > nul 2>&1

:: Copy all batch files (except installer)
for %%f in ("%INSTALLER_DIR%*.bat") do (
    if /i not "%%~nxf"=="Install_TechWriterReview.bat" (
        copy "%%f" "%APP_DIR%\" /Y > nul 2>&1
    )
)

:: Copy configuration files
xcopy "%INSTALLER_DIR%*.json" "%APP_DIR%\" /Y /Q > nul 2>&1
xcopy "%INSTALLER_DIR%*.txt" "%APP_DIR%\" /Y /Q > nul 2>&1

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

:: Copy nlp_offline folder if present
if exist "%INSTALLER_DIR%nlp_offline" (
    xcopy "%INSTALLER_DIR%nlp_offline" "%APP_DIR%\nlp_offline\" /E /Y /Q > nul 2>&1
)

echo  [OK] Application files copied

:: ============================================================================
:: Step 4: Install Core Python Dependencies
:: ============================================================================
echo.
echo  [Step 4/7] Installing core Python dependencies...
echo  (This may take a few minutes)
echo.

:: Check if offline packages exist
if exist "%APP_DIR%\nlp_offline\packages" (
    echo  Installing from offline packages...
    pip install --no-index --find-links="%APP_DIR%\nlp_offline\packages" flask python-docx openpyxl PyMuPDF pdfplumber requests waitress > nul 2>&1
) else (
    echo  Installing from internet...
    pip install flask python-docx openpyxl PyMuPDF pdfplumber requests waitress > nul 2>&1
)

if errorlevel 1 (
    echo  [WARNING] Some core packages may not have installed correctly.
) else (
    echo  [OK] Core dependencies installed
)

:: ============================================================================
:: Step 5: Install NLP Dependencies
:: ============================================================================
echo.
echo  [Step 5/7] Installing NLP dependencies...
echo.

if exist "%APP_DIR%\nlp_offline\packages" (
    echo  Installing NLP packages from offline bundle...

    :: Install all wheels from the offline package
    pip install --no-index --find-links="%APP_DIR%\nlp_offline\packages" spacy symspellpy textstat proselint nltk > nul 2>&1

    :: Install spaCy model
    if exist "%APP_DIR%\nlp_offline\spacy_model\en_core_web_md-3.7.1.tar.gz" (
        echo  Installing spaCy language model...
        pip install "%APP_DIR%\nlp_offline\spacy_model\en_core_web_md-3.7.1.tar.gz" > nul 2>&1
    )

    :: Setup NLTK data
    if exist "%APP_DIR%\nlp_offline\nltk_data" (
        echo  Setting up NLTK data...
        set "NLTK_TARGET=%USERPROFILE%\nltk_data\corpora"
        mkdir "!NLTK_TARGET!" 2>nul
        xcopy "%APP_DIR%\nlp_offline\nltk_data\*.zip" "!NLTK_TARGET!\" /Y /Q > nul 2>&1

        :: Extract NLTK data
        cd /d "!NLTK_TARGET!"
        for %%z in (*.zip) do (
            set "FOLDER=%%~nz"
            if not exist "!FOLDER!" (
                powershell -command "Expand-Archive -Path '%%z' -DestinationPath '.' -Force" > nul 2>&1
            )
        )
    )

    echo  [OK] NLP dependencies installed (offline)
) else (
    echo  [INFO] NLP offline package not found.
    echo         NLP features will need to be installed separately.
    echo         Run: python install_nlp.py (requires internet)
)

:: ============================================================================
:: Step 6: Create Start/Stop Scripts
:: ============================================================================
echo.
echo  [Step 6/7] Creating launcher scripts...
echo.

:: Create Start_TechWriterReview.bat at top level
(
echo @echo off
echo title TechWriterReview
echo color 0A
echo.
echo echo  ============================================================
echo echo      Starting TechWriterReview...
echo echo  ============================================================
echo echo.
echo cd /d "%APP_DIR%"
echo python app.py
echo.
echo echo.
echo echo  TechWriterReview has stopped.
echo pause
) > "%INSTALL_DIR%\Start_TechWriterReview.bat"

:: Create Stop_TechWriterReview.bat at top level
(
echo @echo off
echo title Stop TechWriterReview
echo color 0C
echo.
echo echo  ============================================================
echo echo      Stopping TechWriterReview...
echo echo  ============================================================
echo echo.
echo taskkill /f /im python.exe /fi "WINDOWTITLE eq TechWriterReview*" 2^>nul
echo taskkill /f /fi "WINDOWTITLE eq TechWriterReview" 2^>nul
echo.
echo :: Also try to kill by port
echo for /f "tokens=5" %%%%a in ('netstat -aon ^| findstr :5000') do (
echo     taskkill /f /pid %%%%a 2^>nul
echo ^)
echo.
echo echo  [OK] TechWriterReview stopped.
echo timeout /t 3
) > "%INSTALL_DIR%\Stop_TechWriterReview.bat"

:: Create README for updates folder
(
echo TechWriterReview - Updates Folder
echo ==================================
echo.
echo To update TechWriterReview:
echo.
echo 1. Download update files from GitHub Releases
echo 2. Place the update files in this folder
echo 3. Start TechWriterReview
echo 4. Go to Settings ^> Updates
echo 5. Click "Check for Updates"
echo 6. Click "Apply Updates"
echo.
echo The update system will:
echo - Automatically backup current files
echo - Apply the new files
echo - Clean up after itself
echo.
echo For more information, see: app\docs\NLP_USAGE.md
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
    echo  [OK] Cleaned up installation files
)

:: Remove test files
del /q "%APP_DIR%\test_*.docx" 2>nul
del /q "%APP_DIR%\test_*.xlsx" 2>nul
del /q "%APP_DIR%\hyperlink_test*.docx" 2>nul
del /q "%APP_DIR%\hyperlink_test*.xlsx" 2>nul
del /q "%APP_DIR%\cookies*.txt" 2>nul

echo  [OK] Cleanup complete

:: ============================================================================
:: Installation Complete
:: ============================================================================
echo.
echo  ============================================================
echo      Installation Complete!
echo  ============================================================
echo.
echo  TechWriterReview has been installed to:
echo  %INSTALL_DIR%
echo.
echo  Folder Structure:
echo    %INSTALL_DIR%\
echo      Start_TechWriterReview.bat  - Double-click to start
echo      Stop_TechWriterReview.bat   - Double-click to stop
echo      updates\                     - Place update files here
echo      backups\                     - Automatic backups
echo      app\                         - Application files
echo.
echo  To start TechWriterReview:
echo    Double-click: Start_TechWriterReview.bat
echo.
echo  To apply updates:
echo    1. Place update files in the 'updates' folder
echo    2. Start TechWriterReview
echo    3. Go to Settings ^> Updates ^> Apply Updates
echo.
echo  ============================================================
echo.
set /p START_NOW="  Start TechWriterReview now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    start "" "%INSTALL_DIR%\Start_TechWriterReview.bat"
)

echo.
echo  Press any key to close this installer...
pause > nul
exit /b 0
