#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"
PIDS="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN || true)"

if [[ -z "$PIDS" ]]; then
  echo "[INFO] no process is listening on port $PORT"
  exit 0
fi

echo "[INFO] stopping process(es) on port $PORT: $PIDS"
kill -9 $PIDS
echo "[INFO] stopped"
