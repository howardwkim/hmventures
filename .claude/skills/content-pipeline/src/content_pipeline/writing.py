import difflib
import json
import uuid
from datetime import datetime, timezone

from content_pipeline import events
from content_pipeline import brief as brief_mod
from content_pipeline import voice

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


def append_draft_version(conn, article_id, text) -> int:
    """Append a draft_versions row (next per-article version), capturing the
    brief_id and voice snapshot that produced this text. Returns the version
    number. Called by save_draft and record_edit_round so every draft and
    edit round is preserved - nothing overwritten."""
    row = conn.execute(
        "SELECT MAX(version) AS v FROM draft_versions WHERE article_id = ?", (article_id,)
    ).fetchone()
    version = (row["v"] or 0) + 1
    cur = brief_mod.current_brief(conn, article_id)
    brief_id = cur["id"] if cur else None
    conn.execute(
        "INSERT INTO draft_versions (article_id, version, text, brief_id, voice_snapshot, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (article_id, version, text, brief_id, voice.voice_doc(conn, article_id), _now()),
    )
    conn.commit()
    return version


def next_candidate(conn):
    """Oldest accepted candidate (status 'yes') that doesn't have an article
    yet, FIFO by decided_at. Returns None when the queue is empty."""
    return conn.execute(
        """SELECT * FROM candidates
           WHERE status = 'yes'
             AND id NOT IN (SELECT candidate_id FROM articles)
           ORDER BY decided_at ASC"""
    ).fetchone()


def pipeline_counts(conn):
    """Counts for the status overview: how many accepted candidates are
    waiting to be written (status 'yes' with no article yet), and how many
    articles sit in each status. Surfaces buckets that would otherwise be
    invisible — a picked-but-not-started candidate belongs to neither the
    pending review queue nor the started-articles set."""
    picked_not_started = conn.execute(
        """SELECT COUNT(*) FROM candidates
           WHERE status = 'yes'
             AND id NOT IN (SELECT candidate_id FROM articles)"""
    ).fetchone()[0]
    rows = conn.execute(
        "SELECT status, COUNT(*) AS n FROM articles GROUP BY status"
    ).fetchall()
    articles_by_status = {row["status"]: row["n"] for row in rows}
    return {
        "picked_not_started_count": picked_not_started,
        "articles_by_status": articles_by_status,
    }


def describe_run(conn, article_id=None):
    """Reconstruct an article's run as an ordered timeline, derived purely
    from the typed tables (articles, interview_answers, briefs,
    draft_versions, edit_rounds) — no dependency on the events log. This is
    the read-only 'what happened' narration: everything here is already
    persisted as durable rows, so nothing is duplicated to produce it.

    article_id defaults to the most recently created article (handy for "show
    me my last run"). Returns None if there is no such article. Style
    synthesis is global (synthesis_runs has no article_id), so the latest run
    is reported separately rather than attributed to this article."""
    if article_id is None:
        row = conn.execute(
            "SELECT id FROM articles ORDER BY created_at DESC, id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        article_id = row["id"]

    art = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    if art is None:
        return None
    cand = conn.execute(
        "SELECT title, source, source_ref FROM candidates WHERE id = ?",
        (art["candidate_id"],),
    ).fetchone()

    timeline = [{"ts": art["created_at"], "step": "started", "status": "interviewing"}]

    answers = conn.execute(
        "SELECT question, chosen, created_at FROM interview_answers "
        "WHERE article_id = ? ORDER BY created_at, id",
        (article_id,),
    ).fetchall()
    for a in answers:
        timeline.append(
            {"ts": a["created_at"], "step": "interview_answer",
             "question": a["question"], "chosen": a["chosen"]}
        )

    for b in conn.execute(
        "SELECT version, created_at FROM briefs WHERE article_id = ? ORDER BY version",
        (article_id,),
    ).fetchall():
        timeline.append({"ts": b["created_at"], "step": "brief_saved", "version": b["version"]})

    for d in conn.execute(
        "SELECT version, text, created_at FROM draft_versions "
        "WHERE article_id = ? ORDER BY version",
        (article_id,),
    ).fetchall():
        timeline.append(
            {"ts": d["created_at"], "step": "draft_version",
             "version": d["version"], "chars": len(d["text"])}
        )

    for e in conn.execute(
        "SELECT round, operator_feedback, edit_size, created_at FROM edit_rounds "
        "WHERE article_id = ? ORDER BY round",
        (article_id,),
    ).fetchall():
        timeline.append(
            {"ts": e["created_at"], "step": "edit_round", "round": e["round"],
             "edit_size": e["edit_size"], "feedback": e["operator_feedback"]}
        )

    if art["approved_at"]:
        timeline.append({"ts": art["approved_at"], "step": "approved"})

    timeline.sort(key=lambda x: x["ts"])

    latest_synthesis = conn.execute(
        "SELECT ts, artifact, event_count FROM synthesis_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()

    return {
        "article_id": article_id,
        "candidate_id": art["candidate_id"],
        "title": cand["title"] if cand else None,
        "status": art["status"],
        "forked_from": art["forked_from"],
        "has_voice_override": bool(art["voice_override"]),
        "answer_count": len(answers),
        "draft_versions": max((t["version"] for t in timeline if t["step"] == "draft_version"), default=0),
        "edit_rounds": sum(1 for t in timeline if t["step"] == "edit_round"),
        "timeline": timeline,
        "latest_synthesis": _row_to_dict_or_none(latest_synthesis),
    }


def _row_to_dict_or_none(row):
    return dict(row) if row is not None else None


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


def fork_article(conn, parent_article_id, voice_override=None) -> str | None:
    """Fork parent_article_id into a new article that snapshots the shared
    upstream (same candidate, a copy of the interview answers, a copy of the
    current brief) but NOT the draft/edit history — the fork diverges at the
    draft. The copy is a point-in-time snapshot: later edits to the parent do
    not flow into the fork. `forked_from` records the parent; an optional
    voice_override becomes the fork's whole voice doc so it regenerates in a
    pasted style without touching global config. Lands in 'interviewing'
    (i.e. briefed, pre-draft — the same state a normal article sits in after
    its brief is saved); the next step is to draft it. Returns the new
    article id, or None if the parent does not exist."""
    parent = conn.execute(
        "SELECT candidate_id FROM articles WHERE id = ?", (parent_article_id,)
    ).fetchone()
    if parent is None:
        return None

    article_id = uuid.uuid4().hex
    conn.execute(
        """INSERT INTO articles (id, candidate_id, status, created_at, forked_from, voice_override)
           VALUES (?, ?, 'interviewing', ?, ?, ?)""",
        (article_id, parent["candidate_id"], _now(), parent_article_id, voice_override),
    )

    conn.execute(
        """INSERT INTO interview_answers
               (article_id, question, options_json, chosen, answer_text, created_at)
           SELECT ?, question, options_json, chosen, answer_text, created_at
             FROM interview_answers WHERE article_id = ? ORDER BY id ASC""",
        (article_id, parent_article_id),
    )
    conn.commit()

    parent_brief = brief_mod.current_brief(conn, parent_article_id)
    if parent_brief is not None:
        carried = {k: v for k, v in parent_brief.items() if k not in ("id", "version")}
        brief_mod.save_brief(conn, article_id, carried)

    events.append(
        conn,
        "article_forked",
        {"forked_from": parent_article_id, "has_voice_override": voice_override is not None},
        article_id=article_id,
        candidate_id=parent["candidate_id"],
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
    append_draft_version(conn, article_id, draft_text)
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

    append_draft_version(conn, article_id, new_text)
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
