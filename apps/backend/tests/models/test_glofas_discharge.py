import datetime as dt

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import GlofasDischarge

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def make_row(**overrides) -> GlofasDischarge:
    values = dict(
        node_id="tarbela",
        observed_on=dt.date(2022, 8, 28),
        discharge_m3s=7420.5,
        product_type="consolidated",
        system_version="test_version",  # not a real version, so it never clashes with loaded data
        source_file="consolidated_2022-01-01_2022-12-31.nc",
    )
    values.update(overrides)
    return GlofasDischarge(**values)


async def test_rejects_duplicate_node_day_version(db_session):
    db_session.add(make_row())
    await db_session.flush()

    db_session.add(make_row(product_type="intermediate"))
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_allows_same_node_day_from_another_version(db_session):
    db_session.add_all([make_row(), make_row(system_version="another_version")])
    await db_session.flush()


async def test_flags_default_to_empty_and_missing_value_is_allowed(db_session):
    row = make_row(discharge_m3s=None)
    db_session.add(row)
    await db_session.flush()
    await db_session.refresh(row)

    assert row.flags == []
    assert row.discharge_m3s is None
    assert row.ingested_at is not None
