# Startup Grind Interviews — CURRENT

**Last updated:** 2026-07-17

**Next:**
- Now: Review data/opportunity_review.md (124 opportunity_signal nuggets, grouped into 8 topic buckets, A/B/C strength-tiered within each group — read A first). Regenerate anytime via `scripts/generate_opportunity_review.py` after re-tagging. Rubric: reference/opportunity-topic-taxonomy-v1.md.
- On deck: Once the review pass is done: continue extraction batches from the 33 remaining interviews (see Remaining Interviews section) using the locked short-v1 prompt, single-pass, no chunking, then re-run both tagging passes (reference/nugget-tagging-prompt-v1.md for opportunity_signal/small_business_focus, reference/opportunity-topic-taxonomy-v1.md for topic/strength) over the newly extracted batches. Also still open: final presentation format for the gold output (structured dataset vs. readable doc) once all 50 are extracted.

**Key decisions:** Gold-extraction prompt locked as reference/gold-extraction-prompt-short-v1.md (2026-07-17). The already-saved first 5 gold files are NOT being re-extracted (Howard's explicit call). Nugget-tagging rubric locked as reference/nugget-tagging-prompt-v1.md (2026-07-17, widened same day after Howard's review pass — see reference/decisions.md for the full why). Opportunity-topic taxonomy (8 buckets + A/B/C strength tier) locked as reference/opportunity-topic-taxonomy-v1.md (2026-07-17), applied via scripts/tag_opportunity_topics.py: 65 tier-A, 56 tier-B, 3 tier-C; topics led by leadership-founder (25), customer-discovery (23), growth-marketing (22). Full decision history: reference/decisions.md.
**Session ref:** `claude --resume 3611c9a3-f5ff-4797-b820-4b6f37c94c0d`

<!-- summary:end -->

## Remaining Interviews

33 remaining (excludes the 17 already extracted): 7TklH3CghgE (Britta Jacobs), qrv_7hxM8PM (Tim
Porter, dup row), oFDwLF8ZwbY (Dan Price), Hd5N-2rNOxc (Aaron Bird), 9lgBJ67YjQU (Bill Bryant, 2nd
interview), 4pd9BzxzFaU (Dan Levitan, 2nd interview), De5jtsW_-Lw (David Israel), vgPlJWUPEe4
(Hansen Hosein), eWCVFCL6DLc (Joe Roets), 7HaDTiploEg (Leslie Feinzaig), bEWSr_tdhyo (Mark Mader),
XDCrar4JBoQ (Scott Berkun, dup row), VLrTAPMDDOk (Kirby Winfield), Fm_iPtM0mqo (Nick Huzar),
IV5QDf5ITUk (Nick Soman), hBgQ9-WTwk0 (Rahul Sood), _X6B-SCm7HU (Rudy Gadre), HIRM3UbIcYc (Sally
Bergesen), Y6bP5bt9abc (Sanjay Parthasarathy), T1rBhAq8KZw (Sarah Bird), nNS-XZWNR8c (Scott Oki),
N2ZIwCy5Wn0 (Rian Buckley), SVXHN9qvYsQ (Eric Breon), yPug9Y8Z2FM (Nick Soman, 2nd interview),
2hQqBB37pwc (Peter Hamilton), aCOWjAE-YYQ (Robbie Bach), U7WPvIWUQno (Spencer Rascoff), pj4j4wKcVP4
(John Lauer), 5zmCJ3wNGvg (Chris DeVore), yJLnC9-ecRE (Oren Etzioni), DV8PM-byXjI (Len Jordan),
8PgYt_Hm930 (Jeana Jorgensen), eBqWDZTTlvg (Lisa Nelson). Includes Sally Bergesen — had the original
locked prompt run on her during earlier validation, but that output was never saved to `data/gold/`,
so she still needs a real extraction pass with the current locked prompt.

Note: `data/silver/interviews.jsonl` has 52 lines but only 50 unique `video_id`s — `qrv_7hxM8PM`
(Tim Porter) and `XDCrar4JBoQ` (Scott Berkun) each appear twice. Not yet deduped or investigated;
don't double-extract these when picking the next batch.

## Gold-Extraction Method

Agent tool, one Sonnet subagent per interview, no raw Anthropic API calls, no model override,
single-pass on the full transcript (no chunking — chunking was a local-model technique to
compensate for a smaller model's recall gap; Sonnet doesn't need it here, though a 2026-07-16 test
found chunking improves Sonnet's own recall too — not adopted for these batches since that wasn't
the ask). Output files land in `data/gold/<video_id>.json`, schema: `{video_id, interviewee_name,
interviewee_title, nuggets: [{category, summary, quote}]}`. Extraction prompt:
`reference/gold-extraction-prompt-short-v1.md` (locked 2026-07-17, see decisions below). Design
history and original-prompt validation in `reference/gold-extraction-prompt-drafts.md`.

Once all 50 unique interviews are extracted, still need to decide the presentation format for the
gold output (structured dataset vs. readable doc) — deliberately undecided, revisit with the full
dataset in hand.

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
