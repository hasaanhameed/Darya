import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import PmdRainfall, RainStation

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

TEST_STATION_ID = "test_station_x"  # not a real station, so it never clashes with loaded data


@pytest.fixture
async def station(db_session):
    db_session.add(RainStation(id=TEST_STATION_ID, name="Test Station X", pmd_name="TEST STATION X", basin="indus"))
    await db_session.flush()


def make_row(**overrides) -> PmdRainfall:
    values = dict(
        station_id=TEST_STATION_ID,
        observed_on=dt.date(2001, 7, 24),
        rainfall_mm=591.9,
        rainfall_raw="591.9",
        source_file="DAILY RAIN - ALL STATIONS - 1981-2015.xls",
        sheet_row=11014,
    )
    values.update(overrides)
    return PmdRainfall(**values)


async def test_rejects_duplicate_station_day(db_session, station):
    db_session.add(make_row())
    await db_session.flush()

    db_session.add(make_row(rainfall_mm=1.0, rainfall_raw="1"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_rejects_unknown_station(db_session):
    db_session.add(make_row(station_id="no_such_station"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_flags_default_to_empty_and_missing_value_is_allowed(db_session, station):
    row = make_row(rainfall_mm=None, rainfall_raw="----")
    db_session.add(row)
    await db_session.flush()
    await db_session.refresh(row)

    assert row.flags == []
    assert row.ingested_at is not None
