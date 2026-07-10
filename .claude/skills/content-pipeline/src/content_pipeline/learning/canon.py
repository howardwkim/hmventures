import json
from datetime import datetime, timezone

VALID_KIND = {"positive", "negative"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def active_rules(conn):
    """permanent_rules rows with status 'active', oldest first."""
    return conn.execute(
        "SELECT * FROM permanent_rules WHERE status = 'active' ORDER BY id ASC"
    ).fetchall()


def tendencies(conn):
    """All provisional_tendencies rows, oldest first."""
    return conn.execute(
        "SELECT * FROM provisional_tendencies ORDER BY id ASC"
    ).fetchall()


def add_permanent_rule(conn, rule_text, kind, provenance_event_ids) -> int:
    """Insert a new active permanent_rules row. kind must be
    'positive' or 'negative'. provenance_event_ids is a list of event ids
    (stored as JSON). Returns the new row id."""
    if kind not in VALID_KIND:
        raise ValueError(f"kind must be one of {sorted(VALID_KIND)}, got {kind!r}")

    cur = conn.execute(
        """INSERT INTO permanent_rules
               (rule_text, kind, status, provenance_event_ids, created_at)
           VALUES (?, ?, 'active', ?, ?)""",
        (rule_text, kind, json.dumps(provenance_event_ids), _now()),
    )
    conn.commit()
    return cur.lastrowid


def supersede_rule(conn, rule_id, reason, superseded_by=None) -> None:
    """Mark a permanent_rules row superseded. Never deletes the row - it
    persists as history with status flipped to 'superseded' and
    superseded_reason/superseded_by recorded."""
    conn.execute(
        """UPDATE permanent_rules
           SET status = 'superseded', superseded_reason = ?, superseded_by = ?
           WHERE id = ?""",
        (reason, superseded_by, rule_id),
    )
    conn.commit()


def style_context(conn) -> str:
    """Prompt-injectable block of active style canon: permanent rules
    (verbatim, grouped positive/negative) followed by labeled current
    tendencies. This is the text Task C's interview_questions/generate_draft
    receive as their style_context parameter."""
    rules = active_rules(conn)
    positive = [r for r in rules if r["kind"] == "positive"]
    negative = [r for r in rules if r["kind"] == "negative"]
    tendency_rows = tendencies(conn)

    sections = []

    if positive:
        lines = "\n".join(f"- {r['rule_text']}" for r in positive)
        sections.append(f"Always (permanent rules):\n{lines}")

    if negative:
        lines = "\n".join(f"- {r['rule_text']}" for r in negative)
        sections.append(f"Never (permanent rules):\n{lines}")

    if tendency_rows:
        lines = "\n".join(f"- {t['tendency_text']}" for t in tendency_rows)
        sections.append(f"Provisional tendencies (not yet locked in, weigh lightly):\n{lines}")

    return "\n\n".join(sections)
