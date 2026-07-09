---
name: content-pipeline
description: Run the content pipeline — discover candidate topics, review and decide which to pursue, interview and draft an article, take edit rounds, and approve. Use when the user says "run discovery", "check the review queue", "review topics", "write the next article", "what should I write about", "content pipeline", "draft the article", "pipeline status", or "/content-pipeline".
---

# content-pipeline

Drive the content pipeline from raw candidate topics to an approved article. The
backend is the `content_pipeline` CLI (Task E1) — a Python package with an
argparse entry point exposing 8 subcommands, each printing one JSON object to
stdout. This skill does not reimplement any of that logic; it just decides
*when* to call which subcommand and how to read the JSON back.

## Invocation

Every subcommand is run the same way, from inside
`plugins/content-pipeline/` in this repo:

```
uv run python -m content_pipeline.cli --db PATH <subcommand> [args...]
```

`--db` is a **top-level** flag (it comes before the subcommand name), pointing
at the pipeline's own sqlite database. If omitted, the CLI falls back to the
`CONTENT_PIPELINE_DB` environment variable, and if that's unset too, to
`~/.content-pipeline/pipeline.sqlite`. For a real operator run, pick one
pipeline DB (env var or `--db`) and use it consistently across the whole
session — the pipeline resumes from whatever's already in that database (e.g.
`write-next` will resume an in-progress article rather than starting a new
one).

Each CLI call opens its own connection and closes it — there is no persistent
process. Every subcommand prints exactly one JSON object; parse stdout as JSON
to read the result.

## The flow

Run these in order. `status` is a side-query you can call any time, not a
step in the sequence.

### 1. Discover — `discover`
Pull new candidate topics in from a source and ingest them into the pipeline DB.

```
discover --source reddit --digest-db PATH
```

Discovery is **pluggable by source** — `--source` selects the adapter
(`reddit` is the only one implemented so far, source #1). For `reddit`,
`--digest-db PATH` points at an *external* sqlite database — Howard's Hermes
Reddit-digest tool's own `digest_posts` table (post_id, subreddit, title,
reddit_url, summary, score, num_comments, upvote_ratio, quality_score,
why_care, digest_date). This pipeline never writes to that database, only
reads from it; if the path doesn't exist, `discover` degrades gracefully —
zero candidates ingested, no error. Result JSON: `{source, fetched, ingested}`.
Ingestion is idempotent (dedupes on source + source_ref), so re-running
`discover` against the same digest is safe.

### 2. Review — `review`
List candidates awaiting a decision.

```
review [--today YYYY-MM-DD]
```

Result JSON: `{today, count, candidates: [...]}`. `--today` overrides the
date used for queue placement — mainly for testing; omit it for real use.

### 3. Decide — `decide`
Record a decision on one candidate from the review queue.

```
decide CANDIDATE_ID yes|no|snooze [--note TEXT]
```

`yes` moves it toward writing, `no` drops it, `snooze` defers it (optionally
with `--note`). Result JSON: `{candidate_id, status}`.

### 4. Write next — `write-next`
Start the next accepted candidate, or resume one already in progress.

```
write-next
```

If an article is mid-flight (interviewing/drafting/reviewing), this resumes
it: `{resumed: true, article_id, status}`. Otherwise it starts the
highest-priority accepted candidate and returns interview questions:
`{resumed: false, article_id, candidate_id, questions}`. If the queue is
empty: `{resumed: false, article_id: null, questions: null}`.

### 5. Answer — `answer`
Record one answer to an interview question (repeat per question).

```
answer ARTICLE_ID --question TEXT --chosen recommended|alternate|custom|skip [--text TEXT]
```

`--chosen` picks which option was taken; `--text` supplies the actual answer
text (required unless skipping). Result JSON: `{article_id, recorded}`.

### 6. Draft — `draft`
Generate the first draft from the recorded interview answers and the current
style canon.

```
draft ARTICLE_ID [--research TEXT]
```

`--research` is optional extra source material to fold in. Result JSON:
`{article_id, draft, pending_rule_notice}`. **Always check
`pending_rule_notice`** — see "Rule promotion and the undo notice" below.

### 7. Edit — `edit`
Record one round of operator feedback plus the resulting revised text. Call
this once per edit round; repeat as many rounds as needed before approving.

```
edit ARTICLE_ID --feedback TEXT --text TEXT
```

`--feedback` is what the operator said about the previous draft;
`--text` is the new draft text after applying it. Result JSON:
`{article_id, round}` (the round number just recorded).

### 8. Approve — `approve`
Finalize the article. This also triggers the one synthesis pass that reads
this article's edit/interview events and updates the style canon.

```
approve ARTICLE_ID --text TEXT
```

`--text` is the final approved text. Result JSON: `{article_id, status}`
(`status` becomes `approved`).

### Status (side-query, any time) — `status`

```
status [--today YYYY-MM-DD]
```

Result JSON: `{review_queue_count, resumable_article, write_next_available,
calibration, edit_effort_trend, nudge}`. Useful for orienting at the start of
a session (is there a review queue to clear, an article to resume, etc.)
without changing anything.

## Rule promotion and the undo notice

After every `approve`, the pipeline runs one synthesis pass over that
article's edit rounds and interview answers to learn the operator's writing
style. Two doors:

- **Explicit directive** in an edit round's `--feedback` (words like "never",
  "always", "stop", "from now on", "don't", "must" — e.g. "never use
  exclamation points") → promoted to a **permanent rule** immediately, applied
  to the style canon used by the *next* `draft` call.
- **Silent, repeated pattern** with no explicit directive → recorded only as a
  **provisional tendency** (rebuilt wholesale each synthesis run), which needs
  more accumulated evidence before it can ever become a permanent rule.

When a rule was just promoted, the **next `draft` call's JSON output carries
it in `pending_rule_notice`** — a string like "Applied a new rule: never use
exclamation points. Tap to undo." Surface this to the operator when you see a
non-null `pending_rule_notice`; each notice is shown exactly once (the CLI
marks it shown internally after returning it). If the operator disagrees with
a promoted rule, the natural path is another `edit` round whose feedback
contradicts it — two contradicting edits demote (supersede) the rule rather
than deleting it.

There is also a thrash guard: if recent edit effort is spiking, promotion is
paused for that approval (no new permanent rules), but provisional tendencies
still rebuild. This is internal to the CLI — nothing extra to do here, just be
aware a `draft` after a "spiking" approval may not show a new rule even if the
feedback looked directive.

## Notes

- Discovery is pluggable by design — `reddit` is source #1, more sources can
  be added later without changing this flow; just check `discover --help` (or
  this file, once updated) for what `--source` values exist.
- There is no separate backend-adapter file for this skill (unlike
  `social-post`'s swappable-backend pattern) — the "backend" already is the
  `content_pipeline` CLI itself, so there's nothing to swap.
