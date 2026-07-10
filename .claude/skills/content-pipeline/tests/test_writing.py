import json

from content_pipeline.models import Candidate
from content_pipeline.discovery import source
from content_pipeline import queue, writing, events, brief as brief_mod


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


def _start_article(conn):
    """Ingest+decide+start helper: one accepted candidate, article started."""
    older_id, _newer_id = _accept_two(conn)
    article_id = writing.start_article(conn, older_id)
    return article_id, older_id


def test_record_answer_logs_choice(conn):
    aid, cid = _start_article(conn)
    writing.record_answer(conn, aid, "Q", "skip", None, {"recommended": "a", "alternate": "b"})
    ev = conn.execute("SELECT * FROM events WHERE kind='interview_choice'").fetchone()
    assert json.loads(ev["payload_json"])["chosen"] == "skip"


def test_save_draft_stores_text_sets_reviewing_and_logs(conn):
    aid, cid = _start_article(conn)

    writing.save_draft(conn, aid, "Here is the full draft body.")

    row = conn.execute(
        "SELECT draft_text, status FROM articles WHERE id=?", (aid,)
    ).fetchone()
    assert row["draft_text"] == "Here is the full draft body."
    assert row["status"] == "reviewing"
    kinds = [e["kind"] for e in events.recent(conn)]
    assert "draft_generated" in kinds


def _draft_article(conn, text="First draft text."):
    aid, cid = _start_article(conn)
    writing.save_draft(conn, aid, text)
    return aid


def test_record_edit_round_computes_size_and_increments_round(conn):
    aid = _draft_article(conn, text="abc")

    round1 = writing.record_edit_round(conn, aid, "make it punchier", "abcdef")
    assert round1 == 1

    row1 = conn.execute(
        "SELECT * FROM edit_rounds WHERE article_id = ? AND round = 1", (aid,)
    ).fetchone()
    assert row1 is not None
    assert row1["operator_feedback"] == "make it punchier"
    assert row1["edit_size"] == 3  # "abc" -> "abcdef", 3 chars added

    article = conn.execute("SELECT * FROM articles WHERE id = ?", (aid,)).fetchone()
    assert article["draft_text"] == "abcdef"

    ev = conn.execute(
        "SELECT * FROM events WHERE kind = 'edit_round'"
    ).fetchone()
    assert ev is not None
    payload = json.loads(ev["payload_json"])
    assert payload["round"] == 1
    assert payload["operator_feedback"] == "make it punchier"
    assert payload["edit_size"] == 3

    round2 = writing.record_edit_round(conn, aid, "tighten intro", "abcdefgh")
    assert round2 == 2

    row2 = conn.execute(
        "SELECT * FROM edit_rounds WHERE article_id = ? AND round = 2", (aid,)
    ).fetchone()
    assert row2 is not None
    assert row2["edit_size"] == 2  # "abcdef" -> "abcdefgh"

    article2 = conn.execute("SELECT * FROM articles WHERE id = ?", (aid,)).fetchone()
    assert article2["draft_text"] == "abcdefgh"


def test_record_edit_round_size_not_blind_to_same_length_rewrite(conn):
    # A same-length full-content rewrite (500 'a's -> 500 'b's) has a length
    # delta of 0. The old abs(len(new) - len(prior)) implementation would
    # have recorded edit_size == 0 here, silently hiding a heavy rewrite
    # from the downstream edit-effort health metric. The real char-diff
    # must register this as a large, non-zero edit.
    prior_text = "a" * 500
    aid = _draft_article(conn, text=prior_text)

    new_text = "b" * 500
    writing.record_edit_round(conn, aid, "full rewrite", new_text)

    row = conn.execute(
        "SELECT * FROM edit_rounds WHERE article_id = ? AND round = 1", (aid,)
    ).fetchone()
    assert row is not None
    # length delta would be 0; the real diff must be close to the full 500
    # characters changed (SequenceMatcher may find a few incidental matches).
    assert row["edit_size"] > 400


def test_approve_sets_approved_and_logs_event_without_synthesis(conn):
    aid = _draft_article(conn)

    writing.approve(conn, aid, "Final approved text.")

    article = conn.execute("SELECT * FROM articles WHERE id = ?", (aid,)).fetchone()
    assert article["status"] == "approved"
    assert article["final_text"] == "Final approved text."
    assert article["approved_at"] is not None

    ev = conn.execute(
        "SELECT * FROM events WHERE kind = 'article_approved'"
    ).fetchone()
    assert ev is not None
    assert ev["article_id"] == aid

    # approve no longer triggers synthesis: no synthesis checkpoint written.
    syn = conn.execute(
        "SELECT 1 FROM synthesis_runs WHERE artifact='style'"
    ).fetchone()
    assert syn is None


def test_resumable_finds_interviewing_article(conn):
    assert writing.resumable(conn) is None

    aid, cid = _start_article(conn)

    resumed = writing.resumable(conn)
    assert resumed is not None
    assert resumed["id"] == aid
    assert resumed["status"] == "interviewing"


def test_resumable_finds_reviewing_article(conn):
    aid = _draft_article(conn)

    resumed = writing.resumable(conn)
    assert resumed is not None
    assert resumed["id"] == aid
    assert resumed["status"] == "reviewing"


def test_resumable_ignores_approved_article(conn):
    aid = _draft_article(conn)
    writing.approve(conn, aid, "Final text.")

    assert writing.resumable(conn) is None


def test_save_draft_appends_version_one_with_inputs(conn, monkeypatch):
    monkeypatch.setattr("content_pipeline.config.brand_context", lambda: "SEEDVOICE")
    aid, cid = _start_article(conn)
    brief_mod.save_brief(conn, aid, {"topic": "t", "angle": "a", "key_points": ["k"]})

    writing.save_draft(conn, aid, "Draft body one.")

    v = conn.execute(
        "SELECT * FROM draft_versions WHERE article_id=? ORDER BY version", (aid,)
    ).fetchall()
    assert len(v) == 1
    assert v[0]["version"] == 1
    assert v[0]["text"] == "Draft body one."
    assert v[0]["brief_id"] is not None
    assert "SEEDVOICE" in v[0]["voice_snapshot"]


def test_regenerate_via_second_save_draft_adds_version_two(conn):
    aid, cid = _start_article(conn)
    writing.save_draft(conn, aid, "first generation")
    writing.save_draft(conn, aid, "regenerated from a changed brief")

    versions = conn.execute(
        "SELECT version, text FROM draft_versions WHERE article_id=? ORDER BY version", (aid,)
    ).fetchall()
    assert [r["version"] for r in versions] == [1, 2]
    assert versions[1]["text"] == "regenerated from a changed brief"


def test_edit_round_also_appends_a_draft_version(conn):
    aid = _draft_article(conn, text="v1 body")  # save_draft -> version 1
    writing.record_edit_round(conn, aid, "tighten it", "v1 body tighter")

    versions = conn.execute(
        "SELECT version, text FROM draft_versions WHERE article_id=? ORDER BY version", (aid,)
    ).fetchall()
    assert [r["version"] for r in versions] == [1, 2]
    assert versions[1]["text"] == "v1 body tighter"
