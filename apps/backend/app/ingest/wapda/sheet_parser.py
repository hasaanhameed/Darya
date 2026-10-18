import datetime as dt
from pathlib import Path

import pandas as pd

from app.ingest.wapda.sheet_finder import DaySheet
from app.ingest.wapda.station_aliases import station_id_for

# Where each field sits in a station row (0-based column index; B=1, D=3, ...).
STATION_COLUMNS = {
    "level_ft": 1,  # B
    "level_ft_last_year": 3,  # D
    "irrigation_indent": 4,  # E
    "inflow_cfs": 8,  # I
    "inflow_cfs_last_year": 10,  # K
    "outflow_turbine_cfs": 13,  # N
    "outflow_other_cfs": 16,  # Q
    "outflow_total_cfs": 20,  # U
    "outflow_total_cfs_last_year": 22,  # W
}
HEADER_TEXT = "POWER STATIONS"
DATE_LABEL = "DATA FOR"
LAST_STATION = "GOMAL ZAM"  # the block always ends with Gomal Zam, even though we don't keep it
MAX_BLOCK_ROWS = 12  # fallback if Gomal Zam is ever missing
ROWS_TO_READ = 40  # the station block ends around row 23; nothing below is needed
EXCEL_EPOCH = dt.date(1899, 12, 30)
EARLIEST_PLAUSIBLE_DATE = dt.date(2000, 1, 1)


def read_grids(path: Path, sheets: list[str]) -> dict[str, pd.DataFrame]:
    """Read the top of each listed sheet as a grid of raw cells (no header row)."""
    workbook = pd.ExcelFile(path)
    return {
        sheet: pd.read_excel(workbook, sheet_name=sheet, header=None, dtype=object, nrows=ROWS_TO_READ)
        for sheet in sheets
    }


def parse_sheet(grid: pd.DataFrame, day_sheet: DaySheet) -> pd.DataFrame:
    """Return one row per station, with the cells exactly as written plus the sheet's details."""
    grid = grid.astype(object).where(grid.notna(), None)
    header_row = find_header_row(grid)

    stations = read_station_block(grid.iloc[header_row + 1 :])
    stations.insert(0, "source_file", day_sheet.path.name)
    stations.insert(1, "sheet", day_sheet.sheet)
    stations.insert(2, "expected_date", day_sheet.expected_date)
    stations.insert(3, "date_in_sheet", find_report_date(grid.iloc[:header_row]))
    return stations


def find_header_row(grid: pd.DataFrame) -> int:
    first_column = grid[0].map(text_of).str.upper()
    matches = first_column.index[first_column == HEADER_TEXT]
    if matches.empty:
        raise ValueError(f"No '{HEADER_TEXT}' header found")
    return matches[0]


def find_report_date(rows: pd.DataFrame) -> dt.date | None:
    """Return the first readable date written to the right of a "DATA FOR:" label."""
    is_label = rows.map(lambda cell: DATE_LABEL in text_of(cell).upper())
    for row, column in is_label[is_label].stack().index:
        cells_to_the_right = rows.loc[row].iloc[column + 1 :]
        filled = cells_to_the_right[cells_to_the_right.map(text_of) != ""]
        report_date = to_date(filled.iloc[0]) if not filled.empty else None
        if report_date is not None:
            return report_date
    return None


def to_date(value) -> dt.date | None:
    """Read a date stored as a datetime, an Excel serial number or a "dd-mm-yyyy" string."""
    if isinstance(value, dt.datetime):
        result = value.date()
    elif isinstance(value, (int, float)):
        result = EXCEL_EPOCH + dt.timedelta(days=int(value))
    elif isinstance(value, str):
        try:
            result = dt.datetime.strptime(value.strip(), "%d-%m-%Y").date()
        except ValueError:
            return None
    else:
        return None
    return result if result >= EARLIEST_PLAUSIBLE_DATE else None


def read_station_block(rows: pd.DataFrame) -> pd.DataFrame:
    """Read station rows by name, from below the header down to Gomal Zam (the last row of the block)."""
    rows = rows.reset_index(drop=True)
    names = rows[0].map(text_of)

    is_last_station = names.str.upper() == LAST_STATION
    block_end = is_last_station.idxmax() if is_last_station.any() else MAX_BLOCK_ROWS
    block = rows.iloc[:block_end]

    station_ids = names.iloc[:block_end].map(station_id_for)
    block = block[station_ids.notna()]
    station_ids = station_ids[station_ids.notna()]

    stations = pd.DataFrame({field: block[column] for field, column in STATION_COLUMNS.items()})
    stations.insert(0, "station", station_ids)
    return stations.drop_duplicates("station").reset_index(drop=True)


def text_of(cell) -> str:
    return "" if cell is None else str(cell).strip()
