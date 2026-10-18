"use client";

import { NodeShape } from "@/components/map/NodeMarker";
import { RiskBadge } from "@/components/reach/RiskBadge";
import type { NodeState, ReachRisk, RiverNetwork, RiverNode } from "@/lib/api/types";
import { formatCfs } from "@/lib/format/units";
import { nodeById, reachesByRiver, reachName } from "@/lib/network";
import { RISK_COLOR, RISK_LABEL } from "@/lib/risk/categories";

interface RiverSchematicProps {
  network: RiverNetwork;
  risks: ReachRisk[];
  states: NodeState[];
  selectedReachId: string | null;
  onSelectReach: (reachId: string) => void;
}

/** The river system as a line diagram, upstream at the top. Each reach is a colored segment you can select. */
export function RiverSchematic({ network, risks, states, selectedReachId, onSelectReach }: RiverSchematicProps) {
  const nodes = nodeById(network);
  const riskByReach = new Map(risks.map((r) => [r.reach_id, r]));
  const stateByNode = new Map(states.map((s) => [s.node_id, s]));

  return (
    <div className="flex flex-col gap-6">
      {reachesByRiver(network).map(({ river, reaches }) => {
        const lastNode = nodes.get(reaches[reaches.length - 1].to_node_id);
        return (
          <section key={river} aria-label={`${river} river`}>
            <h3 className="px-4 pb-1 font-semibold">{river}</h3>
            <ol>
              {reaches.map((reach) => {
                const risk = riskByReach.get(reach.id);
                const category = risk?.category ?? "normal";
                const inflow = stateByNode.get(reach.from_node_id)?.inflow_cfs;
                const selected = reach.id === selectedReachId;
                return (
                  <li key={reach.id}>
                    <StationRow node={nodes.get(reach.from_node_id)} river={river} />
                    <button
                      type="button"
                      onClick={() => onSelectReach(reach.id)}
                      aria-pressed={selected}
                      aria-label={`${reachName(reach, nodes)}, ${RISK_LABEL[category]} risk`}
                      className={`flex w-full items-stretch gap-3 px-4 text-left hover:bg-wash ${selected ? "bg-wash" : ""}`}
                    >
                      <span className="flex w-3 shrink-0 justify-center">
                        <span
                          className={selected ? "w-1.25" : "w-0.75"}
                          style={{ backgroundColor: RISK_COLOR[category] }}
                        />
                      </span>
                      <span className="flex flex-1 items-baseline justify-between gap-2 py-2">
                        <RiskBadge category={category} />
                        {inflow && (
                          <span className="text-meta text-ink-2 tabular-nums">
                            <span className="font-semibold text-ink">{formatCfs(inflow.value)}</span> cfs
                          </span>
                        )}
                      </span>
                    </button>
                  </li>
                );
              })}
              <li>
                <StationRow node={lastNode} river={river} />
              </li>
            </ol>
          </section>
        );
      })}
    </div>
  );
}

function StationRow({ node, river }: { node: RiverNode | undefined; river: string }) {
  if (!node) return null;
  return (
    <div className="flex items-center gap-3 px-4">
      <span className="flex w-3 shrink-0 justify-center">
        <NodeShape type={node.type} size={10} />
      </span>
      <span className="font-medium">{node.name}</span>
      {node.river !== river && <span className="text-meta text-ink-3">on the {node.river}</span>}
    </div>
  );
}
