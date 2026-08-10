# Design tokens — extracted from modernlife.com

Pulled from the live site's computed CSS and stylesheet rules (Playwright), not eyeballed from
screenshots. Source of truth for the MiHo Partners landing page's visual system.

## Typography

- **UI / body / headline font:** `"Noi Grotesk", sans-serif` — geometric grotesk.
- **Accent font:** `"Bradford LL"` — serif, applied via a dedicated `.font-bradford.cc-italic`
  class to single words/phrases inside headlines and to link text. Color is inherited, not
  changed — the accent is carried by font + italic alone, not a color shift.
- **H1:** 60px / line-height 60px / weight 300 (light) / letter-spacing -0.2px.
- **Body:** 16px / line-height 20.8px / weight 400.
- Headline markup pattern: `Bringing the future <span class="font-bradford cc-italic">to
  life</span>` — plain lead-in, accent on the back half only.

## Color palette

Named token families in the source (kept as-is since the naming itself is informative):

**Spring (primary brand green)**
| Token | Hex | Use |
|---|---|---|
| `--spring-deep` | `#005924` | link/text hover color (deepest) |
| `--cta-spring-vibrant` | `#118631` | nav-link hover color |
| `--spring-vibrant` | `#6cd689` | primary CTA button background |
| `--spring-vibrant-50` | `#b6ebc4` | CTA button hover background (lightened) |
| `--spring-bright` | `#f4ffb0` | bright yellow-green |
| `--spring-bright-50` | `#f9ffd8` | pale yellow-green tint |
| `--spring-mute` | `#eef2e4` | muted sage-gray surface |
| `--spring-light-25` | `#fbfcf8` | near-white sage tint |

**Fall (warm secondary, illustration-only — not used as UI accent)**
| Token | Hex | Use |
|---|---|---|
| `--fall-deep` | `#bb4038` | brick red |
| `--fall-vibrant` | `#ff8061` | coral (illustration) |
| `--fall-bright` | `#f8a08c` | peach |
| `--fall-medium` | `#f2e0ca` | tan/peach — the ring halo behind the hero illustration |
| `--fall-light-50` | `#f8efe5` | pale peach |
| `--fall-mute` | `#fff6e9` | cream-peach |

**Neutrals**
| Token | Hex | Use |
|---|---|---|
| `--neutral-black` | `#000000` | primary text |
| `--white` | `#ffffff` | — |
| `--neutral-mid-1` | `#fbfcf5` | page background |
| `--ux-gray-1..4` | `#fafafa` / `#e7e7e7` / `#aeaeae` / `#7a7a7a` | borders, disabled, secondary text |

**System**
| Token | Hex | Use |
|---|---|---|
| `--error` | `#ec1313` | not used on this page |

Note: all three families are available to MiHo — spring, fall and neutrals. Two things to
carry when reaching for `fall`: on Modern Life these warm tones are **illustration-only** and
never UI accents, so using them as UI accents is a deliberate departure from the reference;
and the brief's ban on purple-to-orange *gradients* as AI-startup styling is unaffected — that
rules out a gradient treatment, not these hues.

## Buttons

- Default: `background: #6cd689`, `color: black`, `border-radius: 6px`, `padding: 12px 14px`,
  font Noi Grotesk 16px/400. Not a pill — a soft rounded rectangle.
- Hover: background lightens to `#99e3ad` (a step lighter than default, not darker).

## Link / clickable-text hover behavior

This is the detail that was missing before: **hover states are real color transitions, not
opacity or underline tricks.**

- `.nav-link:hover` → `color: #118631` (cta-spring-vibrant)
- `.nav-link.w--current:hover` → `color: #005924` (spring-deep) — active nav item hovers darker
- `.footer__link:hover`, `.rich-text a:hover`, `.blog__inline-link:hover`,
  `.link-green-inline:hover` → all → `color: #005924` (spring-deep)
- `.link-grey-inline:hover`, `.ins__faq-link:hover` → `color: #6cd689` (spring-vibrant, the
  brighter mint) — a lighter-weight hover for already-muted text
- `.about__team-thumbnail:hover` → `color: #005924` + on the wrapping image,
  `opacity: 0.8; box-shadow: 0 2px 24px rgba(0,0,0,0.1)`
- Form field borders: default gray → `border-bottom-color: #005924` on hover/active

**Pattern to apply site-wide:** any clickable text (nav links, footer links, inline text links,
"learn more" style links) goes from black/neutral to a spring green on hover — `#118631` for
primary nav, `#005924` for inline/body links. No underline-only or opacity-only hovers for text
links; color is the primary signal.

## What this means for our page

- Replace the ad hoc cream/sage/blue/coral tokens with the actual `spring`, `fall` and
  `neutral` families above.
- Give every clickable text element (nav links, footer links, "Book your audit" text treated as
  a link where relevant, inline emphasis links) a `:hover` color transition into spring-deep or
  cta-spring-vibrant — currently only the button itself has any hover treatment.
- Button radius should be 6px, not the ~8-12px we had — tighter, more "soft rectangle" than
  "rounded card."
- Headline accent is carried by the serif italic font alone; stop also changing its color/size
  disproportionately — match Modern Life's restraint (same color, just font + italic + the
  natural size difference from line-wrap).
