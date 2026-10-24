"use client";

import { useRef, useState, type DragEvent } from "react";
import { ImageUp, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ACCEPTED_TYPES, MAX_UPLOAD_MB } from "@/lib/api";
import { cn } from "@/lib/utils";

interface UploadDropzoneProps {
  previewUrl: string | null;
  fileName?: string;
  disabled?: boolean;
  onFileSelected: (file: File) => void;
  onClear: () => void;
  onError: (message: string) => void;
}

export function validateImageFile(file: File): string | null {
  const okType = ACCEPTED_TYPES.includes(file.type) || /\.(jpe?g|png|webp|heic|heif)$/i.test(file.name);
  if (!okType) return "Formato no soportado. Usa JPG, PNG, WEBP o HEIC.";
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `La imagen supera el límite de ${MAX_UPLOAD_MB} MB.`;
  if (file.size === 0) return "La imagen está vacía.";
  return null;
}

export function UploadDropzone({
  previewUrl,
  fileName,
  disabled,
  onFileSelected,
  onClear,
  onError,
}: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    const error = validateImageFile(file);
    if (error) {
      onError(error);
      return;
    }
    onFileSelected(file);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    if (!disabled) handleFiles(e.dataTransfer.files);
  }

  if (previewUrl) {
    return (
      <div className="relative overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
        {/* eslint-disable-next-line @next/next/no-img-element -- blob: URL local, next/image no aplica */}
        <img
          src={previewUrl}
          alt={fileName ? `Vista previa de ${fileName}` : "Vista previa de la factura"}
          className="mx-auto max-h-[460px] w-auto object-contain"
        />
        <div className="flex items-center justify-between gap-2 border-t border-zinc-800 bg-zinc-900/80 px-3 py-2">
          <span className="truncate font-mono text-xs text-zinc-400">{fileName}</span>
          <Button type="button" variant="ghost" size="sm" onClick={onClear} disabled={disabled}>
            <X aria-hidden />
            Quitar
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      aria-label="Subir imagen de factura"
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !disabled) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cn(
        "flex min-h-72 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border border-dashed px-6 py-10 text-center transition-colors outline-none",
        "focus-visible:ring-2 focus-visible:ring-zinc-400",
        dragging ? "border-solid border-zinc-200 bg-zinc-900" : "border-zinc-700 hover:border-zinc-500 hover:bg-zinc-900/50",
        disabled && "pointer-events-none opacity-50",
      )}
    >
      <div className="rounded-md border border-zinc-800 bg-zinc-900 p-3">
        <ImageUp className="size-6 text-zinc-300" strokeWidth={1.5} aria-hidden />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-zinc-100">
          {dragging ? "Suelta la imagen aquí" : "Arrastra una foto de la factura"}
        </p>
        <p className="text-xs text-zinc-500">
          o haz clic para seleccionar · JPG, PNG, WEBP, HEIC · máx. {MAX_UPLOAD_MB} MB
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={[...ACCEPTED_TYPES, ".heic", ".heif"].join(",")}
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
    </div>
  );
}
