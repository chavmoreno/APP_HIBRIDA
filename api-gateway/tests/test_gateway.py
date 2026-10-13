"""Pruebas del API Gateway sin Firebase, MySQL ni microservicio reales (todo se simula)."""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import auth, db, inferencia
from app.main import app
from app.schemas import Resultado

PACIENTE = {
    "gender": "Female", "age": 54, "hypertension": True, "heart_disease": False, "ever_married": "Yes",
    "work_type": "Private", "residence_type": "Urban", "avg_glucose_level": 105.3, "bmi": None,
    "smoking_status": None,
}
RESULTADO = Resultado(probabilidad=0.12, clase_predicha=0, nivel_riesgo="moderado", umbral=0.25, modelo_version="v1")


@pytest.fixture()
def cliente(monkeypatch):
    """Simula Firebase (token 'ok' = usuario válido), la inferencia y la base de datos."""

    def verificar(token):
        if token == "ok":
            return {"uid": "u1", "email": "a@b.com", "email_verified": True, "firebase": {"sign_in_provider": "google.com"}}
        if token == "sin-verificar":
            return {"uid": "u2", "email": "c@d.com", "email_verified": False, "firebase": {"sign_in_provider": "password"}}
        raise ValueError("token inválido")

    guardadas = []
    monkeypatch.setattr(auth, "verificar_token", verificar)
    monkeypatch.setattr(inferencia, "predecir", lambda datos: RESULTADO)
    monkeypatch.setattr(db, "guardar_consulta", lambda *a: (guardadas.append(a) or (1, datetime(2026, 1, 1))))
    monkeypatch.setattr(db, "listar_consultas", lambda uid, l, o: (0, []))
    monkeypatch.setattr(db, "obtener_consulta", lambda uid, cid: None)
    with TestClient(app, base_url="https://localhost") as c:
        c.guardadas = guardadas
        yield c


def test_health_y_cabeceras(cliente):
    r = cliente.get("/api/health")
    assert r.status_code == 200
    assert "max-age" in r.headers["Strict-Transport-Security"]
    assert r.headers["X-Request-ID"]


def test_request_id_se_propaga(cliente):
    r = cliente.get("/api/health", headers={"X-Request-ID": "abc12345-frontend"})
    assert r.headers["X-Request-ID"] == "abc12345-frontend"


def test_sin_token_401(cliente):
    r = cliente.post("/api/consultas", json=PACIENTE)
    assert r.status_code == 401
    assert r.json()["error"]["request_id"]


def test_correo_sin_verificar_403(cliente):
    r = cliente.post("/api/consultas", json=PACIENTE, headers={"Authorization": "Bearer sin-verificar"})
    assert r.status_code == 403


def test_crear_consulta(cliente):
    r = cliente.post("/api/consultas", json=PACIENTE, headers={"Authorization": "Bearer ok"})
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["resultado"]["nivel_riesgo"] == "moderado"
    assert cuerpo["guardada"] is True
    assert cliente.guardadas[0][0] == "u1"  # Se guarda con el uid del token, no con datos del cliente


def test_validacion_no_expone_valores(cliente):
    r = cliente.post("/api/consultas", json={**PACIENTE, "age": 999}, headers={"Authorization": "Bearer ok"})
    assert r.status_code == 422
    assert "999" not in r.text


def test_inferencia_caida_503(cliente, monkeypatch):
    def caida(_):
        raise inferencia.InferenciaNoDisponible("connection refused")

    monkeypatch.setattr(inferencia, "predecir", caida)
    r = cliente.post("/api/consultas", json=PACIENTE, headers={"Authorization": "Bearer ok"})
    assert r.status_code == 503


def test_consulta_ajena_404(cliente):
    assert cliente.get("/api/consultas/99", headers={"Authorization": "Bearer ok"}).status_code == 404


def test_reportar_error_frontend_sin_login(cliente):
    r = cliente.post("/api/errores", json={"mensaje": "x is undefined", "tipo": "TypeError", "ruta": "/historico"})
    assert r.status_code == 204


def test_admin_requiere_rol(cliente):
    assert cliente.get("/api/admin/errores", headers={"Authorization": "Bearer ok"}).status_code == 403


def test_host_no_permitido(cliente):
    assert cliente.get("/api/health", headers={"Host": "evil.com"}).status_code == 400
