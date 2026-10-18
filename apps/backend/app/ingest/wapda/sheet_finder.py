import calendar
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# "JULY - 2022 (31)", "FEB- 2026  (28)", "Daily data July- 2026 (25)"
FILE_NAME_PATTERN = re.compile(r"([A-Za-z]+)\s*-\s*(\d{4})\s*\((\d+)\)")
MONTH_NUMBERS = {name.lower(): number for number, name in enumerate(calendar.month_abbr) if name}


@dataclass(frozen=True)
class DaySheet:
    """One sheet that holds one day's report, and the date it should hold."""

    path: Path
    sheet: str
    expected_date: dt.date


def parse_file_name(file_name: str) -> tuple[int, int, int]:
    """Return (year, month, n) from a workbook name. n is the number in brackets."""
    match = FILE_NAME_PATTERN.search(file_name)
    if match is None:
        raise ValueError(f"Unrecognised WAPDA file name: {file_name}")
    month_name, year, n = match.groups()
    return int(year), MONTH_NUMBERS[month_name[:3].lower()], int(n)


def day_sheets_in_workbook(file_name: str, sheet_names: list[str], path: Path | None = None) -> list[DaySheet]:
    """Pick the sheets worth reading and the date each one should hold.

    A single-day workbook has a "Synopsis" sheet, and its day is the number in the file name.
    A monthly workbook has one sheet per day ("1"…"31"). Sheets for days that don't exist in
    that month are template leftovers, and every other sheet (Summary, Monthly, Sheet1…) is ignored.
    """
    year, month, n = parse_file_name(file_name)
    path = path or Path(file_name)

    if "Synopsis" in sheet_names:
        return [DaySheet(path, "Synopsis", dt.date(year, month, n))]

    days_in_month = calendar.monthrange(year, month)[1]
    day_sheets = [
        DaySheet(path, name, dt.date(year, month, int(name)))
        for name in sheet_names
        if name.isdigit() and 1 <= int(name) <= days_in_month
    ]
    return sorted(day_sheets, key=lambda s: s.expected_date)


def find_day_sheets(root: Path) -> tuple[list[DaySheet], list[Path]]:
    """Find every day sheet in the workbooks under root. Also return the files that couldn't be opened."""
    day_sheets: list[DaySheet] = []
    unreadable: list[Path] = []

    for path in sorted(root.rglob("*.xls*")):
        try:
            sheet_names = pd.ExcelFile(path).sheet_names
        except Exception:  # corrupt or truncated files raise many different errors
            unreadable.append(path)
            continue
        day_sheets.extend(day_sheets_in_workbook(path.name, sheet_names, path))

    return day_sheets, unreadable
