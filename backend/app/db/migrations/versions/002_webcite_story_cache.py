"""webcite_story_cache table

Revision ID: 002_webcite
Revises: 001_initial
Create Date: 2026-04-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_webcite"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webcite_story_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("story_id", sa.Integer(), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("headline_used", sa.String(500), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("has_citations", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_webcite_story_cache_story_id", "webcite_story_cache", ["story_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_webcite_story_cache_story_id", table_name="webcite_story_cache")
    op.drop_table("webcite_story_cache")
