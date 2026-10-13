# Manual de instalación y despliegue

Guía paso a paso para poner en marcha la aplicación. Los comandos están para **Windows (PowerShell)**,
que es donde normalmente corre XAMPP; las variantes de macOS/Linux van entre paréntesis.

## 0. Requisitos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.11 – 3.13 | Gateway e inferencia |
| Node.js | 20+ | Construir el frontend |
| XAMPP | 8.x (MariaDB 10.4+) | `consultas_db` y `errores_db` |
| mkcert | 1.4+ | Certificados HTTPS locales |
| cloudflared | reciente | Cloudflare Tunnel |
| Firebase CLI | `npm i -g firebase-tools` | Desplegar el frontend |
| Cuentas | Google (Firebase/Colab), Kaggle, Cloudflare con un dominio | |

## 1. Entrenar el modelo en Google Colab

1. Abre `ml/stroke_prediction_colab.ipynb` en Colab:
   *Archivo → Abrir notebook → GitHub →* `chavmoreno/APP_HIBRIDA` (o sube el `.ipynb`).
2. (Opcional) Si Kaggle pide autenticación: kaggle.com → *Settings → API → Create New Token*.
   En Colab, panel **🔑 Secrets**, crea `KAGGLE_USERNAME` y `KAGGLE_KEY` y activa el acceso del notebook.
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

## 5. Microservicio de inferencia

```powershell
cd inference-service
python -m venv .venv
.venv\Scripts\activate            # (source .venv/bin/activate)
pip install -r requirements.txt
Copy-Item .env.example .env       # (cp .env.example .env)
```

Edita `.env`: `INTERNAL_API_KEY` (genera con `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
y la contraseña de `app_errores` en `ERRORES_DB_URL`. Arranca:

```powershell
python run.py
# Comprobar:  curl.exe https://127.0.0.1:8001/health   →  {"estado":"ok","modelo_cargado":true}
```

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

- Windows: `scripts\iniciar_windows.bat` (abre inferencia, gateway, alertas y túnel en ventanas separadas).
- macOS/Linux: `scripts/iniciar.sh`.

Antes, inicia MySQL en el panel de XAMPP.

## 10. Pruebas automatizadas

```powershell
cd inference-service; pip install -r requirements-dev.txt; pytest
cd ..\api-gateway;    pip install -r requirements-dev.txt; pytest
```

No necesitan Firebase, MySQL ni el modelo real (se simulan).

## 11. Solución de problemas

| Síntoma | Causa probable / solución |
|---|---|
| `Falta el certificado TLS` al arrancar | Repite el paso 3; revisa `SSL_CERTFILE`/`SSL_KEYFILE`. |
| 503 "servicio de predicción no disponible" | La inferencia no está corriendo, `INTERNAL_API_KEY` distinta, o `INFERENCE_CA_BUNDLE` no apunta a `rootCA.pem`. Mira `errores_db` o `logs/errores_respaldo.log`. |
| `/health` de inferencia dice `degradado` | No encuentra `models/model_v1.joblib` o la versión de scikit-learn no coincide. |
| 401 en todas las peticiones | `FIREBASE_PROJECT_ID` o cuenta de servicio de otro proyecto; reloj del PC desajustado. |
| 403 "verifica tu correo" | La cuenta de correo no abrió el enlace de verificación. |
| Error CORS en el navegador | Falta el origen exacto (con `https://`) en `CORS_ORIGINS`. |
| 400 "Invalid host header" | Agrega el dominio del túnel a `ALLOWED_HOSTS`. |
| Login con Google bloqueado | Dominio no autorizado en Firebase o CSP de `firebase.json` sin los dominios necesarios. |
| Errores no aparecen en `errores_db` | Revisa `logs/errores_respaldo.log` (el campo `fallo_db` dice por qué falló MySQL). |
