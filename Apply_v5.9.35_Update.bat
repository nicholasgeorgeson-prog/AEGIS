@echo off
title AEGIS v5.9.35 Direct Updater
echo.
echo  =============================================
echo    AEGIS v5.9.35 Direct Updater
echo  =============================================
echo.
echo  This will download and apply all v5.9.35 files
echo  directly into your AEGIS installation.
echo  A backup is created automatically.
echo.

:: Find Python
set "PYTHON_EXE="

if exist "%~dp0python\python.exe" (
    set "PYTHON_EXE=%~dp0python\python.exe"
    echo  Found AEGIS Python
    goto :run
)

if exist "%~dp0..\python\python.exe" (
    set "PYTHON_EXE=%~dp0..\python\python.exe"
    echo  Found AEGIS Python
    goto :run
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    echo  Found system Python
    goto :run
)

echo  [ERROR] Could not find Python!
echo  Place this file in your AEGIS installation directory.
echo.
pause
exit /b 1

:run
echo.

:: Check for the .py script next to this .bat
if exist "%~dp0apply_v5.9.35.py" (
    "%PYTHON_EXE%" "%~dp0apply_v5.9.35.py"
    exit /b %errorlevel%
)

:: Try to download it
echo  Downloading apply_v5.9.35.py...
"%PYTHON_EXE%" -c "import urllib.request,ssl;c=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);c.check_hostname=False;c.verify_mode=ssl.CERT_NONE;r=urllib.request.urlopen('https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/apply_v5.9.35.py',context=c);open('apply_v5.9.35.py','wb').write(r.read())" 2>nul

if exist "apply_v5.9.35.py" (
    echo  Downloaded - running...
    echo.
    "%PYTHON_EXE%" "apply_v5.9.35.py"
) else (
    echo.
    echo  [ERROR] Could not download apply_v5.9.35.py
    echo.
    echo  Download both files manually from:
    echo  https://github.com/nicholasgeorgeson-prog/AEGIS/releases/tag/v5.9.21
    echo.
    pause
)
