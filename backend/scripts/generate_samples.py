"""Genera las imágenes de recibos de demo para el frontend (frontend/public/samples).

Uso:  python scripts/generate_samples.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "frontend" / "public" / "samples"

WIDTH = 520
MARGIN = 32
LINE_H = 30
COLS = 34  # caracteres por línea


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("consola.ttf", "cour.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _row(left: str, right: str = "") -> str:
    space = COLS - len(left) - len(right)
    return left + " " * max(space, 1) + right


def _render(lines: list[tuple[str, str]], path: Path) -> None:
    """lines: lista de (texto, estilo) con estilo en {"center", "bold", "normal"}."""
    font = _font(20)
    bold = _font(24)
    height = MARGIN * 2 + LINE_H * len(lines) + 20
    img = Image.new("RGB", (WIDTH, height), (250, 249, 246))
    d = ImageDraw.Draw(img)
    y = MARGIN
    for text, style in lines:
        f = bold if style in {"bold", "center-bold"} else font
        if style.startswith("center"):
            w = d.textlength(text, font=f)
            d.text(((WIDTH - w) / 2, y), text, fill=(25, 25, 25), font=f)
        else:
            d.text((MARGIN, y), text, fill=(25, 25, 25), font=f)
        y += LINE_H
    # Ligero desenfoque para simular impresión térmica
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=True)
    print(f"Generado: {path}")


SEP = "-" * COLS


def hidden_tip_receipt() -> list[tuple[str, str]]:
    # Consumo real: 76 + 42 + 18 + 22 = 158.00
    # Irregularidades: Pisco Sour duplicado (+22), subtotal impreso inflado (187 en vez de 180 con duplicado),
    # cargo por servicio 18% no informado, fee de mesa ambiguo.
    return [
        ("LA PARRILLA DEL CENTRO", "center-bold"),
        ("Av. Principal 245 - Mesa 12", "center"),
        ("24/10/2026  21:47   Mozo: Carlos", "center"),
        (SEP, "normal"),
        (_row("2 Lomo saltado  x38.00", "76.00"), "normal"),
        (_row("1 Ceviche clasico", "42.00"), "normal"),
        (_row("2 Chicha morada  x9.00", "18.00"), "normal"),
        (_row("1 Pisco sour", "22.00"), "normal"),
        (_row("1 Pisco sour", "22.00"), "normal"),
        (SEP, "normal"),
        (_row("SUBTOTAL", "187.00"), "normal"),
        (_row("Cargo por servicio 18%", "33.66"), "normal"),
        (_row("Fee de mesa", "5.00"), "normal"),
        (SEP, "normal"),
        (_row("TOTAL", "$225.66"), "bold"),
        (SEP, "normal"),
        ("Gracias por su visita", "center"),
    ]


def correct_receipt() -> list[tuple[str, str]]:
    # 2x4.50 + 3.75 + 6.25 = 19.00 ; IVA 10% = 1.90 ; total 20.90
    return [
        ("CAFE AURORA", "center-bold"),
        ("Calle Robles 18", "center"),
        ("24/10/2026  09:12   Caja 2", "center"),
        (SEP, "normal"),
        (_row("2 Cappuccino    x4.50", "9.00"), "normal"),
        (_row("1 Croissant mantequilla", "3.75"), "normal"),
        (_row("1 Tostada aguacate", "6.25"), "normal"),
        (SEP, "normal"),
        (_row("SUBTOTAL", "19.00"), "normal"),
        (_row("IVA 10%", "1.90"), "normal"),
        (SEP, "normal"),
        (_row("TOTAL", "$20.90"), "bold"),
        (SEP, "normal"),
        ("Propina no incluida", "center"),
        ("Gracias por su visita", "center"),
    ]


def main() -> None:
    _render(hidden_tip_receipt(), OUT_DIR / "receipt-hidden-tip.png")
    _render(correct_receipt(), OUT_DIR / "receipt-ok.png")


if __name__ == "__main__":
    main()
