# Insights section — build plan

**Status:** planned, not built. Written 2026-07-31.
**Scope:** add a blog/insights section to the existing MiHO Partners landing page.
**Not in scope:** writing the actual articles, the content pipeline, page code.

---

## 1. What this is

The landing page at `web/` is a single route (`app/page.tsx`, 329 lines) that already
implements the locked design system — Modern Life's spring/neutral tokens in
`globals.css`, Manrope for body and Instrument Serif for the italic accent. This plan
extends it with an insights section: a listing page, an article template, a nav entry, and
a homepage component sampling recent posts.

Articles are markdown files in the repo. Adding one means committing a file; Vercel
rebuilds. That is the whole authoring surface, and it is deliberate — content here is
primarily AI-generated, so the authoring surface matters more than the reading surface.

Design reference is Modern Life's insights pages, deliberately lighter. Their version is a
content library with seven categories, whitepapers, webinars and gated PDFs. We take the
restraint and the typography, not the machinery.

## 2. Tooling — `@next/mdx`

**Decision: the official Next.js MDX plugin, not a third-party content layer.**

| Option | Weekly installs | Latest | Assessment |
|---|---|---|---|
| `@next/mdx` | — | 16.2.12 (2026-07-25) | Chosen. Versioned in lockstep with Next, Turbopack documented |
| `next-mdx-remote` | 936k | 6.0.0 (2026-02) | Healthy but built for markdown fetched at runtime; ours is local |
| content-collections | 128k | 0.15.2 (2026-06) | Contentlayer's most-adopted successor; pre-1.0, wraps `next.config` |
| Velite | 80k | 0.4.0 (2026-06) | Same category, smaller, mid-rewrite to 1.0 |
| Contentlayer | — | — | Unmaintained since Netlify acquired Stackbit |

The app runs Next 16.2.12 and `@next/mdx` publishes at 16.2.12 — same release train,
tested against Turbopack by the Next team. Both third-party contenders wrap `next.config`
with their own build plugin and neither documents Next 16 or Turbopack support. That
coupling is exactly what stranded Contentlayer users when Next moved underneath them.

The one thing the third-party options offer that the official plugin does not is
Zod-validated frontmatter. We get the same guarantee more cheaply: each post exports a
typed metadata object, so TypeScript fails the build on a missing or malformed field.

### Packages to add

```
@next/mdx  @mdx-js/loader  @mdx-js/react  @types/mdx
remark-gfm  rehype-slug
@tailwindcss/typography
```

`remark-gfm` (tables, strikethrough, autolinks) and `rehype-slug` (heading anchor ids) are
both Turbopack-safe because neither takes function options — Turbopack cannot pass
JavaScript functions to its Rust core, so plugin options must be serializable. Register
them by string name in `next.config.ts`, per the Next 16 MDX guide.

### Configuration notes

- `next.config.ts` needs `pageExtensions` extended and `createMDX` wrapping the export.
- An `mdx-components.tsx` at the project root is **required** for `@next/mdx` under the
  App Router — it will not work without it. This is where element-level components are
  mapped.
- Tailwind v4 is CSS-first: the typography plugin is registered with
  `@plugin "@tailwindcss/typography";` in `globals.css` directly under the existing
  `@import "tailwindcss";`. There is no `tailwind.config` to edit.

## 3. Content model

Posts live at `web/content/insights/<slug>.mdx`. The filename is the URL slug.

Each post exports a typed metadata object:

```ts
// web/lib/insights/types.ts
export const CATEGORIES = [
  "Time drains",
  "AI tools",
  "Operations",
  "Delegation & hiring",
  "Pricing",
] as const

export type Category = (typeof CATEGORIES)[number]
export type Author = "mike" | "howard"

export type PostMeta = {
  title: string
  deck: string           // one sentence, rendered in serif italic under the title
  date: string           // ISO, YYYY-MM-DD
  category: Category
  author: Author
  image?: string         // optional — see §6
  imageAlt?: string      // required by lint convention when image is set
  draft?: boolean        // true keeps it out of production builds
}
```

Category is a union type, not free text. A post with an invented or misspelled category
fails the build instead of silently creating a ghost category — this matters specifically
because articles are machine-written and nobody proofreads the frontmatter.

`web/lib/insights/posts.ts` reads the content directory for slugs and imports each module
to collect its exported metadata. It exposes `getAllPosts()` (sorted newest first, drafts
filtered in production) and `getPost(slug)`. This is the only hand-written glue in the
system — roughly twenty lines, a directory read, not a blog engine.

Authors are a two-entry record in `web/lib/insights/authors.ts`: name, one-line
credential, headshot path, email. The headshots already exist at
`web/public/founders/mike-closeup.jpg` and `web/public/founders/howard.jpeg`.

## 4. Routes

| Route | File | Rendering |
|---|---|---|
| `/insights` | `app/insights/page.tsx` | Static |
| `/insights/[slug]` | `app/insights/[slug]/page.tsx` | Static via `generateStaticParams`, `dynamicParams = false` |

Both are statically generated at build time. A slug not present in `generateStaticParams`
returns 404 rather than attempting a runtime render.

Per-route `generateMetadata` supplies title, description (from the deck), and OpenGraph
tags. A `sitemap.ts` enumerates the homepage plus every published post.

## 5. The article template

Modern Life's article pages are title, category, date, hero image, subheads, related
links. That is the sparseness worth improving on — it is a page that publishes an article
without doing anything with it.

The design principle: **a cold visitor arriving from search has never seen the homepage.**
The article page has to carry the founder proof and the offer on its own, or it is a page
that builds trust for nobody.

Structure, top to bottom:

1. **Shared nav** — same header as the homepage.
2. **Category label** — small, above the title. Links back to the listing filtered to
   that category.
3. **Title** — Manrope light, matching the homepage's `text-4xl`/`text-5xl` treatment.
4. **Deck** — one sentence in Instrument Serif italic, stating the article's claim. This
   is the site's established emphasis device (`font-accent italic`), reused. Modern Life
   has no equivalent; it is the single cheapest thing that makes an article page feel
   authored rather than generated.
5. **Byline block** — headshot (44px circle), author name, "MiHo Partners", date, reading
   time. Articles alternate between Mike and Howard so the section reads as two people
   writing, not a content feed. No credential line: repeated under every article it reads
   as selling rather than writing, and the face plus the name already do the human work.
6. **Optional hero image** — rendered only when `image` is set in the post's metadata.
   The template must look finished without one; see §6.
7. **Body** — `@tailwindcss/typography` `prose` as the base, overridden to the site's
   tokens (see §8). Single column, roughly 65–70 characters measure, no sidebar.
8. **Takeaway block** — a custom MDX component holding the concrete punch list. See below.
9. **End CTA** — the audit, reusing the ink-background block from the homepage's final
   CTA section.
10. **More insights** — two or three recent posts as compact rows.
11. **Shared footer.**

Explicitly not included: table of contents, share buttons, comments, newsletter signup,
author archive pages, tag clouds, reading-progress bars. Under twenty posts a table of
contents is theater, and every one of these is weight Modern Life carries that we do not
need.

### The takeaway block — the one custom component

`<Takeaway>` is the only bespoke MDX component in the system, and it is the reason the
template is worth designing rather than lifting.

MiHO's entire offer is "one useful thing to fix, not a framework." The audit's promise is
prescription, not diagnosis — that is settled in the decisions ledger and it is why the
entry offer is always paired with a solutions qualifier. An article that ends on a
platitude actively contradicts the thing being sold.

`<Takeaway>` is a visually distinct block near the end of the article holding a short
punch list: the concrete two or three things a reader should actually do. Styled on the
`--surface` sage token with the serif accent on its heading. It is the audit in miniature,
and it gives the AI writing these pieces a structural slot it has to fill with something
specific.

Making it a required element of the template — rather than an optional flourish — is the
mechanism that keeps machine-written content from drifting into generic business advice.

## 6. Images — optional, never required

Images are a per-post choice. The `image` field is optional and both the article template
and the listing row must render correctly with or without one.

- **With an image:** article shows a hero below the byline; listing row shows a small
  thumbnail at the leading edge.
- **Without:** article goes byline straight to body; listing row is type-only, with the
  category label and deck carrying the visual interest.

The listing must not look broken when some posts have images and others do not. The
practical constraint: a fixed row height with the thumbnail slot either filled or
collapsed, not a masonry grid that reflows around missing images.

Optionality is the point — this preserves the choice per article rather than committing
the section to an image budget it may not want to pay.

## 7. Listing page

One flat reverse-chronological list. No featured hero post, no content types, no
pagination until it is actually needed.

Each row: category label, title, deck, date, author name, optional thumbnail. Hover
follows the site convention already documented in `design-tokens-modernlife.md` — a real
colour transition to spring green, never opacity or underline alone.

**Category filtering** is a row of chips above the list, filtering client-side. No
per-category routes, no sidebar navigation, no category landing pages with their own
copy. Five categories, fixed in the type union, extendable later by editing one file.

Page header: a short heading in the homepage's style plus one line of positioning. Not a
manifesto.

## 8. Design system

Everything already exists in `globals.css`. The insights section adds no new tokens — but
the palette is wider than when this plan was first drafted, and three devices now exist.

- Ground `--background` `#fbfcf5`, sage `--surface` `#eef2e4` for the takeaway block and
  alternating sections, `--ink` `#005924` for the CTA block.
- Manrope for body and headings, Instrument Serif italic for the deck, the takeaway
  heading, and accented phrases — same restraint as the homepage: the accent is carried by
  font and italic alone, never by a colour shift.
- Buttons stay `6px` radius on `--accent` `#6cd689`, matching `BookButton`.

### Devices — which apply here

The homepage gained three devices on 2026-07-31. Their use in insights:

- **Scroll reveal** (`.reveal`, `.reveal-delay-1`, `.reveal-delay-2`) — use it. Pure CSS
  via `animation-timeline: view()`, no JavaScript. Apply to listing rows and to the
  article's header and end-CTA blocks. Do **not** apply it to individual body paragraphs;
  a reveal firing mid-read is distracting rather than restrained.
- **Highlighter swipe** (`.highlight-swipe`) — available, at most one phrase per page.
  The natural home is the deck.
- **Gradient sweep** (`.guarantee-shimmer`) — do **not** use. The style guide reserves it
  for the guarantee and states that a second appearance destroys its meaning.

### Palette

The warm "fall" family was admitted 2026-07-31 (see the ledger), so `--warm` tan and
`--highlight` lime are now available alongside the greens. Greens stay primary; the warm
tones are for sparing emphasis. Nothing in the insights section requires them, but the
category chips are a reasonable place if the greens alone read flat.

### Style guide obligation

`app/designs/page.tsx` states its own rule: anything on the site not documented there is
ad hoc and should be fixed. The four new components — takeaway block, byline block,
listing row, category chip — each need an entry. This is a build step, not optional
polish. The page is `robots: noindex` and must stay out of the sitemap.

`prose` is the base but must be overridden to these tokens rather than accepting
Tailwind's grays. In Tailwind v4 this is a `@utility prose-miho { ... }` block in
`globals.css` setting the `--tw-prose-*` variables, applied alongside `prose` on the
article body. Link colour and hover in particular must match the site's inline-link
convention.

## 9. Homepage integration

**Nav.** Add `Insights` to the header nav, before `Beyond the audit`.

`SiteNav` and `BookButton` are already extracted into `app/components/`, with a working
mobile hamburger panel — that part of the prerequisite is done. What remains: every link
in them is still a same-page anchor (`#offer`, `#founders`, `#ladder`, and `#book` inside
`BookButton`). From an article URL those resolve against the article, not the homepage,
and silently do nothing. They must become root-relative (`/#offer`, `/#book`). The footer
is still inline in `page.tsx` and needs extracting the same way.

This is a prerequisite, not a nice-to-have — it is a real bug the moment a second route
exists, and `/designs` already trips it today.

**Sampler component.** A section on the homepage showing the two or three most recent
posts, placed between the Founders section and the Ladder section.

That position is deliberate. The page's sequence becomes: who we are → how we think →
where this goes → book. The sampler extends founder proof rather than interrupting the
Ladder-to-CTA run, which is the page's closing sequence. It reuses the listing row
component so there is one row design, not two.

It gets a heading and a "Read all insights" link. It does not get its own CTA — the
decisions ledger settled that every section resolves to the single audit CTA.

## 10. How this serves trust and the CTA

The page has one goal (trust) and one CTA (book the Time Saver Audit). The blog serves
both, but not equally, and it is worth being honest about which.

**Trust is the primary job.** MiHO has no client roster and no case studies; the ledger
settled that trust comes from founder operating history. A blog is the only trust device
available that demonstrates judgment rather than asserting it. An article that names a
specific time drain and prescribes a specific fix is a free sample of exactly what the
audit sells. That is why the takeaway block is structural: it is the proof mechanism, not
decoration.

**The CTA is secondary and single.** One audit CTA at the end of every article. No
newsletter, no lead magnet, no gated download, no second offer. A reader who arrives cold
on an article and books is a bonus; the realistic job is that a reader who found MiHO
elsewhere reads two articles and books with more confidence.

**The alternating byline is a trust device, not a formatting choice.** Two named people
with headshots and credentials, writing in turn, is the same proof the homepage leans on,
extended to the one surface a search visitor lands on first.

## 11. `_template.mdx` — and why the directory can never be empty

`content/insights/_template.mdx` is permanent. It is the authoring reference: every
metadata field with a comment explaining it, the valid category list, and a worked
`<Takeaway>`. It carries `draft: true`, so production excludes it from the listing, the
routes and the sitemap — a build with only this file prerenders zero articles.

It is also load-bearing. The article route resolves posts through a dynamic import over
`content/insights/`, and a bundler cannot build a module context over an empty directory:
delete every `.mdx` and the build fails with `Can't resolve '@/content/insights/'
<dynamic> '.mdx'`. That is not a hypothetical — it is the state the section ships in
before the first article exists. The template file is what keeps that state buildable.

**Do not delete it**, and do not "clean up" the directory to empty.

Three disposable seed posts were used during the build to verify the with-image row, the
type-only row, the draft exclusion and the prose overrides. They have been removed.

### The empty state

With no published posts, `/insights` renders "Nothing published yet" and the homepage
sampler renders nothing at all rather than an empty heading. The nav still links to
`/insights`. Worth deciding before deploy whether the nav entry should wait for the first
real article.

## 12. Build sequence

1. Make `SiteNav` and `BookButton` links root-relative; extract the footer into a shared
   component; add `Insights` to the nav.
2. Install packages; configure `next.config.ts` and `mdx-components.tsx`; register the
   typography plugin and write the `prose-miho` overrides.
3. Content model: types, authors record, `posts.ts` directory reader.
4. Article route and template, including `<Takeaway>` and the byline block.
5. Listing route with category chips.
6. Homepage sampler section.
7. Metadata, sitemap, `_template.mdx`, verify the draft flag excludes correctly.
8. Document the four new components in `app/designs/page.tsx`.

**Status: built 2026-07-31.** All eight steps done, build and lint clean.

**Before writing any code:** `web/AGENTS.md` states this Next version has breaking changes
against training data and requires reading `node_modules/next/dist/docs/` for the relevant
guide first. That applies to the MDX setup, `generateStaticParams`, and metadata.

## 13. Settled minor calls

- **Reading time — include it.** Computed at build from word count at 200 words per
  minute, shown in the byline block. It costs three lines, and it answers the one question
  a skimming visitor actually has before committing to an article.
- **RSS feed — no.** There are no subscribers and no reason to expect any. It is surface
  area maintained for nobody. Revisit only if someone asks for it.
- **Pagination — no.** The listing renders every published post. Revisit past roughly
  twenty, which at any realistic publishing rate is a long way off.

## 14. Nothing is open

Every question this plan needs answered is answered. Authorship is settled: each article
is bylined to Mike or Howard, alternating, with headshot and credential — that is a field
in the post's metadata, not a dependency. Whatever produces a valid `.mdx` file in
`content/insights/` publishes.

This is ready to build.
