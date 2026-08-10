# Startup Grind Interviews — CURRENT

**Last updated:** 2026-07-21

**Next:**
- Now: Design and run a new founder-wedge filter over the full 732-nugget gold set (all 50 interviews): pull nuggets where the reaction is either "I could automate/AI this" or "this is a real, sharp pain point for this type of business/user, worth digging deeper into." This is narrower than the existing opportunity_signal tag (which just means buildable/solvable pain point) — no rubric or script exists for it yet, needs designing from scratch next session.
- On deck: Run the existing tagging passes (reference/nugget-tagging-prompt-v1.md, reference/opportunity-topic-taxonomy-v1.md via scripts/tag_nuggets.py + scripts/tag_opportunity_topics.py) over the 33 newly extracted interviews — only the original 17 are tagged so far. Then regenerate data/opportunity_review.md (scripts/generate_opportunity_review.py) and do a fresh review pass over the full 50. Also still open: final presentation format for the gold output (structured dataset vs. readable doc) — deliberately deferred until the full dataset was in hand, which it now is.

**Standing constraints:**
- Gold-extraction method (Agent tool, one Sonnet subagent per interview, single-pass, no chunking, locked prompt reference/gold-extraction-prompt-short-v1.md) is settled — reuse as-is for any future re-extraction, don't re-derive.
- Nugget-tagging rubric (reference/nugget-tagging-prompt-v1.md) and opportunity-topic taxonomy (reference/opportunity-topic-taxonomy-v1.md) are locked — reuse verbatim for consistency, don't re-derive.
- data/silver/interviews.jsonl has 52 lines for 50 unique video_ids (qrv_7hxM8PM, XDCrar4JBoQ each duplicated, confirmed byte-identical) — not deduped at the source; don't double-extract or double-count these two.

**Canonical assets:**
- Gold nuggets → data/gold/<video_id>.json → authoritative extracted-insight output, one file per unique interview, all 50 present, schema {video_id, interviewee_name, interviewee_title, nuggets:[{category,summary,quote}]}
- Extraction prompt → reference/gold-extraction-prompt-short-v1.md → locked prompt for any future gold extraction
- Tagging rubrics → reference/nugget-tagging-prompt-v1.md, reference/opportunity-topic-taxonomy-v1.md → locked enrichment criteria, applied to 17/50 interviews so far

**Key decisions:** All 50 unique interviews now have gold files (732 nuggets total) as of 2026-07-21. Full decision history: reference/decisions.md.
**Session ref:** `claude --resume b626e2da-c957-4e15-8e1d-be4d14bbadb1`

<!-- summary:end -->

## Extraction Status

All 50 unique interviews now have gold files (2026-07-21) — the 33 remaining were extracted this
session via 33 parallel Sonnet subagent calls (Agent tool, 4 batches), using the locked
`gold-extraction-prompt-short-v1.md`, one subagent per interview, no chunking. 447 nuggets
extracted across the 33, on top of the original 17's 285 — 732 gold nuggets total, not yet all
tagged (see Next above).

Two of the 33 (`qrv_7hxM8PM` Tim Porter, `XDCrar4JBoQ` Scott Berkun) were the silver-layer
duplicate rows flagged below — confirmed byte-identical transcripts, so each was extracted once,
resolving that open question. Sally Bergesen (`HIRM3UbIcYc`) got a real extraction pass this
session, replacing the earlier validation-only run that was never saved to `data/gold/`.

One subagent (Dan Price, `oFDwLF8ZwbY`) pre-emptively added the not-yet-run tagging fields
(`opportunity_signal`, `small_business_focus`, `opportunity_topic`, `signal_strength`) to its
output, apparently copying an existing tagged file's shape — stripped back to the plain
`{category, summary, quote}` schema so all 33 are consistent ahead of the real tagging pass.

Note: `data/silver/interviews.jsonl` still has 52 lines for 50 unique `video_id`s (the two
duplicate rows above) — not deduped at the source, just not double-extracted.

## Gold-Extraction Method

Agent tool, one Sonnet subagent per interview, no raw Anthropic API calls, no model override,
single-pass on the full transcript (no chunking — chunking was a local-model technique to
compensate for a smaller model's recall gap; Sonnet doesn't need it here, though a 2026-07-16 test
found chunking improves Sonnet's own recall too — not adopted for these batches since that wasn't
the ask). Output files land in `data/gold/<video_id>.json`, schema: `{video_id, interviewee_name,
interviewee_title, nuggets: [{category, summary, quote}]}`. Extraction prompt:
`reference/gold-extraction-prompt-short-v1.md` (locked 2026-07-17, see decisions below). Design
history and original-prompt validation in `reference/gold-extraction-prompt-drafts.md`.

All 50 unique interviews are now extracted (see Extraction Status above). Presentation format for
the gold output (structured dataset vs. readable doc) is still undecided — see Next.

## Nugget Categorization

This is an enrichment pass on top of the gold layer (tags the nuggets that already exist, doesn't
re-derive anything from the transcript) — not a new named layer between silver and gold.

Every nugget in the 17 already-extracted `data/gold/*.json` files now carries two added bool
fields: `opportunity_signal` and `small_business_focus`. Applied by hand-reading all 285 nuggets
and encoding judgments in `scripts/tag_nuggets.py` (re-runnable, writes tags back into the gold
files — not yet applied to the 33 remaining interviews, see On Deck above). Locked rubric:
`reference/nugget-tagging-prompt-v1.md` — reuse this verbatim for future tagging passes so results
stay consistent; don't re-derive the criteria from scratch.

- `opportunity_signal`: pain-point/insider-knowledge framed around customer-discovery thinking —
  would this reveal something buildable/solvable for this person's business? Excludes
  fundraising/financing/deal-and-equity-structure content broadly, not just VC pitch/valuation
  mechanics — also debt vs. equity choice, LLC vs. C-corp, revenue-share/profit-share models, cap
  tables, stock options, vesting, board-approval paperwork for equity. Operational, product, and
  customer pain points at any company scale are in scope.
- `small_business_focus`: independent tag, not a filter — true when the nugget's subject or advice
  is specifically about, or directly usable by, a small/bootstrapped/lifestyle business (most
  interviewees here are VC-backed founders/investors, so this is the minority tag: 41/285).

Rubric history: the first pass (130/285 opportunity_signal=true) excluded only VC-pitch/valuation
mechanics. A Howard review pass over ~25 sampled nuggets flagged 6 false positives, all financing
or equity-structure content that wasn't literally about pitching a VC — SparkToro's LLC
profit-share structure, LiquidPlanner's SaaS Capital debt round, an 83(b) election detail, an
undocumented-stock-option-grant nugget, a Convoy nugget justifying the choice to raise VC funding
(vs. bootstrap) for speed, and Starbucks funding store expansion from cash flow instead of debt.
The rubric was widened same-day to exclude financing/deal/equity-structure content generally
(regardless of whether a VC is involved), landing at 124/285. One item was explicitly left
unresolved on Howard's call: whether a Dave Parker LTV:CAC-plus-validation-ladder nugget should
count — currently still tagged true, revisit if it comes up again.

Results: 124/285 nuggets tagged `opportunity_signal=true`, 41/285 tagged
`small_business_focus=true`. Strongest concentration of opportunity-signal nuggets: Dave Parker
(15/20 — CodeFellows CEO, mostly bootstrapped-validation tactics), Joe Heitzeberg (12/16 — Crowd
Cow), Glenn Kelman (12/16 — Redfin), Marc Barros (14/24 — Moment/Contour). Lightest: Bill Bryant
and Julie Sandler (VC partners, content skews toward financing/deal mechanics that are explicitly
excluded).

**Second enrichment pass (2026-07-17):** the 124 opportunity_signal nuggets now also carry
`opportunity_topic` (one of 8 business-function buckets) and `signal_strength` (A/B/C, how
directly the nugget reveals something buildable vs. just a replicable practice or color).
Rubric: reference/opportunity-topic-taxonomy-v1.md. Applied by hand via
scripts/tag_opportunity_topics.py. Reviewable output regenerated via
scripts/generate_opportunity_review.py into data/opportunity_review.md.
