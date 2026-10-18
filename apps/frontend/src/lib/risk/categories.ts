import type { FloodLimits, RiskCategory } from "@/lib/api/types";

/** PMD-FFD flood categories, lowest to highest. */
export const RISK_ORDER: RiskCategory[] = [
  "normal",
  "low",
  "medium",
  "high",
  "very_high",
  "exceptional",
];

export const RISK_LABEL: Record<RiskCategory, string> = {
  normal: "Normal",
  low: "Low",
  medium: "Medium",
  high: "High",
  very_high: "Very High",
  exceptional: "Exceptional",
};

/** Hex values for the map, which can't read CSS variables. Must match globals.css. */
export const RISK_COLOR: Record<RiskCategory, string> = {
  normal: "#1f66a3",
  low: "#dc9130",
  medium: "#d07226",
  high: "#bc561e",
  very_high: "#9a3b18",
  exceptional: "#672514",
};

export function riskRank(category: RiskCategory): number {
  return RISK_ORDER.indexOf(category);
}

/** The FFD category for a discharge, in thousands of cusecs. Below the Low limit is Normal. */
export function categoryForFlow(flow_kcfs: number, limits: FloodLimits): RiskCategory {
  if (limits.exceptional_kcfs !== null && flow_kcfs >= limits.exceptional_kcfs) return "exceptional";
  if (flow_kcfs >= limits.very_high_kcfs) return "very_high";
  if (flow_kcfs >= limits.high_kcfs) return "high";
  if (flow_kcfs >= limits.medium_kcfs) return "medium";
  if (flow_kcfs >= limits.low_kcfs) return "low";
  return "normal";
}
