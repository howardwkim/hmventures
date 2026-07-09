from content_pipeline import db

def test_schema_creates_core_tables(conn):
    names = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"candidates","articles","interview_answers","edit_rounds",
            "permanent_rules","provisional_tendencies","synthesis_runs",
            "events","schema_meta"} <= names

def test_schema_version_is_set(conn):
    assert db.schema_version(conn) == db.CURRENT_VERSION
