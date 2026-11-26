# Data

This file lists every data source Darya uses or plans to use. It also documents the structure of the raw data we already have.
Raw data is **not in git**. Get it from the team drive and place it under `data/<source>/`.
**Never edit raw files.** Write anything you derive to a separate folder, e.g. `data/<source>/extracted/` or `data/processed/`.

## Source catalog
| Source | Provides | Coverage | History / cadence | Access | Status |
|---|---|---|---|---|---|
| **WAPDA Hydel Synopsis** | Reservoir level, inflow and outflow at WAPDA dams and barrages | Tarbela, Ghazi Barotha, Mangla, Warsak, Chashma, Jinnah (Gomal Zam dropped, ADR-017) | Daily, Jul 2022 – Oct 2026 (with gaps) | Spreadsheets received from WAPDA | **Obtained** |
| **PMD daily rainfall** | Daily rain-gauge totals (mm) at PMD weather stations | 121 station names across Pakistan (about 50 with records from the early 1980s, many only from 2012) | Daily, 1981 – 2015 (with gaps) | One workbook received from PMD | **Obtained** (one-time historical load) |
| PMD-FFD | River discharge and flood category at key sites; flood thresholds | Main rivers, incl. the Chenab, Ravi, Sutlej and lower Indus barrages | Live map; PDF bulletins 2024–25 | ffd.pmd.gov.pk (no public API found) | To investigate |
| FFC Daily Flood Situation Report | Inflow, outflow and flood class per structure | Main dams and barrages | Daily PDFs (seen for the 2022–23 monsoons) | `ffc.gov.pk/wp-content/uploads/YYYY/MM/DFSR-DD-MM-YYYY.pdf` | To investigate |
| IRSA daily flows | Rim-station inflows and barrage flows | Tarbela, Mangla, Nowshera, Marala, Indus barrages | Daily | pakirsa.gov.pk (unreachable during research); republished in news | To investigate |
| Historical gauge records | Long gauge history (2015 onward) | All prototype nodes | Daily | Formal request to FFD/WAPDA through our advisor | To request (first M1 task) |
| GloFAS reanalysis | Modelled daily river discharge (m³/s) | Global, 0.05° grid | 1979 – near real time | Copernicus **EWDS**, `cdsapi` | **Ingesting** (v4.0, 2015 onward; ADR-021) |
| Sentinel-1 SAR | Radar backscatter that sees through cloud, for water detection | Global, 10 m | 6-day repeat (S1C+S1D); 12-day during 2022–25 | CDSE / Planetary Computer / GEE / ASF | Planned |
| Sentinel-2 | Optical imagery for checking water maps on clear days | Global, 10–20 m | ~5 days | CDSE / Planetary Computer / GEE | Planned |
| GPM IMERG | Satellite rainfall | Global, 0.1°, half-hourly / daily | 2000 onward | NASA GES DISC via Harmony (`harmony-py`) | **Loading** (daily Late V07, 2015 onward; ADR-022) |
| HydroRIVERS | River network with flow direction | Global vector | Static | hydrosheds.org | Planned (river graph) |
| JRC Global Surface Water | Where water is normally present | Global, 30 m | 1984–2021 (v1.4) + 2022–24 | JRC download / GEE | Planned (channel mask) |
| Sen1Floods11 | Labelled Sentinel-1 flood chips for training U-Net | 11 global events | Static, ~14 GB | `gs://sen1floods11` | Planned |

### What each planned source is for
| Source | What it is | How often we ingest | What we use it for |
|---|---|---|---|
| **Sentinel-1** | Radar satellite, sees through cloud | Each new image over our area (about every 6 days since mid-2026; far fewer images in 2022) | Mapping where water is spreading. Not a forecast input |
| **GPM IMERG** | Rainfall from satellites | Every few hours | Spotting heavy rain upstream before it reaches the rivers |
| **GloFAS** | Computer-modelled river flow (not a satellite) | Daily | River flow for model input, and history for training (available from 1979; we need 2015 onward) |
| **Sentinel-2** | Optical satellite (normal photos) | Every new clear image (about every 5 days), optional | Checking the Sentinel-1 water maps on clear days |
| **JRC Global Surface Water** | Map of where water normally is | Once | Telling flood water apart from the usual river |
| **HydroRIVERS** | River network map | Once | Checking our river graph (which point flows into which) |
| **Sen1Floods11** | Labelled flood images | Once, when needed | Training the water-detection model (later) |

All of these are free; most need a free account. They feed the forecast, and WAPDA's dam data is what forecasts are checked against. The first version needs only Sentinel-1, IMERG and GloFAS. Open suggestions from the 2026-11-10 review are in `docs/PROGRESS.md`.

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

**History gap:** WAPDA history starts in Jul 2022, but the proposal wants data from 2015. GloFAS reanalysis (loaded from 2015, see "GloFAS" below) fills it with modelled flow, which misses the size of flood peaks.

---

## PMD: daily station rainfall (1981 – 2015)

### What it is
Daily rainfall measured by rain gauges at Pakistan Meteorological Department (PMD) weather stations. It is the only measured rainfall we have from before 2000 (IMERG starts in 2000), so it gives models a long history of how rain turns into river flow. It is **historical data, loaded once**, like WAPDA.

### File layout
```
data/pmd/
  DAILY RAIN - ALL STATIONS - 1981-2015.xls
```
- One legacy `.xls` workbook (9.6 MB) with two sheets.
- **`Sheet1` (the source of truth).** Row 1 is the header. Each later row is **one station-month**:

| Col | Header | Content |
|---|---|---|
| A | `STATION` | Station name, upper case (see "Stations" below) |
| B | `MONTH` | 1–12 |
| C | `YEAR` | 1981–2015 |
| D–AH | `1st` … `31st` | Rainfall for that day of the month |
| AI | `TOT` | `=SUM(D:AH)` formula. Not used |
| AJ | (no header) | Formula averages on 12 Peshawar 1998 rows only. Not used |

- There are 34,718 rows. They are **not sorted** by station or date.
- **`Sheet2`** holds monthly totals (`STATION`, `YEAR`, `MONTH`, `TOT`) for 56 of the stations. It is derived from `Sheet1`, so we don't use it.

### Units and the rainfall day
- **Units:** millimetres (mm). The file doesn't say so, but the values (median 0, 99th percentile 35 mm) only make sense in mm. Columns are named `rainfall_mm`.
- **The rainfall day:** the file doesn't say which 24 hours a "day" covers. PMD normally reports rain over the 24 hours ending at 08:00 PKT (03:00 UTC) *(to verify with PMD)*. We store the date exactly as written, as a `date`.

### Stations
- **121 names** in the file. Two are the same station written two ways: `GUJRANWALA` and `GUJRANWALA ` (trailing space), and `T.T.  SINGH` has a double space. Names are matched after trimming and collapsing spaces.
- Some spellings differ from the usual ones: `JACCOBABAD` (Jacobabad), `GARRHI DOPATTA` (Garhi Dupatta), `PAJNGUR` (Panjgur), `GAWADAR` (Gwadar), `SHAHEED BENAZIRABAD` (Nawabshah).
- The file has **no coordinates and no basin**. Approximate ones are kept in `apps/backend/app/ingest/pmd/rain_stations.csv` *(to verify)*, with a `basin` tag: `indus` (drains to the Indus system) or `outside` (Makran coast, Kharan and Thar deserts, closed basins in Balochistan).
- Lahore has many city gauges (`LAHORE, GULBERG`, `LAHORE, IQBAL TOWN`…), most with only 2015 data.

### Coverage
Days with a number, per station (survey of 2026-11-26):
- **About 50 stations have long records starting 1981–1986** (7,000–13,000 days each; 12,784 days is complete). They include Astore, Gilgit, Bunji, Skardu, Chitral, Balakot, Muzaffarabad, Garhi Dopatta, Kotli, Murree, Islamabad, Islamabad A/P, Peshawar, Cherat, Kohat, Parachinar, D.I. Khan, Zhob, Jhelum, Sialkot, Lahore (PBO), Faisalabad, Multan, Bahawalnagar, Khanpur, Hyderabad, Karachi (AP), Badin, Padidan and Chhor.
- **About 20 stations start between 2001 and 2007**, e.g. Chilas, Kalam, Malam Jabba, Saidu Sharif, Rawalakot, Sargodha, Jhang, M.B. Din, D.G. Khan, Kakul and Thatta.
- **About 40 stations only have data from 2011 or 2012 onward**, e.g. Lahore (A.P), Bannu, Hunza, Dadu, Sukkur, Sahiwal, Okara, Turbat and the Lahore city gauges.
- **Four stations have rows but no data at all:** Ziarat, Rahwali, Chakwal (MUR) and Karachi (Faisal), all 1981–2000.
- Most stations have rows for every year back to 1981 even where the cells are blank. Those template rows simply produce no observations.

### Cell values
On the days that exist in each month, the cells hold:

| Cell | Count | Meaning |
|---|---|---|
| A number | 650,648 | Rainfall in mm |
| Blank | 400,448 | **Missing**, not zero. Months with no data still show `TOT` = 0 |
| `----`, `---`, `-   ----` | ~4,970 | No reading (mostly 1981–2006) |
| `*`, `**` | ~400 | No reading (mostly 2011–2015) |
| `***` | 135 | Marks a day that doesn't exist, but here it is on a real day (e.g. 29 Feb in leap years, 29–31 Mar). Treated as no reading |
| Garbled text | ~100 | Looks like a broken fixed-width import, e.g. `.0   1`, `e   .0`, `0.1 ***`. Not readable |

`***` is the normal marker for days that don't exist (30 Feb, 31 Apr…).

### Known quality issues
Survey of 2026-11-26 over all 34,718 rows.
- **Numbers on dates that don't exist (735, 80 of them non-zero):** 29 Feb in non-leap years, 30–31 Feb and the 31st of 30-day months. A non-zero value there suggests the days in that month are shifted by one or more columns.
- **Duplicate station-months (153):** in 2012–2015, 13 stations (most KP stations, Quetta (SM), Islamabad Bokra, Rawalakot) have the same month twice. **125 pairs are identical; 28 differ.**
- **Negative values (45):** mostly `-0.1` (29, almost all Murree 1988) and `-1` (9), plus single `-0.4`, `-2.1`, `-4`, `-9`, `-16.8` and `-99`. `-1` may be a code for trace rain *(to verify with PMD)*.
- **`0.01` (821 values),** almost all at Islamabad (1981–2004) and D.I. Khan. Probably a trace code *(to verify)*. Kept as written.
- **Extreme values:** 13 values ≥ 250 mm. Some are real, such as **Islamabad 591.9 mm on 24 Jul 2001** (the 2001 cloudburst) and several 240–300 mm values on 5–6 Sep 2014 around Islamabad, Rawalpindi and Lahore. Others are clearly wrong, such as **Moenjodaro 990 mm on 5 Feb 1982**.
- **Values that look modelled:** Garhi Dopatta and Kotli have values with five to nine decimals on almost every day (e.g. `24.6876`, `0.00148744`). Gauges are read to 0.1 mm, so these are probably interpolated or modelled, not measured.

### Parsing rules
These follow ADR-024 (flag, never correct; the same spirit as ADR-017).
1. Read only `Sheet1`. Ignore `TOT`, column AJ and `Sheet2`.
2. Read every cell as text, exactly as written, and keep it as `rainfall_raw`.
3. Turn each row into one record per day. Normalise the station name (trim, collapse spaces) and match it to `rain_stations.csv`.
4. Skip days that don't exist in that month. Count them, and list any that hold a number in the review file.
5. Skip blank cells: no reading means no row.
6. Store every other cell: numbers as `rainfall_mm`, markers and garbled text with an empty `rainfall_mm` and a flag.
7. Identical duplicate station-months become one. For duplicates that differ, keep the first copy (lowest sheet row) and flag it.
8. Each record keeps `source_file` and `sheet_row` (the Excel row number) so any value can be traced back to the file.

### Flags
Each row in `pmd_rainfall` has a `flags` list. Rows with any flag marked **exclude** must be left out of training and scoring.

| Flag | Meaning | Exclude? |
|---|---|---|
| `missing_marker` | The cell held a "no reading" marker (`----`, `*`, `***`…); the value is empty | **exclude** |
| `not_numeric` | The cell held garbled text (e.g. `.0   1`); the value is empty | **exclude** |
| `suspect_negative` | A negative value, kept as written (may be a trace code) | **exclude** |
| `month_has_impossible_day` | That station-month has a non-zero value on a day that doesn't exist, so its days may be shifted | **exclude** |
| `duplicate_conflict` | The station-month appears twice with different values; this is the first copy | **exclude** |
| `not_gauge_precision` | The station's values look modelled, not measured (Garhi Dopatta, Kotli) | **exclude** |
| `extreme_rainfall` | More than 300 mm in a day. Can be real (Islamabad 2001); needs a human check | no |

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
**What it is:** computer-modelled river discharge (not measured). It is the LISFLOOD model driven by ERA5 weather.
- **Datasets:** `cems-glofas-historical` (the reanalysis, which we use) and `cems-glofas-forecast` (ensemble out to 30 days, not used yet).
- **Grid:** daily, 0.05° (about 5 km), 1979 to about 4 days ago.
- **Access:** EWDS with `cdsapi` (url `https://ewds.climate.copernicus.eu/api`). It needs a free account, `EWDS_API_KEY` in `apps/backend/.env`, and the CEMS-FLOODS licence accepted once on the dataset page.

**What we ingest (ADR-021)**
- **Version:** v4.0.
  - **`consolidated`:** final ERA5, up to 2026-06-30.
  - **`intermediate`:** ERA5T, updated daily, about 4 days behind real time.
  - **Why not v5.0 yet:** its reanalysis has no daily (intermediate) updates, there is no v5 upstream-area file, and live forecasts are still v4. Versions are never mixed. Moving to v5 means one full reload.
- **The response is a file, not JSON.** One NetCDF file per request:
  - variable **`avg_dis`** ("time-mean discharge", in **m³/s**). Older docs call it `dis24`;
  - coordinates `valid_time`, `latitude`, `longitude` (cell centres at .x25/.x75);
  - area N37 W66 S23 E76, a 280 × 200 grid. One year is about 26 MB.
- **Request size:** one request per calendar year (365 fields, under the 500-field limit), or one per month for part of a year. A request is queued and takes one to a few minutes.
- **Files:** saved as `data/glofas/raw/version_4_0/<product>_<first-day>_<last-day>.nc` and reused on later runs.
- **Day:** a requested day is the day the 24-hour mean covers. EWDS stamps it 00 UTC the **next** day: asking for 2–31 Aug returns stamps 3 Aug – 1 Sep. So `observed_on` = stamp − 1 day, a UTC day. *(Checked on a real file.)*

**Matching nodes to grid cells**
- `scripts/match_glofas_cells.py` uses the v4.0 upstream-area file (`data/glofas/raw/uparea_glofas_v4_0.nc`, from the ECMWF Confluence "Auxiliary Data" page).
- **Search rule:** look within ±3 cells of the node. Cells draining at least half the largest area nearby count as the main river; the **closest** of those wins. Taking simply the largest area drifts to the downstream edge of the window, because upstream area grows downstream.
- The result is committed as `apps/backend/app/ingest/glofas/node_grid_cells.csv`. All cells are within 7.2 km of the nodes.
- **Two cells were chosen by hand** (`MANUAL_CELLS` in the script):
  - **Panjnad:** the node sits where the Chenab (158k km²) meets the Sutlej (121k km²). The headworks is below the junction, so it uses the 278k km² cell.
  - **Rasul:** GloFAS's 5 km river map joins the Chenab into the Jhelum at Rasul (73k km²), while in reality they meet at Trimmu. Rasul uses the Jhelum cell just above that false junction (38k km²). **Model values between Rasul and Trimmu mix the two rivers.**
- **Known difference:** Tarbela's GloFAS upstream area is 199k km², against about 170k km² usually quoted.

**Table `glofas_discharge`** (ADR-019): one row per node, day and version, with `discharge_m3s`, `product_type`, `system_version`, `flags`, `source_file` and `ingested_at`. Where consolidated and intermediate both cover a day, consolidated is kept.

| Flag | Meaning | Exclude? |
|---|---|---|
| `missing_value` | No value at the node's cell for that day | **exclude** |
| `negative_value` | Discharge below zero (not physical). Value kept as written | **exclude** |

**Compared with WAPDA inflow, Jul–Dec 2022** (GloFAS converted to cfs: 1 m³/s = 35.31 cfs; WAPDA rows flagged for exclusion left out):

| Station | Correlation | Mean GloFAS ÷ WAPDA | 2022 peak: WAPDA | 2022 peak: GloFAS |
|---|---|---|---|---|
| Tarbela | 0.88 | 0.98 | 323,600 (29 Jul) | 430,749 (2 Jul) |
| Chashma | 0.77 | 0.96 | 526,026 (29 Aug) | 449,577 (3 Jul) |
| Jinnah | 0.74 | 1.18 | 420,147 (28 Aug) | 449,531 (2 Jul) |
| Mangla | 0.70 | 0.85 | 73,239 (28 Jul) | 34,315 (3 Aug) |
| Warsak | 0.72 | 0.60 | 133,435 (27 Aug) | 34,879 (29 Aug) |

- **Seasonal shape and volume are roughly right**, especially at Tarbela and Chashma.
- **The 2022 flood peaks are missed.** GloFAS peaks in early July (snowmelt) instead of late August (monsoon rain), and it is far too low at Mangla and Warsak.
- Shifting GloFAS by −2 to +8 days barely changes the correlations, because the seasonal cycle dominates them.
- Ghazi Barotha isn't comparable: WAPDA's "inflow" there is the power-channel flow.
- **Use:** long history, seasonal context and a model input. **Not** a stand-in for measured flood peaks.

**Limits:** GloFAS doesn't know dam operations. Expect it to be weak below Tarbela, Mangla and the barrages, and better for the rivers flowing into the dams (see the review findings in `docs/PROGRESS.md`).

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
**What it is:** NASA satellite rainfall estimates, merged from many satellites.
- **Runs:** the Early run arrives in ~4 h, Late in ~14 h, and Final after ~3.5 months.
- **Final stopped at 2025-09-30** while its V08 is prepared. Early and Late continue as V07.

**What we ingest (ADR-022)**
- **Product:** daily **Late** run, V07 (`GPM_3IMERGDL`, collection `C2723754859-GES_DISC`), from 2015. We use it for both training and live, so training and live data match.
- **Access:** a free NASA Earthdata account:
  - `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` go in `apps/backend/.env`;
  - the **"NASA GESDISC DATA ARCHIVE"** application must be approved once in the Earthdata profile (Applications → Authorized Apps).
- **Download:** NASA **Harmony** cuts each file to our area (W60 S23 E83 N38) and to the `precipitation` variable. That is about 45 MB a year instead of about 10 GB of global files.
  - One Harmony job is sent per month.
  - Files are saved in `data/imerg/raw/` and reused.
  - A failed job leaves no files behind.
- **The response is a file per day, not JSON.** NetCDF4:
  - variable `precipitation`, in **mm/day**;
  - dimensions `(time, lon, lat)`, with lon before lat;
  - grid 0.1°, cell centres at .x5;
  - missing cells are −9999.9.
  - File names carry the day and a version label, e.g. `3B-DAY-L.MS.MRG.3IMERG.20220825-S000000-E235959.V07B.nc4`.
- **Day:** 00–24 UTC (05:00–05:00 PKT). Note that WAPDA's reporting day is different.
- **Version labels change inside V07** (V07B, then V07C in 2026). Each row stores its label. When two files cover a day, the newest label is kept. V08 means re-downloading and reloading everything.
- **Harmony output, checked on Aug 2022:**
  - One file per day of about 140 kB. It covers the full area, a 230 × 150 grid of 0.1° cells.
  - Names look like `<job-id>_GPM_3IMERGDL.07_3B-DAY-L.MS.MRG.3IMERG.20220825-S000000-E235959.V07B_precipitation_subsetted.nc4`.
  - **`lon` is stored as float32** (72.05 is really 72.0500030517578), so coordinates are converted to float64 and rounded before matching the weights.
- **Aug 2022 check:** the wettest local areas were Sukkur and Kotri (about 10 mm/day, about 300 mm for the month), matching the record Sindh rains. The mountain catchments were much drier (Tarbela about 2 mm/day).

**Catchments (ADR-022)**
- `scripts/build_node_catchments.py` traces each node's catchment upstream from its GloFAS cell on the **GloFAS v4.0 flow-direction map** (`data/glofas/raw/ldd_glofas_v4_0.nc`), using `pyflwdir`.
- **Two areas per node:**
  - **catchment:** all land draining to the node;
  - **local:** only the land between the node and the next nodes upstream.
  - The local area suits the river-graph model, which passes upstream rain along itself. The full catchment suits single-node baseline models.
- **Weights:** each 0.05° map cell goes to the 0.1° IMERG cell containing its centre. The result is the land area (km²) of each area inside each IMERG cell, saved in `data/imerg/processed/catchment_weights.csv` (56,451 rows; regenerated by the script, not committed).
- **Check:** every catchment matches GloFAS's upstream area within 0.1%, and all of them fit inside the IMERG area.

| Node | Catchment km² | Local km² | | Node | Catchment km² | Local km² |
|---|---|---|---|---|---|---|
| Tarbela | 198,767 | 198,767 | | Mangla | 33,386 | 33,386 |
| Ghazi Barotha | 198,844 | 77 | | Rasul | 37,950 | 4,565 |
| Jinnah | 317,944 | 29,854 | | Marala | 29,174 | 29,174 |
| Chashma | 345,745 | 27,801 | | Khanki | 32,738 | 3,563 |
| Taunsa | 411,718 | 65,973 | | Qadirabad | 33,914 | 1,176 |
| Guddu | 719,267 | 28,911 | | Trimmu | 95,742 | 23,878 |
| Sukkur | 723,769 | 4,502 | | Balloki | 23,535 | 23,535 |
| Kotri | 832,296 | 108,527 | | Sidhnai | 40,359 | 16,824 |
| Warsak | 68,413 | 68,413 | | Sulemanki | 94,190 | 94,190 |
| Nowshera | 89,246 | 20,833 | | Islam | 98,442 | 4,252 |
| | | | | Panjnad | 278,638 | 44,095 |

- **Averaging:** each day, rain is averaged over each area, weighted by land area. Missing cells are left out.

**Table `imerg_rainfall`** (ADR-019):
- One row per node, day and run.
- Columns: `catchment_rainfall_mm`, `local_rainfall_mm`, `run` (`late`), `version_label`, `flags`, `source_file` and `ingested_at`.

| Flag | Meaning | Exclude? |
|---|---|---|
| `low_coverage` | Under 90% of the catchment or local area had a rain value that day | **exclude** |
| `missing_value` | No rain value at all for the catchment or local area | **exclude** |

**Limits:**
- **Mountains:** IMERG underestimates snow and rain over the Karakoram and other high mountains.
- **Gauges:** the Late run isn't corrected with rain-gauge data, only with a monthly correction learnt from past Final data.
- **Plains:** rain over the flat irrigated plains adds little to river flow.

### HydroRIVERS, Global Surface Water, Sen1Floods11
- **HydroRIVERS v1.0:** Asia shapefile (~91 MB). Free with attribution. Used to build the river graph and draw reach geometry.
- **JRC Global Surface Water:** 30 m tiles or GEE `JRC/GSW1_4/*`. Used as the normal-water mask so permanent water isn't counted as floodwater. Cite Pekel et al. (2016).
- **Sen1Floods11:** `gsutil -m rsync -r gs://sen1floods11 <dir>`. 512×512 chips of S1 VV/VH, 446 hand-labelled. Cite Bonafilia et al. (2020).

## Prototype nodes (approximate)
These coordinates are approximate to about ±0.05°. Confirm them against HydroRIVERS or a map before using them. All 21 nodes are seeded in the `nodes` table, using these ids in lowercase (`ghazi_barotha` for Ghazi Barotha, `jinnah` for Jinnah).

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
