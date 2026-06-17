#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
# A5 Intelligent Tour Guide System — Launch Script
# ═══════════════════════════════════════════════════════
set -e

echo ""
echo "========================================"
echo "  A5 Intelligent Tour Guide System"
echo "========================================"
echo ""

# Python check
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found"
    exit 1
fi

# Virtual environment
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[INFO] Activating venv..."
source venv/bin/activate

# Install dependencies
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt -q 2>/dev/null || echo "[WARN] Some dependencies failed"

# Port
PORT="${1:-8000}"

echo ""
echo "[INFO] Starting backend: http://127.0.0.1:${PORT}"
echo "[INFO] API docs:        http://127.0.0.1:${PORT}/docs"
echo "[INFO] Frontend v4:     http://127.0.0.1:${PORT}/"
echo ""

# Start uvicorn in background
uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" --reload &
UVICORN_PID=$!

echo "[INFO] Waiting for server to be ready..."
for i in $(seq 1 30); do
    if curl -s "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
        echo "[INFO] Server ready!"
        break
    fi
    sleep 1
done

# Open browser
if command -v xdg-open &>/dev/null; then
    xdg-open "http://127.0.0.1:${PORT}/"
elif command -v open &>/dev/null; then
    open "http://127.0.0.1:${PORT}/"
else
    echo "[INFO] Open http://127.0.0.1:${PORT}/ in your browser"
fi

echo ""
echo "========================================"
echo "  Server running (PID: ${UVICORN_PID})"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

# Wait for uvicorn to finish
wait ${UVICORN_PID}
