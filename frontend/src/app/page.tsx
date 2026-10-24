"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AlertCircle, Loader2, ScanSearch } from "lucide-react";

import { AuditResults } from "@/components/billbuster/audit-results";
import { SampleButtons } from "@/components/billbuster/sample-buttons";
import { UploadDropzone } from "@/components/billbuster/upload-dropzone";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { auditInvoice } from "@/lib/api";
import { loadSampleFile, type SampleInvoice } from "@/lib/samples";
import type { AuditResult } from "@/lib/types";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [sampleId, setSampleId] = useState<string | null>(null);
  const [isSampleResult, setIsSampleResult] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Libera la URL de la vista previa cuando cambia o se desmonta
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const selectFile = useCallback((f: File) => {
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
    setResult(null);
    setIsSampleResult(false);
    setSampleId(null);
    setError(null);
  }, []);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setIsSampleResult(false);
    setSampleId(null);
    setError(null);
    setLoading(false);
  }, []);

  async function handleSample(sample: SampleInvoice) {
    setError(null);
    try {
      const f = await loadSampleFile(sample);
      setFile(f);
      setPreviewUrl(URL.createObjectURL(f));
    } catch (e) {
      // Si la imagen no carga, igual mostramos los datos de muestra
      setError(e instanceof Error ? e.message : "No se pudo cargar la imagen de ejemplo.");
    }
    setResult(sample.result);
    setIsSampleResult(true);
    setSampleId(sample.id);
  }

  async function handleAudit() {
    if (!file) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const data = await auditInvoice(file, controller.signal);
      setResult(data);
      setIsSampleResult(false);
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setError(e instanceof Error ? e.message : "Error inesperado al auditar la factura.");
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-zinc-800">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex size-7 items-center justify-center rounded-md border border-zinc-700 bg-zinc-900">
              <ScanSearch className="size-4 text-zinc-100" strokeWidth={1.75} aria-hidden />
            </div>
            <span className="text-sm font-semibold tracking-tight text-zinc-50">BillBuster</span>
            <span className="hidden text-sm text-zinc-500 sm:inline">/ Auditoría de facturas</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden rounded border border-zinc-800 bg-zinc-900 px-2 py-0.5 font-mono text-[11px] text-zinc-400 sm:inline">
              Gemma 4 Multimodal
            </span>
            <span className="font-mono text-xs text-zinc-500">v1.0</span>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:py-10">
        <div className="mb-8 max-w-2xl space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">
            Verifica cada cargo antes de pagar.
          </h1>
          <p className="text-sm leading-relaxed text-zinc-400">
            Sube la foto de una cuenta, factura médica o recibo de servicios. BillBuster revisa los cálculos, detecta
            propinas impuestas, cargos ocultos y duplicados, y redacta el reclamo por ti.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
          {/* Columna izquierda: carga */}
          <div className="space-y-4">
            <Card className="border-zinc-800 bg-zinc-900/60">
              <CardHeader>
                <CardTitle className="text-base text-zinc-50">Factura</CardTitle>
                <CardDescription className="text-zinc-500">Imagen nítida, con todos los importes visibles.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <UploadDropzone
                  previewUrl={previewUrl}
                  fileName={file?.name}
                  disabled={loading}
                  onFileSelected={selectFile}
                  onClear={clear}
                  onError={setError}
                />
                <Button
                  type="button"
                  size="lg"
                  className="w-full"
                  disabled={!file || loading}
                  onClick={handleAudit}
                >
                  {loading ? <Loader2 className="animate-spin" aria-hidden /> : <ScanSearch aria-hidden />}
                  {loading ? "Auditando…" : "Auditar Factura"}
                </Button>
                <SampleButtons onSelect={handleSample} disabled={loading} activeId={sampleId} />
              </CardContent>
            </Card>
          </div>

          {/* Columna derecha: resultados */}
          <div className="space-y-4" aria-live="polite" aria-busy={loading}>
            {error && (
              <Alert className="border-zinc-600 bg-zinc-950 text-zinc-100">
                <AlertCircle aria-hidden />
                <AlertTitle>No se pudo completar la auditoría</AlertTitle>
                <AlertDescription className="text-zinc-400">{error}</AlertDescription>
              </Alert>
            )}

            {loading ? (
              <LoadingState />
            ) : result ? (
              <>
                {isSampleResult && (
                  <p className="text-xs text-zinc-500">
                    Resultado precalculado de ejemplo. Pulsa{" "}
                    <span className="font-medium text-zinc-300">Auditar Factura</span> para analizar esta imagen con
                    la IA.
                  </p>
                )}
                <AuditResults result={result} isSample={isSampleResult} />
              </>
            ) : (
              <EmptyState />
            )}
          </div>
        </div>
      </main>

      <footer className="border-t border-zinc-800">
        <div className="mx-auto max-w-6xl px-4 py-4 text-xs text-zinc-600 sm:px-6">
          BillBuster es una herramienta de apoyo. Verifica siempre los importes con el comercio.
        </div>
      </footer>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex min-h-80 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-800 px-6 text-center">
      <p className="text-sm font-medium text-zinc-300">Sin auditoría todavía</p>
      <p className="max-w-sm text-xs leading-relaxed text-zinc-500">
        Sube una imagen y pulsa «Auditar Factura», o usa uno de los ejemplos de la demo rápida.
      </p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex min-h-80 flex-col items-center justify-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/40 px-6 text-center">
      <Loader2 className="size-6 animate-spin text-zinc-300" aria-hidden />
      <p className="text-sm font-medium text-zinc-200">Analizando la factura…</p>
      <p className="max-w-sm text-xs text-zinc-500">
        Leyendo ítems, verificando sumas, impuestos y cargos adicionales. Puede tardar unos segundos.
      </p>
    </div>
  );
}
