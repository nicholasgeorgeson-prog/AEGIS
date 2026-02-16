#!/bin/bash
# AEGIS - Restart Server (macOS)
# Double-click or run: ./restart_aegis.sh

echo ""
echo "  ============================================================"
echo ""
echo "      AEGIS - Restarting Server..."
echo ""
echo "  ============================================================"
echo ""

# Kill any existing AEGIS/Python processes on port 5050
echo "  [1/2] Stopping existing AEGIS server..."
PID=$(lsof -ti :5050 2>/dev/null)
if [ -n "$PID" ]; then
    echo "        Killing PID $PID..."
    kill -9 $PID 2>/dev/null
    sleep 2
    echo "  [OK] Server stopped."
else
    echo "  [OK] No existing server found."
fi
echo ""

# Start AEGIS fresh
echo "  [2/2] Starting AEGIS..."
echo ""
cd "$(dirname "$0")"

# Offline mode - prevent any external network calls
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export DO_NOT_TRACK=1
export TOKENIZERS_PARALLELISM=false

/Library/Frameworks/Python.framework/Versions/3.10/bin/python3 app.py --debug

echo ""
echo "  AEGIS has stopped."
