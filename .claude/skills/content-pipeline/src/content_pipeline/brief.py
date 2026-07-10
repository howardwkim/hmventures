"""Per-article brief: the interview stage's output and the drafter's main
input. Content only (the *what*): topic, angle, key points, a source
snippet, and content constraints. Versioned - saving a brief appends a new
row; old versions are preserved so a regenerate from a changed brief is a
new artifact beside the old one. Never holds voice/tone/audience - those
live in the voice doc.
"""

import json
from datetime import datetime, timezone

from content_pipeline import events


def _now():
    return datetime.now(timezone.utc).isoformat()


def _validate(brief: dict) -> None:
    if not isinstance(brief, dict):
        raise ValueError(f"brief must be a dict, got {brief!r}")
    if not isinstance(brief.get("topic"), str) or not brief["topic"]:
        raise ValueError("brief missing non-empty string 'topic'")
    if not isinstance(brief.get("angle"), str) or not brief["angle"]:
        raise ValueError("brief missing non-empty string 'angle'")
    if not isinstance(brief.get("key_points"), list):
        raise ValueError("brief missing list 'key_points'")


def save_brief(conn, article_id, brief: dict) -> int:
    """Persist a new brief version for article_id; return the version number."""
    _validate(brief)
    row = conn.execute(
        "SELECT MAX(version) AS v FROM briefs WHERE article_id = ?", (article_id,)
    ).fetchone()
    version = (row["v"] or 0) + 1
    conn.execute(
        "INSERT INTO briefs (article_id, version, brief_json, created_at) VALUES (?, ?, ?, ?)",
        (article_id, version, json.dumps(brief), _now()),
    )
    conn.commit()
    events.append(conn, "brief_saved", {"version": version}, article_id=article_id)
    return version


def current_brief(conn, article_id) -> dict | None:
    """Latest brief for the article as {id, version, **fields}, or None."""
    row = conn.execute(
        "SELECT id, version, brief_json FROM briefs WHERE article_id = ? "
        "ORDER BY version DESC LIMIT 1",
        (article_id,),
    ).fetchone()
    if row is None:
        return None
    data = json.loads(row["brief_json"])
    return {**data, "id": row["id"], "version": row["version"]}
