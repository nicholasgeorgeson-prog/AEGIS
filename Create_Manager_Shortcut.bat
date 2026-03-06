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
    echo   Creating static\img directory...
    mkdir "%INSTALL_DIR%\static\img"
)

if not exist "%ICON_FILE%" (
    echo   Icon file not found locally — downloading from GitHub...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/static/img/aegis_manager_icon.ico' -OutFile '%ICON_FILE%' -UseBasicParsing; Write-Host '    [OK] Downloaded icon' } catch { Write-Host '    [WARN] Download failed:' $_.Exception.Message }"
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
        (
            echo @echo off
            echo title AEGIS Manager
            echo cd /d "%%~dp0"
            echo echo.
            echo echo   Starting AEGIS Manager...
            echo echo.
            echo.
            echo if exist "python\python.exe" ^(
            echo     "python\python.exe" aegis_manager.py
            echo ^) else ^(
            echo     python aegis_manager.py
            echo ^)
            echo.
            echo pause
        ) > "%MGR_TARGET%"
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

echo   [OK] Launcher target: %MGR_TARGET%
echo.

:: ── Step 3: Create the desktop shortcut using VBScript ─────────
::     VBScript + WScript.Shell is the most reliable method on
::     Windows 10 corporate machines (avoids PowerShell policy issues)
echo   Creating desktop shortcut...
echo.

set "VBS_FILE=%TEMP%\aegis_create_shortcut.vbs"

:: Build the VBScript
echo Set ws = CreateObject("WScript.Shell") > "%VBS_FILE%"
echo desktopPath = ws.SpecialFolders("Desktop") >> "%VBS_FILE%"
echo WScript.Echo "    Desktop path: " ^& desktopPath >> "%VBS_FILE%"
echo Set shortcut = ws.CreateShortcut(desktopPath ^& "\AEGIS Manager.lnk") >> "%VBS_FILE%"
echo shortcut.TargetPath = "%MGR_TARGET%" >> "%VBS_FILE%"
echo shortcut.WorkingDirectory = "%INSTALL_DIR%" >> "%VBS_FILE%"

if exist "%ICON_FILE%" (
    echo shortcut.IconLocation = "%ICON_FILE%, 0" >> "%VBS_FILE%"
)

echo shortcut.Description = "AEGIS Manager - Updates, Health Check, Repair" >> "%VBS_FILE%"
echo shortcut.Save >> "%VBS_FILE%"
echo WScript.Echo "    [OK] AEGIS Manager.lnk saved to desktop" >> "%VBS_FILE%"

:: Run the VBScript
echo   Running shortcut creator...
cscript //nologo "%VBS_FILE%"

:: Clean up
del "%VBS_FILE%" 2>nul

echo.

:: ── Step 4: Verify ──────────────────────────────────────────────
echo   Verifying...
echo.

:: Check both possible Desktop locations
set "FOUND=0"

:: Method 1: Check via PowerShell GetFolderPath
for /f "usebackq delims=" %%D in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "[Environment]::GetFolderPath('Desktop')"`) do (
    set "DESKTOP_PS=%%D"
)

if defined DESKTOP_PS (
    echo   Desktop path (System): %DESKTOP_PS%
    if exist "%DESKTOP_PS%\AEGIS Manager.lnk" (
        echo   [OK] Found shortcut at: %DESKTOP_PS%\AEGIS Manager.lnk
        set "FOUND=1"
    ) else (
        echo   [--] Not found at: %DESKTOP_PS%\AEGIS Manager.lnk
    )
)

:: Method 2: Check standard user Desktop
set "DESKTOP_STD=%USERPROFILE%\Desktop"
if exist "%DESKTOP_STD%\AEGIS Manager.lnk" (
    echo   [OK] Found shortcut at: %DESKTOP_STD%\AEGIS Manager.lnk
    set "FOUND=1"
) else (
    echo   [--] Not found at: %DESKTOP_STD%\AEGIS Manager.lnk
)

:: Method 3: Check OneDrive Desktop
set "DESKTOP_OD=%USERPROFILE%\OneDrive - NGC\Desktop"
if exist "%DESKTOP_OD%\AEGIS Manager.lnk" (
    echo   [OK] Found shortcut at: %DESKTOP_OD%\AEGIS Manager.lnk
    set "FOUND=1"
) else (
    if exist "%USERPROFILE%\OneDrive - NGC\Desktop" (
        echo   [--] Not found at: %DESKTOP_OD%\AEGIS Manager.lnk
    )
)

echo.

if "%FOUND%"=="1" (
    echo  ================================================================
    echo.
    echo   SUCCESS! AEGIS Manager shortcut is on your desktop.
    echo.
    echo   Done! You can delete this script after use.
    echo.
    echo  ================================================================
) else (
    echo  ================================================================
    echo.
    echo   SHORTCUT WAS NOT FOUND on any known Desktop path.
    echo.
    echo   Checked:
    if defined DESKTOP_PS echo     - %DESKTOP_PS%
    echo     - %DESKTOP_STD%
    if exist "%USERPROFILE%\OneDrive - NGC\Desktop" echo     - %DESKTOP_OD%
    echo.
    echo   Try creating it manually:
    echo     1. Right-click your Desktop
    echo     2. New ^> Shortcut
    echo     3. Browse to: %MGR_TARGET%
    echo     4. Name it: AEGIS Manager
    echo.
    echo  ================================================================
)

echo.
pause
