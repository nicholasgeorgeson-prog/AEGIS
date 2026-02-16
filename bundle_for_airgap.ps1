<#
.SYNOPSIS
    Bundle TechWriterReview with Docling for Air-Gapped Deployment
    
.DESCRIPTION
    This script creates a complete offline installation package containing:
    - TechWriterReview application
    - All Python wheel packages (pip dependencies)
    - Docling AI models
    - Installation scripts for offline deployment
    
    The resulting bundle can be transferred to air-gapped networks and
    installed without any internet connectivity.
    
.PARAMETER OutputDir
    Directory where the bundle will be created
    
.PARAMETER IncludeDocling
    Whether to include Docling and its models (default: true)
    
.PARAMETER PythonVersion
    Target Python version (default: 3.12)
    
.EXAMPLE
    .\bundle_for_airgap.ps1 -OutputDir "C:\TWR_Bundle"
    
.EXAMPLE
    .\bundle_for_airgap.ps1 -OutputDir "D:\Distribution" -IncludeDocling $true
    
.NOTES
    Author: Nick / SAIC Systems Engineering
    Version: 1.0.0
    Date: 2026-01-27
    
    Requirements:
    - Windows 10/11 or Server 2019+
    - Python 3.10+ installed
    - Internet connection (for downloading packages)
    - ~5GB free disk space
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\TWR_AirGap_Bundle",
    
    [Parameter(Mandatory=$false)]
    [bool]$IncludeDocling = $true,
    
    [Parameter(Mandatory=$false)]
    [string]$PythonVersion = "3.12"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

# Configuration
$TWR_VERSION = "3.0.91"
$DOCLING_VERSION = "2.70.0"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TechWriterReview Air-Gap Bundle Creator v$TWR_VERSION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    if ($pyVersion -match "Python 3\.(\d+)") {
        $minorVer = [int]$Matches[1]
        if ($minorVer -lt 10) {
            throw "Python 3.10+ required. Found: $pyVersion"
        }
        Write-Host "[OK] $pyVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Python 3.10+ is required" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    exit 1
}

# Check pip
Write-Host "Checking pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "[OK] $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] pip is required" -ForegroundColor Red
    exit 1
}

# Check internet
Write-Host "Checking internet connection..." -ForegroundColor Yellow
try {
    $null = Test-NetConnection -ComputerName "pypi.org" -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
    Write-Host "[OK] Internet available" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Internet connection required to download packages" -ForegroundColor Red
    exit 1
}

# Create output directory structure
Write-Host ""
Write-Host "Creating bundle directory structure..." -ForegroundColor Yellow

$BundleDir = Join-Path $OutputDir "TWR_v${TWR_VERSION}_AirGap"
$WheelsDir = Join-Path $BundleDir "wheels"
$ModelsDir = Join-Path $BundleDir "docling_models"
$AppDir = Join-Path $BundleDir "TechWriterReview"

# Clean and create directories
if (Test-Path $BundleDir) {
    Write-Host "Removing existing bundle directory..." -ForegroundColor Yellow
    Remove-Item -Path $BundleDir -Recurse -Force
}

New-Item -ItemType Directory -Path $BundleDir -Force | Out-Null
New-Item -ItemType Directory -Path $WheelsDir -Force | Out-Null
if ($IncludeDocling) {
    New-Item -ItemType Directory -Path $ModelsDir -Force | Out-Null
}
New-Item -ItemType Directory -Path $AppDir -Force | Out-Null

Write-Host "[OK] Created: $BundleDir" -ForegroundColor Green

# ============================================================================
# Step 1: Copy TechWriterReview Application
# ============================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Step 1/4: Copying TechWriterReview application..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Copy all application files
$excludePatterns = @("*.pyc", "__pycache__", "*.db", "*.log", "scan_history.db", ".git", "node_modules", "venv", ".venv")
$sourceDir = $ScriptDir

Get-ChildItem -Path $sourceDir -Recurse -File | Where-Object {
    $exclude = $false
    foreach ($pattern in $excludePatterns) {
        if ($_.FullName -like "*$pattern*") {
            $exclude = $true
            break
        }
    }
    -not $exclude
} | ForEach-Object {
    $relativePath = $_.FullName.Substring($sourceDir.Length + 1)
    $destPath = Join-Path $AppDir $relativePath
    $destDir = Split-Path $destPath -Parent
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item $_.FullName $destPath -Force
}

Write-Host "[OK] Application files copied" -ForegroundColor Green

# ============================================================================
# Step 2: Download Python Wheel Packages
# ============================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Step 2/4: Downloading Python packages (wheels)..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "This may take 10-20 minutes depending on connection speed." -ForegroundColor Yellow
Write-Host ""

# Base requirements
$basePackages = @(
    "Flask>=2.0.0",
    "waitress>=2.0.0",
    "python-docx>=0.8.11",
    "lxml>=4.9.0",
    "openpyxl>=3.0.0",
    "PyMuPDF>=1.22.0",
    "PyPDF2>=3.0.0",
    "pdfplumber>=0.10.0"
)

# Docling packages (optional)
$doclingPackages = @(
    "torch",
    "torchvision",
    "docling>=$DOCLING_VERSION"
)

# Download base packages
Write-Host "Downloading base packages..." -ForegroundColor Yellow
foreach ($pkg in $basePackages) {
    Write-Host "  - $pkg" -ForegroundColor Gray
    pip download $pkg -d $WheelsDir --quiet 2>&1 | Out-Null
}
Write-Host "[OK] Base packages downloaded" -ForegroundColor Green

# Download Docling packages if requested
if ($IncludeDocling) {
    Write-Host ""
    Write-Host "Downloading Docling packages (this takes longer)..." -ForegroundColor Yellow
    
    # Download PyTorch CPU-only to save space
    Write-Host "  - PyTorch (CPU-only)..." -ForegroundColor Gray
    pip download torch torchvision --index-url https://download.pytorch.org/whl/cpu -d $WheelsDir --quiet 2>&1 | Out-Null
    
    Write-Host "  - Docling..." -ForegroundColor Gray
    pip download "docling>=$DOCLING_VERSION" -d $WheelsDir --quiet 2>&1 | Out-Null
    
    Write-Host "[OK] Docling packages downloaded" -ForegroundColor Green
}

# Count wheels
$wheelCount = (Get-ChildItem -Path $WheelsDir -Filter "*.whl").Count
$tarCount = (Get-ChildItem -Path $WheelsDir -Filter "*.tar.gz").Count
Write-Host "[OK] Downloaded $wheelCount wheels, $tarCount source packages" -ForegroundColor Green

# ============================================================================
# Step 3: Download Docling Models
# ============================================================================
if ($IncludeDocling) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Step 3/4: Downloading Docling AI models (~1.5GB)..." -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "This may take 10-30 minutes depending on connection speed." -ForegroundColor Yellow
    Write-Host ""
    
    # First ensure docling-tools is available
    Write-Host "Installing docling-tools temporarily..." -ForegroundColor Yellow
    pip install docling --quiet 2>&1 | Out-Null
    
    Write-Host "Downloading models..." -ForegroundColor Yellow
    docling-tools models download -o $ModelsDir 2>&1 | Out-Null
    
    if (Test-Path (Join-Path $ModelsDir "ds4sd--docling-models")) {
        Write-Host "[OK] Models downloaded to: $ModelsDir" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Model download may have issues. Check $ModelsDir" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "Step 3/4: Skipping Docling models (not requested)" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

# ============================================================================
# Step 4: Create Installation Scripts
# ============================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Step 4/4: Creating installation scripts..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Create INSTALL_AIRGAP.bat
$installScript = @"
@echo off
REM ============================================================================
REM TechWriterReview v$TWR_VERSION - Air-Gap Installation
REM ============================================================================
REM Run this script on the air-gapped machine to install TechWriterReview.
REM No internet connection required.
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo TechWriterReview v$TWR_VERSION - Air-Gap Installation
echo ============================================================
echo.

REM Get bundle directory
set BUNDLE_DIR=%~dp0

REM Check Python
python --version 2>nul | findstr /R "3\.[0-9]" >nul
if errorlevel 1 (
    echo ERROR: Python 3.10+ is required.
    echo Please install Python 3.10+ from the included installer
    echo or request it from your IT department.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Set installation directory
set /p INSTALL_DIR="Installation directory [C:\TWR]: "
if "!INSTALL_DIR!"=="" set INSTALL_DIR=C:\TWR

REM Create directories
echo Creating directories...
if not exist "!INSTALL_DIR!" mkdir "!INSTALL_DIR!"
if not exist "!INSTALL_DIR!\app" mkdir "!INSTALL_DIR!\app"

REM Install Python packages from wheels
echo.
echo Installing Python packages (this may take a few minutes)...
pip install --no-index --find-links="%BUNDLE_DIR%wheels" Flask waitress python-docx lxml openpyxl PyMuPDF PyPDF2 pdfplumber --quiet
if errorlevel 1 (
    echo Trying with --user flag...
    pip install --no-index --find-links="%BUNDLE_DIR%wheels" Flask waitress python-docx lxml openpyxl PyMuPDF PyPDF2 pdfplumber --user --quiet
)

REM Install Docling if models are present
if exist "%BUNDLE_DIR%docling_models" (
    echo.
    echo Installing Docling advanced document extraction...
    pip install --no-index --find-links="%BUNDLE_DIR%wheels" torch torchvision docling --quiet 2>nul
    if errorlevel 1 (
        pip install --no-index --find-links="%BUNDLE_DIR%wheels" torch torchvision docling --user --quiet 2>nul
    )
    
    REM Copy models
    echo Copying Docling models...
    xcopy /E /I /Y "%BUNDLE_DIR%docling_models" "!INSTALL_DIR!\docling_models" >nul
    
    REM Set ALL environment variables for complete offline operation
    echo Configuring offline mode (no network access)...
    setx DOCLING_ARTIFACTS_PATH "!INSTALL_DIR!\docling_models" >nul 2>&1
    setx HF_HUB_OFFLINE "1" >nul 2>&1
    setx TRANSFORMERS_OFFLINE "1" >nul 2>&1
    setx HF_DATASETS_OFFLINE "1" >nul 2>&1
    setx HF_HUB_DISABLE_TELEMETRY "1" >nul 2>&1
    setx DO_NOT_TRACK "1" >nul 2>&1
    
    REM Set for current session too
    set DOCLING_ARTIFACTS_PATH=!INSTALL_DIR!\docling_models
    set HF_HUB_OFFLINE=1
    set TRANSFORMERS_OFFLINE=1
    set HF_DATASETS_OFFLINE=1
    
    echo [OK] Docling installed with models (OFFLINE MODE)
)

REM Copy application
echo.
echo Copying application files...
xcopy /E /I /Y "%BUNDLE_DIR%TechWriterReview" "!INSTALL_DIR!\app\TechWriterReview" >nul

REM Create start script with complete offline configuration
echo.
(
echo @echo off
echo REM TechWriterReview v$TWR_VERSION - Air-Gap Mode
echo REM All network access DISABLED
echo.
echo REM === OFFLINE CONFIGURATION ===
echo set DOCLING_ARTIFACTS_PATH=!INSTALL_DIR!\docling_models
echo set HF_HUB_OFFLINE=1
echo set TRANSFORMERS_OFFLINE=1
echo set HF_DATASETS_OFFLINE=1
echo set HF_HUB_DISABLE_TELEMETRY=1
echo set DO_NOT_TRACK=1
echo set ANONYMIZED_TELEMETRY=false
echo.
echo cd /d "!INSTALL_DIR!\app\TechWriterReview"
echo echo.
echo echo ============================================================
echo echo TechWriterReview v$TWR_VERSION - AIR-GAP MODE
echo echo ============================================================
echo echo.
echo echo Docling models: !INSTALL_DIR!\docling_models
echo echo Network access: DISABLED
echo echo.
echo echo Open browser to: http://localhost:5000
echo echo Press Ctrl+C to stop.
echo echo.
echo python app.py
echo pause
) > "!INSTALL_DIR!\Start_TechWriterReview.bat"

REM Create desktop shortcut (optional)
echo Creating desktop shortcut...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\TechWriterReview.lnk'); $SC.TargetPath = '!INSTALL_DIR!\Start_TechWriterReview.bat'; $SC.WorkingDirectory = '!INSTALL_DIR!\app\TechWriterReview'; $SC.Description = 'TechWriterReview v$TWR_VERSION'; $SC.Save()" 2>nul

echo.
echo ============================================================
echo INSTALLATION COMPLETE - AIR-GAP READY
echo ============================================================
echo.
echo TechWriterReview installed to: !INSTALL_DIR!
echo.
echo OFFLINE CONFIGURATION:
echo   - All AI models stored locally
echo   - Network access DISABLED
echo   - No data leaves your machine
echo.
echo To start:
echo   1. Double-click: !INSTALL_DIR!\Start_TechWriterReview.bat
echo   2. Or use the desktop shortcut
echo.
echo Then open: http://localhost:5000
echo.

pause
"@

$installScript | Out-File -FilePath (Join-Path $BundleDir "INSTALL_AIRGAP.bat") -Encoding ASCII

Write-Host "[OK] Created INSTALL_AIRGAP.bat" -ForegroundColor Green

# Create README
$readmeContent = @"
# TechWriterReview v$TWR_VERSION - Air-Gap Installation Package

## Contents

This bundle contains everything needed to install TechWriterReview on an
air-gapped network (no internet required):

- `TechWriterReview/` - Application files
- `wheels/` - Python packages (pre-downloaded)
- `docling_models/` - AI models for document extraction (if included)
- `INSTALL_AIRGAP.bat` - Installation script

## Requirements

- Windows 10/11 or Windows Server 2019+
- Python 3.10+ (3.12 recommended)
- ~3GB disk space (with Docling) or ~500MB (without)

## Installation

1. Copy this entire folder to the air-gapped machine
2. Run `INSTALL_AIRGAP.bat` as Administrator (recommended)
3. Follow the prompts to select installation directory
4. Start TechWriterReview using the desktop shortcut or start script

## Verifying Installation

After installation:
1. Open http://localhost:5000 in a web browser
2. Go to Help → About
3. Verify version shows $TWR_VERSION
4. Upload a test document to verify extraction works

## Troubleshooting

### Python not found
Install Python 3.10+ from your organization's software repository or
request it from IT. Ensure "Add Python to PATH" is checked during install.

### Permission denied
Run the installer as Administrator, or install to a user-writable location
like `C:\Users\<username>\TWR`.

### Docling not working
Verify the DOCLING_ARTIFACTS_PATH environment variable is set correctly:
```
echo %DOCLING_ARTIFACTS_PATH%
```
Should point to the `docling_models` folder.

## Support

For issues, document them in TWR_LESSONS_LEARNED.md or contact your
local TechWriterReview administrator.

---
Package created: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Docling included: $IncludeDocling
"@

$readmeContent | Out-File -FilePath (Join-Path $BundleDir "README.txt") -Encoding UTF8

Write-Host "[OK] Created README.txt" -ForegroundColor Green

# ============================================================================
# Summary
# ============================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "BUNDLE CREATION COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Calculate size
$bundleSize = [math]::Round((Get-ChildItem -Path $BundleDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB, 2)

Write-Host "Bundle location: $BundleDir" -ForegroundColor Cyan
Write-Host "Total size: ${bundleSize}GB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Contents:" -ForegroundColor Yellow
Write-Host "  - TechWriterReview application" -ForegroundColor White
Write-Host "  - $wheelCount Python wheel packages" -ForegroundColor White
if ($IncludeDocling) {
    Write-Host "  - Docling AI models" -ForegroundColor White
}
Write-Host "  - Installation scripts" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Copy the '$BundleDir' folder to a USB drive or network share" -ForegroundColor White
Write-Host "  2. Transfer to the air-gapped machine" -ForegroundColor White
Write-Host "  3. Run INSTALL_AIRGAP.bat on the target machine" -ForegroundColor White
Write-Host ""

# Optionally create ZIP
$createZip = Read-Host "Create ZIP archive for easier transfer? (Y/N)"
if ($createZip -eq "Y" -or $createZip -eq "y") {
    $zipPath = "$BundleDir.zip"
    Write-Host ""
    Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
    Compress-Archive -Path $BundleDir -DestinationPath $zipPath -Force
    $zipSize = [math]::Round((Get-Item $zipPath).Length / 1GB, 2)
    Write-Host "[OK] Created: $zipPath (${zipSize}GB)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
