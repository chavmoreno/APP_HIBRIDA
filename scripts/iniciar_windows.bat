@echo off
REM Arranca todos los servicios locales (Windows + XAMPP + Docker Desktop).
REM Requisitos: MySQL de XAMPP iniciado, Docker Desktop abierto y entorno virtual del gateway creado
REM (ver docs\manual_instalacion.md).
set RAIZ=%~dp0..

REM 1) Microservicio de inferencia en Docker (si ya corre, no hace nada)
cd /d %RAIZ%
docker compose up -d
if errorlevel 1 (
  echo No se pudo iniciar el contenedor de inferencia. ¿Esta abierto Docker Desktop?
  pause
  exit /b 1
)

REM 2) API Gateway, worker de alertas y Cloudflare Tunnel en ventanas separadas
start "API Gateway :8000" cmd /k "cd /d %RAIZ%\api-gateway && .venv\Scripts\activate && python run.py"
start "Alertas" cmd /k "cd /d %RAIZ%\api-gateway && .venv\Scripts\activate && python -m app.alertas"
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel run stroke-api"
echo Servicios iniciados. Cierra cada ventana para detenerlos; la inferencia se detiene con "docker compose down".
