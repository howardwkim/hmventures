from content_pipeline.models import Candidate
from content_pipeline.discovery import source
from content_pipeline import queue

def _cand(ref="r1"):
    return Candidate(source="reddit", source_ref=ref, title="T", url="u",
                     summary="s", engagement={"score":100}, topic_tags=["ai"],
                     emotional_driver="opportunity", news_hook="now",
                     predicted_relevance=0.8)

def test_ingest_dedupes_on_source_ref(conn):
    assert source.ingest(conn, [_cand("a"), _cand("b")]) == 2
    assert source.ingest(conn, [_cand("a")]) == 0  # already present
    rows = conn.execute("SELECT status FROM candidates").fetchall()
    assert all(r["status"] == "pending" for r in rows) and len(rows) == 2

def test_snooze_hides_until_next_day(conn):
    source.ingest(conn, [_cand("a")])
    cid = conn.execute("SELECT id FROM candidates").fetchone()["id"]
    queue.decide(conn, cid, "snooze", today="2026-07-09")
    assert queue.list_review(conn, today="2026-07-09") == []       # hidden same day
    assert len(queue.list_review(conn, today="2026-07-10")) == 1    # back next day

def test_decision_logs_event_with_prediction(conn):
    source.ingest(conn, [_cand("a")])
    cid = conn.execute("SELECT id FROM candidates").fetchone()["id"]
    queue.decide(conn, cid, "yes", today="2026-07-09")
    ev = conn.execute("SELECT * FROM events WHERE kind='decision'").fetchone()
    import json; p = json.loads(ev["payload_json"])
    assert p["outcome"] == "yes" and p["predicted_relevance"] == 0.8
