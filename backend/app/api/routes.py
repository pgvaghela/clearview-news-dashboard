"""
API routes for ClearView News Dashboard.

Endpoints (Sprint 1):
  GET /api/v1/stories              — paginated list of trending stories
  GET /api/v1/stories/{story_id}   — story detail with articles grouped by lean

Endpoints (Sprint 2):
  GET /api/v1/stories/{story_id}/factchecks — cached fact-check reviews
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.models import Article, Story, FactCheck, WebciteStoryCache
from app.schemas.schemas import (
    StoriesResponse,
    StoryListItem,
    StoryDetailResponse,
    ArticleSchema,
    FactChecksResponse,
    FactCheckSchema,
)
from app.services.labeling import get_lean_info_for_outlet
from app.services.factchecks import sync_fact_checks_for_story
from app.services.webcite import load_webcite_block

router = APIRouter()

# ── Helpers ────────────────────────────────────────────────────────────────


def _article_to_schema(article: Article) -> ArticleSchema:
    lean_info = get_lean_info_for_outlet(article.outlet)
    return ArticleSchema(
        id=article.id,
        title=article.title,
        url=article.url,
        description=article.description,
        published_at=article.published_at,
        outlet_name=article.outlet.name if article.outlet else article.outlet_name,
        image_url=article.image_url,
        lean_display=lean_info["lean_display"],
        why_label=lean_info["why_label"],
        rating_provider="AllSides",
        rating_method=lean_info.get("rating_method"),
        confidence=lean_info.get("confidence"),
    )


def _lean_bucket(lean_display: str | None) -> str:
    """Map a lean_display value to a bucket key."""
    mapping = {
        "Left": "left",
        "Lean Left": "lean_left",
        "Center": "center",
        "Lean Right": "lean_right",
        "Right": "right",
    }
    return mapping.get(lean_display or "", "center")


# ── GET /stories ───────────────────────────────────────────────────────────

@router.get("/stories", response_model=StoriesResponse, summary="List trending stories")
def list_stories(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=50, description="Stories per page"),
    db: Session = Depends(get_db),
):
    """
    Returns a paginated list of active stories ordered by last_updated_at desc.
    Each story includes up to one preview article per lean category.
    """
    total = db.query(Story).filter(Story.is_active).count()

    stories = (
        db.query(Story)
        .filter(Story.is_active)
        .options(joinedload(Story.articles).joinedload(Article.outlet))
        .order_by(Story.article_count.desc(), Story.last_updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    story_ids = [s.id for s in stories]
    factcheck_story_ids: set[int] = set()
    if story_ids:
        factcheck_story_ids = {
            row[0]
            for row in db.query(FactCheck.story_id)
            .filter(
                FactCheck.story_id.in_(story_ids),
                FactCheck.no_match.is_(False),
            )
            .distinct()
            .all()
        }
        webcite_story_ids = {
            row[0]
            for row in db.query(WebciteStoryCache.story_id)
            .filter(
                WebciteStoryCache.story_id.in_(story_ids),
                WebciteStoryCache.ok.is_(True),
                WebciteStoryCache.has_citations.is_(True),
            )
            .all()
        }
    else:
        webcite_story_ids = set()

    story_items = []
    for story in stories:
        # Build one preview article per lean bucket
        seen_leans: set[str] = set()
        preview_articles: list[ArticleSchema] = []
        for article in sorted(
            story.articles,
            key=lambda a: a.published_at or a.fetched_at,
            reverse=True,
        ):
            lean_info = get_lean_info_for_outlet(article.outlet)
            bucket = _lean_bucket(lean_info["lean_display"])
            if bucket not in seen_leans:
                seen_leans.add(bucket)
                preview_articles.append(_article_to_schema(article))
            if len(seen_leans) >= 5:
                break

        story_items.append(
            StoryListItem(
                id=story.id,
                headline=story.headline,
                summary=story.summary,
                first_seen_at=story.first_seen_at,
                last_updated_at=story.last_updated_at,
                article_count=story.article_count,
                lean_categories_present=story.lean_categories_present,
                has_fact_checks=story.id in factcheck_story_ids,
                has_webcite=story.id in webcite_story_ids,
                preview_articles=preview_articles,
            )
        )

    return StoriesResponse(
        total=total,
        page=page,
        page_size=page_size,
        stories=story_items,
    )


# ── GET /stories/{story_id} ────────────────────────────────────────────────

@router.get(
    "/stories/{story_id}",
    response_model=StoryDetailResponse,
    summary="Story detail — articles grouped by lean",
)
def get_story(story_id: int, db: Session = Depends(get_db)):
    """
    Returns full story detail.
    Articles are grouped into left / lean_left / center / lean_right / right buckets.
    """
    story = (
        db.query(Story)
        .options(joinedload(Story.articles).joinedload(Article.outlet))
        .filter(Story.id == story_id)
        .first()
    )
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    buckets: dict[str, list[ArticleSchema]] = {
        "left": [],
        "lean_left": [],
        "center": [],
        "lean_right": [],
        "right": [],
    }

    for article in sorted(
        story.articles,
        key=lambda a: a.published_at or a.fetched_at,
        reverse=True,
    ):
        lean_info = get_lean_info_for_outlet(article.outlet)
        bucket = _lean_bucket(lean_info["lean_display"])
        if bucket in buckets:
            buckets[bucket].append(_article_to_schema(article))

    return StoryDetailResponse(
        id=story.id,
        headline=story.headline,
        first_seen_at=story.first_seen_at,
        last_updated_at=story.last_updated_at,
        article_count=story.article_count,
        lean_categories_present=story.lean_categories_present,
        **buckets,
    )


# ── GET /stories/{story_id}/factchecks ────────────────────────────────────

@router.get(
    "/stories/{story_id}/factchecks",
    response_model=FactChecksResponse,
    summary="Fact-check panel for a story",
)
def get_fact_checks(story_id: int, db: Session = Depends(get_db)):
    """
    Returns fact-check rows for a story (no_match=False only).

    If the story has never been fact-checked (no rows in ``fact_checks``), triggers
    one Google Fact Check Tools sync. If only ``no_match`` placeholders exist, returns
    the empty message without re-querying Google — use ``scripts/run_factchecks.py``
    to clear placeholders and retry after fixing the API key.
    """
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    fact_checks = (
        db.query(FactCheck)
        .filter(FactCheck.story_id == story_id, FactCheck.no_match.is_(False))
        .order_by(FactCheck.review_date.desc())
        .all()
    )

    # First-ever fetch: no rows at all. Avoid re-calling Google on every page view when
    # we already stored no_match (user can re-run scripts/run_factchecks.py to retry).
    if not fact_checks:
        any_row = (
            db.query(FactCheck.id)
            .filter(FactCheck.story_id == story_id)
            .first()
        )
        if any_row is None:
            sync_fact_checks_for_story(db, story_id)
            fact_checks = (
                db.query(FactCheck)
                .filter(FactCheck.story_id == story_id, FactCheck.no_match.is_(False))
                .order_by(FactCheck.review_date.desc())
                .all()
            )

    webcite = load_webcite_block(db, story)

    if not fact_checks:
        return FactChecksResponse(
            story_id=story_id,
            has_results=False,
            message="No matching claim reviews found.",
            fact_checks=[],
            webcite=webcite,
        )

    return FactChecksResponse(
        story_id=story_id,
        has_results=True,
        message=f"{len(fact_checks)} claim review(s) found.",
        fact_checks=[FactCheckSchema.model_validate(fc) for fc in fact_checks],
        webcite=webcite,
    )
