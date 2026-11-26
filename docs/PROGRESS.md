# Progress

This file tracks where the project stands.

**How to use it**
- Add log entries at the **top** of the Log section, with a date and your name.
- Keep each entry to one or two lines: what was done, plus a link or path if useful.
- Update the milestone status when it changes.
- Record decisions in `docs/DECISIONS.md`, not here.

## Milestones
| # | Phase | Dates | Deliverables | Status |
|---|---|---|---|---|
| M1 | Research and design | Oct – Nov 2026 | Literature review, confirmed data sources, system design, data request sent | In progress |
| M2 | Data and satellite pipeline | Dec 2026 – Jan 2027 | Working data collection, database, first water detection, simple end-to-end demo, FYP-I report | Not started |
| M3 | Forecasting models | Feb – Mar 2027 | Baseline models, trained GNN, first comparison results | Not started |
| M4 | Dashboard and integration | Apr – May 2027 | Next.js dashboard, risk view and alerts, all modules connected | Not started |
| M5 | Testing and final demo | Jun 2027 | Final evaluation, user feedback, final report, live demo | Not started |

The first priority is a thin end-to-end slice: one river, one data source of each type, basic water detection, a simple forecast and a basic map. After that, each part is improved on its own. The team works in two-week iterations, with an advisor review at the end of each one.

## Ownership
| Member | Data and satellite | Forecasting models | Web platform |
|---|---|---|---|
| M. Ali Mubashir | Data collection pipeline | Baseline models | Python backend |
| Rohail Najmi | Satellite water detection | GNN model | Next.js dashboard |
| Hasaan Hameed | Database and cleaning | Testing and evaluation | Alerts and risk view |

## Next up
- [ ] Send the historical gauge data request (2015 onward) to FFD/WAPDA through our advisor
- [ ] Confirm the data sources and access accounts: Copernicus EWDS, CDSE or Planetary Computer, NASA Earthdata
- [ ] Decide on the proposed ADRs that block M2 (PostGIS, scheduler, Sentinel-1 platform)
- [ ] Scaffold the backend (FastAPI app, settings, DB connection, Alembic)
- [ ] Frontend: time slider, `/alerts` page, then the node, reach, sources, about, evaluation, terms and privacy pages
- [x] Write the WAPDA parser and load Jul 2022 – Oct 2026 into PostgreSQL
- [ ] WAPDA back-fill from the "last year" columns (467 missing days, see `docs/DATA.md`)
- [x] Satellite and model ingestion phase 0: all nodes seeded, geo libraries, ADR-019/020
- [ ] Phase 1: GloFAS v4.0 reanalysis (2015 onward) into `glofas_discharge`
- [ ] Phase 2: IMERG Late catchment rainfall into `imerg_rainfall`
- [ ] Phase 3: Sentinel-1 water extent per reach (needs reach and PostGIS decisions first)
- [x] PMD rainfall: load 1981–2015 into `rain_stations` and `pmd_rainfall` (branch `feat/pmd-rainfall-ingestion`)
- [ ] PMD rainfall: manual check of the 5 `extreme_rainfall` values and the review files in `data/pmd/processed/`
- [ ] PMD rainfall: link each station to the node catchments (ADR-022), replacing the hand-made `basin` tag
- [ ] **Before modelling with PMD rainfall:** verify station coordinates and basin tags in `app/ingest/pmd/rain_stations.csv`, and ask PMD about the rainfall-day window and trace codes (checklist in `docs/DATA.md`, PMD section)
- [ ] Discuss the data-source review findings below as a team, and record what we accept in `docs/DECISIONS.md`

## Data-source review: open findings (2026-11-10)
An independent review checked the planned sources (table in `docs/DATA.md`). Nothing is a wrong choice, but there are gaps: Indus summer flow is driven mostly by **snow and glacier melt** and by **dam operations**, and our list mostly covers rainfall and satellite images. **These are suggestions, not decisions.** Some claims are still unverified (Sentinel-1 coverage over Pakistan, whether FFD/IRSA archives exist).
- **Add weather forecasts and melt data.** IMERG only shows rain that has already fallen. Candidates: ECMWF open forecasts (rain and temperature for the next days, free since 2025), ERA5-Land temperature history, and VIIRS snow cover.
- **Use GloFAS carefully.** It is weak below the dams, where flow depends on release decisions. Use it mainly for the rivers flowing *into* the dams (above Tarbela, Kabul, Jhelum and Chenab inflows). Use the same GloFAS version for training and live runs, and never feed values a live system wouldn't have yet.
- **Training history is our biggest weakness.** WAPDA starts in 2022, and 2022 and 2025 are held out, leaving about 3 monsoons to train on. More measured history from FFD or IRSA reports is the best fix, so the data request is urgent.
- **Sentinel-1 is for flood mapping, not forecasting.** Its 6-day repeat only started in mid-2026; the 2022 flood had about 14 passes in 6 weeks.
- **Copernicus GFM** publishes free flood maps from every Sentinel-1 image since 2015. Use it as a benchmark and for its masks.
- **Build the ~20-node river graph by hand,** including link canals, which HydroRIVERS doesn't have. Use HydroRIVERS only to check it.
- **JRC's normal-water map ends in 2021.** Use its seasonal layer, or a dry-season Sentinel-1 image instead.
- **For the later water-detection model,** consider Kuro Siwo, which is much larger than Sen1Floods11.

## Log
- **2026-11-26** (Rohail): Loaded the PMD daily rainfall history (1981–2015) into the dev DB: 120 stations in `rain_stations` and 651,552 rows in `pmd_rainfall` (116 stations with data), with flags. Survey, rules and results in `docs/DATA.md`; ADR-023 (storage) and ADR-024 (cleaning). Command: `python -m scripts.ingest_pmd` from `apps/backend`. Station coordinates are approximate; verify them before modelling. Next steps: `docs/handovers/pmd-rainfall.md`.
- **2026-11-22** (Hasaan): Satellite and model ingestion phase 0. Seeded all 21 prototype nodes, added the geo and source-client libraries (all install on Python 3.14), and optional source credentials in settings. ADR-019 (one table per source) and ADR-020 (xarray and geo libraries). Next: GloFAS (phase 1).
- **2026-11-10** (Hasaan): Ran an independent review of the planned data sources. Added a "what each source is for" table to `docs/DATA.md` and the open findings above.
- **2026-10-18** (Hasaan): Loaded the WAPDA history into `daily_observations` on the dev DB: 7,668 rows (1,278 days × 6 stations, Jul 2022 – Oct 2026), with flags. Command: `python -m scripts.ingest_wapda` from `apps/backend`.
- **2026-10-18** (Rohail): Scaffolded the frontend in `apps/frontend`: the map dashboard with the river schematic, active alerts and reach panel (threshold staff and forecast chart). It uses sample data until the API exists. Frontend stack is ADR-010 to ADR-016, and the design system is in `apps/frontend/DESIGN.md`.
- **2026-10-18** (Hasaan): Surveyed all 54 extracted WAPDA workbooks (1,319 day sheets). Updated the quality issues and parsing rules in `docs/DATA.md`, and recorded the scope and cleaning rules as ADR-017.
- **2026-10-15**: Initialized the context docs (README, CLAUDE.md files, docs/*), `.gitignore` and `app/backend/requirements.txt`. Surveyed the WAPDA raw data: 59 workbooks, about 1,262 valid days between Jul 2022 and Oct 2026. Structure and quality issues are in `docs/DATA.md`.
- **Before 2026-10-15**: Proposal approved. WAPDA daily hydel synopsis data obtained for Jul 2022 – Oct 2026.
