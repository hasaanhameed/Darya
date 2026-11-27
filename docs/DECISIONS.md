# Decisions

This is a log of significant technical decisions, kept as lightweight ADRs.

**How to use it**
- One entry per decision. Number entries in sequence and never reuse a number.
- Never delete an entry. When a decision changes, add a new entry and mark the old one `Superseded by ADR-xxx`.
- Status is one of `Proposed`, `Accepted`, `Superseded` or `Deprecated`.
- Proposed items move to Accepted once the team agrees.

**Template**
```
## ADR-XXX: <title>
- Date: YYYY-MM-DD
- Status: Proposed | Accepted | Superseded by ADR-YYY
- Context: why this needed deciding
- Decision: what we will do
- Consequences: what gets easier / harder
```

---

## ADR-001: FastAPI for the backend
- Date: 2026-10-15
- Status: Accepted
- Context: The data pipeline, satellite processing and ML are all in Python. We want one language from raw data through to the API.
- Decision: The backend is a Python FastAPI service in `app/backend`.
- Consequences: We get automatic OpenAPI output, which the frontend uses to generate a typed client. FastAPI is still 0.x, so versions must be pinned exactly.

## ADR-002: Next.js for the frontend
- Date: 2026-10-15
- Status: Accepted
- Context: The dashboard needs an interactive map, charts and a time slider. Next.js is a current framework with good map support.
- Decision: The dashboard is built with Next.js (App Router) in `app/frontend`.
- Consequences: Map libraries must be loaded on the client only, with no server-side rendering. The frontend reaches data only through the FastAPI API.

## ADR-003: PostgreSQL as the database
- Date: 2026-10-15
- Status: Accepted
- Context: The twin needs relational data (nodes, reaches, forecasts), time series and, later, spatial queries.
- Decision: Use PostgreSQL. Schema changes are made with Alembic migrations. Use the psycopg 3 driver. *(The driver is superseded by ADR-009, which uses asyncpg.)*
- Consequences: Plain tables with `(node_id, observed_at)` indexes are enough at our scale. PostGIS and TimescaleDB can be added later without changing databases.

## ADR-004: Monorepo layout
- Date: 2026-10-15
- Status: Accepted
- Decision: One repository with `app/backend`, `app/frontend`, `docs` and `data` (git-ignored).
- Consequences: Docs and code change together in the same PR. Agent context lives in `CLAUDE.md` (root and backend) and `app/frontend/DESIGN.md`.

## ADR-005: Raw data stays out of git
- Date: 2026-10-15
- Status: Accepted
- Context: Raw data will grow large once satellite imagery arrives. Some of it, such as the WAPDA files, was obtained on request.
- Decision: `data/` and the proposal PDF are git-ignored and shared through the team drive. `docs/DATA.md` documents what goes where.
- Consequences: A fresh clone has no data, and setup must say where to get it. Raw files are never edited.

## ADR-006: pip + requirements.txt for the backend
- Date: 2026-10-15
- Status: Accepted
- Decision: Use a plain `venv` and pinned `app/backend/requirements.txt`. Add geo and ML packages only when their ADRs are accepted.
- Consequences: The setup is simple and familiar. Lockfile and dependency-group features (e.g. uv) are not used for now.

## ADR-007: Supabase as hosted PostgreSQL for development
- Date: 2026-10-16
- Status: Accepted
- Context: The team needs a shared PostgreSQL database without having to run a server.
- Decision: Use a Supabase project (`darya-dev-db`, Mumbai region, free tier) **as plain PostgreSQL only**.
  - The Data API is off and GitHub integration is not used.
  - The backend connects through the Session pooler string kept in `.env`.
  - Schema changes still go through Alembic.
- Consequences:
  - There is no database to host ourselves, and PostGIS is available as an extension.
  - The free tier has a 500 MB limit and pauses after about a week of inactivity.
  - We can move to any other PostgreSQL later, because nothing depends on Supabase-specific features.

## ADR-008: Backend tests mirror the app layout
- Date: 2026-10-16
- Status: Accepted
- Decision:
  - `tests/` sits beside `app/` and mirrors its folders (`tests/ingest/wapda/` tests `app/ingest/wapda/`).
  - Tests that need the database are tagged with the pytest marker `integration`, so we don't need separate `unit/` and `integration/` folders.
  - `alembic/` and `alembic.ini` also sit beside `app/`.
- Consequences: Tests for any module are easy to find, and fast tests run with `pytest -m "not integration"`. The details are in `apps/backend/CLAUDE.md`.

## ADR-009: Async database layer with asyncpg
- Date: 2026-10-16
- Status: Accepted
- Context:
  - Darya is meant to **grow past a demo** into a system agencies can rely on.
  - Most of its runtime work is waiting on I/O: downloading from several sources, writing to the twin, and serving many dashboard users during a flood.
  - In real use, large updates can arrive from several sources at once, and the twin should reflect them as soon as possible.
  - Moving from sync to async later would mean rewriting every DB call, route and test. Choosing now, while the codebase is empty, costs almost nothing.
- Decision:
  - The backend uses async SQLAlchemy (`AsyncSession`), `async def` routes, and `httpx.AsyncClient` in collectors.
  - The driver is **asyncpg**. psycopg's async mode doesn't work with Windows' default event loop, and asyncpg works everywhere with no extra setup.
  - CPU-heavy work (forecasting, GNN, raster processing) still runs in separate worker processes. Async doesn't speed it up.
- Consequences:
  - Collectors can fetch from many sources in parallel, and the API handles high traffic efficiently.
  - Code is a bit stricter: every DB call needs `await`, related rows must be loaded up front, and tests need anyio. These rules are in `apps/backend/CLAUDE.md`.
  - Scaling beyond one process means adding more workers, and the database's connection limit becomes the next ceiling.

## ADR-010: MapLibre GL with an OpenFreeMap basemap
- Date: 2026-10-18
- Status: Accepted (resolves P-4)
- Context: The map is the main screen. River reaches must be colored by risk and stand out against a quiet basemap. The time slider redraws the map often, and a satellite water layer comes later.
- Decision: Use MapLibre GL through `react-map-gl`, with an OpenFreeMap vector basemap restyled to be muted.
- Consequences:
  - Free, with no API key. Reach colors come straight from data, and the basemap can be toned down as much as we want.
  - It renders with WebGL, so the component is client-only (`next/dynamic` with `ssr: false`, per ADR-002).
  - It's harder to learn than Leaflet. deck.gl can be added later if layers get heavy.

## ADR-011: Tailwind 4 with shadcn/ui, restyled
- Date: 2026-10-18
- Status: Accepted (resolves P-9, styling)
- Context: We need accessible controls (slider, select, tabs, dialog) without a heavy UI kit or its recognisable default look.
- Decision: Style with Tailwind 4 using our own design tokens. Add shadcn/ui components one at a time, only when a screen needs them, and restyle each to our tokens.
- Consequences:
  - The components are copied into our repo, so we own and can change them. Keyboard support comes from Radix underneath.
  - shadcn's default look and its Lucide icons must not ship (see `apps/frontend/DESIGN.md` and ADR-015).

## ADR-012: TanStack Query, with the generated API client added later
- Date: 2026-10-18
- Status: Accepted (resolves P-9, data fetching)
- Context: The time slider and map request data often, so caching and loading states matter. The backend has no endpoints yet.
- Decision: Use TanStack Query for all API calls. For now, use hand-written types and a small fetch layer in `src/lib/api/`. Once the backend publishes `/openapi.json`, replace them with a client generated by `@hey-api/openapi-ts`.
- Consequences:
  - Caching, retries and loading states come built in.
  - The hand-written types must be kept close to what the backend builds until the generated client replaces them.

## ADR-013: Recharts for charts
- Date: 2026-10-18
- Status: Accepted
- Context: The reach panel needs a time-series chart of observed values, a forecast line and an uncertainty band.
- Decision: Use Recharts. Draw the band as a range area (low to high), and the forecast as a dashed line.
- Consequences: It's widely documented and easy for all three of us. Its default styling is recognisable, so every chart is restyled to our tokens.

## ADR-014: IBM Plex Sans as the UI font
- Date: 2026-10-18
- Status: Accepted
- Context: `apps/frontend/DESIGN.md` bans Inter, Geist and Space Grotesk. The dashboard needs a font that is clear at small sizes and has tabular figures, so numbers line up.
- Decision: Use IBM Plex Sans, loaded with `next/font/google`. Numbers use `font-variant-numeric: tabular-nums`.
- Consequences: The font is free and self-hosted by Next.js at build time. If an Urdu interface is added later, it needs a separate Urdu font.

## ADR-015: Phosphor icons, plus custom map markers
- Date: 2026-10-18
- Status: Accepted
- Context: `apps/frontend/DESIGN.md` says not to use the default Lucide set as-is, and to choose icons deliberately.
- Decision: Use `@phosphor-icons/react` for UI icons, in the Regular weight only. Map markers for node types (dam, barrage, headworks, gauge, confluence) are simple custom shapes. Replace the Lucide imports that shadcn components bring in with Phosphor.
- Consequences: Icons look consistent and aren't the default. Icons are only used where they help recognition, not as decoration.

## ADR-016: npm, with Vitest and Testing Library for frontend tests
- Date: 2026-10-18
- Status: Accepted
- Decision:
  - Use npm, which comes with Node, with a committed `package-lock.json`. Pin exact versions.
  - Use Vitest with React Testing Library for unit tests. Start with the logic that must be right: unit and time formatting (UTC to PKT) and risk-category mapping.
  - Browser end-to-end tests (e.g. Playwright) are left for later, when the pages are stable.
- Consequences: Nothing extra to install, which matches the backend's plain pip setup (ADR-006). There are no browser tests yet.

## ADR-017: WAPDA data scope and cleaning rules
- Date: 2026-10-18
- Status: Accepted
- Context:
  - A full survey of the 54 WAPDA workbooks (1,319 day sheets) found under 1% typo values, 41 stale copied sheets, and sheets copied from months that have no file of their own. Details are in `docs/DATA.md`.
  - WAPDA data is historical, not live. It serves as ground truth for training and evaluating forecasts, so bad values directly distort scores.
- Decision:
  - **Gomal Zam is dropped.** It isn't on the river graph, and it is the noisiest station (most typos, a repeated placeholder level, some flows converted from m³/s). WAPDA ingestion covers 6 stations: Tarbela, Ghazi Barotha, Mangla, Warsak, Chashma and Jinnah. T-4 EXT is read only to check Tarbela's total outflow.
  - **Typos are flagged, never corrected.** A value far from its neighbouring days is kept as written and marked `suspect`. Training and evaluation ignore suspect values.
  - **Stale copies are skipped.** A sheet identical to the sheet for the date it claims is not stored.
  - **Copied sheets from months with no file use the sheet's own date.** If a sheet's `DATA FOR:` date is about a month or more earlier and no real sheet exists for that date, its data is stored under that date and marked `date_from_sheet`.
  - **Date typos use the expected date.** If the claimed date has its own sheet with different data, the date cell is treated as the typo (all 4 cases are one day off).
- Consequences:
  - The prototype loses Gomal Zam. It can be added back later from the same files if needed.
  - Every stored value can be traced to its file and sheet, and every change in how a value was read is visible through its flag.
  - The rules need a short manual review of the flagged rows before the first load.

## ADR-018: Shared daily observation tables
- Date: 2026-10-18
- Status: Accepted. Narrowed by ADR-019: `daily_observations` now holds gauge data (WAPDA), and satellite and model sources get their own tables.
- Context: Several sources (WAPDA now; FFC, IRSA, GloFAS and others later) report daily values for the same river points. One table per source would make every comparison and every API query join several tables.
- Decision:
  - `nodes` holds the river points (slug id, name, river, approximate location). It is seeded with the 6 WAPDA stations.
  - `daily_observations` holds one row per node, per day, per source, with a `source` column. The unique key is `(node_id, observed_on, source)`, so different sources for the same day sit side by side.
  - Its value columns follow the WAPDA structure for now (level, inflow, turbine, other and total outflow, irrigation indent) and are extended by migration when another source needs more.
  - Values keep their native units. Each row carries `flags`, `source_file`, `sheet` and `ingested_at`.
  - A source's loader replaces only its own rows (delete by `source`, then insert), so re-running a load is safe and never touches other sources.
- Consequences: One query covers all sources. The WAPDA-shaped columns will need changes once a source with different variables (e.g. discharge in m³/s, rainfall) arrives.

## ADR-019: One table per satellite and model source
- Date: 2026-11-22
- Status: Accepted. Followed for PMD station rainfall too (ADR-023: `rain_stations` and `pmd_rainfall`).
- Context:
  - GloFAS (modelled discharge in m³/s), IMERG (catchment rainfall in mm) and Sentinel-1 (water extent per image) have different variables, units and provenance (product version, run, scene).
  - Fitting them into the WAPDA-shaped `daily_observations` would mean many mostly empty columns.
- Decision:
  - Each new source gets its own table, shaped for that source: `glofas_discharge`, `imerg_rainfall`, `sentinel1_scenes` and `sentinel1_reach_water`.
  - All tables still key on `node_id` (or reach) and `observed_on`, keep native units in column names, and carry `flags`, `source_file` and `ingested_at`.
  - `daily_observations` stays as the WAPDA table.
  - All 21 prototype nodes are seeded in `nodes`, so gridded sources can cover the whole network.
- Consequences:
  - Each table is easy to read and to load on its own.
  - Model inputs and API queries join several tables. We revisit this choice (for example a shared long-format table or a view) when training starts.

## ADR-020: xarray and geo libraries for gridded data
- Date: 2026-11-22
- Status: Accepted (resolves P-3)
- Context: GloFAS and IMERG come as NetCDF grids, Sentinel-1 as Cloud-Optimised GeoTIFFs, and catchments and reaches are polygons. pandas alone can't read these.
- Decision:
  - **Reading:**
    - xarray reads grids, through the netCDF4 engine;
    - rasterio and rioxarray read rasters;
    - geopandas reads polygons;
    - pyflwdir traces catchments on flow-direction grids (ADR-022).
  - **Clients:** `cdsapi` (GloFAS), `harmony-py` (IMERG), and `pystac-client`, `planetary-computer` and `odc-stac` (Sentinel-1).
  - **Gridded data becomes a pandas DataFrame at the module boundary** (e.g. one row per node per day). Cleaning and loading stay in pandas, as for WAPDA.
  - All of these install from wheels on the dev venv (Python 3.14, GDAL 3.12 bundled with rasterio), so no system GDAL is needed.
- Consequences:
  - The pipelines look alike after the first step, whatever the source format.
  - The dependency list grows. Versions are pinned in `requirements.txt`.

## ADR-021: GloFAS v4.0 reanalysis as modelled river flow
- Date: 2026-11-22
- Status: Accepted (resolves P-7)
- Context:
  - Measured history (WAPDA) starts in Jul 2022, and models need data from 2015.
  - GloFAS v5.0 was released in Jul 2026, but only as consolidated data (no daily updates), with no published upstream-area file. Live GloFAS forecasts are still v4.
- Decision:
  - **Version and products:** v4.0 reanalysis from EWDS, from 2015-01-01:
    - `consolidated` up to 2026-06-30;
    - `intermediate` after that, about 4 days behind.
  - **Never mix versions.** The version is stored on every row and is part of the unique key.
  - **One cell per node:** the nearest main-river cell, chosen by the rule in `docs/DATA.md`. Two cells are chosen by hand (Panjnad, Rasul). The matches are committed as `node_grid_cells.csv`.
  - **The day** is the UTC day the 24-hour mean covers (the value's 00 UTC stamp minus one day).
- Consequences:
  - We get a consistent daily flow series for all 21 nodes from 2015, for training and live use.
  - **Moving to v5** means re-matching the cells and doing a full reload. Plan it once v5 forecasts and v5 intermediate data are both available (expected Dec 2026 or later).

## ADR-022: IMERG Late rainfall averaged over catchments traced on GloFAS's river map
- Date: 2026-11-26
- Status: Accepted
- Context:
  - Rain over each node's catchment (the land that drains into it) is a main forecast input.
  - **IMERG choice:** IMERG Final stopped at 2025-09-30 while its V08 is prepared, and the Late run (~14 h delay) is what a live system would use.
  - **Catchment choice:** catchment outlines could come from HydroBASINS polygons or from GloFAS's own flow-direction (LDD) grid. An independent review compared the two and recommended GloFAS.
- Decision:
  - **Rainfall product:** IMERG daily **Late** V07 (`GPM_3IMERGDL`), for both training and live use. Fetched through NASA Harmony, cut to our area and to the `precipitation` variable only.
  - **Catchment map:** catchments are traced upstream from each node's GloFAS cell (`node_grid_cells.csv`) on the **GloFAS v4.0 LDD grid**, with `pyflwdir`. HydroBASINS is not used.
- Consequences:
  - Rain and flow describe the same water. GloFAS's quirks, such as the Chenab joining the Jhelum at Rasul, appear the same way in both.
  - The tracing checks itself: a catchment's area must match GloFAS's upstream area at the node's cell.
  - Outlines are on a 5 km grid. That is finer than IMERG's 10 km and changes catchment averages by about 1% at our catchment sizes (24,000–830,000 km²).
  - Flat irrigated plains drain on the map to whichever river they reach, and canals aren't represented. Rain there adds little to river flow, so the model has to learn that.
  - Record version labels change within V07 (V07B, V07C). V08 means re-downloading and reloading everything.

## ADR-023: PMD station rainfall in its own tables, with a station catalog
- Date: 2026-11-26
- Status: Accepted
- Context:
  - PMD gave us daily rain-gauge totals for 120 stations (122 names as written), 1981–2015, in one workbook. It is the only measured rainfall from before IMERG (2000), so it gives models a long rain → flow history. It is loaded once, like WAPDA.
  - Rain gauges are weather stations, not points on the river network. The file has no coordinates or basin.
  - Two options: add the stations to `nodes` with a `rainfall_mm` column in `daily_observations`, or give them their own tables (as ADR-019 does for each new source).
- Decision:
  - **Two new tables:**
    - `rain_stations` (slug id, name, PMD name as written, approximate lat/lon, province, basin);
    - `pmd_rainfall` (one row per station per day: `rainfall_mm`, `rainfall_raw` as written, `flags`, `source_file`, `sheet_row`, `ingested_at`; unique on station and day).
  - **All stations are loaded,** each tagged `basin` = `indus` or `outside`, so models can filter later instead of us deciding now.
  - **Station coordinates come from a committed catalog,** `app/ingest/pmd/rain_stations.csv`, compiled from public sources and marked approximate *(to verify)*. The loader replaces `rain_stations` from it on every run.
  - **Linking stations to river nodes is deferred.** It will use the node catchments from ADR-022, so `rain_stations` has no `node_id` yet.
- Consequences:
  - `nodes` stays a river graph, and `daily_observations` keeps its WAPDA shape.
  - Fixing a coordinate means editing the CSV and re-running the load.
  - Model inputs will need a station → catchment join once it is built.

## ADR-024: PMD rainfall cleaning rules
- Date: 2026-11-26
- Status: Accepted
- Context: The survey (`docs/DATA.md`, "PMD: daily station rainfall") found "no reading" markers, garbled cells, values on dates that don't exist, negatives, 153 duplicate station-months, a few extreme values (some real, some not) and two stations whose values look modelled.
- Decision (flag, never correct, as in ADR-017):
  - **Blank cells are missing, not zero,** and produce no row. Days that don't exist (30 Feb…) are not stored, but they are counted and listed in the review file.
  - **Markers and garbled text** (`----`, `*`, `***` on a real day, `.0   1`) are stored with an empty value and flagged `missing_marker` or `not_numeric`.
  - **Negative values** are kept as written and flagged `suspect_negative` (they may be a trace code).
  - **A station-month with a non-zero value on a day that doesn't exist** has all its rows flagged `month_has_impossible_day`, because its days may be shifted.
  - **Duplicate station-months:** identical copies become one row. For copies that differ, the first one (lowest sheet row) is kept and flagged `duplicate_conflict`.
  - **Garhi Dopatta and Kotli** are loaded with `not_gauge_precision` on every row.
  - **More than 300 mm in a day** is flagged `extreme_rainfall`, but **not** excluded, because some are real (Islamabad 591.9 mm on 24 Jul 2001).
  - All flags except `extreme_rainfall` mean "exclude from training and scoring".
- Consequences:
  - Every stored value is exactly as written and can be traced to its Excel row.
  - `extreme_rainfall` rows need a short manual check before training.
  - If PMD confirms the trace codes (`-1`, `0.01`) or the shifted months, the rules change here and the data is reloaded.

---

## Proposed (not yet decided)
| # | Proposal | Notes |
|---|---|---|
| P-1 | **PostGIS** extension | Spatial queries per reach and vector tiles via `ST_AsMVT`. Probably needed once water extents arrive |
| P-2 | **PyTorch + PyTorch Geometric** | For the LSTM and GNN. Check Python version compatibility before adding |
| P-3 | ~~**Rasterio / GDAL / GeoPandas**~~ | Accepted as ADR-020 |
| P-4 | ~~**MapLibre GL via react-map-gl**, OpenFreeMap basemap~~ | Accepted as ADR-010 |
| P-5 | **Scheduler** | APScheduler in its own worker container, or cron calling CLI scripts. Avoid Celery unless needed |
| P-6 | **Docker Compose** (db, backend, frontend) | Gives one-command start and a repeatable demo |
| P-7 | ~~**GloFAS reanalysis** as the historical fallback~~ | Accepted as ADR-021 |
| P-8 | **Sentinel-1 access platform** | CDSE vs Planetary Computer RTC vs GEE (see `docs/DATA.md`) |
| P-9 | ~~**Frontend tooling**~~ | Accepted as ADR-011 (styling) and ADR-012 (data fetching) |
