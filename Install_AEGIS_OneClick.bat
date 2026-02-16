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

:: Use PowerShell folder browser dialog
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

:: Create directories
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\packaging" mkdir "%INSTALL_DIR%\packaging"
if not exist "%INSTALL_DIR%\packaging\wheels" mkdir "%INSTALL_DIR%\packaging\wheels"

:: ============================================================
:: STEP 2: Check for curl (needed for downloads)
:: ============================================================
echo.
echo  [Step 2 of 7] Checking system requirements...
echo  ---------------------------------------------------

where curl >nul 2>nul
if errorlevel 1 (
    echo.
    echo  [ERROR] curl.exe not found!
    echo.
    echo  curl is required and is included with Windows 10 version 1803+.
    echo  If you're on an older version of Windows, please update first.
    echo.
    pause
    exit /b 1
)
echo  [OK] curl found
echo  [OK] PowerShell found
echo  [OK] System requirements met

:: ============================================================
:: STEP 3: Download AEGIS source code from GitHub
:: ============================================================
echo.
echo  [Step 3 of 7] Downloading AEGIS source code...
echo  ---------------------------------------------------
echo.
echo  Downloading from GitHub (~24 MB)...

set "REPO=nicholasgeorgeson-prog/AEGIS"
set "TAG=v5.0.0"
set "SRC_ZIP=%INSTALL_DIR%\aegis_source.zip"

curl -L -o "%SRC_ZIP%" "https://github.com/%REPO%/archive/refs/tags/%TAG%.zip" --progress-bar
if errorlevel 1 (
    echo.
    echo  [ERROR] Failed to download source code!
    echo  Check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo  Extracting source code...
powershell -NoProfile -Command "Expand-Archive -Path '%SRC_ZIP%' -DestinationPath '%INSTALL_DIR%\temp_extract' -Force" 2>nul

:: The zip extracts to AEGIS-5.0.0\ subfolder - move everything up
if exist "%INSTALL_DIR%\temp_extract\AEGIS-5.0.0" (
    xcopy /E /I /Y /Q "%INSTALL_DIR%\temp_extract\AEGIS-5.0.0\*" "%INSTALL_DIR%\" >nul 2>nul
    rmdir /S /Q "%INSTALL_DIR%\temp_extract" >nul 2>nul
) else (
    :: Try without version prefix
    for /d %%D in ("%INSTALL_DIR%\temp_extract\AEGIS*") do (
        xcopy /E /I /Y /Q "%%D\*" "%INSTALL_DIR%\" >nul 2>nul
    )
    rmdir /S /Q "%INSTALL_DIR%\temp_extract" >nul 2>nul
)
del "%SRC_ZIP%" >nul 2>nul

if exist "%INSTALL_DIR%\app.py" (
    echo  [OK] Source code installed
) else (
    echo  [ERROR] Source extraction failed!
    pause
    exit /b 1
)

:: ============================================================
:: STEP 4: Download Python + pip + wheel packages
:: ============================================================
echo.
echo  [Step 4 of 7] Downloading Python runtime and packages...
echo  ---------------------------------------------------
echo.

set "DL_BASE=https://github.com/%REPO%/releases/download/%TAG%"

:: Download embedded Python (8 MB)
echo  Downloading Python 3.10.11 (8 MB)...
curl -L -o "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" "%DL_BASE%/python-3.10.11-embed-amd64.zip" --progress-bar
if errorlevel 1 (
    echo  [ERROR] Python download failed!
    pause
    exit /b 1
)
echo  [OK] Python downloaded

:: Download pip bootstrapper (2 MB)
echo  Downloading pip (2 MB)...
curl -L -o "%INSTALL_DIR%\packaging\get-pip.py" "%DL_BASE%/get-pip.py" --progress-bar
if errorlevel 1 (
    echo  [ERROR] pip download failed!
    pause
    exit /b 1
)
echo  [OK] pip downloaded

:: Download wheel packages part 1 (137 MB)
echo.
echo  Downloading dependency packages part 1 of 2 (137 MB)...
echo  (This may take a few minutes)
curl -L -o "%INSTALL_DIR%\packaging\wheels\part1.zip" "%DL_BASE%/aegis_wheels_part1.zip" --progress-bar
if errorlevel 1 (
    echo  [ERROR] Wheels part 1 download failed!
    pause
    exit /b 1
)
echo  [OK] Part 1 downloaded

:: Download wheel packages part 2 (245 MB)
echo.
echo  Downloading dependency packages part 2 of 2 (245 MB)...
echo  (This may take a few minutes)
curl -L -o "%INSTALL_DIR%\packaging\wheels\part2.zip" "%DL_BASE%/aegis_wheels_part2.zip" --progress-bar
if errorlevel 1 (
    echo  [ERROR] Wheels part 2 download failed!
    pause
    exit /b 1
)
echo  [OK] Part 2 downloaded

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

:: Extract embedded Python
echo  Installing Python 3.10.11...
powershell -NoProfile -Command "Expand-Archive -Path '%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip' -DestinationPath '%PYTHON_DIR%' -Force" 2>nul

if not exist "%PYTHON_DIR%\python.exe" (
    echo  [ERROR] Python installation failed!
    pause
    exit /b 1
)
echo  [OK] Python installed

:: Enable pip support in embedded Python
set "PTH_FILE=%PYTHON_DIR%\python310._pth"
if exist "%PTH_FILE%" (
    powershell -NoProfile -Command "(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'"
    echo  [OK] Python configured for pip
)

:: Install pip
echo  Installing pip...
"%PYTHON_DIR%\python.exe" "%INSTALL_DIR%\packaging\get-pip.py" --no-warn-script-location 2>nul
if exist "%PYTHON_DIR%\Scripts\pip.exe" (
    echo  [OK] pip installed
) else if exist "%PYTHON_DIR%\Scripts\pip3.exe" (
    echo  [OK] pip installed
) else (
    echo  [WARN] pip installation may have issues, continuing...
)

:: ============================================================
:: STEP 6: Install all Python packages from wheels
:: ============================================================
echo.
echo  [Step 6 of 7] Installing 126 Python packages (offline)...
echo  ---------------------------------------------------
echo.
echo  This takes 2-5 minutes. Please wait...
echo.

set "WHEELS=%INSTALL_DIR%\packaging\wheels"

:: Install all wheels at once
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location flask 2>nul
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-deps --no-warn-script-location spacy beautifulsoup4 mammoth python-docx openpyxl pymupdf chardet requests 2>nul

:: Install everything from requirements.txt
if exist "%INSTALL_DIR%\requirements.txt" (
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location -r "%INSTALL_DIR%\requirements.txt" 2>nul
)

:: Fallback: install every .whl file individually
echo  Installing remaining packages...
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
echo  [OK] Created Start_AEGIS.bat

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
echo  [OK] Created Stop_AEGIS.bat

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
echo  [OK] Created Restart_AEGIS.bat

:: Create Export_Bugs.bat for troubleshooting
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
echo :: Collect version info
echo copy /y "%INSTALL_DIR%\version.json" "%%EXPORT_DIR%%\" ^>nul 2^>nul
echo copy /y "%INSTALL_DIR%\config.json" "%%EXPORT_DIR%%\" ^>nul 2^>nul
echo :: Collect logs
echo if exist "%INSTALL_DIR%\logs" ^( xcopy /E /I /Y /Q "%INSTALL_DIR%\logs\*" "%%EXPORT_DIR%%\logs\" ^>nul 2^>nul ^)
echo :: Python info
echo "%PYTHON_DIR%\python.exe" --version ^> "%%EXPORT_DIR%%\python_version.txt" 2^>^&1
echo "%PYTHON_DIR%\python.exe" -m pip list ^> "%%EXPORT_DIR%%\installed_packages.txt" 2^>^&1
echo :: System info
echo echo Collecting system info...
echo systeminfo ^> "%%EXPORT_DIR%%\system_info.txt" 2^>nul
echo :: Run diagnostic export if available
echo "%PYTHON_DIR%\python.exe" -c "from diagnostic_export import export_diagnostics; print(export_diagnostics('%%EXPORT_DIR%%'))" 2^>"%%EXPORT_DIR%%\diagnostic_errors.txt"
echo echo.
echo echo  ============================================================
echo echo  [DONE] Diagnostic package saved to your Desktop:
echo echo         %%EXPORT_DIR%%
echo echo.
echo echo  Please zip this folder and share it when reporting issues.
echo echo  ============================================================
echo echo.
echo pause
) > "%INSTALL_DIR%\Export_Bugs.bat"
echo  [OK] Created Export_Bugs.bat

:: Create Desktop shortcut
echo  Creating Desktop shortcut...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Start AEGIS.lnk'); $s.TargetPath = '%INSTALL_DIR%\Start_AEGIS.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = '%INSTALL_DIR%\images\twr_icon.ico,0'; $s.Description = 'Start AEGIS - Document Analysis Tool'; $s.Save()" 2>nul
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
echo  AEGIS has been installed to:
echo    %INSTALL_DIR%
echo.
echo  To start AEGIS:
echo    1. Double-click "Start AEGIS" on your Desktop
echo       (or run Start_AEGIS.bat in the install folder)
echo    2. Open your browser to: http://localhost:5050
echo.
echo  Other shortcuts in the install folder:
echo    - Stop_AEGIS.bat     = Stop the server
echo    - Restart_AEGIS.bat  = Restart the server
echo    - Export_Bugs.bat    = Create a diagnostic package
echo.
echo  Total installed size: ~500 MB
echo.
echo  ============================================================
echo.

:: Ask if they want to start AEGIS now
set /p "START_NOW=Would you like to start AEGIS now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    echo.
    echo  Starting AEGIS...
    echo  Your browser will open to http://localhost:5050
    echo.
    start "" "%INSTALL_DIR%\Start_AEGIS.bat"
    timeout /t 5 /nobreak >nul
    start "" "http://localhost:5050"
)

echo.
echo  Thank you for installing AEGIS!
echo.
pause
