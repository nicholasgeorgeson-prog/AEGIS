@echo off
REM ============================================================================
REM TechWriterReview v3.0.97 - Docling Advanced Document Extraction Setup
REM ============================================================================
REM This script installs Docling for superior document parsing capabilities.
REM 
REM REQUIREMENTS:
REM   - Python 3.10+ (3.12 recommended)
REM   - ~3GB disk space (packages + AI models)
REM   - Internet connection (REQUIRED for this installation script)
REM
REM HOW IT WORKS:
REM   1. INSTALLATION (this script) - Requires internet to download packages/models
REM   2. RUNTIME (after setup) - Operates 100% offline, no internet needed
REM
REM The offline environment variables are only set AFTER installation completes.
REM During installation, internet access is used to download from PyPI and 
REM Hugging Face model repositories.
REM
REM For truly AIR-GAPPED machines (no internet at all), use: bundle_for_airgap.ps1
REM ============================================================================
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo TechWriterReview - Docling Setup (Air-Gap Ready)
echo Advanced Document Extraction Module
echo ============================================================
echo.
echo This will install:
echo   - Docling document parser (~1.5GB packages)
echo   - PyTorch machine learning framework (CPU-only)
echo   - AI models for table/layout recognition (~1.5GB)
echo.
echo After installation, Docling operates COMPLETELY OFFLINE.
echo No internet connection required for document processing.
echo.
echo Total disk space required: ~3GB
echo.

set /p CONTINUE="Continue with installation? (Y/N): "
if /i not "!CONTINUE!"=="Y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Check Python version
echo.
echo Checking Python version...
python --version 2>nul | findstr /R "3\.1[0-9]" >nul
if errorlevel 1 (
    echo ERROR: Python 3.10+ is required for Docling.
    echo Current version:
    python --version 2>nul || echo Python not found!
    echo.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Python %PYVER% detected
echo.

REM Set models directory
set MODELS_DIR=%SCRIPT_DIR%docling_models
echo Models will be saved to: %MODELS_DIR%
echo.

REM ============================================================================
REM Step 1: Install PyTorch (CPU-only for smaller size and memory efficiency)
REM ============================================================================
echo ============================================================
echo Step 1/4: Installing PyTorch CPU-only (5-10 minutes)...
echo ============================================================
echo.
echo Using CPU-only build to optimize memory usage.
echo.

pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo WARNING: PyTorch installation from pytorch.org failed. Trying PyPI...
    pip install torch torchvision --disable-pip-version-check
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo ERROR: Could not install PyTorch.
        echo ============================================================
        echo.
        echo This usually means:
        echo   1. No internet connection, OR
        echo   2. PyPI/PyTorch servers are blocked by firewall
        echo.
        echo SOLUTION: Use the air-gapped installer instead:
        echo   1. On a machine WITH internet, run: bundle_for_airgap.ps1
        echo   2. Copy the bundle to this machine
        echo   3. Run: INSTALL_AIRGAP.bat
        echo.
        pause
        exit /b 1
    )
)

echo [OK] PyTorch installed (CPU-only)
echo.

REM ============================================================================
REM Step 2: Install Docling
REM ============================================================================
echo ============================================================
echo Step 2/4: Installing Docling document parser...
echo ============================================================
echo.

pip install "docling>=2.70.0" --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo WARNING: First attempt failed. Trying with --user flag...
    pip install docling --disable-pip-version-check --user
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo ERROR: Could not install Docling.
        echo ============================================================
        echo.
        echo This usually means:
        echo   1. No internet connection, OR
        echo   2. PyPI is blocked by firewall
        echo.
        echo SOLUTION: Use the air-gapped installer instead:
        echo   1. On a machine WITH internet, run: bundle_for_airgap.ps1
        echo   2. Copy the bundle to this machine
        echo   3. Run: INSTALL_AIRGAP.bat
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Docling installed
echo.

REM ============================================================================
REM Step 3: Download AI Models (for complete offline operation)
REM ============================================================================
echo ============================================================
echo Step 3/4: Downloading AI models (~1.5GB)...
echo ============================================================
echo.
echo This downloads models for:
echo   - Document layout analysis
echo   - Table structure recognition (TableFormer)
echo   - Text extraction optimization
echo.
echo Models are stored locally for OFFLINE operation.
echo.

if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"

echo Downloading models to: %MODELS_DIR%
echo This may take 10-30 minutes depending on connection speed...
echo.

REM Use Python directly with SSL verification disabled (for corporate proxies)
echo Downloading with SSL bypass for corporate networks...
python -c "import ssl; ssl._create_default_https_context = ssl._create_unverified_context; import os; os.environ['HF_HUB_DISABLE_SSL_VERIFY']='1'; os.environ['CURL_CA_BUNDLE']=''; os.environ['REQUESTS_CA_BUNDLE']=''; from docling.utils.model_downloader import download_models; download_models(r'%MODELS_DIR%')"

if errorlevel 1 (
    echo.
    echo WARNING: Primary download method failed. Trying alternative...
    REM Try with requests SSL disabled
    python -c "import ssl, urllib3; urllib3.disable_warnings(); ssl._create_default_https_context = ssl._create_unverified_context; import os; os.environ['HF_HUB_DISABLE_SSL_VERIFY']='1'; from huggingface_hub import snapshot_download; snapshot_download('ds4sd/docling-models', local_dir=r'%MODELS_DIR%\ds4sd--docling-models', local_dir_use_symlinks=False)"
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo WARNING: Could not download models automatically.
        echo ============================================================
        echo.
        echo Your corporate proxy may be blocking huggingface.co
        echo.
        echo MANUAL SOLUTION:
        echo   1. Download models on another network ^(home, Mac, etc.^)
        echo   2. Run: docling-tools models download -o models_folder
        echo   3. Copy the models folder to: %MODELS_DIR%
        echo.
        echo TechWriterReview will still work without Docling models,
        echo but will use legacy extractors with lower accuracy.
        echo.
    )
)

echo.
echo [OK] Models downloaded to: %MODELS_DIR%
echo.

REM ============================================================================
REM Step 4: Configure Environment for Air-Gap Operation
REM ============================================================================
echo ============================================================
echo Step 4/4: Configuring offline environment...
echo ============================================================
echo.

REM Create environment configuration file
(
echo # Docling Air-Gap Configuration
echo # Generated by TechWriterReview setup_docling.bat
echo # Date: %date% %time%
echo.
echo # Model artifacts location
echo DOCLING_ARTIFACTS_PATH=%MODELS_DIR%
echo DOCLING_SERVE_ARTIFACTS_PATH=%MODELS_DIR%
echo.
echo # Force OFFLINE mode - prevents ALL network access
echo HF_HUB_OFFLINE=1
echo TRANSFORMERS_OFFLINE=1
echo HF_DATASETS_OFFLINE=1
echo.
echo # Disable telemetry
echo HF_HUB_DISABLE_TELEMETRY=1
echo DO_NOT_TRACK=1
echo ANONYMIZED_TELEMETRY=false
) > "%SCRIPT_DIR%docling_env.txt"

echo Created: docling_env.txt (environment reference)

REM Set user environment variables (persists across sessions)
echo.
echo Setting environment variables for offline operation...

setx DOCLING_ARTIFACTS_PATH "%MODELS_DIR%" >nul 2>&1
setx HF_HUB_OFFLINE "1" >nul 2>&1
setx TRANSFORMERS_OFFLINE "1" >nul 2>&1
setx HF_DATASETS_OFFLINE "1" >nul 2>&1
setx HF_HUB_DISABLE_TELEMETRY "1" >nul 2>&1

echo [OK] Environment variables set for offline operation
echo.

REM Set for current session
set DOCLING_ARTIFACTS_PATH=%MODELS_DIR%
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set HF_DATASETS_OFFLINE=1

REM ============================================================================
REM Verification
REM ============================================================================
echo ============================================================
echo Verifying installation...
echo ============================================================
echo.

python -c "import torch; print(f'  [OK] PyTorch {torch.__version__}')" 2>nul
if errorlevel 1 echo   [FAIL] PyTorch

python -c "import docling; print(f'  [OK] Docling {docling.__version__}')" 2>nul
if errorlevel 1 echo   [FAIL] Docling

python -c "from docling_extractor import DoclingExtractor, DoclingManager; status = DoclingManager.check_installation(); print(f'  [OK] Offline ready: {status[\"offline_ready\"]}')" 2>nul
if errorlevel 1 echo   [WARN] DoclingExtractor verification failed

echo.

REM ============================================================================
REM Create startup script with Docling offline configuration
REM ============================================================================
(
echo @echo off
echo REM TechWriterReview with Docling - Air-Gap Mode
echo REM Generated: %date%
echo.
echo REM === OFFLINE CONFIGURATION ===
echo set DOCLING_ARTIFACTS_PATH=%MODELS_DIR%
echo set HF_HUB_OFFLINE=1
echo set TRANSFORMERS_OFFLINE=1
echo set HF_DATASETS_OFFLINE=1
echo set HF_HUB_DISABLE_TELEMETRY=1
echo.
echo cd /d "%SCRIPT_DIR%"
echo echo.
echo echo ============================================================
echo echo TechWriterReview v3.0.97 with Docling (OFFLINE MODE)
echo echo ============================================================
echo echo.
echo echo Docling models: %MODELS_DIR%
echo echo Network access: DISABLED
echo echo.
echo echo Open browser to: http://localhost:5000
echo echo Press Ctrl+C to stop.
echo echo.
echo python app.py
echo pause
) > "%SCRIPT_DIR%start_twr_docling.bat"

echo Created: start_twr_docling.bat

REM ============================================================================
REM Done
REM ============================================================================
echo.
echo ============================================================
echo DOCLING SETUP COMPLETE - OFFLINE READY
echo ============================================================
echo.
echo Installation summary:
echo   - PyTorch: CPU-only (memory optimized)
echo   - Docling: Installed with all dependencies
echo   - Models: %MODELS_DIR%
echo   - Network: DISABLED for all operations
echo.
echo To start TechWriterReview with Docling:
echo   Double-click: start_twr_docling.bat
echo.
echo IMPORTANT: Docling now operates COMPLETELY OFFLINE.
echo   - No data is sent to any external servers
echo   - All AI models run locally on your machine
echo   - Image processing is disabled to save memory
echo.
echo To verify offline status, check Help ^> About in the application.
echo.

pause
