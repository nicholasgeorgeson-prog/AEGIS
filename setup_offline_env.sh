#!/bin/bash
# =============================================================================
# AEGIS Offline Environment Setup
# =============================================================================
# This script sets up environment variables for air-gapped/offline operation
# of the AEGIS PDF extraction capabilities.
#
# Usage:
#   source setup_offline_env.sh
#
# For permanent setup, add these exports to your shell profile:
#   ~/.bashrc (Linux)
#   ~/.bash_profile or ~/.zshrc (Mac)
#
# Author: Nick / SAIC Systems Engineering
# Date: 2026-02-04
# =============================================================================

echo "Setting up AEGIS offline environment..."

# Detect the Hugging Face cache directory
if [ -d "$HOME/.cache/huggingface/hub" ]; then
    HF_CACHE="$HOME/.cache/huggingface/hub"
elif [ -d "$HOME/.cache/docling/models" ]; then
    HF_CACHE="$HOME/.cache/docling/models"
else
    echo "Warning: Could not find model cache directory"
    HF_CACHE="$HOME/.cache/docling/models"
fi

# Set Docling artifacts path
export DOCLING_ARTIFACTS_PATH="$HF_CACHE"
export DOCLING_SERVE_ARTIFACTS_PATH="$HF_CACHE"

# Force offline mode - prevents ALL network access during runtime
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1

# Disable telemetry/analytics
export HF_HUB_DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1
export ANONYMIZED_TELEMETRY=false

echo "Environment configured for offline operation:"
echo "  DOCLING_ARTIFACTS_PATH=$DOCLING_ARTIFACTS_PATH"
echo "  HF_HUB_OFFLINE=$HF_HUB_OFFLINE"
echo "  TRANSFORMERS_OFFLINE=$TRANSFORMERS_OFFLINE"
echo ""
echo "To verify setup, run: python3 check_pdf_capabilities.py"
