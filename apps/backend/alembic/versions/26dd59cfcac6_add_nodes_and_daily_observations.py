"""add nodes and daily_observations

Revision ID: 26dd59cfcac6
Revises:
Create Date: 2026-10-18 18:09:25.031150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26dd59cfcac6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The stations covered by WAPDA data (ADR-017). Coordinates are approximate (docs/DATA.md).
WAPDA_NODES = [
    {"id": "tarbela", "name": "Tarbela Dam", "river": "Indus", "lat": 34.09, "lon": 72.69},
    {"id": "ghazi_barotha", "name": "Ghazi Barotha Barrage", "river": "Indus", "lat": 33.98, "lon": 72.65},
    {"id": "jinnah", "name": "Jinnah Barrage", "river": "Indus", "lat": 32.92, "lon": 71.52},
    {"id": "chashma", "name": "Chashma Barrage", "river": "Indus", "lat": 32.43, "lon": 71.38},
    {"id": "warsak", "name": "Warsak Dam", "river": "Kabul", "lat": 34.17, "lon": 71.36},
    {"id": "mangla", "name": "Mangla Dam", "river": "Jhelum", "lat": 33.14, "lon": 73.64},
]


def upgrade() -> None:
    nodes = op.create_table('nodes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('river', sa.String(), nullable=False),
    sa.Column('lat', sa.Double(), nullable=True),
    sa.Column('lon', sa.Double(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('daily_observations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('node_id', sa.String(), nullable=False),
    sa.Column('observed_on', sa.Date(), nullable=False),
    sa.Column('source', sa.String(), nullable=False),
    sa.Column('level_ft', sa.Double(), nullable=True),
    sa.Column('inflow_cfs', sa.Double(), nullable=True),
    sa.Column('outflow_turbine_cfs', sa.Double(), nullable=True),
    sa.Column('outflow_other_cfs', sa.Double(), nullable=True),
    sa.Column('outflow_total_cfs', sa.Double(), nullable=True),
    sa.Column('irrigation_indent_raw', sa.String(), nullable=True),
    sa.Column('flags', sa.ARRAY(sa.String()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('source_file', sa.String(), nullable=False),
    sa.Column('sheet', sa.String(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['node_id'], ['nodes.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('node_id', 'observed_on', 'source')
    )
    op.create_index('ix_daily_observations_node_id_observed_on', 'daily_observations', ['node_id', 'observed_on'], unique=False)

    op.bulk_insert(nodes, WAPDA_NODES)


def downgrade() -> None:
    op.drop_index('ix_daily_observations_node_id_observed_on', table_name='daily_observations')
    op.drop_table('daily_observations')
    op.drop_table('nodes')
