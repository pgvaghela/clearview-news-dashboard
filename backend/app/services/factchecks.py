"""
Fact-check lookup: Google Fact Check Tools API with Claude AI fallback.

When Google returns no indexed results (common for breaking news), Claude
analyzes the story's key claims and returns a structured assessment.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Article, FactCheck, Story

logger = logging.getLogger(__name__)

FACTCHECK_SEARCH_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "in", "on", "at", "to", "for", "of", "and", "or",
    "but", "with", "from", "that", "this", "it", "its", "are", "was", "were",
    "be", "been", "have", "has", "had", "will", "would", "could", "should",
    "after", "before", "over", "under", "as", "by", "up", "out", "about",
    "into", "than", "not", "no", "so", "if", "do", "does", "did", "get",
    "live", "new", "says", "say",
})

_PLACEHOLDER_GOOGLE_KEYS = frozenset({"your_google_factcheck_api_key_here"})
_placeholder_key_logged = False


def _google_factcheck_key_usable(key: str) -> bool:
    k = (key or "").strip()
    return bool(k) and k not in _PLACEHOLDER_GOOGLE_KEYS


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
    tokens = [t.strip(".,;:!?()[]\"'s") for t in headline.split()]
    significant = [t for t in tokens if t and t.lower() not in _STOP_WORDS and len(t) > 2]
    return " ".join(significant[:n])


def _call_google_claims_search(query: str, api_key: str) -> dict:
    resp = httpx.get(
        FACTCHECK_SEARCH_URL,
        params={"query": query, "key": api_key, "languageCode": "en", "pageSize": 10},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def _ai_fact_check(story: Story, db: Session) -> FactCheck | None:
    """Call Claude to fact-check a story when Google has no indexed results."""
    api_key = (settings.ANTHROPIC_API_KEY or "").strip()
    if not api_key or api_key == "your_anthropic_api_key_here":
        logger.info("Story %s: ANTHROPIC_API_KEY not set, skipping AI fact-check.", story.id)
        return None

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed.")
        return None

    articles = (
        db.query(Article)
        .filter(Article.story_id == story.id)
        .limit(6)
        .all()
    )
    article_snippets = "\n".join(
        f"- [{a.outlet_name}] {a.title}: {(a.description or '')[:200]}"
        for a in articles
    )

    prompt = f"""You are a fact-checker. Analyze the following news story and its coverage.

Story headline: {story.headline}

Coverage from multiple outlets:
{article_snippets}

Respond with ONLY valid JSON in this exact format:
{{
  "verdict": "one of: Accurate | Mostly Accurate | Needs Context | Mixed | Unverified | Misleading",
  "summary": "2-3 sentence fact-check summary explaining the verdict",
  "key_claims": ["claim 1", "claim 2", "claim 3"],
  "caveats": "any important missing context or caveats (1 sentence, or null)"
}}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        parsed = json.loads(raw)

        verdict = parsed.get("verdict", "Unverified")
        summary = parsed.get("summary", "")
        key_claims = parsed.get("key_claims", [])
        caveats = parsed.get("caveats") or ""

        claim_text = summary
        if key_claims:
            claim_text += "\n\nKey claims: " + "; ".join(key_claims)
        if caveats:
            claim_text += f"\n\nCaveats: {caveats}"

        logger.info("Story %s: Claude verdict — %s", story.id, verdict)
        return FactCheck(
            story_id=story.id,
            claim_text=claim_text,
            claim_reviewed=story.headline,
            rating=verdict,
            publisher="Claude AI (Anthropic)",
            review_url=None,
            review_date=None,
            no_match=False,
            is_ai_generated=True,
        )
    except json.JSONDecodeError:
        logger.warning("Story %s: Claude returned non-JSON response.", story.id)
        return None
    except Exception as exc:
        logger.warning("Story %s: Claude AI fact-check failed: %s", story.id, exc)
        return None


def sync_fact_checks_for_story(db: Session, story_id: int) -> None:
    """
    Fetch fact checks for a story. Tries Google first; falls back to Claude AI
    when Google has no indexed results.
    """
    has_positive = (
        db.query(FactCheck)
        .filter(FactCheck.story_id == story_id, FactCheck.no_match.is_(False))
        .first()
    )
    if has_positive is not None:
        logger.info("Story %s: fact checks already cached, skipping.", story_id)
        return

    removed = (
        db.query(FactCheck)
        .filter(FactCheck.story_id == story_id, FactCheck.no_match.is_(True))
        .delete(synchronize_session=False)
    )
    if removed:
        db.commit()

    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        logger.warning("Story %s not found.", story_id)
        return

    # ── Step 1: Try Google ──
    google_rows: list[FactCheck] = []
    api_key = (settings.GOOGLE_FACTCHECK_API_KEY or "").strip()
    global _placeholder_key_logged

    if _google_factcheck_key_usable(api_key):
        headline = story.headline or ""
        queries = [headline, _keyword_query(headline)]
        claims: list = []

        for query in queries:
            if not query:
                continue
            try:
                logger.info("Story %s: querying Google Fact Check API (query: %s…)", story_id, query[:80])
                payload = _call_google_claims_search(query, api_key)
            except httpx.HTTPStatusError as exc:
                logger.warning("Story %s: Google API HTTP %s", story_id, exc.response.status_code)
                break
            except Exception as exc:
                logger.warning("Story %s: Google API error: %s", story_id, exc)
                break

            claims = payload.get("claims") or []
            if claims:
                break

        for claim in claims:
            claim_text = claim.get("text")
            claim_date_str = claim.get("claimDate")
            for review in claim.get("claimReview") or []:
                publisher = (review.get("publisher") or {}).get("name")
                textual_rating = review.get("textualRating")
                url = review.get("url")
                title = review.get("title")
                review_date = _parse_rfc3339(review.get("reviewDate")) or _parse_rfc3339(claim_date_str)
                google_rows.append(FactCheck(
                    story_id=story_id,
                    claim_text=claim_text,
                    claim_reviewed=title or claim_text,
                    rating=textual_rating,
                    publisher=publisher,
                    review_url=url,
                    review_date=review_date,
                    no_match=False,
                    is_ai_generated=False,
                ))
    else:
        if not _placeholder_key_logged:
            logger.warning("GOOGLE_FACTCHECK_API_KEY not set. Skipping Google; using AI fallback.")
            _placeholder_key_logged = True

    if google_rows:
        for row in google_rows:
            db.add(row)
        db.commit()
        logger.info("Story %s: saved %d Google fact-check row(s).", story_id, len(google_rows))
        return

    # ── Step 2: Claude AI fallback ──
    logger.info("Story %s: no Google results, trying Claude AI fallback…", story_id)
    ai_row = _ai_fact_check(story, db)
    if ai_row:
        db.add(ai_row)
        db.commit()
        logger.info("Story %s: saved Claude AI fact-check.", story_id)
    else:
        db.add(FactCheck(story_id=story_id, no_match=True))
        db.commit()
        logger.info("Story %s: no fact-check results from any source.", story_id)
