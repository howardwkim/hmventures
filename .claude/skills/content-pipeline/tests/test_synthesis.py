import pytest

from content_pipeline import events, writing
from content_pipeline.learning import canon, health, synthesis


def _seed_yes_candidate(conn, ref="c1", title="T"):
    """Insert one accepted (status='yes') candidate and return its id.
    Mirrors the inserts other tests in this file already do; keeps the
    synthesis tests self-contained without depending on discovery.ingest."""
    conn.execute(
        "INSERT INTO candidates (id, source, source_ref, title, url, summary, "
        "status, created_at, decided_at) "
        "VALUES (?, 'test', ?, ?, 'http://x', 'S', 'yes', "
        "'2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00')",
        (f"test-{ref}", ref, title),
    )
    conn.commit()
    return f"test-{ref}"


def test_synthesis_context_returns_new_events_rules_and_gate(conn):
    canon.add_permanent_rule(conn, "no exclamation points", "negative", [])
    cand_id = _seed_yes_candidate(conn)
    article_id = writing.start_article(conn, cand_id)
    writing.record_answer(conn, article_id, "angle?", "recommended", "founders", options=None)
    writing.save_draft(conn, article_id, "draft one")
    writing.record_edit_round(conn, article_id, "never use exclamation points", "draft two")

    ctx = synthesis.synthesis_context(conn, article_id)

    assert "base_checkpoint" in ctx
    assert ctx["promotion_allowed"] in (True, False)
    assert any(r["rule_text"] == "no exclamation points" for r in ctx["active_rules"])
    kinds = {e["kind"] for e in ctx["new_events"]}
    assert kinds <= {"edit_round", "interview_choice"}
    assert any(e["kind"] == "edit_round" for e in ctx["new_events"])


def test_apply_synthesis_promotes_explicit_rule_when_allowed(conn):
    cand_id = _seed_yes_candidate(conn)
    article_id = writing.start_article(conn, cand_id)
    writing.save_draft(conn, article_id, "d1")
    writing.record_edit_round(conn, article_id, "never use em dashes", "d2")

    ctx = synthesis.synthesis_context(conn, article_id)
    out = synthesis.apply_synthesis(conn, article_id, {
        "new_rules": [{"text": "never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [],
        "tendencies": [],
    }, base_checkpoint=ctx["base_checkpoint"])
    assert out["skipped"] is None
    assert out["promoted"] is True
    assert len(out["new_rule_ids"]) == 1
    assert any(r["rule_text"] == "never use em dashes" for r in canon.active_rules(conn))


def test_apply_synthesis_is_idempotent_on_repeat(conn):
    """The double-apply guard: a second call with the same decision and the
    now-stale base_checkpoint must write nothing (no second rule row)."""
    cand_id = _seed_yes_candidate(conn)
    article_id = writing.start_article(conn, cand_id)
    writing.save_draft(conn, article_id, "d1")
    writing.record_edit_round(conn, article_id, "never use em dashes", "d2")

    ctx = synthesis.synthesis_context(conn, article_id)
    decision = {
        "new_rules": [{"text": "never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": [],
    }
    first = synthesis.apply_synthesis(conn, article_id, decision, base_checkpoint=ctx["base_checkpoint"])
    second = synthesis.apply_synthesis(conn, article_id, decision, base_checkpoint=ctx["base_checkpoint"])
    assert first["skipped"] is None and first["promoted"] is True
    assert second["skipped"] == "checkpoint_advanced"
    rules = [r for r in canon.active_rules(conn) if r["rule_text"] == "never use em dashes"]
    assert len(rules) == 1   # not double-inserted


def test_apply_synthesis_supersedes_existing_rule(conn):
    """Ported from the deleted test_supersede_applied_from_llm_output: an
    active rule is superseded (status flip, not deleted) when the agent's
    decision names it."""
    old_id = canon.add_permanent_rule(conn, "Open with a question.", "positive", [1])
    cand_id = _seed_yes_candidate(conn)
    article_id = writing.start_article(conn, cand_id)
    writing.save_draft(conn, article_id, "d1")
    writing.record_edit_round(conn, article_id, "stop opening with a question", "d2")

    ctx = synthesis.synthesis_context(conn, article_id)
    out = synthesis.apply_synthesis(conn, article_id, {
        "new_rules": [], "tendencies": [],
        "supersede": [{"id": old_id, "reason": "operator reversed this"}],
    }, base_checkpoint=ctx["base_checkpoint"])
    assert old_id in out["superseded_ids"]
    assert all(r["id"] != old_id for r in canon.active_rules(conn))   # no longer active
    row = conn.execute("SELECT status FROM permanent_rules WHERE id=?", (old_id,)).fetchone()
    assert row["status"] == "superseded"   # flipped, not deleted


def test_apply_synthesis_rebuilds_tendencies_wholesale(conn):
    cand_id = _seed_yes_candidate(conn)
    article_id = writing.start_article(conn, cand_id)
    writing.save_draft(conn, article_id, "d1")

    ctx1 = synthesis.synthesis_context(conn, article_id)
    synthesis.apply_synthesis(conn, article_id, {
        "new_rules": [], "supersede": [],
        "tendencies": [{"text": "leans casual", "evidence_ids": []}],
    }, base_checkpoint=ctx1["base_checkpoint"])
    ctx2 = synthesis.synthesis_context(conn, article_id)
    synthesis.apply_synthesis(conn, article_id, {
        "new_rules": [], "supersede": [],
        "tendencies": [{"text": "leans punchy", "evidence_ids": []}],
    }, base_checkpoint=ctx2["base_checkpoint"])
    texts = [t["tendency_text"] for t in canon.tendencies(conn)]
    assert texts == ["leans punchy"]   # wholesale replaced, not appended


def test_apply_synthesis_rejects_rule_without_evidence(conn):
    """Provenance contract: a new rule with no evidence_ids is rejected."""
    with pytest.raises(ValueError):
        synthesis.apply_synthesis(conn, "a1", {
            "new_rules": [{"text": "x", "kind": "positive"}],   # missing evidence_ids
            "supersede": [], "tendencies": [],
        }, base_checkpoint=0)


def test_apply_synthesis_returns_dict_summary(conn):
    events.append(conn, "edit_round",
                  {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5},
                  article_id="a1")
    ctx = synthesis.synthesis_context(conn, "a1")
    result = synthesis.apply_synthesis(conn, "a1", {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []},
        base_checkpoint=ctx["base_checkpoint"])
    assert isinstance(result, dict)
    assert result["promoted"] is True


def test_apply_synthesis_advances_checkpoint(conn):
    e1 = events.append(conn, "edit_round",
                       {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5},
                       article_id="a1")
    ctx = synthesis.synthesis_context(conn, "a1")
    synthesis.apply_synthesis(conn, "a1", {"new_rules": [], "supersede": [], "tendencies": []},
                              base_checkpoint=ctx["base_checkpoint"])

    row = conn.execute(
        "SELECT * FROM synthesis_runs WHERE artifact='style' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row is not None
    assert row["last_event_id_seen"] >= e1

    # a second synthesis pass with no new events sees zero new events
    ctx2 = synthesis.synthesis_context(conn, "a1")
    synthesis.apply_synthesis(conn, "a1", {"new_rules": [], "supersede": [], "tendencies": []},
                              base_checkpoint=ctx2["base_checkpoint"])
    row2 = conn.execute(
        "SELECT * FROM synthesis_runs WHERE artifact='style' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row2["event_count"] == 0


def test_promotion_paused_when_thrashing(conn, monkeypatch):
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: False)
    events.append(conn, "edit_round",
                  {"operator_feedback": "never X", "what_changed": "", "edit_size": 5},
                  article_id="a1")
    ctx = synthesis.synthesis_context(conn, "a1")
    synthesis.apply_synthesis(conn, "a1", {
        "new_rules": [{"text": "Never X", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []},
        base_checkpoint=ctx["base_checkpoint"])
    assert canon.active_rules(conn) == []  # no promotion during thrash
    assert conn.execute("SELECT 1 FROM events WHERE kind='synthesis_skipped_promotion'").fetchone()


def test_promotion_paused_still_rebuilds_provisional_tendencies(conn, monkeypatch):
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: False)
    events.append(conn, "edit_round",
                  {"operator_feedback": "tends to open with a stat", "what_changed": "", "edit_size": 5},
                  article_id="a1")
    ctx = synthesis.synthesis_context(conn, "a1")
    synthesis.apply_synthesis(conn, "a1", {
        "new_rules": [], "supersede": [],
        "tendencies": [{"text": "Tends to open with a stat", "evidence_ids": [1]}]},
        base_checkpoint=ctx["base_checkpoint"])
    rows = canon.tendencies(conn)
    assert len(rows) == 1
    assert rows[0]["tendency_text"] == "Tends to open with a stat"


def test_pending_rule_notice_returns_none_when_no_new_rule(conn):
    assert synthesis.pending_rule_notice(conn, "a1") is None


def test_pending_rule_notice_surfaces_recently_promoted_rule(conn):
    events.append(conn, "edit_round",
                  {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5},
                  article_id="a1")
    ctx = synthesis.synthesis_context(conn, "a1")
    synthesis.apply_synthesis(conn, "a1", {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []},
        base_checkpoint=ctx["base_checkpoint"])

    notice = synthesis.pending_rule_notice(conn, "a2")
    assert notice is not None
    assert "em dashes" in notice
    assert "undo" in notice.lower()


def test_pending_rule_notice_does_not_repeat_after_shown(conn):
    events.append(conn, "edit_round",
                  {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5},
                  article_id="a1")
    ctx = synthesis.synthesis_context(conn, "a1")
    synthesis.apply_synthesis(conn, "a1", {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []},
        base_checkpoint=ctx["base_checkpoint"])

    first = synthesis.pending_rule_notice(conn, "a2")
    assert first is not None
    second = synthesis.pending_rule_notice(conn, "a3")
    assert second is None
