@echo off
setlocal EnableDelayedExpansion
title AEGIS - Update Desktop Shortcuts
color 0A

echo.
echo  ================================================================
echo.
echo      A E G I S   -   S H O R T C U T   U P D A T E R
echo.
echo      Updates all desktop shortcuts and launchers to point
echo      to the current AEGIS installation directory.
echo.
echo  ================================================================
echo.

:: ── Detect install directory (where this script is located) ──────
set "INSTALL_DIR=%~dp0"
:: Remove trailing backslash for clean display
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo   Current AEGIS location:
echo     %INSTALL_DIR%
echo.

:: ── Verify this is actually an AEGIS installation ────────────────
if not exist "%INSTALL_DIR%\app.py" (
    echo   [ERROR] app.py not found in this directory.
    echo   Please run this script from your AEGIS installation folder.
    echo.
    pause
    exit /b 1
)

:: ── Find icon files ──────────────────────────────────────────────
set "ICON_FILE="
if exist "%INSTALL_DIR%\static\img\aegis_icon.ico" (
    set "ICON_FILE=%INSTALL_DIR%\static\img\aegis_icon.ico"
) else if exist "%INSTALL_DIR%\static\favicon.ico" (
    set "ICON_FILE=%INSTALL_DIR%\static\favicon.ico"
) else if exist "%INSTALL_DIR%\static\img\favicon.ico" (
    set "ICON_FILE=%INSTALL_DIR%\static\img\favicon.ico"
)

:: ── Find Manager icon file ──────────────────────────────────────
set "MGR_ICON_FILE="
if exist "%INSTALL_DIR%\static\img\aegis_manager_icon.ico" (
    set "MGR_ICON_FILE=%INSTALL_DIR%\static\img\aegis_manager_icon.ico"
)

:: ── Get version for description ──────────────────────────────────
set "VERSION=6.7"
if exist "%INSTALL_DIR%\version.json" (
    for /f "tokens=2 delims=:, " %%v in ('findstr /i "version" "%INSTALL_DIR%\version.json"') do (
        set "VERSION=%%~v"
    )
)

echo   Detected version: v%VERSION%
echo.

:: ── Step 1: Update AEGIS desktop shortcut ────────────────────────
echo   [Step 1 of 4]  Updating AEGIS desktop shortcut...

set "SC_TARGET=%INSTALL_DIR%\Start_AEGIS.bat"
if not exist "%SC_TARGET%" (
    :: Try alternate starter names
    if exist "%INSTALL_DIR%\start_aegis.bat" set "SC_TARGET=%INSTALL_DIR%\start_aegis.bat"
    if exist "%INSTALL_DIR%\Run_TWR.bat" set "SC_TARGET=%INSTALL_DIR%\Run_TWR.bat"
)

if exist "%SC_TARGET%" (
    if defined ICON_FILE (
        powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS.lnk'); $s.TargetPath = '%SC_TARGET%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = '%ICON_FILE%,0'; $s.Description = 'Start AEGIS v%VERSION% - Document Analysis Tool'; $s.Save(); Write-Host '    [OK] AEGIS.lnk updated'" 2>nul
    ) else (
        powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS.lnk'); $s.TargetPath = '%SC_TARGET%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'Start AEGIS v%VERSION% - Document Analysis Tool'; $s.Save(); Write-Host '    [OK] AEGIS.lnk updated'" 2>nul
    )
) else (
    echo     [SKIP] Start_AEGIS.bat not found - no AEGIS shortcut to create
)

echo.

:: ── Step 2: Update AEGIS Manager shortcut (if exists) ────────────
echo   [Step 2 of 4]  Updating AEGIS Manager shortcut...

set "MGR_TARGET=%INSTALL_DIR%\Run_AEGIS_Manager.bat"
if not exist "%MGR_TARGET%" (
    if exist "%INSTALL_DIR%\aegis_manager.py" (
        :: Create Run_AEGIS_Manager.bat if it doesn't exist
        echo @echo off> "%MGR_TARGET%"
        echo title AEGIS Manager>> "%MGR_TARGET%"
        echo cd /d "%%~dp0">> "%MGR_TARGET%"
        echo echo.>> "%MGR_TARGET%"
        echo echo   Starting AEGIS Manager...>> "%MGR_TARGET%"
        echo echo.>> "%MGR_TARGET%"
        echo.>> "%MGR_TARGET%"
        echo if exist "python\python.exe" (>> "%MGR_TARGET%"
        echo     "python\python.exe" aegis_manager.py>> "%MGR_TARGET%"
        echo ) else (>> "%MGR_TARGET%"
        echo     python aegis_manager.py>> "%MGR_TARGET%"
        echo )>> "%MGR_TARGET%"
        echo.>> "%MGR_TARGET%"
        echo pause>> "%MGR_TARGET%"
        echo     Created Run_AEGIS_Manager.bat
    )
)

if exist "%MGR_TARGET%" (
    if defined MGR_ICON_FILE (
        powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS Manager.lnk'); $s.TargetPath = '%MGR_TARGET%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = '%MGR_ICON_FILE%,0'; $s.Description = 'AEGIS Manager v%VERSION% - Updates, Health Check, Repair'; $s.Save(); Write-Host '    [OK] AEGIS Manager.lnk updated (with icon)'" 2>nul
    ) else (
        powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\AEGIS Manager.lnk'); $s.TargetPath = '%MGR_TARGET%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'AEGIS Manager v%VERSION% - Updates, Health Check, Repair'; $s.Save(); Write-Host '    [OK] AEGIS Manager.lnk updated'" 2>nul
    )
) else (
    echo     [SKIP] No manager launcher found
)

echo.

:: ── Step 3: Remove old OneDrive shortcuts (if they exist) ────────
echo   [Step 3 of 4]  Cleaning up old shortcuts...

set "CLEANED=0"

:: Check if any existing shortcuts point to the old OneDrive location
powershell -NoProfile -Command ^
    "$desktop = [Environment]::GetFolderPath('Desktop');" ^
    "$ws = New-Object -ComObject WScript.Shell;" ^
    "$cleaned = 0;" ^
    "Get-ChildItem $desktop -Filter '*.lnk' | ForEach-Object {" ^
    "  try {" ^
    "    $s = $ws.CreateShortcut($_.FullName);" ^
    "    if ($s.TargetPath -like '*OneDrive*AEGIS*' -or $s.TargetPath -like '*Doc Review*AEGIS*') {" ^
    "      if ($_.Name -notlike 'AEGIS*') {" ^
    "        Write-Host ('    Removed old shortcut: ' + $_.Name);" ^
    "        Remove-Item $_.FullName -Force;" ^
    "        $cleaned++;" ^
    "      }" ^
    "    }" ^
    "  } catch { }" ^
    "};" ^
    "if ($cleaned -eq 0) { Write-Host '    No old shortcuts to clean up' }" 2>nul

echo.

:: ── Step 4: Verify ───────────────────────────────────────────────
echo   [Step 4 of 4]  Verifying shortcuts...
echo.

powershell -NoProfile -Command ^
    "$desktop = [Environment]::GetFolderPath('Desktop');" ^
    "$ws = New-Object -ComObject WScript.Shell;" ^
    "$aegis = Join-Path $desktop 'AEGIS.lnk';" ^
    "$mgr = Join-Path $desktop 'AEGIS Manager.lnk';" ^
    "if (Test-Path $aegis) {" ^
    "  $s = $ws.CreateShortcut($aegis);" ^
    "  Write-Host ('    [OK] AEGIS.lnk  ->  ' + $s.TargetPath)" ^
    "} else {" ^
    "  Write-Host '    [MISS] AEGIS.lnk not found'" ^
    "};" ^
    "if (Test-Path $mgr) {" ^
    "  $s = $ws.CreateShortcut($mgr);" ^
    "  Write-Host ('    [OK] AEGIS Manager.lnk  ->  ' + $s.TargetPath)" ^
    "} else {" ^
    "  Write-Host '    [INFO] AEGIS Manager.lnk not on desktop (optional)'" ^
    "}" 2>nul

echo.
echo  ================================================================
echo.
echo     Shortcuts updated!
echo.
echo     AEGIS will now launch from:
echo       %INSTALL_DIR%
echo.
echo     This script can be deleted after use.
echo.
echo  ================================================================
echo.
pause
