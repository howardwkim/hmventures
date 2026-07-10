"""Style synthesis: the learning step, split into read + persist halves.

The conversational agent does the LLM judgment. This module gives it the
context to reason over (`synthesis_context`) and persists its decision
(`apply_synthesis`). There is no LLM call here.

- Permanent rules (`permanent_rules`) are ADDITIVE ONLY. New rules are
  inserted, existing rules are superseded (status flip, never deleted). The
  full set of permanent rules is never regenerated from scratch.
- Provisional tendencies (`provisional_tendencies`) are the one intentional
  exception: they are wholesale-replaced ("rebuild from scratch") every run,
  because a tendency is a live read of "what does the operator seem to want
  lately," not a durable commitment.

Two-door promotion: an explicit directive in the operator's feedback ("never
X", "always Y", "stop doing Z") earns a permanent rule immediately. A silent,
repeated pattern with no explicit directive earns only a provisional
tendency, which must accumulate more evidence before it can become a rule.

Thrash guard: if `health.promotion_allowed` says the edit-effort trend is
spiking, promotion is skipped for this run (no new permanent rules, no
supersessions), but provisional tendencies are still rebuilt and a
`synthesis_skipped_promotion` event is recorded so the skip is visible.
"""

import json

from content_pipeline import events
from content_pipeline.learning import canon, health

_RELEVANT_EVENT_KINDS = {"edit_round", "interview_choice"}


def _now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _last_checkpoint(conn):
    row = conn.execute(
        "SELECT * FROM synthesis_runs WHERE artifact = 'style' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return row["last_event_id_seen"] if row else 0


def _record_checkpoint(conn, last_event_id_seen, event_count):
    conn.execute(
        "INSERT INTO synthesis_runs (ts, artifact, last_event_id_seen, event_count) "
        "VALUES (?, 'style', ?, ?)",
        (_now(), last_event_id_seen, event_count),
    )
    conn.commit()


def synthesis_context(conn, article_id) -> dict:
    """Read-only context for the agent's style-synthesis reasoning. Returns
    the new edit/interview events since the last synthesis checkpoint, the
    current active permanent rules, and whether promotion is currently
    allowed (thrash guard). The agent reads this, decides new_rules /
    supersede / tendencies by the two-door rules, and calls apply_synthesis."""
    last_seen = _last_checkpoint(conn)
    all_new = events.since(conn, last_seen)
    relevant = [e for e in all_new if e["kind"] in _RELEVANT_EVENT_KINDS]
    new_events = [
        {
            "id": e["id"],
            "kind": e["kind"],
            "payload": json.loads(e["payload_json"]) if e["payload_json"] else {},
        }
        for e in relevant
    ]
    active = [
        {"id": r["id"], "kind": r["kind"], "rule_text": r["rule_text"]}
        for r in canon.active_rules(conn)
    ]
    return {
        "base_checkpoint": last_seen,
        "new_events": new_events,
        "active_rules": active,
        "promotion_allowed": health.promotion_allowed(conn),
    }


def _validate_apply_arg(result) -> None:
    """Guard apply_synthesis's own argument shape (agent-supplied dict).
    Restores the original on_approval validator's strictness: the three
    top-level keys must be present and be lists; every new rule must carry
    a string text, a positive|negative kind, AND evidence_ids (the
    provenance contract - a rule with no evidence is rejected); every
    supersede needs an id and a string reason; every tendency needs string
    text. Bad shapes raise a clean ValueError (never a raw AttributeError/
    TypeError), so the caller/CLI can surface it before any DB write."""
    if not isinstance(result, dict):
        raise ValueError(f"apply_synthesis expects a dict, got {result!r}")
    for key in ("new_rules", "supersede", "tendencies"):
        if key not in result:
            raise ValueError(f"apply_synthesis: missing required key '{key}'")
        if not isinstance(result[key], list):
            raise ValueError(f"apply_synthesis: '{key}' must be a list")
    for rule in result["new_rules"]:
        if not isinstance(rule, dict):
            raise ValueError(f"apply_synthesis: new_rules item is not a dict: {rule!r}")
        if not isinstance(rule.get("text"), str):
            raise ValueError(f"apply_synthesis: new_rules item missing string 'text': {rule!r}")
        if rule.get("kind") not in ("positive", "negative"):
            raise ValueError(f"apply_synthesis: new_rules item bad 'kind': {rule!r}")
        if not isinstance(rule.get("evidence_ids"), list):
            raise ValueError(f"apply_synthesis: new_rules item missing 'evidence_ids' list: {rule!r}")
    for s in result["supersede"]:
        if not isinstance(s, dict) or "id" not in s or not isinstance(s.get("reason"), str):
            raise ValueError(f"apply_synthesis: bad supersede item {s!r}")
    for t in result["tendencies"]:
        if not isinstance(t, dict) or not isinstance(t.get("text"), str):
            raise ValueError(f"apply_synthesis: bad tendencies item {t!r}")


def apply_synthesis(conn, article_id, result, *, base_checkpoint) -> dict:
    """Persist the agent's synthesis decision. Same persistence semantics the
    old LLM on_approval used: additive permanent rules + supersessions when
    promotion is allowed (else a skip event), provisional tendencies always
    rebuilt wholesale, checkpoint advanced, rule_promoted events logged.

    Idempotency: because new_rules/supersede/tendencies come from `result`
    (not the event window), a repeated call would re-insert them. Guard on
    base_checkpoint - if the checkpoint already moved past what the agent
    read, this apply already happened; write nothing and report skipped."""
    _validate_apply_arg(result)

    last_seen = _last_checkpoint(conn)
    if last_seen != base_checkpoint:
        return {
            "skipped": "checkpoint_advanced",
            "promoted": False,
            "new_rule_ids": [],
            "superseded_ids": [],
            "tendency_count": 0,
            "event_count": 0,
        }

    all_new = events.since(conn, last_seen)
    relevant = [e for e in all_new if e["kind"] in _RELEVANT_EVENT_KINDS]

    promotion_allowed = health.promotion_allowed(conn)
    new_rules = result.get("new_rules", []) or []
    supersede = result.get("supersede", []) or []
    tendencies = result.get("tendencies", []) or []

    new_rule_ids, superseded_ids = [], []

    if promotion_allowed:
        for rule in new_rules:
            rule_id = canon.add_permanent_rule(
                conn, rule["text"], rule["kind"], rule.get("evidence_ids", [])
            )
            new_rule_ids.append(rule_id)
            events.append(
                conn, "rule_promoted",
                {
                    "rule_id": rule_id, "rule_text": rule["text"], "kind": rule["kind"],
                    "evidence_ids": rule.get("evidence_ids", []),
                    "undo_note": f"Applied a new rule: {rule['text']}. Tap to undo.",
                },
                article_id=article_id,
            )
        for s in supersede:
            canon.supersede_rule(conn, s["id"], s["reason"])
            superseded_ids.append(s["id"])
    else:
        events.append(
            conn, "synthesis_skipped_promotion",
            {
                "reason": "edit-effort trend is spiking; promotion paused",
                "proposed_new_rules": len(new_rules),
                "proposed_supersede": len(supersede),
            },
            article_id=article_id,
        )

    conn.execute("DELETE FROM provisional_tendencies")
    for t in tendencies:
        conn.execute(
            "INSERT INTO provisional_tendencies (tendency_text, evidence_event_ids, rebuilt_at) "
            "VALUES (?, ?, ?)",
            (t["text"], json.dumps(t.get("evidence_ids", [])), _now()),
        )
    conn.commit()

    # Advance the checkpoint to the true high-water mark AFTER our own appends
    # (rule_promoted / synthesis_skipped_promotion), so "everything through
    # here is accounted for" holds literally, not just for the filtered kinds.
    true_max = conn.execute("SELECT MAX(id) AS m FROM events").fetchone()["m"]
    _record_checkpoint(conn, true_max if true_max is not None else last_seen, len(relevant))

    return {
        "skipped": None,
        "promoted": promotion_allowed,
        "new_rule_ids": new_rule_ids,
        "superseded_ids": superseded_ids,
        "tendency_count": len(tendencies),
        "event_count": len(relevant),
    }


def pending_rule_notice(conn, article_id) -> str | None:
    """The 'Applied a new rule: X - tap to undo' line the next draft
    surfaces. Reads the most recent rule_promoted event that has not yet
    been shown (no matching rule_notice_shown event references it), and
    marks it shown so it is not surfaced again."""
    promoted = events.recent(conn, kind="rule_promoted", limit=50)
    if not promoted:
        return None

    shown = events.recent(conn, kind="rule_notice_shown", limit=200)
    shown_ids = set()
    for e in shown:
        payload = json.loads(e["payload_json"]) if e["payload_json"] else {}
        if "rule_promoted_event_id" in payload:
            shown_ids.add(payload["rule_promoted_event_id"])

    for e in reversed(promoted):  # most recent first
        if e["id"] in shown_ids:
            continue
        payload = json.loads(e["payload_json"]) if e["payload_json"] else {}
        events.append(
            conn,
            "rule_notice_shown",
            {"rule_promoted_event_id": e["id"]},
            article_id=article_id,
        )
        return payload.get("undo_note") or f"Applied a new rule: {payload.get('rule_text')}. Tap to undo."

    return None
