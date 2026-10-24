"""Script de verificación end-to-end de la API en vivo con Gemini real.

Prueba el endpoint /api/audit cargando las imágenes generadas de demo.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import httpx
from app.main import app

SAMPLES = ROOT / "frontend" / "public" / "samples"


async def run_checks() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=90.0) as client:
        # 1. Health check
        print("\n--- [1/3] Probando /api/health ---")
        resp = await client.get("/api/health")
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.json()}")
        assert resp.status_code == 200

        # 2. Factura con propina oculta / irregularidades
        print("\n--- [2/3] Probando /api/audit con receipt-hidden-tip.png ---")
        tip_file = SAMPLES / "receipt-hidden-tip.png"
        with open(tip_file, "rb") as f:
            resp = await client.post(
                "/api/audit",
                files={"file": ("receipt-hidden-tip.png", f.read(), "image/png")},
            )
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print("Respuesta estructurada:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        assert resp.status_code == 200
        assert data["risk_level"] in ("MEDIO", "ALTO")
        assert len(data["suspicious_charges"]) > 0

        # 3. Factura correcta
        print("\n--- [3/3] Probando /api/audit con receipt-ok.png ---")
        ok_file = SAMPLES / "receipt-ok.png"
        with open(ok_file, "rb") as f:
            resp = await client.post(
                "/api/audit",
                files={"file": ("receipt-ok.png", f.read(), "image/png")},
            )
        print(f"Status: {resp.status_code}")
        data_ok = resp.json()
        print("Respuesta estructurada:")
        print(json.dumps(data_ok, indent=2, ensure_ascii=False))
        assert resp.status_code == 200
        assert data_ok["risk_level"] == "BAJO"

        print("\n¡Verificación de llamadas reales con Gemini completada al 100% con éxito!")


def main() -> None:
    asyncio.run(run_checks())


if __name__ == "__main__":
    main()
