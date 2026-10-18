// Response shapes the dashboard expects from the FastAPI backend.
// Hand-written until the backend publishes /openapi.json (ADR-012); then they are replaced by the generated client.
// Units follow the source and are part of every field name. Timestamps are ISO 8601 in UTC.

export type RiskCategory = "normal" | "low" | "medium" | "high" | "very_high" | "exceptional";

export type NodeType = "dam" | "barrage" | "headworks" | "gauge" | "confluence";

/** PMD-FFD discharge limits for a site, in thousands of cusecs. Some sites have no Exceptional limit. */
export interface FloodLimits {
  low_kcfs: number;
  medium_kcfs: number;
  high_kcfs: number;
  very_high_kcfs: number;
  exceptional_kcfs: number | null;
}

export interface RiverNode {
  id: string; // stable slug, e.g. "tarbela"
  name: string;
  river: string;
  type: NodeType;
  lat: number;
  lon: number;
  flood_limits: FloodLimits | null; // null when FFD publishes no limits for the site
}

/** The stretch of river between two consecutive nodes, running upstream to downstream. */
export interface Reach {
  id: string; // e.g. "taunsa-guddu"
  river: string;
  from_node_id: string;
  to_node_id: string;
}

export interface RiverNetwork {
  nodes: RiverNode[];
  reaches: Reach[];
}

/** One measured value with its provenance. */
export interface Reading {
  value: number;
  // A date ("2026-10-17") for daily reports such as WAPDA's, otherwise a UTC timestamp.
  observed_at: string;
  source: string;
}

/** The latest known values at a node (twin state). */
export interface NodeState {
  node_id: string;
  inflow_cfs: Reading | null;
  outflow_cfs: Reading | null;
  level_ft: Reading | null;
}

/** Current risk for a reach, plus the forecast peak over the next 3 days. */
export interface ReachRisk {
  reach_id: string;
  category: RiskCategory;
  peak_category: RiskCategory;
  peak_on: string; // date of the forecast peak
  // The uncertainty range of the peak, as categories.
  peak_range_low: RiskCategory;
  peak_range_high: RiskCategory;
  reasons: string[];
  assessed_at: string;
}

/** Observed and forecast discharge for a reach, measured at its upstream node. */
export interface ReachSeries {
  reach_id: string;
  node_id: string;
  observed: { date: string; flow_cfs: number }[];
  forecast: { date: string; flow_cfs: number; low_cfs: number; high_cfs: number }[];
  model: string;
  issued_at: string;
}

export interface Alert {
  id: string;
  reach_id: string;
  category: RiskCategory;
  message: string;
  status: "active" | "closed";
  issued_at: string;
}
