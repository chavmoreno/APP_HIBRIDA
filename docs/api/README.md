# Documentación de la API (OpenAPI / Swagger)

| Archivo | Contenido |
|---|---|
| `openapi-gateway.yaml` / `.json` | API pública (`https://tu-app.duckdns.org`): consultas, histórico, errores, admin |
| `openapi-inferencia.yaml` / `.json` | Microservicio interno (`https://127.0.0.1:8001`): `/predict`, `/model/info`, `/health` |
| `index.html` | Swagger UI que carga ambas especificaciones |

## Ver el Swagger

```bash
cd docs/api
python -m http.server 8080
# abre http://localhost:8080  (servidor estático local, sólo lectura de la documentación)
```

También puedes pegar el YAML en https://editor.swagger.io.
Con `EXPONER_DOCS=true` en `api-gateway/.env`, el gateway sirve Swagger en vivo en `https://tu-app.duckdns.org/docs` (déjalo en `false` en producción).
El microservicio de inferencia siempre lo sirve en `https://127.0.0.1:8001/docs` (sólo accesible desde dentro de la VM).

## Regenerar las especificaciones

Las specs se generan desde el código (FastAPI), así nunca quedan desactualizadas:

```bash
python scripts/exportar_openapi.py
```

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
