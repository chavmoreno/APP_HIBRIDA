# Documentación de la API (OpenAPI / Swagger)

## ¿Qué es Swagger?

**OpenAPI** es el estándar para describir una API REST en un archivo (JSON o YAML): qué rutas tiene, qué datos
recibe cada una, qué responde, sus códigos de error y cómo se autentica. **Swagger UI** es la página web que lee
ese archivo y lo muestra como documentación interactiva: cada ruta se puede desplegar para ver sus esquemas y
probarla con el botón **Try it out**.

En este proyecto las especificaciones **se generan desde el código** (FastAPI las construye a partir de las rutas y
los modelos Pydantic), así que siempre coinciden con lo que la API acepta de verdad.

## Ver el Swagger

**En línea:** <https://app-hibrida-511815.web.app/swagger/> (se publica con el frontend en Firebase Hosting).
Arriba a la derecha se elige la especificación: *API Gateway (pública)* o *Microservicio de inferencia (interno)*.

Probar rutas desde la página (**Try it out**):

- `GET /api/health` funciona sin autenticación.
- El resto pide un **ID token de Firebase**: inicia sesión en la app, pulsa **F12 → Aplicación (Application) →
  IndexedDB → firebaseLocalStorageDb → firebaseLocalStorage**, copia el valor de `stsTokenManager.accessToken`
  (caduca en 1 hora), pulsa **Authorize** en Swagger y pégalo.
- El microservicio de inferencia **no** se puede probar desde internet: sólo escucha dentro de la VM (por diseño).

Sin publicar: pega `openapi-gateway.yaml` en <https://editor.swagger.io>.

## Archivos

| Archivo | Contenido |
|---|---|
| `openapi-gateway.yaml` / `.json` | API pública (`https://stroke-salva.duckdns.org`): consultas, histórico, errores, admin |
| `openapi-inferencia.yaml` / `.json` | Microservicio interno (`https://127.0.0.1:8001`, sólo dentro de la VM): `/predict`, `/model/info`, `/health` |
| `index.html`, `swagger-init.js` | Página de Swagger UI. `frontend/scripts/copiar_swagger.mjs` la copia a `frontend/public/swagger/` en cada `npm run build`, junto con Swagger UI (`swagger-ui-dist`), para servirla desde el mismo sitio |

## Regenerar las especificaciones (tras cambiar rutas o esquemas)

En el PC no hay Python con las dependencias; se hace en la VM con un contenedor temporal:

```bash
cd APP_HIBRIDA && git pull
docker run --rm -v "$PWD":/repo -w /repo python:3.12.10-slim-bookworm sh -c \
  "pip install -q -r inference-service/requirements.txt -r api-gateway/requirements.txt pyyaml && python scripts/exportar_openapi.py"
```

Luego sube los cambios de `docs/api/` a GitHub y vuelve a publicar el frontend (manual de instalación, §9).

## Resumen de endpoints

### API Gateway

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/health` | — | Estado del gateway |
| POST | `/api/consultas` | Bearer | Crea una consulta: predice y guarda. **201** con el resultado |
| GET | `/api/consultas?limit&offset` | Bearer | Histórico paginado del usuario |
| GET | `/api/consultas/{id}` | Bearer | Detalle (404 si no es del usuario) |
| POST | `/api/errores` | Opcional | Reporte de error JS del frontend. **204** |
| GET | `/api/admin/errores` | Bearer + admin | Log de errores con filtros |
| GET | `/api/admin/errores/resumen?horas` | Bearer + admin | Conteo por origen/severidad |

Formato de error uniforme:

```json
{ "error": { "codigo": 422, "mensaje": "Datos de entrada inválidos", "request_id": "9ae5…", "detalles": [{"campo": "body.age", "error": "…"}] } }
```

### Microservicio de inferencia

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | — | Vivo / modelo cargado |
| POST | `/predict` | `X-Internal-API-Key` | Probabilidad, clase y nivel de riesgo |
| GET | `/model/info` | `X-Internal-API-Key` | Versión, umbral, bandas y métricas del modelo |
