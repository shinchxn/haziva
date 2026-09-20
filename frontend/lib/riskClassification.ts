/**
 * HAZIVA Risk Classification Constants & Helpers
 * Standardized risk thresholds matching HAZIVA map legend:
 * - Lower risk < 50% (< 0.50)
 * - Elevated risk 50–74% (0.50 – 0.7499)
 * - High risk ≥ 75% (≥ 0.75)
 */

export const RISK_THRESHOLDS = {
  ELEVATED: 0.5,
  HIGH: 0.75,
} as const;

export const RISK_COLORS = {
  LOWER: "#16a34a", // Green-600
  ELEVATED: "#f59e0b", // Amber-500
  HIGH: "#dc2626", // Red-600
  NO_DATA: "#94a3b8", // Slate-400
} as const;

export interface RiskCategory {
  label: "Lower" | "Elevated" | "High" | "No Data";
  color: string;
  className: string;
  dot: string;
}

export function classifyRisk(riskValue: number | null | undefined): RiskCategory {
  if (riskValue === null || riskValue === undefined || isNaN(riskValue)) {
    return {
      label: "No Data",
      color: RISK_COLORS.NO_DATA,
      className: "bg-slate-100 text-slate-700",
      dot: "bg-slate-400",
    };
  }

  if (riskValue >= RISK_THRESHOLDS.HIGH) {
    return {
      label: "High",
      color: RISK_COLORS.HIGH,
      className: "bg-red-50 text-red-700 border border-red-200",
      dot: "bg-red-500",
    };
  }

  if (riskValue >= RISK_THRESHOLDS.ELEVATED) {
    return {
      label: "Elevated",
      color: RISK_COLORS.ELEVATED,
      className: "bg-amber-50 text-amber-700 border border-amber-200",
      dot: "bg-amber-500",
    };
  }

  return {
    label: "Lower",
    color: RISK_COLORS.LOWER,
    className: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    dot: "bg-emerald-500",
  };
}
