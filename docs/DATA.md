# Data

This file lists every data source Darya uses or plans to use. It also documents the structure of the raw data we already have.
Raw data is **not in git**. Get it from the team drive and place it under `data/<source>/`.
**Never edit raw files.** Write anything you derive to a separate folder, e.g. `data/<source>/extracted/` or `data/processed/`.

## Source catalog
| Source | Provides | Coverage | History / cadence | Access | Status |
|---|---|---|---|---|---|
| **WAPDA Hydel Synopsis** | Reservoir level, inflow and outflow at WAPDA dams and barrages | Tarbela, Ghazi Barotha, Mangla, Warsak, Chashma, Jinnah (Gomal Zam dropped, ADR-017) | Daily, Jul 2022 – Oct 2026 (with gaps) | Spreadsheets received from WAPDA | **Obtained** |
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
- Each `.rar` holds one folder per fiscal year (Jul–Jun), e.g. `2024-25/`, containing up to 12 workbooks. There are **54 workbooks** in total (7 in 2022-23, 12 each in 2023-24 to 2025-26, 11 in 2026-27). About 104 MB extracted, almost all of it generation data we don't use.
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
8. `GOMAL ZAM` (dropped, see ADR-017)

The header is on row 12 in every sheet except Aug 2026 sheet `12`, which is shifted down one row.

| Col | Field | Unit | Notes |
|---|---|---|---|
| A | Station name | | Match by name and trim whitespace |
| B | Reservoir/pond level, **today** | ft | Above sea level (ft SPD). Warsak and Jinnah are nearly constant (pondage) |
| D | Level, **last year** (same date) | ft | |
| E | Irrigation indent | cusecs | Often **free text**: `1 Feet Rise`, `10000 (Hourly)`, `8000 (Thal Canal only)`, `IF=OF/ Maint level 1550'`. Keep it as raw text |
| I | **Inflow**, today | cusecs | |
| K | Inflow, last year | cusecs | |
| N | Outflow through turbines | cusecs | The T-4 EXT row holds only this column: T-4's turbine flow |
| Q | Outflow through irrigation, spillway or tunnels | cusecs | **Unreliable in floods:** spillway flow is often not entered here |
| U | **Total outflow**, today | cusecs | **The outflow figure to trust.** Usually N + Q; for Tarbela, N + Q + T-4's N. In floods it can be far larger than N + Q (Chashma, 28 Aug 2022: 516,468 vs 17,433) |
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
Counts are days whose `DATA FOR:` date matches the expected date (the month from the file name plus the day from the sheet name). **1,262 of the 1,319 day sheets** match, out of 1,560 calendar days between 1 Jul 2022 and 7 Oct 2026 (survey of 2026-10-18).

| Year | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2022 | | | | | | | 31 | 29 | 30 | 31 | 30 | – |
| 2023 | 26 | – | – | – | – | 28 | 1 | ✗ | 30 | 1 | 24 | 1 |
| 2024 | 31 | 29 | 31 | 30 | 31 | 30 | 31 | 31 | 27 | 31 | 28 | 31 |
| 2025 | 31 | 28 | 31 | 30 | 30 | 30 | 31 | 31 | 29 | 31 | 30 | 31 |
| 2026 | 31 | 28 | 31 | 30 | 31 | 30 | 30 | 29 | 29 | 7 | | |

Key: `–` means no file, `✗` means the file is corrupt, and `1` means a single-day workbook only.

**Back-filling:** the *last year* columns (D, K, W) give level, inflow and outflow for the same date one year earlier.
- They agree with the real value from a year earlier in 97% (level), 93% (inflow) and 97% (total outflow) of the cases that can be checked.
- They can fill **467 days** with no direct sheet: Jul 2021 – Jun 2022, Feb–May 2023, Jul 2023, Aug 2023 (the corrupt file), Oct 2023, Dec 2023 and a few single days.

### Known quality issues
Survey of 2026-10-18 over all 1,319 day sheets.
- **Template leftovers:** sheet `31` in a 30-day month and sheets `29`–`31` in February hold the previous month's data. `Sheet4` and `Sheet5` hold 2018–19 data.
- **Mis-dated sheets (57).** The `DATA FOR:` date doesn't match the expected date. They fall into three groups:
  - **Stale copies (41):** identical to the sheet for the date they claim. They are Aug 2022 day 31; Jan 2023 days 6 and 24; Nov 2024 days 7 and 27; Sep 2024 day 28; Jul 2026 days 13 and 25–31 in the monthly file (2025 data; days 25–31 also exist as separate daily files); Aug 2026 days 10–11; Sep 2026 day 3; and Oct 2026 days 8–31.
  - **One-day date typos (4):** the date is one day early, but the data differs from that day's sheet, so the data is genuine. They are Sep 2024 days 21 and 27, May 2025 day 17 and Sep 2025 day 6.
  - **Copies from months with no file (12):** they claim a date for which we have no real sheet, so they are probably genuine data for that claimed date. They are Nov 2023 days 8, 9, 15 and 22–24 (October data); Jan 2023 days 7, 22 and 28 (December 2022 data); Jun 2023 day 24 (May data); and Jun 2023 day 23 and Aug 2022 day 30 (both claim the next day).
- **Hidden copy:** Apr 2025 days 14 and 15 are identical, even though both carry correct dates. Only a value comparison catches this.
- **Typos (57 values across the 6 kept stations, under 1%):** decimal slips and missing or extra digits, e.g. Tarbela inflow `1107000`, Chashma level `6486`, Mangla level `121.3`, Warsak level `0.5`, and negative inflows. Some are on flood peaks. A few cells are unparseable text (`120.4.95`, `15.49.27`, `1076..30`, `46+464`), and some hold `#REF!` or `#DIV/0!`.
- **Gomal Zam** is the noisiest station. It has a repeated placeholder level (`2084.98`) and some flows converted from m³/s (`35.3147` = 1 m³/s). It was dropped in ADR-017.
- **Corrupt file:** `2023-24/AUG- 2023 (31).xls` is a truncated OLE file and cannot be opened.
- **Layout drift:** the Aug 2026 sheet `12` is shifted down by one row, with a stray `DATA FOR: -1` on row 1 above the real date on row 2. A stray numeric row sometimes appears after `GOMAL ZAM`.
- **Date cell formats:** a datetime (939 sheets), an Excel serial number (286) or a `dd-mm-yyyy` string (111).

### Parsing rules
These follow ADR-017.
1. Read only the day sheets (`1`…`31`) and `Synopsis`.
2. The expected date comes from the file name's month and year plus the sheet name's day. For a single-day workbook, the day is the `(n)` in its file name. Skip day numbers that don't exist in that month.
3. Locate the header row by finding `POWER STATIONS` in column A. Then find station rows **by name**, normalising aliases (`G/BAROTHA` → `ghazi_barotha`, `T-4 EXT:` → `tarbela_t4`). Stop after the station block.
4. Read the `DATA FOR:` date by searching above the header, not at a fixed cell, and take the first value that is a real date. When it doesn't match the expected date:
   - If the sheet is identical to the sheet for its claimed date, it is a stale copy. Skip it.
   - If the claimed date has no real sheet, use the claimed date and flag the row `date_from_sheet`.
   - Otherwise the claimed date has its own, different data, so the date cell is a typo. Use the expected date and flag `date_typo`.
   - If no date can be read at all, use the expected date and flag `date_unreadable`.
5. Coerce values to numbers, keeping the raw text when coercion fails. Flag a value `suspect` when it jumps far from its neighbouring days or is negative. Never correct values.
6. Treat total outflow (U) as the outflow figure. A mismatch with turbine + other is only a note, because spillway flow is often missing from Q. T-4 is used only for this check on Tarbela.
7. Flag problems; don't drop them silently. Each record carries its `source_file`, `sheet` and the list of issues found.

### Flags
Each row in `daily_observations` has a `flags` list. Rows with any flag marked **exclude** must be left out of training and scoring.

| Flag | Meaning | Exclude? |
|---|---|---|
| `suspect_level_ft`, `suspect_inflow_cfs`, `suspect_outflow_total_cfs` | Far from the station's neighbouring days (level > 15 ft away from the 7-day median; flow > 3× and > 5,000 cfs away), or a negative flow. Value kept as written | **exclude** |
| `not_numeric_<field>` | The cell held text that isn't a number (e.g. `120.4.95`); the value is empty | **exclude** |
| `repeated_previous_day` | The whole sheet is identical to the previous day's | **exclude** |
| `date_from_sheet` | A sheet copied from a month with no file; stored under the date written in it | no |
| `date_typo` | The date cell was wrong; stored under the expected date | no |
| `date_unreadable` | No date could be read; stored under the expected date | no |
| `outflow_sum_mismatch` | Total outflow ≠ turbine + other (+ T-4 for Tarbela). Common in floods; total outflow is still trusted | no |

The first full run (2026-10-18) kept 7,668 rows (1,278 days × 6 stations).

### Fit with the prototype scope
**Covered:**
- Upper Indus: Tarbela → Ghazi Barotha → Jinnah → Chashma
- Kabul: Warsak
- Jhelum: Mangla

Gomal Zam is in the files but is dropped (ADR-017).

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
