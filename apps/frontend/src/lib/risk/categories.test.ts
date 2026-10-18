import { describe, expect, it } from "vitest";

import type { FloodLimits } from "@/lib/api/types";
import { categoryForFlow } from "@/lib/risk/categories";

// Tarbela's limits from the FFD table in docs/DATA.md.
const TARBELA: FloodLimits = { low_kcfs: 250, medium_kcfs: 375, high_kcfs: 500, very_high_kcfs: 650, exceptional_kcfs: 800 };
// Warsak has no Exceptional limit.
const WARSAK: FloodLimits = { low_kcfs: 40, medium_kcfs: 60, high_kcfs: 100, very_high_kcfs: 150, exceptional_kcfs: null };

describe("categoryForFlow", () => {
  it("is normal below the low limit", () => {
    expect(categoryForFlow(249, TARBELA)).toBe("normal");
  });

  it("counts a flow exactly at a limit as that category", () => {
    expect(categoryForFlow(250, TARBELA)).toBe("low");
    expect(categoryForFlow(500, TARBELA)).toBe("high");
    expect(categoryForFlow(800, TARBELA)).toBe("exceptional");
  });

  it("stops at very high when a site has no exceptional limit", () => {
    expect(categoryForFlow(900, WARSAK)).toBe("very_high");
  });
});
