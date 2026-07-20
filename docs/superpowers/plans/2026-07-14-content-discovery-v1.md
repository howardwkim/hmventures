# Content Discovery V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and forward-test the standalone `content-discovery` skill, its file-native contracts, and the one-time MiHO authored profile.

**Architecture:** A concise canonical skill in `.claude/skills/content-discovery/` orchestrates two independent research agents, serves a profile-scoped JSONL reservoir, records append-only events, and emits a writing seed. The authored profile is an external Markdown input in `hmventures`; runtime state lives under `~/.content-profiles/<profile_id>/`. Claude configuration is canonical and is mirrored to `.agents/` with `codex-sync`.

**Tech Stack:** Claude Code/Codex skills, Markdown contracts, JSONL state, model web search, capture-service Reddit feed, git, skill-creator validation.

## Global Constraints

- Canonical skill location: `.claude/skills/content-discovery/`; never edit `.agents/skills/content-discovery/` first.
- Skill name: `content-discovery`.
- Runtime is file-native. Add no runtime Python, database, scheduler, daemon, or profile-authoring flow. (The test-only validator at `.claude/skills/content-discovery/scripts/validate_state.py` is exempt: forward tests use it to verify state; the discovery runtime never invokes it.)
- External profile minimum: `profile_id`, an identity statement, and at least one discovery anchor.
- Empty optional profile sections contain `Not specified`; the skill treats them as absent.
- State root: `~/.content-profiles/<profile_id>/`.
- `discovery-events.jsonl` is canonical append-only history; `reservoir.jsonl` is a rebuildable ranked projection.
- The orchestrator is the sole state writer. Research agents return results and never edit shared files.
- Warm minimum: three fresh cards. No reservoir cap — keep every card that clears the evidence bar, sorted by descending rank. Present the strongest single card first.
- V1 sources: the current Reddit digest when reachable and model web search. Reddit failure must not block web search.
- Pitch research is commissioning-grade. Article-grade research remains in `writing-pipeline`.
- IDs minted by this work use stable kebab slugs with no random suffix.
- The MiHO profile is a one-time test input generated from existing shared documents, not a discovery feature.
- Do not modify or delete `~/.content-pipeline/`.

---

### Task 1: Scaffold the canonical skill and external contracts

**Files:**
- Create: `.claude/skills/content-discovery/SKILL.md`
- Create: `.claude/skills/content-discovery/agents/openai.yaml`
- Create: `.claude/skills/content-discovery/references/content-profile-contract.md`
- Create: `.claude/skills/content-discovery/references/pitch-card-contract.md`
- Create: `.claude/skills/content-discovery/references/writing-seed-contract.md`

**Interfaces:**
- Consumes: an authored `content-profile.md` path and optional state-root override.
- Produces: the profile/state path rules, pitch/event schemas, and `seed.md` contract used by every later task.

- [ ] **Step 1: Verify the new skill is absent**

Run:

```bash
test ! -e .claude/skills/content-discovery
```

Expected: exit 0. If the path exists, inspect it and stop rather than overwriting unknown work.

- [ ] **Step 2: Initialize the skill with the required skill-creator scaffold**

Run:

```bash
uv run python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/init_skill.py content-discovery \
  --path .claude/skills \
  --resources references \
  --interface 'display_name=Content Discovery' \
  --interface 'short_description=Pitch current, profile-specific content ideas' \
  --interface 'default_prompt=Use $content-discovery with an authored content profile to recommend the strongest current idea and prepare the next session.'
```

Expected: a new `.claude/skills/content-discovery/` containing `SKILL.md`, `agents/openai.yaml`, and `references/`.

- [ ] **Step 3: Replace the generated profile contract with the complete contract**

Write `.claude/skills/content-discovery/references/content-profile-contract.md`:

```markdown
# Content profile contract

Discovery consumes one authored Markdown file. It never creates or edits it.

## Frontmatter

Required:

- `profile_id`: stable kebab slug
- `version`: string
- `authored_at`: ISO date
- `source_documents`: list of paths or source labels

## Body headings

1. Identity
2. Business and offering
3. Target audience
4. Audience problems
5. Expertise and authority
6. Editorial territory
7. Proven angles
8. Exclusions and boundaries
9. Discovery guidance
10. Writing voice and defaults

Only `Identity` plus one of Business and offering, Target audience, Expertise and
authority, or Editorial territory must contain substantive text. Optional empty
sections contain exactly `Not specified`. Treat that marker as absent. Never infer
missing profile facts merely to make the profile look complete.

## Runtime resolution

Default state directory: `~/.content-profiles/<profile_id>/`.
An explicit state-root supplied by the caller overrides the default for tests.
```

- [ ] **Step 4: Write the complete pitch and lifecycle contract**

Write `.claude/skills/content-discovery/references/pitch-card-contract.md`:

```markdown
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
```

- [ ] **Step 5: Write the complete writing-seed contract**

Write `.claude/skills/content-discovery/references/writing-seed-contract.md`:

```markdown
# Discovery to writing seed contract

When a pitch is accepted, write `seed.md` with these headings and fields:

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

The seed is resumable state, not a chat-only handoff. Acceptance writes the seed before
offering to launch `writing-pipeline`. Discovery sources are starting material and must
be revalidated by the writing pipeline.
```

- [ ] **Step 6: Replace `SKILL.md` with the concise contract-first orchestrator**

Write `.claude/skills/content-discovery/SKILL.md`:

```markdown
---
name: content-discovery
description: Find and pitch current, profile-specific content ideas from an authored content profile, using a saved reservoir plus concurrent Reddit and web research. Use when the user asks what to write about, wants current content ideas, asks to run discovery for a profile, or wants an accepted idea handed to writing-pipeline. Not for writing the article itself and not for creating a content profile.
---

# Content discovery

Act as an editorial companion with a point of view. Present one strongest recommendation,
not a queue. While discussing it, prepare the next session's reservoir.

## Inputs

Require an authored content-profile path. Read `references/content-profile-contract.md`
and validate the minimum fields. Resolve state under `~/.content-profiles/<profile_id>/`
unless the caller supplies a test state root. A missing optional section is not a reason
to invent context.

Read `references/pitch-card-contract.md` before reading or writing discovery state.
Only this orchestrator writes `discovery-events.jsonl`, `reservoir.jsonl`, or
`discovery-preferences.md`.

## Start

1. Load the profile, preferences, events, and reservoir.
2. Remove stale cards only by appending `pitch.expired` first.
3. If a fresh card exists, append `pitch.presented` and immediately present the
   highest-ranked card.
4. Concurrently dispatch the Reddit and web researchers described in the research
   references. If no card exists, wait only until the first defensible result is ready,
   present it, and keep replenishing.

Present: title, signal, why now, audience relevance, recommended angle, strongest
evidence, and material uncertainty. Keep it conversational.

## Reactions

- Accept: append `pitch.accepted`, remove from the reservoir, write the seed using
  `references/writing-seed-contract.md`, then ask whether to start writing-pipeline.
- Pass: append `pitch.passed` with verbatim reason and inferred tags, then remove it.
- Later: append `pitch.deferred` with `eligible_after`, then remove it temporarily.
- Unresolved: append `pitch.unresolved` and preserve it below unseen cards.

Ask one clarifying question only when the reason is genuinely ambiguous. Do not ask the
operator to confirm every inferred tag.

## Replenish

Merge successful researcher results. Validate evidence, deduplicate against the entire
event history, and use `pitch.reintroduced` rather than `pitch.created` only when
materially new evidence changes an old pitch's relevance. Rank against the authored
profile plus recent preferences. There is no reservoir cap: keep every card that clears
the evidence bar, sorted by descending rank. Three fresh cards is the warm-session
minimum. One researcher may fail without invalidating the other's results. Preserve the
old reservoir unless the complete replacement validates.

At session end, append `refresh.completed`, atomically replace `reservoir.jsonl`, and
rewrite `discovery-preferences.md` from recent evidence. Never rewrite the authored
profile. Never weaken evidence requirements merely to fill the reservoir.
```

- [ ] **Step 7: Validate the skill scaffold**

Run:

```bash
uv run --with pyyaml python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/content-discovery
```

Expected: `Skill is valid!`

- [ ] **Step 8: Commit**

```bash
git add .claude/skills/content-discovery
git commit -m "feat(content-discovery): define profile, pitch, and seed contracts"
```

---

### Task 2: Add isolated Reddit and web researcher prompts

**Files:**
- Create: `.claude/skills/content-discovery/references/reddit-researcher.md`
- Create: `.claude/skills/content-discovery/references/web-researcher.md`
- Modify: `.claude/skills/content-discovery/SKILL.md`

**Interfaces:**
- Consumes: validated profile text, discovery preferences, historical pitch titles/IDs, and a source location or web-search capability.
- Produces: JSON arrays of complete pitch-card candidates; never writes state.

- [ ] **Step 1: Write the forward-test prompts before the researcher references exist**

Prepare two fresh-agent test prompts:

```text
Use the content-discovery skill at .claude/skills/content-discovery. Act only as the
Reddit researcher using the supplied profile and supplied Reddit rows. Return the
contract JSON and do not write files.
```

```text
Use the content-discovery skill at .claude/skills/content-discovery. Act only as the web
researcher using the supplied profile. Search the web, open supporting sources, return
the contract JSON, and do not write files.
```

Expected before implementation: each agent is blocked because its dedicated reference
does not exist.

- [ ] **Step 2: Write the Reddit researcher reference**

Write `.claude/skills/content-discovery/references/reddit-researcher.md`:

```markdown
# Reddit researcher

You scout and support commissioning ideas from an already-curated Reddit digest.
Receive only: the authored profile, learned discovery preferences, historical pitch
titles/IDs, and digest rows or a read-only digest URL.

Select signals that are current, specific, and relevant to the profile. Follow the
Reddit or external link when needed to verify what happened. Do not treat engagement as
truth. Return a JSON array of complete pitch cards matching `pitch-card-contract.md`.
Set `search_provenance.kind` to `reddit` and preserve the Reddit post ID. Include an
empty array when nothing clears the evidence standard.

Never edit runtime files, mark Reddit items viewed, or submit Reddit verdicts.
```

- [ ] **Step 3: Write the web researcher reference**

Write `.claude/skills/content-discovery/references/web-researcher.md`:

```markdown
# Web researcher

You scout and support current commissioning ideas through targeted web search. Receive
only: the authored profile, learned discovery preferences, and historical pitch
titles/IDs.

Derive focused searches from the available profile anchors. Search current sources,
open the pages you rely on, compare publication dates, and distinguish when an event
happened from when an article was published. Prefer primary sources. Return a JSON array
of complete pitch cards matching `pitch-card-contract.md`; every central signal needs
accessible, dated evidence. Set `search_provenance.kind` to `web` and record the query.
Return an empty array when nothing clears the evidence standard.

Never edit runtime files. Do not perform article-grade thesis research or generate a
multi-angle menu.
```

- [ ] **Step 4: Wire the references into `SKILL.md`**

In the Start section, replace the generic dispatch sentence with:

```markdown
4. Concurrently dispatch two isolated researchers:
   - Read `references/reddit-researcher.md` and dispatch it when a read-only Reddit
     digest is available. On Howard's first test, use
     `https://home-macbook-pro.tail347253.ts.net/capture/reddit/api/posts`.
   - Read `references/web-researcher.md` and dispatch it with the model's web-search
     capability.
   Neither researcher may write shared state. If Reddit is unavailable, continue with
   web results and record the source failure in `refresh.completed`.
```

- [ ] **Step 5: Re-run the two forward-test prompts**

Expected: each fresh agent returns valid JSON cards or an empty array; neither creates
or modifies `reservoir.jsonl`, `discovery-events.jsonl`, or preferences.

- [ ] **Step 6: Revalidate and commit**

```bash
uv run --with pyyaml python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/content-discovery
git add .claude/skills/content-discovery
git commit -m "feat(content-discovery): add Reddit and web research stations"
```

---

### Task 3: Generate the one-time MiHO authored profile

**Files:**
- Create in `hmventures`: `docs/miho/content-profile.md`
- Read only in `hmventures`: `docs/miho/brand/brand-dna.md`
- Read only in `hmventures`: `docs/miho/brand/brand-voice.md`
- Read only in `hmventures`: `docs/miho/brand/icp.md`
- Read only in `hmventures`: `docs/miho/brand/proven-angles.md`

**Interfaces:**
- Produces: a sparse-valid profile with `profile_id: miho`, version `1`, and no runtime or profile-generation behavior.

- [ ] **Step 1: Confirm the source files exist and the profile does not**

Run from `/Users/howardwkim/src/hmventures`:

```bash
test -f docs/miho/brand/brand-dna.md
test -f docs/miho/brand/brand-voice.md
test -f docs/miho/brand/icp.md
test -f docs/miho/brand/proven-angles.md
test ! -e docs/miho/content-profile.md
```

Expected: all commands exit 0.

- [ ] **Step 2: Write the profile from supported source material**

Create `docs/miho/content-profile.md` with:

```markdown
---
profile_id: miho
version: "1"
authored_at: 2026-07-14
source_documents:
  - docs/miho/brand/brand-dna.md
  - docs/miho/brand/brand-voice.md
  - docs/miho/brand/icp.md
  - docs/miho/brand/proven-angles.md
---

# MiHO Partners content profile

## Identity

MiHO Partners creates practical tools and peer-level content for small-business owners.
Its authority comes from Mike Grabham's experience building, advising, and observing
real businesses, not from generic coaching frameworks.

## Business and offering

MiHO provides direct consulting and free content for owners primarily in the $1M–$3M
range. The core mechanism is identifying the specific activity or system that will
unlock the next stage, then giving the owner one useful thing to fix rather than a
large transformation framework.

## Target audience

Owners of roughly $800K–$3M businesses with 5–30 employees: plateaued owners whose
companies depend on them, accidental CEOs still doing the technical work, and owners
ready to grow but unsure which lever to pull.

## Audience problems

- The business cannot operate cleanly without the owner.
- Hiring and delegation create overhead instead of capacity.
- Growth has stalled while hours and operational fires increase.
- Pricing, management, and systems have not caught up with the business.
- AI feels relevant but overwhelming, generic, or overhyped.
- Prior consultants supplied theory or binders rather than one specific useful action.

## Expertise and authority

Mike has run businesses and observed recurring operating patterns across real companies.
MiHO can speak from observed patterns and peer experience. It cannot claim credentials
Mike does not have, universal applicability, revenue guarantees, or specific ROI promises.

## Editorial territory

Owner dependency, operational systems, delegation, hiring, management, capacity,
pricing, margins, practical AI adoption, and the gap between generic business advice
and what operators actually experience.

## Proven angles

Not specified

## Exclusions and boundaries

Avoid generic business listicles, consultant-safe hedging, universal prescriptions,
unsupported performance claims, AI hype, and advice disconnected from a concrete owner
problem. Do not resurrect an angle merely because it is popular.

## Discovery guidance

Prefer a current signal that exposes a recognizable owner problem and supports one
clear, practical point. Favor specificity, an operator-relevant consequence, and a
reason the topic matters now. A broad trend is useful only after it clears MiHO
relevance. Begin with current Reddit signals plus targeted web search; allow actual
accept/pass reasons to refine the beat over time.

## Writing voice and defaults

Peer-level, direct, plainspoken, and willing to take a side. Use short paragraphs and
mixed sentence lengths. Avoid passive voice, hedging, throat-clearing, jargon, em
dashes, and banned consultant language. Blog is the default register; style remains
`recommend` until the writing pipeline selects one. Dry humor may appear deliberately
but never as a setup-punchline joke.
```

- [ ] **Step 3: Validate the profile against the external contract**

Verify the frontmatter and all ten headings exist, `Identity` is nonempty, and at least
one discovery anchor is populated. Confirm `Proven angles` says `Not specified` because
the source file contains only placeholders, not a confirmed angle.

- [ ] **Step 4: Commit in `hmventures`**

```bash
git add docs/miho/content-profile.md
git commit -m "docs(miho): add authored content profile"
```

---

### Task 4: Forward-test cold start, warm start, and state ownership

**Files:**
- Create temporarily: `/tmp/content-discovery-eval/miho/`
- Create: `projects/miho-content-pipeline/reference/2026-07-14-content-discovery-v1-eval.md`
- Mirror generated: `.agents/skills/content-discovery/`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: evidence that the standalone skill works before writing-pipeline integration.

- [ ] **Step 1: Sync the canonical skill into the Codex mirror**

```bash
uv run python .claude/skills/codex-sync/scripts/sync.py skills --only content-discovery --apply
uv run python .claude/skills/codex-sync/scripts/sync.py skills --only content-discovery
```

Expected second command: `content-discovery` has no drift.

- [ ] **Step 2: Prepare a clean test state root**

Create `/tmp/content-discovery-eval/miho/` with empty `reservoir.jsonl` and
`discovery-events.jsonl`, plus:

```markdown
# Discovery preferences

No learned preferences yet.
```

Do not write to `~/.content-profiles/miho/` during this task.

- [ ] **Step 3: Dispatch a fresh-agent cold-start test**

Prompt:

```text
Use $content-discovery with
/Users/howardwkim/src/hmventures/docs/miho/content-profile.md and state root
/tmp/content-discovery-eval. This is a cold start. Use the read-only Reddit feed at
https://home-macbook-pro.tail347253.ts.net/capture/reddit/api/posts plus web search.
Present the first defensible pitch, replenish the reservoir, and stop before accepting
or passing anything.
```

Expected artifacts: a `pitch.created` and `refresh.completed` event, a valid ranked
reservoir, no writes outside the test state, and one strongest pitch in the response.

- [ ] **Step 4: Verify the cold-start artifacts mechanically**

Run the test-only state validator (JSON parsing, event envelopes, complete pitch
cards, rank ordering, and reservoir-matches-event-replay; no reservoir cap):

```bash
python3 .claude/skills/content-discovery/scripts/validate_state.py /tmp/content-discovery-eval/miho
```

Expected: exit 0 with a `state valid` summary; reservoir has at least three cards if
sources produced three defensible ones. Re-run this same command after Steps 5 and 6
to confirm warm-start and failure-isolation runs also leave valid state.

- [ ] **Step 5: Dispatch a fresh-agent warm-start test**

Prompt:

```text
Use $content-discovery with the same MiHO profile and /tmp/content-discovery-eval state.
This is a warm start. Present the saved top card before reporting any new research.
While we discuss it, replenish in parallel. I pass on the first pitch because it is too
generic. Record that reason and show the next strongest card.
```

Expected: the prior top card is presented first, `pitch.presented` and `pitch.passed`
are appended, the passed card leaves the reservoir but remains in event history, and
the next card is shown.

- [ ] **Step 6: Test source failure isolation**

Repeat warm start with an unreachable Reddit URL and working web search. Expected:
existing cards remain available, web results can replenish, and `refresh.completed`
records the Reddit failure without corrupting state.

- [ ] **Step 7: Write the eval record**

Record exact prompts, dates, event counts, reservoir counts, source outcomes, contract
violations, and whether each acceptance condition passed in
`projects/miho-content-pipeline/reference/2026-07-14-content-discovery-v1-eval.md`.

- [ ] **Step 8: Revalidate, commit canonical artifacts, and leave test state uncommitted**

```bash
uv run --with pyyaml python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/content-discovery
git add .claude/skills/content-discovery projects/miho-content-pipeline/reference/2026-07-14-content-discovery-v1-eval.md
git commit -m "test(content-discovery): verify cold and warm reservoir flows"
```

Do not add `.agents/` or `/tmp/content-discovery-eval/`; the mirror and eval state are regenerable.

---

## Plan 1 Completion Gate

Proceed to `2026-07-14-content-discovery-writing-cutover.md` only when:

- The MiHO profile is committed in `hmventures`.
- The canonical skill validates and the Codex mirror has no drift.
- Cold start, warm start, pass history, and source-failure isolation have recorded evidence.
- At least one accepted-quality source-backed card can satisfy the writing-seed contract.
