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

---

## Proposed (not yet decided)
| # | Proposal | Notes |
|---|---|---|
| P-1 | **PostGIS** extension | Spatial queries per reach and vector tiles via `ST_AsMVT`. Probably needed once water extents arrive |
| P-2 | **PyTorch + PyTorch Geometric** | For the LSTM and GNN. Check Python version compatibility before adding |
| P-3 | **Rasterio / GDAL / GeoPandas** | Sentinel-1 processing and handling the river network |
| P-4 | **MapLibre GL via react-map-gl**, OpenFreeMap basemap | Free with no API key. Add deck.gl if layers get heavy. Leaflet is the simpler fallback |
| P-5 | **Scheduler** | APScheduler in its own worker container, or cron calling CLI scripts. Avoid Celery unless needed |
| P-6 | **Docker Compose** (db, backend, frontend) | Gives one-command start and a repeatable demo |
| P-7 | **GloFAS reanalysis** as the historical fallback | If gauge history from 2015 isn't received in time. Pin one GloFAS version |
| P-8 | **Sentinel-1 access platform** | CDSE vs Planetary Computer RTC vs GEE (see `docs/DATA.md`) |
| P-9 | **Frontend tooling** | Tailwind 4, shadcn/ui, TanStack Query, client generated with `@hey-api/openapi-ts` |
