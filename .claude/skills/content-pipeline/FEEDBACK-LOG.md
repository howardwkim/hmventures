# Content Pipeline — Feedback Log

Change requests captured while evaluating the skill. Each entry: timestamp + verbatim-intent feedback.

---

## 2026-07-10 14:08 PDT — Startup orientation should be a programmatic status + numbered menu

On skill startup, don't just dump the queue. Programmatically fetch and display where everything stands:
- how many candidates are in review,
- how many have been chosen to potentially write about,
- how many have been written but are still in the draft stage.

Grab that state programmatically and spit it out so we know where things are at.

Then the agent asks **"what do you want to work on?"** and presents the options as a **numbered list** (1, 2, 3, 4…). Each number maps to a step:
1. Review the idea candidates
2. Answer interview questions on one of the chosen items
3. …etc. (draft, edit, etc.)

Behavior rules for the menu:
- If a category has **only one option**, intelligently jump straight into it (skip the "which one?" prompt).
- If a category has **more than one option**, jump into that step and then ask **which one**.
- The user can also name a specific item directly ("let's work on this item"). Since each item is unique, infer which step is needed from the item and go there.

---

## 2026-07-10 14:28 PDT — No reset path for a stuck article; and changing the questions orphans recorded answers

Observed: an article sitting in `interviewing` status with **zero answers recorded** reads as "stuck mid-interview," but there's no way to move it back. There is no CLI verb to reset an article's status backward, and no distinct "picked but not yet started" article state — once a candidate is picked, the article jumps straight to `interviewing`.

Want a real **reset-to-picked** path (a way to send a stuck/parked article back to an in-progress-but-not-interviewing state) distinct from active interviewing.

Related concern that complicates resuming: interview **answers are stored keyed to the question text**, and the questions are agent-generated from a swappable guide (`references/interview-guide.md`). If we change the questions in the guide, a partially-interviewed article's recorded answers are pinned to questions that no longer exist — so resuming it doesn't cleanly line up. Need to decide how resume should behave when the question set has changed since the answers were recorded (e.g. re-ask from scratch, or map old answers forward).

---

## 2026-07-10 14:40 PDT — BUG FIXED: `status` dropped picked-but-not-started candidates

Symptom: 10 candidates existed but `status` only accounted for 9 (8 review-queue + 1 in-progress article). A candidate decided `yes` but not yet started as an article ("My business made only $62 yesterday") was counted nowhere and vanished from the overview.

Root cause: `cmd_status` (cli.py) called `writing.next_candidate()` but used it only as the `next_article_available` boolean — it never counted the accepted-but-not-started bucket, and it never counted articles by status either. So drafts would have been invisible for the same reason.

Fix applied (this session):
- Added `writing.pipeline_counts()` returning `picked_not_started_count` (candidates `status='yes'` with no article) and `articles_by_status` (article counts grouped by status).
- Wired both new fields into the `status` JSON output.
- Verified on the live DB: now reports `review_queue_count: 8`, `picked_not_started_count: 1`, `articles_by_status: {"interviewing": 1}` — 8 + 1 + 1 = 10. Full test suite: 99 passed.

This directly delivers the "chosen to potentially write about" and "drafted" counts that feedback #1 (startup orientation) asked for. Startup orientation logic (the numbered menu / auto-jump behavior) is still outstanding.

---

## 2026-07-10 — Interview asked too many questions; want a hard three-question cap

Observed: on the "AI is ruining business" article, the interview walked four of the five
dimensions in `references/interview-guide.md` before the operator stopped it. The operator's
expectation is **three questions**, not five.

Root cause: the guide lists five content dimensions and says only "stop when you have enough…
do not interrogate" — no explicit cap. The agent read that as "walk the list" and kept going.

Want: a **hard cap of three questions** for the interview. Encode it in the guide (and/or the
skill's step 4) so the agent picks the three highest-value dimensions for the candidate and
stops, rather than probing all five. Decide which dimensions are droppable vs. always-ask.

---

## 2026-07-10 — Synthesis should run automatically, no approval prompt

The skill treats synthesis (step 9) as a stopping point and asks "run synthesis now?" before
running it. Don't. Synthesis should just run automatically after approval (and whenever
`synthesis_pending` is set) without asking for the operator's go-ahead. It is a mandatory,
low-stakes learning step, not a decision the operator needs to gate. Remove the confirm-first
behavior for synthesis specifically (other mutating steps keep their go-ahead).
