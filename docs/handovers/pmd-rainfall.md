# Handover: PMD daily rainfall (1981 – 2015)

**Status (2026-11-27, Rohail):** the ingestion pipeline is built, tested, loaded into the dev database and **waiting for review** in [pull request #1](https://github.com/hasaanhameed/Darya/pull/1). What's left is the review, checking the data and linking it to the river network. See "Next steps" below.
**Branch:** `feat/pmd-rainfall-ingestion` (pushed), started from Hasaan's `feat/satellite-ingestion`, so it contains all of his GloFAS/IMERG work too.

## Read first
1. `docs/DATA.md` → "PMD: daily station rainfall": file layout, stations, coverage, quality issues, parsing rules, flags and the first-run results. **Read its "Check before using PMD rainfall for modelling" box.**
2. `docs/DECISIONS.md` → ADR-023 (storage: `rain_stations` + `pmd_rainfall`) and ADR-024 (cleaning rules).
3. `apps/backend/CLAUDE.md`: setup, commands and layout.

## What exists
| Piece | Where |
|---|---|
| Raw file (not in git, get it from the team drive) | `data/pmd/DAILY RAIN - ALL STATIONS - 1981-2015.xls` |
| Tables + migration `38e33b60eddb` | `app/models/rain_station.py`, `app/models/pmd_rainfall.py`, `alembic/versions/38e33b60eddb_*.py` |
| Station catalog: 120 stations, **approximate** lat/lon, province, basin | `app/ingest/pmd/rain_stations.csv` |
| Pipeline | `app/ingest/pmd/`: `station_names` → `sheet_parser` → `cleaning` → `load_to_db` |
| Command | `scripts/ingest_pmd.py` |
| Tests (37 unit + 4 loader + 5 model) | `tests/ingest/pmd/`, `tests/models/test_rain_station.py`, `tests/models/test_pmd_rainfall.py` |
| Review files from the last run (not in git) | `data/pmd/processed/`: `review.csv`, `impossible_day_values.csv`, `duplicate_conflicts.csv` |

**In the dev database:** 120 rows in `rain_stations` and 651,552 rows in `pmd_rainfall` (116 stations with data, 1 Jan 1981 – 30 Nov 2015). 618,589 rows have no flags. Rows with any flag except `extreme_rainfall` must be left out of training.

## How to run
From `apps/backend`, with the venv set up and `DATABASE_URL` in `.env` (ask Hasaan or Rohail; never commit `.env`):
```bash
pytest -m "not integration"              # fast tests, no database
pytest                                   # all tests (database tests roll back and change nothing)
python -m scripts.ingest_pmd --dry-run   # parse + clean, write data/pmd/processed/, no database
python -m scripts.ingest_pmd             # also replace rain_stations and pmd_rainfall (~3 minutes)
```
The load is safe to re-run: it replaces both PMD tables in one transaction and never touches other tables.

## Next steps
0. **Review and merge [pull request #1](https://github.com/hasaanhameed/Darya/pull/1)** (Hasaan or Ali). It targets `feat/satellite-ingestion`, so it shows only the PMD commits. Once that branch is merged into `main`, retarget the pull request to `main`.
1. **Verify the station coordinates and basin tags** in `rain_stations.csv` against an official PMD station list or a map, then re-run the load. They are approximate (about ±0.05°) and came from general knowledge, not from PMD. The doubtful basin tags are listed in `docs/DATA.md`.
2. **Check the review files by hand:**
   - the 5 `extreme_rainfall` values: Dir 422.5 mm, Islamabad 591.9 mm (real, the 2001 cloudburst), Jacobabad 305 mm, Moenjodaro 990 mm (almost certainly wrong) and Murree 323.4 mm;
   - the 28 differing duplicate months (Quetta (SM) and Islamabad Bokra);
   - the 80 non-zero values on days that don't exist.
   If a rule changes, update ADR-024 and `docs/DATA.md` first.
3. **Ask PMD (through our advisor):**
   - which 24 hours a rainfall "day" covers (assumed 08:00–08:00 PKT, unconfirmed);
   - whether `-1` and `0.01` mean trace rain;
   - what the suffixes in `CHAKWAL (MUR)` and `QUETTA (SM)` mean;
   - whether Garhi Dopatta and Kotli values are interpolated (they are flagged `not_gauge_precision`).
4. **Link stations to the river network.** Use the node catchments from ADR-022 (`scripts/build_node_catchments.py`) to find which node catchment each station falls in. That replaces the hand-made `basin` tag and needs a new ADR and migration.

## Merging with the satellite branch
- **Our branch already contains Hasaan's commits.** Merging it into `main` brings in his work too. If he merges `feat/satellite-ingestion` first, ours still merges cleanly on top.
- **The shared dev database is on our migration `38e33b60eddb`** (after Hasaan's `bac4c793a2cb`). If anyone adds a migration on another branch, set its `down_revision` to `38e33b60eddb` (check with `alembic heads`; there must be only one head).
- **The next ADR number is ADR-025.**
- Expect conflicts in `docs/DATA.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/FLOW.md` and `apps/backend/CLAUDE.md` if both branches keep changing them. Keep both sides.
- **The branch is pushed** and tracks `origin/feat/pmd-rainfall-ingestion` (not Hasaan's branch), so `git push` from it only updates this pull request.
