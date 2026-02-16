@echo off
setlocal enabledelayedexpansion
title AEGIS Downloader v5.0.0
color 0B

echo.
echo  ============================================================
echo    AEGIS - Aerospace Engineering Governance ^& Inspection System
echo    Download Script v5.0.0
echo  ============================================================
echo.

:: Configuration
set "REPO=nicholasgeorgeson-prog/AEGIS"
set "TAG=v5.0.0"
set "GITHUB_API=https://api.github.com/repos/%REPO%"
set "DOWNLOAD_BASE=https://github.com/%REPO%/releases/download/%TAG%"

:: Default download location
set "DOWNLOAD_DIR=%~dp0AEGIS_Package"

echo  This script will download everything you need to install AEGIS.
echo.
echo  Default download location: %DOWNLOAD_DIR%
echo.
set /p "CUSTOM_DIR=Press Enter to use default, or type a custom path: "
if not "%CUSTOM_DIR%"=="" set "DOWNLOAD_DIR=%CUSTOM_DIR%"

:: Create directories
if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"
if not exist "%DOWNLOAD_DIR%\wheels" mkdir "%DOWNLOAD_DIR%\wheels"

echo.
echo  Downloading to: %DOWNLOAD_DIR%
echo  ============================================================

:: Check for curl (available on Windows 10+)
where curl >nul 2>nul
if errorlevel 1 (
    echo  [ERROR] curl not found. This script requires Windows 10 or later.
    echo  You can also download manually from:
    echo    https://github.com/%REPO%/releases/tag/%TAG%
    pause
    exit /b 1
)

:: Step 1: Clone the repository (source code)
echo.
echo  [1/6] Downloading AEGIS source code...
where git >nul 2>nul
if errorlevel 1 (
    echo  [INFO] Git not found - downloading as ZIP instead...
    curl -L -o "%DOWNLOAD_DIR%\aegis_source.zip" "https://github.com/%REPO%/archive/refs/tags/%TAG%.zip" --progress-bar
    if errorlevel 1 (
        echo  [ERROR] Failed to download source code.
    ) else (
        echo  [OK] Source code downloaded as ZIP
        echo  [INFO] Extracting source code...
        powershell -Command "Expand-Archive -Path '%DOWNLOAD_DIR%\aegis_source.zip' -DestinationPath '%DOWNLOAD_DIR%' -Force" 2>nul
        if exist "%DOWNLOAD_DIR%\AEGIS-%TAG:~1%" (
            xcopy /E /I /Y "%DOWNLOAD_DIR%\AEGIS-%TAG:~1%\*" "%DOWNLOAD_DIR%\AEGIS\" >nul 2>nul
            rmdir /S /Q "%DOWNLOAD_DIR%\AEGIS-%TAG:~1%" >nul 2>nul
        )
        echo  [OK] Source code extracted to AEGIS folder
    )
) else (
    echo  [INFO] Cloning repository...
    git clone --depth 1 --branch %TAG% "https://github.com/%REPO%.git" "%DOWNLOAD_DIR%\AEGIS" 2>nul
    if errorlevel 1 (
        echo  [WARN] Git clone failed, trying ZIP download...
        curl -L -o "%DOWNLOAD_DIR%\aegis_source.zip" "https://github.com/%REPO%/archive/refs/tags/%TAG%.zip" --progress-bar
        powershell -Command "Expand-Archive -Path '%DOWNLOAD_DIR%\aegis_source.zip' -DestinationPath '%DOWNLOAD_DIR%' -Force" 2>nul
    ) else (
        echo  [OK] Repository cloned successfully
    )
)

:: Step 2: Download Python embedded
echo.
echo  [2/6] Downloading Python 3.10.11 embedded...
curl -L -o "%DOWNLOAD_DIR%\python-3.10.11-embed-amd64.zip" "%DOWNLOAD_BASE%/python-3.10.11-embed-amd64.zip" --progress-bar
if errorlevel 1 (
    echo  [ERROR] Failed to download Python embedded
) else (
    echo  [OK] Python embedded downloaded (8.3 MB)
)

:: Step 3: Download get-pip
echo.
echo  [3/6] Downloading pip bootstrapper...
curl -L -o "%DOWNLOAD_DIR%\get-pip.py" "%DOWNLOAD_BASE%/get-pip.py" --progress-bar
if errorlevel 1 (
    echo  [ERROR] Failed to download get-pip.py
) else (
    echo  [OK] get-pip.py downloaded (2.1 MB)
)

:: Step 4: Download wheel packages (part 1)
echo.
echo  [4/6] Downloading dependency wheels (part 1 of 2)...
curl -L -o "%DOWNLOAD_DIR%\wheels\aegis_wheels_part1.zip" "%DOWNLOAD_BASE%/aegis_wheels_part1.zip" --progress-bar
if errorlevel 1 (
    echo  [ERROR] Failed to download wheels part 1
) else (
    echo  [OK] Wheels part 1 downloaded (137 MB)
)

:: Step 5: Download wheel packages (part 2)
echo.
echo  [5/6] Downloading dependency wheels (part 2 of 2)...
curl -L -o "%DOWNLOAD_DIR%\wheels\aegis_wheels_part2.zip" "%DOWNLOAD_BASE%/aegis_wheels_part2.zip" --progress-bar
if errorlevel 1 (
    echo  [ERROR] Failed to download wheels part 2
) else (
    echo  [OK] Wheels part 2 downloaded (245 MB)
)

:: Step 6: Extract wheel packages
echo.
echo  [6/6] Extracting wheel packages...
powershell -Command "Expand-Archive -Path '%DOWNLOAD_DIR%\wheels\aegis_wheels_part1.zip' -DestinationPath '%DOWNLOAD_DIR%\wheels' -Force" 2>nul
powershell -Command "Expand-Archive -Path '%DOWNLOAD_DIR%\wheels\aegis_wheels_part2.zip' -DestinationPath '%DOWNLOAD_DIR%\wheels' -Force" 2>nul
:: Clean up zip files after extraction
del "%DOWNLOAD_DIR%\wheels\aegis_wheels_part1.zip" 2>nul
del "%DOWNLOAD_DIR%\wheels\aegis_wheels_part2.zip" 2>nul
echo  [OK] All wheels extracted

:: Summary
echo.
echo  ============================================================
echo    Download Complete!
echo  ============================================================
echo.
echo  Package location: %DOWNLOAD_DIR%
echo.
echo  Contents:
echo    AEGIS\           - Application source code
echo    wheels\          - Python dependency wheels (126 packages)
echo    python-3.10.11-embed-amd64.zip  - Embedded Python runtime
echo    get-pip.py       - pip bootstrapper
echo.
echo  Next Steps:
echo    1. Copy python-3.10.11-embed-amd64.zip into AEGIS\packaging\
echo    2. Copy get-pip.py into AEGIS\packaging\
echo    3. Copy all .whl files into AEGIS\packaging\wheels\
echo    4. Run AEGIS\packaging\install_aegis.bat
echo.
echo  Or run the combined installer:
echo    install_aegis_full.bat
echo.
pause
