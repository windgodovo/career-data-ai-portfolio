#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8000}"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

echo "[INFO] project root: $ROOT_DIR"
echo "[INFO] python: $PYTHON_BIN"
echo "[INFO] target port: $PORT"

PIDS="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN || true)"
if [[ -n "$PIDS" ]]; then
  echo "[WARN] port $PORT already in use, stopping existing process(es): $PIDS"
  kill -9 $PIDS
  sleep 1
fi

cd "$ROOT_DIR"
exec "$PYTHON_BIN" -m uvicorn api.main:app --reload --port "$PORT"
