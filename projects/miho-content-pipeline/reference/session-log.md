# Session Log — miho-content-pipeline

## 2026-07-12 — Post-retro path decided: wow-test first, then decisions ledger → re-spec

**Started:** 2026-07-12
**Closed:** 2026-07-12
**Planned:** Invoke `/retro` with the 11 session refs (per prior current.md).
**Actually did:** Discovered the retro had ALREADY run — final five-lens entry in `process/retros.md`
(2026-07-11 heading) + working log at `process/reference/retro-logs/2026-07-11-miho-content-pipeline.md`;
the prior current.md "retro not run yet" line was stale. Howard opened wanting to decide the path
forward (his instinct: scrap everything, re-spec from extracted decisions). Analysis challenged the
premise: the retro's own verdict is the shipped pipeline WORKS end-to-end ("pipeline mechanics held
up — the failure was purely in state-recording"); the 11-session mess was process, not output. Two
strategic issues surfaced and re-ordered the plan (see Key decisions). Also located the actual code:
`~/src/hmventures/.claude/skills/content-pipeline/` (~1,860 lines src + full test suite + 5 stage
prompts in `references/`), NOT `plugins/` as older notes said.
**Left off:** Path agreed; nothing built this session. Step zero (the clean run) not yet set up.
**Key decisions:**
- **Sequence: (0) wow-test → (1) decisions ledger → (2) new spec → (3) build plan.** The clean
  end-to-end run comes FIRST because Howard's only judgment of the experience ("wasn't wowed") was
  taken mid-debug — unreliable. If a clean run doesn't wow, the concept needs rethinking before any
  rebuild; if it does, proceed to ledger → spec with confidence.
- **The UI question is a now-fork, not a later-step.** Howard's standing assumption ("build the
  skill right and programmatic → easy jump to UI") is partly backwards under the agent-native
  architecture: the intelligence (interview/draft/edit/synthesis) lives in the session-bound agent,
  the LEAST portable place for a UI. The new spec must decide: session-bound agent vs. headless
  agent service both skill and UI can call. This fork also subsumes scrap-vs-keep-the-code.
- **Scrap-vs-keep the working code: OPEN**, deliberately deferred until the wow-test + UI fork
  resolve it.
- **Decisions-ledger sources (4), newest thinking is NOT in the oldest doc:** partner-meeting
  decisions Jul 10 (30-min offer, podcast, bronze/silver/gold layer) → PRD Jul 7 + learning-loop
  design Jul 8 (oldest) → shipped code + 5 stage prompts (most evolved — 3 architecture pivots
  post-date all docs and were never written back). Ledger format: every decision deduped, tagged
  keep/revisit/drop, source-stamped; Howard ratifies before any spec is written.
- **Don't redo the retro.** The analysis exists; consume it, don't regenerate it.
**Session ref:** `claude --resume d130acb0-42b4-4762-9e1a-1d745e2e683a`

## 2026-07-11 — Discovered the un-logged build saga; built multi-session /retro tooling and locked scope

**Started:** 2026-07-11
**Closed:** 2026-07-11
**Planned:** N/A — session opened with "is /retro the right skill to analyze what went wrong with the content pipeline build?"
**Actually did:** Discovered `current.md` and `reference/session-log.md` stopped at 2026-07-09 while the real build continued in `~/src/hmventures` through Jul 11 across ~17 more sessions, never logged back here. Built a full session manifest (`reference/session-manifest.md`) covering all of them. Investigated one anomalous 4.5MB session and found it was an unrelated diagram-generation detour (not pipeline work) — used that investigation to validate a transcript-sampling technique, then built it into `/retro` as `scripts/sample_transcript.py` (strips oversized/binary payloads — images, Claude Code's hidden `toolUseResult` field — before any subagent reads a transcript). Redesigned `/retro` for multi-session use: it now accepts multiple past-session refs and, for multi-session runs, spawns an Opus orchestrator that batches sessions using its own judgment, dispatches a Sonnet investigator per session, adapts what it looks for between batches, keeps a working log separate from the final entry, and synthesizes one five-lens entry across the whole arc. Reviewed each of the 17 hmventures sessions (first + follow-up messages) to classify relevance and locked a final 11-session retro scope across 4 narrative beats. Separately, mid-session, consolidated an unrelated fragmentation (operator-assist gate-miss logging routed through its own file, `/feedback`'s log, and productivity's own friction log) into `/feedback` as the one capture surface — logged in `process/current.md`, not this file, since it's a different area's concern.
**Left off:** Tooling and scope are done; the actual retro analysis has not been run. Next session's first move is invoking `/retro` with the 11 refs in `reference/session-manifest.md`.
**Key decisions:**
- The retro orchestrator gets only the 11 raw session refs — no manifest, no beat groupings, no pre-digested narrative from this session. Deliberately blind on content, guided only on method (five lenses, verbatim-quote requirement, batch-and-adapt process).
- Diagram-generation detour session (`34a40fe7`) explicitly excluded from the pipeline retro — Howard set it aside as a separate, unrelated topic (multimodal image-token handling).
- Final 11-session scope: `dbc737c5`, `43b9deae`, `a56c82b5` (personal-ai, already logged) + `a76c2f9c`, `0bc61bb8`, `8070223f`, `0c08ce72`, `1ed39b77`, `e55b36c0`, `c0f27803`, `4d8de1fa` (hmventures). 4 more sessions checked and ruled out as mechanical/procedural with no narrative content.
**Session ref:** `claude --resume 93bc2103-016d-430b-8440-e6126e835ff1`

## 2026-07-09 — Grill-me rejected; agent-native rebuild plan written + Codex-reviewed

**Started:** 2026-07-09
**Closed:** 2026-07-09
**Planned:** Begin the Phase E3 library refactor + 7 gap fixes locked by the prior grill-me session.
**Actually did:** Howard halted the refactor — the build didn't match intent (wanted a Claude Code skill, got a CLI). Audited the PRD, the built code, and interrogated the grill-me session. Found the grill-me refined the *wrong architecture*: both the built pipeline and the grill-me plan use `claude -p` subprocess calls (in `writing.py`/`synthesis.py`/`llm.py`) for the LLM work, when the point of a skill is that the conversational agent does it. Rejected the grill-me plan. Designed an agent-native architecture, wrote a full implementation plan via superpowers:writing-plans, had a Codex subagent review it (verdict: needs revisions), and folded in all 6 findings.
**Left off:** Plan complete and revised at `docs/superpowers/plans/2026-07-09-content-pipeline-agent-native.md` (in personal-ai). No code written yet. Execution option (subagent-driven vs inline) deferred to next session by Howard's call.
**Key decisions:**
- **The grill-me session's architecture is rejected.** Its headline "library refactor" was ~80% already on disk (the modules are already importable; `cli.py` imports them). Its "skill.py in personal-ai `.claude/skills/`" was wrong.
- **Agent-native design.** The skill = `SKILL.md` (agent playbook) + a **deterministic-only CLI** (state + math, no LLM). The agent (Claude in the session) writes interview questions, drafts, edit revisions, and synthesis decisions; the CLI only persists. **No `skill.py` orchestrator, no `claude -p`, delete `llm.py`.**
- **Location: stays in `~/src/hmventures/plugins/content-pipeline/`**, not personal-ai — forced by the PRD self-sufficiency principle (ships in the plugin). Resolves the earlier open where-does-it-live question.
- **4 of 9 audit gaps dissolve** because they only patched the subprocess design (interview-options injection, synthesis JSON validation, synthesis rollback, LLM retry/backoff). Gap 3 (skill.py) reframed to SKILL.md + CLI; gap 9 (real LLM test) reframed to a deterministic backend E2E + a live agent acceptance run.
- **Discovery deferred** — Howard wires his own test data via a new `ingest --json` CLI verb; the reddit adapter is kept but not the default path.
- **The 8 tested deterministic modules** (db, queue, events, canon, selection, health, discovery) are reused unchanged; `writing.py`/`synthesis.py` split into read-context / persist halves.
- **Codex review folded in:** idempotency guard on the synthesis read/apply split (`base_checkpoint`), validator restored to original strictness (evidence_ids required), test harness corrected to the real `_run(capsys, argv)`/`conn` fixtures, supersession test ported, `config.load()` signature fixed, and a `status.synthesis_pending` marker for approved-but-unsynthesized articles.

**Session ref:** `claude --resume a56c82b5-bcdd-48bd-8918-10b87a7bf695`

## 2026-07-09 — Phase 1 Audit & Gap Analysis

**Started:** 2026-07-09  
**Closed:** 2026-07-09  
**Planned:** Analyze Phase 1 gaps; identify what's missing to make the pipeline usable  
**Actually did:** Completed comprehensive codebase audit (Explore agent + manual review). Identified 9 critical gaps: 2 user-facing (no setup, no data ingestion) + 7 code-level (no skill.py, brand context empty, interview options unused, synthesis validation broken, no error recovery, LLM failures not retried, real LLM never tested).  
**Left off:** Audit complete. All gaps documented in `reference/phase1-audit.md`. Next step is grill-me session to design Phase E3 + fixes.  
**Key decisions:** 
- All 9 gaps are blocking (no phased deferral strategy yet)
- Grill-me session will design solutions for all simultaneously before implementation
- Implementation follows design, not vice versa
- Real LLM testing is non-negotiable before ship

**Session ref:** `claude --resume dbc737c5-0f68-4958-a4cc-1daf1d86e79c`

## 2026-07-09 — Phase E3 Grill-Me: Architecture Locked

**Started:** 2026-07-09
**Closed:** 2026-07-09
**Planned:** Grill-me session to design Phase E3 + fixes for the 9 gaps found in the audit
**Actually did:** Ran grill-me across initialization, discovery/data-ingestion scope, and skill orchestration architecture. Corrected two wrong assumptions along the way (see Key decisions) before landing on the final design.
**Left off:** Architecture fully locked and written to `current.md`. No implementation started yet — next session begins the library refactor + gap fixes.
**Key decisions:**
- **Self-sufficiency re-affirmed, but scoped pragmatically for Phase E3:** the pipeline must ultimately work for any operator out of the box with zero dependency on Howard's infrastructure, but Phase E3 uses Howard's Hermes Reddit digest as the discovery source to get the rest of the workflow (review → interview → draft → edit → approve → learning) testable now. Building a real pluggable/general-purpose discovery module is deferred to Phase B2, not folded into E3.
- **Discovery is an evolving concept, not a one-time setup question** — operators will want to add/pause/resume topics over time and that should be logged, but full topic-management commands are out of scope for E3 (single active topic via Hermes digest for now).
- **skill.py lives in `.claude/skills/content-pipeline/`** (a Claude Code skill), not in the `hmventures` package — corrected an initial wrong assumption that it belonged alongside the CLI code.
- **Architecture pivot: library refactor, not CLI-subprocess orchestration.** Phase 1 built a CLI that prints JSON per subcommand assuming the skill would shell out and parse. Decided instead to refactor `content_pipeline` into an importable library that skill.py calls directly — cleaner, faster, and lets the skill hold state across the multi-step interview/edit loops instead of reopening the DB every command. The CLI can remain as a thin test-only wrapper.
- **Operator-facing UX (review list, per-article interview shape, edit-approve loop) is already locked in the PRD** (`reference/2026-07-07-pipeline-prd.md`) — not re-litigated this session; only the implementation-level gaps needed design.
- **Gap-by-gap fixes settled** (full detail in `current.md`): config-driven init (DB path + Hermes digest path + brand context in `~/.content-pipeline/config.json`, invisible to operator), interview options wired into the draft prompt, tighter synthesis validation, deferred approval marking until synthesis succeeds (rollback safety), LLM retry with exponential backoff, and a real E2E test against actual `claude -p`.

**Session ref:** `claude --resume 43b9deae-c11a-4612-8ba9-715f7f6d2a26`

## 2026-07-14 — Reviewed content-discovery spec + both plans, fixed two verification bugs

**Started:** 2026-07-14 (best effort)
**Closed:** 2026-07-14
**Planned:** N/A — session opened cold from an uploaded handoff screenshot (prior agent's
`/tmp/handoff-content-discovery-2026-07-14.md`), not from this project's `current.md` Next
line. `current.md` was stale at open (last touched 2026-07-12/13, pre-redesign).
**Actually did:** Between the 2026-07-13 snapshot below and this session, the discovery
redesign was carried through to a full spec and two implementation plans — evidently in a
separate, unlogged session (see Key decisions). This session read all three documents
(`docs/superpowers/specs/2026-07-14-content-discovery-design.md`,
`docs/superpowers/plans/2026-07-14-content-discovery-v1.md`,
`docs/superpowers/plans/2026-07-14-content-discovery-writing-cutover.md`) and verified them
against the live repo (writing-pipeline anchors exist, MiHO source docs exist, hmventures
untracked files match Plan 2 Task 7's expectations, the Reddit digest feed returns 200).
Verdict: solid — found two real bugs in the plans' *verification commands* (not the
architecture): an inverted `rg -L` isolation check in Plan 2 Task 5 Step 6 that would pass on
contamination and fail on isolation, and a `jq` loop in Plan 1 Task 4 Step 4 whose exit code
only reflects the last JSONL line. Fixed both (commit `733e527d`, on `main`). Also built and
tested a test-only state validator (`.claude/skills/content-discovery/scripts/validate_state.py`,
stdlib-only) that checks JSON parsing, event envelopes/allowed names, complete pitch cards,
reservoir rank ordering and five-card cap, and reservoir-matches-event-replay; wired it into
Plan 1 Task 4 Step 4 in place of the raw jq checks (commit `62a30c32`). Did not execute any
plan task.
**Left off:** Per the handoff screenshot, only Plan 1 / Task 1 was shipped and committed
(`589c1881`) before this session. That status is unchanged — this session only reviewed and
patched the plan documents themselves. Next unexecuted step is still Plan 1 / Task 2.
**Key decisions:**
- **Redesign completed off-log:** the "Discovery redesign (2026-07-13, shape only)" decision
  recorded in the pre-session `current.md` was carried to a full spec and two plans at some
  point between 2026-07-13 and 2026-07-14, but no session logged that work here. The spec
  (`docs/superpowers/specs/2026-07-14-content-discovery-design.md`) is now the canonical
  design, superseding the PRD's discovery section and the shape-only note.
- Plans require `superpowers:subagent-driven-development` (recommended) or
  `superpowers:executing-plans` to execute — stated in both plan files' own headers.
- Reviewed via read + live verification (Bash checks against the repo), not full skill
  execution — no forward tests were run this session.

**Session ref:** `claude --resume 105e0b07-19bb-4ef8-a9d0-d9373d248294`

## 2026-07-14/15 — Plan 1 executed end to end: skill built, forward-tested, reservoir cap removed

**Started:** 2026-07-14 evening (best-effort)
**Closed:** 2026-07-15
**Planned:** Resume at Plan 1 / Task 2, Step 1, using `superpowers:subagent-driven-development`
or `superpowers:executing-plans`, per the prior session's handoff.
**Actually did:** Ran `superpowers:subagent-driven-development` for the rest of Plan 1
(`docs/superpowers/plans/2026-07-14-content-discovery-v1.md`) in this repo (session initially
started in the wrong repo, `hmventures` — corrected once Howard named `personal-ai`). Task 2
(Reddit/web researcher references): the prior session's Task 2 attempt had hung when forward-
test dispatches ran as nested subagents; this session's fix was running those dispatches
directly from the controller instead, which worked with zero hangs for the rest of the plan.
Task 2 shipped (`a52002c2`, review clean). Task 3 (MiHO authored profile, in `hmventures`):
pure transcription of the plan's exact text into `hmventures/docs/miho/content-profile.md`
(commit `0783765`), review clean. Task 4 (forward-testing cold start / warm start / source-
failure isolation): all three dispatches completed live, independently re-verified with
`validate_state.py` rather than trusting agent self-reports (this caught two real problems a
naive run would have missed — see Key decisions). Wrote the eval record
(`reference/2026-07-14-content-discovery-v1-eval.md`, commit `baad9c4f`); task review caught
the record overclaiming on Step 6 (denying corruption that had actually happened), fixed
(commit `f4e4f754`). Reported the surfaced reservoir-capacity defect to Howard rather than
deciding unilaterally; his call was to remove the reservoir cap entirely (commit `f0a3864e`,
review clean). Ran the final whole-branch review (opus): ready to merge with fixes — fixed the
eval record's now-stale cap-removal framing and a validator crash on malformed non-object
cards; three cosmetic Minors logged for Plan 2 rather than fixed (design doc still says "small
reservoir"; its "Representative lifecycle events" list omits `pitch.unresolved`; deferred-card
re-eligibility has no defined return path once `eligible_after` passes).
**Left off:** **Plan 1 is complete** — completion gate met per the eval record's final
assessment. Plan 2 (`docs/superpowers/plans/2026-07-14-content-discovery-writing-cutover.md`,
the writing-pipeline cutover + old-pipeline retirement) has not been started.
**Key decisions:**
- **Nested subagent dispatch was the actual cause of the prior session's Task 2 hang**, not a
  fundamental tooling limitation — running forward-test dispatches directly from the controller
  (this session, throughout Tasks 2 and 4) worked reliably every time. Future sessions on this
  skill's forward tests should keep doing that rather than nesting them inside an implementer
  subagent.
- **Independent re-verification (`validate_state.py`, run by the controller, not trusted from
  agent self-reports) caught two real bugs a naive pass would have missed:** a warm-start test
  agent claimed to "replenish in the background" and then simply stopped (no such thing exists
  for a subagent — the controller re-dispatched to do it synchronously); a source-failure-
  isolation test agent produced a 6-card reservoir that violated the then-current 5-card cap,
  which is what surfaced the capacity-displacement gap in the first place.
- **Reservoir has no storage cap, by Howard's explicit decision** (not the controller's) —
  ranking already orders which card is presented, so storage doesn't need its own ceiling. The
  3-card warm-session minimum is unchanged; this was a cap removal, not a floor removal.
- **The controller's own recovery from the (now-obsolete) cap violation itself broke the
  append-only invariant** (deleted an already-appended `pitch.created` event rather than
  appending a correction) — flagged explicitly in the eval record as contract-violation #3, a
  process lesson that stands regardless of the cap decision: Plan 2 should define a retraction
  event for erroneously-journaled pitches rather than repeat that shortcut.
- Auto-commit cron activity in this repo (no-branches-work-on-main policy) interleaves
  unrelated commits from other concurrent projects into `main` constantly — final whole-branch
  review diffs must be path-scoped (not a raw commit-range diff) or they drown in noise; one
  eval-record edit and one current.md edit this session were swept into generic `auto:` commits
  by that cron before a manual commit could land, which is harmless but explains a couple of
  non-descriptive commit messages in the range.

**Session ref:** `claude --resume d60e1054-40e6-42c9-a81f-ac02a1434c5f`

## 2026-07-15 — Reddit-researcher rebuilt on Scrapling; portability bug fixed

**Started:** 2026-07-15 morning
**Closed:** 2026-07-15 11:25 PDT
**Planned:** Run `/content-discovery` for MiHO as a first real test of the shipped Plan 1 skill.
**Actually did:** First real run surfaced a bug, not a pitch — the reddit-researcher was hardcoded
to a single fixed URL (`references/reddit-researcher.md`), which turned out to be Howard's own
personal Hermes reddit-digest (`~/.hermes/skills/research/reddit-digest/`), configured only for
r/HermesAgent and r/ClaudeCode. It returned zero relevant signal and would break for anyone else
who received this skill. Traced it to the actual endpoint via ssh to home-macbook-pro before
proposing a fix (per working-principles verify-before-building). Rebuilt Reddit access from
scratch: evaluated light (WebSearch/WebFetch — confirmed dead, WebFetch hard-blocks reddit.com
entirely, WebSearch returns zero Reddit results even for generic queries) vs. heavy
(Playwright/nodriver/Steel/Scrapling) tiers; live-tested Scrapling and found its `StealthyFetcher`
(Camoufox, **headless**) clears Reddit's bot-detection block outright — better than the
headed-Playwright-only technique `projects/reddit-data-access/` had previously settled on. Built
`tools/scrapling/` (generic stealth-fetch primitive, three tiers, not Reddit-specific) and
`.claude/skills/content-discovery/scripts/reddit_fetch.py` (Reddit-specific: browse + keyword
search, sort/window levers, post_id dedup, `--exclude-ids` cross-session dedup, and a
detail-fetch stage that pulls real post body + top comments with AutoModerator/stickied
programmatically filtered out — all regex/attribute-based, zero LLM calls in the collection
path). Caught and fixed a real bug during testing: listing rows built permalinks on
`www.reddit.com` (new React app) while the detail parser only understands old.reddit.com's
markup, so body/comment extraction was silently empty until traced. Added a `reddit_sources`
frontmatter field to `docs/miho/content-profile.md` pointing at a sibling
`docs/miho/reddit-sources.yaml` (subreddits/query/sort/window/gate config, schema documented in
new `reddit-sources-contract.md`) so profile and Reddit-targeting changes stay linked. Updated
`projects/web-access/reference/primitives.md` to mark Scrapling wired. Logged feedback
(`process/feedback/log.jsonl`): Scrapling was already named in that catalog from prior research
but never got re-flagged as a contender against the approach actually in production until a bug
forced the look — the catalog shouldn't sit inert like that.
**Left off:** Every piece individually verified working (fetch, sort variants, keyword search,
dedup, exclude-ids, detail-fetch, AutoModerator filtering) via direct CLI runs. One live
end-to-end dispatch through the actual reddit-researcher agent was started to prove the full
skill-level wiring and got interrupted (Howard, for running long) partway through its
per-thread verification pass — not because anything was broken, but because its old instructions
told it to "verify via WebFetch," which is exactly the hard-blocked path; that instruction is
now removed from `reddit-researcher.md` in favor of reading the detail-fetch stage's own
body/comments output. No state was written during that interrupted run — `~/.content-profiles/miho/`
confirmed empty both before and after. Never got a full clean run to completion.
**Key decisions:**
- Reddit config lives in a **sibling YAML file** (`reddit-sources.yaml`), referenced from the
  profile's `reddit_sources` frontmatter field — not baked into profile prose, not in the
  skill's runtime state directory. Howard's call, so profile edits and Reddit-source edits stay
  visibly linked without merging into one file or touching the stable profile contract's core
  schema more than adding one optional field.
- **The whole Reddit collection pipeline must be deterministic — no LLM calls anywhere in
  fetch/parse/dedup/filter.** Judgment (is this a good pitch) is the only place the researcher
  agent's judgment applies, and it now receives already-enriched, already-deduped data. This is
  a hard constraint Howard set explicitly, not just a nice-to-have.
- Cross-session dedup is a two-layer split: post_id dedup within one fetch lives in
  `reddit_fetch.py` itself; "have we already surfaced this exact post before" is the
  **orchestrator's job** (`SKILL.md`, extracting prior Reddit post IDs from
  `discovery-events.jsonl` and passing `--exclude-ids` to the researcher) — deliberately kept
  out of the researcher subagent so it stays deterministic too.
- **Deferred, not built:** auto-exploring new subreddits/search terms beyond the configured set
  when the known-good ones go stale (Howard: real feature, not a one-line change, do later).
  Also deferred: applying the same Scrapling-based technique to replace Howard's own personal
  Hermes reddit-digest's headed-Playwright method — flagged as a good idea but a separate
  system/session, not touched this session.
- `~/.content-profiles/miho/` was wiped once already this session (the first, broken run's
  output) and confirmed empty again at close — genuinely first-time state for the next run.

**Session ref:** `claude --resume 673c30f3-1278-456a-b939-dd4896446a69`

## 2026-07-15 (cont'd) — First real content-discovery run + first writing-pipeline handoff (paused)

**Started:** 2026-07-15 (continuation of the session that rebuilt the Reddit researcher on
Scrapling)
**Closed:** 2026-07-15
**Planned:** Run `/content-discovery docs/miho/content-profile.md` fresh — `~/.content-profiles/miho/`
confirmed empty, first genuine end-to-end run.
**Actually did:** Ran it clean. Reddit researcher (Scrapling-based) fetched 62 posts, gated 39,
detail-fetched 15, judged 4 as on-territory pitches against the MiHO profile. Presented the
top-ranked pitch ("the owner who finally delegated the job she hated") in chat; Howard accepted
it. Wrote the seed per `writing-seed-contract.md`, wrote/validated `discovery-events.jsonl` +
`reservoir.jsonl` (`validate_state.py` passes: 6 events, 3 reservoir cards remaining). Howard then
asked to run the accepted pitch through `writing-pipeline` at its cheapest cost tier
(`bottom`) — that run lives in the `ai-writing-quality` project
(`experiments/miho-first-hire-90-days/run/`), not here, per this project's CLAUDE.md ("What
doesn't belong" — pipeline execution details stay out of this log; see that project's
`current.md` for the full state). It got through brief → material → outline → substance judge →
outline-packet gate, then Howard's review of that gate packet (via `/annotate`) surfaced a
real, higher-priority process defect — the gate format itself is unusably verbose — and the run
is now paused pending a redesign there.
**Left off:** MiHO's content-discovery is validated end-to-end for the first time — this
capability now works for real, not just in test. The reservoir has 3 unreviewed cards left for
next time discovery opens. The accepted piece's writing-pipeline run is parked mid-pipeline
(outline gate never ruled on) until `ai-writing-quality` redesigns the outline-packet-gate
format; don't resume it before then.
**Key decisions:** None new to this project specifically this half — the Reddit-researcher
rebuild decisions from earlier in the session (see the entry above) still stand. The
writing-pipeline process defect and its fix plan are recorded in `ai-writing-quality/current.md`
and `ai-writing-quality/reference/session-log.md`, not duplicated here.
**Session ref:** `claude --resume dff9afb4-8138-40f1-baa0-aa71cca29400`
