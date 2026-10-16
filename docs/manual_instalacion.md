# Manual de instalación y despliegue

Guía paso a paso para poner en marcha la aplicación. **En tu PC sólo vive la base de datos (XAMPP)**; todo lo demás
corre en la nube:

| Dónde | Qué |
|---|---|
| **PC de casa (Windows)** | XAMPP (MySQL) + `scripts\tunel_mysql.bat` (usa el `ssh` que ya trae Windows: no se instala nada) |
| **Oracle Cloud — VM Always Free (ARM)** | Docker: API Gateway, microservicio de inferencia, worker de alertas y Caddy (HTTPS) |
| **Firebase** | Frontend (Hosting) y Authentication |
| **DuckDNS + Let's Encrypt** | Dominio público gratuito `tu-app.duckdns.org` con certificado HTTPS |
| **Google Colab** | Entrenamiento del modelo |

Las tareas que antes necesitaban Python o Node en el PC (construir el frontend, pruebas) se hacen desde
**Google Cloud Shell**, una terminal gratuita en el navegador. **Todo es gratis** (sección 12).

## 0. Requisitos

| Qué | Para qué |
|---|---|
| XAMPP 7.4+ / 8.x (MariaDB 10.4+) en el PC | `consultas_db` y `errores_db` |
| Cuenta de Google | Firebase, Cloud Shell y Colab |
| Cuenta de Oracle Cloud (pide tarjeta sólo para verificar) | VM gratuita |
| Cuenta de DuckDNS (con Google o GitHub) | Dominio gratuito |
| Cuenta de Kaggle | Dataset (opcional: es público) |

## 1. Entrenar el modelo en Google Colab

1. Abre `ml/stroke_prediction_colab.ipynb` en Colab:
   *Archivo → Abrir notebook → GitHub →* `chavmoreno/APP_HIBRIDA` (o sube el `.ipynb`).
2. (Opcional, el dataset es público) Si Kaggle pide autenticación: kaggle.com → *Settings → API →
   Generate New Token*. Kaggle muestra el **API Token una sola vez**: cópialo. En Colab, panel **🔑 Secrets**,
   crea un secreto llamado `KAGGLE_API_TOKEN` con ese valor y activa *Acceso al notebook*.
   (Con un `kaggle.json` antiguo también sirven los secretos `KAGGLE_USERNAME` y `KAGGLE_KEY`.)
3. *Entorno de ejecución → Ejecutar todo*. Al final se descargan `model_v1.joblib` y `model_v1.metadata.json`.
4. Guárdalos: los subirás a la VM en el paso 7.

> El notebook fija `scikit-learn==1.6.1`, la misma versión que `inference-service/requirements.txt`.
> Si las cambias, cámbialas en ambos sitios.

## 2. Bases de datos en XAMPP (PC)

1. Inicia **MySQL** desde el panel de XAMPP.
2. MySQL debe escuchar sólo en la máquina local: en `C:\xampp\mysql\bin\my.ini`, sección `[mysqld]`,
   `bind-address=127.0.0.1`. **No lo cambies**: la VM llega a MySQL por el túnel SSH, que entra por `127.0.0.1`.

   **Atajo / si MySQL deja de arrancar tras editar `my.ini`:** con MySQL detenido, ejecuta desde la raíz del proyecto
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\configurar_xampp_mysql.ps1
   ```
   **¿Olvidaste la contraseña de `root`?** Con MySQL detenido:
   `powershell -ExecutionPolicy Bypass -File scripts\restablecer_root_xampp.ps1`.
3. Edita `database/03_usuarios.sql` y cambia cada `cambia-esta-clave` por contraseñas fuertes
   (las mismas irán en los `.env` del paso 7).
4. Ejecuta los scripts en orden (phpMyAdmin → pestaña SQL, o consola):
   ```powershell
   cd database
   Get-Content 01_consultas_db.sql | C:\xampp\mysql\bin\mysql.exe -u root -p
   Get-Content 02_errores_db.sql   | C:\xampp\mysql\bin\mysql.exe -u root -p
   Get-Content 03_usuarios.sql     | C:\xampp\mysql\bin\mysql.exe -u root -p
   ```

Los usuarios `@127.0.0.1` / `@localhost` sirven tal cual: las conexiones de la VM llegan a MySQL desde el
cliente `ssh` del propio PC.

## 3. Firebase (Authentication + Hosting)

1. [console.firebase.google.com](https://console.firebase.google.com) → *Agregar proyecto* (plan **Spark**, gratuito).
2. **Authentication → Método de acceso**: habilita **Correo electrónico/contraseña** y **Google**.
3. **Authentication → Configuración → Dominios autorizados**: deja `TU-PROYECTO.web.app` y `TU-PROYECTO.firebaseapp.com`.
4. **Configuración del proyecto → Tus apps → Web (</>)**: registra la app y copia `apiKey`, `authDomain`, `projectId`, `appId`.
5. **Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada**: guarda el JSON como
   `firebase-service-account.json` (**no lo compartas ni lo subas a git**). Lo subirás a la VM en el paso 7.

## 4. Cuenta de Oracle Cloud (Always Free)

> **Costo: USD 0.** El nivel *Always Free* de Oracle incluye para siempre una VM ARM **Ampere A1** de hasta
> 2 OCPU y 12 GB de RAM, 200 GB de disco, la **IP pública** y 10 TB/mes de salida. Detalle en la sección 12.

1. Regístrate en [oracle.com/cloud/free](https://www.oracle.com/cloud/free/). Pide una **tarjeta sólo para verificar
   tu identidad** (puede aparecer un cargo temporal que se devuelve; algunas tarjetas prepago no se aceptan).
2. **Región de origen (home region)**: elige la más cercana. **No se puede cambiar después** y los recursos gratuitos
   sólo existen ahí.
3. **Pasa la cuenta a Pay As You Go** (*Billing & Cost Management → Upgrade and Manage Payment*). Sigues sin pagar
   nada mientras uses sólo recursos *Always Free*, y evita que Oracle **detenga la VM por inactividad** (en cuentas
   gratuitas apaga las VM que pasan 7 días con CPU, red y memoria por debajo del 20 %, y esta app casi siempre lo está).
4. **Presupuesto con alerta** (*Billing & Cost Management → Budgets → Create Budget*): monto **USD 1**, alerta al
   100 % a tu correo. Si algo empieza a costar, te enteras. (La alerta avisa, no frena el gasto.)

## 5. Crear la VM

1. En el PC, la llave de administración se crea una sola vez (PowerShell; usa el `ssh-keygen` de Windows):
   ```powershell
   ssh-keygen -t ed25519 -N '""' -C stroke-admin -f $env:USERPROFILE\.ssh\stroke_admin
   Get-Content $env:USERPROFILE\.ssh\stroke_admin.pub     # Copia esta línea (llave PÚBLICA)
   ```
2. **Compute → Instances → Create instance**. Revisa cada campo:

   | Campo | Valor | Por qué |
   |---|---|---|
   | Name | `stroke-vm` | — |
   | Image | **Canonical Ubuntu 24.04** | El script de instalación está hecho para Ubuntu |
   | Shape | **Ampere → VM.Standard.A1.Flex**, **1 OCPU, 6 GB** | Debe decir *Always Free-eligible*. Hasta 2 OCPU / 12 GB sigue siendo gratis |
   | Networking | Crear VCN y **subred pública**; **Assign a public IPv4 address: Sí** | La IP pública es gratuita en Oracle |
   | Add SSH keys | **Paste public keys** → la línea de `stroke_admin.pub` | Para entrar desde PowerShell |
   | Boot volume | El tamaño por defecto (~50 GB) | Entra en los 200 GB gratuitos |

   Si sale **"Out of capacity"**, prueba otro *Availability domain* o reinténtalo más tarde (pasa a menudo con A1).
3. Anota la **Public IP address** de la instancia. Se conserva mientras no **termines** la VM.
4. Abre los puertos web en la red de Oracle: en la instancia, *Primary VNIC → Subnet → Security Lists →
   Default Security List → Add Ingress Rules*, dos reglas con **Source CIDR** `0.0.0.0/0`, **IP Protocol** TCP y
   **Destination Port** `80` y `443`. (El SSH, puerto 22, ya viene abierto. MySQL **no** se abre: va por el túnel.)

## 6. Dominio gratuito en DuckDNS

1. Entra en [duckdns.org](https://www.duckdns.org) con tu cuenta de Google o GitHub.
2. Crea un subdominio, por ejemplo `tu-app` → `tu-app.duckdns.org`.
3. En **current ip** escribe la IP pública de la VM y pulsa **update ip**.

Caddy pedirá el certificado HTTPS de Let's Encrypt para ese nombre (gratis, se renueva solo).

## 7. Preparar la VM

1. Rellena en el PC los archivos que vas a subir (carpeta `secrets\`, ignorada por git; o cópialos de los `.env.example`):

   | Archivo | Contenido |
   |---|---|
   | `gateway.env` | `api-gateway/.env.example` rellenado: Firebase, `CORS_ORIGINS`, `ALLOWED_HOSTS` con tu dominio de DuckDNS, `ADMIN_EMAILS`, contraseñas del paso 2, `INTERNAL_API_KEY`, `IP_HASH_SALT` |
   | `inferencia.env` | `inference-service/.env.example` con la **misma** `INTERNAL_API_KEY` y la contraseña de `app_errores` |
   | `firebase-service-account.json` | El JSON del paso 3 |

   Para `INTERNAL_API_KEY` e `IP_HASH_SALT` usa cadenas aleatorias largas (en la VM: `openssl rand -base64 32`).
2. Súbelos desde PowerShell, en la raíz del proyecto (`scp` viene con Windows):
   ```powershell
   scp -i $env:USERPROFILE\.ssh\stroke_admin secrets\gateway.env secrets\inferencia.env RUTA\firebase-service-account.json ubuntu@IP-DE-LA-VM:
   ```
   (Si reentrenaste el modelo, agrega también `model_v1.joblib` y `model_v1.metadata.json`; si no, el del repo sirve.)
3. Crea la llave del túnel de MySQL (una sola vez) y copia la línea pública:
   ```powershell
   ssh-keygen -t ed25519 -N '""' -C stroke-tunel -f $env:USERPROFILE\.ssh\stroke_tunel
   Get-Content $env:USERPROFILE\.ssh\stroke_tunel.pub
   ```
4. Entra a la VM y ejecuta el instalador:
   ```powershell
   ssh -i $env:USERPROFILE\.ssh\stroke_admin ubuntu@IP-DE-LA-VM
   ```
   ```bash
   git clone https://github.com/chavmoreno/APP_HIBRIDA.git
   cd APP_HIBRIDA
   sudo bash infra/oracle/instalar_vm.sh "ssh-ed25519 AAAA...llave-de-stroke_tunel... stroke-tunel" tu-app.duckdns.org tu-correo@gmail.com
   ```
   El script instala Docker, abre 80/443 en el firewall interno de Ubuntu, genera los certificados TLS internos,
   coloca los archivos subidos, crea el usuario restringido `tunel`, guarda el dominio para Caddy y arranca los
   contenedores. Al final `docker compose ps` debe mostrar `stroke-inferencia` como `healthy` y `stroke-caddy` arriba.
   (Si subes archivos después, repite el script sin argumentos: es seguro.)

## 8. Túnel de MySQL desde el PC

1. Crea `secrets\vm_ip.txt` en la raíz del proyecto con la IP pública de la VM o `tu-app.duckdns.org` (una línea).
2. Con MySQL iniciado en XAMPP, abre con doble clic **`scripts\tunel_mysql.bat`** y déjalo abierto. Se reconecta solo.
3. Comprueba:
   ```bash
   docker compose logs --tail 20 gateway          # en la VM: sin errores de MySQL
   curl https://tu-app.duckdns.org/api/health     # desde cualquier sitio → {"estado":"ok"}
   ```

## 9. Frontend (desde Google Cloud Shell)

Cloud Shell es una terminal gratuita en el navegador con Node incluido: no instalas nada en el PC.

1. Abre [shell.cloud.google.com](https://shell.cloud.google.com) con la cuenta de Google del proyecto de Firebase.
2. ```bash
   git clone https://github.com/chavmoreno/APP_HIBRIDA.git && cd APP_HIBRIDA/frontend
   cp .env.example .env.local && nano .env.local    # datos web de Firebase y VITE_API_URL=https://tu-app.duckdns.org
   sed -i 's#https://tu-app.duckdns.org#https://TU-SUBDOMINIO.duckdns.org#' firebase.json   # CSP connect-src
   cp .firebaserc.example .firebaserc && nano .firebaserc   # tu id de proyecto
   npm ci
   npx firebase-tools login --no-localhost
   npm run build && npx firebase-tools deploy --only hosting
   ```

## 10. Operación diaria

**PC:** inicia MySQL en XAMPP y abre `scripts\tunel_mysql.bat`. Nada más.
**VM:** siempre encendida; los contenedores arrancan solos (`restart: unless-stopped`).

| Tarea | Comando (en la VM, carpeta `APP_HIBRIDA`) |
|---|---|
| Estado | `docker compose ps` |
| Ver logs | `docker compose logs -f gateway` (o `inferencia`, `alertas`, `caddy`) |
| Nuevo modelo con el mismo nombre | Súbelo con `scp`, `sudo bash infra/oracle/instalar_vm.sh` y `docker compose restart inferencia` |
| Nueva versión (`model_v2.joblib`) | Súbelo, `sudo bash infra/oracle/instalar_vm.sh`, cambia `MODEL_PATH` en `inference-service/.env` y `docker compose up -d` |
| Aplicar cambios de un `.env` | `docker compose up -d` |
| Actualizar el código | `git pull && docker compose up -d --build` |
| Ver el respaldo de errores (si MySQL no respondía) | `docker compose exec gateway cat logs/errores_respaldo.log` |
| Detener | `docker compose down` |

Si el PC está apagado o el túnel caído, la app sigue prediciendo pero **no guarda** consultas (`guardada: false`) y los
errores van al respaldo en archivo de cada contenedor.

## 11. Pruebas automatizadas (en Cloud Shell)

```bash
cd APP_HIBRIDA/inference-service && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt && pytest
deactivate; cd ../api-gateway && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt && pytest
```

No necesitan Firebase, MySQL, Docker ni el modelo real (se simulan).

### Solución de problemas

| Síntoma | Causa probable / solución |
|---|---|
| Oracle: "Out of capacity" al crear la VM | Otro *Availability domain*, reintentar más tarde, o 1 OCPU / 6 GB si pediste más. |
| `curl https://tu-app.duckdns.org` no responde / Caddy sin certificado | `docker compose logs caddy`. Revisa: reglas 80/443 en la Security List (paso 5.4), IP correcta en DuckDNS (paso 6), y que `.env` de la raíz tenga `DOMINIO`. |
| `tunel_mysql.bat`: `Permission denied (publickey)` | La llave pública del paso 7.3 no se pasó al script, o no coincide. Repite el instalador con la llave. |
| `tunel_mysql.bat`: `remote port forwarding failed for listen port 3306` | Queda una sesión vieja del túnel en la VM; se libera sola en ~90 s (reintenta automáticamente). |
| Consultas con `guardada: false` / `Can't connect to MySQL server on '127.0.0.1'` | El túnel no está abierto o MySQL de XAMPP está detenido. |
| `Access denied for user 'app_…'` | La contraseña del `.env` no coincide con la de `03_usuarios.sql`. |
| XAMPP: `MySQL shutdown unexpectedly` tras editar `my.ini` | Ejecuta `scripts\configurar_xampp_mysql.ps1` (paso 2) y vuelve a pulsar *Start*. |
| `stroke-inferencia` `unhealthy` / `/health` dice `degradado` | Falta el `.joblib` de `MODEL_PATH` en `inference-service/models/` de la VM. |
| Contenedor reiniciándose: `Sin permiso de lectura sobre '/certs/localhost-key.pem'` | Repite `sudo bash infra/oracle/instalar_vm.sh` (ajusta los permisos de la llave). |
| 502 desde Caddy | `docker compose ps`: ¿gateway arriba? Mira `docker compose logs gateway`. |
| 503 "servicio de predicción no disponible" | Inferencia no `healthy` o `INTERNAL_API_KEY` distinta en los dos `.env`. |
| La VM apareció detenida | Si no pasaste la cuenta a Pay As You Go, Oracle la apagó por inactividad: arráncala y haz el paso 4.3. |
| 401 en todas las peticiones | `FIREBASE_PROJECT_ID` o cuenta de servicio de otro proyecto. |
| 403 "verifica tu correo" | La cuenta de correo no abrió el enlace de verificación. |
| Error CORS en el navegador | Falta el origen exacto (con `https://`) en `CORS_ORIGINS`. |
| 400 "Invalid host header" | Agrega tu dominio de DuckDNS a `ALLOWED_HOSTS`. |
| Login con Google bloqueado | Dominio no autorizado en Firebase o CSP de `firebase.json` sin los dominios necesarios. |

## 12. Costos

| Servicio | Costo |
|---|---|
| VM Oracle **VM.Standard.A1.Flex** (hasta 2 OCPU / 12 GB), 24 h | **USD 0** (Always Free, sin límite de tiempo) |
| Disco de arranque (~50 GB de los 200 GB gratuitos) | **USD 0** |
| IP pública IPv4 de la VM | **USD 0** |
| Salida de datos | **USD 0** hasta 10 TB/mes |
| DuckDNS (dominio) + Let's Encrypt (HTTPS) | **USD 0** |
| Firebase Hosting + Authentication (plan Spark) | **USD 0** |
| Google Cloud Shell, Colab, Kaggle | **USD 0** |
| PC de casa | Sólo la luz: XAMPP y el túnel |

Para que siga en USD 0:

- Crea **sólo** recursos marcados *Always Free-eligible*: una VM A1 (máx. 2 OCPU y 12 GB entre todas), sin
  balanceadores de carga, sin bases de datos de pago, sin volúmenes fuera de la región de origen.
- Mantén el presupuesto de USD 1 con alerta (paso 4.4) y revisa *Billing → Cost Analysis* la primera semana.
- Pay As You Go sólo cobra lo que **supere** el nivel gratuito; si dudas de un recurso, no lo crees.
