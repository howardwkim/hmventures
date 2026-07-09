"""Task D4: synthesis on approval.

The one synthesis pass that runs after every article approval. It reads the
edit and interview events since the last synthesis checkpoint, asks the LLM
to classify what happened, and applies the result to the style canon:

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

from content_pipeline import events, llm
from content_pipeline.learning import canon, health

DEFAULT_MODEL = llm.DEFAULT_MODEL

_STYLE_SYNTH_PROMPT = """You are maintaining a writing style canon for a content pipeline.
You will be given the current active permanent rules and a set of new events
(edit rounds and interview choices) that happened since the last synthesis pass.

Your job is to propose changes to the canon based ONLY on the new events. Follow
these rules exactly:

1. Additive only. Never propose regenerating the full rule set. Only propose
   NEW rules to add, or EXISTING rules to supersede (by id, with a reason).
   Every existing active rule not explicitly superseded stays exactly as is.

2. Cite evidence. Every new rule and every tendency must cite the event ids
   that support it, in evidence_ids. Do not propose a rule with no evidence.

3. Classify each edit as generalizable or one-off before using it as evidence.
   A generalizable edit reflects a lasting preference (a phrasing habit, a
   structural preference, a recurring correction). A one-off is specific to
   that single article (a fact correction, a typo, a detail unique to that
   story) and should not become a rule or a tendency on its own. Only
   generalizable edits earn a rule or tendency.

4. Two-door promotion. If the operator's feedback contains an explicit
   directive (words like never, always, stop, from now on, don't, must),
   propose it as a new permanent rule immediately (new_rules). If the
   evidence instead shows a silent, repeated tendency with no explicit
   directive, propose it as a provisional tendency (tendencies), not a
   permanent rule. Do not promote a silent pattern to a permanent rule
   yourself; that path runs through repeated tendency evidence over time.

5. Never regenerate the permanent rule list. supersede is the only way an
   existing permanent rule changes status, and it always needs a reason.

Return a JSON object with exactly these keys:
- new_rules: list of {text, kind (positive or negative), evidence_ids}
- supersede: list of {id, reason}
- tendencies: list of {text, evidence_ids}
"""

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


def _format_active_rules(conn):
    rules = canon.active_rules(conn)
    if not rules:
        return "(none yet)"
    return "\n".join(f"- id={r['id']} [{r['kind']}] {r['rule_text']}" for r in rules)


def _format_new_events(new_events):
    lines = []
    for e in new_events:
        payload = json.loads(e["payload_json"]) if e["payload_json"] else {}
        lines.append(f"- event_id={e['id']} kind={e['kind']} payload={payload}")
    return "\n".join(lines) if lines else "(none)"


def _validate_synthesis_result(result) -> None:
    """Validate the full shape of the parsed llm.complete_json response
    before anything is applied. llm.complete_json only guarantees "some
    JSON object was parsed" - it does not guarantee the shape matches
    schema_hint. Raises ValueError on any mismatch so the failure happens
    before any DB write in on_approval, keeping the apply step atomic from
    the caller's perspective (checkpoint does not advance on a malformed
    response, so the next approve() call reprocesses the same events
    cleanly)."""
    if not isinstance(result, dict):
        raise ValueError(f"malformed synthesis response: not a dict: {result!r}")

    new_rules = result.get("new_rules")
    if not isinstance(new_rules, list):
        raise ValueError(f"malformed synthesis response: 'new_rules' is not a list: {result!r}")
    for rule in new_rules:
        if not isinstance(rule, dict):
            raise ValueError(f"malformed synthesis response: new_rules item is not a dict: {rule!r}")
        if not isinstance(rule.get("text"), str):
            raise ValueError(f"malformed synthesis response: new_rules item missing string 'text': {rule!r}")
        if not isinstance(rule.get("kind"), str):
            raise ValueError(f"malformed synthesis response: new_rules item missing string 'kind': {rule!r}")
        if "evidence_ids" not in rule:
            raise ValueError(f"malformed synthesis response: new_rules item missing 'evidence_ids': {rule!r}")

    supersede = result.get("supersede")
    if not isinstance(supersede, list):
        raise ValueError(f"malformed synthesis response: 'supersede' is not a list: {result!r}")
    for s in supersede:
        if not isinstance(s, dict):
            raise ValueError(f"malformed synthesis response: supersede item is not a dict: {s!r}")
        if "id" not in s:
            raise ValueError(f"malformed synthesis response: supersede item missing 'id': {s!r}")
        if not isinstance(s.get("reason"), str):
            raise ValueError(f"malformed synthesis response: supersede item missing string 'reason': {s!r}")

    tendencies = result.get("tendencies")
    if not isinstance(tendencies, list):
        raise ValueError(f"malformed synthesis response: 'tendencies' is not a list: {result!r}")
    for t in tendencies:
        if not isinstance(t, dict):
            raise ValueError(f"malformed synthesis response: tendencies item is not a dict: {t!r}")
        if not isinstance(t.get("text"), str):
            raise ValueError(f"malformed synthesis response: tendencies item missing string 'text': {t!r}")


def on_approval(conn, article_id, *, model=llm.DEFAULT_MODEL) -> dict:
    """The one synthesis pass, called from writing.approve() after an
    article is approved. Returns a summary dict describing what happened."""
    # Step 1: checkpoint + gather new events since last synthesis run.
    last_seen = _last_checkpoint(conn)
    all_new = events.since(conn, last_seen)
    relevant = [e for e in all_new if e["kind"] in _RELEVANT_EVENT_KINDS]
    max_event_id = max((e["id"] for e in all_new), default=last_seen)

    promotion_allowed = health.promotion_allowed(conn)

    new_rule_ids = []
    superseded_ids = []

    # Always call the LLM, even with no new relevant events, so a rebuilt
    # (possibly empty) provisional tendency set behaves consistently.
    prompt = (
        f"{_STYLE_SYNTH_PROMPT}\n\n"
        f"Current active permanent rules:\n{_format_active_rules(conn)}\n\n"
        f"New events since last synthesis:\n{_format_new_events(relevant)}\n"
    )
    schema_hint = (
        '{"new_rules": [{"text": "string", "kind": "positive|negative", '
        '"evidence_ids": [int]}], "supersede": [{"id": int, "reason": "string"}], '
        '"tendencies": [{"text": "string", "evidence_ids": [int]}]}'
    )
    result = llm.complete_json(prompt, schema_hint=schema_hint, model=model)
    _validate_synthesis_result(result)

    new_rules = result.get("new_rules", []) or []
    supersede = result.get("supersede", []) or []
    tendencies = result.get("tendencies", []) or []

    if promotion_allowed:
        # Step 4a: apply new permanent rules (additive), auto-promote.
        for rule in new_rules:
            rule_id = canon.add_permanent_rule(
                conn, rule["text"], rule["kind"], rule.get("evidence_ids", [])
            )
            new_rule_ids.append(rule_id)
            events.append(
                conn,
                "rule_promoted",
                {
                    "rule_id": rule_id,
                    "rule_text": rule["text"],
                    "kind": rule["kind"],
                    "evidence_ids": rule.get("evidence_ids", []),
                    "undo_note": f"Applied a new rule: {rule['text']}. Tap to undo.",
                },
                article_id=article_id,
            )

        # Step 4b: apply supersessions.
        for s in supersede:
            canon.supersede_rule(conn, s["id"], s["reason"])
            superseded_ids.append(s["id"])
    else:
        events.append(
            conn,
            "synthesis_skipped_promotion",
            {
                "reason": "edit-effort trend is spiking; promotion paused",
                "proposed_new_rules": len(new_rules),
                "proposed_supersede": len(supersede),
            },
            article_id=article_id,
        )

    # Step 4c: provisional tendencies are always rebuilt wholesale, even
    # when promotion is paused.
    conn.execute("DELETE FROM provisional_tendencies")
    for t in tendencies:
        conn.execute(
            "INSERT INTO provisional_tendencies (tendency_text, evidence_event_ids, rebuilt_at) "
            "VALUES (?, ?, ?)",
            (t["text"], json.dumps(t.get("evidence_ids", [])), _now()),
        )
    conn.commit()

    # Step 5: update the synthesis checkpoint.
    _record_checkpoint(conn, max_event_id, len(relevant))

    return {
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


def demote_on_contradiction(conn, rule_id) -> None:
    """Called when an edit contradicts a rule twice - the edit-as-undo
    path. Supersedes the rule (status transition, never deletes)."""
    canon.supersede_rule(
        conn, rule_id, "contradicted by operator edits twice; demoted"
    )
