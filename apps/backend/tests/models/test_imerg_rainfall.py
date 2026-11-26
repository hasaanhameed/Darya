import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import ImergRainfall

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def make_row(**overrides) -> ImergRainfall:
    values = dict(
        node_id="tarbela",
        observed_on=dt.date(2022, 8, 25),
        catchment_rainfall_mm=12.3,
        local_rainfall_mm=12.3,
        run="test_run",  # not a real run, so it never clashes with loaded data
        version_label="V07B",
        source_file="3B-DAY-L.MS.MRG.3IMERG.20220825-S000000-E235959.V07B.nc4",
    )
    values.update(overrides)
    return ImergRainfall(**values)


async def test_rejects_duplicate_node_day_run(db_session):
    db_session.add(make_row())
    await db_session.flush()

    db_session.add(make_row(version_label="V07C"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_allows_same_node_day_from_another_run(db_session):
    db_session.add_all([make_row(), make_row(run="another_run")])
    await db_session.flush()


async def test_flags_default_to_empty_and_missing_values_are_allowed(db_session):
    row = make_row(catchment_rainfall_mm=None, local_rainfall_mm=None)
    db_session.add(row)
    await db_session.flush()
    await db_session.refresh(row)

    assert row.flags == []
    assert row.ingested_at is not None
