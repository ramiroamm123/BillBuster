"""Esquemas Pydantic: contrato de entrada/salida de la auditoría."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

RiskLevel = Literal["BAJO", "MEDIO", "ALTO"]


class SuspiciousCharge(BaseModel):
    item: str = Field(min_length=1, description="Concepto del cargo")
    amount: str = Field(min_length=1, description="Monto con símbolo de moneda, ej. $0.00")
    reason: str = Field(min_length=1, description="Motivo por el cual es irregular o sospechoso")


class AuditResult(BaseModel):
    merchant: str = Field(default="Desconocido", description="Nombre del comercio o 'Desconocido'")
    total_billed: str = Field(min_length=1, description="Total impreso en la factura, ej. $0.00")
    real_subtotal: str = Field(min_length=1, description="Suma real de consumos legítimos, ej. $0.00")
    risk_level: RiskLevel = Field(description="BAJO | MEDIO | ALTO")
    summary: str = Field(min_length=1, description="Veredicto conciso en 2 oraciones")
    suspicious_charges: list[SuspiciousCharge] = Field(default_factory=list)
    dispute_message: str = Field(min_length=1, description="Mensaje formal de reclamo")

    @field_validator("risk_level", mode="before")
    @classmethod
    def _normalize_risk(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("merchant", mode="before")
    @classmethod
    def _default_merchant(cls, value: object) -> object:
        if value is None or (isinstance(value, str) and not value.strip()):
            return "Desconocido"
        return value.strip() if isinstance(value, str) else value


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    model: str
