import { describe, expect, it } from "vitest";

import type { RiverNetwork } from "@/lib/api/types";
import { reachesByRiver } from "@/lib/network";

const network: RiverNetwork = {
  nodes: [],
  // Deliberately out of order.
  reaches: [
    { id: "chashma-taunsa", river: "Indus", from_node_id: "chashma", to_node_id: "taunsa" },
    { id: "warsak-nowshera", river: "Kabul", from_node_id: "warsak", to_node_id: "nowshera" },
    { id: "tarbela-jinnah", river: "Indus", from_node_id: "tarbela", to_node_id: "jinnah" },
    { id: "jinnah-chashma", river: "Indus", from_node_id: "jinnah", to_node_id: "chashma" },
  ],
};

describe("reachesByRiver", () => {
  it("orders each river's reaches from upstream to downstream", () => {
    const indus = reachesByRiver(network).find((r) => r.river === "Indus");
    expect(indus?.reaches.map((r) => r.id)).toEqual(["tarbela-jinnah", "jinnah-chashma", "chashma-taunsa"]);
  });

  it("lists the Indus before its tributaries", () => {
    expect(reachesByRiver(network).map((r) => r.river)).toEqual(["Indus", "Kabul"]);
  });
});
