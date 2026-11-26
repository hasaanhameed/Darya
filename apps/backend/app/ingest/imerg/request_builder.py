"""Build NASA Harmony requests for IMERG daily Late rainfall over our area (one request per month)."""

import calendar
import datetime as dt

from harmony import BBox, Collection, Request

# GPM_3IMERGDL version 07: IMERG daily Late run, 0.1°, ~14 h after the UTC day ends (ADR-022).
IMERG_COLLECTION_ID = "C2723754859-GES_DISC"
# west, south, east, north: every node's upstream catchment (Upper Indus reaches ~37N and ~82E in Tibet).
# Edges sit on 0.1° lines so the subset lines up with whole IMERG cells.
BBOX = (60, 23, 83, 38)
VARIABLES = ["precipitation"]  # mm/day; the other variables (counts, errors) aren't needed


def split_into_months(start: dt.date, end: dt.date) -> list[tuple[dt.date, dt.date]]:
    """The days start..end as (first, last) pairs, one per calendar month."""
    months = []
    first = start
    while first <= end:
        month_end = dt.date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])
        last = min(month_end, end)
        months.append((first, last))
        first = last + dt.timedelta(days=1)
    return months


def build_request(first_day: dt.date, last_day: dt.date) -> Request:
    """A Harmony subset request: our bounding box and the precipitation variable, for whole UTC days."""
    return Request(
        collection=Collection(id=IMERG_COLLECTION_ID),
        spatial=BBox(*BBOX),
        temporal={
            "start": dt.datetime.combine(first_day, dt.time(0, 0, 0), tzinfo=dt.UTC),
            "stop": dt.datetime.combine(last_day, dt.time(23, 59, 59), tzinfo=dt.UTC),
        },
        variables=VARIABLES,
    )
