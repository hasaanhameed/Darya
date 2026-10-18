import pandas as pd
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DailyObservation

WAPDA_SOURCE = "wapda_hydel_synopsis"
ROWS_PER_INSERT = 1000  # one multi-row INSERT per batch; row-by-row inserts take minutes over the network


async def load_rows(session: AsyncSession, rows: pd.DataFrame) -> int:
    """Replace all WAPDA rows in daily_observations with these rows, in one transaction (ADR-018).

    Only rows from the WAPDA source are deleted, so other sources are never touched.
    Returns the number of rows inserted.
    """
    records = rows.assign(source=WAPDA_SOURCE)
    records = records.astype(object).where(records.notna(), None).to_dict("records")  # NaN → NULL

    await session.execute(delete(DailyObservation).where(DailyObservation.source == WAPDA_SOURCE))
    for start in range(0, len(records), ROWS_PER_INSERT):
        await session.execute(insert(DailyObservation).values(records[start : start + ROWS_PER_INSERT]))
    await session.commit()
    return len(records)
