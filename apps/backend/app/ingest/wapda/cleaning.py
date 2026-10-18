"""Turn parsed WAPDA sheets into clean, flagged rows (rules in ADR-010 and docs/DATA.md).

Values are never corrected. Each rule adds a True/False column, and at the end those columns
become the `flags` list of each row, so problems can be reviewed and filtered.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

T4_STATION = "tarbela_t4"  # read only to check Tarbela's total outflow
SHEET_KEY = ["source_file", "sheet"]
NUMBER_FIELDS = ["level_ft", "inflow_cfs", "outflow_turbine_cfs", "outflow_other_cfs", "outflow_total_cfs"]
FINGERPRINT_FIELDS = ["level_ft", "inflow_cfs", "outflow_total_cfs"]

DATE_FLAGS = ["date_from_sheet", "date_typo", "date_unreadable"]
SHEET_FLAGS = DATE_FLAGS + ["repeated_previous_day"]
ROW_FLAGS = [f"not_numeric_{name}" for name in NUMBER_FIELDS] + [
    "outflow_sum_mismatch",
    "suspect_level_ft",
    "suspect_inflow_cfs",
    "suspect_outflow_total_cfs",
]

NEIGHBOUR_WINDOW_DAYS = 7  # centred on the value being checked
MIN_NEIGHBOURS_FOR_MEDIAN = 3
SUSPECT_LEVEL_JUMP_FT = 15
SUSPECT_FLOW_RATIO = 3
SUSPECT_FLOW_JUMP_CFS = 5000
OUTFLOW_SUM_TOLERANCE_CFS = 100
OUTFLOW_SUM_TOLERANCE_SHARE = 0.01

OUTPUT_COLUMNS = [
    "node_id", "observed_on", *NUMBER_FIELDS, "irrigation_indent_raw", "flags", "source_file", "sheet",
]


@dataclass
class CleaningReport:
    stale_copies: list[str] = field(default_factory=list)  # sheets skipped as copies of another day
    conflicts: list[str] = field(default_factory=list)  # days where two sheets competed and one was dropped


def clean_sheets(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """Take the parsed rows of every sheet and return one clean, flagged row per station per day."""
    report = CleaningReport()
    raw = convert_numbers(raw)

    sheets = summarise_sheets(raw)
    sheets = assign_dates(sheets, report)
    sheets = keep_one_sheet_per_day(sheets, report)
    sheets = flag_repeated_days(sheets)

    # Station rows of the sheets that survived, with each sheet's date and flags
    rows = raw[raw["station"] != T4_STATION].merge(
        sheets[SHEET_KEY + ["observed_on", "t4_turbine_cfs"] + SHEET_FLAGS], on=SHEET_KEY
    )
    rows = flag_outflow_mismatch(rows)
    rows = flag_suspect_values(rows)
    return to_output(rows), report


def to_numbers(cells: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Return (numbers, unreadable). Blanks and "-" mean "no value"; other text that isn't a number is unreadable."""
    text = cells.map(lambda cell: "" if pd.isna(cell) else str(cell)).str.strip().str.replace(",", "")
    blank = text.isin(["", "-"])
    numbers = pd.to_numeric(text.where(~blank), errors="coerce")
    unreadable = ~blank & numbers.isna()
    return numbers, unreadable


def convert_numbers(raw: pd.DataFrame) -> pd.DataFrame:
    raw = raw.copy()
    for name in NUMBER_FIELDS:
        raw[name], raw[f"not_numeric_{name}"] = to_numbers(raw[name])
    raw["expected_date"] = pd.to_datetime(raw["expected_date"])
    raw["date_in_sheet"] = pd.to_datetime(raw["date_in_sheet"])
    return raw


def summarise_sheets(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per sheet: its dates, a fingerprint of its values, and T-4's turbine flow."""
    sheets = raw.groupby(SHEET_KEY, sort=False).agg(
        expected_date=("expected_date", "first"),
        date_in_sheet=("date_in_sheet", "first"),
    )

    # The values that identify a day's data. Two sheets with the same fingerprint are copies.
    by_station = raw.sort_values("station")
    parts = by_station["station"]
    for name in FINGERPRINT_FIELDS:
        parts = parts + "/" + by_station[name].map(str)  # map(str) keeps blanks comparable as "nan"
    sheets["fingerprint"] = parts.groupby([by_station[k] for k in SHEET_KEY]).agg("|".join)

    t4 = raw[raw["station"] == T4_STATION].set_index(SHEET_KEY)["outflow_turbine_cfs"]
    sheets["t4_turbine_cfs"] = t4.reindex(sheets.index).fillna(0)
    return sheets.reset_index()


def assign_dates(sheets: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Decide which day each sheet describes, using the date written in it (ADR-010)."""
    expected, claimed = sheets["expected_date"], sheets["date_in_sheet"]
    matching = sheets[claimed == expected]

    unreadable = claimed.isna()
    mismatch = (claimed != expected) & ~unreadable
    copy_of_claimed_day = pd.MultiIndex.from_frame(sheets[["date_in_sheet", "fingerprint"]]).isin(
        pd.MultiIndex.from_frame(matching[["expected_date", "fingerprint"]])
    )
    claimed_day_has_sheet = claimed.isin(matching["expected_date"])

    stale = mismatch & copy_of_claimed_day
    sheets["date_unreadable"] = unreadable
    # copied from a month we have no sheet for, so it is most likely real data for that day
    sheets["date_from_sheet"] = mismatch & ~stale & ~claimed_day_has_sheet
    # the claimed day has its own, different data, so the date cell is the typo
    sheets["date_typo"] = mismatch & ~stale & claimed_day_has_sheet
    sheets["observed_on"] = claimed.where(sheets["date_from_sheet"], expected)

    for _, sheet in sheets[stale].iterrows():
        report.stale_copies.append(f"{describe(sheet)} (copy of {sheet['date_in_sheet']:%Y-%m-%d})")
    return sheets[~stale]


def keep_one_sheet_per_day(sheets: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """If two sheets describe the same day, keep the one with fewer date flags (the first one on a tie)."""
    sheets = sheets.assign(date_flag_count=sheets[DATE_FLAGS].sum(axis=1))
    sheets = sheets.sort_values(["observed_on", "date_flag_count"], kind="stable")

    dropped = sheets.duplicated("observed_on")
    kept_by_day = sheets[~dropped].set_index("observed_on")
    for _, sheet in sheets[dropped].iterrows():
        kept = kept_by_day.loc[sheet["observed_on"]]
        report.conflicts.append(f"{sheet['observed_on']:%Y-%m-%d}: kept {describe(kept)}, dropped {describe(sheet)}")
    return sheets[~dropped].drop(columns="date_flag_count")


def flag_repeated_days(sheets: pd.DataFrame) -> pd.DataFrame:
    """Flag a sheet identical to the previous day's: a stale copy whose date was updated but not its data."""
    fingerprint_by_day = sheets.set_index("observed_on")["fingerprint"]
    previous_day = sheets["observed_on"] - pd.Timedelta(days=1)
    return sheets.assign(repeated_previous_day=previous_day.map(fingerprint_by_day) == sheets["fingerprint"])


def flag_outflow_mismatch(rows: pd.DataFrame) -> pd.DataFrame:
    """Total outflow should be turbine + other. It often isn't in floods (spillway flow left out of "other")."""
    t4_part = rows["t4_turbine_cfs"].where(rows["station"] == "tarbela", 0)
    parts = rows["outflow_turbine_cfs"] + rows["outflow_other_cfs"].fillna(0) + t4_part
    tolerance = np.maximum(OUTFLOW_SUM_TOLERANCE_CFS, OUTFLOW_SUM_TOLERANCE_SHARE * rows["outflow_total_cfs"].abs())
    return rows.assign(outflow_sum_mismatch=(rows["outflow_total_cfs"] - parts).abs() > tolerance)


def flag_suspect_values(rows: pd.DataFrame) -> pd.DataFrame:
    """Flag values far from the same station's neighbouring days, and negative flows. Values are left unchanged."""
    rows = rows.sort_values(["station", "observed_on"]).reset_index(drop=True)

    def neighbour_median(name: str) -> pd.Series:
        return rows.groupby("station")[name].transform(
            lambda values: values.rolling(NEIGHBOUR_WINDOW_DAYS, center=True, min_periods=MIN_NEIGHBOURS_FOR_MEDIAN).median()
        )

    level, median = rows["level_ft"], neighbour_median("level_ft")
    rows["suspect_level_ft"] = (level - median).abs() > SUSPECT_LEVEL_JUMP_FT

    for name in ["inflow_cfs", "outflow_total_cfs"]:
        flow, median = rows[name], neighbour_median(name)
        far_from_neighbours = ((flow - median).abs() > SUSPECT_FLOW_JUMP_CFS) & (
            (flow > SUSPECT_FLOW_RATIO * median) | (flow < median / SUSPECT_FLOW_RATIO)
        )
        rows[f"suspect_{name}"] = (flow < 0) | far_from_neighbours
    return rows


def to_output(rows: pd.DataFrame) -> pd.DataFrame:
    """Shape the rows like the daily_observations table."""
    flag_names = SHEET_FLAGS + ROW_FLAGS
    output = rows.rename(columns={"station": "node_id"})
    output["observed_on"] = output["observed_on"].dt.date
    output["irrigation_indent_raw"] = output["irrigation_indent"].map(indent_text)
    output["flags"] = output[flag_names].apply(lambda row: [name for name in flag_names if row[name]], axis=1)
    return output[OUTPUT_COLUMNS].sort_values(["observed_on", "node_id"]).reset_index(drop=True)


def indent_text(cell) -> str | None:
    if pd.isna(cell):
        return None
    if isinstance(cell, float) and cell.is_integer():
        cell = int(cell)
    text = str(cell).strip()
    return None if text in ("", "-") else text


def describe(sheet: pd.Series) -> str:
    return f"{sheet['source_file']} / sheet {sheet['sheet']}"
