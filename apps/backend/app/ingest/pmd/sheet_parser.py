"""Read the PMD daily rainfall workbook into one row per station per day, cells exactly as written.

Layout (docs/DATA.md, "PMD: daily station rainfall"): Sheet1 has one row per station-month with
columns STATION, MONTH, YEAR, 1st … 31st, TOT. Only Sheet1 is read; TOT and Sheet2 are not used.
"""

from pathlib import Path

import pandas as pd

SHEET = "Sheet1"
DAY_COLUMNS = [
    "1st", "2nd", "3rd", *[f"{day}th" for day in range(4, 21)],
    "21st", "22nd", "23rd", *[f"{day}th" for day in range(24, 31)], "31st",
]
FIRST_DATA_ROW = 2  # Excel row of the first station-month; row 1 is the header

OUTPUT_COLUMNS = ["station", "year", "month", "day", "rainfall_raw", "sheet_row", "source_file"]


def read_rain_sheet(path: Path) -> pd.DataFrame:
    """Read Sheet1 with every cell as the raw Python value (int, float or text; blanks are NaN)."""
    return pd.read_excel(path, sheet_name=SHEET, dtype=object)


def parse_rain_rows(sheet: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """Turn the station-month rows into one row per day column, keeping each cell as text.

    Every day column is returned, including days that don't exist in that month and blank cells
    (as ""), so cleaning can count them. Station names are left exactly as written.
    """
    station_months = sheet[["STATION", "YEAR", "MONTH", *DAY_COLUMNS]].assign(
        sheet_row=sheet.index + FIRST_DATA_ROW
    )
    rows = station_months.melt(
        id_vars=["STATION", "YEAR", "MONTH", "sheet_row"],
        value_vars=DAY_COLUMNS,
        var_name="day_column",
        value_name="cell",
    )
    rows = rows.assign(
        station=rows["STATION"],
        year=rows["YEAR"].astype(int),
        month=rows["MONTH"].astype(int),
        day=rows["day_column"].map({column: day for day, column in enumerate(DAY_COLUMNS, start=1)}),
        rainfall_raw=rows["cell"].where(rows["cell"].notna(), "").astype(str),
        source_file=source_file,
    )
    return rows.sort_values(["sheet_row", "day"], ignore_index=True)[OUTPUT_COLUMNS]
