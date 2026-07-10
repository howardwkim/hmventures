# Content Pipeline: Stage Isolation & Artifact Handoffs

**Date:** 2026-07-10
**Status:** Design approved, pending spec review
**Scope:** Restructure the `content-pipeline` skill so each stage of the flow is
an isolated unit that consumes a defined input artifact and emits a defined
output artifact, communicating only through those artifacts. Full decomposition:
all four judgment stages (interview, draft, edit, synthesis) run as isolated
subagents with artifact handoffs.

---

## 1. Motivation & Principle

Today the skill is one blob of prose in `SKILL.md` that the main conversation
interprets end to end. The drafting step sees everything — the candidate's
Reddit provenance, the rejected candidates, the interview transcript, the
accumulated style rules — all at once. That coupling means:

- You can't change how questions are generated without editing the whole skill.
- You can't regenerate a draft from a changed brief, or re-style an existing
  brief, without re-running the flow.
- Earlier-stage reasoning contaminates later stages.
- You can't resume at an arbitrary stage.

**Principle:** every stage consumes a well-defined input artifact and emits a
well-defined output artifact. A stage never sees another stage's internals or
provenance — only the artifact handed to it. Because every artifact persists in
the one SQLite store, the pipeline can resume at any stage given that stage's
inputs.

This mirrors the existing backend philosophy: the Python side is deterministic
bookkeeping with typed verb inputs/outputs and never calls an LLM. This design
gives the *LLM-judgment* stages the same clean seams.

---

## 2. The Four Stages

The **orchestrator** is this skill running in the main conversation. It owns
everything interactive (talking to the operator) and every CLI call. Each
judgment stage is an isolated **subagent** dispatched via the `Task` tool, with
its prompt loaded on demand from a file.

| Stage | Runner | Input → Output |
|---|---|---|
| **Interview** | Orchestrator (live with operator) + **brief-writer subagent** | Orchestrator reads the interview guide, asks the operator one question at a time, records answers → `interview_answers`. Brief-writer subagent takes {answers, source snippet, voice doc} → **brief**. |
| **Draft** | **drafter subagent** | {brief, voice doc} → draft version |
| **Edit** | **edit subagent** | {current draft, operator feedback verbatim, brief, voice doc} → revised draft version |
| **Synthesis** | **synthesis subagent** | {new_events, active_rules, base_checkpoint} → two-door decision JSON |

**Provenance stays in the orchestrator.** Which candidate this came from, the
yes/no decisions, the raw interview transcript — none of it reaches the drafter.
The drafter only ever sees {brief, voice doc}.

**Why the interview is split.** A `Task` subagent runs autonomously and cannot
stop to ask the operator questions mid-run. The interview is inherently a live
back-and-forth, so only the orchestrator can conduct it. The *distillation* of
answers into a structured brief is not interactive, so it runs as the
brief-writer subagent with a clean {answers → brief} contract that can be tested
and changed independently.

---

## 3. The Two Voice Inputs → One Composed Doc

Both the brief-writer and the drafter receive a **single composed voice doc**.
It is built from two layers:

1. **Static seed** — the hand-owned floor. Sourced from the operator's
   `config.json` `brand_context`. When that is empty, a **generic good-writing
   default** (a constant in code) is used instead. The operator's own
   `brand_context`, once set, replaces the default.
2. **Learned layer** — evolves over time. Rendered by `canon.style_context()`
   from `permanent_rules` + `provisional_tendencies`, which synthesis writes
   from the operator's edits.

**Composition rule:** the seed is the floor; the learned layer is composed on
top. The guideline wins at read time; the learned layer only *proposes* changes
(as tendencies, or promoted rules). This is Model 1: the authored seed and the
machine-learned rules stay separate stores, so the operator can always
distinguish "what I authored" from "what the machine inferred," reject a learned
change, or reset to intent. (Rejected alternative — Model 2, a single living
document that promotions rewrite — was declined because it collapses that
boundary and lets authored and inferred voice drift together.)

**The voice changes over time via the learned layer (in the DB), not by
mutating the seed constant.** Keeping the seed as a code constant (rather than
seeding it into `config.json` on first run) means the default *improves when the
skill updates*, instead of freezing at whatever the default was on first run.

**What belongs to voice, not the brief:** audience, tone, length, structure,
phrasing rules. These are cross-article *how*, set once and learned. They must
not leak into per-article briefs — if they did, you couldn't change them in one
place, which is the whole point of the split.

---

## 4. Artifacts & Data Model

### Brief (new)
The interview stage's output and the drafter's main input. Content only — the
*what*, never the *how*.

- **New `briefs` table:** `id, article_id, version, brief_json, created_at`.
- **`brief_json` fields:** working title, topic (one line), angle/thesis, key
  points (3–5), **source snippet** (a short verbatim excerpt from the original
  candidate so the drafter can ground a reference without seeing the whole
  candidate record), content-specific constraints / must-avoids.
- **Versioned:** regenerating a brief writes a new row; old rows are preserved.
- **New verbs:** `save-brief` (persist a brief version), `brief-context` (read
  the current brief + voice doc for the drafter — the "resume at draft" entry
  point).

### Draft versions (new)
- **New `draft_versions` table:** `id, article_id, version, text, brief_id,
  voice_snapshot, created_at`.
- Every draft and every regenerate writes a **new version**; nothing is
  overwritten (additive / nothing-ephemeral). `brief_id` + `voice_snapshot`
  record exactly which inputs produced each version.
- Edit rounds continue to track forward, per-round changes (existing
  `edit_rounds` table); a full regenerate from a changed brief or voice is a new
  draft version, distinct from an edit round.

### Versioning mechanism: SQLite, not git
Draft/brief history lives in the DB, **not** in git. Rationale:

- The pipeline DB is `~/.content-pipeline/pipeline.sqlite` — a data dir, **not a
  git repo**. "Use git" would mean standing up a dedicated repo inside that data
  dir: a second persistence system beside SQLite, reintroducing the coupling
  this redesign removes.
- **One source of truth.** Drafts in git + everything else in SQLite means two
  stores that must stay consistent and an ambiguous authority when they
  disagree.
- **Atomicity.** A SQLite transaction writes draft + version + status + event
  atomically. Git-commit-then-DB-write can half-fail and tear state.
- **Queryability.** "The draft from brief v2" is a trivial join; in git it means
  mapping versions to commit refs.
- **No environmental assumptions.** The backend is deterministic and env-free by
  design; git adds a dependency (installed? repo initialized? commit identity?)
  and hidden state.
- **Scale.** Articles are kilobytes; a few versions across dozens of articles is
  nothing. Git's delta compression solves a problem this doesn't have; SQLite is
  a more portable single file.
- Git's real strengths (branching, merge, distributed collaboration) are unused
  by a single-user linear draft history. Diffs come free from two rows
  (`difflib` is already used in `writing.py`).

---

## 5. Swappable Spec Artifacts (progressive disclosure)

Stage logic that the operator may want to change lives in files under the
skill's **`references/` directory** (Anthropic skill convention; `skill-creator`
and `mcp-builder` use it), loaded on demand — never inlined into `SKILL.md` and
never stored in the DB (the DB holds per-run state only).

- **`references/interview-guide.md`** — the swappable interview spec. Describes
  the **content dimensions** to probe: the operator's take/thesis on this topic,
  the key insight, which points matter, any personal experience or example to
  ground it, what makes it worth saying now. **Content only** — not tone, not
  audience (those are voice). The orchestrator reads this and *generates*
  candidate-tailored questions from it (an adaptive interview guide, not a fixed
  question list), so what-to-probe can change without editing the skill.
- **`references/brief-writer-prompt.md`** — brief-writer subagent prompt.
- **`references/drafter-prompt.md`** — drafter subagent prompt.
- **`references/edit-prompt.md`** — edit subagent prompt.
- **`references/synthesis-prompt.md`** — synthesis subagent prompt (the two-door
  reasoning moves here from `SKILL.md`).

`SKILL.md` stays lean: the orchestration flow, the stopping points, and which
file to load when each stage dispatches.

---

## 6. Regeneration & Resume Semantics

- **Change the brief** → re-dispatch the drafter → new draft version; old
  version preserved. Voice untouched.
- **Change the voice** → re-dispatch the drafter on the same brief → new draft
  version in the new voice. Brief untouched.
- **Resume at any stage** = load that stage's input artifact and dispatch:
  brief exists → skip to draft; draft exists → skip to edit. The existing
  `resumable()` logic (article stuck in `interviewing`/`reviewing`) still
  offers "pick up where you left off?"

Because {brief, voice} are independent inputs to the drafter, either axis moves
without the other and without re-running the whole flow.

---

## 7. Learning Flow (unchanged in mechanism, relocated in prose)

Synthesis stays as designed: run it every time an article is approved
(`status.synthesis_pending` flags any approved article still missing it). The
two-door reasoning (explicit directive → new permanent rule; silent repeated
preference → provisional tendency; contradiction → supersede) moves into
`references/synthesis-prompt.md`. The learned layer it produces is what composes
on top of the seed in the voice doc (§3). This is the mechanism by which
"if we keep writing this way" turns into a proposed change to the effective
voice.

---

## 8. Non-Goals / YAGNI

- **No onboarding flow** to capture the operator's starting voice — that is a
  later, separate project. Until it exists, the generic good-writing default
  seed is the floor and the learned layer personalizes it through use.
- **No Model-2 single-living-guideline document.**
- **No git-based versioning.**
- **The generic voice default is not written now** — this design changes how a
  *rerun* behaves; the actual default doc content is a separate task.

---

## 9. Open Implementation Details (for the plan, not the design)

- Exact `Task` dispatch shape for each subagent (agent type, structured-output
  schema for the brief and the synthesis decision).
- Schema migration (`_MIGRATIONS` registry) for `briefs` and `draft_versions`;
  bump `CURRENT_VERSION`.
- Whether `draft-context` is superseded by `brief-context` or both coexist
  during transition.
- `voice_doc` render helper (compose seed + `style_context`) and where it lives
  (`canon` vs a new `voice` module).
