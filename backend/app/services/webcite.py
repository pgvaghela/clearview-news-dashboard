"""
WebCite API — authoritative source search for a headline (paid tier, credit-based).

Docs: https://api.webcite.co — we use POST /api/v1/sources/search (2 credits/call).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Story, WebciteStoryCache
from app.schemas.schemas import WebciteBlock, WebciteCitationOut

logger = logging.getLogger(__name__)

WEBCITE_SEARCH_URL = "https://api.webcite.co/api/v1/sources/search"

_PLACEHOLDER_KEYS = frozenset({"", "your_webcite_api_key_here"})


def _key_usable(key: str) -> bool:
    k = (key or "").strip()
    return bool(k) and k not in _PLACEHOLDER_KEYS


def _parse_search_payload(data: dict) -> tuple[list[WebciteCitationOut], str | None, str | None, str | None]:
    """Extract citations, stance summary, claim, thread_id from sources/search JSON."""
    thread_id = data.get("thread_id")
    groups = data.get("claim_groups") or []
    if not groups:
        return [], None, data.get("content"), thread_id

    g0 = groups[0]
    claim = g0.get("claim")
    stance_summary = g0.get("stance_summary")
    raw_cites = g0.get("citations") or []

    citations: list[WebciteCitationOut] = []
    for c in raw_cites[:15]:
        citations.append(
            WebciteCitationOut(
                title=c.get("title"),
                url=c.get("url"),
                snippet=c.get("snippet"),
                credibility_score=c.get("credibility_score"),
                source_type=c.get("source_type"),
                stance=c.get("stance"),
            )
        )
    return citations, stance_summary, claim, thread_id


def _call_sources_search(query: str, api_key: str, limit: int) -> dict:
    resp = httpx.post(
        WEBCITE_SEARCH_URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
        },
        json={"query": query, "limit": min(max(limit, 1), 20)},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()


def sync_webcite_for_story(db: Session, story: Story) -> WebciteBlock:
    """
    Fetch WebCite sources for ``story.headline`` and upsert ``WebciteStoryCache``.
    Returns a public summary block for the API.
    """
    api_key = (settings.WEBCITE_API_KEY or "").strip()
    if not _key_usable(api_key):
        return WebciteBlock(
            available=False,
            status="skipped",
            message="WebCite API key not configured.",
        )

    headline = (story.headline or "").strip()
    if not headline:
        return WebciteBlock(available=True, status="no_data", message="No headline to search.")

    cached = (
        db.query(WebciteStoryCache)
        .filter(WebciteStoryCache.story_id == story.id)
        .first()
    )
    if cached and cached.headline_used == headline and cached.response_json is not None:
        return _block_from_cache_row(cached)

    limit = max(1, min(settings.WEBCITE_SOURCES_LIMIT, 20))

    try:
        payload = _call_sources_search(headline, api_key, limit)
    except httpx.HTTPStatusError as exc:
        err = (exc.response.text or "")[:400].replace("\n", " ")
        logger.warning("WebCite HTTP %s for story %s: %s", exc.response.status_code, story.id, err)
        row = cached or WebciteStoryCache(story_id=story.id)
        row.headline_used = headline
        row.ok = False
        row.has_citations = False
        row.error_message = err or exc.response.reason_phrase
        row.response_json = None
        row.fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if cached is None:
            db.add(row)
        db.commit()
        return WebciteBlock(
            available=True,
            status="error",
            message="WebCite request failed. Check credits and rate limits.",
        )
    except Exception as exc:
        logger.warning("WebCite error for story %s: %s", story.id, exc)
        row = cached or WebciteStoryCache(story_id=story.id)
        row.headline_used = headline
        row.ok = False
        row.has_citations = False
        row.error_message = str(exc)[:500]
        row.response_json = None
        row.fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if cached is None:
            db.add(row)
        db.commit()
        return WebciteBlock(
            available=True,
            status="error",
            message="WebCite request failed.",
        )

    citations, stance_summary, claim, thread_id = _parse_search_payload(payload)
    has_citations = len(citations) > 0 or int(payload.get("totalResults") or 0) > 0

    row = cached or WebciteStoryCache(story_id=story.id)
    row.headline_used = headline
    row.ok = True
    row.has_citations = has_citations
    row.error_message = None
    row.response_json = payload
    row.fetched_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if cached is None:
        db.add(row)
    db.commit()

    if not has_citations:
        return WebciteBlock(
            available=True,
            status="no_data",
            message="No matching sources returned for this headline.",
            thread_id=thread_id,
            stance_summary=stance_summary,
            claim=claim or headline,
            citations=[],
        )

    return WebciteBlock(
        available=True,
        status="ok",
        message="WebCite source search only — not a fact-check verdict.",
        thread_id=thread_id,
        stance_summary=stance_summary,
        claim=claim or headline,
        citations=citations,
    )


def _block_from_cache_row(cached: WebciteStoryCache) -> WebciteBlock:
    if not cached.ok:
        return WebciteBlock(
            available=True,
            status="error",
            message=cached.error_message or "WebCite error.",
        )
    if not cached.response_json:
        return WebciteBlock(available=True, status="no_data", message="No cached WebCite data.")

    citations, stance_summary, claim, thread_id = _parse_search_payload(cached.response_json)
    if not cached.has_citations:
        return WebciteBlock(
            available=True,
            status="no_data",
            message="No matching sources returned for this headline.",
            thread_id=thread_id,
            stance_summary=stance_summary,
            claim=claim or cached.headline_used,
            citations=[],
        )
    return WebciteBlock(
        available=True,
        status="ok",
        message="WebCite source search only — not a fact-check verdict.",
        thread_id=thread_id,
        stance_summary=stance_summary,
        claim=claim or cached.headline_used,
        citations=citations,
    )


def load_webcite_block(db: Session, story: Story) -> WebciteBlock:
    """Return WebCite panel data: use cache if headline matches, else sync."""
    api_key = (settings.WEBCITE_API_KEY or "").strip()
    if not _key_usable(api_key):
        return WebciteBlock(
            available=False,
            status="skipped",
            message="WebCite API key not configured.",
        )

    headline = (story.headline or "").strip()
    cached = (
        db.query(WebciteStoryCache)
        .filter(WebciteStoryCache.story_id == story.id)
        .first()
    )
    if cached and cached.headline_used == headline:
        return _block_from_cache_row(cached)

    return sync_webcite_for_story(db, story)
