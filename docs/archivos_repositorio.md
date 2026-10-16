# Archivos del repositorio

Qué es cada archivo de Stroke Risk App y para qué sirve, agrupado por carpeta.
Los secretos (`.env`, `secrets/`, certificados y llaves) **no** están en el repositorio: viven sólo en el PC o en la VM.

## Raíz

| Archivo | Qué es |
|---|---|
| `README.md` | Portada del proyecto: qué hace, enlaces en línea, arquitectura resumida, inicio rápido y costo |
| `INSTRUCCIONES_INICIO_FIN.md` | Cómo encender y apagar la app, qué pasa con cada pieza apagada, costos y cómo borrar todo al terminar |
| `CLAUDE.md` | Guía para asistentes de IA que trabajen en el repo: mapa del código, comandos, convenciones y reglas que no se deben romper |
| `docker-compose.yml` | Define los 4 contenedores de la VM (inferencia, gateway, alertas y Caddy), su seguridad, volúmenes y límites de memoria |
| `.gitignore` | Lo que git nunca sube: `.env`, `secrets/`, certificados, logs, `node_modules`, copias generadas del Swagger… |
| `.gitattributes` | Fija los finales de línea: CRLF en `.bat` (Windows) y LF en `.sh` (Linux) |

## `api-gateway/` — API pública (FastAPI, puerto 8000)

| Archivo | Qué es |
|---|---|
| `Dockerfile` | Imagen del gateway (también la usa el worker de alertas): Python 3.12, usuario sin privilegios |
| `.dockerignore` | Excluye de la imagen secretos, pruebas, logs y entornos virtuales |
| `.env.example` | Plantilla de configuración: Firebase, CORS, dominio, bases de datos, llave interna, alertas |
| `requirements.txt` | Dependencias de producción (FastAPI, uvicorn, SQLAlchemy, PyMySQL, firebase-admin…) con versión fija |
| `requirements-dev.txt` | Dependencias de producción + `pytest` para las pruebas |
| `run.py` | Arranca el gateway **sólo por HTTPS**; si falta el certificado, no arranca |
| `app/__init__.py` | Marca la carpeta `app` como paquete de Python |
| `app/main.py` | Crea la aplicación FastAPI: CORS, hosts permitidos, rutas y `/api/health` |
| `app/config.py` | Lee la configuración de variables de entorno / `.env` (Pydantic Settings) |
| `app/middleware.py` | Asigna el `X-Request-ID`, añade cabeceras de seguridad y convierte todo error en una respuesta uniforme que se registra |
| `app/auth.py` | Verifica el ID token de Firebase (firma, expiración, revocación) y el correo verificado; detecta administradores |
| `app/contexto.py` | Objetos compartidos: request-id de la petición, registrador de errores, IP real del cliente y su hash |
| `app/db.py` | Acceso a MySQL con consultas parametrizadas: guardar y listar consultas (siempre por usuario) y leer errores |
| `app/inferencia.py` | Cliente HTTPS hacia el microservicio de inferencia (verifica su certificado con la CA interna) |
| `app/schemas.py` | Modelos de datos de entrada y salida (Pydantic): datos del paciente, resultado, consulta, errores |
| `app/error_logger.py` | Guarda errores en `errores_db`, sanitizados; si MySQL falla, en un archivo rotativo (copia idéntica a la de inferencia) |
| `app/alertas.py` | Worker que cada 60 s envía por Telegram o correo los errores CRITICAL no notificados |
| `app/routers/__init__.py` | Marca la carpeta `routers` como paquete |
| `app/routers/consultas.py` | Rutas `/api/consultas`: crear consulta (predecir y guardar), histórico y detalle |
| `app/routers/errores.py` | Ruta `POST /api/errores` para que la página reporte sus errores de JavaScript (con límite por IP) |
| `app/routers/admin.py` | Rutas `/api/admin/...` del panel de errores, sólo para administradores |
| `tests/__init__.py` | Marca la carpeta de pruebas como paquete |
| `tests/conftest.py` | Configuración de pruebas: variables seguras sin Firebase ni MySQL reales |
| `tests/test_gateway.py` | 11 pruebas automáticas del gateway (autenticación, validación, errores, aislamiento por usuario…) |

## `inference-service/` — Microservicio del modelo (FastAPI, puerto 8001, interno)

| Archivo | Qué es |
|---|---|
| `Dockerfile` | Imagen de la inferencia: Python 3.12 y scikit-learn 1.6.1 fijos; los pesos se montan, no se copian |
| `.dockerignore` | Excluye de la imagen secretos, pruebas, logs y el propio modelo |
| `.env.example` | Plantilla: ruta del modelo, llave interna y base de errores |
| `requirements.txt` | Dependencias con versión fija (scikit-learn debe coincidir con el notebook) |
| `requirements-dev.txt` | Dependencias + `pytest` y `httpx` para las pruebas |
| `run.py` | Arranca el servicio sólo por HTTPS y comprueba que pueda leer la llave del certificado |
| `healthcheck.py` | Lo usa Docker para saber si el contenedor está sano (consulta `/health` por HTTPS) |
| `app/__init__.py` | Marca la carpeta `app` como paquete |
| `app/main.py` | Rutas `/predict`, `/model/info` y `/health`; exige la llave interna del gateway |
| `app/config.py` | Configuración desde variables de entorno |
| `app/model_loader.py` | Carga el `.joblib` y convierte los datos de la API al formato del dataset antes de predecir |
| `app/schemas.py` | Contrato de entrada/salida del modelo (Pydantic) |
| `app/error_logger.py` | Registro de errores (copia idéntica a la del gateway) |
| `models/README.md` | Cómo funciona el registro de modelos y cómo publicar una versión nueva |
| `models/model_v1.joblib` | **El modelo entrenado**: pipeline completo (limpieza + modelo + calibración), umbral y bandas |
| `models/model_v1.metadata.json` | Métricas y datos legibles del modelo (algoritmo, umbral, comparación de modelos, versión) |
| `tests/__init__.py` | Marca la carpeta de pruebas como paquete |
| `tests/test_inferencia.py` | 4 pruebas automáticas de la inferencia con un modelo simulado |

## `frontend/` — Página web (React + Vite, en Firebase Hosting)

| Archivo | Qué es |
|---|---|
| `index.html` | HTML base donde se monta la aplicación React |
| `package.json` | Dependencias y comandos (`dev`, `build`, `deploy`; `prebuild` copia el Swagger) |
| `package-lock.json` | Versiones exactas de todas las dependencias (para que `npm ci` instale siempre lo mismo) |
| `vite.config.js` | Configuración del empaquetador Vite |
| `firebase.json` | Configuración de Firebase Hosting: carpeta publicada, rutas y cabeceras de seguridad (CSP, HSTS…) |
| `.env.example` | Plantilla de `.env.local`: datos web de Firebase y URL de la API |
| `.firebaserc.example` | Plantilla de `.firebaserc`: id del proyecto de Firebase |
| `public/favicon.svg` | Ícono de la pestaña del navegador |
| `scripts/copiar_swagger.mjs` | Antes de cada build copia `docs/api` y Swagger UI a `public/swagger` |
| `src/main.jsx` | Punto de entrada: monta la app y captura errores globales para reportarlos |
| `src/App.jsx` | Rutas de la aplicación (login, nueva consulta, histórico, admin, páginas de error) |
| `src/firebase.js` | Inicializa Firebase (app y autenticación) con los datos de `.env.local` |
| `src/constants.js` | Opciones del formulario (sexo, tipo de trabajo, tabaquismo…) con sus etiquetas en español |
| `src/styles.css` | Estilos de toda la página |
| `src/context/AuthContext.jsx` | Estado de la sesión: login con correo o Google, registro, verificación y cierre de sesión |
| `src/services/api.js` | Llama a la API con el token y el `X-Request-ID`; exige `https://` |
| `src/services/errorReporter.js` | Envía los errores de JavaScript a `POST /api/errores` |
| `src/services/useManejarErrorApi.js` | Decide qué hacer ante un error de la API: ir a 401/500 o mostrar un mensaje |
| `src/components/Layout.jsx` | Estructura común: encabezado, pestañas y botón de salir |
| `src/components/ProtectedRoute.jsx` | Deja entrar sólo a usuarios con sesión (y a admins en `/admin`) |
| `src/components/ErrorBoundary.jsx` | Atrapa errores de React, los reporta y muestra «Algo salió mal» |
| `src/components/ResultadoCard.jsx` | Tarjeta con la probabilidad, el nivel de riesgo y su explicación |
| `src/pages/Login.jsx` | Pantalla de inicio de sesión y registro |
| `src/pages/NuevaConsulta.jsx` | Formulario de la consulta y resultado |
| `src/pages/Historico.jsx` | Lista paginada de las consultas del usuario |
| `src/pages/Admin.jsx` | Panel de errores para administradores |
| `src/pages/PaginasEstado.jsx` | Páginas 404, 401 y 500 |

## `database/` — Base de datos (MySQL de XAMPP, en el PC)

| Archivo | Qué es |
|---|---|
| `01_consultas_db.sql` | Crea la base `consultas_db` y la tabla de consultas y resultados |
| `02_errores_db.sql` | Crea la base `errores_db` y la tabla del registro de errores |
| `03_usuarios.sql` | Crea los 3 usuarios de la app con permisos mínimos (las contraseñas se cambian antes de ejecutarlo) |
| `README.md` | Cómo ejecutar los scripts y cómo llega la VM a la base por el túnel |

## `infra/` — Infraestructura de la VM

| Archivo | Qué es |
|---|---|
| `oracle/instalar_vm.sh` | Prepara la VM de Oracle: Docker, firewall 80/443, certificados internos, secretos, dominio, usuario `tunel` y arranque |
| `caddy/Caddyfile` | Configuración de Caddy: certificado de Let's Encrypt para el dominio y reenvío seguro al gateway |
| `certs/README.md` | Explica los certificados internos (se generan en la VM; nunca se suben) |

## `scripts/` — Utilidades

| Archivo | Qué es |
|---|---|
| `tunel_mysql.bat` | **Se usa a diario**: abre el túnel SSH del PC a la VM para que la app llegue a MySQL; se reconecta solo |
| `configurar_xampp_mysql.ps1` | Deja MySQL escuchando sólo en 127.0.0.1 y diagnostica si no arranca |
| `restablecer_root_xampp.ps1` | Restablece la contraseña de `root` de MySQL si se olvidó |
| `exportar_openapi.py` | Genera las especificaciones OpenAPI (Swagger) desde el código |

## `ml/` — Entrenamiento del modelo

| Archivo | Qué es |
|---|---|
| `stroke_prediction_colab.py` | **Fuente** del notebook: EDA, limpieza, comparación de modelos, calibración y exportación del `.joblib` |
| `stroke_prediction_colab.ipynb` | El notebook para abrir en Google Colab (se genera desde el `.py`) |
| `tools/py_to_ipynb.py` | Convierte el `.py` en `.ipynb` |

## `docs/` — Documentación

| Archivo | Qué es |
|---|---|
| `arquitectura.md` | Arquitectura completa: diagrama, componentes, flujos, seguridad, modelo de datos y decisiones |
| `manual_instalacion.md` | Instalación paso a paso desde cero (Colab, XAMPP, Firebase, Oracle, DuckDNS, túnel, frontend), costos y solución de problemas |
| `manual_usuario.md` | Cómo usar la app: cuenta, nueva consulta, histórico, mensajes de error |
| `modelo.md` | Detalle del modelo de machine learning |
| `archivos_repositorio.md` | Este documento |
| `diagramas/Arquitectura.drawio` | Diagrama de arquitectura para abrir en draw.io (se genera con el script de al lado) |
| `diagramas/generar_arquitectura_drawio.py` | Genera el diagrama `.drawio` |
| `api/README.md` | Qué es Swagger, cómo verlo y probarlo, y resumen de endpoints |
| `api/openapi-gateway.json` / `.yaml` | Especificación OpenAPI de la API pública (generada) |
| `api/openapi-inferencia.json` / `.yaml` | Especificación OpenAPI del microservicio interno (generada) |
| `api/index.html` | Página de Swagger UI (publicada en `/swagger`) |
| `api/swagger-init.js` | Inicializa Swagger UI con las dos especificaciones |
