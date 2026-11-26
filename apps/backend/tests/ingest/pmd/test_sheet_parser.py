import numpy as np
import pandas as pd

from app.ingest.pmd.sheet_parser import DAY_COLUMNS, parse_rain_rows

SOURCE_FILE = "DAILY RAIN - ALL STATIONS - 1981-2015.xls"


def make_sheet(rows: list[dict]) -> pd.DataFrame:
    """A small Sheet1 as read by pandas: blanks are NaN, numbers are int or float, the rest is text."""
    full_rows = []
    for row in rows:
        days = {column: np.nan for column in DAY_COLUMNS}
        days.update(row.get("days", {}))
        full_rows.append({"STATION": row["station"], "MONTH": row["month"], "YEAR": row["year"], **days, "TOT": 0})
    return pd.DataFrame(full_rows).astype(object)


def test_returns_one_row_per_day_column():
    sheet = make_sheet([{"station": "ASTORE", "month": 2, "year": 1982}])
    rows = parse_rain_rows(sheet, SOURCE_FILE)

    assert len(rows) == 31
    assert rows["day"].tolist() == list(range(1, 32))
    assert (rows[["station", "year", "month"]].drop_duplicates().values.tolist()) == [["ASTORE", 1982, 2]]


def test_keeps_cells_exactly_as_written():
    sheet = make_sheet([
        {"station": "ASTORE", "month": 2, "year": 1982,
         "days": {"1st": 14, "2nd": 1.5, "3rd": "----", "4th": "***", "5th": ".0   1", "6th": 0.00148744}},
    ])
    rows = parse_rain_rows(sheet, SOURCE_FILE).set_index("day")

    assert rows.loc[[1, 2, 3, 4, 5, 6], "rainfall_raw"].tolist() == ["14", "1.5", "----", "***", ".0   1", "0.00148744"]


def test_blank_cells_become_empty_text():
    sheet = make_sheet([{"station": "ASTORE", "month": 2, "year": 1982, "days": {"1st": 3}}])
    rows = parse_rain_rows(sheet, SOURCE_FILE).set_index("day")

    assert rows.loc[2, "rainfall_raw"] == ""


def test_records_the_excel_row_and_source_file():
    sheet = make_sheet([
        {"station": "ASTORE", "month": 1, "year": 1982},
        {"station": "BADIN", "month": 1, "year": 1982},
    ])
    rows = parse_rain_rows(sheet, SOURCE_FILE)

    # Row 1 of the sheet is the header, so the first data row is Excel row 2
    assert rows.groupby("station")["sheet_row"].first().to_dict() == {"ASTORE": 2, "BADIN": 3}
    assert (rows["source_file"] == SOURCE_FILE).all()


def test_ignores_the_total_and_unnamed_columns():
    sheet = make_sheet([{"station": "ASTORE", "month": 1, "year": 1982}]).assign(**{"Unnamed: 35": 1.4})
    rows = parse_rain_rows(sheet, SOURCE_FILE)

    assert list(rows.columns) == ["station", "year", "month", "day", "rainfall_raw", "sheet_row", "source_file"]
