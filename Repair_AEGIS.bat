@echo off
setlocal enabledelayedexpansion
title AEGIS Repair Tool v5.9.26
color 0E

:: ============================================================================
:: AEGIS Repair Tool - Fix Missing/Broken Dependencies
:: ============================================================================
:: Diagnoses and repairs Python package issues without re-running the full
:: installer. Shows actual error messages instead of suppressing them.
::
:: Usage: Double-click this file from the AEGIS installation directory
::        OR place it in the AEGIS folder and run it
:: ============================================================================

echo.
echo  ============================================================
echo.
echo      AEGIS Repair Tool v5.9.26
echo      Diagnose ^& Fix Missing Dependencies
echo.
echo  ============================================================
echo.

:: ============================================================
:: PHASE 1: Find AEGIS Installation
:: ============================================================
echo  [Phase 1] Locating AEGIS installation...
echo  ---------------------------------------------------
echo.

:: Try current directory first
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

:: Check if we're in the AEGIS directory (has python subfolder)
if exist "%INSTALL_DIR%\python\python.exe" (
    set "PYTHON_DIR=%INSTALL_DIR%\python"
    echo  [OK] Found AEGIS at: %INSTALL_DIR%
    goto :found_python
)

:: Try common locations
for %%d in (
    "C:\AEGIS"
    "%USERPROFILE%\Desktop\AEGIS"
    "%USERPROFILE%\Desktop\Doc Review\AEGIS"
    "%USERPROFILE%\OneDrive\Desktop\AEGIS"
    "%USERPROFILE%\OneDrive\Desktop\Doc Review\AEGIS"
    "%USERPROFILE%\OneDrive - NGC\Desktop\AEGIS"
    "%USERPROFILE%\OneDrive - NGC\Desktop\Doc Review\AEGIS"
) do (
    if exist "%%~d\python\python.exe" (
        set "INSTALL_DIR=%%~d"
        set "PYTHON_DIR=%%~d\python"
        echo  [OK] Found AEGIS at: %%~d
        goto :found_python
    )
)

echo  [ERROR] Could not find AEGIS installation!
echo  Please run this script from your AEGIS folder.
echo.
set /p "CUSTOM_DIR=  Enter AEGIS path (e.g., C:\AEGIS): "
if exist "%CUSTOM_DIR%\python\python.exe" (
    set "INSTALL_DIR=%CUSTOM_DIR%"
    set "PYTHON_DIR=%CUSTOM_DIR%\python"
    echo  [OK] Found AEGIS at: %CUSTOM_DIR%
    goto :found_python
)
echo  [ERROR] No python\python.exe found at that path.
pause
exit /b 1

:found_python
echo.

:: ============================================================
:: PHASE 2: Environment Checks
:: ============================================================
echo  [Phase 2] Checking Python environment...
echo  ---------------------------------------------------
echo.

:: Show Python version
"%PYTHON_DIR%\python.exe" --version 2>&1
echo.

:: Check python310._pth file
set "PTH_FILE=%PYTHON_DIR%\python310._pth"
if exist "%PTH_FILE%" (
    findstr /C:"#import site" "%PTH_FILE%" >nul 2>nul
    if not errorlevel 1 (
        echo  [FIXING] python310._pth: "import site" is commented out
        echo           Enabling site-packages...
        powershell -NoProfile -Command "(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'"
        echo  [OK] Fixed python310._pth
    ) else (
        echo  [OK] python310._pth: site-packages enabled
    )
) else (
    echo  [WARN] No python310._pth file found
)

:: Check sys.path includes site-packages
echo.
echo  Checking sys.path...
"%PYTHON_DIR%\python.exe" -c "import sys; sp=[p for p in sys.path if 'site-packages' in p]; print('  [OK] site-packages on path: ' + sp[0] if sp else '  [FAIL] site-packages NOT on sys.path!')"
echo.

:: ============================================================
:: PHASE 3: Diagnose - Test Each Critical Package
:: ============================================================
echo  [Phase 3] Diagnosing package imports (errors shown)...
echo  ---------------------------------------------------
echo.

set "FAIL_COUNT=0"
set "PASS_COUNT=0"
set "FAILED_PACKAGES="

:: --- Core Framework ---
echo  --- Core Framework ---
call :check_import flask "flask" "Core Web Framework"
call :check_import waitress "waitress" "Production Server"

:: --- Document Processing ---
echo.
echo  --- Document Processing ---
call :check_import docx "python-docx" "Word Document Processing"
call :check_import mammoth "mammoth" "DOCX-to-HTML Conversion"
call :check_import lxml "lxml" "XML Processing"
call :check_import openpyxl "openpyxl" "Excel Processing"

:: --- PDF ---
echo.
echo  --- PDF Processing ---
call :check_import fitz "PyMuPDF" "PDF Text Extraction"
call :check_import pdfplumber "pdfplumber" "PDF Table Extraction"

:: --- NLP Core (spaCy dependency chain) ---
echo.
echo  --- NLP Core (spaCy dependency chain) ---
call :check_import cymem "cymem" "spaCy: Memory Management"
call :check_import murmurhash "murmurhash" "spaCy: Hash Functions"
call :check_import preshed "preshed" "spaCy: Pre-hashed Data"
call :check_import blis "blis" "spaCy: Linear Algebra"
call :check_import srsly "srsly" "spaCy: Serialization"
call :check_import thinc "thinc" "spaCy: ML Framework"
call :check_import spacy "spacy" "NLP Engine"

:: --- spaCy Model ---
echo.
echo  --- spaCy Model ---
"%PYTHON_DIR%\python.exe" -c "import spacy; nlp=spacy.load('en_core_web_sm'); print('  [OK] en_core_web_sm (' + nlp.meta['version'] + ')')" 2>&1 && (
    set /a PASS_COUNT+=1
) || (
    set /a FAIL_COUNT+=1
    set "FAILED_PACKAGES=!FAILED_PACKAGES! en_core_web_sm"
    echo  [FAIL] en_core_web_sm - spaCy English model
)

:: --- NLP Libraries ---
echo.
echo  --- NLP Libraries ---
call :check_import sklearn "scikit-learn" "ML/Clustering"
call :check_import nltk "nltk" "Text Processing"
call :check_import textstat "textstat" "Readability Metrics"
call :check_import textblob "textblob" "Sentiment Analysis"
call :check_import rapidfuzz "rapidfuzz" "Fuzzy Matching"
call :check_import symspellpy "symspellpy" "Spell Checking"

:: --- Data Libraries ---
echo.
echo  --- Data Libraries ---
call :check_import pandas "pandas" "Data Analysis"
call :check_import numpy "numpy" "Numerical Computing"
call :check_import requests "requests" "HTTP Client"
call :check_import reportlab "reportlab" "PDF Report Generation"
call :check_import colorama "colorama" "Terminal Colors (Windows)"

:: --- Optional Packages ---
echo.
echo  --- Optional Packages ---
call :check_import_opt torch "PyTorch" "AI/Deep Learning"
call :check_import_opt docling "Docling" "AI Document Extraction"
call :check_import_opt requests_negotiate_sspi "SSPI Auth" "Windows SSO"
call :check_import_opt requests_ntlm "NTLM Auth" "Windows Domain Auth"

echo.
echo  ---------------------------------------------------
echo  Results: !PASS_COUNT! passed, !FAIL_COUNT! failed
echo  ---------------------------------------------------
echo.

if !FAIL_COUNT!==0 (
    echo  All packages are working! No repairs needed.
    goto :check_nltk
)

:: ============================================================
:: PHASE 4: Repair Failed Packages
:: ============================================================
echo  [Phase 4] Attempting to repair !FAIL_COUNT! failed package(s)...
echo  ---------------------------------------------------
echo.
echo  Failed packages: !FAILED_PACKAGES!
echo.

:: Look for wheels directory
set "WHEELS="
if exist "%INSTALL_DIR%\packaging\wheels" set "WHEELS=%INSTALL_DIR%\packaging\wheels"
if exist "%INSTALL_DIR%\wheels" set "WHEELS=%INSTALL_DIR%\wheels"

if defined WHEELS (
    echo  [OK] Found wheels at: %WHEELS%
) else (
    echo  [NOTE] No bundled wheels found. Will try online install.
)
echo.

:: ---- Step 4a: Install colorama FIRST (it's needed by spaCy and Flask on Windows) ----
echo !FAILED_PACKAGES! | findstr /i "colorama" >nul
if not errorlevel 1 (
    echo  [PRIORITY] Installing colorama (required by spaCy and Flask on Windows)...
    if defined WHEELS (
        "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location colorama 2>&1
        if errorlevel 1 (
            echo  [NOTE] colorama not in wheels, trying online...
            "%PYTHON_DIR%\python.exe" -m pip install --no-warn-script-location colorama 2>&1
        )
    ) else (
        "%PYTHON_DIR%\python.exe" -m pip install --no-warn-script-location colorama 2>&1
    )
    echo.
)

:: ---- Step 4b: If spaCy or any C extension dep failed, reinstall the whole chain ----
echo !FAILED_PACKAGES! | findstr /i "spacy cymem murmurhash preshed blis srsly thinc" >nul
if not errorlevel 1 (
    echo  Reinstalling spaCy and ALL dependencies together...
    echo  (This ensures version compatibility across the chain)
    echo.
    if defined WHEELS (
        "%PYTHON_DIR%\python.exe" -m pip install --force-reinstall --no-index --find-links="%WHEELS%" --no-warn-script-location spacy cymem murmurhash preshed blis srsly thinc wasabi weasel catalogue confection colorama 2>&1
        if errorlevel 1 (
            echo.
            echo  [NOTE] Offline spaCy reinstall failed. Trying with online fallback for missing deps...
            "%PYTHON_DIR%\python.exe" -m pip install --force-reinstall --find-links="%WHEELS%" --no-warn-script-location spacy 2>&1
        )
    ) else (
        "%PYTHON_DIR%\python.exe" -m pip install --force-reinstall --no-warn-script-location spacy 2>&1
    )
    echo.
)

:: ---- Step 4c: Repair each remaining failed package individually ----
for %%p in (!FAILED_PACKAGES!) do (
    :: Skip packages already handled above
    echo %%p | findstr /i "spacy cymem murmurhash preshed blis srsly thinc colorama en_core_web_sm" >nul
    if errorlevel 1 (
        echo  Reinstalling %%p...
        if defined WHEELS (
            "%PYTHON_DIR%\python.exe" -m pip install --force-reinstall --no-index --find-links="%WHEELS%" --no-warn-script-location %%p 2>&1
            if errorlevel 1 (
                echo  [NOTE] Offline install failed for %%p, trying online...
                "%PYTHON_DIR%\python.exe" -m pip install --force-reinstall --no-warn-script-location %%p 2>&1
            )
        ) else (
            "%PYTHON_DIR%\python.exe" -m pip install --force-reinstall --no-warn-script-location %%p 2>&1
        )
        echo.
    )
)

:: ---- Step 4d: Handle en_core_web_sm separately ----
echo !FAILED_PACKAGES! | findstr /i "en_core_web_sm" >nul
if not errorlevel 1 (
    echo  Reinstalling spaCy English model...
    set "SM_FOUND=0"
    if defined WHEELS (
        for %%f in ("%WHEELS%\en_core_web_sm*.whl") do (
            echo  Installing from wheel: %%~nxf
            "%PYTHON_DIR%\python.exe" -m pip install --force-reinstall --no-warn-script-location "%%f" 2>&1
            set "SM_FOUND=1"
        )
    )
    if "!SM_FOUND!"=="0" (
        echo  Downloading en_core_web_sm from internet...
        "%PYTHON_DIR%\python.exe" -m spacy download en_core_web_sm 2>&1
    )
    echo.
)

:: ============================================================
:: PHASE 5: NLTK Data Check
:: ============================================================
:check_nltk
echo.
echo  [Phase 5] Checking NLTK data...
echo  ---------------------------------------------------
echo.

"%PYTHON_DIR%\python.exe" -c "import nltk; nltk.data.find('corpora/wordnet'); print('  [OK] wordnet')" 2>nul || (
    echo  [FIXING] wordnet missing - downloading...
    "%PYTHON_DIR%\python.exe" -c "import ssl; ssl._create_default_https_context=ssl._create_unverified_context; import nltk; nltk.download('wordnet', quiet=True); nltk.download('omw-1.4', quiet=True)" 2>nul
)
"%PYTHON_DIR%\python.exe" -c "import nltk; nltk.data.find('tokenizers/punkt'); print('  [OK] punkt')" 2>nul || (
    echo  [FIXING] punkt missing - downloading...
    "%PYTHON_DIR%\python.exe" -c "import ssl; ssl._create_default_https_context=ssl._create_unverified_context; import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)" 2>nul
)
"%PYTHON_DIR%\python.exe" -c "import nltk; nltk.data.find('corpora/stopwords'); print('  [OK] stopwords')" 2>nul || (
    echo  [FIXING] stopwords missing - downloading...
    "%PYTHON_DIR%\python.exe" -c "import ssl; ssl._create_default_https_context=ssl._create_unverified_context; import nltk; nltk.download('stopwords', quiet=True)" 2>nul
)
"%PYTHON_DIR%\python.exe" -c "import nltk; nltk.data.find('taggers/averaged_perceptron_tagger_eng'); print('  [OK] tagger_eng')" 2>nul || (
    echo  [FIXING] tagger_eng missing - downloading...
    "%PYTHON_DIR%\python.exe" -c "import ssl; ssl._create_default_https_context=ssl._create_unverified_context; import nltk; nltk.download('averaged_perceptron_tagger_eng', quiet=True)" 2>nul
)

:: Fix wordnet zip extraction bug
"%PYTHON_DIR%\python.exe" -c "import zipfile, os; p=os.path.join(os.path.expanduser('~'),'nltk_data','corpora','wordnet.zip'); d=os.path.join(os.path.expanduser('~'),'nltk_data','corpora','wordnet'); (zipfile.ZipFile(p).extractall(os.path.dirname(p)) if os.path.exists(p) and not os.path.isdir(d) else None)" 2>nul

echo.

:: ============================================================
:: PHASE 6: Final Verification
:: ============================================================
echo  [Phase 6] Final Verification (all errors visible)...
echo  ---------------------------------------------------
echo.

set "FINAL_PASS=0"
set "FINAL_FAIL=0"

:: Verify each critical package
call :verify_final flask "Flask"
call :verify_final docx "python-docx"
call :verify_final mammoth "mammoth"
call :verify_final lxml "lxml"
call :verify_final openpyxl "openpyxl"
call :verify_final fitz "PyMuPDF"
call :verify_final pandas "Pandas"
call :verify_final numpy "NumPy"
call :verify_final requests "requests"
call :verify_final waitress "waitress"
call :verify_final colorama "colorama"
call :verify_final cymem "cymem"
call :verify_final thinc "thinc"
call :verify_final spacy "spaCy"
call :verify_final sklearn "scikit-learn"
call :verify_final nltk "NLTK"
call :verify_final reportlab "reportlab"

:: spaCy model
"%PYTHON_DIR%\python.exe" -c "import spacy; nlp=spacy.load('en_core_web_sm'); print('  [OK] spaCy en_core_web_sm model')" 2>&1 && (
    set /a FINAL_PASS+=1
) || (
    echo  [FAIL] spaCy en_core_web_sm model
    set /a FINAL_FAIL+=1
)

:: Optional (don't count as failures)
echo.
echo  --- Optional ---
call :verify_optional torch "PyTorch"
call :verify_optional docling "Docling"
call :verify_optional requests_negotiate_sspi "SSPI Auth"
call :verify_optional requests_ntlm "NTLM Auth"

:: ============================================================
:: SUMMARY
:: ============================================================
echo.
echo  ============================================================
echo.
echo      Repair Complete
echo.
echo      Passed: !FINAL_PASS!
if !FINAL_FAIL! GTR 0 (
    echo      FAILED: !FINAL_FAIL! (see error messages above^)
    echo.
    echo      If packages still fail, the actual error messages
    echo      above show exactly why. Common fixes:
    echo.
    echo      1. Missing wheel: Download the .whl file and place
    echo         it in the wheels folder, then re-run this script.
    echo      2. DLL error: Reinstall Visual C++ Redistributable.
    echo      3. Version conflict: Delete python\Lib\site-packages
    echo         and re-run the full OneClick installer.
) else (
    echo      Failed: 0
    echo.
    echo      All packages are working!
)
echo.
echo  ============================================================
echo.
pause
exit /b 0

:: ============================================================
:: SUBROUTINES
:: ============================================================

:check_import
:: %1 = Python module name, %2 = pip package name, %3 = description
:: Uses && / || for reliable success/fail detection (no temp files)
"%PYTHON_DIR%\python.exe" -c "import %~1; print('  [OK] %~3')" 2>&1 && (
    set /a PASS_COUNT+=1
) || (
    echo  [FAIL] %~3 (%~2^)
    set /a FAIL_COUNT+=1
    set "FAILED_PACKAGES=!FAILED_PACKAGES! %~2"
)
goto :eof

:check_import_opt
:: %1 = Python module name, %2 = display name, %3 = description
"%PYTHON_DIR%\python.exe" -c "import %~1; print('  [OK] %~2 - %~3')" 2>nul && (
    set /a PASS_COUNT+=1
) || (
    echo  [SKIP] %~2 - %~3 (optional, not critical^)
)
goto :eof

:verify_final
:: %1 = Python module name, %2 = display name
"%PYTHON_DIR%\python.exe" -c "import %~1; print('  [OK] %~2')" 2>&1 && (
    set /a FINAL_PASS+=1
) || (
    echo  [FAIL] %~2 - STILL BROKEN
    set /a FINAL_FAIL+=1
)
goto :eof

:verify_optional
:: %1 = Python module name, %2 = display name
"%PYTHON_DIR%\python.exe" -c "import %~1; print('  [OK] %~2 (optional)')" 2>nul && (
    set /a FINAL_PASS+=1
) || (
    echo  [SKIP] %~2 (optional^)
)
goto :eof
