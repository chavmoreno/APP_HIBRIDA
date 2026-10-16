# Model registry

Archivos exportados por el notebook de Colab (`ml/stroke_prediction_colab.ipynb`). En producción viven en esta
carpeta **dentro de la VM de Oracle Cloud**:

- `model_v1.joblib` — paquete con el pipeline (preprocesamiento + modelo + calibración), umbral y bandas de riesgo.
- `model_v1.metadata.json` — métricas y metadatos legibles.

Esta carpeta se **monta en el contenedor** de inferencia como `/app/models` (sólo lectura): los pesos
**no** se copian a la imagen Docker. Los `.joblib` están en `.gitignore`.

Publicar una versión nueva:

1. Sube `model_v2.joblib` a la VM desde el PC: `scp -i $env:USERPROFILE\.ssh\stroke_admin model_v2.joblib ubuntu@IP-DE-LA-VM:`
2. `sudo bash infra/oracle/instalar_vm.sh` (mueve el archivo a esta carpeta).
3. Cambia `MODEL_PATH=models/model_v2.joblib` en `inference-service/.env`.
4. `docker compose up -d` (recrea el contenedor con la nueva variable).

Si sólo reemplazas `model_v1.joblib` por otro con el mismo nombre, basta `docker compose restart inferencia`.
