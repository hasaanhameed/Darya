# Darya frontend

The Next.js dashboard: a map of the river network, a schematic of the river system, active alerts and per-reach details.
Read `DESIGN.md` before any UI work. Stack decisions are ADR-010 to ADR-016 in `docs/DECISIONS.md`.

## Setup
You need Node.js 22 or newer. npm comes with it.

```bash
cd apps/frontend
npm install
cp .env.example .env.local     # Windows PowerShell: Copy-Item .env.example .env.local
```

## Commands
| Task | Command |
|---|---|
| Run the dev server | `npm run dev`, then open http://localhost:3000 |
| Unit tests | `npm test` |
| Lint | `npm run lint` |
| Production build | `npm run build`, then `npm start` |

## Data: real API or sample data
The dashboard only reads from the FastAPI backend, at `NEXT_PUBLIC_API_BASE_URL`.
- **The backend has no endpoints yet.** So by default the page says it can't reach the API.
- **To preview with made-up values,** set `NEXT_PUBLIC_USE_SAMPLE_DATA=true` in `.env.local` and restart `npm run dev`.
  - A dark banner at the top says the data is sample data.
  - The sample lives in `src/lib/api/sample.ts`. The node list and FFD flood limits in it are real (from `docs/DATA.md`). Every flow, forecast and alert is made up.
  - Never turn it on for a shared or deployed build.

## API the frontend expects
The response types are in `src/lib/api/types.ts`. All times are UTC, and units are part of the field names.
Once the backend publishes `/openapi.json`, the hand-written types get replaced by a generated client (ADR-012).

| Method | Path | Returns | Used for |
|---|---|---|---|
| GET | `/network` | `RiverNetwork` (nodes with FFD limits, reaches) | Map lines and markers, schematic |
| GET | `/state` | `NodeState[]` (latest inflow, outflow, level per node) | Schematic flows, reach panel values |
| GET | `/risk` | `ReachRisk[]` (current category, forecast peak, range, reasons) | Reach colors, reach panel |
| GET | `/alerts?status=active` | `Alert[]` | Active alerts list |
| GET | `/reaches/{reach_id}/series` | `ReachSeries` (14 days observed, 3 days forecast with range) | Reach panel chart and staff |

Later, `/state`, `/risk` and `/reaches/{id}/series` will take an `at` query parameter for the time slider.

## Layout
```
src/
  app/            routes, layout, global styles and design tokens (globals.css)
  components/
    dashboard/    the map page: resizable rail + map + reach panel
    legend/       the map key
    map/          MapLibre map (client-only) and node marker shapes
    schematic/    the river line diagram in the left rail
    alerts/       alert list
    reach/        reach panel, risk badge, threshold staff
    charts/       observed + forecast chart with uncertainty band
    layout/       header, disclaimer line, sample-data banner
    ui/           small shared pieces (skeleton, collapsible section)
  lib/
    api/          types, the fetch client, query hooks, sample data
    format/       units and PKT time formatting
    risk/         flood categories, labels, colors
    network.ts    reach names and upstream-to-downstream ordering
```
Unit tests sit next to the code they test (`*.test.ts`).

## Known limits
- Reaches are straight lines between nodes, until real river geometry from HydroRIVERS is added.
- Not built yet: the time slider, and the `/alerts`, `/nodes/[id]`, `/reaches/[id]`, `/sources`, `/about`, `/evaluation`, `/terms` and `/privacy` pages.
