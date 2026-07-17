# Gold-layer extraction prompt — design history

Working notes on how the extraction prompt was designed. Kept so earlier drafts and
the reasoning behind each change aren't lost. **The prompt is locked as of
2026-07-15 — for the prompt text itself, use `reference/gold-extraction-prompt.md`.**
This file is the decision trail behind it: rounds 1-2, the rejected alternatives, and
the validation results.

## Final (locked) — 2026-07-15

Resolved the fixed-vs-adaptive question from the round-1/2 status note below:
**fixed, single prompt, no role/industry detection step** (an adaptive/detection
step was rejected on the same grounds Howard flagged earlier — it's another place
the pipeline can silently narrow the search). The fix for the round-1/2 categories'
VC-specific flaw was *not* Howard's rejected "cross-domain examples" approach —
instead, the same 5 shape-categories were kept (they're role-agnostic in structure)
but stripped of the VC-specific nouns baked into their wording (e.g. "deal term,"
"valuation," "startup/VC wisdom" → generic phrasing), plus one added catch-all
clause so a nugget that passes the core test but doesn't fit a listed shape still
gets included, tagged "other."

Validated two ways on this prompt, both via a Sonnet subagent (no raw Anthropic API
calls — consistent with the standing constraint):
1. **Same-transcript parity check** — reran both the round-2 (VC-flavored) and this
   generalized prompt on the same Jason Stoffer/Maveron transcript. Differences
   between the two runs were minor and read as ordinary LLM sampling noise, not a
   quality cost from generalizing the wording.
2. **Cross-domain test (the real test)** — ran this prompt on a non-VC interview
   (Sally Bergesen, CEO of Oiselle, women's running apparel — zero deal/VC content).
   Result: 26 nuggets, all genuinely operator/apparel-specific (MOQ thresholds, no
   formal contracts with overseas factories, the dated decision to exit Amazon,
   Nike's athlete-evaluation philosophy vs. Oiselle's, declining wearable tech on
   philosophical grounds), nothing forced into deal/metric framing. The "other"
   catch-all fired twice and correctly caught two nuggets that didn't cleanly match
   any of the five shapes, instead of dropping them or mangling them into the wrong
   bucket. This is the actual design goal working as intended.

**Locked prompt text:** `reference/gold-extraction-prompt.md`.

## History — how this was reached

Tested on one interview (Jason Stoffer / Maveron, `KtauDMsH-mA`), two rounds before
the final version above.
**Open decision, now resolved (see "Final" above):** whether the final prompt should
be a fixed "universal" prompt (one set of role-agnostic instructions, no
per-interview branching) or an "adaptive" prompt that detects the interviewee's
role/industry and reorients what it looks for. Howard's concern with the adaptive
route: an industry-detection step is another place the pipeline can silently
misfire and narrow the search — defeats the point of a single prompt.

## Draft v1 — fixed category list (VC-flavored, known problem)

Used for the first test pass. **Known flaw:** the five categories below were
reverse-engineered from what one VC interview happened to contain, not from a
role-independent definition of "gold" — e.g. `concrete-deal-detail` only makes
sense for someone who does deals. It would not have surfaced an operator-only
insight from an unrelated domain (e.g. a funeral home salesperson's non-obvious
lead-generation channel). Kept here as a reference point, not a candidate for the
final prompt as-is.

```
Extract "golden nuggets" — specific, hard-won, TACIT knowledge that only exists
because this particular person lived it. A nugget must be one of:
- A specific number, metric, or concrete detail (a real figure, timeline, deal
  term, headcount, valuation, etc. — not a rounded generality)
- A specific mistake the person made and what they actually learned from it
- A moment where their model of the world/industry changed — a real "I used to
  think X, then Y happened, now I think Z"
- A belief that contradicts conventional startup/VC wisdom
- A concrete, specific detail of how an actual deal, decision, or event unfolded

REJECT anything that is:
- Generic startup/VC advice a well-read outsider could write without having lived it
- Vague inspirational statements with no specific detail attached
- Standard industry facts/definitions anyone could look up
- Career-history narration with no extractable lesson
```

Secondary signal tested alongside this: host (Mike Grabham) reaction as
corroborating-not-load-bearing evidence. Confirmed unreliable as a strong signal
— transcript has no speaker diarization, so turn attribution is inference-only
(see session log). Treated as supporting evidence at most, never a gate.

### Round 1 output shape (also superseded)

First pass returned `quote` + one-line `paraphrase` as coequal fields. Howard's
correction: the quote is raw material (bronze-equivalent), not the deliverable —
a one-line paraphrase strips the context that makes a nugget legible without the
transcript. Fixed in round 2 by making a full contextual `summary` paragraph (3-6
sentences: setup, what happened, why it's non-obvious) the primary field, `quote`
demoted to backing citation. That output shape (summary-primary, quote-secondary)
is confirmed good and carries forward regardless of how the category question
resolves.

## Next

Category/prompt design is done — see `current.md` for the actual next step
(validation batch of 5 more interviews on the locked prompt).
