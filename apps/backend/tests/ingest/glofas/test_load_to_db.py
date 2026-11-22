import datetime as dt

import pandas as pd
import pytest
from sqlalchemy import func, select

from app.ingest.glofas.load_to_db import load_rows
from app.models import GlofasDischarge

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

VERSION = "test_version"  # not a real version, so tests never touch loaded data
AUG_28, AUG_29, AUG_30 = dt.date(2022, 8, 28), dt.date(2022, 8, 29), dt.date(2022, 8, 30)


def clean_rows(days=(AUG_28, AUG_29), discharge_m3s=7420.5, version=VERSION):
    """Rows shaped like the output of cleaning.clean_discharge."""
    return pd.DataFrame([
        {
            "node_id": "tarbela", "observed_on": day, "discharge_m3s": discharge_m3s, "product_type": "consolidated",
            "system_version": version, "flags": [], "source_file": "consolidated_2022-01-01_2022-12-31.nc",
        }
        for day in days
    ])


async def stored(session, version=VERSION):
    return (await session.scalars(
        select(GlofasDischarge).where(GlofasDischarge.system_version == version).order_by(GlofasDischarge.observed_on)
    )).all()


async def test_loads_rows(db_session):
    inserted = await load_rows(db_session, clean_rows(), AUG_28, AUG_29)

    rows = await stored(db_session)
    assert inserted == 2
    assert [row.observed_on for row in rows] == [AUG_28, AUG_29]
    assert rows[0].discharge_m3s == 7420.5


async def test_stores_missing_values_as_null(db_session):
    await load_rows(db_session, clean_rows(discharge_m3s=float("nan")), AUG_28, AUG_29)

    assert (await stored(db_session))[0].discharge_m3s is None


async def test_reload_of_a_range_replaces_its_rows_without_duplicates(db_session):
    await load_rows(db_session, clean_rows(), AUG_28, AUG_29)
    await load_rows(db_session, clean_rows(discharge_m3s=9000.0), AUG_28, AUG_29)

    rows = await stored(db_session)
    assert len(rows) == 2
    assert {row.discharge_m3s for row in rows} == {9000.0}


async def test_reload_keeps_days_outside_the_range(db_session):
    await load_rows(db_session, clean_rows(days=(AUG_28, AUG_29, AUG_30)), AUG_28, AUG_30)

    await load_rows(db_session, clean_rows(days=(AUG_30,), discharge_m3s=1.0), AUG_30, AUG_30)

    assert [row.discharge_m3s for row in await stored(db_session)] == [7420.5, 7420.5, 1.0]


async def test_reload_leaves_other_versions_untouched(db_session):
    await load_rows(db_session, clean_rows(version="another_version"), AUG_28, AUG_29)

    await load_rows(db_session, clean_rows(), AUG_28, AUG_29)

    assert len(await stored(db_session, "another_version")) == 2


async def test_rejects_rows_from_more_than_one_version(db_session):
    mixed = pd.concat([clean_rows(days=(AUG_28,)), clean_rows(days=(AUG_29,), version="another_version")])

    with pytest.raises(ValueError):
        await load_rows(db_session, mixed, AUG_28, AUG_29)
