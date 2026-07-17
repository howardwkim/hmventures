# Decisions

> Append-only ledger (reversal preset in correction-handling): superseded entries stay; the why is the point.

## 2026-07-17 — Widen opportunity_signal tagging rule to exclude financing/equity-structure content broadly
**Decision:** opportunity_signal now excludes any financing/deal/equity-structure content (debt vs. equity choice, LLC vs. C-corp, revenue-share models, cap tables, stock options, vesting, board-approval paperwork for equity), not just narrow VC-pitch/valuation mechanics. Locked rubric: reference/nugget-tagging-prompt-v1.md. Re-tagged the 17 gold files: opportunity_signal=true count went from 130/285 to 124/285.
**Why:** Howard reviewed ~25 sampled tagged nuggets and rejected 6 as false positives, all financing/equity-structure content that wasn't literally a VC pitch or valuation mechanic (SparkToro's LLC profit-share structure, LiquidPlanner's SaaS Capital debt round, an 83(b) election detail, an undocumented stock-option-grant nugget, a Convoy nugget justifying raising VC funding over bootstrapping, Starbucks funding expansion from cash flow instead of debt). The original rule's exclusion boundary was too narrow.
**Session ref:** `claude --resume 3611c9a3-f5ff-4797-b820-4b6f37c94c0d`
