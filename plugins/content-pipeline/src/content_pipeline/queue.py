from datetime import date, datetime, timedelta, timezone

from content_pipeline import events


def _now():
    return datetime.now(timezone.utc).isoformat()


def list_review(conn, today):
    """Pending + due-snooze candidates, FIFO by created_at. A candidate
    snoozed today (snoozed_until == today, set by decide()) stays hidden;
    one whose snoozed_until has already arrived (<= today) resurfaces."""
    return conn.execute(
        """SELECT * FROM candidates
           WHERE status = 'pending'
              OR (status = 'snoozed' AND snoozed_until <= ?)
           ORDER BY created_at ASC""",
        (today,),
    ).fetchall()


def decide(conn, candidate_id, outcome, *, today, idea_note=None):
    """Record a review decision. outcome in {yes, no, snooze}:
    - yes/no -> status set to the outcome
    - snooze -> status 'snoozed', snoozed_until = today + 1 day
    Sets decided_at, appends a 'decision' event (outcome + the candidate's
    stored predicted_relevance, for later calibration), and commits
    immediately (save-as-you-go)."""
    row = conn.execute(
        "SELECT predicted_relevance FROM candidates WHERE id = ?", (candidate_id,)
    ).fetchone()

    status = "snoozed" if outcome == "snooze" else outcome
    snoozed_until = (
        (date.fromisoformat(today) + timedelta(days=1)).isoformat()
        if outcome == "snooze"
        else None
    )

    conn.execute(
        """UPDATE candidates
           SET status = ?, snoozed_until = ?, idea_note = ?, decided_at = ?
           WHERE id = ?""",
        (status, snoozed_until, idea_note, _now(), candidate_id),
    )
    conn.commit()

    events.append(
        conn,
        "decision",
        {
            "outcome": outcome,
            "predicted_relevance": row["predicted_relevance"] if row else None,
        },
        candidate_id=candidate_id,
    )
