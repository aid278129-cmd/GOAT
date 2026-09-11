#!/usr/bin/env bash
set -e

# ==============================================================================
# Zyntrix BIS Compliance Compiler — One-Command Startup (Linux / macOS)
# SIH Problem Statement 26107
# ==============================================================================

echo "=============================================================================="
echo "  ZYNTRIX BIS COMPLIANCE COMPILER — ONE-COMMAND STARTUP"
echo "=============================================================================="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[OK] Detected Python $PY_VER"

# 2. Check Node.js and npm
if ! command -v npm &> /dev/null; then
    echo "[ERROR] Node.js/npm is not installed or not in PATH."
    exit 1
fi
echo "[OK] Detected Node.js $(node -v)"

# 3. Environment configuration
if [ ! -f .env ]; then
    echo "[INFO] Creating .env from .env.example..."
    cp .env.example .env
fi

# 4. Create required directories
mkdir -p storage uploads logs generated data

# 5. Optional install
if [ "$1" == "--install" ]; then
    echo "[INFO] Installing Python backend dependencies..."
    python3 -m pip install -r requirements.txt
    echo "[INFO] Installing Frontend npm dependencies..."
    (cd frontend && npm install)
fi

# 6. Cleanup trap
cleanup() {
    echo ""
    echo "[INFO] Shutting down Zyntrix services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo ""
echo "=============================================================================="
echo "  LAUNCHING ZYNTRIX SERVICES"
echo "  Backend API:   http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  Health Check:  http://localhost:8000/api/v1/system/health"
echo "  Frontend UI:   http://localhost:5173"
echo "=============================================================================="
echo ""

# 7. Start Backend
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 8. Start Frontend
(cd frontend && npm run dev) &
FRONTEND_PID=$!

wait
