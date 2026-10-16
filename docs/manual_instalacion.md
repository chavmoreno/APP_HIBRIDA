# Manual de instalación y despliegue

Guía paso a paso para poner en marcha la aplicación. Los comandos están para **Windows (PowerShell)**,
que es donde normalmente corre XAMPP; las variantes de macOS/Linux van entre paréntesis.

## 0. Requisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.11 – 3.13 | API Gateway (la inferencia trae su propio Python en la imagen Docker) |
| Docker Desktop | 4.x (Windows: con backend WSL2) | Microservicio de inferencia en contenedor |
| Node.js | 20+ | Construir el frontend |
| XAMPP | 7.4+ / 8.x (MariaDB 10.4+) | `consultas_db` y `errores_db` |
| mkcert | 1.4+ | Certificados HTTPS locales |
| cloudflared | reciente | Cloudflare Tunnel |
| Firebase CLI | `npm i -g firebase-tools` | Desplegar el frontend |
| Cuentas | Google (Firebase/Colab), Kaggle, Cloudflare con un dominio | |

## 1. Entrenar el modelo en Google Colab

1. Abre `ml/stroke_prediction_colab.ipynb` en Colab:
   *Archivo → Abrir notebook → GitHub →* `chavmoreno/APP_HIBRIDA` (o sube el `.ipynb`).
2. (Opcional, el dataset es público) Si Kaggle pide autenticación: kaggle.com → *Settings → API →
   Generate New Token*. Kaggle muestra el **API Token una sola vez**: cópialo. En Colab, panel **🔑 Secrets**,
   crea un secreto llamado `KAGGLE_API_TOKEN` con ese valor y activa *Acceso al notebook*.
   (Con un `kaggle.json` antiguo también sirven los secretos `KAGGLE_USERNAME` y `KAGGLE_KEY`.)
3. *Entorno de ejecución → Ejecutar todo*. Al final se descargan `model_v1.joblib` y `model_v1.metadata.json`.
4. Copia ambos archivos a `inference-service/models/`.

> El notebook fija `scikit-learn==1.6.1`, la misma versión que `inference-service/requirements.txt`.
> Si las cambias, cámbialas en ambos sitios.

## 2. Bases de datos en XAMPP

1. Inicia **MySQL** desde el panel de XAMPP.
2. Restringe MySQL a la máquina local: en `C:\xampp\mysql\bin\my.ini`, sección `[mysqld]`:
   ```ini
   bind-address=127.0.0.1
   ```
   Reinicia MySQL. Pon contraseña a `root` si no tiene (phpMyAdmin → *Cuentas de usuario*).
3. Edita `database/03_usuarios.sql` y cambia cada `cambia-esta-clave` por contraseñas fuertes.
4. Ejecuta los scripts en orden (phpMyAdmin → pestaña SQL, o consola):
   ```powershell
   cd database
   Get-Content 01_consultas_db.sql | C:\xampp\mysql\bin\mysql.exe -u root -p
   Get-Content 02_errores_db.sql   | C:\xampp\mysql\bin\mysql.exe -u root -p
   Get-Content 03_usuarios.sql     | C:\xampp\mysql\bin\mysql.exe -u root -p
   ```
   (macOS/Linux: `mysql -u root -p < 01_consultas_db.sql`, etc.)

## 3. Certificados HTTPS locales

```powershell
choco install mkcert          # (brew install mkcert)
mkcert -install
cd infra\certs
mkcert -cert-file localhost.pem -key-file localhost-key.pem localhost 127.0.0.1 ::1
Copy-Item "$(mkcert -CAROOT)\rootCA.pem" .     # (cp "$(mkcert -CAROOT)/rootCA.pem" .)
```

## 4. Firebase (Authentication + Hosting)

1. [console.firebase.google.com](https://console.firebase.google.com) → *Agregar proyecto*.
2. **Authentication → Método de acceso**: habilita **Correo electrónico/contraseña** y **Google**.
3. **Authentication → Configuración → Dominios autorizados**: deja `TU-PROYECTO.web.app`,
   `TU-PROYECTO.firebaseapp.com` y `localhost`.
4. **Configuración del proyecto → Tus apps → Web (</>)**: registra la app y copia `apiKey`, `authDomain`, `projectId`, `appId`.
5. **Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada**: guarda el JSON como
   `api-gateway/secrets/firebase-service-account.json` (carpeta ignorada por git; **no lo compartas**).

## 5. Microservicio de inferencia (Docker)

El microservicio corre en un contenedor Docker. La imagen fija Python 3.12 y `scikit-learn==1.6.1`,
así el `.joblib` de Colab siempre carga con la versión correcta. Los pesos **no** van dentro de la imagen:
`inference-service/models/` se monta como volumen de sólo lectura.

1. Instala y abre **Docker Desktop**: [docs.docker.com/desktop](https://docs.docker.com/desktop/)
   (Windows: backend WSL2). Actívalo en *Settings → General → Start Docker Desktop when you sign in*
   para que la inferencia arranque sola con Windows.
2. Configura el servicio:
   ```powershell
   cd inference-service
   Copy-Item .env.example .env       # (cp .env.example .env)
   ```
   Edita `.env`: `INTERNAL_API_KEY` (genera con `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   y la contraseña de `app_errores` en `ERRORES_DB_URL`. Deja el host como `host.docker.internal`.
3. Comprueba que existen `inference-service/models/model_v1.joblib` (paso 1) y los certificados de `infra/certs/` (paso 3).
   En **Linux**, da permiso de lectura de la llave al contenedor: `sudo chgrp 10001 infra/certs/localhost-key.pem && chmod 640 infra/certs/localhost-key.pem`.
4. Construye y arranca desde la raíz del repositorio:
   ```powershell
   cd ..
   docker compose up -d --build
   docker compose ps          # Debe decir "Up … (healthy)" y 127.0.0.1:8001->8001/tcp
   curl.exe https://127.0.0.1:8001/health   # → {"estado":"ok","modelo_cargado":true}
   ```

| Tarea | Comando (desde la raíz) |
|---|---|
| Ver logs | `docker compose logs -f inferencia` |
| Reiniciar tras reemplazar el `.joblib` (mismo nombre) | `docker compose restart inferencia` |
| Aplicar cambios del `.env` (p. ej. `MODEL_PATH=models/model_v2.joblib`) | `docker compose up -d` |
| Reconstruir tras cambiar código o `requirements.txt` | `docker compose up -d --build` |
| Ver el respaldo de errores (si MySQL falló) | `docker compose exec inferencia cat logs/errores_respaldo.log` |
| Detener | `docker compose down` |

Seguridad del contenedor: publica el puerto **sólo** en `127.0.0.1` (no es accesible desde la red), corre como
usuario sin privilegios, con sistema de archivos de sólo lectura, sin capacidades de Linux y con
`no-new-privileges`; límite de 1 CPU y 1 GB de RAM; `restart: unless-stopped`.

### 5.1 Docker y MySQL de XAMPP

Desde el contenedor, la máquina anfitriona se llama `host.docker.internal` (no `127.0.0.1`).

- **Windows / macOS (Docker Desktop):** normalmente no hay que tocar nada: Docker Desktop reenvía la
  conexión desde la propia máquina y el usuario `app_errores@127.0.0.1` sirve. Si
  `docker compose logs inferencia` o el respaldo de errores muestran
  `Host 'X.X.X.X' is not allowed to connect`, ejecuta `database/04_usuario_docker.sql` cambiando `'172.%'`
  por la red de esa IP (p. ej. `'192.168.65.%'`).
- **Linux (Docker Engine):** el contenedor llega desde la red puente de Docker (`172.x`). Ejecuta
  `database/04_usuario_docker.sql` y haz que MariaDB escuche también en esa interfaz
  (`bind-address=0.0.0.0` en `my.cnf`) **bloqueando el puerto 3306 desde fuera** con el firewall
  (p. ej. `sudo ufw deny 3306` y `sudo ufw allow from 172.16.0.0/12 to any port 3306`).

Si MySQL no está disponible, los errores del microservicio no se pierden: van al archivo rotativo del
volumen Docker `inferencia-logs`.

### 5.2 (Alternativa) Ejecutarlo sin Docker

Para depurar puedes correrlo directamente: `python -m venv .venv`, `pip install -r requirements.txt`,
cambia en `.env` el host de `ERRORES_DB_URL` a `127.0.0.1` y ejecuta `python run.py`
(usa por defecto los certificados de `../infra/certs/`). Detén antes el contenedor (`docker compose down`): ambos usan el puerto 8001.

## 6. API Gateway

```powershell
cd api-gateway
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env`:

| Variable | Valor |
|---|---|
| `CORS_ORIGINS` | `https://TU-PROYECTO.web.app,https://TU-PROYECTO.firebaseapp.com` |
| `ALLOWED_HOSTS` | `api.tudominio.com,localhost,127.0.0.1` |
| `FIREBASE_PROJECT_ID` | id del proyecto |
| `ADMIN_EMAILS` | tu correo (acceso a `/admin`) |
| `INTERNAL_API_KEY` | **la misma** que en la inferencia |
| `CONSULTAS_DB_URL`, `ERRORES_DB_URL`, `ERRORES_ADMIN_DB_URL` | contraseñas del paso 2 |
| `IP_HASH_SALT` | cadena aleatoria |
| `TELEGRAM_*` / `SMTP_*` / `ALERT_EMAIL_TO` | opcional, para alertas |

```powershell
python run.py                 # Gateway en https://localhost:8000
python -m app.alertas         # (otra terminal) worker de alertas
```

## 7. Cloudflare Tunnel

Requiere un dominio gestionado en Cloudflare.

```powershell
winget install --id Cloudflare.cloudflared      # (brew install cloudflared)
cloudflared tunnel login
cloudflared tunnel create stroke-api            # Anota el ID del túnel
cloudflared tunnel route dns stroke-api api.tudominio.com
```

Copia `infra/cloudflared/config.yml.example` a `%USERPROFILE%\.cloudflared\config.yml`, reemplaza
`<ID-DEL-TUNEL>`, rutas y dominio, y ejecuta `cloudflared tunnel run stroke-api`.

En Cloudflare → *SSL/TLS*: modo **Full (strict)**, activa **Always Use HTTPS** y **HSTS**.

Comprobación: `curl https://api.tudominio.com/api/health` → `{"estado":"ok"}`.

## 8. Frontend

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
```

Rellena `.env.local` con los datos web de Firebase y `VITE_API_URL=https://api.tudominio.com`.
En `firebase.json`, reemplaza `https://api.tudominio.com` dentro de la `Content-Security-Policy` por tu dominio real.

```powershell
npm run dev                   # Desarrollo en https://localhost:5173 (usa los certificados de mkcert)
firebase login
Copy-Item .firebaserc.example .firebaserc   # pon tu id de proyecto
npm run deploy                # build + firebase deploy --only hosting
```

> Para desarrollo local agrega `https://localhost:5173` a `CORS_ORIGINS` del gateway.

## 9. Arranque diario

Antes, inicia MySQL en el panel de XAMPP y abre Docker Desktop.

- Windows: `scripts\iniciar_windows.bat` (levanta el contenedor de inferencia con `docker compose up -d`
  y abre gateway, alertas y túnel en ventanas separadas).
- macOS/Linux: `scripts/iniciar.sh` (espera a que el contenedor esté `healthy` antes de arrancar el gateway).

Con `restart: unless-stopped`, el contenedor vuelve a arrancar solo cuando se inicia Docker Desktop.

## 10. Pruebas automatizadas

```powershell
cd inference-service; python -m venv .venv; .venv\Scripts\activate; pip install -r requirements-dev.txt; pytest
cd ..\api-gateway;    pip install -r requirements-dev.txt; pytest
```

No necesitan Firebase, MySQL, Docker ni el modelo real (se simulan). Las pruebas de la inferencia
usan un entorno virtual local aparte del contenedor.

## 11. Solución de problemas

| Síntoma | Causa probable / solución |
|---|---|
| `Falta el certificado TLS` al arrancar | Repite el paso 3; revisa `SSL_CERTFILE`/`SSL_KEYFILE` (gateway) o que `infra/certs/` tenga los 3 archivos (contenedor). |
| Contenedor reiniciándose: `Sin permiso de lectura sobre '/certs/localhost-key.pem'` | Sólo Linux: `sudo chgrp 10001 infra/certs/localhost-key.pem && chmod 640 infra/certs/localhost-key.pem`. |
| `docker compose` no responde / `cannot connect to the Docker daemon` | Docker Desktop no está abierto. |
| `port is already allocated` en el 8001 | Hay un `python run.py` de la inferencia corriendo fuera de Docker; deténlo. |
| 503 "servicio de predicción no disponible" | El contenedor no está `healthy` (`docker compose ps`), `INTERNAL_API_KEY` distinta en los dos `.env`, o `INFERENCE_CA_BUNDLE` no apunta a `rootCA.pem`. Mira `errores_db` o `docker compose logs inferencia`. |
| Contenedor `unhealthy` / `/health` dice `degradado` | No encuentra el `.joblib` de `MODEL_PATH` en `inference-service/models/`. |
| Errores de la inferencia no llegan a `errores_db` | Ver 5.1 (`host.docker.internal`, `04_usuario_docker.sql`). Revisa `docker compose exec inferencia cat logs/errores_respaldo.log`: el campo `fallo_db` dice por qué falló MySQL. |
| 401 en todas las peticiones | `FIREBASE_PROJECT_ID` o cuenta de servicio de otro proyecto; reloj del PC desajustado. |
| 403 "verifica tu correo" | La cuenta de correo no abrió el enlace de verificación. |
| Error CORS en el navegador | Falta el origen exacto (con `https://`) en `CORS_ORIGINS`. |
| 400 "Invalid host header" | Agrega el dominio del túnel a `ALLOWED_HOSTS`. |
| Login con Google bloqueado | Dominio no autorizado en Firebase o CSP de `firebase.json` sin los dominios necesarios. |
| Errores del gateway no aparecen en `errores_db` | Revisa `api-gateway/logs/errores_respaldo.log` (el campo `fallo_db` dice por qué falló MySQL). |
