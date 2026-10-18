"use client";

import { useState } from "react";

import type { Alert, RiverNetwork } from "@/lib/api/types";
import { nodeById, reachName } from "@/lib/network";
import { RISK_COLOR, RISK_LABEL, riskRank } from "@/lib/risk/categories";

// The rail shows the most severe alerts first and keeps room for the river schematic below.
const COLLAPSED_COUNT = 3;

interface AlertListProps {
  alerts: Alert[];
  network: RiverNetwork;
  onSelectReach: (reachId: string) => void;
}

export function AlertList({ alerts, network, onSelectReach }: AlertListProps) {
  const [expanded, setExpanded] = useState(false);
  const nodes = nodeById(network);
  const reaches = new Map(network.reaches.map((r) => [r.id, r]));

  if (alerts.length === 0) {
    return <p className="px-4 py-3 text-ink-2">No active alerts.</p>;
  }

  const sorted = [...alerts].sort((a, b) => riskRank(b.category) - riskRank(a.category));
  const visible = expanded ? sorted : sorted.slice(0, COLLAPSED_COUNT);
  const hiddenCount = sorted.length - visible.length;

  return (
    <div>
      <ul className="divide-y divide-rule">
        {visible.map((alert) => {
          const reach = reaches.get(alert.reach_id);
          return (
            <li key={alert.id}>
              <button
                type="button"
                onClick={() => onSelectReach(alert.reach_id)}
                className="flex w-full items-start gap-2.5 px-4 py-2 text-left hover:bg-shallows-2"
              >
                {/* The color square is read with the key above; screen readers get the level as text. */}
                <span
                  className="mt-1.25 size-2.5 shrink-0 rounded-[2px]"
                  style={{ backgroundColor: RISK_COLOR[alert.category] }}
                  title={`${RISK_LABEL[alert.category]} risk`}
                />
                <span className="flex flex-col">
                  <span className="font-medium">{reach ? reachName(reach, nodes) : alert.reach_id}</span>
                  <span className="sr-only">{RISK_LABEL[alert.category]} risk.</span>
                  <span className="text-meta text-ink-2">{alert.message}</span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {sorted.length > COLLAPSED_COUNT && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
          className="px-4 py-2 font-medium text-channel hover:underline"
        >
          {expanded ? "Show fewer" : `Show ${hiddenCount} more`}
        </button>
      )}
    </div>
  );
}
