#!/bin/bash
# AEGIS Offline Installation Script
# Installs all dependencies from pre-downloaded wheels for offline environments
# Usage: ./install_offline.sh or bash install_offline.sh
# Requirements: Python 3.10+ must be installed

set -e

echo ""
echo "============================================================"
echo "AEGIS v4.6.2 - Offline Dependency Installation"
echo "Aerospace Engineering Governance & Inspection System"
echo "============================================================"
echo ""

# Detect Python executable
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10+ using:"
    echo "  macOS: brew install python"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Detected Python: $PYTHON_VERSION"

# Verify Python is 3.10+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "ERROR: Python 3.10 or higher is required"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi
echo ""

# Check if wheels directory exists
if [ ! -d "wheels" ]; then
    echo "ERROR: wheels directory not found!"
    echo "Expected: $(pwd)/wheels/"
    echo "Please ensure wheels directory exists in the project root."
    exit 1
fi

echo "Found wheels directory with packages..."
WHEEL_COUNT=$(ls wheels/ | wc -l)
echo "Package count: $WHEEL_COUNT"
echo ""

# Create virtual environment (optional but recommended)
if [ "$1" = "--venv" ]; then
    echo "[1/4] Creating virtual environment..."
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        echo "Virtual environment created."
    fi
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo ""
fi

echo "[1/3] Upgrading pip, setuptools, and wheel..."
$PYTHON_CMD -m pip install --upgrade pip setuptools wheel --quiet 2>/dev/null || {
    echo "WARNING: Could not upgrade pip, continuing with current version..."
}
echo ""

echo "[2/3] Installing requirements from wheels..."
echo "This may take several minutes. Please wait..."
echo ""

$PYTHON_CMD -m pip install --no-index --find-links=wheels -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Installation failed!"
    echo "Some packages may have failed to install."
    exit 1
fi

echo ""
echo "[3/3] Verifying installation..."
echo ""

# Verify key dependencies
FAILED=0

if $PYTHON_CMD -c "import flask" 2>/dev/null; then
    echo "[OK] Flask"
else
    echo "[FAIL] Flask - CRITICAL"
    FAILED=1
fi

if $PYTHON_CMD -c "import docx" 2>/dev/null; then
    echo "[OK] python-docx"
else
    echo "[FAIL] python-docx - CRITICAL"
    FAILED=1
fi

if $PYTHON_CMD -c "import pandas" 2>/dev/null; then
    echo "[OK] Pandas"
else
    echo "[FAIL] Pandas - CRITICAL"
    FAILED=1
fi

if $PYTHON_CMD -c "import spacy" 2>/dev/null; then
    echo "[OK] spaCy"
else
    echo "[WARN] spaCy - Optional but recommended"
fi

if $PYTHON_CMD -c "import torch" 2>/dev/null; then
    echo "[OK] PyTorch"
else
    echo "[WARN] PyTorch - Optional (for enhanced NLP)"
fi

echo ""

if [ $FAILED -eq 1 ]; then
    echo "============================================================"
    echo "Installation verification FAILED!"
    echo "============================================================"
    echo ""
    echo "Some core dependencies could not be verified."
    echo "Please check the error messages above."
    exit 1
fi

echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Run the AEGIS application: python3 app.py"
echo "2. Open http://localhost:5050 in your browser"
echo "3. For debug mode with auto-reload: python3 app.py --debug"
echo ""

if [ "$1" = "--venv" ]; then
    echo "Virtual environment active. To deactivate later, run: deactivate"
    echo ""
fi

exit 0
