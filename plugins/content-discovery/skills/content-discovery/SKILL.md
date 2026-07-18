---
name: content-discovery
description: Find and pitch current, profile-specific content ideas from an authored content profile, using a saved reservoir plus Reddit research (web research is paused — see Start). Use when the user asks what to write about, wants current content ideas, asks to run discovery for a profile, or wants an accepted idea handed off as a writing seed. Not for writing the article itself and not for creating a content profile.
---

# Content discovery

Act as an editorial companion with a point of view. Present one strongest recommendation,
not a queue. While discussing it, prepare the next session's reservoir.

## Inputs

Require an authored content-profile path. If the operator doesn't name one and
`profiles/` (sibling to this file) contains exactly one profile, use it as the default
without asking — that's the bundled team profile, not a placeholder. If it contains more
than one, ask which. Read `references/content-profile-contract.md`
and validate the minimum fields. Read `config.json` at this skill's root for `state_root`
(default `~/.content-profiles` if the file or key is absent — expand `~` and resolve
relative paths against the skill root) and resolve state under
`<state_root>/<profile_id>/`, unless the caller supplies a test state root. A missing
optional section is not a reason to invent context.

This skill is self-contained: the Reddit stealth-fetch tool it depends on ships vendored
at `scripts/vendor/scrapling/`, also overridable via `config.json` (`scrapling_project`).
An operator running this skill on a different machine only needs to edit `config.json` —
no other file should need path changes.

Read `references/pitch-card-contract.md` before reading or writing discovery state.
Only this orchestrator writes `discovery-events.jsonl`, `reservoir.jsonl`,
`discovery-preferences.md`, `seeds-queue.jsonl`, or files under `seeds/`.

## Setup (once per machine)

Reddit research needs `uv` on PATH — nothing else to install by hand; `uv` manages its own
Python, so it doesn't matter whether the operator already has Python installed. If `uv
--version` fails, stop and tell the operator to install it, then wait:
- Windows (PowerShell): `irm https://astral.sh/uv/install.ps1 | iex`
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Before the first Reddit fetch ever run on a machine, prime the vendored stealth-fetch tool's
browser binary once: `uv run --project scripts/vendor/scrapling scrapling install`. Run this
proactively the first time this skill dispatches Reddit research in a session — don't wait
for a fetch to fail first. If a fetch ever does fail with a browser-not-found or
Camoufox-related error, run this command and retry once before reporting the failure.

## Start

1. Load the profile, preferences, events, reservoir, and seeds queue.
2. If the seeds queue is non-empty, mention the outstanding count (accepted pitches not
   yet started) before presenting anything new — see
   `references/writing-seed-contract.md`. Don't block on it; the operator may ignore it
   and keep browsing.
3. Remove stale cards only by appending `pitch.expired` first.
4. If a fresh card exists, append `pitch.presented` and immediately present the
   highest-ranked card.
5. Dispatch research. **Web-researcher is paused as of 2026-07-15 — Reddit-only until
   re-enabled.** Do not read or dispatch `references/web-researcher.md` while paused.
   - Read `references/reddit-researcher.md` and dispatch it when the profile has a
     `reddit_sources` field (see `references/content-profile-contract.md` and
     `references/reddit-sources-contract.md`). No field, no Reddit research — this is
     optional per profile, not a default every profile gets. Before dispatch, pull
     every Reddit post ID already used in this profile's `discovery-events.jsonl`
     (`search_provenance.kind == "reddit"`, its `query_or_ref` is the post ID) — plain
     data extraction, no judgment — and hand it to the researcher as `--exclude-ids` so
     it never re-fetches-and-re-judges a thread already surfaced in an earlier session.
   The researcher may not write shared state. If Reddit is unavailable (or the profile
   has no `reddit_sources`), record the source status in `refresh.completed` — there is
   no web fallback while web-researcher is paused.
   If no card exists, wait only until at least 3 cards clear the evidence bar (the
   Replenish section's warm-session minimum) or every currently-dispatched researcher
   has returned, whichever comes first — then rank and present the single
   highest-ranked card. Do not block presentation on a researcher that isn't needed to
   reach that count. Anything still in flight past that point (a slower researcher,
   or any later-dispatched follow-up) keeps running and merges into the reservoir
   silently whenever it lands — it never delays or interrupts the present operator
   interaction, and it's surfaced only when next needed: the next pass/defer/accept in
   this session, or the next time discovery opens. **Never narrate the dispatch,
   fetch, merge, or ranking process to the operator** — no progress updates, no
   reservoir counts, no source-status notes, no mention of researchers by name. The
   operator sees only the Present template below, and nothing else, until they react.

Present: title, signal, angle, and the catch — the operator-facing subset defined in
`references/pitch-card-contract.md` (audience relevance only when the fit isn't obvious).
Keep it conversational.

## Reactions

- Accept: append `pitch.accepted`, remove from the reservoir, write the seed and queue
  row using `references/writing-seed-contract.md` (`seed.written`), then ask whether to
  write it up now or keep reviewing more pitches. Choosing to keep reviewing re-enters
  this loop: present the next highest-ranked reservoir card (Start step 4) and continue
  reacting. Accepting again before an earlier seed is started is fine — it queues, it
  never overwrites.
- Pass: append `pitch.passed` with verbatim reason and inferred tags, then remove it.
- Later: append `pitch.deferred` with `eligible_after`, then remove it temporarily.
- Unresolved: append `pitch.unresolved` and preserve it below unseen cards.

Any question put to the operator lays out its options explicitly: a multiple-choice
question labels each option A., B., C., etc.; a binary question states it as y/n (or the
equivalent two words, e.g. write-now/keep-reviewing). Never leave the choice implicit in
prose.

Ask one clarifying question only when the reason is genuinely ambiguous. Do not ask the
operator to confirm every inferred tag.

## Replenish

Merge successful researcher results. Validate evidence, deduplicate against the entire
event history, and use `pitch.reintroduced` rather than `pitch.created` only when
materially new evidence changes an old pitch's relevance. Rank against the authored
profile plus recent preferences. There is no reservoir cap: keep every card that clears
the evidence bar, sorted by descending rank. Three fresh cards is the warm-session
minimum. One researcher may fail without invalidating another's results. Preserve the
old reservoir unless the complete replacement validates. This entire step is silent —
it produces state, not conversation; nothing here reaches the operator.

At session end, append `refresh.completed`, atomically replace `reservoir.jsonl`, and
rewrite `discovery-preferences.md` from recent evidence. Never rewrite the authored
profile. Never weaken evidence requirements merely to fill the reservoir.
