# CLAUDE.md

Guía para agentes (Claude Code) que trabajen en este repositorio.

## Qué es

App web de predicción de riesgo de stroke. SPA React en Firebase Hosting → Cloudflare Tunnel → API Gateway
FastAPI local (:8000, nativo) → microservicio de inferencia FastAPI (:8001) **en un contenedor Docker** con un
pipeline scikit-learn entrenado en Colab. MySQL de XAMPP (MariaDB) guarda consultas (`consultas_db`) y errores (`errores_db`).
Arquitectura completa: `docs/arquitectura.md`.

## Mapa del código

| Ruta | Contenido |
|---|---|
| `ml/stroke_prediction_colab.py` | **Fuente de verdad** del notebook (formato percent `# %%`) |
| `ml/stroke_prediction_colab.ipynb` | Generado: `python ml/tools/py_to_ipynb.py ml/stroke_prediction_colab.py ml/stroke_prediction_colab.ipynb` |
| `inference-service/app/` | `main.py` (rutas), `model_loader.py` (traduce API → columnas del dataset), `schemas.py`, `error_logger.py` |
| `inference-service/Dockerfile`, `healthcheck.py`, `docker-compose.yml` (raíz) | Imagen y despliegue del microservicio |
| `api-gateway/app/` | `main.py`, `middleware.py` (X-Request-ID, cabeceras, manejadores de excepciones), `auth.py` (Firebase), `db.py`, `inferencia.py`, `routers/`, `alertas.py` |
| `frontend/src/` | `pages/`, `components/` (ErrorBoundary, ProtectedRoute, Layout), `services/api.js`, `context/AuthContext.jsx` |
| `database/*.sql` | Esquemas y usuarios MySQL |
| `docs/api/` | OpenAPI generado: `python scripts/exportar_openapi.py` |

## Comandos

```bash
# Pruebas (no requieren Firebase, MySQL ni modelo real)
cd inference-service && pytest
cd api-gateway && pytest
# Frontend
cd frontend && npm run build
# Inferencia en Docker (desde la raíz)
docker compose up -d --build && docker compose ps   # debe quedar "healthy"
# Regenerar notebook y Swagger tras cambiar código
python ml/tools/py_to_ipynb.py ml/stroke_prediction_colab.py ml/stroke_prediction_colab.ipynb
python scripts/exportar_openapi.py
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
2. Contrato de entrada idéntico en 3 sitios: `inference-service/app/schemas.py`, `api-gateway/app/schemas.py`
   y `frontend/src/constants.js` + ENUMs de `database/01_consultas_db.sql`. Si cambias uno, cambia todos.
3. `model_loader._a_dataframe` debe replicar la limpieza del notebook (banderas como `"0"/"1"`, `Residence_type`,
   `Unknown` → nulo si `tratar_unknown_como_nulo`).
4. `scikit-learn==1.6.1` fijado en el notebook y en `inference-service/requirements.txt` (deben coincidir).
5. Consultas siempre filtradas por el `uid` del token, nunca por un valor enviado por el cliente.
6. Nunca registrar valores clínicos, tokens ni IPs en claro en `errores_db` (usar `sanitizar` / `hash_ip`).
7. `api-gateway/app/error_logger.py` e `inference-service/app/error_logger.py` son copias idénticas (servicios desplegables por separado): mantenlas sincronizadas.
8. Nunca subir `.env`, `secrets/`, `*.pem`, `*.joblib`.
9. Docker: los pesos y certificados se **montan** (nunca `COPY` a la imagen); el puerto se publica sólo como
   `127.0.0.1:8001:8001`; el contenedor corre como uid 10001 con `read_only`, `cap_drop: ALL` y `no-new-privileges`.
   Valores propios del contenedor (HOST, PORT, rutas `/certs`) van en `environment:` de `docker-compose.yml` para que el `.env` no los pise.
10. Desde el contenedor, XAMPP es `host.docker.internal`, no `127.0.0.1`.
