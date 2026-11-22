import datetime as dt

import pandas as pd
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GlofasDischarge

ROWS_PER_INSERT = 1000  # one multi-row INSERT per batch; row-by-row inserts take minutes over the network


async def load_rows(session: AsyncSession, rows: pd.DataFrame, start: dt.date, end: dt.date) -> int:
    """Replace this version's rows for days start..end with these rows, in one transaction.

    Other days and other GloFAS versions are never touched, so the same call serves the
    one-off history load and later catch-up runs. Returns the number of rows inserted.
    """
    versions = rows["system_version"].unique()
    if len(versions) > 1:
        raise ValueError(f"rows mix GloFAS versions {list(versions)}; load one version at a time")
    if len(rows) == 0:
        return 0

    records = rows.astype(object).where(rows.notna(), None).to_dict("records")  # NaN → NULL

    await session.execute(
        delete(GlofasDischarge).where(
            GlofasDischarge.system_version == versions[0],
            GlofasDischarge.observed_on.between(start, end),
        )
    )
    for first in range(0, len(records), ROWS_PER_INSERT):
        await session.execute(insert(GlofasDischarge).values(records[first : first + ROWS_PER_INSERT]))
    await session.commit()
    return len(records)
