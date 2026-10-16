# CLAUDE.md

Guía para agentes (Claude Code) que trabajen en este repositorio.

## Qué es

App web de predicción de riesgo de stroke. SPA React en Firebase Hosting → Caddy (HTTPS, dominio DuckDNS) → **VM de Oracle Cloud
Always Free** (Ampere A1, ARM; todo debe costar USD 0) con Docker: API Gateway FastAPI (:8000), microservicio de inferencia FastAPI (:8001, pipeline scikit-learn
entrenado en Colab) y worker de alertas. **Lo único local es MySQL de XAMPP (MariaDB)** en el PC de casa, que guarda
consultas (`consultas_db`) y errores (`errores_db`); la VM lo alcanza en su `127.0.0.1:3306` por un túnel SSH inverso
que abre el PC (`scripts/tunel_mysql.bat`). El PC no debe necesitar Docker, Python ni Node.
Arquitectura completa: `docs/arquitectura.md`.

## Mapa del código

| Ruta | Contenido |
|---|---|
| `ml/stroke_prediction_colab.py` | **Fuente de verdad** del notebook (formato percent `# %%`) |
| `ml/stroke_prediction_colab.ipynb` | Generado: `python ml/tools/py_to_ipynb.py ml/stroke_prediction_colab.py ml/stroke_prediction_colab.ipynb` |
| `inference-service/app/` | `main.py` (rutas), `model_loader.py` (traduce API → columnas del dataset), `schemas.py`, `error_logger.py` |
| `inference-service/Dockerfile`, `healthcheck.py` | Imagen del microservicio |
| `api-gateway/app/` | `main.py`, `middleware.py` (X-Request-ID, cabeceras, manejadores de excepciones), `auth.py` (Firebase), `db.py`, `inferencia.py`, `routers/`, `alertas.py` |
| `api-gateway/Dockerfile`, `docker-compose.yml` (raíz) | Imagen del gateway (también la usa el worker de alertas) y despliegue de los 3 contenedores en la VM |
| `infra/oracle/instalar_vm.sh` | Prepara la VM: Docker, iptables 80/443, CA/certificados internos, secretos subidos, dominio, usuario `tunel`, arranque |
| `infra/caddy/Caddyfile` | Única entrada pública: HTTPS de Let's Encrypt → gateway por HTTPS en el loopback |
| `scripts/tunel_mysql.bat` | Túnel SSH inverso PC → VM para MySQL (usa el `ssh` de Windows) |
| `frontend/src/` | `pages/`, `components/` (ErrorBoundary, ProtectedRoute, Layout), `services/api.js`, `context/AuthContext.jsx` |
| `frontend/scripts/copiar_swagger.mjs` | `prebuild`: copia `docs/api` + Swagger UI a `public/swagger` → `https://app-hibrida-511815.web.app/swagger/` |
| `database/*.sql` | Esquemas y usuarios MySQL |
| `docs/api/` | OpenAPI generado (`scripts/exportar_openapi.py`, se ejecuta en la VM: ver `docs/api/README.md`) + página Swagger UI |
| `INSTRUCCIONES_INICIO_FIN.md` | Encender/apagar la app y costos |

Despliegue real: API `https://stroke-salva.duckdns.org` (VM Oracle `159.54.154.188`, usuario `ubuntu`, llave
`%USERPROFILE%\.ssh\stroke_admin`), web `https://app-hibrida-511815.web.app`, Firebase `app-hibrida-511815`.

## Comandos

```bash
# Pruebas (no requieren Firebase, MySQL ni modelo real). El PC no tiene Python/Node útiles: en la VM, con contenedores temporales
docker run --rm -v "$PWD":/repo -w /repo/inference-service python:3.12.10-slim-bookworm sh -c "pip install -q -r requirements-dev.txt && pytest -q"
docker run --rm -v "$PWD":/repo -w /repo/api-gateway python:3.12.10-slim-bookworm sh -c "pip install -q -r requirements-dev.txt && pytest -q"
# Frontend (Cloud Shell o contenedor node:22): el prebuild copia el Swagger
cd frontend && npm ci && npm run build
# Contenedores (en la VM, desde la raíz del repo)
docker compose up -d --build && docker compose ps   # stroke-inferencia debe quedar "healthy"
# Regenerar notebook y Swagger tras cambiar código
python ml/tools/py_to_ipynb.py ml/stroke_prediction_colab.py ml/stroke_prediction_colab.ipynb
# OpenAPI: comando completo en docs/api/README.md (contenedor con las dependencias de ambos servicios)
# Probar el notebook fuera de Colab con un CSV local
STROKE_CSV=/ruta/stroke.csv MPLBACKEND=Agg python ml/stroke_prediction_colab.py
```

## Convenciones

- **Idioma**: código, comentarios, mensajes y documentación en **español**. Excepción: los nombres de
  columnas/valores del dataset de Kaggle (`gender`, `Private`, `never smoked`…) se mantienen en inglés en la API y BD.
- **Comentarios**: el usuario pidió *todo el código comentado*. Cada módulo lleva docstring y cada función/bloque no trivial un comentario.
- Python: type hints, Pydantic v2, SQLAlchemy Core con `text()` **siempre parametrizado**.
- Respuestas de error del gateway: `{"error": {"codigo", "mensaje", "request_id", "detalles?"}}`.

## Invariantes (no romper)

1. **HTTPS exclusivo**: los `run.py` abortan sin certificado; nunca `verify=False`, `noTLSVerify` ni URLs `http://`.
   Los certificados internos los genera `infra/oracle/instalar_vm.sh` (CA propia); Caddy verifica al gateway con `rootCA.pem`.
2. Contrato de entrada idéntico en 3 sitios: `inference-service/app/schemas.py`, `api-gateway/app/schemas.py`
   y `frontend/src/constants.js` + ENUMs de `database/01_consultas_db.sql`. Si cambias uno, cambia todos.
3. `model_loader._a_dataframe` debe replicar la limpieza del notebook (banderas como `"0"/"1"`, `Residence_type`,
   `Unknown` → nulo si `tratar_unknown_como_nulo`).
4. `scikit-learn==1.6.1` fijado en el notebook y en `inference-service/requirements.txt` (deben coincidir).
5. Consultas siempre filtradas por el `uid` del token, nunca por un valor enviado por el cliente.
6. Nunca registrar valores clínicos, tokens ni IPs en claro en `errores_db` (usar `sanitizar` / `hash_ip`).
7. `api-gateway/app/error_logger.py` e `inference-service/app/error_logger.py` son copias idénticas (servicios desplegables por separado): mantenlas sincronizadas.
8. Nunca subir `.env`, `secrets/`, `*.pem` ni llaves. `*.joblib` está ignorado, **salvo** `inference-service/models/model_v1.joblib`,
   que se versiona a propósito (decisión del usuario) para que la VM lo reciba con `git clone`.
9. Docker: pesos, certificados y secretos se **montan** (nunca `COPY` a la imagen); los contenedores usan
   `network_mode: host` y cada servicio escucha **sólo en `127.0.0.1`** (nunca `0.0.0.0`, nunca `ports:`), salvo Caddy en 80/443; corren como
   uid 10001 con `read_only`, `cap_drop: ALL` y `no-new-privileges`. Valores propios del contenedor (HOST, PORT, rutas
   `/certs`, INFERENCE_URL…) van en `environment:` de `docker-compose.yml` para que el `.env` no los pise.
10. MySQL de XAMPP sigue con `bind-address=127.0.0.1` y nunca se expone: la VM lo ve en su `127.0.0.1:3306` sólo a
    través del túnel SSH inverso. El usuario `tunel` de la VM no tiene shell y sólo puede `permitlisten="127.0.0.1:3306"`.
