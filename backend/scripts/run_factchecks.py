"""
Pipeline script: fetch and cache fact checks for active stories missing rows.

Run after ingest + cluster_and_label in cron.

Usage:
  cd backend
  python scripts/run_factchecks.py
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.models import FactCheck, Story
from app.services.factchecks import sync_fact_checks_for_story

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    db = SessionLocal()
    try:
        active = db.query(Story).filter(Story.is_active).order_by(Story.id).all()
        processed = 0
        for story in active:
            has_row = (
                db.query(FactCheck).filter(FactCheck.story_id == story.id).first()
            )
            if has_row:
                logger.info("Story %s: already has fact_check row(s), skip.", story.id)
                continue
            logger.info("Story %s: fetching fact checks…", story.id)
            sync_fact_checks_for_story(db, story.id)
            processed += 1
        logger.info("Fact-check run complete (%d stories processed).", processed)
    except Exception as exc:
        logger.error("Fact-check pipeline failed: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
