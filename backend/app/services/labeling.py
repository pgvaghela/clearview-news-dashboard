"""
Lean labeling service — attaches AllSides outlet bias data to articles.

For each article, we attempt to resolve its outlet by:
1. Exact domain match (e.g. "foxnews.com" → Fox News)
2. Partial name match (e.g. "Fox News" in title → Fox News outlet)

If resolved, the article's outlet_id is set and the outlet's lean fields
are available on article.outlet for API responses.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.models import Article, Outlet

logger = logging.getLogger(__name__)

# Human-readable display labels and explanations keyed by AllSides lean value.
LEAN_META: dict[str, dict] = {
    "left": {
        "lean_display": "Left",
        "why_label": (
            "This outlet is rated Left by AllSides based on blind surveys of thousands of "
            "Americans who read the outlet's coverage without knowing the source. "
            "Readers consistently placed this outlet on the left of the political spectrum."
        ),
        "rating_method": "Multi-partisan panel review + blind surveys",
        "confidence": "Community consensus",
    },
    "lean_left": {
        "lean_display": "Lean Left",
        "why_label": (
            "AllSides rates this outlet as Lean Left. Coverage tends to align somewhat "
            "with liberal or progressive viewpoints, though less strongly than outlets "
            "rated simply 'Left'. Rating is based on blind reader surveys and editorial review."
        ),
        "rating_method": "Multi-partisan panel review + blind surveys",
        "confidence": "Community consensus",
    },
    "center": {
        "lean_display": "Center",
        "why_label": (
            "AllSides rates this outlet as Center, meaning coverage does not consistently "
            "favor either liberal or conservative viewpoints. "
            "This rating comes from blind surveys and an editorial review by a "
            "multi-partisan AllSides panel."
        ),
        "rating_method": "Multi-partisan panel review + blind surveys",
        "confidence": "Community consensus",
    },
    "lean_right": {
        "lean_display": "Lean Right",
        "why_label": (
            "AllSides rates this outlet as Lean Right. Coverage tends to align somewhat "
            "with conservative viewpoints, though less strongly than outlets rated simply 'Right'. "
            "Rating is based on blind reader surveys and editorial review."
        ),
        "rating_method": "Multi-partisan panel review + blind surveys",
        "confidence": "Community consensus",
    },
    "right": {
        "lean_display": "Right",
        "why_label": (
            "This outlet is rated Right by AllSides based on blind surveys of thousands of "
            "Americans who read the outlet's coverage without knowing the source. "
            "Readers consistently placed this outlet on the right of the political spectrum."
        ),
        "rating_method": "Multi-partisan panel review + blind surveys",
        "confidence": "Community consensus",
    },
}

UNKNOWN_META = {
    "lean_display": "Unknown",
    "why_label": "This outlet has not yet been rated by AllSides. No lean label is available.",
    "rating_method": None,
    "confidence": None,
}


def _extract_domain(url: str) -> str | None:
    """Return the bare domain (e.g. 'foxnews.com') from a URL."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        # Strip www.
        host = re.sub(r"^www\.", "", host)
        return host if host else None
    except Exception:
        return None


def resolve_outlet_for_article(article: Article, db: Session) -> Outlet | None:
    """
    Try to find an Outlet record that matches the article's source.
    Returns the Outlet if found, None otherwise.
    """
    # 1. Domain match
    if article.url:
        domain = _extract_domain(article.url)
        if domain:
            outlet = db.query(Outlet).filter(Outlet.domain == domain).first()
            if outlet:
                return outlet

    # 2. Name match (case-insensitive substring)
    if article.outlet_name:
        name_lower = article.outlet_name.lower().strip()
        outlets = db.query(Outlet).all()
        for o in outlets:
            if o.name.lower() == name_lower:
                return o
        # Partial match fallback
        for o in outlets:
            if name_lower in o.name.lower() or o.name.lower() in name_lower:
                return o

    return None


def label_articles(db: Session) -> dict:
    """
    For all articles without an outlet_id, attempt to resolve and attach an outlet.
    Returns summary: {"labeled": int, "unresolved": int}.
    """
    unlabeled = (
        db.query(Article).filter(Article.outlet_id.is_(None)).all()
    )

    labeled = 0
    unresolved = 0

    for article in unlabeled:
        outlet = resolve_outlet_for_article(article, db)
        if outlet:
            article.outlet_id = outlet.id
            labeled += 1
        else:
            unresolved += 1

    db.commit()
    logger.info("Labeling: %d labeled, %d unresolved.", labeled, unresolved)
    return {"labeled": labeled, "unresolved": unresolved}


def get_lean_info_for_outlet(outlet: Outlet | None) -> dict:
    """
    Return the lean display label, why_label, method, and confidence
    for a given Outlet (or the unknown defaults if None).
    """
    if not outlet or not outlet.lean:
        return UNKNOWN_META
    return LEAN_META.get(outlet.lean, UNKNOWN_META)
