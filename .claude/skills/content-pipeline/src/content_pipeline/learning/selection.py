import json


def _decision_rows(conn, limit=None):
    """decision events joined against candidates for the title, oldest-first
    (i.e. newest-last) within the window. candidate_id is a real column on
    events (set by queue.decide), not part of the JSON payload."""
    query = """
        SELECT e.payload_json AS payload_json, c.title AS title
        FROM events e
        JOIN candidates c ON c.id = e.candidate_id
        WHERE e.kind = 'decision'
        ORDER BY e.id DESC
    """
    if limit is not None:
        query += " LIMIT ?"
        rows = conn.execute(query, (limit,)).fetchall()
    else:
        rows = conn.execute(query).fetchall()
    return list(reversed(rows))  # oldest-first / newest-last


def selection_context(conn, limit=30) -> str:
    """Raw-recent render of the last `limit` decision events as rows of
    {title, outcome, predicted_relevance}, newest-last. No distillation -
    this is a plain text block for the surfacing prompt."""
    rows = _decision_rows(conn, limit=limit)

    lines = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        lines.append(
            f"- {row['title']} | outcome={payload['outcome']} "
            f"| predicted_relevance={payload['predicted_relevance']}"
        )
    return "\n".join(lines)


def calibration(conn) -> dict:
    """Live-computed calibration over all decision events: how well
    predicted_relevance tracked the actual operator outcome (yes=1/no=0).
    snooze outcomes are excluded (no accept/reject signal)."""
    rows = _decision_rows(conn)

    errors = []
    over_accepts = 0
    scored = 0

    for row in rows:
        payload = json.loads(row["payload_json"])
        outcome = payload["outcome"]
        if outcome not in ("yes", "no"):
            continue

        predicted = payload["predicted_relevance"]
        if predicted is None:
            continue

        actual = 1 if outcome == "yes" else 0
        errors.append(abs(predicted - actual))
        scored += 1
        if predicted >= 0.5 and outcome == "no":
            over_accepts += 1

    n = scored
    mean_abs_error = sum(errors) / n if n else 0
    over_accept_rate = over_accepts / n if n else 0

    return {
        "n": n,
        "mean_abs_error": mean_abs_error,
        "over_accept_rate": over_accept_rate,
    }
