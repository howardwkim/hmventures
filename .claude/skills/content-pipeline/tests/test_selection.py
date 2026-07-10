import pytest

from content_pipeline.learning import selection
from content_pipeline.models import Candidate
from content_pipeline.discovery import source
from content_pipeline import queue


def _cand(ref, title, predicted_relevance=0.8):
    return Candidate(
        source="reddit",
        source_ref=ref,
        title=title,
        url="u",
        summary="s",
        engagement={"score": 100},
        topic_tags=["ai"],
        emotional_driver="opportunity",
        news_hook="now",
        predicted_relevance=predicted_relevance,
    )


def _decide(conn, ref, title, outcome, predicted_relevance=0.8, today="2026-07-09"):
    source.ingest(conn, [_cand(ref, title, predicted_relevance)])
    cid = conn.execute(
        "SELECT id FROM candidates WHERE source_ref = ?", (ref,)
    ).fetchone()["id"]
    queue.decide(conn, cid, outcome, today=today)
    return cid


def test_selection_context_renders_title_outcome_predicted_relevance(conn):
    _decide(conn, "a", "Article A", "yes", predicted_relevance=0.9)

    context = selection.selection_context(conn)

    assert "Article A" in context
    assert "yes" in context
    assert "0.9" in context


def test_selection_context_respects_limit_and_newest_last(conn):
    for i in range(5):
        _decide(conn, f"r{i}", f"Article {i}", "yes")

    context = selection.selection_context(conn, limit=3)
    lines = [line for line in context.splitlines() if line.strip()]

    assert len(lines) <= 3
    # newest-last: Article 4 (most recent decision) should appear after
    # Article 2 (an earlier decision still within the limit window)
    assert context.index("Article 4") > context.index("Article 2")
    # oldest decisions fall outside the limit window
    assert "Article 0" not in context
    assert "Article 1" not in context


def test_selection_context_empty_state_does_not_error(conn):
    context = selection.selection_context(conn)
    assert context == "" or isinstance(context, str)


def test_calibration_computes_mean_abs_error(conn):
    _decide(conn, "a", "Article A", "no", predicted_relevance=0.9)

    result = selection.calibration(conn)

    assert result["n"] == 1
    assert result["mean_abs_error"] == pytest.approx(0.9)


def test_calibration_excludes_snooze_outcomes(conn):
    _decide(conn, "a", "Article A", "yes", predicted_relevance=1.0)  # error 0
    _decide(conn, "b", "Article B", "snooze", predicted_relevance=0.5)  # excluded

    result = selection.calibration(conn)

    assert result["n"] == 1
    assert result["mean_abs_error"] == pytest.approx(0.0)


def test_calibration_over_accept_rate(conn):
    # predicted high (>=0.5), actually rejected -> over-accept
    _decide(conn, "a", "Article A", "no", predicted_relevance=0.9)
    # predicted high, actually accepted -> not an over-accept
    _decide(conn, "b", "Article B", "yes", predicted_relevance=0.9)

    result = selection.calibration(conn)

    assert result["n"] == 2
    assert result["over_accept_rate"] == pytest.approx(0.5)


def test_calibration_empty_state_does_not_error(conn):
    result = selection.calibration(conn)
    assert result["n"] == 0
    assert result["mean_abs_error"] == 0
    assert result["over_accept_rate"] == 0
