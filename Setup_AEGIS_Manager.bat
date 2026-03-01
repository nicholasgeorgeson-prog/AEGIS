@echo off
setlocal EnableDelayedExpansion
title AEGIS Manager - One-Time Setup
color 0A

echo.
echo  ================================================================
echo.
echo      A E G I S   M A N A G E R   -   S E T U P
echo.
echo      Downloads and configures the AEGIS Manager tool
echo      from GitHub for permanent use on this machine.
echo.
echo  ================================================================
echo.

:: ── Configuration ──────────────────────────────────────────────────
set "REPO_OWNER=nicholasgeorgeson-prog"
set "REPO_NAME=AEGIS"
set "BRANCH=main"
set "RAW_BASE=https://raw.githubusercontent.com/%REPO_OWNER%/%REPO_NAME%/%BRANCH%"

:: ── Detect install directory ───────────────────────────────────────
set "INSTALL_DIR=%~dp0"
echo   Install directory:
echo     %INSTALL_DIR%
echo.

:: ── Get or load PAT ────────────────────────────────────────────────
set "GH_PAT="

:: Check if aegis_pat.txt already exists
if exist "%INSTALL_DIR%aegis_pat.txt" (
    for /f "usebackq delims=" %%P in ("%INSTALL_DIR%aegis_pat.txt") do (
        if not defined GH_PAT set "GH_PAT=%%P"
    )
    if defined GH_PAT (
        echo   Found existing aegis_pat.txt
        echo.
        goto :have_pat
    )
)

:: Prompt user for PAT
echo   ----------------------------------------------------------------
echo   GitHub Personal Access Token required for first-time setup.
echo.
echo   This is saved locally in aegis_pat.txt and never uploaded.
echo   You only need to enter this ONCE.
echo   ----------------------------------------------------------------
echo.
set /p "GH_PAT=  Paste your GitHub PAT here: "

if not defined GH_PAT (
    echo.
    echo   [ERROR] No token entered. Cannot download from GitHub.
    pause
    exit /b 1
)

:: Validate format
echo !GH_PAT! | findstr /b "ghp_" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [WARN] Token doesn't start with "ghp_" - it may not be valid.
    echo   Continuing anyway...
    echo.
)

:have_pat

:: ────────────────────────────────────────────────────────────────────
:: STEP 1: Find Python
:: ────────────────────────────────────────────────────────────────────
echo   [Step 1 of 5]  Locating Python...
set "PYTHON_EXE="

:: Check embedded Python first (OneClick installer layout)
if exist "%INSTALL_DIR%python\python.exe" (
    set "PYTHON_EXE=%INSTALL_DIR%python\python.exe"
    echo     Found embedded Python
    goto :found_python
)

:: Check system Python
where python >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('where python 2^>nul') do (
        if not defined PYTHON_EXE (
            set "PYTHON_EXE=%%i"
            echo     Found system Python
        )
    )
    if defined PYTHON_EXE goto :found_python
)

:: Check python3
where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('where python3 2^>nul') do (
        if not defined PYTHON_EXE (
            set "PYTHON_EXE=%%i"
            echo     Found python3
        )
    )
    if defined PYTHON_EXE goto :found_python
)

echo.
echo   [ERROR] Python not found!
echo.
echo   The AEGIS Manager requires Python to run.
echo   Either:
echo     1. Install Python from python.org
echo     2. Use the OneClick installer which includes Python
echo.
pause
exit /b 1

:found_python
echo     Path: !PYTHON_EXE!
echo.

:: ────────────────────────────────────────────────────────────────────
:: STEP 2: Download aegis_manager.py
:: ────────────────────────────────────────────────────────────────────
echo   [Step 2 of 5]  Downloading aegis_manager.py...

set "DL_OK=0"
set "DL_FILE=%INSTALL_DIR%aegis_manager.py"

:: Strategy 1: PowerShell (most reliable on modern Windows)
echo     Trying PowerShell...
powershell -ExecutionPolicy Bypass -NoProfile -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ^
    $h = @{Authorization='token !GH_PAT!'; 'User-Agent'='AEGIS-Setup/1.0'}; ^
    try { ^
        Invoke-WebRequest -Uri '!RAW_BASE!/aegis_manager.py' -Headers $h -OutFile '!DL_FILE!' -UseBasicParsing; ^
        Write-Host '    Downloaded via PowerShell'; ^
        exit 0 ^
    } catch { ^
        try { ^
            [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}; ^
            Invoke-WebRequest -Uri '!RAW_BASE!/aegis_manager.py' -Headers $h -OutFile '!DL_FILE!' -UseBasicParsing; ^
            Write-Host '    Downloaded via PowerShell (SSL bypass)'; ^
            exit 0 ^
        } catch { ^
            Write-Host ('    PowerShell failed: ' + $_.Exception.Message); ^
            exit 1 ^
        } ^
    }" 2>nul

if not errorlevel 1 (
    set "DL_OK=1"
    goto :download_done
)

:: Strategy 2: curl (available on newer Windows 10+)
echo     Trying curl...
curl -sL -H "Authorization: token !GH_PAT!" -H "User-Agent: AEGIS-Setup/1.0" -o "!DL_FILE!" "!RAW_BASE!/aegis_manager.py" 2>nul
if not errorlevel 1 (
    if exist "!DL_FILE!" (
        set "DL_OK=1"
        echo     Downloaded via curl
        goto :download_done
    )
)

:: Strategy 3: Python urllib (last resort)
echo     Trying Python urllib...
"!PYTHON_EXE!" -c "import urllib.request,ssl,sys;u='!RAW_BASE!/aegis_manager.py';r=urllib.request.Request(u,headers={'Authorization':'token !GH_PAT!','User-Agent':'AEGIS-Setup'});c=ssl._create_unverified_context();d=urllib.request.urlopen(r,context=c,timeout=30).read();open(sys.argv[1],'wb').write(d);print(f'    Downloaded {len(d):,} bytes via Python')" "!DL_FILE!" 2>nul

if not errorlevel 1 (
    set "DL_OK=1"
    goto :download_done
)

:download_done
if "!DL_OK!"=="0" (
    echo.
    echo   [ERROR] All download methods failed.
    echo   Check your network/VPN and that the PAT is valid.
    echo.
    pause
    exit /b 1
)

:: Verify file size
for %%F in ("!DL_FILE!") do set "DL_SIZE=%%~zF"
if not defined DL_SIZE set "DL_SIZE=0"
if !DL_SIZE! LSS 1000 (
    echo.
    echo     [ERROR] File too small (!DL_SIZE! bytes) - likely an error page.
    del "!DL_FILE!" >nul 2>&1
    echo     Check that the GitHub PAT is valid.
    echo.
    pause
    exit /b 1
)
echo     Size: !DL_SIZE! bytes  [OK]
echo.

:: ────────────────────────────────────────────────────────────────────
:: STEP 3: Save PAT to aegis_pat.txt
:: ────────────────────────────────────────────────────────────────────
echo   [Step 3 of 5]  Saving authentication token...

<nul set /p "=!GH_PAT!" > "%INSTALL_DIR%aegis_pat.txt"
echo.>> "%INSTALL_DIR%aegis_pat.txt"

if exist "%INSTALL_DIR%aegis_pat.txt" (
    echo     Saved to aegis_pat.txt
) else (
    echo     [WARN] Could not save aegis_pat.txt
)
echo.

:: ────────────────────────────────────────────────────────────────────
:: STEP 4: Create launcher (Run_AEGIS_Manager.bat)
:: ────────────────────────────────────────────────────────────────────
echo   [Step 4 of 5]  Creating launcher...

> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo @echo off
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo title AEGIS Manager
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo cd /d "%%~dp0"
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo echo.
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo echo   Starting AEGIS Manager...
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo echo.
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo.
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo if exist "python\python.exe" (
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo     "python\python.exe" aegis_manager.py
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo ) else (
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo     python aegis_manager.py
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo )
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo.
>> "%INSTALL_DIR%Run_AEGIS_Manager.bat" echo pause

echo     Created Run_AEGIS_Manager.bat
echo.

:: ────────────────────────────────────────────────────────────────────
:: STEP 5: Verify
:: ────────────────────────────────────────────────────────────────────
echo   [Step 5 of 5]  Verifying...

set "ALL_OK=1"

if exist "%INSTALL_DIR%aegis_manager.py" (
    echo     [OK]  aegis_manager.py
) else (
    echo     [FAIL] aegis_manager.py NOT FOUND
    set "ALL_OK=0"
)

if exist "%INSTALL_DIR%aegis_pat.txt" (
    echo     [OK]  aegis_pat.txt
) else (
    echo     [WARN] aegis_pat.txt missing
)

if exist "%INSTALL_DIR%Run_AEGIS_Manager.bat" (
    echo     [OK]  Run_AEGIS_Manager.bat
) else (
    echo     [WARN] Run_AEGIS_Manager.bat missing
)

echo.

if "%ALL_OK%"=="0" (
    echo   Setup incomplete. See errors above.
    echo.
    pause
    exit /b 1
)

:: ── Success ─────────────────────────────────────────────────────────
echo   ================================================================
echo.
echo     Setup complete!
echo.
echo     Files created:
echo       aegis_manager.py       Main tool (11 features)
echo       aegis_pat.txt          GitHub authentication
echo       Run_AEGIS_Manager.bat  Double-click launcher
echo.
echo     TO USE:  Double-click  Run_AEGIS_Manager.bat
echo.
echo     This setup script can be deleted after installation.
echo.
echo   ================================================================
echo.

set /p "LAUNCH=  Launch AEGIS Manager now? (Y/N): "
if /i "!LAUNCH!"=="Y" (
    echo.
    "!PYTHON_EXE!" "%INSTALL_DIR%aegis_manager.py"
)

echo.
pause
