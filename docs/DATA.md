# Data

This file lists every data source Darya uses or plans to use. It also documents the structure of the raw data we already have.
Raw data is **not in git**. Get it from the team drive and place it under `data/<source>/`.
**Never edit raw files.** Write anything you derive to a separate folder, e.g. `data/<source>/extracted/` or `data/processed/`.

## Source catalog
| Source | Provides | Coverage | History / cadence | Access | Status |
|---|---|---|---|---|---|
| **WAPDA Hydel Synopsis** | Reservoir level, inflow and outflow at WAPDA dams and barrages | Tarbela, Ghazi Barotha, Mangla, Warsak, Chashma, Jinnah, Gomal Zam | Daily, Jul 2022 – Oct 2026 (with gaps) | Spreadsheets received from WAPDA | **Obtained** |
| PMD-FFD | River discharge and flood category at key sites; flood thresholds | Main rivers, incl. the Chenab, Ravi, Sutlej and lower Indus barrages | Live map; PDF bulletins 2024–25 | ffd.pmd.gov.pk (no public API found) | To investigate |
| FFC Daily Flood Situation Report | Inflow, outflow and flood class per structure | Main dams and barrages | Daily PDFs (seen for the 2022–23 monsoons) | `ffc.gov.pk/wp-content/uploads/YYYY/MM/DFSR-DD-MM-YYYY.pdf` | To investigate |
| IRSA daily flows | Rim-station inflows and barrage flows | Tarbela, Mangla, Nowshera, Marala, Indus barrages | Daily | pakirsa.gov.pk (unreachable during research); republished in news | To investigate |
| Historical gauge records | Long gauge history (2015 onward) | All prototype nodes | Daily | Formal request to FFD/WAPDA through our advisor | To request (first M1 task) |
| GloFAS reanalysis | Modelled daily river discharge (m³/s) | Global, 0.05° grid | 1979 – near real time | Copernicus **EWDS**, `cdsapi` | Planned (history fallback) |
| Sentinel-1 SAR | Radar backscatter that sees through cloud, for water detection | Global, 10 m | 6-day repeat (S1C+S1D); 12-day during 2022–25 | CDSE / Planetary Computer / GEE / ASF | Planned |
| Sentinel-2 | Optical imagery for checking water maps on clear days | Global, 10–20 m | ~5 days | CDSE / Planetary Computer / GEE | Planned |
| GPM IMERG | Satellite rainfall | Global, 0.1°, half-hourly / daily | 2000 onward | NASA GES DISC, `earthaccess` | Planned |
| HydroRIVERS | River network with flow direction | Global vector | Static | hydrosheds.org | Planned (river graph) |
| JRC Global Surface Water | Where water is normally present | Global, 30 m | 1984–2021 (v1.4) + 2022–24 | JRC download / GEE | Planned (channel mask) |
| Sen1Floods11 | Labelled Sentinel-1 flood chips for training U-Net | 11 global events | Static, ~14 GB | `gs://sen1floods11` | Planned |

---

## WAPDA: Daily Hydel Operational Synopsis

### What it is
WAPDA publishes a daily report on its hydropower operations. Most of each report covers generation, which we don't need. Each report also has a reservoir and flow block for the dams and barrages, and that block is the part Darya uses.

### Archive layout
```
data/wapda/
  2022-23 (1).rar   2023-24.rar   2024-25.rar   2025-26.rar   2026-27.rar
```
- Each `.rar` holds one folder per fiscal year (Jul–Jun), e.g. `2024-25/`, containing about 12 workbooks. There are 59 workbooks in total.
- To extract on Windows, run `tar -xf "data/wapda/2024-25.rar" -C data/wapda/extracted`. The built-in bsdtar can read RAR.
- File names follow the pattern `<MONTH>- <YYYY> (<n>).xls[x]`, but the spelling, case and spacing vary, e.g. `JULY - 2022 (31).xlsx`, `April-2024 (30).xls`, `FEB- 2026  (28).xls`.
  - `<n>` is the number of days in the month, or the last day covered (e.g. `OCT- 2026 (07)`).
  - Parse the month and year from the name case-insensitively.

### Workbook types
| Type | Where | Sheets | Use |
|---|---|---|---|
| **Monthly workbook** | Most files (`.xls` from 2023; `.xlsx` in 2022) | `Comparison`, `Monthly`, `Peak`, `Summary`, then **`1`…`31` (one sheet per day)**, then `Sheet1`–`Sheet5` | Day sheets only |
| **Single-day workbook** | `July-2023 (30)`, `Oct-2023 (31)`, `Dec-2023 (31)`, `Daily data July- 2026 (25…31)` | `Main`, **`Synopsis`**, `Ministry`, `Hydel`, `Chairman`, `MP` | `Synopsis` (same layout as a day sheet). `Hydel` and `Chairman` are useful for cross-checking |

Do **not** use `Summary`, `Monthly`, `Comparison` or `Peak`. Their header dates are stale (2021), and their rows are mis-ordered or full of typos.
`Sheet1`–`Sheet5` are template leftovers containing data from 2018–19.

### Day-sheet layout (the source of truth)
**Header**
- Cell `AG1` holds `DATA FOR:` and cell `AI1` holds the **reporting date**. The date can be stored as an Excel serial, a datetime, or a `dd-mm-yyyy` string.
- `AM1` holds the weekday.
- `B46` holds the issue date, which is normally the following day.

**Station block.** The header is on rows 12–14 and the stations are on rows 15–22, in this order:
1. `TARBELA`
2. `T-4 EXT:` (Tarbela 4th extension, generation only)
3. `GHAZI BAROTHA` (also written `G/BAROTHA`)
4. `MANGLA`
5. `WARSAK`
6. `CHASHMA`
7. `JINNAH`
8. `GOMAL ZAM`

| Col | Field | Unit | Notes |
|---|---|---|---|
| A | Station name | | Match by name and trim whitespace |
| B | Reservoir/pond level, **today** | ft | Above sea level (ft SPD). Warsak and Jinnah are nearly constant (pondage) |
| D | Level, **last year** (same date) | ft | |
| E | Irrigation indent | cusecs | Often **free text**: `1 Feet Rise`, `10000 (Hourly)`, `8000 (Thal Canal only)`, `IF=OF/ Maint level 1550'`. Keep it as raw text |
| I | **Inflow**, today | cusecs | |
| K | Inflow, last year | cusecs | |
| N | Outflow through turbines | cusecs | |
| Q | Outflow through irrigation, spillway or tunnels | cusecs | Spillway use shows up here |
| U | **Total outflow**, today | cusecs | Should equal N + Q |
| W | Total outflow, last year | cusecs | |
| Y–AP | Capability, max load, generation, load and plant factors | MW, GWh, % | Not needed for hydrology |
| AQ–BC | WAPDA internal check columns (`Logic`, `Review/Next`) | | Ignore |

**Other areas of the sheet**
| Rows | Content | Use |
|---|---|---|
| 25–50 | Unit-wise generation, peak sharing, cumulative energy | Ignore |
| ~52–75 | Free-text outage remarks per station | Optional. Sometimes mentions spillway operation or floods, e.g. "Auxiliary spillways in operation…" |
| ~83–95 | Old "Outflows / Remarks" table with 2014 text and formula errors | Ignore |

**Single-day extras**
- `Hydel` is a clean table of level (ft), inflow, outflow (cusecs) and **live storage (MAF)** for Tarbela, Mangla and Chashma.
- `Chairman` gives the same values next to last year and the 5-year average.

### Glossary
| Term | Meaning |
|---|---|
| **cusecs (cfs)** | ft³/s. 1 cusec ≈ 0.0283 m³/s. FFD flood limits are in thousands of cusecs |
| **ft SPD** | Reservoir level in feet above datum. Tarbela ranges ~1,400–1,550 ft and Mangla ~1,040–1,242 ft (to verify) |
| **MAF** | Million acre-feet of storage |
| **Irrigation indent** | The release IRSA requests for irrigation |
| **T-4 / T-5** | Tarbela 4th/5th extension power houses (generation only) |
| **NJHP** | Neelum–Jhelum hydropower project |

### Coverage
Counts are days whose `DATA FOR:` date matches the expected date (the month from the file name plus the day from the sheet name). There are **about 1,262 valid days out of 1,560** between 1 Jul 2022 and 7 Oct 2026.

| Year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2022 | | | | | | | 31 | 29 | 30 | 31 | 30 | – |
| 2023 | 26 | – | – | – | – | 28 | 1 | ✗ | 30 | 1 | 24 | 1 |
| 2024 | 31 | 29 | 31 | 30 | 31 | 30 | 31 | 31 | 27 | 31 | 28 | 31 |
| 2025 | 31 | 28 | 31 | 30 | 30 | 30 | 31 | 31 | 29 | 31 | 30 | 31 |
| 2026 | 31 | 28 | 31 | 30 | 31 | 30 | 30 | 29 | 29 | 7 | | |

Key: `–` means no file, `✗` means the file is corrupt, and `1` means a single-day workbook only.

**Back-filling:** the *last year* columns (D, K, W) give level, inflow and outflow for the same date one year earlier. They can partly fill these gaps (e.g. Feb–May 2023 from the 2024 sheets) and give data for Jul 2021 – Jun 2022.

### Known quality issues
- **Template leftovers:** sheet `31` in a 30-day month and sheets `29`–`31` in February hold the previous month's data. `Sheet4` and `Sheet5` hold 2018–19 data.
- **Stale copies:** some day sheets were never updated and still hold an earlier day's data. The `DATA FOR:` date gives them away. Known cases:
  - Nov 2023 days 8, 9, 15 and 22–24 (October data)
  - Jan 2023 days 6, 7, 22, 24 and 28
  - Aug 2026 days 10–11 (identical to July)
  - Jul 2026 days 13 and 25–31 in the monthly file (2025 data). Days 25–31 exist as separate daily files.
  - Oct 2026 days 8–31 (September data)
  - Other single-day mismatches: Jun 2023 days 23–24, Sep 2024 days 21/27/28, Nov 2024 days 7/27, May 2025 day 17, Sep 2026 day 3
- **Date typos:** sometimes the date cell is wrong but the data is genuine. For example, Sep 2025 sheet `6` is dated 2025-09-05 but holds data different from sheet `5`.
  - Rule: a mismatched sheet is a stale copy if its values match the sheet for the date it claims. Otherwise flag it for review.
- **Corrupt file:** `2023-24/AUG- 2023 (31).xls` is a truncated OLE file and cannot be opened.
- **Manual typos:** e.g. a Mangla level written `121.3` instead of ~1213, or `120.4.95` stored as text. There are also `#REF!` and `#DIV/0!` errors in some cells.
- **Layout drift:** the Aug 2026 sheet `12` is shifted down by one row, and a stray numeric row sometimes appears after `GOMAL ZAM`.

### Parsing rules
1. Read only the day sheets (`1`…`31`) and `Synopsis`.
2. The expected date comes from the file name's month and year plus the sheet name's day. Skip day numbers that don't exist in that month.
3. Read the `DATA FOR:` cell. If it doesn't match the expected date, mark the row `date_mismatch` and don't use it for training until it has been reviewed.
4. Locate the header row by finding `POWER STATIONS` in column A. Then find station rows **by name**, normalising aliases (`G/BAROTHA` → `ghazi_barotha`, `T-4 EXT:` → `tarbela_t4`).
5. Coerce values to numbers. Keep the raw text when coercion fails. Check ranges per station (level band, flow ≥ 0, `total ≈ turbine + other`).
6. Flag problems; don't drop them silently. Each record carries its `source_file`, `sheet` and the list of issues found.

### Target normalized record
One row per station per day:
```
station, date, level_ft, level_ft_last_year,
inflow_cfs, inflow_cfs_last_year,
outflow_turbine_cfs, outflow_other_cfs, outflow_total_cfs, outflow_total_cfs_last_year,
indent_raw, source_file, sheet, date_in_sheet, flags
```

### Fit with the prototype scope
**Covered:**
- Upper Indus: Tarbela → Ghazi Barotha → Jinnah → Chashma
- Kabul: Warsak
- Jhelum: Mangla

**Not covered:**
- The Chenab, Ravi and Sutlej
- Nowshera
- Rasul
- Taunsa, Guddu, Sukkur and Kotri

These nodes need FFD, FFC, IRSA or the historical-records request.

**History gap:** WAPDA history starts in Jul 2022, but the proposal wants data from 2015. GloFAS reanalysis is the fallback for training.

---

## Other sources: notes
Claims marked *(to verify)* came from desk research and have not been confirmed yet.

### PMD Flood Forecasting Division (FFD)
- River state map (`/river-state`), flood dashboard, historical peaks and annual flood reports.
- PDF bulletin archive covering 2024–25 only. No public JSON API was found, so we would need to look for an endpoint the site itself uses *(to verify)* and check its terms of use.
- An old site (`pmd.gov.pk/FFD/...`) has monthly HTML sheets going back to about 2015, at least for the Tarbela and Mangla reservoirs *(to verify)*.
- **The flood limits page (`/flood-limits`) is what Darya's risk levels map to.** The table below gives discharge thresholds in thousands of cusecs:

| Sites | Low | Medium | High | Very High | Exceptional |
|---|---|---|---|---|---|
| Tarbela, Attock, Kalabagh, Chashma, Taunsa | 250 | 375 | 500 | 650 | 800 |
| Guddu, Sukkur | 200 | 350 | 500 | 700 | 900 |
| Kotri | 200 | 300 | 450 | 650 | 800 |
| Warsak | 40 | 60 | 100 | 150 | – |
| Nowshera | 60 | 90 | 140 | 200 | – |
| Mangla, Rasul | 75 | 110 | 150 | 225 | 300 |
| Marala, Khanki, Qadirabad | 100 | 150 | 200 | 400 | 600 |
| Trimmu | 150 | 200 | 300 | 450 | 600 |
| Panjnad | 150 | 250 | 400 | 550 | 700 |
| Jassar (Ravi) | 50 | 75 | 100 | 150 | 200 |
| Shahdara, Balloki | 40 | 65 | 90 | 135 | 180 |
| Sidhnai | 30 | 46 | 60 | 90 | 130 |
| Sulemanki, Islam | 50 | 80 | 120 | 175 | 225 |

These figures were taken from the FFD page in Oct 2026. Re-check them against the live page before relying on them.

### FFC / IRSA / provincial irrigation
- **FFC daily flood situation reports:** PDFs with a table per structure listing inflow, outflow and flood class. Best structured source found so far for the barrages that WAPDA doesn't cover. Whether they are issued year-round, and how far back they go, is *(to verify)*.
- **IRSA:** publishes daily rim-station and barrage flows. Its site was unreachable during research; the same figures are republished in news articles.
- **Sindh Irrigation "Daily Discharge Reporting System":** covers Guddu, Sukkur and Kotri *(format to verify)*.
- **Reading time:** barrage values are usually gauge readings taken at 06:00, not daily means. Record which kind each value is.

### GloFAS (Copernicus Emergency Management Service)
- **Datasets:** `cems-glofas-historical` (daily, 0.05°, 1979 to near real time) and `cems-glofas-forecast` (ensemble out to 30 days).
- **Access:** through the **EWDS** with `cdsapi` (url `https://ewds.climate.copernicus.eu/api`). It needs a separate account, and the dataset licence must be accepted per dataset.
- **Versions:** v5.0 of the reanalysis was released in 2026, while the forecast product is still on v4.0. **Pin one version and never mix them.**
- **Node matching:** snap each node to the right grid cell using the upstream-area file.

### Sentinel-1 / Sentinel-2
- **Sentinel-1 constellation:**
  - Sentinel-1A was retired in Jun 2026. 1C and 1D now give a 6-day repeat.
  - Between Dec 2021 and 2025 only 1A was flying, so the 2022 floods have a **12-day** revisit.
- **Where to get Sentinel-1 data:**
  - Copernicus Data Space (CDSE): GRD via STAC or openEO, with terrain correction available on demand.
  - Planetary Computer `sentinel-1-rtc`: ready terrain-corrected (RTC) data, CC-BY-4.0, account needed. S1D was not listed *(to verify)*.
  - GEE `COPERNICUS/S1_GRD`: values in dB, orthorectified but **not** terrain-corrected.
  - ASF HyP3: on-demand RTC.

### GPM IMERG
- **Current version:** V07. The Early run arrives in ~4 h, Late in ~14 h, and Final after ~3.5 months.
- **Access:** short names `GPM_3IMERGDE`, `GPM_3IMERGDL` and `GPM_3IMERGDF` through `earthaccess`. A free Earthdata login is required.
- **Version transition:** V07 is moving to V08 during 2026–27. **Don't mix versions.** Record the run and version with every value.

### HydroRIVERS, Global Surface Water, Sen1Floods11
- **HydroRIVERS v1.0:** Asia shapefile (~91 MB). Free with attribution. Used to build the river graph and draw reach geometry.
- **JRC Global Surface Water:** 30 m tiles or GEE `JRC/GSW1_4/*`. Used as the normal-water mask so permanent water isn't counted as floodwater. Cite Pekel et al. (2016).
- **Sen1Floods11:** `gsutil -m rsync -r gs://sen1floods11 <dir>`. 512×512 chips of S1 VV/VH, 446 hand-labelled. Cite Bonafilia et al. (2020).

## Prototype nodes (approximate)
These coordinates are approximate to about ±0.05°. Confirm them against HydroRIVERS or a map before using them.

| Node | River | Lat | Lon | WAPDA? |
|---|---|---|---|---|
| Tarbela | Indus | 34.09 | 72.69 | ✓ |
| Ghazi Barotha | Indus | 33.98 | 72.65 | ✓ |
| Jinnah (Kalabagh) | Indus | 32.92 | 71.52 | ✓ |
| Chashma | Indus | 32.43 | 71.38 | ✓ |
| Taunsa | Indus | 30.51 | 70.85 | |
| Guddu | Indus | 28.42 | 69.71 | |
| Sukkur | Indus | 27.68 | 68.85 | |
| Kotri | Indus | 25.44 | 68.32 | |
| Warsak | Kabul | 34.17 | 71.36 | ✓ |
| Nowshera | Kabul | 34.01 | 71.98 | |
| Mangla | Jhelum | 33.14 | 73.64 | ✓ |
| Rasul | Jhelum | 32.68 | 73.52 | |
| Marala | Chenab | 32.67 | 74.46 | |
| Khanki | Chenab | 32.41 | 73.97 | |
| Qadirabad | Chenab | 32.32 | 73.69 | |
| Trimmu | Chenab | 31.14 | 72.15 | |
| Balloki | Ravi | 31.22 | 73.86 | |
| Sidhnai | Ravi | ~30.6 | ~72.1 | |
| Sulemanki | Sutlej | 30.38 | 73.87 | |
| Islam | Sutlej | 29.83 | 72.55 | |
| Panjnad | Panjnad | 29.35 | 71.02 | |

The directed edges between these nodes are listed in `docs/ARCHITECTURE.md`.
