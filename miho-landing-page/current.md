# miho-landing-page — CURRENT

**Last updated:** 2026-07-31

**Next:**
- Now: Commit the insights work — nothing is committed in either repo. The nested web/ repo (howardwkim/miho-partners-landing, Vercel-linked) holds the whole insights section plus fixes to SiteNav/BookButton/page.tsx/globals.css/designs; hmventures holds reference/blog-plan.md, the decisions entries, this file and .claude/launch.json. Build and lint are clean. Committing web/ deploys to Vercel — so decide first whether the Insights nav link should ship before any real article exists, since /insights currently renders its empty state.
- On deck: Write the first real article (copy content/insights/_template.mdx). Separately and pre-existing, unrelated to this session: reference/copy-draft-v1.md still has no pricing set for the bottom services section.

**Standing constraints:**
- Never delete or empty web/content/insights/ — the article route resolves posts through a dynamic import and an empty directory fails the build outright. _template.mdx is permanent and stays draft:true.
- The guarantee gradient sweep (.guarantee-shimmer) is reserved for the money-back guarantee. A second use on any page destroys its meaning.
- Anything on the site not documented in the /designs style guide is ad hoc and should be fixed — new components get an entry there in the same change.
- Do not reopen design reference hunting — four rounds did not converge; design goes generative against the written brief.
- Trust is the single goal of the page; every design and copy choice serves it. One CTA everywhere: book the Time Saver Audit.
- Avoid the saturated AI-startup look: no near-black grounds, monospace/terminal type, purple-to-orange gradients, glow or grid overlays. The warm 'fall' palette family is admitted and is not covered by the gradient ban.
- Avoid the professional-services look (accountant/law firm) — Howard rejects it as boring.
- Select references for boutique presentation, not venture scale: no member counts, press logo walls, award laurels or Enterprise mega-menus.
- Keep design references and copy references as separate lists — a site can be right on arena and wrong on design.
- Read the MiHO brand ground-truth at hmventures/docs/miho/brand/ before writing any copy; do not duplicate it here.

**Canonical assets:**
- Design brief → hmventures/miho-landing-page/CLAUDE.md → the agreed look-and-feel and scope rules
- Insights build plan → hmventures/miho-landing-page/reference/blog-plan.md → the built architecture, article template rationale, and why the content directory can never be empty
- Design tokens → hmventures/miho-landing-page/reference/design-tokens-modernlife.md → the Modern Life extraction the palette derives from
- Live style guide → hmventures/miho-landing-page/web/app/designs/page.tsx → every colour, type size, device and component the site is built from; noindex, excluded from the sitemap
- Post authoring template → hmventures/miho-landing-page/web/content/insights/_template.mdx → the metadata contract and body conventions for a new article
- Founder photos → hmventures/miho-landing-page/assets/founders/ → Howard's and Mike's portraits plus Mike's transparent cutout
- Corey Gannon transcript → personal-ai/projects/video-clipper/work/greg-isenberg-corey-ganim-ai-business/transcript.txt → the source offer architecture; its $999 price is Gannon's, not MiHO's
- Design reference library → personal-ai/design/references/ → all 153 collected candidates, 27 tagged for this project
- Mike's public positioning → michaelgrabham.com → his own words for the same audience

**Key decisions:** The audit is $399 (not $999 — that figure is Gannon's source model). Insights lives at /insights inside the existing Next.js app, built on @next/mdx with local .mdx files; adding an article means committing one file. Articles alternate between Mike and Howard, bylined to the person plus "MiHo Partners" with no credential line. Five fixed categories filtered by chips; post images optional per article. Full reasoning in reference/decisions.md.
**Session ref:** `claude --resume 4260ea63-dde7-471d-bd4e-c0d2f44669d7`

<!-- summary:end -->

## Where the work stands

**The page is built.** `web/app/page.tsx` is a working single-route landing page — nav, hero
with both founder photos, problem, offer (three steps, $399, guarantee), objections, founder
bios, insights sampler, ladder, final CTA, footer. The Modern Life design tokens are live in
`web/app/globals.css` (spring greens, the warm fall family, neutrals), with Manrope for body
and Instrument Serif for the italic accent, plus three devices: highlighter swipe, guarantee
gradient sweep and a pure-CSS scroll reveal. Deployed via Vercel from
`howardwkim/miho-partners-landing`.

**Insights section — built.** `/insights` listing with category chips, `/insights/[slug]`
article template, homepage sampler, sitemap. Runs on `@next/mdx` with posts as `.mdx` files in
`web/content/insights/`. No real articles yet, so it renders its empty state.
`reference/blog-plan.md` is the architecture and the reasoning.

**Copy references.** Three consultancy sites are maybes, not settled models:

| Reference | Mine it for |
|---|---|
| Draft (draft.nu) | The offer ladder — Strategy Call → Teardown as low-risk entry → flagship engagement → retainer. Closest structural match to the Gannon model. Carries a numeric promise and humour in the headline. |
| Jonathan Stark (jonathanstark.com) | Problem-first framing. Headline is the reader's pain as a question; positioning is one plain sentence; the argument turns on a single reframe. |
| Greg Kogan (gkogan.co) | Solo-consultant credibility — blunt named founder testimonials plus one operator credential. CTA is literally "Email me". |

Secondary copy references, also maybes: Caboodle (caboodle.studio), Other Land
(otherland.studio), Test Double (testdouble.com). All three are right on arena and were
rejected on design.

**Design — resolved for the homepage, extends to insights.** Only two references were ever
accepted, both from the first batch: Modern Life (modernlife.com) and Boords (boords.com).
They remain the sole calibration points. The insights section reuses the existing tokens and
adds none — Modern Life's own insights pages are the reference for it, deliberately lighter
(no content-type taxonomy, no whitepapers or webinars, no sidebar).

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
