"""
Story clustering using TF-IDF + cosine similarity on article headlines.

Algorithm:
1. Collect all un-clustered articles (story_id IS NULL).
2. Build a TF-IDF matrix over their titles.
3. Compute pairwise cosine similarity.
4. Group pairs where TF-IDF sim >= threshold OR entity overlap matches (union-find).
5. For each group:
   - If the group overlaps an existing story, extend that story.
   - Otherwise create a new Story with a representative headline.
6. Update article.story_id for all grouped articles.

Threshold tuned to merge cross-outlet coverage on the same event (manual spot-check as needed).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.models import Article, Story

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────
SIMILARITY_THRESHOLD = 0.15   # cosine sim >= this → same story (pair with entity OR branch)
MIN_CLUSTER_SIZE = 1          # single articles get their own story
MAX_FEATURES = 5000


def _representative_headline(articles: list[Article]) -> str:
    """Return the headline of the article with the most words (usually most descriptive)."""
    return max(articles, key=lambda a: len(a.title.split())).title


def _extract_entities(title: str) -> set[str]:
    """
    Very lightweight named-entity proxy: extract capitalized multi-word runs.
    A proper NER library (spaCy) is on the post-MVP roadmap.
    """
    tokens = title.split()
    entities = set()
    current = []
    for tok in tokens:
        cleaned = tok.strip(".,!?\"'()")
        if cleaned and cleaned[0].isupper() and len(cleaned) > 2:
            current.append(cleaned)
        else:
            if len(current) >= 1:
                entities.add(" ".join(current))
            current = []
    if current:
        entities.add(" ".join(current))
    return entities


def _entity_overlap(a1: Article, a2: Article) -> bool:
    """True if both articles share at least one named entity."""
    e1 = _extract_entities(a1.title)
    e2 = _extract_entities(a2.title)
    return bool(e1 & e2)


def cluster_articles(db: Session) -> dict:
    """
    Main entry point. Clusters un-assigned articles and assigns story_ids.
    Returns a summary dict: {"new_stories": int, "articles_assigned": int}.
    """
    # Fetch articles without a story assignment
    unclustered: list[Article] = (
        db.query(Article)
        .filter(Article.story_id.is_(None))
        .order_by(Article.published_at.desc())
        .all()
    )

    if not unclustered:
        logger.info("No unclustered articles found.")
        return {"new_stories": 0, "articles_assigned": 0}

    logger.info("Clustering %d unclustered articles...", len(unclustered))

    titles = [a.title for a in unclustered]

    # Build TF-IDF matrix
    vectorizer = TfidfVectorizer(
        max_features=MAX_FEATURES,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(titles)
    except ValueError:
        logger.warning("TF-IDF fit failed (too few documents?).")
        return {"new_stories": 0, "articles_assigned": 0}

    sim_matrix = cosine_similarity(tfidf_matrix)

    # Union-Find for grouping
    parent = list(range(len(unclustered)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i in range(len(unclustered)):
        for j in range(i + 1, len(unclustered)):
            if sim_matrix[i][j] >= SIMILARITY_THRESHOLD:
                union(i, j)
            elif _entity_overlap(unclustered[i], unclustered[j]):
                union(i, j)

    # Build groups
    groups: dict[int, list[int]] = {}
    for idx in range(len(unclustered)):
        root = find(idx)
        groups.setdefault(root, []).append(idx)

    new_stories = 0
    articles_assigned = 0

    for root, indices in groups.items():
        articles_in_group = [unclustered[i] for i in indices]

        # Check if any article in the group already belongs to an existing story
        existing_story: Optional[Story] = None
        for a in articles_in_group:
            # Look for a very similar article already assigned
            similar_assigned = (
                db.query(Article)
                .filter(
                    Article.story_id.isnot(None),
                    Article.title == a.title,
                )
                .first()
            )
            if similar_assigned and similar_assigned.story_id:
                existing_story = db.query(Story).get(similar_assigned.story_id)
                break

        if existing_story:
            story = existing_story
        else:
            story = Story(
                headline=_representative_headline(articles_in_group),
                first_seen_at=min(
                    (a.published_at or a.fetched_at) for a in articles_in_group
                ),
                last_updated_at=datetime.utcnow(),
                article_count=0,
            )
            db.add(story)
            db.flush()  # get story.id
            new_stories += 1

        for a in articles_in_group:
            a.story_id = story.id
            articles_assigned += 1

        # Flush so _refresh_story_meta can query the newly assigned story_ids
        # (session uses autoflush=False, so we must flush explicitly).
        db.flush()
        _refresh_story_meta(db, story)

    db.commit()
    logger.info(
        "Clustering complete: %d new stories, %d articles assigned.",
        new_stories,
        articles_assigned,
    )
    return {"new_stories": new_stories, "articles_assigned": articles_assigned}


def _refresh_story_meta(db: Session, story: Story) -> None:
    """Update article_count and lean_categories_present on a story."""
    articles = db.query(Article).filter(Article.story_id == story.id).all()
    story.article_count = len(articles)
    story.last_updated_at = datetime.utcnow()

    leans = set()
    for a in articles:
        if a.outlet and a.outlet.lean_display:
            leans.add(a.outlet.lean_display.lower())
    story.lean_categories_present = ",".join(sorted(leans)) if leans else None
