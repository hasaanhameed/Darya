import type { FloodLimits, RiskCategory } from "@/lib/api/types";
import { RISK_COLOR, RISK_LABEL } from "@/lib/risk/categories";

interface ThresholdStaffProps {
  limits: FloodLimits;
  today_kcfs: number;
  peak_kcfs: number | null;
}

const HEIGHT = 220;
const BAR_X = 22;
const BAR_WIDTH = 10;

/**
 * A vertical gauge staff showing the site's FFD flood limits, like the painted staff at a barrage.
 * Solid marker: today's flow. Hollow marker: the forecast peak.
 */
export function ThresholdStaff({ limits, today_kcfs, peak_kcfs }: ThresholdStaffProps) {
  const top = limits.exceptional_kcfs ?? limits.very_high_kcfs * 1.25;
  const max = Math.max(top * 1.1, today_kcfs, peak_kcfs ?? 0) * 1.02;
  const y = (kcfs: number) => HEIGHT - (kcfs / max) * HEIGHT;

  const bands: { category: RiskCategory; from: number; to: number }[] = [
    { category: "normal", from: 0, to: limits.low_kcfs },
    { category: "low", from: limits.low_kcfs, to: limits.medium_kcfs },
    { category: "medium", from: limits.medium_kcfs, to: limits.high_kcfs },
    { category: "high", from: limits.high_kcfs, to: limits.very_high_kcfs },
    { category: "very_high", from: limits.very_high_kcfs, to: limits.exceptional_kcfs ?? max },
  ];
  if (limits.exceptional_kcfs !== null) {
    bands.push({ category: "exceptional", from: limits.exceptional_kcfs, to: max });
  }

  return (
    <figure className="flex flex-col gap-2">
      <svg
        width="150"
        height={HEIGHT + 8}
        viewBox={`0 -4 150 ${HEIGHT + 8}`}
        role="img"
        aria-label={`FFD flood limits. Today ${Math.round(today_kcfs)} thousand cusecs${
          peak_kcfs ? `, forecast peak ${Math.round(peak_kcfs)} thousand cusecs` : ""
        }.`}
      >
        {bands.map((band) => (
          <g key={band.category}>
            <rect
              x={BAR_X}
              y={y(band.to)}
              width={BAR_WIDTH}
              height={y(band.from) - y(band.to)}
              fill={RISK_COLOR[band.category]}
            />
            {band.category !== "normal" && (
              <>
                <line x1={BAR_X + BAR_WIDTH} x2={BAR_X + BAR_WIDTH + 6} y1={y(band.from)} y2={y(band.from)} stroke="var(--color-ink-3)" />
                <text x={BAR_X + BAR_WIDTH + 10} y={y(band.from) + 4} fontSize="12" fill="var(--color-ink-2)">
                  {RISK_LABEL[band.category]} {band.from}
                </text>
              </>
            )}
          </g>
        ))}
        {/* Today: solid pointer */}
        <path
          d={`M ${BAR_X - 3} ${y(today_kcfs)} l -9 -6 v 12 z`}
          fill="var(--color-ink)"
        />
        {/* Forecast peak: hollow pointer */}
        {peak_kcfs !== null && (
          <path
            d={`M ${BAR_X - 3} ${y(peak_kcfs)} l -9 -6 v 12 z`}
            fill="var(--color-sheet)"
            stroke="var(--color-ink)"
            strokeWidth="1.5"
          />
        )}
      </svg>
      <figcaption className="text-meta text-ink-2">
        FFD limits, thousand cusecs.
        <br />
        Solid marker: today. Hollow marker: forecast peak.
      </figcaption>
    </figure>
  );
}
