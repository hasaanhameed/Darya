import datetime as dt

import pandas as pd
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImergRainfall

ROWS_PER_INSERT = 1000  # one multi-row INSERT per batch; row-by-row inserts take minutes over the network


async def load_rows(session: AsyncSession, rows: pd.DataFrame, start: dt.date, end: dt.date) -> int:
    """Replace this run's rows for days start..end with these rows, in one transaction.

    Other days and other IMERG runs are never touched, so the same call serves the one-off
    history load and later catch-up runs. Returns the number of rows inserted.
    """
    runs = rows["run"].unique()
    if len(runs) > 1:
        raise ValueError(f"rows mix IMERG runs {list(runs)}; load one run at a time")
    if len(rows) == 0:
        return 0

    records = rows.astype(object).where(rows.notna(), None).to_dict("records")  # NaN → NULL

    await session.execute(
        delete(ImergRainfall).where(ImergRainfall.run == runs[0], ImergRainfall.observed_on.between(start, end))
    )
    for first in range(0, len(records), ROWS_PER_INSERT):
        await session.execute(insert(ImergRainfall).values(records[first : first + ROWS_PER_INSERT]))
    await session.commit()
    return len(records)
