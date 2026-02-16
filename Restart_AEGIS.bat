@echo off
REM AEGIS - Restart Server (Windows)
REM Double-click or run: restart_aegis.bat

echo.
echo   ============================================================
echo.
echo       AEGIS - Restarting Server...
echo.
echo   ============================================================
echo.

REM Kill any existing AEGIS/Python processes on port 5050
echo   [1/2] Stopping existing AEGIS server...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5050" ^| findstr "LISTENING" 2^>nul') do (
    echo         Killing PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul
echo   [OK] Server stopped (or no existing server found).
echo.

REM Start AEGIS fresh
echo   [2/2] Starting AEGIS...
echo.
cd /d "%~dp0"
python app.py --debug

echo.
echo   AEGIS has stopped.
pause
