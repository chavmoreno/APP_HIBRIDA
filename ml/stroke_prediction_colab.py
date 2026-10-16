# %% [markdown]
# # Predicción de probabilidad de derrame cerebral (stroke)
#
# Notebook pensado para ejecutarse en **Google Colab**. Hace todo el ciclo:
#
# 1. Instala dependencias con versiones fijas (deben coincidir con las del microservicio local).
# 2. Carga el dataset **directamente desde Kaggle** con `kagglehub` (no hay que descargar nada a mano).
# 3. Análisis exploratorio de datos (EDA).
# 4. Preprocesamiento: imputación **moda** para categóricas, **mediana** para numéricas,
#    escalado y one-hot encoding, todo dentro de un `Pipeline` de scikit-learn.
# 5. Compara varios modelos con validación cruzada estratificada (el dataset está muy desbalanceado).
# 6. Calibra las probabilidades del mejor modelo (la app muestra una *probabilidad*, no solo una clase).
# 7. Evalúa en un conjunto de prueba y elige un umbral de decisión.
# 8. Exporta `model_v1.joblib` + `model_v1.metadata.json` para copiarlos al microservicio de inferencia.
#
# Dataset: https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset
#
# > **Aviso:** el modelo es educativo. No sustituye un diagnóstico médico.

# %% [markdown]
# ## 1. Instalación de dependencias
# Fijamos `scikit-learn==1.6.1` porque el archivo `.joblib` sólo es compatible con la misma
# versión con la que se entrenó. El microservicio local (`inference-service/requirements.txt`)
# usa exactamente esta versión.

# %%
# El "!" / "%pip" sólo funciona dentro de Jupyter/Colab; fuera de él se ignora.
try:
    get_ipython().run_line_magic(  # type: ignore[name-defined]
        "pip", "install -q scikit-learn==1.6.1 kagglehub[pandas-datasets] seaborn joblib"
    )
except NameError:
    print("No estamos en Jupyter/Colab: se asume que las dependencias ya están instaladas.")

# %% [markdown]
# ## 2. Importaciones y configuración global

# %%
import json  # Para guardar la metadata del modelo
import os  # Para leer variables de entorno (credenciales de Kaggle, rutas)
import warnings  # Para silenciar avisos ruidosos de librerías
from datetime import datetime, timezone  # Para fechar el entrenamiento

import joblib  # Serialización del pipeline entrenado
import matplotlib.pyplot as plt  # Gráficas base
import numpy as np  # Cálculo numérico
import pandas as pd  # Manipulación de datos tabulares
import seaborn as sns  # Gráficas estadísticas
import sklearn  # Para registrar la versión usada
from sklearn.calibration import CalibratedClassifierCV, calibration_curve  # Calibración de probabilidades
from sklearn.compose import ColumnTransformer  # Preprocesamiento por tipo de columna
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier  # Modelos de árboles
from sklearn.impute import SimpleImputer  # Imputación de nulos (moda / mediana)
from sklearn.linear_model import LogisticRegression  # Modelo lineal base
from sklearn.metrics import (  # Métricas de evaluación
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split  # Validación
from sklearn.pipeline import Pipeline  # Encadena preprocesamiento + modelo
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # Codificación y escalado

warnings.filterwarnings("ignore", category=FutureWarning)  # Menos ruido en la salida

# Semilla global para que los resultados sean reproducibles
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Versión del modelo que se exporta (el microservicio la reporta en cada predicción)
MODEL_VERSION = "v1"

# Identificador del dataset en Kaggle y nombre del CSV dentro del dataset
KAGGLE_DATASET = "fedesoriano/stroke-prediction-dataset"
KAGGLE_FILE = "healthcare-dataset-stroke-data.csv"

# En el dataset, smoking_status = "Unknown" significa "dato no disponible".
# Con True lo convertimos en nulo para que se impute con la MODA de la columna,
# tal como se pide para las categóricas nulas. Ponerlo en False lo deja como categoría propia.
TRATAR_UNKNOWN_COMO_NULO = True

# Columnas del modelo agrupadas por tipo (deben coincidir con el contrato de la API)
COLUMNAS_NUMERICAS = ["age", "avg_glucose_level", "bmi"]
COLUMNAS_CATEGORICAS = [
    "gender",
    "hypertension",  # 0/1, se trata como categórica (bandera clínica)
    "heart_disease",  # 0/1, se trata como categórica (bandera clínica)
    "ever_married",
    "work_type",
    "Residence_type",
    "smoking_status",
]
OBJETIVO = "stroke"

# Bandas de riesgo sobre la probabilidad calibrada (la prevalencia del dataset es ~5 %)
BANDAS_RIESGO = {"bajo": [0.0, 0.05], "moderado": [0.05, 0.15], "alto": [0.15, 1.0]}

# Estilo de gráficas
sns.set_theme(style="whitegrid")
print("scikit-learn:", sklearn.__version__, "| pandas:", pd.__version__)

# %% [markdown]
# ## 3. Carga del dataset directamente desde Kaggle
#
# `kagglehub.load_dataset` lee el CSV de Kaggle y lo entrega como `DataFrame`;
# no hace falta descargar el archivo manualmente ni subirlo a Colab.
#
# El dataset es público, así que normalmente no hace falta autenticarse. Si Kaggle la pide:
# 1. kaggle.com → tu foto → **Settings** → sección **API** → **Generate New Token** (o *Create New Token*).
#    Kaggle muestra el token **una sola vez**: cópialo.
# 2. En Colab abre el panel **🔑 Secrets**, crea un secreto llamado `KAGGLE_API_TOKEN`, pega el token
#    y activa *Acceso al notebook*.
#
# (Si tienes un `kaggle.json` antiguo, también sirven los secretos `KAGGLE_USERNAME` y `KAGGLE_KEY`.)
# La celda los lee automáticamente.

# %%
def configurar_credenciales_kaggle() -> None:
    """Copia las credenciales de Kaggle desde los Secrets de Colab a variables de entorno."""
    try:
        from google.colab import userdata  # Sólo existe dentro de Colab

        # KAGGLE_API_TOKEN: token nuevo de Kaggle. KAGGLE_USERNAME/KAGGLE_KEY: credenciales antiguas (kaggle.json)
        for clave in ("KAGGLE_API_TOKEN", "KAGGLE_USERNAME", "KAGGLE_KEY"):
            try:
                valor = userdata.get(clave)  # Lanza excepción si el secreto no existe
                if valor:
                    os.environ[clave] = valor  # kagglehub lee estas variables
            except Exception:
                pass  # El secreto es opcional: los datasets públicos suelen funcionar sin él
    except ImportError:
        pass  # Fuera de Colab no hay Secrets; se usan las variables de entorno existentes


def cargar_dataset() -> pd.DataFrame:
    """Devuelve el dataset de stroke como DataFrame leyendo directamente desde Kaggle."""
    # Atajo SOLO para pruebas locales/CI: si STROKE_CSV apunta a un CSV, se usa ese archivo.
    ruta_local = os.environ.get("STROKE_CSV")
    if ruta_local:
        print(f"Usando CSV local de pruebas: {ruta_local}")
        return pd.read_csv(ruta_local)

    configurar_credenciales_kaggle()
    import kagglehub  # Cliente oficial de Kaggle
    from kagglehub import KaggleDatasetAdapter  # Adaptador para obtener un DataFrame de pandas

    return kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,  # Queremos un pandas.DataFrame
        KAGGLE_DATASET,  # Dataset de Kaggle
        KAGGLE_FILE,  # Archivo dentro del dataset
    )


df_original = cargar_dataset()  # Datos crudos, tal cual vienen de Kaggle
print("Dimensiones:", df_original.shape)
df_original.head()

# %% [markdown]
# ## 4. Análisis exploratorio de datos (EDA)
# ### 4.1 Estructura, tipos y estadísticos

# %%
df_original.info()  # Tipos de dato y conteo de no-nulos por columna

# %%
df_original.describe(include="all").T  # Estadísticos descriptivos de todas las columnas

# %% [markdown]
# ### 4.2 Valores nulos y valores "ocultos"
# `bmi` trae `N/A` (pandas lo lee como NaN) y `smoking_status` usa `Unknown` como valor faltante.

# %%
nulos = pd.DataFrame(
    {
        "nulos": df_original.isna().sum(),  # Nulos reales por columna
        "porcentaje": (df_original.isna().mean() * 100).round(2),  # Porcentaje de nulos
    }
)
print(nulos[nulos["nulos"] > 0])
print("\nsmoking_status == 'Unknown':", (df_original["smoking_status"] == "Unknown").sum())
print("Filas duplicadas:", df_original.duplicated().sum())

# %% [markdown]
# ### 4.3 Distribución de la variable objetivo
# El dataset está **muy desbalanceado** (~5 % de casos positivos). Por eso usamos ROC-AUC y PR-AUC,
# validación estratificada y pesos de clase en lugar de accuracy.

# %%
conteo_objetivo = df_original[OBJETIVO].value_counts()  # Casos sin/con stroke
print(conteo_objetivo, "\nProporción positiva:", round(df_original[OBJETIVO].mean(), 4))
ax = sns.countplot(data=df_original, x=OBJETIVO)  # Barra por clase
ax.set_title("Distribución de la variable objetivo (stroke)")
plt.show()

# %% [markdown]
# ### 4.4 Variables numéricas vs. objetivo

# %%
fig, ejes = plt.subplots(2, 3, figsize=(16, 8))
for i, col in enumerate(COLUMNAS_NUMERICAS):
    # Fila superior: histograma por clase (densidad para comparar formas)
    sns.histplot(data=df_original, x=col, hue=OBJETIVO, stat="density", common_norm=False, kde=True, ax=ejes[0, i])
    ejes[0, i].set_title(f"Distribución de {col}")
    # Fila inferior: boxplot por clase para detectar outliers
    sns.boxplot(data=df_original, x=OBJETIVO, y=col, ax=ejes[1, i])
    ejes[1, i].set_title(f"{col} por clase")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 4.5 Variables categóricas: tasa de stroke por categoría

# %%
fig, ejes = plt.subplots(2, 4, figsize=(20, 9))
for eje, col in zip(ejes.flatten(), COLUMNAS_CATEGORICAS):
    tasa = df_original.groupby(col)[OBJETIVO].mean().sort_values(ascending=False)  # % positivo por categoría
    sns.barplot(x=tasa.index.astype(str), y=tasa.values, ax=eje)
    eje.set_title(f"Tasa de stroke por {col}")
    eje.set_ylabel("Proporción con stroke")
    eje.tick_params(axis="x", rotation=30)
ejes.flatten()[-1].axis("off")  # Hay 7 categóricas y 8 ejes: ocultamos el sobrante
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 4.6 Correlaciones entre numéricas (incluye banderas clínicas y objetivo)

# %%
columnas_corr = COLUMNAS_NUMERICAS + ["hypertension", "heart_disease", OBJETIVO]
plt.figure(figsize=(7, 5))
sns.heatmap(df_original[columnas_corr].corr(), annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1)
plt.title("Matriz de correlación")
plt.show()

# %% [markdown]
# **Hallazgos típicos del EDA:**
# - `age` es el predictor más fuerte; la tasa de stroke crece mucho a partir de ~50 años.
# - `avg_glucose_level`, `hypertension` y `heart_disease` muestran mayor tasa en positivos.
# - `bmi` tiene ~4 % de nulos → se imputan con la **mediana**.
# - `gender` tiene una única fila `Other` → se elimina (no hay datos suficientes para aprender de ella).
# - `id` es un identificador sin valor predictivo → se elimina.

# %% [markdown]
# ## 5. Limpieza y preprocesamiento

# %%
df = df_original.copy()  # Trabajamos sobre una copia para conservar los datos crudos

df = df.drop(columns=["id"])  # El id no aporta información predictiva
df = df[df["gender"] != "Other"]  # Una sola fila; evita una categoría sin soporte estadístico
df = df.drop_duplicates()  # Quita duplicados exactos si los hubiera

# bmi puede venir como texto "N/A" según la versión del CSV: lo forzamos a numérico (N/A → NaN)
df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")

if TRATAR_UNKNOWN_COMO_NULO:
    # "Unknown" significa dato faltante → lo pasamos a NaN para imputarlo con la moda
    df["smoking_status"] = df["smoking_status"].replace("Unknown", np.nan)

# Las banderas 0/1 se tratan como categóricas: las convertimos a texto para el OneHotEncoder
for col in ["hypertension", "heart_disease"]:
    df[col] = df[col].astype("Int64").astype(str).replace("<NA>", np.nan)

print("Nulos que se imputarán:\n", df.isna().sum()[df.isna().sum() > 0])

X = df[COLUMNAS_NUMERICAS + COLUMNAS_CATEGORICAS]  # Variables de entrada
y = df[OBJETIVO].astype(int)  # Variable objetivo

# Partición 80/20 estratificada: conserva la proporción de positivos en ambos conjuntos
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
)
print("Entrenamiento:", X_train.shape, "| Prueba:", X_test.shape)

# %% [markdown]
# ### 5.1 Transformador de columnas
# - **Numéricas**: `SimpleImputer(strategy="median")` → `StandardScaler`.
# - **Categóricas**: `SimpleImputer(strategy="most_frequent")` (moda) → `OneHotEncoder`.
#
# Los imputadores se ajustan **solo con datos de entrenamiento** (dentro del pipeline), así
# la mediana y la moda no "ven" el conjunto de prueba (evita fuga de datos). Además quedan
# guardados dentro del `.joblib`, por lo que si en producción llega un campo nulo, el
# microservicio lo imputa con la misma mediana/moda del entrenamiento.

# %%
def crear_preprocesador() -> ColumnTransformer:
    """Construye el preprocesador: mediana+escalado para numéricas, moda+one-hot para categóricas."""
    numericas = Pipeline(
        steps=[
            ("imputador_mediana", SimpleImputer(strategy="median")),  # Nulos numéricos → mediana
            ("escalado", StandardScaler()),  # Media 0, desviación 1
        ]
    )
    categoricas = Pipeline(
        steps=[
            ("imputador_moda", SimpleImputer(strategy="most_frequent")),  # Nulos categóricos → moda
            ("one_hot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),  # Categorías → columnas 0/1
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numericas, COLUMNAS_NUMERICAS),
            ("cat", categoricas, COLUMNAS_CATEGORICAS),
        ]
    )


# Verificación rápida de la imputación: valores aprendidos en entrenamiento
prep_demo = crear_preprocesador().fit(X_train)
print("Medianas numéricas:", dict(zip(COLUMNAS_NUMERICAS, prep_demo.named_transformers_["num"]["imputador_mediana"].statistics_)))
print("Modas categóricas:", dict(zip(COLUMNAS_CATEGORICAS, prep_demo.named_transformers_["cat"]["imputador_moda"].statistics_)))

# %% [markdown]
# ## 6. Comparación de modelos con validación cruzada estratificada
# Se usan pesos de clase balanceados para compensar el desbalance.
# Métrica principal: **ROC-AUC**; también se reporta **PR-AUC** (average precision).

# %%
candidatos = {
    "regresion_logistica": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE),
    "random_forest": RandomForestClassifier(
        n_estimators=400, min_samples_leaf=5, class_weight="balanced_subsample", n_jobs=-1, random_state=RANDOM_STATE
    ),
    "hist_gradient_boosting": HistGradientBoostingClassifier(
        learning_rate=0.05, max_depth=4, class_weight="balanced", random_state=RANDOM_STATE
    ),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)  # 5 folds estratificados
resultados_cv = []
for nombre, modelo in candidatos.items():
    pipeline = Pipeline(steps=[("preprocesamiento", crear_preprocesador()), ("modelo", modelo)])
    puntajes = cross_validate(pipeline, X_train, y_train, cv=cv, scoring=["roc_auc", "average_precision"], n_jobs=-1)
    resultados_cv.append(
        {
            "modelo": nombre,
            "roc_auc_media": puntajes["test_roc_auc"].mean(),
            "roc_auc_std": puntajes["test_roc_auc"].std(),
            "pr_auc_media": puntajes["test_average_precision"].mean(),
        }
    )

tabla_cv = pd.DataFrame(resultados_cv).sort_values("roc_auc_media", ascending=False).reset_index(drop=True)
print(tabla_cv)
mejor_nombre = tabla_cv.loc[0, "modelo"]  # Modelo con mayor ROC-AUC promedio
print("\nModelo seleccionado:", mejor_nombre)

# %% [markdown]
# ## 7. Entrenamiento final + calibración de probabilidades
# Los pesos de clase "inflan" las probabilidades. `CalibratedClassifierCV` (sigmoide, 5 folds)
# las reajusta para que un 0.20 signifique realmente ~20 % de riesgo observado.

# %%
pipeline_final = CalibratedClassifierCV(
    estimator=Pipeline(steps=[("preprocesamiento", crear_preprocesador()), ("modelo", candidatos[mejor_nombre])]),
    method="sigmoid",  # Platt scaling: robusto con pocos positivos
    cv=cv,
)
pipeline_final.fit(X_train, y_train)  # Ajusta preprocesamiento + modelo + calibrador
proba_test = pipeline_final.predict_proba(X_test)[:, 1]  # Probabilidad de stroke en prueba

# %% [markdown]
# ## 8. Evaluación en el conjunto de prueba

# %%
# Umbral de decisión que maximiza F1 (equilibrio precisión/sensibilidad para la clase positiva)
precisiones, sensibilidades, umbrales = precision_recall_curve(y_test, proba_test)
f1s = 2 * precisiones[:-1] * sensibilidades[:-1] / np.clip(precisiones[:-1] + sensibilidades[:-1], 1e-12, None)
umbral_optimo = float(umbrales[np.argmax(f1s)])
pred_test = (proba_test >= umbral_optimo).astype(int)  # Clase predicha con el umbral elegido

metricas = {
    "roc_auc": float(roc_auc_score(y_test, proba_test)),
    "pr_auc": float(average_precision_score(y_test, proba_test)),
    "brier": float(brier_score_loss(y_test, proba_test)),  # Error cuadrático de las probabilidades
    "f1_umbral": float(f1_score(y_test, pred_test)),
    "umbral": umbral_optimo,
    "prevalencia_test": float(y_test.mean()),
}
print(json.dumps(metricas, indent=2))
print(classification_report(y_test, pred_test, target_names=["sin stroke", "stroke"]))

# %%
fig, ejes = plt.subplots(1, 3, figsize=(18, 5))
# Curva ROC
fpr, tpr, _ = roc_curve(y_test, proba_test)
ejes[0].plot(fpr, tpr, label=f"AUC = {metricas['roc_auc']:.3f}")
ejes[0].plot([0, 1], [0, 1], "--", color="grey")
ejes[0].set(title="Curva ROC", xlabel="Falsos positivos", ylabel="Verdaderos positivos")
ejes[0].legend()
# Curva de calibración: probabilidad predicha vs. frecuencia observada
frac_pos, media_pred = calibration_curve(y_test, proba_test, n_bins=10, strategy="quantile")
ejes[1].plot(media_pred, frac_pos, marker="o", label="Modelo")
ejes[1].plot([0, 1], [0, 1], "--", color="grey", label="Calibración perfecta")
ejes[1].set(title="Curva de calibración", xlabel="Probabilidad predicha", ylabel="Frecuencia observada")
ejes[1].legend()
# Matriz de confusión
sns.heatmap(confusion_matrix(y_test, pred_test), annot=True, fmt="d", cmap="Blues", ax=ejes[2])
ejes[2].set(title=f"Matriz de confusión (umbral={umbral_optimo:.3f})", xlabel="Predicho", ylabel="Real")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 9. Prueba de humo: predicción con un registro que trae nulos
# Confirma que el pipeline imputa sólo (mediana / moda) cuando llega un dato faltante.

# %%
ejemplo = pd.DataFrame(
    [
        {
            "age": 67, "avg_glucose_level": 228.69, "bmi": np.nan,  # bmi nulo → mediana
            "gender": "Male", "hypertension": "0", "heart_disease": "1", "ever_married": "Yes",
            "work_type": "Private", "Residence_type": "Urban", "smoking_status": np.nan,  # nulo → moda
        }
    ]
)
print("Probabilidad de stroke del ejemplo:", round(float(pipeline_final.predict_proba(ejemplo)[0, 1]), 4))

# %% [markdown]
# ## 10. Exportación del modelo
# Se guarda un **paquete** (diccionario) con el pipeline y todo lo que el microservicio necesita.
# Copia `model_v1.joblib` a `inference-service/models/` en tu máquina local.

# %%
paquete = {
    "pipeline": pipeline_final,  # Preprocesamiento + modelo + calibración
    "version": MODEL_VERSION,
    "algoritmo": mejor_nombre,
    "umbral": umbral_optimo,
    "bandas_riesgo": BANDAS_RIESGO,
    "columnas_numericas": COLUMNAS_NUMERICAS,
    "columnas_categoricas": COLUMNAS_CATEGORICAS,
    "tratar_unknown_como_nulo": TRATAR_UNKNOWN_COMO_NULO,
    "metricas": metricas,
    "sklearn_version": sklearn.__version__,
    "entrenado_en": datetime.now(timezone.utc).isoformat(),
}
archivo_modelo = f"model_{MODEL_VERSION}.joblib"
joblib.dump(paquete, archivo_modelo, compress=3)  # Comprimido para que pese menos

# Metadata legible (sin el objeto pipeline) para documentación y auditoría
metadata = {k: v for k, v in paquete.items() if k != "pipeline"}
metadata["comparacion_cv"] = tabla_cv.to_dict(orient="records")
with open(f"model_{MODEL_VERSION}.metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print("Guardado:", archivo_modelo, f"({os.path.getsize(archivo_modelo) / 1024:.1f} KB)")

# %%
# Descarga los archivos a tu computadora (sólo en Colab)
try:
    from google.colab import files

    files.download(archivo_modelo)
    files.download(f"model_{MODEL_VERSION}.metadata.json")
except ImportError:
    print("Fuera de Colab: los archivos quedaron en el directorio actual.")
