#!/usr/bin/env bash
# One command: API (:8000) + React web app (:5173). `--streamlit` runs the Streamlit fallback (:8501).
# Port overrides: API_PORT, WEB_PORT, ST_PORT.
set -euo pipefail
cd "$(dirname "$0")/.."

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"
ST_PORT="${ST_PORT:-8501}"
MODE=web
[ "${1:-}" = "--streamlit" ] && MODE=streamlit

if [ ! -x .venv/bin/python ]; then
  echo "Creating .venv and installing requirements..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi

if [ "$MODE" = streamlit ]; then
  echo "Streamlit fallback: http://localhost:$ST_PORT"
  exec .venv/bin/streamlit run app.py --server.port "$ST_PORT" --server.headless true
fi

if [ ! -f web/package.json ]; then
  echo "React UI not on this branch yet; use --streamlit" >&2
  exit 1
fi
if [ ! -d web/node_modules ]; then
  echo "Installing web dependencies..."
  npm --prefix web install
fi

API_PID=""
cleanup() { [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

.venv/bin/uvicorn server:app --port "$API_PORT" &
API_PID=$!
echo "API: http://localhost:$API_PORT   Web: http://localhost:$WEB_PORT"
npm --prefix web run dev -- --port "$WEB_PORT"
