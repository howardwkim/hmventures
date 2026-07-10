from content_pipeline import db


def test_schema_creates_core_tables(conn):
    names = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"candidates","articles","interview_answers","edit_rounds",
            "permanent_rules","provisional_tendencies","synthesis_runs",
            "events","schema_meta"} <= names

def test_schema_version_is_set(conn):
    assert db.schema_version(conn) == db.CURRENT_VERSION


def test_fresh_db_is_v2_with_new_tables(conn):
    assert db.schema_version(conn) == 2
    for table in ("briefs", "draft_versions"):
        found = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        assert found is not None, f"missing table {table}"


def test_v1_to_v2_migration_backfills_draft_versions(tmp_path):
    c = db.connect(str(tmp_path / "v1.sqlite"))
    c.executescript(db._SCHEMA_V1)
    c.execute("INSERT INTO schema_meta(version) VALUES (1)")
    c.execute(
        "INSERT INTO articles (id, candidate_id, status, draft_text, created_at) "
        "VALUES ('a1', NULL, 'reviewing', 'existing draft body', '2026-01-01T00:00:00+00:00')"
    )
    c.execute(
        "INSERT INTO articles (id, candidate_id, status, draft_text, created_at) "
        "VALUES ('a2', NULL, 'interviewing', NULL, '2026-01-01T00:00:00+00:00')"
    )
    c.commit()

    db.migrate(c)

    assert db.schema_version(c) == 2
    v = c.execute("SELECT * FROM draft_versions WHERE article_id='a1'").fetchone()
    assert v["version"] == 1
    assert v["text"] == "existing draft body"
    assert v["brief_id"] is None
    # article with no draft_text is not backfilled
    none_row = c.execute("SELECT * FROM draft_versions WHERE article_id='a2'").fetchone()
    assert none_row is None
