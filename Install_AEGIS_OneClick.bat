@echo off
setlocal enabledelayedexpansion
title AEGIS One-Click Installer v5.0.0
color 0B

echo.
echo  ============================================================
echo.
echo       A E G I S   I N S T A L L E R
echo.
echo       Aerospace Engineering Governance
echo       ^& Inspection System  v5.0.0
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
echo  [Step 1 of 7] Where do you want to install AEGIS?
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
echo  [Step 2 of 7] Testing internet connection...
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
echo  [Step 3 of 7] Downloading AEGIS source code...
echo  ---------------------------------------------------
echo.

set "REPO=nicholasgeorgeson-prog/AEGIS"
set "TAG=v5.0.0"
set "SRC_ZIP=%INSTALL_DIR%\aegis_source.zip"
set "DL_BASE=https://github.com/%REPO%/releases/download/%TAG%"

echo  Downloading source code from GitHub...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://github.com/%REPO%/archive/refs/tags/%TAG%.zip' -OutFile '%SRC_ZIP%' -UseBasicParsing -ErrorAction Stop; Write-Host 'SUCCESS' } catch { Write-Host \"DOWNLOAD_ERROR: $($_.Exception.Message)\" }" > "%TEMP%\aegis_dl_result.txt" 2>nul
set /p DL_RESULT=<"%TEMP%\aegis_dl_result.txt"
del "%TEMP%\aegis_dl_result.txt" >nul 2>nul

if not "%DL_RESULT%"=="SUCCESS" (
    echo.
    echo  [ERROR] Failed to download source code!
    echo  %DL_RESULT%
    echo.
    echo  Trying alternative method with curl...
    curl.exe -L -o "%SRC_ZIP%" "https://github.com/%REPO%/archive/refs/tags/%TAG%.zip" 2>nul
    if not exist "%SRC_ZIP%" (
        echo  [ERROR] Both download methods failed!
        echo  Please download manually from:
        echo    https://github.com/%REPO%/releases/tag/%TAG%
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

:: ============================================================
:: STEP 4: Download Python + pip + wheels
:: ============================================================
echo.
echo  [Step 4 of 7] Downloading Python and dependencies...
echo  ---------------------------------------------------
echo.
echo  This downloads ~400 MB total. Please be patient.
echo.

:: Helper function - download with PowerShell, fallback to curl
:: Download Python embedded (8 MB)
echo  [1/4] Python 3.10.11 embedded (8 MB)...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_BASE%/python-3.10.11-embed-amd64.zip' -OutFile '%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" (
    echo  [WARN] PowerShell download failed, trying curl...
    curl.exe -L -o "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" "%DL_BASE%/python-3.10.11-embed-amd64.zip" 2>nul
)
if exist "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" (
    echo  [OK] Python downloaded
) else (
    echo  [ERROR] Python download failed!
    pause
    exit /b 1
)

:: Download pip (2 MB)
echo  [2/4] pip bootstrapper (2 MB)...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_BASE%/get-pip.py' -OutFile '%INSTALL_DIR%\packaging\get-pip.py' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\get-pip.py" (
    curl.exe -L -o "%INSTALL_DIR%\packaging\get-pip.py" "%DL_BASE%/get-pip.py" 2>nul
)
if exist "%INSTALL_DIR%\packaging\get-pip.py" (
    echo  [OK] pip downloaded
) else (
    echo  [ERROR] pip download failed!
    pause
    exit /b 1
)

:: Download wheels part 1 (137 MB)
echo  [3/4] Dependency packages part 1 (137 MB)...
echo        (This may take 2-5 minutes)
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_BASE%/aegis_wheels_part1.zip' -OutFile '%INSTALL_DIR%\packaging\wheels\part1.zip' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\wheels\part1.zip" (
    echo  [WARN] PowerShell failed, trying curl...
    curl.exe -L -o "%INSTALL_DIR%\packaging\wheels\part1.zip" "%DL_BASE%/aegis_wheels_part1.zip" 2>nul
)
if exist "%INSTALL_DIR%\packaging\wheels\part1.zip" (
    echo  [OK] Part 1 downloaded
) else (
    echo  [ERROR] Wheels part 1 download failed!
    pause
    exit /b 1
)

:: Download wheels part 2 (245 MB)
echo  [4/4] Dependency packages part 2 (245 MB)...
echo        (This may take 3-8 minutes)
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DL_BASE%/aegis_wheels_part2.zip' -OutFile '%INSTALL_DIR%\packaging\wheels\part2.zip' -UseBasicParsing" 2>nul
if not exist "%INSTALL_DIR%\packaging\wheels\part2.zip" (
    echo  [WARN] PowerShell failed, trying curl...
    curl.exe -L -o "%INSTALL_DIR%\packaging\wheels\part2.zip" "%DL_BASE%/aegis_wheels_part2.zip" 2>nul
)
if exist "%INSTALL_DIR%\packaging\wheels\part2.zip" (
    echo  [OK] Part 2 downloaded
) else (
    echo  [ERROR] Wheels part 2 download failed!
    pause
    exit /b 1
)

:: Extract wheel packages
echo.
echo  Extracting dependency packages...
powershell -NoProfile -Command "Expand-Archive -Path '%INSTALL_DIR%\packaging\wheels\part1.zip' -DestinationPath '%INSTALL_DIR%\packaging\wheels' -Force" 2>nul
powershell -NoProfile -Command "Expand-Archive -Path '%INSTALL_DIR%\packaging\wheels\part2.zip' -DestinationPath '%INSTALL_DIR%\packaging\wheels' -Force" 2>nul
del "%INSTALL_DIR%\packaging\wheels\part1.zip" >nul 2>nul
del "%INSTALL_DIR%\packaging\wheels\part2.zip" >nul 2>nul
echo  [OK] All packages extracted

:: ============================================================
:: STEP 5: Install Python
:: ============================================================
echo.
echo  [Step 5 of 7] Setting up Python environment...
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

:: Enable pip in embedded Python
set "PTH_FILE=%PYTHON_DIR%\python310._pth"
if exist "%PTH_FILE%" (
    powershell -NoProfile -Command "(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'"
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
echo  [Step 6 of 7] Installing 126 Python packages...
echo  ---------------------------------------------------
echo.
echo  This takes 2-5 minutes. Please wait...
echo.

set "WHEELS=%INSTALL_DIR%\packaging\wheels"

:: Install core packages first
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location flask 2>nul
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location spacy beautifulsoup4 mammoth python-docx openpyxl pymupdf chardet requests 2>nul

:: Install from requirements.txt
if exist "%INSTALL_DIR%\requirements.txt" (
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location -r "%INSTALL_DIR%\requirements.txt" 2>nul
)

:: Install any remaining wheels individually
for %%f in ("%WHEELS%\*.whl") do (
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --no-deps --no-warn-script-location "%%f" 2>nul
)

echo.
echo  [OK] All packages installed

:: ============================================================
:: STEP 7: Create shortcuts and launcher scripts
:: ============================================================
echo.
echo  [Step 7 of 7] Creating shortcuts...
echo  ---------------------------------------------------

:: Create Start_AEGIS.bat
(
echo @echo off
echo title AEGIS v5.0.0
echo color 0B
echo echo.
echo echo  Starting AEGIS...
echo echo  Once started, open your browser to: http://localhost:5050
echo echo.
echo echo  DO NOT close this window while using AEGIS.
echo echo  Press Ctrl+C to stop the server.
echo echo.
echo cd /d "%INSTALL_DIR%"
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

:: Create Desktop shortcut
echo  Creating Desktop shortcut...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Start AEGIS.lnk'); $s.TargetPath = '%INSTALL_DIR%\Start_AEGIS.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'Start AEGIS - Document Analysis Tool'; $s.Save()" 2>nul
echo  [OK] Desktop shortcut created

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
echo  AEGIS installed to: %INSTALL_DIR%
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
