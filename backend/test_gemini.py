"""Smoke test de conectividad con la API de Gemini.

Verifica:
  1. Que la API key del .env es válida (listado de modelos).
  2. Que el modelo configurado acepta entrada multimodal (imagen + texto).
  3. Que el modelo devuelve salida JSON estructurada con response_schema.

Uso:  python test_gemini.py
"""

from __future__ import annotations

import io
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from PIL import Image, ImageDraw
from pydantic import BaseModel

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = os.getenv("GEMINI_MODEL", "gemma-4-26b-a4b-it")
# Candidatos a probar si el modelo configurado falla (algunos modelos listados devuelven 404 a cuentas nuevas).
CANDIDATES = [MODEL, os.getenv("GEMINI_FALLBACK_MODEL", ""), "gemma-4-26b-a4b-it", "gemini-3.5-flash",
              "gemini-3-flash-preview"]


def make_receipt_png() -> bytes:
    img = Image.new("RGB", (360, 260), "white")
    d = ImageDraw.Draw(img)
    lines = [
        "CAFE PRUEBA",
        "------------------------",
        "Cafe americano     $3.50",
        "Croissant          $2.50",
        "------------------------",
        "TOTAL              $6.00",
    ]
    for i, line in enumerate(lines):
        d.text((20, 20 + i * 32), line, fill="black", font_size=20)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TotalCheck(BaseModel):
    merchant: str
    total: str


def main() -> int:
    if not API_KEY:
        print("[FAIL] GEMINI_API_KEY no está definida en .env")
        return 1

    client = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=45_000, retry_options=types.HttpRetryOptions(attempts=1)),
    )

    # 1. Listar modelos
    print("[1/3] Listando modelos con generateContent...")
    names = [
        m.name
        for m in client.models.list()
        if "generateContent" in (m.supported_actions or [])
    ]
    flash = [n for n in names if "flash" in n]
    print(f"      {len(names)} modelos disponibles. Flash: {', '.join(flash[:8])}...")

    png = make_receipt_png()

    # 2. Llamada multimodal en texto libre (probando candidatos en orden)
    print("[2/3] Llamada multimodal (imagen + texto)...")
    model = None
    text = ""
    seen: set[str] = set()
    for candidate in CANDIDATES:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if f"models/{candidate}" not in names:
            print(f"      - {candidate}: no listado, se omite")
            continue
        t0 = time.perf_counter()
        try:
            resp = client.models.generate_content(
                model=candidate,
                contents=[
                    types.Part.from_bytes(data=png, mime_type="image/png"),
                    "¿Cuál es el total impreso en este recibo? Responde solo con el monto.",
                ],
            )
        except errors.APIError as exc:
            print(f"      - {candidate}: {exc.code} {exc.status} -> {str(exc.message)[:90]}")
            continue
        text = (resp.text or "").strip()
        print(f"      - {candidate}: OK ({time.perf_counter() - t0:.1f}s) -> {text!r}")
        model = candidate
        break

    if model is None:
        print("[FAIL] Ningún modelo candidato aceptó la llamada multimodal.")
        return 1
    if "6" not in text:
        print("[FAIL] El modelo no leyó correctamente el total.")
        return 1
    print(f"[OK]  Lectura multimodal correcta con {model}.")
    if model != MODEL:
        print(f"[WARN] Actualiza GEMINI_MODEL={model} en .env")

    # 3. Salida estructurada
    print("[3/3] Salida JSON estructurada (response_schema)...")
    t0 = time.perf_counter()
    resp = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=png, mime_type="image/png"),
            "Extrae el nombre del comercio y el total.",
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TotalCheck,
            temperature=0,
        ),
    )
    parsed = resp.parsed
    print(f"      Parsed ({time.perf_counter() - t0:.1f}s): {parsed!r}")
    if not isinstance(parsed, TotalCheck):
        print("[FAIL] La respuesta no se pudo parsear al esquema.")
        return 1
    print("[OK]  Salida estructurada válida.")

    print("\nTodo OK: Gemini listo para BillBuster.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
