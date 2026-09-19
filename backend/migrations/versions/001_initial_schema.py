"""Initial schema for habitations, risks, and relocation sites

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'habitations',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
        sa.Column('population', sa.Integer(), nullable=True),
        sa.Column('households', sa.Integer(), nullable=True),
        sa.Column('exposure_info', sa.JSON(), nullable=True),
        sa.Column('vulnerability_info', sa.JSON(), nullable=True),
        sa.Column('accessibility_info', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'risks',
        sa.Column('habitation_id', sa.String(length=64), nullable=False),
        sa.Column('current_risk', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_24h', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_72h', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('trajectory', sa.String(length=64), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('risk_drivers', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['habitation_id'], ['habitations.id'], ),
        sa.PrimaryKeyConstraint('habitation_id')
    )

    op.create_table(
        'relocation_sites',
        sa.Column('site_id', sa.String(length=64), nullable=False),
        sa.Column('habitation_id', sa.String(length=64), nullable=False),
        sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT', name='geometry'), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='candidate'),
        sa.Column('safety_result', sa.String(length=32), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('infrastructure_info', sa.JSON(), nullable=True),
        sa.Column('accessibility', sa.String(length=64), nullable=True),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['habitation_id'], ['habitations.id'], ),
        sa.PrimaryKeyConstraint('site_id')
    )


def downgrade() -> None:
    op.drop_table('relocation_sites')
    op.drop_table('risks')
    op.drop_table('habitations')
