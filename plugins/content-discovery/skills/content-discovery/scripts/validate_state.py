#!/usr/bin/env python3
"""Test-only validator for content-discovery state (not part of the runtime flow).

Usage: python3 validate_state.py <state-dir>

Checks a profile state directory (containing discovery-events.jsonl and
reservoir.jsonl) against references/pitch-card-contract.md:

1. Every line in both files parses as JSON.
2. Every event has a valid envelope and an allowed event name;
   pitch.created payloads carry a complete pitch card.
3. Every reservoir row is a complete pitch card, ranks are sorted
   descending, and there are no duplicate pitch_ids. No cap on reservoir size.
4. The reservoir matches a replay of the event log: exactly the pitches
   that are currently available, no dropped history and no ghosts.
5. seeds-queue.jsonl (optional; absent counts as empty) has no duplicate
   pitch_ids and matches a replay of the event log: exactly the accepted
   pitches with a seed.written and no later seed.consumed.

Exit 0 when valid; exit 1 with one line per violation otherwise.
"""

import json
import sys
from pathlib import Path

ALLOWED_EVENTS = {
    "pitch.created", "pitch.presented", "pitch.accepted", "pitch.passed",
    "pitch.deferred", "pitch.unresolved", "pitch.expired", "pitch.superseded",
    "pitch.reintroduced", "seed.written", "seed.consumed", "refresh.completed",
}
CARD_FIELDS = {
    "schema_version", "pitch_id", "profile_id", "title", "signal_summary",
    "why_now", "audience_relevance", "proposed_angle", "evidence",
    "search_provenance", "freshness", "ranking", "uncertainties", "created_at",
}
EVIDENCE_FIELDS = {"url", "source", "published_at", "supports"}
MAKES_AVAILABLE = {"pitch.created", "pitch.reintroduced"}
REMOVES = {"pitch.accepted", "pitch.passed", "pitch.deferred",
           "pitch.expired", "pitch.superseded"}
QUEUES_SEED = {"seed.written"}
DEQUEUES_SEED = {"seed.consumed"}


def load_jsonl(path, errors):
    rows = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append((i, json.loads(line)))
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}:{i}: invalid JSON ({e.msg})")
    return rows


def check_card(card, where, errors):
    if not isinstance(card, dict):
        errors.append(f"{where}: card must be a JSON object")
        return
    missing = CARD_FIELDS - card.keys()
    if missing:
        errors.append(f"{where}: card missing fields: {', '.join(sorted(missing))}")
    if "runner_up_contrast" in card:
        errors.append(f"{where}: forbidden field runner_up_contrast")
    evidence = card.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{where}: evidence must be a non-empty array")
    else:
        for j, row in enumerate(evidence):
            miss = EVIDENCE_FIELDS - row.keys() if isinstance(row, dict) else EVIDENCE_FIELDS
            if miss:
                errors.append(f"{where}: evidence[{j}] missing: {', '.join(sorted(miss))}")
    ranking = card.get("ranking")
    if not (isinstance(ranking, dict) and isinstance(ranking.get("score"), (int, float))
            and ranking.get("rationale")):
        errors.append(f"{where}: ranking needs numeric score and rationale")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    state = Path(sys.argv[1]).expanduser()
    events_path = state / "discovery-events.jsonl"
    reservoir_path = state / "reservoir.jsonl"
    queue_path = state / "seeds-queue.jsonl"
    errors = []
    for p in (events_path, reservoir_path):
        if not p.exists():
            sys.exit(f"missing file: {p}")

    events = load_jsonl(events_path, errors)
    reservoir = load_jsonl(reservoir_path, errors)
    queue = load_jsonl(queue_path, errors) if queue_path.exists() else []

    available = set()
    queued = set()
    for i, ev in events:
        where = f"{events_path.name}:{i}"
        name = ev.get("event")
        if name not in ALLOWED_EVENTS:
            errors.append(f"{where}: unknown event {name!r}")
            continue
        if ev.get("schema_version") != 1:
            errors.append(f"{where}: schema_version must be 1")
        if not ev.get("at"):
            errors.append(f"{where}: missing at timestamp")
        pid = ev.get("pitch_id")
        if (name.startswith("pitch.") or name.startswith("seed.")) and not pid:
            errors.append(f"{where}: {name} event missing pitch_id")
            continue
        if name == "pitch.created":
            check_card(ev.get("payload") or {}, where, errors)
        if name in MAKES_AVAILABLE:
            available.add(pid)
        elif name in REMOVES:
            available.discard(pid)
        if name in QUEUES_SEED:
            queued.add(pid)
        elif name in DEQUEUES_SEED:
            queued.discard(pid)

    seen, prev_score = set(), None
    for i, card in reservoir:
        where = f"{reservoir_path.name}:{i}"
        check_card(card, where, errors)
        if not isinstance(card, dict):
            continue
        pid = card.get("pitch_id")
        if pid in seen:
            errors.append(f"{where}: duplicate pitch_id {pid}")
        seen.add(pid)
        score = (card.get("ranking") or {}).get("score")
        if isinstance(score, (int, float)):
            if prev_score is not None and score > prev_score:
                errors.append(f"{where}: reservoir not sorted by descending rank")
            prev_score = score
    ghosts = seen - available
    dropped = available - seen
    if ghosts:
        errors.append(f"reservoir has pitches the event log says are unavailable: {', '.join(sorted(ghosts))}")
    if dropped:
        errors.append(f"event log says these pitches are available but reservoir lacks them: {', '.join(sorted(dropped))}")

    queue_seen = set()
    for i, row in queue:
        where = f"{queue_path.name}:{i}"
        if not isinstance(row, dict):
            errors.append(f"{where}: row must be a JSON object")
            continue
        pid = row.get("pitch_id")
        if not pid or not row.get("seed_path") or not row.get("accepted_at"):
            errors.append(f"{where}: needs pitch_id, seed_path, accepted_at")
        if pid in queue_seen:
            errors.append(f"{where}: duplicate pitch_id {pid}")
        queue_seen.add(pid)
    queue_ghosts = queue_seen - queued
    queue_dropped = queued - queue_seen
    if queue_ghosts:
        errors.append(f"seeds-queue has pitches the event log says are consumed or never seeded: {', '.join(sorted(queue_ghosts))}")
    if queue_dropped:
        errors.append(f"event log says these pitches have an outstanding seed but the queue lacks them: {', '.join(sorted(queue_dropped))}")

    if errors:
        print("\n".join(errors))
        sys.exit(1)
    print(f"state valid: {len(events)} events, {len(reservoir)} reservoir cards, {len(queue)} queued seeds")


if __name__ == "__main__":
    main()
