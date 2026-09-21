#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

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
(cd "$BACKEND_DIR" && source venv/bin/activate && exec python main.py) &
PIDS+=($!)

# Start frontend
echo "Starting frontend on :3000 ..."
(cd "$FRONTEND_DIR" && exec npm run dev) &
PIDS+=($!)

echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop."
echo ""

wait
