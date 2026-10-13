#!/usr/bin/env bash
# Arranca todos los servicios locales (macOS / Linux). Ctrl+C detiene todo.
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

(cd "$RAIZ/inference-service" && .venv/bin/python run.py) &
sleep 3  # La inferencia debe estar arriba antes que el gateway
(cd "$RAIZ/api-gateway" && .venv/bin/python run.py) &
(cd "$RAIZ/api-gateway" && .venv/bin/python -m app.alertas) &
cloudflared tunnel run stroke-api &

trap 'kill $(jobs -p) 2>/dev/null' EXIT INT TERM
wait
