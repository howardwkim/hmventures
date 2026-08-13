# The article format

The one contract that matters. The site validates every field of it during the build, so a
mistake here does not ship a slightly-wrong page — it fails the build and stops the site from
updating until it's fixed. Follow this exactly.

Source of truth on the site: `lib/insights/types.ts` (the field types and the category list)
and `lib/insights/posts.ts` (the validator that runs at build time). If this file and those
ever disagree, the site wins — read them and update this file.

## File and slug

One article is one file: `content/insights/<slug>.mdx`

The slug is the URL — `mihopartners.com/insights/<slug>` — and it comes from the filename, not
from any metadata field. Derive it from the title: lowercase, words joined by hyphens, no
punctuation, no dates, no stop-word padding. Short beats complete.

> "The three hours a week your inbox is quietly eating"
> → `inbox-three-hours-a-week.mdx`

Never rename a published file. The old URL dies and any link to it breaks.

## The metadata block

Every article opens with a YAML frontmatter block — the fenced `---` pair — before any prose:

```
---
title: "Sentence case, no title case"
deck: "One sentence stating the article's claim."
date: "2026-08-13"
category: "Operations"
author: "howard"
draft: false
---
```

Quote every value. It costs nothing and it stops a title containing a colon, a `#`, or a
leading `>` from silently breaking the parse.

The `---` block is invisible on the page — the site strips it before rendering — and it never
appears in the article body.

| Field | Required | Rule |
|---|---|---|
| `title` | yes | Non-empty. Sentence case. Becomes the page `<h1>` and the browser tab title. Do **not** repeat it as a heading in the body. |
| `deck` | yes | Non-empty. One sentence stating the article's claim. Renders in italic serif under the title and doubles as the meta description and the listing summary. Not a teaser, not a question — a claim. |
| `date` | yes | Exactly `YYYY-MM-DD`. **Today's date** — not a date found in the author's file. It sorts the listing, prints under the byline, and feeds the sitemap and the article's social-preview metadata, so a stale one is visible in several places. The build only checks the *shape*: `2026-13-45` passes and then renders as "Invalid Date". |
| `category` | yes | **Exactly one of the five below.** Closed list. |
| `author` | yes | Exactly `"mike"` or `"howard"`. Lowercase. **This is who actually wrote the article, not whose turn it is** — never infer it from the previous post, and never from this template's default. Always confirm it with the person publishing. It sets the byline name and photo, and the build cannot catch it being wrong. |
| `image` | no | Path under `/insights/`, e.g. `"/insights/inbox.jpg"`. The file goes in `public/insights/`. Most posts have no image and that is the normal case. |
| `imageAlt` | only with `image` | Required and non-empty whenever `image` is set. Omitting it fails the build. |
| `draft` | no | Boolean. `true` = visible in local development, excluded from production, the listing and the sitemap. Omit or set `false` to publish. |

### The five categories

```
Time drains
AI tools
Operations
Delegation & hiring
Pricing
```

Copy one of those strings character for character — the case and the `&` matter, and a
trailing space fails. The list is closed on purpose: articles here are largely
machine-written and nobody proofreads metadata, so free text would quietly accumulate ghost
categories. **If an article genuinely fits none of the five, that is a conversation with
Howard and Mike, not a metadata edit.** Do not add a category to make one article fit.

## The body

Below the metadata block, write markdown. Headings, lists, links, tables, bold, italic and code
all work with no extra syntax and no classes. Styling is applied automatically by the article
template; never add CSS classes, `<div>`s, or inline styles.

### It is MDX, not plain markdown — two characters will break the build

`<` and `{` are code characters here, and both appear in ordinary business prose. Scan the
article for them before writing the file and escape them. This is the one edit you make to the
author's text, and it changes how a character is written, never what it says.

| In the prose | Breaks as | Write instead |
|---|---|---|
| `spend <5 minutes a day` | `Unexpected character '5' before name` — fails at compile | `spend &lt;5 minutes a day` |
| `a {customer_name} placeholder` | `ReferenceError: customer_name is not defined` — **compiles clean, then fails during "Generating static pages"** | `` a `{customer_name}` placeholder `` or `a \{customer_name\} placeholder` |
| `<https://example.com>` or `<mike@mihopartners.com>` | same as the first row | a real markdown link: `[example.com](https://example.com)` |

Anything already inside backticks or a fenced code block is safe and needs no change.

The brace failure is the nasty one: the build looks fine right up until the last stage, and the
error names a word from the article with no file path, so it reads like an unrelated code bug.

Two conventions that are specific to this site:

**Start headings at `##`.** The title is already the page's `<h1>`. A `#` in the body produces
a second one and breaks the page's document outline.

**Every article carries exactly one `<Takeaway>`, near the end.** This one is a convention, not
a build check — zero or three will compile fine, and a malformed one renders wrong without
failing. It is the one custom
component the site provides. It holds the two or three concrete things a reader should
actually do. It is a structural slot, not decoration, and it exists because MiHO sells
prescription rather than diagnosis — an article that ends on a platitude contradicts the
thing being sold.

```
<Takeaway>

1. Something specific enough to start today.
2. Something with a clear yes/no outcome.
3. Something that compounds if they do it.

</Takeaway>
```

No import is needed — it is available in every post. Its heading defaults to "What to do
about it"; override it with `<Takeaway title="Where to start">` when the default reads wrong.
The blank lines inside the tags are required for the markdown inside to render.

Close with a short paragraph after the Takeaway. Not a summary — a last thought that lands.

## The working reference

`content/insights/_template.mdx` in the site repo is the live annotated example. It stays
`draft: true` forever and it is also what keeps `content/insights/` non-empty, which the build
requires. **Copy it, never edit or delete it.**

## Converting from whatever the article arrived as

The author's file will not look like this, and that is expected. Do the whole conversion
yourself:

- **Their front matter** (a YAML block with different field names, a different metadata shape,
  or none at all) — mine it for useful values, then rewrite it as exactly the block above.
  Matching field names is not enough: an unknown extra key is harmless, but a *missing* or
  *misnamed* required one fails the build.
- **A `#` title at the top of their body** — pull it into the `title` field and delete it from the
  body.
- **A summary, subtitle, or standfirst line** — that is the `deck`. If there isn't one, lift
  the article's own thesis sentence verbatim. If nothing in the article works as one, **ask the
  author for a sentence — do not write it yourself.** The deck is published copy, and writing
  copy is not this skill's job.
- **Their headings** — shift the whole tree so the top level is `##`.
- **A conclusion, "key takeaways", "next steps", or an action list** — move it, as written,
  inside the single `<Takeaway>`. That is a structural move, not a rewrite; keep their wording.
  If the article has no such section, say so to the author and let them supply one. Never
  invent the actions yourself.
- **Smart quotes, em dashes, footnotes, emoji** — all fine, leave them alone.
