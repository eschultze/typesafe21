#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo ""
  echo "Shutting down..."
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  echo "Done."
  exit 0
}

trap cleanup SIGINT SIGTERM

PIDS=()

# Start backend
echo "Starting backend on :8000 ..."
(cd "$ROOT_DIR" && exec uv run uvicorn web_main:app --host 0.0.0.0 --port 8000 --reload) > /tmp/backend.log 2>&1 &
PIDS+=($!)

# Start frontend
echo "Starting frontend on :3000 ..."
(cd "$ROOT_DIR/frontend" && exec npm run dev) > /tmp/frontend.log 2>&1 &
PIDS+=($!)

echo "  Logs: /tmp/backend.log /tmp/frontend.log"

echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop."
echo ""

wait
