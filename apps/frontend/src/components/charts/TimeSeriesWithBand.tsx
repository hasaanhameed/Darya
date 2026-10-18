"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";

import type { ReachSeries } from "@/lib/api/types";
import { formatDay } from "@/lib/format/time";
import { formatCfs } from "@/lib/format/units";

interface ChartRow {
  date: string;
  observed?: number;
  forecast?: number;
  band?: [number, number];
}

const AXIS_TICK = { fontSize: 12, fill: "var(--color-ink-3)" };

/** Observed flow (solid), forecast flow (dashed) and its uncertainty band, in thousand cusecs. */
export function TimeSeriesWithBand({ series }: { series: ReachSeries }) {
  const lastObserved = series.observed[series.observed.length - 1];
  const rows: ChartRow[] = series.observed.map((point) => ({ date: point.date, observed: point.flow_cfs / 1000 }));
  // The forecast line starts at the last observed value so the two lines connect.
  if (lastObserved) rows[rows.length - 1].forecast = lastObserved.flow_cfs / 1000;
  for (const point of series.forecast) {
    rows.push({
      date: point.date,
      forecast: point.flow_cfs / 1000,
      band: [point.low_cfs / 1000, point.high_cfs / 1000],
    });
  }

  return (
    <figure className="flex flex-col gap-2">
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
            <CartesianGrid vertical={false} stroke="var(--color-rule)" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDay}
              tick={AXIS_TICK}
              tickLine={false}
              axisLine={{ stroke: "var(--color-rule-strong)" }}
              interval="preserveStartEnd"
              minTickGap={24}
            />
            <YAxis tick={AXIS_TICK} tickLine={false} axisLine={false} width={44} />
            <Tooltip content={ChartTooltip} cursor={{ stroke: "var(--color-ink-3)", strokeWidth: 1 }} />
            {lastObserved && (
              <ReferenceLine
                x={lastObserved.date}
                stroke="var(--color-ink-3)"
                label={{ value: "Today", position: "insideTopLeft", fontSize: 12, fill: "var(--color-ink-2)" }}
              />
            )}
            <Area dataKey="band" stroke="none" fill="var(--color-channel)" fillOpacity={0.16} isAnimationActive={false} />
            <Line dataKey="observed" stroke="var(--color-channel)" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line
              dataKey="forecast"
              stroke="var(--color-channel)"
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="text-meta text-ink-2">
        Flow in thousand cusecs. Solid: observed. Dashed: forecast, with its likely range shaded. Model: {series.model}.
      </figcaption>
    </figure>
  );
}

function ChartTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload as ChartRow;
  return (
    <div className="rounded-control border border-rule bg-sheet px-2 py-1 text-meta tabular-nums">
      <div className="font-medium">{formatDay(row.date)}</div>
      {row.observed !== undefined && row.band === undefined && (
        <div>Observed {formatCfs(row.observed * 1000)} cusecs</div>
      )}
      {row.band && (
        <>
          <div>Forecast {formatCfs((row.forecast ?? 0) * 1000)} cusecs</div>
          <div className="text-ink-2">
            Range {formatCfs(row.band[0] * 1000)} to {formatCfs(row.band[1] * 1000)} cusecs
          </div>
        </>
      )}
    </div>
  );
}
