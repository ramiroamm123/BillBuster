import type { AuditResult } from "@/lib/types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"];
export const MAX_UPLOAD_MB = 10;

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function auditInvoice(file: File, signal?: AbortSignal): Promise<AuditResult> {
  const body = new FormData();
  body.append("file", file);

  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/audit`, { method: "POST", body, signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(`No se pudo conectar con el backend (${API_URL}). ¿Está corriendo uvicorn?`);
  }

  if (!response.ok) {
    let detail = `Error ${response.status} al auditar la factura.`;
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") detail = data.detail;
    } catch {
      /* respuesta sin JSON */
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as AuditResult;
}
