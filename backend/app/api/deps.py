"""Dependencias inyectables (sustituibles en tests vía app.dependency_overrides)."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.gemini_service import GeminiAuditService, build_service


@lru_cache
def get_audit_service() -> GeminiAuditService:
    settings = get_settings()
    return build_service(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.gemini_model,
        fallback_model=settings.gemini_fallback_model,
        timeout_s=settings.gemini_timeout_s,
    )
