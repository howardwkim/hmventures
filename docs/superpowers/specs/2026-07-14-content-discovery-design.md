# Content Discovery — Design Specification

**Date:** 2026-07-14
**Status:** Approved design
**Origin:** `projects/miho-content-pipeline/`
**First profile:** MiHO Partners
**Downstream consumer:** `writing-pipeline`

## Summary

Build a general, on-demand `content-discovery` skill that behaves like an editorial
companion. It opens with its strongest prepared idea, learns from the operator's
conversational reaction, and replenishes a small reservoir of source-backed pitches
while the conversation continues.

Discovery and writing remain separate capabilities:

```text
external authored profile
          │
          ▼
content-discovery ──accepted pitch / seed──▶ writing-pipeline
          │                                      │
          ▼                                      ▼
profile-scoped discovery state          publishing handoff
```

MiHO is an external content profile consumed by both capabilities, not a pipeline or
dispatcher. Once this replacement proves the end-to-end path, retire the existing
MiHO `content-pipeline` implementation rather than preserving two overlapping writing
systems.

## Goals

- Give the operator a useful, opinionated topic recommendation immediately on every
  warm invocation.
- Prepare future recommendations during the current invocation without requiring an
  always-on service, scheduler, or installation beyond the skill itself.
- Keep discovery research separate from article research while reusing discovery
  evidence as writing-pipeline input.
- Learn from ordinary conversation without recreating an operator-managed review
  queue or calibration form.
- Keep authored profile context separate from learned runtime state.
- Isolate every learned signal by profile so MiHO, test runs, and unrelated writing
  surfaces cannot contaminate one another.
- Preserve an inspectable history of every pitch and its lifecycle even after it
  leaves the active reservoir.
- Make the first implementation simple and file-native while preserving a stable
  contract for later deterministic tooling.

## Non-goals

- Creating, interviewing for, or maintaining authored content profiles.
- Scheduled or always-on discovery.
- Publishing or social-distribution execution.
- Migrating the old content-pipeline database or test-generated learning state.
- Generalizing the first implementation beyond the Reddit digest and model web
  search.
- Building a programmatic state engine in v1.

A future profile-authoring skill may produce the same profile contract. Publishing
and distribution may consume the handoff contract defined here. Neither capability
belongs inside `content-discovery`.

## System boundaries

### `content-discovery` owns

- Loading and validating an external content profile.
- Loading the profile's current pitch reservoir and discovery preferences.
- Presenting the strongest prepared pitch first.
- Conducting the topic conversation.
- Dispatching independent Reddit and web research agents during the conversation.
- Validating, deduplicating, ranking, and persisting returned pitches.
- Recording pitch lifecycle events and conversational reactions.
- Updating the learned discovery-preference projection.
- Creating a writing seed when the operator accepts a pitch.

### `writing-pipeline` owns

- Brief development and pushback.
- Thesis-specific material gathering and fact verification.
- Outline creation and substance judgment.
- Drafting, cutting, style checking, revision, and final review.
- Profile-scoped editorial learning.
- Producing the approved final artifact and publishing handoff.

### Publishing and distribution own

- Consuming the approved output package.
- Publishing, scheduling, or adapting the piece for channels.
- Recording publication-specific state and outcomes.

## External content-profile contract

Discovery requires the path to one structured Markdown profile. The profile is an
external input, not something discovery creates or modifies.

### Format

```text
content-profile.md
  YAML frontmatter
    profile_id
    version
    authored_at
    source_documents

  Markdown sections
    Identity
    Business and offering
    Target audience
    Audience problems
    Expertise and authority
    Editorial territory
    Proven angles
    Exclusions and boundaries
    Discovery guidance
    Writing voice and defaults
```

The contract is sparse-tolerant. Only these values are required:

1. `profile_id`
2. A short identity statement describing who or what the content represents
3. At least one discovery anchor among audience, offering, expertise, or editorial
   territory

All other sections may contain `Not specified`. The skill treats that value as absent,
does not invent missing context, and lowers ranking confidence when relevant profile
information is unavailable.

### MiHO test profile

The profile-generation capability is out of scope, but the system needs a real input
for testing. Generate one MiHO profile manually, once, from these existing authored
documents in `hmventures`:

- `docs/miho/brand/brand-dna.md`
- `docs/miho/brand/brand-voice.md`
- `docs/miho/brand/icp.md`
- `docs/miho/brand/proven-angles.md`

The generated profile lives in `hmventures`, is versioned and shared, and records its
source documents. Populate only what those sources support. Do not add a profile
interview, automatic synchronization, or unsupported inference to make the profile
appear complete.

## File-native runtime state

Authored profile context is shared and versioned. Learned runtime state is local,
profile-scoped, and explicitly exportable. Resolve it under:

```text
~/.content-profiles/<profile_id>/
  reservoir.jsonl
  discovery-events.jsonl
  discovery-preferences.md
  editorial-ledger.jsonl
  editorial-taste.md
  runs/
```

### Canonical history and current projection

`discovery-events.jsonl` is the canonical append-only history. The event that first
creates a pitch contains the complete pitch card. Later events refer to its stable
`pitch_id` and preserve the reason for every transition.

Representative lifecycle events:

```text
pitch.created
pitch.presented
pitch.accepted
pitch.passed
pitch.deferred
pitch.expired
pitch.superseded
pitch.reintroduced
refresh.completed
```

`reservoir.jsonl` is the active shelf: one currently available pitch per line, ordered
by rank. It is a replaceable materialized projection, not history. Acceptance, passing,
deferral, expiry, supersession, or deduplication can remove a pitch from the reservoir
without deleting any historical record. The reservoir must be rebuildable from the
event log.

Rewrite the reservoir atomically only after validating the complete new projection.
Research subagents never write shared state. They return results to the orchestrator,
which is the sole writer.

### Learned projections

`discovery-preferences.md` is the current learned view of the operator's discovery
taste. `editorial-taste.md` is the corresponding writing-taste projection consumed by
`writing-pipeline`. The two JSONL files remain the auditable source histories.

Learned projections never rewrite the authored content profile. Moving accumulated
MiHO intelligence to another operator is an explicit export/import of the `miho`
runtime directory; nothing silently syncs or becomes shared authored truth.

## Pitch-card contract

A source-backed pitch card contains enough evidence to justify commissioning a piece,
not enough research to draft the article.

```text
pitch_id                 stable kebab slug
profile_id
title
signal_summary
why_now
audience_relevance
proposed_angle           one provisional editorial recommendation
evidence[]               URL, source, date, and what the source supports
search_provenance        Reddit item or web query
freshness                expiry or review date
ranking                  score plus short rationale
uncertainties[]
created_at
```

Every card makes one editorial recommendation. Discovery may revise it through the
conversation, but it does not present an angle menu by default.

The originally considered `runner_up_contrast` field is explicitly dropped from v1.

## Commissioning research versus article research

Discovery research answers:

> Is this topic worth commissioning for this profile now?

It establishes what happened, why it is timely, why the audience may care, which angle
looks promising, and what credible evidence supports the recommendation.

Writing-pipeline research answers:

> Can we build and defend the chosen piece from a specific thesis?

It gathers material against the developed brief, tests whether examples instantiate
the claims, verifies facts, and closes thesis-specific gaps.

The accepted pitch and its sources become starting material for writing. They are not
treated as complete or pre-verified article research. Brief development may change the
provisional angle, and material gathering must validate the discovery sources before
relying on them.

## Invocation flow

### Warm invocation

1. Load and validate the external profile.
2. Load its reservoir and learned discovery preferences.
3. Check the top card's evidence freshness.
4. Immediately present the strongest fresh pitch.
5. Concurrently dispatch:
   - one agent to mine the existing Reddit digest and return source-backed pitch cards;
   - one agent to perform targeted web searches and return source-backed pitch cards.
6. Continue the pitch conversation while those agents work.
7. Merge successful results, validate them, deduplicate against all historical pitches,
   rank them, and replenish the reservoir with every card that clears the evidence bar.
8. Persist completed events and the valid replacement reservoir before ending the
   discovery session.

The source agents both scout and support their own pitches. Do not create a separate
deep-research fan-out in v1. Add that separation only if real use shows the returned
cards are routinely under-supported.

### Cold invocation

With no usable reservoir, start both searches synchronously. Present the first
defensible pitch as soon as it clears validation, then continue research toward the
three-card minimum.

This warm-up is honest and unavoidable. Do not assume a pre-populated Reddit cache on a
new operator's machine, ship manually seeded topical cards, or use unsupported model
knowledge as if it were current research.

### Reservoir targets

- Minimum ready at warm invocation: 3 fresh, fully formed cards
- No storage cap: every card that clears the evidence bar and hasn't resolved (accepted,
  passed, deferred, superseded) or gone stale (`pitch.expired`) stays in the reservoir
- Presentation default: strongest single pitch, sorted by descending rank
- Additional choices: show only when requested or after the first pitch is declined

## Conversational reactions and learning

The operator does not work a queue or complete a calibration form. Capture ordinary
conversation as:

- `accept`
- `pass`
- `later`
- `unresolved`
- verbatim reason when stated
- inferred signals such as topic, angle, source, timeliness, and audience fit

Ask one brief clarifying question only when the reason is genuinely ambiguous. Do not
ask the operator to confirm every inferred tag. Keep the event history inspectable and
correctable.

Lifecycle behavior:

- `accept`: remove from the reservoir, record the reaction, create a writing seed, and
  ask whether to start writing now.
- `pass`: remove and preserve the stated or inferred reason.
- `later`: remove temporarily and record a future eligibility date.
- `unresolved`: keep available below unseen pitches.

At session end, update `discovery-preferences.md` from recent evidence. This projection
guides later searches and ranking. Search begins broadly in v1—current Reddit signals
plus targeted web search, filtered through the authored profile. Actual reactions can
gradually refine topics, sources, and search targets toward a more beat-driven model.

## Writing-pipeline handoff

When the operator accepts a pitch, discovery creates a valid `seed.md` containing:

- Topic
- Surface/register
- `chosen_by: agent`
- Full `why_this_topic` rationale
- Accepted or conversationally revised angle
- Source-backed discovery evidence
- Content-profile ID and version
- Originating `pitch_id`

Discovery then asks whether to start the writing run. It does not create a separate
operator-managed “ready to write” queue. If the operator stops, the accepted event and
seed remain available for resumption.

Writing-pipeline must:

1. Freeze the relevant authored profile inputs and learned-taste snapshot into the run.
2. Treat the proposed angle as a starting hypothesis.
3. Develop and stress-test the brief.
4. Reuse discovery evidence as initial material while verifying it independently.
5. Keep editorial rulings under the originating `profile_id`.

MiHO rulings append to `~/.content-profiles/miho/editorial-ledger.jsonl`, and the current
projection lives at `editorial-taste.md`. Test runs and unrelated profiles never write
to those files.

## Publishing handoff

Every completed writing run emits:

```text
final.md
publishing-handoff.json
```

The handoff includes:

- Profile ID and version
- Title and slug
- Summary or excerpt
- Originating pitch ID
- Final artifact path
- Approved status and completion date
- Register-specific publishing metadata

Publishing and social-distribution tools consume this package. They are separate
clients and remain out of scope here.

## Failure handling

- A replenishment failure never empties or corrupts the existing valid reservoir.
- Research agents succeed independently; one failure does not discard another's valid
  cards.
- A pitch enters the reservoir only when it satisfies the schema and has accessible,
  dated evidence supporting its central signal.
- Before presentation, expire a stale card through a recorded event rather than silently
  deleting it.
- Validate a complete reservoir projection before atomically replacing the prior file.
- An interrupted session preserves the prior reservoir and every event already appended.
- If cold-start research finds no defensible pitch, report that result instead of
  weakening the evidence standard or fabricating an idea.
- Give every persisted schema an explicit version so deterministic tooling can migrate
  it later.

Freshness attaches to underlying evidence, not merely card creation time. Durable
topics can remain viable longer; news-hook pitches expire quickly. A previously removed
idea may be reintroduced only through a recorded event when materially new evidence
changes its relevance.

## Skill shape and progressive disclosure

Keep `SKILL.md` concise. Its frontmatter description should trigger on requests such as:

- “What should we write about?”
- “Run content discovery for this profile.”
- “Pitch me a content idea.”
- “Find current topics for MiHO.”

The skill body contains only the orchestration flow, stopping points, state ownership,
and instructions for dispatching research agents. Put detailed contracts in one-level
references loaded when needed:

```text
content-discovery/
  SKILL.md
  references/
    content-profile-contract.md
    pitch-card-contract.md
    writing-seed-contract.md
```

No scripts are required in v1. Research and relevance remain agent judgment; the
orchestrator performs file-native bookkeeping.

## V2 deterministic boundary

Move work into a programmatic helper when real usage validates the file contract.
Candidates include:

- Schema validation
- URL normalization
- Exact and fuzzy deduplication
- Freshness calculation
- Lifecycle transitions
- Reservoir reconstruction
- Atomic persistence
- State migrations

Agents should eventually own only search, source interpretation, relevance judgment,
synthesis, and conversational reaction interpretation. This is deferred deliberately;
v1 first validates the workflow and the state shapes the helper will automate.

## Verification

### Contract and state checks

- Load a sparse but valid profile.
- Reject a profile missing the minimum identity/anchor contract.
- Rebuild the active reservoir from discovery events.
- Preserve complete history after accept, pass, later, expiration, and supersession.
- Deduplicate against removed historical pitches, not only active cards.
- Reintroduce a pitch only after materially new evidence.
- Preserve the prior reservoir after partial research-agent failure or interrupted
  replenishment.

### Workflow checks

- Cold start produces a defensible first pitch and builds the initial reservoir.
- The next invocation presents a saved card before new searches complete.
- Reddit and web agents each return source-backed cards under the same contract.
- Conversational reactions alter later preference projections and ranking.
- Accepting a pitch creates a valid writing seed.
- A MiHO seed completes a writing-pipeline run and emits a valid publishing handoff.

### Isolation checks

- MiHO discovery events and editorial rulings remain under `profile_id: miho`.
- A test profile cannot read or write MiHO learned state.
- Test-run editorial rulings never enter MiHO's taste projection.
- A writing run records the exact authored-profile version and learned snapshot it used.

## Cutover and retirement

1. Generate the one-time MiHO authored profile from existing shared documents.
2. Build `content-discovery` against the external profile contract.
3. Make `writing-pipeline` accept the discovery seed and scope editorial state by
   profile.
4. Verify one cold discovery invocation.
5. Verify a later warm invocation immediately serves saved cards while replenishing.
6. Accept one MiHO pitch and complete writing through the publishing handoff.
7. Remove the old `content-pipeline` skill, plugin registration, and live implementation
   from `hmventures`.
8. Do not migrate its database or test-generated state.
9. Preserve design history through git and close `projects/miho-content-pipeline/` after
   its relevant conclusions are represented here.

The old implementation receives no further development during cutover. It remains only
until the replacement proves that no active capability or meaningful runtime data will
be lost.

## Acceptance criteria

The design is successfully implemented when:

1. A cold run produces a source-backed pitch and initial reservoir from Reddit plus web
   search using the external MiHO profile.
2. A warm run immediately presents a saved pitch while independent research agents
   replenish in parallel.
3. At least three fresh cards are ready at warm invocation; there is no reservoir cap,
   and cards are always sorted by descending rank.
4. Accept, pass, later, and unresolved reactions are preserved and affect later
   discovery preferences.
5. Removed pitches remain fully inspectable and cannot be accidentally rediscovered as
   new.
6. An accepted pitch becomes a valid writing seed and completes the existing writing
   pipeline.
7. The writing run emits `final.md` and `publishing-handoff.json`.
8. MiHO learned state remains isolated from all other profiles and test runs.
9. The old MiHO content-pipeline implementation can be deleted without losing an active
   workflow or meaningful data.
