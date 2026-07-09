from content_pipeline.models import Candidate
from content_pipeline.discovery import source
from content_pipeline import queue, writing


def _cand(ref="r1"):
    return Candidate(source="reddit", source_ref=ref, title="T", url="u",
                     summary="s", engagement={"score": 100}, topic_tags=["ai"],
                     emotional_driver="opportunity", news_hook="now",
                     predicted_relevance=0.8)


def _accept_two(conn):
    """Ingest two candidates and accept both, older one decided first."""
    source.ingest(conn, [_cand("older"), _cand("newer")])
    rows = conn.execute(
        "SELECT id FROM candidates ORDER BY created_at ASC, id ASC"
    ).fetchall()
    older_id, newer_id = rows[0]["id"], rows[1]["id"]
    queue.decide(conn, older_id, "yes", today="2026-07-09")
    queue.decide(conn, newer_id, "yes", today="2026-07-09")
    return older_id, newer_id


def test_next_candidate_returns_older_of_two_accepted(conn):
    older_id, newer_id = _accept_two(conn)
    nxt = writing.next_candidate(conn)
    assert nxt is not None
    assert nxt["id"] == older_id


def test_next_candidate_returns_none_when_queue_empty(conn):
    assert writing.next_candidate(conn) is None


def test_start_article_creates_interviewing_row_and_skips_started_candidate(conn):
    older_id, newer_id = _accept_two(conn)

    article_id = writing.start_article(conn, older_id)
    assert isinstance(article_id, str) and article_id

    article = conn.execute(
        "SELECT * FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    assert article is not None
    assert article["candidate_id"] == older_id
    assert article["status"] == "interviewing"

    # exactly one article row created
    count = conn.execute("SELECT COUNT(*) AS c FROM articles").fetchone()["c"]
    assert count == 1

    # article_started event logged
    ev = conn.execute(
        "SELECT * FROM events WHERE kind = 'article_started'"
    ).fetchone()
    assert ev is not None
    assert ev["candidate_id"] == older_id
    assert ev["article_id"] == article_id

    # next_candidate now skips the started one and returns the newer candidate
    nxt = writing.next_candidate(conn)
    assert nxt is not None
    assert nxt["id"] == newer_id
