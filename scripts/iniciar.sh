#!/usr/bin/env bash
# Arranca todos los servicios locales (macOS / Linux). Ctrl+C detiene gateway, alertas y túnel;
# el contenedor de inferencia sigue corriendo (se detiene con "docker compose down").
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

# 1) Microservicio de inferencia en Docker; espera a que el healthcheck lo marque "healthy"
(cd "$RAIZ" && docker compose up -d)
for _ in $(seq 1 30); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' stroke-inferencia 2>/dev/null)" = healthy ] && break
  sleep 2
done

# 2) Gateway, worker de alertas y túnel
(cd "$RAIZ/api-gateway" && .venv/bin/python run.py) &
(cd "$RAIZ/api-gateway" && .venv/bin/python -m app.alertas) &
cloudflared tunnel run stroke-api &

trap 'kill $(jobs -p) 2>/dev/null' EXIT INT TERM
wait
