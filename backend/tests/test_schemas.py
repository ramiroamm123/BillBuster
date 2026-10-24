"""Validación de los esquemas Pydantic del contrato de auditoría."""

from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from app.schemas.audit import AuditResult, SuspiciousCharge
from tests.conftest import VALID_RESULT


def test_valid_full_result() -> None:
    result = AuditResult.model_validate(VALID_RESULT)
    assert result.merchant == "La Parrilla del Centro"
    assert result.risk_level == "ALTO"
    assert len(result.suspicious_charges) == 2
    assert isinstance(result.suspicious_charges[0], SuspiciousCharge)


def test_empty_suspicious_charges_is_valid() -> None:
    data = {**VALID_RESULT, "risk_level": "BAJO", "suspicious_charges": []}
    assert AuditResult.model_validate(data).suspicious_charges == []


def test_missing_suspicious_charges_defaults_to_empty() -> None:
    data = {k: v for k, v in VALID_RESULT.items() if k != "suspicious_charges"}
    assert AuditResult.model_validate(data).suspicious_charges == []


@pytest.mark.parametrize("raw, expected", [("bajo", "BAJO"), (" Medio ", "MEDIO"), ("alto", "ALTO")])
def test_risk_level_is_normalized(raw: str, expected: str) -> None:
    assert AuditResult.model_validate({**VALID_RESULT, "risk_level": raw}).risk_level == expected


@pytest.mark.parametrize("merchant", ["", "   ", None])
def test_blank_merchant_defaults_to_unknown(merchant: str | None) -> None:
    assert AuditResult.model_validate({**VALID_RESULT, "merchant": merchant}).merchant == "Desconocido"


def test_round_trip_json_matches_contract_keys() -> None:
    dumped = AuditResult.model_validate(VALID_RESULT).model_dump()
    assert set(dumped) == {
        "merchant", "total_billed", "real_subtotal", "risk_level",
        "summary", "suspicious_charges", "dispute_message",
    }
    assert set(dumped["suspicious_charges"][0]) == {"item", "amount", "reason"}


@pytest.mark.parametrize("risk", ["CRÍTICO", "NINGUNO", "", 3])
def test_invalid_risk_level(risk: object) -> None:
    with pytest.raises(ValidationError):
        AuditResult.model_validate({**VALID_RESULT, "risk_level": risk})


@pytest.mark.parametrize("field", ["total_billed", "real_subtotal", "risk_level", "summary", "dispute_message"])
def test_missing_required_field(field: str) -> None:
    data = {k: v for k, v in VALID_RESULT.items() if k != field}
    with pytest.raises(ValidationError):
        AuditResult.model_validate(data)


def test_empty_summary_is_invalid() -> None:
    with pytest.raises(ValidationError):
        AuditResult.model_validate({**VALID_RESULT, "summary": ""})


def test_suspicious_charge_without_reason_is_invalid() -> None:
    data = copy.deepcopy(VALID_RESULT)
    del data["suspicious_charges"][0]["reason"]
    with pytest.raises(ValidationError):
        AuditResult.model_validate(data)


def test_suspicious_charges_must_be_a_list() -> None:
    with pytest.raises(ValidationError):
        AuditResult.model_validate({**VALID_RESULT, "suspicious_charges": "ninguno"})
