#!/usr/bin/env bash
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-8080}"

echo "Starting Boulder Dash NES Map Editor (Server Mode) on http://localhost:${PORT} ..."
(sleep 1 && open "http://localhost:${PORT}" 2>/dev/null || true) &
exec python3 "${DIR}/app/server.py" "${PORT}"
