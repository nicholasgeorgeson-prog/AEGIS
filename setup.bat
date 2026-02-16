@echo off
REM ============================================================================
REM TechWriterReview v3.0.124 - Complete Setup (NO ADMIN REQUIRED)
REM ============================================================================
REM Installs ALL dependencies for full functionality without admin privileges.
REM Uses portable/local installations where possible.
REM
REM CORE:
REM   - Flask web framework
REM   - python-docx for Word documents
REM   - openpyxl for Excel files
REM
REM PDF EXTRACTION:
REM   - PyMuPDF (best text extraction)
REM   - pdfplumber (table extraction)
REM   - Camelot, Tabula (advanced tables)
REM
REM OCR (for scanned documents):
REM   - pytesseract, pdf2image, Pillow
REM   - Tesseract OCR (LOCAL/PORTABLE - no admin needed)
REM   - Poppler (LOCAL/PORTABLE - no admin needed)
REM
REM NLP ENHANCEMENT:
REM   - spaCy with English model
REM   - scikit-learn, NLTK, textstat
REM   - language-tool-python (grammar)
REM
REM FIX ASSISTANT v2 & DOCUMENT COMPARISON:
REM   - ReportLab (PDF report generation)
REM   - diff-match-patch (word-level diff for scan comparison)
REM
REM HEADLESS BROWSER (for bot-protected site validation):
REM   - Playwright with Chromium browser
REM
REM AI-POWERED EXTRACTION:
REM   - Docling (offline/air-gapped ready)
REM
REM For AI-powered extraction setup, run: setup_docling.bat
REM ============================================================================
setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Local tool directories (no admin needed)
set "LOCAL_TOOLS=%SCRIPT_DIR%\tools"
set "LOCAL_TESSERACT=%LOCAL_TOOLS%\tesseract"
set "LOCAL_POPPLER=%LOCAL_TOOLS%\poppler"
set "BUNDLED_PACKAGE=%SCRIPT_DIR%\tesseract_package"

echo.
echo ============================================================
echo TechWriterReview v3.0.124 - Complete Setup
echo ============================================================
echo.
echo This installs ALL dependencies for full functionality.
echo.
echo What will be installed:
echo   [Core]        Flask, python-docx, openpyxl, lxml
echo   [PDF]         PyMuPDF, pdfplumber, Camelot, Tabula
echo   [OCR]         pytesseract, pdf2image, Pillow
echo   [NLP]         spaCy, scikit-learn, NLTK, textstat
echo   [Grammar]     language-tool-python
echo   [Fix Assist]  ReportLab, diff-match-patch
echo   [Headless]    Playwright (bot-protected site validation)
echo   [Utilities]   pandas, numpy, requests
echo.
echo Estimated time: 5-15 minutes
echo Disk space: ~800MB
echo.
echo NOTE: For AI-powered document extraction (Docling),
echo       run setup_docling.bat separately after this completes.
echo.

set /p CONTINUE="Continue with installation? (Y/N): "
if /i not "!CONTINUE!"=="Y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM ============================================================================
REM Check Python Version
REM ============================================================================
echo.
echo ============================================================
echo Checking Python version...
echo ============================================================

python --version 2>nul | findstr /R "3\.1[0-9]" >nul
if errorlevel 1 (
    echo.
    echo ERROR: Python 3.10+ is required but not found.
    echo.
    echo Please install Python 3.10 or later:
    echo   1. Download from https://python.org
    echo   2. During install, check "Add Python to PATH"
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Python %PYVER% detected
echo.

REM ============================================================================
REM Step 1: Core Dependencies
REM ============================================================================
echo ============================================================
echo Step 1/8: Installing core dependencies...
echo ============================================================
echo.

echo Installing Flask (web framework)...
pip install Flask>=2.0.0 --quiet --disable-pip-version-check --user 2>nul

echo Installing waitress (production server)...
pip install waitress --quiet --disable-pip-version-check --user 2>nul

echo Installing python-docx (Word documents)...
pip install python-docx --quiet --disable-pip-version-check --user 2>nul

echo Installing lxml (XML processing)...
pip install lxml --quiet --disable-pip-version-check --user 2>nul

echo Installing openpyxl (Excel files)...
pip install openpyxl --quiet --disable-pip-version-check --user 2>nul

echo [OK] Core dependencies installed
echo.

REM ============================================================================
REM Step 2: PDF Extraction Libraries
REM ============================================================================
echo ============================================================
echo Step 2/8: Installing PDF extraction libraries...
echo ============================================================
echo.

echo Installing PyMuPDF (best text extraction)...
pip install PyMuPDF --quiet --disable-pip-version-check --user 2>nul

echo Installing pdfplumber (table extraction)...
pip install pdfplumber --quiet --disable-pip-version-check --user 2>nul

echo Installing PyPDF2 (lightweight fallback)...
pip install PyPDF2 --quiet --disable-pip-version-check --user 2>nul

echo Installing Camelot (bordered table extraction)...
pip install "camelot-py[base]" --quiet --disable-pip-version-check --user 2>nul

echo Installing Tabula (alternative tables)...
pip install tabula-py --quiet --disable-pip-version-check --user 2>nul

echo [OK] PDF extraction libraries installed
echo.

REM ============================================================================
REM Step 3: OCR Support
REM ============================================================================
echo ============================================================
echo Step 3/8: Installing OCR support...
echo ============================================================
echo.

echo Installing pytesseract (OCR bindings)...
pip install pytesseract --quiet --disable-pip-version-check --user 2>nul

echo Installing pdf2image (PDF to image)...
pip install pdf2image --quiet --disable-pip-version-check --user 2>nul

echo Installing Pillow (image processing)...
pip install Pillow --quiet --disable-pip-version-check --user 2>nul

echo [OK] OCR support packages installed
echo.

REM ============================================================================
REM Step 4: NLP Enhancement
REM ============================================================================
echo ============================================================
echo Step 4/8: Installing NLP enhancement...
echo ============================================================
echo.

echo Installing scikit-learn (text analysis)...
pip install scikit-learn --quiet --disable-pip-version-check --user 2>nul

echo Installing spaCy (NLP framework)...
pip install spacy --quiet --disable-pip-version-check --user 2>nul

echo Downloading spaCy English model (this may take a minute)...
python -m spacy download en_core_web_sm --quiet 2>nul
if errorlevel 1 (
    echo   Note: spaCy model download may have failed - will work without it
)

echo Installing NLTK (natural language toolkit)...
pip install nltk --quiet --disable-pip-version-check --user 2>nul

echo Installing textblob (text processing)...
pip install textblob --quiet --disable-pip-version-check --user 2>nul

echo Installing textstat (readability metrics)...
pip install textstat --quiet --disable-pip-version-check --user 2>nul

echo [OK] NLP enhancement packages installed
echo.

REM ============================================================================
REM Step 5: Grammar Checking
REM ============================================================================
echo ============================================================
echo Step 5/8: Installing grammar checking...
echo ============================================================
echo.

echo Installing language-tool-python (grammar checker)...
pip install language-tool-python --quiet --disable-pip-version-check --user 2>nul

echo [OK] Grammar checking installed
echo.

REM ============================================================================
REM Step 6: Fix Assistant v2 & Document Comparison Dependencies
REM ============================================================================
echo ============================================================
echo Step 6/8: Installing Fix Assistant v2 ^& Document Comparison...
echo ============================================================
echo.

echo Installing ReportLab (PDF report generation)...
pip install reportlab --quiet --disable-pip-version-check --user 2>nul

echo Installing diff-match-patch (Document Comparison word-level diff)...
pip install diff-match-patch --quiet --disable-pip-version-check --user 2>nul

echo [OK] Fix Assistant v2 ^& Document Comparison dependencies installed
echo.

REM ============================================================================
REM Step 7: Utilities
REM ============================================================================
echo ============================================================
echo Step 7/8: Installing utilities...
echo ============================================================
echo.

echo Installing pandas (data analysis)...
pip install pandas --quiet --disable-pip-version-check --user 2>nul

echo Installing numpy (numerical computing)...
pip install numpy --quiet --disable-pip-version-check --user 2>nul

echo Installing requests (HTTP client)...
pip install requests --quiet --disable-pip-version-check --user 2>nul

echo Installing python-dateutil (date handling)...
pip install python-dateutil --quiet --disable-pip-version-check --user 2>nul

echo Installing jsonschema (JSON validation)...
pip install jsonschema --quiet --disable-pip-version-check --user 2>nul

echo [OK] Utilities installed
echo.

REM ============================================================================
REM Step 8: Headless Browser (Playwright)
REM ============================================================================
echo ============================================================
echo Step 8/8: Installing headless browser for bot-protected sites...
echo ============================================================
echo.

echo Installing Playwright (browser automation)...
pip install playwright --quiet --disable-pip-version-check --user 2>nul

echo Downloading Chromium browser (this may take a minute)...
python -m playwright install chromium 2>nul
if errorlevel 1 (
    echo   Note: Chromium download may have failed - headless rescan may not work
)

echo [OK] Headless browser installed
echo.

REM ============================================================================
REM Verification
REM ============================================================================
echo ============================================================
echo Verifying installation...
echo ============================================================
echo.

set CORE_OK=1
set WARNINGS=0

REM --- Core checks ---
echo [Core]
python -c "import flask" 2>nul
if errorlevel 1 (echo   [FAIL] Flask & set CORE_OK=0) else (echo   [OK] Flask)

python -c "from docx import Document" 2>nul
if errorlevel 1 (echo   [FAIL] python-docx & set CORE_OK=0) else (echo   [OK] python-docx)

python -c "import openpyxl" 2>nul
if errorlevel 1 (echo   [WARN] openpyxl & set /a WARNINGS+=1) else (echo   [OK] openpyxl)

REM --- PDF checks ---
echo.
echo [PDF Extraction]
python -c "import fitz" 2>nul
if errorlevel 1 (echo   [WARN] PyMuPDF & set /a WARNINGS+=1) else (echo   [OK] PyMuPDF)

python -c "import pdfplumber" 2>nul
if errorlevel 1 (echo   [WARN] pdfplumber & set /a WARNINGS+=1) else (echo   [OK] pdfplumber)

python -c "import camelot" 2>nul
if errorlevel 1 (echo   [WARN] Camelot ^(needs Ghostscript^) & set /a WARNINGS+=1) else (echo   [OK] Camelot)

python -c "import tabula" 2>nul
if errorlevel 1 (echo   [WARN] Tabula ^(needs Java^) & set /a WARNINGS+=1) else (echo   [OK] Tabula)

REM --- OCR checks ---
echo.
echo [OCR Support]
python -c "import pytesseract" 2>nul
if errorlevel 1 (echo   [WARN] pytesseract & set /a WARNINGS+=1) else (echo   [OK] pytesseract)

python -c "from pdf2image import convert_from_path" 2>nul
if errorlevel 1 (echo   [WARN] pdf2image & set /a WARNINGS+=1) else (echo   [OK] pdf2image)

python -c "from PIL import Image" 2>nul
if errorlevel 1 (echo   [WARN] Pillow & set /a WARNINGS+=1) else (echo   [OK] Pillow)

REM Check local Tesseract
if exist "%LOCAL_TESSERACT%\tesseract.exe" (
    echo   [OK] Tesseract OCR ^(local installation^)
) else (
    where tesseract >nul 2>&1
    if errorlevel 1 (
        echo   [WARN] Tesseract OCR not found
    ) else (
        echo   [OK] Tesseract OCR ^(system^)
    )
)

REM --- NLP checks ---
echo.
echo [NLP Enhancement]
python -c "import spacy; spacy.load('en_core_web_sm')" 2>nul
if errorlevel 1 (echo   [WARN] spaCy model ^(run: python -m spacy download en_core_web_sm^) & set /a WARNINGS+=1) else (echo   [OK] spaCy + en_core_web_sm)

python -c "from sklearn.feature_extraction.text import TfidfVectorizer" 2>nul
if errorlevel 1 (echo   [WARN] scikit-learn & set /a WARNINGS+=1) else (echo   [OK] scikit-learn)

python -c "import textstat" 2>nul
if errorlevel 1 (echo   [WARN] textstat & set /a WARNINGS+=1) else (echo   [OK] textstat)

REM --- Grammar checks ---
echo.
echo [Grammar Checking]
python -c "import language_tool_python" 2>nul
if errorlevel 1 (echo   [WARN] language-tool-python ^(needs Java 8+^) & set /a WARNINGS+=1) else (echo   [OK] language-tool-python)

REM --- Fix Assistant v2 & Document Comparison checks ---
echo.
echo [Fix Assistant v2 ^& Document Comparison]
python -c "from reportlab.lib.pagesizes import letter" 2>nul
if errorlevel 1 (echo   [WARN] ReportLab & set /a WARNINGS+=1) else (echo   [OK] ReportLab)

python -c "import diff_match_patch" 2>nul
if errorlevel 1 (echo   [WARN] diff-match-patch & set /a WARNINGS+=1) else (echo   [OK] diff-match-patch)

REM --- Headless Browser checks ---
echo.
echo [Headless Browser]
python -c "from playwright.sync_api import sync_playwright" 2>nul
if errorlevel 1 (echo   [WARN] Playwright ^(run: pip install playwright ^&^& playwright install chromium^) & set /a WARNINGS+=1) else (echo   [OK] Playwright)

python -c "import sqlite3" 2>nul
if errorlevel 1 (echo   [FAIL] sqlite3 & set CORE_OK=0) else (echo   [OK] sqlite3 ^(built-in^))

REM --- TechWriterReview module checks ---
echo.
echo [TechWriterReview Modules]
python -c "from core import TechWriterReviewEngine" 2>nul
if errorlevel 1 (echo   [FAIL] core engine & set CORE_OK=0) else (echo   [OK] Core engine)

python -c "from fix_assistant_api import build_document_content" 2>nul
if errorlevel 1 (echo   [WARN] fix_assistant_api & set /a WARNINGS+=1) else (echo   [OK] Fix Assistant API)

python -c "from decision_learner import DecisionLearner" 2>nul
if errorlevel 1 (echo   [WARN] decision_learner & set /a WARNINGS+=1) else (echo   [OK] Decision Learner)

REM --- Docling check (optional) ---
echo.
echo [Optional: AI Extraction]
python -c "import docling; print(f'  [OK] Docling {docling.__version__}')" 2>nul
if errorlevel 1 (
    echo   [INFO] Docling not installed
    echo         For AI-powered extraction, run: setup_docling.bat
)

REM ============================================================================
REM Step 9: Setup Local Tesseract and Poppler (NO ADMIN REQUIRED)
REM ============================================================================
echo.
echo ============================================================
echo Step 9/10: Setting up local OCR tools (no admin required)...
echo ============================================================
echo.

REM Create tools directory
if not exist "%LOCAL_TOOLS%" mkdir "%LOCAL_TOOLS%"

REM --- Setup Local Tesseract ---
if exist "%LOCAL_TESSERACT%\tesseract.exe" (
    echo [OK] Local Tesseract already installed
) else (
    echo Setting up local Tesseract OCR...

    REM Check for pre-extracted bundled Tesseract first
    if exist "%BUNDLED_PACKAGE%\tesseract\tesseract.exe" (
        echo   Copying bundled Tesseract...
        xcopy "%BUNDLED_PACKAGE%\tesseract" "%LOCAL_TESSERACT%\" /E /I /Q >nul 2>&1
        echo   [OK] Tesseract copied from bundle

    REM Check for bundled installer (tesseract-installer.exe)
    ) else if exist "%BUNDLED_PACKAGE%\tesseract-installer.exe" (
        echo   Found bundled Tesseract installer, extracting...

        REM Try 7-Zip first (most reliable for NSIS installers)
        where 7z >nul 2>&1
        if not errorlevel 1 (
            7z x "%BUNDLED_PACKAGE%\tesseract-installer.exe" -o"%LOCAL_TESSERACT%" -y >nul 2>&1
            echo   [OK] Tesseract extracted with 7-Zip
        ) else (
            REM Try PowerShell extraction (may not work for NSIS)
            echo   7-Zip not found, trying alternative extraction...
            powershell -Command "Start-Process '%BUNDLED_PACKAGE%\tesseract-installer.exe' -ArgumentList '/S','/D=%LOCAL_TESSERACT%' -Wait -NoNewWindow" 2>nul
            if exist "%LOCAL_TESSERACT%\tesseract.exe" (
                echo   [OK] Tesseract installed silently
            ) else (
                echo   [NOTE] Could not auto-extract. Manual steps:
                echo          1. Install 7-Zip from https://7-zip.org
                echo          2. Right-click tesseract-installer.exe -^> 7-Zip -^> Extract
                echo          3. Copy contents to: %LOCAL_TESSERACT%
            )
        )

    REM Check for zip file
    ) else if exist "%BUNDLED_PACKAGE%\tesseract-portable.zip" (
        echo   Extracting bundled Tesseract zip...
        powershell -Command "Expand-Archive -Path '%BUNDLED_PACKAGE%\tesseract-portable.zip' -DestinationPath '%LOCAL_TESSERACT%' -Force" 2>nul
        echo   [OK] Tesseract extracted from bundle

    ) else (
        echo   [NOTE] Tesseract not bundled - will attempt download...
        echo   Downloading portable Tesseract ^(~50MB^)...

        REM Download to temp
        if not exist "%SCRIPT_DIR%\temp" mkdir "%SCRIPT_DIR%\temp"

        powershell -Command "& {try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe' -OutFile '%SCRIPT_DIR%\temp\tesseract-setup.exe' -UseBasicParsing } catch { exit 1 }}" 2>nul

        if exist "%SCRIPT_DIR%\temp\tesseract-setup.exe" (
            echo   Downloaded installer. Extracting portable files...
            REM Extract using 7zip if available, otherwise note manual step
            where 7z >nul 2>&1
            if not errorlevel 1 (
                7z x "%SCRIPT_DIR%\temp\tesseract-setup.exe" -o"%LOCAL_TESSERACT%" -y >nul 2>&1
                echo   [OK] Tesseract extracted
            ) else (
                echo   [NOTE] Cannot extract automatically.
                echo          Please manually extract tesseract to: %LOCAL_TESSERACT%
                echo          Or install 7-Zip and run setup again.
            )
        ) else (
            echo   [WARN] Could not download Tesseract.
            echo          For offline setup, place portable Tesseract in:
            echo          %BUNDLED_PACKAGE%\tesseract\
        )
    )
)

REM --- Copy Tesseract Language Data ---
if exist "%LOCAL_TESSERACT%\tesseract.exe" (
    set "LOCAL_TESSDATA=%LOCAL_TESSERACT%\tessdata"
    if not exist "!LOCAL_TESSDATA!" mkdir "!LOCAL_TESSDATA!"

    if exist "%BUNDLED_PACKAGE%\tessdata\eng.traineddata" (
        if not exist "!LOCAL_TESSDATA!\eng.traineddata" (
            echo   Copying language data...
            copy "%BUNDLED_PACKAGE%\tessdata\*.traineddata" "!LOCAL_TESSDATA!\" >nul 2>&1
            echo   [OK] Language data copied
        )
    )
)

REM --- Setup Local Poppler ---
if exist "%LOCAL_POPPLER%\bin\pdftoppm.exe" (
    echo [OK] Local Poppler already installed
) else (
    echo Setting up local Poppler ^(for PDF to image conversion^)...

    if exist "%BUNDLED_PACKAGE%\poppler\bin\pdftoppm.exe" (
        echo   Copying bundled Poppler...
        xcopy "%BUNDLED_PACKAGE%\poppler" "%LOCAL_POPPLER%\" /E /I /Q >nul 2>&1
        echo   [OK] Poppler copied from bundle
    ) else if exist "%BUNDLED_PACKAGE%\poppler-portable.zip" (
        echo   Extracting bundled Poppler...
        powershell -Command "Expand-Archive -Path '%BUNDLED_PACKAGE%\poppler-portable.zip' -DestinationPath '%LOCAL_POPPLER%' -Force" 2>nul
        echo   [OK] Poppler extracted from bundle
    ) else (
        echo   [NOTE] Poppler not bundled.
        echo          PDF-to-image OCR may not work without Poppler.
        echo          To add: place poppler in %BUNDLED_PACKAGE%\poppler\
    )
)

echo.

REM ============================================================================
REM Step 10: Configure Environment and Create Activation Script
REM ============================================================================
echo ============================================================
echo Step 10/10: Configuring environment...
echo ============================================================
echo.

REM Determine cache paths
set "USER_CACHE=%USERPROFILE%\.cache\huggingface\hub"
if not exist "%USER_CACHE%" set "USER_CACHE=%USERPROFILE%\.cache\docling\models"

REM Create the activation script
echo Creating environment activation script...

(
echo @echo off
echo REM ============================================================================
echo REM AEGIS TechWriterReview - Environment Activation
echo REM ============================================================================
echo REM Run this script before using TechWriterReview to configure paths.
echo REM This is automatically called by start_twr.bat
echo REM ============================================================================
echo.
echo REM Script directory
echo set "AEGIS_DIR=%SCRIPT_DIR%"
echo.
echo REM Local tools paths
echo set "LOCAL_TESSERACT=%LOCAL_TESSERACT%"
echo set "LOCAL_POPPLER=%LOCAL_POPPLER%"
echo.
echo REM Add local tools to PATH ^(for this session^)
echo if exist "%LOCAL_TESSERACT%\tesseract.exe" set "PATH=%LOCAL_TESSERACT%;%%PATH%%"
echo if exist "%LOCAL_POPPLER%\bin" set "PATH=%LOCAL_POPPLER%\bin;%%PATH%%"
echo.
echo REM Tesseract configuration
echo if exist "%LOCAL_TESSERACT%\tesseract.exe" ^(
echo     set "TESSERACT_CMD=%LOCAL_TESSERACT%\tesseract.exe"
echo     set "TESSDATA_PREFIX=%LOCAL_TESSERACT%\tessdata"
echo ^)
echo.
echo REM Poppler configuration ^(for pdf2image^)
echo if exist "%LOCAL_POPPLER%\bin" set "POPPLER_PATH=%LOCAL_POPPLER%\bin"
echo.
echo REM Docling/AI offline configuration
echo set "DOCLING_ARTIFACTS_PATH=%USER_CACHE%"
echo set "DOCLING_SERVE_ARTIFACTS_PATH=%USER_CACHE%"
echo set "HF_HUB_OFFLINE=1"
echo set "TRANSFORMERS_OFFLINE=1"
echo set "HF_DATASETS_OFFLINE=1"
echo set "HF_HUB_DISABLE_TELEMETRY=1"
echo set "DO_NOT_TRACK=1"
echo set "ANONYMIZED_TELEMETRY=false"
echo.
echo echo [AEGIS] Environment activated
echo if exist "%LOCAL_TESSERACT%\tesseract.exe" echo   - Tesseract: %LOCAL_TESSERACT%
echo if exist "%LOCAL_POPPLER%\bin" echo   - Poppler: %LOCAL_POPPLER%
echo echo   - Offline mode: ENABLED
) > "%SCRIPT_DIR%\activate_env.bat"

echo [OK] Created: activate_env.bat
echo.

REM Set persistent user-level environment variables
echo Setting user environment variables ^(no admin required^)...
setx DOCLING_ARTIFACTS_PATH "%USER_CACHE%" >nul 2>&1
setx HF_HUB_OFFLINE "1" >nul 2>&1
setx TRANSFORMERS_OFFLINE "1" >nul 2>&1

if exist "%LOCAL_TESSERACT%\tesseract.exe" (
    setx TESSERACT_CMD "%LOCAL_TESSERACT%\tesseract.exe" >nul 2>&1
    setx TESSDATA_PREFIX "%LOCAL_TESSERACT%\tessdata" >nul 2>&1
)

if exist "%LOCAL_POPPLER%\bin" (
    setx POPPLER_PATH "%LOCAL_POPPLER%\bin" >nul 2>&1
)

echo [OK] User environment variables set
echo.

REM ============================================================================
REM External Dependencies Notice (only for optional features)
REM ============================================================================
echo ============================================================
echo Optional External Dependencies
echo ============================================================
echo.
echo Most features work without additional installation.
echo The following are only needed for specific features:
echo.
echo   JAVA 8+ (grammar checking, Tabula tables):
echo     https://www.java.com/download/
echo.
echo   GHOSTSCRIPT (Camelot table extraction):
echo     https://ghostscript.com/releases/gsdnld.html
echo.

REM ============================================================================
REM Create Startup Scripts
REM ============================================================================
echo ============================================================
echo Creating startup scripts...
echo ============================================================
echo.

REM Main startup script with environment activation
(
echo @echo off
echo REM TechWriterReview v3.0.124 - Startup Script
echo REM Generated: %date%
echo.
echo cd /d "%SCRIPT_DIR%"
echo.
echo REM Activate AEGIS environment ^(sets paths for local tools^)
echo if exist "activate_env.bat" call activate_env.bat
echo.
echo echo.
echo echo ============================================================
echo echo TechWriterReview v3.0.124
echo echo ============================================================
echo echo.
echo echo Starting server...
echo echo Open browser to: http://localhost:5050
echo echo Press Ctrl+C to stop.
echo echo.
echo python app.py
echo pause
) > "%SCRIPT_DIR%start_twr.bat"

echo Created: start_twr.bat

REM ============================================================================
REM Summary
REM ============================================================================
echo.
echo ============================================================
if %CORE_OK%==1 (
    if %WARNINGS% GTR 0 (
        echo SETUP COMPLETE with %WARNINGS% warnings
    ) else (
        echo SETUP COMPLETE - All packages installed successfully!
    )
) else (
    echo SETUP COMPLETE with errors - check messages above
)
echo ============================================================
echo.
echo Installed components:
echo   [Core]        Flask, python-docx, openpyxl
echo   [PDF]         PyMuPDF, pdfplumber, Camelot, Tabula
echo   [OCR]         pytesseract, pdf2image, Pillow
echo   [NLP]         spaCy, scikit-learn, NLTK, textstat
echo   [Grammar]     language-tool-python
echo   [Fix Assist]  ReportLab, diff-match-patch (PDF reports, Document Comparison)
echo   [Headless]    Playwright (bot-protected site validation/rescan)
echo.
echo Local tools installed ^(no admin required^):
if exist "%LOCAL_TESSERACT%\tesseract.exe" (
    echo   [OCR]         Tesseract OCR at: %LOCAL_TESSERACT%
) else (
    echo   [OCR]         Tesseract not installed - see notes above
)
if exist "%LOCAL_POPPLER%\bin\pdftoppm.exe" (
    echo   [PDF2IMG]     Poppler at: %LOCAL_POPPLER%
) else (
    echo   [PDF2IMG]     Poppler not installed - PDF image OCR limited
)
echo.
echo To start TechWriterReview:
echo   Double-click: start_twr.bat
echo   Or run: activate_env.bat ^&^& python app.py
echo.
echo Then open: http://localhost:5050
echo.
echo ============================================================
echo For AI-powered document extraction ^(+7%% accuracy^):
echo   Run: setup_docling.bat
echo ============================================================
echo.
echo To verify PDF extraction capabilities:
echo   Run: python check_pdf_capabilities.py
echo.

if %CORE_OK%==1 (
    set /p START_NOW="Start TechWriterReview now? (Y/N): "
    if /i "!START_NOW!"=="Y" (
        echo.
        echo Starting TechWriterReview...
        echo Browser will open automatically when server is ready.
        python app.py
    )
)

pause
