---
name: content-pipeline
description: Run the content pipeline. Discover candidate topics, review and decide which to pursue, interview and draft an article, take edit rounds, and approve. Use when the user says "run discovery", "check the review queue", "review topics", "write the next article", "what should I write about", "content pipeline", "draft the article", "pipeline status", or "/content-pipeline".
---

# content-pipeline

Drive the content pipeline from raw candidate topics to an approved article,
learning the operator's writing style as you go.

**You are the writer.** The Python backend is deterministic (it persists state
and does the bookkeeping math), and it never calls an LLM. Every piece of LLM
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
call**. Pass it explicitly every time, don't rely on an environment variable
or shell profile to fill it in. There is no fallback: `--db` unset and
`CONTENT_PIPELINE_DB` unset makes every verb exit with an error rather than
guessing a path. This is a code-level guard against an unconfigured
invocation (e.g. an ad hoc smoke test) silently landing on the wrong file.

**The operator's real pipeline DB is `~/.content-pipeline/pipeline.sqlite`.**
That is the canonical path for every real, operator-directed run of this
skill. Pass `--db ~/.content-pipeline/pipeline.sqlite` explicitly for real
work in this conversation.

**Mutating verbs need an explicit go-ahead first.** `decide`, `next-article`,
`answer`, `save-draft`, `edit`, `approve`, and `apply-synthesis` change real
pipeline state (they start articles, consume candidates, advance checkpoints).
Never run one speculatively or to "check that it works" (that includes while
developing or verifying changes to this skill or the CLI itself). If you need
to exercise a mutating verb for testing, pass `--db` pointing at a throwaway
file under the scratchpad directory, never
`~/.content-pipeline/pipeline.sqlite`.

## The flow

Each numbered step below is a discrete stopping point. When one finishes, ask
the operator whether to proceed to the next step rather than continuing on
your own, e.g. after decisions are recorded, ask "start the next article?"
before running `next-article`; after a draft is saved, ask before moving into
the edit loop; after approval, ask before running synthesis (unless
`synthesis_pending` makes it mandatory first). Exception: within a step that
is inherently a back-and-forth (the edit loop's rounds), keep going per the
operator's ongoing feedback without re-asking each round.

### 1. Orient (`status` and `review`)
Start here. `status` returns `{review_queue_count, resumable_article,
next_article_available, calibration, edit_effort_trend, nudge, synthesis_pending}`.
Check `synthesis_pending`: if it is `true`, an article was approved but its
style-synthesis step never ran. Do step 9 for that outstanding article before
anything else. Run `review` to see the candidates awaiting a decision.

### 2. Ingest candidates (`ingest`)
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

### 3. Review and decide (`review`, `decide`)
Present the full candidate list to the operator top-down. For each decision:

```
decide CANDIDATE_ID yes|no|snooze [--note TEXT]
```

`yes` moves it toward writing, `no` drops it, `snooze` defers it until the next
day. Save as you go. Result: `{candidate_id, status}`.

### 4. Start the next article (`next-article`)
```
next-article
```

If an article is mid-flight, this resumes it: `{resumed: true, article_id,
status}`. Ask the operator "pick up where you left off?" before continuing.
If starting fresh: `{resumed: false, article_id, candidate_id, candidate:
{title, summary, url}, brand_context, style_context}`. Empty queue:
`{resumed: false, article_id: null}`.

There is **no `questions` field**. You generate the interview questions
yourself from the returned `candidate`, `brand_context`, and `style_context`.
Ask **one question at a time**. Never batch multiple questions into a
single message. For each question, offer a **recommended** answer (your best
read of the operator's take) and one **alternate**, and always allow
free-text or skip. Wait for the answer (and record it via `answer`) before
asking the next question. Converse naturally; don't interrogate.

Load `references/interview-guide.md` for the content dimensions to probe. It is
a swappable spec: change what gets asked by editing that file, not this skill.
**Ask at most three questions** — the guide names the two always-ask dimensions
plus one chosen for the candidate. Stop at three (fewer if you already have
enough for a brief); do not walk the whole list.

### 5. Record answers (`answer`)
After each answer:

```
answer ARTICLE_ID --question TEXT --chosen recommended|alternate|custom|skip [--text TEXT]
```

Result: `{article_id, recorded}`.

### 6. Brief, then draft (subagents)
The interview's answers become a **brief**, then the brief plus the voice doc
become a **draft**. Both are subagent steps.

**Brief-writer.** Load `references/brief-writer-prompt.md`. Read
`brief-writer-context ARTICLE_ID` ({answers, source_snippet, voice_doc}).
Dispatch a `Task` subagent with the prompt + that context; it returns the brief
JSON. Persist it:

    save-brief ARTICLE_ID --json '<brief JSON>'

**Drafter.** Load `references/drafter-prompt.md`. Read
`brief-context ARTICLE_ID` ({brief, voice_doc}). Dispatch a `Task` subagent; it
returns the full draft text. Show the operator, then persist:

    save-draft ARTICLE_ID --text "<the full draft>"

`save-draft` records a new draft version each call, so to **regenerate** (after
a changed brief or voice) just run the drafter again and `save-draft` the new
text. Surface `pending_rule_notice` if non-null.

### 7. Edit loop (edit subagent)
For each round of operator feedback: load `references/edit-prompt.md`, read
`edit-context ARTICLE_ID` ({current_draft, brief, voice_doc}), dispatch a `Task`
subagent with the prompt + context + the operator's verbatim feedback. It
returns the revised draft. Show it, then record the round:

    edit ARTICLE_ID --feedback "<verbatim operator feedback>" --text "<revised draft>"

Repeat per the operator's feedback until they approve. (This step is an inherent
back-and-forth; keep going without re-asking each round.)

### 8. Approve (`approve`)
```
approve ARTICLE_ID --text "<final text>"
```

Result: `{article_id, status: "approved"}`. Approve does **not** trigger
synthesis. That is the next step, and it is yours to run.

### 9. Synthesize style (`synthesis-context`, then `apply-synthesis`)
This is the learning step. Run it **every time you approve an article**
(`status.synthesis_pending` flags any approved article still missing it).

Load `references/synthesis-prompt.md` (it carries the full two-door reasoning).
Read `synthesis-context ARTICLE_ID`, dispatch a `Task` subagent with the prompt
+ that context; it returns the decision JSON. Persist it:

    apply-synthesis ARTICLE_ID --base-checkpoint <base_checkpoint> --json '<decision>'

Passing `base_checkpoint` back is required (idempotency). See
`references/synthesis-prompt.md` for the reasoning rules; do not restate them
here.

## Rule promotion and the undo notice

When your synthesis promotes a rule, the **next `save-draft` call's JSON carries
it in `pending_rule_notice`**, e.g. "Applied a new rule: never use exclamation
points. Tap to undo." Surface it to the operator when non-null; each notice
shows exactly once (the CLI marks it shown after returning it). If the operator
disagrees with a promoted rule, the natural path is another `edit` round whose
feedback contradicts it. The next synthesis pass reads that edit and you
propose superseding the rule.

Thrash guard: if recent edit effort is spiking, `synthesis-context` returns
`promotion_allowed: false`; that approval promotes no permanent rules, but
provisional tendencies still rebuild. Nothing extra to do, just expect a draft
after a spiking stretch may not show a new rule even on directive-looking
feedback.
