"""
Pipeline script: run clustering then lean labeling in sequence.

Run manually: python scripts/cluster_and_label.py
Will be scheduled after ingest.py in the cron job.

Usage:
  cd backend
  python scripts/cluster_and_label.py
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.services.clustering import cluster_articles
from app.services.labeling import label_articles
from app.services.summarize import generate_summaries

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline():
    db = SessionLocal()
    try:
        logger.info("=== Step 1: Clustering ===")
        cluster_result = cluster_articles(db)
        logger.info("Clustering result: %s", cluster_result)

        logger.info("=== Step 2: Lean Labeling ===")
        label_result = label_articles(db)
        logger.info("Labeling result: %s", label_result)

        logger.info("=== Step 3: Story Summaries ===")
        summary_result = generate_summaries(db)
        logger.info("Summary result: %s", summary_result)

        logger.info("=== Pipeline complete ===")
    except Exception as e:
        logger.error("Pipeline failed: %s", e)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_pipeline()
