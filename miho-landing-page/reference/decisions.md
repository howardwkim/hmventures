# Decisions

> Append-only ledger (reversal preset in correction-handling): superseded entries stay; the why is the point.

## 2026-07-31 — Article byline shows the firm, not a founder credential
**Decision:** The article byline is headshot, name, and "MiHo Partners" — not a one-line credential. Articles still alternate between Mike and Howard.
**Why:** Howard's call on seeing it built. The credential under every single article reads as selling rather than writing, and repetition drains it: a résumé line that appears on all content stops being proof and becomes a signature block. The face and the name still carry the human trust the byline exists for, and anyone who wants the background has the nav one click away. The earlier reasoning — that a search visitor never sees the homepage, so the article must carry founder proof alone — was not wrong, it was outweighed: the photo and named human do most of that work without the cost.
**Supersedes:** Article template carries founder proof and a required takeaway block (2026-07-31)

---

## 2026-07-31 — Modern Life's warm 'fall' colour family is admitted to the palette
**Decision:** The fall family from the Modern Life extraction is available to MiHO: fall-deep #bb4038 brick red, fall-vibrant #ff8061 coral, fall-bright #f8a08c peach, fall-medium #f2e0ca tan, fall-light-50 #f8efe5 pale peach, fall-mute #fff6e9 cream-peach. Also promotes the already-permitted but unused spring-bright #f4ffb0 lime. The design brief's ban on purple-to-orange gradients as AI-startup styling still stands — this admits Modern Life's specific warm family, not orange gradients generally.
**Why:** Howard reviewed modernlife.com directly and judged our page too narrow on colour: we shipped greens and neutrals only while the reference site runs lime, red/orange and tan. He reversed his own earlier ban. That ban was not wrong when made — it is superseded. Two things a future session should not re-derive: on Modern Life these warm tones are illustration-only and never UI accents, so using them as UI accents goes further than the reference does and is a deliberate departure; and the lime was never banned at all, it sits in the permitted spring family and was simply unused, so it costs no decision. Rejected alternative: deferring until the /designs style guide page existed to show the whole palette side by side, so the call could be made against the real thing rather than hex values. Howard chose to reverse now rather than wait.
**Supersedes:** MiHo's brief bans the fall orange family (recorded in reference/design-tokens-modernlife.md, 2026-07-28)

---

## 2026-07-31 — Post images are optional per article, never required
**Decision:** The image field on a post is optional. Both the article template and the listing row must render correctly with or without one — article goes byline straight to body when absent; listing uses a fixed row height with the thumbnail slot filled or collapsed, not a masonry grid that reflows around missing images.
**Why:** Howard's explicit call: do not remove the optionality, since we may or may not want an image on any given piece. Rejected the proposal to ban article images entirely — that argument was that AI-generated header art is a loud machine-written tell and works against trust, which is the page's only goal, and that the brief already calls for a type-, layout- and colour-led design. The concern is real but does not justify foreclosing the choice; it argues for restraint per article, which optionality permits and a ban does not.

---

## 2026-07-31 — Five fixed categories as a type union, filtered by chips, no per-category routes
**Decision:** Insights posts carry one category from a fixed set of five — Time drains, AI tools, Operations, Delegation & hiring, Pricing — declared as a TypeScript union in one file. The listing is a flat reverse-chronological list with category filter chips above it. No sidebar navigation, no per-category routes or landing pages, no content types, no pagination until it is actually needed.
**Why:** Howard wanted categories but not Modern Life's taxonomy weight — their insights page is a content library with seven categories, sidebar filtering, whitepapers, webinars and gated PDFs. Chips over a flat list give the organising signal without the machinery or the empty-archive problem that per-category landing pages create at low post counts. The union type rather than free-text strings matters specifically because articles are machine-written and nobody proofreads frontmatter: a misspelled or invented category fails the build instead of silently creating a ghost category. Rejected: no categories at all, which was proposed first on the grounds that under twenty posts categories are furniture — Howard overrode it.

---

## 2026-07-31 — Article template carries founder proof and a required takeaway block
**Decision:** The article page adds three things Modern Life's article pages lack: a one-sentence deck in Instrument Serif italic under the title, a byline block with the author's headshot, name and one-line credential, and a required Takeaway component holding a concrete punch list near the end. Articles alternate between Mike and Howard. Explicitly excluded: table of contents, share buttons, comments, newsletter signup, author archive pages, reading-progress bars. One CTA per article — book the audit.
**Why:** A visitor arriving from search has never seen the homepage, so the article page must carry the founder proof on its own or it builds trust for nobody — and founder operating history is the only trust device MiHO has, there being no client roster. Modern Life's article pages were judged too sparse to lift directly: title, category, date, image, subheads, related links, nothing that does anything with the article. The Takeaway block is structural rather than decorative because MiHO's offer is prescription not diagnosis (see the 2026-07-28 entry on the solutions qualifier); an article ending on a platitude contradicts what is being sold, and a required punch-list slot is the mechanism that stops machine-written content drifting into generic business advice. Alternating named bylines with headshots was Howard's call, to make the section read as two people writing rather than a content feed. The excluded elements are all weight Modern Life carries as a content library with whitepapers and webinars; under twenty posts a table of contents is theater.

---

## 2026-07-31 — Blog tooling is the official @next/mdx plugin, not a third-party content layer
**Decision:** Articles are local .mdx files at web/content/insights/, rendered through @next/mdx with remark-gfm and rehype-slug. Frontmatter is a typed exported metadata object rather than YAML validated by a schema library. Adding an article means committing one file.
**Why:** The app runs Next 16.2.12 and @next/mdx publishes at 16.2.12 — same release train, Turbopack support documented by the Next team. Chosen over content-collections (128k weekly installs) and Velite (80k), both of which are pre-1.0 and wrap next.config with their own build plugin while documenting neither Next 16 nor Turbopack; that coupling is precisely what stranded Contentlayer users when Next moved underneath them, and Contentlayer is now unmaintained. Also rejected next-mdx-remote (936k installs, healthy) because it exists to render markdown fetched at runtime and ours lives in the repo. The one thing the content layers offer that the official plugin does not is Zod-validated frontmatter; a typed metadata export buys the same build-time failure on a malformed field without the dependency. Howard's stated constraint was to use something simple that works with the setup rather than hand-roll blog glue — the remaining hand-written code is a roughly twenty-line directory read for the index.

---

## 2026-07-31 — Insights section lives inside the existing landing-page app at /insights
**Decision:** The blog/insights section is built into the existing Next.js app at miho-landing-page/web/, served at mihopartners.com/insights. Not a separate site, not a subdomain, not a hosted blog platform.
**Why:** The app is already its own git repo (howardwkim/miho-partners-landing) wired to Vercel, so a second property would mean a second deploy pipeline and split domain authority for no gain. A two-person firm with no traffic cannot afford to divide SEO signal or maintain two codebases. Rejected alternatives: a subdomain (blog.mihopartners.com), which splits domain authority and reads as a bolted-on afterthought, and a hosted platform such as Substack or Ghost, which puts content outside git and makes machine-authored publishing an API problem instead of a commit.

---

## 2026-07-28 — MiHO Partners is a distinct venture from Mike's solo brand, not a rebrand of it
**Decision:** MiHO Partners (Mike + Howard) is a new, distinct joint venture. Its landing page sells the productized AI audit-to-implementation offer, not Mike's general consulting practice at michaelgrabham.com. Voice, tactics and content elements may still be pulled from the solo brand where useful, but the ICP, offer and pricing are MiHO's own — not inherited wholesale.
**Why:** `docs/miho/brand/brand-dna.md` describes Mike's existing solo consulting as broad SMB coaching with pricing TBD per project and no AI mechanism — that doc cannot double as MiHO's ground truth without contradiction. Treating MiHO as a separate venture resolves the contradiction and matches CLAUDE.md's premise (two named co-founders, one specific offer from the Gannon transcript). Rejected alternative: MiHO as a rebrand of Mike's existing practice with an AI-audit line item bolted on — rejected because that offer has no fixed pricing or productized shape, which the landing page brief requires.

---

## 2026-07-28 — Page shows the whole offer ladder, one CTA, services section pushed to the bottom
**Decision:** The page presents the full ladder (audit → implementation → retainer) rather than the audit alone, but every section resolves to a single CTA: book the audit. Implementation and retainer get a real section with its own heading — not a folded-in line — but it sits at the bottom of the page, after objections and founder proof, right before the final CTA. No separate CTA of its own.
**Why:** The goal is booking the audit; other services are foot-in-the-door follow-on, not a parallel offer to choose between. Showing them at all answers a real objection in `icp.md` ("is this worth the money") by proving the audit leads somewhere. But showing them early or with their own CTA forces a choice mid-pitch and splits conversion intent. Bottom placement means a visitor has already decided to book (or not) by the time they see it, so it reads as depth/credibility rather than a second offer. Rejected alternatives: audit-only page (loses the ROI reassurance), a single folded-in line instead of a section (undersold the "other things we can do" signal Howard wanted visible), and mid-page placement (competes with the audit case for attention).

---

## 2026-07-28 — Lead persona is the Ready-to-Grow Owner
**Decision:** Of the three ICP personas in `icp.md` (Plateaued Owner, Accidental CEO, Ready-to-Grow Owner), the page leads with the Ready-to-Grow Owner. The other two are folded in as secondary recognition, not the headline's target.
**Why:** The Ready-to-Grow Owner's stated pain — "AI feels overwhelming, I don't know where to start or if it even applies to my business," actively evaluating tools, not paralyzed — maps directly onto what the audit sells: a clear, low-risk answer to "where do I start." The Plateaued Owner and Accidental CEO are buried in day-to-day execution and are a better fit further down the ladder (implementation/retainer) once trust is established, not as the persona who books a discrete diagnostic cold.

---

## 2026-07-28 — Trust is carried by founder operating history, not a client roster
**Decision:** MiHO Partners has no client track record under its own name yet. The page establishes trust by borrowing from Mike's and Howard's individual operating histories — framed as "who's behind this" — rather than claiming results MiHO itself hasn't produced yet. No case study or client roster exists to draw on.
**Why:** Confirmed with Howard: there is no early client or case study available. The audit itself (cheap, fast, low-risk) is the mechanism that compensates for the missing track record — that's the objection-handling logic the low-risk entry offer already carries, not a gap the copy needs to disguise.

---

## 2026-07-28 — Audit price is shown, but in the offer section, not the hero
**Decision:** The $399 audit price is disclosed on the page, but not at first landing (hero). It appears in the offer detail section, further down.
**Why:** A visible, specific number still serves as the trust device for the "is this worth the money" objection — hiding it entirely would read as evasive against the direct, no-hedging brand voice. But Howard wants the hero focused on the hook and pain, not the transaction, so price waits until the visitor is reading the actual offer, not at first impression.

---

## 2026-07-28 — Entry offer is called "audit," but always paired with a solutions qualifier
**Decision:** The entry offer keeps the plain word "audit." But it never stands alone in copy — it's always paired with language making clear the deliverable is prescribed, usable solutions, not a diagnostic report. ("Audit" describes the process; the promise is what comes out of it.)
**Why:** Howard flagged that "audit" alone reads as "you tell me what's wrong," not "you tell me what to do" — and the actual deliverable (per the Gannon model) is prescriptive: specific AI tools/fixes, not just a findings list. Losing that in the name would undersell the offer's real value. Rejected alternative: switching the word entirely — rejected in the same breath, since the fix is adding a qualifier, not renaming.

---

## 2026-07-28 — Audit guarantee finalized: refund if the diagnosis can't find 5+ hours/week
**Decision:** The audit's money-back guarantee follows Gannon's mechanism exactly: if the assessment can't identify at least 5 hours/week of reclaimable time, MiHO refunds the fee, no questions asked. This is checkable at report time, before the client acts on anything — not conditioned on the client implementing the recommendations.
**Why:** Superseded the earlier version logged same-day (follow-through-conditioned, no fixed day count) once the Gannon transcript was extracted and the mechanism mismatch was surfaced. Howard chose to match Gannon's source model rather than invent a different mechanism — matching source material data (Gannon's own average client saves 7 hrs/week against a 5-hr guarantee floor) over a self-invented, harder-to-verify "did you get value" standard. Rejected alternative: the follow-through/no-time-window version — rejected because it can't be evaluated objectively (no clear standard for "didn't get value" if the client never acted), where the 5-hour floor is checked directly against the report itself.

## 2026-07-28 — Reference hunting stopped; next design attempt goes generative
**Decision:** Stop collecting design references. Do not open another round. When design resumes, design against the written brief directly using Modern Life and Boords as the only calibration points.
**Why:** Four rounds and roughly thirty candidates produced two accepted references, both from the first batch, and nothing since has landed. The search is not converging. The brief is agreed and stable; what is missing is a page satisfying it, which is a generative problem rather than a discovery one. Rejected alternative: a fifth hunt on a different axis.

---

## 2026-07-28 — Design references and copy references are hunted in different categories
**Decision:** Hunt look-and-feel among small, well-designed product and brand companies with category ignored. Hunt copy, voice and offer framing among 1-5 person consultancies with design ignored. Two lists, two hunts.
**Why:** Every site found in the consultancy arena was rejected on design (Caboodle, Other Land, Test Double, Clearleft, Aspen Search, Stereo Associates, Hoare), while the only two ever accepted, Modern Life and Boords, are not consultancies at all but small product companies. Consultancies sell judgment rather than craft and rarely invest at that level, so searching for a well-designed consultancy keeps returning under-designed sites in the right category. The rejected alternative was continuing to hunt a single combined list.

---

## 2026-07-28 — Scale of presentation is a selection criterion separate from aesthetics
**Decision:** Reject references that present at venture scale, independent of how good they look. Select for boutique/practice presentation: named humans and candid photos over logo walls, first-person voice, short nav ending in Book a call, personality or an explicit anti-scale stance in place of metrics.
**Why:** A first hunt matched only visual signals and returned Collective, HoneyBook, Found, Gusto and Mercury, all rejected as 'too large, like banking'. The tell is the trust devices themselves: thousand-member counts, press logo walls, award laurels and Enterprise mega-menus are scale-proofs a two-person firm cannot use and should not want. This is about how a page presents scale, not company size.

---

## 2026-07-28 — Landing page design brief: restrained modern tech, founder-forward, trust-first
**Decision:** Trust is the single goal. Warm neutral grounds, type/layout/colour-led, one confident accent colour, an editorial accent, founder photos of Mike and Howard carrying credibility. Motion and 3D allowed later but not in the first draft.
**Why:** Rejected two alternatives explicitly. The professional-services look (accountant/law firm) was rejected as boring. The saturated AI-startup look (near-black grounds, monospace/terminal type, purple-orange gradients, glow, grid overlays) was rejected as category-saturated and as reading like vendor hype to a small business owner. Looking different from other AI automation agencies is an asset, not a limitation.
