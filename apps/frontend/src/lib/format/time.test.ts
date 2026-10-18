import { describe, expect, it } from "vitest";

import { formatDay, formatObservedAt } from "@/lib/format/time";

describe("formatObservedAt", () => {
  it("shows a UTC timestamp in PKT (UTC+5)", () => {
    expect(formatObservedAt("2026-10-17T01:00:00Z")).toBe("17 Oct, 06:00 PKT");
  });

  it("moves a late-evening UTC time to the next day in PKT", () => {
    expect(formatObservedAt("2026-10-17T20:30:00Z")).toBe("18 Oct, 01:30 PKT");
  });

  it("shows a daily report date as that day, without a time", () => {
    expect(formatObservedAt("2026-10-17")).toBe("17 Oct");
  });
});

describe("formatDay", () => {
  it("does not shift a plain date across midnight", () => {
    expect(formatDay("2026-10-01")).toBe("1 Oct");
  });
});
