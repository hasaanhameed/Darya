import type { Reach, RiverNetwork, RiverNode } from "@/lib/api/types";

/** The order rivers are listed in the schematic: the main stem first, then tributaries west to east. */
const RIVER_ORDER = ["Indus", "Kabul", "Jhelum", "Chenab", "Ravi", "Sutlej", "Panjnad"];

export function nodeById(network: RiverNetwork): Map<string, RiverNode> {
  return new Map(network.nodes.map((node) => [node.id, node]));
}

/** "Taunsa to Guddu" */
export function reachName(reach: Reach, nodes: Map<string, RiverNode>): string {
  const from = nodes.get(reach.from_node_id)?.name ?? reach.from_node_id;
  const to = nodes.get(reach.to_node_id)?.name ?? reach.to_node_id;
  return `${from} to ${to}`;
}

/** Each river's reaches in upstream-to-downstream order. */
export function reachesByRiver(network: RiverNetwork): { river: string; reaches: Reach[] }[] {
  const rivers = [...new Set(network.reaches.map((reach) => reach.river))].sort(
    (a, b) => riverPosition(a) - riverPosition(b),
  );

  return rivers.map((river) => {
    const riverReaches = network.reaches.filter((reach) => reach.river === river);
    const downstreamIds = new Set(riverReaches.map((reach) => reach.to_node_id));
    const ordered: Reach[] = [];
    // Start at the reach whose upstream node isn't fed by another reach of the same river.
    let current = riverReaches.find((reach) => !downstreamIds.has(reach.from_node_id));
    while (current) {
      ordered.push(current);
      const nextFrom: string = current.to_node_id;
      current = riverReaches.find((reach) => reach.from_node_id === nextFrom);
    }
    return { river, reaches: ordered };
  });
}

function riverPosition(river: string): number {
  const index = RIVER_ORDER.indexOf(river);
  return index === -1 ? RIVER_ORDER.length : index;
}
