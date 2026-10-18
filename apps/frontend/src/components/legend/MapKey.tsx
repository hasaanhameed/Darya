import { NodeShape } from "@/components/map/NodeMarker";
import type { NodeType, ReachRisk } from "@/lib/api/types";
import { RISK_COLOR, RISK_LABEL, RISK_ORDER, riskRank } from "@/lib/risk/categories";

const STATION_TYPES: { type: NodeType; label: string }[] = [
  { type: "dam", label: "Dam" },
  { type: "barrage", label: "Barrage" },
  { type: "gauge", label: "Gauge" },
];

/** What the colors, shapes and units on the page mean, plus a strip with one cell per reach. */
export function MapKey({ risks }: { risks: ReachRisk[] }) {
  const sorted = [...risks].sort((a, b) => riskRank(b.category) - riskRank(a.category));
  const countByCategory = new Map(RISK_ORDER.map((c) => [c, risks.filter((r) => r.category === c).length]));

  return (
    <div className="flex flex-col gap-3 px-4 py-3">
      <div>
        <p className="font-medium text-ink-2">{risks.length} reaches, most at risk first</p>
        <div aria-hidden className="mt-1.5 flex h-3 gap-0.5">
          {sorted.map((r) => (
            <span key={r.reach_id} className="flex-1 rounded-[2px]" style={{ backgroundColor: RISK_COLOR[r.category] }} />
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-medium text-ink-2">Flood risk level</h3>
        <ul className="mt-1 grid grid-cols-2 gap-x-4 gap-y-1">
          {RISK_ORDER.map((category) => (
            <li key={category} className="flex items-center gap-2">
              <span aria-hidden className="size-2.5 shrink-0 rounded-[2px]" style={{ backgroundColor: RISK_COLOR[category] }} />
              <span className="flex-1">{RISK_LABEL[category]}</span>
              <span className="text-meta text-ink-3 tabular-nums" aria-label={`${countByCategory.get(category)} reaches`}>
                {countByCategory.get(category)}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-1 text-meta text-ink-3">Levels follow the PMD-FFD flood categories.</p>
      </div>

      <div>
        <h3 className="font-medium text-ink-2">Stations</h3>
        <ul className="mt-1 flex gap-4">
          {STATION_TYPES.map(({ type, label }) => (
            <li key={type} className="flex items-center gap-1.5">
              <NodeShape type={type} size={10} />
              {label}
            </li>
          ))}
        </ul>
      </div>

      <p className="text-meta text-ink-2">
        Flow is in <span className="font-semibold text-ink">cusecs</span>, cubic feet of water per second. One cusec is
        about 28 litres a second.
      </p>
    </div>
  );
}
