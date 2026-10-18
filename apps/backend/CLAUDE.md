# Backend (FastAPI): agent context

This is the Python service. It covers data ingestion, the digital twin state, forecasting, risk and alerts, and the HTTP API the dashboard uses.
Read the root `CLAUDE.md` first for the domain rules (units, UTC, provenance).

## Environment
- Python 3.12 or newer. Python 3.12/3.13 is safest once the ML and geo packages are added.
- Dependencies live in `requirements.txt`. Pin exact versions. FastAPI is still 0.x, so a minor bump can break things.

```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
```

<!-- Confirm these once the app is scaffolded. -->
| Task | Command |
|---|---|
| Run API | `uvicorn app.main:app --reload` (docs at `/docs`) |
| Tests | `pytest` (fast only: `pytest -m "not integration"`) |
| Migrations | `alembic revision --autogenerate -m "<msg>"`, then `alembic upgrade head` |
| WAPDA load | `python -m scripts.ingest_wapda` (`--dry-run` writes only `data/wapda/processed/review.csv`) |

Configuration lives in `app/core/config.py`, which reads environment variables through `pydantic-settings`.
- Put local values in `.env`, which is git-ignored. Keep `.env.example` committed and up to date.
- `DATABASE_URL` must use the `postgresql+asyncpg://` scheme.

## Layout
The code is organised by domain. Folders marked *(planned)* don't exist yet.
```
app/
  main.py          FastAPI app factory, router registration (planned)
  core/            settings, async DB engine/session
  models/          SQLAlchemy tables: Node, DailyObservation
  routes/          API routers + Pydantic request/response schemas (empty)
  ingest/wapda/    station_aliases → sheet_finder → sheet_parser → cleaning → load_to_db
  ingest/<source>/ one package per further source (ffd, glofas, imerg, ...) (planned)
  twin/            reach state updates, history (planned)
  forecast/        baselines, LSTM/GNN wrappers, forecast runs (planned)
  risk/            category mapping, reasons, alert rules (planned)
alembic/           migrations
scripts/           CLI jobs, e.g. ingest_wapda.py
tests/
```
The API never imports `ingest`. Only scripts (and a scheduler, later) call it.

## Conventions
- **Models and schemas:**
  - Use SQLAlchemy 2.x typed models (`Mapped[...]`).
  - Keep API shapes in Pydantic v2 schemas, separate from the models.
- **Schema changes:** every schema change goes through an Alembic migration. Never change tables by hand.
- **Async database (ADR-009):** the DB layer is async, using SQLAlchemy `AsyncSession` and the asyncpg driver. The engine, `SessionLocal`, `Base` and `get_db` live in `app/core/database.py`.
  - `await` every DB call (`await session.execute(...)`, `await session.commit()`).
  - Never rely on lazy loading. Load related rows up front with `selectinload(...)`, or you'll get a `MissingGreenlet` error.
  - Routes that touch the DB are `async def` and get their session from `Depends(get_db)`.
  - Never call blocking code inside `async def`, e.g. `requests`, `time.sleep` or heavy pandas/model work. Use `httpx.AsyncClient` for downloads.
  - CPU-heavy work, such as raster processing, model training or GNN inference, runs in separate scripts or worker processes, not inside request handlers.
  - Async tests use `@pytest.mark.anyio`.
- **Data handling uses pandas.** Parsing, cleaning and reshaping work on DataFrames, the same way for every source, so the pipelines look alike. Prefer column operations and boolean masks over loops through rows.
- **Collectors:**
  - Each collector is idempotent: fetch raw data, store it untouched, parse, validate, then upsert. Re-running it for the same date must not create duplicates.
  - Validation flags bad values and does not silently drop them. Record why a row was rejected.
- **Naming:** units go in names (`inflow_cfs`, `level_ft`, `storage_maf`). Station and node IDs are stable lowercase slugs (`tarbela`, `ghazi_barotha`).
- **File names:** a module's name says what it does, e.g. `sheet_finder.py`, `sheet_parser.py`, `load_to_db.py`. Avoid vague names such as `utils.py`, `helpers.py`, `common.py`, `misc.py`, or single generic words like `files.py` and `load.py`.
- **API:**
  - Set the router tags and operation ids to clean names, because the frontend generates its typed client from `/openapi.json`.
  - Every response that carries a value also carries its timestamp, so the UI can show how fresh it is.
- **Tests:** see the Tests section below.

## Tests
Tests use pytest and live in `tests/`, beside `app/`, not inside it. **The `tests/` tree mirrors `app/`**, so the tests for any module are easy to find.
```
tests/
  conftest.py            shared setup (test DB session, API client)
  fixtures/              small real sample files (e.g. a few WAPDA sheets)
  core/                  tests for app/core/
  models/                tests for app/models/
  routes/                tests for app/routes/   (API tests)
  ingest/wapda/          tests for app/ingest/wapda/
  ...                    one folder per app/ module, added as modules appear
```
- **Naming:** test files are named `test_<thing>.py`, e.g. `tests/ingest/wapda/test_parser.py` tests `app/ingest/wapda/parser.py`. One test function checks one behaviour, and its name says what that behaviour is (`test_skips_stale_template_sheets`).
- **Fast vs slow tests:**
  - Unit tests are fast and use no database or network. Write these by default.
  - Tests that need the database are marked `@pytest.mark.integration`. Run only the fast ones with `pytest -m "not integration"`.
- **API tests** use httpx `ASGITransport` against the FastAPI app, with dependencies swapped through `app.dependency_overrides`.
- **Fixtures:** files in `tests/fixtures/` are small extracts of real raw data. Never point tests at the full files in `data/`.

## Data parsing gotchas
Before touching `ingest/wapda`, read the WAPDA section of `docs/DATA.md`. In short:
- Parse only the per-day sheets (`1`…`31` and `Synopsis`). Ignore `Summary`, `Monthly`, `Comparison`, `Peak` and `Sheet1–5`.
- Find station rows by name, not by fixed row number. At least one sheet is shifted down by one row.
- The expected date is the filename month plus the sheet day. Cross-check it against the `DATA FOR:` cell, and flag mismatches because they are usually stale copies.
- Range-check every value. The files contain manual typos such as `121.3` for `1213` and `120.4.95`, as well as `#REF!` errors.
