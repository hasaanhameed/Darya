# Darya: agent context

Darya is a digital twin of the Indus river system for flood monitoring and forecasting. It is a final-year research prototype.
It collects satellite, rainfall and river data and keeps a versioned state per river reach. It forecasts 1–3 days ahead and shows explained risk levels on a web map.

## Stack
- **Confirmed:**
  - FastAPI backend (Python)
  - Next.js frontend
  - PostgreSQL
- **Planned, not yet decided:**
  - PostGIS
  - PyTorch + PyG
  - Rasterio/GDAL/GeoPandas
  - MapLibre
  - Docker Compose
  - a job scheduler

Do not introduce a new framework or service without adding an ADR to `docs/DECISIONS.md`.

## Repo map
| Path | Contents |
|---|---|
| `app/backend/` | FastAPI service. Read `app/backend/CLAUDE.md` before working here. |
| `app/frontend/` | Next.js dashboard. Read `app/frontend/DESIGN.md` before any UI work. |
| `data/` | Raw and derived data. Git-ignored, and may be absent on a fresh clone. |
| `docs/` | Project documentation. Read the relevant file when a task touches it (table below). |

| Doc | Read it when |
|---|---|
| `docs/ARCHITECTURE.md` | You need components, core concepts (node, reach, twin state) or invariants. |
| `docs/FLOW.md` | You need the order of operations: ingestion → twin → forecast → risk → API → UI. |
| `docs/DATA.md` | You touch any data source. It includes the WAPDA spreadsheet layout and its quality issues. |
| `docs/DECISIONS.md` | You check whether something is decided, or record a new decision. |
| `docs/PROGRESS.md` | You need current status, milestones or who owns what. |

## Domain rules
- **Units:** keep the source's native units. These are cusecs (ft³/s) for flow, feet for reservoir level and MAF for storage.
  - Every column, field and API value must name its unit, e.g. `inflow_cfs`, `level_ft`.
  - Convert units only at clearly defined boundaries, such as model input or display.
- **Time:** store timestamps as timezone-aware UTC. Display them in PKT (UTC+5).
  - Daily WAPDA values are for a reporting day, so store them as a `date`, not a timestamp.
- **Provenance:** every observation records its `source`, `observed_at` and `ingested_at`.
  - Forecasts and backtests may only use data that was available at the forecast time. Never leak future data.
- **Flood categories:** match PMD-FFD's flood categories (Low → Exceptional) wherever a site has published thresholds. See `docs/DATA.md`.
- **Network topology:** the river network is a directed graph that runs upstream → downstream.

## Working rules
- **Explain simply.** In chat, use a plain, easy-to-follow tone. Don't overcomplicate explanations.
- **Write obvious code.** Names and logic should be clear enough to understand just by reading. Avoid clever tricks.
- **Follow industry-standard structure.** Organise the repo the way well-maintained production projects do:
  - Each module has one clear job and a clear boundary. Ingestion, the twin, forecasting, risk and the API stay separate.
  - Tests and config go in their conventional places.
  - Don't invent unusual layouts.
- **Write only what's needed.** Before adding any code, ask "is this required?" Skip speculative helpers, options and abstractions.
- **Let the developer decide.** When a choice comes up (stack, schema, approach, library):
  - Don't pick on your own. Explain the options simply, with their trade-offs and your recommendation.
  - Let the developer choose.
  - Record the decision as an ADR in `docs/DECISIONS.md`.
- **Commit messages** use the Conventional Commits format with an effective one-line summary, e.g. `feat: add WAPDA day-sheet parser`, `fix: skip stale template sheets`, `docs: update DATA.md coverage`. Other types: `refactor`, `test`, `chore`.
- **One logical change per commit.** Group files that belong to the same change into one commit. Split unrelated changes into separate commits, even when they were made in the same session.
- **IMPORTANT: never commit or push without explicit permission** from the user.

## Guardrails
- Never modify raw files under `data/`. Write derived outputs to a separate folder.
- Never commit data, `.env` files, credentials, satellite imagery or model weights.
- Never word any output (UI text, alerts, docs) as an official flood warning. Darya is a support tool.
- Do not trust WAPDA "Summary"/"Monthly" sheets. Parse only the per-day sheets. The reasons are in `docs/DATA.md`.

## Workflow
- Git branches off `main`. Every change is reviewed by another member before merge.
- After finishing a meaningful task, add a dated line to `docs/PROGRESS.md`.
- Keep docs short and current. Edit or replace stale text rather than appending contradictions.

## Commands
<!-- Fill in once the backend and frontend are scaffolded. -->
- Backend: see `app/backend/CLAUDE.md`.
- Frontend: TBD.
