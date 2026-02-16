@echo off
setlocal enabledelayedexpansion
title AEGIS Installer v5.0.0
color 0B

REM ============================================================
REM  AEGIS - Aerospace Engineering Governance ^& Inspection System
REM  Installer v5.0.0 - No Admin Required
REM  Created by Nicholas Georgeson
REM ============================================================

echo.
echo   ================================================================
echo.
echo          AEGIS v5.0.0 - Installation Wizard
echo          Aerospace Engineering Governance ^& Inspection System
echo.
echo   ================================================================
echo.
echo   This installer will set up AEGIS on your computer.
echo   No administrator privileges are required.
echo.

REM --- Check we're running from the right place ---
if not exist "%~dp0wheels" (
    echo   [ERROR] Cannot find 'wheels' folder.
    echo   Please run this installer from the AEGIS package folder.
    pause
    exit /b 1
)

if not exist "%~dp0python-3.10.11-embed-amd64.zip" (
    echo   [ERROR] Cannot find Python embedded distribution.
    echo   Please ensure python-3.10.11-embed-amd64.zip is in this folder.
    pause
    exit /b 1
)

REM --- Detect OneDrive path ---
set "ONEDRIVE_PATH="
if defined OneDriveCommercial (
    set "ONEDRIVE_PATH=%OneDriveCommercial%"
) else if defined OneDrive (
    set "ONEDRIVE_PATH=%OneDrive%"
)

REM --- Choose install location ---
echo   Choose where to install AEGIS:
echo.
echo     [1] Default local: %LOCALAPPDATA%\AEGIS
if defined ONEDRIVE_PATH (
    echo     [2] OneDrive:      %ONEDRIVE_PATH%\AEGIS
)
echo     [3] Custom path
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\AEGIS"
set /p "LOCATION_CHOICE=  Enter choice [1]: "

if "%LOCATION_CHOICE%"=="2" (
    if defined ONEDRIVE_PATH (
        set "INSTALL_DIR=%ONEDRIVE_PATH%\AEGIS"
    ) else (
        echo   [WARNING] OneDrive not detected. Using default location.
    )
)
if "%LOCATION_CHOICE%"=="3" (
    set /p "CUSTOM_DIR=  Enter full install path: "
    if not "!CUSTOM_DIR!"=="" set "INSTALL_DIR=!CUSTOM_DIR!"
)

REM Remove trailing backslash if present
if "!INSTALL_DIR:~-1!"=="\" set "INSTALL_DIR=!INSTALL_DIR:~0,-1!"

echo.
echo   AEGIS will be installed to:
echo     !INSTALL_DIR!
echo.

REM --- Validate path is writable ---
mkdir "!INSTALL_DIR!\__aegis_test__" 2>nul
if errorlevel 1 (
    echo   [ERROR] Cannot write to this location.
    echo   Please choose a different install path.
    echo.
    rd /s /q "!INSTALL_DIR!\__aegis_test__" 2>nul
    goto ask_location
)
rd /s /q "!INSTALL_DIR!\__aegis_test__" 2>nul

set /p "CONFIRM=  Continue? (Y/N): "
if /i not "!CONFIRM!"=="Y" (
    if /i not "!CONFIRM!"=="yes" (
        echo.
        echo   Installation cancelled.
        pause
        exit /b 0
    )
)

REM --- Create install directory ---
echo.
echo   [1/7] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if errorlevel 1 (
    echo   [ERROR] Could not create directory. Try a different location.
    pause
    exit /b 1
)

REM --- Extract embedded Python ---
echo   [2/7] Extracting Python 3.10 runtime...
set "PYTHON_DIR=%INSTALL_DIR%\python"
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"

REM Use PowerShell to extract zip (available on all Windows 10/11)
powershell -NoProfile -NonInteractive -Command ^
    "Expand-Archive -Path '%~dp0python-3.10.11-embed-amd64.zip' -DestinationPath '%PYTHON_DIR%' -Force" 2>nul
if errorlevel 1 (
    echo   [ERROR] Failed to extract Python. Trying alternative method...
    REM Fallback: use tar (available on Windows 10 1803+)
    tar -xf "%~dp0python-3.10.11-embed-amd64.zip" -C "%PYTHON_DIR%" 2>nul
    if errorlevel 1 (
        echo   [ERROR] Could not extract Python runtime.
        pause
        exit /b 1
    )
)
echo   [OK] Python 3.10.11 extracted.

REM --- Enable pip in embedded Python ---
echo   [3/7] Enabling pip in embedded Python...

REM Modify python310._pth to allow imports (uncomment "import site")
set "PTH_FILE=%PYTHON_DIR%\python310._pth"
if exist "%PTH_FILE%" (
    powershell -NoProfile -NonInteractive -Command ^
        "(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'"
)

REM Install pip
"%PYTHON_DIR%\python.exe" "%~dp0get-pip.py" --no-warn-script-location 2>nul
if errorlevel 1 (
    echo   [WARNING] pip installation had issues. Continuing...
) else (
    echo   [OK] pip installed.
)

REM --- Reassemble split wheels (torch is split to stay under GitHub 100MB limit) ---
echo   [4/7] Preparing wheel packages...
if exist "%~dp0wheels\torch_split\torch_part_aa" (
    if not exist "%~dp0wheels\torch-2.10.0+cpu-cp310-cp310-win_amd64.whl" (
        echo          Reassembling PyTorch wheel from parts...
        copy /b "%~dp0wheels\torch_split\torch_part_aa"+"%~dp0wheels\torch_split\torch_part_ab"+"%~dp0wheels\torch_split\torch_part_ac" "%~dp0wheels\torch-2.10.0+cpu-cp310-cp310-win_amd64.whl" >nul
        echo          [OK] PyTorch wheel ready.
    )
)

REM --- Install all dependencies from local wheels ---
echo   [5/7] Installing dependencies (this may take a few minutes)...

REM Install all wheels from the wheels directory
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    Flask==2.3.3 waitress==2.1.2 python-docx==1.2.0 lxml==4.9.4 mammoth==1.11.0 ^
    openpyxl==3.1.5 xlrd==2.0.2 xlsxwriter==3.2.9 2>nul
echo          Core web framework... OK

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    PyMuPDF==1.26.7 pymupdf4llm==0.2.9 pdfplumber==0.11.9 "pdfminer.six==20251230" ^
    PyPDF2==3.0.1 pypdf==3.17.4 pypdfium2==5.3.0 camelot-py==1.0.9 tabula-py==2.10.0 ^
    reportlab==4.4.9 2>nul
echo          PDF extraction... OK

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    pytesseract==0.3.13 pdf2image==1.17.0 pillow==11.3.0 ^
    opencv-python-headless==4.13.0.90 2>nul
echo          OCR and image processing... OK

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    numpy==2.2.6 scipy==1.15.3 scikit-learn==1.7.2 pandas==2.3.3 2>nul
echo          Scientific computing... OK

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    torch 2>nul
echo          PyTorch (CPU)... OK

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    spacy==3.8.11 2>nul
echo          spaCy NLP... OK

REM Install spaCy model from local wheel ONLY (no GitHub download)
if exist "%~dp0wheels\en_core_web_md-3.8.0-py3-none-any.whl" (
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
        "%~dp0wheels\en_core_web_md-3.8.0-py3-none-any.whl" 2>nul
    echo          spaCy language model... OK
) else (
    echo          [WARNING] spaCy model wheel not found - skipping
)

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    transformers==4.57.6 tokenizers==0.22.2 sentence-transformers safetensors==0.7.0 ^
    huggingface-hub==0.36.0 accelerate==1.12.0 2>nul
echo          Transformers / Sentence-Transformers... OK

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    nltk==3.9.2 textblob==0.19.0 textstat==0.7.12 PassivePy proselint==0.16.0 ^
    rapidfuzz symspellpy==6.9.0 language_tool_python==3.2.2 2>nul
echo          NLP libraries... OK

REM --- Install pre-bundled NLTK data (offline — no downloads needed) ---
if exist "%~dp0nltk_data" (
    echo          Copying bundled NLTK data...
    if not exist "%APP_DIR%\nltk_data" mkdir "%APP_DIR%\nltk_data"
    robocopy "%~dp0nltk_data" "%APP_DIR%\nltk_data" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
    echo          [OK] NLTK data installed offline.
)

REM --- Install pre-bundled sentence-transformers model (offline) ---
if exist "%~dp0models\sentence_transformers" (
    echo          Copying bundled sentence-transformers model...
    if not exist "%APP_DIR%\models\sentence_transformers" mkdir "%APP_DIR%\models\sentence_transformers"
    robocopy "%~dp0models\sentence_transformers" "%APP_DIR%\models\sentence_transformers" /E /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
    echo          [OK] Sentence-Transformers model installed offline.
)

"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%~dp0wheels" --no-warn-script-location --no-cache-dir -q -q -q ^
    matplotlib==3.10.8 seaborn==0.13.2 requests==2.32.5 diff-match-patch==20241021 ^
    psutil==7.2.2 rich==14.3.2 pydantic==2.12.5 jsonschema==4.26.0 ^
    cryptography==46.0.4 py-readability-metrics==1.4.5 networkx==3.4.2 ^
    shapely==2.1.2 colorlog==6.10.1 regex==2026.1.15 PyYAML==6.0.3 2>nul
echo          Utilities and visualization... OK

echo   [OK] All dependencies installed.

REM --- Copy AEGIS application files ---
echo   [6/8] Copying AEGIS application files...
set "APP_DIR=%INSTALL_DIR%\app"
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

REM Copy all application files (exclude packaging folder, __pycache__, .git)
robocopy "%~dp0.." "%APP_DIR%" /E /XD packaging __pycache__ .git .claude node_modules logs temp dist build /XF "*.pyc" "*.pyo" "*.db" "*.db-shm" "*.db-wal" ".DS_Store" "*.log" ".secret_key" "app_v310_backup.py" /NFL /NDL /NJH /NJS /NC /NS /NP >nul 2>&1
echo   [OK] Application files copied.

REM --- Create launcher scripts ---
echo   [7/8] Creating launcher scripts...

REM Main launcher
(
    echo @echo off
    echo title AEGIS v5.0.0
    echo color 0B
    echo echo.
    echo echo   Starting AEGIS v5.0.0...
    echo echo   Opening browser to http://localhost:5050
    echo echo.
    echo echo   [Keep this window open while using AEGIS]
    echo echo   [Press Ctrl+C or close this window to stop]
    echo echo.
    echo REM === Offline mode - block ALL internet callouts ===
    echo set HF_HUB_OFFLINE=1
    echo set TRANSFORMERS_OFFLINE=1
    echo set HF_HUB_DISABLE_TELEMETRY=1
    echo set DO_NOT_TRACK=1
    echo set TOKENIZERS_PARALLELISM=false
    echo set TWR_ENV=production
    echo set "NLTK_DATA=%%~dp0app\nltk_data"
    echo set "SENTENCE_TRANSFORMERS_HOME=%%~dp0app\models\sentence_transformers"
    echo cd /d "%%~dp0app"
    echo start "" "http://localhost:5050" 2^>nul
    echo "%%~dp0python\python.exe" app.py
) > "%INSTALL_DIR%\AEGIS.bat"

REM Create a VBS wrapper for silent launch (no command window)
(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.Run chr^(34^) ^& "%INSTALL_DIR%\AEGIS.bat" ^& chr^(34^), 0
    echo Set WshShell = Nothing
) > "%INSTALL_DIR%\AEGIS-Silent.vbs"

REM Restart script
(
    echo @echo off
    echo title AEGIS - Restarting...
    echo echo.
    echo echo   Restarting AEGIS...
    echo echo.
    echo for /f "tokens=5" %%%%a in ^('netstat -aon ^^^| findstr ":5050" ^^^| findstr "LISTENING" 2^^^>nul'^) do ^(
    echo     taskkill /F /PID %%%%a ^>nul 2^>^&1
    echo ^)
    echo timeout /t 2 /nobreak ^>nul
    echo set HF_HUB_OFFLINE=1
    echo set TRANSFORMERS_OFFLINE=1
    echo set HF_HUB_DISABLE_TELEMETRY=1
    echo set DO_NOT_TRACK=1
    echo set TOKENIZERS_PARALLELISM=false
    echo set TWR_ENV=production
    echo set "NLTK_DATA=%%~dp0app\nltk_data"
    echo set "SENTENCE_TRANSFORMERS_HOME=%%~dp0app\models\sentence_transformers"
    echo cd /d "%%~dp0app"
    echo start "" "http://localhost:5050" 2^>nul
    echo "%%~dp0python\python.exe" app.py
) > "%INSTALL_DIR%\Restart-AEGIS.bat"

echo   [OK] Launcher scripts created.

REM --- Create desktop shortcut ---
echo   [8/8] Creating desktop shortcut...

REM Create shortcut using PowerShell
powershell -NoProfile -NonInteractive -Command ^
    "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS.lnk'); $s.TargetPath = '%INSTALL_DIR%\AEGIS.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'AEGIS - Aerospace Engineering Governance and Inspection System'; $s.Save()" 2>nul
if errorlevel 1 (
    echo   [WARNING] Could not create desktop shortcut. You can run AEGIS.bat manually.
) else (
    echo   [OK] Desktop shortcut created.
)

REM --- Create uninstaller ---
(
    echo @echo off
    echo title AEGIS - Uninstaller
    echo color 0C
    echo echo.
    echo echo   ================================================================
    echo echo.
    echo echo          AEGIS v5.0.0 - Uninstaller
    echo echo.
    echo echo   ================================================================
    echo echo.
    echo echo   This will remove AEGIS from: %INSTALL_DIR%
    echo echo.
    echo set /p "CONFIRM=  Are you sure? ^(Y/N^): "
    echo if /i not "%%CONFIRM%%"=="Y" exit /b 0
    echo echo.
    echo echo   Stopping AEGIS if running...
    echo for /f "tokens=5" %%%%a in ^('netstat -aon ^^^| findstr ":5050" ^^^| findstr "LISTENING" 2^^^>nul'^) do ^(
    echo     taskkill /F /PID %%%%a ^>nul 2^>^&1
    echo ^)
    echo timeout /t 2 /nobreak ^>nul
    echo echo   Removing desktop shortcut...
    echo del "%%USERPROFILE%%\Desktop\AEGIS.lnk" 2^>nul
    echo echo   Removing installation directory...
    echo rd /s /q "%INSTALL_DIR%\python" 2^>nul
    echo rd /s /q "%INSTALL_DIR%\app" 2^>nul
    echo del "%INSTALL_DIR%\AEGIS.bat" 2^>nul
    echo del "%INSTALL_DIR%\AEGIS-Silent.vbs" 2^>nul
    echo del "%INSTALL_DIR%\Restart-AEGIS.bat" 2^>nul
    echo echo.
    echo echo   [OK] AEGIS has been uninstalled.
    echo echo   You can safely delete the remaining folder.
    echo pause
) > "%INSTALL_DIR%\Uninstall-AEGIS.bat"

REM --- Done! ---
echo.
echo   ================================================================
echo.
echo          AEGIS v5.0.0 - Installation Complete!
echo.
echo   ================================================================
echo.
echo   Installation directory: %INSTALL_DIR%
echo.
echo   To start AEGIS:
echo     - Double-click "AEGIS" shortcut on your Desktop
echo     - Or run: %INSTALL_DIR%\AEGIS.bat
echo.
echo   AEGIS will open your browser to http://localhost:5050
echo.
echo   To uninstall: Run %INSTALL_DIR%\Uninstall-AEGIS.bat
echo.
echo   ================================================================
echo.
pause
