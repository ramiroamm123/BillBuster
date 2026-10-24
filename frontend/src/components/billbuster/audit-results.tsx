import { CheckCircle2, FileWarning, Info } from "lucide-react";

import { CopyDisputeButton } from "@/components/billbuster/copy-dispute-button";
import { RiskBadge } from "@/components/billbuster/risk-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AuditResult } from "@/lib/types";

function Amount({ label, value, emphasis }: { label: string; value: string; emphasis?: boolean }) {
  return (
    <div className="flex flex-col gap-1 rounded-md border border-zinc-800 bg-zinc-950 p-4">
      <span className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">{label}</span>
      <span className={emphasis ? "font-mono text-2xl font-semibold text-zinc-50" : "font-mono text-2xl text-zinc-300"}>
        {value}
      </span>
    </div>
  );
}

export function AuditResults({ result, isSample }: { result: AuditResult; isSample?: boolean }) {
  const charges = result.suspicious_charges ?? [];

  return (
    <Card className="border-zinc-800 bg-zinc-900/60">
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <CardDescription className="text-xs uppercase tracking-wider text-zinc-500">Comercio</CardDescription>
            <CardTitle className="truncate text-xl font-semibold text-zinc-50">{result.merchant}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {isSample && (
              <Badge variant="outline" className="h-7 rounded-md border-zinc-700 text-zinc-400">
                Datos de muestra
              </Badge>
            )}
            <RiskBadge level={result.risk_level} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Amount label="Total facturado" value={result.total_billed} emphasis />
          <Amount label="Subtotal real" value={result.real_subtotal} />
        </div>

        <Alert className="border-zinc-800 bg-zinc-950 text-zinc-200">
          <Info aria-hidden />
          <AlertTitle>Veredicto</AlertTitle>
          <AlertDescription className="text-zinc-400">{result.summary}</AlertDescription>
        </Alert>

        <Separator className="bg-zinc-800" />

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-zinc-200">Cargos sospechosos</h3>
            <span className="font-mono text-xs text-zinc-500">{charges.length} detectado(s)</span>
          </div>

          {charges.length === 0 ? (
            <div className="flex items-center gap-2 rounded-md border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-zinc-400">
              <CheckCircle2 className="size-4 text-zinc-300" aria-hidden />
              No se detectaron cargos irregulares.
            </div>
          ) : (
            <div className="overflow-hidden rounded-md border border-zinc-800">
              <Table>
                <TableHeader>
                  <TableRow className="border-zinc-800 hover:bg-transparent">
                    <TableHead className="text-zinc-500">Concepto</TableHead>
                    <TableHead className="text-right text-zinc-500">Monto</TableHead>
                    <TableHead className="text-zinc-500">Motivo</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {charges.map((c, i) => (
                    <TableRow key={`${c.item}-${i}`} className="border-zinc-800 hover:bg-zinc-900">
                      <TableCell className="align-top font-medium whitespace-normal text-zinc-100">{c.item}</TableCell>
                      <TableCell className="text-right align-top font-mono text-zinc-100">{c.amount}</TableCell>
                      <TableCell className="min-w-56 align-top whitespace-normal text-zinc-400">{c.reason}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </section>

        <Separator className="bg-zinc-800" />

        <section className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="flex items-center gap-2 text-sm font-medium text-zinc-200">
              <FileWarning className="size-4 text-zinc-400" aria-hidden />
              Mensaje de reclamo
            </h3>
            <CopyDisputeButton text={result.dispute_message} />
          </div>
          <div className="rounded-md border border-zinc-800 bg-zinc-950 p-4 text-sm leading-relaxed whitespace-pre-wrap text-zinc-300">
            {result.dispute_message}
          </div>
        </section>
      </CardContent>
    </Card>
  );
}
