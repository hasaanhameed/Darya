"use client";

import { NodeShape } from "@/components/map/NodeMarker";
import { Collapsible } from "@/components/ui/Collapsible";
import type { NodeState, ReachRisk, RiskCategory, RiverNetwork, RiverNode } from "@/lib/api/types";
import { formatObservedAt } from "@/lib/format/time";
import { formatCfs } from "@/lib/format/units";
import { nodeById, reachesByRiver, reachName } from "@/lib/network";
import { RISK_COLOR, RISK_LABEL, riskRank } from "@/lib/risk/categories";

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
    <div className="flex flex-col py-1">
      {reachesByRiver(network).map(({ river, reaches }) => {
        const lastNode = nodes.get(reaches[reaches.length - 1].to_node_id);
        const categories = reaches.map((r) => riskByReach.get(r.id)?.category ?? "normal");
        const worst = categories.reduce<RiskCategory>((a, b) => (riskRank(b) > riskRank(a) ? b : a), "normal");
        return (
          <Collapsible
            key={river}
            level="group"
            title={river}
            aside={
              <span className="flex items-center gap-1.5 text-meta font-normal text-ink-3">
                Highest
                <span
                  className="size-2.5 rounded-[2px]"
                  style={{ backgroundColor: RISK_COLOR[worst] }}
                  title={`${RISK_LABEL[worst]} risk`}
                />
                <span className="sr-only">{RISK_LABEL[worst]}</span>
              </span>
            }
          >
            <ol className="pb-2">
              {reaches.map((reach, index) => {
                const category = categories[index];
                const inflow = stateByNode.get(reach.from_node_id)?.inflow_cfs;
                const fromName = nodes.get(reach.from_node_id)?.name;
                const selected = reach.id === selectedReachId;
                return (
                  <li key={reach.id}>
                    <StationRow node={nodes.get(reach.from_node_id)} river={river} />
                    <button
                      type="button"
                      onClick={() => onSelectReach(reach.id)}
                      aria-pressed={selected}
                      aria-label={`${reachName(reach, nodes)}, ${RISK_LABEL[category]} risk`}
                      title={`${reachName(reach, nodes)}: ${RISK_LABEL[category]} risk`}
                      className={`flex w-full items-stretch gap-3 px-4 text-left ${selected ? "bg-sheet" : "hover:bg-shallows-2"}`}
                    >
                      <span className="flex w-3 shrink-0 justify-center">
                        <span className={selected ? "w-1.5" : "w-1"} style={{ backgroundColor: RISK_COLOR[category] }} />
                      </span>
                      {inflow ? (
                        <span
                          className="flex flex-1 items-baseline justify-between gap-2 py-2 tabular-nums"
                          title={`Water flowing into ${fromName}, ${formatObservedAt(inflow.observed_at)}`}
                        >
                          <span className="text-meta text-ink-3">Flow in</span>
                          <span>
                            <span className="font-semibold">{formatCfs(inflow.value)}</span>{" "}
                            <span className="text-meta text-ink-2">cusecs</span>
                          </span>
                        </span>
                      ) : (
                        <span className="flex-1 py-2 text-meta text-ink-3">No flow reading</span>
                      )}
                    </button>
                  </li>
                );
              })}
              <li>
                <StationRow node={lastNode} river={river} />
              </li>
            </ol>
          </Collapsible>
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
