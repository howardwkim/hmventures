# Pitch card and discovery-state contract

## Pitch card

Every `pitch.created` event and active reservoir row uses:

```json
{
  "schema_version": 1,
  "pitch_id": "stable-kebab-slug",
  "profile_id": "miho",
  "title": "One editorial recommendation",
  "signal_summary": "What changed or became salient.",
  "why_now": "Why this is timely now.",
  "audience_relevance": "Why this profile's audience should care.",
  "proposed_angle": "One provisional angle, not a menu.",
  "evidence": [
    {
      "url": "https://example.com/source",
      "source": "Publisher or r/subreddit",
      "published_at": "2026-07-14",
      "supports": "The precise signal this source supports"
    }
  ],
  "search_provenance": {"kind": "web", "query_or_ref": "query text"},
  "freshness": {"review_after": "2026-07-21", "reason": "time-sensitive signal"},
  "ranking": {"score": 0.84, "rationale": "Short comparative rationale"},
  "uncertainties": [],
  "created_at": "2026-07-14T12:00:00-07:00"
}
```

Requirements: at least one accessible, dated evidence row; evidence must support the
central signal; `proposed_angle` is a hypothesis; no `runner_up_contrast` field. A claim
generalizing beyond the source (that a behavior is common or recurring) is marked
inference ("suggests…"), not asserted, and carries its artifact inline — a short verbatim
quote — inside `signal_summary`; the source URL is its `evidence` row.

## What the operator sees

A compressed subset, thesis stated once: **title**, **Signal** (`signal_summary` + the
evidence URL inline; genuine urgency stated as fact here), **Angle** (`proposed_angle`),
and **The catch** (`uncertainties`). Surface `audience_relevance` only when the fit isn't
obvious. `why_now`, `ranking`, `freshness`, `search_provenance`, and the evidence
`supports` prose are never surfaced.

## Event envelope

```json
{"schema_version":1,"event":"pitch.created","at":"ISO-8601","pitch_id":"slug","payload":{}}
```

Allowed events: `pitch.created`, `pitch.presented`, `pitch.accepted`, `pitch.passed`,
`pitch.deferred`, `pitch.unresolved`, `pitch.expired`, `pitch.superseded`,
`pitch.reintroduced`, `seed.written`, `seed.consumed`, and `refresh.completed`.
`pitch.created.payload` contains the full card. Transition events contain the verbatim
reason when supplied, inferred tags, and any eligibility date. `seed.written.payload` is
`{"seed_path": "seeds/<pitch_id>.md"}`; `seed.consumed` has no required payload.

`discovery-events.jsonl` is append-only and canonical. `reservoir.jsonl` contains only
currently available cards, one per line, sorted by descending rank. Validate the full
replacement before atomically rewriting it. A removed pitch remains recoverable from
events and remains part of historical deduplication.

## Seeds queue

`seeds-queue.jsonl` contains only accepted pitches not yet started, one per line, in
acceptance order:

```json
{"schema_version":1,"pitch_id":"slug","seed_path":"seeds/slug.md","accepted_at":"ISO-8601"}
```

A row is added when `seed.written` is appended and removed when `seed.consumed` is
appended for that `pitch_id`. Same atomic-replace discipline as `reservoir.jsonl`.
