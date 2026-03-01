"""
Seed script — loads the AllSides outlet bias CSV into the outlets table.

The CSV (data/allsides_outlets.csv) has columns:
  name, domain, lean

Run once after alembic upgrade head:
  cd backend
  python scripts/seed_outlets.py
"""

import sys
import os
import csv
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.models import Outlet
from app.services.labeling import LEAN_META, UNKNOWN_META

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "allsides_outlets.csv",
)


def seed_outlets():
    if not os.path.exists(CSV_PATH):
        logger.error("CSV not found at %s", CSV_PATH)
        sys.exit(1)

    db = SessionLocal()
    inserted = 0
    updated = 0

    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("name", "").strip()
                domain = row.get("domain", "").strip() or None
                lean = row.get("lean", "").strip().lower().replace(" ", "_")

                if not name:
                    continue

                meta = LEAN_META.get(lean, UNKNOWN_META)

                outlet = db.query(Outlet).filter(Outlet.name == name).first()
                if outlet:
                    outlet.domain = domain
                    outlet.lean = lean
                    outlet.lean_display = meta["lean_display"]
                    outlet.why_label = meta["why_label"]
                    outlet.rating_method = meta.get("rating_method")
                    outlet.confidence = meta.get("confidence")
                    updated += 1
                else:
                    outlet = Outlet(
                        name=name,
                        domain=domain,
                        lean=lean,
                        lean_display=meta["lean_display"],
                        why_label=meta["why_label"],
                        rating_provider="AllSides",
                        rating_method=meta.get("rating_method"),
                        confidence=meta.get("confidence"),
                    )
                    db.add(outlet)
                    inserted += 1

        db.commit()
        logger.info("Seed complete — %d inserted, %d updated.", inserted, updated)
    except Exception as e:
        db.rollback()
        logger.error("Seed failed: %s", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_outlets()
