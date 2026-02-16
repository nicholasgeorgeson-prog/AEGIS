@echo off
REM =============================================================================
REM AEGIS Offline Environment Setup (Windows)
REM =============================================================================
REM This script sets up environment variables for air-gapped/offline operation
REM of the AEGIS PDF extraction capabilities.
REM
REM Usage:
REM   setup_offline_env.bat
REM
REM For permanent setup, add these to System Environment Variables.
REM
REM Author: Nick / SAIC Systems Engineering
REM Date: 2026-02-04
REM =============================================================================

echo Setting up AEGIS offline environment...

REM Check for model cache locations
set HF_CACHE=%USERPROFILE%\.cache\huggingface\hub
if not exist "%HF_CACHE%" (
    set HF_CACHE=%USERPROFILE%\.cache\docling\models
)

REM Set Docling artifacts path
set DOCLING_ARTIFACTS_PATH=%HF_CACHE%
set DOCLING_SERVE_ARTIFACTS_PATH=%HF_CACHE%

REM Force offline mode - prevents ALL network access during runtime
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set HF_DATASETS_OFFLINE=1

REM Disable telemetry/analytics
set HF_HUB_DISABLE_TELEMETRY=1
set DO_NOT_TRACK=1
set ANONYMIZED_TELEMETRY=false

echo.
echo Environment configured for offline operation:
echo   DOCLING_ARTIFACTS_PATH=%DOCLING_ARTIFACTS_PATH%
echo   HF_HUB_OFFLINE=%HF_HUB_OFFLINE%
echo   TRANSFORMERS_OFFLINE=%TRANSFORMERS_OFFLINE%
echo.
echo To verify setup, run: python check_pdf_capabilities.py
