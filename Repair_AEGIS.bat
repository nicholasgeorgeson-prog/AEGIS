@echo off
title AEGIS Repair Tool
color 0E

:: ============================================================================
:: AEGIS Repair Tool - Thin Wrapper
:: ============================================================================
:: Finds python.exe and calls repair_aegis.py which handles all the work.
:: This avoids batch scripting pitfalls (errorlevel, paths with spaces, etc.)
:: ============================================================================

echo.
echo  Locating AEGIS Python...
echo.

:: Try current directory first
set "INSTALL_DIR=%~dp0"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

:: Check for python in AEGIS subdirectory
if exist "%INSTALL_DIR%\python\python.exe" (
    set "PYTHON_EXE=%INSTALL_DIR%\python\python.exe"
    goto :found
)

:: Check common install locations
for %%d in (
    "C:\AEGIS"
    "%USERPROFILE%\Desktop\AEGIS"
    "%USERPROFILE%\Desktop\Doc Review\AEGIS"
    "%USERPROFILE%\OneDrive\Desktop\AEGIS"
    "%USERPROFILE%\OneDrive\Desktop\Doc Review\AEGIS"
    "%USERPROFILE%\OneDrive - NGC\Desktop\AEGIS"
    "%USERPROFILE%\OneDrive - NGC\Desktop\Doc Review\AEGIS"
) do (
    if exist "%%~d\python\python.exe" (
        set "INSTALL_DIR=%%~d"
        set "PYTHON_EXE=%%~d\python\python.exe"
        goto :found
    )
)

:: Ask user
echo  [ERROR] Could not find AEGIS installation!
echo.
set /p "CUSTOM_DIR=  Enter AEGIS path (e.g., C:\AEGIS): "
if exist "%CUSTOM_DIR%\python\python.exe" (
    set "INSTALL_DIR=%CUSTOM_DIR%"
    set "PYTHON_EXE=%CUSTOM_DIR%\python\python.exe"
    goto :found
)
echo  [ERROR] No python\python.exe found at that path.
pause
exit /b 1

:found

:: Check for repair_aegis.py in the install directory
set "REPAIR_PY=%INSTALL_DIR%\repair_aegis.py"

:: Also check the script's own directory (if bat was placed elsewhere)
if not exist "%REPAIR_PY%" (
    set "REPAIR_PY=%~dp0repair_aegis.py"
)

if not exist "%REPAIR_PY%" (
    echo  [ERROR] Cannot find repair_aegis.py
    echo  Please ensure repair_aegis.py is in the same folder as this .bat file
    echo  or in your AEGIS installation directory.
    pause
    exit /b 1
)

:: Pre-flight: Ensure setuptools is installed (pkg_resources needed by repair script and spaCy)
:: This must happen in batch because without pkg_resources, Python scripts may fail to import
"%PYTHON_EXE%" -c "import pkg_resources" >nul 2>nul
if errorlevel 1 (
    echo  [PRE-FLIGHT] Installing setuptools (required for pkg_resources^)...
    set "WHEELS="
    if exist "%INSTALL_DIR%\wheels" set "WHEELS=%INSTALL_DIR%\wheels"
    if exist "%INSTALL_DIR%\packaging\wheels" set "WHEELS=%INSTALL_DIR%\packaging\wheels"
    if defined WHEELS (
        "%PYTHON_EXE%" -m pip install --no-index --find-links="%WHEELS%" --no-warn-script-location setuptools >nul 2>nul
    ) else (
        "%PYTHON_EXE%" -m pip install --no-warn-script-location setuptools >nul 2>nul
    )
    echo  [OK] setuptools installed
    echo.
)

:: Run the Python repair tool
"%PYTHON_EXE%" "%REPAIR_PY%"
exit /b %errorlevel%
