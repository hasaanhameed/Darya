import type { RiskCategory } from "@/lib/api/types";
import { RISK_LABEL } from "@/lib/risk/categories";

// Static class names so Tailwind can find them.
const SWATCH_CLASS: Record<RiskCategory, string> = {
  normal: "bg-risk-normal",
  low: "bg-risk-low",
  medium: "bg-risk-medium",
  high: "bg-risk-high",
  very_high: "bg-risk-very-high",
  exceptional: "bg-risk-exceptional",
};

/** A risk category as a color square plus its name. Color is never shown on its own. */
export function RiskBadge({ category, size = "body" }: { category: RiskCategory; size?: "body" | "focal" }) {
  const swatch = size === "focal" ? "size-4" : "size-2.5";
  const text = size === "focal" ? "text-focal font-semibold" : "font-medium";
  return (
    <span className={`inline-flex items-center gap-2 ${text}`}>
      <span aria-hidden className={`${swatch} shrink-0 rounded-[2px] ${SWATCH_CLASS[category]}`} />
      {RISK_LABEL[category]}
    </span>
  );
}
