import type { NodeType } from "@/lib/api/types";

/** Small shapes by node type (DESIGN.md): dam square, barrage/headworks diamond, gauge circle, confluence dot. */
export function NodeShape({ type, size = 12 }: { type: NodeType; size?: number }) {
  const common = { fill: "var(--color-sheet)", stroke: "var(--color-ink)", strokeWidth: 1.5 };
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" aria-hidden>
      {type === "dam" && <rect x="1.5" y="1.5" width="9" height="9" {...common} />}
      {(type === "barrage" || type === "headworks") && <path d="M6 1 L11 6 L6 11 L1 6 Z" {...common} />}
      {type === "gauge" && <circle cx="6" cy="6" r="4.5" {...common} />}
      {type === "confluence" && <circle cx="6" cy="6" r="2.5" fill="var(--color-ink)" />}
    </svg>
  );
}
