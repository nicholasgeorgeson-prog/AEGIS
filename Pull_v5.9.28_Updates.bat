@echo off
setlocal enabledelayedexpansion
title AEGIS v5.9.28 Update Puller
echo.
echo  ============================================
echo    AEGIS v5.9.28 Update Puller
echo  ============================================
echo.

:: Try to find Python
set "PYTHON_EXE="

:: 1. Check if AEGIS embedded Python exists (same directory)
if exist "%~dp0python\python.exe" (
    set "PYTHON_EXE=%~dp0python\python.exe"
    echo  Found AEGIS Python
    goto :found_python
)

:: 2. Check parent directory
if exist "%~dp0..\python\python.exe" (
    set "PYTHON_EXE=%~dp0..\python\python.exe"
    echo  Found AEGIS Python ^(parent dir^)
    goto :found_python
)

:: 3. Check system Python
where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    echo  Found system Python
    goto :found_python
)

where python3 >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python3"
    echo  Found system Python3
    goto :found_python
)

echo  [ERROR] Could not find Python!
echo.
echo  Place this file in your AEGIS installation directory
echo  (next to the "python" folder), or install Python.
echo.
pause
exit /b 1

:found_python
echo.

:: Check if pull_updates.py exists alongside this bat
if exist "%~dp0pull_updates.py" (
    echo  Found pull_updates.py - running...
    echo.
    "%PYTHON_EXE%" "%~dp0pull_updates.py"
    goto :done
)

:: If not, download it from GitHub first
echo  Downloading pull_updates.py from GitHub...
"%PYTHON_EXE%" -c "import urllib.request,ssl;c=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);c.check_hostname=False;c.verify_mode=ssl.CERT_NONE;r=urllib.request.urlopen('https://raw.githubusercontent.com/nicholasgeorgeson-prog/AEGIS/main/pull_updates.py',context=c);open('pull_updates.py','wb').write(r.read())" 2>nul

if exist "pull_updates.py" (
    echo  Downloaded successfully - running...
    echo.
    "%PYTHON_EXE%" "pull_updates.py"
) else (
    echo.
    echo  [ERROR] Could not download pull_updates.py
    echo.
    echo  Please download both files from:
    echo  https://github.com/nicholasgeorgeson-prog/AEGIS/releases/tag/v5.9.21
    echo  Place pull_updates.py next to this .bat file and try again.
)

:done
echo.
pause
