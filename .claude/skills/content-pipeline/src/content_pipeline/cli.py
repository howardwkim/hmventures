"""Task E1: argparse CLI entry point for the content-pipeline skill.

Each subcommand opens its own connection (db.connect + bootstrap/migrate),
does its work against the real modules built in Task Groups A-D, and prints
one JSON object to stdout for the skill to parse/render. No subcommand
shares a connection across invocations - each CLI call is a fresh process.
"""

import argparse
import json

from content_pipeline import db, queue, writing, brief, voice
from content_pipeline.discovery import source
from content_pipeline.discovery.reddit_digest import RedditDigestSource
from content_pipeline.learning import canon, health, selection, synthesis

def _brand_context(conn):
    """Brand/voice context for the agent's prompts, read from
    ~/.content-pipeline/config.json (empty string if unset)."""
    from content_pipeline import config
    return config.brand_context()


def _get_conn(db_path):
    """Open a connection and ensure the schema is present. A brand-new
    sqlite file has no tables at all (db.migrate() assumes schema_meta
    already exists), so bootstrap with init_schema on first use and
    migrate() otherwise."""
    conn = db.connect(db_path)
    has_schema_meta = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
    ).fetchone()
    if has_schema_meta is None:
        db.init_schema(conn)
    else:
        db.migrate(conn)
    return conn


def _row_to_dict(row):
    return dict(row) if row is not None else None


def _rows_to_dicts(rows):
    return [dict(r) for r in rows]


def _print_json(obj):
    print(json.dumps(obj, default=str))


def _source_snippet(conn, article_id) -> str:
    """Short grounding excerpt from the originating candidate: title + summary."""
    row = conn.execute(
        "SELECT c.title, c.summary FROM candidates c "
        "JOIN articles a ON a.candidate_id = c.id WHERE a.id = ?",
        (article_id,),
    ).fetchone()
    if row is None:
        return ""
    return f"{row['title'] or ''}\n\n{row['summary'] or ''}".strip()


def cmd_discover(args):
    conn = _get_conn(args.db)
    try:
        if args.source == "reddit":
            adapter = RedditDigestSource(args.digest_db)
        else:
            raise SystemExit(f"unknown discovery source: {args.source!r}")

        candidates = adapter.fetch()
        count = source.ingest(conn, candidates)
        _print_json({"source": args.source, "fetched": len(candidates), "ingested": count})
    finally:
        conn.close()


def cmd_review(args):
    conn = _get_conn(args.db)
    try:
        today = args.today or _today_str()
        rows = queue.list_review(conn, today)
        candidates = _rows_to_dicts(rows)
        _print_json({"today": today, "count": len(candidates), "candidates": candidates})
    finally:
        conn.close()


def cmd_decide(args):
    conn = _get_conn(args.db)
    try:
        today = args.today or _today_str()
        try:
            queue.decide(conn, args.candidate_id, args.outcome, today=today, idea_note=args.note)
        except ValueError as e:
            raise SystemExit(str(e))

        row = conn.execute(
            "SELECT * FROM candidates WHERE id = ?", (args.candidate_id,)
        ).fetchone()
        _print_json({"candidate_id": args.candidate_id, "status": row["status"] if row else None})
    finally:
        conn.close()


def cmd_next_article(args):
    conn = _get_conn(args.db)
    try:
        resumable_article = writing.resumable(conn)
        if resumable_article is not None:
            _print_json({
                "resumed": True,
                "article_id": resumable_article["id"],
                "status": resumable_article["status"],
            })
            return

        candidate = writing.next_candidate(conn)
        if candidate is None:
            _print_json({"resumed": False, "article_id": None})
            return

        article_id = writing.start_article(conn, candidate["id"])
        _print_json({
            "resumed": False,
            "article_id": article_id,
            "candidate_id": candidate["id"],
            "candidate": {
                "title": candidate["title"],
                "summary": candidate["summary"],
                "url": candidate["url"],
            },
            "brand_context": _brand_context(conn),
            "style_context": canon.style_context(conn),
        })
    finally:
        conn.close()


def cmd_answer(args):
    conn = _get_conn(args.db)
    try:
        try:
            writing.record_answer(
                conn, args.article_id, args.question, args.chosen, args.text, options=None
            )
        except ValueError as e:
            raise SystemExit(str(e))

        _print_json({"article_id": args.article_id, "recorded": True})
    finally:
        conn.close()


def cmd_draft_context(args):
    conn = _get_conn(args.db)
    try:
        cand = conn.execute(
            """SELECT c.title, c.summary, c.url FROM candidates c
               JOIN articles a ON a.candidate_id = c.id WHERE a.id = ?""",
            (args.article_id,),
        ).fetchone()
        answers = conn.execute(
            """SELECT question, chosen, answer_text FROM interview_answers
               WHERE article_id = ? ORDER BY id ASC""",
            (args.article_id,),
        ).fetchall()
        _print_json({
            "article_id": args.article_id,
            "candidate": _row_to_dict(cand),
            "answers": _rows_to_dicts(answers),
            "brand_context": _brand_context(conn),
            "style_context": canon.style_context(conn),
        })
    finally:
        conn.close()


def cmd_save_brief(args):
    conn = _get_conn(args.db)
    try:
        try:
            data = json.loads(args.json)
            version = brief.save_brief(conn, args.article_id, data)
        except ValueError as e:
            raise SystemExit(str(e))
        _print_json({"article_id": args.article_id, "version": version})
    finally:
        conn.close()


def cmd_brief_writer_context(args):
    conn = _get_conn(args.db)
    try:
        answers = conn.execute(
            "SELECT question, chosen, answer_text FROM interview_answers "
            "WHERE article_id = ? ORDER BY id ASC",
            (args.article_id,),
        ).fetchall()
        _print_json({
            "article_id": args.article_id,
            "answers": _rows_to_dicts(answers),
            "source_snippet": _source_snippet(conn, args.article_id),
            "voice_doc": voice.voice_doc(conn, args.article_id),
        })
    finally:
        conn.close()


def cmd_brief_context(args):
    conn = _get_conn(args.db)
    try:
        _print_json({
            "article_id": args.article_id,
            "brief": brief.current_brief(conn, args.article_id),
            "voice_doc": voice.voice_doc(conn, args.article_id),
        })
    finally:
        conn.close()


def cmd_edit_context(args):
    conn = _get_conn(args.db)
    try:
        row = conn.execute(
            "SELECT draft_text FROM articles WHERE id = ?", (args.article_id,)
        ).fetchone()
        _print_json({
            "article_id": args.article_id,
            "current_draft": row["draft_text"] if row else None,
            "brief": brief.current_brief(conn, args.article_id),
            "voice_doc": voice.voice_doc(conn, args.article_id),
        })
    finally:
        conn.close()


def cmd_fork(args):
    conn = _get_conn(args.db)
    try:
        new_id = writing.fork_article(conn, args.article_id, voice_override=args.voice)
        if new_id is None:
            raise SystemExit(f"no such article: {args.article_id}")
        _print_json({
            "article_id": new_id,
            "forked_from": args.article_id,
            "has_voice_override": args.voice is not None,
        })
    finally:
        conn.close()


def cmd_save_draft(args):
    conn = _get_conn(args.db)
    try:
        writing.save_draft(conn, args.article_id, args.text)
        notice = synthesis.pending_rule_notice(conn, args.article_id)
        _print_json({
            "article_id": args.article_id,
            "status": "reviewing",
            "pending_rule_notice": notice,
        })
    finally:
        conn.close()


def cmd_synthesis_context(args):
    conn = _get_conn(args.db)
    try:
        _print_json(synthesis.synthesis_context(conn, args.article_id))
    finally:
        conn.close()


def cmd_apply_synthesis(args):
    conn = _get_conn(args.db)
    try:
        result = json.loads(args.json)
        try:
            out = synthesis.apply_synthesis(
                conn, args.article_id, result, base_checkpoint=args.base_checkpoint
            )
        except ValueError as e:
            raise SystemExit(str(e))
        _print_json(out)
    finally:
        conn.close()


def cmd_ingest(args):
    from content_pipeline.models import Candidate
    conn = _get_conn(args.db)
    try:
        raw = json.loads(args.json)
        candidates = [
            Candidate(
                source=c["source"], source_ref=c["source_ref"], title=c["title"],
                url=c.get("url", ""), summary=c.get("summary", ""),
                engagement=c.get("engagement", {}), topic_tags=c.get("topic_tags", []),
                emotional_driver=c.get("emotional_driver"), news_hook=c.get("news_hook"),
                predicted_relevance=c.get("predicted_relevance"),
            )
            for c in raw
        ]
        _print_json({"ingested": source.ingest(conn, candidates)})
    finally:
        conn.close()


def _synthesis_pending(conn) -> bool:
    """True if an article was approved but the style-synthesis step hasn't
    run for it yet. Because approve() no longer auto-triggers synthesis, a
    forgotten apply-synthesis would silently stall learning; status surfaces
    this. Detected structurally: an 'article_approved' event exists with an
    id beyond the last style-synthesis checkpoint (which apply_synthesis
    advances past all events it processed)."""
    last = synthesis._last_checkpoint(conn)
    row = conn.execute(
        "SELECT 1 FROM events WHERE kind='article_approved' AND id > ? LIMIT 1",
        (last,),
    ).fetchone()
    return row is not None


def cmd_edit(args):
    conn = _get_conn(args.db)
    try:
        round_number = writing.record_edit_round(conn, args.article_id, args.feedback, args.text)
        _print_json({"article_id": args.article_id, "round": round_number})
    finally:
        conn.close()


def cmd_approve(args):
    conn = _get_conn(args.db)
    try:
        writing.approve(conn, args.article_id, args.text)
        row = conn.execute(
            "SELECT * FROM articles WHERE id = ?", (args.article_id,)
        ).fetchone()
        _print_json({"article_id": args.article_id, "status": row["status"] if row else None})
    finally:
        conn.close()


def cmd_status(args):
    conn = _get_conn(args.db)
    try:
        today = args.today or _today_str()
        review_rows = queue.list_review(conn, today)
        resumable_article = writing.resumable(conn)
        next_up = writing.next_candidate(conn)
        counts = writing.pipeline_counts(conn)

        _print_json(
            {
                "review_queue_count": len(review_rows),
                "picked_not_started_count": counts["picked_not_started_count"],
                "articles_by_status": counts["articles_by_status"],
                "resumable_article": _row_to_dict(resumable_article),
                "next_article_available": resumable_article is not None or next_up is not None,
                "calibration": selection.calibration(conn),
                "edit_effort_trend": health.edit_effort_trend(conn),
                "nudge": health.nudge(conn),
                "synthesis_pending": _synthesis_pending(conn),
            }
        )
    finally:
        conn.close()


def cmd_describe_run(args):
    conn = _get_conn(args.db)
    try:
        _print_json(writing.describe_run(conn, args.article_id))
    finally:
        conn.close()


def _today_str():
    from datetime import date

    return date.today().isoformat()


def build_parser():
    parser = argparse.ArgumentParser(prog="content-pipeline")
    parser.add_argument("--db", default=None, help="Path to the pipeline sqlite DB")
    sub = parser.add_subparsers(dest="command", required=True)

    p_discover = sub.add_parser("discover", help="Fetch and ingest candidates from a source")
    p_discover.add_argument("--source", default="reddit", choices=["reddit"])
    p_discover.add_argument("--digest-db", dest="digest_db", required=True)
    p_discover.set_defaults(func=cmd_discover)

    p_review = sub.add_parser("review", help="Print the review queue")
    p_review.add_argument("--today", default=None)
    p_review.set_defaults(func=cmd_review)

    p_decide = sub.add_parser("decide", help="Record a review decision")
    p_decide.add_argument("candidate_id")
    p_decide.add_argument("outcome", help="yes|no|snooze")
    p_decide.add_argument("--note", default=None)
    p_decide.add_argument("--today", default=None)
    p_decide.set_defaults(func=cmd_decide)

    p_next_article = sub.add_parser("next-article", help="Resume or start the next article")
    p_next_article.set_defaults(func=cmd_next_article)

    p_answer = sub.add_parser("answer", help="Record one interview answer")
    p_answer.add_argument("article_id")
    p_answer.add_argument("--question", required=True)
    p_answer.add_argument("--chosen", required=True, choices=["recommended", "alternate", "custom", "skip"])
    p_answer.add_argument("--text", default=None, dest="text")
    p_answer.set_defaults(func=cmd_answer)

    p_draft_ctx = sub.add_parser("draft-context", help="Context for the agent to write the draft")
    p_draft_ctx.add_argument("article_id")
    p_draft_ctx.set_defaults(func=cmd_draft_context)

    p_save_brief = sub.add_parser("save-brief", help="Persist a versioned brief")
    p_save_brief.add_argument("article_id")
    p_save_brief.add_argument("--json", required=True, dest="json")
    p_save_brief.set_defaults(func=cmd_save_brief)

    p_bw_ctx = sub.add_parser("brief-writer-context", help="Context for the brief-writer subagent")
    p_bw_ctx.add_argument("article_id")
    p_bw_ctx.set_defaults(func=cmd_brief_writer_context)

    p_brief_ctx = sub.add_parser("brief-context", help="Context for the drafter subagent")
    p_brief_ctx.add_argument("article_id")
    p_brief_ctx.set_defaults(func=cmd_brief_context)

    p_edit_ctx = sub.add_parser("edit-context", help="Context for the edit subagent")
    p_edit_ctx.add_argument("article_id")
    p_edit_ctx.set_defaults(func=cmd_edit_context)

    p_save_draft = sub.add_parser("save-draft", help="Persist an agent-written draft")
    p_save_draft.add_argument("article_id")
    p_save_draft.add_argument("--text", required=True)
    p_save_draft.set_defaults(func=cmd_save_draft)

    p_syn_ctx = sub.add_parser("synthesis-context", help="Context for the agent's style synthesis")
    p_syn_ctx.add_argument("article_id")
    p_syn_ctx.set_defaults(func=cmd_synthesis_context)

    p_apply = sub.add_parser("apply-synthesis", help="Persist the agent's synthesis decision")
    p_apply.add_argument("article_id")
    p_apply.add_argument("--json", required=True, dest="json")
    p_apply.add_argument("--base-checkpoint", required=True, type=int, dest="base_checkpoint",
                         help="The base_checkpoint value from synthesis-context (idempotency guard)")
    p_apply.set_defaults(func=cmd_apply_synthesis)

    p_ingest = sub.add_parser("ingest", help="Ingest candidate topics from a JSON array")
    p_ingest.add_argument("--json", required=True, dest="json")
    p_ingest.set_defaults(func=cmd_ingest)

    p_edit = sub.add_parser("edit", help="Record an edit round")
    p_edit.add_argument("article_id")
    p_edit.add_argument("--feedback", required=True)
    p_edit.add_argument("--text", required=True)
    p_edit.set_defaults(func=cmd_edit)

    p_approve = sub.add_parser("approve", help="Approve the article")
    p_approve.add_argument("article_id")
    p_approve.add_argument("--text", required=True)
    p_approve.set_defaults(func=cmd_approve)

    p_status = sub.add_parser("status", help="Print queues + calibration + health nudge")
    p_status.add_argument("--today", default=None)
    p_status.set_defaults(func=cmd_status)

    p_fork = sub.add_parser(
        "fork",
        help="Fork an article (snapshot answers+brief) to regenerate in a new style",
    )
    p_fork.add_argument("article_id", help="Parent article id to fork from")
    p_fork.add_argument("--voice", default=None,
                        help="Pasted style guide used as the fork's whole voice doc")
    p_fork.set_defaults(func=cmd_fork)

    p_describe = sub.add_parser(
        "describe-run",
        help="Narrate an article's run (timeline derived from the tables, no events)",
    )
    p_describe.add_argument("article_id", nargs="?", default=None,
                            help="Article id; defaults to the most recent article")
    p_describe.set_defaults(func=cmd_describe_run)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except db.NoDatabaseConfigured as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    main()
