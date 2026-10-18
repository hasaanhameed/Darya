// SAMPLE DATA FOR LOCAL DEVELOPMENT ONLY.
// Used when NEXT_PUBLIC_USE_SAMPLE_DATA=true, while the backend has no endpoints. The UI shows a
// "Sample data, not live" banner whenever it is on.
// - Node list, coordinates and FFD flood limits come from docs/DATA.md.
// - The river graph comes from docs/ARCHITECTURE.md.
// - Every flow, level, forecast, reason and alert below is MADE UP.

import type {
  Alert,
  FloodLimits,
  NodeState,
  NodeType,
  Reach,
  ReachRisk,
  ReachSeries,
  RiverNetwork,
  RiverNode,
} from "@/lib/api/types";
import { formatDay } from "@/lib/format/time";
import { categoryForFlow, riskRank, RISK_LABEL } from "@/lib/risk/categories";

function limits(
  low: number,
  medium: number,
  high: number,
  very_high: number,
  exceptional: number | null,
): FloodLimits {
  return { low_kcfs: low, medium_kcfs: medium, high_kcfs: high, very_high_kcfs: very_high, exceptional_kcfs: exceptional };
}

const UPPER_INDUS = limits(250, 375, 500, 650, 800);
const GUDDU_SUKKUR = limits(200, 350, 500, 700, 900);
const CHENAB_HEADWORKS = limits(100, 150, 200, 400, 600);
const MANGLA_RASUL = limits(75, 110, 150, 225, 300);
const SUTLEJ = limits(50, 80, 120, 175, 225);

function node(
  id: string,
  name: string,
  river: string,
  type: NodeType,
  lat: number,
  lon: number,
  flood_limits: FloodLimits | null,
): RiverNode {
  return { id, name, river, type, lat, lon, flood_limits };
}

const NODES: RiverNode[] = [
  node("tarbela", "Tarbela", "Indus", "dam", 34.09, 72.69, UPPER_INDUS),
  node("ghazi_barotha", "Ghazi Barotha", "Indus", "barrage", 33.98, 72.65, null),
  node("jinnah", "Jinnah", "Indus", "barrage", 32.92, 71.52, UPPER_INDUS),
  node("chashma", "Chashma", "Indus", "barrage", 32.43, 71.38, UPPER_INDUS),
  node("taunsa", "Taunsa", "Indus", "barrage", 30.51, 70.85, UPPER_INDUS),
  node("guddu", "Guddu", "Indus", "barrage", 28.42, 69.71, GUDDU_SUKKUR),
  node("sukkur", "Sukkur", "Indus", "barrage", 27.68, 68.85, GUDDU_SUKKUR),
  node("kotri", "Kotri", "Indus", "barrage", 25.44, 68.32, limits(200, 300, 450, 650, 800)),
  node("warsak", "Warsak", "Kabul", "dam", 34.17, 71.36, limits(40, 60, 100, 150, null)),
  node("nowshera", "Nowshera", "Kabul", "gauge", 34.01, 71.98, limits(60, 90, 140, 200, null)),
  node("mangla", "Mangla", "Jhelum", "dam", 33.14, 73.64, MANGLA_RASUL),
  node("rasul", "Rasul", "Jhelum", "barrage", 32.68, 73.52, MANGLA_RASUL),
  node("marala", "Marala", "Chenab", "headworks", 32.67, 74.46, CHENAB_HEADWORKS),
  node("khanki", "Khanki", "Chenab", "headworks", 32.41, 73.97, CHENAB_HEADWORKS),
  node("qadirabad", "Qadirabad", "Chenab", "headworks", 32.32, 73.69, CHENAB_HEADWORKS),
  node("trimmu", "Trimmu", "Chenab", "headworks", 31.14, 72.15, limits(150, 200, 300, 450, 600)),
  node("balloki", "Balloki", "Ravi", "headworks", 31.22, 73.86, limits(40, 65, 90, 135, 180)),
  node("sidhnai", "Sidhnai", "Ravi", "headworks", 30.6, 72.1, limits(30, 46, 60, 90, 130)),
  node("sulemanki", "Sulemanki", "Sutlej", "headworks", 30.38, 73.87, SUTLEJ),
  node("islam", "Islam", "Sutlej", "headworks", 29.83, 72.55, SUTLEJ),
  node("panjnad", "Panjnad", "Panjnad", "headworks", 29.35, 71.02, limits(150, 250, 400, 550, 700)),
];

function reach(river: string, from: string, to: string): Reach {
  return { id: `${from}-${to}`, river, from_node_id: from, to_node_id: to };
}

const REACHES: Reach[] = [
  reach("Indus", "tarbela", "ghazi_barotha"),
  reach("Indus", "ghazi_barotha", "jinnah"),
  reach("Indus", "jinnah", "chashma"),
  reach("Indus", "chashma", "taunsa"),
  reach("Indus", "taunsa", "guddu"),
  reach("Indus", "guddu", "sukkur"),
  reach("Indus", "sukkur", "kotri"),
  reach("Kabul", "warsak", "nowshera"),
  reach("Kabul", "nowshera", "jinnah"),
  reach("Jhelum", "mangla", "rasul"),
  reach("Jhelum", "rasul", "trimmu"),
  reach("Chenab", "marala", "khanki"),
  reach("Chenab", "khanki", "qadirabad"),
  reach("Chenab", "qadirabad", "trimmu"),
  reach("Chenab", "trimmu", "panjnad"),
  reach("Ravi", "balloki", "sidhnai"),
  reach("Ravi", "sidhnai", "panjnad"),
  reach("Sutlej", "sulemanki", "islam"),
  reach("Sutlej", "islam", "panjnad"),
  reach("Panjnad", "panjnad", "guddu"),
];

// Made-up inflow today and forecast peak, in thousands of cusecs.
const FLOW_KCFS: Record<string, { today: number; peak: number }> = {
  tarbela: { today: 262, peak: 290 },
  ghazi_barotha: { today: 248, peak: 270 },
  jinnah: { today: 331, peak: 368 },
  chashma: { today: 352, peak: 401 },
  taunsa: { today: 418, peak: 512 },
  guddu: { today: 371, peak: 468 },
  sukkur: { today: 318, peak: 362 },
  kotri: { today: 214, peak: 246 },
  warsak: { today: 52, peak: 58 },
  nowshera: { today: 83, peak: 96 },
  mangla: { today: 61, peak: 66 },
  rasul: { today: 57, peak: 79 },
  marala: { today: 162, peak: 214 },
  khanki: { today: 141, peak: 188 },
  qadirabad: { today: 133, peak: 176 },
  trimmu: { today: 176, peak: 221 },
  balloki: { today: 28, peak: 31 },
  sidhnai: { today: 19, peak: 21 },
  sulemanki: { today: 34, peak: 39 },
  islam: { today: 29, peak: 33 },
  panjnad: { today: 238, peak: 284 },
};

// Made-up reservoir levels for the two big dams.
const LEVEL_FT: Record<string, number> = { tarbela: 1546.3, mangla: 1238.4 };

const DAY_MS = 24 * 60 * 60 * 1000;

/** Today's date in Pakistan, as "YYYY-MM-DD". */
function todayInPkt(): string {
  return new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function addDays(date: string, days: number): string {
  return new Date(Date.parse(`${date}T00:00:00Z`) + days * DAY_MS).toISOString().slice(0, 10);
}

const nodesById = new Map(NODES.map((n) => [n.id, n]));

function buildState(today: string): NodeState[] {
  const readingAt = `${today}T01:00:00Z`; // 06:00 PKT gauge reading
  return NODES.map((n) => {
    const inflow_cfs = FLOW_KCFS[n.id].today * 1000;
    const isWapda = n.type === "dam" || n.id === "ghazi_barotha" || n.id === "jinnah" || n.id === "chashma";
    const source = isWapda ? "WAPDA (sample)" : "PMD-FFD (sample)";
    const observed_at = isWapda ? today : readingAt;
    return {
      node_id: n.id,
      inflow_cfs: { value: inflow_cfs, observed_at, source },
      outflow_cfs: { value: Math.round(inflow_cfs * 0.96), observed_at, source },
      level_ft: n.id in LEVEL_FT ? { value: LEVEL_FT[n.id], observed_at, source } : null,
    };
  });
}

function buildSeries(reachId: string, today: string): ReachSeries {
  const r = REACHES.find((x) => x.id === reachId) ?? REACHES[0];
  const { today: now, peak } = FLOW_KCFS[r.from_node_id];
  const observed = Array.from({ length: 14 }, (_, i) => {
    const daysAgo = 13 - i;
    const rise = 0.62 + 0.38 * Math.pow(i / 13, 1.6);
    // Today's point matches today's reading exactly.
    const wiggle = daysAgo === 0 ? 1 : 1 + 0.025 * Math.sin(i * 1.7);
    return { date: addDays(today, -daysAgo), flow_cfs: Math.round(now * rise * wiggle * 1000) };
  });
  const shape = [0.55, 1, 0.8];
  const forecast = shape.map((s, i) => {
    const flow = now + (peak - now) * s;
    const spread = 0.05 * (i + 1);
    return {
      date: addDays(today, i + 1),
      flow_cfs: Math.round(flow * 1000),
      low_cfs: Math.round(flow * (1 - spread) * 1000),
      high_cfs: Math.round(flow * (1 + spread) * 1000),
    };
  });
  return {
    reach_id: r.id,
    node_id: r.from_node_id,
    observed,
    forecast,
    model: "Sample curve",
    issued_at: `${today}T02:00:00Z`,
  };
}

function buildRisk(today: string): ReachRisk[] {
  return REACHES.map((r) => {
    const from = nodesById.get(r.from_node_id)!;
    const { today: now, peak } = FLOW_KCFS[from.id];
    const lim = from.flood_limits;
    const category = lim ? categoryForFlow(now, lim) : "normal";
    const peak_category = lim ? categoryForFlow(peak, lim) : "normal";
    const reasons: string[] = [];
    if (peak > now * 1.05) reasons.push(`Flow at ${from.name} has been rising for 5 days.`);
    if (riskRank(peak_category) > riskRank(category)) {
      reasons.push(`Forecast peak passes the ${RISK_LABEL[peak_category]} limit for ${from.name}.`);
    }
    if (!lim) reasons.push(`FFD publishes no flood limits for ${from.name}.`);
    return {
      reach_id: r.id,
      category,
      peak_category,
      peak_on: addDays(today, 2),
      peak_range_low: lim ? categoryForFlow(peak * 0.9, lim) : "normal",
      peak_range_high: lim ? categoryForFlow(peak * 1.1, lim) : "normal",
      reasons,
      assessed_at: `${today}T02:00:00Z`,
    };
  });
}

function buildAlerts(today: string): Alert[] {
  return buildRisk(today)
    .filter((risk) => riskRank(risk.peak_category) > riskRank(risk.category) && riskRank(risk.peak_category) >= riskRank("medium"))
    .sort((a, b) => riskRank(b.peak_category) - riskRank(a.peak_category))
    .map((risk) => ({
      id: `sample-${risk.reach_id}`,
      reach_id: risk.reach_id,
      category: risk.peak_category,
      message: `Forecast to reach ${RISK_LABEL[risk.peak_category]} on ${formatDay(risk.peak_on)}.`,
      status: "active",
      issued_at: `${today}T02:00:00Z`,
    }));
}

export function sampleResponse(path: string): unknown {
  const today = todayInPkt();
  if (path === "/network") return { nodes: NODES, reaches: REACHES } satisfies RiverNetwork;
  if (path === "/state") return buildState(today);
  if (path === "/risk") return buildRisk(today);
  if (path.startsWith("/alerts")) return buildAlerts(today);
  const series = path.match(/^\/reaches\/([^/]+)\/series$/);
  if (series) return buildSeries(series[1], today);
  throw new Error(`No sample data for ${path}`);
}
