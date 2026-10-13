"""Carga del paquete del modelo (.joblib) y lógica de predicción."""

import logging

import joblib
import numpy as np
import pandas as pd
import sklearn

from .schemas import DatosPaciente, ResultadoPrediccion

log = logging.getLogger(__name__)


class ModeloStroke:
    """Envuelve el pipeline entrenado en Colab y traduce la entrada de la API al formato del dataset."""

    def __init__(self, ruta: str) -> None:
        self.paquete: dict = joblib.load(ruta)  # Diccionario exportado por el notebook
        self.pipeline = self.paquete["pipeline"]
        self.version: str = self.paquete["version"]
        self.umbral: float = float(self.paquete["umbral"])
        self.bandas: dict[str, list[float]] = self.paquete["bandas_riesgo"]
        # Un .joblib de otra versión de scikit-learn puede predecir mal o no cargar
        if self.paquete.get("sklearn_version") != sklearn.__version__:
            log.warning(
                "Versión de scikit-learn distinta: modelo=%s, local=%s",
                self.paquete.get("sklearn_version"),
                sklearn.__version__,
            )

    def _a_dataframe(self, datos: DatosPaciente) -> pd.DataFrame:
        """Convierte la entrada al mismo formato de columnas con el que se entrenó el pipeline."""
        fumador = datos.smoking_status
        if fumador == "Unknown" and self.paquete.get("tratar_unknown_como_nulo", False):
            fumador = None  # En entrenamiento "Unknown" se trató como nulo → se imputa con la moda
        fila = {
            "age": datos.age,
            "avg_glucose_level": datos.avg_glucose_level if datos.avg_glucose_level is not None else np.nan,
            "bmi": datos.bmi if datos.bmi is not None else np.nan,
            "gender": datos.gender,
            "hypertension": str(int(datos.hypertension)),  # En entrenamiento: "0"/"1" como texto
            "heart_disease": str(int(datos.heart_disease)),
            "ever_married": datos.ever_married,
            "work_type": datos.work_type,
            "Residence_type": datos.residence_type,  # El dataset usa R mayúscula
            "smoking_status": fumador if fumador is not None else np.nan,
        }
        columnas = self.paquete["columnas_numericas"] + self.paquete["columnas_categoricas"]
        return pd.DataFrame([fila])[columnas]

    def nivel_riesgo(self, probabilidad: float) -> str:
        """Clasifica la probabilidad en bajo / moderado / alto según las bandas del entrenamiento."""
        for nombre, (minimo, maximo) in self.bandas.items():
            if minimo <= probabilidad < maximo:
                return nombre
        return "alto"  # probabilidad == 1.0

    def predecir(self, datos: DatosPaciente) -> ResultadoPrediccion:
        """Calcula la probabilidad de stroke para un paciente."""
        probabilidad = float(self.pipeline.predict_proba(self._a_dataframe(datos))[0, 1])
        return ResultadoPrediccion(
            probabilidad=round(probabilidad, 5),
            clase_predicha=int(probabilidad >= self.umbral),
            nivel_riesgo=self.nivel_riesgo(probabilidad),
            umbral=round(self.umbral, 5),
            modelo_version=self.version,
        )
