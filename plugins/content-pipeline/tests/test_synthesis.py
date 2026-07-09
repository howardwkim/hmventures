import pytest

from content_pipeline import events, writing
from content_pipeline.learning import canon, health, synthesis


def test_explicit_directive_promotes_immediately(conn, monkeypatch):
    # one edit event that reads as a directive
    events.append(conn, "edit_round", {"operator_feedback": "never use em dashes", "what_changed": "...", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []})
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)
    synthesis.on_approval(conn, "a1")
    assert any("em dashes" in r["rule_text"] for r in canon.active_rules(conn))


def test_explicit_directive_on_first_ever_article_promotes_end_to_end(conn, monkeypatch):
    # Regression test for the cold-start promotion gate bug: with exactly
    # one approved article, health.promotion_allowed must not be a
    # trivially-false positive spike, and an explicit directive on that
    # very first article must actually reach a permanent rule. Exercises
    # writing.approve -> synthesis.on_approval -> the REAL
    # health.promotion_allowed (not mocked), so it proves the fix end to
    # end rather than just asserting on health.py in isolation.
    conn.execute(
        "INSERT INTO articles (id, status, created_at) VALUES ('a1', 'reviewing', '2026-01-01T00:00:00+00:00')"
    )
    conn.commit()
    conn.execute(
        "INSERT INTO edit_rounds (article_id, round, operator_feedback, what_changed, edit_size, created_at) "
        "VALUES ('a1', 1, 'never use em dashes', 'removed em dashes', 5, '2026-01-01T00:00:00+00:00')"
    )
    conn.commit()
    events.append(
        conn,
        "edit_round",
        {"operator_feedback": "never use em dashes", "what_changed": "removed em dashes", "edit_size": 5},
        article_id="a1",
    )
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []})

    # Sanity check the real (unmocked) health gate first, since that's the
    # actual bug this test guards against.
    assert health.promotion_allowed(conn) is True

    writing.approve(conn, "a1", "final text")

    assert any("em dashes" in r["rule_text"] for r in canon.active_rules(conn))


def test_promotion_paused_when_thrashing(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "never X", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: False)
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [{"text": "Never X", "kind": "negative", "evidence_ids": [1]}], "supersede": [], "tendencies": []})
    synthesis.on_approval(conn, "a1")
    assert canon.active_rules(conn) == []  # no promotion during thrash
    assert conn.execute("SELECT 1 FROM events WHERE kind='synthesis_skipped_promotion'").fetchone()


def test_promotion_paused_still_rebuilds_provisional_tendencies(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "tends to open with a stat", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: False)
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [], "supersede": [],
        "tendencies": [{"text": "Tends to open with a stat", "evidence_ids": [1]}]})
    synthesis.on_approval(conn, "a1")
    rows = canon.tendencies(conn)
    assert len(rows) == 1
    assert rows[0]["tendency_text"] == "Tends to open with a stat"


def test_on_approval_returns_dict_summary(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []})
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)
    result = synthesis.on_approval(conn, "a1")
    assert isinstance(result, dict)
    assert result["promoted"] is True


def test_on_approval_updates_synthesis_runs_checkpoint(conn, monkeypatch):
    e1 = events.append(conn, "edit_round", {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {"new_rules": [], "supersede": [], "tendencies": []})
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)

    synthesis.on_approval(conn, "a1")

    row = conn.execute(
        "SELECT * FROM synthesis_runs WHERE artifact='style' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row is not None
    assert row["last_event_id_seen"] >= e1

    # a second run with no new events should see zero new events
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {"new_rules": [], "supersede": [], "tendencies": []})
    synthesis.on_approval(conn, "a1")
    row2 = conn.execute(
        "SELECT * FROM synthesis_runs WHERE artifact='style' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row2["event_count"] == 0


def test_supersede_applied_from_llm_output(conn, monkeypatch):
    old_id = canon.add_permanent_rule(conn, "Open with a question.", "positive", [1])
    events.append(conn, "edit_round", {"operator_feedback": "actually open with the number instead", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [{"text": "Open with the number.", "kind": "positive", "evidence_ids": [1]}],
        "supersede": [{"id": old_id, "reason": "operator reversed this call"}],
        "tendencies": []})

    synthesis.on_approval(conn, "a1")

    old_row = conn.execute("SELECT * FROM permanent_rules WHERE id=?", (old_id,)).fetchone()
    assert old_row["status"] == "superseded"
    assert any(r["rule_text"] == "Open with the number." for r in canon.active_rules(conn))


def test_pending_rule_notice_returns_none_when_no_new_rule(conn):
    assert synthesis.pending_rule_notice(conn, "a1") is None


def test_pending_rule_notice_surfaces_recently_promoted_rule(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []})
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)
    synthesis.on_approval(conn, "a1")

    notice = synthesis.pending_rule_notice(conn, "a2")
    assert notice is not None
    assert "em dashes" in notice
    assert "undo" in notice.lower()


def test_pending_rule_notice_does_not_repeat_after_shown(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [{"text": "Never use em dashes", "kind": "negative", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []})
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)
    synthesis.on_approval(conn, "a1")

    first = synthesis.pending_rule_notice(conn, "a2")
    assert first is not None
    second = synthesis.pending_rule_notice(conn, "a3")
    assert second is None


def test_malformed_new_rules_item_raises_and_applies_nothing(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        # missing "kind" on this new_rules item
        "new_rules": [{"text": "Never use em dashes", "evidence_ids": [1]}],
        "supersede": [], "tendencies": []})
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)

    with pytest.raises(ValueError):
        synthesis.on_approval(conn, "a1")

    assert canon.active_rules(conn) == []
    # checkpoint must not advance on a malformed response
    row = conn.execute(
        "SELECT * FROM synthesis_runs WHERE artifact='style' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row is None


def test_malformed_supersede_item_raises_and_applies_nothing(conn, monkeypatch):
    old_id = canon.add_permanent_rule(conn, "Open with a question.", "positive", [1])
    events.append(conn, "edit_round", {"operator_feedback": "actually open with the number instead", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [],
        # missing "reason" on this supersede item
        "supersede": [{"id": old_id}],
        "tendencies": []})

    with pytest.raises(ValueError):
        synthesis.on_approval(conn, "a1")

    old_row = conn.execute("SELECT * FROM permanent_rules WHERE id=?", (old_id,)).fetchone()
    assert old_row["status"] != "superseded"


def test_malformed_tendencies_item_raises_and_applies_nothing(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "tends to open with a stat", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: {
        "new_rules": [], "supersede": [],
        # missing "text" on this tendencies item
        "tendencies": [{"evidence_ids": [1]}]})

    with pytest.raises(ValueError):
        synthesis.on_approval(conn, "a1")

    assert canon.tendencies(conn) == []


def test_non_dict_response_raises_and_applies_nothing(conn, monkeypatch):
    events.append(conn, "edit_round", {"operator_feedback": "never use em dashes", "what_changed": "", "edit_size": 5}, article_id="a1")
    monkeypatch.setattr(synthesis.llm, "complete_json", lambda *a, **k: ["not", "a", "dict"])
    monkeypatch.setattr(synthesis.health, "promotion_allowed", lambda c: True)

    with pytest.raises(ValueError):
        synthesis.on_approval(conn, "a1")

    assert canon.active_rules(conn) == []
