"""add rain_stations and pmd_rainfall (ADR-023)

Revision ID: 38e33b60eddb
Revises: bac4c793a2cb
Create Date: 2026-11-26 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38e33b60eddb'
down_revision: Union[str, Sequence[str], None] = 'bac4c793a2cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('rain_stations',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('pmd_name', sa.String(), nullable=False),
    sa.Column('lat', sa.Double(), nullable=True),
    sa.Column('lon', sa.Double(), nullable=True),
    sa.Column('province', sa.String(), nullable=True),
    sa.Column('basin', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pmd_rainfall',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('station_id', sa.String(), nullable=False),
    sa.Column('observed_on', sa.Date(), nullable=False),
    sa.Column('rainfall_mm', sa.Double(), nullable=True),
    sa.Column('rainfall_raw', sa.String(), nullable=False),
    sa.Column('flags', sa.ARRAY(sa.String()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('source_file', sa.String(), nullable=False),
    sa.Column('sheet_row', sa.Integer(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['station_id'], ['rain_stations.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('station_id', 'observed_on')
    )
    op.create_index('ix_pmd_rainfall_station_id_observed_on', 'pmd_rainfall', ['station_id', 'observed_on'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_pmd_rainfall_station_id_observed_on', table_name='pmd_rainfall')
    op.drop_table('pmd_rainfall')
    op.drop_table('rain_stations')
