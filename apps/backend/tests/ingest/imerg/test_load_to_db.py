import datetime as dt

import pandas as pd
import pytest
from sqlalchemy import select

from app.ingest.imerg.load_to_db import load_rows
from app.models import ImergRainfall

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

RUN = "test_run"  # not a real run, so tests never touch loaded data
AUG_25, AUG_26, AUG_27 = dt.date(2022, 8, 25), dt.date(2022, 8, 26), dt.date(2022, 8, 27)


def clean_rows(days=(AUG_25, AUG_26), rain_mm=12.3, run=RUN):
    """Rows shaped like the output of cleaning.clean_rainfall."""
    return pd.DataFrame([
        {
            "node_id": "tarbela", "observed_on": day, "catchment_rainfall_mm": rain_mm, "local_rainfall_mm": rain_mm,
            "run": run, "version_label": "V07B", "flags": [], "source_file": f"3IMERG.{day:%Y%m%d}-S000000.V07B.nc4",
        }
        for day in days
    ])


async def stored(session, run=RUN):
    return (await session.scalars(
        select(ImergRainfall).where(ImergRainfall.run == run).order_by(ImergRainfall.observed_on)
    )).all()


async def test_loads_rows(db_session):
    inserted = await load_rows(db_session, clean_rows(), AUG_25, AUG_26)

    rows = await stored(db_session)
    assert inserted == 2
    assert [row.observed_on for row in rows] == [AUG_25, AUG_26]
    assert rows[0].catchment_rainfall_mm == 12.3


async def test_stores_missing_values_as_null(db_session):
    await load_rows(db_session, clean_rows(rain_mm=float("nan")), AUG_25, AUG_26)

    assert (await stored(db_session))[0].local_rainfall_mm is None


async def test_reload_of_a_range_replaces_its_rows_without_duplicates(db_session):
    await load_rows(db_session, clean_rows(), AUG_25, AUG_26)
    await load_rows(db_session, clean_rows(rain_mm=40.0), AUG_25, AUG_26)

    rows = await stored(db_session)
    assert len(rows) == 2
    assert {row.catchment_rainfall_mm for row in rows} == {40.0}


async def test_reload_keeps_days_outside_the_range(db_session):
    await load_rows(db_session, clean_rows(days=(AUG_25, AUG_26, AUG_27)), AUG_25, AUG_27)

    await load_rows(db_session, clean_rows(days=(AUG_27,), rain_mm=1.0), AUG_27, AUG_27)

    assert [row.catchment_rainfall_mm for row in await stored(db_session)] == [12.3, 12.3, 1.0]


async def test_reload_leaves_other_runs_untouched(db_session):
    await load_rows(db_session, clean_rows(run="another_run"), AUG_25, AUG_26)

    await load_rows(db_session, clean_rows(), AUG_25, AUG_26)

    assert len(await stored(db_session, "another_run")) == 2


async def test_rejects_rows_from_more_than_one_run(db_session):
    mixed = pd.concat([clean_rows(days=(AUG_25,)), clean_rows(days=(AUG_26,), run="another_run")])

    with pytest.raises(ValueError):
        await load_rows(db_session, mixed, AUG_25, AUG_26)
