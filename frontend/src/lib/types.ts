export type RiskLevel = "BAJO" | "MEDIO" | "ALTO";

export interface SuspiciousCharge {
  item: string;
  amount: string;
  reason: string;
}

export interface AuditResult {
  merchant: string;
  total_billed: string;
  real_subtotal: string;
  risk_level: RiskLevel;
  summary: string;
  suspicious_charges: SuspiciousCharge[];
  dispute_message: string;
}
