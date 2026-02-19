@echo off
setlocal enabledelayedexpansion
title AEGIS Repair Tool
color 0E

:: ============================================================================
:: AEGIS Repair Tool - Thin Wrapper
:: ============================================================================
:: 1. Finds python.exe
:: 2. Ensures setuptools is installed (pkg_resources needed by spaCy model)
:: 3. Calls repair_aegis.py for all diagnostics and repairs
:: ============================================================================

echo.
echo  Locating AEGIS Python...
echo.

:: --- Find Python ---
set "INSTALL_DIR=%~dp0"
if "!INSTALL_DIR:~-1!"=="\" set "INSTALL_DIR=!INSTALL_DIR:~0,-1!"

if exist "!INSTALL_DIR!\python\python.exe" (
    set "PYTHON_EXE=!INSTALL_DIR!\python\python.exe"
    goto :found
)

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

echo  [ERROR] Could not find AEGIS installation!
echo.
set /p "CUSTOM_DIR=  Enter AEGIS path (e.g., C:\AEGIS): "
if exist "!CUSTOM_DIR!\python\python.exe" (
    set "INSTALL_DIR=!CUSTOM_DIR!"
    set "PYTHON_EXE=!CUSTOM_DIR!\python\python.exe"
    goto :found
)
echo  [ERROR] No python\python.exe found at that path.
pause
exit /b 1

:found
echo  [OK] Python: !PYTHON_EXE!

:: --- Find wheels directory ---
set "WHEELS_DIR="
if exist "!INSTALL_DIR!\wheels" set "WHEELS_DIR=!INSTALL_DIR!\wheels"
if exist "!INSTALL_DIR!\packaging\wheels" set "WHEELS_DIR=!INSTALL_DIR!\packaging\wheels"

:: --- Find repair_aegis.py ---
set "REPAIR_PY=!INSTALL_DIR!\repair_aegis.py"
if not exist "!REPAIR_PY!" set "REPAIR_PY=%~dp0repair_aegis.py"
if not exist "!REPAIR_PY!" (
    echo  [ERROR] Cannot find repair_aegis.py
    pause
    exit /b 1
)

:: ============================================================================
:: PRE-FLIGHT: Install setuptools if pkg_resources is missing
:: ============================================================================
:: spaCy model loading needs pkg_resources. Without setuptools, even the
:: Python repair script can crash if any installed package's __init__.py
:: imports pkg_resources during Python startup via site.py.
::
:: We do NOT hide errors here (no >nul 2>nul on install commands) so the
:: user can see what's happening if something goes wrong.
:: ============================================================================

echo.
echo  [PRE-FLIGHT] Checking pkg_resources...

"!PYTHON_EXE!" -c "import pkg_resources" >nul 2>nul
if errorlevel 1 goto :need_setuptools
goto :setuptools_ok

:need_setuptools
echo  [PRE-FLIGHT] pkg_resources missing - installing setuptools...
echo.

:: Try from wheels directory first (offline)
if not defined WHEELS_DIR goto :try_online_setuptools
"!PYTHON_EXE!" -m pip install --no-index --find-links="!WHEELS_DIR!" --no-warn-script-location setuptools 2>&1
if not errorlevel 1 goto :verify_setuptools

:: Try direct wheel file path
for %%f in ("!WHEELS_DIR!\setuptools*.whl") do (
    echo  [PRE-FLIGHT] Trying direct wheel: %%~nxf
    "!PYTHON_EXE!" -m pip install --no-warn-script-location "%%f" 2>&1
    if not errorlevel 1 goto :verify_setuptools
)

:try_online_setuptools
echo  [PRE-FLIGHT] Trying online install...
"!PYTHON_EXE!" -m pip install --no-warn-script-location setuptools 2>&1

:verify_setuptools
echo.
"!PYTHON_EXE!" -c "import pkg_resources; print('  [OK] setuptools/pkg_resources now available')" 2>&1
if errorlevel 1 (
    echo  [WARNING] setuptools install may have failed. Continuing anyway...
    echo  If repair_aegis.py crashes, install setuptools manually:
    echo    "!PYTHON_EXE!" -m pip install setuptools
    echo.
)
goto :run_repair

:setuptools_ok
echo  [OK] pkg_resources available
echo.

:: ============================================================================
:: Run repair_aegis.py
:: ============================================================================
:run_repair
"!PYTHON_EXE!" "!REPAIR_PY!"
pause
exit /b 0
