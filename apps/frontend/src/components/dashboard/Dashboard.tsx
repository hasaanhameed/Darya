"use client";

import dynamic from "next/dynamic";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { AlertList } from "@/components/alerts/AlertList";
import { RAIL_WIDTH, RailResizeHandle, useRailWidth } from "@/components/dashboard/RailResizeHandle";
import { MapKey } from "@/components/legend/MapKey";
import { ReachPanel } from "@/components/reach/ReachPanel";
import { RiverSchematic } from "@/components/schematic/RiverSchematic";
import { Collapsible } from "@/components/ui/Collapsible";
import { Skeleton } from "@/components/ui/Skeleton";
import { useActiveAlerts, useNetwork, useNodeStates, useReachRisks } from "@/lib/api/hooks";
import { nodeById, reachName } from "@/lib/network";

// MapLibre needs the browser, so the map is never rendered on the server (ADR-002, ADR-010).
const RiverMap = dynamic(() => import("@/components/map/RiverMap"), {
  ssr: false,
  loading: () => <Skeleton className="size-full rounded-none" />,
});

/** The map dashboard: a resizable rail (alerts, river schematic) on the left, the map with its key on the right. */
export function Dashboard() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const selectedReachId = searchParams.get("reach");

  const network = useNetwork();
  const risks = useReachRisks();
  const states = useNodeStates();
  const alerts = useActiveAlerts();
  const [railWidth, setRailWidth] = useRailWidth();

  // The selected reach lives in the URL, so a view can be shared by copying the link.
  function selectReach(reachId: string | null) {
    const params = new URLSearchParams(searchParams.toString());
    if (reachId) params.set("reach", reachId);
    else params.delete("reach");
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  if (network.isError) {
    return <ApiUnavailable message={network.error.message} />;
  }

  const nodes = network.data ? nodeById(network.data) : null;
  const selectedReach = network.data?.reaches.find((r) => r.id === selectedReachId);

  return (
    <div className="grid min-h-0 flex-1" style={{ gridTemplateColumns: `${railWidth}px 1fr` }}>
      <div className="relative min-h-0">
        <aside
          aria-label="Alerts and river system"
          className="flex h-full flex-col overflow-y-auto border-r border-rule bg-shallows"
        >
          <Collapsible title="Active alerts" aside={alerts.data && <Count value={alerts.data.length} />}>
            {alerts.isPending || !network.data ? (
              <div className="flex flex-col gap-2 p-4">
                <Skeleton className="h-12" />
                <Skeleton className="h-12" />
              </div>
            ) : alerts.isError ? (
              <p className="px-4 py-3 text-ink-2">{alerts.error.message}</p>
            ) : (
              <AlertList alerts={alerts.data} network={network.data} onSelectReach={selectReach} />
            )}
          </Collapsible>

          <Collapsible title="River system" aside={<span className="text-meta font-normal text-ink-2">upstream at top</span>}>
            {network.data && risks.data && states.data ? (
              <RiverSchematic
                network={network.data}
                risks={risks.data}
                states={states.data}
                selectedReachId={selectedReachId}
                onSelectReach={selectReach}
              />
            ) : (
              <div className="flex flex-col gap-2 p-4">
                {Array.from({ length: 8 }, (_, i) => (
                  <Skeleton key={i} className="h-8" />
                ))}
              </div>
            )}
          </Collapsible>
        </aside>
        <RailResizeHandle width={railWidth} onChange={setRailWidth} />
      </div>

      <div className="relative min-h-0">
        {network.data && risks.data ? (
          <RiverMap
            network={network.data}
            risks={risks.data}
            selectedReachId={selectedReachId}
            onSelectReach={selectReach}
          />
        ) : (
          <Skeleton className="size-full rounded-none" />
        )}

        {risks.data && (
          <div className="absolute top-3 left-3 z-10 w-64 overflow-hidden rounded-panel border border-rule bg-sheet">
            <Collapsible title="Key">
              <MapKey risks={risks.data} />
            </Collapsible>
          </div>
        )}

        {selectedReach && nodes && (
          <ReachPanel
            key={selectedReach.id}
            reach={selectedReach}
            name={reachName(selectedReach, nodes)}
            fromNode={nodes.get(selectedReach.from_node_id)!}
            risk={risks.data?.find((r) => r.reach_id === selectedReach.id)}
            state={states.data?.find((s) => s.node_id === selectedReach.from_node_id)}
            onClose={() => selectReach(null)}
          />
        )}
      </div>
    </div>
  );
}

function Count({ value }: { value: number }) {
  return (
    <span className="min-w-6 rounded-control bg-deep px-1.5 text-center text-meta font-semibold text-deep-ink tabular-nums">
      {value}
    </span>
  );
}

/** Shown when the backend can't be reached: say what happened and what to do, with no invented data. */
function ApiUnavailable({ message }: { message: string }) {
  return (
    <div className="mx-auto flex max-w-xl flex-col gap-2 px-4 py-16">
      <h2 className="text-page font-semibold">No river data to show</h2>
      <p>{message}</p>
      <p className="text-ink-2">
        The Darya API has no endpoints yet. To preview the dashboard with made-up values, set{" "}
        <code className="font-medium text-ink">NEXT_PUBLIC_USE_SAMPLE_DATA=true</code> in{" "}
        <code className="font-medium text-ink">apps/frontend/.env.local</code> and restart the dev server.
      </p>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="grid min-h-0 flex-1" style={{ gridTemplateColumns: `${RAIL_WIDTH.default}px 1fr` }}>
      <div className="flex flex-col gap-2 border-r border-rule bg-shallows p-4">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-12" />
        <Skeleton className="h-12" />
      </div>
      <Skeleton className="size-full rounded-none" />
    </div>
  );
}
