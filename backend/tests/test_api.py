"""
Backend tests — Sprint 1 + Sprint 2 smoke suite.

Covers:
  - GET /health
  - GET /api/v1/stories        (US-1: Trending Dashboard)
  - GET /api/v1/stories/:id    (US-2: Story Page Comparison)
  - GET /api/v1/stories/:id    lean grouping (US-3: Lean Label)
  - GET /api/v1/stories/999    404 handling
  - GET /api/v1/stories/:id/factchecks (with results / no_match)

Uses an in-memory SQLite database so no Postgres is required to run tests.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from app.schemas.schemas import WebciteBlock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.models.models import Outlet, Article, Story, FactCheck

# ── Test database (SQLite in-memory) ──────────────────────────────────────

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables, seed test data, tear down after each test."""
    Base.metadata.create_all(bind=engine)
    db = TestSessionLocal()

    # Seed two outlets with different leans
    left_outlet = Outlet(
        id=1, name="Test Left", domain="testleft.com",
        lean="left", lean_display="Left",
        why_label="Rated Left by AllSides.", rating_provider="AllSides",
        rating_method="Blind surveys", confidence="Community consensus",
    )
    right_outlet = Outlet(
        id=2, name="Test Right", domain="testright.com",
        lean="right", lean_display="Right",
        why_label="Rated Right by AllSides.", rating_provider="AllSides",
        rating_method="Blind surveys", confidence="Community consensus",
    )
    center_outlet = Outlet(
        id=3, name="Test Center", domain="testcenter.com",
        lean="center", lean_display="Center",
        why_label="Rated Center by AllSides.", rating_provider="AllSides",
        rating_method="Blind surveys", confidence="Community consensus",
    )
    db.add_all([left_outlet, right_outlet, center_outlet])
    db.flush()

    # Seed a story
    story = Story(
        id=1,
        headline="Senate passes major infrastructure bill",
        first_seen_at=datetime(2026, 3, 20, 10, 0, 0),
        last_updated_at=datetime(2026, 3, 20, 12, 0, 0),
        article_count=3,
        lean_categories_present="left,center,right",
        is_active=True,
    )
    db.add(story)
    db.flush()

    # Seed 3 articles — one per lean
    db.add_all([
        Article(
            id=1, title="Senate passes major infrastructure bill",
            url="https://testleft.com/story1",
            published_at=datetime(2026, 3, 20, 10, 0, 0),
            outlet_id=1, outlet_name="Test Left", story_id=1,
        ),
        Article(
            id=2, title="Infrastructure bill clears Senate vote",
            url="https://testcenter.com/story1",
            published_at=datetime(2026, 3, 20, 10, 30, 0),
            outlet_id=3, outlet_name="Test Center", story_id=1,
        ),
        Article(
            id=3, title="Senate approves controversial infrastructure package",
            url="https://testright.com/story1",
            published_at=datetime(2026, 3, 20, 11, 0, 0),
            outlet_id=2, outlet_name="Test Right", story_id=1,
        ),
    ])
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


# ── Tests ──────────────────────────────────────────────────────────────────

def test_health_check(client):
    """API is reachable and healthy."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_stories_returns_stories(client):
    """
    US-1 (Trending Dashboard):
    GET /api/v1/stories returns a list with at least 1 story,
    each story has a headline, timestamps, and article_count.
    """
    resp = client.get("/api/v1/stories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert len(data["stories"]) >= 1

    story = data["stories"][0]
    assert "headline" in story
    assert "first_seen_at" in story
    assert "last_updated_at" in story
    assert story["article_count"] >= 1
    assert "has_fact_checks" in story
    assert isinstance(story["has_fact_checks"], bool)
    assert "has_webcite" in story
    assert isinstance(story["has_webcite"], bool)


def test_list_stories_includes_preview_articles(client):
    """
    US-1 (Trending Dashboard):
    Each story in the list includes preview_articles with outlet names.
    """
    resp = client.get("/api/v1/stories")
    assert resp.status_code == 200
    story = resp.json()["stories"][0]
    assert len(story["preview_articles"]) >= 1
    for article in story["preview_articles"]:
        assert "title" in article
        assert "url" in article
        assert "outlet_name" in article


def test_list_stories_has_fact_checks_when_cached(client):
    """GET /stories sets has_fact_checks True when real fact-check rows exist."""
    db = TestSessionLocal()
    db.add(FactCheck(story_id=1, no_match=False))
    db.commit()
    db.close()

    resp = client.get("/api/v1/stories")
    assert resp.status_code == 200
    story = next(s for s in resp.json()["stories"] if s["id"] == 1)
    assert story["has_fact_checks"] is True


def test_get_story_groups_by_lean(client):
    """
    US-2 (Story Page Comparison) + US-3 (Lean Label):
    GET /api/v1/stories/1 groups articles into left/center/right
    and each article carries lean_display and why_label.
    """
    resp = client.get("/api/v1/stories/1")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == 1
    assert "headline" in data

    # At least two lean buckets should have articles
    filled_buckets = [
        k for k in ("left", "lean_left", "center", "lean_right", "right")
        if len(data.get(k, [])) > 0
    ]
    assert len(filled_buckets) >= 2

    # Every article must carry lean_display and why_label
    for bucket in ("left", "center", "right"):
        for article in data.get(bucket, []):
            assert article["lean_display"] is not None
            assert article["why_label"] is not None
            assert article["rating_provider"] == "AllSides"


def test_list_stories_includes_summary(client):
    """
    AT-1 enhancement: each story in the list exposes a summary field.
    """
    db = TestSessionLocal()
    story = db.query(Story).filter(Story.id == 1).first()
    story.summary = "Senate passed an infrastructure bill with bipartisan support."
    db.commit()
    db.close()

    resp = client.get("/api/v1/stories")
    assert resp.status_code == 200
    story_data = resp.json()["stories"][0]
    assert "summary" in story_data
    assert story_data["summary"] == "Senate passed an infrastructure bill with bipartisan support."


def test_get_story_not_found(client):
    """
    GET /api/v1/stories/999 returns 404 for a nonexistent story.
    """
    resp = client.get("/api/v1/stories/999")
    assert resp.status_code == 404


@patch("app.api.routes.load_webcite_block")
def test_factcheck_panel_with_results(mock_wc, client):
    """GET /factchecks returns seeded fact-check rows when no_match=False."""
    mock_wc.return_value = WebciteBlock(available=False, status="skipped", message="")
    db = TestSessionLocal()
    db.add(
        FactCheck(
            story_id=1,
            claim_text="Infrastructure spending claim",
            claim_reviewed="Senate passed infrastructure bill",
            rating="Mostly True",
            publisher="PolitiFact",
            review_url="https://example.com/factcheck/1",
            review_date=datetime(2026, 3, 15, 12, 0, 0),
            no_match=False,
        )
    )
    db.commit()
    db.close()

    resp = client.get("/api/v1/stories/1/factchecks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_results"] is True
    assert len(data["fact_checks"]) >= 1
    assert "webcite" in data


@patch("app.api.routes.load_webcite_block")
def test_factcheck_ai_generated_flag(mock_wc, client):
    """
    AT-4a enhancement: AI-generated fact checks expose is_ai_generated=True.
    """
    mock_wc.return_value = WebciteBlock(available=False, status="skipped", message="")
    db = TestSessionLocal()
    db.add(FactCheck(
        story_id=1,
        claim_text="AI analysis of infrastructure bill coverage.",
        claim_reviewed="Senate passes major infrastructure bill",
        rating="Mostly Accurate",
        publisher="Claude AI (Anthropic)",
        no_match=False,
        is_ai_generated=True,
    ))
    db.commit()
    db.close()

    resp = client.get("/api/v1/stories/1/factchecks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_results"] is True
    ai_checks = [fc for fc in data["fact_checks"] if fc["is_ai_generated"]]
    assert len(ai_checks) == 1
    assert ai_checks[0]["publisher"] == "Claude AI (Anthropic)"
    assert ai_checks[0]["rating"] == "Mostly Accurate"


@patch("app.api.routes.load_webcite_block")
def test_factcheck_panel_no_match(mock_wc, client):
    """GET /factchecks ignores no_match placeholder rows (no lazy sync when a row exists)."""
    mock_wc.return_value = WebciteBlock(available=False, status="skipped", message="")
    db = TestSessionLocal()
    db.add(FactCheck(story_id=1, no_match=True))
    db.commit()
    db.close()

    resp = client.get("/api/v1/stories/1/factchecks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_results"] is False
    assert "No matching claim reviews found." in data["message"]
    assert "webcite" in data
