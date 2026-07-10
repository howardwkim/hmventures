---
name: content-pipeline
description: Run the content pipeline — discover candidate topics, review and decide which to pursue, interview and draft an article, take edit rounds, and approve. Use when the user says "run discovery", "check the review queue", "review topics", "write the next article", "what should I write about", "content pipeline", "draft the article", "pipeline status", or "/content-pipeline".
---

# content-pipeline

Drive the content pipeline from raw candidate topics to an approved article,
learning the operator's writing style as you go.

**You are the writer.** The Python backend is deterministic — it persists state
and does the bookkeeping math, and it never calls an LLM. Every piece of LLM
judgment is *your* job in this conversation: you generate the interview
questions, write the draft, revise it on operator feedback, and decide what
style rules to learn. The CLI verbs below are how you read context and persist
what you produced. Do not expect the CLI to write anything for you.

## Invocation

Every verb runs the same way, from inside `.claude/skills/content-pipeline/`:

```
uv run python -m content_pipeline.cli --db PATH <verb> [args...]
```

`--db` is a **top-level** flag (before the verb) and is **mandatory on every
call** — pass it explicitly every time, don't rely on an environment variable
or shell profile to fill it in. There is no fallback: `--db` unset and
`CONTENT_PIPELINE_DB` unset makes every verb exit with an error rather than
guessing a path. This is a code-level guard against an unconfigured
invocation (e.g. an ad hoc smoke test) silently landing on the wrong file.

**The operator's real pipeline DB is `~/.content-pipeline/pipeline.sqlite`.**
That is the canonical path for every real, operator-directed run of this
skill — pass `--db ~/.content-pipeline/pipeline.sqlite` explicitly for real
work in this conversation.

**Mutating verbs need an explicit go-ahead first.** `decide`, `next-article`,
`answer`, `save-draft`, `edit`, `approve`, and `apply-synthesis` change real
pipeline state (they start articles, consume candidates, advance checkpoints).
Never run one speculatively or to "check that it works" — that includes while
developing or verifying changes to this skill or the CLI itself. If you need
to exercise a mutating verb for testing, pass `--db` pointing at a throwaway
file under the scratchpad directory, never
`~/.content-pipeline/pipeline.sqlite`.

## The flow

Each numbered step below is a discrete stopping point. When one finishes, ask
the operator whether to proceed to the next step rather than continuing on
your own — e.g. after decisions are recorded, ask "start the next article?"
before running `next-article`; after a draft is saved, ask before moving into
the edit loop; after approval, ask before running synthesis (unless
`synthesis_pending` makes it mandatory first). Exception: within a step that
is inherently a back-and-forth (the edit loop's rounds), keep going per the
operator's ongoing feedback without re-asking each round.

### 1. Orient — `status` (and `review`)
Start here. `status` returns `{review_queue_count, resumable_article,
next_article_available, calibration, edit_effort_trend, nudge, synthesis_pending}`.
Check `synthesis_pending`: if it is `true`, an article was approved but its
style-synthesis step never ran — do step 9 for that outstanding article before
anything else. Run `review` to see the candidates awaiting a decision.

### 2. Ingest candidates — `ingest`
For this phase candidates are operator-supplied test data:

```
ingest --json '[{"source":"test","source_ref":"r1","title":"...","url":"...","summary":"..."}]'
```

Each object mirrors the `Candidate` fields: required `source, source_ref,
title`; optional `url, summary, engagement, topic_tags, emotional_driver,
news_hook, predicted_relevance`. The candidate id is derived as
`<source>-<source_ref>` (e.g. `test-r1`). Ingestion dedupes on
(source, source_ref); re-ingesting is safe. Result: `{ingested}`.

`discover --source reddit --digest-db PATH` remains available (reddit adapter),
but is not the default path in this phase.

### 3. Review and decide — `review`, `decide`
Present the full candidate list to the operator top-down. For each decision:

```
decide CANDIDATE_ID yes|no|snooze [--note TEXT]
```

`yes` moves it toward writing, `no` drops it, `snooze` defers it until the next
day. Save as you go. Result: `{candidate_id, status}`.

### 4. Start the next article — `next-article`
```
next-article
```

If an article is mid-flight, this resumes it: `{resumed: true, article_id,
status}` — ask the operator "pick up where you left off?" before continuing.
If starting fresh: `{resumed: false, article_id, candidate_id, candidate:
{title, summary, url}, brand_context, style_context}`. Empty queue:
`{resumed: false, article_id: null}`.

There is **no `questions` field** — you generate the interview questions
yourself from the returned `candidate`, `brand_context`, and `style_context`.
For each question, offer a **recommended** answer (your best read of the
operator's take) and one **alternate**, and always allow free-text or skip.
Converse naturally; don't interrogate.

### 5. Record answers — `answer`
After each answer:

```
answer ARTICLE_ID --question TEXT --chosen recommended|alternate|custom|skip [--text TEXT]
```

Result: `{article_id, recorded}`.

### 6. Draft — `draft-context`, then `save-draft`
```
draft-context ARTICLE_ID
```

Returns `{article_id, candidate, answers, brand_context, style_context}`.
**Write the full draft yourself** from the answers + `style_context` +
`brand_context`. Apply every active style rule verbatim. Hard constraint:
**no em dashes** anywhere — use commas, periods, or parentheses instead. Show
the operator the draft, then persist it:

```
save-draft ARTICLE_ID --text "<the full draft>"
```

Result: `{article_id, status: "reviewing", pending_rule_notice}`. If
`pending_rule_notice` is non-null, surface it to the operator ("Applied a new
rule: X. Tap to undo.") — see "Rule promotion" below.

### 7. Edit loop — `edit`
For each round of operator feedback, **revise the draft yourself**, show it,
then record the round:

```
edit ARTICLE_ID --feedback "<verbatim operator feedback>" --text "<revised draft>"
```

Pass the operator's feedback verbatim (the synthesis step reads it to detect
directives). Result: `{article_id, round}`. Repeat until the operator approves.

### 8. Approve — `approve`
```
approve ARTICLE_ID --text "<final text>"
```

Result: `{article_id, status: "approved"}`. Approve does **not** trigger
synthesis — that is the next step, and it is yours to run.

### 9. Synthesize style — `synthesis-context`, then `apply-synthesis`
This is the learning step. Run it **every time you approve an article**
(`status.synthesis_pending` flags any approved article still missing it).

```
synthesis-context ARTICLE_ID
```

Returns `{base_checkpoint, new_events, active_rules, promotion_allowed}`.
Reason over `new_events` (the edit rounds and interview choices since the last
synthesis) by the **two-door rule** described below, producing a decision:

```json
{
  "new_rules": [{"text": "...", "kind": "positive|negative", "evidence_ids": [<ids from new_events>]}],
  "supersede": [{"id": <active_rule_id>, "reason": "..."}],
  "tendencies": [{"text": "...", "evidence_ids": [...]}]
}
```

Then persist it:

```
apply-synthesis ARTICLE_ID --base-checkpoint <base_checkpoint from synthesis-context> --json '<your decision>'
```

Passing `base_checkpoint` back is **required**: it makes the write idempotent.
A repeated call with the same base_checkpoint returns
`{skipped: "checkpoint_advanced", ...}` instead of double-applying the rules.
If `promotion_allowed` is `false` (thrash guard), still send `tendencies` but
expect no rule promotion. Result: `{skipped, promoted, new_rule_ids,
superseded_ids, tendency_count, event_count}`.

## The two-door reasoning (how to decide new_rules vs tendencies)

Apply these rules exactly when building your synthesis decision:

1. **Additive only.** Never regenerate the full permanent-rule set. Only
   propose NEW rules to add, or EXISTING active rules to supersede (by id, with
   a reason). Every active rule you don't explicitly supersede stays as is.
   `supersede` is the only way a permanent rule changes status — it flips to
   "superseded" (a status change), it is never deleted.

2. **Cite evidence.** Every new rule and every tendency must cite the
   `new_events` ids that support it, in `evidence_ids`. A rule with no evidence
   is rejected by the backend — do not propose one.

3. **Generalizable vs one-off.** Classify each edit before using it. A
   generalizable edit reflects a lasting preference (a phrasing habit, a
   structural preference, a recurring correction). A one-off is specific to
   that single article (a fact correction, a typo, a detail unique to that
   story) and earns nothing — no rule, no tendency.

4. **Two-door promotion.** If the operator's feedback contains an explicit
   directive (words like never, always, stop, from now on, don't, must),
   propose it as a **new permanent rule** immediately (`new_rules`). If the
   evidence instead shows a silent, repeated preference with no explicit
   directive, propose it as a **provisional tendency** (`tendencies`), never a
   permanent rule. Do not promote a silent pattern to a permanent rule
   yourself; that path runs through repeated tendency evidence over time.

5. **Contradiction → supersede.** If an edit contradicts an existing active
   rule, propose that rule in `supersede` with the reason, alongside any new
   rule the edit implies.

## Rule promotion and the undo notice

When your synthesis promotes a rule, the **next `save-draft` call's JSON carries
it in `pending_rule_notice`** — e.g. "Applied a new rule: never use exclamation
points. Tap to undo." Surface it to the operator when non-null; each notice
shows exactly once (the CLI marks it shown after returning it). If the operator
disagrees with a promoted rule, the natural path is another `edit` round whose
feedback contradicts it — the next synthesis pass reads that edit and you
propose superseding the rule.

Thrash guard: if recent edit effort is spiking, `synthesis-context` returns
`promotion_allowed: false`; that approval promotes no permanent rules, but
provisional tendencies still rebuild. Nothing extra to do — just expect a draft
after a spiking stretch may not show a new rule even on directive-looking
feedback.
