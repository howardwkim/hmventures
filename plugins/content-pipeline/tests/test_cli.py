import json

import pytest

from content_pipeline import cli, db, queue, writing
from content_pipeline.discovery import source
from content_pipeline.models import Candidate


def _run(capsys, argv):
    cli.main(argv)
    out = capsys.readouterr().out
    return json.loads(out)


def test_status_on_empty_db_prints_valid_json_with_zeroed_queues(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")

    result = _run(capsys, ["--db", db_path, "status"])

    assert result["review_queue_count"] == 0
    assert result["write_next_available"] is False
    assert result["calibration"]["n"] == 0
    assert result["nudge"] is None


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


def test_write_next_starts_article_and_returns_questions(tmp_path, capsys, monkeypatch):
    db_path = str(tmp_path / "t.sqlite")
    _seed_accepted_candidate(db_path)

    monkeypatch.setattr(
        writing.llm,
        "complete_json",
        lambda *a, **k: {
            "questions": [
                {"question": "Q1?", "recommended": "R1", "alternate": "A1"}
            ]
        },
    )

    result = _run(capsys, ["--db", db_path, "write-next"])

    assert result["resumed"] is False
    assert "article_id" in result
    assert result["questions"] == [
        {"question": "Q1?", "recommended": "R1", "alternate": "A1"}
    ]


def test_write_next_resumes_existing_article(tmp_path, capsys, monkeypatch):
    db_path = str(tmp_path / "t.sqlite")
    _seed_accepted_candidate(db_path)

    conn = db.connect(db_path)
    db.migrate(conn)
    article_id = writing.start_article(conn, "reddit-abc123")
    conn.close()

    result = _run(capsys, ["--db", db_path, "write-next"])

    assert result["resumed"] is True
    assert result["article_id"] == article_id


def test_write_next_empty_queue_reports_none(tmp_path, capsys):
    db_path = str(tmp_path / "t.sqlite")
    conn = db.connect(db_path)
    db.init_schema(conn)
    conn.close()

    result = _run(capsys, ["--db", db_path, "write-next"])

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


def test_draft_generates_and_returns_text(tmp_path, capsys, monkeypatch):
    db_path = str(tmp_path / "t.sqlite")
    article_id = _start_article(db_path)

    monkeypatch.setattr(writing.llm, "complete", lambda *a, **k: "Draft body text.")

    result = _run(capsys, ["--db", db_path, "draft", article_id])

    assert result["draft"] == "Draft body text."
    assert "pending_rule_notice" in result


def test_edit_records_round(tmp_path, capsys, monkeypatch):
    db_path = str(tmp_path / "t.sqlite")
    article_id = _start_article(db_path)

    monkeypatch.setattr(writing.llm, "complete", lambda *a, **k: "Draft body text.")
    conn = db.connect(db_path)
    db.migrate(conn)
    writing.generate_draft(conn, article_id, research="", brand_context="", style_context="")
    conn.close()

    result = _run(
        capsys,
        ["--db", db_path, "edit", article_id, "--feedback", "tighten this", "--text", "New draft text."],
    )

    assert result["round"] == 1


def test_approve_marks_article_approved(tmp_path, capsys, monkeypatch):
    db_path = str(tmp_path / "t.sqlite")
    article_id = _start_article(db_path)

    monkeypatch.setattr(writing.llm, "complete", lambda *a, **k: "Draft body text.")
    conn = db.connect(db_path)
    db.migrate(conn)
    writing.generate_draft(conn, article_id, research="", brand_context="", style_context="")
    conn.close()

    from content_pipeline.learning import synthesis

    monkeypatch.setattr(
        synthesis.llm,
        "complete_json",
        lambda *a, **k: {"new_rules": [], "supersede": [], "tendencies": []},
    )

    result = _run(capsys, ["--db", db_path, "approve", article_id, "--text", "Final text."])

    assert result["status"] == "approved"

    conn = db.connect(db_path)
    db.migrate(conn)
    row = conn.execute(
        "SELECT status, final_text FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    assert row["status"] == "approved"
    assert row["final_text"] == "Final text."
