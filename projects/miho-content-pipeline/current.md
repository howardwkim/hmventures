# miho-content-pipeline — Current Status

**Last updated:** 2026-07-17

**Next:**
- Also open: content-discovery has no writing skill to hand off to inside this repo.
  `writing-pipeline` (the staged outline-architecture pipeline) stays in `personal-ai` — too heavy
  to port, and it's coupled to the `ai-writing-quality` pack (style guides, taste ledger, stage
  templates) which isn't moving. `content-pipeline`, the self-contained alternative that used to
  live in this repo, was deleted 2026-07-17 (Howard: it was abandoned mid-evaluation, had serious
  issues, never a real replacement). A lightweight writing skill that lives natively here doesn't
  exist yet — needs its own charter before building.
- 3 unreviewed cards were sitting in the reservoir as of 2026-07-15
  (`~/.content-profiles/miho/reservoir.jsonl`) — check before assuming a fresh run is needed.
- Progress ledger with full task-by-task detail: `.superpowers/sdd/progress.md`.

**Key decisions:**
- **Multiple concurrently-accepted seeds shipped 2026-07-17.** `seed.md` was a single file per
  profile, overwritten on every accept. Fixed to mirror the existing pitch-reservoir pattern:
  each accepted pitch now gets its own `seeds/<pitch_id>.md`, plus a `seeds-queue.jsonl`
  current-state index (accepted, not yet started) and two new events, `seed.written` /
  `seed.consumed`, on `discovery-events.jsonl`. See `references/writing-seed-contract.md` and
  `references/pitch-card-contract.md` in the skill dir; `scripts/validate_state.py` checks the
  new file the same way it already checks the reservoir.
  **One real casualty from the old singleton behavior:** the live MiHO state had accepted two
  pitches — `owner-identity-after-first-real-hire` (2026-07-15) then
  `ada-web-accessibility-lawsuit-compliance-gap` (2026-07-17) — and the second accept had already
  silently overwritten the first's seed content before this fix landed. That was the trigger for
  the full reset below rather than a partial recovery.
- **`~/.content-profiles/miho/` reset to empty 2026-07-17**, on Howard's call, to run
  content-discovery clean against the new seeds-queue contract — no history, reservoir, or seeds
  carried forward. The authored input (`docs/miho/content-profile.md`,
  `docs/miho/reddit-sources.yaml`) is untouched; this only wiped generated state. Next run starts
  from a genuinely empty reservoir/event log.
- **This project (design + architecture + session history) moved here from `personal-ai`
  2026-07-17**, alongside the code (which moved 2026-07-17 earlier the same day — see below).
  `personal-ai/projects/miho-content-pipeline/` is now archive-only: Mike Grabham partner-meeting
  notes and the dead `content-pipeline` skill's build history. This repo is the single place
  content-discovery is developed — design and code together — specifically to stop switching
  between two codebases.
- **`content-pipeline` (the self-contained discover→draft→approve skill that used to live at
  `.claude/skills/content-pipeline/`) was deleted 2026-07-17.** It was abandoned mid-evaluation —
  Howard: "It had serious issues... I realized I needed to do steps one, two, three separately,"
  i.e. its own discovery/ingest/decide loop duplicated what content-discovery does better, and
  the drafted/approved articles it produced during testing weren't a sign it actually worked.
  Deletion is reversible via git history (last commit `0fe1947`) if anything needs recovering.
- **Content-discovery skill moved to `hmventures` 2026-07-17** — was built in `personal-ai` at
  `.claude/skills/content-discovery/`; now lives at `hmventures/.claude/skills/content-discovery/`,
  packaged standalone (the Reddit stealth-fetch dependency is vendored inside the skill at
  `scripts/vendor/scrapling/`, and `config.json` at the skill root makes `state_root` and the
  scrapling tool path operator-configurable).
- **Content-discovery validated end-to-end for real, 2026-07-15** — first genuine run (state
  confirmed empty going in): Reddit researcher fetched/gated/judged live posts, produced 4
  pitches, Howard accepted the top one, seed + state all written and `validate_state.py`-clean.
  See `reference/session-log.md`'s second 2026-07-15 entry.
- **Canonical design is `docs/superpowers/specs/2026-07-14-content-discovery-design.md`.**
  Discovery and writing are separate capabilities: `content-discovery` owns pitch
  sourcing/ranking/state; something else (currently `writing-pipeline` in `personal-ai`, TBD
  going forward) owns drafting and the publishing handoff. MiHO is an external authored profile,
  not a pipeline.
- **Reddit research is deterministic, zero LLM calls** in fetch/parse/dedup/filter — Howard's
  explicit hard requirement. Built on `tools/scrapling` (headless stealth fetch), vendored here.
- **Reservoir has no storage cap** (2026-07-14 decision) — cap removal, not floor removal; the
  3-card warm-session minimum still applies.
- Full session-by-session detail: `reference/session-log.md`.

**Session ref (personal-ai, pre-move):** `claude --resume 673c30f3-1278-456a-b939-dd4896446a69`
