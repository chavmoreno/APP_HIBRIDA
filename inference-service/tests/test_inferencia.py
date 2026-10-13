"""Pruebas del microservicio de inferencia con un modelo mínimo entrenado al vuelo."""

import importlib

import joblib
import numpy as np
import pandas as pd
import pytest
import sklearn
from fastapi.testclient import TestClient
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

NUM = ["age", "avg_glucose_level", "bmi"]
CAT = ["gender", "hypertension", "heart_disease", "ever_married", "work_type", "Residence_type", "smoking_status"]
LLAVE = "llave-de-prueba"
PACIENTE = {
    "gender": "Male", "age": 67, "hypertension": False, "heart_disease": True, "ever_married": "Yes",
    "work_type": "Private", "residence_type": "Urban", "avg_glucose_level": 228.69, "bmi": None,
    "smoking_status": "Unknown",
}


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    """Entrena un pipeline pequeño con el mismo formato que el de Colab y levanta la app."""
    rng = np.random.default_rng(0)
    n = 200
    X = pd.DataFrame({
        "age": rng.uniform(1, 80, n), "avg_glucose_level": rng.uniform(60, 250, n), "bmi": rng.uniform(15, 45, n),
        "gender": rng.choice(["Male", "Female"], n), "hypertension": rng.choice(["0", "1"], n),
        "heart_disease": rng.choice(["0", "1"], n), "ever_married": rng.choice(["Yes", "No"], n),
        "work_type": rng.choice(["Private", "Govt_job"], n), "Residence_type": rng.choice(["Urban", "Rural"], n),
        "smoking_status": rng.choice(["smokes", "never smoked"], n),
    })
    y = (X["age"] > 60).astype(int)
    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUM),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore"))]), CAT),
    ])
    pipe = Pipeline([("p", prep), ("m", LogisticRegression(max_iter=1000))]).fit(X, y)
    ruta = tmp_path / "model_test.joblib"
    joblib.dump({
        "pipeline": pipe, "version": "test", "algoritmo": "lr", "umbral": 0.5,
        "bandas_riesgo": {"bajo": [0.0, 0.05], "moderado": [0.05, 0.15], "alto": [0.15, 1.0]},
        "columnas_numericas": NUM, "columnas_categoricas": CAT, "tratar_unknown_como_nulo": True,
        "metricas": {"roc_auc": 1.0}, "sklearn_version": sklearn.__version__, "entrenado_en": "2026-01-01",
    }, ruta)
    monkeypatch.setenv("MODEL_PATH", str(ruta))
    monkeypatch.setenv("INTERNAL_API_KEY", LLAVE)
    monkeypatch.setenv("ERRORES_DB_URL", "")  # Sin MySQL: los errores van al archivo de respaldo
    monkeypatch.setenv("LOG_FALLBACK_PATH", str(tmp_path / "errores.log"))
    from app import config, main
    config.get_settings.cache_clear()
    importlib.reload(main)  # Recarga con la nueva configuración
    with TestClient(main.app) as c:
        yield c


def test_health(cliente):
    assert cliente.get("/health").json() == {"estado": "ok", "modelo_cargado": True}


def test_predict_requiere_llave(cliente):
    assert cliente.post("/predict", json=PACIENTE).status_code == 401
    assert cliente.post("/predict", json=PACIENTE, headers={"X-Internal-API-Key": "mala"}).status_code == 401


def test_predict_con_nulos_imputa(cliente):
    r = cliente.post("/predict", json=PACIENTE, headers={"X-Internal-API-Key": LLAVE})
    assert r.status_code == 200
    cuerpo = r.json()
    assert 0 <= cuerpo["probabilidad"] <= 1
    assert cuerpo["nivel_riesgo"] in {"bajo", "moderado", "alto"}
    assert cuerpo["modelo_version"] == "test"


def test_predict_valida_rangos(cliente):
    malo = {**PACIENTE, "age": 500}
    assert cliente.post("/predict", json=malo, headers={"X-Internal-API-Key": LLAVE}).status_code == 422
