"""Tests unitarios del GeminiAuditService con el cliente de Gemini mockeado."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from google.genai import errors as genai_errors

from app.schemas.audit import AuditResult
from app.services.gemini_service import (
    GeminiAuditService,
    GeminiServiceError,
    InvalidImageError,
    decode_base64_image,
    detect_image_mime,
    validate_image,
)
from tests.conftest import VALID_RESULT


def _client_with(generate: AsyncMock) -> MagicMock:
    client = MagicMock()
    client.aio.models.generate_content = generate
    return client


def _response(parsed=None, text=None) -> SimpleNamespace:
    return SimpleNamespace(parsed=parsed, text=text)


def _run(coro):
    return asyncio.run(coro)


def test_audit_returns_parsed_object(png_bytes: bytes) -> None:
    expected = AuditResult.model_validate(VALID_RESULT)
    gen = AsyncMock(return_value=_response(parsed=expected))
    service = GeminiAuditService(_client_with(gen), "model-a")
    assert _run(service.audit(png_bytes, "image/png")) == expected
    kwargs = gen.await_args.kwargs
    assert kwargs["model"] == "model-a"
    assert kwargs["config"].response_mime_type == "application/json"


def test_audit_falls_back_to_text_json(png_bytes: bytes) -> None:
    gen = AsyncMock(return_value=_response(text=json.dumps(VALID_RESULT)))
    service = GeminiAuditService(_client_with(gen), "model-a")
    assert _run(service.audit(png_bytes, "image/png")).merchant == "La Parrilla del Centro"


def test_audit_malformed_json_raises(png_bytes: bytes) -> None:
    gen = AsyncMock(return_value=_response(text="{ esto no es json"))
    service = GeminiAuditService(_client_with(gen), "model-a")
    with pytest.raises(GeminiServiceError):
        _run(service.audit(png_bytes, "image/png"))


def test_audit_schema_mismatch_raises(png_bytes: bytes) -> None:
    gen = AsyncMock(return_value=_response(text=json.dumps({**VALID_RESULT, "risk_level": "EXTREMO"})))
    service = GeminiAuditService(_client_with(gen), "model-a")
    with pytest.raises(GeminiServiceError):
        _run(service.audit(png_bytes, "image/png"))


def test_audit_empty_response_raises(png_bytes: bytes) -> None:
    gen = AsyncMock(return_value=_response(text=""))
    service = GeminiAuditService(_client_with(gen), "model-a")
    with pytest.raises(GeminiServiceError, match="vacía"):
        _run(service.audit(png_bytes, "image/png"))


def test_audit_uses_fallback_model_on_404(png_bytes: bytes) -> None:
    not_found = genai_errors.ClientError(404, {"error": {"code": 404, "message": "gone", "status": "NOT_FOUND"}})
    ok = _response(text=json.dumps(VALID_RESULT))
    gen = AsyncMock(side_effect=[not_found, ok])
    service = GeminiAuditService(_client_with(gen), "model-a", "model-b")
    assert _run(service.audit(png_bytes, "image/png")).risk_level == "ALTO"
    assert [c.kwargs["model"] for c in gen.await_args_list] == ["model-a", "model-b"]


def test_audit_uses_fallback_on_503_and_timeout(png_bytes: bytes) -> None:
    server_err = genai_errors.ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}})
    ok = _response(text=json.dumps(VALID_RESULT))
    for first in (server_err, TimeoutError("lento")):
        gen = AsyncMock(side_effect=[first, ok])
        service = GeminiAuditService(_client_with(gen), "model-a", "model-b")
        assert _run(service.audit(png_bytes, "image/png")).merchant == "La Parrilla del Centro"
        assert gen.await_count == 2


def test_audit_both_models_fail_raises(png_bytes: bytes) -> None:
    server_err = genai_errors.ServerError(503, {"error": {"code": 503, "message": "busy", "status": "UNAVAILABLE"}})
    gen = AsyncMock(side_effect=[server_err, server_err])
    service = GeminiAuditService(_client_with(gen), "model-a", "model-b")
    with pytest.raises(GeminiServiceError, match="503"):
        _run(service.audit(png_bytes, "image/png"))
    assert gen.await_count == 2


def test_audit_non_retryable_error_does_not_use_fallback(png_bytes: bytes) -> None:
    bad_request = genai_errors.ClientError(400, {"error": {"code": 400, "message": "bad", "status": "INVALID_ARGUMENT"}})
    gen = AsyncMock(side_effect=bad_request)
    service = GeminiAuditService(_client_with(gen), "model-a", "model-b")
    with pytest.raises(GeminiServiceError, match="400"):
        _run(service.audit(png_bytes, "image/png"))
    assert gen.await_count == 1


def test_build_service_requires_api_key() -> None:
    from app.services.gemini_service import build_service

    with pytest.raises(GeminiServiceError):
        build_service("", "model-a", None)


def test_audit_network_error_raises(png_bytes: bytes) -> None:
    gen = AsyncMock(side_effect=ConnectionError("sin red"))
    service = GeminiAuditService(_client_with(gen), "model-a")
    with pytest.raises(GeminiServiceError):
        _run(service.audit(png_bytes, "image/png"))


# ---------- utilidades de imagen ----------

def test_detect_mime(png_bytes: bytes, jpeg_bytes: bytes) -> None:
    assert detect_image_mime(png_bytes) == "image/png"
    assert detect_image_mime(jpeg_bytes) == "image/jpeg"
    assert detect_image_mime(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert detect_image_mime(b"\x00\x00\x00\x18ftypheic....") == "image/heic"
    assert detect_image_mime(b"GIF89a") is None


def test_validate_image_rejects_empty_and_unknown() -> None:
    with pytest.raises(InvalidImageError):
        validate_image(b"")
    with pytest.raises(InvalidImageError):
        validate_image(b"not an image")


def test_decode_base64_variants(png_bytes: bytes) -> None:
    import base64

    raw = base64.b64encode(png_bytes).decode()
    assert decode_base64_image(raw) == png_bytes
    assert decode_base64_image(f"data:image/png;base64,{raw}") == png_bytes
    with pytest.raises(InvalidImageError):
        decode_base64_image("   ")
    with pytest.raises(InvalidImageError):
        decode_base64_image("###")
