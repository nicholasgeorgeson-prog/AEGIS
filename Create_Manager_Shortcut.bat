@echo off
title AEGIS - Create Manager Desktop Shortcut
color 0A

echo.
echo  ================================================================
echo.
echo   Creating AEGIS Manager desktop shortcut with custom icon...
echo.
echo  ================================================================
echo.

:: ── Detect install directory ────────────────────────────────────
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo   AEGIS location: %INSTALL_DIR%
echo.

:: ── Step 1: Download the icon from GitHub if missing ────────────
set "ICON_FILE=%INSTALL_DIR%\static\img\aegis_manager_icon.ico"

if not exist "%INSTALL_DIR%\static\img" (
    mkdir "%INSTALL_DIR%\static\img"
)

if not exist "%ICON_FILE%" (
    echo   Icon file not found locally — downloading from GitHub...
    powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/static/img/aegis_manager_icon.ico' -OutFile '%ICON_FILE%' -UseBasicParsing; Write-Host '    [OK] Downloaded icon' } catch { Write-Host '    [WARN] Download failed — shortcut will use default icon' }" 2>nul
    echo.
)

if exist "%ICON_FILE%" (
    echo   [OK] Icon file found: %ICON_FILE%
) else (
    echo   [INFO] No icon file — shortcut will use default Windows icon
)
echo.

:: ── Step 2: Make sure Run_AEGIS_Manager.bat exists ──────────────
set "MGR_TARGET=%INSTALL_DIR%\Run_AEGIS_Manager.bat"

if not exist "%MGR_TARGET%" (
    if exist "%INSTALL_DIR%\aegis_manager.py" (
        echo   Creating Run_AEGIS_Manager.bat...
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
        echo     [OK] Created Run_AEGIS_Manager.bat
        echo.
    ) else (
        echo   [ERROR] aegis_manager.py not found in %INSTALL_DIR%
        echo   Cannot create shortcut without the manager script.
        echo.
        pause
        exit /b 1
    )
)

echo   [OK] Launcher: %MGR_TARGET%
echo.

:: ── Step 3: Create the desktop shortcut ─────────────────────────
echo   Creating desktop shortcut...
echo.

if exist "%ICON_FILE%" (
    powershell -NoProfile -Command ^
        "$ws = New-Object -ComObject WScript.Shell;" ^
        "$desktop = [Environment]::GetFolderPath('Desktop');" ^
        "$lnk = Join-Path $desktop 'AEGIS Manager.lnk';" ^
        "$s = $ws.CreateShortcut($lnk);" ^
        "$s.TargetPath = '%MGR_TARGET%';" ^
        "$s.WorkingDirectory = '%INSTALL_DIR%';" ^
        "$s.IconLocation = '%ICON_FILE%,0';" ^
        "$s.Description = 'AEGIS Manager - Updates, Health Check, Repair';" ^
        "$s.Save();" ^
        "Write-Host '    [OK] AEGIS Manager.lnk created on desktop (with gold gear icon)';" ^
        "Write-Host '    Location:' $lnk"
) else (
    powershell -NoProfile -Command ^
        "$ws = New-Object -ComObject WScript.Shell;" ^
        "$desktop = [Environment]::GetFolderPath('Desktop');" ^
        "$lnk = Join-Path $desktop 'AEGIS Manager.lnk';" ^
        "$s = $ws.CreateShortcut($lnk);" ^
        "$s.TargetPath = '%MGR_TARGET%';" ^
        "$s.WorkingDirectory = '%INSTALL_DIR%';" ^
        "$s.Description = 'AEGIS Manager - Updates, Health Check, Repair';" ^
        "$s.Save();" ^
        "Write-Host '    [OK] AEGIS Manager.lnk created on desktop (default icon)';" ^
        "Write-Host '    Location:' $lnk"
)

echo.

:: ── Step 4: Verify ──────────────────────────────────────────────
echo   Verifying...
powershell -NoProfile -Command ^
    "$desktop = [Environment]::GetFolderPath('Desktop');" ^
    "$lnk = Join-Path $desktop 'AEGIS Manager.lnk';" ^
    "if (Test-Path $lnk) {" ^
    "  $ws = New-Object -ComObject WScript.Shell;" ^
    "  $s = $ws.CreateShortcut($lnk);" ^
    "  Write-Host '    Target:' $s.TargetPath;" ^
    "  Write-Host '    Icon:  ' $s.IconLocation;" ^
    "  Write-Host '';" ^
    "  Write-Host '    SUCCESS — shortcut is ready!'" ^
    "} else {" ^
    "  Write-Host '    [FAIL] Shortcut was not created'" ^
    "}"

echo.
echo  ================================================================
echo.
echo   Done! You can delete this script after use.
echo.
echo  ================================================================
echo.
pause
