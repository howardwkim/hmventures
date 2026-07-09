from content_pipeline import events

def test_append_returns_monotonic_ids_and_since_filters(conn):
    a = events.append(conn, "decision", {"x": 1})
    b = events.append(conn, "decision", {"x": 2})
    assert b > a
    new = events.since(conn, a)
    assert [r["id"] for r in new] == [b]

def test_recent_filters_by_kind(conn):
    events.append(conn, "decision", {"x": 1})
    events.append(conn, "edit_round", {"y": 2})
    got = events.recent(conn, kind="edit_round", limit=10)
    assert len(got) == 1 and got[0]["kind"] == "edit_round"
