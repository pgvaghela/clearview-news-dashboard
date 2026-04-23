"""
Article ingestion script — fetches articles from NewsAPI and RSS feeds.

Outlets covered (13 total, spanning all five lean categories):
  Center:     BBC News, Reuters, Associated Press
  Lean Left:  NPR, The Guardian, CNN, ABC News
  Left:       MSNBC
  Lean Right: The Wall Street Journal, The New York Post
  Right:      Fox News, Breitbart

Run manually: python scripts/ingest.py
Will be scheduled via cron every 60 minutes (target: Sprint 1 completion 03/27).

Usage:
  cd backend
  python scripts/ingest.py
"""

import sys
import os
import logging
from datetime import datetime

# Allow imports from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.models import Article

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── NewsAPI sources to fetch ───────────────────────────────────────────────

NEWSAPI_SOURCES = [
    # Center
    "bbc-news",
    "reuters",
    "associated-press",
    # Lean Left
    "npr",
    "the-guardian-uk",
    "cnn",
    "abc-news",
    # Left
    "msnbc",
    # Lean Right
    "the-wall-street-journal",
    "the-new-york-post",
    # Right
    "fox-news",
    "breitbart-news",
]

NEWSAPI_BASE = "https://newsapi.org/v2/top-headlines"
ARTICLES_PER_SOURCE = 20


def fetch_newsapi(source: str, api_key: str) -> list[dict]:
    """Fetch top headlines for a single NewsAPI source."""
    try:
        resp = httpx.get(
            NEWSAPI_BASE,
            params={"sources": source, "pageSize": ARTICLES_PER_SOURCE, "apiKey": api_key},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            logger.warning("NewsAPI error for %s: %s", source, data.get("message"))
            return []
        return data.get("articles", [])
    except Exception as e:
        logger.error("Failed to fetch %s: %s", source, e)
        return []


def parse_newsapi_article(raw: dict, source_name: str) -> dict | None:
    """Convert a raw NewsAPI article dict into our Article field dict."""
    url = raw.get("url", "").strip()
    title = raw.get("title", "").strip()
    if not url or not title or url == "https://removed.com":
        return None

    published_str = raw.get("publishedAt")
    published_at = None
    if published_str:
        try:
            published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    return {
        "title": title,
        "url": url,
        "description": (raw.get("description") or "")[:1000],
        "published_at": published_at,
        "outlet_name": (
            raw.get("source", {}).get("name") or source_name
        ).strip(),
    }


def upsert_article(db, fields: dict) -> bool:
    """Insert article if URL not already in DB. Returns True if inserted."""
    existing = db.query(Article).filter(Article.url == fields["url"]).first()
    if existing:
        return False
    article = Article(**fields)
    db.add(article)
    try:
        db.flush()
        return True
    except IntegrityError:
        db.rollback()
        return False


def run_ingestion():
    api_key = settings.NEWSAPI_KEY
    if not api_key:
        logger.error("NEWSAPI_KEY is not set in .env — aborting ingestion.")
        sys.exit(1)

    db = SessionLocal()
    total_new = 0
    total_skipped = 0

    try:
        for source in NEWSAPI_SOURCES:
            logger.info("Fetching: %s", source)
            raw_articles = fetch_newsapi(source, api_key)

            for raw in raw_articles:
                fields = parse_newsapi_article(raw, source)
                if not fields:
                    continue
                inserted = upsert_article(db, fields)
                if inserted:
                    total_new += 1
                else:
                    total_skipped += 1

        db.commit()
        logger.info(
            "Ingestion complete — %d new articles, %d duplicates skipped.",
            total_new,
            total_skipped,
        )
    except Exception as e:
        db.rollback()
        logger.error("Ingestion failed: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()
