# Model registry local

Coloca aquí los archivos exportados por el notebook de Colab (`ml/stroke_prediction_colab.ipynb`):

- `model_v1.joblib` — paquete con el pipeline (preprocesamiento + modelo + calibración), umbral y bandas de riesgo.
- `model_v1.metadata.json` — métricas y metadatos legibles.

Esta carpeta se **monta en el contenedor** de inferencia como `/app/models` (sólo lectura): los pesos
**no** se copian a la imagen Docker y viven sólo en tu máquina local. Los `.joblib` están en `.gitignore`.

Publicar una versión nueva:

1. Copia `model_v2.joblib` aquí.
2. Cambia `MODEL_PATH=models/model_v2.joblib` en `inference-service/.env`.
3. `docker compose up -d` (recrea el contenedor con la nueva variable).

Si sólo reemplazas `model_v1.joblib` por otro con el mismo nombre, basta `docker compose restart inferencia`.
