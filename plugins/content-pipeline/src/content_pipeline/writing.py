import uuid
from datetime import datetime, timezone

from content_pipeline import events


def _now():
    return datetime.now(timezone.utc).isoformat()


def next_candidate(conn):
    """Oldest accepted candidate (status 'yes') that doesn't have an article
    yet, FIFO by decided_at. Returns None when the queue is empty."""
    return conn.execute(
        """SELECT * FROM candidates
           WHERE status = 'yes'
             AND id NOT IN (SELECT candidate_id FROM articles)
           ORDER BY decided_at ASC"""
    ).fetchone()


def start_article(conn, candidate_id) -> str:
    """Create an articles row (status 'interviewing') for candidate_id,
    append an 'article_started' event, and return the new article id."""
    article_id = uuid.uuid4().hex
    conn.execute(
        """INSERT INTO articles (id, candidate_id, status, created_at)
           VALUES (?, ?, 'interviewing', ?)""",
        (article_id, candidate_id, _now()),
    )
    conn.commit()

    events.append(
        conn,
        "article_started",
        {"candidate_id": candidate_id},
        article_id=article_id,
        candidate_id=candidate_id,
    )

    return article_id
