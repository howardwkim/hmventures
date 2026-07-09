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
