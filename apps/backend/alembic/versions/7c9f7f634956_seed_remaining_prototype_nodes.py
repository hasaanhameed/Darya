"""seed remaining prototype nodes

Revision ID: 7c9f7f634956
Revises: 26dd59cfcac6
Create Date: 2026-11-22 12:29:33.552419

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c9f7f634956'
down_revision: Union[str, Sequence[str], None] = '26dd59cfcac6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Prototype nodes not covered by WAPDA, so the gridded sources (GloFAS, IMERG) can cover all of them.
# Coordinates are approximate (docs/DATA.md "Prototype nodes"); Sidhnai's are rougher still.
NEW_NODES = [
    {"id": "taunsa", "name": "Taunsa Barrage", "river": "Indus", "lat": 30.51, "lon": 70.85},
    {"id": "guddu", "name": "Guddu Barrage", "river": "Indus", "lat": 28.42, "lon": 69.71},
    {"id": "sukkur", "name": "Sukkur Barrage", "river": "Indus", "lat": 27.68, "lon": 68.85},
    {"id": "kotri", "name": "Kotri Barrage", "river": "Indus", "lat": 25.44, "lon": 68.32},
    {"id": "nowshera", "name": "Nowshera", "river": "Kabul", "lat": 34.01, "lon": 71.98},
    {"id": "rasul", "name": "Rasul Barrage", "river": "Jhelum", "lat": 32.68, "lon": 73.52},
    {"id": "marala", "name": "Marala Headworks", "river": "Chenab", "lat": 32.67, "lon": 74.46},
    {"id": "khanki", "name": "Khanki Headworks", "river": "Chenab", "lat": 32.41, "lon": 73.97},
    {"id": "qadirabad", "name": "Qadirabad Barrage", "river": "Chenab", "lat": 32.32, "lon": 73.69},
    {"id": "trimmu", "name": "Trimmu Barrage", "river": "Chenab", "lat": 31.14, "lon": 72.15},
    {"id": "balloki", "name": "Balloki Headworks", "river": "Ravi", "lat": 31.22, "lon": 73.86},
    {"id": "sidhnai", "name": "Sidhnai Barrage", "river": "Ravi", "lat": 30.6, "lon": 72.1},
    {"id": "sulemanki", "name": "Sulemanki Headworks", "river": "Sutlej", "lat": 30.38, "lon": 73.87},
    {"id": "islam", "name": "Islam Headworks", "river": "Sutlej", "lat": 29.83, "lon": 72.55},
    {"id": "panjnad", "name": "Panjnad Headworks", "river": "Panjnad", "lat": 29.35, "lon": 71.02},
]

nodes = sa.table(
    "nodes",
    sa.column("id", sa.String),
    sa.column("name", sa.String),
    sa.column("river", sa.String),
    sa.column("lat", sa.Double),
    sa.column("lon", sa.Double),
)


def upgrade() -> None:
    op.bulk_insert(nodes, NEW_NODES)


def downgrade() -> None:
    op.execute(nodes.delete().where(nodes.c.id.in_([node["id"] for node in NEW_NODES])))
