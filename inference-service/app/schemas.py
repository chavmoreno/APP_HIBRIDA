"""Esquemas (contratos) de entrada y salida del microservicio de inferencia."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DatosPaciente(BaseModel):
    """Variables clínicas que usa el modelo. Los valores categóricos siguen el dataset de Kaggle."""

    model_config = ConfigDict(
        extra="forbid",  # Rechaza campos desconocidos
        json_schema_extra={
            "example": {
                "gender": "Male",
                "age": 67,
                "hypertension": False,
                "heart_disease": True,
                "ever_married": "Yes",
                "work_type": "Private",
                "residence_type": "Urban",
                "avg_glucose_level": 228.69,
                "bmi": 36.6,
                "smoking_status": "formerly smoked",
            }
        },
    )

    gender: Literal["Male", "Female"] = Field(description="Sexo")
    age: float = Field(ge=0, le=120, description="Edad en años")
    hypertension: bool = Field(description="¿Tiene hipertensión?")
    heart_disease: bool = Field(description="¿Tiene alguna enfermedad cardíaca?")
    ever_married: Literal["Yes", "No"] = Field(description="¿Ha estado casado/a alguna vez?")
    work_type: Literal["Private", "Self-employed", "Govt_job", "children", "Never_worked"] = Field(
        description="Tipo de trabajo"
    )
    residence_type: Literal["Urban", "Rural"] = Field(description="Tipo de residencia")
    # Opcionales: si llegan nulos, el pipeline los imputa (mediana / moda del entrenamiento)
    avg_glucose_level: float | None = Field(default=None, ge=40, le=400, description="Glucosa promedio (mg/dL)")
    bmi: float | None = Field(default=None, ge=10, le=100, description="Índice de masa corporal")
    smoking_status: Literal["formerly smoked", "never smoked", "smokes", "Unknown"] | None = Field(
        default=None, description="Tabaquismo"
    )


class ResultadoPrediccion(BaseModel):
    """Respuesta del modelo."""

    probabilidad: float = Field(description="Probabilidad calibrada de stroke (0 a 1)")
    clase_predicha: int = Field(description="1 si la probabilidad supera el umbral del modelo")
    nivel_riesgo: Literal["bajo", "moderado", "alto"]
    umbral: float = Field(description="Umbral de decisión elegido en el entrenamiento")
    modelo_version: str


class InfoModelo(BaseModel):
    """Metadatos públicos del modelo cargado."""

    version: str
    algoritmo: str
    umbral: float
    bandas_riesgo: dict[str, list[float]]
    metricas: dict[str, float]
    sklearn_version: str
    entrenado_en: str
