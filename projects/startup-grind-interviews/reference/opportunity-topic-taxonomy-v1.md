# Opportunity-Signal Topic & Strength Taxonomy (v1)

Locked 2026-07-17. Second enrichment pass on top of the `opportunity_signal=true` subset
(124/285 nuggets) — adds a topic bucket and a strength tier so those 124 are reviewable without
reading each one individually. Reuse this rubric verbatim for future tagging passes on the 33
remaining interviews once they're extracted and tagged for `opportunity_signal`.

## Topic (8 buckets)

Every `opportunity_signal=true` nugget gets exactly one topic — the business function the
pain-point/insight is about:

- `customer-discovery` — validating demand, talking to prospects, idea selection, problem
  identification before building
- `product-mvp` — what to build, how much to build, MVP philosophy, product scope decisions
- `growth-marketing` — acquisition channels, branding, positioning, distribution, PR
- `hiring-people` — recruiting, interviewing, firing, team structure, talent pipeline
- `pricing-economics` — pricing mechanics, unit economics (LTV/CAC, margins), non-financing
  business-model choices (bootstrapping cash flow, freemium fit) — distinct from the
  fundraising/equity-structure content `opportunity_signal` already excludes
- `ops-failure` — operational breakdowns, process/instrumentation gaps, failure-mode detection
- `leadership-founder` — founder psychology, decision-making under pressure, delegation, CEO
  transition, layoffs-as-leadership-act, co-founder dynamics
- `market-timing` — competitive dynamics, being early/late, market sizing, structural market
  shape

Some nuggets plausibly span two buckets (e.g. a hiring practice that's also a leadership
lesson) — pick the single bucket that's the nugget's primary point, not every bucket it touches.

## Strength tier (A/B/C)

Ranks how directly the nugget reveals something buildable/solvable — the same "would this
reveal something buildable/solvable" test from the `opportunity_signal` definition, not a
generic quality score:

- **A — live gap**: names a specific unsolved pain point, inefficiency, or market gap that
  reads as a startup-shaped hole, or a concrete/highly-generalizable mechanism a founder could
  act on directly (e.g. Crowd Cow's silent warehouse order loss, LiquidPlanner's
  under-instrumentation problem, the Sounders' immigrant-talent scouting blind spot)
- **B — replicable practice**: a tactic or heuristic that worked for this person, copyable by
  another founder, but describes a known move rather than surfacing a new gap (Parker's
  ascending-dollar validation ladder, Heitzeberg's cheap-to-expensive demand ladder)
- **C — color/anecdote**: instructive context or a war story, not directly actionable as a
  wedge (Bryant's QPass burn story, Moment's two-Kickstarter-campaigns aside)

Read order: A, then B, skim C.

## Mechanics

Same pattern as `nugget-tagging-prompt-v1.md`: hand-read all 124, encode judgments in
`scripts/tag_opportunity_topics.py`, write `opportunity_topic` and `signal_strength` back into
the `data/gold/*.json` files. Only nuggets with `opportunity_signal=true` get these two new
fields; all others are left untouched.
