"use client";

import { XIcon } from "@phosphor-icons/react";

import { TimeSeriesWithBand } from "@/components/charts/TimeSeriesWithBand";
import { RiskBadge } from "@/components/reach/RiskBadge";
import { ThresholdStaff } from "@/components/reach/ThresholdStaff";
import { Skeleton } from "@/components/ui/Skeleton";
import { useReachSeries } from "@/lib/api/hooks";
import type { NodeState, Reach, ReachRisk, Reading, RiverNode } from "@/lib/api/types";
import { formatDay, formatObservedAt } from "@/lib/format/time";
import { formatCfs, formatFt } from "@/lib/format/units";
import { RISK_LABEL } from "@/lib/risk/categories";

interface ReachPanelProps {
  reach: Reach;
  name: string;
  fromNode: RiverNode;
  risk: ReachRisk | undefined;
  state: NodeState | undefined;
  onClose: () => void;
}

export function ReachPanel({ reach, name, fromNode, risk, state, onClose }: ReachPanelProps) {
  const series = useReachSeries(reach.id);
  const peakCfs = series.data ? Math.max(...series.data.forecast.map((p) => p.flow_cfs)) : null;
  const sources = [state?.inflow_cfs, state?.outflow_cfs, state?.level_ft].filter((r): r is Reading => r !== null && r !== undefined);
  const sourceNames = [...new Set(sources.map((r) => r.source))];

  return (
    <aside
      aria-label={`${name} details`}
      className="absolute inset-y-0 right-0 z-10 flex w-90 flex-col overflow-y-auto border-l border-rule bg-sheet"
    >
      <header className="flex items-start justify-between gap-4 border-b border-rule bg-shallows px-4 py-3">
        <div>
          <h2 className="text-title font-semibold">{name}</h2>
          <p className="text-ink-2">{reach.river} river</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close reach details"
          className="-m-2 rounded-control p-2 text-ink-2 hover:bg-shallows-2 hover:text-ink"
        >
          <XIcon size={18} />
        </button>
      </header>

      <section className="flex flex-col gap-1 px-4 pt-4">
        {risk ? (
          <>
            <RiskBadge category={risk.category} size="focal" />
            {risk.peak_category !== risk.category ? (
              <p>
                Forecast to reach <span className="font-semibold">{RISK_LABEL[risk.peak_category]}</span> on{" "}
                {formatDay(risk.peak_on)}.
              </p>
            ) : (
              <p>Forecast to stay {RISK_LABEL[risk.category]} for the next 3 days.</p>
            )}
            <p className="text-ink-2">
              Likely range at the peak:{" "}
              {risk.peak_range_low === risk.peak_range_high
                ? RISK_LABEL[risk.peak_range_low]
                : `${RISK_LABEL[risk.peak_range_low]} to ${RISK_LABEL[risk.peak_range_high]}`}
              .
            </p>
          </>
        ) : (
          <p className="text-ink-2">No risk assessment yet for this reach.</p>
        )}
      </section>

      {risk && risk.reasons.length > 0 && (
        <section className="px-4 pt-6">
          <h3 className="font-semibold">Why</h3>
          <ul className="mt-1 flex list-disc flex-col gap-1 pl-5">
            {risk.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="px-4 pt-6">
        <h3 className="font-semibold">Now at {fromNode.name}</h3>
        {sources.length > 0 ? (
          <table className="mt-1 w-full tabular-nums">
            <thead className="sr-only">
              <tr>
                <th>Measure</th>
                <th>Value</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule">
              <ValueRow label="Flow in" reading={state?.inflow_cfs} unit="cusecs" format={formatCfs} />
              <ValueRow label="Flow out" reading={state?.outflow_cfs} unit="cusecs" format={formatCfs} />
              <ValueRow label="Water level" reading={state?.level_ft} unit="ft" format={formatFt} />
            </tbody>
          </table>
        ) : (
          <p className="mt-1 text-ink-2">No readings yet for {fromNode.name}.</p>
        )}
      </section>

      <section className="flex gap-4 px-4 pt-6">
        {fromNode.flood_limits && state?.inflow_cfs ? (
          <ThresholdStaff
            limits={fromNode.flood_limits}
            today_kcfs={state.inflow_cfs.value / 1000}
            peak_kcfs={peakCfs !== null ? peakCfs / 1000 : null}
          />
        ) : (
          <p className="text-ink-2">FFD publishes no flood limits for {fromNode.name}.</p>
        )}
      </section>

      <section className="px-4 pt-6">
        <h3 className="font-semibold">Flow at {fromNode.name}, past 2 weeks and next 3 days</h3>
        <div className="mt-2">
          {series.isPending && <Skeleton className="h-48 w-full" />}
          {series.isError && <p className="text-ink-2">{series.error.message}</p>}
          {series.data && <TimeSeriesWithBand series={series.data} />}
        </div>
      </section>

      <footer className="mt-auto px-4 py-6 text-meta text-ink-3">
        {sourceNames.length > 0 ? `Sources: ${sourceNames.join(", ")}.` : "No sources yet."}
        {risk && ` Assessed ${formatObservedAt(risk.assessed_at)}.`}
      </footer>
    </aside>
  );
}

interface ValueRowProps {
  label: string;
  reading: Reading | null | undefined;
  unit: string;
  format: (value: number) => string;
}

function ValueRow({ label, reading, unit, format }: ValueRowProps) {
  if (!reading) return null;
  return (
    <tr>
      <td className="py-1.5 font-medium text-ink-2">{label}</td>
      <td className="py-1.5 text-right">
        <span className="font-semibold">{format(reading.value)}</span> <span className="text-meta text-ink-2">{unit}</span>
      </td>
      <td className="py-1.5 text-right text-meta text-ink-3">{formatObservedAt(reading.observed_at)}</td>
    </tr>
  );
}
