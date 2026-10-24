"""Tests de los endpoints con el servicio de Gemini mockeado."""

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services.gemini_service import GeminiServiceError
from tests.conftest import VALID_RESULT, FakeAuditService


def test_health(client: TestClient) -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert resp.json()["model"]


# ---------- Casos de éxito ----------

def test_audit_with_png_file(client: TestClient, fake_service: FakeAuditService, png_bytes: bytes) -> None:
    resp = client.post("/api/audit", files={"file": ("factura.png", png_bytes, "image/png")})
    assert resp.status_code == 200
    assert resp.json() == VALID_RESULT
    assert fake_service.calls == [(len(png_bytes), "image/png")]


def test_audit_detects_mime_from_bytes_not_header(
    client: TestClient, fake_service: FakeAuditService, jpeg_bytes: bytes
) -> None:
    resp = client.post("/api/audit", files={"file": ("foto.bin", jpeg_bytes, "application/octet-stream")})
    assert resp.status_code == 200
    assert fake_service.calls[0][1] == "image/jpeg"


def test_audit_with_base64(client: TestClient, png_bytes: bytes) -> None:
    b64 = base64.b64encode(png_bytes).decode()
    resp = client.post("/api/audit", data={"image_base64": b64})
    assert resp.status_code == 200
    assert resp.json()["risk_level"] == "ALTO"


def test_audit_with_data_url(client: TestClient, png_bytes: bytes) -> None:
    b64 = "data:image/png;base64," + base64.b64encode(png_bytes).decode()
    resp = client.post("/api/audit", data={"image_base64": b64})
    assert resp.status_code == 200


# ---------- Errores 400 / 413 ----------

def test_audit_without_image_returns_400(client: TestClient, fake_service: FakeAuditService) -> None:
    resp = client.post("/api/audit", data={})
    assert resp.status_code == 400
    assert "imagen" in resp.json()["detail"].lower()
    assert fake_service.calls == []


def test_audit_empty_file_returns_400(client: TestClient) -> None:
    resp = client.post("/api/audit", files={"file": ("vacia.png", b"", "image/png")})
    assert resp.status_code == 400


def test_audit_non_image_file_returns_400(client: TestClient, fake_service: FakeAuditService) -> None:
    resp = client.post("/api/audit", files={"file": ("notas.txt", b"hola mundo", "text/plain")})
    assert resp.status_code == 400
    assert "formato" in resp.json()["detail"].lower()
    assert fake_service.calls == []


def test_audit_fake_png_extension_returns_400(client: TestClient) -> None:
    resp = client.post("/api/audit", files={"file": ("factura.png", b"%PDF-1.7 not an image", "image/png")})
    assert resp.status_code == 400


def test_audit_invalid_base64_returns_400(client: TestClient) -> None:
    resp = client.post("/api/audit", data={"image_base64": "esto-no-es-base64!!!"})
    assert resp.status_code == 400
    assert "base64" in resp.json()["detail"].lower()


def test_audit_base64_of_non_image_returns_400(client: TestClient) -> None:
    resp = client.post("/api/audit", data={"image_base64": base64.b64encode(b"texto plano").decode()})
    assert resp.status_code == 400


def test_audit_too_large_returns_413(client: TestClient, png_bytes: bytes, monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "max_upload_mb", 0)  # límite 0 bytes
    resp = client.post("/api/audit", files={"file": ("factura.png", png_bytes, "image/png")})
    assert resp.status_code == 413


# ---------- Errores 500 ----------

def test_audit_gemini_error_returns_500(client: TestClient, fake_service: FakeAuditService, png_bytes: bytes) -> None:
    fake_service.exc = GeminiServiceError("Error de la API de Gemini (503).")
    resp = client.post("/api/audit", files={"file": ("factura.png", png_bytes, "image/png")})
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Error de la API de Gemini (503)."}


def test_audit_unexpected_error_returns_generic_500(
    client: TestClient, fake_service: FakeAuditService, png_bytes: bytes
) -> None:
    fake_service.exc = RuntimeError("secreto interno")
    resp = client.post("/api/audit", files={"file": ("factura.png", png_bytes, "image/png")})
    assert resp.status_code == 500
    assert "secreto" not in resp.json()["detail"]


def test_audit_service_build_failure_returns_500(png_bytes: bytes) -> None:
    """Si el servicio no se puede construir (p. ej. sin API key) se devuelve 500 JSON, no un crash."""
    from app.api.deps import get_audit_service
    from app.main import app

    def broken() -> None:
        raise GeminiServiceError("GEMINI_API_KEY no está configurada.")

    app.dependency_overrides[get_audit_service] = broken
    try:
        with TestClient(app) as c:
            resp = c.post("/api/audit", files={"file": ("factura.png", png_bytes, "image/png")})
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 500
    assert resp.json()["detail"] == "GEMINI_API_KEY no está configurada."


def test_cors_preflight_allows_frontend(client: TestClient) -> None:
    resp = client.options(
        "/api/audit",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:3000"
