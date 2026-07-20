# Discovery redesign — conversational companion to writing-pipeline

**Date:** 2026-07-13
**Status:** shape agreed, not yet spec'd or built. Supersedes the PRD's Stage 1 design
(`2026-07-07-pipeline-prd.md`, "Stage 1 — Discovery") on the operator-triage question below.

## The pivot

The PRD's discovery stage was a manual triage queue: the system scans and appends
candidates, the operator works the full list top-down (yes/no/snooze), and that
click-through log is what calibrates future scoring. Howard's instinct: that's still
mechanical bookkeeping work he has to manage, and he'd rather not do it — not even in a
lighter form.

**New shape: discovery becomes an agent-owned capability, not an operator-run queue.**
The agent maintains its own trend awareness and surfaces ideas conversationally instead
of handing Howard a stack to review.

## What stays the same

The underlying data model doesn't need to change — same tables the PRD already specs:
candidates with source platform, engagement numbers, topic tags, emotional driver, news
hook, predicted-relevance score, and the decision outcome (accept/reject/snooze) with
calibration tracking (predicted vs. actual).

## What changes

1. **Ownership flips.** The agent scans, scores, dedupes, and refreshes its own trend
   library in the background. Howard never opens a queue or clicks through rows — that
   bookkeeping is the skill's job, not his.
2. **Sourcing is conversational, not a review pass.** A lightweight profile intake
   (what business you're in, what you're good at) plus ongoing back-and-forth. The
   skill proactively pitches topic ideas pulled from its self-maintained trend library,
   tuned to that profile — Howard doesn't initiate discovery, it surfaces on its own.
3. **Interaction style stays structured where possible.** Same texture as the PRD's
   interview mechanic (recommended answer + alternate + free-text override + skip) —
   default to multiple-choice / yes-no prompts, go open-ended only when the question
   genuinely requires it.
4. **The learning signal is conversational reaction, not logged clicks.** How Howard
   responds in conversation refines two things: the taste/profile model, and the
   discovery search targets themselves — what the skill looks for and where it looks
   adapts, not just a relevance score bolted onto a fixed candidate list.
5. **Data stays visible on request, just not operator-managed.** Howard can ask "what's
   trending" or "what have you pitched me" and get it surfaced — the bookkeeping isn't
   hidden, it's just not his to maintain.

## Relationship to writing-pipeline

**Companion skill, not a folded-in stage.** Discovery lives separately from
`writing-pipeline` — it's a different problem shape (continuous scanning + standing
trend memory + conversational surfacing vs. writing-pipeline's one-shot
seed-a-topic-and-produce-gated-prose model). The handoff: a topic that lands from a
discovery conversation becomes the topic / why-this-topic input to a writing-pipeline
`seed.md` run. Discovery feeds writing-pipeline; it isn't absorbed by it.

## Open questions (not yet resolved)

- Exact profile-intake shape (what questions, how deep, one-time vs. revisited).
- How the trend library refreshes (trigger: on-demand when Howard opens a conversation,
  background/scheduled, or both).
- Whether calibration data (predicted-relevance vs. actual reaction) needs any
  structured capture beyond "the skill remembers," or if conversational memory alone is
  sufficient signal over time.
- Where this skill lives (new skill under `.claude/skills/`, likely paired alongside
  `writing-pipeline`) and what it's named.
