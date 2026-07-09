import json
import uuid
from datetime import datetime, timezone

from content_pipeline import events, llm

VALID_CHOSEN = {"recommended", "alternate", "custom", "skip"}


def _now():
    return datetime.now(timezone.utc).isoformat()


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


def interview_questions(conn, article_id, *, brand_context, style_context) -> list[dict]:
    """Generate interview questions for article_id via one llm.complete_json
    call. Each question comes back as {question, recommended, alternate} so
    the operator can accept a recommendation, pick the alternate, or write
    their own answer. brand_context and style_context are plain strings
    supplied by the caller (e.g. brand/voice docs text, active permanent
    rules and provisional tendencies) - this function does not compute them."""
    article = conn.execute(
        "SELECT * FROM articles WHERE id = ?", (article_id,)
    ).fetchone()
    candidate = conn.execute(
        "SELECT * FROM candidates WHERE id = ?", (article["candidate_id"],)
    ).fetchone()

    prompt = (
        "You are helping prepare an interview for a content article before "
        "drafting begins. Given the candidate story below, the brand context, "
        "and the style context, generate a short list of interview questions "
        "that will surface the operator's take on the story.\n\n"
        f"Candidate title: {candidate['title']}\n"
        f"Candidate summary: {candidate['summary']}\n\n"
        f"Brand context:\n{brand_context}\n\n"
        f"Style context:\n{style_context}\n\n"
        "For each question, propose a recommended answer and one alternate "
        "answer the operator could pick instead."
    )
    schema_hint = (
        '{"questions": [{"question": "string", "recommended": "string", '
        '"alternate": "string"}]}'
    )

    result = llm.complete_json(prompt, schema_hint=schema_hint)
    if not isinstance(result, dict) or not isinstance(result.get("questions"), list):
        raise ValueError(f"LLM response missing 'questions' list: {result!r}")
    return result["questions"]


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


def generate_draft(conn, article_id, *, research, brand_context, style_context) -> str:
    """Generate the first draft for article_id via one llm.complete call.
    The prompt injects the interview answers (confirmed/edited/skipped),
    the style rules verbatim, and an explicit no-em-dash constraint.
    Stores the result in articles.draft_text, moves status to 'reviewing',
    and appends a 'draft_generated' event. Returns the draft text."""
    candidate_row = conn.execute(
        """SELECT c.* FROM candidates c
           JOIN articles a ON a.candidate_id = c.id
           WHERE a.id = ?""",
        (article_id,),
    ).fetchone()

    answers = conn.execute(
        """SELECT question, chosen, answer_text
           FROM interview_answers WHERE article_id = ?
           ORDER BY id ASC""",
        (article_id,),
    ).fetchall()
    answers_text = "\n".join(
        f"- Q: {row['question']}\n  Chosen: {row['chosen']}\n  Answer: {row['answer_text']}"
        for row in answers
    ) or "(no interview answers recorded)"

    prompt = (
        "You are drafting a content article. Write the full first draft "
        "based on the research, the candidate story, the operator's interview "
        "answers, the brand context, and the style rules below.\n\n"
        f"Candidate title: {candidate_row['title'] if candidate_row else ''}\n"
        f"Candidate summary: {candidate_row['summary'] if candidate_row else ''}\n\n"
        f"Research:\n{research}\n\n"
        f"Interview answers:\n{answers_text}\n\n"
        f"Brand context:\n{brand_context}\n\n"
        "Style rules (apply verbatim):\n"
        f"{style_context}\n\n"
        "Constraint: do not use em dashes anywhere in the draft. Use commas, "
        "periods, or parentheses instead.\n\n"
        "Write the complete draft now."
    )

    draft_text = llm.complete(prompt)

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

    return draft_text


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
    edit_size = abs(len(new_text) - len(prior_text))

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
    """Mark article_id approved: stores final_text, sets status 'approved'
    and approved_at, appends an 'article_approved' event, then triggers
    the learning synthesis hook. Imported lazily to avoid a module-load
    cycle between writing and learning.synthesis."""
    from content_pipeline.learning import synthesis

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

    synthesis.on_approval(conn, article_id)


def resumable(conn):
    """Return the single article stuck in 'interviewing' or 'reviewing'
    (oldest by created_at), or None if none exists. Used by the CLI to
    offer "pick up where you left off?" before starting a new article."""
    return conn.execute(
        """SELECT * FROM articles
           WHERE status IN ('interviewing', 'reviewing')
           ORDER BY created_at ASC"""
    ).fetchone()
