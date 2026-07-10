import json
import pytest
from content_pipeline import brief, events, writing
from content_pipeline.models import Candidate
from content_pipeline.discovery import source
from content_pipeline import queue


def _brief(topic="Pricing", angle="Raise prices, lose the wrong customers"):
    return {
        "title": "The customers you want to lose",
        "topic": topic,
        "angle": angle,
        "key_points": ["cheap price attracts high-support churn", "revenue rose after the hike"],
        "source_snippet": "I raised it to $39. Lost about 40 users.",
        "constraints": ["do not name the product"],
    }


def _cand(ref="r1"):
    return Candidate(
        source="reddit", source_ref=ref, title="T", url="u",
        summary="s", engagement={"score": 100}, topic_tags=["ai"],
        emotional_driver="opportunity", news_hook="now",
        predicted_relevance=0.8)


def _create_article(conn):
    """Create an article and return its ID."""
    c = _cand(ref="test_ref")
    source.ingest(conn, [c])
    cand_id = conn.execute(
        "SELECT id FROM candidates ORDER BY created_at DESC LIMIT 1"
    ).fetchone()["id"]
    queue.decide(conn, cand_id, "yes", today="2026-07-09")
    article_id = writing.start_article(conn, cand_id)
    return article_id


def test_save_brief_returns_incrementing_versions(conn):
    article_id = _create_article(conn)
    assert brief.save_brief(conn, article_id, _brief()) == 1
    assert brief.save_brief(conn, article_id, _brief(angle="revised angle")) == 2


def test_current_brief_returns_latest_with_id_and_version(conn):
    article_id = _create_article(conn)
    brief.save_brief(conn, article_id, _brief(angle="first"))
    brief.save_brief(conn, article_id, _brief(angle="second"))
    cur = brief.current_brief(conn, article_id)
    assert cur["version"] == 2
    assert cur["angle"] == "second"
    assert isinstance(cur["id"], int)


def test_current_brief_none_when_absent(conn):
    assert brief.current_brief(conn, "nope") is None


def test_save_brief_logs_event(conn):
    article_id = _create_article(conn)
    brief.save_brief(conn, article_id, _brief())
    kinds = [e["kind"] for e in events.recent(conn)]
    assert "brief_saved" in kinds


def test_save_brief_rejects_missing_required_fields(conn):
    article_id = _create_article(conn)
    with pytest.raises(ValueError):
        brief.save_brief(conn, article_id, {"topic": "x"})  # no angle, no key_points
