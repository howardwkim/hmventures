# Content Discovery Writing Integration and Cutover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate accepted discovery pitches with `writing-pipeline`, isolate editorial state by profile, emit a publishing handoff, prove the complete MiHO flow, and retire the old MiHO content pipeline.

**Architecture:** The discovery seed is the only boundary between the two skills. `writing-pipeline` freezes the external profile and learned taste into its run, treats discovery evidence as unverified starting material, and writes profile-scoped editorial events plus a final publishing manifest. Cutover occurs only after one real cold/warm discovery cycle and one accepted MiHO piece complete successfully.

**Tech Stack:** Claude Code/Codex skills, Markdown stage templates, JSON/JSONL state, existing writing-pipeline stage agents, git across `personal-ai` and `hmventures`.

## Global Constraints

- Complete `2026-07-14-content-discovery-v1.md` first.
- Canonical skills live in `.claude/skills`; `.agents/skills` is a generated Codex mirror.
- Discovery remains separate from writing. Do not add search or pitch ranking to `writing-pipeline`.
- Writing accepts the discovery `seed.md`; it may revise the angle during brief development.
- Discovery evidence is starting material and must be reopened and revalidated before article use.
- For a profiled run, runtime root is `~/.content-profiles/<profile_id>/`; tests use an explicit `/tmp` root.
- MiHO editorial events never write to `projects/ai-writing-quality/pack/taste/`.
- Profileless legacy runs may continue using the current pack taste files; test runs must use an isolated test profile.
- A completed run emits both `final.md` and `publishing-handoff.json`.
- Publishing and distribution execution remain out of scope.
- Do not migrate, mutate, or delete `~/.content-pipeline/pipeline.sqlite`.
- Preserve untracked old-pipeline evaluation logs in git before removing the old skill directory.
- The `hmventures` marketplace has no content-pipeline registration; verify that fact and do not edit unrelated marketplace entries.

---

### Task 1: Define profile-scoped editorial and publishing contracts

**Files:**
- Create: `.claude/skills/writing-pipeline/references/profile-state-contract.md`
- Create: `.claude/skills/writing-pipeline/references/publishing-handoff-contract.md`

**Interfaces:**
- Consumes: `profile_id`, profile version/path, runtime root, originating pitch ID.
- Produces: exact editorial JSONL and publishing JSON schemas used by later tasks.

- [ ] **Step 1: Verify the contracts do not exist**

```bash
test ! -e .claude/skills/writing-pipeline/references/profile-state-contract.md
test ! -e .claude/skills/writing-pipeline/references/publishing-handoff-contract.md
```

Expected: both commands exit 0. Stop if either file contains unknown work.

- [ ] **Step 2: Write the profile-state contract**

Create `.claude/skills/writing-pipeline/references/profile-state-contract.md`:

```markdown
# Profile-scoped writing state

For a seed with `Profile ID`, resolve state under the caller's state root or
`~/.content-profiles/<profile_id>/`.

Required files:

- `editorial-ledger.jsonl`: append-only rulings
- `editorial-taste.md`: current distilled projection fed to brief and outline judgment
- `runs/<slug>/`: complete run artifacts

Initialize a missing taste projection as:

```markdown
# Editorial taste

## Standing rules

None confirmed.

## Recent rulings

None recorded.
```

Each ledger line uses:

```json
{
  "schema_version": 1,
  "event": "editorial.ruling",
  "at": "2026-07-14T12:00:00-07:00",
  "profile_id": "miho",
  "run_id": "stable-run-slug",
  "scope": "thesis|angle|argument",
  "ruling": "Verbatim operator ruling",
  "disposition": "recent|standing|quarantined|superseded",
  "source": "outline-gate|verdict-session"
}
```

Only a ruling from a run carrying the same `profile_id` may update the projection.
Test runs use their own test profile ID and state root. Profile-scoped writes never
touch the global pack taste files.
```

- [ ] **Step 3: Write the publishing-handoff contract**

Create `.claude/skills/writing-pipeline/references/publishing-handoff-contract.md`:

```markdown
# Publishing handoff contract

After `final.md` survives the final gate, write `publishing-handoff.json` beside it:

```json
{
  "schema_version": 1,
  "profile_id": "miho",
  "profile_version": "1",
  "title": "Final article title",
  "slug": "final-article-title",
  "summary": "One or two sentence publishing excerpt.",
  "originating_pitch_id": "pitch-slug",
  "register": "blog",
  "final_artifact": "final.md",
  "status": "approved",
  "completed_at": "2026-07-14T12:00:00-07:00",
  "publishing_metadata": {}
}
```

Use a stable kebab slug. `final_artifact` is run-relative. The summary must describe
the final piece, not the original pitch. `publishing_metadata` contains only fields
required by the selected register; keep it empty when none are known. This file is a
handoff, not permission to publish.
```

- [ ] **Step 4: Validate and commit**

```bash
test -s .claude/skills/writing-pipeline/references/profile-state-contract.md
test -s .claude/skills/writing-pipeline/references/publishing-handoff-contract.md
git add .claude/skills/writing-pipeline/references
git commit -m "docs(writing-pipeline): define profile state and publishing contracts"
```

---

### Task 2: Feed the external profile and discovery evidence into the correct stages

**Files:**
- Modify: `.claude/skills/writing-pipeline/stages/brief-writer.md`
- Modify: `.claude/skills/writing-pipeline/stages/material-gatherer.md`
- Modify: `projects/ai-writing-quality/pack/stage-inputs.md`

**Interfaces:**
- Consumes: frozen `content-profile.md`, seed `Discovery evidence`, and existing brief/register/taste inputs.
- Produces: a profile-aware brief and a material pool that revalidates discovery sources.

- [ ] **Step 1: Record the failing structural checks**

Run:

```bash
rg -n 'CONTENT_PROFILE_LINE' .claude/skills/writing-pipeline/stages/brief-writer.md
rg -n 'DISCOVERY_EVIDENCE_LINE' .claude/skills/writing-pipeline/stages/material-gatherer.md
```

Expected before changes: both commands exit 1 with no matches.

- [ ] **Step 2: Make the brief-writer profile-aware**

In `.claude/skills/writing-pipeline/stages/brief-writer.md`:

1. Extend the header placeholder list with `{{CONTENT_PROFILE_LINE}}`.
2. Replace the numbered `Read ONLY these files` block with:

```markdown
Read ONLY these files:
- Assignment: {{SEED_PATH}} — topic/question, surface, chooser, why-this-topic, and
  discovery evidence.
- Register: {{REGISTER_PATH}} — what this surface must do and its claim rules.
{{CONTENT_PROFILE_LINE}}
- Editorial taste: {{EDITORIAL_TASTE_PATH}} — rulings on arguments and angles the
  owner stands behind.
{{FACT_BASE_LINE}}
```

The runner substitutes:

```text
- Content profile: <run>/content-profile.md — authored identity, audience, expertise,
  editorial territory, boundaries, and writing defaults.
```

for profiled runs and an empty string otherwise.

In the brief-writer's `Why this piece` rule, treat `agent` and `machine-suggested` as
the same chooser category: both require the full selection rationale.

- [ ] **Step 3: Make material gathering revalidate discovery evidence**

In `.claude/skills/writing-pipeline/stages/material-gatherer.md`:

1. Add `{{DISCOVERY_EVIDENCE_LINE}}` to the header placeholder list.
2. Add after the brief input:

```markdown
{{DISCOVERY_EVIDENCE_LINE}}
```

3. Add before the output format:

```markdown
If discovery evidence is supplied, treat it as candidate material only. Reopen the
source, verify that it still says what the seed claims, and apply the same instantiation
test as every other item. Discovery provenance does not waive verification.
```

The runner substitutes:

```text
2. <run>/seed.md — source-backed discovery evidence; starting material, not verified
   article evidence.
```

when the seed contains discovery evidence and an empty string otherwise.

- [ ] **Step 4: Update the stage-input table**

In `projects/ai-writing-quality/pack/stage-inputs.md`:

- Row 1 Receives: add `external content profile when supplied`.
- Row 2 Receives: add `discovery seed evidence when supplied, revalidated before use`.
- Row 2 Must NOT receive: add `discovery recommendation as settled thesis`.

Do not change which stages receive style files or the existing contamination rule.

- [ ] **Step 5: Run structural checks and inspect the exact diff**

```bash
rg -n 'CONTENT_PROFILE_LINE|Content profile' .claude/skills/writing-pipeline/stages/brief-writer.md
rg -n 'DISCOVERY_EVIDENCE_LINE|Discovery provenance' .claude/skills/writing-pipeline/stages/material-gatherer.md
git diff --check
```

Expected: both placeholders and both behavioral instructions appear; diff check exits 0.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/writing-pipeline/stages/brief-writer.md .claude/skills/writing-pipeline/stages/material-gatherer.md projects/ai-writing-quality/pack/stage-inputs.md
git commit -m "feat(writing-pipeline): accept profile and discovery evidence inputs"
```

---

### Task 3: Make the writing runner profile-aware and isolate editorial learning

**Files:**
- Modify: `.claude/skills/writing-pipeline/SKILL.md`

**Interfaces:**
- Consumes: discovery seed fields from Plan 1, profile-state contract from Task 1, stage placeholders from Task 2.
- Produces: run-directory resolution, frozen profile/taste snapshots, and profile-scoped editorial write-back.

- [ ] **Step 1: Forward-test the current runner against a profiled seed**

Use a fresh agent with a temporary seed containing `Profile ID`, `Content profile`, and
`Originating pitch`. Ask it to orient without running stages.

Expected before implementation: it follows the generic run-dir and global
`pack/taste/editorial.md`; it has no profile-state rule. Record this failure.

- [ ] **Step 2: Add profile-aware run resolution to `SKILL.md`**

Add under Run dir:

```markdown
### Profile-aware runs

When `seed.md` contains `Profile ID`, also require `Profile version`, `Content profile`,
and `Originating pitch`. Read `references/profile-state-contract.md`.

Resolve state as `<state-root>/<profile_id>/`, where the default state root is
`~/.content-profiles` and a caller-supplied test root overrides it. Unless the caller
supplies a run directory, write the run to `<profile-state>/runs/<slug>/`.

Copy the authored profile to `run/content-profile.md`. Copy the current profile taste
projection to `run/editorial-taste.md`. The copies are immutable run snapshots; later
state changes do not rewrite them.

For profileless legacy runs, keep the existing run-dir and pack-taste behavior. A test
run that can write rulings must use an isolated test profile; never label a test run
`miho`.
```

Add `content-profile.md` and `editorial-taste.md` to the run-directory layout.

- [ ] **Step 3: Extend Procedure step 0**

After the existing seed fields, add:

```markdown
For a discovery seed, preserve `why_this_topic`, discovery evidence, profile ID/version,
profile path, and originating pitch exactly. Freeze the profile and current taste into
the run before dispatching any stage. Pass the frozen profile through
`CONTENT_PROFILE_LINE`. Pass the seed through `DISCOVERY_EVIDENCE_LINE` during material
gathering.
```

- [ ] **Step 4: Replace profile-scoped taste write-back behavior**

In Procedure step 5, retain the existing global behavior only for profileless runs.
For profiled runs, replace the write target with:

```markdown
**Profile-scoped taste write-back:** append every thesis/angle/argument ruling as one
`editorial.ruling` JSON line to the profile's `editorial-ledger.jsonl`, then rebuild the
profile's `editorial-taste.md` recent window. Write only when the ruling's run
`profile_id` equals the target profile. Test profiles write to their own state root.
Never update `projects/ai-writing-quality/pack/taste/` from a profiled run.
```

- [ ] **Step 5: Repeat the fresh-agent orientation test**

Expected: the agent resolves the temporary profile state, names the frozen profile and
taste paths, and refuses to write the global MiHO or pack taste files.

- [ ] **Step 6: Revalidate and commit**

```bash
uv run --with pyyaml python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/writing-pipeline
git diff --check
git add .claude/skills/writing-pipeline/SKILL.md
git commit -m "feat(writing-pipeline): isolate runs and taste by content profile"
```

---

### Task 4: Emit the publishing handoff after the final gate

**Files:**
- Modify: `.claude/skills/writing-pipeline/SKILL.md`

**Interfaces:**
- Consumes: final artifact, seed metadata, profile snapshot, register.
- Produces: `publishing-handoff.json` matching Task 1.

- [ ] **Step 1: Record the missing-output failure**

Inspect an existing completed run:

```bash
test ! -e projects/ai-writing-quality/experiments/pipeline-v2-run-1/run/publishing-handoff.json
```

Expected: exit 0, proving the current runner emits no handoff.

- [ ] **Step 2: Add the packaging step**

In `.claude/skills/writing-pipeline/SKILL.md`, insert after verdict session and before
the `After any run` actions:

```markdown
**12. Package.** Read `references/publishing-handoff-contract.md`. After the verdict
session leaves an approved `final.md`, write `publishing-handoff.json` from that final
artifact and seed metadata. Validate it with `jq -e .`. This is a handoff only; do not
publish, schedule, or invoke distribution tools.
```

Keep Verdict session as step 11. Packaging must run afterward so a verdict-driven edit
cannot leave a stale handoff.

- [ ] **Step 3: Add output requirements to the run layout and failure discipline**

Add `publishing-handoff.json` to the run tree. Add this failure rule:

```markdown
- A run is not complete when `final.md` exists but `publishing-handoff.json` is missing
  or invalid. Repair the handoff before token rollup or review-page generation.
```

- [ ] **Step 4: Structural verification and commit**

```bash
rg -n 'Package|publishing-handoff.json|handoff only' .claude/skills/writing-pipeline/SKILL.md
uv run --with pyyaml python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/writing-pipeline
git diff --check
git add .claude/skills/writing-pipeline/SKILL.md
git commit -m "feat(writing-pipeline): emit publishing handoff package"
```

---

### Task 5: Forward-test profile isolation and publishing output

**Files:**
- Create temporarily: `/tmp/writing-pipeline-profile-eval/`
- Create: `projects/ai-writing-quality/experiments/profile-isolation-eval/`
- Mirror generated: `.agents/skills/writing-pipeline/`

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: artifact evidence for profile isolation without spending a full live MiHO run.

- [ ] **Step 1: Sync the writing skill to Codex**

```bash
uv run python .claude/skills/codex-sync/scripts/sync.py skills --only writing-pipeline --apply
uv run python .claude/skills/codex-sync/scripts/sync.py skills --only writing-pipeline
```

Expected second command: no `writing-pipeline` drift.

- [ ] **Step 2: Prepare two isolated profiles and seeds**

Under `/tmp/writing-pipeline-profile-eval`, create `miho/` and `test-profile/`, each
with its own minimal valid `content-profile.md`, empty `editorial-ledger.jsonl`, and
initial `editorial-taste.md`. Create a discovery-format seed for each using different
originating pitch IDs and evidence URLs.

- [ ] **Step 3: Run both pipelines only through brief development**

Dispatch fresh agents with `outline_gate: on` and explicit temporary run directories.
Stop after each `brief.md` is written. Expected:

- Each run freezes the correct content profile and taste file.
- Each brief sees its own audience and never the other profile.
- Neither run modifies `projects/ai-writing-quality/pack/taste/`.

- [ ] **Step 4: Simulate one gate ruling per profile**

Continue each run through its outline packet with a distinct ruling. Expected: each
ruling appends only to its own `editorial-ledger.jsonl`; neither appears in the other's
projection.

- [ ] **Step 5: Complete the cheaper test-profile run**

Use `tier: bottom` and finish the test-profile run. Expected: `final.md` and a valid
`publishing-handoff.json` with the test profile/version/pitch, `status: approved`, and
no publishing side effect.

- [ ] **Step 6: Validate artifacts**

```bash
jq -e '.schema_version == 1 and .status == "approved" and .final_artifact == "final.md"' /tmp/writing-pipeline-profile-eval/test-profile/runs/profile-isolation-eval/publishing-handoff.json
rg -n 'test-profile' /tmp/writing-pipeline-profile-eval/test-profile/editorial-ledger.jsonl
! rg -q 'test-profile' /tmp/writing-pipeline-profile-eval/miho/editorial-ledger.jsonl
git diff --exit-code -- projects/ai-writing-quality/pack/taste
```

Expected: every command exits 0.

- [ ] **Step 7: Record and commit the eval artifacts that belong in the repo**

Write `projects/ai-writing-quality/experiments/profile-isolation-eval/report.md` with
the exact prompts, artifact paths, results, and failures. Do not commit `/tmp` state.

```bash
git add projects/ai-writing-quality/experiments/profile-isolation-eval
git commit -m "test(writing-pipeline): verify profile isolation and publishing handoff"
```

---

### Task 6: Run the real MiHO end-to-end cutover acceptance

**Files:**
- Runtime: `~/.content-profiles/miho/`
- Create: `projects/miho-content-pipeline/reference/2026-07-14-cutover-acceptance.md`

**Interfaces:**
- Consumes: a real accepted pitch from Plan 1 and Tasks 1–5.
- Produces: one complete MiHO run proving the replacement before retirement.

- [ ] **Step 1: Protect existing runtime state**

Inspect `~/.content-profiles/miho/` and `~/.content-pipeline/`. Do not delete, rename,
or import from the old database. If new profile state already exists, preserve it and
resume rather than replacing it.

- [ ] **Step 2: Run a real warm discovery session**

Invoke `content-discovery` with the committed MiHO profile. Confirm it presents a saved
card before reporting new research. Choose a pitch only if Howard genuinely wants the
piece; do not accept one merely to satisfy the test.

- [ ] **Step 3: Verify the accepted seed before writing**

Confirm the seed contains topic, register, `chosen_by: agent`, full why-this-topic,
accepted angle, discovery evidence, profile ID/version/path, and originating pitch.

- [ ] **Step 4: Complete the writing pipeline**

Run the existing outline gate and verdict protocol. Discovery evidence must be reopened
and validated during material gathering. Complete through `final.md` and
`publishing-handoff.json`; do not publish.

- [ ] **Step 5: Verify the real artifacts**

```bash
jq -e '.profile_id == "miho" and .profile_version == "1" and .status == "approved"' ~/.content-profiles/miho/runs/*/publishing-handoff.json
test -s ~/.content-profiles/miho/editorial-ledger.jsonl
git diff --exit-code -- projects/ai-writing-quality/pack/taste
```

If multiple run directories exist, target the exact accepted run instead of relying on
the glob.

- [ ] **Step 6: Write the acceptance record**

In `projects/miho-content-pipeline/reference/2026-07-14-cutover-acceptance.md`, record:

- Cold and warm discovery evidence
- Accepted pitch ID and seed path
- Writing run path
- Discovery sources revalidated or rejected
- Final and handoff paths
- Profile-state writes
- Global taste diff result
- Howard's verdict on whether the replacement is operationally complete

- [ ] **Step 7: Commit the acceptance record**

```bash
git add projects/miho-content-pipeline/reference/2026-07-14-cutover-acceptance.md
git commit -m "test(miho): prove discovery to publishing-handoff cutover"
```

Do not start retirement unless Howard's verdict in the acceptance record is affirmative.

---

### Task 7: Preserve evaluation history and retire the old `hmventures` pipeline

**Files:**
- Preserve then remove in `hmventures`: `.claude/skills/content-pipeline/FEEDBACK-LOG.md`
- Preserve then remove in `hmventures`: `.claude/skills/content-pipeline/current.md`
- Preserve then remove in `hmventures`: `.claude/skills/content-pipeline/reference/session-log.md`
- Remove in `hmventures`: `.claude/skills/content-pipeline/`
- Remove in `hmventures`: `.claude/commands/content-pipeline.md`
- Verify only: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: affirmative Task 6 acceptance.
- Produces: no live old skill or command; all authored/evaluation history recoverable through git.

- [ ] **Step 1: Audit the `hmventures` worktree**

```bash
git -C /Users/howardwkim/src/hmventures status --short
```

Expected known untracked files are the feedback log, current state, and reference log
inside `.claude/skills/content-pipeline/`. Stop for any unrelated change.

- [ ] **Step 2: Commit the previously untracked authored history before removal**

```bash
git -C /Users/howardwkim/src/hmventures add .claude/skills/content-pipeline/FEEDBACK-LOG.md .claude/skills/content-pipeline/current.md .claude/skills/content-pipeline/reference/session-log.md
git -C /Users/howardwkim/src/hmventures commit -m "docs(content-pipeline): preserve evaluation history before retirement"
```

Expected: the three files are now recoverable by commit SHA.

- [ ] **Step 3: Verify there is no marketplace registration to edit**

```bash
rg -n 'content-pipeline' /Users/howardwkim/src/hmventures/.claude-plugin/marketplace.json
```

Expected: exit 1 with no matches. Leave the social-post marketplace entry untouched.

- [ ] **Step 4: Remove the tracked skill and command**

First preview and remove ignored machine exhaust while the skill-local `.gitignore`
still exists:

```bash
git -C /Users/howardwkim/src/hmventures clean -ndX -- .claude/skills/content-pipeline
git -C /Users/howardwkim/src/hmventures clean -fdX -- .claude/skills/content-pipeline
```

The preview must list only `.venv`, `.pytest_cache`, `__pycache__`, and equivalent
regenerable caches. Stop if it names authored files.

```bash
git -C /Users/howardwkim/src/hmventures rm -r .claude/skills/content-pipeline .claude/commands/content-pipeline.md
```

Do not remove `~/.content-pipeline/`; runtime data remains untouched and simply has no
active client.

- [ ] **Step 5: Verify live entry points are gone**

```bash
test ! -e /Users/howardwkim/src/hmventures/.claude/skills/content-pipeline
test ! -e /Users/howardwkim/src/hmventures/.claude/commands/content-pipeline.md
git -C /Users/howardwkim/src/hmventures diff --cached --check
```

Expected: all exit 0. Mike's reference-only `docs/miho/commands/staff-writer.md` and
`social-package.md` remain untouched.

- [ ] **Step 6: Commit retirement**

```bash
git -C /Users/howardwkim/src/hmventures commit -m "refactor(miho): retire superseded content pipeline"
```

---

### Task 8: Close the personal project and mark the writing defect resolved

**Files:**
- Modify: `projects/miho-content-pipeline/current.md`
- Modify: `projects/ai-writing-quality/current.md`

**Interfaces:**
- Consumes: completed cutover and retirement commits.
- Produces: accurate project state for future sessions; project remains on disk as design history.

- [ ] **Step 1: Replace the active MiHO project status**

Replace the top active-status section of `projects/miho-content-pipeline/current.md` with:

```markdown
# miho-content-pipeline — Complete

**Completed:** 2026-07-14

The MiHO-specific content pipeline has been replaced by two general capabilities:
`content-discovery` supplies a profile-scoped, source-backed writing seed, and
`writing-pipeline` produces the approved piece plus a publishing handoff. MiHO is an
external authored profile, not a pipeline or dispatcher.

The old `hmventures/.claude/skills/content-pipeline/` implementation and command were
retired after a real cold/warm discovery cycle and one accepted MiHO piece completed
the writing path. Its database was not migrated or deleted. Design and evaluation
history remain recoverable through git and this project's reference files.

**Canonical design:** `docs/superpowers/specs/2026-07-14-content-discovery-design.md`
**Implementation plans:**
- `docs/superpowers/plans/2026-07-14-content-discovery-v1.md`
- `docs/superpowers/plans/2026-07-14-content-discovery-writing-cutover.md`
```

Keep older snapshots below a clear `## Historical snapshots` heading.

- [ ] **Step 2: Mark the taste contamination defect resolved**

In `projects/ai-writing-quality/current.md`, change the known-defect heading to:

```markdown
**RESOLVED 2026-07-14 — profile-scoped editorial taste.** Profiled writing runs now
write rulings only to `~/.content-profiles/<profile_id>/editorial-ledger.jsonl` and
consume that profile's `editorial-taste.md`. Test profiles and MiHO cannot contaminate
one another. The global pack taste remains only as the compatibility path for explicitly
profileless legacy runs.
```

Retain the old incident description beneath it as history, but remove wording that says
the architectural fix remains pending.

- [ ] **Step 3: Final cross-repository verification**

```bash
uv run --with pyyaml python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/content-discovery
uv run --with pyyaml python /Users/howardwkim/.codex/skills/.system/skill-creator/scripts/quick_validate.py .claude/skills/writing-pipeline
uv run python .claude/skills/codex-sync/scripts/sync.py skills --only content-discovery writing-pipeline
git diff --check
git -C /Users/howardwkim/src/hmventures status --short
```

Expected: both skills validate, mirrors have no drift, personal-ai diff check is clean,
and `hmventures` is clean.

- [ ] **Step 4: Commit project closeout**

```bash
git add projects/miho-content-pipeline/current.md projects/ai-writing-quality/current.md
git commit -m "closeout: replace MiHO pipeline with discovery and writing skills"
```

---

## Plan 2 Completion Gate

The replacement is complete only when:

- A real MiHO pitch has traversed discovery, seed, brief, research, outline, draft, final, and publishing handoff.
- The real run preserves the MiHO profile version and originating pitch.
- MiHO and test editorial state are isolated and global pack taste is unchanged.
- The old `hmventures` skill and command are removed, their evaluation history is in git, and their live database remains untouched.
- Both canonical skills validate and their Codex mirrors have no drift.
