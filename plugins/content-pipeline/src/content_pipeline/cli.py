"""Task E1: argparse CLI entry point for the content-pipeline skill.

Each subcommand opens its own connection (db.connect + bootstrap/migrate),
does its work against the real modules built in Task Groups A-D, and prints
one JSON object to stdout for the skill to parse/render. No subcommand
shares a connection across invocations - each CLI call is a fresh process.
"""

import argparse
import json

from content_pipeline import db, queue, writing
from content_pipeline.discovery import source
from content_pipeline.discovery.reddit_digest import RedditDigestSource
from content_pipeline.learning import canon, health, selection, synthesis

# brand_context has no dedicated task in this plan (deferred/out of scope).
# Passed through as an empty placeholder wherever writing.* needs a string.
BRAND_CONTEXT = ""


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


def cmd_write_next(args):
    conn = _get_conn(args.db)
    try:
        resumable_article = writing.resumable(conn)
        if resumable_article is not None:
            article_id = resumable_article["id"]
            _print_json(
                {
                    "resumed": True,
                    "article_id": article_id,
                    "status": resumable_article["status"],
                }
            )
            return

        candidate = writing.next_candidate(conn)
        if candidate is None:
            _print_json({"resumed": False, "article_id": None, "questions": None})
            return

        article_id = writing.start_article(conn, candidate["id"])
        try:
            questions = writing.interview_questions(
                conn,
                article_id,
                brand_context=BRAND_CONTEXT,
                style_context=canon.style_context(conn),
            )
        except ValueError as e:
            raise SystemExit(str(e))

        _print_json(
            {
                "resumed": False,
                "article_id": article_id,
                "candidate_id": candidate["id"],
                "questions": questions,
            }
        )
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


def cmd_draft(args):
    conn = _get_conn(args.db)
    try:
        draft_text = writing.generate_draft(
            conn,
            args.article_id,
            research=args.research or "",
            brand_context=BRAND_CONTEXT,
            style_context=canon.style_context(conn),
        )
        notice = synthesis.pending_rule_notice(conn, args.article_id)
        _print_json(
            {
                "article_id": args.article_id,
                "draft": draft_text,
                "pending_rule_notice": notice,
            }
        )
    finally:
        conn.close()


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

        _print_json(
            {
                "review_queue_count": len(review_rows),
                "resumable_article": _row_to_dict(resumable_article),
                "write_next_available": resumable_article is not None or next_up is not None,
                "calibration": selection.calibration(conn),
                "edit_effort_trend": health.edit_effort_trend(conn),
                "nudge": health.nudge(conn),
            }
        )
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

    p_write_next = sub.add_parser("write-next", help="Resume or start the next article")
    p_write_next.set_defaults(func=cmd_write_next)

    p_answer = sub.add_parser("answer", help="Record one interview answer")
    p_answer.add_argument("article_id")
    p_answer.add_argument("--question", required=True)
    p_answer.add_argument("--chosen", required=True, choices=["recommended", "alternate", "custom", "skip"])
    p_answer.add_argument("--text", default=None, dest="text")
    p_answer.set_defaults(func=cmd_answer)

    p_draft = sub.add_parser("draft", help="Generate the first draft")
    p_draft.add_argument("article_id")
    p_draft.add_argument("--research", default=None)
    p_draft.set_defaults(func=cmd_draft)

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

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
