"""initial schema — 5 tables

Revision ID: 001_initial
Revises:
Create Date: 2026-03-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outlets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("domain", sa.String(200), nullable=True),
        sa.Column("lean", sa.String(20), nullable=True),
        sa.Column("lean_display", sa.String(20), nullable=True),
        sa.Column("why_label", sa.Text(), nullable=True),
        sa.Column("rating_provider", sa.String(100), server_default="AllSides"),
        sa.Column("rating_method", sa.String(200), nullable=True),
        sa.Column("confidence", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_outlets_domain", "outlets", ["domain"])

    op.create_table(
        "stories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("headline", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("article_count", sa.Integer(), server_default="0"),
        sa.Column("lean_categories_present", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )
    op.create_index("ix_stories_first_seen_at", "stories", ["first_seen_at"])

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("outlet_id", sa.Integer(), sa.ForeignKey("outlets.id"), nullable=True),
        sa.Column("outlet_name", sa.String(200), nullable=True),
        sa.Column("story_id", sa.Integer(), sa.ForeignKey("stories.id"), nullable=True),
    )
    op.create_index("ix_articles_published_at", "articles", ["published_at"])
    op.create_index("ix_articles_story_id", "articles", ["story_id"])
    op.create_unique_constraint("uq_article_url", "articles", ["url"])

    op.create_table(
        "lean_labels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("outlet_id", sa.Integer(), sa.ForeignKey("outlets.id"), nullable=False, unique=True),
        sa.Column("lean", sa.String(20), nullable=False),
        sa.Column("lean_display", sa.String(20), nullable=False),
        sa.Column("why_label", sa.Text(), nullable=False),
        sa.Column("rating_provider", sa.String(100), server_default="AllSides"),
        sa.Column("rating_method", sa.String(200), nullable=True),
        sa.Column("confidence", sa.String(100), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "fact_checks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("story_id", sa.Integer(), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=True),
        sa.Column("claim_reviewed", sa.Text(), nullable=True),
        sa.Column("rating", sa.String(100), nullable=True),
        sa.Column("publisher", sa.String(200), nullable=True),
        sa.Column("review_url", sa.String(1000), nullable=True),
        sa.Column("review_date", sa.DateTime(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("no_match", sa.Boolean(), server_default="false"),
    )
    op.create_index("ix_fact_checks_story_id", "fact_checks", ["story_id"])


def downgrade() -> None:
    op.drop_table("fact_checks")
    op.drop_table("lean_labels")
    op.drop_table("articles")
    op.drop_table("stories")
    op.drop_table("outlets")
