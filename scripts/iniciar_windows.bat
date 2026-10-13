@echo off
REM Arranca todos los servicios locales en ventanas separadas (Windows + XAMPP).
REM Requisitos: XAMPP con MySQL iniciado, entornos virtuales creados (ver docs\manual_instalacion.md).
set RAIZ=%~dp0..

start "Inferencia :8001" cmd /k "cd /d %RAIZ%\inference-service && .venv\Scripts\activate && python run.py"
start "API Gateway :8000" cmd /k "cd /d %RAIZ%\api-gateway && .venv\Scripts\activate && python run.py"
start "Alertas" cmd /k "cd /d %RAIZ%\api-gateway && .venv\Scripts\activate && python -m app.alertas"
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel run stroke-api"
echo Servicios iniciados. Cierra cada ventana para detenerlos.
