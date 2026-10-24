"""Endpoints de la API: /api/health y /api/audit."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_audit_service
from app.core.config import Settings, get_settings
from app.schemas.audit import AuditResult, ErrorResponse, HealthResponse
from app.services.gemini_service import (
    GeminiAuditService,
    GeminiServiceError,
    InvalidImageError,
    decode_base64_image,
    validate_image,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(model=settings.gemini_model)


@router.post(
    "/audit",
    response_model=AuditResult,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def audit_invoice(
    settings: Annotated[Settings, Depends(get_settings)],
    service: Annotated[GeminiAuditService, Depends(get_audit_service)],
    file: Annotated[UploadFile | None, File(description="Imagen de la factura")] = None,
    image_base64: Annotated[str | None, Form(description="Imagen en base64 o data URL")] = None,
) -> AuditResult:
    # 1. Obtener bytes de la imagen (archivo o base64)
    try:
        if file is not None and file.filename:
            data = await file.read(settings.max_upload_bytes + 1)
        elif image_base64:
            data = decode_base64_image(image_base64)
        else:
            raise InvalidImageError("Debes enviar una imagen en 'file' o 'image_base64'.")

        if len(data) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"La imagen supera el límite de {settings.max_upload_mb} MB.",
            )
        mime_type = validate_image(data)
    except InvalidImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # 2. Auditar con Gemini
    try:
        return await service.audit(data, mime_type)
    except GeminiServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado auditando la factura")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la factura.",
        ) from exc
