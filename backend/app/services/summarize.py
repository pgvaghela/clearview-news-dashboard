"""
Story summary generation via Claude Haiku.

Runs after clustering. Skips stories that already have a summary.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Article, Story

logger = logging.getLogger(__name__)


def _ai_summary(headline: str, snippets: str) -> str | None:
    api_key = (settings.ANTHROPIC_API_KEY or "").strip()
    if not api_key or api_key == "your_anthropic_api_key_here":
        return None

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed.")
        return None

    prompt = f"""Write a single sentence (max 25 words) summarizing this news story based on the headline and article snippets below. Return only the sentence, no quotes, no punctuation at the end beyond a period.

Headline: {headline}

Coverage:
{snippets}"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip().strip('"')
    except Exception as exc:
        logger.warning("Summary generation failed: %s", exc)
        return None


def generate_summaries(db: Session) -> dict:
    stories = (
        db.query(Story)
        .filter(Story.summary.is_(None), Story.is_active.is_(True))
        .all()
    )

    if not stories:
        logger.info("All stories already have summaries.")
        return {"generated": 0, "skipped": 0}

    generated = 0
    skipped = 0

    for story in stories:
        articles = (
            db.query(Article)
            .filter(Article.story_id == story.id)
            .limit(5)
            .all()
        )
        snippets = "\n".join(
            f"- [{a.outlet_name}] {(a.description or a.title or '')[:150]}"
            for a in articles
        )

        summary = _ai_summary(story.headline, snippets)
        if summary:
            story.summary = summary
            generated += 1
            logger.info("Story %s: summary generated.", story.id)
        else:
            skipped += 1

    db.commit()
    logger.info("Summaries: %d generated, %d skipped.", generated, skipped)
    return {"generated": generated, "skipped": skipped}
