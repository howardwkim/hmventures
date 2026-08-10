# Call with Mike Grabham — 2026-07-07, 09:30 PDT

**Source:** Google Meet, Howard's personal Drive. Video: "Mike <> Howard - 2026/07/07 09:30 PDT -
Recording". Transcript/notes: "Mike <> Howard - 2026/07/07 09:30 PDT - Notes by Gemini" (Google Doc,
file id `1gV6BsivN1oZ-jIbZ8rrp4eab5YmDX9PDv_3ruCXzhjA`). This file is a synthesis, not a copy — the
Drive doc is the record; pull it again via `google drive export <id> -o <path> -m text/plain` if the
verbatim transcript is needed.

## The bottleneck Mike actually has

Not discovery/sourcing (he said that's fine) and not distribution (already built, already tested
across blog/social/LinkedIn/YouTube/TikTok/X). It's the **Q&A interview step** in his existing
`staff-writer` pipeline: 15–20 minutes per article answering questions to pull his opinion into the
piece. When he already knew the article going in and skipped the questions entirely, the whole thing
took him ~5 minutes end to end.

## Workflow shape agreed on the call

Three decoupled pipeline stages, each with its own queue that can back up independently:

1. **Discovery — async, ahead of time.** Candidate articles delivered the day before, not generated
   on demand. Read/pick happens in idle time, not inside a writing session.
2. **Writing — batched.** Queue up picks, draft them in one sitting (his target: a 90-minute block
   covering a week of content, likely shrinking over time).
3. **The interview — shrinks via an onboarding period.** First ~10 articles: 3 mandatory short
   answers to seed voice/brand/opinion. After that, questions go optional — the system should
   already know.

## Data capture (what makes stage 3 actually shrink)

Two mechanisms discussed on the call, expanded in the follow-up discussion:

- **Decision logger** — every choice (article picked/skipped, Q&A answers, which draft got accepted)
  recorded as structured data.
- **Draft-vs-published diff** — silently diff generated draft against what Mike actually publishes
  (he edits in Beehiiv) to learn his humor/asides/edit patterns without him ever stating them.
- **Not just final outcomes — abandoned/incomplete sessions too.** A candidate read but not written,
  questions started but not finished, are signal as well. This needs a broader event-log capture,
  not just success-path logging.

## Explicitly parked, not in scope for this pipeline

- **Video quality / non-talking-head design tooling** — real problem (talking-head via HeyGen is
  fine; non-talking-head needs a more flexible/consistent-character tool) but sequenced after text:
  "if we get the text right, we have better fuel for the video." Separate track.
- **Multi-channel distribution** — already solved, not being rebuilt here.

## Open questions (unresolved, to hit in the grill-me session)

1. **Rewrite `staff-writer` in place, or build a totally separate command?** Not decided.
2. **Data substrate for the pipeline's structured state** (queues, decisions, diffs, statuses) —
   likely SQL-shaped (filter/status-transition access pattern per this repo's
   `.claude/rules/data-substrate.md`), not markdown. Open question whether this venture reuses the
   `tools/capture` pattern (Postgres, append-only event log, FastAPI + local-overlay UI) already
   built in personal-ai, or gets its own store.
3. **UI**: once the flow is locked, a local-only UI overlay — runs on whoever's machine (Howard's or
   Mike's), reads the structured data the pipeline produces. Not a hosted/shared app.

## Next steps named on the call

- Howard: verify consistent-character support in video-gen tools (parked, not urgent).
- Howard: build the decision logger.
- Mike: push his existing skills/codebase to the `hmventures` GitHub repo — **done same day**,
  commit `ece713c`, landed in `hmventures/docs/miho/` (brand docs + `staff-writer.md` +
  `social-package.md`).
- Mike: run `/insights` over his own conversation history for process recommendations.
