"""Esquemas (contratos) públicos del API Gateway."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class DatosPaciente(BaseModel):
    """Datos que el usuario captura en la pestaña 'Nueva consulta'."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "gender": "Female",
                "age": 54,
                "hypertension": True,
                "heart_disease": False,
                "ever_married": "Yes",
                "work_type": "Private",
                "residence_type": "Urban",
                "avg_glucose_level": 105.3,
                "bmi": 27.4,
                "smoking_status": "never smoked",
            }
        },
    )

    gender: Literal["Male", "Female"] = Field(description="Sexo")
    age: float = Field(ge=0, le=120, description="Edad en años")
    hypertension: bool = Field(description="¿Tiene hipertensión?")
    heart_disease: bool = Field(description="¿Tiene alguna enfermedad cardíaca?")
    ever_married: Literal["Yes", "No"] = Field(description="¿Ha estado casado/a alguna vez?")
    work_type: Literal["Private", "Self-employed", "Govt_job", "children", "Never_worked"]
    residence_type: Literal["Urban", "Rural"]
    avg_glucose_level: float | None = Field(default=None, ge=40, le=400, description="Opcional; se imputa con la mediana")
    bmi: float | None = Field(default=None, ge=10, le=100, description="Opcional; se imputa con la mediana")
    smoking_status: Literal["formerly smoked", "never smoked", "smokes", "Unknown"] | None = Field(
        default=None, description="Opcional; se imputa con la moda"
    )


class Resultado(BaseModel):
    """Resultado del modelo para una consulta."""

    probabilidad: float = Field(description="Probabilidad calibrada de stroke (0 a 1)")
    clase_predicha: int
    nivel_riesgo: Literal["bajo", "moderado", "alto"]
    umbral: float
    modelo_version: str


class Consulta(BaseModel):
    """Consulta guardada en consultas_db (entrada + resultado)."""

    id: int | None = Field(description="Id en consultas_db (null si no se pudo guardar)")
    request_id: str
    creado_en: datetime
    datos: DatosPaciente
    resultado: Resultado
    guardada: bool = Field(default=True, description="False si la predicción se hizo pero no se pudo guardar")


class PaginaConsultas(BaseModel):
    """Histórico paginado del usuario."""

    total: int
    limit: int
    offset: int
    items: list[Consulta]


class ErrorFrontend(BaseModel):
    """Error de JavaScript reportado por la SPA (ErrorBoundary, window.onerror, promesas rechazadas)."""

    model_config = ConfigDict(extra="forbid")

    mensaje: str = Field(max_length=2000)
    tipo: str | None = Field(default=None, max_length=120, description="Nombre del error (TypeError, ...)")
    stack: str | None = Field(default=None, max_length=8000)
    ruta: str | None = Field(default=None, max_length=255, description="Ruta de la SPA donde ocurrió")
    severidad: Literal["WARNING", "ERROR", "CRITICAL"] = "ERROR"
    contexto: dict[str, Any] | None = Field(default=None, description="Datos extra (componente, versión, etc.)")


class ErrorRegistrado(BaseModel):
    """Fila de errores_db expuesta en el panel admin."""

    id: int
    request_id: str | None
    origen: str
    severidad: str
    codigo_http: int | None
    tipo: str | None
    mensaje: str
    ruta: str | None
    metodo: str | None
    firebase_uid: str | None
    creado_en: datetime
    notificado: bool


class PaginaErrores(BaseModel):
    total: int
    items: list[ErrorRegistrado]


class RespuestaError(BaseModel):
    """Formato uniforme de todas las respuestas de error."""

    error: dict[str, Any] = Field(
        json_schema_extra={"example": {"codigo": 401, "mensaje": "Falta el token de autenticación", "request_id": "…"}}
    )
