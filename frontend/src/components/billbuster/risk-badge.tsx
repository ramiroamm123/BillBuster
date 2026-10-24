import { AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/lib/types";

const STYLES: Record<RiskLevel, { className: string; label: string; Icon: typeof AlertTriangle }> = {
  BAJO: {
    className: "bg-black text-white border-white",
    label: "Riesgo bajo",
    Icon: ShieldCheck,
  },
  MEDIO: {
    className: "bg-zinc-500 text-white border-zinc-500",
    label: "Riesgo medio",
    Icon: ShieldAlert,
  },
  ALTO: {
    className: "bg-white text-black border-white font-semibold",
    label: "Riesgo alto",
    Icon: AlertTriangle,
  },
};

export function RiskBadge({ level, className }: { level: RiskLevel; className?: string }) {
  const { className: variant, label, Icon } = STYLES[level] ?? STYLES.MEDIO;
  return (
    <Badge
      className={cn("h-7 rounded-md border px-2.5 text-xs uppercase tracking-wider", variant, className)}
      aria-label={label}
    >
      <Icon data-icon="inline-start" aria-hidden />
      {label}
    </Badge>
  );
}
