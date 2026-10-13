# Model registry local

Coloca aquí los archivos exportados por el notebook de Colab (`ml/stroke_prediction_colab.ipynb`):

- `model_v1.joblib` — paquete con el pipeline (preprocesamiento + modelo + calibración), umbral y bandas de riesgo.
- `model_v1.metadata.json` — métricas y metadatos legibles.

Los `.joblib` están en `.gitignore`: los pesos del modelo viven **sólo en tu máquina local**.
Para publicar una versión nueva, entrena `model_v2.joblib` y cambia `MODEL_PATH` en `.env`.
