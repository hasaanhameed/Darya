import datetime as dt

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models import DailyObservation, Node

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

WAPDA_NODE_IDS = {"tarbela", "ghazi_barotha", "mangla", "warsak", "chashma", "jinnah"}


def make_observation(**overrides) -> DailyObservation:
    values = dict(
        node_id="tarbela",
        observed_on=dt.date(2022, 8, 28),
        source="wapda_hydel_synopsis",
        inflow_cfs=264700.0,
        source_file="AUG - 2022 (31).xlsx",
        sheet="28",
    )
    values.update(overrides)
    return DailyObservation(**values)


async def test_seeded_wapda_nodes_exist(db_session):
    node_ids = set(await db_session.scalars(select(Node.id)))
    assert WAPDA_NODE_IDS <= node_ids


async def test_rejects_duplicate_node_day_source(db_session):
    db_session.add(make_observation())
    await db_session.flush()

    db_session.add(make_observation())
    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_allows_same_node_day_from_another_source(db_session):
    db_session.add_all([make_observation(), make_observation(source="another_source")])
    await db_session.flush()

    count = await db_session.scalar(
        select(func.count()).select_from(DailyObservation).where(DailyObservation.node_id == "tarbela")
    )
    assert count == 2


async def test_flags_default_to_empty(db_session):
    observation = make_observation()
    db_session.add(observation)
    await db_session.flush()
    await db_session.refresh(observation)

    assert observation.flags == []
