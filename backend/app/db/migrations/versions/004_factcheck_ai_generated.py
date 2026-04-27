"""add is_ai_generated to fact_checks

Revision ID: 004
Revises: 003
Create Date: 2026-04-26
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'fact_checks',
        sa.Column('is_ai_generated', sa.Boolean(), nullable=True, server_default='false')
    )


def downgrade():
    op.drop_column('fact_checks', 'is_ai_generated')
