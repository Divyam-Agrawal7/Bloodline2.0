#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "      BLOODLINE 2.0 — Bank-Grade Mule Defense Platform    "
echo "=========================================================="

# Check Python environment
PYTHON_BIN=".venv/bin/python3"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

# Ensure synthetic database exists
if [ ! -f "data/bloodline.db" ]; then
    echo "[1/4] Generating synthetic multi-bank ledger (seed 42)..."
    "$PYTHON_BIN" data/simulator.py
else
    echo "[1/4] Synthetic database ready at data/bloodline.db"
fi

# Ensure trained models exist
if [ ! -f "data/models/xgboost_mule.joblib" ]; then
    echo "[2/4] Training XGBoost mule detection model..."
    "$PYTHON_BIN" app/ml/train.py
else
    echo "[2/4] Trained ML models ready at data/models/"
fi

# Ensure frontend build exists
if [ ! -f "frontend/dist/index.html" ]; then
    echo "[3/4] Building React frontend..."
    if command -v pnpm >/dev/null 2>&1; then
        (cd frontend && pnpm run build)
    elif [ -f "/Users/divyamagrawal/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm" ]; then
        (cd frontend && /Users/divyamagrawal/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm run build)
    fi
else
    echo "[3/4] Production frontend bundle ready in frontend/dist/"
fi

echo "[4/4] Starting server on http://127.0.0.1:8000 ..."
echo "  • Web Platform:     http://127.0.0.1:8000"
echo "  • Swagger API Docs: http://127.0.0.1:8000/docs"
echo "  • ReDoc:            http://127.0.0.1:8000/redoc"
echo "=========================================================="

if [ -f ".venv/bin/uvicorn" ]; then
    exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
else
    exec "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
fi
