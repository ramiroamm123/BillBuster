"""Integración con la API de Gemini: imagen + prompt -> AuditResult estructurado."""

from __future__ import annotations

import base64
import binascii
import logging
import re

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.schemas.audit import AuditResult
from app.services.prompts import SYSTEM_PROMPT, USER_PROMPT

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
_DATA_URL_RE = re.compile(r"^data:(?P<mime>[\w/+.-]+)?;base64,", re.IGNORECASE)


class InvalidImageError(ValueError):
    """La entrada no es una imagen válida/soportada (-> HTTP 400)."""


class GeminiServiceError(RuntimeError):
    """Fallo al llamar o interpretar la respuesta de Gemini (-> HTTP 500)."""


_RETRYABLE_CODES = {404, 408, 429, 500, 502, 503, 504}


def _is_retryable(exc: Exception) -> bool:
    """Errores ante los que tiene sentido probar el modelo de respaldo."""
    if isinstance(exc, genai_errors.APIError):
        return exc.code in _RETRYABLE_CODES
    if isinstance(exc, (httpx.HTTPError, TimeoutError, ConnectionError, OSError)):
        return True
    name = type(exc).__name__.lower()
    return any(k in name for k in ("timeout", "read", "connection", "protocol", "transport", "reset"))


def detect_image_mime(data: bytes) -> str | None:
    """Detecta el tipo de imagen por sus magic bytes (no confiamos en el content-type del cliente)."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis"}:
            return "image/heic"
        if brand in {b"mif1", b"msf1"}:
            return "image/heif"
    return None


def decode_base64_image(value: str) -> bytes:
    """Decodifica base64 puro o un data URL (data:image/png;base64,...)."""
    payload = _DATA_URL_RE.sub("", value.strip(), count=1)
    payload = re.sub(r"\s+", "", payload)
    if not payload:
        raise InvalidImageError("El campo image_base64 está vacío.")
    try:
        return base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InvalidImageError("image_base64 no es un base64 válido.") from exc


def validate_image(data: bytes) -> str:
    """Valida que los bytes sean una imagen soportada y devuelve su MIME type."""
    if not data:
        raise InvalidImageError("La imagen está vacía.")
    mime = detect_image_mime(data)
    if mime is None or mime not in SUPPORTED_MIME_TYPES:
        raise InvalidImageError("Formato no soportado. Usa JPG, PNG, WEBP o HEIC.")
    return mime


class GeminiAuditService:
    def __init__(self, client: genai.Client, model: str, fallback_model: str | None = None) -> None:
        self._client = client
        self.model = model
        self.fallback_model = fallback_model if fallback_model and fallback_model != model else None

    def _config(self, model: str) -> types.GenerateContentConfig:
        # Los modelos Gemma (open-weights) funcionan de forma óptima con JSON nativo
        # guiado por el system prompt, mientras que Gemini usa grammar-based response_schema.
        is_gemma = "gemma" in model.lower()
        return types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=None if is_gemma else AuditResult,
            temperature=0.2 if is_gemma else 0.1,
        )

    async def _generate(self, model: str, image_bytes: bytes, mime_type: str) -> types.GenerateContentResponse:
        return await self._client.aio.models.generate_content(
            model=model,
            contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), USER_PROMPT],
            config=self._config(model),
        )

    async def audit(self, image_bytes: bytes, mime_type: str) -> AuditResult:
        try:
            try:
                response = await self._generate(self.model, image_bytes, mime_type)
            except Exception as exc:
                if not (self.fallback_model and _is_retryable(exc)):
                    raise
                logger.warning(
                    "Modelo %s falló (%s); usando fallback %s", self.model, type(exc).__name__, self.fallback_model
                )
                response = await self._generate(self.fallback_model, image_bytes, mime_type)
        except genai_errors.APIError as exc:
            logger.exception("Error de la API de Gemini")
            raise GeminiServiceError(f"Error de la API de Gemini ({exc.code}).") from exc
        except Exception as exc:  # red, timeouts, etc.
            logger.exception("Fallo inesperado llamando a Gemini")
            raise GeminiServiceError("No se pudo contactar con el servicio de IA.") from exc

        return self._parse(response)

    @staticmethod
    def _parse(response: types.GenerateContentResponse) -> AuditResult:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, AuditResult):
            return parsed
        text = getattr(response, "text", None)
        if not text:
            raise GeminiServiceError("La IA devolvió una respuesta vacía.")

        # Limpiar posibles bloques markdown ```json ... ```
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            cleaned = cleaned.strip()

        # Intentar parsear diccionario o primer elemento si vino en lista
        try:
            import json
            raw_data = json.loads(cleaned)
            if isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], dict):
                raw_data = raw_data[0]
            if isinstance(raw_data, dict):
                return AuditResult.model_validate(raw_data)
        except Exception:
            pass

        try:
            return AuditResult.model_validate_json(cleaned)
        except ValidationError as exc:
            logger.error("Respuesta de Gemini no cumple el esquema: %s", text[:500])
            raise GeminiServiceError("La respuesta de la IA no cumple el formato esperado.") from exc


def build_service(
    api_key: str, model: str, fallback_model: str | None, timeout_s: int = 60
) -> GeminiAuditService:
    if not api_key:
        raise GeminiServiceError("GEMINI_API_KEY no está configurada.")
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=timeout_s * 1000,  # milisegundos
            retry_options=types.HttpRetryOptions(attempts=2),
        ),
    )
    return GeminiAuditService(client, model, fallback_model)
