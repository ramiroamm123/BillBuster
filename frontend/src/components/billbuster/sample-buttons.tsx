"use client";

import { FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SAMPLES, type SampleInvoice } from "@/lib/samples";

export function SampleButtons({
  onSelect,
  disabled,
  activeId,
}: {
  onSelect: (sample: SampleInvoice) => void;
  disabled?: boolean;
  activeId?: string | null;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-wider text-zinc-500">Demo rápida</p>
      <div className="flex flex-col gap-2 sm:flex-row">
        {SAMPLES.map((s) => (
          <Button
            key={s.id}
            type="button"
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={() => onSelect(s)}
            aria-pressed={activeId === s.id}
            className="justify-start border-zinc-800 bg-transparent text-zinc-300 hover:bg-zinc-900 hover:text-zinc-50 aria-pressed:border-zinc-500 aria-pressed:text-zinc-50"
          >
            <FileText aria-hidden />
            {s.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
