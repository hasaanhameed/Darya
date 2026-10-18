"use client";

import { useState } from "react";

import { RiskBadge } from "@/components/reach/RiskBadge";
import type { Alert, RiverNetwork } from "@/lib/api/types";
import { nodeById, reachName } from "@/lib/network";
import { riskRank } from "@/lib/risk/categories";

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
    return <p className="px-4 text-ink-2">No active alerts.</p>;
  }

  const sorted = [...alerts].sort((a, b) => riskRank(b.category) - riskRank(a.category));
  const visible = expanded ? sorted : sorted.slice(0, COLLAPSED_COUNT);
  const hiddenCount = sorted.length - visible.length;

  return (
    <div>
      <ul className="divide-y divide-rule border-y border-rule">
        {visible.map((alert) => {
          const reach = reaches.get(alert.reach_id);
          return (
            <li key={alert.id}>
              <button
                type="button"
                onClick={() => onSelectReach(alert.reach_id)}
                className="flex w-full flex-col px-4 py-2 text-left hover:bg-wash"
              >
                <span className="flex items-baseline justify-between gap-2">
                  <span className="font-medium">{reach ? reachName(reach, nodes) : alert.reach_id}</span>
                  <RiskBadge category={alert.category} />
                </span>
                <span className="text-meta text-ink-2">{alert.message}</span>
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
          className="px-4 pt-2 font-medium text-channel hover:underline"
        >
          {expanded ? "Show fewer" : `Show ${hiddenCount} more`}
        </button>
      )}
    </div>
  );
}
