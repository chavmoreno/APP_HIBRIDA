# Modelo de predicción de stroke

Notebook: [`ml/stroke_prediction_colab.ipynb`](../ml/stroke_prediction_colab.ipynb)
(fuente editable: [`ml/stroke_prediction_colab.py`](../ml/stroke_prediction_colab.py)).

## Dataset

[Stroke Prediction Dataset](https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset) (fedesoriano, Kaggle):
5 110 pacientes, 11 variables + objetivo `stroke` (~4,9 % positivos).

Se carga **directamente desde Kaggle** con `kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS, ...)`,
sin descargar ni subir archivos. Para pruebas locales, la variable `STROKE_CSV` permite usar un CSV.

| Variable | Tipo en el modelo | Notas |
|---|---|---|
| `id` | — | Eliminada (identificador) |
| `gender` | Categórica | Se elimina la única fila `Other` |
| `age` | Numérica | |
| `hypertension`, `heart_disease` | Categóricas (`"0"`/`"1"`) | Banderas clínicas |
| `ever_married`, `work_type`, `Residence_type` | Categóricas | |
| `avg_glucose_level` | Numérica | |
| `bmi` | Numérica | ~4 % `N/A` → mediana |
| `smoking_status` | Categórica | `Unknown` (~30 %) se trata como nulo → moda (configurable con `TRATAR_UNKNOWN_COMO_NULO`) |

## EDA incluido

Estructura y tipos, estadísticos descriptivos, nulos y valores "ocultos" (`N/A`, `Unknown`), duplicados,
distribución del objetivo (desbalance), histogramas y boxplots de numéricas por clase, tasa de stroke por
categoría y matriz de correlación.

## Preprocesamiento (dentro del `Pipeline`)

| Tipo | Paso 1 | Paso 2 |
|---|---|---|
| Numéricas (`age`, `avg_glucose_level`, `bmi`) | `SimpleImputer(strategy="median")` | `StandardScaler` |
| Categóricas (7 columnas) | `SimpleImputer(strategy="most_frequent")` (moda) | `OneHotEncoder(handle_unknown="ignore")` |

Los imputadores se ajustan **sólo con el conjunto de entrenamiento** (sin fuga de datos) y se guardan en el
`.joblib`: si en producción llega un campo vacío, se imputa con la misma mediana/moda.

## Entrenamiento

1. Partición 80/20 estratificada (`random_state=42`).
2. Comparación con validación cruzada estratificada de 5 folds (ROC-AUC y PR-AUC):
   regresión logística, random forest y histogram gradient boosting, todos con pesos de clase balanceados.
3. El mejor por ROC-AUC se envuelve en `CalibratedClassifierCV(method="sigmoid", cv=5)` para obtener
   probabilidades calibradas (los pesos de clase las inflan).
4. Umbral de decisión: el que maximiza F1 en prueba (se usa para `clase_predicha`).
5. Métricas reportadas: ROC-AUC, PR-AUC, Brier, F1, matriz de confusión, curva ROC y de calibración.

Referencia de rendimiento esperado con este dataset: ROC-AUC ≈ 0,83–0,85. La PR-AUC es baja (pocos positivos):
el modelo sirve para **ordenar riesgo**, no para diagnosticar.

## Artefacto exportado (`model_v1.joblib`)

Diccionario con:

| Clave | Contenido |
|---|---|
| `pipeline` | `CalibratedClassifierCV` con preprocesamiento + modelo |
| `version` | `"v1"` |
| `algoritmo` | Nombre del modelo ganador |
| `umbral` | Umbral F1-óptimo |
| `bandas_riesgo` | `{"bajo": [0, 0.05], "moderado": [0.05, 0.15], "alto": [0.15, 1]}` |
| `columnas_numericas`, `columnas_categoricas` | Orden de columnas esperado |
| `tratar_unknown_como_nulo` | Para replicar la limpieza en inferencia |
| `metricas`, `sklearn_version`, `entrenado_en` | Auditoría |

`model_v1.metadata.json` contiene lo mismo sin el pipeline, más la tabla de validación cruzada.

## Interpretación en la app

- **Probabilidad**: salida calibrada del modelo.
- **Nivel de riesgo**: bandas relativas a la prevalencia (~5 %). Un "alto" significa ≥ 3 veces la prevalencia.
- **Clase predicha**: `probabilidad ≥ umbral`. Se guarda para análisis, pero la interfaz muestra probabilidad y nivel,
  que son más informativos.

## Limitaciones

- Dataset pequeño, de origen no documentado y con pocos casos positivos (249).
- No incluye variables clínicas clave (colesterol, fibrilación auricular, antecedentes familiares…).
- No validado clínicamente: uso educativo/orientativo.
