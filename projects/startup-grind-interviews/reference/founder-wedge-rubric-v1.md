# Founder-Wedge Filter — Rubric v1

Purpose: over the full 732-nugget gold set, surface the nuggets that trigger a founder's
"there's something here" reaction — narrower than `opportunity_signal` (which only means
"buildable/solvable pain point at all"). A nugget passes only if it triggers ONE of two
specific reactions:

1. **Automate/AI it** — the nugget describes a manual, repetitive, or judgment-patternable
   task/process/decision that today's AI (LLMs, agents, extraction, generation, matching)
   could plausibly automate or 10x-augment. The wedge is a product you'd build.
2. **Sharp pain worth digging** — the nugget names a *specific, acute, recurring* pain felt
   by an *identifiable segment* (this kind of business / this kind of user), concrete enough
   that you'd want to go interview 10 more people who have it. The wedge is a validated-hunch
   worth customer discovery.

Both are about *forward opportunity*, not "good advice." A wise generic lesson (hire slow,
culture matters, be resilient) is NOT a wedge. A pattern only counts if you can point at who
hurts and what you'd build or investigate.

## Per-nugget output fields (added to each nugget)

- `founder_wedge` (bool) — passes the filter or not.
- `wedge_kind` (`"automate"` | `"pain"` | `"both"` | `null`) — which reaction; `null` if not a wedge.
- `wedge_score` (int 1–5, or `null` if not a wedge) — sharpness/promise, anchored below.
- `wedge_note` (string, or `""`) — ONE line: name the wedge — what you'd build (automate) or
  who you'd go interview and about what (pain). Not a restatement of the nugget.

## `wedge_score` anchors (be strict — most nuggets are NOT wedges)

- **5** — Sharp, specific, obvious segment pain AND a clear thing to build/validate. You could
  write the landing page today. (Rare.)
- **4** — Clear pain + clear segment; the wedge is real but needs one inference to see the
  product, or the segment is niche.
- **3** — Genuine signal but fuzzy on either the pain-sharpness or the who; worth a look, not a
  conviction bet. (Default for a real-but-soft pass.)
- **2** — Marginal. A wedge only if you squint; likely a generalizable practice dressed as pain.
- **1** — Barely. Included so it's visible, but you'd almost certainly trim it.

If it's not a 2+, set `founder_wedge=false`. When torn between false and a 2, lean false —
Howard wants a filter, not a dragnet.

## Hard excludes (never a wedge, regardless of how interesting)

- Fundraising / financing / cap-table / equity-structure mechanics (same exclusion as
  `opportunity_signal`: VC pitch, valuation, debt vs. equity, LLC vs. C-corp, vesting, 83(b),
  board paperwork). Investing *as the interviewee's own business* is fine to consider, but the
  generic "how to raise" advice is out.
- Generic leadership/culture/resilience/mindset wisdom with no identifiable hurting segment.
- Pure personal-narrative or historical color with no transferable pain.
- Macro/industry observation you couldn't act on ("the market is shifting to X").

## Calibration examples (apply consistently)

- "We manually reconcile every affiliate payout in spreadsheets across 40 partners each month" →
  `automate`, score 4–5, note: "agent that ingests partner reports and reconciles payouts."
- "Contractors lose bids because they can't produce an estimate fast enough on-site" →
  `pain`, score 4, note: "interview GCs on estimate turnaround; on-site AI estimator."
- "Hire people who admit mistakes; we never fire for the mistake, only for hiding it" →
  NOT a wedge (generic hiring wisdom, no segment/product). `founder_wedge=false`.
- "Managing investor information flow tightly during a raise gives you leverage" →
  hard-excluded (fundraising mechanics). `founder_wedge=false`.
