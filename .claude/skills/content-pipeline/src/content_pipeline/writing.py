import difflib
import json
import uuid
from datetime import datetime, timezone

from content_pipeline import events

VALID_CHOSEN = {"recommended", "alternate", "custom", "skip"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _char_diff_size(prior: str, new: str) -> int:
    """Character-level edit magnitude between prior and new text, using
    difflib.SequenceMatcher opcodes. Sums the larger of the two changed
    spans for every non-'equal' opcode, so it is sensitive to actual
    content change (insertions, deletions, and same-length replacements)
    rather than just the net length delta - a same-length full rewrite
    correctly registers as a large edit instead of edit_size == 0."""
    matcher = difflib.SequenceMatcher(None, prior, new)
    return sum(
        max(i2 - i1, j2 - j1)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    )


def next_candidate(conn):
    """Oldest accepted candidate (status 'yes') that doesn't have an article
    yet, FIFO by decided_at. Returns None when the queue is empty."""
    return conn.execute(
        """SELECT * FROM candidates
           WHERE status = 'yes'
             AND id NOT IN (SELECT candidate_id FROM articles)
           ORDER BY decided_at ASC"""
    ).fetchone()


def start_article(conn, candidate_id) -> str:
    """Create an articles row (status 'interviewing') for candidate_id,
    append an 'article_started' event, and return the new article id."""
    article_id = uuid.uuid4().hex
    conn.execute(
        """INSERT INTO articles (id, candidate_id, status, created_at)
           VALUES (?, ?, 'interviewing', ?)""",
        (article_id, candidate_id, _now()),
    )
    conn.commit()

    events.append(
        conn,
        "article_started",
        {"candidate_id": candidate_id},
        article_id=article_id,
        candidate_id=candidate_id,
    )

    return article_id


def record_answer(conn, article_id, question, chosen, answer_text, options) -> None:
    """Persist one interview answer immediately (save-as-you-go, so an
    interrupted interview doesn't lose already-answered questions) and log
    an 'interview_choice' event. chosen must be one of
    {recommended, alternate, custom, skip}."""
    if chosen not in VALID_CHOSEN:
        raise ValueError(f"chosen must be one of {sorted(VALID_CHOSEN)}, got {chosen!r}")

    conn.execute(
        """INSERT INTO interview_answers
               (article_id, question, options_json, chosen, answer_text, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (article_id, question, json.dumps(options), chosen, answer_text, _now()),
    )
    conn.commit()

    events.append(
        conn,
        "interview_choice",
        {"chosen": chosen, "question": question},
        article_id=article_id,
    )


def save_draft(conn, article_id, draft_text) -> None:
    """Persist an agent-written first draft: store it, move the article to
    'reviewing', and log a 'draft_generated' event. The draft text itself is
    produced by the conversational agent, not by this module."""
    conn.execute(
        "UPDATE articles SET draft_text = ?, status = 'reviewing' WHERE id = ?",
        (draft_text, article_id),
    )
    conn.commit()
    events.append(
        conn,
        "draft_generated",
        {"length": len(draft_text)},
        article_id=article_id,
    )


def record_edit_round(conn, article_id, operator_feedback, new_text) -> int:
    """Record one review-iterate round: computes edit_size as the character
    difference between the prior draft_text and new_text, bumps the round
    number, updates articles.draft_text, writes an edit_rounds row, and
    appends an 'edit_round' event. Returns the round number (1-indexed,
    per article)."""
    article = conn.execute(
        "SELECT draft_text FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    prior_text = article["draft_text"] if article and article["draft_text"] else ""
    edit_size = _char_diff_size(prior_text, new_text)

    last_round = conn.execute(
        "SELECT MAX(round) AS r FROM edit_rounds WHERE article_id = ?",
        (article_id,),
    ).fetchone()
    round_number = (last_round["r"] or 0) + 1

    what_changed = f"draft_text updated ({len(prior_text)} -> {len(new_text)} chars)"

    conn.execute(
        """INSERT INTO edit_rounds
               (article_id, round, operator_feedback, what_changed, edit_size, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (article_id, round_number, operator_feedback, what_changed, edit_size, _now()),
    )
    conn.execute(
        "UPDATE articles SET draft_text = ? WHERE id = ?",
        (new_text, article_id),
    )
    conn.commit()

    events.append(
        conn,
        "edit_round",
        {
            "round": round_number,
            "operator_feedback": operator_feedback,
            "what_changed": what_changed,
            "edit_size": edit_size,
        },
        article_id=article_id,
    )

    return round_number


def approve(conn, article_id, final_text) -> None:
    """Mark article_id approved: store final_text, set status 'approved' and
    approved_at, append an 'article_approved' event. Style synthesis is a
    separate, agent-driven step (synthesis_context + apply_synthesis), not
    triggered here."""
    conn.execute(
        """UPDATE articles
           SET status = 'approved', final_text = ?, approved_at = ?
           WHERE id = ?""",
        (final_text, _now(), article_id),
    )
    conn.commit()

    events.append(
        conn,
        "article_approved",
        {},
        article_id=article_id,
    )


def resumable(conn):
    """Return the single article stuck in 'interviewing' or 'reviewing'
    (oldest by created_at), or None if none exists. Used by the CLI to
    offer "pick up where you left off?" before starting a new article."""
    return conn.execute(
        """SELECT * FROM articles
           WHERE status IN ('interviewing', 'reviewing')
           ORDER BY created_at ASC"""
    ).fetchone()
