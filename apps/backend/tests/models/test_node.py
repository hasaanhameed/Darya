import pytest
from sqlalchemy import select

from app.models import Node

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

# All prototype nodes from docs/DATA.md "Prototype nodes".
PROTOTYPE_NODE_IDS = {
    "tarbela", "ghazi_barotha", "jinnah", "chashma", "taunsa", "guddu", "sukkur", "kotri",
    "warsak", "nowshera",
    "mangla", "rasul",
    "marala", "khanki", "qadirabad", "trimmu",
    "balloki", "sidhnai",
    "sulemanki", "islam",
    "panjnad",
}


async def test_all_prototype_nodes_are_seeded(db_session):
    node_ids = set(await db_session.scalars(select(Node.id)))
    assert PROTOTYPE_NODE_IDS <= node_ids


async def test_every_prototype_node_has_coordinates(db_session):
    nodes = (await db_session.scalars(select(Node).where(Node.id.in_(PROTOTYPE_NODE_IDS)))).all()
    assert all(node.lat is not None and node.lon is not None for node in nodes)
