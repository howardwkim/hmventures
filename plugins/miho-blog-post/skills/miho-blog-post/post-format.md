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

Every article opens with this, before any prose:

```
export const meta = {
  title: "Sentence case, no title case",
  deck: "One sentence stating the article's claim.",
  date: "2026-08-13",
  category: "Operations",
  author: "howard",
  draft: false,
};
```

| Field | Required | Rule |
|---|---|---|
| `title` | yes | Non-empty. Sentence case. Becomes the page `<h1>` and the browser tab title. Do **not** repeat it as a heading in the body. |
| `deck` | yes | Non-empty. One sentence stating the article's claim. Renders in italic serif under the title and doubles as the meta description and the listing summary. Not a teaser, not a question — a claim. |
| `date` | yes | Exactly `YYYY-MM-DD`. Anything else fails the build. Sorts the listing; nothing else reads it. Use the publish date. |
| `category` | yes | **Exactly one of the five below.** Closed list. |
| `author` | yes | Exactly `"mike"` or `"howard"`. Lowercase. Articles alternate between them. |
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

Below the metadata block, write plain markdown. Headings, lists, links, tables, bold, italic,
code — all work with no extra syntax and no classes. Styling is applied automatically by the
article template; never add CSS classes, `<div>`s, or inline styles.

Two conventions that are specific to this site:

**Start headings at `##`.** The title is already the page's `<h1>`. A `#` in the body produces
a second one and breaks the page's document outline.

**Every article carries exactly one `<Takeaway>`, near the end.** This is the one custom
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

- **Their front matter** (YAML `---` blocks, a different metadata shape, none at all) — read
  whatever is there for useful values, then discard it and write the `export const meta`
  block above. Do not leave a YAML block in the file; MDX does not read it.
- **A `#` title at the top of their body** — pull it into `meta.title` and delete it from the
  body.
- **A summary, subtitle, or standfirst line** — that is the `deck`. If there isn't one, write
  one from the article's actual argument.
- **Their headings** — shift the whole tree so the top level is `##`.
- **A conclusion, "key takeaways", "next steps", or an action list** — reshape it into the
  single `<Takeaway>`. If the article has no concrete actions at all, say so to the author
  before publishing; a missing Takeaway is a content problem, not a formatting one.
- **Smart quotes, em dashes, footnotes, emoji** — all fine, leave them alone.
