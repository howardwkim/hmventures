# Discovery to writing seed contract

Accepted pitches form a pipeline, not a single slot: the operator can accept several
before any of them gets written up. Each accepted pitch gets its own seed file — never a
single shared `seed.md` — so accepting pitch B never clobbers pitch A's seed.

When a pitch is accepted, write `seeds/<pitch_id>.md` with these headings and fields:

```markdown
# Assignment seed

**Topic/question:** <accepted topic>
**Surface/register:** <register>
**Who chose the topic:** agent (machine-suggested)
**Profile ID:** <profile_id>
**Profile version:** <version>
**Content profile:** <absolute profile path>
**Originating pitch:** <pitch_id>
**Style:** <profile default or recommend>
**Stop criterion:** ship after ≤2 verdict sessions

## Why this topic
<full commissioning rationale>

## Starting angle
<accepted or conversationally revised provisional angle>

## Discovery evidence
- <URL> — <what it supports>
```

Each seed is resumable state, not a chat-only handoff. Acceptance appends `seed.written`
to `discovery-events.jsonl`, writes the seed file, and adds a row to `seeds-queue.jsonl`
(schema: `references/pitch-card-contract.md`) before offering to start writing it up.
Discovery sources are starting material and must be revalidated by whatever consumes the
seed.

## Multiple outstanding seeds

`seeds-queue.jsonl` is the current-state list of accepted pitches not yet started —
mirrors `reservoir.jsonl`'s role for unreacted pitches. When it's non-empty at the start
of a session, mention the outstanding count before presenting a new pitch; don't let
seeds pile up silently. There's no cap and no forced order — the operator picks which
queued seed to start whenever they're ready.

Discovery has no visibility into a seed once a writing run has actually started (that
run happens in a separate skill/process). A seed leaves the queue only when the operator
tells discovery it's been started — discovery then appends `seed.consumed` and removes
the row. Until the operator says so, an accepted pitch stays in the queue even if it's
actually being worked — that's a known limitation, not a bug: discovery would need a
signal from outside its own state to know otherwise.
