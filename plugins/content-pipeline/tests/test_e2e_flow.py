import json

from content_pipeline import cli, db


def _run(args, dbpath, capsys):
    cli.main(["--db", str(dbpath), *args])
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_full_lifecycle_backend(tmp_path, capsys):
    dbpath = tmp_path / "pipe.sqlite"
    _run(["ingest", "--json", json.dumps([{
        "source": "test", "source_ref": "e1", "title": "Remote work ruling",
        "url": "http://x", "summary": "A court ruling on remote work."}])], dbpath, capsys)
    _run(["decide", "test-e1", "yes"], dbpath, capsys)
    started = _run(["write-next"], dbpath, capsys)
    aid = started["article_id"]
    assert started["candidate"]["title"] == "Remote work ruling"
    _run(["answer", aid, "--question", "What's the angle?", "--chosen", "recommended",
          "--text", "employer risk"], dbpath, capsys)
    ctx = _run(["draft-context", aid], dbpath, capsys)
    assert ctx["answers"][0]["answer_text"] == "employer risk"
    _run(["save-draft", aid, "--text", "First draft body."], dbpath, capsys)
    _run(["edit", aid, "--feedback", "never use exclamation points",
          "--text", "Second draft body."], dbpath, capsys)
    _run(["approve", aid, "--text", "Second draft body."], dbpath, capsys)
    assert _run(["status"], dbpath, capsys)["synthesis_pending"] is True
    sctx = _run(["synthesis-context", aid], dbpath, capsys)
    out = _run(["apply-synthesis", aid,
                "--base-checkpoint", str(sctx["base_checkpoint"]),
                "--json", json.dumps({
                    "new_rules": [{"text": "never use exclamation points", "kind": "negative",
                                   "evidence_ids": [ev["id"] for ev in sctx["new_events"]
                                                    if ev["kind"] == "edit_round"]}],
                    "supersede": [], "tendencies": []})], dbpath, capsys)
    assert out["promoted"] is True
    assert _run(["status"], dbpath, capsys)["synthesis_pending"] is False

    conn = db.connect(str(dbpath))
    art = conn.execute("SELECT status FROM articles WHERE id=?", (aid,)).fetchone()
    assert art["status"] == "approved"
    rules = conn.execute("SELECT rule_text FROM permanent_rules WHERE status='active'").fetchall()
    assert any(r["rule_text"] == "never use exclamation points" for r in rules)
