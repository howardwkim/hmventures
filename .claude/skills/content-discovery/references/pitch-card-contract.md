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
central signal; `proposed_angle` is a hypothesis; no `runner_up_contrast` field.

## Event envelope

```json
{"schema_version":1,"event":"pitch.created","at":"ISO-8601","pitch_id":"slug","payload":{}}
```

Allowed events: `pitch.created`, `pitch.presented`, `pitch.accepted`, `pitch.passed`,
`pitch.deferred`, `pitch.unresolved`, `pitch.expired`, `pitch.superseded`,
`pitch.reintroduced`, and `refresh.completed`. `pitch.created.payload` contains the full card. Transition events
contain the verbatim reason when supplied, inferred tags, and any eligibility date.

`discovery-events.jsonl` is append-only and canonical. `reservoir.jsonl` contains only
currently available cards, one per line, sorted by descending rank. Validate the full
replacement before atomically rewriting it. A removed pitch remains recoverable from
events and remains part of historical deduplication.
