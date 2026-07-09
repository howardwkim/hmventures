import json
from datetime import datetime, timezone

def _now():
    return datetime.now(timezone.utc).isoformat()

def append(conn, kind, payload, *, article_id=None, candidate_id=None):
    cur = conn.execute(
        "INSERT INTO events(ts,kind,article_id,candidate_id,payload_json) VALUES (?,?,?,?,?)",
        (_now(), kind, article_id, candidate_id, json.dumps(payload)))
    conn.commit()
    return cur.lastrowid

def since(conn, last_id):
    return conn.execute("SELECT * FROM events WHERE id > ? ORDER BY id", (last_id,)).fetchall()

def recent(conn, kind=None, limit=30):
    if kind:
        rows = conn.execute("SELECT * FROM events WHERE kind=? ORDER BY id DESC LIMIT ?",
                            (kind, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return list(reversed(rows))
