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
- [ ] Scaffold the backend (FastAPI app, settings, DB connection, Alembic) and frontend (Next.js)
- [ ] Write the WAPDA parser and load Jul 2022 – Oct 2026 into PostgreSQL

## Log
- **2026-10-18**: Surveyed all 54 extracted WAPDA workbooks (1,319 day sheets). Updated the quality issues and parsing rules in `docs/DATA.md`, and recorded the scope and cleaning rules as ADR-010.
- **2026-10-15**: Initialized the context docs (README, CLAUDE.md files, docs/*), `.gitignore` and `app/backend/requirements.txt`. Surveyed the WAPDA raw data: 59 workbooks, about 1,262 valid days between Jul 2022 and Oct 2026. Structure and quality issues are in `docs/DATA.md`.
- **Before 2026-10-15**: Proposal approved. WAPDA daily hydel synopsis data obtained for Jul 2022 – Oct 2026.
