"""Punto de entrada de la API de BillBuster."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.services.gemini_service import GeminiServiceError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="BillBuster API",
        description="Auditor visual multimodal de facturas y recibos.",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(GeminiServiceError)
    async def _gemini_error_handler(_: Request, exc: GeminiServiceError) -> JSONResponse:
        # Cubre fallos al construir el servicio (p. ej. API key ausente) durante la resolución de dependencias.
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    app.include_router(router)
    return app


app = create_app()
