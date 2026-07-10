import json

import pytest

from content_pipeline import cli, db, writing
from content_pipeline.discovery import source
from content_pipeline.models import Candidate
from content_pipeline import queue


def _run(capsys, argv):
    cli.main(argv)
    out = capsys.readouterr().out
    return json.loads(out)


def test_missing_db_config_errors_loudly_instead_of_defaulting(monkeypatch, capsys):
    monkeypatch.delenv("CONTENT_PIPELINE_DB", raising=False)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(["status"])

    assert "CONTENT_PIPELINE_DB" in str(excinfo.value)


def test_status_on_empty_db_prints_valid_json_with_zeroed_queues(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")

    result = _run(capsys, ["--db", db_path, "status"])

    assert result["review_queue_count"] == 0
    assert result["next_article_available"] is False
    assert result["calibration"]["n"] == 0
    assert result["nudge"] is None
    assert result["synthesis_pending"] is False


def test_status_runs_on_already_migrated_db(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    conn = db.connect(db_path)
    db.init_schema(conn)
    conn.close()

    result = _run(capsys, ["--db", db_path, "status"])

    assert result["review_queue_count"] == 0


def test_discover_ingests_from_reddit_digest_db(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    digest_db_path = str(tmp_path / "digest.sqlite")

    import sqlite3

    dconn = sqlite3.connect(digest_db_path)
    dconn.execute(
        """CREATE TABLE digest_posts (
            post_id TEXT, subreddit TEXT, title TEXT, reddit_url TEXT,
            summary TEXT, score INTEGER, num_comments INTEGER,
            upvote_ratio REAL, quality_score REAL, why_care TEXT, digest_date TEXT
        )"""
    )
    dconn.execute(
        "INSERT INTO digest_posts VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("abc123", "test", "A title", "https://reddit.com/x", "summary",
         100, 5, 0.9, 8.0, "why care", "2026-01-01"),
    )
    dconn.commit()
    dconn.close()

    result = _run(
        capsys,
        ["--db", db_path, "discover", "--source", "reddit", "--digest-db", digest_db_path],
    )

    assert result["ingested"] == 1

    conn = db.connect(db_path)
    db.migrate(conn)
    row = conn.execute("SELECT COUNT(*) AS n FROM candidates").fetchone()
    assert row["n"] == 1


def test_discover_missing_digest_db_ingests_zero(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    missing_path = str(tmp_path / "does-not-exist.sqlite")

    result = _run(
        capsys,
        ["--db", db_path, "discover", "--source", "reddit", "--digest-db", missing_path],
    )

    assert result["ingested"] == 0


def test_ingest_verb_adds_candidates(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    result = _run(capsys, ["--db", db_path, "ingest", "--json", json.dumps([{
        "source": "test", "source_ref": "r1", "title": "T1",
        "url": "http://x", "summary": "S1"}])])
    assert result["ingested"] == 1


def _seed_candidate(db_path, candidate_id="reddit-abc123"):
    conn = db.connect(db_path)
    db.init_schema(conn)
    source.ingest(
        conn,
        [
            Candidate(
                source="reddit",
                source_ref="abc123",
                title="A title",
                url="https://reddit.com/x",
                summary="summary",
                predicted_relevance=0.8,
            )
        ],
    )
    conn.close()


def test_review_lists_pending_candidates(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _seed_candidate(db_path)

    result = _run(capsys, ["--db", db_path, "review"])

    assert result["count"] == 1
    assert result["candidates"][0]["title"] == "A title"


def test_review_accepts_today_override(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _seed_candidate(db_path)

    result = _run(capsys, ["--db", db_path, "review", "--today", "2026-01-01"])

    assert result["count"] == 1


def test_decide_yes_updates_status(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _seed_candidate(db_path)

    result = _run(capsys, ["--db", db_path, "decide", "reddit-abc123", "yes"])

    assert result["status"] == "yes"

    conn = db.connect(db_path)
    db.migrate(conn)
    row = conn.execute(
        "SELECT status FROM candidates WHERE id = ?", ("reddit-abc123",)
    ).fetchone()
    assert row["status"] == "yes"


def test_decide_snooze_with_note(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _seed_candidate(db_path)

    result = _run(
        capsys,
        ["--db", db_path, "decide", "reddit-abc123", "snooze", "--note", "revisit later"],
    )

    assert result["status"] == "snoozed"


def test_decide_invalid_outcome_errors_cleanly(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _seed_candidate(db_path)

    with pytest.raises(SystemExit):
        cli.main(["--db", db_path, "decide", "reddit-abc123", "bogus"])


def _seed_accepted_candidate(db_path, candidate_id="reddit-abc123"):
    conn = db.connect(db_path)
    db.init_schema(conn)
    source.ingest(
        conn,
        [
            Candidate(
                source="reddit",
                source_ref="abc123",
                title="A title",
                url="https://reddit.com/x",
                summary="summary",
                predicted_relevance=0.8,
            )
        ],
    )
    from content_pipeline import queue as queue_mod

    queue_mod.decide(conn, candidate_id, "yes", today="2026-01-01")
    conn.close()


def test_next_article_returns_context_not_questions(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _run(capsys, ["--db", db_path, "ingest", "--json", json.dumps([{
        "source": "test", "source_ref": "r1", "title": "T1",
        "url": "http://x", "summary": "S1"}])])
    _run(capsys, ["--db", db_path, "decide", "test-r1", "yes"])
    out = _run(capsys, ["--db", db_path, "next-article"])
    assert out["resumed"] is False
    assert out["article_id"]
    assert "questions" not in out
    assert "style_context" in out and "brand_context" in out
    assert out["candidate"]["title"] == "T1"


def test_next_article_resumes_existing_article(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _seed_accepted_candidate(db_path)

    conn = db.connect(db_path)
    db.migrate(conn)
    article_id = writing.start_article(conn, "reddit-abc123")
    conn.close()

    result = _run(capsys, ["--db", db_path, "next-article"])

    assert result["resumed"] is True
    assert result["article_id"] == article_id


def test_next_article_empty_queue_reports_none(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    conn = db.connect(db_path)
    db.init_schema(conn)
    conn.close()

    result = _run(capsys, ["--db", db_path, "next-article"])

    assert result["article_id"] is None


def _start_article(db_path, candidate_id="reddit-abc123"):
    _seed_accepted_candidate(db_path, candidate_id)
    conn = db.connect(db_path)
    db.migrate(conn)
    article_id = writing.start_article(conn, candidate_id)
    conn.close()
    return article_id


def test_answer_records_interview_answer(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    article_id = _start_article(db_path)

    result = _run(
        capsys,
        [
            "--db", db_path, "answer", article_id,
            "--question", "Q1?", "--chosen", "recommended", "--text", "R1",
        ],
    )

    assert result["recorded"] is True

    conn = db.connect(db_path)
    db.migrate(conn)
    row = conn.execute(
        "SELECT * FROM interview_answers WHERE article_id = ?", (article_id,)
    ).fetchone()
    assert row["chosen"] == "recommended"
    assert row["answer_text"] == "R1"


def test_save_draft_and_draft_context_roundtrip(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _run(capsys, ["--db", db_path, "ingest", "--json", json.dumps([{
        "source": "test", "source_ref": "r2", "title": "T2",
        "url": "http://y", "summary": "S2"}])])
    _run(capsys, ["--db", db_path, "decide", "test-r2", "yes"])
    started = _run(capsys, ["--db", db_path, "next-article"])
    aid = started["article_id"]
    _run(capsys, ["--db", db_path, "answer", aid, "--question", "angle?",
                  "--chosen", "recommended", "--text", "founders"])
    ctx = _run(capsys, ["--db", db_path, "draft-context", aid])
    assert ctx["answers"][0]["answer_text"] == "founders"
    saved = _run(capsys, ["--db", db_path, "save-draft", aid, "--text", "the full draft"])
    assert saved["status"] == "reviewing"


def test_edit_records_round(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    article_id = _start_article(db_path)
    _run(capsys, ["--db", db_path, "save-draft", article_id, "--text", "Draft body text."])

    result = _run(
        capsys,
        ["--db", db_path, "edit", article_id, "--feedback", "tighten this", "--text", "New draft text."],
    )

    assert result["round"] == 1


def test_approve_marks_article_approved(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    article_id = _start_article(db_path)
    _run(capsys, ["--db", db_path, "save-draft", article_id, "--text", "Draft body text."])

    result = _run(capsys, ["--db", db_path, "approve", article_id, "--text", "Final text."])

    assert result["status"] == "approved"

    conn = db.connect(db_path)
    db.migrate(conn)
    row = conn.execute(
        "SELECT status, final_text FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    assert row["status"] == "approved"
    assert row["final_text"] == "Final text."


def test_apply_synthesis_via_cli(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _run(capsys, ["--db", db_path, "ingest", "--json", json.dumps([{
        "source": "test", "source_ref": "r3", "title": "T3",
        "url": "http://z", "summary": "S3"}])])
    _run(capsys, ["--db", db_path, "decide", "test-r3", "yes"])
    aid = _run(capsys, ["--db", db_path, "next-article"])["article_id"]
    _run(capsys, ["--db", db_path, "save-draft", aid, "--text", "d1"])
    _run(capsys, ["--db", db_path, "edit", aid, "--feedback", "never shout", "--text", "d2"])
    _run(capsys, ["--db", db_path, "approve", aid, "--text", "d2"])
    sctx = _run(capsys, ["--db", db_path, "synthesis-context", aid])
    assert sctx["promotion_allowed"] in (True, False)
    out = _run(capsys, ["--db", db_path, "apply-synthesis", aid,
                        "--base-checkpoint", str(sctx["base_checkpoint"]),
                        "--json", json.dumps({
                            "new_rules": [{"text": "never shout", "kind": "negative",
                                           "evidence_ids": [1]}],
                            "supersede": [], "tendencies": []})])
    assert out["promoted"] is True


def test_status_reports_synthesis_pending(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    _run(capsys, ["--db", db_path, "ingest", "--json", json.dumps([{
        "source": "test", "source_ref": "r4", "title": "T4",
        "url": "http://q", "summary": "S4"}])])
    _run(capsys, ["--db", db_path, "decide", "test-r4", "yes"])
    aid = _run(capsys, ["--db", db_path, "next-article"])["article_id"]
    _run(capsys, ["--db", db_path, "save-draft", aid, "--text", "d1"])
    _run(capsys, ["--db", db_path, "approve", aid, "--text", "d1"])
    st = _run(capsys, ["--db", db_path, "status"])
    assert st["synthesis_pending"] is True     # approved, apply-synthesis not yet run
    sctx = _run(capsys, ["--db", db_path, "synthesis-context", aid])
    _run(capsys, ["--db", db_path, "apply-synthesis", aid,
                  "--base-checkpoint", str(sctx["base_checkpoint"]),
                  "--json", json.dumps({"new_rules": [], "supersede": [], "tendencies": []})])
    assert _run(capsys, ["--db", db_path, "status"])["synthesis_pending"] is False


# --- Task 5: save-brief / brief-writer-context / brief-context / edit-context ---
#
# These tests use `_cli` rather than the file's existing `_run` helper: the
# brief's reference helper is `_run(capsys, dbpath, *argv)` (variadic argv,
# reads only the last stdout line), which collides with the existing
# `_run(capsys, argv)` (single argv list) used by every test above. Since
# Python module-level function names are late-bound, redefining `_run` here
# would silently repoint *all* earlier calls to the new signature and break
# them. Renamed to `_cli` to avoid that; behavior is otherwise verbatim from
# the task brief.

def _cli(capsys, dbpath, *argv):
    cli.main(["--db", dbpath, *argv])
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def _started_article(dbpath):
    c = db.connect(dbpath)
    # brand-new file has no tables; bootstrap exactly as the CLI's _get_conn does
    has_meta = c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
    ).fetchone()
    db.init_schema(c) if has_meta is None else db.migrate(c)
    source.ingest(c, [Candidate(source="reddit", source_ref="r1", title="Pricing story",
                                url="u", summary="Raised price to $39, lost 40 users.")])
    cid = c.execute("SELECT id FROM candidates").fetchone()["id"]
    queue.decide(c, cid, "yes", today="2026-07-09")
    aid = writing.start_article(c, cid)
    c.close()
    return aid


def test_save_brief_and_brief_context_roundtrip(tmp_path, capsys):
    dbp = str(tmp_path / "p.sqlite")
    aid = _started_article(dbp)
    brief_json = json.dumps({"topic": "pricing", "angle": "lose the wrong customers",
                             "key_points": ["support-heavy churn"], "source_snippet": "…"})

    saved = _cli(capsys, dbp, "save-brief", aid, "--json", brief_json)
    assert saved["version"] == 1

    ctx = _cli(capsys, dbp, "brief-context", aid)
    assert ctx["brief"]["angle"] == "lose the wrong customers"
    assert isinstance(ctx["voice_doc"], str) and ctx["voice_doc"]


def test_brief_writer_context_has_answers_and_snippet(tmp_path, capsys):
    dbp = str(tmp_path / "p.sqlite")
    aid = _started_article(dbp)
    _cli(capsys, dbp, "answer", aid, "--question", "What is the takeaway?",
         "--chosen", "custom", "--text", "cheap price selects bad customers")

    ctx = _cli(capsys, dbp, "brief-writer-context", aid)
    assert ctx["answers"][0]["answer_text"] == "cheap price selects bad customers"
    assert "Raised price to $39" in ctx["source_snippet"]
    assert ctx["voice_doc"]


def test_edit_context_returns_current_draft(tmp_path, capsys):
    dbp = str(tmp_path / "p.sqlite")
    aid = _started_article(dbp)
    _cli(capsys, dbp, "save-draft", aid, "--text", "the current draft body")

    ctx = _cli(capsys, dbp, "edit-context", aid)
    assert ctx["current_draft"] == "the current draft body"
    assert "voice_doc" in ctx and "brief" in ctx
