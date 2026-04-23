"""
Fact-check lookup via Google Fact Check Tools API.

Caches positive results in `fact_checks`. Skips API when real rows exist; clears
`no_match` placeholders so a new API key or headline can re-query.
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

# Common English stop-words excluded when building a shorter fallback query.
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "in", "on", "at", "to", "for", "of", "and", "or",
    "but", "with", "from", "that", "this", "it", "its", "are", "was", "were",
    "be", "been", "have", "has", "had", "will", "would", "could", "should",
    "after", "before", "over", "under", "as", "by", "up", "out", "about",
    "into", "than", "not", "no", "so", "if", "do", "does", "did", "get",
    "live", "new", "says", "say",
})

# Literal from .env.example — not a real key; Google returns 400 if used.
_PLACEHOLDER_GOOGLE_KEYS = frozenset({"your_google_factcheck_api_key_here"})
_placeholder_key_logged = False


def _google_factcheck_key_usable(key: str) -> bool:
    k = (key or "").strip()
    if not k or k in _PLACEHOLDER_GOOGLE_KEYS:
        return False
    return True


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


def _keyword_query(headline: str, n: int = 5) -> str:
    """Return the top-n significant words from a headline as a shorter fallback query.

    Strips punctuation and common stop-words so that e.g.
    "Common vaccine slashes Alzheimer's disease risk when dose is increased"
    becomes "vaccine slashes Alzheimers disease risk", which the Fact Check
    API can match even when the full verbatim headline has no indexed results.
    """
    tokens = [t.strip(".,;:!?()[]\"'s") for t in headline.split()]
    significant = [
        t for t in tokens
        if t and t.lower() not in _STOP_WORDS and len(t) > 2
    ]
    return " ".join(significant[:n])


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

    - If any no_match=False row exists, returns immediately (cache).
    - Deletes no_match-only rows before calling the API so runs can recover after fixing the key.
    - On empty API results, inserts one row with no_match=True.
    - On success, inserts one row per claimReview from the API.
    """
    has_positive = (
        db.query(FactCheck)
        .filter(FactCheck.story_id == story_id, FactCheck.no_match.is_(False))
        .first()
    )
    if has_positive is not None:
        logger.info(
            "Story %s: fact checks already cached (has results), skipping API.",
            story_id,
        )
        return

    removed = (
        db.query(FactCheck)
        .filter(FactCheck.story_id == story_id, FactCheck.no_match.is_(True))
        .delete(synchronize_session=False)
    )
    if removed:
        db.commit()
        logger.info(
            "Story %s: removed %d no_match placeholder(s); will query Google API.",
            story_id,
            removed,
        )

    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        logger.warning("Story %s not found.", story_id)
        return

    api_key = (settings.GOOGLE_FACTCHECK_API_KEY or "").strip()
    global _placeholder_key_logged
    if not _google_factcheck_key_usable(api_key):
        if not _placeholder_key_logged:
            logger.warning(
                "GOOGLE_FACTCHECK_API_KEY is empty or still the .env.example placeholder. "
                "Get a key from Google Cloud Console, enable Fact Check Tools API, and set "
                "GOOGLE_FACTCHECK_API_KEY in backend/.env. Skipping API calls; storing no_match."
            )
            _placeholder_key_logged = True
        db.add(FactCheck(story_id=story_id, no_match=True))
        db.commit()
        return

    headline = story.headline or ""
    # Try the full headline first; fall back to keyword-only query when the
    # verbatim headline has no indexed fact-checks (common for breaking news).
    queries = [headline, _keyword_query(headline)]

    claims: list = []
    for query in queries:
        if not query:
            continue
        try:
            logger.info(
                "Story %s: querying Google Fact Check API (query: %s…)",
                story_id,
                query[:80],
            )
            payload = _call_google_claims_search(query, api_key)
        except httpx.HTTPStatusError as exc:
            err_body = (exc.response.text or "")[:300].replace("\n", " ")
            logger.warning(
                "Story %s: Google Fact Check API HTTP %s — %s",
                story_id,
                exc.response.status_code,
                err_body or exc.response.reason_phrase,
            )
            db.add(FactCheck(story_id=story_id, no_match=True))
            db.commit()
            return
        except Exception as exc:
            logger.warning("Story %s: Fact check API error: %s", story_id, exc)
            db.add(FactCheck(story_id=story_id, no_match=True))
            db.commit()
            return

        claims = payload.get("claims") or []
        if claims:
            break  # Full headline matched — no need for fallback
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
