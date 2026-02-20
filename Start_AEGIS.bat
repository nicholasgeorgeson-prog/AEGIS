@echo off
:: AEGIS - Start Script (v5.9.35)
:: Starts AEGIS server minimized and opens browser
:: Double-click to launch AEGIS

title AEGIS - Aerospace Engineering Governance ^& Inspection System

:: Find Python - check common locations
set PYTHON_EXE=
if exist "%~dp0python\python.exe" set PYTHON_EXE=%~dp0python\python.exe
if "%PYTHON_EXE%"=="" where python >nul 2>&1 && set PYTHON_EXE=python
if "%PYTHON_EXE%"=="" where python3 >nul 2>&1 && set PYTHON_EXE=python3

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Kill any existing AEGIS process on port 5050
echo Checking for existing AEGIS instance...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5050 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 1 >nul

:: Start AEGIS minimized using PowerShell
echo Starting AEGIS (minimized)...
powershell -Command "Start-Process '%PYTHON_EXE%' -ArgumentList 'app.py' -WorkingDirectory '%~dp0' -WindowStyle Minimized"

:: Wait for server to come up
echo Waiting for server...
set TRIES=0
:waitloop
timeout /t 1 >nul
set /a TRIES+=1
if %TRIES% GEQ 15 (
    echo [WARN] Server may not have started. Opening browser anyway...
    goto openbrowser
)
powershell -Command "try { (Invoke-WebRequest -Uri 'http://localhost:5050/api/version' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto waitloop

:openbrowser
echo Opening AEGIS in browser...
start http://localhost:5050
echo.
echo AEGIS is running at http://localhost:5050
echo To stop: Run Restart_AEGIS.bat or close the minimized terminal window
echo.
