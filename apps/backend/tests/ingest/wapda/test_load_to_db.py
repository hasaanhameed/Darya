import datetime as dt

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.ingest.wapda.load_to_db import WAPDA_SOURCE, load_rows
from app.models import DailyObservation

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def clean_rows(inflow_cfs=264700.0):
    """Two rows shaped like the output of cleaning.clean_sheets."""
    return pd.DataFrame(
        [
            {
                "node_id": "tarbela", "observed_on": dt.date(2022, 8, 28), "level_ft": 1546.3,
                "inflow_cfs": inflow_cfs, "outflow_turbine_cfs": 113400.0, "outflow_other_cfs": 0.0,
                "outflow_total_cfs": 264700.0, "irrigation_indent_raw": None, "flags": ["outflow_sum_mismatch"],
                "source_file": "AUG - 2022 (31).xlsx", "sheet": "28",
            },
            {
                "node_id": "mangla", "observed_on": dt.date(2022, 8, 28), "level_ft": float("nan"),
                "inflow_cfs": 57147.0, "outflow_turbine_cfs": 9885.0, "outflow_other_cfs": 115.0,
                "outflow_total_cfs": 10000.0, "irrigation_indent_raw": "10000 (Hourly)", "flags": [],
                "source_file": "AUG - 2022 (31).xlsx", "sheet": "28",
            },
        ]
    )


async def count_rows(session, source):
    return await session.scalar(select(func.count()).select_from(DailyObservation).where(DailyObservation.source == source))


async def test_loads_rows_into_daily_observations(db_session):
    await load_rows(db_session, clean_rows())

    tarbela = await db_session.scalar(select(DailyObservation).where(DailyObservation.node_id == "tarbela"))
    assert tarbela.source == WAPDA_SOURCE
    assert tarbela.inflow_cfs == 264700.0
    assert tarbela.flags == ["outflow_sum_mismatch"]
    assert await count_rows(db_session, WAPDA_SOURCE) == 2


async def test_stores_missing_values_as_null(db_session):
    await load_rows(db_session, clean_rows())

    mangla = await db_session.scalar(select(DailyObservation).where(DailyObservation.node_id == "mangla"))
    assert mangla.level_ft is None


async def test_reload_replaces_wapda_rows_without_duplicates(db_session):
    await load_rows(db_session, clean_rows())
    await load_rows(db_session, clean_rows(inflow_cfs=300000.0))

    assert await count_rows(db_session, WAPDA_SOURCE) == 2
    tarbela = await db_session.scalar(select(DailyObservation.inflow_cfs).where(DailyObservation.node_id == "tarbela"))
    assert tarbela == 300000.0


async def test_reload_leaves_other_sources_untouched(db_session):
    db_session.add(
        DailyObservation(node_id="tarbela", observed_on=dt.date(2022, 8, 28), source="another_source", source_file="x", sheet="x")
    )
    await db_session.flush()

    await load_rows(db_session, clean_rows())

    assert await count_rows(db_session, "another_source") == 1
