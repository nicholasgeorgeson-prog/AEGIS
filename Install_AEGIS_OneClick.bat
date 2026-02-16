@echo off
setlocal enabledelayedexpansion
title AEGIS One-Click Installer v5.1.0
color 0B

echo.
echo  ============================================================
echo.
echo       A E G I S   I N S T A L L E R
echo.
echo       Aerospace Engineering Governance
echo       ^& Inspection System  v5.1.0
echo.
echo  ============================================================
echo.
echo  This will download and install AEGIS on your computer.
echo  No prior setup needed - everything is included.
echo.
echo  Press any key to begin, or close this window to cancel.
pause >nul

:: ============================================================
:: STEP 1: Choose where to install
:: ============================================================
echo.
echo  [Step 1 of 8] Where do you want to install AEGIS?
echo  ---------------------------------------------------
echo.
echo  A folder picker will open. Choose or create a folder.
echo  AEGIS will be installed inside an "AEGIS" subfolder there.
echo.

for /f "delims=" %%I in ('powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'Choose where to install AEGIS'; $f.RootFolder = 'MyComputer'; $f.ShowNewFolderButton = $true; if ($f.ShowDialog() -eq 'OK') { $f.SelectedPath } else { 'CANCELLED' }"') do set "PARENT=%%I"

if "%PARENT%"=="CANCELLED" (
    echo.
    echo  Installation cancelled. No changes were made.
    echo.
    pause
    exit /b 0
)

set "INSTALL_DIR=%PARENT%\AEGIS"
echo.
echo  Installing to: %INSTALL_DIR%
echo.

if exist "%INSTALL_DIR%\app.py" (
    echo  [NOTE] AEGIS is already installed here!
    echo  This will update/overwrite the existing installation.
    echo  Your scan history database will NOT be deleted.
    echo.
    set /p "CONFIRM=Continue? (Y/N): "
    if /i not "!CONFIRM!"=="Y" (
        echo  Installation cancelled.
        pause
        exit /b 0
    )
)

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\packaging" mkdir "%INSTALL_DIR%\packaging"
if not exist "%INSTALL_DIR%\packaging\wheels" mkdir "%INSTALL_DIR%\packaging\wheels"

:: ============================================================
:: STEP 2: Test internet connectivity
:: ============================================================
echo.
echo  [Step 2 of 8] Testing internet connection...
echo  ---------------------------------------------------

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'https://github.com' -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop; Write-Host 'OK' } catch { Write-Host 'FAIL' }" > "%TEMP%\aegis_net_test.txt" 2>nul
set /p NET_TEST=<"%TEMP%\aegis_net_test.txt"
del "%TEMP%\aegis_net_test.txt" >nul 2>nul

if not "%NET_TEST%"=="OK" (
    echo.
    echo  [ERROR] Cannot connect to GitHub!
    echo.
    echo  Please check:
    echo    - Your internet connection is active
    echo    - You can open https://github.com in a browser
    echo    - Your firewall/proxy allows HTTPS connections
    echo.
    pause
    exit /b 1
)
echo  [OK] Internet connection confirmed

:: ============================================================
:: STEP 3: Download AEGIS source code
:: ============================================================
echo.
echo  [Step 3 of 8] Downloading AEGIS source code...
echo  ---------------------------------------------------
echo.

set "REPO=nicholasgeorgeson-prog/AEGIS"
set "SRC_ZIP=%INSTALL_DIR%\aegis_source.zip"
:: Binary assets (Python, pip, models) hosted on v5.1.0 release
set "DL_BINARY=https://github.com/%REPO%/releases/download/v5.1.0"
:: Torch wheel hosted on v5.1.0-wheels release
set "DL_TORCH=https://github.com/%REPO%/releases/download/v5.1.0-wheels"

echo  Downloading latest source code from GitHub (main branch)...
echo  (This includes all dependency wheels - ~500 MB total)
echo  Please be patient, this may take 5-15 minutes...
echo.
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://github.com/%REPO%/archive/refs/heads/main.zip' -OutFile '%SRC_ZIP%' -UseBasicParsing -ErrorAction Stop; Write-Host 'SUCCESS' } catch { Write-Host \"DOWNLOAD_ERROR: $($_.Exception.Message)\" }" > "%TEMP%\aegis_dl_result.txt" 2>nul
set /p DL_RESULT=<"%TEMP%\aegis_dl_result.txt"
del "%TEMP%\aegis_dl_result.txt" >nul 2>nul

if not "%DL_RESULT%"=="SUCCESS" (
    echo.
    echo  [WARN] PowerShell download failed, trying curl...
    curl.exe -L -o "%SRC_ZIP%" "https://github.com/%REPO%/archive/refs/heads/main.zip" 2>nul
    if not exist "%SRC_ZIP%" (
        echo  [ERROR] Both download methods failed!
        echo  Please download manually from:
        echo    https://github.com/%REPO%
        pause
        exit /b 1
    )
)

if not exist "%SRC_ZIP%" (
    echo  [ERROR] Source code download produced no file!
    pause
    exit /b 1
)

echo  [OK] Source code downloaded
echo  Extracting...
powershell -NoProfile -Command "Expand-Archive -Path '%SRC_ZIP%' -DestinationPath '%INSTALL_DIR%\temp_extract' -Force" 2>nul

:: Move files from extracted subfolder to install dir
for /d %%D in ("%INSTALL_DIR%\temp_extract\AEGIS*") do (
    xcopy /E /I /Y /Q "%%D\*" "%INSTALL_DIR%\" >nul 2>nul
)
rmdir /S /Q "%INSTALL_DIR%\temp_extract" >nul 2>nul
del "%SRC_ZIP%" >nul 2>nul

if exist "%INSTALL_DIR%\app.py" (
    echo  [OK] Source code extracted
) else (
    echo  [ERROR] Source extraction failed!
    echo  The download may have been incomplete. Please try again.
    pause
    exit /b 1
)

:: The source archive includes wheels/ directory with all 195 dependency packages.
:: Copy them to the packaging/wheels location for installation.
if exist "%INSTALL_DIR%\wheels" (
    echo  Copying bundled wheels to packaging directory...
    xcopy /E /I /Y /Q "%INSTALL_DIR%\wheels\*" "%INSTALL_DIR%\packaging\wheels\" >nul 2>nul
    echo  [OK] Bundled wheels ready
)

:: ============================================================
:: STEP 4: Download Python + pip + torch
:: ============================================================
echo.
echo  [Step 4 of 8] Downloading Python, pip, and PyTorch...
echo  ---------------------------------------------------
echo.

:: Download Python embedded (8 MB)
echo  [1/3] Python 3.10.11 embedded (8 MB)...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_BINARY%/python-3.10.11-embed-amd64.zip' -OutFile '%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" (
    echo  [WARN] PowerShell download failed, trying curl...
    curl.exe -L -o "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" "%DL_BINARY%/python-3.10.11-embed-amd64.zip" 2>nul
)
if exist "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" (
    echo  [OK] Python downloaded
) else (
    echo  [ERROR] Python download failed!
    pause
    exit /b 1
)

:: Download pip (2 MB)
echo  [2/3] pip bootstrapper (2 MB)...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_BINARY%/get-pip.py' -OutFile '%INSTALL_DIR%\packaging\get-pip.py' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\get-pip.py" (
    curl.exe -L -o "%INSTALL_DIR%\packaging\get-pip.py" "%DL_BINARY%/get-pip.py" 2>nul
)
if exist "%INSTALL_DIR%\packaging\get-pip.py" (
    echo  [OK] pip downloaded
) else (
    echo  [ERROR] pip download failed!
    pause
    exit /b 1
)

:: Download PyTorch Windows x64 wheel from v5.1.0-wheels release (109 MB)
echo  [3/3] PyTorch for Windows x64 (109 MB)...
echo        (This may take 2-5 minutes)
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_TORCH%/torch-2.10.0-cp310-cp310-win_amd64.whl' -OutFile '%INSTALL_DIR%\packaging\wheels\torch-2.10.0-cp310-cp310-win_amd64.whl' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\wheels\torch-2.10.0-cp310-cp310-win_amd64.whl" (
    echo  [WARN] PowerShell failed, trying curl...
    curl.exe -L -o "%INSTALL_DIR%\packaging\wheels\torch-2.10.0-cp310-cp310-win_amd64.whl" "%DL_TORCH%/torch-2.10.0-cp310-cp310-win_amd64.whl" 2>nul
)
if exist "%INSTALL_DIR%\packaging\wheels\torch-2.10.0-cp310-cp310-win_amd64.whl" (
    echo  [OK] PyTorch downloaded
) else (
    echo  [WARN] PyTorch download failed - AI features will be limited
    echo         You can install it later with: pip install torch
)

:: Download NLP/ML models (240 MB) - hosted on v5.0.5 release (unchanged between versions)
set "DL_MODELS=https://github.com/%REPO%/releases/download/v5.0.5"
echo.
echo  Downloading NLP/ML models (240 MB)...
echo  (sentence-transformers, NLTK data)
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_MODELS%/aegis_models.zip' -OutFile '%INSTALL_DIR%\packaging\aegis_models.zip' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\aegis_models.zip" (
    echo  [WARN] PowerShell failed, trying curl...
    curl.exe -L -o "%INSTALL_DIR%\packaging\aegis_models.zip" "%DL_MODELS%/aegis_models.zip" 2>nul
)
if exist "%INSTALL_DIR%\packaging\aegis_models.zip" (
    echo  [OK] Models downloaded
    echo  Extracting models...
    powershell -NoProfile -Command "Expand-Archive -Path '%INSTALL_DIR%\packaging\aegis_models.zip' -DestinationPath '%INSTALL_DIR%\models' -Force" 2>nul
    del "%INSTALL_DIR%\packaging\aegis_models.zip" >nul 2>nul
    echo  [OK] Models extracted
) else (
    echo  [WARN] Models download failed - they will be downloaded on first use
    echo         ^(requires internet connection^)
)

:: ============================================================
:: STEP 5: Install Python
:: ============================================================
echo.
echo  [Step 5 of 8] Setting up Python environment...
echo  ---------------------------------------------------
echo.

set "PYTHON_DIR=%INSTALL_DIR%\python"
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"

echo  Installing Python 3.10.11...
powershell -NoProfile -Command "Expand-Archive -Path '%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip' -DestinationPath '%PYTHON_DIR%' -Force" 2>nul

if not exist "%PYTHON_DIR%\python.exe" (
    echo  [ERROR] Python installation failed!
    pause
    exit /b 1
)
echo  [OK] Python installed

:: Enable pip and local imports in embedded Python
set "PTH_FILE=%PYTHON_DIR%\python310._pth"
if exist "%PTH_FILE%" (
    powershell -NoProfile -Command "(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'"
    :: Add parent directory (..) so Python finds app modules one level up from python\ subfolder
    powershell -NoProfile -Command "Add-Content '%PTH_FILE%' '..'"
    echo  [OK] Python configured
)

:: Install pip
echo  Installing pip...
"%PYTHON_DIR%\python.exe" "%INSTALL_DIR%\packaging\get-pip.py" --no-warn-script-location 2>nul
echo  [OK] pip installed

:: ============================================================
:: STEP 6: Install Python packages
:: ============================================================
echo.
echo  [Step 6 of 8] Installing Python packages (195+ packages)...
echo  ---------------------------------------------------
echo.
echo  This takes 3-8 minutes. Please wait...
echo.

set "WHEELS=%INSTALL_DIR%\packaging\wheels"

:: Remove any Linux-only wheels that would cause confusion
del "%WHEELS%\*manylinux*aarch64*.whl" >nul 2>nul

:: Install core packages first
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location flask 2>nul
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location spacy beautifulsoup4 mammoth python-docx openpyxl pymupdf chardet requests 2>nul

:: Install torch first (large, has dependencies)
echo  Installing PyTorch...
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location torch 2>nul
if errorlevel 1 (
    echo  [WARN] PyTorch offline install failed, trying online...
    "%PYTHON_DIR%\python.exe" -m pip install torch --no-warn-script-location 2>nul
    if errorlevel 1 (
        echo  [WARN] PyTorch installation failed - AI features will be limited
    ) else (
        echo  [OK] PyTorch installed from PyPI
    )
) else (
    echo  [OK] PyTorch installed from bundled wheel
)

:: Install torchvision
echo  Installing TorchVision...
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location torchvision 2>nul

:: Install from requirements.txt
echo  Installing remaining packages from requirements.txt...
if exist "%INSTALL_DIR%\requirements.txt" (
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location -r "%INSTALL_DIR%\requirements.txt" 2>nul
)

:: Install any remaining wheels individually (catch stragglers)
for %%f in ("%WHEELS%\*.whl") do (
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --no-deps --no-warn-script-location "%%f" 2>nul
)

:: Install Playwright browser (for headless .mil/.gov link validation)
echo  Installing headless browser for link validation...
"%PYTHON_DIR%\python.exe" -m playwright install chromium --with-deps 2>nul
if errorlevel 1 (
    echo  [WARN] Playwright browser install failed - headless link validation will be unavailable
    echo         ^(This is optional - standard link checking still works^)
) else (
    echo  [OK] Headless browser installed
)

echo.
echo  [OK] All packages installed

:: ============================================================
:: STEP 7: Configure NLP models
:: ============================================================
echo.
echo  [Step 7 of 8] Configuring NLP models...
echo  ---------------------------------------------------
echo.

:: Install spaCy English model from bundled wheel
set "SPACY_MODEL_FOUND=0"
for %%f in ("%WHEELS%\en_core_web_sm*.whl") do (
    set "SPACY_MODEL_FOUND=1"
    echo  Installing spaCy English model from package...
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location "%%f" 2>nul
    echo  [OK] spaCy model installed
)
if "%SPACY_MODEL_FOUND%"=="0" (
    :: Try en_core_web_md if sm not available
    for %%f in ("%WHEELS%\en_core_web_md*.whl") do (
        set "SPACY_MODEL_FOUND=1"
        echo  Installing spaCy English model ^(medium^) from package...
        "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location "%%f" 2>nul
        echo  [OK] spaCy model installed
    )
)
if "%SPACY_MODEL_FOUND%"=="0" (
    echo  Downloading spaCy English model...
    "%PYTHON_DIR%\python.exe" -m spacy download en_core_web_sm --no-warn-script-location 2>nul
    if errorlevel 1 (
        echo  [WARN] spaCy model download failed - will retry on first launch
    ) else (
        echo  [OK] spaCy model downloaded
    )
)

:: Configure sentence-transformers model from bundled models
if exist "%INSTALL_DIR%\models\sentence_transformers" (
    echo  [OK] Sentence-transformers model ready ^(bundled^)
) else (
    echo  [NOTE] Sentence-transformers model will download on first use ^(~80 MB^)
)

:: Configure NLTK data from bundled models
if exist "%INSTALL_DIR%\models\nltk_data" (
    echo  [OK] NLTK data ready ^(bundled^)
) else (
    echo  [NOTE] NLTK data will download on first use ^(~120 MB^)
)

echo.
echo  [OK] NLP models configured

:: ============================================================
:: STEP 8: Create shortcuts and launcher scripts
:: ============================================================
echo.
echo  [Step 8 of 8] Creating shortcuts...
echo  ---------------------------------------------------

:: Create Start_AEGIS.bat
(
echo @echo off
echo title AEGIS v5.1.0
echo color 0B
echo echo.
echo echo  Starting AEGIS v5.1.0...
echo echo  Once started, open your browser to: http://localhost:5050
echo echo.
echo echo  DO NOT close this window while using AEGIS.
echo echo  Press Ctrl+C to stop the server.
echo echo.
echo cd /d "%INSTALL_DIR%"
echo set "HF_HUB_OFFLINE=1"
echo set "TRANSFORMERS_OFFLINE=1"
echo set "HF_HUB_DISABLE_TELEMETRY=1"
echo set "DO_NOT_TRACK=1"
echo set "TOKENIZERS_PARALLELISM=false"
echo if exist "%INSTALL_DIR%\models\nltk_data" set "NLTK_DATA=%INSTALL_DIR%\models\nltk_data"
echo if exist "%INSTALL_DIR%\models\sentence_transformers" set "SENTENCE_TRANSFORMERS_HOME=%INSTALL_DIR%\models\sentence_transformers"
echo "%PYTHON_DIR%\python.exe" app.py
echo echo.
echo echo  AEGIS has stopped.
echo pause
) > "%INSTALL_DIR%\Start_AEGIS.bat"
echo  [OK] Start_AEGIS.bat

:: Create Stop_AEGIS.bat
(
echo @echo off
echo echo Stopping AEGIS...
echo for /f "tokens=5" %%%%a in ^('netstat -aon 2^>nul ^| findstr :5050 ^| findstr LISTENING'^) do ^(
echo     taskkill /PID %%%%a /F ^>nul 2^>nul
echo ^)
echo echo AEGIS stopped.
echo timeout /t 2 /nobreak ^>nul
) > "%INSTALL_DIR%\Stop_AEGIS.bat"
echo  [OK] Stop_AEGIS.bat

:: Create Restart_AEGIS.bat
(
echo @echo off
echo echo Restarting AEGIS...
echo for /f "tokens=5" %%%%a in ^('netstat -aon 2^>nul ^| findstr :5050 ^| findstr LISTENING'^) do ^(
echo     taskkill /PID %%%%a /F ^>nul 2^>nul
echo ^)
echo timeout /t 3 /nobreak ^>nul
echo cd /d "%INSTALL_DIR%"
echo start "" "%INSTALL_DIR%\Start_AEGIS.bat"
) > "%INSTALL_DIR%\Restart_AEGIS.bat"
echo  [OK] Restart_AEGIS.bat

:: Create Export_Bugs.bat
(
echo @echo off
echo title AEGIS - Export Diagnostic Report
echo color 0E
echo echo.
echo echo  ============================================================
echo echo    AEGIS Diagnostic Export
echo echo  ============================================================
echo echo.
echo set "EXPORT_DIR=%%USERPROFILE%%\Desktop\AEGIS_Diagnostics"
echo if not exist "%%EXPORT_DIR%%" mkdir "%%EXPORT_DIR%%"
echo echo  Creating diagnostic package on your Desktop...
echo echo.
echo cd /d "%INSTALL_DIR%"
echo copy /y "%INSTALL_DIR%\version.json" "%%EXPORT_DIR%%\" ^>nul 2^>nul
echo copy /y "%INSTALL_DIR%\config.json" "%%EXPORT_DIR%%\" ^>nul 2^>nul
echo if exist "%INSTALL_DIR%\logs" xcopy /E /I /Y /Q "%INSTALL_DIR%\logs\*" "%%EXPORT_DIR%%\logs\" ^>nul 2^>nul
echo "%PYTHON_DIR%\python.exe" --version ^> "%%EXPORT_DIR%%\python_version.txt" 2^>^&1
echo "%PYTHON_DIR%\python.exe" -m pip list ^> "%%EXPORT_DIR%%\installed_packages.txt" 2^>^&1
echo systeminfo ^> "%%EXPORT_DIR%%\system_info.txt" 2^>nul
echo "%PYTHON_DIR%\python.exe" -c "from diagnostic_export import export_diagnostics; print(export_diagnostics('%%EXPORT_DIR%%'))" 2^>"%%EXPORT_DIR%%\diagnostic_errors.txt"
echo echo.
echo echo  [DONE] Diagnostic package saved to: %%EXPORT_DIR%%
echo echo  Please zip this folder and share it when reporting issues.
echo echo.
echo pause
) > "%INSTALL_DIR%\Export_Bugs.bat"
echo  [OK] Export_Bugs.bat

:: Create Desktop shortcut with AEGIS icon
set "ICON_FILE=%INSTALL_DIR%\static\img\aegis_icon.ico"
echo  Creating Desktop shortcut...
if exist "%ICON_FILE%" (
    powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS.lnk'); $s.TargetPath = '%INSTALL_DIR%\Start_AEGIS.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = '%ICON_FILE%,0'; $s.Description = 'Start AEGIS v5.1.0 - Document Analysis Tool'; $s.Save()" 2>nul
    echo  [OK] Desktop shortcut created with AEGIS icon
) else (
    powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS.lnk'); $s.TargetPath = '%INSTALL_DIR%\Start_AEGIS.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'Start AEGIS v5.1.0 - Document Analysis Tool'; $s.Save()" 2>nul
    echo  [OK] Desktop shortcut created
)

:: Clean up packaging directory to save space
echo  Cleaning up temporary files...
rmdir /S /Q "%INSTALL_DIR%\packaging" >nul 2>nul
echo  [OK] Cleanup complete

:: ============================================================
:: VERIFICATION
:: ============================================================
echo.
echo  Verifying installation...
echo  ---------------------------------------------------
echo.

"%PYTHON_DIR%\python.exe" -c "import flask; print('  [OK] Flask ' + flask.__version__)" 2>nul || echo  [FAIL] Flask
"%PYTHON_DIR%\python.exe" -c "import docx; print('  [OK] python-docx')" 2>nul || echo  [FAIL] python-docx
"%PYTHON_DIR%\python.exe" -c "import pandas; print('  [OK] Pandas ' + pandas.__version__)" 2>nul || echo  [FAIL] Pandas
"%PYTHON_DIR%\python.exe" -c "import numpy; print('  [OK] NumPy ' + numpy.__version__)" 2>nul || echo  [FAIL] NumPy
"%PYTHON_DIR%\python.exe" -c "import torch; print('  [OK] PyTorch ' + torch.__version__)" 2>nul || echo  [SKIP] PyTorch (optional - AI features)
"%PYTHON_DIR%\python.exe" -c "import spacy; print('  [OK] spaCy ' + spacy.__version__)" 2>nul || echo  [SKIP] spaCy (optional)
"%PYTHON_DIR%\python.exe" -c "import spacy; nlp=spacy.load('en_core_web_sm'); print('  [OK] spaCy en_core_web_sm model')" 2>nul || echo  [SKIP] spaCy model (optional)
"%PYTHON_DIR%\python.exe" -c "import fitz; print('  [OK] PyMuPDF')" 2>nul || echo  [FAIL] PyMuPDF
"%PYTHON_DIR%\python.exe" -c "import sklearn; print('  [OK] scikit-learn')" 2>nul || echo  [SKIP] scikit-learn (optional)
"%PYTHON_DIR%\python.exe" -c "import docling; print('  [OK] Docling')" 2>nul || echo  [SKIP] Docling (optional)
"%PYTHON_DIR%\python.exe" -c "import torchvision; print('  [OK] TorchVision ' + torchvision.__version__)" 2>nul || echo  [SKIP] TorchVision (optional)

:: ============================================================
:: DONE!
:: ============================================================
echo.
echo  ============================================================
echo.
echo       INSTALLATION COMPLETE!
echo.
echo  ============================================================
echo.
echo  AEGIS v5.1.0 installed to: %INSTALL_DIR%
echo.
echo  To start:
echo    1. Double-click "Start AEGIS" on your Desktop
echo    2. Open http://localhost:5050 in your browser
echo.
echo  Other scripts in install folder:
echo    Stop_AEGIS.bat    - Stop the server
echo    Restart_AEGIS.bat - Restart the server
echo    Export_Bugs.bat   - Create diagnostic package
echo.

set /p "START_NOW=Start AEGIS now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    echo.
    echo  Starting AEGIS...
    start "" "%INSTALL_DIR%\Start_AEGIS.bat"
    timeout /t 5 /nobreak >nul
    start "" "http://localhost:5050"
)

echo.
echo  Thank you for installing AEGIS!
echo.
pause
