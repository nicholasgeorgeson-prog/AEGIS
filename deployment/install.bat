@echo off
REM ============================================================================
REM TechWriterReview - Air-Gapped Installer
REM ============================================================================
REM Run this on the target machine to install TWR and all dependencies.
REM No internet connection required.
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo TechWriterReview v3.0.86 - Air-Gapped Installer
echo ============================================================
echo.

REM Check Python version
python --version 2>nul | findstr "3.12" >nul
if errorlevel 1 (
    python --version 2>nul | findstr "3.1" >nul
    if errorlevel 1 (
        echo ERROR: Python 3.10+ is required but not found.
        echo.
        echo Please install Python 3.12:
        echo   1. Download from python.org
        echo   2. During install, check "Add Python to PATH"
        echo   3. Run this installer again
        echo.
        pause
        exit /b 1
    )
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Python %PYVER% detected
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Check for wheels
if not exist "%SCRIPT_DIR%wheels" (
    echo ERROR: wheels folder not found.
    echo Make sure you extracted the complete distribution package.
    pause
    exit /b 1
)

echo [OK] Package files found
echo.

REM ============================================================================
REM Get installation path
REM ============================================================================
echo Where would you like to install TechWriterReview?
echo.
echo Default: C:\TWR
echo.
set /p INSTALL_PATH="Enter path (or press Enter for default): "

if "%INSTALL_PATH%"=="" set INSTALL_PATH=C:\TWR

echo.
echo Installing to: %INSTALL_PATH%
echo.

REM Create directory if needed
if not exist "%INSTALL_PATH%" (
    mkdir "%INSTALL_PATH%"
    if errorlevel 1 (
        echo ERROR: Could not create directory. Try running as Administrator.
        pause
        exit /b 1
    )
)

REM ============================================================================
REM Install Python packages from wheels
REM ============================================================================
echo ============================================================
echo Installing Python packages (this may take a few minutes)...
echo ============================================================
echo.

pip install --no-index --find-links="%SCRIPT_DIR%wheels" flask waitress 2>nul
if errorlevel 1 pip install --no-index --find-links="%SCRIPT_DIR%wheels" --user flask waitress

pip install --no-index --find-links="%SCRIPT_DIR%wheels" python-docx lxml openpyxl 2>nul
if errorlevel 1 pip install --no-index --find-links="%SCRIPT_DIR%wheels" --user python-docx lxml openpyxl

pip install --no-index --find-links="%SCRIPT_DIR%wheels" PyMuPDF PyPDF2 2>nul
if errorlevel 1 pip install --no-index --find-links="%SCRIPT_DIR%wheels" --user PyMuPDF PyPDF2

pip install --no-index --find-links="%SCRIPT_DIR%wheels" pdfplumber 2>nul
if errorlevel 1 pip install --no-index --find-links="%SCRIPT_DIR%wheels" --user pdfplumber 2>nul

REM Optional: spaCy
pip install --no-index --find-links="%SCRIPT_DIR%wheels" spacy 2>nul
pip install --no-index --find-links="%SCRIPT_DIR%wheels" en_core_web_sm 2>nul

echo.
echo Verifying packages...
python -c "import flask" 2>nul && echo   [OK] flask || echo   [WARN] flask
python -c "from docx import Document" 2>nul && echo   [OK] python-docx || echo   [WARN] python-docx
python -c "import pdfplumber" 2>nul && echo   [OK] pdfplumber || echo   [WARN] pdfplumber

REM ============================================================================
REM Copy application files
REM ============================================================================
echo.
echo ============================================================
echo Installing application files...
echo ============================================================
echo.

REM Copy Python files
for %%f in ("%SCRIPT_DIR%*.py") do (
    copy /Y "%%f" "%INSTALL_PATH%\" >nul
)
echo   [OK] Python modules

REM Copy config files
copy /Y "%SCRIPT_DIR%version.json" "%INSTALL_PATH%\" >nul 2>&1
copy /Y "%SCRIPT_DIR%requirements.txt" "%INSTALL_PATH%\" >nul 2>&1
copy /Y "%SCRIPT_DIR%config.json" "%INSTALL_PATH%\" >nul 2>&1
copy /Y "%SCRIPT_DIR%README.md" "%INSTALL_PATH%\" >nul 2>&1
copy /Y "%SCRIPT_DIR%TWR_LESSONS_LEARNED.md" "%INSTALL_PATH%\" >nul 2>&1
echo   [OK] Configuration files

REM Copy directories
if exist "%SCRIPT_DIR%static" xcopy /E /I /Y /Q "%SCRIPT_DIR%static" "%INSTALL_PATH%\static\" >nul
if exist "%SCRIPT_DIR%templates" xcopy /E /I /Y /Q "%SCRIPT_DIR%templates" "%INSTALL_PATH%\templates\" >nul
if exist "%SCRIPT_DIR%statement_forge" xcopy /E /I /Y /Q "%SCRIPT_DIR%statement_forge" "%INSTALL_PATH%\statement_forge\" >nul
if exist "%SCRIPT_DIR%tools" xcopy /E /I /Y /Q "%SCRIPT_DIR%tools" "%INSTALL_PATH%\tools\" >nul
if exist "%SCRIPT_DIR%images" xcopy /E /I /Y /Q "%SCRIPT_DIR%images" "%INSTALL_PATH%\images\" >nul
echo   [OK] Static files and templates

REM Create empty directories
mkdir "%INSTALL_PATH%\logs" 2>nul
mkdir "%INSTALL_PATH%\temp" 2>nul
mkdir "%INSTALL_PATH%\backups" 2>nul
mkdir "%INSTALL_PATH%\data" 2>nul
echo   [OK] Working directories

REM ============================================================================
REM Create start script
REM ============================================================================
echo.
(
echo @echo off
echo cd /d "%INSTALL_PATH%"
echo echo Starting TechWriterReview v3.0.86...
echo echo Open browser to: http://localhost:5000
echo echo Press Ctrl+C to stop.
echo echo.
echo python app.py
echo pause
) > "%INSTALL_PATH%\start_twr.bat"

echo Created: %INSTALL_PATH%\start_twr.bat

REM ============================================================================
REM Test installation
REM ============================================================================
echo.
echo ============================================================
echo Testing installation...
echo ============================================================
echo.

pushd "%INSTALL_PATH%"
python -c "from role_integration import RoleIntegration; r = RoleIntegration(); print('  Role extraction:', 'available' if r.is_available() else 'limited')" 2>nul
if errorlevel 1 echo   [WARN] Role extraction test failed
popd

REM ============================================================================
REM Summary
REM ============================================================================
echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo TechWriterReview installed to: %INSTALL_PATH%
echo.
echo To start TechWriterReview:
echo   1. Run: %INSTALL_PATH%\start_twr.bat
echo   2. Open browser to http://localhost:5000
echo.
pause
