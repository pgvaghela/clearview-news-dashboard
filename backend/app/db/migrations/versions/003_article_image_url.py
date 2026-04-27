"""add image_url to articles

Revision ID: 003_article_image_url
Revises: 002_webcite_story_cache
Create Date: 2026-04-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_article_image_url"
down_revision: Union[str, None] = "002_webcite"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("image_url", sa.String(1000), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "image_url")
