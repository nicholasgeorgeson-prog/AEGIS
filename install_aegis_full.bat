@echo off
setlocal enabledelayedexpansion
title AEGIS Installer v5.0.0
color 0B

echo.
echo  ============================================================
echo    AEGIS - Aerospace Engineering Governance ^& Inspection System
echo    Full Installer v5.0.0
echo  ============================================================
echo.
echo  This installer will set up AEGIS on your Windows computer.
echo  No existing Python installation is required.
echo.

:: ============================================================
:: STEP 1: Choose installation folder
:: ============================================================
echo  [Step 1/8] Choose Installation Folder
echo  ------------------------------------------------------------
set "INSTALL_DIR=C:\AEGIS"
echo  Default location: %INSTALL_DIR%
echo.

:: Use PowerShell folder picker dialog
echo  Opening folder picker...
for /f "delims=" %%I in ('powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'Choose AEGIS Installation Folder'; $f.SelectedPath = 'C:\'; $f.ShowNewFolderButton = $true; if ($f.ShowDialog() -eq 'OK') { $f.SelectedPath } else { 'CANCELLED' }"') do set "SELECTED=%%I"

if "%SELECTED%"=="CANCELLED" (
    echo  Installation cancelled.
    pause
    exit /b 0
)
if "%SELECTED%"=="" (
    echo  No folder selected, using default: %INSTALL_DIR%
) else (
    set "INSTALL_DIR=%SELECTED%\AEGIS"
)

echo  Installing to: %INSTALL_DIR%
echo.

:: Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\packaging" mkdir "%INSTALL_DIR%\packaging"
if not exist "%INSTALL_DIR%\packaging\wheels" mkdir "%INSTALL_DIR%\packaging\wheels"

:: ============================================================
:: STEP 2: Locate or download source files
:: ============================================================
echo  [Step 2/8] Locating Source Files
echo  ------------------------------------------------------------

set "SOURCE_DIR="
set "NEED_DOWNLOAD=0"

:: Check if running from within a downloaded package
if exist "%~dp0app.py" (
    set "SOURCE_DIR=%~dp0"
    echo  [OK] Source code found in current directory
) else if exist "%~dp0AEGIS\app.py" (
    set "SOURCE_DIR=%~dp0AEGIS"
    echo  [OK] Source code found in AEGIS subfolder
) else (
    echo  [INFO] Source code not found locally.
    set "NEED_DOWNLOAD=1"
)

:: Check for packaging files
set "NEED_WHEELS=0"
set "NEED_PYTHON=0"
set "NEED_PIP=0"

:: Look in multiple locations for wheels
if exist "%~dp0packaging\wheels\*.whl" (
    set "WHEELS_DIR=%~dp0packaging\wheels"
) else if exist "%~dp0wheels\*.whl" (
    set "WHEELS_DIR=%~dp0wheels"
) else if exist "%~dp0AEGIS\packaging\wheels\*.whl" (
    set "WHEELS_DIR=%~dp0AEGIS\packaging\wheels"
) else (
    set "NEED_WHEELS=1"
)

if exist "%~dp0python-3.10.11-embed-amd64.zip" (
    set "PYTHON_ZIP=%~dp0python-3.10.11-embed-amd64.zip"
) else if exist "%~dp0packaging\python-3.10.11-embed-amd64.zip" (
    set "PYTHON_ZIP=%~dp0packaging\python-3.10.11-embed-amd64.zip"
) else (
    set "NEED_PYTHON=1"
)

if exist "%~dp0get-pip.py" (
    set "PIP_PY=%~dp0get-pip.py"
) else if exist "%~dp0packaging\get-pip.py" (
    set "PIP_PY=%~dp0packaging\get-pip.py"
) else (
    set "NEED_PIP=1"
)

:: Download missing files if needed
if "%NEED_DOWNLOAD%"=="1" (
    echo  [INFO] Downloading AEGIS from GitHub...
    set "REPO=nicholasgeorgeson-prog/AEGIS"
    set "TAG=v5.0.0"
    set "DL_BASE=https://github.com/!REPO!/releases/download/!TAG!"

    :: Download source
    echo  Downloading source code...
    curl -L -o "%INSTALL_DIR%\aegis_source.zip" "https://github.com/!REPO!/archive/refs/tags/!TAG!.zip" --progress-bar
    powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\aegis_source.zip' -DestinationPath '%INSTALL_DIR%' -Force" 2>nul
    if exist "%INSTALL_DIR%\AEGIS-5.0.0" (
        xcopy /E /I /Y "%INSTALL_DIR%\AEGIS-5.0.0\*" "%INSTALL_DIR%\" >nul 2>nul
        rmdir /S /Q "%INSTALL_DIR%\AEGIS-5.0.0" >nul 2>nul
    )
    del "%INSTALL_DIR%\aegis_source.zip" 2>nul
    set "SOURCE_DIR=%INSTALL_DIR%"
    echo  [OK] Source code downloaded
)

if "%NEED_PYTHON%"=="1" (
    echo  Downloading Python 3.10.11 embedded...
    curl -L -o "%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip" "https://github.com/nicholasgeorgeson-prog/AEGIS/releases/download/v5.0.0/python-3.10.11-embed-amd64.zip" --progress-bar
    set "PYTHON_ZIP=%INSTALL_DIR%\packaging\python-3.10.11-embed-amd64.zip"
    echo  [OK] Python embedded downloaded
)

if "%NEED_PIP%"=="1" (
    echo  Downloading pip bootstrapper...
    curl -L -o "%INSTALL_DIR%\packaging\get-pip.py" "https://github.com/nicholasgeorgeson-prog/AEGIS/releases/download/v5.0.0/get-pip.py" --progress-bar
    set "PIP_PY=%INSTALL_DIR%\packaging\get-pip.py"
    echo  [OK] get-pip.py downloaded
)

if "%NEED_WHEELS%"=="1" (
    echo  Downloading dependency wheels (part 1/2)...
    curl -L -o "%INSTALL_DIR%\packaging\wheels\part1.zip" "https://github.com/nicholasgeorgeson-prog/AEGIS/releases/download/v5.0.0/aegis_wheels_part1.zip" --progress-bar
    echo  Downloading dependency wheels (part 2/2)...
    curl -L -o "%INSTALL_DIR%\packaging\wheels\part2.zip" "https://github.com/nicholasgeorgeson-prog/AEGIS/releases/download/v5.0.0/aegis_wheels_part2.zip" --progress-bar
    echo  Extracting wheels...
    powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\packaging\wheels\part1.zip' -DestinationPath '%INSTALL_DIR%\packaging\wheels' -Force" 2>nul
    powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\packaging\wheels\part2.zip' -DestinationPath '%INSTALL_DIR%\packaging\wheels' -Force" 2>nul
    del "%INSTALL_DIR%\packaging\wheels\part1.zip" 2>nul
    del "%INSTALL_DIR%\packaging\wheels\part2.zip" 2>nul
    set "WHEELS_DIR=%INSTALL_DIR%\packaging\wheels"
    echo  [OK] All wheels downloaded and extracted
)

:: ============================================================
:: STEP 3: Copy source files to installation directory
:: ============================================================
echo.
echo  [Step 3/8] Copying Application Files
echo  ------------------------------------------------------------
if defined SOURCE_DIR (
    if not "%SOURCE_DIR%"=="%INSTALL_DIR%" (
        echo  Copying from %SOURCE_DIR% to %INSTALL_DIR%...
        xcopy /E /I /Y "%SOURCE_DIR%\*" "%INSTALL_DIR%\" >nul 2>nul
        echo  [OK] Application files copied
    ) else (
        echo  [OK] Files already in installation directory
    )
) else (
    echo  [OK] Files already in place
)

:: ============================================================
:: STEP 4: Install embedded Python
:: ============================================================
echo.
echo  [Step 4/8] Installing Embedded Python 3.10.11
echo  ------------------------------------------------------------
set "PYTHON_DIR=%INSTALL_DIR%\python"
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"

if defined PYTHON_ZIP (
    powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force" 2>nul
    echo  [OK] Python 3.10.11 installed to %PYTHON_DIR%
) else (
    echo  [WARN] Python embed not found - checking if already installed...
    if exist "%PYTHON_DIR%\python.exe" (
        echo  [OK] Python already installed
    ) else (
        echo  [ERROR] Python embed missing! Download python-3.10.11-embed-amd64.zip
        echo          from the GitHub Release and place it in the packaging folder.
    )
)

:: Enable pip in embedded Python
set "PTH_FILE=%PYTHON_DIR%\python310._pth"
if exist "%PTH_FILE%" (
    powershell -Command "(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'"
    echo  [OK] Enabled import site in Python
)

:: ============================================================
:: STEP 5: Install pip
:: ============================================================
echo.
echo  [Step 5/8] Installing pip
echo  ------------------------------------------------------------
set "PIP_TARGET=%PYTHON_DIR%\get-pip.py"
if defined PIP_PY (
    copy "%PIP_PY%" "%PIP_TARGET%" >nul 2>nul
)

if exist "%PIP_TARGET%" (
    "%PYTHON_DIR%\python.exe" "%PIP_TARGET%" --no-warn-script-location 2>nul
    echo  [OK] pip installed
) else if exist "%PYTHON_DIR%\Scripts\pip.exe" (
    echo  [OK] pip already installed
) else (
    echo  [ERROR] get-pip.py not found!
)

:: ============================================================
:: STEP 6: Install dependencies from wheels
:: ============================================================
echo.
echo  [Step 6/8] Installing Python Dependencies (126 packages)
echo  ------------------------------------------------------------

:: Find wheels directory
set "FINAL_WHEELS="
if defined WHEELS_DIR (
    set "FINAL_WHEELS=%WHEELS_DIR%"
) else if exist "%INSTALL_DIR%\packaging\wheels\*.whl" (
    set "FINAL_WHEELS=%INSTALL_DIR%\packaging\wheels"
)

if defined FINAL_WHEELS (
    echo  Installing from: %FINAL_WHEELS%
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%FINAL_WHEELS%" --no-deps --no-warn-script-location flask spacy beautifulsoup4 mammoth python-docx openpyxl pymupdf pymupdf4llm chardet requests 2>nul
    "%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%FINAL_WHEELS%" --no-deps --no-warn-script-location -r "%INSTALL_DIR%\requirements.txt" 2>nul
    echo  [OK] Dependencies installed
) else (
    echo  [WARN] No wheel files found! Dependencies must be installed manually.
    echo         Run: python -m pip install -r requirements.txt
)

:: ============================================================
:: STEP 7: Configure updater and create launcher scripts
:: ============================================================
echo.
echo  [Step 7/8] Creating Launcher Scripts
echo  ------------------------------------------------------------

:: Create Start script
(
echo @echo off
echo title AEGIS v5.0.0
echo cd /d "%INSTALL_DIR%"
echo echo Starting AEGIS...
echo "%PYTHON_DIR%\python.exe" app.py
echo if errorlevel 1 ^(
echo     echo.
echo     echo AEGIS encountered an error. Check the logs above.
echo     pause
echo ^)
) > "%INSTALL_DIR%\Start_AEGIS.bat"

:: Create Stop script
(
echo @echo off
echo echo Stopping AEGIS...
echo for /f "tokens=5" %%%%a in ^('netstat -aon ^| findstr :5050 ^| findstr LISTENING'^) do ^(
echo     taskkill /PID %%%%a /F ^>nul 2^>nul
echo ^)
echo echo AEGIS stopped.
echo timeout /t 2 /nobreak ^>nul
) > "%INSTALL_DIR%\Stop_AEGIS.bat"

:: Create Restart script
(
echo @echo off
echo echo Restarting AEGIS...
echo call "%INSTALL_DIR%\Stop_AEGIS.bat"
echo timeout /t 2 /nobreak ^>nul
echo call "%INSTALL_DIR%\Start_AEGIS.bat"
) > "%INSTALL_DIR%\Restart_AEGIS.bat"

:: Create Export Bugs script
(
echo @echo off
echo title AEGIS - Export Diagnostic Report
echo cd /d "%INSTALL_DIR%"
echo echo.
echo echo  ============================================================
echo echo    AEGIS Diagnostic Export
echo echo  ============================================================
echo echo.
echo echo  This will create a diagnostic package for troubleshooting.
echo echo.
echo set "EXPORT_DIR=%%USERPROFILE%%\Desktop\AEGIS_Diagnostics_%%date:~-4%%%%date:~4,2%%%%date:~7,2%%"
echo if not exist "%%EXPORT_DIR%%" mkdir "%%EXPORT_DIR%%"
echo echo  Exporting to: %%EXPORT_DIR%%
echo echo.
echo :: Copy logs
echo if exist "%INSTALL_DIR%\logs" xcopy /E /I /Y "%INSTALL_DIR%\logs\*" "%%EXPORT_DIR%%\logs\" ^>nul 2^>nul
echo :: Copy version info
echo copy "%INSTALL_DIR%\version.json" "%%EXPORT_DIR%%\" ^>nul 2^>nul
echo copy "%INSTALL_DIR%\config.json" "%%EXPORT_DIR%%\" ^>nul 2^>nul
echo :: Python info
echo "%PYTHON_DIR%\python.exe" --version ^> "%%EXPORT_DIR%%\python_version.txt" 2^>^&1
echo "%PYTHON_DIR%\python.exe" -m pip list ^> "%%EXPORT_DIR%%\pip_packages.txt" 2^>^&1
echo :: System info
echo systeminfo ^> "%%EXPORT_DIR%%\system_info.txt" 2^>nul
echo :: Export database diagnostics
echo "%PYTHON_DIR%\python.exe" -c "from diagnostic_export import export_diagnostics; export_diagnostics('%%EXPORT_DIR%%')" 2^>nul
echo echo.
echo echo  [OK] Diagnostic package created at:
echo echo       %%EXPORT_DIR%%
echo echo.
echo echo  Please share this folder when reporting issues.
echo pause
) > "%INSTALL_DIR%\Export_Bugs.bat"

:: Configure update_manager.py with correct paths
set "UPDATE_CONFIG=%INSTALL_DIR%\config.json"
if exist "%UPDATE_CONFIG%" (
    powershell -Command "$c = Get-Content '%UPDATE_CONFIG%' | ConvertFrom-Json; $c | Add-Member -NotePropertyName 'install_dir' -NotePropertyValue '%INSTALL_DIR%' -Force; $c | Add-Member -NotePropertyName 'python_dir' -NotePropertyValue '%PYTHON_DIR%' -Force; $c | Add-Member -NotePropertyName 'github_repo' -NotePropertyValue 'nicholasgeorgeson-prog/AEGIS' -Force; $c | ConvertTo-Json -Depth 10 | Set-Content '%UPDATE_CONFIG%'" 2>nul
)

echo  [OK] Created Start_AEGIS.bat
echo  [OK] Created Stop_AEGIS.bat
echo  [OK] Created Restart_AEGIS.bat
echo  [OK] Created Export_Bugs.bat

:: ============================================================
:: STEP 8: Create Desktop shortcut
:: ============================================================
echo.
echo  [Step 8/8] Creating Desktop Shortcut
echo  ------------------------------------------------------------
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS.lnk'); $s.TargetPath = '%INSTALL_DIR%\Start_AEGIS.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'AEGIS - Aerospace Engineering Governance and Inspection System'; $s.Save()" 2>nul
echo  [OK] Desktop shortcut created

:: ============================================================
:: DONE
:: ============================================================
echo.
echo  ============================================================
echo    Installation Complete!
echo  ============================================================
echo.
echo  AEGIS has been installed to: %INSTALL_DIR%
echo.
echo  Quick Start:
echo    - Double-click "AEGIS" shortcut on your Desktop
echo    - Or run: %INSTALL_DIR%\Start_AEGIS.bat
echo    - Open browser to: http://localhost:5050
echo.
echo  Troubleshooting:
echo    - Run Export_Bugs.bat to create a diagnostic package
echo    - Check logs in: %INSTALL_DIR%\logs\
echo.
echo  Updates:
echo    - Check for updates at: https://github.com/nicholasgeorgeson-prog/AEGIS/releases
echo    - The app will notify you when updates are available
echo.
pause
