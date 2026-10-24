# BillBuster 🧾🔍

Auditor visual multimodal de facturas y recibos potenciado por **Gemma 4** (Google Open-Weights AI), **FastAPI** y **Next.js**.

> 🏆 **Producido para competir en:**
> - **Best Use of Gemma 4**: Utiliza `gemma-4-26b-a4b-it` vía Gemini API para proveer una experiencia multimodal que audita recibos reales y desglosa cargos sospechosos.
> - **Best Open-Source AI Project (DigitalOcean)**: Utiliza un modelo de IA de pesos abiertos (open-weights) como núcleo funcional indispensable.

BillBuster analiza fotos de facturas o tickets (restaurantes, clínicas, servicios) para detectar:
1. **Errores de cálculo matemático:** suma de ítems vs subtotal o total cobrado.
2. **Propinas automáticas:** cargos por "servicio" agregados sin aviso o calculados con fórmulas infladas.
3. **Cargos ocultos o duplicados:** fees ambiguos ("cargo de mesa", cubiertos) o ítems cobrados más de una vez.
4. **Mensaje formal de reclamo:** redacción educada, profesional y lista para copiar y presentar al comercio.

---

## Estructura del Proyecto

```
BillBuster/
├── backend/                  # API en FastAPI (Python 3.10+)
│   ├── app/
│   │   ├── api/              # Rutas: /api/health, /api/audit
│   │   ├── core/             # Configuración pydantic-settings (.env)
│   │   ├── schemas/          # Modelos Pydantic del contrato estructurado
│   │   ├── services/         # Integración Gemini multimodal y system prompt
│   │   └── main.py           # FastAPI app + CORS
│   ├── scripts/              # Generador de recibos y verificación
│   ├── tests/                # Suite de pruebas unitarias (pytest)
│   ├── requirements.txt      # Dependencias backend
│   └── .env                  # Variables de entorno (API Key, modelos)
├── frontend/                 # Aplicación Next.js (App Router + Tailwind CSS)
│   ├── src/
│   │   ├── app/              # layout, page principal monocromo
│   │   ├── components/       # Componentes shadcn y UI de BillBuster
│   │   └── lib/              # Cliente API, tipos TypeScript y mocks
│   └── public/samples/       # Imágenes de prueba para demostración rápida
└── README.md
```

---

## Requisitos Previos

- **Python 3.10+** (probado con Python 3.12 en Windows nativo)
- **Node.js 18+** y **npm** (probado con Node v24 y npm 11)

---

## Puesta en Marcha Local

### 1. Backend (FastAPI)

En una terminal PowerShell:

```powershell
# Ir a la carpeta backend
cd backend

# Activar el entorno virtual existente (o crearlo con `python -m venv .venv`)
.\.venv\Scripts\Activate.ps1

# (Opcional si ya está instalado) Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor uvicorn en el puerto 8000
uvicorn app.main:app --reload --port 8000
```

> La API estará disponible en `http://localhost:8000`.
> Puedes verificar el estado en `http://localhost:8000/api/health` o consultar la documentación interactiva en `http://localhost:8000/docs`.

### 2. Frontend (Next.js)

En una segunda terminal PowerShell:

```powershell
# Ir a la carpeta frontend
cd frontend

# Iniciar el servidor de desarrollo
npm run dev
```

> Abre tu navegador en **`http://localhost:3000`**.

---

## Ejecución de Pruebas Unitarias

Para ejecutar la suite completa de pruebas del backend con `pytest`:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -v
```

Cobertura de pruebas:
- Validación de esquemas Pydantic (entradas válidas, límites, normalizaciones de riesgo y casos inválidos).
- Endpoints de la API con mocks (`/api/health`, `/api/audit`, límites de tamaño 413, formatos inválidos 400, errores 500 controlados y preflight CORS).
- Servicio multimodal de Gemini con manejo de fallbacks y reintentos.

---

## Modo Demo Rápida

La interfaz incluye dos botones de acceso rápido para validar el flujo completo sin requerir una foto externa:
- **Factura con propina no informada:** carga un recibo térmico con un Pisco Sour duplicado, subtotal inflado, fee de mesa y 18% de servicio impuesto.
- **Factura correcta:** carga un recibo con consumos e IVA calculados al céntimo.

Puedes pulsar cualquiera de estos botones para previsualizar los resultados y hacer clic en **"Auditar Factura"** para enviar la imagen al modelo de Gemini en tiempo real.
