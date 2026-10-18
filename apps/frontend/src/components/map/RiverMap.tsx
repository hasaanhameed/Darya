"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import { setWorkerUrl } from "maplibre-gl";
import { useMemo, useState } from "react";
import Map, {
  AttributionControl,
  Layer,
  Marker,
  Source,
  type MapEvent,
  type MapLayerMouseEvent,
} from "react-map-gl/maplibre";

import { NodeShape } from "@/components/map/NodeMarker";
import type { ReachRisk, RiverNetwork } from "@/lib/api/types";
import { RISK_COLOR } from "@/lib/risk/categories";

// MapLibre finds its worker file relative to its own location, which breaks once bundled.
// Point it at the file explicitly so the bundler ships it.
setWorkerUrl(new URL("maplibre-gl/dist/maplibre-gl-worker.mjs", import.meta.url).href);

// Muted, free basemap with no API key (ADR-010).
const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/positron";

// Node names appear once the map is zoomed in enough for them not to overlap.
const LABEL_MIN_ZOOM = 6.5;

// Opens framed on the prototype river network (Tarbela in the north to Kotri in the south).
const NETWORK_BOUNDS: [[number, number], [number, number]] = [
  [67.6, 24.9],
  [75.0, 34.6],
];

/** Fade the basemap's place names so rivers, nodes and risk colors stay the strongest thing on the map. */
function quietBasemapLabels(event: MapEvent) {
  const map = event.target;
  for (const layer of map.getStyle().layers) {
    if (layer.type === "symbol") map.setPaintProperty(layer.id, "text-opacity", 0.55);
  }
}

interface RiverMapProps {
  network: RiverNetwork;
  risks: ReachRisk[];
  selectedReachId: string | null;
  onSelectReach: (reachId: string) => void;
}

export default function RiverMap({ network, risks, selectedReachId, onSelectReach }: RiverMapProps) {
  const [cursor, setCursor] = useState("");
  const [zoom, setZoom] = useState(0);

  // Reaches are drawn as straight lines between nodes until real geometry from HydroRIVERS is available.
  const reachLines = useMemo(() => {
    const nodes = new globalThis.Map(network.nodes.map((n) => [n.id, n]));
    const riskByReach = new globalThis.Map(risks.map((r) => [r.reach_id, r]));
    return {
      type: "FeatureCollection" as const,
      features: network.reaches.map((reach) => {
        const from = nodes.get(reach.from_node_id)!;
        const to = nodes.get(reach.to_node_id)!;
        const category = riskByReach.get(reach.id)?.category ?? "normal";
        return {
          type: "Feature" as const,
          properties: { id: reach.id, color: RISK_COLOR[category], selected: reach.id === selectedReachId },
          geometry: {
            type: "LineString" as const,
            coordinates: [
              [from.lon, from.lat],
              [to.lon, to.lat],
            ],
          },
        };
      }),
    };
  }, [network, risks, selectedReachId]);

  function handleClick(event: MapLayerMouseEvent) {
    const reachId = event.features?.[0]?.properties?.id;
    if (typeof reachId === "string") onSelectReach(reachId);
  }

  return (
    <Map
      initialViewState={{ bounds: NETWORK_BOUNDS, fitBoundsOptions: { padding: 32 } }}
      mapStyle={BASEMAP_STYLE}
      onLoad={quietBasemapLabels}
      interactiveLayerIds={["reach-hit"]}
      onClick={handleClick}
      onMouseEnter={() => setCursor("pointer")}
      onMouseLeave={() => setCursor("")}
      onZoom={(event) => setZoom(event.viewState.zoom)}
      cursor={cursor}
      // Bottom-left, so the reach panel on the right never covers the required attribution.
      attributionControl={false}
      style={{ width: "100%", height: "100%" }}
    >
      <AttributionControl position="bottom-left" compact />
      <Source id="reaches" type="geojson" data={reachLines}>
        <Layer
          id="reach-line"
          type="line"
          layout={{ "line-cap": "round", "line-join": "round" }}
          paint={{
            "line-color": ["get", "color"],
            "line-width": ["case", ["get", "selected"], 5, 3],
          }}
        />
        {/* Wider invisible line on top, so reaches are easy to click. */}
        <Layer id="reach-hit" type="line" paint={{ "line-color": "#000000", "line-opacity": 0, "line-width": 16 }} />
      </Source>

      {network.nodes.map((node) => (
        <Marker key={node.id} longitude={node.lon} latitude={node.lat} anchor="center">
          {/* The label is positioned outside the flow so the shape stays centred on the node. */}
          <div className="relative" title={node.name}>
            <NodeShape type={node.type} />
            {zoom >= LABEL_MIN_ZOOM && (
              <span className="absolute top-1/2 left-full ml-1 -translate-y-1/2 rounded-control bg-sheet/90 px-1 text-meta font-medium whitespace-nowrap text-ink">
                {node.name}
              </span>
            )}
          </div>
        </Marker>
      ))}
    </Map>
  );
}
