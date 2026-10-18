import datetime as dt
from pathlib import Path

import pandas as pd

from app.ingest.wapda.sheet_finder import DaySheet
from app.ingest.wapda.sheet_parser import parse_sheet

DAY_SHEET = DaySheet(Path("AUG- 2024 (31).xls"), "15", dt.date(2024, 8, 15))

# Column positions in a real day sheet: A=0, B=1, E=4, I=8, N=13, Q=16, U=20
STATION_ROWS = [
    # name,          level,  indent,          inflow, turbine, other,  total
    ("TARBELA",      1549,   "1 Feet Rise",   313000, 113600, 131800, 283500),
    ("T-4 EXT:",     None,   None,            None,   38100,  None,   None),
    ("G/BAROTHA",    1086.34, "-",            55219,  56061,  0,      56061),
    ("MANGLA",       121.3,  "10000 (Hourly)", 46881, 9885,   115,    10000),
    ("WARSAK",       1270,   "-",             37865,  12872,  24993,  37865),
    ("CHASHMA",      638.6,  235000,          320921, 25984,  294936, 320920),
    ("JINNAH",       693.5,  8000,            302401, 13023,  289378, 302401),
    ("GOMAL ZAM",    2433.12, 423.77,         686,    100,    851,    951),
    ("8.7",          None,   None,            None,   None,   None,   None),  # stray row seen in real sheets
]


def make_grid(date_cell, header_row=11):
    """A blank 45 x 40 grid laid out like a real WAPDA day sheet."""
    grid = [[None] * 40 for _ in range(45)]
    grid[header_row - 11][32] = "     DATA FOR:"
    grid[header_row - 11][34] = date_cell
    grid[header_row][0] = "POWER STATIONS"
    for offset, (name, level, indent, inflow, turbine, other, total) in enumerate(STATION_ROWS):
        row = grid[header_row + 3 + offset]
        row[0], row[1], row[4], row[8], row[13], row[16], row[20] = name, level, indent, inflow, turbine, other, total
    grid[header_row + 13][0] = "TARBELA"  # the unit-wise generation table further down
    grid[header_row + 13][1] = "INSTALLED CAPACITY 3478 MW"
    return pd.DataFrame(grid, dtype=object)


def date_read_from(grid):
    return parse_sheet(grid, DAY_SHEET)["date_in_sheet"].iloc[0]


def test_reads_date_stored_as_datetime():
    assert date_read_from(make_grid(dt.datetime(2024, 8, 15))) == dt.date(2024, 8, 15)


def test_reads_date_stored_as_excel_serial():
    assert date_read_from(make_grid(45519)) == dt.date(2024, 8, 15)


def test_reads_date_stored_as_string():
    assert date_read_from(make_grid("15-08-2024")) == dt.date(2024, 8, 15)


def test_date_is_none_when_unreadable():
    assert date_read_from(make_grid("not a date")) is None


def test_skips_placeholder_date_above_the_real_one():
    # Aug 2026 sheet 12: row 1 holds "DATA FOR: -1", row 2 holds the real date
    grid = make_grid(dt.datetime(2026, 8, 12), header_row=12)
    grid.iat[0, 32], grid.iat[0, 34] = "     DATA FOR:", -1
    assert date_read_from(grid) == dt.date(2026, 8, 12)


def test_every_row_carries_the_sheet_details():
    parsed = parse_sheet(make_grid(dt.datetime(2024, 8, 15)), DAY_SHEET)

    assert (parsed["source_file"] == "AUG- 2024 (31).xls").all()
    assert (parsed["sheet"] == "15").all()
    assert (parsed["expected_date"] == dt.date(2024, 8, 15)).all()


def test_finds_header_shifted_down_one_row():
    parsed = parse_sheet(make_grid(dt.datetime(2024, 8, 15), header_row=12), DAY_SHEET).set_index("station")
    assert parsed.loc["tarbela", "inflow_cfs"] == 313000


def test_reads_station_rows_by_name():
    parsed = parse_sheet(make_grid(dt.datetime(2024, 8, 15)), DAY_SHEET).set_index("station")

    assert parsed.loc["ghazi_barotha", "level_ft"] == 1086.34
    assert parsed.loc["mangla", "irrigation_indent"] == "10000 (Hourly)"
    assert parsed.loc["chashma", "outflow_total_cfs"] == 320920
    assert parsed.loc["tarbela_t4", "outflow_turbine_cfs"] == 38100


def test_stops_after_station_block():
    parsed = parse_sheet(make_grid(dt.datetime(2024, 8, 15)), DAY_SHEET).set_index("station")

    assert set(parsed.index) == {"tarbela", "tarbela_t4", "ghazi_barotha", "mangla", "warsak", "chashma", "jinnah"}
    assert parsed.loc["tarbela", "level_ft"] == 1549  # not overwritten by the generation table
