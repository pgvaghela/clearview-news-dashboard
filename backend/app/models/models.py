from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.database import Base


class Outlet(Base):
    """News outlet with AllSides bias rating."""
    __tablename__ = "outlets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    domain = Column(String(200), nullable=True, index=True)
    lean = Column(String(20), nullable=True)          # left | lean_left | center | lean_right | right
    lean_display = Column(String(20), nullable=True)  # "Left", "Center", "Right" (display label)
    why_label = Column(Text, nullable=True)           # plain-language explanation
    rating_provider = Column(String(100), default="AllSides")
    rating_method = Column(String(200), nullable=True)
    confidence = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    articles = relationship("Article", back_populates="outlet")


class Article(Base):
    """A single news article fetched from an outlet."""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    outlet_id = Column(Integer, ForeignKey("outlets.id"), nullable=True)
    outlet_name = Column(String(200), nullable=True)  # raw name from API
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True, index=True)

    outlet = relationship("Outlet", back_populates="articles")
    story = relationship("Story", back_populates="articles")

    __table_args__ = (
        UniqueConstraint("url", name="uq_article_url"),
    )


class Story(Base):
    """A cluster of articles about the same event."""
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    headline = Column(String(500), nullable=False)      # representative headline
    summary = Column(Text, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    article_count = Column(Integer, default=0)
    lean_categories_present = Column(String(100), nullable=True)  # e.g. "left,center,right"
    is_active = Column(Boolean, default=True)

    articles = relationship("Article", back_populates="story")
    fact_checks = relationship("FactCheck", back_populates="story")
    webcite_cache = relationship(
        "WebciteStoryCache", back_populates="story", uselist=False
    )


class LeanLabel(Base):
    """
    Cached lean label for a specific outlet.
    Populated from AllSides CSV. Stored separately so it can be
    updated without re-seeding the whole outlets table.
    """
    __tablename__ = "lean_labels"

    id = Column(Integer, primary_key=True, index=True)
    outlet_id = Column(Integer, ForeignKey("outlets.id"), nullable=False, unique=True)
    lean = Column(String(20), nullable=False)
    lean_display = Column(String(20), nullable=False)
    why_label = Column(Text, nullable=False)
    rating_provider = Column(String(100), default="AllSides")
    rating_method = Column(String(200), nullable=True)
    confidence = Column(String(100), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    outlet = relationship("Outlet")


class FactCheck(Base):
    """A professional fact-check claim review linked to a story. (Sprint 2)"""
    __tablename__ = "fact_checks"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    claim_text = Column(Text, nullable=True)
    claim_reviewed = Column(Text, nullable=True)
    rating = Column(String(100), nullable=True)       # e.g. "False", "Mostly True"
    publisher = Column(String(200), nullable=True)
    review_url = Column(String(1000), nullable=True)
    review_date = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    no_match = Column(Boolean, default=False)          # True = queried and found nothing

    story = relationship("Story", back_populates="fact_checks")


class WebciteStoryCache(Base):
    """Cached WebCite sources/search response per story (headline-scoped)."""

    __tablename__ = "webcite_story_cache"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, unique=True)
    headline_used = Column(String(500), nullable=False)
    ok = Column(Boolean, default=True, nullable=False)
    has_citations = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    response_json = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("Story", back_populates="webcite_cache")
