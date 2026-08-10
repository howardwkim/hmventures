# Decisions

> Append-only ledger (reversal preset in correction-handling): superseded entries stay; the why is the point.

## 2026-07-21 — Silver-layer duplicate rows are byte-identical — extract once each
**Decision:** qrv_7hxM8PM (Tim Porter) and XDCrar4JBoQ (Scott Berkun), the two video_ids with 52 vs 50 unique rows in data/silver/interviews.jsonl, were diffed and confirmed byte-identical duplicate rows (not two different interviews or transcript variants). Extracted one gold file per video_id; the second copy was not used.
**Why:** current.md had flagged this as unresolved ("not yet deduped or investigated") ahead of this session's extraction batch. Needed to know whether to treat them as two distinct interviews (extract both) or one duplicated row (extract once) before running the batch — a full-file diff settled it cheaply.
**Session ref:** `claude --resume b626e2da-c957-4e15-8e1d-be4d14bbadb1`

---

## 2026-07-17 — Widen opportunity_signal tagging rule to exclude financing/equity-structure content broadly
**Decision:** opportunity_signal now excludes any financing/deal/equity-structure content (debt vs. equity choice, LLC vs. C-corp, revenue-share models, cap tables, stock options, vesting, board-approval paperwork for equity), not just narrow VC-pitch/valuation mechanics. Locked rubric: reference/nugget-tagging-prompt-v1.md. Re-tagged the 17 gold files: opportunity_signal=true count went from 130/285 to 124/285.
**Why:** Howard reviewed ~25 sampled tagged nuggets and rejected 6 as false positives, all financing/equity-structure content that wasn't literally a VC pitch or valuation mechanic (SparkToro's LLC profit-share structure, LiquidPlanner's SaaS Capital debt round, an 83(b) election detail, an undocumented stock-option-grant nugget, a Convoy nugget justifying raising VC funding over bootstrapping, Starbucks funding expansion from cash flow instead of debt). The original rule's exclusion boundary was too narrow.
**Session ref:** `claude --resume 3611c9a3-f5ff-4797-b820-4b6f37c94c0d`
