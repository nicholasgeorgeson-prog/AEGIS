@echo off
REM ============================================================================
REM AEGIS - Distribution Packager v4.3.0
REM ============================================================================
REM Run this on a CONNECTED Windows machine to create a distributable package
REM that includes all dependencies for air-gapped installation.
REM
REM Output: dist\AEGIS_Distribution.zip (ready to transfer and install)
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo AEGIS - Distribution Packager v4.3.0
echo ============================================================
echo.
echo This creates a complete package for air-gapped deployment.
echo Requirements: Python 3.12, pip, internet connection
echo.

REM Check Python version
python --version 2>nul | findstr "3.12" >nul
if errorlevel 1 (
    echo ERROR: Python 3.12 is required.
    pause
    exit /b 1
)

echo [OK] Python 3.12 detected
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set AEGIS_ROOT=%SCRIPT_DIR%..

REM Create output directory
set OUTPUT_DIR=%AEGIS_ROOT%\dist
set PACKAGE_NAME=AEGIS_Distribution

if exist "%OUTPUT_DIR%\%PACKAGE_NAME%" (
    echo Removing existing package...
    rmdir /s /q "%OUTPUT_DIR%\%PACKAGE_NAME%"
)

mkdir "%OUTPUT_DIR%" 2>nul
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%"
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%\deployment"
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%\deployment\wheels"

echo Created: %OUTPUT_DIR%\%PACKAGE_NAME%
echo.

REM ============================================================================
REM Download Python dependencies
REM ============================================================================
echo ============================================================
echo Downloading Python dependencies...
echo ============================================================
echo.

set WHEEL_DIR=%OUTPUT_DIR%\%PACKAGE_NAME%\deployment\wheels

echo [1/8] Downloading Flask and web dependencies...
pip download flask waitress -d "%WHEEL_DIR%" --only-binary=:all: --python-version 3.12 --platform win_amd64 2>nul
if errorlevel 1 pip download flask waitress -d "%WHEEL_DIR%"

echo [2/8] Downloading document processing libraries...
pip download python-docx lxml openpyxl -d "%WHEEL_DIR%" --only-binary=:all: --python-version 3.12 --platform win_amd64 2>nul
if errorlevel 1 pip download python-docx lxml openpyxl -d "%WHEEL_DIR%"

echo [3/8] Downloading mammoth for DOCX-to-HTML conversion (v4.3.0)...
pip download mammoth -d "%WHEEL_DIR%" --only-binary=:all: --python-version 3.12 --platform win_amd64 2>nul
if errorlevel 1 pip download mammoth -d "%WHEEL_DIR%"

echo [4/8] Downloading PDF processing (PyMuPDF, pymupdf4llm, pdfplumber, PyPDF2)...
pip download PyMuPDF pymupdf4llm pdfplumber PyPDF2 -d "%WHEEL_DIR%" --only-binary=:all: --python-version 3.12 --platform win_amd64 2>nul
if errorlevel 1 pip download PyMuPDF pymupdf4llm pdfplumber PyPDF2 -d "%WHEEL_DIR%"

echo [5/8] Downloading spaCy and NLP dependencies...
pip download spacy scikit-learn nltk textblob textstat -d "%WHEEL_DIR%" --only-binary=:all: --python-version 3.12 --platform win_amd64 2>nul
if errorlevel 1 pip download spacy scikit-learn nltk textblob textstat -d "%WHEEL_DIR%"

echo [6/8] Downloading utility packages...
pip download pandas numpy requests reportlab diff-match-patch rapidfuzz bokeh jsonschema python-dateutil -d "%WHEEL_DIR%" --only-binary=:all: --python-version 3.12 --platform win_amd64 2>nul
if errorlevel 1 pip download pandas numpy requests reportlab diff-match-patch rapidfuzz bokeh jsonschema python-dateutil -d "%WHEEL_DIR%"

echo [7/8] Downloading additional NLP packages...
pip download sentence-transformers passivepy language-tool-python py-readability-metrics -d "%WHEEL_DIR%" --only-binary=:all: --python-version 3.12 --platform win_amd64 2>nul
if errorlevel 1 pip download sentence-transformers passivepy language-tool-python py-readability-metrics -d "%WHEEL_DIR%"

echo [8/8] Downloading spaCy English model...
curl -L -o "%WHEEL_DIR%\en_core_web_sm-3.8.0-py3-none-any.whl" https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl 2>nul
if errorlevel 1 (
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl' -OutFile '%WHEEL_DIR%\en_core_web_sm-3.8.0-py3-none-any.whl'" 2>nul
)

REM ============================================================================
REM Copy AEGIS application files
REM ============================================================================
echo.
echo ============================================================
echo Copying AEGIS application files...
echo ============================================================
echo.

REM Copy all Python files
for %%f in ("%AEGIS_ROOT%\*.py") do (
    copy "%%f" "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul && echo   [OK] %%~nxf
)

REM Copy other root files
copy "%AEGIS_ROOT%\version.json" "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul 2>&1
copy "%AEGIS_ROOT%\requirements.txt" "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul 2>&1
copy "%AEGIS_ROOT%\config.json" "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul 2>&1
copy "%AEGIS_ROOT%\CHANGELOG.md" "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul 2>&1
copy "%AEGIS_ROOT%\Install_AEGIS.bat" "%OUTPUT_DIR%\%PACKAGE_NAME%\" >nul 2>&1

REM Copy directories
xcopy "%AEGIS_ROOT%\static" "%OUTPUT_DIR%\%PACKAGE_NAME%\static\" /E /I /Q >nul && echo   [OK] static/
xcopy "%AEGIS_ROOT%\templates" "%OUTPUT_DIR%\%PACKAGE_NAME%\templates\" /E /I /Q >nul && echo   [OK] templates/
xcopy "%AEGIS_ROOT%\statement_forge" "%OUTPUT_DIR%\%PACKAGE_NAME%\statement_forge\" /E /I /Q >nul 2>&1 && echo   [OK] statement_forge/
xcopy "%AEGIS_ROOT%\document_compare" "%OUTPUT_DIR%\%PACKAGE_NAME%\document_compare\" /E /I /Q >nul 2>&1
xcopy "%AEGIS_ROOT%\hyperlink_validator" "%OUTPUT_DIR%\%PACKAGE_NAME%\hyperlink_validator\" /E /I /Q >nul 2>&1
xcopy "%AEGIS_ROOT%\portfolio" "%OUTPUT_DIR%\%PACKAGE_NAME%\portfolio\" /E /I /Q >nul 2>&1
xcopy "%AEGIS_ROOT%\nlp" "%OUTPUT_DIR%\%PACKAGE_NAME%\nlp\" /E /I /Q >nul 2>&1
xcopy "%AEGIS_ROOT%\dictionaries" "%OUTPUT_DIR%\%PACKAGE_NAME%\dictionaries\" /E /I /Q >nul 2>&1
xcopy "%AEGIS_ROOT%\tools" "%OUTPUT_DIR%\%PACKAGE_NAME%\tools\" /E /I /Q >nul 2>&1
xcopy "%AEGIS_ROOT%\images" "%OUTPUT_DIR%\%PACKAGE_NAME%\images\" /E /I /Q >nul 2>&1
xcopy "%AEGIS_ROOT%\docs" "%OUTPUT_DIR%\%PACKAGE_NAME%\docs\" /E /I /Q >nul 2>&1

REM Copy nlp_offline if present (spaCy model, NLTK data)
if exist "%AEGIS_ROOT%\nlp_offline" (
    xcopy "%AEGIS_ROOT%\nlp_offline" "%OUTPUT_DIR%\%PACKAGE_NAME%\nlp_offline\" /E /I /Q >nul 2>&1 && echo   [OK] nlp_offline/
)

REM Create empty directories
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%\logs" 2>nul
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%\temp" 2>nul
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%\backups" 2>nul
mkdir "%OUTPUT_DIR%\%PACKAGE_NAME%\data" 2>nul

REM ============================================================================
REM Create ZIP archive
REM ============================================================================
echo.
echo ============================================================
echo Creating distribution archive...
echo ============================================================
echo.

cd "%OUTPUT_DIR%"
powershell -Command "Compress-Archive -Path '%PACKAGE_NAME%\*' -DestinationPath '%PACKAGE_NAME%.zip' -Force" 2>nul
if errorlevel 1 (
    echo PowerShell compression failed, folder ready at: %OUTPUT_DIR%\%PACKAGE_NAME%\
) else (
    echo [OK] Created: %OUTPUT_DIR%\%PACKAGE_NAME%.zip
)

REM ============================================================================
REM Summary
REM ============================================================================
echo.
echo ============================================================
echo Packaging Complete!
echo ============================================================
echo.
echo Distribution package: %OUTPUT_DIR%\%PACKAGE_NAME%.zip
echo.
for /f %%a in ('dir /b /a-d "%WHEEL_DIR%\*.whl" 2^>nul ^| find /c /v ""') do echo   Wheels included: %%a
echo.
echo To distribute:
echo   1. Copy %PACKAGE_NAME%.zip to the target machine
echo   2. Extract the ZIP
echo   3. Run Install_AEGIS.bat
echo.
pause
