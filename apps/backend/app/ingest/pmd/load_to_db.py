import pandas as pd
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PmdRainfall, RainStation

ROWS_PER_INSERT = 1000  # one multi-row INSERT per batch; row-by-row inserts take minutes over the network


def to_records(frame: pd.DataFrame) -> list[dict]:
    """DataFrame rows as plain dicts, with NaN turned into None (NULL)."""
    return frame.astype(object).where(frame.notna(), None).to_dict("records")


async def load_rows(session: AsyncSession, stations: pd.DataFrame, rows: pd.DataFrame) -> int:
    """Replace everything in rain_stations and pmd_rainfall with these stations and rows, in one transaction.

    Both tables hold only PMD data (ADR-023), so the whole tables are replaced. Rainfall is deleted
    first because it points at the stations. Returns the number of rainfall rows inserted.
    """
    records = to_records(rows)

    await session.execute(delete(PmdRainfall))
    await session.execute(delete(RainStation))
    await session.execute(insert(RainStation).values(to_records(stations)))
    for start in range(0, len(records), ROWS_PER_INSERT):
        await session.execute(insert(PmdRainfall).values(records[start : start + ROWS_PER_INSERT]))
    await session.commit()
    return len(records)
