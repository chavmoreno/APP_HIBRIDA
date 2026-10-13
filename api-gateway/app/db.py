"""Acceso a las bases de datos de XAMPP (MySQL/MariaDB) con SQLAlchemy Core y consultas parametrizadas."""

from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import get_settings
from .schemas import Consulta, DatosPaciente, ErrorRegistrado, Resultado

settings = get_settings()


def _crear_engine(url: str) -> Engine:
    """Engine con pool pequeño; pre_ping detecta conexiones cortadas por XAMPP."""
    if not url:
        raise RuntimeError("URL de base de datos no configurada")
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5, pool_recycle=1800)


@lru_cache
def engine_consultas() -> Engine:
    return _crear_engine(settings.consultas_db_url)


@lru_cache
def engine_errores_admin() -> Engine:
    return _crear_engine(settings.errores_admin_db_url)


# ---------------------------------------------------------------- consultas_db

COLUMNAS_DATOS = list(DatosPaciente.model_fields)  # gender, age, hypertension, ...


def guardar_consulta(uid: str, request_id: str, datos: DatosPaciente, resultado: Resultado) -> tuple[int, object]:
    """Inserta la consulta y devuelve (id, creado_en)."""
    valores = {**datos.model_dump(), **resultado.model_dump(), "firebase_uid": uid, "request_id": request_id}
    with engine_consultas().begin() as conn:
        res = conn.execute(
            text(
                "INSERT INTO consultas (request_id, firebase_uid, gender, age, hypertension, heart_disease, "
                "ever_married, work_type, residence_type, avg_glucose_level, bmi, smoking_status, probabilidad, "
                "clase_predicha, nivel_riesgo, umbral, modelo_version) VALUES (:request_id, :firebase_uid, :gender, "
                ":age, :hypertension, :heart_disease, :ever_married, :work_type, :residence_type, "
                ":avg_glucose_level, :bmi, :smoking_status, :probabilidad, :clase_predicha, :nivel_riesgo, :umbral, "
                ":modelo_version)"
            ),
            valores,
        )
        nuevo_id = res.lastrowid
        creado_en = conn.execute(text("SELECT creado_en FROM consultas WHERE id = :id"), {"id": nuevo_id}).scalar_one()
    return nuevo_id, creado_en


def _fila_a_consulta(fila) -> Consulta:
    """Convierte una fila de la tabla consultas en el esquema público."""
    m = fila._mapping
    return Consulta(
        id=m["id"],
        request_id=m["request_id"],
        creado_en=m["creado_en"],
        datos=DatosPaciente(
            **{c: m[c] for c in COLUMNAS_DATOS}
            | {"hypertension": bool(m["hypertension"]), "heart_disease": bool(m["heart_disease"]),
               "age": float(m["age"]),
               "avg_glucose_level": float(m["avg_glucose_level"]) if m["avg_glucose_level"] is not None else None,
               "bmi": float(m["bmi"]) if m["bmi"] is not None else None}
        ),
        resultado=Resultado(
            probabilidad=float(m["probabilidad"]),
            clase_predicha=m["clase_predicha"],
            nivel_riesgo=m["nivel_riesgo"],
            umbral=float(m["umbral"]),
            modelo_version=m["modelo_version"],
        ),
    )


def listar_consultas(uid: str, limit: int, offset: int) -> tuple[int, list[Consulta]]:
    """Histórico del usuario, más recientes primero. Siempre filtra por firebase_uid (aislamiento)."""
    with engine_consultas().connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM consultas WHERE firebase_uid = :uid"), {"uid": uid}).scalar_one()
        filas = conn.execute(
            text(
                "SELECT * FROM consultas WHERE firebase_uid = :uid ORDER BY creado_en DESC, id DESC "
                "LIMIT :limit OFFSET :offset"
            ),
            {"uid": uid, "limit": limit, "offset": offset},
        ).fetchall()
    return total, [_fila_a_consulta(f) for f in filas]


def obtener_consulta(uid: str, consulta_id: int) -> Consulta | None:
    """Una consulta concreta, sólo si pertenece al usuario."""
    with engine_consultas().connect() as conn:
        fila = conn.execute(
            text("SELECT * FROM consultas WHERE id = :id AND firebase_uid = :uid"), {"id": consulta_id, "uid": uid}
        ).first()
    return _fila_a_consulta(fila) if fila else None


# ---------------------------------------------------------------- errores_db (panel admin)


def listar_errores(severidad: str | None, origen: str | None, limit: int, offset: int) -> tuple[int, list[ErrorRegistrado]]:
    """Errores más recientes con filtros opcionales."""
    filtros, params = [], {"limit": limit, "offset": offset}
    if severidad:
        filtros.append("severidad = :severidad")
        params["severidad"] = severidad
    if origen:
        filtros.append("origen = :origen")
        params["origen"] = origen
    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""  # Sólo fragmentos fijos: sin inyección
    with engine_errores_admin().connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM errores {where}"), params).scalar_one()
        filas = conn.execute(
            text(
                "SELECT id, request_id, origen, severidad, codigo_http, tipo, mensaje, ruta, metodo, firebase_uid, "
                f"creado_en, notificado FROM errores {where} ORDER BY id DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        ).fetchall()
    return total, [ErrorRegistrado(**dict(f._mapping)) for f in filas]


def resumen_errores(horas: int) -> list[dict]:
    """Conteo por origen y severidad en las últimas N horas."""
    with engine_errores_admin().connect() as conn:
        filas = conn.execute(
            text(
                "SELECT origen, severidad, COUNT(*) AS total FROM errores "
                "WHERE creado_en >= NOW() - INTERVAL :horas HOUR GROUP BY origen, severidad ORDER BY total DESC"
            ),
            {"horas": horas},
        ).fetchall()
    return [dict(f._mapping) for f in filas]
