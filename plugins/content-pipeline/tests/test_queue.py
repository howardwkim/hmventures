from content_pipeline.models import Candidate
from content_pipeline.discovery import source

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
