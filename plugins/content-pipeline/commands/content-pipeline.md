---
description: Run the content pipeline — orient on the queue, review candidates, write, edit, approve, and learn style.
---

Invoke the `content-pipeline` skill and follow it exactly: orient with `status`
(and `review`), then proceed through whichever step applies (ingest, review,
decide, write-next, answer, draft-context/save-draft, edit, approve,
synthesis-context/apply-synthesis) per that skill's instructions. Do not
duplicate or reinterpret its flow here — that file is the single source of
truth.

If the user passed an argument after `/content-pipeline`, treat it as a
shortcut into a specific step (e.g. "review" → jump to the review step,
"status" → just run status and report). With no argument, start at orient.
