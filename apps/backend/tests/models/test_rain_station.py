import pytest
from sqlalchemy.exc import IntegrityError

from app.models import RainStation

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def make_station(**overrides) -> RainStation:
    values = dict(
        id="test_station_x",  # not a real station, so it never clashes with loaded data
        name="Test Station X",
        pmd_name="TEST STATION X",
        lat=33.6,
        lon=73.1,
        province="Punjab",
        basin="indus",
    )
    values.update(overrides)
    return RainStation(**values)


async def test_rejects_duplicate_station_id(db_session):
    db_session.add(make_station())
    await db_session.flush()

    db_session.add(make_station(name="Another name"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_coordinates_and_province_are_optional(db_session):
    db_session.add(make_station(lat=None, lon=None, province=None))
    await db_session.flush()
