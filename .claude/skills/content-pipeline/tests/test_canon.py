from content_pipeline.learning import canon


def test_active_rules_returns_added_rules(conn):
    canon.add_permanent_rule(conn, "Always open with the number.", "positive", [1])
    canon.add_permanent_rule(conn, "Never use em dashes.", "negative", [2])

    rules = canon.active_rules(conn)

    assert len(rules) == 2
    assert {r["rule_text"] for r in rules} == {
        "Always open with the number.",
        "Never use em dashes.",
    }
    assert all(r["status"] == "active" for r in rules)


def test_supersede_rule_flips_status_but_row_persists(conn):
    rule_id = canon.add_permanent_rule(conn, "Never use em dashes.", "negative", [2])

    canon.supersede_rule(conn, rule_id, "operator reversed this call")

    assert canon.active_rules(conn) == []

    row = conn.execute(
        "SELECT * FROM permanent_rules WHERE id = ?", (rule_id,)
    ).fetchone()
    assert row is not None  # row persists, never deleted
    assert row["status"] == "superseded"
    assert row["superseded_reason"] == "operator reversed this call"

    total_rows = conn.execute(
        "SELECT COUNT(*) AS n FROM permanent_rules"
    ).fetchone()["n"]
    assert total_rows == 1  # supersede never deletes


def test_supersede_rule_records_superseded_by(conn):
    old_id = canon.add_permanent_rule(conn, "Open with a question.", "positive", [1])
    new_id = canon.add_permanent_rule(conn, "Open with the number.", "positive", [3])

    canon.supersede_rule(conn, old_id, "replaced by sharper rule", superseded_by=new_id)

    row = conn.execute(
        "SELECT * FROM permanent_rules WHERE id = ?", (old_id,)
    ).fetchone()
    assert row["superseded_by"] == new_id

    active_ids = {r["id"] for r in canon.active_rules(conn)}
    assert active_ids == {new_id}


def test_tendencies_returns_all_rows(conn):
    conn.execute(
        "INSERT INTO provisional_tendencies (tendency_text, evidence_event_ids, rebuilt_at) "
        "VALUES (?, ?, ?)",
        ("Tends to prefer shorter openers.", "[1, 2]", "2026-07-09T00:00:00+00:00"),
    )
    conn.commit()

    rows = canon.tendencies(conn)

    assert len(rows) == 1
    assert rows[0]["tendency_text"] == "Tends to prefer shorter openers."


def test_style_context_contains_rule_text_and_never_section(conn):
    canon.add_permanent_rule(conn, "Always open with the number.", "positive", [1])
    canon.add_permanent_rule(conn, "Never use em dashes.", "negative", [2])
    conn.execute(
        "INSERT INTO provisional_tendencies (tendency_text, evidence_event_ids, rebuilt_at) "
        "VALUES (?, ?, ?)",
        ("Tends to prefer shorter openers.", "[1]", "2026-07-09T00:00:00+00:00"),
    )
    conn.commit()

    context = canon.style_context(conn)

    assert "Always open with the number." in context
    assert "Never use em dashes." in context
    assert "Tends to prefer shorter openers." in context
    assert "never" in context.lower()  # negative-rules section is labeled


def test_style_context_excludes_superseded_rules(conn):
    rule_id = canon.add_permanent_rule(conn, "Never use em dashes.", "negative", [2])
    canon.supersede_rule(conn, rule_id, "reversed")

    context = canon.style_context(conn)

    assert "Never use em dashes." not in context


def test_style_context_empty_state_does_not_error(conn):
    context = canon.style_context(conn)
    assert isinstance(context, str)
