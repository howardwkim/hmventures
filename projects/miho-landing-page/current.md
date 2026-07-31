# miho-landing-page — CURRENT

**Last updated:** 2026-07-28

**Next:**
- Now: Copy draft v1 is complete — reference/copy-draft-v1.md. Full page copy (hero, problem, offer, objections, founder bios for both Mike and Howard, bottom services section, final CTA), following brand-voice.md. Founder bios were subagent-researched against real sources (Howard's career/resume files; Mike's from michaelgrabham.com) — not placeholders. One correction caught in the process: the draft's original Mike bio claimed unsupported advisory experience; replaced with his verified operator facts. One open item remains: pricing for the bottom services section (never set for MiHO — brand-dna.md's "TBD per project" was about Mike's old solo practice). Next: Howard reviews the full draft and gives feedback; decide services pricing or leave uncosted.
- Note: the `/landing-page-messaging` skill referenced in earlier session notes does not exist in this install — draft v1 was written directly instead.
- Logo generation: 4 options generated via gpt-image (`personal-ai/tools/openai-image/generate.py`), background-removed to transparent PNGs, in `assets/brand/` — option1-wordmark (clean wordmark, orange dot-accent on the 'i'), option2-mark-wordmark ("MiHO Partners" with an overlapping-circles partnership mark), option3-monogram-badge (circular "MH" seal), option4-hand-highlight (wordmark with a hand-drawn highlighter underline, echoing the "emphasis by hand" device below). Raw pre-key sources kept in `assets/brand/raw/`. Next: Howard picks a direction (or requests iteration).
- On deck: Whether to generate a photo of Mike and Howard together. Resuming design generatively against the written brief.

**Standing constraints:**
- Do not reopen design reference hunting — four rounds did not converge; when design resumes, go generative against the written brief.
- Trust is the single goal of the page; every design and copy choice serves it.
- Avoid the saturated AI-startup look: no near-black grounds, monospace/terminal type, purple-orange gradients, glow or grid overlays.
- Avoid the professional-services look (accountant/law firm) — Howard rejects it as boring.
- Select references for boutique presentation, not venture scale: no thousand-member counts, press logo walls, award laurels or Enterprise mega-menus.
- Keep design references and copy references as separate lists — a site can be right on arena and wrong on design.
- Read the MiHO brand ground-truth at hmventures/docs/miho/brand/ before writing any copy; do not duplicate it here.

**Canonical assets:**
- Design brief → hmventures/projects/miho-landing-page/CLAUDE.md → the agreed look-and-feel and scope rules
- Founder photos → hmventures/projects/miho-landing-page/assets/founders/ → Howard's LinkedIn portrait, Mike's LinkedIn portrait, and Mike's transparent-background cutout
- Corey Gannon transcript → personal-ai/projects/video-clipper/work/greg-isenberg-corey-ganim-ai-business/transcript.txt → the source offer architecture (audit into implementation ladder, seven acquisition channels)
- Design reference library → personal-ai/design/references/ → all 153 collected candidates, 27 tagged for this project, each with screenshot, provenance and accept/reject reasoning
- Mike's public positioning → michaelgrabham.com → his own words for the same audience (6X founder, small business expert, cash flow optimization, growth strategy, CEO group coaching)

**Key decisions:** Page architecture settled via grill-with-docs (2026-07-28): MiHO Partners is a distinct venture from Mike's solo brand, selling the audit-to-implementation offer specifically, not general consulting. Whole ladder shown, one CTA (book the audit); implementation/retainer get a real section at the bottom, no CTA of their own. Lead persona is the Ready-to-Grow Owner. Trust comes from founder operating history, not a client roster (none exists yet). Price shown, but in the offer section, not the hero. Entry offer is called "audit," always paired with a solutions qualifier. Audit carries a money-back guarantee conditioned on client follow-through, not a fixed day count. Full reasoning in reference/decisions.md.

Design direction is unresolved: only Modern Life (modernlife.com) and Boords (boords.com) were ever accepted, both from the first batch. Copy references Draft (draft.nu), Jonathan Stark (jonathanstark.com) and Greg Kogan (gkogan.co) are maybes, not settled models.
**Session ref:** `claude --resume 577f2059-1031-4b9f-8cd3-df366a0af825`

<!-- summary:end -->

## Where the work stands

**Copy — not started.** This is the live thread. Three consultancy sites are maybes, not
settled models:

| Reference | Mine it for |
|---|---|
| Draft (draft.nu) | The offer ladder — Strategy Call → Teardown as low-risk entry → flagship engagement → retainer. Closest structural match to the Gannon model. Carries a numeric promise and humour in the headline. |
| Jonathan Stark (jonathanstark.com) | Problem-first framing. Headline is the reader's pain as a question; positioning is one plain sentence; the argument turns on a single reframe. |
| Greg Kogan (gkogan.co) | Solo-consultant credibility — blunt named founder testimonials plus one operator credential. CTA is literally "Email me". |

Secondary copy references, also maybes: Caboodle (caboodle.studio), Other Land
(otherland.studio), Test Double (testdouble.com). All three are right on arena and were
rejected on design.

**Design — unresolved, parked.** Only two references were ever accepted, both from the first
batch: Modern Life (modernlife.com) and Boords (boords.com). They are the sole calibration
points. Everything found across three further rounds was rejected. The brief is agreed and
stable; what is missing is a page satisfying it.

The bar extracted from those two:
- Warm cream / off-white ground — never pure white, never dark
- Generous geometric sans with an editorial accent (italic serif, or highlighted phrases)
- One confident accent colour carrying the CTA — a real choice, not default blue
- Trust devices built into the hero rather than bolted on below it
- Human warmth in light mode
- Boutique presentation: named humans over logo walls, first-person voice, short nav ending
  in Book a call, personality in place of metrics

**Assets — ready.** Both founder headshots plus a transparent-background cutout of Mike, in
`assets/founders/`. Logo not started.

## One device worth using

Every small-practice site that landed well marks a single key phrase **by hand** — a
highlighter swipe or a coloured pull-out (Other Land, Test Double, Caboodle, Tally, Fathom).
Emphasis by hand rather than by scale. Small firms reach for it because they cannot lean on a
logo wall, which is exactly MiHO's position.
