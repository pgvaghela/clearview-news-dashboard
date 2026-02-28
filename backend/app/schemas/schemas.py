from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Outlet / Lean Label ────────────────────────────────────────────────────

class LeanLabelSchema(BaseModel):
    lean: str
    lean_display: str
    why_label: str
    rating_provider: str
    rating_method: Optional[str] = None
    confidence: Optional[str] = None


class OutletSchema(BaseModel):
    id: int
    name: str
    domain: Optional[str] = None
    lean_display: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Article ────────────────────────────────────────────────────────────────

class ArticleSchema(BaseModel):
    id: int
    title: str
    url: str
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    outlet_name: Optional[str] = None
    lean_display: Optional[str] = None   # resolved from outlet
    why_label: Optional[str] = None
    rating_provider: Optional[str] = None
    rating_method: Optional[str] = None
    confidence: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Story (list view — dashboard) ─────────────────────────────────────────

class StoryListItem(BaseModel):
    id: int
    headline: str
    first_seen_at: datetime
    last_updated_at: datetime
    article_count: int
    lean_categories_present: Optional[str] = None
    # Preview: one article per lean category
    preview_articles: list[ArticleSchema] = []

    model_config = {"from_attributes": True}


class StoriesResponse(BaseModel):
    total: int
    page: int
    page_size: int
    stories: list[StoryListItem]


# ── Story (detail view — story page) ──────────────────────────────────────

class StoryDetailResponse(BaseModel):
    id: int
    headline: str
    first_seen_at: datetime
    last_updated_at: datetime
    article_count: int
    lean_categories_present: Optional[str] = None
    left: list[ArticleSchema] = []
    lean_left: list[ArticleSchema] = []
    center: list[ArticleSchema] = []
    lean_right: list[ArticleSchema] = []
    right: list[ArticleSchema] = []

    model_config = {"from_attributes": True}


# ── Fact Checks ────────────────────────────────────────────────────────────

class FactCheckSchema(BaseModel):
    id: int
    claim_text: Optional[str] = None
    claim_reviewed: Optional[str] = None
    rating: Optional[str] = None
    publisher: Optional[str] = None
    review_url: Optional[str] = None
    review_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class FactChecksResponse(BaseModel):
    story_id: int
    has_results: bool
    message: str   # "No matching claim reviews found." if empty
    fact_checks: list[FactCheckSchema] = []
