@echo off
REM Túnel SSH inverso: publica MySQL de XAMPP (127.0.0.1:3306 de este PC) en 127.0.0.1:3306 de la VM de Oracle Cloud.
REM Usa el cliente ssh que ya trae Windows (no instala nada). La conexión sale del PC: no se abren puertos en casa
REM y MySQL sigue escuchando sólo en 127.0.0.1. Déjalo abierto mientras uses la app; si se cae, se reconecta solo.
REM Requisitos (ver docs\manual_instalacion.md): MySQL de XAMPP iniciado, llave %USERPROFILE%\.ssh\stroke_tunel
REM y la IP pública de la VM (o su dominio de DuckDNS) en secrets\vm_ip.txt (una sola línea).
set RAIZ=%~dp0..
set LLAVE=%USERPROFILE%\.ssh\stroke_tunel

if not exist "%LLAVE%" (
  echo Falta la llave %LLAVE%. Ver docs\manual_instalacion.md
  pause
  exit /b 1
)
if not exist "%RAIZ%\secrets\vm_ip.txt" (
  echo Falta secrets\vm_ip.txt con la IP externa de la VM.
  pause
  exit /b 1
)
set /p VM_IP=<"%RAIZ%\secrets\vm_ip.txt"

:bucle
echo [%date% %time%] Conectando el tunel de MySQL con %VM_IP% ...
REM -N: sin comando remoto. -R: 127.0.0.1:3306 de la VM -> 127.0.0.1:3306 de este PC (XAMPP)
ssh -N -i "%LLAVE%" -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=accept-new -R 127.0.0.1:3306:127.0.0.1:3306 tunel@%VM_IP%
echo Tunel caido. Reintento en 10 s (Ctrl+C para salir)...
timeout /t 10 /nobreak >nul
goto bucle
