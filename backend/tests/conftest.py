"""Fixtures compartidas: app con servicio de Gemini falso e imágenes de prueba."""

from __future__ import annotations

import io
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.deps import get_audit_service
from app.main import app
from app.schemas.audit import AuditResult

VALID_RESULT = {
    "merchant": "La Parrilla del Centro",
    "total_billed": "$225.66",
    "real_subtotal": "$158.00",
    "risk_level": "ALTO",
    "summary": "La cuenta incluye un ítem duplicado y un cargo por servicio no informado. Se cobraron $67.66 de más.",
    "suspicious_charges": [
        {"item": "Pisco sour (duplicado)", "amount": "$22.00", "reason": "Ítem cobrado dos veces."},
        {"item": "Cargo por servicio 18%", "amount": "$33.66", "reason": "Propina incluida sin aviso."},
    ],
    "dispute_message": "Buenas noches, solicito amablemente la corrección de la cuenta.",
}


class FakeAuditService:
    """Sustituto del GeminiAuditService: devuelve un resultado fijo o lanza la excepción indicada."""

    def __init__(self, result: dict | None = None, exc: Exception | None = None) -> None:
        self.result = result or VALID_RESULT
        self.exc = exc
        self.calls: list[tuple[int, str]] = []

    async def audit(self, image_bytes: bytes, mime_type: str) -> AuditResult:
        self.calls.append((len(image_bytes), mime_type))
        if self.exc:
            raise self.exc
        return AuditResult.model_validate(self.result)


def _image_bytes(fmt: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, format=fmt)
    return buf.getvalue()


@pytest.fixture
def png_bytes() -> bytes:
    return _image_bytes("PNG")


@pytest.fixture
def jpeg_bytes() -> bytes:
    return _image_bytes("JPEG")


@pytest.fixture
def fake_service() -> FakeAuditService:
    return FakeAuditService()


@pytest.fixture
def client(fake_service: FakeAuditService) -> Iterator[TestClient]:
    app.dependency_overrides[get_audit_service] = lambda: fake_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
