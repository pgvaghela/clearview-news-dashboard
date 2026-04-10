"""
Fact-check lookup via Google Fact Check Tools API.

Caches results in `fact_checks`; skips API calls when any row exists for the story.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import FactCheck, Story

logger = logging.getLogger(__name__)

FACTCHECK_SEARCH_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"


def _parse_rfc3339(s: str | None) -> datetime | None:
    if not s:
        return None
    text = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _call_google_claims_search(query: str, api_key: str) -> dict:
    resp = httpx.get(
        FACTCHECK_SEARCH_URL,
        params={
            "query": query,
            "key": api_key,
            "languageCode": "en",
            "pageSize": 10,
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def sync_fact_checks_for_story(db: Session, story_id: int) -> None:
    """
    Fetch fact checks for a story headline and persist to `fact_checks`.

    - If any row already exists for this story_id, returns immediately (cache).
    - On empty API results, inserts one row with no_match=True.
    - On success, inserts one row per claimReview from the API.
    """
    cached = db.query(FactCheck).filter(FactCheck.story_id == story_id).first()
    if cached is not None:
        logger.info("Story %s: fact checks already cached, skipping API.", story_id)
        return

    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        logger.warning("Story %s not found.", story_id)
        return

    api_key = (settings.GOOGLE_FACTCHECK_API_KEY or "").strip()
    if not api_key:
        logger.warning(
            "GOOGLE_FACTCHECK_API_KEY not set; recording no_match for story %s.",
            story_id,
        )
        db.add(FactCheck(story_id=story_id, no_match=True))
        db.commit()
        return

    try:
        payload = _call_google_claims_search(story.headline, api_key)
    except Exception as exc:
        logger.exception("Fact check API error for story %s: %s", story_id, exc)
        db.add(FactCheck(story_id=story_id, no_match=True))
        db.commit()
        return

    claims = payload.get("claims") or []
    rows: list[FactCheck] = []

    for claim in claims:
        claim_text = claim.get("text")
        claim_date_str = claim.get("claimDate")
        for review in claim.get("claimReview") or []:
            publisher = (review.get("publisher") or {}).get("name")
            textual_rating = review.get("textualRating")
            url = review.get("url")
            title = review.get("title")
            claim_reviewed = title or claim_text
            review_date = _parse_rfc3339(review.get("reviewDate")) or _parse_rfc3339(
                claim_date_str
            )

            rows.append(
                FactCheck(
                    story_id=story_id,
                    claim_text=claim_text,
                    claim_reviewed=claim_reviewed,
                    rating=textual_rating,
                    publisher=publisher,
                    review_url=url,
                    review_date=review_date,
                    no_match=False,
                )
            )

    if not rows:
        db.add(FactCheck(story_id=story_id, no_match=True))
        logger.info("Story %s: no fact-check results from API.", story_id)
    else:
        for row in rows:
            db.add(row)
        logger.info("Story %s: saved %d fact-check row(s).", story_id, len(rows))

    db.commit()
