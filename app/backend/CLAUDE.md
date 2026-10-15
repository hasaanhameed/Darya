# Backend (FastAPI): agent context

This is the Python service. It covers data ingestion, the digital twin state, forecasting, risk and alerts, and the HTTP API the dashboard uses.
Read the root `CLAUDE.md` first for the domain rules (units, UTC, provenance).

## Environment
- Python 3.12 or newer. Python 3.12/3.13 is safest once the ML and geo packages are added.
- Dependencies live in `requirements.txt`. Pin exact versions. FastAPI is still 0.x, so a minor bump can break things.

```bash
cd app/backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
```

<!-- Confirm these once the app is scaffolded. -->
| Task | Command |
|---|---|
| Run API | `uvicorn app.main:app --reload` (docs at `/docs`) |
| Tests | `pytest` |
| Migrations | `alembic revision --autogenerate -m "<msg>"`, then `alembic upgrade head` |

Configuration comes from environment variables, read through `pydantic-settings`. Put local values in `.env`, which is git-ignored. Keep `.env.example` committed and up to date.

## Proposed layout
The code is organised by domain. It is not scaffolded yet, so update this section when it is.
```
app/
  main.py          FastAPI app factory, router registration
  core/            settings, DB engine/session, logging
  ingest/<source>/ one package per data source (wapda, ffd, glofas, imerg, sentinel1, ...)
  twin/            reach/node models, state updates, history
  forecast/        baselines, LSTM/GNN wrappers, forecast runs
  risk/            category mapping, reasons, alert rules
  api/             routers + Pydantic request/response schemas
alembic/           migrations
scripts/           one-off / CLI jobs (backfills, training, extraction)
tests/
```

## Conventions
- **Models and schemas:**
  - Use SQLAlchemy 2.x typed models (`Mapped[...]`).
  - Keep API shapes in Pydantic v2 schemas, separate from the models.
- **Schema changes:** every schema change goes through an Alembic migration. Never change tables by hand.
- **Async:**
  - Use `async def` routes only for non-blocking I/O.
  - CPU-heavy work, such as raster processing, model training or GNN inference, runs in scripts or worker jobs, not inside request handlers.
- **Collectors:**
  - Each collector is idempotent: fetch raw data, store it untouched, parse, validate, then upsert. Re-running it for the same date must not create duplicates.
  - Validation flags bad values and does not silently drop them. Record why a row was rejected.
- **Naming:** units go in names (`inflow_cfs`, `level_ft`, `storage_maf`). Station and node IDs are stable lowercase slugs (`tarbela`, `ghazi_barotha`).
- **API:**
  - Set the router tags and operation ids to clean names, because the frontend generates its typed client from `/openapi.json`.
  - Every response that carries a value also carries its timestamp, so the UI can show how fresh it is.
- **Tests:** use pytest, with httpx `ASGITransport` for API tests. Parsers get tests with small fixture files taken from real raw data.

## Data parsing gotchas
Before touching `ingest/wapda`, read the WAPDA section of `docs/DATA.md`. In short:
- Parse only the per-day sheets (`1`…`31` and `Synopsis`). Ignore `Summary`, `Monthly`, `Comparison`, `Peak` and `Sheet1–5`.
- Find station rows by name, not by fixed row number. At least one sheet is shifted down by one row.
- The expected date is the filename month plus the sheet day. Cross-check it against the `DATA FOR:` cell, and flag mismatches because they are usually stale copies.
- Range-check every value. The files contain manual typos such as `121.3` for `1213` and `120.4.95`, as well as `#REF!` errors.
