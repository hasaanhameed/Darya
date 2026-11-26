"""Turn parsed PMD rainfall cells into clean, flagged rows (rules in ADR-024 and docs/DATA.md).

Values are never corrected. Each rule adds a True/False column, and at the end those columns
become the `flags` list of each row, so problems can be reviewed and filtered.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

STATION_MONTH = ["station_id", "year", "month"]

MISSING_MARKER_PATTERN = r"[-*\s]+"  # "----", "*", "**", "-  ***" ...: only dashes, stars and spaces
EXTREME_RAINFALL_MM = 300
NOT_GAUGE_PRECISION_STATIONS = {"garhi_dupatta", "kotli"}  # values with 5–9 decimals, probably modelled

# The order here is the order flags appear in each row's list
FLAG_NAMES = [
    "missing_marker",
    "not_numeric",
    "suspect_negative",
    "extreme_rainfall",
    "month_has_impossible_day",
    "duplicate_conflict",
    "not_gauge_precision",
]

OUTPUT_COLUMNS = ["station_id", "observed_on", "rainfall_mm", "rainfall_raw", "flags", "source_file", "sheet_row"]


@dataclass
class CleaningReport:
    blank_cells: int = 0  # empty cells on real days of the kept station-months: no reading, so no row
    impossible_day_cells: int = 0  # filled cells on days that don't exist (mostly "***")
    impossible_day_values: pd.DataFrame = field(default_factory=pd.DataFrame)  # non-zero numbers on those days
    identical_duplicate_months: int = 0  # extra copies dropped because they matched the first copy
    duplicate_conflicts: pd.DataFrame = field(default_factory=pd.DataFrame)  # months whose copies differ


def clean_rows(cells: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """Take parsed cells (with station_id) and return one flagged row per station per day with a reading."""
    report = CleaningReport()
    cells = add_dates_and_numbers(cells)

    cells = flag_impossible_days(cells, report)
    cells = keep_first_copy_of_each_month(cells, report)

    blank = cells["text"] == ""
    report.blank_cells = int((blank & cells["observed_on"].notna()).sum())
    rows = cells[~blank & cells["observed_on"].notna()].copy()

    rows = flag_values(rows)
    return to_output(rows), report


def add_dates_and_numbers(cells: pd.DataFrame) -> pd.DataFrame:
    """Add the date (empty for days that don't exist), the trimmed text and the number in each cell."""
    dates = pd.to_datetime(cells[["year", "month", "day"]], errors="coerce")
    text = cells["rainfall_raw"].str.strip()
    return cells.assign(
        observed_on=dates.dt.date.where(dates.notna(), None),
        text=text,
        rainfall_mm=pd.to_numeric(text, errors="coerce"),
    )


def flag_impossible_days(cells: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Count cells on days that don't exist, and flag every day of a month that has a non-zero value there."""
    impossible = cells["observed_on"].isna() & (cells["text"] != "")
    has_value = impossible & cells["rainfall_mm"].notna() & (cells["rainfall_mm"] != 0)

    report.impossible_day_cells = int(impossible.sum())
    report.impossible_day_values = cells.loc[
        has_value, ["station_id", "year", "month", "day", "rainfall_raw", "sheet_row"]
    ].reset_index(drop=True)

    shifted_rows = cells.loc[has_value, "sheet_row"].unique()
    return cells.assign(month_has_impossible_day=cells["sheet_row"].isin(shifted_rows))


def keep_first_copy_of_each_month(cells: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Keep only the first copy (lowest sheet row) of each station-month and flag it if the copies differ."""
    # One fingerprint per sheet row: all 31 cells joined, so two copies match only if every cell matches
    copies = (
        cells.sort_values(["sheet_row", "day"])
        .groupby([*STATION_MONTH, "sheet_row"], as_index=False)["text"]
        .agg("|".join)
        .rename(columns={"text": "fingerprint"})
    )
    months = copies.groupby(STATION_MONTH).agg(
        kept_sheet_row=("sheet_row", "min"),
        copies=("sheet_row", "size"),
        versions=("fingerprint", "nunique"),
        sheet_rows=("sheet_row", lambda rows: sorted(rows)),
    ).reset_index()

    duplicated = months["copies"] > 1
    conflicting = months["versions"] > 1
    report.identical_duplicate_months = int((duplicated & ~conflicting).sum())
    report.duplicate_conflicts = months.loc[conflicting, [*STATION_MONTH, "kept_sheet_row"]].assign(
        dropped_sheet_rows=months.loc[conflicting, "sheet_rows"].map(lambda rows: ";".join(map(str, rows[1:])))
    ).reset_index(drop=True)

    kept = cells[cells["sheet_row"].isin(months["kept_sheet_row"])]
    conflict_rows = months.loc[conflicting, "kept_sheet_row"]
    return kept.assign(duplicate_conflict=kept["sheet_row"].isin(conflict_rows))


def flag_values(rows: pd.DataFrame) -> pd.DataFrame:
    """Add the flags that depend only on each row's own value or station."""
    not_a_number = rows["rainfall_mm"].isna()
    marker = not_a_number & rows["text"].str.fullmatch(MISSING_MARKER_PATTERN)
    return rows.assign(
        missing_marker=marker,
        not_numeric=not_a_number & ~marker,
        suspect_negative=rows["rainfall_mm"] < 0,
        extreme_rainfall=rows["rainfall_mm"] > EXTREME_RAINFALL_MM,
        not_gauge_precision=rows["station_id"].isin(NOT_GAUGE_PRECISION_STATIONS),
    )


def to_output(rows: pd.DataFrame) -> pd.DataFrame:
    """Combine the flag columns into one list per row, e.g. ["suspect_negative", "not_gauge_precision"]."""
    joined = pd.Series("", index=rows.index)
    for name in FLAG_NAMES:
        joined = joined + np.where(rows[name], name + ";", "")
    flags = joined.str.rstrip(";").str.split(";").map(lambda names: [name for name in names if name])
    return rows.assign(flags=flags).sort_values(["station_id", "observed_on"], ignore_index=True)[OUTPUT_COLUMNS]
