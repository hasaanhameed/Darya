"""Plan the GloFAS reanalysis downloads (EWDS requests) for a range of days.

A requested day is the day the 24-hour mean covers (EWDS stamps it 00 UTC the next day).
"""

import calendar
import datetime as dt
from dataclasses import dataclass

GLOFAS_DATASET = "cems-glofas-historical"
SYSTEM_VERSION = "version_4_0"  # never mix versions (ADR-021)
AREA = [37, 66, 23, 76]  # north, west, south, east: every prototype node with a margin
# v4.0 consolidated data (final ERA5) ends here. Later days only exist as intermediate data (ERA5T, ~4 days behind).
CONSOLIDATED_END = dt.date(2026, 6, 30)


@dataclass(frozen=True)
class Download:
    product_type: str  # "consolidated" or "intermediate"
    first_day: dt.date
    last_day: dt.date
    file_name: str
    request: dict


def plan_downloads(start: dt.date, end: dt.date) -> list[Download]:
    """Split the days start..end into EWDS requests.

    A whole calendar year is one request (365 fields, under the 500-field limit).
    A partial year is one request per month, asking only for the days in the range.
    """
    downloads = []
    for product_type, first, last in _split_by_product(start, end):
        for chunk_first, chunk_last in _split_into_chunks(first, last):
            downloads.append(_make_download(product_type, chunk_first, chunk_last))
    return downloads


def _split_by_product(start: dt.date, end: dt.date) -> list[tuple[str, dt.date, dt.date]]:
    periods = []
    if start <= CONSOLIDATED_END:
        periods.append(("consolidated", start, min(end, CONSOLIDATED_END)))
    if end > CONSOLIDATED_END:
        periods.append(("intermediate", max(start, CONSOLIDATED_END + dt.timedelta(days=1)), end))
    return periods


def _split_into_chunks(first: dt.date, last: dt.date) -> list[tuple[dt.date, dt.date]]:
    chunks = []
    for year in range(first.year, last.year + 1):
        year_first = max(first, dt.date(year, 1, 1))
        year_last = min(last, dt.date(year, 12, 31))
        if (year_first, year_last) == (dt.date(year, 1, 1), dt.date(year, 12, 31)):
            chunks.append((year_first, year_last))
            continue
        for month in range(year_first.month, year_last.month + 1):
            month_end = dt.date(year, month, calendar.monthrange(year, month)[1])
            chunks.append((max(year_first, dt.date(year, month, 1)), min(year_last, month_end)))
    return chunks


def _make_download(product_type: str, first: dt.date, last: dt.date) -> Download:
    if first.month == 1 and first.day == 1 and last.month == 12 and last.day == 31:
        months, days = range(1, 13), range(1, 32)  # the server skips dates that don't exist
    else:
        months, days = [first.month], range(first.day, last.day + 1)

    request = {
        "system_version": [SYSTEM_VERSION],
        "hydrological_model": ["lisflood"],
        "product_type": [product_type],
        "timespan": ["time_mean"],
        "variable": ["average_river_discharge_in_the_last_24_hours"],
        "year": [str(first.year)],
        "month": [f"{m:02d}" for m in months],
        "day": [f"{d:02d}" for d in days],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": AREA,
    }
    file_name = f"{product_type}_{first.isoformat()}_{last.isoformat()}.nc"
    return Download(product_type, first, last, file_name, request)
